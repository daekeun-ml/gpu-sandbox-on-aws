# Decision guide

This lab runs model-generated code on a GPU and uses the result as a training reward. First choose **how to operate the cluster and its workers**. Then choose **how the grading sandbox will access its GPU**.

![Self-managed EC2 (A) and the hybrid setup (B1) grade on EC2 with gVisor or Kata + QEMU. Managed HyperPod (B2) grades on HyperPod with gVisor.](../images/figures/concepts-05_decision_guide--exercise-path.en.svg?v=2)

## 1. How do you want to operate the cluster and workers? { #choose-a-platform }

Amazon EKS manages the Kubernetes control plane in all three scenarios. The differences are how you provision the cluster and who manages the training and grading workers.

- **Self-managed EC2 (A).** Choose A when you want to select the instances, images and node groups for both training and grading. The CDK provisions the EKS cluster. An EC2 training worker sends code to separate EC2 grading workers. [EC2 GPU lab](../handson/scenarios/a/index.md)
- **Hybrid EC2 and HyperPod (B1).** Choose B1 to keep your EC2 grading pool and use HyperPod for training-node recovery and job restarts. Attach a HyperPod training group to the existing EKS cluster. The graders stay where they are. [Train on HyperPod and grade on EC2](../handson/scenarios/b/b1.md)
- **Managed HyperPod (B2).** Choose B2 when starting a cluster and you want HyperPod to manage all the workers. The deployment script creates the EKS cluster and its system, training and grading instance groups together. You still install the sandbox runtime on the grading workers. [Managed HyperPod lab](../handson/scenarios/b/b2.md)

## 2. Which GPU sandbox fits the workload? { #choose-a-runtime }

**Start with gVisor on a regular GPU instance.** Its `nvproxy` forwards supported requests to the node’s NVIDIA driver. Each grading sandbox can use an A10G without booting a separate VM. This is the default on EC2 in A and B1 and on HyperPod in B2. Check that the gVisor release supports the node’s driver version. [Set up gVisor on EC2](../handson/common/02_runtimes/gvisor.md) / [Prepare the HyperPod grading workers](../handson/common/02_runtimes/b2_workers.md)

**Choose Kata + QEMU if each sandbox needs a separate Linux kernel.** Each sandbox runs in a VM whose NVIDIA driver controls an assigned physical GPU. In A or B1, add an EC2 `g4dn.metal` and assign one T4 to each VM. Allow for the cost of the whole bare-metal node and the time to boot each new VM. [Attach a GPU to a Kata VM](../handson/common/02_runtimes/kata.md#kata-gpu)

## Start the lab { #first-checks-by-path }

Check the required worker counts in [instances and quotas by platform](04_platforms_and_instances.md), then follow the same scenario tab in [cluster provisioning](../handson/common/01_provision/index.md). All three GPU labs start with a gVisor grading pool. A and B1 can add a Kata GPU pool to compare the two runtimes.

??? note "If GPU capacity or budget is tight"
    Optional scenario C grades prepared submissions on CPUs and switches sandbox versions. Use it to try the grading workflow at a lower cost or while you wait for GPU capacity. Check CUDA correctness and speed in the GPU lab. [Try the CPU lab](../handson/scenarios/c/index.md)
