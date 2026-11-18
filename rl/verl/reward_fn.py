"""veRL custom reward for the kernel task, scored through the sandbox gateway.

veRL (0.9.x) scores samples one at a time and recommends async reward functions for sandboxed
execution: each reward worker runs many ``compute_score`` coroutines concurrently. Because
samples arrive individually, the batch-level version snapshot used with TRL is not available;
instead every request carries a ``group_key`` and the gateway keeps all samples of one prompt
group on the same sandbox version, even across a rollout.

Wire it up with (veRL 0.9.1 keys):
    reward.custom_reward_function.path=/opt/gpusandbox/rl/verl/reward_fn.py
    reward.custom_reward_function.name=compute_score
"""

from __future__ import annotations

from typing import Any

from gpusandbox.client import SandboxClient
from gpusandbox.harness.policy import check_source
from gpusandbox.rewards import DEFAULT_WEIGHTS, extract_code, score_verdict

_client: SandboxClient | None = None


def _get_client() -> SandboxClient:
    # One client per reward worker process; it reads SANDBOX_GATEWAY and SANDBOX_TOKEN_FILE.
    global _client
    if _client is None:
        _client = SandboxClient.from_env()
    return _client


def _score(
    score: float,
    status: str,
    *,
    correctness: float = 0.0,
    speedup_reward: float = 0.0,
    speedup: float = 0.0,
    sandbox_version: str = "",
    sandbox_error: int = 0,
) -> dict[str, Any]:
    # Always the same keys: veRL 0.9.1 builds the reward_extra_info columns from the first
    # sample's keys (agent_loop.py), so a key missing from a later sample raises KeyError.
    return {
        "score": score,
        "status": status,
        "correctness": correctness,
        "speedup_reward": speedup_reward,
        "speedup": speedup,
        "sandbox_version": sandbox_version,
        "sandbox_error": sandbox_error,
    }


async def compute_score(
    data_source: str,
    solution_str: str,
    ground_truth: str,
    extra_info: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    task_id = ground_truth
    info = extra_info or {}
    code = extract_code(solution_str)
    if code is None:
        return _score(0.0, "no_code")
    report = check_source(code)
    if not report.ok:
        parts = score_verdict({"status": "policy_violation"}, code)
        return _score(parts["total"], "policy_violation", correctness=parts["correctness"])

    # Prompt row index identifies the GRPO group within a step; the gateway's pin TTL
    # separates the same row seen again in a later epoch.
    group_key = f"{task_id}:{info.get('index', 'na')}"
    result = await _get_client().evaluate_grouped(
        {"task_id": task_id, "code": code}, group_key=group_key
    )
    status = str(result.get("status", "sandbox_error"))
    parts = score_verdict(result, code)
    if parts["total"] is None:
        # veRL has no "skip this sample" signal, so score only what the policy controls (the
        # format) and flag it; watch reward_extra_info/sandbox_error in the logs.
        version = str(result.get("sandbox_version") or "")
        return _score(DEFAULT_WEIGHTS[0], status, sandbox_version=version, sandbox_error=1)
    return _score(
        parts["total"],
        status,
        correctness=parts["correctness"],
        speedup_reward=parts["speedup"],
        speedup=float(result.get("speedup") or 0.0),
        sandbox_version=str(result.get("sandbox_version")),
    )
