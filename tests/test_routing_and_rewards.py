import importlib.util
import json
import math
import os
import time
from pathlib import Path

import pytest

from gpusandbox.client.routing import RoutingError, RoutingTable
from gpusandbox.rewards import KernelRewards, extract_code, speedup_score


def _write(path, active_version):
    path.write_text(
        json.dumps(
            {
                "active": {"runtime": "gvisor", "version": active_version},
                "pools": {"gvisor": {"v1": "svc-v1:8000", "v2": "svc-v2:8000"}},
            }
        )
    )


def test_routing_table_reloads_and_bumps_revision(tmp_path):
    path = tmp_path / "routing.json"
    _write(path, "v1")
    table = RoutingTable(path, min_reload_interval_s=0)
    first = table.snapshot()
    assert (first.version, first.address, first.revision) == ("v1", "svc-v1:8000", 1)

    _write(path, "v2")
    os.utime(path, (time.time() + 1, time.time() + 1))
    second = table.snapshot()
    assert (second.version, second.address, second.revision) == ("v2", "svc-v2:8000", 2)

    # A torn write keeps the last good table instead of failing the training step.
    path.write_text("{not json")
    assert table.snapshot().version == "v2"


def test_routing_table_errors_on_unknown_pool():
    table = RoutingTable(document={"active": {"runtime": "kata-clh", "version": "v1"}, "pools": {}})
    with pytest.raises(RoutingError):
        table.snapshot()


def test_extract_code_prefers_block_with_model_new():
    text = "```python\nprint(1)\n```\nthen\n```python\nclass ModelNew:\n    pass\n```\n```\nnotes\n```"
    assert extract_code(text).startswith("class ModelNew")
    assert extract_code("no code here") is None


def test_extract_code_skips_blocks_in_other_languages():
    text = (
        "Run it with:\n```bash\npython run.py\n```\n"
        "Output:\n```text\nok\n```\n"
        "```python\nclass ModelNew(nn.Module):\n    pass\n```"
    )
    assert extract_code(text).startswith("class ModelNew")
    assert extract_code("```bash\nls\n```") is None
    assert extract_code("```py\nx = 1\n```") == "x = 1\n"


def test_speedup_score_is_log_scaled_and_capped():
    assert math.isclose(speedup_score(1.0), 0.5)
    assert math.isclose(speedup_score(2.0), 1.0)
    assert math.isclose(speedup_score(0.5), 0.0)
    assert math.isclose(speedup_score(100.0), 1.5)
    assert math.isclose(speedup_score(0.01), 0.0)


class FakeSnapshot:
    def __init__(self, version):
        self.runtime, self.version, self.revision = "gvisor", version, 1


class FakeClient:
    """Returns canned verdicts keyed by the first line of the submitted code."""

    def __init__(self, verdicts):
        self.verdicts = verdicts
        self.calls = 0

    def evaluate_batch_sync(self, items, runtime=None):
        self.calls += 1
        results = []
        for item in items:
            marker = item["code"].splitlines()[0].strip("# ").strip()
            results.append({**self.verdicts[marker], "sandbox_version": "v1"})
        return FakeSnapshot("v1"), results


def _completion(marker):
    return [{"role": "assistant", "content": f"```python\n# {marker}\nimport torch\nfrom torch import nn\nclass ModelNew(nn.Module):\n    def forward(self, x):\n        return x\n```"}]


def test_kernel_rewards_grade_verdicts_and_skip_infra_errors(tmp_path):
    verdicts = {
        "fast": {"status": "ok", "custom_kernel": True, "speedup": 2.0},
        "torchonly": {"status": "ok", "custom_kernel": False, "speedup": 1.0},
        "wrong": {"status": "wrong_answer"},
        "infra": {"status": "sandbox_error"},
    }
    client = FakeClient(verdicts)
    rewards = KernelRewards(client, metrics_file=tmp_path / "m.jsonl")
    markers = ["fast", "torchonly", "wrong", "infra"]
    prompts = [[{"role": "user", "content": "p"}]] * 4
    completions = [_completion(m) for m in markers]
    task_ids = ["relu_bias"] * 4

    fmt = rewards.format_reward(prompts, completions, task_id=task_ids)
    cor = rewards.correctness_reward(prompts, completions, task_id=task_ids)
    spd = rewards.speedup_reward(prompts, completions, task_id=task_ids)

    assert client.calls == 1, "one sandbox round trip must feed all three reward functions"
    assert fmt == [1.0, 1.0, 1.0, None]
    assert cor == [1.0, 0.3, 0.2, None]
    assert spd == [1.0, 0.0, 0.0, None]
    logged = [json.loads(l) for l in (tmp_path / "m.jsonl").read_text().splitlines()]
    assert logged[0]["event"] == "reward_batch" and logged[0]["n"] == 4


class SwitchingClient(FakeClient):
    """Like FakeClient, but the pool that answers can be switched between batches."""

    def __init__(self, verdicts):
        super().__init__(verdicts)
        self.version = "v1"
        self.sent = []

    def evaluate_batch_sync(self, items, runtime=None):
        self.calls += 1
        markers = [item["code"].splitlines()[0].strip("# ").strip() for item in items]
        self.sent.append(markers)
        results = [{**self.verdicts[m], "sandbox_version": self.version} for m in markers]
        return FakeSnapshot(self.version), results


def _score(rewards, markers):
    prompts = [[{"role": "user", "content": "p"}]] * len(markers)
    completions = [_completion(m) for m in markers]
    task_ids = ["relu_bias"] * len(markers)
    return [
        fn(prompts, completions, task_id=task_ids)
        for fn in (rewards.format_reward, rewards.correctness_reward, rewards.speedup_reward)
    ]


def test_a_batch_after_a_version_switch_is_scored_by_the_new_pool_only(tmp_path):
    ok = {"status": "ok", "custom_kernel": True, "speedup": 2.0}
    client = SwitchingClient({"a": ok, "b": ok, "c": ok})
    rewards = KernelRewards(client, metrics_file=tmp_path / "m.jsonl")
    _score(rewards, ["a", "b"])
    client.version = "v2"
    _score(rewards, ["a", "c"])  # "a" was cached from v1

    # "c" goes to v2 first, then the cached v1 verdict for "a" is scored again on v2; the
    # second and third reward functions of each batch reuse the cache.
    assert client.sent == [["a", "b"], ["c"], ["a"]]
    logged = [json.loads(l) for l in (tmp_path / "m.jsonl").read_text().splitlines()]
    last = [r for r in logged if r["event"] == "reward_batch"][-1]
    assert last["version"] == "v2" and last["served_versions"] == {"v2": 2}


def test_cached_verdicts_from_two_pools_are_scored_again_together():
    ok = {"status": "ok", "custom_kernel": True, "speedup": 2.0}
    client = SwitchingClient({"a": ok, "b": ok})
    rewards = KernelRewards(client)
    _score(rewards, ["a"])
    client.version = "v2"
    _score(rewards, ["b"])
    _score(rewards, ["a", "b"])  # both cached, from v1 and v2
    assert client.sent[-1] == ["a", "b"]
    _score(rewards, ["a", "b"])  # now both from v2: no round trip
    assert client.calls == 3


class FlappingClient(SwitchingClient):
    """Answers each call with the next pool in ``versions``: the pool switches mid-batch."""

    def __init__(self, verdicts, versions):
        super().__init__(verdicts)
        self.versions = list(versions)

    def evaluate_batch_sync(self, items, runtime=None):
        self.version = self.versions.pop(0)
        return super().evaluate_batch_sync(items, runtime)


def test_a_batch_stays_on_one_pool_even_if_the_pool_switches_while_it_is_scored():
    ok = {"status": "ok", "custom_kernel": True, "speedup": 2.0}
    client = FlappingClient({"a": ok, "b": ok}, ["v1", "v2", "v3", "v4"])
    rewards = KernelRewards(client)
    _score(rewards, ["a"])  # "a" cached from v1
    # The new answer "b" is scored by v2, the re-score of "a" by v3; the last try sends both.
    _score(rewards, ["a", "b"])
    assert client.sent == [["a"], ["b"], ["a"], ["a", "b"]]
    pools = {rewards._cache[k][0] for k in rewards._cache}
    assert pools == {("gvisor", "v4")}


def test_policy_violations_never_reach_the_sandbox():
    client = FakeClient({})
    rewards = KernelRewards(client)
    bad = [[{"role": "assistant", "content": "```python\nimport os\nclass ModelNew:\n    def forward(self):\n        pass\n```"}]]
    assert rewards.correctness_reward([["p"]], bad, task_id=["relu_bias"]) == [0.0]
    assert client.calls == 0


class FakeGroupedClient:
    """veRL path: canned verdicts keyed by the first line of the submitted code."""

    def __init__(self, verdicts):
        self.verdicts = verdicts

    async def evaluate_grouped(self, item, *, group_key):
        marker = item["code"].splitlines()[0].strip("# ").strip()
        return dict(self.verdicts[marker])


async def test_verl_reward_returns_the_same_keys_for_every_outcome(monkeypatch):
    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("verl_reward_under_test", root / "rl/verl/reward_fn.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    client = FakeGroupedClient({
        "fast": {"status": "ok", "custom_kernel": True, "speedup": 2.0, "sandbox_version": "v1"},
        "infra": {"status": "sandbox_error"},
    })
    monkeypatch.setattr(module, "_get_client", lambda: client)

    def text(completion):
        return completion[0]["content"]

    samples = {
        "no_code": "no code block here",
        "policy_violation": "```python\nimport os\nclass ModelNew:\n    def forward(self):\n        pass\n```",
        "sandbox_error": text(_completion("infra")),
        "ok": text(_completion("fast")),
    }
    infos = [await module.compute_score("gpusandbox/kernels", s, "relu_bias", extra_info={"index": i})
             for i, s in enumerate(samples.values())]
    assert [info["status"] for info in infos] == list(samples)
    assert [info["sandbox_error"] for info in infos] == [0, 0, 1, 0]
    assert infos[3]["score"] > infos[2]["score"] > 0.0 == infos[0]["score"]

    # What veRL 0.9.1 does with reward_extra_info: one column per key of the first sample. A
    # scored sample first must not raise KeyError on a no_code sample later, and a no_code
    # sample first must not drop the columns of the scored samples.
    for batch in (infos, infos[::-1]):
        columns = {key: [info[key] for info in batch] for key in batch[0]}
        assert set(columns) == set(infos[3])
    assert columns["sandbox_version"] == ["v1", "", "", ""]
    assert columns["speedup"] == [2.0, 0.0, 0.0, 0.0]
