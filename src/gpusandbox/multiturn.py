"""Multi-turn (agentic) episodes: one task, several submissions, one claimed sandbox.

Single-turn grading (the TRL GRPO rewards, ``tools simulate``) scores every completion on its
own, on whichever pool pod is free. In an episode the agent submits a kernel, reads the verdict
as feedback, and submits again, up to ``max_turns`` times. Every turn goes to the same sandbox,
claimed from an Agent Sandbox warm pool (EpisodeSandbox), so the agent sees one GPU and one
sandbox version for the whole episode, and the claim is released when the episode ends.

The episode reward is ``score_verdict`` of the final submission, the ``calc_reward`` of the veRL
sketch in docs/concepts/06_agent_sandbox.md (rl/verl/sandbox_tool.py hands the same number to
the reward function): the episode is judged by what the sandbox measured for the kernel the
agent ended with. Earlier failing turns reach the agent only as feedback. Summing per-turn
scores would pay for many mediocre attempts (a wrong answer still earns 0.2), and taking the
best turn would credit an episode that ended on a broken kernel. An episode stops early when
the stop condition holds (default: ``solved``) or on a sandbox_error.

The runner is policy-agnostic. ``ScriptedPolicy`` replays golden submissions so that episodes
run without a model or a GPU (scenario C):

    python -m gpusandbox.tools multiturn --warm-pool kernel-eval-gvisor-cpu --device cpu
"""

from __future__ import annotations

import json
import statistics
import time
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from gpusandbox.agent_sandbox import EpisodeSandbox
from gpusandbox.golden import Golden, golden_for
from gpusandbox.rewards import score_verdict

# veRL 0.9.1 truncates tool responses longer than multi_turn.max_tool_response_length
# (default 256 characters), so feedback stays below that.
FEEDBACK_LIMIT = 240
ERROR_EXCERPT = 120

Emit = Callable[[dict[str, Any]], None]


def emit_json(record: dict[str, Any]) -> None:
    """One JSON object per line on stdout, like the reward_batch events of ``simulate``."""
    record["ts"] = round(time.time(), 3)
    print(json.dumps(record), flush=True)


def solved(verdict: dict[str, Any], *, require_triton: bool = True) -> bool:
    """Full correctness credit under score_verdict: ok, plus a custom kernel when required."""
    return verdict.get("status") == "ok" and (bool(verdict.get("custom_kernel")) or not require_triton)


def stop_reason(
    verdict: dict[str, Any], *, turn: int, max_turns: int, stop: Callable[[dict[str, Any]], bool]
) -> str | None:
    """Why the episode ends after this verdict, or None to let the agent submit again."""
    if verdict.get("status") == "sandbox_error":
        # The rest of the episode would no longer measure the policy; free the sandbox. The
        # reward is None, so the episode is excluded like a single-turn sandbox_error sample.
        return "sandbox_error"
    if stop(verdict):
        return "solved"
    if turn >= max_turns:
        return "max_turns"
    return None


def _excerpt(text: str) -> str:
    # The last line of a traceback or harness message names the problem.
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    last = lines[-1] if lines else ""
    return last if len(last) <= ERROR_EXCERPT else last[: ERROR_EXCERPT - 3] + "..."


def format_feedback(
    verdict: dict[str, Any], *, require_triton: bool = True, limit: int = FEEDBACK_LIMIT
) -> str:
    """The short text an agent reads before its next turn: status, flags, speedup, error.

    ``limit`` caps the length; keep it at or below the trainer's tool response limit so that
    the status at the front is never the part that gets cut.
    """
    status = str(verdict.get("status", "sandbox_error"))
    parts = [f"status: {status}"]
    if status == "ok":
        speedup = verdict.get("speedup")
        parts.append(f"speedup: {float(speedup):.2f}x" if speedup else "speedup: n/a")
        if require_triton and not verdict.get("custom_kernel"):
            parts.append("no custom Triton kernel ran, so correctness gets partial credit")
    flags = verdict.get("flags") or []
    if flags:
        parts.append("flags: " + ", ".join(str(f) for f in flags))
    violations = verdict.get("violations") or []
    if violations:
        parts.append(f"violation: {_excerpt(violations[0])}")
    error = verdict.get("error")
    # A sandbox_error message describes the infrastructure (auth, pod, gateway), not the code.
    if error and status not in ("ok", "policy_violation", "sandbox_error"):
        parts.append(f"error: {_excerpt(error)}")
    if status == "sandbox_error":
        parts.append("infrastructure failure, not caused by your code")
    text = "; ".join(parts)
    return text if len(text) <= limit else text[: limit - 3] + "..."


@dataclass(frozen=True)
class Turn:
    turn: int
    code: str
    verdict: dict[str, Any]
    feedback: str
    latency_s: float
    # What single-turn grading would give this submission on its own.
    single_turn_reward: float | None


class Policy(Protocol):
    def __call__(self, task_id: str, turn: int, history: Sequence[Turn]) -> str:
        """Source code of the next submission. ``history`` holds the earlier turns."""
        ...


# Golden names per task and device, in submission order: failing attempts first, so that the
# feedback has something to report, then the submission that solves the task.
SCRIPTS: dict[str, dict[str, tuple[str, ...]]] = {
    "relu_bias": {
        "cuda": ("read_host_file", "relu_bias_wrong", "relu_bias_triton"),
        "cpu": ("read_host_file", "relu_bias_wrong", "relu_bias_torch_only"),
    },
    "vector_add": {"cuda": ("vector_add_triton",)},
}


class ScriptedPolicy:
    """Golden submissions in a fixed order, standing in for a model.

    It does not interpret the feedback: turn n submits entry n of the task's script (the last
    entry again once the script runs out). It exercises the episode mechanics (one claim,
    feedback between turns, early stop, final-submission reward), not learning.
    """

    name = "scripted"

    def __init__(self, device: str) -> None:
        self.device = device
        by_name = {g.name: g for g in golden_for(device)}
        self.scripts = {
            task: tuple(by_name[n] for n in names[device])
            for task, names in SCRIPTS.items()
            if device in names
        }

    def script(self, task_id: str) -> tuple[Golden, ...]:
        if task_id not in self.scripts:
            raise ValueError(f"no scripted episode for {task_id} on {self.device}; "
                             f"choose from {sorted(self.scripts)}")
        return self.scripts[task_id]

    def entry(self, task_id: str, turn: int) -> Golden:
        script = self.script(task_id)
        return script[min(turn, len(script)) - 1]

    def __call__(self, task_id: str, turn: int, history: Sequence[Turn]) -> str:
        return self.entry(task_id, turn).code


@dataclass
class EpisodeResult:
    episode: int
    task_id: str
    claim: str
    address: str | None
    turns: list[Turn] = field(default_factory=list)
    reward: dict[str, float | None] = field(default_factory=dict)
    solved: bool = False
    stop_reason: str | None = None

    @property
    def pods(self) -> set[str]:
        """Pods that answered, as reported by the sandbox server in each verdict."""
        return {str(t.verdict["pod"]) for t in self.turns if t.verdict.get("pod")}


def run_episode(
    open_sandbox: Callable[[], EpisodeSandbox],
    policy: Policy,
    *,
    episode: int,
    task_id: str,
    max_turns: int,
    require_triton: bool = True,
    stop_when: Callable[[dict[str, Any]], bool] | None = None,
    emit: Emit = emit_json,
) -> EpisodeResult:
    """Run one episode in one claimed sandbox. The claim is released on exit, also on errors."""
    if max_turns < 1:
        raise ValueError("max_turns must be at least 1")
    stop = stop_when or (lambda v: solved(v, require_triton=require_triton))
    sandbox = open_sandbox()
    result = EpisodeResult(episode=episode, task_id=task_id, claim=sandbox.name, address=None)
    started = time.monotonic()
    try:
        with sandbox:
            result.address = sandbox.address
            claim_ready_s = round(time.monotonic() - started, 3)
            try:
                info = sandbox.info()
            except (httpx.HTTPError, ValueError) as exc:
                # Decorative only: the verdicts below carry runtime, version and pod as well.
                info = {"info_error": f"{type(exc).__name__}: {exc}"}
            emit({
                "event": "episode_start", "episode": episode, "task_id": task_id,
                "claim": sandbox.name, "warm_pool": sandbox.warm_pool,
                "sandbox": sandbox.sandbox_name, "address": sandbox.address,
                "claim_ready_s": claim_ready_s,
                "runtime": info.get("runtime"), "version": info.get("sandbox_version"),
                "pod": info.get("pod"), "kernel_release": info.get("kernel_release"),
                "gpu": (info.get("device") or {}).get("name"),
                **({"info_error": info["info_error"]} if "info_error" in info else {}),
            })
            for turn in range(1, max_turns + 1):
                code = policy(task_id, turn, tuple(result.turns))
                t0 = time.monotonic()
                verdict = sandbox.evaluate(task_id=task_id, code=code)
                latency_s = round(time.monotonic() - t0, 3)
                feedback = format_feedback(verdict, require_triton=require_triton)
                score = score_verdict(verdict, code, require_triton=require_triton)["total"]
                result.turns.append(Turn(turn, code, verdict, feedback, latency_s, score))
                emit({
                    "event": "turn", "episode": episode, "turn": turn, "task_id": task_id,
                    "claim": sandbox.name, "address": sandbox.address, "pod": verdict.get("pod"),
                    "version": verdict.get("sandbox_version"),
                    "status": verdict.get("status"), "speedup": verdict.get("speedup"),
                    "flags": verdict.get("flags") or [], "feedback": feedback,
                    "single_turn_reward": score, "latency_s": latency_s,
                    "eval_s": verdict.get("duration_s"),
                })
                result.stop_reason = stop_reason(verdict, turn=turn, max_turns=max_turns, stop=stop)
                if result.stop_reason:
                    break
    except Exception as exc:
        emit({"event": "episode_error", "episode": episode, "claim": result.claim,
              "turns_done": len(result.turns), "error": f"{type(exc).__name__}: {exc}"})
        raise

    final = result.turns[-1]
    result.reward = score_verdict(final.verdict, final.code, require_triton=require_triton)
    result.solved = solved(final.verdict, require_triton=require_triton)
    emit({
        "event": "episode_end", "episode": episode, "task_id": task_id, "claim": result.claim,
        "address": result.address, "turns_used": len(result.turns),
        "stop_reason": result.stop_reason,
        "final_status": final.verdict.get("status"), "solved": result.solved,
        "reward": result.reward["total"],
        "reward_components": {k: v for k, v in result.reward.items() if k != "total"},
        "first_turn_reward": result.turns[0].single_turn_reward,
        "released": True,
    })
    return result


def summarize(results: Sequence[EpisodeResult]) -> dict[str, Any]:
    """Across episodes: rewards, and whether each episode stayed on one sandbox."""
    rewards = [r.reward["total"] for r in results if r.reward.get("total") is not None]
    first = [r.turns[0].single_turn_reward for r in results
             if r.turns and r.turns[0].single_turn_reward is not None]
    return {
        "event": "multiturn_summary",
        "episodes": len(results),
        "solved": sum(r.solved for r in results),
        "stop_reasons": dict(Counter(str(r.stop_reason) for r in results)),
        "mean_turns": round(statistics.fmean(len(r.turns) for r in results), 3) if results else None,
        "mean_reward": round(statistics.fmean(rewards), 4) if rewards else None,
        "mean_first_turn_reward": round(statistics.fmean(first), 4) if first else None,
        "claims": len({r.claim for r in results}),
        "distinct_sandboxes": len({r.address for r in results if r.address}),
        "one_sandbox_per_episode": all(len(r.pods) <= 1 for r in results),
        "sandbox_errors": sum(t.verdict.get("status") == "sandbox_error" for r in results for t in r.turns),
    }
