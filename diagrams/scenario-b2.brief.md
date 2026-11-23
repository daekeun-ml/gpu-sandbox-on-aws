# Scenario B2 architecture brief

This diagram describes the managed HyperPod EKS lab in `us-east-1`. It follows a single GRPO submission from trainer to grading pool and shows which AWS service provisions and schedules the four workers. The two A10G grading workers both served v1 in this run.

| Component | Responsibility | Source |
|---|---|---|
| AWS CloudFormation | Regional HyperPod wizard template creates the VPC, EKS and HyperPod cluster together | [Stack entry point](../scripts/hyperpod/create_managed.sh), [stack parameters](../infra/hyperpod/managed-parameters.py) |
| Amazon EKS 1.36 | Kubernetes API and pod scheduling on the registered workers | [Node and node-group checks](../docs/handson/07_hyperpod_b2.en.md) |
| HyperPod `system` | One `ml.m5.xlarge` runs CoreDNS and CPU benchmark jobs | [CoreDNS placement](../scripts/hyperpod/prepare_managed.sh), [benchmark clients](../scripts/hyperpod/bench_b2.sh) |
| HyperPod `trainer` | One `ml.g5.2xlarge` runs a GRPO job and subsequently the second benchmark client | [Training job](../k8s/trainer/hyperpod-job-grpo.yaml.tpl), [run record](../docs/handson/data/hyperpod-b2.json) |
| HyperPod `sandbox` | Two `ml.g5.xlarge` workers run one gVisor v1 pod per A10G | [Driver preparation](../scripts/hyperpod/reboot_sandboxes.sh), [run record](../docs/handson/data/hyperpod-b2.json) |

The diagram depicts provisioning, scheduling and the bidirectional grading request. The stack also uses a lifecycle S3 bucket and the pods use images from ECR. Both appear in the [walkthrough](../docs/handson/07_hyperpod_b2.en.md). The earlier CDK experiment with an EC2 AMI builder is documented separately in the [HyperPod chapter](../docs/handson/07_hyperpod.en.md#b2).
