"""Per-episode sandboxes through kubernetes-sigs/agent-sandbox (v1beta1 SandboxClaim).

For multi-turn agentic RL an episode may submit many kernels and read the feedback between
turns. Claiming a dedicated, pre-warmed sandbox per episode keeps those turns on one GPU and
one sandbox version, and releasing the claim returns the sandbox (and, under Kata, the VM and
its GPU) for replacement.

    with EpisodeSandbox(warm_pool="kernel-eval-gvisor") as episode:
        verdict = episode.evaluate(task_id="relu_bias", code=code)

Field names follow agent-sandbox v1.0.11 (extensions/api/v1beta1/sandboxclaim_types.go):
spec.warmPoolRef.name, spec.lifecycle.shutdownTime/shutdownPolicy, status.conditions,
status.sandbox.{name, podIPs, serviceFQDN}. Re-verify when upgrading the controller.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from gpusandbox.auth import read_token
from gpusandbox.client import BackgroundLoop
from gpusandbox.client.pool import SandboxPool

GROUP = "extensions.agents.x-k8s.io"
VERSION = "v1beta1"
PLURAL = "sandboxclaims"
SANDBOX_PORT = 8000


def claim_body(name: str, warm_pool: str, *, max_lifetime_s: int, episode_labels: dict[str, str]) -> dict[str, Any]:
    """A SandboxClaim that adopts one warm sandbox and deletes itself if the trainer dies."""
    shutdown = datetime.now(timezone.utc) + timedelta(seconds=max_lifetime_s)
    return {
        "apiVersion": f"{GROUP}/{VERSION}",
        "kind": "SandboxClaim",
        "metadata": {"name": name, "labels": {"gpusandbox/episode": "true", **episode_labels}},
        "spec": {
            "warmPoolRef": {"name": warm_pool},
            # Safety net: a crashed trainer must not hold a GPU sandbox forever.
            "lifecycle": {
                "shutdownTime": shutdown.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "shutdownPolicy": "Delete",
            },
        },
    }


def sandbox_address(claim: dict[str, Any]) -> str | None:
    """host:port of the claimed sandbox, or None until the claim is Ready."""
    status = claim.get("status") or {}
    ready = any(
        c.get("type") == "Ready" and c.get("status") == "True" for c in status.get("conditions", [])
    )
    if not ready:
        return None
    sandbox = status.get("sandbox") or {}
    if sandbox.get("serviceFQDN"):
        return f"{sandbox['serviceFQDN']}:{SANDBOX_PORT}"
    ips = sandbox.get("podIPs") or []
    return f"{ips[0]}:{SANDBOX_PORT}" if ips else None


class EpisodeSandbox:
    """Claim a warm sandbox for one episode; evaluate through it; release it on exit."""

    def __init__(
        self,
        warm_pool: str,
        *,
        namespace: str = "sandbox",
        token_file: str | None = None,
        max_lifetime_s: int = 3600,
        ready_timeout_s: float = 600.0,
        labels: dict[str, str] | None = None,
        api: Any = None,
        loop: BackgroundLoop | None = None,
    ) -> None:
        self.warm_pool = warm_pool
        self.namespace = namespace
        self.token_file = token_file
        self.max_lifetime_s = max_lifetime_s
        self.ready_timeout_s = ready_timeout_s
        self.labels = labels or {}
        self.name = f"episode-{uuid.uuid4().hex[:12]}"
        self.address: str | None = None
        self.sandbox_name: str | None = None
        self._api = api
        self._pool: SandboxPool | None = None
        # A process that runs many episodes passes one shared loop; BackgroundLoop threads are
        # never stopped, so one loop per episode would leak a thread per episode.
        self._shared_loop = loop
        self._bg: BackgroundLoop | None = None

    def _client(self) -> Any:
        if self._api is None:
            from kubernetes import client, config

            config.load_incluster_config()
            self._api = client.CustomObjectsApi()
        return self._api

    def __enter__(self) -> EpisodeSandbox:
        api = self._client()
        api.create_namespaced_custom_object(
            GROUP, VERSION, self.namespace, PLURAL,
            claim_body(self.name, self.warm_pool, max_lifetime_s=self.max_lifetime_s,
                       episode_labels=self.labels),
        )
        try:
            deadline = time.monotonic() + self.ready_timeout_s
            while time.monotonic() < deadline:
                claim = api.get_namespaced_custom_object(GROUP, VERSION, self.namespace, PLURAL, self.name)
                self.address = sandbox_address(claim)
                if self.address:
                    self.sandbox_name = ((claim.get("status") or {}).get("sandbox") or {}).get("name")
                    break
                time.sleep(1.0)
            if not self.address:
                raise TimeoutError(f"claim {self.name} on {self.warm_pool} not Ready in {self.ready_timeout_s}s")
        except BaseException:
            # __exit__ does not run when __enter__ fails: an API error or an interrupt while
            # waiting must not leave the claim holding a GPU sandbox until shutdownTime.
            self.release()
            raise
        self._pool = SandboxPool(f"static:{self.address}", token_file=self.token_file)
        self._bg = self._shared_loop or BackgroundLoop()
        return self

    def info(self) -> dict[str, Any]:
        """GET /info of the claimed sandbox: runtime, version, kernel and GPU it reports."""
        if self.address is None:
            raise RuntimeError("use EpisodeSandbox as a context manager")
        token = read_token(self.token_file)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = httpx.get(f"http://{self.address}/info", headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def evaluate(self, *, task_id: str, code: str) -> dict[str, Any]:
        if self._pool is None or self._bg is None:
            raise RuntimeError("use EpisodeSandbox as a context manager")
        result = self._bg.run(self._pool.evaluate({"task_id": task_id, "code": code}))
        result["episode_claim"] = self.name
        return result

    def release(self) -> None:
        if self._pool is not None and self._bg is not None:
            self._bg.run(self._pool.aclose())
            self._pool = None
        from kubernetes.client.exceptions import ApiException

        try:
            self._client().delete_namespaced_custom_object(GROUP, VERSION, self.namespace, PLURAL, self.name)
        except ApiException as exc:
            if exc.status != 404:
                raise

    def __exit__(self, *exc: Any) -> None:
        self.release()
