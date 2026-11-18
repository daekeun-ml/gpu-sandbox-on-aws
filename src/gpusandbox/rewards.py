"""Reward functions for on-policy RL over sandbox verdicts.

One sandbox evaluation per completion feeds three reward components, which TRL logs
separately (rewards/format_reward, rewards/correctness_reward, rewards/speedup_reward):

  format       1.0 when the answer contains a parsable module that defines ModelNew
  correctness  graded verdict: wrong but runnable code earns a little, correct code earns 1.0
  speedup      log2-scaled speedup over the PyTorch reference, only for correct custom kernels

Infrastructure failures (status sandbox_error) are not the policy's fault. They return None for
every component so that the sample is excluded instead of being scored as a bad answer.
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import math
import re
import statistics
import sys
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from gpusandbox.client import SandboxClient
from gpusandbox.harness.policy import check_source

log = logging.getLogger(__name__)

_CODE_BLOCK = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)

CORRECTNESS_BY_STATUS = {
    "policy_violation": 0.0,
    "compile_error": 0.0,
    "timeout": 0.0,
    # Triton compiles lazily on the first launch, so kernel compile errors land here.
    "runtime_error": 0.05,
    "wrong_answer": 0.2,
}
CORRECT_WITHOUT_CUSTOM_KERNEL = 0.3


def completion_text(completion: Any) -> str:
    """TRL passes plain strings for standard datasets and message lists for chat datasets."""
    if isinstance(completion, str):
        return completion
    if isinstance(completion, list) and completion and isinstance(completion[-1], dict):
        return str(completion[-1].get("content", ""))
    return str(completion)


def extract_code(text: str) -> str | None:
    """Return the last fenced block that defines ModelNew, else the last fenced block."""
    blocks = _CODE_BLOCK.findall(text)
    if not blocks:
        return None
    for block in reversed(blocks):
        if "class ModelNew" in block:
            return block.strip() + "\n"
    return blocks[-1].strip() + "\n"


def _parses_with_model_new(code: str | None) -> bool:
    if not code:
        return False
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    return any(isinstance(n, ast.ClassDef) and n.name == "ModelNew" for n in tree.body)


def speedup_score(speedup: float) -> float:
    """0.0 at 0.5x, 0.5 at 1x (parity), 1.0 at 2x, capped at 1.5 (4x)."""
    return 0.5 + 0.5 * max(-1.0, min(2.0, math.log2(max(speedup, 1e-6))))


DEFAULT_WEIGHTS = (0.1, 1.0, 0.5)  # format, correctness, speedup


def score_verdict(
    result: dict[str, Any] | None,
    code: str | None,
    *,
    require_triton: bool = True,
    weights: tuple[float, float, float] = DEFAULT_WEIGHTS,
) -> dict[str, float | None]:
    """Reward components for one sandbox verdict. The TRL reward functions, the veRL reward
    and the demo recording all use this, so they can never disagree.

    Every component is None for an infrastructure failure (status sandbox_error).
    """
    status = (result or {}).get("status", "no_code")
    if status == "sandbox_error":
        return {"format": None, "correctness": None, "speedup": None, "total": None}
    fmt = 1.0 if _parses_with_model_new(code) else 0.0
    custom = bool((result or {}).get("custom_kernel")) or not require_triton
    if status == "ok":
        correctness = 1.0 if custom else CORRECT_WITHOUT_CUSTOM_KERNEL
        speed = speedup_score(float(result["speedup"])) if custom and result.get("speedup") else 0.0
    else:
        correctness = CORRECTNESS_BY_STATUS.get(status, 0.0)
        speed = 0.0
    total = weights[0] * fmt + weights[1] * correctness + weights[2] * speed
    return {"format": fmt, "correctness": correctness, "speedup": speed, "total": round(total, 6)}


class KernelRewards:
    def __init__(
        self,
        client: SandboxClient,
        *,
        require_triton: bool = True,
        runtime: str | None = None,
        metrics_file: str | Path | None = None,
        cache_size: int = 8192,
    ) -> None:
        self.client = client
        self.require_triton = require_triton
        self.runtime = runtime
        self.metrics_file = Path(metrics_file) if metrics_file else None
        self.cache_size = cache_size
        self._cache: dict[str, dict[str, Any] | None] = {}
        self._last_version: tuple[str, str] | None = None
        self.batches = 0

    @property
    def reward_funcs(self) -> list[Any]:
        return [self.format_reward, self.correctness_reward, self.speedup_reward]

    # --- evaluation ----------------------------------------------------------------------
    @staticmethod
    def _key(prompt: Any, text: str, task_id: str) -> str:
        h = hashlib.sha256()
        h.update(task_id.encode())
        h.update(json.dumps(prompt, sort_keys=True, default=str).encode())
        h.update(text.encode())
        return h.hexdigest()

    def _evaluate(
        self,
        prompts: Sequence[Any],
        completions: Sequence[Any],
        task_ids: Sequence[str],
        trainer_state: Any = None,
    ) -> list[dict[str, Any] | None]:
        texts = [completion_text(c) for c in completions]
        keys = [self._key(p, t, tid) for p, t, tid in zip(prompts, texts, task_ids)]
        pending: list[tuple[str, dict[str, Any]]] = []
        for key, text, tid in zip(keys, texts, task_ids):
            if key in self._cache:
                continue
            code = extract_code(text)
            if code is None:
                self._cache[key] = {"status": "no_code"}
                continue
            report = check_source(code)
            if not report.ok:
                # Same verdict the sandbox would return; skip the round trip.
                self._cache[key] = {"status": "policy_violation", "violations": report.violations}
                continue
            pending.append((key, {"task_id": tid, "code": code, "request_id": key[:16]}))

        if pending:
            started = time.monotonic()
            info, results = self.client.evaluate_batch_sync(
                [item for _, item in pending], runtime=self.runtime
            )
            for (key, _), result in zip(pending, results):
                self._cache[key] = result
            step = getattr(trainer_state, "global_step", None)
            self._log_batch(info, results, time.monotonic() - started, step)

        out = [self._cache.get(k) for k in keys]
        if len(self._cache) > self.cache_size:
            # Keep only the current batch; older entries are never asked for again.
            self._cache = {k: self._cache[k] for k in keys if k in self._cache}
        return out

    def _log_batch(
        self, info: Any, results: list[dict[str, Any]], wall_s: float, step: int | None
    ) -> None:
        self.batches += 1
        version = (info.runtime, info.version)
        if self._last_version is not None and version != self._last_version:
            self._emit(
                {
                    "event": "sandbox_version_switch",
                    "from": "/".join(self._last_version),
                    "to": "/".join(version),
                    "routing_revision": info.revision,
                    "global_step": step,
                }
            )
        self._last_version = version
        statuses = Counter(str(r.get("status")) for r in results)
        speedups = [r["speedup"] for r in results if r.get("status") == "ok" and r.get("speedup")]
        durations = sorted(float(r["duration_s"]) for r in results if r.get("duration_s"))
        served_versions = Counter(str(r.get("sandbox_version")) for r in results)
        self._emit(
            {
                "event": "reward_batch",
                "batch": self.batches,
                "global_step": step,
                "runtime": info.runtime,
                "version": info.version,
                "served_versions": dict(served_versions),
                "routing_revision": info.revision,
                "n": len(results),
                "status": dict(statuses),
                "pass_rate": round(statuses.get("ok", 0) / max(1, len(results)), 4),
                "custom_kernel_rate": round(
                    sum(1 for r in results if r.get("custom_kernel")) / max(1, len(results)), 4
                ),
                "mean_speedup": round(statistics.fmean(speedups), 4) if speedups else None,
                "eval_p50_s": round(durations[len(durations) // 2], 3) if durations else None,
                "eval_p95_s": round(durations[int(len(durations) * 0.95) - 1], 3)
                if len(durations) >= 2
                else None,
                "batch_wall_s": round(wall_s, 3),
            }
        )

    def _emit(self, record: dict[str, Any]) -> None:
        record["ts"] = round(time.time(), 3)
        line = json.dumps(record)
        print(line, file=sys.stdout, flush=True)
        if self.metrics_file is not None:
            with self.metrics_file.open("a") as fh:
                fh.write(line + "\n")

    # --- TRL reward functions ------------------------------------------------------------
    def _components(self, prompts, completions, task_id, kwargs) -> list[dict[str, float | None]]:
        results = self._evaluate(prompts, completions, task_id, kwargs.get("trainer_state"))
        return [
            score_verdict(result, extract_code(completion_text(c)), require_triton=self.require_triton)
            for c, result in zip(completions, results)
        ]

    def format_reward(self, prompts, completions, task_id, **kwargs) -> list[float | None]:
        return [c["format"] for c in self._components(prompts, completions, task_id, kwargs)]

    def correctness_reward(self, prompts, completions, task_id, **kwargs) -> list[float | None]:
        return [c["correctness"] for c in self._components(prompts, completions, task_id, kwargs)]

    def speedup_reward(self, prompts, completions, task_id, **kwargs) -> list[float | None]:
        return [c["speedup"] for c in self._components(prompts, completions, task_id, kwargs)]
