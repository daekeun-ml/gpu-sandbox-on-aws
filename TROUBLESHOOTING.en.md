[한국어](TROUBLESHOOTING.md) | **English**

# Troubleshooting

Find the symptom you see below. For more diagnostic commands, see the [troubleshooting guide](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/).

| Symptom | Start here |
|---|---|
| `set ... in scripts/config.env`, `missing tool` | [Configuration and scripts](#configuration-and-scripts) |
| `kubectl` cannot connect, or nodes are missing | [CDK, tunnel and cluster](#cdk-tunnel-and-cluster) |
| GPU smoke test fails | [gVisor](#gvisor), [Kata](#kata) |
| `Pending`, `ContainerCreating`, or `Running` with `0/1` ready | [Sandbox pools](#sandbox-pools) |
| HTTP `401` or `403` | [Authentication errors](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#401-and-403-responses) |
| `CUDA out of memory` or repeated `sandbox_error` | [Training](#training) |
| Missing `hyperpodrun` or a failed cluster creation | [HyperPod](#hyperpod) |
| A switch leaves the old version grading requests | [Version switches](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#version-switches-routing) |
| Resources or charges remain after cleanup | [Cleanup and cost](#cleanup-and-cost) |

## Check these first

1. If `kubectl` cannot connect on A, B1 or C, check `cdk/tunnel.sh` and the `<CLUSTER_NAME>-tunnel` context. Managed B2 uses the `$CLUSTER_NAME` context from the [B2 connection step](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/07_hyperpod_b2/).
2. Once connected, replace `<pod>` with the pod name from the first command below.

```bash
kubectl -n sandbox get pods -o wide -L gpusandbox/runtime,gpusandbox/version
kubectl -n sandbox describe pod <pod>
kubectl -n sandbox logs <pod>
```

- For `Pending` or `ContainerCreating`, read the events in `describe`.
- For `Running` with `0/1` ready, check `device probe ok=` and `egress is open`. The pod takes new requests when it is Ready.
- For repeated scoring failures during training, check `sandbox_error` in TRL's `reward_batch` or veRL's `reward_extra_info`.

## Configuration and scripts

- **`[error] set <NAME> in scripts/config.env`**: the value is empty or still contains `__SET_ME__`. For the image addresses (`SANDBOX_IMAGE_URI` and others), paste the `export` lines that `03_build_push_images.sh` prints at the end.
- **`[error] missing tool: <tool>`**: install the tool and run `scripts/01_check_prereqs.sh` again.
- **Push fails on a duplicate tag when you run `03_build_push_images.sh` again**: the ECR repositories never overwrite a tag. Set a new `IMAGE_TAG`, run it again, and update `config.env` with the new addresses it prints.
- **Image builds are very slow or run out of disk**: building amd64 images on an arm64 PC is slow because of emulation. Build on an x86_64 host with at least 100 GB of disk.

More: [Configuration and scripts](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#configuration-and-scripts)

## CDK, tunnel and cluster

- **`SSM parameter /cdk-bootstrap/hnb659fds/version not found`**: CDK is not bootstrapped in that account and Region. Run the `cdk bootstrap` command from "Common setup" in the README once.
- **`python3 cannot import aws_cdk` or `ModuleNotFoundError: No module named 'aws_cdk'`**: the virtualenv is not active in this terminal. Run `source .venv/bin/activate` and try again. If there is no virtualenv yet, run `uv pip install -r cdk/requirements.txt` first, as in "Common setup" in the README.
- **`Cloud assembly schema version mismatch`**: the CDK CLI is too old. Upgrade it to 2.1148.1 or later with `npm install -g aws-cdk`.
- **`ADMIN_PRINCIPAL_ARN must list IAM role or user ARNs, not sts assumed-role ARNs`**: one of the values is not in IAM role or user ARN form. If you set an STS session ARN (`arn:aws:sts::...:assumed-role/...`), replace it with the ARN of that role, or leave the value empty.
- **`cdk/tunnel.sh` ends with `TargetNotConnected`**: right after deployment the access instance may not be ready yet.
    1. Run it again in a few minutes.
    2. If it still fails after 10 minutes, check the SSM `PingStatus` of the access instance.
    3. If it is `ConnectionLost`, reboot it with `aws ec2 reboot-instances --instance-ids <instance-id>` and try again once it is `Online`. The instance ID is the `via i-...` value that `tunnel.sh` prints.
- **kubectl fails with `TLS handshake timeout`**: a tunnel to an earlier cluster may still hold `127.0.0.1:8443`. Close the terminal of the old tunnel with Ctrl-C and run `cdk/tunnel.sh` again.
- **Node group creation fails with a vCPU limit error**:
    - **For a GPU node group**: raise `Running On-Demand G and VT instances` in Service Quotas. Scenario A needs 16 vCPU: 8 for the trainer and 4 for each of the two gVisor nodes.
    - **If a system node or CPU node failed**: check the `Running On-Demand Standard` quota instead.
- **Node group creation fails with `InsufficientInstanceCapacity`, or the first creation hangs for about 30 minutes and then rolls back entirely**: first check why the node group failed. `InsufficientInstanceCapacity` means the AZ could not provide the requested number of instances of that type.
    - **If you were adding a GPU node group to an existing cluster**: only that update rolls back, so wait and retry the failed step.
    - **If GPU capacity caused the initial cluster creation to roll back**: use the commands below to create the cluster without GPU node groups and then add them one at a time (for `SCENARIO` `A` and `WITH_KATA_GPU` `"0"` in `scripts/config.env`).

```bash
scripts/02_create_cluster.sh --hyperpod-b2                  # no EC2 GPU node groups
CHANGE_SCENARIO=1 scripts/02_create_cluster.sh --hyperpod   # adds the gVisor nodes (B1)
CHANGE_SCENARIO=1 scripts/02_create_cluster.sh              # adds the trainer (A)
```

More: [CDK and the tunnel](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#cdk-and-the-tunnel), [Cluster and nodes](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#cluster-and-nodes)

## gVisor

- **The smoke pod prints a PyTorch error instead of a `cuda ok:` line, or the sandbox log says `torch.cuda.is_available() is False`**: the GPU check inside the sandbox failed.
    1. Check the node's `nvidia.com/gpu` count and the NVIDIA device plugin pods.
    2. If the GPU count shows, check that the device plugin uses `deviceListStrategy: cdi-cri`, and read the PyTorch error.
- **A GPU pod ends in `StartError` with `reading mounts file:` in its events**: one CDI hook of the NVIDIA toolkit does not work with gVisor. `04_install_gpu_stack.sh` turns that hook off. Check that `CDI_DISABLE_HOOKS` on the device plugin DaemonSet is `disable-device-node-modification`.
- **`04_install_gpu_stack.sh` stops with `every GPU on the sandbox-gvisor nodes is in use`**: a sandbox pool you already deployed holds every GPU on the gVisor nodes, so the smoke pod cannot get one. Scale the pool to zero with the printed command, run the script again, then bring the pool back with `scripts/06_deploy_sandboxes.sh gvisor v1`.
- **The node log says `NVIDIA driver ... is not supported by gVisor`**: the node's driver version is not on the support list of the pinned gVisor release. Use an AMI with a supported driver, or change `GVISOR_RELEASE` to a release that supports that driver.
    - **CDK-managed EC2 node groups**: each new node installs gVisor on first boot. If you changed `GVISOR_RELEASE` for these node groups, run `scripts/02_create_cluster.sh` again with the same scenario.

More: [gVisor](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#gvisor)

## Kata

- **A Kata CPU pod cannot open KVM (no `/dev/kvm` on the node)**: nested virtualization is not on for the node. Check the `CpuOptions` of the running instance, and whether the instance type supports nested virtualization (`SupportedFeatures`).
- **`scripts/kata/gpu_nodes.sh` ends with `add KATA_IOMMU_AMI_ID and WITH_KATA_GPU=1 ...`**: this is expected. The first run only builds the AMI. Put the printed `KATA_IOMMU_AMI_ID` in `scripts/config.env`, set `WITH_KATA_GPU` to `"1"`, then run `scripts/02_create_cluster.sh` and `scripts/kata/gpu_nodes.sh` again, in that order.
- **`no passthrough GPUs advertised`**: the IOMMU is off, or the GPU Operator did not prepare the node. First check that `KATA_IOMMU_AMI_ID` is an AMI built by this repository's script. If the AMI is right, check the node label `nvidia.com/gpu.workload.config=vm-passthrough` and the GPU Operator pods.
- **A Kata GPU pod stays in `ContainerCreating` and the node log says `No available IOMMU models`**: an older AMI did not load the `vfio_iommu_type1` module.
    - **For new nodes**: rebuild the AMI with the current script, update `KATA_IOMMU_AMI_ID`, and run `scripts/02_create_cluster.sh` again.
    - **On the current node**: run `modprobe vfio_iommu_type1`. You need to run it again after a reboot.

More: [Kata](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#kata)

## Sandbox pools

- **`06_deploy_sandboxes.sh` fails with `exceeded its progress deadline`**: look at the pod STATUS first.
    - **If it is `Pending` or `ContainerCreating`**: check the Events in `kubectl -n sandbox describe pod <pod>`.
    - **If it is `Running` but `0/1`**: look in `kubectl -n sandbox logs <pod>`. On a `device probe ok=False` line, the `info` on the same line gives the reason the device check failed. On an `egress is open, refusing work:` line, check the egress blocking setup.
- **The log says `egress is open, refusing work: 169.254.169.254:80 (connected)`**: the pod opened a connection to the EC2 Instance Metadata Service (IMDS) address, so the NetworkPolicy is not enforced. List the policies with `kubectl -n sandbox get networkpolicy`, and check that `enableNetworkPolicy` is on for the VPC CNI add-on.
- **`sandbox_error` with `no free sandbox in sandbox-<runtime>-<version>...`**: no pod took the evaluation within 600 seconds. First check that some pods are Ready.
    - **If every pod stays busy**: add replicas. On a GPU pool each pod uses one GPU, so if no GPU is free, add nodes as well.
- **401 and 403 responses**: a token, JWKS or allowlist setting is wrong. Fixes per error message are in [401 and 403 responses](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#401-and-403-responses).

More: [Sandbox pools and readiness](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#sandbox-pools-and-readiness)

## Training

- **`CUDA out of memory` in the TRL trainer log**: vLLM and training share one GPU. Add `--per-device-batch=2` and `--grad-accum=8` to the Job template `args` (the product stays 16). If memory is still short, add `--max-completion-length=512`, then `--vllm-gpu-memory-utilization=0.3`.
- **Many `sandbox_error` results in `reward_batch`**: check the same pool with `scripts/ops/verify.sh <runtime> <version>`. The failed step and its error message tell you whether to look at authentication, the network, too few pods, or evaluation timeouts first.

More: [Training](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#training)

## HyperPod

### Managed B2 in Northern Virginia

| Symptom observed during the lab | What resolved it |
|---|---|
| The group shows `InService`, but `CurrentCount` is below `TargetCount` | Inspect `list-cluster-nodes --include-node-logical-ids`. The original GPU requests reported `INSUFFICIENT_CAPACITY_ERROR`. HyperPod retried in `Continuous` mode and allocated all three GPUs. |
| The wizard stack is `CREATE_COMPLETE`, but the training add-on reports `K8sResourceNotFound` for cert-manager | Run `scripts/hyperpod/prepare_managed.sh` after the workers are ready. It waits for the certificate webhook and recreates the failed add-on at the same version. |
| The grading nodes report driver `595.112.07` or `nvidia_uvm` is in use | Once both grading workers are `Ready`, `scripts/hyperpod/reboot_sandboxes.sh` stages `580.178.04` on disk, reboots the workers through HyperPod and verifies the running module. |

[Commands, screenshots and cleanup](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/07_hyperpod_b2/)

- **Cluster `InService`, trainer instance `Pending`.** During the B1 run, the cluster reached `InService` before the trainer joined EKS. Run `source scripts/config.env`, check the trainer with `aws sagemaker list-cluster-nodes --region "$AWS_REGION" --cluster-name "$HYPERPOD_CLUSTER_NAME"`, then use `kubectl get nodes -L sagemaker.amazonaws.com/node-health-status` to look for `Ready` and `Schedulable`. [B1 run and screenshots](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/handson/07_hyperpod/#how-to-verify)
- **Worker `Pending` with `Insufficient cpu` or `Insufficient memory`.** Check allocated resources with `kubectl describe node <trainer-node>`. On the `ml.g5.2xlarge` used for B1, the worker shared the node with the operator and system pods. The template requests 5 vCPUs and 24 GiB for the worker.

- **A pod cannot find `hyperpodrun`**: the trainer image was built without `HYPERPOD=1`. Run `HYPERPOD=1 scripts/03_build_push_images.sh` with a new `IMAGE_TAG`, put the printed `TRAINER_IMAGE_URI` in `scripts/config.env`, and start training again.
- **`check_gvisor.sh` prints `NOT supported`**:
    - **On the trainer node**: this is expected. The trainer node does not run sandboxes.
    - **If a sandbox node prints it**: check that the instance group's `ImageId` matches `HYPERPOD_B2_AMI_ID`, and that `GVISOR_RELEASE` supports the driver in that AMI.
- **The cluster is `Failed` after CreateCluster**: read the reason in the `failure` field of the script output, and compare it with the HyperPod EKS prerequisites.

More: [HyperPod](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#hyperpod)

## Cleanup and cost

Run `source scripts/config.env` from the repository root before checking the Region or using the AWS CLI below.

- **Charges remain after `08_cleanup.sh`**: check that you ran it in the right Region and whether AMIs or snapshots remain.
    - **If you created HyperPod**: `08_cleanup.sh` does not delete HyperPod. Run `scripts/hyperpod/delete.sh` before `scripts/08_cleanup.sh`.
    - **If only ECR remains**: check the repository names in the ECR delete command that `cdk/destroy.sh` printed, then run it.
    - **To delete ECR in the same pass**: run the first cleanup as `scripts/08_cleanup.sh --images`.
- **`g4dn.metal` is billed while you are not using it**: scale the node group to zero (command below).

```bash
aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu \
  --scaling-config minSize=0,maxSize=1,desiredSize=0
```

More: [Cleanup and cost](https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/reference/troubleshooting/#cleanup-and-cost)
