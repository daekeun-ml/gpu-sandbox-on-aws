# Decision guide

!!! info "TL;DR"
    If the sandbox needs no GPU, a CPU sandbox is enough; if it does, choose between "VM boundary + T4" (Kata + QEMU on `g4dn.metal`) and "current GPUs + a user-space kernel boundary" (gVisor on G/P family VMs) by your isolation requirement and measurement GPU.

## Pain point

GPU type, isolation strength, operating burden and cost move together, so choosing by one of them gets you stuck on another. You may want a VM boundary and a current GPU such as H100 together, but the only x86 NVIDIA GPU that EC2 lets you pass into a VM is the T4 on `g4dn.metal`. A newly launched managed isolation service looks as if it solves the GPU case too, but at launch it is CPU-only.

![A grid of isolation boundary against measurement GPU. VM boundary with T4 works as Kata + QEMU on g4dn.metal (VFIO); VM boundary with a current GPU (L4, L40S, H100) is not on EC2 (red). User-space kernel boundary with T4 is gVisor on g4dn, unverified in this asset; with a current GPU it is gVisor + nvproxy on G/P family VMs (g5, g6, g6e, p5). AWS managed isolation, Nitro Sandboxes and EKS isolated pods, spans both GPU columns as CPU only at launch with no GPU passthrough (red).](../images/figures/concepts-05_decision_guide.svg)

*Takeaway: Two combinations are ready to use as GPU sandboxes; a VM boundary with a current GPU does not exist on EC2, and Nitro Sandboxes do not support GPUs at launch.*


## Why

- **Decide in question order.** Narrow down by GPU need, preference for managed services, need for a VM boundary, and measurement GPU.

**Before you start:** reading [02 Isolation runtimes](02_isolation_runtimes.md) and [04 Platforms and instances](04_platforms_and_instances.md) first makes the tables easier to read. Unfamiliar terms are in the "Terms" box below and in the [Glossary](../reference/glossary.md).

??? note "Terms (expand if a word is new to you)"
    - **VM boundary**: isolation in which untrusted code runs inside a separate VM built with hardware virtualization. Escaping means breaking the hypervisor.
    - **User-space kernel boundary**: isolation, as in gVisor, in which a user-space program receives the syscalls instead of the host kernel. It is not a VM.
    - **Multi-tenant**: a setup in which the work of different customers or teams shares one pool.
    - **Adversarial code**: code assumed to try deliberately to break the isolation.
    - **Measurement GPU**: the GPU that times the reward. The policy learns kernels that are fast on this GPU.
    - **T4**: an NVIDIA GPU model. On EC2 it comes in `g4dn` instances, and `g4dn.metal` has eight of them. It is the only x86 NVIDIA GPU on EC2 that can be assigned directly to a VM, so using a GPU with Kata fixes the measurement GPU to T4.
    - **Compensating controls**: measures that cover a weaker part of the isolation boundary by other means (an exclusive GPU, egress denial, pod recycling and so on).
    - **Nitro Sandboxes, EKS isolated pods**: managed isolation runtimes AWS launched on 2026-11-09. They do not support GPUs at launch.
    - **AgentCore Code Interpreter**: a managed code execution tool provided by Amazon Bedrock AgentCore.
    - **Warm pool**: a set of sandboxes started before requests arrive, so that taking one is quick.

## Decision tree

![A decision ladder running down the left with six outcomes on the right. If no GPU is needed inside the sandbox and you prefer a managed service: AgentCore Code Interpreter or Nitro Sandboxes, EKS isolated pods (CPU only); otherwise Kata + CLH on c8i (nested virtualization). If a GPU is needed and you prefer a managed GPU sandbox: a third-party service (for example Modal, gVisor-based, out of scope). Otherwise, without a VM boundary requirement: gVisor + nvproxy on G/P family VMs (g5 A10G, g6 L4, g6e L40S, p5 H100). With a VM boundary and T4 acceptable for measurement: Kata + QEMU on g4dn.metal (VM boundary + VFIO); if T4 is not acceptable, EC2 has no VM boundary + current GPU combination, so accept the risk with gVisor + compensating controls or revisit the requirements (red). The three combinations this asset builds are blue.](../images/figures/concepts-05_decision_guide--decision-tree.svg)

*Takeaway: When you need both a GPU and a VM boundary, the only GPU Kata can use on EC2 is the T4 in `g4dn.metal`. If measuring reward timing on a T4 is acceptable, choose Kata; if you must measure on the GPU you deploy to (L4, H100 and so on), EC2 has no matching combination, so either accept the risk with gVisor and compensating controls or revisit the requirements.*


If the deployment GPU is known, choose the same or a similar GPU for measurement, because the policy optimizes for the GPU that measured its reward (the misconception note in [01](01_why_gpu_sandbox.md)).

## Choices by situation

| Situation | Choose | Reasoning | What you accept |
|---|---|---|---|
| Running code and taking measurements inside the sandbox need no GPU, and you want to run it yourself | Kata + CLH on `c8i` (nested virtualization) | VM boundary, no `.metal` needed, a combination supported upstream | AWS recommends bare metal for performance-sensitive virtualization workloads. `c8i.2xlarge` is 0.37484 USD per hour |
| You want a managed CPU sandbox | AWS Nitro Sandboxes, EKS isolated pods, or AgentCore Code Interpreter | you do not operate the runtime | Nitro Sandboxes launched on 2026-11-09, needs Kubernetes 1.36 or later, no GPU passthrough. The AgentCore Code Interpreter documentation describes a containerized environment and does not mention GPUs |
| Adversarial code from different customers is scored on GPUs and T4 measurements are acceptable | Kata + QEMU on `g4dn.metal` | VM + IOMMU boundary, the Kata GPU path supported upstream | T4 is unverified upstream (NVIDIA CI covers A100, H100). 7.824 USD/hour, up to 8 VMs with one T4 each |
| The deployment GPU is L4, L40S or H100, so timing must be measured on that GPU | gVisor + nvproxy on `g6`, `g6e`, `p5` | nvproxy documents T4, A100/A10G, L4 and H100. L40S shares L4's architecture, so per the documentation it "will likely work" | the host driver must match the nvproxy support list exactly. Isolation on the GPU driver path is weaker than a VM boundary |
| Adversarial code and a current GPU are both required | gVisor + compensating controls (one GPU per pod, no time-sharing, Ready after egress denial is verified, node guard, pod recycling) and a written risk acceptance | the only x86 NVIDIA GPU EC2 lets you pass into a VM is the T4 | residual risk remains: driver vulnerabilities and unvalidated DMA buffers |
| Multi-turn agent training needs a clean sandbox per episode | [Agent Sandbox extension](06_agent_sandbox.md): claim a sandbox per episode from a warm pool and release it at the end | it keeps using the RuntimeClass, so it applies to gVisor and Kata alike | warm GPU sandboxes hold their GPU while idle. The Kata GPU template is unverified. Not run on a cluster |
| You want to train on HyperPod | B1: the trainer on HyperPod, the sandboxes on EC2 in the same EKS cluster | gVisor does not know the HyperPod AMI driver 595.91.07, and HyperPod has no `.metal` | To have HyperPod recover the sandbox nodes too, B2 (experimental): a `sandbox` instance group from a custom AMI with a replaced driver |
| You want a managed GPU sandbox | evaluate third-party services (out of scope for this asset) | Modal documentation: "GPU Sandboxes are only supported with `runtime="gvisor"`". Public material says Northflank uses Kata for GPUs and falls back to gVisor where nested virtualization is unavailable (original source URL not confirmed) | check each service's isolation method, GPU types and Regions yourself |
| You want GPUs with Cloud Hypervisor | only as an evaluation experiment (`infra/kata/experimental-clh-gpu/`) | not supported upstream, no CI | use `kata-qemu-nvidia-gpu` for anything that matters |

## Customer examples

| Customer situation | Combination | Reason |
|---|---|---|
| An in-house research team trains Triton kernels for L4 serving with its own model | gVisor on `g6.xlarge` (a supported alternative in this asset; the default is `g5.xlarge`) | a pool used by one team does not require a VM boundary, and the measurement GPU can match the deployment GPU (L4) |
| Training jobs of several customers use the same GPU nodes, and rankings on T4 are good enough | Kata + QEMU on `g4dn.metal`, one pool per customer | customers are separated by a VM boundary only when each has its own pool and its requests go to that pool (list below the table). T4 measurement is accepted |
| Kernels for H100 serving are trained in a pool shared by several customers | gVisor on `p5` + compensating controls, consider separate nodes per customer, a written risk acceptance | EC2 has no VM boundary + H100 combination |
| Code RL scored by unit tests | Kata + CLH on `c8i` or a managed CPU sandbox | the GPU is not on the reward path |
| You want to separate the nvcc compile stage from the measurement stage | CPU tier (Kata + CLH on `c8i`) + GPU tier (gVisor or Kata + QEMU) | compilation and static checks do not spend GPU time |

- **Why the second example needs one pool per customer**: Kata creates a VM per pod, but the pool picks an idle pod for each request, so in one shared pool requests from several customers use the same VM in turn.

The second and third examples are the same multi-tenant situation with different measurement GPU requirements, and that difference decides whether a VM boundary is available.

## Comparison table

| Item | gVisor + nvproxy | Kata + QEMU (GPU) | Kata + CLH (CPU) | Kata + CLH (GPU, experimental) | Nitro Sandboxes, EKS isolated pods |
|---|---|---|---|---|---|
| Isolation boundary | user-space kernel. The GPU goes through an ioctl allowlist, weaker than a VM | VM + IOMMU | VM | VM + IOMMU (unverified upstream) | managed by AWS (see the documentation for details) |
| GPUs available on AWS | G/P family VMs. This asset uses A10G (`g5`, default) and L4 (`g6`, alternative) | T4 (`g4dn.metal`) only | none | T4 (`g4dn.metal`) | none (at launch) |
| Installation effort | medium: runsc via user data, containerd handler, RuntimeClass, device plugin `cdi-cri` | high: IOMMU AMI bake, GPU Operator, kata-deploy, `.metal` node | medium: nested-virtualization launch template, kata-deploy | high: the QEMU path plus experimental values. In this repository's run the VM did not start | low: Kubernetes 1.36 or later |
| Density (this asset's setup) | one per `g5.xlarge` node | up to 8 VMs per `g4dn.metal`, all guest RAM pinned | 1.25 CPU per pod (request 1 + overhead 250m) and 2 GiB + 130Mi of memory; whichever of the node's allocatable CPU and memory runs out first sets the limit | shares the node with `kata-qemu` | see the documentation |
| Upstream support | supported (nvproxy documentation) | supported (NVIDIA CI covers A100, H100) | supported | not supported | supported by AWS (launched 2026-11-09) |
| Driver coupling | the host driver version must match the nvproxy support list exactly | guest driver (kata-deploy, open 615.71.09). The host loads no driver | none | guest driver | none |
| On-Demand per GPU per hour | 1.006 (A10G, `g5.xlarge`) | about 0.978 (7.824 / 8, with all eight in use) | n/a | about 0.978 | n/a |

- **Values for Kata + CLH (GPU, experimental)**: the 4.3.1 values already hold the guest kernel and image paths; check the paths for other versions.

Prices are computed from us-east-1 and us-west-2 list prices. With fewer T4s in use, the cost per GPU on `g4dn.metal` goes up.

## What to check right after choosing

How to run the scripts and sample output are on the matching hands-on page.

- **gVisor combination**: `04_install_gpu_stack.sh` and `scripts/ops/verify.sh gvisor v1` ran on `g5.xlarge` in the practice account.
- **Kata + QEMU (GPU)**: it ran on `g4dn.metal`, where `scripts/ops/verify.sh kata-qemu v1` confirmed the T4 and the golden verdicts ([run record](../reference/sources.md#aws-run-record)). NVIDIA's upstream CI covers A100 and H100.

Verify them against the expected results.

| Combination | Check script | Expected result | Hands-on |
|---|---|---|---|
| gVisor | `scripts/04_install_gpu_stack.sh` | `dmesg` inside the smoke pod shows the gVisor Sentry instead of the host kernel, and torch sees the GPU and runs a kernel (`cuda ok:` followed by the GPU name and `2048.0`; on the default `g5.xlarge`, `cuda ok: NVIDIA A10G 2048.0`) | [02 gVisor](../handson/02_gvisor.md) |
| Kata CPU (`kata-clh`, `kata-qemu`) | `scripts/kata/cpu_nodes.sh` | both runtime classes exist, and the guest kernel version printed by the smoke pods differs from the host kernel version the script prints | [03 Kata](../handson/03_kata.md) |
| Kata + QEMU (GPU) | `scripts/kata/gpu_nodes.sh` | the node's allocatable `nvidia.com/pgpu` is above 0 and the `kata-qemu-nvidia-gpu` runtime class exists | [03 Kata](../handson/03_kata.md) |
| Deployment pool | `scripts/ops/verify.sh <runtime> [version]` | isolation evidence per pod, IMDS, API server, kubelet and the internet blocked, golden verdicts, access from another namespace refused | [04 Sandbox pools](../handson/04_sandbox_pools.md) |
| Agent Sandbox warm pool | open one claim and run the probe Job against its `status.sandbox.serviceFQDN` | golden verdicts from the claimed sandbox | "Checking evaluations as well" in [06 Agent Sandbox](06_agent_sandbox.md) |

- **If the gVisor node's driver is not on the nvproxy support list**: the node's boot log carries the warning from `install-gvisor.sh`.
- **Why `verify.sh` is not used for the Agent Sandbox warm pool**: warm pods have no `gpusandbox/version` label, so `verify.sh` does not find them, and if a Deployment pool of the same runtime exists it checks that pool instead.

**If it fails:** when a result differs from the expected one, look first at the runtime's section (gVisor, Kata) or the "sandbox pools and readiness" section of [Troubleshooting](../reference/troubleshooting.md).

## Signals to revisit the decision

Revisit the runtime choice if one of these facts changes.

| Changing fact | Impact | How to check |
|---|---|---|
| A new gVisor release supports the default HyperPod AMI's driver | B2 can skip the driver swap. To use the default AMI as is, the lifecycle script must also install gVisor (`on_create_sandbox.sh` fails when `runsc` is missing) | set `GVISOR_RELEASE` to the new release, then run `scripts/hyperpod/check_gvisor.sh` |
| The EKS NVIDIA AMI, the NVIDIA driver or the gVisor version changes | gVisor on the default `g5` (proprietary module with GSP off) rests on this repository's verification, not on the gVisor documentation, so it must be checked again | the steps in the list below the table |
| you can get `g6` On-Demand capacity in the Availability Zones you use | you can choose `g6`, which uses the open driver, matches the gVisor documentation and is cheaper | launch an instance and terminate it at once to check, then change `GVISOR_INSTANCE_TYPE` and `TRAINER_INSTANCE_TYPE` in `scripts/config.env` |
| A G or P family joins the nested virtualization list | Kata + GPU without `.metal` becomes worth evaluating (check VFIO support separately) | the nested virtualization User Guide, the `describe-instance-types` filter |
| A new `.metal` type with an x86 NVIDIA GPU | a VM boundary + current GPU combination becomes possible | EC2 accelerated computing instance specifications |
| Nitro Sandboxes supports GPU passthrough | a managed GPU tier becomes worth evaluating | the Nitro Sandboxes documentation, EKS sandboxing limitations |
| NVIDIA CI covers T4, or Kata supports CLH GPUs | the verification status of `g4dn.metal` or the CLH GPU path changes | Kata release notes, upstream `docs/hypervisors.md` |

- **When the EKS NVIDIA AMI, the NVIDIA driver or the gVisor version changes**: first check `/proc/driver/nvidia/version` and `runsc nvproxy list-supported-drivers` on the node. Then check the following.
    - **While a GPU is free**: run the `04_install_gpu_stack.sh` smoke test (it creates its own pod that uses one GPU).
    - **For a deployed pool**: check it with `scripts/ops/verify.sh gvisor v1`.

!!! question "❓ Misconception: with gVisor, GPU code is isolated as well as in a VM"
    gVisor handles syscalls in a user-space kernel (the Sentry), but the GPU path is an ioctl allowlist to the host driver, and the gVisor documentation says nvproxy is "much less effective at mitigating vulnerabilities within the NVIDIA GPU drivers themselves" and has "no validation of things like DMA buffers". For adversarial code from different customers, evaluate a VM boundary (Kata + VFIO) first; if you use gVisor because you need a current GPU, document the compensating controls and the residual risk.

!!! question "❓ Misconception: Nitro Sandboxes are out, so GPU sandboxes are solved as a managed service"
    AWS Nitro Sandboxes and EKS isolated pods (launched 2026-11-09) state in their documentation "GPU and other device passthrough are not supported at launch". For now they are a managed alternative for the CPU tier; run the GPU tier with this asset's gVisor or Kata + QEMU.

!!! tip "What to read next"
    - Runtime structure and AWS placement conditions: [02 Isolation runtimes](02_isolation_runtimes.md)
    - Instances, quotas and hourly cost: [04 Platforms and instances](04_platforms_and_instances.md)
    - Taking a sandbox from a warm pool per episode: [06 Extending with Agent Sandbox](06_agent_sandbox.md)
    - Building it yourself: [Hands-on 00 Overview](../handson/00_overview.md)
    - Operating design and threat model: [Production 00 Architecture](../production/00_architecture.md), [Production 02 Security](../production/02_security.md)

??? note "References"
    | Topic | Link |
    |---|---|
    | AWS Nitro Sandboxes, EKS sandboxing limitations | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
    | Amazon Bedrock AgentCore Code Interpreter | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html |
    | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
    | gVisor GPU support, GitHub | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
    | Kata NVIDIA GPU passthrough (4.3.1), GitHub | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers |

    All sources: [this page in All references](../reference/references.md#ref-concepts-05-decision-guide)
