# 05 Grade locally and compare runtimes on AWS

A deliberately wrong submission comes back and the test says `PASSED`. Is that a success? In this chapter you will **check whether the grader recognizes different kinds of answers** on your own CPU. You can do the local part without an AWS account or GPU.

## Run it on your computer { #1-install-the-tools }

Install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/), then run the commands below. If you already have the project, run just the last line from its directory.

```bash
git clone https://github.com/daekeun-ml/gpu-sandbox-on-aws.git
cd gpu-sandbox-on-aws
./scripts/quickstart.sh local
```

The script prepares the Python environment and starts a test. The test launches two CPU grading servers on your computer, sends prepared answers and shuts the servers down when it finishes. Look for `1 passed` at the end.

![When a wrong submission receives the expected wrong_answer verdict, the check for that submission passes.](../images/figures/beginner-05_hands_on--local-scoring.en.svg?v=3)

??? note "Install the environment by hand or rerun just the test"
    Follow the [local Python setup](../handson/start.md#2-local-python-environment) for your operating system. After installation, the following command reruns the same test from the project directory.

    ```bash
    source .venv/bin/activate
    python -m pytest -q tests/test_server_and_client.py::test_golden_probe_and_parity_on_cpu_pools
    ```

## Why the test passes when an answer is wrong { #2-run-the-scoring-test }

Take the `relu_bias` problem from chapter 03. Adding `[1, 1]` to `[-3, 2]` gives `[-2, 3]`. Setting negative results to zero gives the expected output `[0, 3]`. If a submission skips that last step, the grader should return `wrong_answer`.

| Prepared submission | Expected verdict |
|---|---|
| Computes the right output | `ok` |
| Returns a wrong value | `wrong_answer` |
| Changes its output during timing | `wrong_answer` |
| Attempts a prohibited file access | `policy_violation` (rejected before execution) |

**`wrong_answer` describes the submitted code. `PASSED` describes the test of the grader.** The `1 passed` in the screenshot means the prepared answers received the expected verdicts and the two servers produced consistent results.

![Pytest output showing the local CPU grading test passed](../images/learning/local-cpu-grading.png)

<span id="start-two-sandbox-servers"></span><span id="grade-the-test-answers"></span>

??? note "See a line of output for each answer on macOS"
    Start the servers on separate ports and send the prepared answers with `probe`. You will see lines such as `PASS … status=wrong_answer`. In the main exercise, `pytest` captures this output to check it. [Start the servers manually](../handson/start.md#4-loopback-smoke-run-macos)

## Compare three runtimes on AWS (optional) { #aws-cpu }

This part creates billable AWS resources. Your two local servers use your computer’s operating system. On AWS you can run gVisor and both Kata runtimes on one `c8i.2xlarge` node and check the kernel release seen by each one, as in chapter 02.

<span id="configure-and-create-the-cluster"></span><span id="open-the-tunnel-and-check-the-nodes"></span>

1. Use [step 01, tab C](../handson/common/01_provision/index.md#__tabbed_1_4) to prepare the CPU cluster. The default setup requires 14 free Standard On-Demand vCPUs. Keep the tunnel open in a second terminal and check that the `c8i.2xlarge` node with the `sandbox-kata` role is `Ready`.
2. In [step 02, tab C](../handson/common/02_runtimes/index.md#__tabbed_1_4), run `scripts/kata/cpu_nodes.sh`. It checks the kernel release using `uname -r` in each runtime.

<span id="interpret-the-three-runtime-outputs"></span>

In the screenshot, `gvisor-cpu` reports `4.19.0-gvisor` and the two Kata lines report the same guest release, `6.18.56`. The `host kernel` line is the node’s own kernel. The last `runc` line comes from a separate comparison with an ordinary container. [Interpret the output in chapter 02](02_container_vs_sandbox.md)

![Kernel releases reported by gVisor, Kata and an ordinary container on the same CPU node](../images/learning/aws-runtime-kernels.png)

??? example "Compare with an ordinary runc container on the same node"
    This pod omits `runtimeClassName` and uses the default runtime. Compare `kubectl logs` with the `host kernel` line above.

    ```bash
    cat <<'EOF' | kubectl apply -f -
    apiVersion: v1
    kind: Pod
    metadata: {name: runc-smoke, namespace: default}
    spec:
      restartPolicy: Never
      automountServiceAccountToken: false
      nodeSelector: {gpusandbox/kata-gpu: "false"}
      tolerations: [{key: gpusandbox/role, operator: Equal, value: sandbox-kata, effect: NoSchedule}]
      containers:
        - name: smoke
          image: public.ecr.aws/amazonlinux/amazonlinux:2023
          command: ["/bin/sh", "-c", "echo kernel seen inside: $(uname -r) $(uname -v)"]
    EOF
    kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/runc-smoke --timeout=180s
    kubectl logs runc-smoke
    kubectl delete pod runc-smoke
    ```

### Clean up the AWS resources { #clean-up-the-lab-resources }

To continue with the cluster, proceed to [deploy CPU pools and switch versions](../handson/scenarios/c/index.md). If you finish here, follow the [cleanup instructions](../handson/cleanup.md) for the method you used to deploy.

Next, follow an agent as it receives a wrong-answer verdict and tries the same problem again. [06 How an agent revises an answer](06_multi_turn_agent.md)
