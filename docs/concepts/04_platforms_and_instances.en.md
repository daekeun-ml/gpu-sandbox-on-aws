# Platforms and instances

!!! info "TL;DR"
    **Scenario A** runs both training and grading on EC2. **Scenario B1** keeps the EC2 grading pool and moves training to HyperPod. **Scenario B2** runs all workers on HyperPod, from the CPU worker for cluster services to the GPU workers for training and grading.

    HyperPod workers run in a separate VPC managed by AWS and connect to your account’s VPC through elastic network interfaces (ENIs). [AWS architecture diagram](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks.html)

    Choose a training GPU with enough memory for the model. For grading, start with the GPU you want to test on and the isolation runtime your sandbox needs.

## Architecture by scenario

=== "A (EC2 GPU)"

    Both training and grading run on EC2. The training node sends model-generated code to gVisor GPU sandboxes in the same EKS cluster.

    ![An EC2 training node sends code to two gVisor GPU grading nodes in the same EKS cluster.](../images/architecture/scenario-a.drawio.png)

=== "B1 (Hybrid)"

    Train the model on HyperPod and grade its code on EC2. The HyperPod training group joins the existing EKS cluster.

    ![Training runs on HyperPod and grading runs on EC2 GPU nodes in the same EKS cluster.](../images/architecture/scenario-b1.drawio.png)

=== "B2 (HyperPod)"

    The EKS control plane schedules pods on the HyperPod workers. The `system` group runs cluster services, `trainer` trains the model, and `sandbox` grades its code on GPUs.

    ![The HyperPod system, trainer and sandbox groups run cluster services, training and grading under EKS.](../images/architecture/scenario-b2.drawio.png?layout=aws)

=== "C (CPU, optional)"

    Choose this setup if GPU capacity or budget is tight. A simulator on the system nodes sends prepared submissions to CPU sandboxes on the `c8i` node for grading.

    ![The simulator on the system nodes sends submissions to a CPU grading pool on the c8i node.](../images/architecture/scenario-c.drawio.png)

<span id="training-and-grading-on-separate-nodes"></span>

## Default workers for the GPU labs { #compare-scenarios-a-b1-b2-and-c }

The training node generates answers and updates the model’s weights. The grading node runs the submitted code to check its output and execution time.

| Lab | Training node | Grading nodes |
|---|---|---|
| [A (EC2 GPU)](../handson/scenarios/a/index.md) | 1 EC2 `g5.2xlarge` | 2 EC2 `g5.xlarge` |
| [B1 (HyperPod and EC2)](../handson/scenarios/b/b1.md) | 1 HyperPod `ml.g5.2xlarge` | 2 EC2 `g5.xlarge` |
| [B2 (HyperPod)](../handson/scenarios/b/b2.md) | 1 HyperPod `ml.g5.2xlarge` | 2 HyperPod `ml.g5.xlarge` |

**System workers** run services such as CoreDNS, which resolves names inside the cluster. A and B1 use two EC2 `m6i.large` instances for that role. B2 uses one `ml.m5.xlarge` in the HyperPod `system` group. That gives B2 four workers in total, one CPU instance and three GPU instances.

<span id="further-detail"></span>
<span id="distinguish-the-training-gpu-from-the-grading-gpus-in-b1"></span>

## What changes between B1 and B2?

In both scenarios the model trains on an A10G on a HyperPod worker. The choice comes down to **who manages the other workers**.

![In B1, HyperPod manages the training worker and EC2 provides the system and grading workers. In B2, all three roles run in HyperPod instance groups.](../images/figures/concepts-04_platforms_and_instances.en.svg?v=2)

- **B1** attaches a HyperPod training group to the EKS cluster provisioned with the CDK. Choose it to keep an EC2 grading pool or add an EC2 node for Kata GPU grading. The operator connects to the EKS API through an SSM tunnel. [Connect the B1 trainer](../handson/common/02_runtimes/b1_trainer.md)
- **B2** uses `scripts/hyperpod/create_managed.sh` to deploy the EKS cluster and all three HyperPod instance groups in one CloudFormation stack. `kubectl` connects directly to the EKS API. Both grading workers run gVisor, with one A10G assigned to each sandbox. [Create the B2 cluster and workers](../handson/common/01_provision/hyperpod.md)

<span id="what-hyperpod-gives-the-trainer"></span>
<span id="job-recovery-and-checkpoints"></span>

??? question "Will training resume at the same step if a node is replaced?"
    HyperPod can recover a faulty GPU node, and the training operator can restart the job. To resume at the last saved step, the new pod must be able to read the previous checkpoint. The lab mounts `/outputs` on an `emptyDir` volume, which Kubernetes removes with the pod. Put checkpoints on shared storage if training needs to resume after node replacement. [HyperPod training jobs and checkpoints](../handson/scenarios/b/b1.md)

<span id="what-hyperpod-does-not-give-the-sandbox-tier"></span>
<span id="why-b2-changes-the-grading-workers-driver"></span>

??? question "Why change the driver only on the B2 grading workers?"
    gVisor’s `nvproxy` forwards GPU requests to supported NVIDIA driver versions. The lab's HyperPod image shipped with `595.112.07`, which the gVisor release used here did not support. We installed `580.178.04` on the two grading workers and rebooted them through HyperPod. The training worker accessed its GPU directly and kept its original driver. [Prepare the grading workers and verify CUDA](../handson/common/02_runtimes/b2_workers.md)

## Match the instance to the grading runtime { #instance-choice }

- **To grade GPU code on an A10G**, use gVisor on `g5.xlarge` in A and B1, or on `ml.g5.xlarge` in B2. If your target device is an L4, consider EC2 `g6.xlarge`. Check the node driver against gVisor’s supported versions and time both the reference code and the submission on the L4. [Set up a gVisor GPU sandbox](../handson/common/02_runtimes/gvisor.md)
- **For a GPU and a separate Linux kernel per sandbox**, add an EC2 `g4dn.metal` in A or B1. Kata + QEMU assigns one of the server’s physical T4s to each VM. [Attach a GPU to a Kata VM](../handson/common/02_runtimes/kata.md#kata-gpu)

<span id="quotas"></span>

## Quotas and hourly worker costs { #hourly-cost-of-the-hands-on-setups-estimate }

EC2 quotas count **vCPUs**. SageMaker HyperPod’s `for cluster usage` quotas count **instances of each type**. For example, B1 needs capacity for its two EC2 grading GPUs as well as a SageMaker quota for one `ml.g5.2xlarge` trainer.

| Default setup | Available EC2 quota | Available HyperPod quota | Workers (USD/hour) |
|---|---|---|---:|
| A | Standard 6, G/VT 16 | — | 3.416 |
| B1 | Standard 6, G/VT 8 | 1 `ml.g5.2xlarge` | 3.719 |
| B2 | No separate EC2 instances | 1 `ml.m5.xlarge`, 1 `ml.g5.2xlarge`, 2 `ml.g5.xlarge` | 4.561 |

The estimates use the lab’s On-Demand rates in `us-west-2` for A and B1 and in `us-east-1` for B2. The Standard quota for A and B1 includes two vCPUs for the `t4g.nano` SSM access instance. The cost column covers workers only. Budget separately for the access instance, EKS control plane, NAT gateway, storage and data transfer. [Cost breakdown](../production/08_cost.md) / [Clean up lab resources](../handson/cleanup.md)

??? note "When a lab adds nodes to the default setup"
    - **Switching gVisor versions during training in A** adds two `g5.xlarge` nodes while both pools are running. This brings G/VT to 24 vCPUs and adds USD 2.012 per hour in worker costs. [Switch grading pools during training](../handson/scenarios/a/pool_update.md)
    - **Adding Kata GPU to A or B1** adds one `g4dn.metal`, which needs another 96 G/VT vCPUs and costs USD 7.824 per hour at the lab rate. The temporary AMI builder also needs two Standard vCPUs while it runs. [Kata GPU lab](../handson/common/02_runtimes/kata.md#kata-gpu)

[Provision the cluster for your scenario](../handson/common/01_provision/index.md) / [Check the three SageMaker quotas for B2](../handson/common/01_provision/hyperpod.md)

??? note "If GPU capacity or budget is tight (optional scenario C)"
    Practice grading and switching pool versions with prepared submissions, without training a model. Use two `m6i.large` system workers and one `c8i.2xlarge` for grading. With nested virtualization enabled on the `c8i`, you can compare gVisor, Kata + QEMU and Kata + Cloud Hypervisor on CPU.

    Allow 14 EC2 Standard vCPUs including the access instance. The three workers cost about USD 0.567 per hour at the lab’s On-Demand rates. [CPU lab and cost breakdown](../handson/scenarios/c/index.md)

<span id="scope-and-limits"></span>

??? note "Run records and official documentation"
    - [AWS lab runs by scenario](../reference/sources.md#aws-run-record) / [Runtime benchmarks](../handson/benchmarks/index.md#runtime-results)
    - [HyperPod node recovery](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html) / [HyperPod training operator](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html)
    - [EC2 On-Demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/) / [SageMaker AI pricing](https://aws.amazon.com/sagemaker/ai/pricing/)
