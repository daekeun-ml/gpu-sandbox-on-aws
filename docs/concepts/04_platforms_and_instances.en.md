# Platforms and instances

!!! info "TL;DR"
    In Scenarios A and B1 the sandboxes stay on EC2 nodes and only the trainer moves between EC2 (`g5.2xlarge`, Scenario A) and HyperPod (`ml.g5.2xlarge`, Scenario B1). The experimental B2 puts the gVisor sandboxes in a HyperPod group `sandbox` that runs a custom AMI; gVisor uses `g5.xlarge`, Kata GPU `g4dn.metal` and Kata CPU `c8i.2xlarge`.

## Pain point

Once you choose HyperPod it seems natural to put the sandboxes on HyperPod nodes too, but with the default HyperPod AMI, driver and `.metal` constraints make that impossible. The instance criteria are unclear as well. T4 (`g4dn`) looks cheap but is unverified in this asset's gVisor setup, and the `.metal` type that Kata GPU needs has a high hourly price. In new accounts the GPU On-Demand quotas can be 0, so cluster creation can stop at the node stage.

![Two panels. a: putting the trainer (ml.g5.2xlarge) and the sandboxes together in a default-AMI HyperPod instance group of an EKS cluster fails: the gVisor sandbox because driver 595.91.07 is unknown, the Kata sandbox because there is no ml.*.metal and no nested virtualization (red). b B1: in the same EKS cluster only the trainer sits in the HyperPod instance group, and the gVisor sandbox (g5.xlarge) and the Kata sandbox (g4dn.metal for GPU, c8i.2xlarge for CPU) sit in EC2 node groups.](../images/figures/concepts-04_platforms_and_instances.svg)

*Takeaway: gVisor and Kata are both blocked on HyperPod nodes with the default AMI, so B1 puts only the trainer on HyperPod and keeps the sandboxes on EC2 nodes in the same cluster. B2, which runs gVisor sandboxes on a HyperPod group with a custom AMI and a different driver, is experimental.*


## Why

- **Who handles trainer node failures differs by scenario.** In A you build it yourself; in B1 and B2 HyperPod handles node recovery and health monitoring.
- **The sandbox runtime, isolation checks and scoring versions are not HyperPod features.** This asset's code handles them. HyperPod node recovery is a cluster setting, so it also covers the B2 `sandbox` group.

**Before you start:** look at the "Where each runtime can run on AWS" table in [02 Isolation runtimes](02_isolation_runtimes.md) first. Unfamiliar terms are in the "Terms" box below and in the [Glossary](../reference/glossary.md).

??? note "Terms (expand if a word is new to you)"
    - **SageMaker HyperPod**: an AWS service that manages GPU clusters for long training runs. Here it runs in EKS orchestrator mode, which attaches its nodes to an existing EKS cluster.
    - **Instance group**: a set of nodes of the same instance type inside a HyperPod cluster.
    - **NodeRecovery, deep health check**: the HyperPod setting that replaces faulty nodes automatically, and checks that test hardware such as GPUs and the network in depth.
    - **HyperPodPyTorchJob, training operator**: the Kubernetes resource that defines a training job on HyperPod, and the EKS add-on that runs and restarts it.
    - **Lifecycle script**: a setup script that runs when a HyperPod node is first created. It is read from an S3 bucket.
    - **Execution role**: the IAM role HyperPod nodes use to call AWS APIs.
    - **Taint, toleration**: a taint is a mark on a node that says "only pods that tolerate this may come"; a toleration is the pod setting that declares it tolerates that mark.
    - **ENI**: a virtual network card attached to an EC2 instance. The VPC CNI hands the ENI's IPs to pods, so the ENI count limits the pod count.
    - **IMDS, hostNetwork**: IMDS is the EC2 instance metadata service (the address that hands out node credentials); a hostNetwork pod uses the node's network directly.
    - **On-Demand list price**: the public hourly price without a commitment. Discounts and taxes are not included.

## Scenarios A, B1 and B2 compared

| Item | A. EC2 self-managed | B1. HyperPod (default) | B2. HyperPod (experimental) |
|---|---|---|---|
| Trainer location | EC2 GPU node in EKS, `g5.2xlarge` (A10G 24 GB, 8 vCPU, 32 GiB) | HyperPod instance group `ml.g5.2xlarge` attached to the same EKS cluster (HyperPod EKS orchestrator) | same as B1 |
| GPU sandbox location | EC2 nodes in the same cluster | EC2 nodes in the same cluster | gVisor on the HyperPod instance group `sandbox` (`ml.g5.xlarge`) |
| Trainer node failures | you build it (GPU fault detection, node replacement, job restarts) | `NodeRecovery: Automatic`, health monitoring agent, deep health checks (optional) | same as B1 |
| Trainer job | Kubernetes Job (`k8s/trainer/job-grpo.yaml.tpl`) | `HyperPodPyTorchJob` (`k8s/trainer/hyperpod-job-grpo.yaml.tpl`) | same as B1 |
| Extra setup | none | HyperPod dependency Helm chart, execution role, lifecycle-script bucket, training operator add-on, a trainer image with `hyperpodrun` | B1 + a custom AMI with the driver replaced by 580.178.04 (`scripts/hyperpod/build_b2_ami.sh`) and the `sandbox` instance group |
| Status | available. Ran with `g5` in the practice account | available. Not run on AWS, so not verified | experimental: set up to work with a custom AMI, not run on AWS (not verified). gVisor release-20261109.0 does not know the default AMI's driver 595.91.07 |

## What HyperPod gives the trainer

- **Node recovery:** the cluster is created with `NodeRecovery: Automatic` (`infra/hyperpod/cluster.json.tpl`). Node health shows up as the `sagemaker.amazonaws.com/node-health-status` label (`Schedulable`, `Unschedulable` and others), and the trainer job is placed only on `Schedulable` nodes.
- **Deep health checks:** an instance group's `OnStartDeepHealthChecks` can enable `InstanceStress` (GPU/NVLink count, DCGM diagnostics, EFA and others) and `InstanceConnectivity` (NCCL and others). This asset's template does not set this field; if you add it, see the taint constraint below.
- **Job restarts and hang detection:** the training operator add-on (`amazon-sagemaker-hyperpod-training-operator`) runs `HyperPodPyTorchJob`, with `jobMaxRetryCount: 3` and a `restartPolicy` (`numRestartBeforeFullJobRestart: 1`, `evalPeriodSeconds: 3600`, `maxFullJobRestarts: 2`). There are two log-pattern detections: `JobStart` expects a `"event": "routing"` line within 1200 seconds, and `RewardStalled` expects a `"event": "reward_batch"` line every 1800 seconds. The HyperPod trainer image installs `hyperpod-elastic-agent` without a pinned version, and the Job starts the trainer with `hyperpodrun`. The installed version can differ with the build date.
- **Checkpoint resume:** after a restart, `train_grpo.py` resumes from the latest checkpoint in its output directory. The hands-on keeps `/outputs` on an emptyDir (a scratch volume that disappears with the pod), so resuming after a node replacement needs shared storage (an FSx for Lustre PVC, for example).
- **Other features:** the `hyp` CLI (`pip install sagemaker-hyperpod`), the task governance and observability add-ons, and Karpenter-based autoscaling (`AutoScalerType: Karpenter`, `NodeProvisioningMode: Continuous`).

!!! warning "Training operator and Kubernetes versions"
    This asset uses Kubernetes 1.36. The HyperPod EKS AMI release notes list 1.36 AMIs, but the HyperPod prerequisites page still lists 1.30 to 1.35 and the training operator documentation lists 1.28 through 1.33 (the documentation may be out of date). Before creating the cluster, check add-on compatibility with the read-only command below.

    ```bash
    aws eks describe-addon-versions \
      --addon-name amazon-sagemaker-hyperpod-training-operator \
      --kubernetes-version 1.36
    ```

    **What to look for:** if the `addons[0].addonVersions` list in the JSON has at least one version, a 1.36-compatible add-on exists. If the list is empty, consider a lower `K8S_VERSION`.

??? info "HyperPod (EKS) prerequisites in short"
    You need EKS authentication mode `API` or `API_AND_CONFIG_MAP`, VPC CNI 1.18.3 or later, and private subnets. When creating through the API, first install the HyperPod dependency Helm chart (`helm_chart/HyperPodHelmChart` in `sagemaker-hyperpod-cli`), which installs the health monitoring agent, deep health check RBAC, job auto-restart, the MPI operator, nvidia-device-plugin, the Neuron and EFA plugins, and Kueue. HyperPod nodes and EKS nodes use different IAM roles, and the execution role gets `AmazonSageMakerClusterInstanceRolePolicy` plus an EC2 ENI and ECR inline policy.

## What HyperPod does not give the sandbox tier

| Item | Fact | This asset's answer |
|---|---|---|
| Sandbox runtime | The NVIDIA driver 595.91.07 in the HyperPod EKS AMI is unknown to gVisor release-20261109.0, so nvproxy does not work. Kata is impossible: there is no `ml.*.metal`, and CreateCluster has no nested-virtualization CPU option | sandboxes stay on EC2 nodes (B1). B2 builds a separate instance group from a custom AMI with a replaced driver |
| Dedicated node taints | "You cannot add custom taints to nodes in instance groups with DeepHealthChecks turned on." | sandbox nodes are separated by the `gpusandbox/role` taint on EC2 node groups |
| Isolation checks | deep health checks test hardware (GPU, NVLink, EFA, NCCL), not sandbox isolation (egress denial and so on) | Ready only after egress denial is verified, `scripts/ops/verify.sh` |
| Pod density | one ENI per instance, so `ml.g6.xlarge` and `ml.g6.2xlarge` allow at most 14 pods (the limit of the default `ml.g5` has not been checked) | B1 runs only the trainer on HyperPod nodes. The B2 `sandbox` group runs one sandbox pod per node |
| CPU node replacement | "Node auto-replacement is not supported for CPU instances." | the CPU tier is on EC2 (`c8i`) |
| Version pinning, parity, gateway | not HyperPod features | code in this repository |

On HyperPod nodes, by default only hostNetwork pods can reach IMDS. That default favors sandboxes, but it does not lift the constraints above.

## EC2 sandboxes in B1 and the custom AMI in B2

gVisor needs an exact driver version match, and an unknown version does not work even with the override flag, so B2 bakes its own custom AMI with the driver replaced by 580.178.04 ([B2 in 07 HyperPod scenario](../handson/07_hyperpod.md#b2)). The script below checks a node's driver (needs a HyperPod cluster). It runs a debug pod on each node and, when it ends, deletes every pod in the `default` namespace whose name starts with `node-debugger-`, which can include other people's debugging sessions.

```bash
scripts/hyperpod/check_gvisor.sh
```

**What to look for:** a default-AMI node (the trainer) prints the line below, and a B2 custom-AMI node (sandbox) prints `driver 580.178.04: SUPPORTED ...`.

```text
  driver 595.91.07: NOT supported by gVisor 20261109.0: keep sandboxes on EC2 (mode B1)
```

The pod limit above still applies to B2, and a taint can only be added to an instance group without deep health checks, so B2's sandbox group is created without them. B1 stays the default because it needs no custom AMI to maintain. B1 and B2 on `ml.g5` were not run on AWS and are not verified. In B2, `scripts/04_install_gpu_stack.sh` does not create a smoke pod. Check which module flavor loaded on the sandbox node (`/proc/driver/nvidia/version`) and confirm with `scripts/hyperpod/check_gvisor.sh` above that the driver is on the support list. Then deploy the pool with `scripts/06_deploy_sandboxes.sh gvisor-hyperpod v1` and verify it with `scripts/ops/verify.sh gvisor-hyperpod v1`.

**If it fails:** `no HyperPod nodes found` means no HyperPod node has joined the cluster yet; see [07 HyperPod scenario](../handson/07_hyperpod.md) and the "HyperPod" section of [Troubleshooting](../reference/troubleshooting.md).

## Instance choice

| Role | Choice | Reason | On-Demand (USD/hour) |
|---|---|---|---|
| Trainer (A) | `g5.2xlarge` (1 x A10G 24 GB, 8 vCPU, 32 GiB) | configured to fit a 1.5B model + LoRA + vLLM colocate on one A10G (`vllm_gpu_memory_utilization` 0.35). A 5-step GRPO run finished in the practice account | 1.212 |
| Trainer (B) | `ml.g5.2xlarge` | the same hardware through HyperPod. About 25% higher at list prices (1.515 / 1.212 = 1.25) | 1.515 |
| gVisor sandbox | `g5.xlarge` (1 x A10G), one sandbox per node | the driver the AMI loads, 580.178.04, is on the nvproxy support list. Verification scope is in "Driver and verification scope of `g5`" below | 1.006 |
| Kata GPU sandbox | `g4dn.metal` (8 x T4, 96 vCPU, 384 GiB), one T4 per VM | the only `.metal` type with an x86 NVIDIA GPU | 7.824 (Seoul 9.624) |
| Kata CPU sandbox | `c8i.2xlarge` (nested virtualization) | `/dev/kvm` without `.metal`. Kata rehearsal and the CPU tier | 0.37484 |
| System | `m6i.large` x 2 | CoreDNS and controllers | 0.096 (each) |

Prices are On-Demand list prices in us-east-1 and us-west-2.

!!! note "Driver and verification scope of `g5`"
    On a `g5.xlarge` node deployed on 2026-11-18, the EKS AL2023 NVIDIA AMI loaded the proprietary kernel module 580.178.04 with GSP off (`/proc/driver/nvidia/version`, and `EnableGpuFirmware: 0` in `/proc/driver/nvidia/params`). gVisor documents nvproxy against NVIDIA's open driver and does not mention the proprietary driver. Still, 580.178.04 is on the support list of runsc `release-20261109.0` (`runsc nvproxy list-supported-drivers`). In the practice account, the gVisor smoke test (`cuda ok: NVIDIA A10G 2048.0`) and `scripts/ops/verify.sh gvisor v1` passed on `g5.xlarge`, and a 5-step GRPO run finished with the trainer on `g5.2xlarge`. So this combination is verified by this repository, not documented by gVisor. Check again after changing the driver, AMI or gVisor version. The `04_install_gpu_stack.sh` smoke test creates its own pod that uses one GPU, so run it while a gVisor node has a free GPU; check a pool that is already deployed with `scripts/ops/verify.sh gvisor v1`.

    `g6` (L4) is a supported alternative. The AMI loads the open module 580.178.04 there, which matches the gVisor documentation, and it is cheaper (`g6.xlarge` 0.8048, `g6.2xlarge` 0.9776). To use it, set `GVISOR_INSTANCE_TYPE` and `TRAINER_INSTANCE_TYPE` (`HYPERPOD_*` for HyperPod) in `scripts/config.env`.

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
| Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances | 6 (`m6i.large` 2 x 2 + the SSM access `t4g.nano` 2). Kata CPU adds `c8i.2xlarge` 8 (14 in total). While the B2 or Kata GPU AMI is being built, the builder `m6i.large` needs 2 more (8, or 16 with the Kata CPU node) | documented default is 5 |
| `ml.g5.2xlarge for cluster usage` | 1 (B) | HyperPod uses `ml.<type> for cluster usage` quotas |
| `ml.g5.xlarge for cluster usage` | 2 (B2) | the B2 `sandbox` instance group (`HYPERPOD_SANDBOX_COUNT`) |

`scripts/01_check_prereqs.sh` prints, read-only, the G and VT quota, nested virtualization support for `c8i.2xlarge` and which AZs offer each GPU type. How to run it and what to check are in section 5 of [Getting started](../getting_started.md).

## Hourly cost of the hands-on setups (estimate)

| Setup | Nodes | Node subtotal (USD/hour) |
|---|---|---|
| A base (gVisor + trainer) | `m6i.large` x 2 + `g5.xlarge` x 2 + `g5.2xlarge` | 0.192 + 2.012 + 1.212 = about 3.42 |
| A + Kata CPU | A base + `c8i.2xlarge` x 1 | about 3.79 |
| A + Kata GPU | A base + `g4dn.metal` x 1 | 3.416 + 7.824 = about 11.24 |
| B1 (HyperPod trainer) | `m6i.large` x 2 + `g5.xlarge` x 2 + `ml.g5.2xlarge` | 0.192 + 2.012 + 1.515 = about 3.72 |

The table is an estimate from list prices and leaves out the EKS control plane, NAT gateway, the SSM access `t4g.nano`, EBS, data transfer, ECR and CloudWatch.

!!! warning "Scale `g4dn.metal` to zero when you are not using it"
    In the A + Kata GPU setup a single `g4dn.metal` is about 70% of the node cost (7.824 / 11.24). When you are not using it, scale the node group to zero with the command below, and run [99 Cleanup](../handson/99_cleanup.md) when you finish.

    ```bash
    aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu \
      --scaling-config minSize=0,maxSize=1,desiredSize=0
    ```

    **What to look for:** after a few minutes, `kubectl get nodes -l gpusandbox/kata-gpu=true` (with `cdk/tunnel.sh` running) lists no nodes. If `CLUSTER_NAME` is not set in your shell, run `source scripts/config.env` first.

!!! question "❓ Misconception: with HyperPod, HyperPod manages the sandboxes too"
    HyperPod's node recovery, deep health checks and job restarts are resiliency features for nodes and jobs. Node recovery is a cluster setting, so it also covers B2's `sandbox` group, but HyperPod does not install sandbox runtimes, verify isolation or pin versions.

!!! question "❓ Misconception: T4 is cheaper, so make the gVisor nodes `g4dn`"
    `g4dn.xlarge` (0.526) is cheaper than `g5.xlarge` (1.006). `g4dn` has the same driver condition as `g5` (the AMI loads the proprietary kernel module with GSP off), so the driver flavor is not a reason to exclude it, but this asset has not tested gVisor on T4, so it stays unverified. T4 serves as the Kata + QEMU GPU (`g4dn.metal`); to use it with gVisor, verify it yourself.

## Scope and limits

- Scenario A's `g5` setup ran in the practice account ([run record](../reference/sources.md#aws-run-record)). The gVisor sandbox (1 replica) and `scripts/ops/verify.sh gvisor v1` passed, and a 5-step GRPO run finished with the trainer configuration (1.5B + LoRA + vLLM colocate on one A10G).
- On a different cluster setup, Kata + QEMU ran on `g4dn.metal` (`kata-qemu` replica 4, `scripts/ops/verify.sh kata-qemu v1`), and `scripts/ops/bench.sh 32` measured two GPU pools and three CPU pools.
- HyperPod B1 and B2 (`ml.g5`) and a `scripts/ops/rollout.sh` version switch during scenario A training were not run on AWS. Verify them with the checks on each hands-on page.
- `c8i.2xlarge` is 0.37484 USD per hour in us-east-1 and us-west-2 and 0.42336 USD in the Seoul Region. Scenario C, which uses only this node and no GPU, is in [10 CPU-only path on c8i](../handson/10_cpu_only.md).

??? note "References"
    | Topic | Link |
    |---|---|
    | HyperPod resiliency, deep health checks | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html |
    | HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
    | EC2 accelerated computing instance specifications, quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html , https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
    | Pricing (EC2, SageMaker AI) | https://aws.amazon.com/ec2/pricing/on-demand/ , https://aws.amazon.com/sagemaker/ai/pricing/ |
    | This asset's HyperPod template and check script | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/cluster.json.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh |

    All sources: [this page in All references](../reference/references.md#ref-concepts-04-platforms-and-instances)
