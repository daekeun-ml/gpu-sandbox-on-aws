#!/usr/bin/env python3
"""Show sandbox and trainer logs as short, colored lines: ... | python3 scripts/logview.py

The tools, the reward function and the trainer write one JSON event per line (reward_batch,
sandbox_version_switch, parity, episode events, ...). Those lines stay as they are in the pod
logs and in metrics files; this filter only changes what an operator sees in a terminal.

- stdout is not a terminal, or GPUSANDBOX_LOG=json: every line passes through unchanged, so
  `| grep`, `| tee file` and `> file` keep the raw JSON.
- NO_COLOR set (any value): the summary has no colors.
- Lines that are not JSON pass through; PASS, FAIL, errors and tracebacks get a color.

Standard library only, so it runs with the workstation's python3 outside the virtualenv.
"""

from __future__ import annotations

import ast
import json
import os
import sys
import time
from typing import Any, Callable

COLORS = {
    "dim": "2", "bold": "1", "red": "31", "green": "32", "yellow": "33",
    "blue": "34", "magenta": "35", "cyan": "36",
}
STATUS_COLORS = {
    "ok": "green", "wrong_answer": "yellow", "policy_violation": "yellow",
    "timeout": "red", "sandbox_error": "red", "compile_error": "yellow", "runtime_error": "yellow",
}
TRAINER_KEYS = ("loss", "reward", "reward_std", "kl", "grad_norm", "learning_rate", "epoch")


class View:
    def __init__(self, color: bool) -> None:
        self.color = color

    def c(self, name: str, text: str) -> str:
        if not self.color:
            return text
        return f"\033[{COLORS[name]}m{text}\033[0m"

    def stamp(self, record: dict[str, Any] | None = None) -> str:
        ts = record.get("ts") if record else None
        clock = time.strftime("%H:%M:%S", time.localtime(ts if isinstance(ts, (int, float)) else None))
        return self.c("blue", f"[{clock}]")

    def statuses(self, counts: dict[str, Any]) -> str:
        parts = []
        for status, n in counts.items():
            parts.append(self.c(STATUS_COLORS.get(status, "cyan"), f"{status} {n}"))
        return "  ".join(parts)

    # --- one formatter per event -----------------------------------------------------------
    def reward_batch(self, r: dict[str, Any]) -> str:
        pool = f"{r.get('runtime')}/{r.get('version')}"
        line = f"batch {r.get('batch', '?'):>3}  {self.c('cyan', pool)}  {self.statuses(r.get('status') or {})}"
        if r.get("pass_rate") is not None:
            line += f"  pass {float(r['pass_rate']) * 100:.0f}%"
        if r.get("mean_speedup") is not None:
            line += f"  speedup {float(r['mean_speedup']):.2f}"
        if r.get("batch_wall_s") is not None:
            line += self.c("dim", f"  {float(r['batch_wall_s']):.1f}s")
        served = r.get("served_versions") or {}
        if len(served) > 1:
            line += "  " + self.c("red", f"MIXED VERSIONS {served}")
        return line

    def sandbox_version_switch(self, r: dict[str, Any]) -> str:
        detail = f"(routing rev {r.get('routing_revision')}, step {r.get('global_step')})"
        return self.c("magenta", self.c("bold", f"SWITCH  {r.get('from')} -> {r.get('to')}")) + "  " + self.c("dim", detail)

    def parity(self, r: dict[str, Any]) -> str:
        mark = self.c("green", "PARITY PASS") if r.get("passed") else self.c("red", "PARITY FAIL")
        return f"{mark}  {r.get('baseline')} -> {r.get('candidate')}"

    def simulate(self, r: dict[str, Any]) -> str:
        return self.c("dim", f"simulate: {r.get('steps')} batches on {r.get('device')}, no model (golden submissions)")

    def episode_start(self, r: dict[str, Any]) -> str:
        pool = f"{r.get('runtime')}/{r.get('version')}"
        return f"episode {r.get('episode')} start  {self.c('cyan', pool)}  claim {r.get('claim')}" + self.c(
            "dim", f"  ready {r.get('claim_ready_s')}s")

    def turn(self, r: dict[str, Any]) -> str:
        status = r.get("status")
        line = f"episode {r.get('episode')} turn {r.get('turn')}  " + self.c(STATUS_COLORS.get(status, "cyan"), str(status))
        if r.get("speedup") is not None:
            line += f"  speedup {float(r['speedup']):.2f}"
        return line + self.c("dim", f"  {r.get('latency_s')}s")

    def episode_end(self, r: dict[str, Any]) -> str:
        solved = self.c("green", "solved") if r.get("solved") else self.c("yellow", "not solved")
        return f"episode {r.get('episode')} end  {solved}  turns {r.get('turns_used')}  reward {r.get('reward')}" + self.c(
            "dim", f"  stop {r.get('stop_reason')}")

    def episode_error(self, r: dict[str, Any]) -> str:
        return self.c("red", f"episode {r.get('episode')} error after {r.get('turns_done')} turns: {r.get('error')}")

    def multiturn_summary(self, r: dict[str, Any]) -> str:
        return self.c("bold", f"summary  solved {r.get('solved')}/{r.get('episodes')}  mean turns {r.get('mean_turns')}"
                              f"  mean reward {r.get('mean_reward')}")

    def generic(self, r: dict[str, Any]) -> str:
        fields = "  ".join(f"{k} {v}" for k, v in r.items() if k not in ("event", "ts"))
        return f"{self.c('bold', str(r['event']))}  {fields}"

    # --- records without an "event" key --------------------------------------------------
    def pod_info(self, r: dict[str, Any]) -> str:
        blocked = self.c("green", "egress blocked") if r.get("egress_blocked") else self.c("red", "EGRESS OPEN")
        gpu = r.get("gpu") or "no GPU"
        pool = f"{r.get('runtime')}/{r.get('version')}"
        return f"pod {r.get('pod')}  {self.c('cyan', pool)}  kernel {r.get('kernel_release')}  {gpu}  {blocked}"

    def bench_report(self, r: dict[str, Any]) -> str:
        return (f"bench  {self.c('cyan', str(r.get('runtime')))}  ok {r.get('ok')}/{r.get('requests')}"
                f"  p50 {r.get('eval_p50_s')}s  p95 {r.get('eval_p95_s')}s"
                f"  {r.get('throughput_eval_per_s')} eval/s  speedup {r.get('speedup_median')}")

    def trainer_metrics(self, r: dict[str, Any]) -> str:
        # Transformers 5 prints floats already formatted as strings ('0.3725'); accept both.
        def fields(keys: tuple[str, ...]) -> str:
            shown = []
            for key in keys:
                value = _number(r.get(key))
                if value is not None:
                    shown.append(f"{key} {value:.4g}")
            return "  ".join(shown)

        if "train_runtime" in r:  # the trainer's final summary
            return self.c("bold", "train done  ") + fields(("train_runtime", "train_loss", "epoch"))
        return self.c("dim", "train  ") + fields(TRAINER_KEYS)

    # --- plain text -----------------------------------------------------------------------
    def text(self, line: str) -> str:
        stripped = line.lstrip()
        if stripped.startswith("PASS "):
            return line.replace("PASS", self.c("green", "PASS"), 1)
        if stripped.startswith("FAIL "):
            return self.c("red", line)
        if stripped.startswith(("Traceback", "Error", "error:")) or "Error:" in stripped:
            return self.c("red", line)
        return line

    def render(self, line: str) -> str:
        stripped = line.strip()
        if stripped.startswith("{"):
            record = _parse(stripped)
            if isinstance(record, dict):
                formatted = self.record(record)
                if formatted is not None:
                    return f"{self.stamp(record)} {formatted}"
        return self.text(line)

    def record(self, r: dict[str, Any]) -> str | None:
        event = r.get("event")
        if isinstance(event, str):
            handlers: dict[str, Callable[[dict[str, Any]], str]] = {
                "reward_batch": self.reward_batch,
                "sandbox_version_switch": self.sandbox_version_switch,
                "parity": self.parity,
                "simulate": self.simulate,
                "episode_start": self.episode_start,
                "turn": self.turn,
                "episode_end": self.episode_end,
                "episode_error": self.episode_error,
                "multiturn_summary": self.multiturn_summary,
            }
            return handlers.get(event, self.generic)(r)
        if "endpoint" in r and "pod" in r:
            return self.pod_info(r)
        if "throughput_eval_per_s" in r:
            return self.bench_report(r)
        if "train_runtime" in r or any(key in r for key in TRAINER_KEYS):
            return self.trainer_metrics(r)
        return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _parse(text: str) -> Any:
    try:
        return json.loads(text)
    except ValueError:
        pass
    try:  # the Hugging Face trainer prints Python dicts: {'loss': 0.1, ...}
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return None


def main() -> int:
    raw = os.environ.get("GPUSANDBOX_LOG", "").lower() == "json" or not sys.stdout.isatty()
    view = View(color="NO_COLOR" not in os.environ)
    for line in iter(sys.stdin.readline, ""):
        line = line.rstrip("\n")
        try:
            sys.stdout.write((line if raw else view.render(line)) + "\n")
            sys.stdout.flush()
        except BrokenPipeError:
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
