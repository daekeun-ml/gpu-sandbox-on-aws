# 03 Isolating the GPU too

**TL;DR** GPU code sends commands to the driver inside the kernel, so the way you bring the GPU inside the wall decides the isolation level: gVisor checks those commands and passes them on, and Kata hands the whole GPU to a VM.

## Pain points

A sandbox that grades code usually needs only a CPU, so widely used microVM sandboxes (Firecracker-based ones and so on) have no device for handing over a GPU. But to give "how much faster did this GPU kernel get" as a score, the place that does the grading needs a real GPU. And the GPU driver runs inside the kernel, so a driver bug is a kernel bug, and container isolation alone cannot block this path.

![a: grading a GPU kernel needs a real GPU; a Firecracker-based microVM has no device for a GPU, so it cannot grade, and in a regular container (runc) a driver bug reaches the server kernel. b: gVisor + nvproxy (g5.xlarge) checks ioctls and lets only allowlisted calls reach the server driver, and Kata + VFIO (g4dn.metal) hands the whole GPU to the VM, so driver bugs stay inside the VM](../images/figures/beginner-03_gpu_sandbox.svg)

*Takeaway: A microVM without a GPU cannot grade, and in a regular container a driver bug reaches the server kernel. gVisor + nvproxy passes only allowlisted calls to the server driver, and Kata + VFIO keeps the GPU and the driver inside the VM.*


## Why

- **If you follow the path to the GPU, you can see where to block it.**
- **We compare the trade-offs of the two approaches in a table.** The thickness of the wall, the server you need, and the GPUs you can use pull in different directions.
- **We connect it all the way to the instances you would pick on AWS.**

**Before you start:** Read about the three walls (runc, gVisor, Kata) in [chapter 02](02_container_vs_sandbox.md) first.

??? note "Terms (expand if a word is new)"
    - **GPU driver:** The program that lets the operating system work with the GPU. The NVIDIA driver runs inside the kernel.
    - **ioctl:** A command a program sends to a device driver. Think of it as the "order form" you use to give the GPU work.
    - **nvproxy:** A gVisor feature that checks GPU commands (ioctls) and passes only the ones on an allowlist to the server's driver.
    - **VFIO passthrough:** A way of handing one whole GPU to a VM so that it is used directly inside the VM.
    - **IOMMU:** A feature that uses hardware to fence in the memory a device (GPU) can reach. It is required for passthrough.
    - **bare metal (`.metal`):** An EC2 instance where you rent a whole physical server, not a VM.
    - **nested virtualization:** A feature that starts a VM inside a VM. On EC2, it can be turned on for some instance families.

## The path to the GPU

![The path runs PyTorch code, CUDA library, ioctl (order form), NVIDIA driver inside the kernel, GPU. gVisor + nvproxy puts a wall on the ioctl path in front of the driver and passes only allowlisted commands. A bracket below shows Kata + VFIO passthrough, which puts the code, the driver and the GPU whole inside the pod's VM](../images/figures/beginner-03_gpu_sandbox--gpu-path.svg)

*Takeaway: Every command that gives the GPU work goes through the driver inside the kernel, so the key question is where on this path you put up the wall. gVisor checks the commands in front of the driver, and Kata puts the whole path inside the VM.*


## Two approaches

**gVisor: a clerk who checks the order forms (nvproxy)**

When a program inside gVisor issues a GPU order form (ioctl), nvproxy compares it against an allowlist for each driver version, passes only the matching ones on to the server's driver, and rejects the rest. You do not need to change your PyTorch code.

- **Good points:** Runs on regular GPU instances (for example `g5.xlarge`), is light and starts fast.
- **Weak points:** If the server's driver version is not on the allowlist, you cannot use the GPU, and commands that pass the check reach the server's driver. The gVisor docs also say that, with nvproxy, gVisor is "much less effective at mitigating vulnerabilities within the NVIDIA GPU drivers themselves."

**Kata: bringing the GPU inside the house (VFIO passthrough)**

Kata hands one whole GPU to that pod's VM. The driver also runs inside the VM, so even if the driver breaks, the damage ends inside that VM, and the IOMMU fences the memory the GPU can touch to that VM's memory.

- **Good points:** The wall is the thickest.
- **Weak points:** The server has to hold the GPU directly, so the requirements are strict (`/dev/kvm` and the IOMMU, and the server itself must not load the NVIDIA driver). The GPU path that upstream Kata officially supports is the QEMU hypervisor, and GPU support in Cloud Hypervisor is still experimental.

| Item | gVisor + nvproxy | Kata + VFIO |
|---|---|---|
| Wall | Checks the commands going to the driver | Puts the GPU and the driver whole inside the VM |
| Driver bugs | Reach the server's driver | Trapped inside the VM |
| Server needed | Regular GPU instance | Bare metal that can hold the GPU directly |
| Driver version | Must exactly match the allowlist | Pick the driver inside the VM separately |
| This repository's choice | One sandbox per `g5.xlarge` (A10G) node | On `g4dn.metal` (8 T4s), one T4 per VM |

!!! question "❓ Misconception: Using a GPU with gVisor is as safe as a VM"
    Even after the check, commands go to the server's driver, so the path to driver bugs only gets narrower. If you need a VM-level boundary, consider Kata + GPU.

## Which instance to use on AWS

| What you want | Instance | Why |
|---|---|---|
| GPU sandbox with gVisor | A regular GPU VM such as `g5.xlarge` | gVisor does not need KVM, and it only needs a driver that nvproxy supports |
| GPU sandbox with Kata | `g4dn.metal` | To hand the whole GPU to a VM, the server has to hold the GPU directly, so you need bare metal. Among AWS x86 NVIDIA instances, `g4dn.metal` is the only bare metal one |
| CPU sandbox with Kata | A VM that supports nested virtualization, such as `c8i.2xlarge` | Without a GPU you only need to start a VM, so `/dev/kvm` is all you need. Since 2026-02, nested virtualization can be turned on for some VM families |

!!! question "❓ Misconception: Kata always needs `.metal`"
    `.metal` is required only when you hand a GPU to Kata. Kata with only a CPU runs on a VM with nested virtualization turned on (for example the `c8i.2xlarge` that starts the three runtimes in [chapter 05](05_hands_on.md)). On the other hand, GPU instances (G and P families) do not support nested virtualization, so you cannot use Kata on top of a GPU VM.

## One more thing to watch in a GPU sandbox

A GPU leaves state behind when it runs kernels (computations), so one run that breaks the GPU state can throw off the next run too. This repository therefore runs each grading in a separate process and, depending on the sandbox version, starts a fresh pod after a set number of runs. Why grading has to be this accurate is the topic of the next chapter.

## In one line

- GPU isolation is a choice between "checking the commands that go to the GPU (gVisor)" and "bringing the whole GPU inside a VM (Kata)."
- gVisor runs easily on regular GPU instances, while Kata + GPU gives a thicker wall but needs `g4dn.metal` on AWS.

## Next

In [04 Reinforcement learning and sandboxes](04_rl_and_sandbox.md), we look at the grader role a sandbox plays in training.

??? note "References"
    | Topic | Link |
    |---|---|
    | gVisor GPU support (nvproxy) | https://gvisor.dev/docs/user_guide/gpu/ |
    | Kata Containers GPU passthrough | https://github.com/kata-containers/kata-containers/tree/main/docs/use-cases |
    | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
    | Accelerated computing instances | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |

    All sources: [this page in All references](../reference/references.md#ref-beginner-03-gpu-sandbox)
