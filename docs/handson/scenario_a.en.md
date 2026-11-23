# Scenario A · Train and grade on EC2 GPUs

[Back to scenario selection](00_overview.md)

One EKS cluster runs system pods on two `m6i.large` nodes, the trainer on one `g5.2xlarge`, and the gVisor grading pool on two `g5.xlarge` nodes. The trainer generates code and the grading nodes execute it and return verdicts. Choose a five-step run to see one training cycle, or the 60-step path in step 5 to switch graders during training.

## 1. Check the account and GPU quotas { #prepare }

Use [Getting started](../getting_started.md) to set up the AWS CLI, CDK CLI, Session Manager plugin, Docker buildx, Helm, kubectl, jq, uv, and a Python virtual environment. Run the commands below from the `gpu-sandbox-on-aws` directory on your workstation with your AWS credentials active.

```bash
test -f scripts/config.env || cp scripts/config.env.example scripts/config.env
source .venv/bin/activate
uv pip install -r cdk/requirements.txt
aws sts get-caller-identity
```

In `scripts/config.env`, check `AWS_REGION` (default `us-west-2`), `CLUSTER_NAME`, and `SCENARIO="A"`. This path uses `WITH_KATA_CPU="0"`, `WITH_KATA_GPU="0"`, and `GVISOR_NODES="2"`. If your IAM role has a path, as with IAM Identity Center, set `ADMIN_PRINCIPAL_ARN` to the full IAM role ARN. [Account and tool setup](01_cluster_and_images.md)

```bash
source scripts/config.env
scripts/01_check_prereqs.sh
cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"
```

Continue once CDK bootstrap succeeds in your selected account and Region. The base cluster needs room for 6 Standard and 16 G/VT On-Demand vCPUs. Switching graders raises the G/VT requirement to 24 vCPUs. Account for instances that already use those quotas.

## 2. Create the cluster and connect { #cluster }

```bash
scripts/02_create_cluster.sh
```

Once the CDK outputs include `ClusterEndpoint` and `AccessInstanceId`, open **a separate terminal** in the same project directory and run `cdk/tunnel.sh`. Leave this SSM tunnel open to reach the private EKS API. Run the following commands in the original work terminal.

```bash
kubectl config current-context
kubectl get nodes -L gpusandbox/role,node.kubernetes.io/instance-type
```

The context should be `<CLUSTER_NAME>-tunnel`. Look for two `system` nodes, one `trainer`, and two `sandbox-gvisor` nodes, all `Ready`. Baseline compute costs about USD 3.42 per hour, plus EKS, NAT, and other charges. [Deployment errors and costs](01_cluster_and_images.md)

## 3. Push the images and verify GPU access { #gpu }

```bash
scripts/03_build_push_images.sh
```

Copy the three `export` lines printed at the end into `scripts/config.env`, using the actual values for `SANDBOX_IMAGE_URI`, `TRAINER_IMAGE_URI`, and `CONTROL_IMAGE_URI`. Run this GPU check **before deploying the grading pool** so the smoke pod can claim a free GPU.

```bash
scripts/04_install_gpu_stack.sh
```

Look for `Starting gVisor...` in the smoke pod log to identify the runtime. The separate line `cuda ok: NVIDIA A10G 2048.0` confirms the A10G completed the CUDA operation and returned the expected sum of 2048. If the script ends with a warning, check that both lines appeared before continuing. [gVisor GPU check](02_gvisor.md)

## 4. Deploy the v1 grading pool { #pool }

```bash
scripts/05_setup_namespaces_auth.sh
scripts/06_deploy_sandboxes.sh gvisor v1
scripts/ops/verify.sh gvisor v1
```

Check that both `sandbox-gvisor-v1` pods show `1/1` Ready. The first `verify.sh` check prints the gVisor kernel version under `sandbox:` and the host kernel version under `node:`. Compare the two yourself. The script prints `pool sandbox-gvisor-v1 verified` after the automated checks, including blocked connections and the verdicts for the test submissions, pass. [Read the verification results](04_sandbox_pools.md)

**Optional benchmark.** Run `scripts/ops/bench.sh 32` before training starts. It benchmarks v1 pools. For `gvisor`, check how many of the 32 requests succeeded, the p50 and p95 grading times, and the requests completed per second. The script prints the path to `bench-*.jsonl` at the end. [Benchmark results and measurement conditions](08_benchmark.md#runtime-results)

## 5. Start training { #train }

Choose one path below. The training command follows the logs. Look for `gvisor/v1` on the `routing` line, verdicts on the `batch` lines, and model updates on the `train` lines. Note the Job name (`grpo-…`). [Read the training log](05_grpo_training.md)

=== "Five steps · Verify training"

    ```bash
    scripts/07_run_grpo.sh 5
    ```

    When you see `done`, go to [step 7](#cleanup).

=== "60 steps · Switch graders during training"

    Both pools will run side by side. **Before starting training**, expand the `sandbox-gvisor` group to four nodes. The two extra `g5.xlarge` instances add about USD 2.012 per hour.

    ```bash
    source scripts/config.env
    aws eks update-nodegroup-config --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
      --nodegroup-name sandbox-gvisor --scaling-config minSize=0,maxSize=4,desiredSize=4
    kubectl get nodes -l gpusandbox/role=sandbox-gvisor
    ```

    Check the node list again until four nodes are `Ready`, then start training.

    ```bash
    scripts/07_run_grpo.sh
    ```

    Once the first batch has verdicts from v1, leave the trainer logs and SSM tunnel running. Continue to step 6 in another work terminal.

## 6. Optional · Switch the running trainer to v2 { #switch }

```bash
scripts/ops/rollout.sh gvisor v1 v2
```

The script deploys and verifies v2, then compares both versions on the same test submissions. It changes the routing configuration after `PARITY PASS`. In the trainer terminal, wait for `SWITCH` (`sandbox_version_switch` in raw JSON), **then a v2 batch with a verdict other than `sandbox_error`**. When all results in a batch come from one pool’s cache, the trainer logs no new `reward_batch` event.

Run the following command to scale v1 pods to zero only after confirming a verdict from v2. If the parity check fails, v1 keeps serving. If v2 returns only errors after routing changes, keep v1 available and follow the [rollback procedure](06_sandbox_update.md). If training finishes before a v2 verdict appears, the live switch remains unconfirmed for this run.

```bash
scripts/ops/rollout.sh gvisor v1 v2 --finish
```

Keep all four nodes until training finishes. Scaling the node group down during training could terminate a node that hosts a v2 pod. [Example of a trainer batch after the switch](06_sandbox_update.md#switch-batches)

## 7. Confirm completion and clean up { #cleanup }

```bash
kubectl -n rl-trainer get jobs
aws sts get-caller-identity
kubectl config current-context
```

Check that the Job you recorded in step 5 shows `Complete`. Verify that the account and context match the lab you intend to delete. If you have finished using the cluster, leave the tunnel open and run the cleanup script.

```bash
scripts/08_cleanup.sh
```

Check and enter the cluster name at the prompt. To delete the ECR images and repositories as well, use `scripts/08_cleanup.sh --images` instead. Follow [99 Cleanup](99_cleanup.md) to check that the final instance table is empty and that the EKS cluster and CDK stack are gone, then close the tunnel.
