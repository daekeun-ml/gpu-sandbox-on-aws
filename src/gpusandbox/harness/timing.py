"""Timing shared by the trusted reference path and the candidate path.

Both paths must use exactly the same procedure, otherwise the speedup ratio is biased.
"""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable, Sequence
from typing import Any

Checksum = tuple[float, float]


def checksum(output: Any) -> Checksum:
    """Cheap fingerprint of an output: (sum, sum of absolute values) in float64."""
    import torch

    tensors = output if isinstance(output, (list, tuple)) else [output]
    total, total_abs = 0.0, 0.0
    for t in tensors:
        # Exact type: a Tensor subclass can defer the real work until it is read, which would
        # move the computation outside the timed window (the "lazy tensor" hack).
        if type(t) is not torch.Tensor:
            raise TypeError(f"output must be a plain torch.Tensor, got {type(t).__name__}")
        t64 = t.detach().to(torch.float64)
        total += float(t64.sum())
        total_abs += float(t64.abs().sum())
    return total, total_abs


def measure_ms(
    fn: Callable[..., Any],
    warmup_inputs: Sequence[Sequence[Any]],
    timed_inputs: Sequence[Sequence[Any]],
    *,
    device: str,
) -> tuple[list[float], list[Checksum]]:
    """Return per-iteration latency in milliseconds and a checksum of every timed output.

    * Host clock around a device-wide synchronize. CUDA events on the default stream miss work
      that candidate code launches on a side stream (a documented KernelBench timing hole);
      torch.cuda.synchronize() waits for every stream. The cost is a few microseconds of
      launch overhead, paid equally by reference and candidate.
    * Every timed iteration gets its own input set, so an output cache keyed on the input
      tensor never hits.
    * The checksum is computed after the clock stops and lets the trusted parent verify the
      timed outputs, not only the correctness-check outputs.
    """
    import torch

    if not timed_inputs:
        raise ValueError("timed_inputs must not be empty")
    cuda = device == "cuda"

    def sync() -> None:
        if cuda:
            torch.cuda.synchronize()

    samples: list[float] = []
    sums: list[Checksum] = []
    with torch.inference_mode():
        for args in warmup_inputs:
            fn(*args)
        sync()
        for args in timed_inputs:
            t0 = time.perf_counter()
            out = fn(*args)
            sync()
            samples.append((time.perf_counter() - t0) * 1e3)
            sums.append(checksum(out))
    return samples, sums


def checksums_match(cand: Checksum, ref: Checksum, *, numel: int, atol: float, rtol: float) -> bool:
    tol = atol * numel + rtol * ref[1]
    return abs(cand[0] - ref[0]) <= tol and abs(cand[1] - ref[1]) <= tol


def median(samples: Sequence[float]) -> float:
    return float(statistics.median(samples))


def make_input_sets(
    get_inputs: Callable[..., list[Any]], *, base_seed: int, count: int, device: str, size: str
) -> list[list[Any]]:
    return [get_inputs(base_seed + i, device, size) for i in range(count)]
