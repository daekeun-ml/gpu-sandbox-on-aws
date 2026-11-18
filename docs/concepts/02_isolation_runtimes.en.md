# Isolation runtimes

**TL;DR** GPU sandbox runtimes differ in who receives syscalls and GPU ioctls and where the NVIDIA driver lives; on AWS, Kata + GPU runs only on `g4dn.metal` and gVisor + GPU on regular G/P family VMs.

## Pain point

gVisor and Kata pass the GPU in different ways. gVisor forwards only allowed ioctls to the host driver, while Kata hands the whole GPU to a VM and uses the guest driver. "Kata needs `.metal`" now holds only for GPU passthrough. CPU sandboxes run on EC2 nested virtualization since 2026-02, and unlike QEMU, Cloud Hypervisor is listed upstream as not supporting GPUs.

![Three columns. gVisor + GPU forwards only allowed ioctls to the host driver and needs no /dev/kvm, so it runs on regular GPU VMs such as g5.xlarge. Kata + GPU passes the whole GPU into the VM (VFIO) and uses the guest driver; it needs /dev/kvm, an IOMMU and a host that owns the GPU, so it runs only on g4dn.metal, and upstream supports only QEMU there, not Cloud Hypervisor (both cells in red). Kata CPU only has no GPU; nested virtualization provides /dev/kvm, so since 2026-02 it runs on VMs such as c8i.2xlarge with both Cloud Hypervisor and QEMU.](../images/figures/concepts-02_isolation_runtimes.svg)

*Takeaway: gVisor and Kata take different GPU paths, only Kata + GPU needs `.metal`, and there the hypervisor upstream supports is QEMU.*


## Why

- **One table compares the structure.** Where syscalls are handled, where the driver lives, the GPU path and whether `/dev/kvm` is needed, side by side.
- **AWS placement is laid out from facts.** A table shows which runtimes run with a GPU on each instance.
- **Overhead uses only published numbers with a source.** These are Kata's RuntimeClass settings and upstream CI numbers.

**Before you start:** knowing Kubernetes pods and containers is enough, and reading [01 When the sandbox needs a GPU](01_why_gpu_sandbox.md) first helps. Unfamiliar terms are in the "Terms" box below and in the [Glossary](../reference/glossary.md).

??? note "Terms (expand if a word is new to you)"
    - **Container runtime**: the program that actually creates and runs a pod's containers. The default is runc.
    - **RuntimeClass**: a Kubernetes object that selects the runtime a pod runs with. The pod spec names it in `runtimeClassName`.
    - **containerd shim**: a small process between containerd and the actual runtime (runsc, Kata). The RuntimeClass `handler` decides which shim is used.
    - **Syscall**: a call in which a program asks the kernel to do something, such as opening a file or allocating memory.
    - **gVisor Sentry**: the kernel gVisor runs in user space. It receives the container's syscalls instead of the host kernel.
    - **systrap**: one of the ways (platforms) the Sentry intercepts syscalls. It works on regular VMs without `/dev/kvm`.
    - **ioctl**: the syscall a program uses to send commands to a device driver. CUDA talks to the GPU driver through ioctls.
    - **nvproxy**: the gVisor feature that forwards only allowlisted GPU ioctls to the host NVIDIA driver.
    - **KVM, `/dev/kvm`**: the Linux kernel's hardware virtualization feature and its device file. Kata creates VMs with it.
    - **IOMMU**: hardware that limits the memory a device can reach with direct memory access (DMA).
    - **VFIO, GPU passthrough**: the Linux feature that detaches a physical GPU from the host driver and hands it to a VM whole, and that way of using it.
    - **Cold-plug**: attaching a device before the VM starts, as opposed to hot-plug while it runs.
    - **Nested virtualization**: the ability to start VMs inside a VM. It gives a regular EC2 VM a `/dev/kvm`.
    - **Bare metal (`.metal`)**: an EC2 instance that uses a whole physical server without a hypervisor.
    - **CDI, device plugin**: CDI is a standard specification that describes how to put a device into a container; a device plugin advertises the node's GPUs as a Kubernetes resource (`nvidia.com/gpu`).
    - **NodeConfig, nodeadm**: the settings document of an EKS AL2023 node and the tool that applies it on every boot.

## Structure of the four runtimes

runc shares the host kernel, gVisor has a user-space kernel (the Sentry) receive syscalls first, and Kata gives each pod its own VM (with its own guest kernel).

| Item | runc | gVisor (runsc) | Kata (QEMU, Cloud Hypervisor) | Firecracker |
|---|---|---|---|---|
| Who receives syscalls | host kernel | the Sentry (a user-space kernel). systrap platform on VMs; the KVM platform only on bare metal | guest kernel inside the VM | guest kernel inside the microVM |
| Isolation boundary | namespaces, cgroups, seccomp | user-space kernel | hardware virtualization (KVM) | hardware virtualization (KVM), minimal device model |
| NVIDIA driver location | host | host | guest (the host does not load the NVIDIA driver) | n/a |
| GPU path | direct access to device nodes | nvproxy forwards only allowed ioctls to the host driver | VFIO passthrough (cold-plug) | none |
| `/dev/kvm` | not needed | not needed (systrap) | needed | needed |
| In this asset | trainer and system pods | `gvisor` RuntimeClass (handler `runsc`) | `kata-qemu-nvidia-gpu`, `kata-qemu`, `kata-clh` | not used (it is also one of Kata's hypervisors) |

The sandbox image is the same for all three runtimes and contains no NVIDIA kernel driver, only the CUDA user-space libraries bundled with the PyTorch wheel.

## Two GPU paths

![Two panels with the same five rows. a gVisor + nvproxy (g5.xlarge): inside the pod (gVisor) boundary are the candidate code (CUDA user-space libraries), the Sentry (user-space kernel, systrap platform) and nvproxy (ioctl allowlist per driver version); below, on the host, are the host NVIDIA driver 580.178.04 (proprietary, GSP off) and the A10G. b Kata + QEMU (g4dn.metal): inside the guest VM boundary are the candidate code and the guest kernel + guest NVIDIA driver (shipped by kata-deploy, open 615.71.09); on the host, VFIO passthrough (IOMMU confines DMA to the VM) leads straight to the T4 (the host binds only vfio-pci), with no NVIDIA driver on the host.](../images/figures/concepts-02_isolation_runtimes--gpu-paths.svg)

*Takeaway: With gVisor the candidate shares the host driver through an allowlist; with Kata the GPU moves into the VM and only the guest driver touches it.*


### gVisor + nvproxy

- **Configuration:** set `nvproxy = "true"` under `[runsc_config]` in `runsc.toml`. The default capabilities are `compute,utility`, and the shim reads only the file in the runtime option `ConfigPath`. GPU support turns on automatically when NVIDIA devices are in the OCI spec.
- **Driver policy:** versions must match exactly. There are three states: supported, unsupported (works only with `--nvproxy-allow-unsupported-driver`) and unknown (fails regardless of flags). Check with `runsc nvproxy list-supported-drivers`. 580.178.04 is supported since release-20260831.0, and 595.91.07 is unknown as of release-20261109.0.
- **Documented GPUs:** T4, A100/A10G, L4 and H100. Other GPUs of the same architecture "will likely work".
- **Device injection:** "runsc is fully CDI-compatible", and the documented path is `deviceListStrategy: cdi-cri` in the NVIDIA k8s-device-plugin. The host still needs nvidia-container-toolkit, but runsc configures the devices itself, so no prestart hook is needed.
- **containerd registration:** with containerd 2.x (the AMI ships 2.3.7) and config v3, put `runtime_type = 'io.containerd.runsc.v1'` and the `TypeUrl` and `ConfigPath` options under `[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runsc]`. Placed in NodeConfig `spec.containerd.config`, nodeadm merges this block on every boot. The RuntimeClass `handler` must equal the `runtimes.<name>` key (`runsc`).

!!! warning "Driver condition of gVisor nodes"
    The EKS AL2023 NVIDIA AMI loads the proprietary kernel module with GSP off on `g4dn`, `g5` and `g5g`, and the open module on `g6` (driver 580.178.04 on both `g5` and `g6`). gVisor documents nvproxy against NVIDIA's open driver and does not mention the proprietary driver. Still, 580.178.04 is on the support list of runsc `release-20261109.0`, and in the practice account on 2026-11-18 the smoke test (`cuda ok: NVIDIA A10G 2048.0`) and `ops/verify.sh gvisor v1` passed on `g5.xlarge` (A10G). This asset's default is `g5.xlarge`. This combination is verified by this repository, not documented by gVisor, so after changing the driver, AMI or gVisor version, re-run the smoke test and `ops/verify.sh`.

    `g6.xlarge` (L4) is a supported alternative; it loads the open module, which the gVisor documentation covers. T4 (`g4dn`) has the same driver condition as `g5` but is not tested in this asset, so it is unverified. Details are in [04 Platforms and instances](04_platforms_and_instances.md).

### Kata + VFIO passthrough

- **Host requirements:** `/dev/kvm`, an IOMMU, and a host that owns the GPU. AL2023 kernels have `CONFIG_INTEL_IOMMU_DEFAULT_ON` unset and need `intel_iommu=on`, so this asset bakes the kernel arguments `intel_iommu=on iommu=pt` into an AL2023 standard EKS AMI (`infra/kata/build-iommu-ami.sh`).
- **Supported mode:** the upstream documentation states "Cold-plug is by design the only supported mode for NVIDIA GPU passthrough".
- **Guest stack:** kata-deploy ships the NVIDIA guest kernel, rootfs, NVRC and the open kernel modules 615.71.09 (whose README lists Tesla T4). The host must not load the NVIDIA driver.
- **Shim choice:** GPU cold-plug in runtime-rs, the default since Kata 4.0.0, needs iommufd, and AL2023 kernels have `CONFIG_IOMMUFD` unset, so this asset uses the Go shim based `kata-qemu-nvidia-gpu`. The Go runtime is deprecated but still supported (as of Kata 4.3.1).
- **GPU Operator v26.7.2:** `sandboxWorkloads.enabled=true`, `sandboxWorkloads.mode=kata`, `ccManager.defaultMode=off` (with `on`, cc-manager exits on T4), the node label `nvidia.com/gpu.workload.config=vm-passthrough` and the resource name `nvidia.com/pgpu`. The official documentation states "A node can only run one container runtime at a time", so container GPU workloads and VM passthrough do not share a node.

??? info "Third-party reports (for reference)"
    One report says that on Ubuntu 24.04 on `g4dn.metal`, `intel_iommu=on iommu=pt` bound all eight T4s to vfio-pci with IOMMU groups suitable for passthrough. Another reports a warm reboot that did not come back, so this asset bakes the kernel arguments into an AMI instead of rebooting in user data.

## Kata's hypervisors: QEMU and Cloud Hypervisor

| Item | QEMU | Cloud Hypervisor (CLH) |
|---|---|---|
| CPU sandbox | supported (`kata-qemu`) | supported (`kata-clh`) |
| GPU passthrough | supported upstream (`kata-qemu-nvidia-gpu`) | not supported upstream. This asset ships only an experimental `kata-clh-nvidia-gpu` |
| RuntimeClass `overhead.podFixed` (Kata 4.3.1) | 320Mi, 250m. The GPU class is 10240Mi, 1 CPU | 130Mi, 250m |
| Boot to workload (Kata metrics CI, 3.28.0) | 0.71 s | 0.39 s |

`overhead.podFixed` is a RuntimeClass setting, not a measurement, that tells the scheduler to add the memory and CPU of the VM itself to the pod's requests.

Upstream `docs/hypervisors.md` marks GPU support for Cloud Hypervisor as not supported, and in 2025-08 a maintainer answered "You should use the QEMU GPU runtime class. I haven't done any work on CLH to enable proper GPU support." The Go `kata-clh` shim has VFIO cold-plug code since 3.29.0, but it is untested upstream and disabled in the shipped configuration, and the runtime-rs CLH configuration has no VFIO keys. So QEMU is the only GPU path in Kata that upstream supports, and this asset keeps CLH + GPU in `infra/kata/experimental-clh-gpu/` for evaluation only (no CI). CLH is supported as a CPU sandbox, and the CPU tier (`kata-clh-cpu` profile) is this combination.

!!! warning "How to read the overhead numbers"
    The boot times above come from the Kata metrics CI (3.28.0), measured on different machines with a wide tolerance; they are not AWS measurements. The AWS China blog's "CLH about 130 MB, QEMU about 160 MB" equals the Kata 3.31.0 `podFixed` defaults, so it is probably not a measurement (inference). What the post did measure is a cold start of about 3 s and about 230 ms to take a sandbox from a pre-started pool. This repository presents no measurements, so measure yourself with [08 Runtime benchmark](../handson/08_benchmark.md).

The VM size of `kata-qemu-nvidia-gpu` is `default_memory` 8192 MiB plus the container limits. VFIO type1 pins all guest RAM, so memory cannot be overcommitted. This asset's profile gives each T4 pod 8 CPUs and 16 GiB, and 8 x (16 + 10) GiB = 208 GiB fits in the 384 GiB of `g4dn.metal`.

## Isolation strength and residual risk

| Runtime | Between untrusted code and the host | Residual risk | What this asset adds |
|---|---|---|---|
| runc | shares the host kernel and driver | kernel or driver vulnerabilities are exposed directly | not used for sandboxes |
| gVisor + nvproxy | syscalls go to the Sentry, the GPU goes through an ioctl allowlist | per the gVisor documentation nvproxy is "much less effective at mitigating vulnerabilities within the NVIDIA GPU drivers themselves" and has "no validation of things like DMA buffers". Weaker than a VM boundary | one GPU per pod (no time-sharing), one sandbox per node, Ready only after egress denial is verified, node guard iptables |
| Kata + VFIO | VM boundary + IOMMU | the hypervisor and the GPU device itself. The IOMMU confines DMA to the VM (the unsafe noiommu mode stays off). vfio-pci resets the function (or the bus) on release, and T4 reports `reset_method=bus` (third-party report, not an NVIDIA guarantee). T4 has no confidential computing | v2 marks a pod as draining after 200 evaluations, and the production gateway's recycler deletes it so that a new pod (a new VM with Kata) replaces it |
| Kata (CPU only) | VM boundary | the hypervisor | the same network controls |

The GKE Sandbox documentation also advises "Don't use GPU time-sharing in sandboxed Pods". The full security boundary and threat model are in [Production 02 Security](../production/02_security.md).

## Where each runtime can run on AWS

| Location | Kata + GPU | Kata CPU only | gVisor + GPU |
|---|---|---|---|
| EC2 `.metal` (`g4dn.metal`) | yes (VFIO passthrough) | yes | yes (not used in this asset) |
| EC2 nested virtualization (C8i, M8i, R8i and others) | no: those families have no GPU | yes, no `.metal` needed | n/a |
| EC2 GPU VM (`g5.xlarge` and others) | no: no `/dev/kvm` | no | yes (systrap platform) |
| HyperPod node (`ml.g5` and others) | no | judged no (unverified) | not today (driver 595.91.07) |

The table rests on three facts.

1. **Kata needs `/dev/kvm`.** Both QEMU and Cloud Hypervisor use KVM. GPU passthrough also needs an IOMMU and a host that owns the physical GPU and can bind it to vfio-pci.
2. **EC2 nested virtualization gives a regular VM a `/dev/kvm`.** It launched on 2026-02-16 on C8i, M8i and R8i. The User Guide now lists M7i, M7i-flex, M8i, M8id, M8i-flex, C7i, C7i-flex, C8i, C8id, C8i-flex, R7i, R7iz, R8i, R8id, R8i-flex, X8i, I7i and I7ie. Supported L1 hypervisors are KVM and Hyper-V, and no G or P family is listed. AWS recommends bare metal for performance-sensitive virtualization workloads.
3. **The only x86 NVIDIA GPU `.metal` is `g4dn.metal`.** EC2's NVIDIA GPU bare metal types are this one (8x T4, 96 vCPU, 384 GiB) and the arm64 `g5g.metal` (2x T4G). HyperPod has no `ml.*.metal`, CreateCluster has no nested-virtualization CPU option, and the G and P families do not support nested virtualization.

Nested virtualization is enabled with `--cpu-options "NestedVirtualization=enabled"` on `run-instances`, `NestedVirtualization` in launch template `CpuOptions`, or `spec.cpuOptions.nestedVirtualization` in the Karpenter v1.15.2 EC2NodeClass. This asset's CDK stack ([`cdk/gpusandbox_cdk/stack.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py)) puts `NestedVirtualization: enabled` together with `CoreCount` and `ThreadsPerCore` into the `CpuOptions` of the c8i node group's launch template. No document says that EKS managed node groups pass this option to the nodes, but they did in the practice-account deployment (2026-11-14; the node had `/dev/kvm`).

A read-only check:

```bash
# Instance types that support nested virtualization in the current Region
aws ec2 describe-instance-types \
  --filters "Name=processor-info.supported-features,Values=nested-virtualization" \
  --query 'InstanceTypes[].InstanceType' --output text
```

**What to look for:** instance type names separated by spaces. Check that `c8i.2xlarge`, used in the hands-on, is among them. Empty output means the Region offers no supported type, so try another Region with `--region`.

**If it fails:** the "Kata" section of [Troubleshooting](../reference/troubleshooting.md) has commands that check nested virtualization.

!!! question "❓ Misconception: Kata needs a `.metal` instance"
    This was mostly true before 2026-02; now it applies only to GPU passthrough. For CPU sandboxes, `kata-clh` and `kata-qemu` run on a regular VM with nested virtualization, such as `c8i.2xlarge` (this asset's Kata CPU node script, `scripts/kata/cpu_nodes.sh`).

!!! tip "Managed CPU alternative"
    AWS Nitro Sandboxes and EKS isolated pods (launched 2026-11-09) use `isolated-sandbox` or `confidential-sandbox` as the `runtimeClassName` and need Kubernetes 1.36 or later. The documentation states "GPU and other device passthrough are not supported at launch", so they are a CPU sandbox alternative only. Selection criteria are in [05 Decision guide](05_decision_guide.md).

!!! tip "Orchestration above the runtime: Agent Sandbox"
    An orchestrator above the runtime decides when sandboxes are created and who gets them. [06 Extending with Agent Sandbox](06_agent_sandbox.md) uses kubernetes-sigs/agent-sandbox to claim one sandbox per episode from a pre-started warm pool, and since it keeps using the RuntimeClass, it works with either gVisor or Kata.

## Scope and limits

- **T4 on gVisor:** unverified, because of the AMI condition above.
- **Kata + GPU on `g4dn.metal`:** not verified upstream. The NVIDIA CI covers A100 and H100, not T4, and the EKS configuration NVIDIA validated is Ubuntu (AL2023 is not listed).
- **Kata CPU on HyperPod nodes:** judged not possible, but not checked directly.

??? note "References"
    | Topic | Link |
    |---|---|
    | EC2 nested virtualization (User Guide, What's New) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html , https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
    | EC2 accelerated computing instance specifications | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
    | gVisor installation, GPU support, GitHub | https://gvisor.dev/docs/user_guide/install/ , https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
    | Kata NVIDIA GPU passthrough (4.3.1), CLH GPU issue | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers/issues/11687 |
    | This asset's runtime settings | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/gvisor/install-gvisor.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/kata-deploy-values.yaml , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/gpu-operator-values.yaml |

    All sources: [this page in All references](../reference/references.md#ref-concepts-02-isolation-runtimes)
