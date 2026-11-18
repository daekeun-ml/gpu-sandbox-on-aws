"""Untrusted child process: import candidate code, write outputs and timings to the workdir.

Invoked by evaluate.py as ``python -I -m gpusandbox.harness.runner ...``. Everything this
process writes is treated as untrusted input by the parent.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import traceback
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

EXIT_OK, EXIT_INIT, EXIT_LOAD, EXIT_RUN, EXIT_TIMING = 0, 2, 3, 4, 5


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:]


def _install_triton_launch_counter() -> SimpleNamespace | None:
    """Count Triton kernel launches so the parent can tell a real kernel from a torch call.

    Best effort: returns None when Triton is missing or its internals differ from what this
    hook expects. The policy forbids candidates from assigning module attributes, so the
    candidate cannot simply restore the original method.
    """
    try:
        from triton.runtime import jit as triton_jit
    except Exception:
        return None
    counter = SimpleNamespace(count=0)
    original = getattr(triton_jit.JITFunction, "run", None)
    if original is None:
        return None

    def counted_run(self: Any, *args: Any, **kwargs: Any) -> Any:
        counter.count += 1
        return original(self, *args, **kwargs)

    triton_jit.JITFunction.run = counted_run
    return counter


def _load_candidate(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("candidate", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # Triton's @jit reads source through inspect, which needs the module registered.
    sys.modules["candidate"] = module
    spec.loader.exec_module(module)
    return module


def _to_cpu(result: Any) -> Any:
    import torch

    # Exact type check: Tensor subclasses can hide deferred computation (see timing.checksum).
    if type(result) is torch.Tensor:
        return result.detach().to("cpu")
    if isinstance(result, (tuple, list)) and all(type(t) is torch.Tensor for t in result):
        return [t.detach().to("cpu") for t in result]
    raise TypeError(f"ModelNew.forward must return a tensor, got {type(result).__name__}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--code", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--size", default="full", choices=["full", "smoke"])
    parser.add_argument("--seeds", required=True, help="comma-separated correctness seeds")
    parser.add_argument("--timing-seed", type=int, required=True)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iters", type=int, default=20)
    args = parser.parse_args(argv)

    status_path = args.outdir / "runner.json"

    def write_status(**payload: Any) -> None:
        status_path.write_text(json.dumps(payload))

    try:
        import torch

        from gpusandbox.harness.timing import make_input_sets, measure_ms
        from gpusandbox.tasks import get_task

        task = get_task(args.task).module
        counter = _install_triton_launch_counter() if args.device == "cuda" else None
        seeds = [int(s) for s in args.seeds.split(",") if s]
    except Exception:
        write_status(stage="init", error=_tail(traceback.format_exc()))
        return EXIT_INIT

    try:
        module = _load_candidate(args.code)
        model_cls = getattr(module, "ModelNew")
        model = model_cls(*task.get_init_inputs()).to(args.device).eval()
    except Exception:
        write_status(stage="load", error=_tail(traceback.format_exc()))
        return EXIT_LOAD

    try:
        with torch.inference_mode():
            for seed in seeds:
                result = model(*task.get_inputs(seed, args.device, args.size))
                if args.device == "cuda":
                    torch.cuda.synchronize()
                torch.save(_to_cpu(result), args.outdir / f"cand_{seed}.pt")
    except Exception:
        write_status(stage="run", error=_tail(traceback.format_exc()))
        return EXIT_RUN

    launches = counter.count if counter is not None else None
    try:
        # Same seeds as the parent's reference timing, so per-iteration checksums line up.
        inputs = make_input_sets(
            task.get_inputs,
            base_seed=args.timing_seed,
            count=args.warmup + args.iters,
            device=args.device,
            size=args.size,
        )
        samples, sums = measure_ms(
            model, inputs[: args.warmup], inputs[args.warmup :], device=args.device
        )
    except Exception:
        write_status(stage="timing", error=_tail(traceback.format_exc()), triton_launches=launches)
        return EXIT_TIMING

    write_status(stage="done", triton_launches=launches, cand_ms=samples, checksums=sums)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
