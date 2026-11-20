# 02 Containers and sandboxes

!!! info "TL;DR"
    A sandbox runtime puts up one more wall between the container and the server kernel: gVisor builds it as "a fake kernel kept separately for each pod," and Kata as "a small VM started separately for each pod."

## Pain points

A container makes files and processes look separate and can also limit privileges and system calls, but it shares the kernel underneath with the server. So a kernel weakness that one container can exploit can put other containers on the same server at risk.

The alternatives come with many names too (runc, gVisor, Kata, Firecracker, QEMU, Cloud Hypervisor), and it is confusing which is an alternative to which, and which goes inside which. To choose, you also need to know what you lose when the wall gets thicker (speed, compatibility, the servers you can use).

![a: containers A, B and C share one server kernel, so a kernel weakness that one container can exploit may put A, B and C at risk. b: in each sandbox pod, a Sentry or a VM kernel stands between the containers inside it and the server kernel, adding one more wall in front of A, B and C](../images/figures/beginner-02_container_vs_sandbox.svg)

*Takeaway: With one shared kernel, a kernel weakness that one container can exploit can threaten the other containers too. A sandbox runtime keeps a Sentry or a VM kernel for each pod and puts one more wall between the container and the server kernel.*


## Why

- **The three runtimes handle system calls in different places.** runc uses the server kernel, gVisor uses the Sentry, and Kata uses the kernel inside a VM.
- **Stronger isolation has a cost.** Part 2 of the blog compared the performance of runc and gVisor on the same node.

**Before you start:** If you look at the list of risks in [chapter 01](01_why_sandbox.md) first, you will see more clearly "what the wall blocks."

??? note "Terms (expand if a word is new)"
    - **Kernel:** The core of the operating system. It manages files, memory, the network, and devices.
    - **System call (syscall):** The window through which a program asks the kernel for things like "open this file" or "give me memory."
    - **Container, runc:** A container is a set of processes bundled so they look separate. runc is the container runtime that Kubernetes uses by default.
    - **namespace, cgroup:** Linux features that limit what a process can see (namespace) and how much it can use (cgroup).
    - **VM (virtual machine), microVM:** A computer made in software, with its own separate kernel. A microVM is a small VM that includes only the devices it really needs, so it starts fast.
    - **Hypervisor:** A program that creates and runs VMs (QEMU, Cloud Hypervisor, Firecracker).
    - **KVM:** The piece of Linux that lets it use the CPU's virtualization features. On a server it shows up as `/dev/kvm`.
    - **RuntimeClass:** A Kubernetes setting that chooses which runtime a pod starts with.

## What sharing the kernel means

To read a file or send something over the network, a program must ask the kernel (a system call). A regular container (runc) splits "what it can see" and "how much it can use" with namespaces and cgroups, and can add a system call filter (seccomp) and dropped privileges. The kernel that takes the requests is still the server's one kernel.

In part 1 of the blog, typing `uname -r` (show the kernel version) inside a container on the same node showed the node's kernel version (`6.18.51-120.162.amzn2023`) under runc and `4.19.0-gvisor` under gVisor (blog measurement, EKS 1.36). A program inside gVisor talks to a kernel that gVisor imitates.

## Three walls

![Three panels with the same structure. a runc: code in the pod reaches the server kernel directly with system calls (wall: namespace, cgroup). b gVisor: a Sentry, one per pod, takes the system calls inside the pod and passes only a necessary few to the server kernel. c Kata: the kernel inside the VM, one per pod, takes them, and the path to the server kernel crosses the KVM boundary (wall: hardware virtualization)](../images/figures/beginner-02_container_vs_sandbox--three-walls.svg)

*Takeaway: runc reaches the server kernel directly, gVisor has a Sentry kept for each pod take the calls instead, and Kata keeps a separate VM, with its own kernel, for each pod.*


- **runc:** namespaces and cgroups divide what each container can see and how much it can use, and the server kernel handles the allowed system calls directly. Even with limited privileges and system calls the kernel is shared, so a kernel vulnerability usable from one container can threaten the other containers on the same node.
- **gVisor:** runs a user-space kernel called Sentry for each pod. Sentry handles most of a program's system calls and passes only a necessary few to the server kernel, so far fewer calls reach the server kernel directly.
- **Kata:** starts a small VM for each pod, and the kernel inside that VM handles the system calls. The VM and the server are separated by hardware virtualization (KVM).

gVisor and Kata do not remove the risk entirely either. gVisor still sends some calls to the server kernel, and Kata's VM runs on the same server, so a vulnerability in the hypervisor can still affect it.

| Item | runc | gVisor | Kata |
|---|---|---|---|
| Kernel the code asks | Server kernel | Sentry kept for each pod (user-space kernel) | Kernel of the VM started for each pod |
| Wall | namespace, cgroup | Sentry handles system calls instead | Hardware virtualization (KVM) boundary |
| Server requirement | None | None (runs on a regular VM) | `/dev/kvm`: bare metal or an instance with nested virtualization turned on |
| Where it slows down | Almost nowhere | Work with many system calls | Time to start the VM, attaching devices |
| GPU | Used as is | Checks driver calls and forwards them | Hands the whole GPU to the VM ([chapter 03](03_gpu_sandbox.md)) |

## The cost of the wall: real numbers

Part 2 of the blog compared runc and gVisor on the same node (EKS 1.36, `m7i.xlarge`). Below are the blog's measurements, not values that this repository measured.

| Task | runc | gVisor | Difference |
|---|---|---|---|
| CPU-only repeated calculation | 0.144 s | 0.146 s | Almost the same |
| 200,000 system calls (`getppid`) | 0.035 s | 0.444 s | About 12.5 times |
| Creating 1,000 files | 0.041 s | 0.195 s | About 4.7 times |
| Running Python 5 times | 0.206 s | 0.399 s | About 1.9 times |

The more system calls code makes, the slower it gets, and the blog says the cost of one system call went from about 0.18 µs to 2.2 µs. What the blog measured is the system call cost of CPU work.

For GPU grading, keep the run time of one call of the submitted function apart from the time the server takes to grade one answer. Below is this repository's A10G gVisor recording.

- **Run time of one call of the submitted function**: one call of the vector-add function, until its GPU work finished, took about 0.47 ms (including the output tensor allocation, median of several runs).
- **Time the server takes to grade one answer**: the sandbox server took about 9.4 s to grade that one answer, from process start through CUDA initialization, checks and cleanup. Time the client spent waiting for a free pod is not part of this value ([08 Runtime benchmark](../handson/08_benchmark.md)).

## Choosing a runtime per pod

In Kubernetes, you choose a runtime per pod with `RuntimeClass`, so pods in one cluster can use runc, gVisor or Kata. The CPU exercise in [chapter 05](05_hands_on.md) starts gVisor, Kata (Cloud Hypervisor) and Kata (QEMU) pods from the same test image on one node, starts a regular container (runc) pod separately, and compares the kernel each pod sees. The GPU grading pools have one profile per runtime, so the node selector and the GPU resource name change along with the RuntimeClass.

!!! question "❓ Misconception: Using Agent Sandbox makes isolation stronger"
    Agent Sandbox is a management tool that starts sandboxes ahead of time (warm pool) and lends them out. The actual isolation is decided by the `RuntimeClass` underneath. The production case in part 3 of the blog (Ably) also uses Agent Sandbox with regular containers (runc) and plans to evaluate microVMs.

!!! question "❓ Misconception: If it does not show up in the server's `ps`, it is safe"
    Processes inside gVisor do not show up in `ps` on the server. But part 1 of the blog states that it did not test container escape attacks. "Cannot be seen" and "cannot get out" are different things.

## In one line

- A regular container shares the server kernel, and a sandbox runtime puts up one more wall in between.
- gVisor builds the wall with a Sentry for each pod, and Kata with a VM for each pod. The thicker the wall, the more server requirements and cost you take on.

## Next

In [03 Isolating the GPU too](03_gpu_sandbox.md), we look at why a GPU makes things harder.

??? note "References"
    | Topic | Link |
    |---|---|
    | AI agent sandbox, EKS isolation part 1 (experiment comparing runc and gVisor) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ |
    | Same series, part 2 (system call cost measurements) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
    | Kubernetes RuntimeClass | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
    | gVisor | https://github.com/google/gvisor |
    | Kata Containers | https://github.com/kata-containers/kata-containers |

    All sources: [this page in All references](../reference/references.md#ref-beginner-02-container-vs-sandbox)
