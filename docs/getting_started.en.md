# Getting started

!!! info "TL;DR"
    Check the plumbing on a local CPU machine without AWS first, then fill in `scripts/config.env` and pick a scenario.

## Pain point

If an import error or a missing setting shows up only after the GPU nodes are running, the nodes keep billing while you fix it. Some of the values the scripts read (image URIs, AMI IDs) only exist after an earlier step has finished. EC2 only, HyperPod attached, or the production setup also each runs a different set of scripts.

![a: an import error or a missing setting is found after the GPU nodes start, and GPU node billing continues through the fix and the rerun. b: the plumbing is checked on a local CPU with 109 pytest tests and a 2-step GRPO dry run (no AWS cost), scripts/config.env is filled in (each script stops when a value its step needs is empty or __SET_ME__), a path is picked (A, B1, B2, C, production), and only then do the GPU nodes start billing](images/figures/getting_started.svg)

*Takeaway: (a) starts the GPU nodes first. (b) runs pytest and the dry run on a local CPU, fills in the settings file and picks a path. The AWS nodes start after that, and scenario C runs CPU sandboxes with no GPU node.*


## Why

- **Check the plumbing before paying for AWS.** The sandbox server, the two-process harness, authentication, routing and the reward functions run the same code on CPU.
- **Reproduce what the author verified with the same commands.** The pytest suite and the 2-step GRPO dry run were run and checked on macOS (CPU only), when the suite had 94 tests (it now has 109).
- **Keep settings in one file.** Every script reads `scripts/config.env` through `scripts/lib.sh` and stops right away when a required value is empty or still `__SET_ME__`.

**Before you start:** a terminal, `git` and Python virtual environments are enough, and the local steps (sections 1 to 4) need no Kubernetes or AWS knowledge. The starting point is in [Choose a learning path](learning_paths.md), the overall picture in "What you build" on [Home](index.md), and the reason for GPU sandboxes in [01 When the sandbox needs a GPU](concepts/01_why_gpu_sandbox.md).

??? note "Terms (expand if a word is new to you)"
    - **Sandbox**: an environment that runs untrusted code in isolation. In this asset it is the HTTP server that runs and scores kernel code written by the model.
    - **Harness**: the scoring program that runs candidate code, measures correctness and speed, and returns a verdict.
    - **Golden**: a test submission whose expected verdict is fixed in advance. It checks that the server scores correctly.
    - **Loopback**: an address (`127.0.0.1`) that only your own machine can reach. Other machines cannot connect to it.
    - **Smoke run**: a short run that only checks that the plumbing is connected, before the real run.
    - **GRPO**: an RL algorithm that generates several answers per prompt and reinforces the answers that beat the group average.
    - **Dry run**: a very short run (2 steps here) that checks the wiring instead of training for real.
    - **Reward**: the score RL gives one answer. In this asset it is the weighted sum of format, correctness and speedup.
    - **Quota**: the upper limit on the resources an AWS account can use at the same time. EC2 GPU quotas count vCPUs, not instances.
    - **Fail closed**: rejecting requests, instead of allowing them, when a setting is missing or cannot be verified.

    More detail is in the [Glossary](reference/glossary.md).

## What you need

### Local tools

| Tool | Used for | Notes |
|---|---|---|
| AWS CLI v2 | every AWS step | `aws sts get-caller-identity` must work |
| AWS CDK CLI | creates (`02_create_cluster.sh`) and deletes (`08_cleanup.sh`) the VPC, cluster and node groups | 2.1148.1 or later, `npm install -g aws-cdk` |
| Node.js | runs the CDK CLI | 22 or 24 LTS (versions jsii supports) |
| Session Manager plugin | reaches the private API endpoint through `cdk/tunnel.sh` | the plugin for the AWS CLI. Check with `session-manager-plugin --version` |
| kubectl | deployment and verification | within one minor version of the cluster (1.36) |
| helm | device plugin, kata-deploy (OCI chart), GPU Operator, HyperPod dependency chart | Helm 3 |
| docker (buildx) | builds the three images for `linux/amd64` and pushes them to ECR | on an arm64 workstation, an x86_64 host with 100+ GB of disk is recommended |
| python3 | renders the manifest templates (`scripts/render.py`), runs the CDK app | the CDK app runs in the repository's virtual environment |
| jq | JSON processing | |
| git | clones the HyperPod dependency chart (Scenario B) | |
| uv | local Python environment | local tests only |

`scripts/01_check_prereqs.sh` checks that `aws cdk node kubectl helm docker python3 jq session-manager-plugin` are installed. eksctl cannot create a cluster with only a private endpoint, so it is not used.

### AWS account and quotas

| Quota (vCPU-based) | Needed for the hands-on | Notes |
|---|---|---|
| Running On-Demand G and VT instances | scenario A 16, B1 8, B2 and C 0 | the default can be 0 for new accounts |
| Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances | 6 (system `m6i.large` 2 x 2 + the SSM access instance `t4g.nano` 2) | documented default is 5 |
| `ml.g5.2xlarge for cluster usage` (SageMaker) | 1 (Scenario B) | HyperPod-specific quota |
| `ml.g5.xlarge for cluster usage` (SageMaker) | 2 (Scenario B2) | the B2 `sandbox` instance group (`HYPERPOD_SANDBOX_COUNT`) |

- **G and VT, scenario A**: the 16 is trainer `g5.2xlarge` 8 + gVisor `g5.xlarge` 4 x 2.
- **G and VT, B1**: the trainer moves to HyperPod, so the requirement drops to 8 (the gVisor nodes).
- **G and VT, B2 and C**: they have no EC2 GPU nodes and need no G and VT quota.
- **With Kata GPU**: add `g4dn.metal` 96 to G and VT.
- **Standard, scenario C or with Kata CPU**: add `c8i.2xlarge` 8, for 14.
- **Standard, B2 and Kata GPU**: they need 2 more for the `m6i.large` builder while the custom AMI builds: 8, or 16 together with c8i.
- **B1 and B2**: check the SageMaker quotas above separately.

Quota increases can take time, so request them before creating the cluster.

## 1. Clone the repository

Download the repository and change into its folder.

```bash
git clone https://github.com/daekeun-ml/gpu-sandbox-on-aws.git
cd gpu-sandbox-on-aws
```

**What to look for:** `ls` shows the folders `docs`, `scripts`, `src` and `tests`.

## 2. Local Python environment

Create a virtual environment, install CPU-only PyTorch first, then install this package in editable mode (source changes apply without reinstalling) with the `dev` extra. The order matches the GitHub Actions test workflow.

=== "macOS"

    ```bash
    uv venv --python 3.14
    source .venv/bin/activate
    # macOS: the default PyPI wheels have no CUDA, so this is enough
    uv pip install torch numpy
    uv pip install -e ".[dev]"
    ```

=== "Linux"

    ```bash
    uv venv --python 3.14
    source .venv/bin/activate
    # Linux: CPU-only wheels, as in .github/workflows/tests.yml
    uv pip install --index-url https://download.pytorch.org/whl/cpu torch numpy
    uv pip install -e ".[dev]"
    ```

`.[dev]` contains pytest, FastAPI, uvicorn, httpx, PyJWT, PyYAML and kubernetes. The CI additionally installs the `gateway` extra and `shellcheck-py`, and runs shellcheck on the shell scripts after pytest.

Check the installation.

```bash
python -c "import torch, gpusandbox; print(torch.__version__, torch.cuda.is_available())"
```

**What to look for:** the PyTorch version followed by `False` (expected for a CPU-only install).

## 3. Run the tests

Run the whole test suite of the repository.

```bash
python -m pytest -q
```

**What to look for:** the last line starts with `109 passed` (the duration after it depends on your machine).

- **Breakdown**: the 109 tests are 68 core, 30 [Agent Sandbox extension](concepts/06_agent_sandbox.md) and [multi-turn episode](handson/11_multi_turn.md) and 11 [demo site](handson/09_demo_site.md) tests.
- **Coverage**: the AST policy, the two-process harness on CPU (correct, wrong, crash, timeout, benchmark cheat, monkeypatch), fail-closed authentication, readiness after egress denial is verified, the client, the gateway's per-group version pinning, the operator tools, rendering of the manifest, node user data (`infra/eks/userdata.py`) and Karpenter templates, and the demo site's security properties. Per-file coverage is in [Repository map](reference/repository_map.md#tests).
- **CDK stack tests**: the 18 CDK stack tests live separately in `cdk/tests`; after the CDK preparation in section 5, run them with `cd cdk && python -m pytest -q tests`.

**If it fails:** a `ModuleNotFoundError` usually means the virtual environment is not active or section 2 was skipped; run `source .venv/bin/activate` again and repeat section 2.

!!! warning "Steps that start servers on a Linux host"
    After every evaluation the sandbox server sends SIGKILL to every process in `/proc` except itself and its ancestors ([`procs.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/procs.py)).

    - **Inside a pod**: the scope is limited to the container's PID namespace.
    - **Run directly on a Linux host**: it also hits your other processes (editor, the other server, the trainer), and system processes too when run as root.
    - **On macOS**: there is no `/proc`, so the behavior is off there.

    How to run things safely:

    - **pytest**: an autouse fixture in `tests/conftest.py` turns this behavior off under pytest, so `python -m pytest -q` above is safe on a Linux host as it is.
    - **Steps that start servers directly, such as section 4**: run them in a separate container (separate PID namespace) per server rather than on a Linux host.
    - **If the container has its own network namespace**: the server binds to `127.0.0.1` by default (`SANDBOX_HOST`), so the requests in 4.2 and 4.3 sent from the host do not reach it.
    - **If the container shares the host network**: (for example `docker run --network host`, which still keeps its own PID namespace) it can be reached with the default bind.

    To check only the tests that start no servers, skip `slow`.

    ```bash
    # Skips the tests marked "slow" (harness subprocesses and in-process servers)
    python -m pytest -q -m "not slow"
    ```

    **What to look for:** `91 passed, 18 deselected`.

## 4. Loopback smoke run (macOS)

Instead of two sandbox pods in a cluster, start two CPU sandbox servers on loopback for the golden probe and the GRPO dry run.

### 4.1 Start two sandbox servers

Run one in each of two terminals. The servers differ only in port and work directory.

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

| Variable | Value | Meaning |
|---|---|---|
| `SANDBOX_DEVICE` | `cpu` | run the harness on CPU (default `cuda`) |
| `SANDBOX_SIZE` | `smoke` | small input shapes (default `full`) |
| `SANDBOX_AUTH_TEST_BYPASS` | `1` | turns token verification off. Local loopback only, off by default |
| `SANDBOX_RUNTIME`, `SANDBOX_VERSION` | `local`, `v1` | labels that appear in responses and logs |
| `SANDBOX_WORK_ROOT` | `/tmp/gpusandbox/<port>` | root of the per-request work directories. The default `/work` assumes a container, so change it locally |
| `SANDBOX_PORT` | `18001`, `18002` | default `8000` |

**What to look for:** each terminal shows a startup log like this one (a macOS run; versions and process numbers differ).

```text
WARNING:gpusandbox.auth:authentication TEST BYPASS is enabled; use only on loopback
WARNING:gpusandbox.server:egress self-test disabled (SANDBOX_EGRESS_PROBE_TARGETS is empty)
INFO:gpusandbox.server:device probe ok=True info={'torch': '2.15.0', 'cuda_runtime': None}
INFO:     Uvicorn running on http://127.0.0.1:18001 (Press CTRL+C to quit)
```

Both warnings are expected in a local run. By default the server binds to `127.0.0.1` only (`SANDBOX_HOST`).

??? note "Bind address and access limits in the cluster"
    In the cluster the pod manifest sets `SANDBOX_HOST=0.0.0.0`, and a headless ClusterIP Service (pod addresses through DNS, no virtual IP) plus a NetworkPolicy (a firewall rule between pods) admit the trainer namespace only.

**If it fails:** `address already in use` means another process holds that port; switch to another port (for example `18011`) and match the addresses in 4.2 and 4.3.

!!! warning "The test bypass is for loopback only"
    `SANDBOX_AUTH_TEST_BYPASS=1` turns off token verification for `/v1/evaluate`, `/info` and `/metrics` entirely.

    - **The bypass with `SANDBOX_HOST=0.0.0.0`**: the code does not block combining the two, so do not set both.
    - **In the cluster**: the repository's manifests do not set this variable. Sandbox pods in the cluster verify audience-bound ServiceAccount tokens and reject evaluation, server info and metrics requests (`/v1/evaluate`, `/info`, `/metrics`) with 401 when the authentication settings are missing (fail closed).
    - **`/healthz` and `/readyz`**: they report server state without authentication, so the `/readyz` response below says nothing about the authentication settings.

### 4.2 Check the servers (golden probe)

In a third terminal, check readiness and send the golden probe to both servers. The probe is an operator tool that compares the verdicts of golden submissions with the expected ones.

```bash
source .venv/bin/activate
curl -s http://127.0.0.1:18001/readyz
python -m gpusandbox.tools probe --address 127.0.0.1:18001,127.0.0.1:18002 --device cpu
```

**What to look for:**

- Output similar to the following and exit code 0 (a macOS run).
- The server accepts requests only after the device probe finishes, so run this after both terminals show `Uvicorn running`. Before that the connection is refused and `curl -s` prints nothing.
- The `pod`, `kernel_release` and `speedup` values differ per machine and run.

```text
{"status":"ready"}
{"endpoint": "127.0.0.1:18001", "pod": "842f578ca5a5", "runtime": "local", "version": "v1", "kernel_release": "25.6.0", "gpu": null, "egress_blocked": true}
{"endpoint": "127.0.0.1:18002", "pod": "842f578ca5a5", "runtime": "local", "version": "v1", "kernel_release": "25.6.0", "gpu": null, "egress_blocked": true}
PASS relu_bias_torch_only         status=ok                speedup=0.9474
PASS relu_bias_wrong              status=wrong_answer      speedup=None
PASS relu_bias_benchmark_cheat    status=wrong_answer      speedup=None
PASS read_host_file               status=policy_violation  speedup=None
```

On CPU the goldens that need a Triton kernel are skipped and only these four run.

| Golden | Expected verdict |
|---|---|
| `relu_bias_torch_only` | `ok` |
| `relu_bias_wrong` | `wrong_answer` |
| `relu_bias_benchmark_cheat` | `wrong_answer` (code that turns wrong once the benchmark starts) |
| `read_host_file` | `policy_violation` |

`egress_blocked` is `true` because the self-test target list (`SANDBOX_EGRESS_PROBE_TARGETS`) is empty. In the cluster a pod turns Ready only after verifying that IMDS (the EC2 instance metadata service that hands out node credentials), the API server and the node's kubelet are unreachable.

**If it fails:**

- **If there is a `FAIL` line or a connection error**: first check that both startup logs contain `device probe ok=True`.
- **If it fails in the cluster**: see the "sandbox pools and readiness" section of [Troubleshooting](reference/troubleshooting.md).

### 4.3 TRL GRPO dry run

Install the TRL stack at the trainer image's versions, then run the dry run. It downloads `HuggingFaceTB/SmolLM2-135M-Instruct` from the Hugging Face Hub.

```bash
# Same pins as trainer/Dockerfile (as of 2026-11, re-verify)
uv pip install "trl==1.18.0" "peft==0.21.3" "datasets>=4.7"

SANDBOX_ADDRESS="127.0.0.1:18001,127.0.0.1:18002" SANDBOX_RUNTIME=local \
python rl/trl/train_grpo.py --dry-run \
  --model HuggingFaceTB/SmolLM2-135M-Instruct \
  --output-dir /tmp/grpo-dry-run \
  --allow-torch-only
```

- `--dry-run` runs 2 steps on CPU without vLLM and cuts completions at 32 tokens.
- `--output-dir` must be writable (the default `/outputs/grpo` is a pod path).
- `--allow-torch-only` gives a correctness score of 1.0 to correct answers without a Triton kernel. Without it, a correct PyTorch-only answer gets 0.3. CPU cannot run Triton kernels, so this dry run turns it on.
- Locally, the comma-separated server addresses in `SANDBOX_ADDRESS` are used verbatim. The cluster Job does not set this variable; it reads the current pool's Service address from the routing table (ConfigMap) that `SANDBOX_ROUTING_FILE` points to.
- LoRA trains small adapter matrices instead of all model weights. The trainer uses it by default.

**What to look for:**

- First, `{"event": "routing", "mode": "direct", "runtime": "local", "version": "v1", "address": "127.0.0.1:18001,127.0.0.1:18002"}`.
- Two steps of TRL logs, with values per reward function (`rewards/format_reward` and so on).
- At the end, `{"event": "done", "output": "/tmp/grpo-dry-run/final", "reward_batches": ...}`.

**If it fails:**

- **A model download error**: it is a network or Hugging Face Hub access problem.
- **Errors from training in the cluster**: see the "training" section of [Troubleshooting](reference/troubleshooting.md).

!!! note "`reward_batches` can be 0"
    If the 135M model does not close a code block within 32 tokens, the trainer scores the sample as `no_code` and never calls a sandbox. This step checks the wiring between TRL and the reward functions (routing, function signatures, LoRA, saving); the probe in 4.2 and pytest check the sandbox path.

## 5. Create `scripts/config.env`

Copy the example file to create the settings file.

```bash
cp scripts/config.env.example scripts/config.env
```

**What to look for:** `scripts/config.env` exists. Fill in the "first" values of the table below.

| Variable | When | Value |
|---|---|---|
| `AWS_REGION` | first | default `us-west-2`. Prices in this guide are for us-east-1 and us-west-2 |
| `CLUSTER_NAME` | first | default `gpu-sandbox` |
| `K8S_VERSION` | first | `1.36`, inside EKS standard support (until 2027-08-02) and the versions in the HyperPod EKS AMI release notes |
| `SCENARIO` | first | `A` (default), `B1`, `B2`, `C`. The options of `scripts/02_create_cluster.sh` override it for that run only (see below the table) |
| `ADMIN_PRINCIPAL_ARN` | first (optional) | IAM role or user ARNs (comma-separated) that get the cluster admin access entry |
| `HYPERPOD_LCS_BUCKET` | before Scenario B (required) | a unique name replacing `__SET_ME__`. HyperPod's managed policy expects the `sagemaker-` prefix |
| `SANDBOX_IMAGE_URI`, `TRAINER_IMAGE_URI`, `CONTROL_IMAGE_URI` | after `scripts/03_build_push_images.sh` | paste the `export` lines the script prints |
| `WITH_KATA_CPU` | before adding Kata CPU nodes (`scripts/kata/cpu_nodes.sh`) | set it to `1` and run `02_create_cluster.sh` again to get the `sandbox-kata-cpu` (`c8i.2xlarge`) node group. Scenario C has it from the start |
| `KATA_IOMMU_AMI_ID`, `WITH_KATA_GPU` | after the first run of the Kata GPU node script (`scripts/kata/gpu_nodes.sh`) | the AMI ID is printed by `infra/kata/build-iommu-ami.sh`. Add it with `WITH_KATA_GPU=1` and run `02_create_cluster.sh` again to get the `sandbox-kata-gpu` (`g4dn.metal`) node group |
| Instance types, pinned versions | usually unchanged | `GVISOR_RELEASE=20261109.0`, `KATA_VERSION=4.3.1`, `GPU_OPERATOR_VERSION=v26.7.2`, `NVIDIA_DEVICE_PLUGIN_VERSION=0.20.1` |

- **`K8S_VERSION` and the HyperPod prerequisites page**: that page still says up to 1.35.
- **Options that override `SCENARIO`**: `--hyperpod`, `--hyperpod-b2` and `--cpu-only`. If you deployed with an option, set this value to the deployed scenario, or pass the same option again when you rerun the script to add node groups (`cdk/deploy.sh` stops on a mismatch).
- **If `ADMIN_PRINCIPAL_ARN` is empty**: `cdk/deploy.sh` uses your current role.
- **If the role has a path**: set `ADMIN_PRINCIPAL_ARN` yourself.

!!! note "Good to know"
    - The ECR repositories are created with immutable tags. Change `IMAGE_TAG` when you rebuild images.
    - The Scenario B trainer image needs `hyperpodrun`, so build it with `HYPERPOD=1 scripts/03_build_push_images.sh`.
    - `scripts/config.env` holds account-specific values, so do not commit it.

`scripts/02_create_cluster.sh` creates the infrastructure with the CDK app, so prepare CDK once before the AWS steps. Install the AWS CDK CLI, Node.js and the Session Manager plugin from the tool table, then run the following commands. `cdk bootstrap` creates the S3 bucket and IAM roles that CDK deploys with, once per account and Region.

```bash
# One-time CDK setup (in the activated .venv)
uv pip install -r cdk/requirements.txt
source scripts/config.env              # exports AWS_REGION
cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"
```

**What to look for:** the command ends without errors, and CloudFormation has the bootstrap stack `CDKToolkit`. How to narrow its permissions is in [Production 09 Provisioning with CDK](production/09_cdk.md).

Once the values are in, run the preflight script (read-only).

```bash
scripts/01_check_prereqs.sh
```

**What to look for:** the AWS identity table, tool versions, the G and VT quota, nested virtualization support for `c8i.2xlarge`, and the AZs that offer each GPU instance type, in that order. The script queries every candidate instance type, so check only the nodes your scenario creates:

- **G and VT quota**: the `Running On-Demand G and VT instances` value is at least 16 for scenario A and 8 for B1 (0 for B2 and C). Kata GPU adds 96 in any scenario, and switching the gVisor pool from v1 to v2 needs 8 more for two extra `g5.xlarge` nodes while both versions run
- **Standard quota**: the value is at least 6 (at least 14 for scenario C or with Kata CPU; B2 and Kata GPU build a custom AMI and need 2 more, 8, or 16 together with c8i)
- **If you use c8i (scenario C, Kata CPU)**: the nested virtualization line contains `nested-virtualization`
- **GPU node AZs**: the AZ list next to each GPU instance type you create (`g5.2xlarge` and `g5.xlarge` for A, `g5.xlarge` for B1, `g4dn.metal` for Kata GPU) includes at least one of the two AZs the CDK stack uses (the first two of the region AZ list CDK looks up). The script queries the whole region, so other AZ names alone do not mean the node can be created

**If it fails:**

- **If it stops with a message such as `[error] set CLUSTER_NAME in scripts/config.env`**: fill in that value and run it again.
- **Messages such as `missing tool`**: see the "config and scripts" section of [Troubleshooting](reference/troubleshooting.md).

## 6. Choose your path

| Path | When | First command | Next page |
|---|---|---|---|
| Scenario A (EC2 self-managed) | you want to control every component | `scripts/02_create_cluster.sh` | [Hands-on 00 Overview](handson/00_overview.md) |
| Scenario B1 (HyperPod, default) | a long run needs HyperPod's automatic node replacement and job restarts | `scripts/02_create_cluster.sh --hyperpod`, then `scripts/hyperpod/create.sh` | [07 HyperPod scenario](handson/07_hyperpod.md) |
| Scenario B2 (HyperPod, experimental) | you want the sandbox nodes on a HyperPod instance group too | `scripts/02_create_cluster.sh --hyperpod-b2`, then `scripts/hyperpod/build_b2_ami.sh` | [B2 in 07 HyperPod scenario](handson/07_hyperpod.md#b2). You maintain a custom AMI |
| Scenario C (c8i only, no GPU) | you have no GPU quota yet, or want to learn the runtime comparison and the version swap first for about 0.57 USD per hour | `scripts/02_create_cluster.sh --cpu-only` | [Hands-on 10 CPU-only path on c8i](handson/10_cpu_only.md) |
| Production | you scale out with Karpenter NodePools, the sandbox gateway and veRL | after the hands-on | [Production 00 Architecture](production/00_architecture.md) |

When `02_create_cluster.sh` is done, keep `cdk/tunnel.sh` running in a second terminal. With a private-only EKS API endpoint, every step that uses kubectl or helm reaches the API through this SSM port forwarding (`127.0.0.1:8443`, kubectl context `<CLUSTER_NAME>-tunnel`).

If you have not chosen a runtime and instance types yet, read [05 Decision guide](concepts/05_decision_guide.md) and [04 Platforms and instances](concepts/04_platforms_and_instances.md) first.

## Scope and limits

- The author checked the local steps (sections 1 to 4) on macOS (CPU only) when the suite had 94 tests (it now has 109); server tests on a Linux host were not run.
- The author did not run `scripts/01_check_prereqs.sh` in section 5.
- Of the later steps, the gVisor path of scenario A (`02` to `08`), scenario C, Kata GPU (`g4dn.metal`) and the runtime benchmark ran in a practice account. The dated run record is in [Verified facts and sources](reference/sources.md#aws-run-record).
- `ops/rollout.sh` during training in scenario A and HyperPod B1 and B2 were not run. Verify the steps that were not run with the checks on each hands-on page.
- The dry run shows no training effect; real training runs on a GPU in [05 On-policy GRPO training](handson/05_grpo_training.md).

## Time and cost

- **Local steps (sections 1 to 4):** no AWS cost, and roughly 15 to 30 minutes depending on the PyTorch wheel and model downloads (an estimate, not a measurement).
- **AWS steps:**
    - **Cluster creation**: the CDK deploy of `02_create_cluster.sh` took about 20 minutes in the practice account (scenario C).
    - **When a GPU node group cannot launch (`InsufficientInstanceCapacity`)**: CloudFormation waits about 30 minutes, then rolls back the whole initial create. The workaround order is in the cluster creation section of [01 Cluster and images](handson/01_cluster_and_images.md).
    - **GRPO Job**: the 5-step GRPO Job run in the practice account on 2026-11-18 (`g5.2xlarge`) took about 12 minutes, including the image pull and model download.
    - **Cost**: GPU instances bill while they run, and the scenario A gVisor minimal path costs about 3.42 USD per hour for compute alone (estimate). Hourly estimates per configuration are in [04 Platforms and instances](concepts/04_platforms_and_instances.md).

## Cleanup

Stop both servers with Ctrl-C in their terminals, then remove the local work directories.

```bash
# Stop both servers with Ctrl-C first, then remove the local work directories
rm -rf /tmp/gpusandbox /tmp/grpo-dry-run
```

**What to look for:** no output.

- **For a fresh dry run**: `train_grpo.py` resumes from the latest `checkpoint-*` in its output directory, so delete `/tmp/grpo-dry-run` first.
- **AWS resources**: follow [99 Cleanup](handson/99_cleanup.md).

??? note "References"
    | Topic | Link |
    |---|---|
    | Install AWS CLI v2 | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |
    | EC2 instance type quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
    | AWS CDK v2 Developer Guide, bootstrapping | https://docs.aws.amazon.com/cdk/v2/guide/home.html , https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html |
    | uv | https://github.com/astral-sh/uv |
    | GRPO trainer, example settings | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/trl/train_grpo.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/config.env.example |

    All sources: [this page in All references](reference/references.md#ref-getting-started)
