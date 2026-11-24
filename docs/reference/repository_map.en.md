# Repository map

Use the [script reference](scripts.md) for commands and [Configuration](configuration.md) for environment variables. This page points to the implementation when you need to change behavior or follow a request.

## Starting points by task

| Task | First file to open |
|---|---|
| Find where the sandbox handles a request | [`server/app.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py) |
| Change correctness checks or timing | [`harness/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/src/gpusandbox/harness) |
| Inspect GRPO rewards and logs | [`rewards.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py), [`rl/trl/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/rl/trl) |
| Inspect gateway scheduling and routing | [`gateway/app.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py), [`client/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/src/gpusandbox/client) |
| Change runtime, pod resources, or grader version | [`k8s/sandbox/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/sandbox) |
| Change AWS nodes or cluster placement | [`cdk/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/cdk), [`infra/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/infra) |
| Inspect episode allocation or the replay demo | [`agent_sandbox.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/agent_sandbox.py), [`demo/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/demo) |

## How values and templates come together

`scripts/06_deploy_sandboxes.sh` reads account settings from `scripts/config.env`, runtime settings from `k8s/sandbox/profiles/`, and grader settings from `k8s/sandbox/versions/`. `scripts/render.py` fills the template, and the script passes the result to `kubectl apply`. `cdk/deploy.sh` reads the same `config.env` to provision the VPC and EKS cluster.

## Following an evaluation request

1. `rl/trl/train_grpo.py` generates answers, and `src/gpusandbox/rewards.py` converts verdicts to rewards. The distributed training entry point is under `rl/verl/`.
2. `src/gpusandbox/client/` reads routing. In production, `src/gpusandbox/gateway/app.py` selects the pool and version.
3. `src/gpusandbox/server/app.py` accepts the evaluation. `harness/evaluate.py` uses a separate `harness/runner.py` process to execute the submission, compares its output with the reference, and returns the verdict.

## Tests

The tests in `tests/` run without AWS. Start with `test_harness_cpu.py` and `test_server_and_client.py` for local evaluation, `test_routing_and_rewards.py` for version switches and rewards, and `test_manifests.py` for deployment templates. CDK stack tests are in `cdk/tests/`.

Guide sources are in `docs/`, and `mkdocs.yml` sets the menu order. Edit the [script reference](scripts.md) and run `python3 tools/sync_scripts_md.py` to refresh the root script reference.

The hands-on sources follow the sidebar. `docs/handson/common/` contains provisioning, runtime setup and pool verification. `scenarios/` holds the A, B and C walkthroughs. The benchmark and multi-turn lab live in `benchmarks/` and `extensions/`.
