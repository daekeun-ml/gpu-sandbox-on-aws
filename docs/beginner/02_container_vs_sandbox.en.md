# 02 Containers and sandboxes

Suppose a generated script tries to open a file. The operating system handles that request. The location of the handler is what differs across runc, gVisor, and Kata.

## Nodes and kernels

A **node** is the machine that runs the program. Its operating system **kernel** handles access to files, memory, and devices. A program's request to the kernel is a **system call**.

Ordinary containers can give each program its own view of files and processes. Two containers on the same node still send their file requests to the same Linux kernel.

| Runtime | Where the file request goes |
|---|---|
| runc | To the node's kernel. |
| gVisor | To Sentry, a kernel implemented in user space. |
| Kata | To the Linux kernel inside a virtual machine (VM). |

![Where runc, gVisor, and Kata handle a system call](../images/figures/beginner-02_container_vs_sandbox--three-walls.en.svg)

A **runtime** prepares the execution environment and starts the program. Kubernetes deploys containers in units called **pods**. A pod's `runtimeClassName` selects its runtime. Most sandbox deployments in this guide run one grading server per pod.

[Chapter 03](03_gpu_sandbox.md) follows requests to a GPU. [Runtime comparison](../concepts/02_isolation_runtimes.md) covers the trade-offs and node requirements.
