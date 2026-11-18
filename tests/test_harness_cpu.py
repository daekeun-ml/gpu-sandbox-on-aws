"""Run the real two-process harness on CPU with smoke-size inputs."""

import pytest

from gpusandbox.harness.evaluate import evaluate
from tests.conftest import (
    BENCHMARK_CHEAT,
    CORRECT_RELU_BIAS,
    CRASHING,
    INFINITE_LOOP,
    MONKEYPATCH,
    SYNTAX_ERROR,
    WRONG_RELU_BIAS,
)

pytestmark = pytest.mark.slow


def _run(tmp_path, code, *, timeout_s=60.0, task="relu_bias"):
    import uuid

    work = tmp_path / uuid.uuid4().hex
    work.mkdir()
    code_path = work / "candidate.py"
    code_path.write_text(code)
    return evaluate(
        task_id=task,
        code_path=code_path,
        workdir=work,
        device="cpu",
        size="smoke",
        n_seeds=2,
        warmup=1,
        iters=4,
        timeout_s=timeout_s,
        allow_cuda_cpp=False,
        max_speedup=0.0,
    )


def test_correct_candidate(tmp_path):
    verdict = _run(tmp_path, CORRECT_RELU_BIAS)
    assert verdict["status"] == "ok", verdict
    assert verdict["correct"] and verdict["speedup"] > 0
    assert verdict["custom_kernel"] is False  # no Triton on CPU


def test_wrong_candidate(tmp_path):
    assert _run(tmp_path, WRONG_RELU_BIAS)["status"] == "wrong_answer"


def test_crash_and_syntax_error(tmp_path):
    assert _run(tmp_path, CRASHING)["status"] == "runtime_error"
    assert _run(tmp_path, SYNTAX_ERROR)["status"] == "policy_violation"


def test_benchmark_cheat_is_caught_by_timed_checksums(tmp_path):
    verdict = _run(tmp_path, BENCHMARK_CHEAT)
    assert verdict["status"] == "wrong_answer", verdict
    assert "timed_output_mismatch" in verdict["flags"]


def test_monkeypatch_is_a_policy_violation(tmp_path):
    verdict = _run(tmp_path, MONKEYPATCH)
    assert verdict["status"] == "policy_violation"


def test_timeout_kills_the_candidate(tmp_path):
    verdict = _run(tmp_path, INFINITE_LOOP, timeout_s=3)
    assert verdict["status"] == "timeout"


@pytest.mark.parametrize("task", ["vector_add", "rms_norm", "layer_norm", "matmul_bias_relu"])
def test_reference_as_candidate_is_correct(tmp_path, task):
    """Every task's own reference, renamed to ModelNew, must pass its own checks."""
    import inspect

    from gpusandbox.tasks import get_task

    spec = get_task(task)
    source = inspect.getsource(spec.module)
    source = source.replace("from gpusandbox.tasks._common import generator, pick\n", "")
    body = source.split("class Model(nn.Module):", 1)[1].split("\ndef get_init_inputs", 1)[0]
    header = "import torch\nfrom torch import nn\nfrom torch.nn import functional as F\n"
    code = header + "class ModelNew(nn.Module):" + body
    verdict = _run(tmp_path, code, task=task)
    assert verdict["status"] == "ok", verdict
