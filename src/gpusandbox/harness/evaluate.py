"""Trusted parent for one evaluation: policy check, candidate child, reference, verdict.

Invoked by the sandbox server as ``python -I -m gpusandbox.harness.evaluate ...`` and writes a
single JSON verdict to ``--out``. The server never imports torch, so a CUDA fault can only take
down this short-lived process tree, not the server.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import secrets
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from gpusandbox.harness import HARNESS_VERSION
from gpusandbox.harness.policy import check_source

STAGE_TO_STATUS = {
    "init": "sandbox_error",
    "load": "compile_error",
    "run": "runtime_error",
    "timing": "runtime_error",
}
MAX_RUNNER_JSON_BYTES = 1 << 20

# Environment passed to the untrusted child. Everything else (pod env, proxies, tokens) is dropped.
CHILD_ENV_ALLOWLIST = (
    "PATH",
    "LD_LIBRARY_PATH",
    "CUDA_VISIBLE_DEVICES",
    "NVIDIA_VISIBLE_DEVICES",
    "NVIDIA_DRIVER_CAPABILITIES",
    "LANG",
    "LC_ALL",
    "CC",
)


def _tail(text: str | bytes | None, limit: int = 2000) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    return text[-limit:]


def _child_env(workdir: Path) -> dict[str, str]:
    env = {k: os.environ[k] for k in CHILD_ENV_ALLOWLIST if k in os.environ}
    # Per-request caches: a candidate must not poison Triton or CUDA caches used by later
    # evaluations in the same pod.
    for key, sub in (
        ("HOME", "home"),
        ("TMPDIR", "tmp"),
        ("TRITON_CACHE_DIR", "triton"),
        ("CUDA_CACHE_PATH", "nv"),
    ):
        path = workdir / sub
        path.mkdir(mode=0o700, exist_ok=True)
        env[key] = str(path)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    return env


def _read_runner_json(path: Path) -> dict[str, Any] | None:
    # Written by the untrusted process: size-limit and type-check before use.
    if not path.exists() or path.stat().st_size > MAX_RUNNER_JSON_BYTES:
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _valid_samples(samples: Any, expected: int) -> list[float] | None:
    if not isinstance(samples, list) or len(samples) != expected:
        return None
    out: list[float] = []
    for value in samples:
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            return None
        out.append(float(value))
    return out


def _valid_checksums(sums: Any, expected: int) -> list[tuple[float, float]] | None:
    if not isinstance(sums, list) or len(sums) != expected:
        return None
    out: list[tuple[float, float]] = []
    for pair in sums:
        if not (isinstance(pair, list) and len(pair) == 2):
            return None
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in pair):
            return None
        out.append((float(pair[0]), float(pair[1])))
    return out


def _compare(ref: Any, cand: Any, atol: float, rtol: float) -> tuple[bool, float | None, str]:
    import torch

    refs = ref if isinstance(ref, (list, tuple)) else [ref]
    cands = cand if isinstance(cand, (list, tuple)) else [cand]
    if len(refs) != len(cands):
        return False, None, f"expected {len(refs)} outputs, got {len(cands)}"
    worst = 0.0
    for r, c in zip(refs, cands):
        if not isinstance(c, torch.Tensor):
            return False, None, "output is not a tensor"
        if c.shape != r.shape:
            return False, None, f"shape mismatch: expected {tuple(r.shape)}, got {tuple(c.shape)}"
        if c.dtype != r.dtype:
            return False, None, f"dtype mismatch: expected {r.dtype}, got {c.dtype}"
        if not torch.isfinite(c).all() and torch.isfinite(r).all():
            return False, None, "output contains NaN or Inf"
        diff = (c.double() - r.double()).abs()
        worst = max(worst, float(diff.max()) if diff.numel() else 0.0)
        if not torch.allclose(c, r, atol=atol, rtol=rtol):
            return False, worst, "values differ beyond tolerance"
    return True, worst, ""


def run_child(cmd: list[str], *, env: dict[str, str], cwd: Path, timeout_s: float):
    """Run the child in its own session so that a timeout kills every process it spawned."""
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
        return proc.returncode, stdout, stderr, False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr, True


def evaluate(
    *,
    task_id: str,
    code_path: Path,
    workdir: Path,
    device: str,
    size: str,
    n_seeds: int,
    warmup: int,
    iters: int,
    timeout_s: float,
    allow_cuda_cpp: bool,
    max_speedup: float,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "harness_version": HARNESS_VERSION,
        "task_id": task_id,
        "status": "sandbox_error",
        "correct": False,
        "custom_kernel": False,
        "uses_triton": False,
        "triton_launches": None,
        "max_abs_err": None,
        "ref_ms": None,
        "cand_ms": None,
        "speedup": None,
        "flags": [],
        "violations": [],
        "error": "",
        "stdout_tail": "",
        "stderr_tail": "",
        "timings_s": {},
    }
    t0 = time.monotonic()

    # 1) Static policy.
    report = check_source(code_path.read_text(encoding="utf-8"), allow_cuda_cpp=allow_cuda_cpp)
    result["uses_triton"] = report.uses_triton
    result["timings_s"]["policy"] = round(time.monotonic() - t0, 4)
    if not report.ok:
        result.update(status="policy_violation", violations=report.violations)
        return result

    # 2) Untrusted child. Seeds are drawn fresh per request so that outputs cannot be memorized
    #    across rollouts.
    rng = secrets.SystemRandom()
    seeds = [rng.randrange(1, 2**31) for _ in range(n_seeds)]
    timing_seed = rng.randrange(1, 2**31)
    outdir = workdir / "out"
    outdir.mkdir(mode=0o700, exist_ok=True)
    cmd = [
        sys.executable,
        "-I",
        "-m",
        "gpusandbox.harness.runner",
        "--task", task_id,
        "--code", str(code_path),
        "--outdir", str(outdir),
        "--device", device,
        "--size", size,
        "--seeds", ",".join(map(str, seeds)),
        "--timing-seed", str(timing_seed),
        "--warmup", str(warmup),
        "--iters", str(iters),
    ]  # fmt: skip
    t1 = time.monotonic()
    rc, stdout, stderr, timed_out = run_child(
        cmd, env=_child_env(workdir), cwd=workdir, timeout_s=timeout_s
    )
    result["timings_s"]["candidate"] = round(time.monotonic() - t1, 4)
    result["stdout_tail"] = _tail(stdout)
    result["stderr_tail"] = _tail(stderr)
    if timed_out:
        result.update(status="timeout", error=f"candidate exceeded {timeout_s:.0f}s")
        return result

    runner = _read_runner_json(outdir / "runner.json")
    if runner is None:
        # A crash with no status file (segfault, os._exit, CUDA abort) is the candidate's fault.
        result.update(status="runtime_error", error=f"runner exited with code {rc}, no status")
        return result
    stage = runner.get("stage")
    if stage != "done":
        result.update(status=STAGE_TO_STATUS.get(stage, "runtime_error"))
        result["error"] = _tail(str(runner.get("error", "")))
        return result

    launches = runner.get("triton_launches")
    result["triton_launches"] = launches if isinstance(launches, int) and launches >= 0 else None
    cand_samples = _valid_samples(runner.get("cand_ms"), iters)
    cand_sums = _valid_checksums(runner.get("checksums"), iters)
    if cand_samples is None or cand_sums is None:
        result.update(status="runtime_error", error="invalid timing report from runner")
        result["flags"].append("invalid_runner_report")
        return result

    # 3) Trusted reference: correctness on the same seeds, then timing on the same inputs.
    t2 = time.monotonic()
    try:
        import torch

        from gpusandbox.harness.timing import checksums_match, make_input_sets, measure_ms, median
        from gpusandbox.tasks import get_task

        spec = get_task(task_id)
        task = spec.module
        ref_model = task.Model(*task.get_init_inputs()).to(device).eval()
        worst = 0.0
        with torch.inference_mode():
            for seed in seeds:
                ref_out = ref_model(*task.get_inputs(seed, device, size))
                ref_out = ref_out.detach().to("cpu")
                cand_file = outdir / f"cand_{seed}.pt"
                if not cand_file.exists():
                    result.update(status="runtime_error", error="missing candidate output")
                    return result
                try:
                    # weights_only=True: written by untrusted code, never unpickle objects.
                    cand_out = torch.load(cand_file, map_location="cpu", weights_only=True)
                except Exception:
                    result.update(status="runtime_error", error="unreadable candidate output")
                    return result
                ok, err, reason = _compare(ref_out, cand_out, spec.atol, spec.rtol)
                if err is not None:
                    worst = max(worst, err)
                if not ok:
                    result.update(status="wrong_answer", error=reason, max_abs_err=err)
                    return result
        result["max_abs_err"] = worst

        inputs = make_input_sets(
            task.get_inputs, base_seed=timing_seed, count=warmup + iters, device=device, size=size
        )
        ref_samples, ref_sums = measure_ms(
            ref_model, inputs[:warmup], inputs[warmup:], device=device
        )
        numel = int(ref_out.numel())
        for i, (c_sum, r_sum) in enumerate(zip(cand_sums, ref_sums)):
            if not checksums_match(c_sum, r_sum, numel=numel, atol=spec.atol, rtol=spec.rtol):
                # Correct on the check inputs but not on the timed inputs: the classic
                # "be right until the benchmark starts" hack.
                result.update(status="wrong_answer", error=f"timed iteration {i} output mismatch")
                result["flags"].append("timed_output_mismatch")
                return result
    except Exception as exc:  # A failure here is an infrastructure problem, not a policy one.
        result.update(status="sandbox_error", error=_tail(traceback.format_exc()))
        if "CUDA" in str(exc) or "cuda" in type(exc).__name__.lower():
            result["flags"].append("gpu_fault")
        return result
    finally:
        result["timings_s"]["reference"] = round(time.monotonic() - t2, 4)

    ref_ms, cand_ms = median(ref_samples), median(cand_samples)
    speedup = ref_ms / cand_ms
    if max_speedup > 0 and speedup > max_speedup:
        # Memory-bound ops cannot beat ATen by this much on the same GPU; treat as a
        # measurement exploit and withhold the speed bonus.
        result["flags"].append("implausible_speedup")
        speedup = 1.0
    result.update(
        status="ok",
        correct=True,
        ref_ms=round(ref_ms, 6),
        cand_ms=round(cand_ms, 6),
        speedup=round(speedup, 4),
    )
    result["custom_kernel"] = bool(report.uses_triton) and (
        result["triton_launches"] is None or result["triton_launches"] > 0
    )
    if report.uses_triton and result["triton_launches"] == 0:
        result["flags"].append("triton_kernel_never_launched")
    result["timings_s"]["total"] = round(time.monotonic() - t0, 4)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--code", required=True, type=Path)
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--size", default="full", choices=["full", "smoke"])
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iters", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--allow-cuda-cpp", action="store_true")
    parser.add_argument("--max-speedup", type=float, default=0.0, help="0 disables the cap")
    args = parser.parse_args(argv)

    try:
        verdict = evaluate(
            task_id=args.task,
            code_path=args.code,
            workdir=args.workdir,
            device=args.device,
            size=args.size,
            n_seeds=args.seeds,
            warmup=args.warmup,
            iters=args.iters,
            timeout_s=args.timeout,
            allow_cuda_cpp=args.allow_cuda_cpp,
            max_speedup=args.max_speedup,
        )
    except Exception:
        verdict = {
            "harness_version": HARNESS_VERSION,
            "task_id": args.task,
            "status": "sandbox_error",
            "error": _tail(traceback.format_exc()),
        }
    # Written last, after the child tree is gone, so the child cannot pre-write a verdict.
    args.out.write_text(json.dumps(verdict))
    return 0


if __name__ == "__main__":
    sys.exit(main())
