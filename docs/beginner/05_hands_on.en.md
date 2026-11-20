# 05 Try scoring on your computer

In this exercise, two local CPU servers grade prepared submissions. The test uses `relu_bias`, a function that adds a bias to each value and clamps negative results to zero. For example, adding `[1, 1]` to `[-3, 2]` gives `[-2, 3]`, so the expected output is `[0, 3]`. No model or AWS account is needed.

![The same prepared answers run on two local CPU servers. pytest checks the verdicts.](../images/figures/beginner-05_hands_on--local-scoring.en.svg)

## 1. Install the tools

With Git and `uv` installed, clone the repository and install the grading server and test dependencies in a Python environment.

```bash
git clone https://github.com/daekeun-ml/gpu-sandbox-on-aws.git
cd gpu-sandbox-on-aws
uv venv --python 3.14
source .venv/bin/activate
uv pip install torch numpy
uv pip install -e ".[dev]"
```

On Linux, add `--index-url https://download.pytorch.org/whl/cpu` to the `uv pip install torch numpy` command to install CPU-only PyTorch.

## 2. Run the scoring test

```bash
python -m pytest -q tests/test_server_and_client.py::test_golden_probe_and_parity_on_cpu_pools
```

`1 passed` means the test got the expected verdicts from both local servers. `ok` means the output matches the reference answer, `wrong_answer` means it differs, and `policy_violation` means the submission was rejected by the execution policy. A deliberately incorrect submission should get `wrong_answer` for the test to pass.

If Python reports `ModuleNotFoundError`, activate `.venv` in the repository root and rerun the installation commands.

??? note "Run the servers directly on macOS"
    On a Linux host, use the pytest route above. See [Getting started](../getting_started.md) for the difference when starting the server directly.

    ### Start two sandbox servers

    Open two terminals, move to the repository folder in each, and run one command in each. The two servers differ only in their port and work directory (`SANDBOX_WORK_ROOT`).

    ```bash
    # Terminal 1
    source .venv/bin/activate
    SANDBOX_DEVICE=cpu SANDBOX_SIZE=smoke SANDBOX_AUTH_TEST_BYPASS=1 \
    SANDBOX_RUNTIME=local SANDBOX_VERSION=v1 \
    SANDBOX_WORK_ROOT=/tmp/gpusandbox/18001 SANDBOX_PORT=18001 \
    gpusandbox-server
    ```

    ```bash
    # Terminal 2
    source .venv/bin/activate
    SANDBOX_DEVICE=cpu SANDBOX_SIZE=smoke SANDBOX_AUTH_TEST_BYPASS=1 \
    SANDBOX_RUNTIME=local SANDBOX_VERSION=v1 \
    SANDBOX_WORK_ROOT=/tmp/gpusandbox/18002 SANDBOX_PORT=18002 \
    gpusandbox-server
    ```

    **What to check:** Each terminal shows `Uvicorn running on http://127.0.0.1:18001` (or `18002`).

    **What is happening now:** One server imitates one sandbox pod of the cluster (open only on `127.0.0.1`). `SANDBOX_AUTH_TEST_BYPASS=1` turns off the token check for this local practice only, so it is never used in a cluster.

    ### Grade the test answers

    In a third terminal, move to the repository folder and send the four test answers (golden) to the two servers.

    ```bash
    source .venv/bin/activate
    python -m gpusandbox.tools probe --address 127.0.0.1:18001,127.0.0.1:18002 --device cpu
    ```

    **What to check:** All four lines should say `PASS` (the speed values differ on every run).

    ```text
    PASS relu_bias_torch_only         status=ok                speedup=0.9474
    PASS relu_bias_wrong              status=wrong_answer      speedup=None
    PASS relu_bias_benchmark_cheat    status=wrong_answer      speedup=None
    PASS read_host_file               status=policy_violation  speedup=None
    ```

    | Answer | What it tests | Expected verdict |
    |---|---|---|
    | `relu_bias_torch_only` | Correct code | `ok` |
    | `relu_bias_wrong` | Wrong code | `wrong_answer` |
    | `relu_bias_benchmark_cheat` | Cheating code that does less work only while time is being measured (the reward hacking from [chapter 04](04_rl_and_sandbox.md)) | `wrong_answer` |
    | `read_host_file` | Code that tries to read a server file (a risk from [chapter 01](01_why_sandbox.md)) | `policy_violation` (rejected before running) |

    **What is happening now:** You check that the grader passes only the correct answer and does not run dangerous code at all. When you are done, stop the servers with `Ctrl-C` in the two server terminals.

## 3. Next exercises

Use the [CPU-only hands-on guide](../handson/10_cpu_only.md) to compare isolation runtimes on AWS. The cluster incurs charges until you remove it. Follow its cleanup steps when finished.

[Chapter 06](06_multi_turn_agent.md) follows what happens when an agent revises and resubmits an answer.
