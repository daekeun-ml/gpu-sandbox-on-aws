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
