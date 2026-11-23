[한국어](scenario-b2.guide.md) | **English**

# Scenario B2 · System services, training and grading on HyperPod

Amazon EKS supplies the Kubernetes API and scheduler. All four workers registered with this cluster in `us-east-1` belong to SageMaker HyperPod instance groups.

[![EKS control plane and the HyperPod system, trainer and sandbox instance groups](scenario-b2.drawio.png)](scenario-b2.drawio.png)

## Read the diagram

1. **CloudFormation and EKS at the top.** The regional template used by the HyperPod EKS creation wizard provisions the VPC, EKS control plane and HyperPod cluster together. The operator connects from their workstation with `aws eks update-kubeconfig`.
2. **The three worker groups below.** One `ml.m5.xlarge` in `system` runs CoreDNS and the CPU benchmark client. One `ml.g5.2xlarge` in `trainer` runs GRPO. Each of the two `ml.g5.xlarge` workers in `sandbox` runs a v1 gVisor grading pod with its own A10G.
3. **The arrows between training and grading.** The trainer sends generated code to the v1 pool. A grading pod returns a verdict and execution time for the trainer to use in its reward. All 12 submissions in the training step went to the same pool version.

## What ran on the workers

The default NVIDIA driver `595.112.07` was outside the support list for gVisor `20261109.0`. The two grading workers received `580.178.04` and rebooted through the HyperPod API. A CUDA operation inside a gVisor pod then confirmed access to the A10G. The trainer kept its default driver.

After training, `system` and `trainer` took turns sending 32 requests each. Both clients sent the same fixed kernel to the same pool and all 64 requests succeeded. [Deployment and screenshots](../docs/handson/07_hyperpod_b2.en.md) · [Latency and throughput](../docs/handson/08_benchmark.en.md#hyperpod-b2) · [Editable draw.io file](scenario-b2.drawio)
