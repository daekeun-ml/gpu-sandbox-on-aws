# B1 · Train on HyperPod and grade on EC2

[Choose another scenario](00_overview.md#step-order)


In B1 the model trains on a SageMaker HyperPod node and its generated code is graded by a gVisor pool on EC2. Check **both the training node's identity and the grading results** to trace work across the two.

1. [Check the Region and quotas](#before-you-begin), then follow the [B1 steps](#b1-steps). This path provisions its own EKS cluster and EC2 grading nodes.
2. Once the HyperPod trainer is `Schedulable` and the EC2 pool passes verification, [submit one step](#6-training).
3. In the [run and its logs](#how-to-verify), find the trainer pod's node, the verdicts in `reward_batch`, and the job's `Completed` status. [Delete HyperPod first](#cleanup) during cleanup.

The [B2 lab](07_hyperpod_b2.md) puts the CPU system worker, GPU trainer and GPU graders in HyperPod instance groups.

??? note "Terms (expand if a word is new to you)"
    - **SageMaker HyperPod**: an AWS managed cluster for long-running training. With EKS as the orchestrator, it attaches groups of nodes to an existing EKS cluster.
    - **Instance group**: a set of HyperPod nodes that share an instance type and settings. It is similar to an EKS node group.
    - **HyperPodPyTorchJob, training operator**: the Kubernetes custom resource that describes a training job for HyperPod, and the controller (an EKS add-on) that runs and restarts that job.
    - **Elastic agent (`hyperpodrun`)**: the launcher that starts the training processes inside the container and reports their state to the operator. It extends the PyTorch ElasticAgent.
    - **Lifecycle script**: a shell script that runs when a HyperPod node is created. It is read from an S3 bucket.
    - **Dependency Helm chart**: the Helm chart that installs the components HyperPod needs, such as the health monitoring agent and device plugins, into the cluster.
    - **Execution role**: the IAM role HyperPod nodes use to call AWS APIs.
    - **NodeRecovery, deep health check**: the setting that automatically reboots or replaces a faulty node, and a long check that puts load on the GPUs and the network.
    - **nvproxy**: the gVisor feature that filters GPU driver calls (ioctl) and passes them on. Each driver version has its own allowlist.
    - **Device plugin**: a DaemonSet that advertises a node's GPUs to Kubernetes as a resource such as `nvidia.com/gpu`.
    - **emptyDir**: a temporary volume that exists only while its pod lives. Its content disappears when the pod is deleted.
    - **Taint**: a mark on a node. Pods without a matching toleration are not scheduled onto that node.
    - **IMDS**: the address (169.254.169.254) where an EC2 instance reads its own metadata and temporary credentials.
    - **ENI**: a virtual network interface attached to an instance. The VPC CNI hands out the ENI's IP addresses to pods, so the number of ENIs sets the per-node pod limit.

## Layout

[![Scenario B1: the trainer on a HyperPod instance group and the gVisor pools on EC2 nodes](../images/architecture/scenario-b1.drawio.png)](../images/architecture/scenario-b1.drawio.png)

*Takeaway: In AWS resources, only the trainer sits on a HyperPod instance group and the rest is the same as scenario A.*

<details class="note" markdown="1">
<summary>B1 network path and authentication</summary>

```mermaid
flowchart LR
    subgraph EKS["Same EKS cluster"]
        subgraph HP["HyperPod instance group trainer"]
            T["HyperPodPyTorchJob<br/>hyperpodrun + train_grpo.py<br/>ml.g5.2xlarge (A10G)"]
        end
        subgraph EC2["EC2 node groups"]
            G["sandbox-gvisor<br/>g5.xlarge x 2"]
            K["(optional) sandbox-kata-gpu<br/>g4dn.metal"]
            S["system<br/>m6i.large x 2"]
        end
    end
    T -->|"label gpusandbox/client, audience token"| G
    T -.->|optional| K
```

*Takeaway: the sandboxes stay on EC2 nodes in the same cluster, so the NetworkPolicy and token authentication of scenario A apply unchanged.*

</details>

## Before you begin

For a first deployment, follow [preparation 1 in chapter 01](01_cluster_and_images.md#preparation-1-scriptsconfigenv) to create `scripts/config.env`. Set `AWS_REGION` (`us-west-2` for the recorded run), `CLUSTER_NAME` and `SCENARIO="B1"`. The base lab uses `GVISOR_NODES="2"`, `WITH_KATA_CPU="0"` and `WITH_KATA_GPU="0"`. Choose a separate B1 cluster name if you are keeping an existing cluster.

Follow [preparation 2](01_cluster_and_images.md#preparation-2-once-cdk-and-the-session-manager-plugin) to set up CDK and the Session Manager plugin, install the CDK dependencies in your Python virtual environment and run `cdk bootstrap` for this account and region. Return here with the virtual environment active and check the following three values in `scripts/config.env`.

| Variable | Value in the example file | What to do |
|---|---|---|
| `HYPERPOD_CLUSTER_NAME` | `gpu-sandbox-hp` | Can stay as is. It is also used in the execution role name (`<this value>-execution`) |
| `HYPERPOD_TRAINER_INSTANCE_TYPE` | `ml.g5.2xlarge` | Leave it. The job template's nodeAffinity uses this value too |
| `HYPERPOD_LCS_BUCKET` | `sagemaker-gpu-sandbox-lcs-__SET_ME__` | Replace `__SET_ME__` with a unique value. S3 bucket names must be unique worldwide. Keep the `sagemaker-` prefix |

Check the required CLIs, your AWS identity and the G/VT vCPU quota in one pass (the HyperPod scripts also use `git`).

```bash
scripts/01_check_prereqs.sh
```

Allow 6 free EC2 Standard vCPUs for the two system nodes and the access instance, 8 EC2 G/VT vCPUs for two `g5.xlarge` graders and one HyperPod `ml.g5.2xlarge` for training. Under Amazon SageMaker in Service Quotas, check `ml.g5.2xlarge for cluster usage` in the lab region.

**If it fails:** see the "Configuration and scripts" section of [Troubleshooting](../reference/troubleshooting.md).

![Applied HyperPod quota and EKS 1.36 training operator versions in us-west-2](../images/terminal/hyperpod-prereqs.png)

## Time and cost

Allow 20–30 minutes for EKS deployment. In the B1 run, the HyperPod cluster reached `InService` about 2½ minutes after `CreateCluster` returned. The trainer instance finished provisioning about 8 minutes after the request.

| Item | Count | USD/hour |
|---|---|---|
| HyperPod `ml.g5.2xlarge` (trainer) | 1 | 1.515 |
| EC2 `g5.xlarge` (gVisor sandboxes) | 2 | 2.012 |
| EC2 `m6i.large` (system) | 2 | 0.192 |
| Total | | 3.719 |

Prices are us-east-1 and us-west-2 On-Demand list prices. EKS control plane, NAT gateway and EBS are extra, and `g4dn.metal` adds 7.824 USD per hour. When you are done, follow "Cleanup" at the end.

## B1 steps

### 1. Cluster

One CDK stack creates the VPC, the EKS control plane (private API endpoint only), two system nodes, two gVisor sandbox nodes and an access instance. `--hyperpod` leaves out only the EC2 trainer node group. The deploy flow and the review of IAM changes (y/n) are the same as cluster creation (`02_create_cluster.sh`) in [01 Cluster and images](01_cluster_and_images.md).

```bash
scripts/02_create_cluster.sh --hyperpod
```

When deployment finishes, open a separate terminal in the project’s top-level directory and leave this command running. Continue in the original work terminal.

```bash
cdk/tunnel.sh
```

**What to look for:**

- When the deploy finishes, `Outputs` shows `EndpointPublicAccess = false`.
- With the tunnel open, the `ROLE` column of `kubectl get nodes -L gpusandbox/role` shows two `system` nodes and two `sandbox-gvisor` nodes, and no `trainer` node.

HyperPod supports EKS 1.36 and publishes a matching x86_64 AMI. [HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)

??? note "What the CDK stack sets up for HyperPod"
    The CDK stack sets the authentication mode `API_AND_CONFIG_MAP` that HyperPod requires and the VPC CNI with NetworkPolicy enabled. It also tags the private subnets with `kubernetes.io/role/internal-elb=1`, which step 4 uses to find a subnet.

**If it fails:** see the "Cluster and nodes" section of [Troubleshooting](../reference/troubleshooting.md) (vCPU limits, AZs, insufficient capacity).

### 2. Images

Build the sandbox, trainer and control images and push them to ECR. With `HYPERPOD=1`, the trainer image gets `hyperpod-elastic-agent` 1.1.3 on vLLM 0.26.0 and PyTorch 2.11.0. The build runs `hyperpodrun --help` to check that the launcher starts.

```bash
HYPERPOD=1 scripts/03_build_push_images.sh
```

**What to look for:** at the end, `Add to scripts/config.env:` is followed by three lines, `export SANDBOX_IMAGE_URI=...`, `export TRAINER_IMAGE_URI=...` and `export CONTROL_IMAGE_URI=...`. Put these three lines into `scripts/config.env`.

!!! warning "Rebuild with a new IMAGE_TAG"
    ECR tags are IMMUTABLE, so if scenario A already pushed the same `IMAGE_TAG` (default `v1`), the push is rejected. Change `IMAGE_TAG` in `scripts/config.env` (for example to `v1-hp`) and rebuild. The script reads `config.env`, so a command-line environment variable cannot override it.

**If it fails:** see the "Configuration and scripts" section of [Troubleshooting](../reference/troubleshooting.md) (duplicate tags, slow builds).

### 3. GPU stack and runtimes

The command below installs the NVIDIA device plugin (CDI mode) for the EC2 GPU nodes, then registers the gVisor RuntimeClass and runs a GPU smoke test pod on one gVisor node. The smoke pod uses the `SANDBOX_IMAGE_URI` image you added in step 2, so without that value the script stops right at the start.

```bash
scripts/04_install_gpu_stack.sh
```

**What to look for:**

- The `allocatable GPUs per node` table in the output shows the `sandbox-gvisor` nodes with one GPU each (right after the device plugin restarts it can briefly show `0`).
- In the smoke pod log, `Starting gVisor...` identifies the runtime and `cuda ok: NVIDIA A10G 2048.0` confirms the calculation on the A10G.
- HyperPod nodes appear only in step 4, so they are not in the table yet.

This device plugin runs on EC2 sandbox nodes with the `gpusandbox/device-plugin=cdi` label. The dependency chart in step 4 installs a separate plugin on the HyperPod trainer node.

To use Kata sandboxes as well (optional, full procedure in [03 Kata sandboxes](03_kata.md)), run the commands below in this order.

- **Bake the IOMMU AMI first**: with `WITH_KATA_GPU=1` and an empty `KATA_IOMMU_AMI_ID`, cluster creation stops in the CDK step.
- **When you run `scripts/kata/gpu_nodes.sh` with `KATA_IOMMU_AMI_ID` empty**: it bakes the AMI and stops, which is normal. The script bakes the AMI and stops only while this value is empty.
- **Running this again after a cleanup**: `08_cleanup.sh` deletes the AMI but leaves the `KATA_IOMMU_AMI_ID` line in `config.env`, so remove that line first.

```bash
# optional Kata pools: see 03_kata.md
scripts/kata/gpu_nodes.sh              # KATA_IOMMU_AMI_ID empty: bakes the IOMMU AMI, then stops
# in scripts/config.env: set WITH_KATA_CPU="1" and WITH_KATA_GPU="1", and paste the printed line  export KATA_IOMMU_AMI_ID="ami-..."
scripts/02_create_cluster.sh --hyperpod  # adds the Kata node groups; type 'metal' for g4dn.metal
scripts/kata/cpu_nodes.sh
scripts/kata/gpu_nodes.sh              # second run: GPU Operator, kata-deploy, pgpu check
```

For the Kata CPU pool alone, set only `WITH_KATA_CPU="1"`, then run cluster creation and `scripts/kata/cpu_nodes.sh`.

**If it fails:** if the gVisor smoke test fails, see [02 gVisor GPU sandboxes](02_gvisor.md) and the "gVisor" section of [Troubleshooting](../reference/troubleshooting.md).

### 4. HyperPod cluster

Create the HyperPod cluster and attach it to the EKS cluster. HyperPod instance charges start here.

```bash
scripts/hyperpod/create.sh
```

The script's five steps:

| Step | What it does | Why |
|---|---|---|
| 1 dependency chart | Clones `aws/sagemaker-hyperpod-cli` and installs `helm_chart/HyperPodHelmChart` into `kube-system` as `hyperpod-dependencies` | Required when HyperPod is created through the API |
| 2 lifecycle bucket | Creates `HYPERPOD_LCS_BUCKET` if missing, turns on all four Block Public Access settings (`BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets`) and uploads `infra/hyperpod/lifecycle/` | Lifecycle scripts run when a node is created and can change the node's configuration, so they must not be public |
| 3 execution role | `${HYPERPOD_CLUSTER_NAME}-execution`: trusts `sagemaker.amazonaws.com`, with `AmazonSageMakerClusterInstanceRolePolicy` + inline `hyperpod-eks` (EC2 ENI, ECR pull) + inline `lifecycle-bucket-read` | The role for HyperPod nodes is separate from the EKS node role |
| 4 CreateCluster | Creates the cluster with `Orchestrator.Eks.ClusterArn`, instance group `trainer`, the EKS cluster security group and a private subnet, `NodeRecovery: Automatic`. Polls every 30 seconds while creating and stops on failure | With the same security group, HyperPod nodes, EC2 nodes and the control plane can talk to each other |
| 5 training operator | Waits for a schedulable, Ready trainer node, runs `aws eks create-addon --addon-name amazon-sagemaker-hyperpod-training-operator`, then waits for `addon-active` | Installs the HyperPodPyTorchJob CRD and controller |

- **Defaults of the step 1 dependency chart**: with the main-branch values, the health monitoring agent, deep health check, job auto-restart, MPI operator and the NVIDIA, EFA and Neuron device plugins are on by default.
- **Instance group `trainer` in step 4**: one `ml.g5.2xlarge`, `ThreadsPerCore` 2 (8 vCPUs), `OnCreate` `on_create.sh`. The worker requests 5 vCPUs, 24 GiB and one GPU. The operator, its per-job pod manager and the other system pods together requested 2.75 vCPUs on this node.
- **Private subnet in step 4**: found by the tag `kubernetes.io/role/internal-elb=1`, set by the CDK stack.

**What to look for:**

- In step 4, the cluster status is printed after `waiting for InService (15-30 min)`. `status` must be `InService` and `failure` must be empty.
- In the final `kubectl get nodes` table, the node with instance type `ml.g5.2xlarge` has `node-health-status` `Schedulable`. The output looks roughly like this (example):

```text
NAME              STATUS   ROLES    AGE   VERSION   NODE-HEALTH-STATUS   INSTANCE-TYPE
<ec2-node>        Ready    <none>   40m   v1.36.x                        g5.xlarge
<hyperpod-node>   Ready    <none>   5m    v1.36.x   Schedulable          ml.g5.2xlarge
```

??? note "The `sagemaker-` prefix of the bucket name"
    The `sagemaker-` prefix of the bucket name follows the comment in `config.env.example` that the HyperPod managed policy expects this prefix. Read access comes from the separate inline policy.

`cluster.json.tpl` does not configure deep health checks (`OnStartDeepHealthChecks`: `InstanceStress`, `InstanceConnectivity` and others); add them to the instance group yourself if you need them.

??? note "Training operator permissions"
    The B1 CDK stack installs the `cert-manager` and `eks-pod-identity-agent` add-ons and associates the `aws-hyperpod/hp-training-operator-controller-manager` service account with an IAM role. `create.sh` tags the HyperPod cluster `SageMaker=true`, which the role’s `AmazonSageMakerHyperPodTrainingOperatorAccess` policy requires for `DescribeClusterNode`.

On a rerun, the script behaves differently per step.

- **Applied again**: the step 1 Helm chart, the step 2 Block Public Access settings and the lifecycle file upload.
- **Run only when missing**: it creates the bucket only when it is missing, and creates the step 3 role and attaches its policies only when the role is missing.
- **Step 4's `create-cluster`**: expected to fail if a cluster with the same name exists (inference).

So if only step 5 failed, do not rerun the script: put the prerequisites in place and run just these commands.

```bash
source scripts/config.env
aws eks create-addon --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
  --addon-name amazon-sagemaker-hyperpod-training-operator
aws eks wait addon-active --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
  --addon-name amazon-sagemaker-hyperpod-training-operator
```

**What to look for:** the second command finishes without an error. If the first command says the add-on already exists, skip it and run only the second.

**If it fails:** if the status is `Failed` or the node never becomes `Schedulable`, see the "HyperPod" section of [Troubleshooting](../reference/troubleshooting.md).

### 5. Namespaces and sandbox pools

Same as scenario A: create the namespaces, authentication, NetworkPolicies and routing table, deploy the gVisor sandbox pool, then verify isolation and verdicts.

```bash
scripts/05_setup_namespaces_auth.sh
scripts/06_deploy_sandboxes.sh gvisor
scripts/ops/verify.sh gvisor
```

**What to look for:** compare the sandbox kernel in the first check with the host kernel yourself. They should differ. The third command should finish with `pool sandbox-gvisor-v1 verified`. The output of each step is the same as "What to look for" in [04 Deploy and verify sandbox pools](04_sandbox_pools.md).

![Two ready gVisor replicas and six checks from the authenticated probe in the B1 cluster](../images/terminal/hyperpod-sandboxes.png)

**If it fails:** see the "If it fails" table in [04 Deploy and verify sandbox pools](04_sandbox_pools.md) and the "Sandbox pools and readiness" section of [Troubleshooting](../reference/troubleshooting.md).

### 6. Training

Set a run ID, submit a one-step job and save its output locally. The operator removes the worker pod on completion.

```bash
export RUN_ID="b1-$(date +%Y%m%d-%H%M%S)"
scripts/hyperpod/run_grpo.sh 1      # smoke test; omit 1 for 60 steps
kubectl -n rl-trainer wait --for=create pods -l "HPJob=grpo-${RUN_ID}" --timeout=5m
kubectl -n rl-trainer wait --for=condition=Ready pods -l "HPJob=grpo-${RUN_ID}" --timeout=20m
kubectl -n rl-trainer get pods -l "HPJob=grpo-${RUN_ID}" -o wide | tee "placement-${RUN_ID}.txt"
kubectl -n rl-trainer logs -f -l "HPJob=grpo-${RUN_ID}" --tail=-1 | tee trainer.log | grep --line-buffered '"event"'
```

**What to look for:**

- `run_grpo.sh` prints `HyperPodPyTorchJob grpo-<RUN_ID> submitted` and one line for the job.
- In the trainer log, `{"event": "routing", ...}` appears within 20 minutes, followed by a `{"event": "reward_batch", ...}` line for every step that sent completions to the sandboxes. The first step includes the model download and vLLM initialization, so it takes a while.

See the [HyperPod training script](../reference/scripts.md#scriptshyperpodrun_grposh) for configuration and what happens after submission. Rewards and log formats match the [GRPO exercise](05_grpo_training.md).

**If it fails:**

- **If the pod is Pending or cannot find `hyperpodrun`**: see the "HyperPod" section of [Troubleshooting](../reference/troubleshooting.md).
- **If no events appear**: see the "Training" section of the same page.

<details class="note" markdown="1">
<summary>Training job template and node placement</summary>

## The HyperPodPyTorchJob template

The template sets placement, the trainer command, and log patterns used to detect a stalled job.

The HyperPod-specific settings in `k8s/trainer/hyperpod-job-grpo.yaml.tpl`:

| Field | Value | Meaning (per the AWS documentation) |
|---|---|---|
| command | `hyperpodrun --nproc_per_node=1 --nnodes=1 /opt/gpusandbox/rl/trl/train_grpo.py ...` | Launcher of the HyperPod elastic agent, an extension of the PyTorch ElasticAgent |
| `runPolicy.jobMaxRetryCount` | 3 | Maximum number of restarts at the process level |
| `restartPolicy.numRestartBeforeFullJobRestart` | 1 | Process-level restarts allowed before the operator restarts at the job level |
| `restartPolicy.evalPeriodSeconds` | 3600 | Period, in seconds, over which the restart limit is evaluated |
| `restartPolicy.maxFullJobRestarts` | 2 | Maximum full job restarts before the job fails |
| `cleanPodPolicy` | All | Which pods the operator cleans up |
| log rule `JobStart` | `.*"event": "routing".*`, `expectedStartCutOffInSeconds: 1200` | HANGING if no routing event appears within 20 minutes of the start |
| log rule `RewardStalled` | `.*"event": "reward_batch".*`, `expectedRecurringFrequencyInSeconds: 1800` | HANGING if more than 30 minutes pass between reward_batch lines |
| nodeAffinity | `node.kubernetes.io/instance-type In [ml.g5.2xlarge]`, `sagemaker.amazonaws.com/node-health-status In [Schedulable]` | Only healthy HyperPod nodes |
| pod labels | `app: grpo-trainer`, `gpusandbox/client: "true"` | Admitted by the same NetworkPolicy as in scenario A |
| `/outputs` | emptyDir | Pod Security `baseline` in the `rl-trainer` namespace forbids hostPath |

Per the AWS documentation, when a rule evaluates to HANGING, the HyperPod elastic agent treats the container as stuck and restarts the job with the training operator. Log monitoring reads stdout, where this repository prints its events with a flush.

A step that sends no answer to a sandbox leaves no `reward_batch` line, so if every answer has no code or fails the trainer-side policy for more than 30 minutes, `RewardStalled` can classify the job as hanging.

!!! note "Checkpoints after a restart"
    On start, `train_grpo.py` resumes from the latest checkpoint in `/outputs/grpo` (saved every 20 steps). An emptyDir lives as long as its pod, though.

    - **After a full job restart that recreates the pod, or a node replacement**: the directory is empty and training starts over.
    - **A process-level restart**: the result depends on whether the pod is reused.

    To resume after a node replacement, mount a shared storage PVC such as FSx for Lustre at `/outputs` ([06 Scaling with veRL](../production/06_scaling_with_verl.md)).

HyperPod nodes have two limits.

- **Pods per node**. Kubernetes reported a limit of 14 pods on the `ml.g5.2xlarge` trainer in this run. Check `.status.allocatable.pods` on your node. The limit depends on the AMI and VPC CNI version.
- **IMDS access**: only hostNetwork pods reach IMDS by default, so the trainer pod cannot read node credentials.

</details>

## How to verify

`InService` describes the HyperPod cluster. To check the path in the [B1 diagram](#layout), use steps 4–5 below to match the trainer pod to its node and find verdicts from the EC2 gVisor pool.

The AWS console showed `InService` while the trainer instance was still `Pending`. Check its status with `list-cluster-nodes`, then check node placement and trainer logs in Kubernetes.

![The EKS-orchestrated lab cluster marked InService in the AWS HyperPod console](../images/console/hyperpod-b1.png)

```bash
source scripts/config.env
aws sagemaker list-cluster-nodes --region "$AWS_REGION" --cluster-name "$HYPERPOD_CLUSTER_NAME" \
  --query 'ClusterNodeSummaries[].[InstanceGroupName,InstanceStatus.Status]' --output table
```

1. In the last table of `hyperpod/create.sh`, the HyperPod node has `node-health-status` `Schedulable` and instance type `ml.g5.2xlarge`.
2. The HyperPod cluster status and failure message:

    ```bash
    aws sagemaker describe-cluster --region "$AWS_REGION" --cluster-name "$HYPERPOD_CLUSTER_NAME" \
      --query '{status: ClusterStatus, failure: FailureMessage}'
    ```

    **What to look for:** `status` is `InService` and `failure` is empty (`null`).

3. The training operator add-on status:

    ```bash
    aws eks describe-addon --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
      --addon-name amazon-sagemaker-hyperpod-training-operator --query addon.status
    ```

    **What to look for:** it prints `"ACTIVE"`.

4. Inspect the job and the pod placement saved in step 6. The file retains the node name after the operator removes the worker pod.

    ```bash
    kubectl -n rl-trainer get hyperpodpytorchjob "grpo-${RUN_ID}"
    cat "placement-${RUN_ID}.txt"
    ```

    **What to look for:** the job shows one line, and the pod's NODE is the HyperPod node from item 1.

    ![The running trainer on a schedulable HyperPod node with an NVIDIA A10G](../images/terminal/hyperpod-trainer-node.png)

5. `{"event": "routing", ...}` appears in the trainer log within 20 minutes, followed by a `reward_batch` line for every step that sent completions to the sandboxes.

    ```bash
    kubectl -n rl-trainer wait --for=condition=Completed "hyperpodpytorchjob/grpo-${RUN_ID}" --timeout=30m
    jq -Rrc 'fromjson? | select(.event=="reward_batch" or .event=="done")' trainer.log
    ```

    The one-step job `grpo-b1-grpo` ran from 13:11:57 to 13:17:35 UTC, including image pull and model initialization. TRL reported 49.2 s of training. Of the 12 submissions sent to gVisor v1, one passed, two gave wrong answers, eight raised runtime errors and one failed to compile.

    ![Completed job condition, routing, reward counts and done event from the saved trainer log](../images/terminal/hyperpod-grpo-result.png)

Load `$AWS_REGION`, `$CLUSTER_NAME` and `$HYPERPOD_CLUSTER_NAME` with `source scripts/config.env` first. If a check fails, see the "HyperPod" section of [Troubleshooting](../reference/troubleshooting.md).

A separate fixed-kernel benchmark sent 32 requests from the HyperPod trainer node to the two EC2 sandboxes. All 32 passed. Server-side p50 was 9.937 s and pool throughput was 0.199 eval/s. [Benchmark, screenshot and run data](08_benchmark.md#hyperpod-b1)

<details class="note" markdown="1">
<summary>Node requirements for Kata VMs</summary>

## Why Kata cannot run on HyperPod nodes

Kata starts a small VM per pod, so the node needs `/dev/kvm` (the KVM virtualization device). HyperPod nodes do not meet this condition.

| Condition | What Kata needs | HyperPod nodes |
|---|---|---|
| `/dev/kvm` | QEMU and Cloud Hypervisor use KVM. On AWS that means bare metal or an instance with nested virtualization | There is no `ml.*.metal` instance type (`CreateCluster` instance type list) |
| Nested virtualization | On EC2 it is turned on with a CPU option on C8i, M8i, R8i and others | The instance group settings have no such CPU option, and the G and P families are not nested-virtualization capable anyway |
| GPU passthrough | An IOMMU, and the host must own the GPU through `vfio-pci` | The HyperPod AMI loads the NVIDIA driver on the host |

A custom AMI does not change this: an AMI only changes software, while `/dev/kvm` depends on the instance type (bare metal or nested virtualization).

If you need Kata sandboxes, keep them on EC2 node groups in the same cluster (`g4dn.metal`, `c8i`), as in B1.

!!! question "❓ Misconception: with HyperPod, the GPU sandboxes have to run on HyperPod nodes too"
    HyperPod on EKS attaches instance groups to an existing EKS cluster, so the sandboxes can stay on EC2 node groups in the same cluster with the same NetworkPolicy and token authentication. Here HyperPod handles node recovery and job restarts for the long-running trainer. In [managed B2](07_hyperpod_b2.md), the system pods and the GPU grading pool also run on HyperPod workers.

</details>

<span id="scope-and-limits"></span>

B1 verified one training step and a benchmark. Testing recovery after node replacement requires a persistent checkpoint.

## Cleanup

Use both commands below for B1. Managed B2 has its own [stack cleanup procedure](07_hyperpod_b2.md#cleanup).

Delete HyperPod first, then the EKS cluster. Both scripts ask you to type a confirmation word at each step.

```bash
scripts/hyperpod/delete.sh   # HyperPodPyTorchJobs, HyperPod cluster, execution role, lifecycle bucket
scripts/08_cleanup.sh        # EKS cluster and the rest
```

In the B1 test, CloudWatch retained the log group `/aws/sagemaker/Clusters/<cluster-name>/<cluster-id>` after `hyperpod/delete.sh` finished. To clean up a test account, check the exact name under CloudWatch Logs and delete that group when you have saved the logs you need.

**What to look for:** the first command ends with `HyperPod resources deleted`. The words to type at each prompt, the resources that can remain and the check commands are in [99 Cleanup](99_cleanup.md).

??? note "References"
    | Topic | Link |
    |---|---|
    | HyperPod EKS prerequisites | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
    | Installing the training operator (cert-manager, Pod Identity) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html |
    | HyperPod EKS AMI releases (driver versions) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-release-ami-eks.html |
    | CreateCluster API (NodeRecovery, Orchestrator) | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateCluster.html |
    | HyperPod CLI and dependency Helm chart | https://github.com/aws/sagemaker-hyperpod-cli |

    [Selected references on this topic](../reference/references.md#ref-handson-07-hyperpod)
