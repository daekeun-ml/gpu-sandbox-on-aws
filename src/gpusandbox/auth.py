"""Workload authentication with audience-bound Kubernetes ServiceAccount tokens.

Callers (the trainer, or the gateway in production) present a projected ServiceAccount token
whose audience is this service. Sandbox pods verify it offline against the cluster's
ServiceAccount issuer public keys (a JWKS document mounted from a ConfigMap), so they need no
Kubernetes API access and hold no secrets that candidate code could steal. Authorization is an
explicit allowlist of ServiceAccount subjects.

Fails closed: if the audience, issuer, allowlist or key set is missing or unreadable, every
protected request is rejected. ``<PREFIX>TEST_BYPASS=1`` disables verification for local smoke
tests on loopback only; it is off by default.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class AuthError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class AuthConfig:
    audience: str
    issuer: str
    allowed_subjects: frozenset[str]
    jwks_file: Path | None
    test_bypass: bool = False

    @classmethod
    def from_env(cls, prefix: str = "SANDBOX_AUTH_") -> AuthConfig:
        subjects = os.environ.get(f"{prefix}ALLOWED_SUBJECTS", "")
        jwks = os.environ.get(f"{prefix}JWKS_FILE", "")
        return cls(
            audience=os.environ.get(f"{prefix}AUDIENCE", ""),
            issuer=os.environ.get(f"{prefix}ISSUER", ""),
            allowed_subjects=frozenset(s.strip() for s in subjects.split(",") if s.strip()),
            jwks_file=Path(jwks) if jwks else None,
            test_bypass=os.environ.get(f"{prefix}TEST_BYPASS", "") == "1",
        )

    def problems(self) -> list[str]:
        missing = []
        if not self.audience:
            missing.append("audience")
        if not self.issuer:
            missing.append("issuer")
        if not self.allowed_subjects:
            missing.append("allowed_subjects")
        if self.jwks_file is None:
            missing.append("jwks_file")
        return missing


class TokenVerifier:
    """Verify RS256 ServiceAccount tokens against a JWKS file that may be updated in place."""

    def __init__(self, config: AuthConfig) -> None:
        self.config = config
        self._lock = threading.Lock()
        self._keys: dict[str | None, Any] = {}
        self._mtime: float | None = None
        if config.test_bypass:
            log.warning("authentication TEST BYPASS is enabled; use only on loopback")
        elif config.problems():
            log.error("authentication not configured (missing %s): rejecting all requests",
                      ", ".join(config.problems()))

    def _load_keys(self) -> dict[str | None, Any]:
        import jwt

        assert self.config.jwks_file is not None
        mtime = self.config.jwks_file.stat().st_mtime
        with self._lock:
            if self._mtime != mtime:
                document = json.loads(self.config.jwks_file.read_text())
                jwk_set = jwt.PyJWKSet.from_dict(document)
                self._keys = {k.key_id: k.key for k in jwk_set.keys}
                self._mtime = mtime
            return self._keys

    def verify(self, authorization: str | None) -> str:
        """Return the caller's subject or raise AuthError (401 unauthenticated, 403 forbidden)."""
        if self.config.test_bypass:
            return "test-bypass"
        if self.config.problems():
            raise AuthError(401, "authentication is not configured on this service")
        if not authorization or not authorization.startswith("Bearer "):
            raise AuthError(401, "missing bearer token")
        token = authorization[len("Bearer ") :].strip()

        import jwt

        try:
            keys = self._load_keys()
        except (OSError, ValueError, jwt.PyJWTError) as exc:
            log.error("cannot load JWKS from %s: %s", self.config.jwks_file, exc)
            raise AuthError(401, "token verification keys unavailable") from exc
        try:
            kid = jwt.get_unverified_header(token).get("kid")
            key = keys.get(kid) if kid in keys else (next(iter(keys.values())) if len(keys) == 1 else None)
            if key is None:
                raise AuthError(401, "unknown signing key")
            claims = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                audience=self.config.audience,
                issuer=self.config.issuer,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
                leeway=30,
            )
        except jwt.PyJWTError as exc:
            raise AuthError(401, f"invalid token: {exc}") from exc
        subject = str(claims.get("sub", ""))
        if subject not in self.config.allowed_subjects:
            raise AuthError(403, f"subject {subject!r} is not allowed")
        return subject


def read_token(path: str | os.PathLike[str] | None) -> str | None:
    """Read a projected token file. kubelet rotates it in place, so read it per request."""
    if not path:
        return None
    try:
        return Path(path).read_text().strip() or None
    except OSError:
        return None
