# GPU Sandbox on AWS

Run model-generated code in a GPU sandbox separate from the training server. This guide shows how to check its output and execution time on Amazon EKS and use those results to calculate a reinforcement learning reward.

<a id="aws-network" href="images/figures/index--aws-architecture.svg?v=2">
<picture>
  <source media="(max-width: 34em)" srcset="images/figures/index--aws-architecture-compact.svg?v=2" width="360" height="716">
  <img class="off-glb" src="images/figures/index--aws-architecture.svg?v=2" width="824" height="521" alt="A and B1 reach the EKS API through an EC2 access instance and grade on EC2. B2 connects directly to the EKS API. Its system CPU worker, training GPU worker and two grading GPU workers all run on HyperPod.">
</picture>
</a>

<div class="grid cards" markdown>

-   :material-sprout:{ .lg .middle } **I am new to this**

    ---

    You have not used sandboxes, isolation runtimes or reinforcement learning before. Pictures first show why they are needed and what they are, then you bring one up yourself following real screenshots.

    [:octicons-arrow-right-24: Start the beginner guide](beginner/index.md)

-   :material-rocket-launch:{ .lg .middle } **I have experience**

    ---

    You have worked with Kubernetes, gVisor or Kata, or GRPO. Pick a path that fits your goal and budget and go straight to the hands-on or the production design.

    [:octicons-arrow-right-24: Choose a learning path](learning_paths.md)

</div>

## Scenarios on AWS

=== "A EC2 GPU"

    Train the model on one EC2 GPU node and grade its code on separate GPU nodes in the same EKS cluster. [EC2 GPU lab](handson/scenarios/a/index.md)

    [![An EC2 training node sends code to two gVisor GPU sandboxes in EKS.](images/architecture/scenario-a.drawio.png)](images/architecture/scenario-a.drawio.png)

=== "B1 Hybrid"

    Train on SageMaker HyperPod and grade the code on EC2 GPU nodes in the same EKS cluster. [Train on HyperPod and grade on EC2](handson/scenarios/b/b1.md)

    [![A HyperPod training node connects to EC2 grading nodes in EKS.](images/architecture/scenario-b1.drawio.png)](images/architecture/scenario-b1.drawio.png)

=== "B2 HyperPod"

    Put all workers on HyperPod. One CPU worker runs cluster services, one GPU worker trains the model, and two GPU workers grade its code. [Train and grade on HyperPod](handson/scenarios/b/b2.md)

    [![The system, training and grading workers run in HyperPod instance groups.](images/architecture/scenario-b2.drawio.png?layout=aws)](images/architecture/scenario-b2.drawio.png)

=== "C CPU"

    Run the same answer under gVisor, Kata + QEMU and Kata + Cloud Hypervisor on one EC2 `c8i` CPU node. You can also switch sandbox versions while grading continues. [CPU lab](handson/scenarios/c/index.md)

    [![Three sandbox runtimes share one c8i CPU node.](images/architecture/scenario-c.drawio.png)](images/architecture/scenario-c.drawio.png)

## Getting started

- **Run a lab on AWS.** Choose a scenario in the quickstart script. Start with the shared steps to prepare the cluster and the grading pool. [Hands-on quickstart](handson/index.md#quickstart)
- **Watch a run.** Pick a submission in the public demo and replay its evaluation. [Open the demo](https://dohbsn4kn34ya.cloudfront.net/?lang=en#try)

??? note "Benchmarks, optional exercises and production design"

    - [Runtime benchmarks and measurement conditions](handson/benchmarks/index.md#runtime-results)
    - [Switch grading pools during a training run](handson/scenarios/a/pool_update.md#switch-batches)
    - [Grade answers across several turns with Agent Sandbox](handson/extensions/multi_turn.md)
    - [Scale sandboxes and GPU nodes for production](production/00_architecture.md)

??? note "About this guide and its license"
    This guide summarizes the author's personal views and research. It does not represent the official documentation or positions of the company the author works for. Where it differs from official documentation, the official documentation takes precedence.

    Code and documentation are [MIT](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/LICENSE); model licenses are separate. The default model `Qwen/Qwen2.5-Coder-1.5B-Instruct` and `Qwen/Qwen2.5-Coder-7B-Instruct` in the production examples are Apache-2.0; `Qwen2.5-Coder-3B-Instruct` has a non-commercial license, so this asset does not use it.
