[한국어](README.md) | **English**

# GPU Sandbox on AWS

> [!NOTE]
> **TL;DR** GPU kernels written by the model are scored in isolated GPU sandboxes, and the score is the reward for on-policy RL post-training. This repository holds the code and guidebook that build this setup on Amazon EKS (self-managed EC2) and SageMaker HyperPod with gVisor, Kata + QEMU and Kata + Cloud Hypervisor.

**Guidebook:** https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/ (Korean: https://daekeun-ml.github.io/gpu-sandbox-on-aws/)

If you are new, pick a path that fits your goal and budget in [Choose a learning path](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/learning_paths/) (the free reading and local run paths come first).

**Jump to:** [Architecture](#architecture) | [Scenarios and runtimes](#scenarios-and-runtimes) | [Getting started](#getting-started) | [Key pages of the guidebook](#key-pages-of-the-guidebook) | [Troubleshooting](TROUBLESHOOTING.en.md)

## Architecture

![What you build: the policy model and vLLM on the training node send kernel code, with the version pinned, to the selected sandbox pool (gVisor, Kata + QEMU, or Kata + Cloud Hypervisor as the CPU tier) and get correctness and speedup back as the reward](docs/images/figures/index--what-we-build.en.svg)

*Takeaway: Kernel code from the policy model goes to the sandbox pool of the selected runtime with its version pinned per group, and correctness and speedup come back as the reward. GPU scoring runs on the gVisor and Kata + QEMU pools; Kata + Cloud Hypervisor runs on CPU by default.*

All four scenarios use the same CDK stack (private EKS API, SSM tunnel, KMS key, logs). A, B1 and B2 differ in where the trainer and the sandboxes run; C has no trainer or model and practices scoring and version swaps on CPU sandboxes.

### Scenario A: EC2 GPU (default)

![Scenario A: the private EKS API reached through the SSM tunnel, and a trainer on g5.2xlarge sending kernel code to gVisor pools on two g5.xlarge nodes](docs/images/architecture/scenario-a.drawio.png)

*Takeaway: The trainer and the gVisor pools both run on EC2 nodes of EKS, and the model comes from Hugging Face Hub through the NAT.*

<details>
<summary><b>Scenario B1: training on HyperPod</b></summary>

![Scenario B1: the trainer on a HyperPod instance group and the gVisor pools on EC2 nodes](docs/images/architecture/scenario-b1.drawio.png)

*Takeaway: Only the trainer moves to a HyperPod instance group (ml.g5.2xlarge), booted with lifecycle scripts from S3; the sandboxes stay on the same EC2 gVisor nodes as in A.*

</details>

<details>
<summary><b>Scenario B2: training and sandboxes on HyperPod</b></summary>

![Scenario B2: the trainer and the gVisor pools both on HyperPod instance groups, the sandbox nodes booting from a custom AMI](docs/images/architecture/scenario-b2.drawio.png)

*Takeaway: The sandboxes also move to a HyperPod instance group (ml.g5.xlarge x2), whose nodes boot from a custom AMI baked once (driver 580.178.04). This experimental path has not been run on AWS.*

</details>

<details>
<summary><b>Scenario C: CPU only</b></summary>

![Scenario C: CPU pools of three runtimes on one c8i.2xlarge, no GPU](docs/images/architecture/scenario-c.drawio.png)

*Takeaway: With no GPU node, the pools of three runtimes share one c8i.2xlarge, and a simulate Job on the system nodes sends golden code in place of the trainer.*

</details>

### Request path

- Each time the trainer sends requests to the sandbox, it picks the runtime and version from a snapshot of the routing ConfigMap (`sandbox-routing`), and it takes all results of one reward batch from one pool. If you switch to v2 during training, cached results from the previous pool that fall in the same batch are scored again on the v2 pool. When every completion in a batch is already cached from one pool, the trainer uses those results without calling the sandbox. If the routing switches more than once within one batch, the third request sends the whole batch to one pool, so one batch is always scored by one version.
- The trainer resolves the headless Service through CoreDNS and sends `POST /v1/evaluate` straight to each Ready pod. A busy pod answers `503`, and the trainer retries another pod.
- Each request carries a projected ServiceAccount token with the audience `gpu-sandbox`, which the pod verifies offline against the JWKS. The `sandbox` namespace is default-deny, so only labelled pods from `rl-trainer` can connect.

The production layout (Karpenter NodePools, sandbox gateway, veRL on KubeRay) is in [Production 00 Architecture](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/production/00_architecture/), and node groups, namespaces and a reading of each arrow are in [Hands-on 00 Overview](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/00_overview/). The diagram sources (`.drawio`) are in [`diagrams/`](diagrams/).

## Scenarios and runtimes

| Scenario | Where training runs | Where sandboxes run | When |
|---|---|---|---|
| A. Self-managed EC2 (default) | EC2 GPU node in EKS (`g5.2xlarge`) | EC2 nodes in the same cluster | When you want to control every component yourself |
| B1. HyperPod (HyperPod default) | HyperPod instance group (`ml.g5.2xlarge`) | EC2 nodes in the same EKS cluster that HyperPod is attached to | When long training runs need HyperPod's automatic node replacement and job restart |
| B2. HyperPod (experimental) | HyperPod instance group | gVisor on a HyperPod instance group built from a custom AMI with a replaced driver | When the sandbox nodes also need HyperPod's node recovery (you maintain the custom AMI; not run on AWS) |
| C. c8i only (no GPU) | none (a reward loop without a model) | CPU sandboxes on one `c8i.2xlarge` (gVisor, Kata + CLH, Kata + QEMU) | When you want to learn the runtime comparison and the version swap first, without GPU quota, for about 0.57 USD of compute per hour ([Hands-on 10](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/10_cpu_only/)) |

| Runtime (RuntimeClass) | Isolation boundary | GPU path | Node | Status |
|---|---|---|---|---|
| gVisor (`gvisor`) | User-space kernel (Sentry) | nvproxy forwards to the host driver through an ioctl allowlist per driver version | `g5.xlarge` (A10G) | Default GPU path. Weaker than a VM boundary |
| Kata + QEMU (`kata-qemu-nvidia-gpu`) | VM (KVM) | VFIO GPU passthrough, guest driver | `g4dn.metal` (8 T4, one per VM) | The Kata GPU path upstream supports. T4 is outside upstream CI coverage |
| Kata + Cloud Hypervisor (`kata-clh`) | VM (KVM) | None (CPU tier) | `c8i.2xlarge` (nested virtualization) | CPU sandbox. GPU (`kata-clh-nvidia-gpu`) is not supported upstream; experimental |
| Kata + QEMU CPU (`kata-qemu`) | VM (KVM) | None | `c8i.2xlarge` | CPU sandbox |

There is one sandbox image and one server; a runtime profile (`k8s/sandbox/profiles/`) sets the `RuntimeClass`, the node selector and the GPU request together. How to choose is in the guidebook's [05 Decision guide](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/concepts/05_decision_guide/).

## Getting started

Start with the local tests (no AWS cost), then run the scripts in order. Step-by-step explanations and what to look for are in [Getting started](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/getting_started/) in the guidebook.

### 1. Start with the local tests (no AWS cost)

Install CPU-only PyTorch and the development dependencies, then run the whole local test suite (no AWS account or GPU needed).

```bash
git clone https://github.com/daekeun-ml/gpu-sandbox-on-aws.git
cd gpu-sandbox-on-aws
uv venv --python 3.14
source .venv/bin/activate
# Linux: CPU-only wheels, as in .github/workflows/tests.yml
uv pip install --index-url https://download.pytorch.org/whl/cpu torch numpy
# macOS: the default PyPI wheels have no CUDA, so this is enough instead
# uv pip install torch numpy
uv pip install -e ".[dev]"
python -m pytest -q
```

**What to look for:** the last line shows `109 passed` and no failures. The tests check the AST policy, the two-process harness, token authentication, readiness, the client and the gateway, and the rendering of manifests and node user data on CPU. The 18 CDK stack tests live separately in `cdk/tests`; after installing the CDK libraries, run them with `cd cdk && python -m pytest -q tests`.

> [!WARNING]
> **Starting a server directly on a Linux host:** after every evaluation, the sandbox server sends SIGKILL to every process in `/proc` except itself and its ancestors. Inside a pod this is limited to the container, but `gpusandbox-server` started directly on a Linux host also targets other processes of the same user, so run it in a separate container. pytest turns this behavior off in `tests/conftest.py`, so the commands above are safe on a Linux host as they are ([Getting started](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/getting_started/)).

### 2. Run on AWS (billable)

Pick one scenario and run its commands from top to bottom. If this is your first time, start with **scenario C**. It needs no GPU and takes you from cluster creation to cleanup for about 0.57 USD per hour. What to check at each step is in [Hands-on 00 Overview](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/00_overview/).

#### Common setup (once)

1. Create the configuration file. Every script reads it and stops where a value it needs is empty. If you leave `ADMIN_PRINCIPAL_ARN` empty, the IAM role you are using becomes the cluster admin. If the role ARN has a path, set the full ARN, path included.

    ```bash
    cp scripts/config.env.example scripts/config.env
    ```

2. Set up CDK. Install Node.js 22 or 24 and the Session Manager plugin for the AWS CLI first.

    ```bash
    npm install -g aws-cdk                 # AWS CDK CLI 2.1148.1 or later
    uv pip install -r cdk/requirements.txt # into the activated .venv
    source scripts/config.env              # exports AWS_REGION
    cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"
    ```

3. Three rules apply to the commands below.
    - **Run `source .venv/bin/activate` first in every new work terminal.** The CDK app that creates and deletes the cluster (`02`, `08`) uses the CDK library in the virtualenv.
    - **Keep `cdk/tunnel.sh` running in a second terminal.** The cluster API is private, so kubectl and helm connect only through this tunnel.
    - **Paste the `export` lines that `03_build_push_images.sh` prints at the end into `scripts/config.env`.** Without the image addresses the next steps stop.

#### Scenario C: start without a GPU (recommended)

One `c8i.2xlarge` runs CPU sandboxes for three runtimes (gVisor, Kata + Cloud Hypervisor, Kata + QEMU), and you practice scoring and a version switch without a model. The first command adds a setting to `scripts/config.env` that keeps one pod per pool. Without it, the v2 pool does not fit on the node during the version switch.

```bash
printf '\nexport KATA_CPU_REPLICAS="1"\n' >> scripts/config.env  # one pod per pool, so v2 fits on the node
scripts/01_check_prereqs.sh                        # tools, identity, quotas (read-only)
scripts/02_create_cluster.sh --cpu-only            # VPC, private EKS, nodes (about 20 min)
cdk/tunnel.sh                                      # second terminal, keep it open
scripts/03_build_push_images.sh --no-trainer       # paste the printed export lines into config.env
scripts/kata/cpu_nodes.sh                          # Kata and gVisor runtimes on the c8i node
ACTIVE_RUNTIME=kata-clh-cpu scripts/05_setup_namespaces_auth.sh
for rt in gvisor-cpu kata-clh-cpu kata-qemu-cpu; do
  scripts/06_deploy_sandboxes.sh "${rt}" v1        # one sandbox pool per runtime
  scripts/ops/verify.sh "${rt}" v1                 # isolation, blocked egress, expected verdicts
done
scripts/ops/simulate.sh 30 20                      # reward batches without a model (about 16 min)
scripts/ops/rollout.sh kata-clh-cpu v1 v2          # another terminal, while simulate.sh runs
scripts/08_cleanup.sh                              # delete everything
```

Step-by-step explanations are in [Hands-on 10 c8i-only low-cost path](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/10_cpu_only/).

#### Scenario A: EC2 GPU (default)

The trainer (`g5.2xlarge`) trains with GRPO, and gVisor GPU sandboxes (two `g5.xlarge`) score the rewards. The `Running On-Demand G and VT instances` quota must be at least 16 vCPU.

```bash
scripts/01_check_prereqs.sh                        # tools, identity, quotas (read-only)
scripts/02_create_cluster.sh                       # VPC, private EKS, GPU nodes (20-30 min)
cdk/tunnel.sh                                      # second terminal, keep it open
scripts/03_build_push_images.sh                    # paste the printed export lines into config.env
scripts/04_install_gpu_stack.sh                    # NVIDIA device plugin, gVisor, smoke pod
scripts/05_setup_namespaces_auth.sh                # namespaces, auth, NetworkPolicy, routing
scripts/06_deploy_sandboxes.sh gvisor v1           # gVisor sandbox pool
scripts/ops/verify.sh gvisor v1                    # isolation, blocked egress, expected verdicts
scripts/07_run_grpo.sh                             # GRPO training Job (60 steps by default)
scripts/08_cleanup.sh                              # delete everything
```

To switch the sandbox version during training (`scripts/ops/rollout.sh`), first scale the nodes to 4. The procedure is in [Hands-on 06](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/06_sandbox_update/).

**Adding Kata runtimes (optional):** run these between 04 and 05.

- **Kata CPU:** set `WITH_KATA_CPU` to `"1"` in `scripts/config.env`, run `02_create_cluster.sh` again, then run `scripts/kata/cpu_nodes.sh`.
- **Kata GPU (`g4dn.metal`, about 7.8 USD per hour):** The first run of `scripts/kata/gpu_nodes.sh` builds an AMI and stops. Add the printed `KATA_IOMMU_AMI_ID` line, set `WITH_KATA_GPU` to `"1"`, then run `02_create_cluster.sh` and `scripts/kata/gpu_nodes.sh` again. Details are in [Hands-on 03](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/03_kata/).

#### Scenarios B1 and B2: HyperPod

These paths have not run on AWS yet. Before you run `scripts/hyperpod/create.sh`, fill the HyperPod-only values (such as `HYPERPOD_LCS_BUCKET`) and prepare the training operator prerequisites. Details are in [Hands-on 07](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/07_hyperpod/).

<details>
<summary><b>B1: only the trainer on HyperPod</b></summary>

```bash
scripts/01_check_prereqs.sh
scripts/02_create_cluster.sh --hyperpod            # EKS with the gVisor nodes, no trainer node
cdk/tunnel.sh                                      # second terminal, keep it open
HYPERPOD=1 scripts/03_build_push_images.sh         # paste the printed export lines into config.env
scripts/04_install_gpu_stack.sh
scripts/hyperpod/create.sh                         # HyperPod trainer group (15-30 min)
scripts/05_setup_namespaces_auth.sh
scripts/06_deploy_sandboxes.sh gvisor v1
scripts/ops/verify.sh gvisor v1
scripts/hyperpod/run_grpo.sh                       # instead of 07_run_grpo.sh
scripts/hyperpod/delete.sh                         # delete HyperPod first
scripts/08_cleanup.sh
```

</details>

<details>
<summary><b>B2: trainer and sandboxes on HyperPod (experimental)</b></summary>

```bash
scripts/01_check_prereqs.sh
scripts/02_create_cluster.sh --hyperpod-b2         # EKS with system nodes only
cdk/tunnel.sh                                      # second terminal, keep it open
HYPERPOD=1 scripts/03_build_push_images.sh         # paste the printed export lines into config.env
scripts/04_install_gpu_stack.sh
ACTIVE_RUNTIME=gvisor-hyperpod scripts/05_setup_namespaces_auth.sh
scripts/hyperpod/build_b2_ami.sh                   # custom AMI (20-40 min), paste HYPERPOD_B2_AMI_ID
scripts/hyperpod/create.sh --b2                    # trainer and sandbox groups
scripts/hyperpod/check_gvisor.sh                   # driver and gVisor support per node
scripts/06_deploy_sandboxes.sh gvisor-hyperpod v1
scripts/ops/verify.sh gvisor-hyperpod v1
scripts/hyperpod/run_grpo.sh
scripts/hyperpod/delete.sh                         # delete HyperPod first
scripts/08_cleanup.sh
```

</details>

#### Script folders

| Location | Purpose |
|---|---|
| `scripts/01_*.sh` to `08_*.sh` | The main steps, run in numeric order |
| `scripts/kata/` | Kata runtime setup |
| `scripts/ops/` | Pool checks (`verify.sh`), version switch (`rollout.sh`), scoring loop without a model (`simulate.sh`), benchmark (`bench.sh`) |
| `scripts/hyperpod/` | HyperPod cluster creation, training, deletion |
| `scripts/extensions/` | Agent Sandbox extension |
| `cdk/` | The CDK app that creates the infrastructure (VPC, EKS, node groups) and the tunnel |

<details>
<summary><b>What each script does (expand)</b></summary>

| Script | What it does |
|---|---|
| `scripts/01_check_prereqs.sh` | Checks local tools, the AWS identity, quotas, nested virtualization support and per-AZ availability of the GPU instance types. Read-only; it creates nothing. |
| `scripts/02_create_cluster.sh` | Creates the VPC, the private EKS cluster, the scenario's node groups and the SSM access instance with CDK. No option uses `SCENARIO` from `scripts/config.env` (default A), `--hyperpod` B1, `--hyperpod-b2` B2, `--cpu-only` C. Running it again with changed settings adds or changes node groups. |
| `cdk/tunnel.sh` | The connection you keep open in a second terminal. It forwards `127.0.0.1:8443` on your PC to the private EKS API through SSM port forwarding, and creates the kubectl context `<CLUSTER_NAME>-tunnel`. Keep it running while you use kubectl and helm after the cluster exists. |
| `scripts/03_build_push_images.sh` | Builds the sandbox, trainer and control images for `linux/amd64`, pushes them to ECR, and prints the image addresses as `export` lines. `--no-trainer` skips the trainer; `HYPERPOD=1` adds `hyperpodrun` to the trainer image. |
| `scripts/04_install_gpu_stack.sh` | Installs the NVIDIA device plugin (CDI mode), then registers the `gvisor` RuntimeClass and runs a smoke pod to confirm that GPU work runs inside gVisor. In B2 and C it installs only the device plugin and skips the rest. |
| `scripts/05_setup_namespaces_auth.sh` | Creates the namespaces, NetworkPolicies, ServiceAccounts and the routing ConfigMap, and copies the cluster's token signing public keys (JWKS) into the `sandbox` namespace. `ACTIVE_RUNTIME` sets the first runtime to use. |
| `scripts/06_deploy_sandboxes.sh <runtime> [version] [replicas]` | Deploys one sandbox pool (Deployment and headless Service) and waits until all pods are Ready. |
| `scripts/07_run_grpo.sh [max_steps]` | Submits the GRPO training Job (60 steps by default) and follows its logs. Ctrl-C stops following, not training. |
| `scripts/08_cleanup.sh [--images]` | After you confirm by typing the cluster name, deletes the Jobs, pools and the CDK stack in order. It asks separately about each AMI in the config, and `--images` also deletes the ECR repositories. |
| `cdk/deploy.sh`, `cdk/destroy.sh` | Deploy and delete the CDK stack. `02_create_cluster.sh` and `08_cleanup.sh` call them. |
| `scripts/kata/cpu_nodes.sh` | Installs kata-deploy on the c8i node, registers the `gvisor-cpu` RuntimeClass, and runs smoke pods for the three runtimes (gVisor, Kata + Cloud Hypervisor, Kata + QEMU). |
| `scripts/kata/gpu_nodes.sh` | The first run builds an AMI with the IOMMU on and stops. Once the `g4dn.metal` node exists, the next run installs the GPU Operator and kata-deploy and checks GPU passthrough (`nvidia.com/pgpu`). |
| `scripts/ops/verify.sh <runtime> [version]` | Verifies one pool: it checks that IMDS, the API server and the internet are blocked, that the prepared test code gets the expected results, and that callers from other namespaces are blocked. It also prints the kernel inside the sandbox and the node's kernel; check yourself that they differ (isolation). |
| `scripts/ops/rollout.sh <runtime> <from> <to> [--finish]` | Switches the sandbox version during training (blue/green). It starts the new version, verifies it, checks that it gives the same results as the old one, then switches the routing. After the switch, once a `batch` line on the new version shows verdicts other than `sandbox_error`, run the same command with `--finish` to scale the old version to zero. |
| `scripts/ops/simulate.sh [steps] [interval_s]` | In scenario C, scores prepared test code batch by batch without a model, and shows from which batch the new version is used. It does not train. |
| `scripts/ops/bench.sh [requests]` | Measures cold start, evaluation latency, throughput and speedup for every deployed v1 pool. |
| `scripts/ops/sync_jwks.sh` | Copies the cluster's token signing public keys into the sandbox namespace again. Run it when the API server keys change and you get 401 `unknown signing key`. |
| `scripts/hyperpod/create.sh [--b2]` | Creates the HyperPod cluster (trainer group) and attaches it to the EKS cluster. `--b2` adds the sandbox group. |
| `scripts/hyperpod/build_b2_ami.sh` | Builds the custom AMI for the B2 sandbox group (an NVIDIA driver that gVisor supports, plus gVisor). Run it before `create.sh --b2`. |
| `scripts/hyperpod/check_gvisor.sh` | Starts a debug pod on each HyperPod node and prints its NVIDIA driver version and whether gVisor supports it. At the end it deletes every pod whose name starts with `node-debugger-` in the `default` namespace. |
| `scripts/hyperpod/run_grpo.sh [max_steps]` | In scenario B, runs GRPO training on the HyperPod node instead of `07_run_grpo.sh`. |
| `scripts/hyperpod/delete.sh` | Deletes the HyperPod cluster, its execution role and the lifecycle bucket. Run it before `08_cleanup.sh`. |
| `scripts/extensions/agent_sandbox.sh` | The Agent Sandbox extension. `install` installs the controller and `pool` creates a warm pool. `claim` borrows one sandbox, prints its address and returns it, and `episodes` runs multi-turn episodes without a model. |
| `demo/deploy.sh`, `demo/teardown.sh` | Deploy the demo site to a private S3 bucket behind CloudFront (us-east-1), and remove it. |
| `scripts/logview.py` | Shows the JSON events of Job logs as short colored lines on a terminal. `07_run_grpo.sh`, the check and measurement scripts in `ops/` and `agent_sandbox.sh episodes` go through it. HyperPod's `run_grpo.sh` prints a command for following the logs; run that command yourself. For the raw JSON, put `GPUSANDBOX_LOG=json` in front of the command. |
| `scripts/lib.sh`, `scripts/lib_jobs.sh` | Shared functions that the other scripts load. You do not run them directly. |

</details>

If something fails, check [TROUBLESHOOTING.en.md](TROUBLESHOOTING.en.md) for common problems per step. The full list is in the guidebook's [Troubleshooting](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/).

## Key pages of the guidebook

| Page | Content |
|---|---|
| [Getting started](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/getting_started/) | Local tests, the loopback smoke run, `scripts/config.env`, choosing a path |
| [02 Isolation runtimes](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/concepts/02_isolation_runtimes/) | GPU paths of gVisor and Kata, where each runtime can run on AWS |
| [05 Decision guide](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/concepts/05_decision_guide/) | Choosing runtimes and instances by isolation needs and the GPU you measure on |
| [Hands-on 00 Overview](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/00_overview/) | Script order, the minimal and the full path, hourly cost estimates |
| [Production 00 Architecture](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/production/00_architecture/) | Karpenter NodePools, the sandbox gateway, veRL on KubeRay |
| [04 Reward integrity](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/production/04_reward_integrity/) | The two-process harness, the measurement contract, the response to each public reward hacking case |
| [Misconceptions](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/faq/) | Corrections to beliefs such as "Kata needs .metal" and "it runs on HyperPod nodes" |
| [Verified facts and sources](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/sources/) | Source list and the re-verify checklist before deploying |

## Agent Sandbox extension

This extension lends each multi-turn episode one sandbox that is already running. It uses [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) v1.0.11.

- Sandboxes are started ahead of time for each runtime profile (gvisor, kata-qemu, kata-clh-cpu and others) in a warm pool. An episode takes one when it starts and returns it when it ends (`EpisodeSandbox` in `src/gpusandbox/agent_sandbox.py`).
- A sandbox accepts connections only from labeled trainer pods on port 8000 and blocks every outbound connection. Its DNS server is fixed to 127.0.0.1 so that the controller cannot add a public one.
- Install, warm pool, claim and multi-turn episodes (`episodes`) ran on a scenario C cluster (`kata-clh-cpu`). Use with a GPU runtime is not verified on a cluster yet.
- GPU sandboxes in a warm pool hold their GPU while idle, so they are billed the whole time.

```bash
scripts/extensions/agent_sandbox.sh install                 # controller, CRDs, claim RBAC
scripts/extensions/agent_sandbox.sh pool gvisor-cpu 2       # warm pool of two sandboxes
scripts/extensions/agent_sandbox.sh episodes gvisor-cpu 2 3 # 2 episodes of 3 turns, no model
```

The concepts are in [06 Extending with Agent Sandbox](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/concepts/06_agent_sandbox/), and the steps are in [Hands-on 11 Multi-turn episodes](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/11_multi_turn/).

## Replay demo site

https://dohbsn4kn34ya.cloudfront.net/?lang=en

- A static site that replays, in the browser, run records captured on the cluster. Visitors never reach the cluster or a GPU.
- It shows gVisor and Kata scoring the same code, terminal output of access attempts blocked inside the sandbox, GRPO training and version switch charts, benchmarks and per-scenario architecture flows. A tour video of about two minutes is also there.
- The recordings are in `demo/recordings/`. IP addresses and node names are masked and scanned again before upload.
- The site sits in a private S3 bucket that only CloudFront reads, with AWS WAF and security headers (CSP, HSTS and others).
- To deploy your own, run `demo/deploy.sh`; to remove it, run `demo/teardown.sh`. The procedure is in [09 Demo site (CloudFront)](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/09_demo_site/).

## Validation status

- **Run on AWS:** scenario A (gVisor GPU on `g5`, including the default 60-step training run), scenario C (three CPU runtimes) with a version switch, Kata GPU (`g4dn.metal`), the runtime benchmark on five pools and the public demo site ran in a practice account. The experimental Kata CLH GPU did not start its VM. The measurements are in [08 Runtime benchmark](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/08_benchmark/), and the dated run record is in [Verified facts and sources](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/sources/#aws-run-record).
- **Not run on AWS:** `ops/rollout.sh` during training (scenario A), and HyperPod B1 and B2. Confirm these steps with the checks on each hands-on page.
- **Numbers:** prices and versions come from official documentation and public material, not measurements.

## Cost

GPU instances are billed for as long as they run. The amounts below are estimates that add up only the On-Demand compute prices (us-east-1 and us-west-2, as of 2026-11, so check again before you deploy).

- Scenario C (two system nodes and one `c8i.2xlarge`): about 0.57 USD per hour
- The minimal gVisor path of scenario A: about 3.42 USD per hour
- `g4dn.metal` for Kata GPU: 7.824 USD per hour per node
- Items such as the EKS control plane, the NAT gateway, EBS and ECR are not included above.
- Scale node groups to zero while you take a break, and when you finish, delete everything with `scripts/08_cleanup.sh`.

For example, this scales the Kata GPU nodes to zero:

```bash
aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu \
  --scaling-config minSize=0,maxSize=1,desiredSize=0
```

## Security

- **Private binds:** the sandbox server binds only to `127.0.0.1` by default. Only the pod manifest uses `0.0.0.0`, inside the pod network; Services are headless ClusterIP only, and NetworkPolicy allowlists restrict the callers.
- **Audience-bound tokens:** sandbox pods verify projected ServiceAccount tokens with audience `gpu-sandbox` offline against the cluster issuer's JWKS (public keys), and reject `/v1/evaluate`, `/info` and `/metrics` requests if the authentication settings are empty (fail closed). `/healthz` and `/readyz`, which the kubelet uses, answer without a token, so a Ready pod does not prove that authentication is configured. There are no secrets in the pod and no access to the Kubernetes API. The gateway checks callers with TokenReview and a subject allowlist.
- **No public endpoints:** no cluster service is exposed to the internet; the only public part by design is the demo site, which holds only the recording JSON and static files. The EKS API endpoint is private only, and operators connect through `cdk/tunnel.sh`, which goes through an SSM access instance with no inbound rules.
- **Verified egress denial:** a sandbox turns Ready only after it confirms that IMDS, the API server and the node kubelet are unreachable, and sandbox nodes have an iptables node guard.
- **Local-only settings:** `SANDBOX_AUTH_TEST_BYPASS=1` is for loopback tests only, so do not combine it with a `0.0.0.0` bind. `scripts/config.env` holds account-specific values, so do not commit it (it is in `.gitignore`).

The threat model and the remaining risks are in [02 Security](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/production/02_security/).

## License

Code and documentation are [MIT](LICENSE); model licenses are separate. The default model `Qwen/Qwen2.5-Coder-1.5B-Instruct` and `Qwen/Qwen2.5-Coder-7B-Instruct` in the production examples are Apache-2.0; `Qwen2.5-Coder-3B-Instruct` has a non-commercial license (qwen-research), so this repository does not use it. When you change models or datasets, check each license yourself.

This repository summarizes the author's personal views and research; it does not represent the official documentation or positions of the company the author works for.
