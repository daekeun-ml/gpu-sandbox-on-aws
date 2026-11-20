[한국어](README.md) | **English**

# GPU Sandbox on AWS

GPU Sandbox on AWS provides example code and hands-on guides for teams that need to run AI-generated code on a GPU. Deploy an execution environment on AWS that is separate from the training server.

The guide covers running the trainer and sandboxes on EC2 nodes in Amazon EKS, as well as training on SageMaker HyperPod. Compare gVisor and Kata by isolation boundary, supported GPUs, and node requirements.

The GRPO exercise grades model-generated code in GPU sandboxes and uses correctness and execution speed as rewards for model updates. A CPU exercise covers the scoring flow without GPUs.

[Guidebook](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/) | [Replay demo](https://dohbsn4kn34ya.cloudfront.net/?lang=en) | [Scripts](SCRIPTS.en.md) | [Troubleshooting](TROUBLESHOOTING.en.md)

| Goal | Start here |
|---|---|
| Understand how execution and training fit together | [Beginner guide](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/beginner/) |
| Grade code on your computer | [Local exercise](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/beginner/05_hands_on/) (no AWS account or GPU needed) |
| Compare runtimes on AWS | [CPU-only exercise](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/10_cpu_only/) (billed) |
| Connect GPU grading to training | [Hands-on overview](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/00_overview/), starting with A |

## Architecture

![What you build: the policy model and vLLM on the training node send kernel code, with the version pinned, to the selected sandbox pool (gVisor, Kata + QEMU, or Kata + Cloud Hypervisor as the CPU tier) and get correctness and speedup back as the reward](docs/images/figures/index--what-we-build.en.svg)

*Takeaway: Kernel code from the policy model goes to the sandbox pool of the selected runtime with its version pinned per group, and correctness and speedup come back as the reward. GPU scoring runs on the gVisor and Kata + QEMU pools; Kata + Cloud Hypervisor runs on CPU by default.*

All four scenarios use the same CDK stack (private EKS API, SSM tunnel, KMS key, logs). A, B1 and B2 differ in where the trainer and the sandboxes run; C has no trainer or model and practices scoring and version swaps on CPU sandboxes.

### Scenario A: EC2 GPU (default)

![Scenario A: the private EKS API reached through the SSM tunnel, and a trainer on g5.2xlarge sending kernel code to gVisor pools on two g5.xlarge nodes](docs/images/architecture/scenario-a.drawio.png)

*Takeaway: The trainer and the gVisor pools both run on EC2 nodes of EKS, and the model comes from Hugging Face Hub through the NAT.*

<details>
<summary><b>Scenario B1: training on HyperPod</b></summary>

![Scenario B1: the trainer on a HyperPod instance group and the gVisor pools on EC2 nodes](docs/images/architecture/scenario-b1.drawio.png)

*Takeaway: Only the trainer moves to a HyperPod instance group (ml.g5.2xlarge), booted with lifecycle scripts from S3; the sandboxes stay on the same EC2 gVisor nodes as in A.*

</details>

<details>
<summary><b>Scenario B2: training and sandboxes on HyperPod</b></summary>

![Scenario B2: the trainer and the gVisor pools both on HyperPod instance groups, the sandbox nodes booting from a custom AMI](docs/images/architecture/scenario-b2.drawio.png)

*Takeaway: The sandboxes also move to a HyperPod instance group (ml.g5.xlarge x2), whose nodes boot from a custom AMI baked once (driver 580.178.04). This experimental path has not been run on AWS.*

</details>

<details>
<summary><b>Scenario C: CPU only</b></summary>

![Scenario C: CPU pools of three runtimes on one c8i.2xlarge, no GPU](docs/images/architecture/scenario-c.drawio.png)

*Takeaway: With no GPU node, the pools of three runtimes share one c8i.2xlarge, and a simulate Job on the system nodes sends golden code in place of the trainer.*

</details>

### Request path

- Each time the trainer sends requests to the sandbox, it picks the runtime and version from a snapshot of the routing ConfigMap (`sandbox-routing`), and it takes all results of one reward batch from one pool.
    - **If you switch to v2 during training**: when the batch has completions that still need scoring, cached results from the previous pool that fall in the same batch are scored again on the v2 pool.
    - **When every completion in a batch is already cached from one pool**: the trainer uses those results without calling the sandbox, even after a switch.
    - **If the routing switches more than once within one batch**: the third request sends the whole batch to one pool, so one batch is always scored by one version.
- The trainer resolves the headless Service through CoreDNS and sends `POST /v1/evaluate` straight to each Ready pod. A busy pod answers `503`, and the trainer retries another pod.
- Each request carries a projected ServiceAccount token with the audience `gpu-sandbox`, which the pod verifies offline against the JWKS. The `sandbox` namespace is default-deny, so only labelled pods from `rl-trainer` can connect.

The production layout (Karpenter NodePools, sandbox gateway, veRL on KubeRay) is in [Production 00 Architecture](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/production/00_architecture/), and node groups, namespaces and a reading of each arrow are in [Hands-on 00 Overview](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/00_overview/). The diagram sources (`.drawio`) are in [`diagrams/`](diagrams/).

## Getting started

The local exercise checks whether prepared answers receive the expected verdicts on a CPU. Follow [environment setup](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/getting_started/) to install the tools.

Choose an AWS path that matches your goal.

- **C (CPU only)** Run scoring without a model and compare gVisor and Kata. [CPU exercise](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/10_cpu_only/)
- **A (EC2 GPU)** Score GPU kernels and use the results for GRPO training. [Cluster setup](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/01_cluster_and_images/)
- **B1 and B2 (HyperPod)** B1 places the trainer on HyperPod. B2 also places sandboxes there as an experimental path. [HyperPod exercise](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/07_hyperpod/)

AWS resources can incur charges while idle. Check the [cost estimates](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/concepts/04_platforms_and_instances/) before deployment and follow the [cleanup steps](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/99_cleanup/) at the end.

## Further reading

- **Isolation** Compare GPU access and node requirements in [gVisor and Kata](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/concepts/02_isolation_runtimes/).
- **Multi-turn grading** The [Agent Sandbox exercise](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/11_multi_turn/) sends an episode's submissions to the same sandbox.
- **Production** See the [reference architecture](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/production/00_architecture/) and [security design](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/production/02_security/).

## Validation status

The AWS exercises ran EC2 GPU training (A), CPU grading and version switching (C), and Kata GPU with QEMU. HyperPod B1 and B2 and switching pools during GPU training were not verified on AWS. The experimental Kata GPU configuration with Cloud Hypervisor failed to start its VM. [Run records and measurement scope](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/sources/#aws-run-record)

## License

Code and documentation are [MIT](LICENSE). Models and datasets have their own licenses.

This repository records the author's personal views and research. It does not represent official documentation or the position of the author's employer.
