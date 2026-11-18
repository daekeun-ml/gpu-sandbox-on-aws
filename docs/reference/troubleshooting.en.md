# Troubleshooting

**TL;DR** Per-stage "symptom, cause, fix" tables for what commonly blocks installation and operation, with the diagnostic commands to run at each stage.

## Pain point

Symptoms appear far from their cause: a node user data error shows up several steps later as "pod Pending" or "no GPU". The kernel, devices and network seen inside gVisor and Kata pods differ from the node's, so you need to separate what to check on the node from what to check inside the pod. Authentication failures and NetworkPolicy blocks only turn the reward into `None` and do not stop training, so the training log shows them only as a count of `sandbox_error`.

## Why

- **It starts from the symptom.** Find the row by error message or observation, and the cause and the fix are on the same line.
- **The diagnostic commands use the same names, labels and paths as the repository scripts.** You can paste and run them as they are.
- **The causes come from the repository code and verified facts.** Parts not confirmed by code or documentation are marked "(presumed)".

!!! warning "Basis of this page"
    On 2026-11-14 the author ran the CDK deploy of scenario C, the tunnel, adding Kata CPU nodes (`kata/cpu_nodes.sh`) and the deletion in a practice account. In the practice account on 2026-11-18, scenario A ran on `g5` in us-west-2. The cluster was created without GPU node groups and they were added with updates (see "When there is no GPU capacity" below), and `03_build_push_images.sh`, `04_install_gpu_stack.sh`, `05_setup_namespaces_auth.sh`, `06_deploy_sandboxes.sh gvisor v1` (1 replica) with `ops/verify.sh gvisor v1`, `07_run_grpo.sh 5` and `08_cleanup.sh --images` ran. `ops/rollout.sh` in scenario A, `ops/bench.sh`, Kata GPU and HyperPod B1 and B2 were not run ([validation status](../index.md)). The symptoms and causes come from the scripts' error messages, the code's behavior and official documentation, and the wording can differ by tool version, so check the rows marked "(presumed)" yourself in particular.

??? note "Terms"
    - **readiness**: the check the kubelet runs to see whether a pod is ready to receive requests. In this repository a pod becomes Ready only when both the GPU probe and the egress denial check pass.
    - **`kubectl debug node`**: a command that starts a privileged debug pod on a node so that you can see the node's file system (`/host`) and processes.
    - **user data, cloud-init**: user data is the script an EC2 instance runs at first boot, and cloud-init is the tool that runs it. Its output goes to `/var/log/cloud-init-output.log`.
    - **nodeadm, NodeConfig**: the bootstrap tool that joins EKS AL2023 nodes to the cluster, and its configuration. The containerd runtime settings are merged here too.
    - **EndpointSlice**: the list of pod addresses behind a Service, with the Ready state of each address. The DNS of a headless Service returns only Ready addresses.
    - **SSM Session Manager**: an AWS Systems Manager feature that opens a shell on an instance with IAM permissions, without SSH.

    More terms are in the [Glossary](glossary.md).

## Diagnostic tools

### Pod status, events and logs

The commands below show, in order, the list of sandbox pods (with the runtime and version labels), the events and logs of one pod, and the recent events of the whole cluster.

```bash
source scripts/config.env      # CLUSTER_NAME and AWS_REGION for the AWS commands on this page
kubectl -n sandbox get pods -o wide -L gpusandbox/runtime,gpusandbox/version
kubectl -n sandbox describe pod <pod>          # Events: scheduling, RuntimeClass, probe failures
kubectl -n sandbox logs <pod>                  # "device probe ok=..." and "egress is open, refusing work: ..."
kubectl -n sandbox logs <pod> --previous       # after a restart (for example a gpu_fault)
kubectl get events -A --sort-by=.lastTimestamp | tail -30
```

Two lines of the server log classify most readiness problems. At startup the sandbox server logs `device probe ok=<True|False> info=<...>`, and when it reaches an egress target it logs `egress is open, refusing work: <target list>` at ERROR level.

### Checking inside the sandbox (kubectl exec)

The commands below pick one pod of the gVisor v1 pool, compare the kernel version inside the sandbox with the node's, and check whether a new process sees the GPU.

```bash
pod="$(kubectl -n sandbox get pods -l gpusandbox/runtime=gvisor,gpusandbox/version=v1 \
  -o jsonpath='{.items[0].metadata.name}')"
# Kernel seen inside the sandbox (gVisor Sentry or Kata guest kernel) vs the node's kernel
kubectl -n sandbox exec "$pod" --\
  uname -r
kubectl get node "$(kubectl -n sandbox get pod "$pod" -o jsonpath='{.spec.nodeName}')" \
  -o jsonpath='{.status.nodeInfo.kernelVersion}{"\n"}'
# GPU from a fresh process inside the sandbox, the same check the readiness probe runs
kubectl -n sandbox exec "$pod" --\
  python -c "import torch; ok = torch.cuda.is_available(); print('cuda', ok, torch.version.cuda); print(torch.cuda.get_device_name(0) if ok else 'no device')"
```

If the two kernel values are the same, the pod is running under runc, so check the RuntimeClass first. A process started with `exec` also runs inside the sandbox, so the NetworkPolicy and the node guard apply to it in the same way. The `--\` at the end of a line is the kubectl argument separator `--` followed by a line continuation.

### Viewing /info with the probe tool

`/info` requires authentication, so `curl` cannot show it. Instead, run the control image's probe tool as a Job in the `rl-trainer` namespace (ServiceAccount `sandbox-probe`, label `gpusandbox/client: "true"`) to get an `/info` summary per pod and the golden verdicts. The first command below checks every Ready pod, and the second checks one pod that is not Ready directly by its IP.

```bash
# Ready pods behind the headless Service: /info summary per pod and golden verdicts
scripts/ops/verify.sh gvisor v1

# A pod that is not Ready is not in DNS: point the probe tool at its pod IP (run from the repo root)
pod_ip="$(kubectl -n sandbox get pod "$pod" -o jsonpath='{.status.podIP}')"
bash -c "source scripts/lib.sh && source scripts/lib_jobs.sh && run_tool_job probe-debug probe --address ${pod_ip}:8000 --device cuda"
```

The first lines of the output are one `{"endpoint": ..., "pod": ..., "runtime": ..., "version": ..., "kernel_release": ..., "gpu": ..., "egress_blocked": ...}` per pod, followed by a `PASS` or `FAIL` line per golden entry. A pod that is not Ready returns 503 to evaluation requests, so it is normal for its golden lines to FAIL with `sandbox_error`. The probe tool does not print `egress_open_targets` from `/info`, so find out which target is open from the `egress is open` line in the server log. For CPU pools use `--device cpu`.

### Checking on the node (kubectl debug node)

The commands below start a privileged debug pod on the node the pod runs on and open a shell in it. A shell prompt means it worked.

```bash
node="$(kubectl -n sandbox get pod "$pod" -o jsonpath='{.spec.nodeName}')"
kubectl debug "node/$node" -it --profile=sysadmin \
  --image=public.ecr.aws/amazonlinux/amazonlinux:2023
```

Inside the debug shell, the node's root file system is mounted at `/host`.

```bash
chroot /host
cat /proc/cmdline                                 # Kata GPU node: intel_iommu=on iommu=pt
ls -l /dev/kvm                                    # Kata nodes (CPU and GPU) need it
cat /proc/driver/nvidia/version                   # gVisor and trainer nodes: loaded driver
/usr/local/bin/runsc nvproxy list-supported-drivers | grep -wF <driver-version>
grep -n -A3 runsc /etc/containerd/config.toml     # runsc handler merged by nodeadm
cat /etc/containerd/runsc.toml                    # nvproxy settings read by the shim
iptables -w -S GPUSANDBOX-GUARD                   # node guard chain on sandbox nodes
systemctl status gpusandbox-node-guard --no-pager
tail -n 100 /var/log/cloud-init-output.log        # user data output (gVisor install, node guard)
journalctl -u containerd -u kubelet --since "30 min ago" --no-pager | tail -50
exit
```

When you are done, delete the debug pod left in the `default` namespace.

```bash
kubectl get pods -n default -o name | grep node-debugger-
kubectl -n default delete pod <node-debugger-pod>
```

### Checking on the AWS side (node groups, instances)

The commands below show the node group's status and health issues, and the five most recent activities of the Auto Scaling group that the node group uses.

```bash
ng=sandbox-gvisor      # system, trainer, sandbox-gvisor, sandbox-kata-cpu, sandbox-kata-gpu
aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "$ng" \
  --region "$AWS_REGION" --query 'nodegroup.{status: status, health: health}'
asg="$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "$ng" \
  --region "$AWS_REGION" --query 'nodegroup.resources.autoScalingGroups[0].name' --output text)"
aws autoscaling describe-scaling-activities --auto-scaling-group-name "$asg" \
  --region "$AWS_REGION" --max-items 5 --query 'Activities[].[StatusCode,StatusMessage]' --output text
```

If a node does not join the cluster, connect to the instance ID shown in `health` and read the user data log. The Session Manager plugin must be installed locally, and the node IAM role needs SSM permissions (`AmazonSSMManagedInstanceCore`) for the session to open. The node role of the CDK stack does not have this policy (`node_policies` in `cdk/gpusandbox_cdk/stack.py`). If you need an SSM session, attach it to the node role only while you debug; otherwise use the console output below.

```bash
aws ssm start-session --target <instance-id> --region "$AWS_REGION"
# on the instance
sudo tail -n 200 /var/log/cloud-init-output.log
sudo journalctl -u nodeadm-config -u nodeadm-run --no-pager | tail -100
```

If you cannot use SSM, the console output often shows user data errors as well (presumed).

```bash
aws ec2 get-console-output --instance-id <instance-id> --latest --output text --region "$AWS_REGION" | tail -100
```

## Configuration and scripts

| Symptom | Cause | Fix |
|---|---|---|
| `scripts/config.env not found. Copy scripts/config.env.example and edit it.` | The configuration file does not exist | `cp scripts/config.env.example scripts/config.env`, then fill in the values |
| A message such as `[error] set CLUSTER_NAME in scripts/config.env` | A value is empty or still `__SET_ME__` (`require_vars`) | Fill in the value. For values a script prints, such as image URIs, run that script (`03_build_push_images.sh`, `kata/gpu_nodes.sh`) first |
| `[error] missing tool: <tool>` | A required CLI is not on PATH (`require_tools`) | Install it and rerun `scripts/01_check_prereqs.sh` |
| `render: <template>: missing variable 'X'` | The template's `${X}` has no value. `render.py` does not fall back to an empty value | `export X=...` in config.env or in the shell |
| Adding Kata CPU nodes (`scripts/kata/cpu_nodes.sh`) stops with `no sandbox-kata-cpu node group: set WITH_KATA_CPU=1 in scripts/config.env and run scripts/02_create_cluster.sh again` | The stack was created without `WITH_KATA_CPU=1` in a scenario other than C | Put `WITH_KATA_CPU=1` into config.env and rerun `02_create_cluster.sh` (CDK adds only the c8i node group), then rerun `kata/cpu_nodes.sh` |
| Adding Kata GPU nodes (`scripts/kata/gpu_nodes.sh`) ends with `add KATA_IOMMU_AMI_ID and WITH_KATA_GPU=1 to scripts/config.env, run scripts/02_create_cluster.sh again, then re-run this script` | Expected behavior: the first run only bakes the AMI (about 10 minutes, per the script's message) | Put the printed AMI ID and `WITH_KATA_GPU=1` in, rerun `02_create_cluster.sh` (type `metal`), then rerun `kata/gpu_nodes.sh` |
| `scripts/kata/gpu_nodes.sh` stops with `no sandbox-kata-gpu node group: set WITH_KATA_GPU=1 in scripts/config.env and run scripts/02_create_cluster.sh again` | The AMI exists, but `02_create_cluster.sh` was not rerun with `WITH_KATA_GPU=1` | Set `WITH_KATA_GPU=1`, rerun `02_create_cluster.sh`, then rerun `kata/gpu_nodes.sh` |
| Rerunning `03_build_push_images.sh` fails to push because the tag already exists | The ECR repositories were created with IMMUTABLE tags | Change `IMAGE_TAG` to a new value (for example `v1-hp`), rerun, and update config.env with the printed URIs |
| The `03_build_push_images.sh` build is very slow or runs out of disk | Emulating linux/amd64 on an arm64 machine, large base images (PyTorch, vLLM) | Build on an x86_64 host with 100 GB or more of disk (per the script comment) |

## CDK and the tunnel

| Symptom | Cause | Fix |
|---|---|---|
| `cdk deploy` fails with `SSM parameter /cdk-bootstrap/hnb659fds/version not found. Has the environment been bootstrapped?` | CDK was not bootstrapped in that account and Region | Run `cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"` once |
| The deploy stops during synth with cdk-nag `AwsSolutions-...` findings and `ValidationFailed` | cdk-nag found a finding that is not acknowledged (the stack code or the cdk-nag version changed) | Fix it from the rule ID and the resource in the output. If you deliberately do not follow the rule, acknowledge it with a reason in `_suppress` of `cdk/gpusandbox_cdk/stack.py`; never without a reason |
| `Cloud assembly schema version mismatch` | The CDK CLI is older than `aws-cdk-lib` in `cdk/requirements.txt` | Upgrade the CLI to 2.1148.1 or later with `npm install -g aws-cdk`. This repository pins `aws-cdk-lib` 2.276.0 instead of 2.277.0, which needs CLI 2.1148.2 (as of 2026-11-14) |
| `ADMIN_PRINCIPAL_ARN must list IAM role or user ARNs, not sts assumed-role ARNs` | An STS session ARN (`arn:aws:sts::...:assumed-role/...`) was set | Set the role ARN from `aws iam get-role --role-name <role> --query Role.Arn --output text`, or leave it empty |
| `EKS_PUBLIC_ACCESS_CIDR must be a single IPv4 address in /32 form` | A range such as `0.0.0.0/0` or a /24 was set | Leave it empty (private only) or set one workstation address as `/32` |
| `cdk/tunnel.sh` stops with `stack <CLUSTER_NAME>-cdk has no outputs; run cdk/deploy.sh first` | The stack does not exist yet, or `CLUSTER_NAME` or `AWS_REGION` differs from the deploy | Check the config.env values and run `02_create_cluster.sh` |
| `cdk/tunnel.sh` ends with `TargetNotConnected` | The access instance's SSM agent has not registered with Systems Manager yet (right after the deploy) | Wait a few minutes and run it again |
| `cdk/tunnel.sh` stops with `[error] missing tool: session-manager-plugin` | The Session Manager plugin for the AWS CLI is missing | [Install the Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) and check with `session-manager-plugin --version` |
| `cdk/destroy.sh` warns `cluster API not reachable (is cdk/tunnel.sh running?)` | The tunnel is down, so the pools and Jobs cannot go first | You can leave it: the stack deletion removes the nodes anyway. To delete the pools first, start the tunnel and run it again |

## Cluster and nodes

| Symptom | Cause | Fix |
|---|---|---|
| Node group creation fails, with a vCPU limit error (`VcpuLimitExceeded` or similar) in health or the scaling activities | Not enough "Running On-Demand G and VT instances" quota (vCPU based). New accounts can have a default of 0 | Request an increase in Service Quotas. Trainer 8 + gVisor 2 x 4 = 16 vCPU, and `g4dn.metal` adds 96 vCPU. HyperPod has separate "ml.<type> for cluster usage" quotas |
| Node group creation fails with an error that the instance type is not supported in the requested AZ | The AZs of the cluster subnets do not offer that type (especially `g4dn.metal`) | Check the per-AZ offerings printed by `scripts/01_check_prereqs.sh`. The CDK stack creates private subnets in two AZs of the Region (`max_azs=2`), and every node group uses both. If an AZ without the type is picked, use another Region or change the subnet selection in `cdk/gpusandbox_cdk/stack.py` (this repository has no option for it) |
| Node group creation fails with a capacity error (`InsufficientInstanceCapacity` or similar) | On-Demand capacity in that AZ is temporarily short (general EC2 behavior) | Use another AZ or retry after a while. To switch to an instance type that has capacity, see "When there is no GPU capacity" below |
| The initial cluster create hangs for about 30 minutes, then rolls back completely | When a GPU node group cannot launch (`InsufficientInstanceCapacity`), CloudFormation waits about 30 minutes, then rolls back the whole initial create | Create the cluster without GPU node groups first and add them with updates ("When there is no GPU capacity" below). A failed update rolls back only that update |
| The node group exists, but nodes do not appear in `kubectl get nodes` (node creation failures in health) | Errors in user data (the NodeConfig and shell parts built by `infra/eks/userdata.py`), a failed gVisor tarball download or sha512 check, a wrong custom AMI | Find the instance as in "Checking on the AWS side" above and read `/var/log/cloud-init-output.log` and `journalctl -u nodeadm-config -u nodeadm-run` |
| `kubectl` or `helm` fails with `Unable to connect to the server`, a timeout, or connection refused on `127.0.0.1:8443` | The EKS API endpoint is private only, so it is unreachable without the tunnel. The tunnel terminal was closed, or another kubectl context is in use | Run `cdk/tunnel.sh` again in a second terminal, and check that `kubectl config current-context` is `<CLUSTER_NAME>-tunnel` |

**When there is no GPU capacity:** an initial create that includes GPU node groups rolls back completely on a single capacity failure. Create the cluster in a layout without GPU node groups first, then add the node groups one update at a time. A failed update rolls back only that update.

```bash
scripts/02_create_cluster.sh --hyperpod-b2                  # no EC2 GPU node groups
CHANGE_SCENARIO=1 scripts/02_create_cluster.sh --hyperpod   # adds the gVisor nodes (B1)
CHANGE_SCENARIO=1 scripts/02_create_cluster.sh              # adds the trainer (A)
```

To check capacity, launch an instance and terminate it at once. An On-Demand Capacity Reservation request can report no capacity even when a launch succeeds. You can override the instance types per run in `scripts/config.env`. For example, when `g6` has capacity, set `GVISOR_INSTANCE_TYPE` and `TRAINER_INSTANCE_TYPE` to `g6.xlarge` and `g6.2xlarge`.

## gVisor

| Symptom | Cause | Fix |
|---|---|---|
| The pod stays in `ContainerCreating`, and the events show a message like `no runtime for "runsc" is configured` (wording differs by containerd version) | The RuntimeClass `handler` (`runsc`) differs from the containerd `runtimes.<name>` key, or the NodeConfig merge failed | Compare the `handler` in `kubectl get runtimeclass gvisor -o yaml` with `runtimes.runsc` in the node's `/etc/containerd/config.toml`. If you renamed it, make both the same |
| Events show an error that `containerd-shim-runsc-v1` cannot be found or run (presumed) | The gVisor install in user data failed (download, sha512 check) | On the node, check `ls -l /usr/local/bin/runsc /usr/local/bin/containerd-shim-runsc-v1` and `cloud-init-output.log`. Fix the cause, then replace the node |
| The gVisor smoke pod of `04_install_gpu_stack.sh` has no `cuda ok:` line and shows a torch error, or the sandbox log shows `torch.cuda.is_available() is False` | The device plugin is not on that node, or it is not in `cdi-cri` mode. Without NVIDIA devices in the OCI spec, nvproxy does not turn on | With the commands below, check the node's `nvidia.com/gpu` allocatable, the device plugin pod and `deviceListStrategy: cdi-cri` |
| A gVisor GPU pod ends in `StartError` with the event `OCI runtime start failed: starting container: reading mounts file: error unmarshaling mounts: unexpected end of JSON input` | nvidia-container-toolkit 1.20.1 on the AMI adds a `disable-device-node-modification` CDI hook, which reads `<rootfs>/proc/driver/nvidia/params`. runsc runs CDI hooks in the gofer, before the container has a `/proc`, so the hook fails. The runsc debug log shows `error opening nvidia driver params file: openat proc/driver/nvidia/params: no such file or directory`. It is not GPU-specific (`g6` is affected too), and a gVisor pod without a GPU on the same node runs fine | `04_install_gpu_stack.sh` runs `kubectl -n kube-system set env ds/nvdp-nvidia-device-plugin CDI_DISABLE_HOOKS=disable-device-node-modification` after `helm upgrade --install nvdp ...` and waits for the rollout (this sets the plugin's `--cdi-disable-hooks` flag, which chart v0.20.1 does not expose as a value). Check with the last command below, and if the setting is missing, run `04_install_gpu_stack.sh` again. runc pods (the trainer) lose only this hook, and they cannot create device nodes anyway without `CAP_MKNOD` |
| `nvidia.com/gpu` is visible but CUDA initialization fails, and the node's `cloud-init-output.log` shows `WARNING: NVIDIA driver ... is not supported by gVisor ... nvproxy` | The node's driver is not on the nvproxy list of the pinned gVisor release. Unknown versions, which are not on the list, fail in every case | Check on the node with `runsc nvproxy list-supported-drivers`. Use an AMI with a supported driver, or raise `GVISOR_RELEASE` to a release that knows that driver |
| gVisor GPU does not work on T4 nodes such as `g4dn` | T4 on gVisor is not tested in this repository, so it is unverified. The driver condition (the EKS AL2023 NVIDIA AMI loads the proprietary module with GSP off) is the same as on the default g5, so the driver flavor is not a reason to exclude it | Use g5 (A10G), this repository's default, or the alternative g6 (L4). To use T4, verify it yourself with `runsc nvproxy list-supported-drivers` on the node, the smoke test and `ops/verify.sh` |
| You edited `runsc.toml`, but nothing changed | The shim reads only the file named by the runtime option's `ConfigPath`, and pods already running keep the old settings | Check `ConfigPath = '/etc/containerd/runsc.toml'` in NodeConfig, then recreate the pods |

The commands below show, in order, the GPU allocatable of the nodes with the device plugin label, the device plugin pods, the values of the installed chart and the CDI hook setting. Right after `04_install_gpu_stack.sh` restarts the device plugin, the GPU column can briefly show `0` for the gVisor node, and the smoke pod still gets its GPU. If the column is still empty or `0` when you check again, the device plugin did not advertise a GPU on that node.

```bash
kubectl get nodes -l gpusandbox/device-plugin=cdi \
  -o custom-columns='NODE:.metadata.name,ROLE:.metadata.labels.gpusandbox/role,GPU:.status.allocatable.nvidia\.com/gpu'
kubectl -n kube-system get pods -o wide | grep nvdp
helm get values nvdp -n kube-system
kubectl -n kube-system get ds nvdp-nvidia-device-plugin -o yaml | grep -A1 CDI_DISABLE_HOOKS
```

The last command should print `name: CDI_DISABLE_HOOKS` and, on the next line, `value: disable-device-node-modification`.

## Kata

| Symptom | Cause | Fix |
|---|---|---|
| The Kata CPU smoke pod fails with an error like "cannot open KVM" in events or logs, and the node has no `/dev/kvm` | Nested virtualization did not reach the node (the CDK stack sets it in the launch template `CpuOptions`, but no document says that managed node groups pass it through), or the instance type does not support nested virtualization in that Region | With the commands below, check the running instance's `CpuOptions` and the instance type's `SupportedFeatures` (`nested-virtualization`) |
| `scripts/kata/cpu_nodes.sh` stops with `kata runtime classes missing` | The kata-deploy DaemonSet did not start on the Kata node (nodeSelector `gpusandbox/role=sandbox-kata`, taint toleration), or the install failed | kata-deploy pod status and logs, `kubectl get runtimeclass` |
| Kata nodes added later do not get the runtime installed | The kata-deploy chart's default `deploymentMode: job` handles only the nodes present at install time | `deploymentMode: daemonset`, as in this repository's values |
| Kata pods do not start after a node reboot (presumed) | nodeadm rewrites `/etc/containerd/config.toml` on every boot, so the handler that kata-deploy added disappears | Keep NodeConfig's `imports = ["/etc/containerd/conf.d/*.toml"]` (included in `infra/eks/userdata.py`; its effect is unverified) |
| `scripts/kata/gpu_nodes.sh` stops with `no passthrough GPUs advertised; see docs/reference/troubleshooting.md`, and there is no `nvidia.com/pgpu` | (1) IOMMU off: the AMI lacks `intel_iommu=on` (2) the node label `nvidia.com/gpu.workload.config=vm-passthrough` is missing (3) the host loaded the NVIDIA driver (an NVIDIA AMI was used) (4) GPU Operator operands or NFD do not tolerate the taint and never start (5) with `ccManager.defaultMode` set to `on`, cc-manager exits on T4 (its effect on pgpu advertising is presumed) | With the commands below, check `/proc/cmdline`, the number of IOMMU groups, `lsmod`, `lspci -nnk`, the node labels and the `gpu-operator` pods. Check that `KATA_IOMMU_AMI_ID` is the AMI that `build-iommu-ami.sh` built |
| A Kata GPU pod is Pending, and events show a node affinity or selector mismatch | The `scheduling.nodeSelector` of the RuntimeClass `kata-qemu-nvidia-gpu` (`nvidia.com/cc.ready.state=false`) is merged into the pod, and the node lacks this label (cc-manager did not set it, or `ccManager.defaultMode` is `on`) | Check the node labels. Check the GPU Operator value `ccManager.defaultMode: "off"`, then rerun `kata/gpu_nodes.sh` |
| A Kata GPU pod is Pending with `Insufficient memory` or `Insufficient nvidia.com/pgpu` | The RuntimeClass overhead (10240Mi, 1 CPU) is added to the pod's requests: 16Gi + 10Gi per pod | Reduce the replicas, as in `scripts/06_deploy_sandboxes.sh kata-qemu v1 2`, or check Allocated resources in `kubectl describe node <node>`. Also count the experimental kata-clh pool, which shares the same node |
| Pods of the `kata-clh` pool are not created, and the ReplicaSet events say the RuntimeClass `kata-clh-nvidia-gpu` does not exist | The experimental RuntimeClass exists only if `kata/gpu_nodes.sh` ran with `ENABLE_EXPERIMENTAL_CLH_GPU=1` | Check with `kubectl -n sandbox describe rs -l gpusandbox/runtime=kata-clh`. To use it, first replace `__NVIDIA_GUEST_VMLINUX__` and `__NVIDIA_GUEST_IMAGE__` in the values file, run `ENABLE_EXPERIMENTAL_CLH_GPU=1 scripts/kata/gpu_nodes.sh`, and then `infra/kata/experimental-clh-gpu/check-clh-gpu.sh`. Upstream does not support this path |
| Kata GPU pod creation fails with a timeout (presumed) | VFIO pins the whole guest memory before the VM starts, which takes time | Keep kubelet `runtimeRequestTimeout: 20m` (included in the Kata GPU NodeConfig of `infra/eks/userdata.py`), and do not make memory limits larger than needed |
| A `g4dn.metal` node does not come back after a reboot (third-party report) | There are reports of warm reboot problems on metal instances | Bake the kernel arguments into the AMI so that user data does not reboot (`build-iommu-ami.sh`). If the node does not come back, replace the instance |

The commands below check, in order, the nested virtualization setting of the CPU nodes, the Kata runtime components, and the labels and pgpu advertising of the GPU node. `"NestedVirtualization": "enabled"` in `CpuOptions` and `8` on the pgpu line mean everything is in order.

```bash
# CPU node: nested virtualization on the running instance and support for the instance type
aws ec2 describe-instances --region "$AWS_REGION" \
  --filters "Name=tag:eks:nodegroup-name,Values=sandbox-kata-cpu" "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].CpuOptions'
aws ec2 describe-instance-types --instance-types "$KATA_CPU_INSTANCE_TYPE" --region "$AWS_REGION" \
  --query 'InstanceTypes[0].ProcessorInfo.SupportedFeatures'
# Kata runtime pieces
kubectl -n kube-system get pods -o wide | grep kata-deploy
kubectl get runtimeclass
# GPU node: labels the GPU Operator and the RuntimeClass depend on
node="$(kubectl get nodes -l gpusandbox/kata-gpu=true -o jsonpath='{.items[0].metadata.name}')"
kubectl get node "$node" -L nvidia.com/gpu.workload.config,nvidia.com/cc.ready.state
kubectl get node "$node" -o jsonpath='{.status.allocatable.nvidia\.com/pgpu}{"\n"}'
kubectl -n gpu-operator get pods -o wide
kubectl get runtimeclass kata-qemu-nvidia-gpu -o yaml
```

In the debug shell on a Kata GPU node, look at the PCI binding before you `chroot`.

```bash
dnf install -y -q pciutils && lspci -nnk -d 10de:   # every T4 should show "Kernel driver in use: vfio-pci"
chroot /host
cat /proc/cmdline                                    # must contain intel_iommu=on iommu=pt
ls /sys/kernel/iommu_groups | wc -l                  # 0 means the IOMMU is off
lsmod | grep -E 'vfio|nvidia'                        # vfio_pci loaded, nvidia not loaded
```

## Sandbox pools and readiness

| Symptom | Cause | Fix |
|---|---|---|
| The rollout in `06_deploy_sandboxes.sh` times out after 30 minutes; pods are Running but `0/1` | Readiness failure. `/readyz` returns 200 only when the GPU probe succeeded, egress denial is verified and the pod is not draining | Use the `device probe ok=` line and the `egress is open, refusing work:` line in `kubectl -n sandbox logs <pod>` to tell the causes apart, then go to the rows below |
| The log shows `egress is open, refusing work: 169.254.169.254:80 (connected)` | The pod reaches IMDS: the NetworkPolicy is not applied | Check with the commands below whether NetworkPolicy is enforced. Also check the IMDS settings of the node group launch template (IMDSv2 required, hop limit 1) |
| The log shows `<node IP>:10250 (refused: reachable)` or `(connected)` | The VPC CNI policy agent allows traffic between a pod and its own node's IP regardless of policies. The node guard (iptables) is missing or not applied yet | On the node, `iptables -w -S GPUSANDBOX-GUARD` and `systemctl status gpusandbox-node-guard`. Check that the node template includes the node guard |
| The log shows the API server address (`<IP>:443`) as open | The default deny is not applied yet. Standard mode allows new pods until the policies apply | Wait a moment; the check repeats every 5 seconds. If it persists, check `kubectl -n sandbox get networkpolicy` and the vpc-cni settings |
| The log shows `device probe ok=False info={'error': ...}` | No GPU visible (see the gVisor and Kata tables), a CUDA initialization error, or the 120-second timeout | Read the error string. Reproduce it with the `python -c` command in "Checking inside the sandbox" |
| The sandbox verification (`scripts/ops/verify.sh`) stops at step 2 with `a denial check failed: see docs/reference/troubleshooting.md` | A target marked `REACHABLE` in the output (IMDS, Kubernetes API, node kubelet, internet) is open | Follow the rows above per target. If the internet is open, the default deny NetworkPolicy is not applied |
| `scripts/ops/verify.sh` stops at step 4 with `NetworkPolicy did not block an outside caller` | NetworkPolicy enforcement is off | Check `enableNetworkPolicy` of the vpc-cni add-on |
| The result is `sandbox_error` with the error `no free sandbox in sandbox-<runtime>-<version>.sandbox.svc.cluster.local:8000` | No Ready pods (the headless Service DNS is empty), or every pod was busy evaluating for 600 seconds | Check the Ready addresses with the EndpointSlice command below, add replicas |
| After switching to v2, pods turn NotReady one by one and you eventually get `no free sandbox` | v2's `SANDBOX_MAX_EVALS=200`: a pod starts draining after 200 evaluations. Only the production gateway (`GATEWAY_RECYCLE_PODS=1`) deletes such pods, so in direct mode they stay NotReady | Delete them with `kubectl -n sandbox delete pod <pod>`, and the Deployment creates new ones. In the hands-on, set the value in the version file to `0` or use the gateway |
| A pod restarts right after an evaluation, and the verdict has the `gpu_fault` flag | A CUDA error on the reference path makes the server suspect the device and turn fatal, and liveness restarts the container (intended behavior) | `kubectl -n sandbox logs <pod> --previous`. If it repeats on the same node, `kubectl cordon <node>` and replace the node |
| The `sandbox_error` error is `harness exceeded outer timeout` | The whole harness exceeded `2 x SANDBOX_EVAL_TIMEOUT_S + 30` seconds (210 seconds by default). The reference or the GPU hung | Check the node and GPU state; if it repeats, delete the pod |

The commands below show the vpc-cni add-on settings (`enableNetworkPolicy`), the NetworkPolicies in the `sandbox` namespace, and the EndpointSlice of the pool Service. The number of Ready addresses in the EndpointSlice is the number of pods that can take requests.

```bash
aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name vpc-cni --region "$AWS_REGION" \
  --query 'addon.{version: addonVersion, config: configurationValues}'
kubectl -n sandbox get networkpolicy
kubectl -n sandbox get endpointslices -l kubernetes.io/service-name=sandbox-gvisor-v1 -o wide
```

## 401 and 403 responses

Look up the actual error strings (`HTTP 401: {"detail": ...}`) in the `FAIL` lines of the probe tool. The `reward_batch` events in the trainer log show only counts per status. The client does not retry 4xx responses on another pod.

| Response and detail | Cause | Fix |
|---|---|---|
| 401 `authentication is not configured on this service` | One of the four `SANDBOX_AUTH_*` values is empty (the pod log shows `authentication not configured (missing ...)`) | Check the pod env with the commands below, rerun `scripts/06_deploy_sandboxes.sh` |
| 401 `missing bearer token` | The caller sent no token: `SANDBOX_TOKEN_FILE` is missing or the projected volume is not mounted | Check the Job template's `sandbox-token` volume and the `SANDBOX_TOKEN_FILE` env |
| 401 `token verification keys unavailable` | The JWKS file could not be read: the ConfigMap `sandbox-auth-jwks` is missing or broken | `scripts/ops/sync_jwks.sh` |
| 401 `unknown signing key` | The token's `kid` is not in the JWKS: the API server's signing key changed and was not synced | `scripts/ops/sync_jwks.sh` (the jwks-sync CronJob in production) |
| 401 `invalid token: Audience doesn't match` | A token with a different audience: the default API token was sent, or the gateway token (`gpu-sandbox-gateway`) was sent to a sandbox | Check `audience: gpu-sandbox` on the projected token |
| 401 `invalid token: Invalid issuer` | `SANDBOX_AUTH_ISSUER` differs from the cluster issuer | Compare with the issuer from `aws eks describe-cluster`, rerun `06_deploy_sandboxes.sh` |
| 401 `invalid token: Signature has expired` | An expired token: a client that read the token once and cached it for a long time | Re-read the file on every request, as `read_token` does |
| 403 `subject '...' is not allowed` | The ServiceAccount is not on the allowlist | Add it to `SANDBOX_ALLOWED_SUBJECTS` and rerun `06_deploy_sandboxes.sh` (the Deployment env changes) |
| 401 `token not authenticated for this audience` (gateway) | The audience of the token calling the gateway is not `gpu-sandbox-gateway`, or TokenReview failed | Check the projected token audience of the calling pod |
| 403 `subject '...' is not allowed` (gateway) | Not in `GATEWAY_ALLOWED_SUBJECTS` | Edit the gateway Deployment env |

The wording after `invalid token:` is a PyJWT message and can differ slightly by version.

The commands below show, in order, the auth settings the pod actually received, the issuer and key IDs of the cluster and of the ConfigMap, and the claims of a short-lived token made for an allowed subject. The two `kid` lists should be the same, and the token's `iss` and `aud` should match the pod settings.

```bash
# Auth settings the sandbox pod actually received
kubectl -n sandbox get pod "$pod" \
  -o jsonpath='{range .spec.containers[0].env[*]}{.name}={.value}{"\n"}{end}' | grep SANDBOX_AUTH
# Issuer and key IDs: cluster vs ConfigMap
aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" \
  --query cluster.identity.oidc.issuer --output text
kubectl get --raw /openid/v1/jwks \
  | python3 -c "import json,sys; print(sorted(k['kid'] for k in json.load(sys.stdin)['keys']))"
kubectl -n sandbox get configmap sandbox-auth-jwks -o jsonpath='{.data.jwks\.json}' \
  | python3 -c "import json,sys; print(sorted(k['kid'] for k in json.load(sys.stdin)['keys']))"
# Claims of a short-lived token for an allowed subject (do not paste the token anywhere)
kubectl -n rl-trainer create token sandbox-probe --audience gpu-sandbox --duration 10m \
  | python3 -c "import sys,json,base64; p=sys.stdin.read().split('.')[1]; print(json.dumps(json.loads(base64.urlsafe_b64decode(p + '=' * (-len(p) % 4))), indent=2))"
```

## NetworkPolicy

| Symptom | Cause | Fix |
|---|---|---|
| The probe Job or trainer requests fail with a connection timeout (`ConnectTimeout`), and the probe shows FAIL | The calling pod lacks the `gpusandbox/client: "true"` label, or the call comes from a namespace other than `rl-trainer` | `kubectl -n rl-trainer get pods --show-labels`. For a Job you wrote yourself, add the label to the pod template |
| After deploying the gateway in production, the probe of `ops/verify.sh` and the parity of `ops/rollout.sh` fail | `k8s/production/gateway.yaml.tpl` overwrites `allow-clients-to-sandbox-api` of the same name so that it admits only the gateway | Add a policy that admits only the probe Job (`app: sandbox-probe`), as below (an example, not in the repository). Another option is to apply it only while verifying and delete it afterwards |
| Pods in other namespaces cannot connect to the gateway | `allow-trainers-to-gateway` admits only pods in the `rl-trainer` namespace on TCP 8080 | Move the caller to `rl-trainer` or add a policy |

```yaml
# Example, not in the repository: lets the operator probe Jobs reach sandbox pods
# next to the production policy that admits the gateway only (policies are additive).
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-probe-to-sandbox-api
  namespace: sandbox
spec:
  podSelector:
    matchLabels: {app.kubernetes.io/name: gpu-sandbox}
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels: {kubernetes.io/metadata.name: rl-trainer}
          podSelector:
            matchLabels: {app: sandbox-probe}
      ports: [{protocol: TCP, port: 8000}]
```

## Training

| Symptom | Cause | Fix |
|---|---|---|
| CUDA out of memory in the trainer log (A10G 24 GB) | vLLM colocate shares the GPU with training: `--vllm-gpu-memory-utilization` 0.35 plus the training memory (1.5B, LoRA, activations) | Reduce one at a time: `--per-device-batch 2 --grad-accum 8` (keeps the product at 16), `--max-completion-length 512`, `--vllm-gpu-memory-utilization 0.3`, `--vllm-max-model-length 1536`. Add the flags to the Job template's `args` |
| Startup fails with an error saying vLLM cannot allocate the KV cache or similar (wording differs by vLLM version, presumed) | `--vllm-gpu-memory-utilization` is too low to hold a KV cache for the `--vllm-max-model-length` length | Raise the value a little or lower `--vllm-max-model-length` |
| Startup fails with an error saying the generation batch is not divisible by `num_generations` or similar (as of TRL 1.18.0) | `--per-device-batch` x `--grad-accum` is not a multiple of `--num-generations` (8) | Make the product a multiple of 8 |
| Training runs, but `status` in `reward_batch` shows many `sandbox_error` | Authentication, NetworkPolicy, pool exhaustion (tables above) | See the actual error strings with the probe tool: `scripts/ops/verify.sh <runtime> <version>` |
| No checkpoints, `final` adapter or `sandbox_metrics.jsonl` remain after training | `/outputs` in the Job template is an emptyDir: once the container ends there is no way to take the files out, and they disappear with the pod | `reward_batch` events remain in `kubectl logs`. To keep the results, mount a PVC (for example FSx for Lustre) at `/outputs` (see [06 Scaling with veRL](../production/06_scaling_with_verl.md)) |

```yaml
# k8s/trainer/job-grpo.yaml.tpl: extra flags go into args
          args:
            - --output-dir=/outputs/grpo
            - --max-steps=${MAX_STEPS}
            - --model=${MODEL_ID}
            - --metrics-file=/outputs/grpo/sandbox_metrics.jsonl
            # Example: lower memory use on a 24 GB A10G
            - --per-device-batch=2
            - --grad-accum=8
            - --max-completion-length=512
```

## Version switches (routing)

| Symptom | Cause | Fix |
|---|---|---|
| After step 4 of the version switch (`scripts/ops/rollout.sh`), the trainer never logs `sandbox_version_switch` | (1) The ConfigMap is mounted with `subPath`, so updates are not delivered (2) kubelet sync delay (about 1 minute, per the script's message) (3) a ConfigMap in another namespace was changed (4) in gateway mode the gateway reads the routing, not the trainer (5) a JSON error makes it keep the last good table | Check the mount type and the file inside the pod with the commands below. This repository's templates mount a directory, so if you edited the template, revert it |
| The trainer stops with `RoutingError: no pool for runtime=... version=...` | The active version is not in that runtime's `pools`. For example, `--runtime kata-clh-cpu` while the active version is `v2`, or the new version was not added to `routing.json.tpl` | Add it to `pools` in `routing.json.tpl` and render again. To go back to the previous version, `scripts/ops/rollout.sh <runtime> <to> <from>` |
| The trainer pod stays in `ContainerCreating`, and the events show a mount error saying the ConfigMap `sandbox-routing` does not exist | `rl-trainer` has no routing ConfigMap | `scripts/05_setup_namespaces_auth.sh` |
| With veRL (gateway), some requests are still scored on the previous version after the switch | Expected behavior: a group that has already started stays pinned to its version for the TTL (900 seconds) from its first request | Check `GATEWAY_GROUP_PIN_TTL_S`. Do not delete the previous pool until the pins end |
| Parity fails with `speedup moved <old> -> <new>` | The speedup ratio between the two versions exceeds the tolerance (`--speedup-tolerance`, default 0.35) | If the change is intended, add `--speedup-tolerance` to the parity call in `ops/rollout.sh` to adjust it; otherwise investigate the cause. `ops/rollout.sh` does not switch when parity fails |

The commands below show, in order, the content of the routing ConfigMap, how the trainer pod mounts it, the routing file inside the pod, and the latest switch and batch events. The `active` value in the ConfigMap and in the file inside the pod should be the same.

```bash
kubectl -n rl-trainer get configmap sandbox-routing -o jsonpath='{.data.routing\.json}' | python3 -m json.tool
trainer="$(kubectl -n rl-trainer get pods -l app=grpo-trainer -o jsonpath='{.items[0].metadata.name}')"
kubectl -n rl-trainer get pod "$trainer" -o jsonpath='{.spec.containers[0].volumeMounts}{"\n"}'   # no subPath
kubectl -n rl-trainer exec "$trainer" --\
  cat /etc/gpusandbox/routing/routing.json
kubectl -n rl-trainer logs "$trainer" | grep -E '"event": "(sandbox_version_switch|reward_batch)"' | tail -5
```

## Agent Sandbox and multi-turn episodes

Before it submits the Job, the multi-turn episode run (`scripts/extensions/agent_sandbox.sh episodes <runtime>`) checks the CRDs, the ServiceAccount and the warm pool, and stops with one of the messages below when a check fails. This path has been checked with local tests only and has not been run on a cluster. How to run it is in [11 Multi-turn episodes](../handson/11_multi_turn.md).

| Symptom | Cause | Fix |
|---|---|---|
| `agent-sandbox CRDs not found: run scripts/extensions/agent_sandbox.sh install` | The Agent Sandbox controller and CRDs (`sandboxclaims`, `sandboxwarmpools`) are not in the cluster | Run `scripts/extensions/agent_sandbox.sh install`, then run `episodes` again |
| `ServiceAccount rl-trainer/sandbox-episode not found: run scripts/extensions/agent_sandbox.sh install` or `system:serviceaccount:rl-trainer:sandbox-episode may not create SandboxClaims: run scripts/extensions/agent_sandbox.sh install` | The ServiceAccount `sandbox-episode` that the multi-turn Job uses is missing, or the RoleBinding `sandbox-claims` that gives it claim permissions does not list it. This happens when `05_setup_namespaces_auth.sh` or `install` ran before the account was added to the repository | Run `install` again. It re-applies `k8s/base/trainer-rbac.yaml` and `trainer-claims-rbac.yaml` and is safe to re-run |
| `warm pool kernel-eval-<runtime> not found: run scripts/extensions/agent_sandbox.sh pool <runtime>` | The SandboxTemplate and SandboxWarmPool for that runtime were not created | Run `scripts/extensions/agent_sandbox.sh pool <runtime> [n]` |
| `warm pool kernel-eval-<runtime> has no Ready sandbox (kubectl -n sandbox get sandboxwarmpool kernel-eval-<runtime>)` | `status.readyReplicas` of the warm pool is 0: the sandbox pods are still starting or have not passed readiness (GPU probe, egress denial check) | Check with the command in the message and `kubectl -n sandbox get pods -l gpusandbox/managed-by=agent-sandbox`. If pods stay at `0/1`, follow the "Sandbox pools and readiness" table above |
| `sandboxes started without system:serviceaccount:rl-trainer:sandbox-episode in their allowlist: <names>. Run scripts/extensions/agent_sandbox.sh pool <runtime>, then delete them ...` | Warm sandboxes keep the env they started with (`updateStrategy` `OnReplenish`). A sandbox started before `sandbox-episode` was on the allowlist answers episode requests with 403 (`subject '...' is not allowed`). The same happens when `pool` runs with `SANDBOX_ALLOWED_SUBJECTS` set in the shell or config.env without `sandbox-episode` | Run `scripts/extensions/agent_sandbox.sh pool <runtime>` again to update the template, then delete the sandboxes named in the message with `kubectl -n sandbox delete sandboxes.agents.x-k8s.io <name>`. The pool starts replacements with the new env |

## HyperPod

| Symptom | Cause | Fix |
|---|---|---|
| `scripts/hyperpod/check_gvisor.sh` prints `NOT supported by gVisor ...: keep sandboxes on EC2 (mode B1)` | Expected on the trainer node: gVisor release-20261109.0 does not know the default HyperPod EKS AMI driver 595.91.07. On a sandbox node it means the custom AMI was not applied | Leave the trainer node as it is. For a sandbox node, check `HYPERPOD_B2_AMI_ID` and the instance group's `ImageId` |
| B2 `create-cluster` goes to `Failed`, and the lifecycle log shows `runsc missing` or `NVIDIA driver ... is not supported` | The sandbox group did not boot from the custom AMI, or the AMI was baked with another `B2_NVIDIA_DRIVER_VERSION` or `GVISOR_RELEASE` | Run `scripts/hyperpod/build_b2_ami.sh` again and create the cluster with the new `HYPERPOD_B2_AMI_ID` |
| The B2 lifecycle log shows `unsupported or missing config version` or `containerd rejected the edited` | containerd's config file location or schema is not what the script expects | On the node, find the `--config` path with `ps -o args= -C containerd`, set `HYPERPOD_CONTAINERD_CONFIG` in `on_create_sandbox.sh` to it, and upload the lifecycle scripts again |
| `scripts/hyperpod/build_b2_ami.sh` reports `customization failed` | The driver swap or the gVisor check failed on the builder | Read the `GPUSANDBOX-B2-BUILD: FAILED ...` line and the log before it with the printed `get-console-output` command, then delete the stopped builder with `terminate-instances` |
| The status is `Failed` after CreateCluster | See the `FailureMessage` the script prints. Prerequisites (EKS authentication mode API or API_AND_CONFIG_MAP, VPC CNI 1.18.3 or later, private subnets, a supported Kubernetes version), S3 read permission for the lifecycle scripts | Compare with the [HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html). Keep the `sagemaker-` prefix in the bucket name |
| HyperPodPyTorchJob pods are Pending | The node label `sagemaker.amazonaws.com/node-health-status` is not `Schedulable` (for example during deep health checks), or the instance type does not match | `kubectl get nodes -L sagemaker.amazonaws.com/node-health-status,node.kubernetes.io/instance-type` |
| Pods fail because they cannot find `hyperpodrun` | The trainer image was built without `HYPERPOD=1` | `HYPERPOD=1 scripts/03_build_push_images.sh`. ECR tags are IMMUTABLE, so you need a new `IMAGE_TAG` |
| No more pods fit on a HyperPod node (`Too many pods`) | One ENI per instance: ml.g6.xlarge and ml.g6.2xlarge allow at most 14 pods (the limit of the default ml.g5 has not been checked) | Count the DaemonSets running on that node, and exclude unneeded DaemonSets from HyperPod nodes |
| Training starts from the beginning again after a job restart | `/outputs` is an emptyDir, so the pod on the new node has no checkpoints | Mount shared storage (an FSx for Lustre PVC) at `/outputs` |

## Cleanup and cost

| Symptom | Cause | Fix |
|---|---|---|
| Charges remain after running `08_cleanup.sh` | HyperPod was not deleted first, the AMI and snapshot confirmation step was skipped, ECR remains because `--images` was not passed, or it ran in a different Region | `scripts/hyperpod/delete.sh` first, check the remaining-instances table printed at the end of `08_cleanup.sh`, and if needed run `scripts/08_cleanup.sh --images` |
| Costs keep coming while you are not using `g4dn.metal` for a while | A node bills as long as it exists (about 7.8 USD per hour) | `aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu --scaling-config minSize=0,maxSize=1,desiredSize=0` |
| `cdk destroy` takes long or fails with `DELETE_FAILED` (presumed) | Resources created outside the stack still hold on to the VPC (HyperPod ENIs, nodes launched by Karpenter and so on) | Delete HyperPod first (`scripts/hyperpod/delete.sh`) and retry `scripts/08_cleanup.sh`. Find the failed resource in the stack events in the CloudFormation console |

> ❓ **Misconception: if a pod is Running, the sandbox is ready.**
> In this repository, Running only means that the container started. Readiness also requires the GPU probe and the egress denial check to pass, and a pod that is not Ready does not appear in the headless Service DNS, so it receives no requests. "Running, but no requests arrive" is mostly a readiness problem, so look at the READY column (`0/1`) of `kubectl -n sandbox get pods` and at the server log first.

> ❓ **Misconception: if training keeps running, the sandboxes are fine.**
> Infrastructure errors become reward `None` and do not stop training. If errors continue, training still runs, but fewer samples get a score. Check the share of `sandbox_error` in the `status` of the `reward_batch` events regularly.

??? note "References"
    | Topic | Link |
    |---|---|
    | Configure Amazon VPC CNI network policy | [Configure Amazon VPC CNI network policy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
    | Amazon EC2 nested virtualization | [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) |
    | gVisor GPU support | [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/), [gVisor installation](https://gvisor.dev/docs/user_guide/install/), [google/gvisor](https://github.com/google/gvisor) |
    | Kata Containers 4.3.1 NVIDIA GPU passthrough | [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md), [Kata issue #11687](https://github.com/kata-containers/kata-containers/issues/11687) |
    | scripts/ops/verify.sh | [scripts/ops/verify.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/verify.sh), [scripts/lib_jobs.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib_jobs.sh), [scripts/kata/gpu_nodes.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/kata/gpu_nodes.sh) |

    All sources: [this page in All references](references.md#ref-reference-troubleshooting)
