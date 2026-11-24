---
hide:
  - footer
---

# Attach the HyperPod trainer in B1

After the CUDA check on the EC2 graders, keep the EKS tunnel open and attach the trainer.


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

**If it fails:** if the status is `Failed` or the node never becomes `Schedulable`, see the "HyperPod" section of [Troubleshooting](../../../reference/troubleshooting.md).


When the trainer is `Schedulable` and the operator is `ACTIVE`, deploy the EC2 pool in [step 03 for B1](../03_pools/index.md#__tabbed_1_2).
