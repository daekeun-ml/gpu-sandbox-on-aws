"""veRL multi-turn tool: one claimed sandbox per trajectory (Agent Sandbox extension).

The model calls ``submit_kernel(code=...)``. Each call is evaluated in the trajectory's own
sandbox, claimed from a SandboxWarmPool on the first call (gpusandbox.agent_sandbox), and the
verdict comes back as the tool response (gpusandbox.multiturn.format_feedback), which the model
reads before its next turn. The episode stops when the kernel is solved, after max_turns
submissions, or on a sandbox_error, and the claim is deleted then. The trajectory reward is
score_verdict of the final submission, the same rule as ``python -m gpusandbox.tools multiturn``.

How veRL 0.9.1 drives a BaseTool, and what this module does about it (read in
verl-project/verl@v0.9.1: verl/experimental/agent_loop/tool_agent_loop.py, agent_loop.py,
verl/tools/base_tool.py, verl/tools/tool_registry.py, reward_loop/reward_manager/naive.py):

* ToolAgentLoop._call_tool runs create -> execute -> release for every tool call, so a BaseTool
  instance lives for one call, not for a trajectory. Episodes are kept in a registry keyed by a
  per-trajectory key that is stored in agent_data.extra_fields (one AgentData per trajectory;
  execute receives it as kwargs["agent_data"]). agent_data.request_id is not used: with
  rollout.full_determinism it is "det-<priority>", and priorities restart at 0 every batch.
* Nothing in 0.9.1 calls calc_reward. The episode summary goes into
  agent_data.extra_fields["gpusandbox_episode"]; the reward loop merges extra_fields into the
  reward function's extra_info (tool_extra_fields), and compute_score below reads it there.
* ToolAgentLoop gives tools no end-of-trajectory hook. SandboxToolAgentLoop (registered as
  "sandbox_tool_agent") wraps run() and deletes the claim when the trajectory ends. Under the
  plain "tool_agent" loop, an episode that did not stop on its own keeps its sandbox until no
  call arrived for idle_release_s, and the claim's shutdownTime is the last safety net.
* veRL truncates tool responses longer than multi_turn.max_tool_response_length (default 256),
  so feedback is capped at max_feedback_chars; keep that at or below the veRL setting.

Wire-up (veRL 0.9.1 keys):
    actor_rollout_ref.rollout.multi_turn.enable=True
    actor_rollout_ref.rollout.multi_turn.tool_config_path=/opt/gpusandbox/rl/verl/sandbox_tool_config.yaml
    actor_rollout_ref.rollout.multi_turn.max_assistant_turns=4     # >= max_turns submissions
    actor_rollout_ref.rollout.agent.default_agent_loop=sandbox_tool_agent
    reward.custom_reward_function.path=pkg://sandbox_tool
    reward.custom_reward_function.name=compute_score
veRL imports the tool class by module name (tool_registry.get_tool_class), so the directory of
this file (/opt/gpusandbox/rl/verl in the veRL image) must be on PYTHONPATH in every Ray worker,
for example as an env var of the RayCluster pods. # TODO verify the PYTHONPATH route on a
cluster (pod env, or ray job submit --runtime-env-json env_vars). Importing the module by name
also registers SandboxToolAgentLoop; pkg:// loads the reward function from that same module.
SandboxToolAgentLoop takes the task id from extra_info.task_id (written by
rl/verl/prepare_data.py); under "tool_agent" each row needs
extra_info.tools_kwargs.submit_kernel.create_kwargs.task_id instead.

The rollout workers need what EpisodeSandbox needs, and k8s/production/raycluster-verl.yaml.tpl
provides none of it: a Kubernetes API token for a ServiceAccount bound to the sandbox-claims Role
(k8s/extensions/agent-sandbox/trainer-claims-rbac.yaml), the kubernetes Python package, a
projected token with the sandbox audience (not the gateway audience) in SANDBOX_TOKEN_FILE, the
gpusandbox/client=true label, and that ServiceAccount in the warm pool's allowed subjects. A
trajectory holds one sandbox, which is one GPU on GPU pools, from its first submission to the end
of its episode, so the warm pool size bounds the number of concurrent trajectories.
"""

# No "from __future__ import annotations" here: veRL may load this file by path without adding it
# to sys.modules (utils/import_utils.load_module), and dataclasses cannot resolve string
# annotations of such a module.
import asyncio
import copy
import importlib.util
import logging
import os
import time
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from gpusandbox.agent_sandbox import EpisodeSandbox
from gpusandbox.client import BackgroundLoop
from gpusandbox.multiturn import FEEDBACK_LIMIT, format_feedback, solved, stop_reason
from gpusandbox.rewards import DEFAULT_WEIGHTS, extract_code, score_verdict

try:
    from verl.tools.base_tool import BaseTool
    from verl.tools.schemas import ToolResponse

    HAVE_VERL = True
except ImportError:  # the control image and the unit tests have no verl
    HAVE_VERL = False
    BaseTool = object

    @dataclass
    class ToolResponse:  # type: ignore[no-redef]
        """The field of verl.tools.schemas.ToolResponse that this tool sets."""

        text: str | None = None


log = logging.getLogger(__name__)

TOOL_NAME = "submit_kernel"
KEY_FIELD = "gpusandbox_episode_key"
SUMMARY_FIELD = "gpusandbox_episode"


def submitted_code(parameters: dict[str, Any]) -> str:
    """The module the model passed; a fenced block is unwrapped like a single-turn answer."""
    raw = str(parameters.get("code") or "")
    return extract_code(raw) or raw


def with_episode_key(
    tools_kwargs: dict[str, Any] | None, tool_names: Iterable[str], key: str, *, task_id: str | None
) -> dict[str, Any]:
    """tools_kwargs for one trajectory, with its episode key and a default task_id added.

    The row's tools_kwargs may be one object shared by the rollout.n copies of a prompt, so it
    is copied, never changed in place.
    """
    out = copy.deepcopy(dict(tools_kwargs or {}))
    for name in tool_names:
        entry = dict(out.get(name) or {})
        create = dict(entry.get("create_kwargs") or {})
        create["episode_key"] = key
        if task_id and not create.get("task_id"):
            create["task_id"] = task_id
        out[name] = {**entry, "create_kwargs": create}
    return out


def episode_score(summary: dict[str, Any] | None) -> dict[str, Any]:
    """Trajectory reward from the episode summary.

    Always the same keys: veRL stacks reward_extra_info key by key across the batch.
    """
    if not summary or summary.get("final_status") is None:
        return {"score": 0.0, "status": "no_submission", "turns": 0, "first_turn_reward": 0.0,
                "sandbox_error": 0}
    turns = int(summary.get("turns") or 0)
    first = float(summary.get("first_turn_reward") or 0.0)  # 0.0 when unavailable
    if summary.get("reward") is None:
        # sandbox_error: as in reward_fn.py, score only the format and flag the sample.
        return {"score": DEFAULT_WEIGHTS[0], "status": str(summary["final_status"]), "turns": turns,
                "first_turn_reward": first, "sandbox_error": 1}
    return {"score": float(summary["reward"]), "status": str(summary["final_status"]),
            "turns": turns, "first_turn_reward": first, "sandbox_error": 0}


def compute_score(
    data_source: str,
    solution_str: str,
    ground_truth: str,
    extra_info: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """veRL custom reward: score the trajectory's final submission, not its final text.

    The sandbox already judged every submission during the rollout; scoring the episode summary
    avoids a second GPU evaluation per trajectory.
    """
    return episode_score((extra_info or {}).get(SUMMARY_FIELD))


@dataclass
class _Episode:
    key: str
    task_id: str
    extra: dict[str, Any] | None = None  # the trajectory's agent_data.extra_fields
    sandbox: EpisodeSandbox | None = None
    claim: str | None = None
    address: str | None = None
    statuses: list[str] = field(default_factory=list)
    single_turn_rewards: list[float | None] = field(default_factory=list)
    final_code: str | None = None
    final_verdict: dict[str, Any] | None = None
    stop_reason: str | None = None
    last_used: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def summary(self, *, require_triton: bool) -> dict[str, Any]:
        parts = (score_verdict(self.final_verdict, self.final_code, require_triton=require_triton)
                 if self.final_verdict is not None else {"total": None})
        return {
            "task_id": self.task_id,
            "claim": self.claim,
            "address": self.address,
            "turns": len(self.statuses),
            "statuses": list(self.statuses),
            "single_turn_rewards": list(self.single_turn_rewards),
            "first_turn_reward": self.single_turn_rewards[0] if self.single_turn_rewards else None,
            "final_status": (self.final_verdict or {}).get("status"),
            "stop_reason": self.stop_reason,
            "reward": parts["total"],
        }

    def publish(self, *, require_triton: bool) -> None:
        if self.extra is not None:
            self.extra[SUMMARY_FIELD] = self.summary(require_triton=require_triton)


class KernelSandboxTool(BaseTool):
    """``submit_kernel``: evaluate a submission in the trajectory's claimed sandbox."""

    def __init__(self, config: dict[str, Any], tool_schema: Any = None) -> None:
        if HAVE_VERL:
            super().__init__(config, tool_schema)
        else:
            self.config, self.tool_schema, self.name = config, tool_schema, TOOL_NAME
        self.warm_pool = str(config["warm_pool"])
        self.namespace = str(config.get("namespace", "sandbox"))
        self.token_file = config.get("token_file") or os.environ.get("SANDBOX_TOKEN_FILE")
        self.max_turns = int(config.get("max_turns", 3))
        self.require_triton = bool(config.get("require_triton", True))
        self.max_feedback_chars = int(config.get("max_feedback_chars", FEEDBACK_LIMIT))
        self.idle_release_s = float(config.get("idle_release_s", 600))
        self.claim_lifetime_s = int(config.get("claim_lifetime_s", 3600))
        self.ready_timeout_s = float(config.get("ready_timeout_s", 600))
        self._episodes: dict[str, _Episode] = {}
        self._instances: dict[str, tuple[str | None, str | None]] = {}  # id -> (task_id, key)
        self._api: Any = None  # one CustomObjectsApi for all claims; tests inject a fake
        self._loop: BackgroundLoop | None = None

    # --- BaseTool ------------------------------------------------------------------------
    async def create(self, instance_id: str | None = None, **kwargs: Any) -> tuple[str, ToolResponse]:
        create_kwargs = kwargs.get("create_kwargs") or {}
        instance_id = instance_id or uuid.uuid4().hex
        self._instances[instance_id] = (create_kwargs.get("task_id"), create_kwargs.get("episode_key"))
        await self.sweep()
        return instance_id, ToolResponse()

    async def execute(
        self, instance_id: str, parameters: dict[str, Any], **kwargs: Any
    ) -> tuple[ToolResponse, float, dict[str, Any]]:
        task_id, key = self._instances.get(instance_id, (None, None))
        if not task_id:
            raise ValueError(f"{self.name}: no task_id; set tools_kwargs.{self.name}.create_kwargs.task_id "
                             "or use the sandbox_tool_agent loop")
        extra = getattr(kwargs.get("agent_data"), "extra_fields", None)
        if key is None:
            # Plain tool_agent loop: the trajectory's AgentData carries the key. Without one, the
            # instance is the episode (a caller that keeps one instance per trajectory).
            key = extra.setdefault(KEY_FIELD, uuid.uuid4().hex) if extra is not None else instance_id
        elif extra is not None:
            extra[KEY_FIELD] = key
        self._instances[instance_id] = (task_id, key)

        episode = self._episodes.get(key)
        if episode is None:
            if extra is not None and (extra.get(SUMMARY_FIELD) or {}).get("stop_reason"):
                # Released earlier (idle timeout); a new claim would break one sandbox per episode.
                return self._over(extra[SUMMARY_FIELD]["stop_reason"]), 0.0, {}
            episode = self._episodes[key] = _Episode(key=key, task_id=task_id, extra=extra)

        async with episode.lock:
            episode.last_used = time.monotonic()
            if episode.stop_reason:
                return self._over(episode.stop_reason), 0.0, {"turn": len(episode.statuses)}
            code = submitted_code(parameters)
            if episode.sandbox is None:
                try:
                    episode.sandbox = await self._claim()
                except Exception as exc:
                    # Infrastructure, not the policy: logged, and flagged in the reward.
                    log.exception("claiming a sandbox from %s failed", self.warm_pool)
                    episode.final_code = code
                    episode.final_verdict = {"status": "sandbox_error", "error": f"claim: {exc}"}
                    episode.stop_reason = "sandbox_error"
                    episode.publish(require_triton=self.require_triton)
                    return self._over("sandbox_error"), 0.0, {"turn": 0}
                episode.claim, episode.address = episode.sandbox.name, episode.sandbox.address

            verdict = await asyncio.to_thread(episode.sandbox.evaluate, task_id=episode.task_id, code=code)
            turn = len(episode.statuses) + 1
            episode.statuses.append(str(verdict.get("status")))
            episode.single_turn_rewards.append(
                score_verdict(verdict, code, require_triton=self.require_triton)["total"]
            )
            episode.final_code, episode.final_verdict = code, verdict
            episode.stop_reason = stop_reason(
                verdict, turn=turn, max_turns=self.max_turns,
                stop=lambda v: solved(v, require_triton=self.require_triton),
            )
            suffix = f"; episode over: {episode.stop_reason}" if episode.stop_reason else ""
            feedback = format_feedback(verdict, require_triton=self.require_triton,
                                       limit=self.max_feedback_chars - len(suffix)) + suffix
            if episode.stop_reason:
                await self._release(episode)
            episode.publish(require_triton=self.require_triton)
            metrics = {"turn": turn, "status": verdict.get("status"), "claim": episode.claim,
                       "pod": verdict.get("pod"), "stop_reason": episode.stop_reason}
        # No per-turn reward: paying failing turns would reward many cheap attempts.
        return ToolResponse(text=feedback), 0.0, metrics

    async def calc_reward(self, instance_id: str, **kwargs: Any) -> float:
        """Final-submission reward of the instance's episode.

        veRL 0.9.1 never calls this; compute_score reads the same number from extra_info.
        """
        _, key = self._instances.get(instance_id, (None, None))
        episode = self._episodes.get(key or instance_id)
        if episode is None:
            return 0.0
        return float(episode_score(episode.summary(require_triton=self.require_triton))["score"])

    async def release(self, instance_id: str, **kwargs: Any) -> None:
        # Runs after every call; the sandbox belongs to the trajectory and stays claimed. Only an
        # instance that is its own episode (no agent_data) takes the sandbox with it.
        self._instances.pop(instance_id, None)
        if instance_id in self._episodes:
            await self.end_episode(instance_id)

    # --- episode lifecycle ---------------------------------------------------------------
    async def end_episode(self, key: str) -> None:
        """Delete the episode's claim and forget it (the trajectory has ended)."""
        episode = self._episodes.pop(key, None)
        if episode is None:
            return
        async with episode.lock:
            await self._release(episode)

    async def sweep(self) -> None:
        """Release sandboxes of episodes with no call for idle_release_s (abandoned trajectories)."""
        now = time.monotonic()
        idle = [e for e in self._episodes.values()
                if now - e.last_used > self.idle_release_s and not e.lock.locked()]
        for episode in idle:
            async with episode.lock:
                if time.monotonic() - episode.last_used <= self.idle_release_s:
                    continue  # a call came in while this sweep waited for the lock
                self._episodes.pop(episode.key, None)
                if episode.sandbox is not None:
                    episode.stop_reason = episode.stop_reason or "idle_timeout"
                    await self._release(episode)
                    episode.publish(require_triton=self.require_triton)

    def _over(self, reason: str) -> ToolResponse:
        return ToolResponse(text=f"episode over: {reason}; further submissions are not evaluated")

    async def _claim(self) -> EpisodeSandbox:
        if self._api is None:
            from kubernetes import client, config

            config.load_incluster_config()
            self._api = client.CustomObjectsApi()
        if self._loop is None:
            # One loop thread for every episode of this worker; BackgroundLoop threads never stop.
            self._loop = BackgroundLoop()
        sandbox = EpisodeSandbox(
            self.warm_pool, namespace=self.namespace, token_file=self.token_file,
            max_lifetime_s=self.claim_lifetime_s, ready_timeout_s=self.ready_timeout_s,
            labels={"gpusandbox/source": "verl-tool"}, api=self._api, loop=self._loop,
        )
        # EpisodeSandbox blocks while it waits for Ready; keep the rollout event loop free.
        return await asyncio.to_thread(sandbox.__enter__)

    async def _release(self, episode: _Episode) -> None:
        sandbox, episode.sandbox = episode.sandbox, None
        if sandbox is None:
            return
        try:
            await asyncio.to_thread(sandbox.release)
        except Exception:
            # The verdicts stay valid; the claim still expires at its shutdownTime.
            log.exception("deleting claim %s failed; it expires at shutdownTime", sandbox.name)


if HAVE_VERL:
    from verl.experimental.agent_loop.agent_loop import AgentLoopOutput, register
    from verl.experimental.agent_loop.tool_agent_loop import ToolAgentLoop

    class SandboxToolAgentLoop(ToolAgentLoop):
        """ToolAgentLoop that deletes the trajectory's sandbox claim as soon as it ends."""

        async def run(self, sampling_params: dict[str, Any], **kwargs: Any) -> AgentLoopOutput:
            key = uuid.uuid4().hex
            tools = [t for t in self.tools.values() if isinstance(t, KernelSandboxTool)]
            extra_info = kwargs.get("extra_info") or {}
            task_id = extra_info.get("task_id") or (kwargs.get("reward_model") or {}).get("ground_truth")
            kwargs["tools_kwargs"] = with_episode_key(
                kwargs.get("tools_kwargs"), [t.name for t in tools], key, task_id=task_id
            )
            try:
                return await super().run(sampling_params, **kwargs)
            finally:
                for tool in tools:
                    await tool.end_episode(key)

    # hydra instantiates the loop by module name, so register only when this module was imported
    # by name (tool_config_path, pkg://sandbox_tool); a copy loaded from a file path would
    # register a target that cannot be imported.
    # TODO verify on a cluster: this relies on AgentLoopWorker loading the tools (and so this
    # module) before it looks up default_agent_loop, as agent_loop.py v0.9.1 reads.
    if importlib.util.find_spec(__name__) is not None:
        register("sandbox_tool_agent")(SandboxToolAgentLoop)
