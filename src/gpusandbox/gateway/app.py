"""Sandbox gateway (production track).

Why a gateway: with many trainer processes (veRL reward workers, several TRL ranks), each
process has its own view of which sandbox pod is free, so they collide and retry. The
gateway is the single scheduler in front of the pools, and it owns version pinning:

  POST /v1/evaluate_batch  {runtime?, items}       one routing snapshot for the whole batch
  POST /v1/evaluate        {task_id, code, group_key}
                           every sample with the same group_key (all completions of one GRPO
                           prompt) is scored by the same sandbox version, even if the active
                           version changes while the group is in flight
  GET  /v1/routing         current routing snapshot
  GET  /healthz, /readyz   kubelet probes
  GET  /metrics            Prometheus (authenticated)

Callers authenticate with an audience-bound ServiceAccount token, verified with the
Kubernetes TokenReview API (which also rejects tokens of deleted pods). The gateway calls
sandbox pods with its own projected token (audience gpu-sandbox).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

from gpusandbox.auth import AuthError
from gpusandbox.client.pool import SandboxPool
from gpusandbox.client.routing import RoutingSnapshot, RoutingTable
from gpusandbox.harness.policy import MAX_SOURCE_BYTES

log = logging.getLogger("gpusandbox.gateway")

REQUESTS = Counter("gateway_evaluations_total", "Evaluations by verdict", ["runtime", "version", "status"])
LATENCY = Histogram(
    "gateway_evaluation_seconds", "Gateway end-to-end latency", buckets=(1, 2, 4, 8, 15, 30, 60, 120, 300)
)
RECYCLED = Counter("gateway_recycled_pods_total", "Sandbox pods deleted for recycling")


class TokenReviewVerifier:
    """Authenticate callers with the TokenReview API; authorize by ServiceAccount allowlist.

    Successful reviews are cached for a short time keyed by a hash of the token, so that a
    veRL run sending thousands of requests does not send thousands of TokenReviews.
    """

    def __init__(
        self, audience: str, allowed_subjects: frozenset[str], *, cache_ttl_s: float = 60.0
    ) -> None:
        self.audience = audience
        self.allowed = allowed_subjects
        self.cache_ttl_s = cache_ttl_s
        self._cache: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()
        self._api = None
        if not audience or not allowed_subjects:
            log.error("gateway auth not configured: rejecting all requests")

    def _client(self):
        if self._api is None:
            from kubernetes import client, config

            config.load_incluster_config()
            self._api = client.AuthenticationV1Api()
        return self._api

    def verify(self, authorization: str | None) -> str:
        if not self.audience or not self.allowed:
            raise AuthError(401, "authentication is not configured on this service")
        if not authorization or not authorization.startswith("Bearer "):
            raise AuthError(401, "missing bearer token")
        token = authorization[len("Bearer ") :].strip()
        digest = hashlib.sha256(token.encode()).hexdigest()
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(digest)
            if cached and cached[1] > now:
                return cached[0]

        from kubernetes import client

        review = client.V1TokenReview(
            spec=client.V1TokenReviewSpec(token=token, audiences=[self.audience])
        )
        status = self._client().create_token_review(review).status
        if not status.authenticated or self.audience not in (status.audiences or []):
            raise AuthError(401, "token not authenticated for this audience")
        subject = status.user.username
        if subject not in self.allowed:
            raise AuthError(403, f"subject {subject!r} is not allowed")
        with self._lock:
            self._cache[digest] = (subject, now + self.cache_ttl_s)
            if len(self._cache) > 4096:
                self._cache = {k: v for k, v in self._cache.items() if v[1] > now}
        return subject


@dataclass
class Pin:
    snapshot: RoutingSnapshot
    expires_at: float


class Recycler:
    """Delete sandbox pods that report draining, so their Deployment replaces them.

    A pod drains after SANDBOX_MAX_EVALS evaluations or after a GPU fault. Under Kata a new pod
    is a new VM, and VFIO resets the GPU when the old VM releases it.
    """

    def __init__(self, namespace: str, enabled: bool) -> None:
        self.namespace = namespace
        self.enabled = enabled
        self._pending: set[str] = set()
        self._api = None

    def _client(self):
        if self._api is None:
            from kubernetes import client, config

            config.load_incluster_config()
            self._api = client.CoreV1Api()
        return self._api

    async def maybe_recycle(self, result: dict[str, Any]) -> None:
        pod = result.get("pod")
        if not (self.enabled and result.get("draining") and pod) or pod in self._pending:
            return
        self._pending.add(pod)
        try:
            await asyncio.to_thread(
                self._client().delete_namespaced_pod, pod, self.namespace, grace_period_seconds=10
            )
            RECYCLED.inc()
            log.info("recycled sandbox pod %s", pod)
        except Exception as exc:  # The pod may already be gone; recycling is best effort.
            log.warning("could not recycle %s: %s", pod, exc)
        finally:
            self._pending.discard(pod)


class EvalItem(BaseModel):
    task_id: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=MAX_SOURCE_BYTES)
    request_id: str | None = Field(default=None, max_length=128)


class BatchRequest(BaseModel):
    runtime: str | None = Field(default=None, max_length=32)
    items: list[EvalItem] = Field(min_length=1, max_length=4096)


class GroupedRequest(EvalItem):
    group_key: str = Field(min_length=1, max_length=256)
    runtime: str | None = Field(default=None, max_length=32)


def create_app() -> FastAPI:
    env = os.environ.get
    routing = RoutingTable(env("GATEWAY_ROUTING_FILE", "/etc/gpusandbox/routing/routing.json"))
    sandbox_token_file = env("GATEWAY_SANDBOX_TOKEN_FILE", "/var/run/secrets/gpusandbox/token")
    pin_ttl_s = float(env("GATEWAY_GROUP_PIN_TTL_S", "900"))
    verifier = TokenReviewVerifier(
        env("GATEWAY_AUTH_AUDIENCE", ""),
        frozenset(s.strip() for s in env("GATEWAY_ALLOWED_SUBJECTS", "").split(",") if s.strip()),
    )
    recycler = Recycler(env("GATEWAY_SANDBOX_NAMESPACE", "sandbox"), env("GATEWAY_RECYCLE_PODS", "1") == "1")
    pools: dict[str, SandboxPool] = {}
    pins: dict[str, Pin] = {}

    app = FastAPI(title="gpu-sandbox-gateway", docs_url=None, redoc_url=None, openapi_url=None)

    def caller(authorization: str | None = Header(default=None)) -> str:
        try:
            return verifier.verify(authorization)
        except AuthError as exc:
            headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
            raise HTTPException(status_code=exc.status_code, detail=exc.detail, headers=headers)

    def pool_for(snap: RoutingSnapshot) -> SandboxPool:
        if snap.address not in pools:
            pools[snap.address] = SandboxPool(snap.address, token_file=sandbox_token_file)
        return pools[snap.address]

    async def run_one(snap: RoutingSnapshot, item: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        result = await pool_for(snap).evaluate(item)
        LATENCY.observe(time.monotonic() - started)
        REQUESTS.labels(snap.runtime, snap.version, str(result.get("status"))).inc()
        result.setdefault("sandbox_version", snap.version)
        result.setdefault("runtime", snap.runtime)
        result["routing_revision"] = snap.revision
        asyncio.create_task(recycler.maybe_recycle(result))
        return result

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/readyz")
    async def readyz() -> dict[str, str]:
        try:
            routing.snapshot()
        except Exception:
            raise HTTPException(status_code=503, detail="routing table unavailable")
        return {"status": "ready"}

    @app.get("/metrics")
    async def metrics(_: str = Depends(caller)) -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/v1/routing")
    async def current_routing(_: str = Depends(caller)) -> dict[str, Any]:
        snap = routing.snapshot()
        return {"runtime": snap.runtime, "version": snap.version, "revision": snap.revision}

    @app.post("/v1/evaluate_batch")
    async def evaluate_batch(req: BatchRequest, _: str = Depends(caller)) -> dict[str, Any]:
        snap = routing.snapshot(req.runtime)
        results = await asyncio.gather(*(run_one(snap, i.model_dump()) for i in req.items))
        return {
            "runtime": snap.runtime,
            "version": snap.version,
            "revision": snap.revision,
            "results": list(results),
        }

    @app.post("/v1/evaluate")
    async def evaluate(req: GroupedRequest, _: str = Depends(caller)) -> dict[str, Any]:
        now = time.monotonic()
        pin = pins.get(req.group_key)
        if pin is None or pin.expires_at < now:
            pin = Pin(routing.snapshot(req.runtime), now + pin_ttl_s)
            pins[req.group_key] = pin
            if len(pins) > 100_000:
                for key in [k for k, v in pins.items() if v.expires_at < now]:
                    del pins[key]
        item = req.model_dump(exclude={"group_key", "runtime"})
        return await run_one(pin.snapshot, item)

    return app


def main() -> None:
    import uvicorn

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    uvicorn.run(
        create_app(),
        # Loopback by default; the Deployment sets 0.0.0.0 behind a ClusterIP Service and a
        # NetworkPolicy that admits the trainer namespace only.
        host=os.environ.get("GATEWAY_HOST", "127.0.0.1"),
        port=int(os.environ.get("GATEWAY_PORT", "8080")),
        workers=1,
        access_log=False,
    )


if __name__ == "__main__":
    main()
