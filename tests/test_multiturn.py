"""Multi-turn episodes: one claim per episode, feedback between turns, final-submission reward.

Everything runs without a cluster: a fake CustomObjectsApi hands out Ready claims, and the
sandbox's /v1/evaluate is replaced by the verdict each golden is known to produce. The last test
runs the same episodes against real loopback sandbox servers (CPU harness).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpusandbox import tools
from gpusandbox.agent_sandbox import EpisodeSandbox
from gpusandbox.client.pool import SandboxPool
from gpusandbox.golden import GOLDEN_SET
from gpusandbox.multiturn import (
    FEEDBACK_LIMIT,
    ScriptedPolicy,
    format_feedback,
    run_episode,
    summarize,
)
from gpusandbox.rewards import score_verdict

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = {g.name: g for g in GOLDEN_SET}
BY_CODE = {g.code: g for g in GOLDEN_SET}
POOL = "kernel-eval-gvisor-cpu"


class FakeClaims:
    """CustomObjectsApi stand-in: every claim is Ready at once, each on its own sandbox."""

    def __init__(self, fail_create: Exception | None = None) -> None:
        self.created: list[dict] = []
        self.deleted: list[str] = []
        self.fail_create = fail_create

    def create_namespaced_custom_object(self, group, version, ns, plural, body):
        if self.fail_create:
            raise self.fail_create
        self.created.append(body)

    def get_namespaced_custom_object(self, group, version, ns, plural, name):
        return {"status": {"conditions": [{"type": "Ready", "status": "True"}],
                           "sandbox": {"name": f"sb-{name}",
                                       "serviceFQDN": f"sb-{name}.sandbox.svc.cluster.local"}}}

    def delete_namespaced_custom_object(self, group, version, ns, plural, name):
        self.deleted.append(name)

    @property
    def names(self) -> list[str]:
        return [b["metadata"]["name"] for b in self.created]


def golden_verdict(code: str, host: str) -> dict:
    golden = BY_CODE.get(code)
    status = golden.expect_status if golden else "wrong_answer"
    verdict = {"status": status, "pod": f"pod-{host.split('.')[0]}", "sandbox_version": "v1",
               "flags": [], "violations": [], "error": "", "duration_s": 0.5}
    if status == "ok":
        verdict.update(speedup=1.05, custom_kernel=bool(golden.expect_custom_kernel))
    elif status == "wrong_answer":
        verdict["error"] = "Traceback (most recent call last):\n  ...\nmax abs err 0.51 > atol 1e-05"
    elif status == "policy_violation":
        verdict["violations"] = ["file access is not allowed: open"]
    return verdict


@pytest.fixture
def sandbox_calls(monkeypatch):
    """Replace the HTTP call to the sandbox; record which sandbox answered which task."""
    calls: list[tuple[str, str]] = []

    async def evaluate(self, request):
        host = self.resolver.address.removeprefix("static:")
        calls.append((host, request["task_id"]))
        return golden_verdict(request["code"], host)

    monkeypatch.setattr(SandboxPool, "evaluate", evaluate)
    monkeypatch.setattr(EpisodeSandbox, "info", lambda self: {
        "runtime": "gvisor-cpu", "sandbox_version": "v1", "pod": f"pod-{self.address.split('.')[0]}",
        "kernel_release": "4.4.0", "device": {"name": None}})
    return calls


def _sandbox(api, **kwargs):
    return lambda: EpisodeSandbox(POOL, api=api, **kwargs)


def test_episode_keeps_every_turn_on_one_claimed_sandbox(sandbox_calls):
    api, events = FakeClaims(), []
    result = run_episode(_sandbox(api), ScriptedPolicy("cpu"), episode=1, task_id="relu_bias",
                         max_turns=3, require_triton=False, emit=events.append)

    assert [e["event"] for e in events] == ["episode_start", "turn", "turn", "turn", "episode_end"]
    start, *turns, end = events
    assert api.names == [start["claim"]] and api.deleted == [start["claim"]]
    assert start["warm_pool"] == POOL and start["runtime"] == "gvisor-cpu"
    assert {(t["claim"], t["address"], t["pod"]) for t in turns} == {
        (start["claim"], start["address"], start["pod"])}
    assert {host for host, _ in sandbox_calls} == {start["address"]}
    assert [t["status"] for t in turns] == ["policy_violation", "wrong_answer", "ok"]
    assert all(len(t["feedback"]) <= FEEDBACK_LIMIT for t in turns)
    assert "max abs err 0.51" in turns[1]["feedback"]  # last line of the error, not the traceback

    # The episode is scored by its final submission; turn 1 is what single-turn grading gives.
    final = score_verdict(result.turns[-1].verdict, GOLDEN["relu_bias_torch_only"].code,
                          require_triton=False)
    assert end["reward"] == final["total"] and end["stop_reason"] == "solved" and end["solved"]
    assert end["first_turn_reward"] == turns[0]["single_turn_reward"] == pytest.approx(0.1)
    assert end["reward"] > end["first_turn_reward"]


def test_stop_conditions(sandbox_calls):
    api = FakeClaims()
    single = run_episode(_sandbox(api), ScriptedPolicy("cpu"), episode=1, task_id="relu_bias",
                         max_turns=1, require_triton=False, emit=lambda e: None)
    assert len(single.turns) == 1 and single.stop_reason == "max_turns" and not single.solved
    assert single.reward["total"] == single.turns[0].single_turn_reward

    custom = run_episode(_sandbox(api), ScriptedPolicy("cpu"), episode=2, task_id="relu_bias",
                         max_turns=3, stop_when=lambda v: v["status"] == "wrong_answer",
                         emit=lambda e: None)
    assert [t.verdict["status"] for t in custom.turns] == ["policy_violation", "wrong_answer"]
    assert custom.stop_reason == "solved"
    assert api.deleted == api.names


def test_sandbox_error_ends_the_episode_and_is_excluded(monkeypatch, sandbox_calls):
    async def broken(self, request):
        return {"status": "sandbox_error", "error": "HTTP 403: subject 'x' is not allowed"}

    monkeypatch.setattr(SandboxPool, "evaluate", broken)
    api = FakeClaims()
    result = run_episode(_sandbox(api), ScriptedPolicy("cpu"), episode=1, task_id="relu_bias",
                         max_turns=3, emit=lambda e: None)
    assert len(result.turns) == 1 and result.stop_reason == "sandbox_error"
    assert result.reward["total"] is None
    assert "403" not in result.turns[0].feedback  # infrastructure details are not feedback
    assert api.deleted == api.names


def test_claim_is_released_when_the_policy_fails(sandbox_calls):
    def policy(task_id, turn, history):
        if turn == 2:
            raise RuntimeError("model server went away")
        return GOLDEN["relu_bias_wrong"].code

    api, events = FakeClaims(), []
    with pytest.raises(RuntimeError, match="went away"):
        run_episode(_sandbox(api), policy, episode=1, task_id="relu_bias", max_turns=3,
                    emit=events.append)
    assert len(api.names) == 1 and api.deleted == api.names
    assert events[-1]["event"] == "episode_error" and events[-1]["turns_done"] == 1


def test_scripted_policy_fails_first_then_fixes():
    cpu, cuda = ScriptedPolicy("cpu"), ScriptedPolicy("cuda")
    assert [g.name for g in cpu.script("relu_bias")] == [
        "read_host_file", "relu_bias_wrong", "relu_bias_torch_only"]
    assert cuda.script("relu_bias")[-1].name == "relu_bias_triton"
    assert [g.expect_status for g in cpu.script("relu_bias")] == ["policy_violation", "wrong_answer", "ok"]
    # Past the end of the script the solving submission repeats.
    assert cpu("relu_bias", 5, ()) == GOLDEN["relu_bias_torch_only"].code
    with pytest.raises(ValueError):
        cpu.script("vector_add")  # Triton only, so no CPU script


def test_feedback_is_short_and_actionable():
    long_error = {"status": "runtime_error", "error": "x" * 1000, "flags": ["gpu_fault"]}
    assert len(format_feedback(long_error)) <= FEEDBACK_LIMIT
    assert len(format_feedback(long_error, limit=80)) <= 80
    torch_only = {"status": "ok", "speedup": 0.98, "custom_kernel": False}
    assert "partial credit" in format_feedback(torch_only, require_triton=True)
    assert "partial credit" not in format_feedback(torch_only, require_triton=False)
    assert format_feedback({"status": "policy_violation", "violations": ["no open()"]}) == (
        "status: policy_violation; violation: no open()")


def test_multiturn_cli_gives_every_episode_its_own_sandbox(sandbox_calls, capsys):
    api = FakeClaims()
    assert tools.multiturn(warm_pool=POOL, episodes=2, max_turns=3, device="cpu", task="relu_bias",
                           run_id="episodes-1", api=api) == 0
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert events[0]["event"] == "multiturn" and "not training" in events[0]["note"]
    summary = events[-1]
    assert summary["event"] == "multiturn_summary" and summary["unexpected"] == []
    assert summary["episodes"] == summary["solved"] == summary["claims"] == 2
    assert summary["distinct_sandboxes"] == 2 and summary["one_sandbox_per_episode"]
    assert summary["mean_first_turn_reward"] < summary["mean_reward"]
    assert all(b["metadata"]["labels"]["gpusandbox/run"] == "episodes-1" for b in api.created)
    assert sorted(api.deleted) == sorted(api.names)
    starts = [e for e in events if e["event"] == "episode_start"]
    assert len({s["address"] for s in starts}) == 2


def test_multiturn_cli_fails_on_an_unexpected_verdict(monkeypatch, sandbox_calls, capsys):
    async def always_ok(self, request):
        return {"status": "ok", "speedup": 1.0, "custom_kernel": False, "pod": "p"}

    monkeypatch.setattr(SandboxPool, "evaluate", always_ok)
    assert tools.multiturn(warm_pool=POOL, episodes=1, max_turns=3, device="cpu",
                           task="relu_bias", api=FakeClaims()) == 1
    summary = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert summary["unexpected"][0]["golden"] == "read_host_file"


def test_multiturn_cli_arguments_match_the_episodes_subcommand(monkeypatch):
    """The flags scripts/extensions/agent_sandbox.sh episodes passes are the ones main() accepts."""
    import re
    import shlex

    script = (ROOT / "scripts/extensions/agent_sandbox.sh").read_text().replace("\\\n", " ")
    match = re.search(r'run_job_template (\S+) "\$\{name\}"\s+(multiturn .*?) \|\| status', script)
    template, args = match.group(1), match.group(2)
    assert (ROOT / template).is_file()
    values = {"pool": POOL, "episodes": "2", "max_turns": "3", "device": "cpu", "name": "episodes-1"}
    argv = shlex.split(re.sub(r'"\$\{(\w+)\}"', lambda m: values[m.group(1)], args))

    seen, handlers = {}, {}
    monkeypatch.setattr(tools, "multiturn", lambda **kw: seen.update(kw) or 0)
    monkeypatch.setattr(tools.signal, "signal", lambda sig, fn: handlers.update({sig: fn}))
    assert tools.main(argv) == 0
    assert seen == {"warm_pool": POOL, "episodes": 2, "max_turns": 3, "device": "cpu",
                    "task": "relu_bias", "run_id": "episodes-1"}
    # SIGTERM must unwind through the context managers so that claims are deleted.
    with pytest.raises(SystemExit):
        handlers[tools.signal.SIGTERM](tools.signal.SIGTERM, None)
    with pytest.raises(SystemExit):
        tools.main(["multiturn", "--warm-pool", POOL, "--device", "cpu", "--task", "vector_add"])


def test_summary_reports_mixed_pods():
    from gpusandbox.multiturn import EpisodeResult, Turn

    turns = [Turn(i, "", {"status": "ok", "pod": f"p{i}"}, "", 0.1, 1.0) for i in (1, 2)]
    summary = summarize([EpisodeResult(1, "relu_bias", "c1", "a1", turns, {"total": 1.0}, True, "solved")])
    assert summary["one_sandbox_per_episode"] is False


# --- veRL tool (rl/verl/sandbox_tool.py) without verl -----------------------------------------
def _load_tool_module():
    spec = importlib.util.spec_from_file_location("sandbox_tool_under_test", ROOT / "rl/verl/sandbox_tool.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.HAVE_VERL:
        pytest.skip("covers the module without verl installed")
    return module


def _tool(module, api, **config):
    tool = module.KernelSandboxTool({"type": "native", "warm_pool": POOL, "require_triton": False,
                                     **config})
    tool._api = api
    return tool


async def _call(tool, code, *, agent_data=None, create_kwargs=None):
    """One tool call the way veRL 0.9.1 ToolAgentLoop._call_tool makes it."""
    if create_kwargs is None:
        create_kwargs = {"task_id": "relu_bias"}
    instance_id, _ = await tool.create(create_kwargs=create_kwargs)
    try:
        if agent_data is None:
            return await tool.execute(instance_id, {"code": code})
        return await tool.execute(instance_id, {"code": code}, agent_data=agent_data)
    finally:
        await tool.release(instance_id)


async def test_verl_tool_keeps_a_trajectory_on_one_sandbox_across_calls(sandbox_calls):
    module, api = _load_tool_module(), FakeClaims()
    tool = _tool(module, api)
    trajectory = SimpleNamespace(extra_fields={})
    fenced = f"Fixed the bias.\n```python\n{GOLDEN['relu_bias_wrong'].code}```"
    responses = []
    for code in (GOLDEN["read_host_file"].code, fenced, GOLDEN["relu_bias_torch_only"].code):
        response, step_reward, _ = await _call(tool, code, agent_data=trajectory)
        responses.append(response.text)
        assert step_reward == 0.0  # the episode is paid once, from the final submission
        assert len(response.text) <= tool.max_feedback_chars
    assert [r.split(";")[0] for r in responses] == [
        "status: policy_violation", "status: wrong_answer", "status: ok"]
    assert responses[-1].endswith("episode over: solved")
    assert len(api.names) == 1 and api.deleted == api.names  # released as soon as it was solved
    assert len({host for host, _ in sandbox_calls}) == 1

    summary = trajectory.extra_fields[module.SUMMARY_FIELD]
    assert summary["statuses"] == ["policy_violation", "wrong_answer", "ok"]
    assert summary["first_turn_reward"] == pytest.approx(0.1)
    # veRL hands extra_fields to the reward function inside extra_info.
    score = module.compute_score("gpusandbox/kernels", "", "relu_bias", extra_info=dict(trajectory.extra_fields))
    assert score["score"] == summary["reward"] > score["first_turn_reward"]
    assert score["sandbox_error"] == 0 and score["turns"] == 3

    # A call after the end is answered without the sandbox; another trajectory gets a new one.
    response, _, _ = await _call(tool, GOLDEN["relu_bias_torch_only"].code, agent_data=trajectory)
    assert response.text.startswith("episode over: solved") and len(sandbox_calls) == 3
    await _call(tool, GOLDEN["relu_bias_wrong"].code, agent_data=SimpleNamespace(extra_fields={}))
    assert len(api.names) == 2 and len({host for host, _ in sandbox_calls}) == 2


async def test_verl_tool_releases_abandoned_trajectories(sandbox_calls):
    module, api = _load_tool_module(), FakeClaims()
    tool = _tool(module, api, idle_release_s=600)
    abandoned = SimpleNamespace(extra_fields={})
    await _call(tool, GOLDEN["relu_bias_wrong"].code, agent_data=abandoned)
    assert api.deleted == []  # not solved, turns left: the sandbox stays claimed
    key = abandoned.extra_fields[module.KEY_FIELD]
    tool._episodes[key].last_used -= 3600

    await _call(tool, GOLDEN["relu_bias_wrong"].code, agent_data=SimpleNamespace(extra_fields={}))
    assert api.deleted == [api.names[0]]
    assert abandoned.extra_fields[module.SUMMARY_FIELD]["stop_reason"] == "idle_timeout"
    response, _, _ = await _call(tool, GOLDEN["relu_bias_torch_only"].code, agent_data=abandoned)
    assert response.text.startswith("episode over: idle_timeout") and len(api.names) == 2


async def test_verl_agent_loop_key_and_end_of_trajectory_release(sandbox_calls):
    module, api = _load_tool_module(), FakeClaims()
    row_kwargs = {"submit_kernel": {"create_kwargs": {"task_id": "relu_bias", "extra": 1}}}
    patched = module.with_episode_key(row_kwargs, ["submit_kernel"], "k1", task_id="ignored")
    assert patched["submit_kernel"]["create_kwargs"] == {"task_id": "relu_bias", "extra": 1, "episode_key": "k1"}
    assert "episode_key" not in row_kwargs["submit_kernel"]["create_kwargs"]  # shared row untouched
    filled = module.with_episode_key(None, ["submit_kernel"], "k2", task_id="relu_bias")
    assert filled["submit_kernel"]["create_kwargs"] == {"episode_key": "k2", "task_id": "relu_bias"}

    tool = _tool(module, api)
    trajectory = SimpleNamespace(extra_fields={})
    await _call(tool, GOLDEN["relu_bias_wrong"].code, agent_data=trajectory,
                create_kwargs=filled["submit_kernel"]["create_kwargs"])
    assert trajectory.extra_fields[module.KEY_FIELD] == "k2" and api.deleted == []
    await tool.end_episode("k2")  # what SandboxToolAgentLoop.run does when the trajectory ends
    assert api.deleted == api.names


async def test_verl_tool_without_agent_data_and_on_claim_failure(sandbox_calls):
    module = _load_tool_module()
    api = FakeClaims()
    tool = _tool(module, api)
    await _call(tool, GOLDEN["relu_bias_wrong"].code)  # the instance is the episode
    assert len(api.names) == 1 and api.deleted == api.names

    failing = _tool(module, FakeClaims(fail_create=RuntimeError("forbidden")))
    trajectory = SimpleNamespace(extra_fields={})
    response, _, _ = await _call(failing, GOLDEN["relu_bias_wrong"].code, agent_data=trajectory)
    assert response.text.startswith("episode over: sandbox_error")
    score = module.compute_score("d", "", "relu_bias", extra_info=trajectory.extra_fields)
    assert score["sandbox_error"] == 1 and score["score"] == pytest.approx(0.1)

    with pytest.raises(ValueError, match="task_id"):
        await _call(tool, "x", create_kwargs={})
    # Same keys for every outcome: veRL stacks reward_extra_info key by key.
    assert set(module.compute_score("d", "", "t", extra_info={})) == set(score)


def test_verl_tool_config_matches_the_tool():
    import yaml

    module = _load_tool_module()
    (entry,) = yaml.safe_load((ROOT / "rl/verl/sandbox_tool_config.yaml").read_text())["tools"]
    module_name, class_name = entry["class_name"].rsplit(".", 1)
    assert (ROOT / "rl/verl" / f"{module_name}.py").is_file() and hasattr(module, class_name)
    assert entry["config"]["type"] == "native"
    function = entry["tool_schema"]["function"]
    assert function["name"] == module.TOOL_NAME and function["parameters"]["required"] == ["code"]
    # veRL truncates tool responses at multi_turn.max_tool_response_length (default 256).
    assert entry["config"]["max_feedback_chars"] <= 256
    tool = getattr(module, class_name)(entry["config"])
    assert tool.warm_pool.startswith("kernel-eval-") and tool.max_turns == 3


# --- end to end on loopback sandboxes (real harness, CPU) ---------------------------------------
@pytest.mark.slow
def test_multiturn_against_loopback_sandboxes(sandbox_servers, monkeypatch, capsys):
    """Two episodes, two sandbox servers: real verdicts from the CPU harness for every turn."""
    from gpusandbox import agent_sandbox

    api = FakeClaims()
    addresses: dict[str, str] = {}

    def address_of(claim):
        name = claim["status"]["sandbox"]["name"]
        return addresses.setdefault(name, sandbox_servers[len(addresses) % len(sandbox_servers)])

    monkeypatch.setattr(agent_sandbox, "sandbox_address", address_of)
    assert tools.multiturn(warm_pool=POOL, episodes=2, max_turns=3, device="cpu", task="relu_bias",
                           api=api) == 0
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    turns = [e for e in events if e["event"] == "turn"]
    assert [t["status"] for t in turns] == ["policy_violation", "wrong_answer", "ok"] * 2
    assert {t["pod"] for t in turns if t["episode"] == 1} == {"pod-0"}
    assert {t["pod"] for t in turns if t["episode"] == 2} == {"pod-1"}
    assert events[-1]["distinct_sandboxes"] == 2 and api.deleted == api.names
