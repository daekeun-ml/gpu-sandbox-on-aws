[한국어](README.md) | **English**

# GPU Sandbox on AWS

**TL;DR** GPU kernels written by the model are scored in isolated GPU sandboxes, and the score is the reward for on-policy RL post-training. This repository holds the code and guidebook that build this setup on Amazon EKS (self-managed EC2) and SageMaker HyperPod with gVisor, Kata + QEMU and Kata + Cloud Hypervisor.

**Guidebook:** https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/ (Korean: https://daekeun-ml.github.io/gpu-sandbox-on-aws/)

If you are new, pick a path that fits your goal and budget in [Choose a learning path](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/learning_paths/) (the free reading and local run paths come first).

**Jump to:** [Architecture](#architecture) | [Scenarios and runtimes](#scenarios-and-runtimes) | [Getting started](#getting-started) | [Key pages of the guidebook](#key-pages-of-the-guidebook)

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

**What to look for:** the last line shows `105 passed` and no failures. The tests check the AST policy, the two-process harness, token authentication, readiness, the client and the gateway, and the rendering of manifests and node user data on CPU. The 18 CDK stack tests live separately in `cdk/tests`; after installing the CDK libraries, run them with `cd cdk && python -m pytest -q tests`.

> [!WARNING]
> **Starting a server directly on a Linux host:** after every evaluation, the sandbox server sends SIGKILL to every process in `/proc` except itself and its ancestors. Inside a pod this is limited to the container, but `gpusandbox-server` started directly on a Linux host also targets other processes of the same user, so run it in a separate container. pytest turns this behavior off in `tests/conftest.py`, so the commands above are safe on a Linux host as they are ([Getting started](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/getting_started/)).

### 2. Run the scripts in numeric order (AWS, billable)

First create the configuration file with `cp scripts/config.env.example scripts/config.env`. You can also pick `SCENARIO` (A, B1, B2, C) with the options of `02_create_cluster.sh`, and if you leave `ADMIN_PRINCIPAL_ARN` empty, the IAM role you are using becomes the cluster admin. If the role ARN has a path, set the full role ARN, path included, yourself. Every script reads this file and stops if a value that its step needs is empty or contains `__SET_ME__`. Fill the HyperPod-only values (such as `HYPERPOD_LCS_BUCKET`) before you start B1 or B2.

The CDK app creates the infrastructure, so set it up once before you run `02_create_cluster.sh`. Install Node.js 22 or 24, the AWS CDK CLI 2.1148.1 or later and the Session Manager plugin for the AWS CLI, add the CDK libraries to the virtual environment, and run bootstrap once per account and Region.

```bash
npm install -g aws-cdk                 # AWS CDK CLI 2.1148.1 or later
uv pip install -r cdk/requirements.txt # into the activated .venv
source scripts/config.env              # exports AWS_REGION
cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"
```

The numbered scripts 01 to 08 are the main order, `scripts/kata/` holds optional steps and `scripts/ops/` holds verification and operations scripts.

| Step | Command | What it does |
|---|---|---|
| 01 | `scripts/01_check_prereqs.sh` | Checks tools (aws, cdk, node, kubectl, helm, docker, python3, jq, session-manager-plugin), AWS identity, the G and VT vCPU quota, nested virtualization support and per-AZ availability of the GPU instance types (read-only) |
| 02 | `scripts/02_create_cluster.sh` | Creates the VPC, EKS (private API endpoint), the node groups of the scenario and an SSM access instance with the CDK stack (`cdk/deploy.sh`) (A by default, B1 with `--hyperpod`, B2 with `--hyperpod-b2`, C with `--cpu-only`). About 20 minutes in the practice account |
| Tunnel | `cdk/tunnel.sh` | SSM port forwarding that you keep running in a second terminal. It connects the private API endpoint to `127.0.0.1:8443` and creates the kubectl context `<CLUSTER_NAME>-tunnel`. Every step that uses kubectl or helm needs it |
| 03 | `scripts/03_build_push_images.sh` | Builds the sandbox, trainer and control images for `linux/amd64` and pushes them to ECR. Paste the `export` lines (image URIs) it prints at the end into `scripts/config.env`, or the next steps stop. For scenarios B1 and B2, run it with `HYPERPOD=1` (adds `hyperpodrun` to the trainer image) |
| 04 | `scripts/04_install_gpu_stack.sh` | Installs the NVIDIA device plugin (CDI mode), then registers the `gvisor` RuntimeClass and runs a GPU smoke pod. In scenario B2 it installs only the device plugin (scenario C does not run this step) |
| Optional | `scripts/kata/cpu_nodes.sh` | kata-deploy, the `gvisor-cpu` RuntimeClass and smoke pods on the Kata CPU node (`c8i.2xlarge`, nested virtualization). The node group exists in scenario C or after you run `02_create_cluster.sh` again with `WITH_KATA_CPU=1` |
| Optional | `scripts/kata/gpu_nodes.sh` | The first run builds the IOMMU AMI and stops. Add `KATA_IOMMU_AMI_ID` and `WITH_KATA_GPU=1`, run `02_create_cluster.sh` again to add `g4dn.metal` (about 7.8 USD per hour), then run it again to install the GPU Operator and kata-deploy |
| 05 | `scripts/05_setup_namespaces_auth.sh` | Namespaces, NetworkPolicies, ServiceAccounts, JWKS, the routing ConfigMap. The routing table's default active runtime is `gvisor`, so run it with `ACTIVE_RUNTIME=gvisor-hyperpod` for B2 and `ACTIVE_RUNTIME=kata-clh-cpu` for C |
| 06 | `scripts/06_deploy_sandboxes.sh gvisor v1` | Deploys a sandbox pool (Deployment + headless Service). The first argument is the runtime profile: B2 uses `gvisor-hyperpod`, C uses `gvisor-cpu`, `kata-clh-cpu` and `kata-qemu-cpu` (`ops/verify.sh` takes the same name). In C, add `export KATA_CPU_REPLICAS="1"` to `scripts/config.env` so that the v2 pool also fits on the one node |
| Ops | `scripts/ops/verify.sh gvisor v1` | Checks isolation evidence, egress denial, golden verdicts and the NetworkPolicy |
| 07 | `scripts/07_run_grpo.sh` | TRL GRPO training Job (60 steps by default). After submitting the Job it keeps following the logs; Ctrl-C stops following, not training |
| Ops | `scripts/ops/simulate.sh` | (Scenario C) A loop that sends reward batches of golden submissions without a model. Not training |
| Ops | `scripts/ops/rollout.sh gvisor v1 v2` | Blue/green switch of the sandbox from v1 to v2 during training. Run it in a terminal other than the one following 07's logs. In the default A, first scale the `sandbox-gvisor` node group to 4 (G and VT quota 24 vCPU, [hands-on 06](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/06_sandbox_update/)). In C, run `scripts/ops/rollout.sh kata-clh-cpu v1 v2` while `ops/simulate.sh` is running |
| Ops | `scripts/ops/bench.sh` | (Optional) Compares cold start, latency and speedup of the deployed v1 pools. To include a runtime you switched, run it before a command such as `scripts/ops/rollout.sh gvisor v1 v2 --finish` scales v1 down |
| 08 | `scripts/08_cleanup.sh` | After you confirm the cluster name, deletes the whole stack with `cdk/destroy.sh`, asks about each AMI, and with `--images` also deletes the ECR repositories (if you created HyperPod, run `scripts/hyperpod/delete.sh` first) |

One CDK app creates the infrastructure (VPC, cluster, node groups), and the scripts under `scripts/` do the in-cluster setup through the tunnel. eksctl cannot create a cluster with only a private endpoint (eksctl documentation), so it is not used. The stack layout and security defaults are in [Production 09 Provisioning with CDK](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/production/09_cdk/).

To start without a GPU, follow scenario C (`--cpu-only`, one `c8i.2xlarge`) in [Hands-on 10](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/10_cpu_only/). For the HyperPod scenario (B1), run `scripts/hyperpod/create.sh` after `scripts/02_create_cluster.sh --hyperpod`, and use `scripts/hyperpod/run_grpo.sh` instead of `07_run_grpo.sh`. B2 (`--hyperpod-b2`) creates only the system nodes in EKS, so before 06 build the custom AMI with `scripts/hyperpod/build_b2_ami.sh` and create the HyperPod nodes with `scripts/hyperpod/create.sh --b2`. Training starts with `scripts/hyperpod/run_grpo.sh`, as in B1. Explanations and checks per step are in [Hands-on 00 Overview](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/00_overview/), and if something fails, see [Troubleshooting](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/).

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

This extension uses [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) v1.0.11 to lend one pre-warmed sandbox to each multi-turn episode. The SandboxTemplate and SandboxWarmPool in `k8s/extensions/agent-sandbox/` wrap this repository's sandbox server for each runtime profile (gvisor, kata-qemu, kata-clh-cpu and others), and `EpisodeSandbox` in `src/gpusandbox/agent_sandbox.py` takes one through a SandboxClaim and returns it when the episode ends. Install and create pools with `scripts/extensions/agent_sandbox.sh install` and `scripts/extensions/agent_sandbox.sh pool <runtime> [n]`.

The template admits ingress only from labeled trainer pods on port 8000, denies all egress (`egress: []`), and sets `dnsPolicy: None` with nameserver 127.0.0.1 explicitly so that the controller cannot inject public resolvers. The unit tests with a fake API pass, but it has not been run on a cluster, and Kata GPU inside a SandboxTemplate is unverified. Warm GPU sandboxes hold their GPU while idle and are billed. Details are in [06 Extending with Agent Sandbox](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/concepts/06_agent_sandbox/).

## Replay demo site

`demo/` is a static replay site (HTML, CSS, JS, no external scripts) that only replays run records, so visitors never reach the cluster or a GPU. It has a clickable architecture diagram, a replay of gVisor and Kata scoring the same code, real terminal output of access attempts being blocked inside the sandbox, GRPO training and version switch charts, benchmark charts, a tour video of about two minutes, and an architecture patterns page that animates each scenario's flows step by step. The data is a recording from `python -m gpusandbox.tools record` and an `extras.json` that `demo/build_extras.py` builds from cluster logs; IP addresses and node names in the logs are masked and scanned again before deployment. The GPU recording published on 2026-11-18 is in `demo/recordings/`.

The site sits in a private S3 bucket with Block Public Access on and is read only by CloudFront through Origin Access Control. The bucket policy allows only the CloudFront service principal with an `AWS:SourceArn` condition and denies non-TLS requests, and responses carry a strict Content-Security-Policy, HSTS, nosniff, `frame-ancestors 'none'` and a referrer policy. AWS WAF (a per-IP rate limit and managed rules) is attached and access logs go to a private log bucket. Deploy with `demo/deploy.sh` (always us-east-1) and remove with `demo/teardown.sh`. With the default `*.cloudfront.net` certificate the viewer TLS policy cannot be raised, so if you need TLSv1.2_2021, use a custom domain and an ACM certificate in us-east-1. The procedure is in [09 Demo site (CloudFront)](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/09_demo_site/).

## Validation status

- **Run on AWS:** on 2026-11-14, in a practice account in us-west-2, the scenario C CDK deploy, adding the Kata CPU node (`kata/cpu_nodes.sh`) with smoke pods on the three runtimes, and the delete. On 2026-11-17, on a scenario C cluster in the same region, `ops/rollout.sh kata-clh-cpu v1 v2` was run, and the model-free reward loop run alongside it (`ops/simulate.sh`, 30 batches) recorded the switch to v2 at batch 8. In the practice account on 2026-11-18, the scenario A gVisor path was also run (us-west-2): the image build, `04_install_gpu_stack.sh`, `05_setup_namespaces_auth.sh`, `06_deploy_sandboxes.sh gvisor v1` with `ops/verify.sh gvisor v1`, a 5-step GRPO run on `g5.2xlarge` and `08_cleanup.sh --images`.
- **Also run on AWS (2026-11-18):** Kata GPU (Kata + QEMU on `g4dn.metal`, T4) and Kata CPU, `ops/bench.sh` on five pools, and the public demo site (CloudFront with WAF). The measurements are in [08 Runtime benchmark](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/08_benchmark/). The experimental Kata CLH GPU was also attempted, but its VM did not start.
- **Not run on AWS:** `ops/rollout.sh` during training (scenario A), `rollout.sh --finish`, the 60-step default training run, and HyperPod B1 and B2. Confirm these steps with the checks on each hands-on page.
- **Numbers:** prices and versions come from official documentation and public material, not measurements.

## Cost

GPU instances are billed while they run. The hands-on minimal gVisor path costs about 3.42 USD per hour for compute alone (an estimate summing On-Demand list prices), and one `g4dn.metal` costs 7.824 USD per hour (us-east-1 and us-west-2 On-Demand, as of 2026-11, re-verify). While you take a break, scale node groups to zero (for example `aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu --scaling-config minSize=0,maxSize=1,desiredSize=0`), and when you finish, run `scripts/08_cleanup.sh`. Items such as the NAT gateway, EBS and ECR are not included in the totals above.

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
