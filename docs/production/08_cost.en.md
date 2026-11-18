# 08 Cost

**TL;DR** Cost splits into trainer GPUs, sandbox GPUs, the wait of empty bare-metal nodes, and the EKS control plane plus NAT gateway; the main levers are sizing the sandbox pool to the reward phase and returning empty nodes quickly (amounts are estimates from On-Demand list prices).

## Pain point

A `g4dn.metal` left running after the hands-on costs 7.824 USD per hour, or 375.552 USD over a 48-hour weekend. A pool fixed at a generous size keeps billing for sandbox GPUs that are busy only during the reward phase and idle during generation and updates. Billing is per node, so using 4 of the 8 T4s on a metal node doubles the price per T4 used, and two blue/green pools that overlap for long bill sandbox GPUs twice for that whole time.

![a: through the trainer's generation, reward and update phases the sandbox GPU is busy only during reward but bills per node throughout, and a pool kept after the run leaves g4dn.metal billing 7.824 USD per hour (375.552 USD over a 48-hour weekend). Using only 4 of the 8 T4s costs 1.956 USD/hour per T4 used. b: with the pool sized to the reward phase and replicas 0 after the run, the empty node is returned after consolidateAfter 30 min, at most 3.912 USD per empty period, and with all 8 T4s in use one T4 costs 0.978 USD/hour](../images/figures/production-08_cost.svg)

*Takeaway: Sandbox nodes bill per node whether busy or idle, and keep billing when left running after the run. Size the pool to the reward phase, scale it to 0 after the run so empty nodes go back quickly, and fill all 8 T4s of a metal node to halve the price per T4.*


## Why

- **Split the cost into four parts.** You can only pick where to cut when you can see which lever reduces which part.
- **Compute with public list prices only.** With no measured usage, amounts are estimates: price times hours.
- **State what the HyperPod premium buys for the trainer.** The EC2 price and the `ml.*` price of the same GPU sit side by side with the features the difference pays for.

**Before you start:** the instance choices in [04 Platforms and instances](../concepts/04_platforms_and_instances.md) and the NodePool settings in [01 Capacity and nodes](01_capacity_and_nodes.md) help.

??? note "Terms"
    - **On-Demand list price**: the public hourly price without commitments or discounts. Every amount on this page uses it.
    - **Savings Plans, Spot**: Savings Plans give a discount in exchange for a usage commitment; Spot instances use spare capacity at a lower price, and AWS can reclaim them.
    - **Per-node billing**: the whole node is billed for its hours, however many GPUs the pods use. Using 4 T4s of a `g4dn.metal` still costs the price of 8.
    - **consolidateAfter**: how long Karpenter waits for new work before returning an empty node.
    - **warm placeholder**: an empty pod that keeps a slow-booting metal node ready. The price of one node keeps running.
    - **NAT gateway**: the managed device through which nodes in private subnets reach the internet (image pulls, model downloads). It charges per hour and per GB processed.

    More terms are in the [Glossary](../reference/glossary.md).

## Cost model

```text
hourly cost ≈ trainer GPU nodes
            + sandbox GPU nodes (whole nodes, billed whether busy or idle)
            + idle bare-metal time (empty g4dn.metal waiting for consolidation)
            + EKS control plane + NAT gateway (hourly + per GB processed)
            + smaller items (EBS volumes, FSx, ECR storage, CloudWatch)
```

- **Trainer**: `g5.2xlarge` in scenario A, `ml.g5.2xlarge` in scenario B, an 8-GPU node in the production veRL example.
- **Sandboxes**: gVisor runs one sandbox per `g5.xlarge` node; Kata GPU runs 8 T4s per `g4dn.metal`.
- **Metal waiting time**: the Karpenter `sandbox-kata-gpu` NodePool waits 30 minutes before returning an empty node.
- **Control plane and NAT**: nodes sit in private subnets (`privateNetworking: true`), so image pulls and model downloads pass the NAT gateway (`gateway: Single`), billed per hour and per GB processed. Sandbox pods have no egress and do not use the NAT.

## Prices (On-Demand list prices)

| Instance | Use in this repo | USD/hour |
|---|---|---|
| `m6i.large` | System nodes (2) | 0.096 |
| `g5.xlarge` | gVisor sandbox (1x A10G) | 1.006 |
| `g5.2xlarge` | Scenario A trainer (1x A10G), alternative in the gVisor NodePool | 1.212 |
| `g6.xlarge`, `g6.2xlarge` | Alternative instances (1x L4); set them with `GVISOR_INSTANCE_TYPE` and `TRAINER_INSTANCE_TYPE` | 0.8048, 0.9776 |
| `g4dn.metal` | Kata GPU sandboxes (8x T4) | 7.824 (Seoul 9.624) |
| `c8i.2xlarge` | Kata CPU (nested virtualization) | 0.37484 |
| `g6e.12xlarge`, `g6e.48xlarge`, `p5.48xlarge` | Production trainer NodePool candidates | 10.49264, 30.13118, 55.04 |
| `ml.g5.2xlarge` | Scenario B trainer (HyperPod) | 1.515 |

!!! warning "Prices for estimates only"
    These are On-Demand list prices for us-east-1 and us-west-2; Savings Plans, Spot and other Regions differ. For the EKS control plane, NAT gateway, EBS, FSx for Lustre, ECR and CloudWatch, see their pricing pages.

## Levers

### Size the sandbox pool to the reward phase

Size the pool for the reward burst and scale it to zero between runs. Scaling every step does not fit: a GPU node takes minutes to join, and bare metal longer.

```text
step_time(P)     ≈ t_generate + t_update + ceil(N / P) × t_eval
cost_per_step(P) ≈ (C_trainer + P × C_sandbox + C_fixed) × step_time(P)
```

Increase `P` only while `cost_per_step` keeps going down. Measure `t_eval` with `scripts/ops/bench.sh`, the step time from the trainer log, and the real utilization of sandbox GPUs with `avg_over_time(sandbox_busy[1h])`. For example, adding one more `g5.xlarge` to the hands-on minimal path (EC2 subtotal 3.416 USD/hour) raises the hourly cost to 4.422 USD, so the step time must drop by more than about 23% for the cost per step to fall (3.416 ÷ 4.422 ≈ 0.773); fixed costs such as the control plane lower that threshold slightly.

### Return empty nodes quickly

| NodePool | Consolidation | Maximum waiting cost of one empty period |
|---|---|---|
| `sandbox-gvisor` | `WhenEmpty`, 10 minutes | `g5.xlarge` 0.1677 USD |
| `sandbox-kata-gpu` | `WhenEmpty`, 30 minutes | `g4dn.metal` 3.912 USD |
| `sandbox-kata-cpu` | `WhenEmptyOrUnderutilized`, 5 minutes | `c8i.2xlarge` 0.0312 USD |
| `trainer` | `WhenEmpty`, 15 minutes | For example `g6e.48xlarge` 7.5328 USD |

`WhenEmpty` only considers nodes without workload pods (karpenter.sh docs). The hands-on EKS managed node groups (CDK stack) have no consolidation and bill until you scale them down or delete them, so scale them down yourself (for example `aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu --scaling-config minSize=0,maxSize=1,desiredSize=0`).

### The 30-minute metal wait and the warm placeholder

A metal node takes minutes to join the cluster and kata-deploy more minutes to install, so the 30-minute wait spends at most 3.912 USD per empty period to avoid a cold start when the pool comes back within 30 minutes (blue/green, a rollback window). When a run ends and no pool is coming back, shrink the node group or `consolidateAfter`.

The placeholder in `k8s/production/warm-capacity.yaml` is a low-priority pause pod (60 CPUs, 200 GiB of memory) that keeps one spare metal node. When a sandbox pod needs room, the placeholder is preempted within seconds and Karpenter starts a new spare in the background, but the spare bills all the time, at 7.824 USD per hour or 187.776 USD per day. Use it only for runs whose pool spans several metal nodes or where a node failure must not stall rewards, and otherwise turn it off with `kubectl -n sandbox scale deployment/kata-metal-warm-placeholder --replicas=0`. Two Kata pools of 4 (blue/green) fit on one metal node (208 GiB of memory for 8 pods on a 384 GiB node), so that switch works without the placeholder.

### Runtime and GPU choice

| Setup | Node price | Hourly price per GPU | Condition |
|---|---|---|---|
| gVisor, `g5.xlarge` | 1.006 | 1.006 (A10G) | One sandbox per node |
| gVisor, `g5.2xlarge` | 1.212 | 1.212 (A10G) | When the NodePool cannot get `g5.xlarge`; about 20% more |
| gVisor, `g6.xlarge` (alternative) | 0.8048 | 0.8048 (L4) | 20% less than `g5.xlarge` |
| Kata, `g4dn.metal`, 8 used | 7.824 | 0.978 (T4) | All 8 T4s in use |
| Kata, `g4dn.metal`, 4 used | 7.824 | 1.956 (per T4 used) | `KATA_QEMU_REPLICAS` default of 4 |
| Kata, Seoul `g4dn.metal`, 8 used | 9.624 | 1.203 (T4) | |

Do not choose by price per GPU alone. A10G and T4 speedups cannot be compared, and the isolation levels differ. gVisor nvproxy filters driver ioctls through an allowlist, but it is less effective than a VM boundary against vulnerabilities in the driver itself, while Kata hands the whole GPU to a VM. Decide the runtime from your isolation requirement first, and for Kata size the pool to fill the 8 T4s of a metal node.

### CPU tier and Spot

- **Kata CPU tier (c8i)**: nested virtualization runs Kata without `.metal`. In the hands-on it is a cheap way to practice Kata before turning on `g4dn.metal`; in production it can filter work that needs no GPU (static checks, nvcc compilation) in front of the GPU tier. The CPU pools (`gvisor-cpu`, `kata-*-cpu`) are in the routing table and the reward loop of scenario C ([10 CPU-only path on c8i](../handson/10_cpu_only.md)) uses them, but this two-stage setup is not wired.
- **Savings already built in**: `KernelRewards` scores duplicate completions within a batch once, and completions without code or rejected by the static policy are never sent to a sandbox.
- **Spot only for the CPU tier**: in `infra/karpenter/nodepools.yaml` the only NodePool that allows Spot is `sandbox-kata-cpu`. On the CPU tier an interruption ends in a retry on another pod, but a GPU sandbox interrupted mid-evaluation turns that sample into `sandbox_error` (excluded in TRL, format score only in veRL), and getting GPU capacity back takes minutes. If you want Spot on GPU tiers, put `sandbox_error` alarms and checkpoints on shared storage in place first.

### Trainer: HyperPod `ml.*` versus EC2

| EC2 | USD/hour | HyperPod | USD/hour | Difference | Ratio |
|---|---|---|---|---|---|
| `g4dn.xlarge` | 0.526 | `ml.g4dn.xlarge` | 0.7364 | 0.2104 | 1.40 |
| `g5.xlarge` | 1.006 | `ml.g5.xlarge` | 1.408 | 0.402 | about 1.40 |
| `g5.2xlarge` | 1.212 | `ml.g5.2xlarge` | 1.515 | 0.303 | 1.25 |
| `g6.xlarge` | 0.8048 | `ml.g6.xlarge` | 1.127 | 0.3222 | about 1.40 |
| `g6.2xlarge` | 0.9776 | `ml.g6.2xlarge` | 1.222 | 0.2444 | 1.25 |
| `g6e.xlarge` | 1.861 | `ml.g6e.xlarge` | 2.61 | 0.749 | about 1.40 |

The difference buys a managed node lifecycle: the health monitoring agent, deep health checks (InstanceStress, InstanceConnectivity), `NodeRecovery: Automatic`, which reboots or replaces faulty nodes, and job restarts with log-based hang detection from the training operator.

On EC2 (scenario A) you can also build node replacement itself with managed node groups or Karpenter; the difference is whether you get GPU-level deep health checks and job restarts as managed features. Compare "difference × run hours" with "expected failures × (progress lost since the last checkpoint + recovery time) × cluster cost per hour + operator time" to decide. For the single hands-on node (`g5.2xlarge` and `ml.g5.2xlarge`) the difference is 0.303 USD per hour, or 7.272 USD for a 24-hour run.

Also check that HyperPod uses "ml.<type> for cluster usage" quotas separate from EC2, and that the EC2 "Running On-Demand G and VT instances" quota is counted in vCPUs and can default to 0 (`g4dn.metal` needs 96 vCPUs).

!!! question "❓ Misconception: Kata on g4dn.metal is far more expensive per GPU"
    With all 8 T4s in use, one T4 costs 0.978 USD per hour, not far from the A10G of a `g5.xlarge` (1.006 USD per hour). What raises the cost is per-node billing (1.956 USD per T4 used with only 4 in use), plus the empty 30 minutes and the placeholder on top.

!!! question "❓ Misconception: HyperPod adds a premium to the whole cluster"
    In this design the `ml.*` price applies only to the HyperPod instance group (the trainer). The sandboxes are EC2 nodes in the same EKS cluster and bill at EC2 prices, the control plane follows EKS pricing, and the NAT and storage follow their own prices.

## Hourly estimate: hands-on paths

The minimal path is what `scripts/02_create_cluster.sh` creates (scenario A, gVisor only); the full path adds the Kata CPU node (`WITH_KATA_CPU=1`, `scripts/kata/cpu_nodes.sh`) and the Kata GPU node (`WITH_KATA_GPU=1`, `scripts/kata/gpu_nodes.sh`). Both node groups join the CDK stack when you set those values and run `02_create_cluster.sh` again.

| Item | Count | Price (USD/hour) | USD per hour |
|---|---|---|---|
| `m6i.large` (system) | 2 | 0.096 | 0.192 |
| `g5.xlarge` (gVisor sandboxes) | 2 | 1.006 | 2.012 |
| `g5.2xlarge` (trainer, scenario A) | 1 | 1.212 | 1.212 |
| **Minimal path EC2 subtotal** | | | **3.416** |
| `c8i.2xlarge` (Kata CPU) | 1 | 0.37484 | 0.37484 |
| `g4dn.metal` (Kata GPU) | 1 | 7.824 | 7.824 |
| **Full path EC2 subtotal** | | | **11.61484** |
| EKS control plane, NAT gateway, EBS gp3, SSM access instance (`t4g.nano`), KMS key | | See each pricing page | Extra |

- Scenario B uses `ml.g5.2xlarge` instead of `g5.2xlarge`, so the minimal path is 3.719 and the full path 11.91784 USD per hour.
- Worked example: 8 hours of the minimal path plus 2 hours of `g4dn.metal` is 3.416 × 8 + 7.824 × 2 = 42.976 USD (EC2 only; the durations are assumptions).
- After the cluster is deleted, the EBS snapshot of the Kata AMI and the ECR images can remain and keep billing. `scripts/08_cleanup.sh` asks before deregistering the AMI, and `--images` deletes the ECR repositories as well.

As a production veRL example, 16 gVisor sandboxes next to a `g6e.48xlarge` trainer (30.13118 USD per hour) cost 16.096 USD per hour for the sandboxes alone, about 53% of the trainer, and 8 sandboxes cost 8.048 USD per hour (about 27%). That is a significant share, so set the pool size with the cost-per-step rule above.

## How to verify

The first command lists the cluster's nodes with instance type, NodePool and role label; the second prints a table of the EC2 instances tagged `project=gpu-sandbox-on-aws`. It needs `AWS_REGION`, so run `source scripts/config.env` first.

```bash
# what is running now, and from which NodePool or node group
kubectl get nodes -L node.kubernetes.io/instance-type,karpenter.sh/nodepool,gpusandbox/role
# instances tagged by this asset (the same check scripts/08_cleanup.sh prints at the end)
aws ec2 describe-instances --region "${AWS_REGION}" \
  --filters "Name=tag:project,Values=gpu-sandbox-on-aws" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name]' --output table
```

**What to look for:**

- Count the GPU nodes (`g4dn.metal`, `g5.*`, `g6.*`, `g6e.*`, `p5.*`) in the INSTANCE-TYPE column of the first command. That count times the prices above is roughly your hourly EC2 cost.
- After the hands-on is finished, the table from the second command should be empty.

**If it fails:** if billing continues after cleanup, see the cleanup and cost table in [Troubleshooting](../reference/troubleshooting.md).

When you finish the hands-on, run [99 Cleanup](../handson/99_cleanup.md) (for scenario B, run `scripts/hyperpod/delete.sh` first). Related pages: [04 Platforms and instances](../concepts/04_platforms_and_instances.md), [01 Capacity and nodes](01_capacity_and_nodes.md), [06 Scaling with veRL](06_scaling_with_verl.md).

## Scope and limits

- **Every amount is a calculation.** This repository has no usage or billing measured on AWS.
- **Some items are left out.** The EKS control plane, NAT gateway, EBS, FSx for Lustre, ECR and CloudWatch charges are not in the totals.
- **Measure step times yourself.** The cost-per-step formula in "Levers" assumes you know `t_generate`, `t_update` and `t_eval`, which differ per run.

??? note "References"
    | Topic | Link |
    |---|---|
    | EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
    | SageMaker AI pricing (HyperPod `ml.*`) | https://aws.amazon.com/sagemaker/ai/pricing/ |
    | EKS pricing (control plane) | https://aws.amazon.com/eks/pricing/ |
    | Karpenter (AWS provider) | https://github.com/aws/karpenter-provider-aws |
    | Cleanup script | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/08_cleanup.sh |

    All sources: [this page in All references](../reference/references.md#ref-production-08-cost)
