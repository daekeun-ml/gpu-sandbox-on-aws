[한국어](scenario-b2.guide.md) | **English**

# Scenario B2, System services, training and grading on HyperPod

Amazon EKS supplies the Kubernetes API and scheduler. All four workers registered with this cluster in `us-east-1` belong to SageMaker HyperPod instance groups.

[![EKS control plane and the HyperPod system, trainer and sandbox instance groups](scenario-b2.drawio.png)](scenario-b2.drawio.png)

## Read the diagram

1. **Workstation and EKS.** The operator runs the B2 deployment script from the workstation to create a CloudFormation stack. The stack provisions the VPC, EKS control plane and HyperPod cluster together. The operator then connects `kubectl` directly to the EKS API.
2. **Three HyperPod instance groups.** The inner dashed boxes mark the instance groups. One CPU worker in `system` runs CoreDNS and the benchmark client. `trainer` runs GRPO on one `ml.g5.2xlarge`. Each of the two `ml.g5.xlarge` workers in `sandbox` runs one v1 grading pod with its own A10G.
3. **Grading requests and responses.** Across the center, the trainer sends generated code and receives a verdict and execution time. The upper solid line shows the CPU benchmark client sending requests to the same grading pool after training.
4. **Shared services and model download.** The bottom row shows S3 for lifecycle scripts, ECR for container images and CloudWatch Logs for EKS control plane logs. The trainer downloads the model from Hugging Face Hub through the NAT gateway.

## What ran on the workers

The default NVIDIA driver `595.112.07` was outside the support list for gVisor `20261109.0`. The two grading workers received `580.178.04` and rebooted through the HyperPod API. A CUDA operation inside a gVisor pod then confirmed access to the A10G. The trainer kept its default driver.

After training, `system` and `trainer` took turns sending 32 requests each. Both clients sent the same fixed kernel to the same pool and all 64 requests succeeded. [Deployment and screenshots](../docs/handson/scenarios/b/b2.en.md), [Latency and throughput](../docs/handson/benchmarks/index.en.md#hyperpod-b2), [Editable draw.io file](scenario-b2.drawio)

[Earlier worker overview](variants/b2-worker-overview/scenario-b2.drawio.png), [Editable worker overview](variants/b2-worker-overview/scenario-b2.drawio)
