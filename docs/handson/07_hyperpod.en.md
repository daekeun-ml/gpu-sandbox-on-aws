# 07 HyperPod scenarios

<span id="07-hyperpod-scenario"></span>

Both paths train a GRPO model on SageMaker HyperPod. Choose a path based on **where you want to grade the code the model generates**.

| | B1 · Grade on EC2 | B2 · Grade on HyperPod |
|---|---|---|
| System nodes | EC2 nodes in EKS | HyperPod `system` group |
| Training node | One HyperPod `ml.g5.2xlarge` | One HyperPod `ml.g5.2xlarge` |
| Grading nodes | Two EC2 `g5.xlarge` nodes | Two HyperPod `ml.g5.xlarge` nodes |
| Provisioning | Deploy EKS and EC2 with CDK, then attach the HyperPod training node. | Create EKS and all three instance groups through the HyperPod wizard. |

- **[Start the B1 lab](07_hyperpod_b1.md)** · Deploy the grading pool on EC2 and run one training step on HyperPod.
- **[Start the B2 lab](07_hyperpod_b2.md)** · Run the system services, training, grading and benchmark on HyperPod workers.

[Choose another scenario](00_overview.md#step-order)

<script src="../../../javascripts/hyperpod-bookmarks.js" defer></script>
