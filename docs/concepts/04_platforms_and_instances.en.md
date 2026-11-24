# Platforms and instances

!!! info "TL;DR"
    Choose training nodes and sandbox nodes separately. HyperPod can help recover a long training job. The sandbox still needs a node compatible with its runtime and target GPU.

## Training and grading on separate nodes

The trainer generates answers and updates the model. The sandbox executes submissions, so its node must match the isolation and measurement requirements. Amazon EKS manages the Kubernetes cluster. EC2 provides worker instances, and HyperPod can manage training nodes that join the same cluster.

## Compare scenarios A, B1, B2, and C

| Scenario | Training | Sandbox | Typical use |
|---|---|---|---|
| A | EC2 | EC2 | Connect training and scoring in EKS |
| B1 | HyperPod | EC2 | Add node recovery and job restart for training |
| B2 | HyperPod `trainer` | HyperPod `sandbox` | Run system pods, training and grading on three dedicated HyperPod groups |
| C | Simulator without a model | CPU pools on EC2 `c8i.2xlarge` | Compare runtimes, score submissions, and switch versions without GPUs |

A, B1 and C ran in `us-west-2`. The [managed B2 walkthrough](../handson/scenarios/b/b2.md) ran in `us-east-1`.

B1 keeps the runtime requirements independent from trainer recovery. Its EC2 sandbox nodes can use a driver supported by gVisor or the virtualization setup required by Kata. Managed B2 installs a compatible NVIDIA driver on the two registered grading workers and activates it with a HyperPod reboot.

## Architecture by scenario

Select a tab to view the scenario.

=== "A: EC2 GPU"

    ![The trainer and GPU sandboxes run in separate EC2 node groups in the same EKS cluster.](../images/architecture/scenario-a.drawio.png)

    **Diagram** Follow `kubectl tunnel` from the workstation through SSM to the private EKS API. During training, the `GRPO trainer Job` sends submissions to the gVisor pool along the `kernel code` arrow. The pool checks correctness and speed on the GPU and returns a verdict, which the trainer uses to compute rewards.

    **Difference** This is the baseline GPU configuration. Both training and scoring run on EC2. [Scenario A exercise](../handson/common/01_provision/cdk.md)

=== "B1: HyperPod training"

    ![The HyperPod trainer and EC2 GPU sandboxes join the same EKS cluster.](../images/architecture/scenario-b1.drawio.png)

    **Diagram** The training operator places the `HyperPodPyTorchJob` on a HyperPod trainer node. The `kernel code` arrow still leads to the EC2 pool in the same cluster, as in A. The sandbox executes the submission and returns the verdict over the same evaluation path.

    **Difference** The trainer moves from EC2 to HyperPod for node recovery and Job restart. The scoring pool stays on EC2. [Scenario B1 exercise](../handson/scenarios/b/b1.md)

=== "B2 (All workers on HyperPod)"

    [![Amazon EKS schedules pods on the HyperPod system, trainer and sandbox instance groups](../images/architecture/scenario-b2.drawio.png?layout=aws)](../images/architecture/scenario-b2.drawio.png?layout=aws)

    `system` runs CoreDNS, `trainer` runs the GRPO job and `sandbox` grades the code with gVisor. The Kubernetes API is provided by EKS. [B2 deployment](../handson/scenarios/b/b2.md)

=== "C: CPU only"

    ![The simulator on the system nodes sends evaluations to CPU sandbox pools on a c8i node.](../images/architecture/scenario-c.drawio.png)

    **Diagram** Follow `golden code` from `simulate and probe Jobs` on the system nodes to the Kata CPU v1 pool on the c8i node. The simulator sends examples with known verdicts and logs v2 results after routing changes. The gVisor and Kata with QEMU CPU pools on the same node also receive verification and benchmark requests.

    **Difference** Use gVisor and Kata to practice scoring and version switches without GPUs or model training. [Scenario C exercise](../handson/scenarios/c/index.md)

## Job recovery and checkpoints

HyperPod can recover a faulty node and the training operator can restart a Job. Resuming from the previous training state requires a checkpoint accessible to the replacement pod. The exercise uses `emptyDir`, which is removed with the pod. See the [HyperPod exercise](../handson/scenarios/b/b1.md) and [runtime comparison](02_isolation_runtimes.md).

## Distinguish the training GPU from the grading GPUs in B1

The A10G in an `ml.g5.2xlarge` generated answers and updated the model. Two separate gVisor sandboxes on EC2 `g5.xlarge` instances executed the 12 submissions. The trainer Job reached `Completed`. One submission was correct. Job completion and the verdicts answer different questions. [Placement and completion logs](../handson/scenarios/b/b1.md#how-to-verify)

What can you learn by changing only the client? With training stopped, an EKS system node and the HyperPod trainer each submitted the fixed kernel 32 times to the same pool. Their median grading times were 9.918 s and 9.937 s, with pool throughput of 0.199 evaluations/s for each client. This records successful scoring through both clients. Recovery after node replacement would require a separate checkpoint-and-resume test. [B1 client comparison](../handson/benchmarks/index.md#hyperpod-b1)

<a id="further-detail"></a>

## What HyperPod gives the trainer

- **Node recovery:** the cluster is created with `NodeRecovery: Automatic` (`infra/hyperpod/cluster.json.tpl`). Node health shows up as the `sagemaker.amazonaws.com/node-health-status` label (`Schedulable`, `Unschedulable` and others), and the trainer job is placed only on `Schedulable` nodes.
- **Deep health checks:** an instance group's `OnStartDeepHealthChecks` can enable `InstanceStress` (GPU/NVLink count, DCGM diagnostics, EFA and others) and `InstanceConnectivity` (NCCL and others). This asset's template does not set this field; if you add it, see the taint constraint below.
- **Job restarts and hang detection:** the training operator add-on (`amazon-sagemaker-hyperpod-training-operator`) runs `HyperPodPyTorchJob`, with `jobMaxRetryCount: 3` and a `restartPolicy` (`numRestartBeforeFullJobRestart: 1`, `evalPeriodSeconds: 3600`, `maxFullJobRestarts: 2`). There are two log-pattern detections.
    - **`JobStart`**: it expects a `"event": "routing"` line within 1200 seconds.
    - **`RewardStalled`**: it expects a `"event": "reward_batch"` line every 1800 seconds.

    The HyperPod trainer image installs `hyperpod-elastic-agent` 1.1.3. The Job starts training with `hyperpodrun`.

- **Checkpoint resume:** after a restart, `train_grpo.py` resumes from the latest checkpoint in its output directory. The hands-on keeps `/outputs` on an emptyDir (a scratch volume that disappears with the pod), so resuming after a node replacement needs shared storage (an FSx for Lustre PVC, for example).
- **Other features:** the `hyp` CLI (`pip install sagemaker-hyperpod`), the task governance and observability add-ons, and Karpenter-based autoscaling (`AutoScalerType: Karpenter`, `NodeProvisioningMode: Continuous`).

!!! warning "Training operator and Kubernetes versions"
    This asset uses Kubernetes 1.36. HyperPod supports this EKS version. Before creating the cluster, check add-on compatibility with the read-only command below.

    ```bash
    aws eks describe-addon-versions \
      --addon-name amazon-sagemaker-hyperpod-training-operator \
      --kubernetes-version 1.36
    ```

    **What to look for:**

    - **If the `addons[0].addonVersions` list in the JSON has at least one version**: a 1.36-compatible add-on exists.
    - **If the list is empty**: consider a lower `K8S_VERSION`.

??? info "HyperPod (EKS) prerequisites in short"
    - You need EKS authentication mode `API` or `API_AND_CONFIG_MAP`, VPC CNI 1.18.3 or later, and private subnets.
    - **When creating through the API**: first install the HyperPod dependency Helm chart (`helm_chart/HyperPodHelmChart` in `sagemaker-hyperpod-cli`), which installs the health monitoring agent, deep health check RBAC, job auto-restart, the MPI operator, nvidia-device-plugin, the Neuron and EFA plugins, and Kueue.
    - **IAM roles**: HyperPod nodes and EKS nodes use different IAM roles, and the execution role gets `AmazonSageMakerClusterInstanceRolePolicy` plus an EC2 ENI and ECR inline policy.

## What HyperPod does not give the sandbox tier

| Item | Fact | This asset's answer |
|---|---|---|
| Sandbox runtime | nvproxy needs a supported host driver. These HyperPod instances lack the virtualization devices required for Kata GPU. | B1 runs gVisor on EC2. B2 installs a compatible driver on its HyperPod `sandbox` group. |
| Dedicated node taints | "You cannot add custom taints to nodes in instance groups with DeepHealthChecks turned on." | sandbox nodes are separated by the `gpusandbox/role` taint on EC2 node groups |
| Isolation checks | deep health checks test hardware (GPU, NVLink, EFA, NCCL), not sandbox isolation (egress denial and so on) | Ready only after egress denial is verified, `scripts/ops/verify.sh` |
| Pod density | The B1 `ml.g5.2xlarge` node advertised 14 pod slots. The AMI and VPC CNI version determine whether the node can attach additional ENIs. | B1 runs only the trainer on HyperPod nodes. The B2 `sandbox` group runs one sandbox pod per node |
| CPU node replacement | "Node auto-replacement is not supported for CPU instances." | B2 runs system pods on a HyperPod CPU worker. Scenario C grades on EC2 `c8i` |
| Version pinning, parity, gateway | not HyperPod features | code in this repository |

On HyperPod nodes, by default only hostNetwork pods can reach IMDS. That default favors sandboxes, but it does not lift the constraints above.

## Why B2 changes the grading workers’ driver

The gVisor GPU interface, nvproxy, supports specific driver versions. The default image in the B2 run shipped `595.112.07`, which gVisor `20261109.0` did not recognize. We installed `580.178.04` on the two grading workers, rebooted them through HyperPod and ran CUDA on the A10G in each gVisor pod. The training worker used its default driver.

[Worker preparation and CUDA output](../handson/scenarios/b/b2.md), [Fixed-kernel benchmark](../handson/benchmarks/index.md#hyperpod-b2)

## Instance choice

| Role | Choice | Reason | On-Demand (USD/hour) |
|---|---|---|---|
| Trainer (A) | `g5.2xlarge` (1 x A10G 24 GB, 8 vCPU, 32 GiB) | configured to fit a 1.5B model + LoRA + vLLM colocate on one A10G (`vllm_gpu_memory_utilization` 0.35). A 5-step GRPO run finished in the practice account | 1.212 |
| Trainer (B) | `ml.g5.2xlarge` | the same hardware through HyperPod. About 25% higher at list prices (1.515 / 1.212 = 1.25) | 1.515 |
| gVisor sandbox | `g5.xlarge` (1 x A10G), one sandbox per node | Tested on A10G. For the L4 alternative (`g6`) and driver compatibility, see the [gVisor lab](../handson/common/02_runtimes/gvisor.md#driver-and-verification-scope-of-g5-nodes). | 1.006 |
| Kata GPU sandbox | `g4dn.metal` (8 x T4, 96 vCPU, 384 GiB), one T4 per VM | the only `.metal` type with an x86 NVIDIA GPU | 7.824 (Seoul 9.624) |
| Kata CPU sandbox | `c8i.2xlarge` (nested virtualization) | `/dev/kvm` without `.metal`. Kata rehearsal and the CPU tier | 0.37484 |
| System | `m6i.large` x 2 | CoreDNS and controllers | 0.096 (each) |

Prices are On-Demand list prices in us-east-1 and us-west-2.

??? info "Prices and GPUs of other candidates"
    | EC2 | GPU | USD/hour |
    |---|---|---|
    | `g4dn.xlarge` | 1 x T4 | 0.526 |
    | `g4dn.2xlarge` | 1 x T4 | 0.752 |
    | `g6.xlarge` | 1 x L4 | 0.8048 |
    | `g6.2xlarge` | 1 x L4 | 0.9776 |
    | `g6e.xlarge` | 1 x L40S | 1.861 |
    | `g6e.12xlarge` | 4 x L40S | 10.49264 |
    | `g6e.48xlarge` | 8 x L40S | 30.13118 |
    | `p4d.24xlarge` | 8 x A100 | 21.95764 |
    | `p5.48xlarge` | 8 x H100 | 55.04 |
    | `g5g.metal` | 2 x T4g (arm64) | 2.744 |
    | `c5.metal` | none | 4.08 |
    | `t3.large` | none | 0.0832 |

    | HyperPod | USD/hour |
    |---|---|
    | `ml.g4dn.xlarge` | 0.7364 |
    | `ml.g6.xlarge` | 1.127 |
    | `ml.g6.2xlarge` | 1.222 |
    | `ml.g6.4xlarge` | 1.654 |
    | `ml.g5.xlarge` | 1.408 |
    | `ml.g5.8xlarge` | 3.06 |
    | `ml.g6e.xlarge` | 2.61 |

    The production trainer NodePool candidates (`infra/karpenter/nodepools.yaml`) are `g6e.12xlarge`, `g6e.48xlarge` and `p5.48xlarge`.

## Quotas

| Quota (vCPU-based) | Needed for the hands-on | Notes |
|---|---|---|
| Running On-Demand G and VT instances | A: 16 (`g5.2xlarge` 8 + `g5.xlarge` 4 x 2), B1: 8 (`g5.xlarge` 4 x 2), B2: 0. Kata GPU adds `g4dn.metal` 96 | documented default can be 0 |
| Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances | A/B1/C: 6 (`m6i.large` 2 x 2 + the SSM access `t4g.nano` 2). Additional needs are in the list below the table | documented default is 5 |
| `ml.m5.xlarge for cluster usage` | 1 (B2) | HyperPod `system` group. Managed B2 requires no standalone EC2 worker quota. |
| `ml.g5.2xlarge for cluster usage` | 1 (B) | HyperPod uses `ml.<type> for cluster usage` quotas |
| `ml.g5.xlarge for cluster usage` | 2 (B2) | the B2 `sandbox` instance group (`HYPERPOD_SANDBOX_COUNT`) |

The Standard quota needs more in these cases.

- **If you practice Kata CPU**: it adds `c8i.2xlarge` 8 (14 in total).
- **While the earlier CDK B2 or Kata GPU AMI is being built**: the builder `m6i.large` needs 2 more (8, or 16 with the Kata CPU node).

`scripts/01_check_prereqs.sh` prints, read-only, the G and VT quota, nested virtualization support for `c8i.2xlarge` and which AZs offer each GPU type. How to run it and what to check are in section 5 of [Getting started](../handson/start.md).

## Hourly cost of the hands-on setups (estimate)

<span id="scope-and-limits"></span>

??? note "Runs behind the scenario estimates"
    On the A10G, scenario A completed five GRPO steps using a 1.5B model, LoRA and colocated vLLM with one verified gVisor grader. A separate cluster ran four Kata + QEMU graders on `g4dn.metal` and benchmarked two GPU pools and three CPU pools with `scripts/ops/bench.sh 32`. Scenario A also switched grading versions during training. Managed B2 completed one step on HyperPod. [AWS run record](../reference/sources.md#aws-run-record), [Switch record](../handson/scenarios/a/pool_update.md#switch-batches)

    For the CPU lab, `c8i.2xlarge` costs USD 0.37484 per hour in us-east-1 and us-west-2, or USD 0.42336 in Seoul. [CPU lab](../handson/scenarios/c/index.md)

| Setup | Nodes | Node subtotal (USD/hour) |
|---|---|---|
| A base (gVisor + trainer) | `m6i.large` x 2 + `g5.xlarge` x 2 + `g5.2xlarge` | 0.192 + 2.012 + 1.212 = about 3.42 |
| A + Kata CPU | A base + `c8i.2xlarge` x 1 | about 3.79 |
| A + Kata GPU | A base + `g4dn.metal` x 1 | 3.416 + 7.824 = about 11.24 |
| B1 (HyperPod trainer) | `m6i.large` x 2 + `g5.xlarge` x 2 + `ml.g5.2xlarge` | 0.192 + 2.012 + 1.515 = about 3.72 |

The table is an estimate from list prices and leaves out the EKS control plane, NAT gateway, the SSM access `t4g.nano`, EBS, data transfer, ECR and CloudWatch.

!!! warning "Scale `g4dn.metal` to zero when you are not using it"
    In the A + Kata GPU setup a single `g4dn.metal` is about 70% of the node cost (7.824 / 11.24). When you are not using it, scale the node group to zero with the command below, and run [Cleanup](../handson/cleanup.md) when you finish.

    ```bash
    aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu \
      --scaling-config minSize=0,maxSize=1,desiredSize=0
    ```

    **What to look for:**

    - After a few minutes, `kubectl get nodes -l gpusandbox/kata-gpu=true` (with `cdk/tunnel.sh` running) lists no nodes.
    - **If `CLUSTER_NAME` is not set in your shell**: run `source scripts/config.env` first.

!!! question "❓ Misconception: with HyperPod, HyperPod manages the sandboxes too"
    HyperPod's node recovery, deep health checks and job restarts are resiliency features for nodes and jobs. Node recovery is a cluster setting, so it also covers B2's `sandbox` group, but HyperPod does not install sandbox runtimes, verify isolation or pin versions.

!!! question "❓ Misconception: T4 is cheaper, so make the gVisor nodes `g4dn`"
    `g4dn.xlarge` (0.526) is cheaper than `g5.xlarge` (1.006). `g4dn` has the same driver condition as `g5` (the AMI loads the proprietary kernel module with GSP off), so the driver flavor is not a reason to exclude it, but this asset has not tested gVisor on T4, so it stays unverified. T4 serves as the Kata + QEMU GPU (`g4dn.metal`); to use it with gVisor, verify it yourself.

??? note "References"
    | Topic | Link |
    |---|---|
    | HyperPod resiliency, deep health checks | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html |
    | HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
    | EC2 accelerated computing instance specifications, quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html , https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
    | Pricing (EC2, SageMaker AI) | https://aws.amazon.com/ec2/pricing/on-demand/ , https://aws.amazon.com/sagemaker/ai/pricing/ |
    | This asset's HyperPod template and check script | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/cluster.json.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh |

    [Selected references on this topic](../reference/references.md#ref-concepts-04-platforms-and-instances)
