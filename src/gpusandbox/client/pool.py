"""Client-side scheduling over a pool of single-GPU sandbox pods.

Each pod runs one evaluation at a time, so the pool hands out one in-flight request per
endpoint and retries on another pod when a pod is busy, draining or unreachable.
"""

from __future__ import annotations

import asyncio
import logging
import socket
import time
from typing import Any

import httpx

from gpusandbox.auth import read_token

log = logging.getLogger(__name__)


class EndpointResolver:
    """Resolve ``host:port`` of a headless Service to the IPs of its ready pods.

    A headless Service publishes one DNS A record per ready pod, so readiness gating (the
    pod's /readyz) is enforced by Kubernetes before an IP ever reaches the client. A comma
    separated list of ``host:port`` entries is used verbatim (local tests).
    """

    def __init__(self, address: str, *, refresh_s: float = 10.0) -> None:
        self.address = address
        self.refresh_s = refresh_s
        self._cached: list[str] = []
        self._resolved_at = 0.0

    async def endpoints(self) -> list[str]:
        if "," in self.address or self.address.startswith("static:"):
            items = self.address.removeprefix("static:").split(",")
            return [i.strip() for i in items if i.strip()]
        now = time.monotonic()
        if self._cached and now - self._resolved_at < self.refresh_s:
            return self._cached
        host, _, port = self.address.rpartition(":")
        if not host:
            raise ValueError(f"address must be host:port, got {self.address!r}")
        loop = asyncio.get_running_loop()
        try:
            infos = await loop.getaddrinfo(host, int(port), type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            log.warning("cannot resolve %s: %s", host, exc)
            return self._cached
        ips = sorted({info[4][0] for info in infos})
        self._cached = [f"[{ip}]:{port}" if ":" in ip else f"{ip}:{port}" for ip in ips]
        self._resolved_at = now
        return self._cached


class PoolExhausted(RuntimeError):
    pass


class SandboxPool:
    def __init__(
        self,
        address: str,
        *,
        token_file: str | None = None,
        per_endpoint_concurrency: int = 1,
        request_timeout_s: float = 300.0,
        acquire_timeout_s: float = 600.0,
        max_attempts: int = 4,
        cooldown_s: float = 5.0,
    ) -> None:
        self.resolver = EndpointResolver(address)
        self.token_file = token_file
        self.limit = per_endpoint_concurrency
        self.request_timeout_s = request_timeout_s
        self.acquire_timeout_s = acquire_timeout_s
        self.max_attempts = max_attempts
        self.cooldown_s = cooldown_s
        self._inflight: dict[str, int] = {}
        self._cooldown_until: dict[str, float] = {}
        self._last_used: dict[str, float] = {}
        self._cond: asyncio.Condition | None = None
        self._client: httpx.AsyncClient | None = None

    def _ensure_loop_objects(self) -> None:
        # Created lazily so that they bind to the event loop that actually runs the requests.
        if self._cond is None:
            self._cond = asyncio.Condition()
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.request_timeout_s)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _acquire(self) -> str:
        self._ensure_loop_objects()
        assert self._cond is not None
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.acquire_timeout_s
        async with self._cond:
            while True:
                endpoints = await self.resolver.endpoints()
                now = time.monotonic()
                free = [
                    ep
                    for ep in endpoints
                    if self._inflight.get(ep, 0) < self.limit
                    and self._cooldown_until.get(ep, 0.0) <= now
                ]
                if free:
                    ep = min(free, key=lambda e: (self._inflight.get(e, 0), self._last_used.get(e, 0.0)))
                    self._inflight[ep] = self._inflight.get(ep, 0) + 1
                    self._last_used[ep] = now
                    return ep
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise PoolExhausted(f"no free sandbox in {self.resolver.address}")
                try:
                    # Wake up on release, or periodically to pick up new pods and expired cooldowns.
                    await asyncio.wait_for(self._cond.wait(), timeout=min(remaining, 1.0))
                except asyncio.TimeoutError:
                    pass

    async def _release(self, endpoint: str, *, cooldown: bool) -> None:
        assert self._cond is not None
        async with self._cond:
            self._inflight[endpoint] = max(0, self._inflight.get(endpoint, 1) - 1)
            if cooldown:
                self._cooldown_until[endpoint] = time.monotonic() + self.cooldown_s
            self._cond.notify_all()

    async def evaluate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Evaluate one request. Infrastructure failures come back as status=sandbox_error."""
        last_error = ""
        for attempt in range(1, self.max_attempts + 1):
            try:
                endpoint = await self._acquire()
            except PoolExhausted as exc:
                return {"status": "sandbox_error", "error": str(exc)}
            cooldown = False
            try:
                assert self._client is not None
                headers = {}
                token = read_token(self.token_file)
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                resp = await self._client.post(
                    f"http://{endpoint}/v1/evaluate", json=request, headers=headers
                )
                if resp.status_code == 503:
                    cooldown = True  # busy or draining: try another pod
                    last_error = f"{endpoint} busy/draining"
                    continue
                if 400 <= resp.status_code < 500:
                    # Credential or request problems do not fix themselves on another pod.
                    return {
                        "status": "sandbox_error",
                        "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                    }
                resp.raise_for_status()
                result = resp.json()
                result["endpoint"] = endpoint
                result["attempts"] = attempt
                return result
            except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as exc:
                cooldown = True
                last_error = f"{endpoint}: {type(exc).__name__}: {exc}"
                log.warning("sandbox request failed (attempt %d): %s", attempt, last_error)
            finally:
                await self._release(endpoint, cooldown=cooldown)
        return {"status": "sandbox_error", "error": last_error or "exhausted retries"}
