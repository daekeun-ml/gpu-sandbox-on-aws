# 03 GPU access in a sandbox

Suppose you ask a model to write a function that adds two arrays. A CPU sandbox can run unit tests for a CPU implementation. If the task is to make the calculation faster on a GPU, the sandbox needs a GPU to run the code and measure its performance.

## GPU kernels and drivers

A **GPU kernel** is code that performs a calculation on the GPU. The **GPU driver** provides the interface for programs to request GPU work.

Suppose both implementations give the same correct answer. On an A10G, the reference takes 4 ms and the new implementation takes 2 ms, so the new one is twice as fast under those conditions. If you deploy on an L4, measure both there with the same input. The balance between compute and memory access can differ across GPUs and change which implementation is faster.

## Choosing a sandbox on EKS

On EKS, Kubernetes picks a node for the pod. If you select **Kata** as the runtime, Kata runs the pod's containers inside a virtual machine (VM) on that node. The program that starts the VM is called a **hypervisor**. Kata can use QEMU or Cloud Hypervisor for this role.

| Configuration | What you do in this repository |
|---|---|
| gVisor | `nvproxy` forwards supported GPU requests to the node's NVIDIA driver. A regular GPU instance works with a supported driver version. [gVisor GPU exercise](../handson/common/02_runtimes/gvisor.md) |
| Kata + QEMU | Assign a physical GPU to the VM using **GPU passthrough**. In this exercise, the driver inside the VM controls one T4 on `g4dn.metal`. [Kata GPU exercise](../handson/common/02_runtimes/kata.md) |
| Kata + Cloud Hypervisor | Check isolation by starting a VM for each pod on `c8i` without a GPU. [CPU-only exercise](../handson/scenarios/c/index.md) |

### GPU support in Cloud Hypervisor

When you manage a VM directly with Cloud Hypervisor, you can specify a physical GPU to attach. When you run a GPU pod with Kata on EKS, Kata has to attach the allocated GPU to the VM and make it available to the container. Kata's supported NVIDIA GPU configuration uses QEMU. The Kata + Cloud Hypervisor GPU experiment in this repository timed out while starting the VM. [Cloud Hypervisor documentation](https://github.com/cloud-hypervisor/cloud-hypervisor/blob/v55.0/docs/vfio.md) [Kata support table](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md#types) [GPU experiment](../handson/common/02_runtimes/kata.md#stage-3-optional-experimental-kata--cloud-hypervisor-gpu)

## GPU request path

![gVisor forwards requests to the node driver. Kata + QEMU uses a driver inside the VM.](../images/figures/beginner-03_gpu_sandbox--gpu-path.en.svg)

An `ioctl` is a system call that lets a program send a device-specific request to a driver.

### Why the location of the driver matters

| Question | gVisor + nvproxy | Kata + QEMU |
|---|---|---|
| Who handles device requests? | The node's NVIDIA driver handles requests that nvproxy permits. | The guest's NVIDIA driver controls the assigned physical GPU. |
| What must the node support? | The installed gVisor release must support the node driver version. | The node must boot VMs and assign a physical device using the IOMMU. |
| What does another pod need? | A default `g5.xlarge` has one A10G. If that card is in use, the next pod needs another node. | It needs one free T4 on `g4dn.metal` and enough CPU and memory for its guest. |

For a `Pending` GPU pod, check the runtime and available devices. If a running pod fails on its first GPU operation, the table identifies which driver and device connection to examine.

## Follow one submission to one GPU

On `g5.xlarge`, gVisor checks GPU device requests and passes supported ones to the node's NVIDIA driver. Check that driver version against the versions `nvproxy` supports. With Kata and QEMU on `g4dn.metal`, a physical GPU is assigned to the guest VM. Its guest driver runs the computation. Check the device reported inside the VM and whether its first operation completes. The IOMMU restricts which memory addresses the device may access.

![A Kata guest identifying its T4 and completing a GPU operation](../images/terminal/kata-gpu-replay.png)

In the EKS lab the gVisor pool processed 0.198 submissions/s on two A10Gs. The Kata QEMU pool processed 0.349/s on four T4s. Both received the same kernel, but the latter had twice as many slots for concurrent grading. To compare **code speed**, run the reference and candidate on the same GPU. To size a **pool**, read throughput alongside its ready pod count. [Conditions and original results](../handson/benchmarks/index.md#runtime-results)

See [when the sandbox needs a GPU](../concepts/01_why_gpu_sandbox.md) for other GPU workloads and [isolation runtimes](../concepts/02_isolation_runtimes.md) for node requirements. [Chapter 04](04_rl_and_sandbox.md) shows how execution results become a training reward.
