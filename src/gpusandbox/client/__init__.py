"""Trainer-side client: version-pinned, concurrent evaluation against sandbox pools."""

from __future__ import annotations

import asyncio
import os
import threading
from collections.abc import Coroutine, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

import httpx

from gpusandbox.auth import read_token
from gpusandbox.client.pool import SandboxPool
from gpusandbox.client.routing import RoutingSnapshot, RoutingTable

T = TypeVar("T")

__all__ = [
    "BackgroundLoop",
    "BatchInfo",
    "RoutingSnapshot",
    "RoutingTable",
    "SandboxClient",
    "SandboxPool",
]


class BackgroundLoop:
    """An event loop on a daemon thread, so synchronous trainers can await async I/O.

    TRL and veRL call reward functions synchronously, sometimes from inside a running loop
    (notebooks), where asyncio.run() would fail.
    """

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def run(self, coro: Coroutine[Any, Any, T], timeout: float | None = None) -> T:
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)


@dataclass(frozen=True)
class BatchInfo:
    """Which pool scored a batch. Logged next to the rewards."""

    runtime: str
    version: str
    revision: int


class SandboxClient:
    """Pins one sandbox version per batch and fans requests out.

    Two modes:
      * direct (hands-on): read the routing table and talk to sandbox pods through their
        headless Service.
      * gateway (production): send the batch to the sandbox gateway, which owns routing,
        schedules across all trainer processes and pins versions per batch or per group.
    """

    def __init__(
        self,
        routing: RoutingTable | None = None,
        *,
        gateway: str | None = None,
        token_file: str | None = None,
        request_timeout_s: float = 300.0,
    ) -> None:
        if (routing is None) == (gateway is None):
            raise ValueError("pass exactly one of routing or gateway")
        self.routing = routing
        self.gateway = gateway
        self.token_file = token_file or os.environ.get("SANDBOX_TOKEN_FILE")
        self.request_timeout_s = request_timeout_s
        self._pools: dict[str, SandboxPool] = {}
        self._http: httpx.AsyncClient | None = None
        self._bg: BackgroundLoop | None = None

    @classmethod
    def from_env(cls) -> SandboxClient:
        gateway = os.environ.get("SANDBOX_GATEWAY")
        if gateway:
            return cls(gateway=gateway)
        return cls(RoutingTable.from_env())

    def _headers(self) -> dict[str, str]:
        token = read_token(self.token_file)
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _pool(self, address: str) -> SandboxPool:
        if address not in self._pools:
            self._pools[address] = SandboxPool(
                address, token_file=self.token_file, request_timeout_s=self.request_timeout_s
            )
        return self._pools[address]

    async def _gateway_batch(
        self, items: Sequence[dict[str, Any]], runtime: str | None
    ) -> tuple[BatchInfo, list[dict[str, Any]]]:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=self.request_timeout_s * 4)
        payload = {"runtime": runtime, "items": list(items)}
        try:
            resp = await self._http.post(
                f"http://{self.gateway}/v1/evaluate_batch", json=payload, headers=self._headers()
            )
            resp.raise_for_status()
            body = resp.json()
            info = BatchInfo(body["runtime"], body["version"], int(body["revision"]))
            results = list(body["results"])
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            info = BatchInfo(runtime or "unknown", "unknown", -1)
            return info, [{"status": "sandbox_error", "error": f"gateway: {exc}"} for _ in items]
        if len(results) != len(items):
            return info, [{"status": "sandbox_error", "error": "gateway result count mismatch"} for _ in items]
        return info, results

    async def evaluate_batch(
        self, items: Sequence[dict[str, Any]], *, runtime: str | None = None
    ) -> tuple[BatchInfo, list[dict[str, Any]]]:
        if self.gateway is not None:
            return await self._gateway_batch(items, runtime)
        assert self.routing is not None
        snap = self.routing.snapshot(runtime)
        pool = self._pool(snap.address)
        results = list(await asyncio.gather(*(pool.evaluate(dict(i)) for i in items)))
        for result in results:
            # Record what the trainer asked for next to what actually answered.
            result.setdefault("sandbox_version", snap.version)
            result.setdefault("runtime", snap.runtime)
            result["routing_revision"] = snap.revision
        return BatchInfo(snap.runtime, snap.version, snap.revision), results

    def evaluate_batch_sync(
        self, items: Sequence[dict[str, Any]], *, runtime: str | None = None
    ) -> tuple[BatchInfo, list[dict[str, Any]]]:
        if self._bg is None:
            self._bg = BackgroundLoop()
        return self._bg.run(self.evaluate_batch(items, runtime=runtime))

    async def evaluate_grouped(self, item: dict[str, Any], *, group_key: str) -> dict[str, Any]:
        """Score one sample; the gateway keeps every sample of ``group_key`` on one version.

        Used by trainers that score samples one at a time (veRL), where a batch-level
        snapshot is not available.
        """
        if self.gateway is None:
            raise RuntimeError("per-sample group pinning needs the gateway (SANDBOX_GATEWAY)")
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=self.request_timeout_s)
        try:
            resp = await self._http.post(
                f"http://{self.gateway}/v1/evaluate",
                json={**item, "group_key": group_key},
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            return {"status": "sandbox_error", "error": f"gateway: {exc}"}
