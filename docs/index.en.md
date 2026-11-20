# GPU Sandbox on AWS

!!! info "TL;DR"
    A hands-on and production guide to on-policy RL post-training in which GPU code written by the model runs in an isolated GPU sandbox to earn its reward, built on Amazon EKS and SageMaker HyperPod with three isolation runtimes.

<div class="grid cards" markdown>

-   :material-sprout:{ .lg .middle } **I am new to this**

    ---

    You have not used sandboxes, isolation runtimes or reinforcement learning before. Pictures first show why they are needed and what they are, then you bring one up yourself following real screenshots.

    [:octicons-arrow-right-24: Start the beginner guide](beginner/index.md)

-   :material-rocket-launch:{ .lg .middle } **I have experience**

    ---

    You have worked with Kubernetes, gVisor or Kata, or GRPO. Pick a path that fits your goal and budget and go straight to the hands-on or the production design.

    [:octicons-arrow-right-24: Choose a learning path](learning_paths.md)

</div>

## Pain point

For RL that scores code by running it (RLVR), a CPU sandbox is usually enough, but **tasks whose reward is itself measured on a GPU** (rewarding "how much faster did the CUDA or Triton kernel get") need a GPU inside the sandbox. Untrusted code from the policy then reaches the GPU driver, and a plain container (runc) shares the host kernel and driver as they are. Firecracker-based sandboxes (E2B and others) have no device door to hand a GPU through, and gVisor and Kata handle GPUs differently, so the AWS instance requirements come first. When the sandbox image or the scoring harness changes during on-policy training that runs for days, versions that mix within one GRPO group break the advantage computation.

![a: two separate problems. In the top row, kernel code from the policy shares the host kernel and GPU driver in a runc container. In the bottom row, changing the image or harness during training mixes v1 and v2 rewards in one GRPO group whatever the runtime, so the advantage goes wrong. b: in the top row, gVisor or Kata, chosen by RuntimeClass, stands between the code and the host kernel; in the bottom row, one version scores each batch (or group), so rewards stay consistent](images/figures/index.svg)

*Takeaway: (a) In a plain container the model's code shares the host kernel and driver. Separately, changing the version during training can mix rewards from two versions in one group, whatever the runtime. (b) gVisor or Kata, chosen by RuntimeClass, sits between the code and the host kernel, and the trainer scores each batch (or group) on a pool of one version.*


## Why

- **Compare three runtimes with the same image and the same API.** One runtime profile sets the `RuntimeClass`, the nodes and the GPU request together to select gVisor (nvproxy), Kata + QEMU (VFIO GPU passthrough) or Kata + Cloud Hypervisor (CPU by default), and tables show why Kata + GPU needs `g4dn.metal`, how far nested virtualization takes Kata without `.metal`, and the custom AMI for HyperPod nodes.
- **Update the sandbox without stopping on-policy training.** Blue/green pools, parity checks with golden submissions, and version pinning per batch (or per group) keep rewards consistent.
- **Reward integrity is covered too.** Of the reward hacking reported around KernelBench, the harness design blocks extra CUDA streams, result caching and lazy tensors, and against "wrong only during the benchmark" it checks the sum and the sum of absolute values of the timed outputs. If both values fall within the tolerance, an output with some wrong elements can still pass.

## Architecture

### What you build

![Left: the policy model + vLLM (GRPO, on-policy, g5.2xlarge or ml.g5.2xlarge) inside training on an EC2 GPU node or a HyperPod node. Right: sandbox pools on EC2 nodes with gVisor + nvproxy (g5.xlarge, A10G), Kata + QEMU (g4dn.metal, T4) and Kata + Cloud Hypervisor (CPU tier on c8i with nested virt, GPU experimental), one image, with a profile per pool setting the RuntimeClass and the nodes. Kernel code goes to the pools with its version pinned per group, and correctness and speedup come back](images/figures/index--what-we-build.svg)

*Takeaway: Kernel code from the policy model goes to the sandbox pool of the selected runtime with its version pinned per group, and correctness and speedup come back as the reward. GPU scoring runs on the gVisor and Kata + QEMU pools; Kata + Cloud Hypervisor runs on CPU by default.*

| Scenario | Where training runs | Where sandboxes run | When |
|---|---|---|---|
| A. Self-managed EC2 (default) | EC2 GPU node in EKS (`g5.2xlarge`) | EC2 nodes in the same cluster | When you want to control every component yourself |
| B1. HyperPod (HyperPod default) | HyperPod instance group (`ml.g5.2xlarge`) | EC2 nodes in the same EKS cluster that HyperPod is attached to | When long training runs need HyperPod's automatic node replacement and job restart |
| B2. HyperPod (experimental) | HyperPod instance group | gVisor on a HyperPod instance group built from a custom AMI with a replaced driver | When the sandbox nodes also need HyperPod's node recovery (you maintain the custom AMI; not run on AWS) |
| C. c8i only (no GPU) | none (a reward loop without a model) | CPU sandboxes on one `c8i.2xlarge` (gVisor, Kata + CLH, Kata + QEMU) | When you want to learn the runtime comparison and the version swap first, without GPU quota, for about 0.57 USD of compute per hour ([Hands-on 10](handson/10_cpu_only.md)) |

### Scenarios on AWS

All four scenarios use the same CDK stack (private EKS API, SSM tunnel, KMS key, logs). A, B1 and B2 differ in where the trainer and the sandboxes run; C has no trainer or model and practices scoring and version swaps on CPU sandboxes.

=== "A: EC2 GPU"

    [![Scenario A: the private EKS API reached through the SSM tunnel, and a trainer on g5.2xlarge sending kernel code to gVisor pools on two g5.xlarge nodes](images/architecture/scenario-a.drawio.png)](images/architecture/scenario-a.drawio.png)

    *Takeaway: The trainer and the gVisor pools both run on EC2 nodes of EKS, and the model comes from Hugging Face Hub through the NAT.*

=== "B1: training on HyperPod"

    [![Scenario B1: the trainer on a HyperPod instance group and the gVisor pools on EC2 nodes](images/architecture/scenario-b1.drawio.png)](images/architecture/scenario-b1.drawio.png)

    *Takeaway: Only the trainer moves to a HyperPod instance group (ml.g5.2xlarge), booted with lifecycle scripts from S3; the sandboxes stay on the same EC2 gVisor nodes as in A.*

=== "B2: training and sandboxes on HyperPod"

    [![Scenario B2: the trainer and the gVisor pools both on HyperPod instance groups, the sandbox nodes booting from a custom AMI](images/architecture/scenario-b2.drawio.png)](images/architecture/scenario-b2.drawio.png)

    *Takeaway: The sandboxes also move to a HyperPod instance group (ml.g5.xlarge x2), whose nodes boot from a custom AMI baked once (driver 580.178.04). This experimental path has not been run on AWS.*

=== "C: CPU only"

    [![Scenario C: CPU pools of three runtimes on one c8i.2xlarge, no GPU](images/architecture/scenario-c.drawio.png)](images/architecture/scenario-c.drawio.png)

    *Takeaway: With no GPU node, the pools of three runtimes share one c8i.2xlarge, and a simulate Job on the system nodes sends golden code in place of the trainer.*

### Request path

- Each time the trainer sends requests to the sandbox, it picks the runtime and version from a snapshot of the routing ConfigMap (`sandbox-routing`), and it takes all results of one reward batch from one pool. If you switch to v2 during training, cached results from the previous pool that fall in the same batch are scored again on the v2 pool. When every completion in a batch is already cached from one pool, the trainer uses those results without calling the sandbox. If the routing switches more than once within one batch, the third request sends the whole batch to one pool, so one batch is always scored by one version.
- The trainer resolves the headless Service through CoreDNS and sends `POST /v1/evaluate` straight to each Ready pod. A busy pod answers `503`, and the trainer retries another pod.
- Each request carries a projected ServiceAccount token with the audience `gpu-sandbox`, which the pod verifies offline against the JWKS. The `sandbox` namespace is default-deny, so only labelled pods from `rl-trainer` can connect.

Node groups, namespaces and a step-by-step reading of each arrow are in [Hands-on 00 Overview](handson/00_overview.md), and the production layout (Karpenter NodePools, sandbox gateway, veRL on KubeRay) is in [Production 00 Architecture](production/00_architecture.md). The diagram sources (`.drawio`) are in `diagrams/` in the repository.

## Getting started

- **Not sure where to begin** → pick a path with a few questions in [Choose a learning path](learning_paths.md) (free paths first).
- **To start the hands-on right away** → the local smoke test in [Getting started](getting_started.md), then [Hands-on 00 Overview](handson/00_overview.md)
- **If the runtime differences are confusing** → the [where each runtime can run on AWS](concepts/02_isolation_runtimes.md#where-each-runtime-can-run-on-aws) table in [02 Isolation runtimes](concepts/02_isolation_runtimes.md)
- **To pick the combination for a customer's situation** → [05 Decision guide](concepts/05_decision_guide.md)
- **If a term is unfamiliar** → [Glossary](reference/glossary.md)

## Tracks

| Track | Purpose | Scope |
|---|---|---|
| [Hands-on (Getting started)](handson/00_overview.md) | See the three runtimes and the on-policy loop for yourself within a day | the CDK stack (private API endpoint) and the SSM tunnel, TRL GRPO (1.5B, LoRA, vLLM colocate), switching the sandbox from v1 to v2 without downtime |
| [Production ready](production/00_architecture.md) | Design and scale a production environment | Karpenter NodePools, sandbox gateway, security threat model, reward integrity, veRL on KubeRay, observability, cost |
| [Agent Sandbox extension](concepts/06_agent_sandbox.md) | A dedicated sandbox per multi-turn episode | SandboxTemplate, SandboxWarmPool and SandboxClaim from kubernetes-sigs/agent-sandbox. gVisor or Kata, chosen by RuntimeClass |
| [Demo site](handson/09_demo_site.md) | Replay an execution record in the browser | Private S3 + CloudFront (OAC, HTTPS, security headers). Visitor requests never reach the cluster or a GPU |

## Validation status

!!! warning "What you need to check yourself"
    Scenario A (gVisor GPU on `g5`), scenario C (three CPU runtimes) with a version switch, Kata GPU (`g4dn.metal`), the runtime benchmark on five pools ([08 Runtime benchmark](handson/08_benchmark.md)) and the public demo site ran in a practice account. The experimental Kata CLH GPU did not start its VM, and `ops/rollout.sh` during training, `rollout.sh --finish` and HyperPod B1 and B2 have not been run yet. The dated run record is in [Verified facts and sources](reference/sources.md#aws-run-record). Confirm the steps that were not run with the checks on each hands-on page. Numbers such as prices and versions come from official documentation and public material, not measurements. What the local tests cover is in [Getting started](getting_started.md).

!!! warning "Cost"
    GPU instances are billed while they run, and `g4dn.metal` costs about 7.8 USD per hour (us-east-1 and us-west-2 On-Demand). Scale the GPU nodes to zero while you take a break, and when you finish the hands-on, make sure to run [99 Cleanup](handson/99_cleanup.md).

!!! note "Values as of 2026-11"
    Prices (On-Demand pricing), versions (gVisor releases, Kata, NVIDIA driver support lists, EKS and HyperPod supported versions), regions and service support in this guide are as of 2026-11. They change often, so re-check them in the official documentation before deploying. The items to check and their links are in [Verified facts and sources](reference/sources.md).

## Disclaimer

This guide summarizes the author's personal views and research. It does not represent the official documentation or positions of the company the author works for. Where it differs from official documentation, the official documentation takes precedence.

## License

Code and documentation are [MIT](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/LICENSE); model licenses are separate. The default model `Qwen/Qwen2.5-Coder-1.5B-Instruct` and `Qwen/Qwen2.5-Coder-7B-Instruct` in the production examples are Apache-2.0; `Qwen2.5-Coder-3B-Instruct` has a non-commercial license, so this asset does not use it.
