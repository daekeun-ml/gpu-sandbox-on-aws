---
hide:
  - footer
---

# Choose a HyperPod training path (scenario B)

<span id="07-hyperpod-scenarios"></span>

<span id="07-hyperpod-scenario"></span>

Both paths train a GRPO model on SageMaker HyperPod. Choose a path based on **where you want to grade the code the model generates**.

| | B1 (Grade on EC2) | B2 (Grade on HyperPod) |
|---|---|---|
| System nodes | EC2 nodes in EKS | HyperPod `system` group |
| Training node | One HyperPod `ml.g5.2xlarge` | One HyperPod `ml.g5.2xlarge` |
| Grading nodes | Two EC2 `g5.xlarge` nodes | Two HyperPod `ml.g5.xlarge` nodes |
| Provisioning | Deploy EKS and EC2 with CDK, then attach the HyperPod training node. | Run the deployment script to create the EKS cluster and all three HyperPod instance groups. |

- **[Start the B1 lab](b1.md)** Deploy the grading pool on EC2 and run one training step on HyperPod.
- **[Start the B2 lab](b2.md)** Run the system services, training, grading and benchmark on HyperPod workers.

[Choose another scenario](../../index.md#step-order)
