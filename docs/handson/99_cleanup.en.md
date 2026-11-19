# 99 Cleanup

**TL;DR** GPU nodes are billed until you delete them, so delete what you used in this order: the Agent Sandbox extension and the demo site, HyperPod, then the EKS cluster (CDK stack), and query what is left (for a short break, scale the node groups to zero).

## Pain point

`g4dn.metal` costs 7.824 USD per hour, so a single forgotten node group costs about 188 USD per day (us-east-1 and us-west-2 On-Demand). HyperPod uses the EKS cluster as its orchestrator, so the cleanup script assumes HyperPod is deleted first, and GPU sandboxes in an Agent Sandbox warm pool hold their GPU even while idle. The demo site is a separate CloudFormation stack that `08_cleanup.sh` does not delete, and AMIs and snapshots, ECR images, HyperPod's S3 bucket and IAM role, and the CDK bootstrap stack also remain after the CDK stack is gone.

![Two panels. a: deleting the CDK stack (cdk destroy) removes only the cluster, node groups, VPC and NAT gateway, while AMIs and snapshots, ECR images, the HyperPod S3 bucket and IAM role, the demo site stack and the CDK bootstrap stack (CDKToolkit) remain. b: 08_cleanup.sh deletes the CDK stack after you type the cluster name and the AMIs, snapshots and, with --images, ECR images after you type ami and images; hyperpod/delete.sh deletes the S3 bucket and IAM role after you type the HyperPod name and bucket; demo/teardown.sh deletes the demo site stack after you type the stack name; CDKToolkit is deleted by hand only for an account you retire.](../images/figures/handson-99_cleanup.svg)

*Takeaway: The CDK stack deletes only what it created, so images, buckets, roles and other stacks outside it stay behind, and the AMIs, ECR images, HyperPod resources and demo stack outside it are deleted by their own scripts, while CDKToolkit stays for the next deployment.*


## Why

- **Every step asks for a confirmation word.** This reduces the chance of deleting the wrong cluster or stack.
- **Each thing you created has its own delete command.** The extension, the demo, HyperPod and the cluster go separately, so it is clear what each removes, and the infrastructure is one CDK stack, so one `cdk destroy` is enough.
- **The remaining instances are listed at the end.** A table shows any instance still tagged `project=gpu-sandbox-on-aws`.

**Before you start:** check what you created. The cluster and images come from [01 Cluster and images](01_cluster_and_images.md), HyperPod from [07 HyperPod scenario](07_hyperpod.md), the demo site from [09 Demo site (CloudFront)](09_demo_site.md), and the Agent Sandbox extension from [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md).

??? note "Terms (expand if a word is new to you)"
    - **CloudFormation stack**: a unit that creates and deletes several AWS resources together. The CDK stack from cluster creation (`02_create_cluster.sh`, `<CLUSTER_NAME>-cdk`) and the demo site are separate stacks.
    - **CDKToolkit**: the stack `cdk bootstrap` creates. It holds the S3 bucket, ECR repository and deployment roles CDK uses.
    - **Node group**: a set of EKS nodes that use the same instance type and settings. You grow and shrink it by changing the node count (`desiredSize`).
    - **Scale to zero**: setting a node group's node count to zero, which stops the instance charges but keeps the configuration.
    - **Launch template**: a set of settings used to launch EC2 instances. In this repository the CDK stack creates one per node group, and the nested virtualization option of the Kata CPU node lives in one too.
    - **KMS key waiting period**: a deleted KMS key does not disappear right away; it stays in the `Pending deletion` state for a set period (7 days here) and is deleted after that.
    - **AMI, snapshot**: the disk image an instance boots from, and the EBS copy where that image is actually stored. The snapshot can remain after the AMI is deregistered.
    - **ECR repository**: the storage unit of the AWS container image registry.
    - **SandboxClaim, SandboxWarmPool, SandboxTemplate**: in the Agent Sandbox extension, a request to borrow one sandbox, a pool of sandboxes started in advance, and the pod settings of those sandboxes.
    - **Warm pool**: a set of sandboxes started before any request arrives. You get one quickly, but they hold resources (including GPUs) while waiting.
    - **NAT gateway, Elastic IP**: the managed gateway that nodes in private subnets use to reach the internet, and the static public IP attached to it. Both are billed by the hour.

    More detail is in the [Glossary](../reference/glossary.md).

!!! warning "Validation status and safety"
    Deleting the scenario C CDK stack and `08_cleanup.sh --images` on a scenario A cluster ran in a practice account; the record does not say whether the AMI step ran ([run record](../reference/sources.md#aws-run-record)). `hyperpod/delete.sh` and `demo/teardown.sh` passed shellcheck only and have not been run end to end on AWS. In a shared or production account, confirm by name, tags and creation time that a resource belongs to this hands-on before deleting it (ideally, run from an account or role dedicated to this hands-on). The check commands below only read.

## Order

```mermaid
flowchart TD
    X["0. Delete Agent Sandbox objects<br/>(only if you used the extension)"] --> A["1. scripts/hyperpod/delete.sh<br/>(only if you built scenario B)"]
    A --> B["2. scripts/08_cleanup.sh<br/>CDK stack and AMIs (--images to delete the images too)"]
    D["Demo site demo/teardown.sh<br/>(only if you built 09, independent of the cluster)"] --> C
    B --> C["3. Check remaining instances and resources outside the scripts"]
```

*Takeaway: delete what lives inside the cluster (Agent Sandbox objects, HyperPod) first, then the cluster. The demo stack is independent and can go at any time, but finish it before the checks in step 3.*

## Time and cost

Deleting the CDK stack (`cdk destroy`) removes the node groups, the cluster and the NAT gateway in turn, so it takes a while, and HyperPod deletion polls every 30 seconds until the cluster is gone (neither duration was measured). The demo stack includes a CloudFront distribution, which can also take a while to delete. After cleanup GPU node charges stop, but ECR images and AMI snapshots you keep incur storage charges, and the secrets KMS key is deleted after a 7-day waiting period.

Load variables such as `$AWS_REGION` and `$CLUSTER_NAME` with `source scripts/config.env` first. Things inside the cluster (Agent Sandbox objects, HyperPodPyTorchJobs, sandbox pools) are deleted with kubectl, so keep `cdk/tunnel.sh` running in a second terminal until cleanup is done. kubectl deletes in the cluster of the current context, so before you start, check that `kubectl config current-context` is `<CLUSTER_NAME>-tunnel` of the cluster you are cleaning up.

## 0. Agent Sandbox extension (only if you used it)

`08_cleanup.sh` first deletes only the Deployments and Services in the `sandbox` namespace and leaves the Agent Sandbox objects alone, so delete them before the cluster to release their GPUs.

Multi-turn episode runs (`scripts/extensions/agent_sandbox.sh episodes`) delete their own claims at the end. If the Job pod is killed before it can, the script deletes the leftover claims by their run label (`gpusandbox/run=episodes-<epoch>`) after the Job. Any claim still left carries that label, so `kubectl -n sandbox get sandboxclaims -L gpusandbox/run` shows which run left it.

This command deletes all remaining claims, warm pools and templates, in that order.

```bash
kubectl -n sandbox delete sandboxclaims,sandboxwarmpools,sandboxtemplates --all
```

**What to look for:** one `... deleted` line per deleted object. A few minutes later, when this command prints `No resources found in sandbox namespace.`, all pods managed by the Agent Sandbox extension are gone. Sandbox pools created as Deployments are deleted in step 2.

```bash
kubectl -n sandbox get pods -l gpusandbox/managed-by=agent-sandbox
```

If you never installed the extension, the first command fails with an error such as `the server doesn't have a resource type "sandboxclaims"`; skip this step.

**If it fails:** if pods remain, see the "Cleanup and scale to zero" section of [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md) and the "Pod status, events and logs" section of [Troubleshooting](../reference/troubleshooting.md).

## Demo site (only if you built 09)

Delete the demo stack and every file in its bucket (table below). The CloudFront distribution goes too, and the demo URL stops working.

```bash
demo/teardown.sh
# if you deployed with another stack name
DEMO_STACK_NAME=<stack-name> demo/teardown.sh
```

The script does not read `scripts/config.env` and, like `demo/deploy.sh`, fixes the Region to `us-east-1`. It ignores `AWS_REGION` in your shell.

| Prompt | Word to type | What it deletes |
|---|---|---|
| `Delete demo stack <stack> and all files in its bucket? Type '<stack>':` | The stack name (default `gpu-sandbox-demo`) | Every object in the site bucket (`aws s3 rm --recursive`), then the whole stack (site bucket, CloudFront distribution, Origin Access Control, response headers policy, bucket policy). Waits for `stack-delete-complete`. The access log bucket has `DeletionPolicy: Retain` and stays |

**What to look for:** `deleted gpu-sandbox-demo` (or the stack name you gave), followed by `kept the access log bucket <log bucket>; when you no longer need the logs: aws s3 rb s3://<log bucket> --force`. The site bucket is deleted and the log bucket stays. Log objects expire after 90 days; delete the bucket with the printed command when you no longer need the logs. If you type a different word, it prints `aborted` and deletes nothing.

**If it fails:** if the stack ends in `DELETE_FAILED`, the resources that failed remain (per the CloudFormation documentation); check the cause in the console and delete again. The demo setup is described in section "6. Cleanup" of [09 Demo site (CloudFront)](09_demo_site.md).

## 1. HyperPod first (scenario B)

Delete the HyperPodPyTorchJobs, the HyperPod cluster, the execution role and the lifecycle bucket; the EKS cluster stays.

```bash
scripts/hyperpod/delete.sh
```

Each prompt ends with `Type '<word>' to continue:`.

| Prompt | Word to type | What it deletes |
|---|---|---|
| `This deletes HyperPod cluster ${HYPERPOD_CLUSTER_NAME} and its instances.` | The HyperPod cluster name (default `gpu-sandbox-hp`) | All HyperPodPyTorchJobs in `rl-trainer`, the HyperPod cluster (waits until it is gone), the execution role `${HYPERPOD_CLUSTER_NAME}-execution` (detaches the managed policy, deletes the inline policies `hyperpod-eks` and `lifecycle-bucket-read`, deletes the role) |
| `Empty and delete s3://${HYPERPOD_LCS_BUCKET}?` | `bucket` | The objects in the lifecycle bucket and the bucket |

**What to look for:** after `waiting for the cluster to disappear` and `deleted role <name>-execution`, the last line is `HyperPod resources deleted`.

The HyperPod dependency Helm release and the training operator add-on live inside the EKS cluster, so they go with it in step 2. A different word at the bucket prompt stops the script with `aborted` and leaves only the bucket; the HyperPod cluster and the role are already deleted by then.

**If it fails:** the script does not stop without the training operator add-on (it deletes the Jobs only when the `HyperPodPyTorchJob` CRD exists, then moves on). If the cluster deletion takes long, check its status in the SageMaker console; for other symptoms, see the "Cleanup and cost" section of [Troubleshooting](../reference/troubleshooting.md).

## 2. EKS cluster (CDK stack) and the rest

If the current kubectl context can read the `sandbox` namespace, this command deletes the sandbox pools and training Jobs first, so that GPUs and VFIO devices are released before the nodes go down, then the CDK stack (cluster, node groups, launch templates, VPC, NAT gateway, access instance, log groups), and then asks whether to delete the AMIs.

Run only one of the two commands. To keep the ECR images, run the first line; to delete them too, run the second line from the start. Running both in turn makes the second call start again from the cluster and AMI steps.

```bash
scripts/08_cleanup.sh            # pools, Jobs, the CDK stack, AMIs (asks); keeps ECR
scripts/08_cleanup.sh --images   # the same, plus the ECR repositories
```

| Order | Prompt | Word to type | What it deletes |
|---|---|---|---|
| 1 | `This deletes EKS cluster ${CLUSTER_NAME} in ${AWS_REGION} and its node groups.` | The cluster name (default `gpu-sandbox`), asked only this once | Runs `cdk/destroy.sh --yes`. If the current kubectl context can read the `sandbox` namespace, it first deletes all Jobs in `rl-trainer` and all Deployments and Services in `sandbox` of that context. The script does not check that the context belongs to the cluster you typed (see the `kubectl config current-context` check above). Then `cdk destroy ${CLUSTER_NAME}-cdk --force`, selected by `CLUSTER_NAME` and `AWS_REGION`, deletes the whole stack. After that, the log groups `/aws/lambda/${CLUSTER_NAME}-cdk-...` created outside the stack are deleted without a prompt if they exist |
| 2 | `Deregister AMI ${KATA_IOMMU_AMI_ID} and delete its snapshot?` | `ami` | Only if `KATA_IOMMU_AMI_ID` is set in `config.env`: deregisters the AMI and deletes the snapshot of its first block device |
| 3 | `Deregister the B2 HyperPod AMI ${HYPERPOD_B2_AMI_ID} and delete its snapshot?` | `ami` | Only if `HYPERPOD_B2_AMI_ID` is set in `config.env`: deregisters the B2 custom AMI and deletes its snapshot. Delete the HyperPod cluster first |
| 4 | `Delete the ECR repositories ${ECR_REPO_PREFIX}/{sandbox,trainer,control} and all images?` | `images` | Only with `--images`: deletes the three repository names one by one with `--force`. A repository that does not exist prints an error and is skipped |
| End | None | | Lists pending, running, stopping and stopped instances tagged `project=gpu-sandbox-on-aws` |

**What to look for:** if the current kubectl context can read the `sandbox` namespace you see `deleting sandbox pools and training jobs first`; if that lookup fails, the warning `cluster API not reachable (is cdk/tunnel.sh running?); the stack deletion removes the nodes anyway`. Then come the `cdk destroy` progress output, `deleting leftover log group /aws/lambda/<CLUSTER_NAME>-cdk-...` (if any) and a first instance table. If `cdk/destroy.sh` ends with `ECR repositories are kept. To delete them:` and a delete command, ignore it when you ran with `--images`; a later step deletes them. The table under the final `remaining instances tagged project=gpu-sandbox-on-aws (should be none):` must be empty. `--images` deletes all three repositories with the prefix, `sandbox`, `trainer` and `control`, whether or not this lab created them. If you share `ECR_REPO_PREFIX` with another lab, check what uses the three repositories first. A line such as `deleted gpu-sandbox/sandbox` appears once for each repository deleted successfully (for example, two lines, sandbox and control, if there is no trainer repository).

The bootstrap stack `CDKToolkit` stays, because the next deployment reuses it (if you will not use the account again, empty its S3 bucket and then delete the `CDKToolkit` stack).

If you type a different word at a prompt, the script ends with `aborted` right there and the later steps (including the final instance list) do not run. So to keep the AMI on purpose, do not decline at the prompt; write the ID down, then before running remove `KATA_IOMMU_AMI_ID` (for the B2 AMI, `HYPERPOD_B2_AMI_ID`) from `config.env`. If you loaded `config.env` into your shell, also run `unset KATA_IOMMU_AMI_ID` (or `unset HYPERPOD_B2_AMI_ID`). The script then skips that AMI step. You do not need to change `WITH_KATA_GPU`: `cdk/destroy.sh` sets both Kata switches to 0 before synth.

**If it fails:** if `cdk destroy` fails or takes very long, find the failed resource in the events of the `<CLUSTER_NAME>-cdk` stack in the CloudFormation console, and see the "Cleanup and cost" section of [Troubleshooting](../reference/troubleshooting.md) (including a remaining HyperPod cluster that holds on to the VPC).

!!! question "❓ Misconception: deleting the CDK stack removes everything from the hands-on"
    The CDK stack deletes only what it created (cluster, node groups, launch templates, VPC, NAT gateway, access instance, KMS key, the stack's log groups). The IOMMU AMI and the B2 AMI with their snapshots, the ECR repositories (created by `03_build_push_images.sh`), HyperPod's S3 bucket and IAM role, the demo stack and `CDKToolkit` are outside the stack, so other steps on this page handle them.

## Pausing: scale node groups to zero

If you plan to come back in a few days, you can keep the stack and scale only the GPU node groups to zero (minimum size 0 in the CDK stack). These commands keep `maxSize` at the stack's value and use only the AWS API, so they work without the tunnel.

```bash
source scripts/config.env
aws eks update-nodegroup-config --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name sandbox-kata-gpu --scaling-config minSize=0,maxSize=1,desiredSize=0
aws eks update-nodegroup-config --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name sandbox-gvisor --scaling-config minSize=0,maxSize=4,desiredSize=0
aws eks update-nodegroup-config --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name trainer --scaling-config minSize=0,maxSize=1,desiredSize=0
# optional: the Kata CPU node (c8i)
aws eks update-nodegroup-config --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name sandbox-kata-cpu --scaling-config minSize=0,maxSize=2,desiredSize=0
```

**What to look for:** each command returns JSON with `"status": "InProgress"` and `"type": "ConfigUpdate"`. A few minutes later, with the tunnel open, `kubectl get nodes -L gpusandbox/role` shows only the two `system` nodes (plus the HyperPod node in scenario B).

- Skip node groups you did not create (a command for a missing one just ends with an error). Scenario B has no `trainer` node group, and scenario C has only `sandbox-kata-cpu`.
- Do not scale down during training. The trainer Job has `backoffLimit: 0`, so it fails when its node disappears, and its results live in an emptyDir, so training has to start over.
- If you used the Agent Sandbox extension, scale the warm pool to zero first (for example `kubectl -n sandbox patch sandboxwarmpool kernel-eval-gvisor --type merge -p '{"spec":{"replicas":0}}'`). `agent_sandbox.sh pool <runtime> 0` also re-applies the template, which goes back to the v1 settings unless `VERSION_FILE` is set.
- To resume, run the same commands with `desiredSize` set to 1 for `trainer`, `sandbox-kata-gpu` and `sandbox-kata-cpu`, and to `$GVISOR_NODES` (default 2) for `sandbox-gvisor`. New nodes rerun their node group's boot setup: `sandbox-gvisor` and `sandbox-kata-cpu` get gVisor and the node guard again, `sandbox-kata-gpu` gets the node guard, kata-deploy (a DaemonSet) installs the Kata runtime on new Kata nodes, and `trainer` nodes have no extra boot setup. The sandbox Deployments keep their replica counts, so their pods are scheduled again once the nodes are back.
- These commands change only the node count, without CloudFormation, so set the values back before you rerun cluster creation (`02_create_cluster.sh`). What happens if you redeploy without setting them back was not checked.

**If it fails:** if nodes do not scale down or back up, see the "Checking on the AWS side (node groups, instances)" section of [Troubleshooting](../reference/troubleshooting.md).

!!! question "❓ Misconception: scaling the node groups to zero stops all charges"
    Only the GPU node charges stop. The EKS control plane, the NAT gateway, the system node group with a minimum size of 2 (two `m6i.large`, 0.192 USD per hour), the access instance (`t4g.nano`), the KMS key, CloudWatch logs, ECR storage, AMI snapshots, the S3 bucket, and the demo's CloudFront and S3 keep billing, and these commands do not stop HyperPod instances. The `CreateCluster` API allows 0 as the minimum `InstanceCount` of an instance group, but this repository neither scripts nor verifies that path, so when you are not using HyperPod, deleting it with `hyperpod/delete.sh` is the recommended option.

## 3. Check what remains

### Instances

The same command as the script's last step lists instances tagged `project=gpu-sandbox-on-aws` in a table.

```bash
aws ec2 describe-instances --region "$AWS_REGION" \
  --filters "Name=tag:project,Values=gpu-sandbox-on-aws" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name]' --output table
```

**What to look for:** the table is empty or nothing is printed.

The tag is set on the AMI builder instance, on every node of the CDK stack (the launch template's `TagSpecifications`) and on the access instance (stack tags). HyperPod instances and instances created with other tools do not carry it, so check once more by this hands-on's instance types, with their Name tag.

```bash
aws ec2 describe-instances --region "$AWS_REGION" \
  --filters "Name=instance-type,Values=${TRAINER_INSTANCE_TYPE},${GVISOR_INSTANCE_TYPE},${KATA_GPU_INSTANCE_TYPE},${KATA_CPU_INSTANCE_TYPE},${SYSTEM_INSTANCE_TYPE},t4g.nano" \
            "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,Tags[?Key==`Name`]|[0].Value]' --output table
```

**What to look for:** no instance has a name from this hands-on (a name that contains the cluster name). In a shared account, other workloads of the same types show up too, so act only after confirming by name and tags that an instance belongs to this hands-on.

This command lists the HyperPod clusters in the Region.

```bash
aws sagemaker list-clusters --region "$AWS_REGION" \
  --query 'ClusterSummaries[].[ClusterName,ClusterStatus]' --output table
```

**What to look for:** `${HYPERPOD_CLUSTER_NAME}` (default `gpu-sandbox-hp`) is not in the list.

### What to check outside the scripts

Check each resource against the expected state in the table. Most should be gone, but right after the stack deletion the KMS key is in its 7-day pending-deletion state, and `CDKToolkit` stays for the next deployment.

| Resource | Created by | Cleaned up automatically | Check command (read-only) |
|---|---|---|---|
| ECR repositories `${ECR_REPO_PREFIX}/sandbox`, `trainer`, `control` | `scripts/03_build_push_images.sh` | Only with `--images` | `aws ecr describe-repositories --region "$AWS_REGION" --query "repositories[?starts_with(repositoryName, '${ECR_REPO_PREFIX}/')].repositoryName" --output text` (after `--images`, `sandbox`, `trainer` and `control` are gone from the list; other repositories with the same prefix, such as `verl` for veRL, remain) |
| IOMMU AMI | `infra/kata/build-iommu-ami.sh` (first run of `scripts/kata/gpu_nodes.sh`) | Only if `KATA_IOMMU_AMI_ID` is set | `aws ec2 describe-images --region "$AWS_REGION" --owners self --filters "Name=tag:project,Values=gpu-sandbox-on-aws" --query 'Images[].[ImageId,Name]' --output table` |
| B2 HyperPod AMI | `infra/hyperpod/ami/build-b2-ami.sh` (`scripts/hyperpod/build_b2_ami.sh`) | Only if `HYPERPOD_B2_AMI_ID` is set | The same command as for the IOMMU AMI (same `project` tag). If a build failed, the stopped builder instance shows up in the final instance list |
| B2 builder security group `${CLUSTER_NAME}-b2-ami-builder-<timestamp>` | `infra/hyperpod/ami/build-b2-ami.sh` | The script deletes it after terminating the builder when the build succeeds. `08_cleanup.sh` does not delete it | `aws ec2 describe-security-groups --region "$AWS_REGION" --filters "Name=tag:project,Values=gpu-sandbox-on-aws" "Name=group-name,Values=${CLUSTER_NAME}-b2-ami-builder-*" --query 'SecurityGroups[].[GroupId,GroupName]' --output table` (empty is expected. If one is left, terminate the builder, then delete it with `aws ec2 delete-security-group --region "$AWS_REGION" --group-id <sg-id>`. It sits in the cluster VPC, so clean it up before deleting the CDK stack) |
| The AMI's snapshot | Created with the AMI | Together with the AMI step above | `aws ec2 describe-snapshots --region "$AWS_REGION" --owner-ids self --filters "Name=description,Values=*<ami-id>*" --query 'Snapshots[].[SnapshotId,Description]' --output table` |
| CDK stack `${CLUSTER_NAME}-cdk` (VPC, NAT gateway, cluster, node groups, launch templates, access instance) | `scripts/02_create_cluster.sh` (`cdk/deploy.sh`) | Yes (`cdk/destroy.sh`); it remains if deletion fails | `aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "${CLUSTER_NAME}-cdk"` (an error saying the stack does not exist is expected) |
| Secrets KMS key | CDK stack | Yes (after the 7-day waiting period) | In the KMS console under customer managed keys, the key with the description `EKS secrets encryption for <CLUSTER_NAME>` is in the `Pending deletion` state |
| Bootstrap stack `CDKToolkit` (S3 bucket, ECR repository, deployment roles) | `cdk bootstrap` (preparation 2 of 01) | No (reused by the next deployment) | `aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name CDKToolkit --query 'Stacks[0].StackStatus' --output text` (it is expected to remain; to delete it, empty the S3 bucket and then delete the stack) |
| S3 bucket `${HYPERPOD_LCS_BUCKET}` | `scripts/hyperpod/create.sh` | The `bucket` prompt of `hyperpod/delete.sh` | `aws s3api head-bucket --bucket "$HYPERPOD_LCS_BUCKET"` (404 is expected) |
| IAM role `${HYPERPOD_CLUSTER_NAME}-execution` | `scripts/hyperpod/create.sh` | `hyperpod/delete.sh` | `aws iam get-role --role-name "${HYPERPOD_CLUSTER_NAME}-execution"` (NoSuchEntity is expected) |
| IAM role for the training operator | If you created it yourself as described in 07 | No | Check in the IAM console under the name you used |
| Demo stack `gpu-sandbox-demo` (including the bucket and CloudFront distribution) | `demo/deploy.sh` | `demo/teardown.sh` | `aws cloudformation describe-stacks --region us-east-1 --stack-name "${DEMO_STACK_NAME:-gpu-sandbox-demo}"` (an error saying the stack does not exist is expected; the demo lives in `us-east-1` whatever the cluster Region; the retained access log bucket stays separately) |
| CloudWatch log groups | The EKS control plane logs (`/aws/eks/<CLUSTER_NAME>/cluster`) and the VPC flow log come from the CDK stack, `/aws/lambda/<CLUSTER_NAME>-cdk-...` from the stack's custom resource Lambda, plus HyperPod cluster logs | The stack's log groups go with the stack, and `cdk/destroy.sh` deletes the Lambda log groups. HyperPod logs: no | `aws logs describe-log-groups --region "$AWS_REGION" --log-group-name-prefix /aws/sagemaker/ --query 'logGroups[].logGroupName' --output text` and `--log-group-name-prefix "/aws/eks/${CLUSTER_NAME}"`, `--log-group-name-prefix "/aws/lambda/${CLUSTER_NAME}-cdk-"` |

If the CDK stack is left in `DELETE_FAILED`, its NAT gateway and Elastic IP may remain and keep billing; check the cause in the CloudFormation console and run `cdk/destroy.sh` again.

When you delete an AMI by hand, delete its snapshot too, or the storage charges continue (per the EC2 documentation, deregistering alone keeps the snapshots by default). This command does both in one go, so confirm `<ami-id>` with the query in the table above first.

```bash
aws ec2 deregister-image --region "$AWS_REGION" --image-id <ami-id> --delete-associated-snapshots
```

**What to look for:** the AMI and snapshot queries in the table above return empty results.

Local leftovers (`bench-*.jsonl`, the cluster entry and the `<CLUSTER_NAME>-tunnel` context in your kubeconfig) cost nothing; clean them up if you like.

## Scope and limits

- **Tag coverage:** HyperPod instances do not carry the `project=gpu-sandbox-on-aws` tag and have to be found by type and name (step 3).
- **Log group names:** the log group naming of HyperPod was not verified; check it yourself. The EKS control plane log group `/aws/eks/<CLUSTER_NAME>/cluster` was checked in the practice account.
- **KMS key:** the key stays in the account during the 7-day waiting period (per the KMS documentation, the actual deletion can be up to 24 hours later). Charges during the waiting period were not checked; see the KMS pricing page.
- **HyperPod scale to zero:** this repository has no script for it (see the ❓ note above).
- **Agent Sandbox objects:** `08_cleanup.sh` does not delete them (step 0), and until they go with the cluster, a warm pool holds its GPUs.

## How to verify

1. The final table of `08_cleanup.sh` is empty.
2. `${CLUSTER_NAME}` is not in the list of this command, and the CDK stack query (table above) returns an error saying the stack does not exist:

    ```bash
    aws eks list-clusters --region "$AWS_REGION" --output text
    ```

3. `${HYPERPOD_CLUSTER_NAME}` is not in the `aws sagemaker list-clusters` list (scenario B).
4. If you built the demo, `demo/teardown.sh` printed `deleted <stack>` and the note about the kept log bucket, and the demo stack query in `us-east-1` returns an error saying the stack does not exist.
5. Each resource matches the expected state in the table above. Right after deletion the KMS key is `Pending deletion` and `CDKToolkit` remains, both as expected. With `--images`, the three repositories drop out of the ECR list; other repositories with the same prefix remain.

If a resource you chose to delete does not match the expected state in the table, see the "Cleanup and cost" section of [Troubleshooting](../reference/troubleshooting.md).

??? note "References"
    | Topic | Link |
    |---|---|
    | AWS CLI `update-nodegroup-config` (resizing a managed node group) | https://docs.aws.amazon.com/cli/latest/reference/eks/update-nodegroup-config.html |
    | AWS CDK `cdk destroy` | https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-destroy.html |
    | Deleting a CloudFormation stack (`DELETE_FAILED`, retry) | https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-delete-stack.html |
    | HyperPod DeleteCluster API | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DeleteCluster.html |
    | Agent Sandbox repository (SandboxClaim, SandboxWarmPool, SandboxTemplate) | https://github.com/kubernetes-sigs/agent-sandbox |

    All sources: [this page in All references](../reference/references.md#ref-handson-99-cleanup)
