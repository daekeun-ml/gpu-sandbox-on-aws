# 02 Containers and sandboxes

Chapter 01 moved the sorting function out of the training program. Now suppose the numbers to sort are in `input.txt`. When the function opens the file, what looks it up and checks the program’s permission to read it?

## What happens when a program opens a file? { #nodes-and-kernels }

The program sends a request to the operating system. The **kernel** is the part of the operating system that manages files, memory and devices. A request from a program to the kernel is a **system call**. The machine running the program is a **node**.

A **container** can give each program its own view of files and processes on the same node. Two ordinary containers can each see their own `input.txt` while the same Linux kernel on the node handles both requests.

## Follow one file request

The **runtime** sets up the environment a program runs in. Pick an environment on the left of the figure and follow its arrow to the right.

![A file request goes to the node kernel under runc, to Sentry under gVisor, or to a virtual machine’s kernel under Kata.](../images/figures/beginner-02_container_vs_sandbox--three-walls.en.svg?v=2)

- **Ordinary container (runc).** The node’s Linux kernel handles the file request directly.
- **gVisor.** A program called **Sentry** acts as the kernel for code inside the sandbox. It handles the request first and asks the node kernel to do the work it needs from the host.
- **Kata.** The code runs inside a separate **virtual machine (VM)**. The Linux kernel running inside that VM receives the file request.

??? note "Where do pods and RuntimeClass fit in?"
    Kubernetes schedules containers in units called **pods**. Each grading server in this lab runs in a pod. The pod’s `runtimeClassName` setting selects a runtime such as gVisor or Kata. [Compare isolation runtimes](../concepts/02_isolation_runtimes.md)

## Read the kernel versions on one node { #read-uname-on-the-same-node }

`uname -r` prints the kernel release a program sees. **Which lines would match if you used the same container image on the same machine?** The image supplies the program and its files. The execution environment determines which kernel release the program sees.

![Output of uname -r under gVisor, two Kata configurations and an ordinary container on the same c8i node](../images/learning/aws-runtime-kernels.png)

Start with `host kernel for comparison` and the `runc` line at the bottom. Both show `6.18.56-125.164.amzn2023.x86_64`. The `gvisor-cpu` line shows the release reported by Sentry, `4.19.0-gvisor`. Both `kata-clh` and `kata-qemu` report `6.18.56` because each VM booted the same Linux kernel release. [Run the comparison](05_hands_on.md#aws-cpu)

<span id="how-the-workload-affects-isolation-costs"></span>

??? note "How does the runtime affect execution time?"
    In an AWS comparison on the same `m7i.xlarge`, a loop that computed in memory took 0.144 s under runc and 0.146 s under gVisor. Calling `getppid` to ask the kernel for the parent process ID 200,000 times took 0.035 s and 0.444 s, respectively. A program that frequently calls the kernel and one that spends most of its time computing can see different overheads. [AWS comparison and conditions](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/)

    With Kata, measure the time to boot the VM separately from the time to run one submission inside a VM that is already up. [Runtime benchmark](../handson/benchmarks/index.md#runtime-results)

The next chapter follows a request to run a calculation on a GPU. [03 GPU access in a sandbox](03_gpu_sandbox.md)
