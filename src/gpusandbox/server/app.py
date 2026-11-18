"""Sandbox HTTP server.

Endpoints
  POST /v1/evaluate   [auth] run one candidate against one task, return the harness verdict
  GET  /info          [auth] sandbox version, runtime, kernel and GPU identity
  GET  /metrics       [auth] Prometheus metrics
  GET  /healthz       liveness for kubelet: fails only when the pod must be restarted
  GET  /readyz        readiness for kubelet: GPU probe passed, egress verified blocked,
                      and the pod is not draining

[auth] routes require an audience-bound ServiceAccount token (see gpusandbox.auth). The
probe routes return no sandbox details because kubelet probes cannot carry a token.

The server never imports torch. Each evaluation runs in a fresh process tree
(evaluate.py -> runner.py) that is killed and reaped afterwards.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import shutil
import signal
import sys
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field

from gpusandbox.auth import AuthConfig, AuthError, TokenVerifier
from gpusandbox.harness import HARNESS_VERSION
from gpusandbox.harness.policy import MAX_SOURCE_BYTES
from gpusandbox.server.procs import reap_strays

log = logging.getLogger("gpusandbox.server")


def _env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    version: str = "dev"
    runtime: str = "unknown"
    device: str = "cuda"
    size: str = "full"
    work_root: Path = Path("/work")
    eval_timeout_s: float = 90.0
    seeds: int = 3
    warmup: int = 3
    iters: int = 20
    max_speedup: float = 0.0
    allow_cuda_cpp: bool = False
    # 0 = unlimited. Otherwise the pod reports not-ready after N evaluations so that it can be
    # replaced with a fresh sandbox (a fresh VM under Kata).
    max_evals: int = 0
    pod_name: str = ""
    node_name: str = ""
    # Readiness requires these host:port targets to be unreachable (see _egress_open).
    # Empty disables the self-test, which is only acceptable for local smoke tests.
    egress_probe_targets: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> Settings:
        env = os.environ.get
        return cls(
            version=env("SANDBOX_VERSION", "dev"),
            runtime=env("SANDBOX_RUNTIME", "unknown"),
            device=env("SANDBOX_DEVICE", "cuda"),
            size=env("SANDBOX_SIZE", "full"),
            work_root=Path(env("SANDBOX_WORK_ROOT", "/work")),
            eval_timeout_s=float(env("SANDBOX_EVAL_TIMEOUT_S", "90")),
            seeds=int(env("HARNESS_SEEDS", "3")),
            warmup=int(env("HARNESS_WARMUP", "3")),
            iters=int(env("HARNESS_ITERS", "20")),
            max_speedup=float(env("HARNESS_MAX_SPEEDUP", "0")),
            allow_cuda_cpp=_env_bool("HARNESS_ALLOW_CUDA_CPP", False),
            max_evals=int(env("SANDBOX_MAX_EVALS", "0")),
            pod_name=env("POD_NAME", platform.node()),
            node_name=env("NODE_NAME", ""),
            egress_probe_targets=tuple(
                t.strip() for t in env("SANDBOX_EGRESS_PROBE_TARGETS", "").split(",") if t.strip()
            ),
        )


EVALS = Counter("sandbox_evaluations_total", "Evaluations by verdict", ["status"])
EVAL_SECONDS = Histogram(
    "sandbox_evaluation_seconds",
    "End-to-end evaluation latency",
    buckets=(0.5, 1, 2, 4, 8, 15, 30, 60, 120),
)
BUSY = Gauge("sandbox_busy", "1 while an evaluation is running")
READY = Gauge("sandbox_ready", "1 when the sandbox accepts work")
REAPED = Counter("sandbox_reaped_processes_total", "Stray processes killed after evaluations")


@dataclass
class State:
    settings: Settings
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    evals_done: int = 0
    gpu_ok: bool = False
    gpu_info: dict[str, Any] = field(default_factory=dict)
    draining: bool = False
    fatal: str = ""
    egress_blocked: bool = False
    egress_detail: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.gpu_ok and self.egress_blocked and not self.draining and not self.fatal


async def _probe_device(settings: Settings) -> tuple[bool, dict[str, Any]]:
    """Check that the accelerator is usable from a fresh process (as evaluations will be)."""
    script = (
        "import json, torch\n"
        "info = {'torch': torch.__version__, 'cuda_runtime': torch.version.cuda}\n"
        "if torch.cuda.is_available():\n"
        "    p = torch.cuda.get_device_properties(0)\n"
        "    info.update(name=p.name, capability=f'{p.major}.{p.minor}',\n"
        "                memory_gib=round(p.total_memory / 2**30, 1),\n"
        "                device_count=torch.cuda.device_count())\n"
        "    torch.ones(1, device='cuda').add_(1)\n"
        "    torch.cuda.synchronize()\n"
        "print(json.dumps(info))\n"
    )
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-I",
        "-c",
        script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        proc.kill()
        return False, {"error": "device probe timed out"}
    if proc.returncode != 0:
        return False, {"error": stderr.decode(errors="replace")[-2000:]}
    info = json.loads(stdout.decode().strip().splitlines()[-1])
    if settings.device == "cuda" and "name" not in info:
        return False, {**info, "error": "torch.cuda.is_available() is False"}
    return True, info


async def _egress_open(targets: tuple[str, ...], timeout_s: float = 2.0) -> list[str]:
    """Return the targets this pod can reach. Verify denial, do not assume it.

    A completed handshake or a refused connection both prove that packets reach the target,
    so both count as open. Only a timeout or an unreachable route counts as blocked. The
    NetworkPolicy is applied asynchronously after pod start, and the VPC CNI always allows
    traffic to the pod's own node, so this check catches both a missing policy and a missing
    node-level guard before any candidate code runs.
    """
    open_targets = []
    for target in targets:
        if target == "apiserver":
            # kubelet always injects the API server's service address, even with
            # enableServiceLinks: false.
            host = os.environ.get("KUBERNETES_SERVICE_HOST")
            port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
            if not host:
                continue
            target = f"{host}:{port}"
        else:
            host, _, port = target.rpartition(":")
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(host, int(port)), timeout_s)
            writer.close()
            open_targets.append(f"{target} (connected)")
        except ConnectionRefusedError:
            open_targets.append(f"{target} (refused: reachable)")
        except (asyncio.TimeoutError, OSError):
            continue
    return open_targets


async def _egress_watch(state: State, interval_s: float = 30.0) -> None:
    targets = state.settings.egress_probe_targets
    while True:
        if targets:
            reachable = await _egress_open(targets)
            state.egress_blocked = not reachable
            state.egress_detail = reachable
            if reachable:
                log.error("egress is open, refusing work: %s", ", ".join(reachable))
        else:
            state.egress_blocked = True
        READY.set(1 if state.ready else 0)
        await asyncio.sleep(interval_s if state.egress_blocked else 5.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    settings.work_root.mkdir(parents=True, exist_ok=True)
    state: State = app.state.sandbox
    if not settings.egress_probe_targets:
        log.warning("egress self-test disabled (SANDBOX_EGRESS_PROBE_TARGETS is empty)")
    watcher = asyncio.create_task(_egress_watch(state))
    state.gpu_ok, state.gpu_info = await _probe_device(settings)
    READY.set(1 if state.ready else 0)
    log.info("device probe ok=%s info=%s", state.gpu_ok, state.gpu_info)
    try:
        yield
    finally:
        watcher.cancel()


class EvaluateRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=MAX_SOURCE_BYTES)
    request_id: str | None = Field(default=None, max_length=128)


def create_app(settings: Settings | None = None, auth: AuthConfig | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    verifier = TokenVerifier(auth or AuthConfig.from_env("SANDBOX_AUTH_"))
    app = FastAPI(
        title="gpu-sandbox",
        version=HARNESS_VERSION,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = settings
    app.state.sandbox = State(settings=settings)

    def caller(authorization: str | None = Header(default=None)) -> str:
        try:
            return verifier.verify(authorization)
        except AuthError as exc:
            headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
            raise HTTPException(status_code=exc.status_code, detail=exc.detail, headers=headers)

    def meta() -> dict[str, Any]:
        return {
            "sandbox_version": settings.version,
            "runtime": settings.runtime,
            "harness_version": HARNESS_VERSION,
            "pod": settings.pod_name,
            "node": settings.node_name,
        }

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        state: State = app.state.sandbox
        if state.fatal:
            raise HTTPException(status_code=500, detail=state.fatal)
        return {"status": "alive"}

    @app.get("/readyz")
    async def readyz() -> dict[str, str]:
        state: State = app.state.sandbox
        if not state.ready:
            raise HTTPException(status_code=503, detail="not ready")
        return {"status": "ready"}

    @app.get("/info")
    async def info(_: str = Depends(caller)) -> dict[str, Any]:
        state: State = app.state.sandbox
        uname = platform.uname()
        return {
            **meta(),
            # Inside gVisor this is the Sentry's synthetic kernel version, inside Kata it is
            # the guest kernel. Comparing it with the node's kernel shows the isolation layer.
            "kernel_release": uname.release,
            "kernel_version": uname.version,
            "device": state.gpu_info,
            "evals_done": state.evals_done,
            "draining": state.draining,
            "egress_blocked": state.egress_blocked,
            "egress_open_targets": state.egress_detail,
        }

    @app.get("/metrics")
    async def metrics(_: str = Depends(caller)) -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/v1/evaluate")
    async def evaluate(req: EvaluateRequest, _: str = Depends(caller)) -> dict[str, Any]:
        state: State = app.state.sandbox
        if not state.ready:
            raise HTTPException(status_code=503, detail="not ready")
        if state.lock.locked():
            # One GPU, one evaluation. The client retries on another pod.
            raise HTTPException(status_code=503, detail="busy")
        async with state.lock:
            BUSY.set(1)
            started = time.monotonic()
            try:
                verdict = await _run_harness(settings, req)
            finally:
                REAPED.inc(reap_strays())
                BUSY.set(0)
            elapsed = time.monotonic() - started
            status = str(verdict.get("status", "sandbox_error"))
            EVALS.labels(status=status).inc()
            EVAL_SECONDS.observe(elapsed)
            state.evals_done += 1
            if "gpu_fault" in verdict.get("flags", []):
                # The reference path failed on CUDA: the device is suspect. Stop taking work and
                # let the liveness probe restart the container.
                state.fatal = "gpu fault during reference evaluation"
                state.draining = True
            elif settings.max_evals and state.evals_done >= settings.max_evals:
                state.draining = True
            READY.set(1 if state.ready else 0)
            return {
                **verdict,
                **meta(),
                "request_id": req.request_id,
                "duration_s": round(elapsed, 4),
                "draining": state.draining,
            }

    return app


async def _run_harness(settings: Settings, req: EvaluateRequest) -> dict[str, Any]:
    workdir = settings.work_root / f"req-{uuid.uuid4().hex}"
    workdir.mkdir(mode=0o700)
    try:
        code_path = workdir / "candidate.py"
        code_path.write_text(req.code, encoding="utf-8")
        out_path = workdir / "result.json"
        cmd = [
            sys.executable,
            "-I",
            "-m",
            "gpusandbox.harness.evaluate",
            "--task", req.task_id,
            "--code", str(code_path),
            "--workdir", str(workdir),
            "--out", str(out_path),
            "--device", settings.device,
            "--size", settings.size,
            "--seeds", str(settings.seeds),
            "--warmup", str(settings.warmup),
            "--iters", str(settings.iters),
            "--timeout", str(settings.eval_timeout_s),
            "--max-speedup", str(settings.max_speedup),
        ]  # fmt: skip
        if settings.allow_cuda_cpp:
            cmd.append("--allow-cuda-cpp")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        try:
            # The parent enforces the candidate timeout; this outer bound covers the reference.
            _, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=settings.eval_timeout_s * 2 + 30
            )
        except asyncio.TimeoutError:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await proc.wait()
            return {"status": "sandbox_error", "error": "harness exceeded outer timeout"}
        if not out_path.exists():
            return {
                "status": "sandbox_error",
                "error": f"harness exited {proc.returncode}: "
                + stderr.decode(errors="replace")[-2000:],
            }
        return json.loads(out_path.read_text())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> None:
    import uvicorn

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    uvicorn.run(
        create_app(),
        # Loopback by default. The pod manifest sets SANDBOX_HOST=0.0.0.0 so that the pod IP is
        # reachable inside the cluster; the Service is ClusterIP-only and a NetworkPolicy
        # admits the trainer namespace only.
        host=os.environ.get("SANDBOX_HOST", "127.0.0.1"),
        port=int(os.environ.get("SANDBOX_PORT", "8000")),
        workers=1,
        access_log=False,
    )


if __name__ == "__main__":
    main()
