"""scripts/logview.py: short lines on a terminal, raw JSON everywhere else."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "logview.py"
spec = importlib.util.spec_from_file_location("logview", SCRIPT)
logview = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(logview)

BATCH = {
    "event": "reward_batch", "batch": 22, "runtime": "kata-clh-cpu", "version": "v1",
    "served_versions": {"v1": 3}, "status": {"ok": 1, "wrong_answer": 2},
    "pass_rate": 0.3333, "mean_speedup": 0.9125, "batch_wall_s": 11.882, "ts": 1795149029.6,
}
SWITCH = {"event": "sandbox_version_switch", "from": "kata-clh-cpu/v1", "to": "kata-clh-cpu/v2",
          "routing_revision": 2, "global_step": 23, "ts": 1795149322.0}


def test_piped_output_is_the_raw_input():
    lines = [json.dumps(BATCH), json.dumps(SWITCH), "PASS relu_bias_wrong  status=wrong_answer",
             "{not json", "{'loss': 0.1}", ""]
    text = "\n".join(lines) + "\n"
    out = subprocess.run([sys.executable, str(SCRIPT)], input=text, capture_output=True, text=True, check=True)
    assert out.stdout == text


def test_events_become_short_lines():
    view = logview.View(color=False)
    batch = view.render(json.dumps(BATCH))
    assert "batch  22" in batch and "kata-clh-cpu/v1" in batch
    assert "ok 1" in batch and "wrong_answer 2" in batch and "pass 33%" in batch
    assert "MIXED" not in batch
    assert "SWITCH  kata-clh-cpu/v1 -> kata-clh-cpu/v2" in view.render(json.dumps(SWITCH))
    mixed = view.render(json.dumps({**BATCH, "served_versions": {"v1": 1, "v2": 2}}))
    assert "MIXED VERSIONS" in mixed
    start = view.render(json.dumps({"event": "multiturn", "warm_pool": "kernel-eval-gvisor-cpu", "episodes": 2,
                                    "max_turns": 3, "device": "cpu", "policy": "scripted"}))
    assert "2 episodes of up to 3 turns from kernel-eval-gvisor-cpu" in start
    assert "PARITY FAIL" in view.render(json.dumps({"event": "parity", "baseline": "a", "candidate": "b",
                                                    "passed": False}))


def test_trainer_dicts_pod_info_and_unknown_events():
    view = logview.View(color=False)
    train = view.render("{'loss': 0.0123, 'reward': 0.45, 'epoch': 0.1}")
    assert "train" in train and "loss 0.0123" in train and "reward 0.45" in train
    final = view.render("{'train_runtime': 401.2, 'train_loss': 0.01, 'epoch': 1.0}")
    assert "train done" in final and "train_runtime 401.2" in final
    # Transformers 5 prints floats as formatted strings.
    as_strings = view.render("{'loss': '0.3725', 'reward': '0.1469', 'epoch': '0.05'}")
    assert "loss 0.3725" in as_strings and "reward 0.1469" in as_strings
    pod = view.render(json.dumps({"endpoint": "10.0.0.1:8000", "pod": "p", "runtime": "gvisor-cpu",
                                  "version": "v1", "kernel_release": "4.19.0-gvisor", "gpu": None,
                                  "egress_blocked": False}))
    assert "gvisor-cpu/v1" in pod and "EGRESS OPEN" in pod
    # An event named like a View method still goes to the generic formatter.
    assert view.render(json.dumps({"event": "text", "x": 1})).endswith("text  x 1")


def test_plain_text_passes_through_and_colors_are_optional():
    plain = logview.View(color=False)
    for line in ("plain line", "{not json", "{'a': 1}"):
        assert plain.render(line) == line
    colored = logview.View(color=True)
    assert "\033[" in colored.render("FAIL relu_bias_wrong")
    assert "\033[" in colored.render(json.dumps(BATCH))
    assert "\033[" not in plain.render(json.dumps(BATCH))
