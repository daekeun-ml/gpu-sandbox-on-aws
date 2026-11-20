# 02 gVisor GPU sandboxes

!!! info "TL;DR"
    Install the NVIDIA device plugin in CDI mode, register the `gvisor` RuntimeClass, and confirm with one smoke pod that CUDA runs on the A10G under the gVisor kernel.

## Pain point

gVisor's own kernel (the Sentry) receives the container's system calls. The `nvidia-container-runtime` hook that attaches GPUs under runc therefore does not apply, and the devices need a path of their own. nvproxy also accepts only driver versions it knows, so an AMI change that brings a different driver can keep sandboxes from starting at all.

![a: on a runc node the nvidia-container-runtime hook injects the GPU, but on a gVisor node the Sentry receives syscalls, the same hook does not apply and the sandbox container has no path for the devices; an AMI change to a driver version nvproxy does not know keeps the sandbox from starting. b: the same device plugin (cdi-cri) hands CDI devices to both the runc trainer node and the gVisor node, where runsc turns on nvproxy, and the g5 (A10G) node's proprietary driver 580.178.04 (GSP off) is a version on the gVisor support list, so the sandbox starts and a mismatch is never Ready (fail closed)](../images/figures/handson-02_gvisor.svg)

*Takeaway: The way runc attaches GPUs does not work under gVisor, and a driver version change can make nvproxy block the sandbox from starting. With devices handed over through CDI and only a driver on the support list, the sandbox container gets its GPU and a mismatch fails closed.*


## Why

- **Use the CDI path gVisor documents.** The trainer nodes, running runc, use the same device plugin.
- **Driver mismatches do not pass silently.** Nodes warn at boot, and a pod whose GPU probe fails never turns Ready (fail closed).
- **Use only a driver on the support list.** The default is `g5` (A10G) with driver 580.178.04. The gVisor documentation does not cover this combination; this repository verified it in a practice account. `runsc.toml` opens only the `compute,utility` capabilities.

**Before you start:** finish [01 Cluster and images](01_cluster_and_images.md) so that the two gVisor nodes and `SANDBOX_IMAGE_URI` are ready, and run kubectl and helm in a second terminal with `cdk/tunnel.sh` running. The concepts are in [02 Isolation runtimes](../concepts/02_isolation_runtimes.md).

??? note "Terms (expand if a word is new to you)"
    - **gVisor Sentry**: a kernel running in user space that receives the container's syscalls instead of the host kernel.
    - **runsc**: gVisor's runtime binary. containerd calls it through a shim (`containerd-shim-runsc-v1`).
    - **nvproxy**: the gVisor feature that forwards to the host NVIDIA driver only the GPU ioctls on the allowlist for that driver version.
    - **ioctl**: the syscall a program uses to send commands to a device driver.
    - **Device plugin**: the component that advertises a node's GPUs as the `nvidia.com/gpu` resource and attaches devices to pods.
    - **CDI, `cdi-cri`**: CDI is a standard that describes the devices to put into a container by name; `cdi-cri` is the mode in which the device plugin passes those names to containerd through a CRI field.
    - **OCI spec**: the container execution specification (JSON) handed to the runtime. The device list goes into it too.
    - **Helm, DaemonSet**: Helm is the Kubernetes package manager; a DaemonSet runs one pod on every matching node.
    - **systrap**: the default way (platform) the Sentry intercepts syscalls. It works on regular VMs without `/dev/kvm`.
    - **GSP, open kernel module, proprietary kernel module**: GSP is a co-processor in recent NVIDIA GPUs; the open kernel module is the NVIDIA driver kernel module whose source NVIDIA publishes. The proprietary kernel module is the older kernel module whose source is not published.
    - **CDI hook**: a helper command listed in the CDI specification that the runtime runs while creating the container.

!!! warning "AWS steps on this page"
    `04_install_gpu_stack.sh` was run in the practice account (`g5.xlarge`, [run record](../reference/sources.md#aws-run-record)). The smoke pod's `cuda ok: NVIDIA A10G 2048.0` line and the GPU count briefly showing `0` were seen in that run; the rest of the output is an example of the shape. Compare the "What to look for" items below with your actual output.

## Install the GPU stack and gVisor: `04_install_gpu_stack.sh`

One script installs the device plugin and prints the GPU count per node, then registers the `gvisor` RuntimeClass and runs one smoke pod on a gVisor node.

```bash
scripts/04_install_gpu_stack.sh
```

If the stack runs scenario B2 or C, there are no EC2 gVisor GPU nodes, so the script installs only the device plugin and ends with `scenario <B2 or C> has no EC2 gVisor GPU nodes: skipping the gvisor RuntimeClass and the smoke pod`.

## NVIDIA device plugin (CDI mode)

The script first adds the `nvdp` Helm repository, installs `nvdp/nvidia-device-plugin` with `--version "${NVIDIA_DEVICE_PLUGIN_VERSION}"` (default 0.20.1) into `kube-system`, and waits for the DaemonSet with `--wait`. It then sets the plugin's `--cdi-disable-hooks` flag with the command below and waits for the rollout (the script runs it; you do not). Chart v0.20.1 does not expose this flag as a value, so it goes in as an environment variable.

```bash
kubectl -n kube-system set env ds/nvdp-nvidia-device-plugin CDI_DISABLE_HOOKS=disable-device-node-modification
```

??? note "Why the CDI hook is turned off"
    - nvidia-container-toolkit 1.20.1 on the AMI adds a `disable-device-node-modification` CDI hook, which reads `<rootfs>/proc/driver/nvidia/params`.
    - runsc runs CDI hooks in the gofer, before the container has a `/proc`, so the hook fails.
    - As a result every gVisor GPU pod ends in `StartError` with `OCI runtime start failed: starting container: reading mounts file: error unmarshaling mounts: unexpected end of JSON input`. The runsc debug log shows `error opening nvidia driver params file: openat proc/driver/nvidia/params: no such file or directory`.
    - The problem does not depend on the GPU model, so `g6` is affected too. A gVisor pod without a GPU on the same node ran fine.
    - runc pods (the trainer) lose only this hook. Without `CAP_MKNOD` they cannot create device nodes anyway.

**What to look for:** GPU 1 on every node (example shape; scenario B has no trainer line). Right after the plugin restarts, the gVisor node can briefly show `0`. The smoke pod requests one GPU and is placed once a node has its GPU registered again, so judge success by the final `cuda ok:` log.

```text
daemonset.apps/nvdp-nvidia-device-plugin env updated
daemon set "nvdp-nvidia-device-plugin" successfully rolled out
[hh:mm:ss] allocatable GPUs per node
NODE                                         ROLE             GPU
ip-192-168-x-x.us-west-2.compute.internal    trainer          1
ip-192-168-x-x.us-west-2.compute.internal    sandbox-gvisor   1
ip-192-168-x-x.us-west-2.compute.internal    sandbox-gvisor   1
```

**If it fails:** an empty or `<none>` GPU column means `nvidia.com/gpu` is not registered in that node's `status.allocatable`. Check in `kube-system` whether a device plugin pod was placed on that node and read its logs; the "gVisor" section of [Troubleshooting](../reference/troubleshooting.md) has the commands.

The settings in `infra/gpu/nvidia-device-plugin-values.yaml`:

| Setting | Value | Reason |
|---|---|---|
| `deviceListStrategy` | `cdi-cri` | passes CDI devices through the CRI `CDIDevices` field, the injection path gVisor documents |
| `nvidiaDriverRoot` | `/` | the EKS AL2023 NVIDIA AMI installs the driver at the host root |
| `nodeSelector` | `gpusandbox/device-plugin: cdi` | installs only on the EC2 trainer and gVisor nodes and the B2 HyperPod sandbox nodes |
| `affinity` | `{}` | the chart's default affinity requires NFD labels, so it is cleared |
| `tolerations` | `nvidia.com/gpu`, `gpusandbox/role` (Exists) | so the plugin also runs on nodes with the dedicated taints |

!!! note "Where the device plugin runs"
    This plugin runs only on nodes labelled `gpusandbox/device-plugin=cdi`: the EC2 trainer and gVisor nodes, and the B2 HyperPod sandbox instance group (`sandbox`). The Kata GPU node uses the GPU Operator's sandbox device plugin (`nvidia.com/pgpu`, [03 Kata sandboxes](03_kata.md)), and the HyperPod trainer nodes the plugin in the HyperPod Helm chart ([07 HyperPod scenario](07_hyperpod.md)).

### Why CDI

```mermaid
flowchart LR
    DP["device plugin<br/>deviceListStrategy cdi-cri"] -->|"CDI device names"| CT["containerd 2.3.7<br/>edits the OCI spec"]
    TK["nvidia-container-toolkit 1.20.1<br/>(host, required)"] -.-> CT
    CT -->|"spec with /dev/nvidia*"| RS["runsc"]
    RS -->|"detects NVIDIA devices, enables nvproxy"| S["sandbox container"]
```

*Takeaway: runsc turns on nvproxy from the NVIDIA devices in the OCI spec alone, without a prestart hook, so the device plugin only has to hand the devices over through CDI.*

Per the gVisor documentation, runsc is fully CDI-compatible and configures the devices itself (skipping `nvidia-container-runtime-hook`), so no `nvidia-container-runtime` shim is needed, but the host still needs nvidia-container-toolkit. The EKS AL2023 NVIDIA AMI (v20261107) has the driver, nvidia-container-toolkit 1.20.1 and containerd 2.3.7 but no device plugin, and nodeadm enables CDI for kubelet 1.32 and later.

## RuntimeClass and smoke pod

Once the device plugin is installed, the same script registers the RuntimeClass and runs one smoke pod on a gVisor node. There is no separate command to run for this part.

The script first applies `k8s/runtimes/runtimeclass-gvisor.yaml`.

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
scheduling:
  nodeSelector:
    gpusandbox/role: sandbox-gvisor
  tolerations:
    - key: gpusandbox/role
      operator: Equal
      value: sandbox-gvisor
      effect: NoSchedule
```

`handler: runsc` must equal the `runtimes.runsc` key of the NodeConfig in [01 Cluster and images](01_cluster_and_images.md). `scheduling` merges into the pod at admission (nodeSelectors intersect, tolerations are added), so a pod that only sets `runtimeClassName: gvisor` still lands on a gVisor node.

Next it starts one smoke pod in the `default` namespace (the sandbox image `SANDBOX_IMAGE_URI`, `nvidia.com/gpu: 1`, 2 CPUs, 8Gi of memory) that prints the three things below, waits up to 15 minutes for `Succeeded` (including the first pull of the large image) and shows the logs. An EXIT trap deletes the pod when the script ends, whether it succeeded or failed, and the delete output is not shown.

1. `uname -r`: the kernel version the Sentry reports (not the node's kernel)
2. `dmesg | head -3`: boot messages generated by gVisor (not the host kernel log)
3. the sum of `torch.ones(1024, device='cuda')` times 2 (2048), and the GPU name: evidence that a CUDA kernel ran through nvproxy

**What to look for:** output of this shape (example; the number in the pod name changes every time).

```text
runtimeclass.node.k8s.io/gvisor created
NAME     HANDLER   AGE
gvisor   runsc     0s
pod/gvisor-smoke-12345 created
pod/gvisor-smoke-12345 condition met
kernel (gVisor reports its own): 4.19.0-gvisor
[    0.000000] Starting gVisor...
[    0.xxxxxx] <a random boot message chosen by gVisor>
[    0.xxxxxx] <a random boot message chosen by gVisor>
cuda ok: NVIDIA A10G 2048.0
```

![End of the 04_install_gpu_stack.sh output: GPUs per node (one briefly 0 right after the device plugin restart), the gvisor RuntimeClass, the smoke pod's kernel 4.19.0-gvisor, Starting gVisor..., and the last line cuda ok: NVIDIA A10G 2048.0](../images/terminal/gpu-stack-a.png)

- The kernel string is the default `4.19.0-gvisor` in the gVisor source (`version.go`). If it differs from the node's kernel (`kubectl get node <node> -o jsonpath='{.status.nodeInfo.kernelVersion}'`), the pod is not using the host kernel directly. The RuntimeClass `gvisor` and the dmesg line `Starting gVisor...` below show that it is gVisor.
- The first dmesg line is `Starting gVisor...`; gVisor picks the following lines at random.

**If it fails:** if the `cuda ok:` line is missing or you see `smoke pod did not succeed`, read "nvproxy driver version matching" below first, then the "gVisor" section of [Troubleshooting](../reference/troubleshooting.md) (which also covers a pod stuck in `ContainerCreating`). If the pod ends in `StartError` with `reading mounts file: error unmarshaling mounts: unexpected end of JSON input`, the CDI hook setting above is missing; check it with `kubectl -n kube-system get ds nvdp-nvidia-device-plugin -o yaml | grep -A1 CDI_DISABLE_HOOKS`.

## nvproxy driver version matching

nvproxy works only when the driver version matches exactly, and gVisor sorts drivers into three classes.

| Class | Meaning | runsc behavior |
|---|---|---|
| supported | versions gVisor has verified | runs normally |
| unsupported | defined in the source but not verified | fails to start by default; with `--nvproxy-allow-unsupported-driver` it logs a warning and tries to run |
| unknown | not defined in the source | always fails to start, even with the flag |

This hands-on's combinations:

| Driver | Where it comes from | gVisor release-20261109.0 | Result |
|---|---|---|---|
| 580.178.04 | default driver of the EKS AL2023 NVIDIA AMI v20261107; loaded as the proprietary module (GSP off) on `g5` and as the open module on `g6` | supported (since release-20260831.0) | works |
| 595.91.07 | in the same AMI but for `g7` only; the driver of the HyperPod EKS AMI | unknown | container fails to start |

Reward sandboxes run untrusted code, so this repository sticks to supported combinations instead of `--nvproxy-allow-unsupported-driver`.

### Symptoms of an unsupported driver

1. **Node boot:** `install-gvisor.sh` leaves `WARNING: NVIDIA driver <version> is not supported by gVisor <release> nvproxy` in the user data log.
2. **The `04_install_gpu_stack.sh` smoke pod:** runsc refuses to start the container, so the script warns `smoke pod did not succeed; its state and events follow (the pod is deleted when this script exits)` and prints the last 25 lines of `kubectl describe pod`, whose events carry the runsc error. If the container never started, it also warns `no logs from gvisor-smoke-<n>: the container did not start`. The pod is deleted when the script ends, so there is nothing to clean up by hand.
3. **Pool deployment (`06_deploy_sandboxes.sh`):** sandbox pods never turn Ready (fail closed, as with a CUDA initialization failure for any other reason), and the deployment fails. The script waits up to 30 minutes in `rollout status`. The Deployment's progress deadline (`progressDeadlineSeconds`) is also 1800 seconds, the same as this wait. The headless Service publishes only Ready pod IPs, so the trainer never gets such a pod.

The fix is to raise `GVISOR_RELEASE` to a gVisor release that supports the driver, or to use an AMI with a supported driver. Either way, before the switch run `runsc nvproxy list-supported-drivers` from the release you are adopting (the `https://storage.googleapis.com/gvisor/releases/release/<release>/x86_64/gvisor.tar.bz2` that `install-gvisor.sh` downloads) and compare it with the driver version of the new AMI. The method below checks the combination installed on a node that has already booted.

### Checking on the node itself

Find a gVisor node name and open a debug pod shell on it (`<gvisor-node>` is a name printed by the first command).

```bash
kubectl get nodes -l gpusandbox/role=sandbox-gvisor
kubectl debug node/<gvisor-node> -it --profile=sysadmin --image=public.ecr.aws/amazonlinux/amazonlinux:2023
```

**What to look for:** a shell prompt after the second command. The node's root file system is mounted at `/host`.

Run the following in the debug shell.

```bash
cat /proc/driver/nvidia/version                         # loaded kernel module version
/host/usr/local/bin/runsc --version                      # installed gVisor release
/host/usr/local/bin/runsc nvproxy list-supported-drivers | grep -Fw 580.178.04   # use the version from the first line
```

**What to look for:** the first prints a module version line containing `580.178.04` (`NVIDIA UNIX x86_64 Kernel Module  580.178.04` for the proprietary module on `g5`). The second prints a version line containing `release-20261109.0`. If the first shows a different version, put that version in place of `580.178.04` in the third. If the third prints the version, the combination is supported; if it prints nothing, it is not.

Debug pods are not deleted automatically, so find and delete it after leaving the shell.

```bash
kubectl get pods -n default -o name | grep node-debugger
kubectl delete -n default pod/<name>
```

**What to look for:** the first command shows a `pod/node-debugger-...` name, and the second prints `pod "node-debugger-..." deleted`.

## runsc.toml settings

The `/etc/containerd/runsc.toml` written by `install-gvisor.sh`:

```toml
# Read by containerd-shim-runsc-v1 through the runtime's ConfigPath option.
[runsc_config]
  # GPU support turns on automatically when NVIDIA devices are in the OCI spec; being explicit
  # documents intent and is harmless.
  nvproxy = "true"
  # compute,utility is the default. Do not add profiling, rdma or graphics for reward sandboxes.
  nvproxy-allowed-driver-capabilities = "compute,utility"
```

- runsc flags are set in this file, the one the NodeConfig `ConfigPath` points to, not in the RuntimeClass or the pod spec.
- `compute,utility` (the default) allows only CUDA compute (compute) and management interfaces such as nvidia-smi and NVML (utility). The gVisor documentation warns that each additional capability widens the host driver surface exposed to the sandbox, and running and timing kernels needs only these two.
- `g5.xlarge` is a virtual instance, so gVisor runs on systrap; the KVM platform is for bare metal only.

## Driver and verification scope of g5 nodes

The EKS AL2023 NVIDIA AMI (v20261107) loads the proprietary kernel module with GSP off on `g4dn`, `g5` and `g5g`, and the open kernel module 580.178.04 on `g6`. On a `g5.xlarge` node deployed on 2026-11-18, `/proc/driver/nvidia/version` showed `NVIDIA UNIX x86_64 Kernel Module  580.178.04` and `/proc/driver/nvidia/params` showed `EnableGpuFirmware: 0`.

The gVisor documentation describes nvproxy against NVIDIA's open driver and does not mention the proprietary driver. Regardless of the driver flavor, 580.178.04 is in the supported list of runsc `release-20261109.0` (`runsc nvproxy list-supported-drivers`).

| Instance | GPU | Kernel module loaded (AMI v20261107) | Driver flavor in the gVisor documentation | This repository | On-Demand (USD/hour) |
|---|---|---|---|---|---|
| `g5.xlarge` (default) | 1x A10G | proprietary 580.178.04, GSP off | not covered | verified in the practice account (2026-11-18) | 1.006 |
| `g6.xlarge` (alternative) | 1x L4 | open 580.178.04 | covered | not run | 0.8048 |
| `g4dn.xlarge` | 1x T4 | proprietary, GSP off | not covered | not tested (unverified) | 0.526 |

Prices are us-east-1 and us-west-2 list prices.

**What this repository verified** (2026-11-18, us-west-2, practice account, `g5.xlarge` with the proprietary, GSP-off module):

- The gVisor smoke test printed `cuda ok: NVIDIA A10G 2048.0`.
- `ops/verify.sh gvisor v1` passed: 6 golden verdicts PASS (including `vector_add_triton` and `relu_bias_triton`), 4 egress targets blocked, and the NetworkPolicy blocked connections from the `default` namespace.
- A 5-step GRPO run with the trainer on `g5.2xlarge` finished.

This combination was verified by this repository in a practice account, so after changing the instance type, driver, AMI or gVisor version, re-run the `04_install_gpu_stack.sh` smoke test and `scripts/ops/verify.sh`. If the default pool (`sandbox-gvisor-v1`, 2 replicas) holds the GPUs of both nodes, the smoke pod gets no GPU and stays `Pending`. The script waits 15 minutes and prints a warning, then the `kubectl logs` that follows fails and the script ends without deleting the pod. So before re-checking, free one GPU with `kubectl -n sandbox scale deployment/sandbox-gvisor-v1 --replicas=1`. If a timeout already happened, find the leftover `gvisor-smoke-<n>` pod with `kubectl get pods -n default`, delete it with `kubectl delete pod gvisor-smoke-<n>`, and run the smoke test. Once you see `cuda ok:`, scale back to 2 and run `verify.sh`.

`g6` is a supported alternative. It loads the open driver, which the gVisor documentation covers, and it costs less (`g6.xlarge` 0.8048, `g6.2xlarge` 0.9776). To use it, change `GVISOR_INSTANCE_TYPE` and `TRAINER_INSTANCE_TYPE` (`HYPERPOD_*` for HyperPod) in `scripts/config.env`.

!!! question "❓ Misconception: gVisor does not support T4"
    The GPU list in the gVisor documentation includes T4, A100/A10G, L4 and H100, and says other GPUs of the same architectures will likely work. T4 (`g4dn`) has the same driver condition as `g5` (proprietary, GSP off), so the driver flavor is not a reason to exclude it. It has not been tested under gVisor in this repository, though, so it stays unverified. T4 is the Kata QEMU GPU on `g4dn.metal`.

!!! question "❓ Misconception: the gVisor sandbox image needs the NVIDIA driver"
    The kernel driver lives on the host and the container uses it through nvproxy, so the image only needs the CUDA user-space libraries (included in the PyTorch wheel). The GPU is the host's real A10G, not a virtual GPU.

## Isolation strength and operating rules

Despite the nvproxy ioctl allowlist, the gVisor documentation states that it is much less effective at mitigating vulnerabilities within the NVIDIA driver itself. Things like DMA buffers are not validated. So this setup treats the gVisor + GPU boundary as weaker than a VM boundary (Kata).

- **Do not share GPUs.** The GKE Sandbox documentation also advises against GPU time-sharing in sandbox pods, and this repository runs one A10G per node, one sandbox pod per GPU and one evaluation per pod at a time (503 when busy).
- **Open the minimum driver capabilities.** The `compute,utility` setting above.
- **Consider Kata when you need a stronger boundary.** See GPU passthrough in [03 Kata sandboxes](03_kata.md) or [02 Isolation runtimes](../concepts/02_isolation_runtimes.md).

!!! note "EKS isolated pods (Nitro Sandboxes)"
    EKS isolated pods, launched on 2026-11-09 (`runtimeClassName: isolated-sandbox` and others, Kubernetes 1.36+), do not support GPU or device passthrough at launch, so treat them as a CPU-only managed alternative.

## Scope and limits

- On AWS only `g5` (A10G, the proprietary GSP-off module the gVisor documentation does not cover) has been run. The smoke test, `ops/verify.sh` and the 5-step training used `g5.xlarge` sandboxes; the benchmark on another cluster (`ops/bench.sh`, [08](08_benchmark.md)) used a gVisor pool on `g5.2xlarge`. `g6` and T4 have not been run with gVisor.
- The kernel string and dmesg lines can change between gVisor releases, so the test is not the value but whether the kernel differs from the node's and the first dmesg line is `Starting gVisor...`.

## Time and cost

| Step | Expected duration | Newly billed resources |
|---|---|---|
| `04_install_gpu_stack.sh`: device plugin | Helm `--wait` (until the DaemonSet is ready), then the rollout wait after the CDI hook setting | none |
| `04_install_gpu_stack.sh`: RuntimeClass and smoke pod | smoke pod timeout 15 min (including the first image pull) | none |

The two gVisor nodes have been billing since `02_create_cluster.sh` at about 2.01 USD per hour (2 x 1.006, On-Demand list price), so scale them to zero if there is a gap before the next step.

```bash
source scripts/config.env
aws eks update-nodegroup-config --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name sandbox-gvisor --scaling-config minSize=0,maxSize=4,desiredSize=0
```

**What to look for:** the command returns JSON with `"type": "ConfigUpdate"`. After a few minutes, `kubectl get nodes -l gpusandbox/role=sandbox-gvisor` (needs the tunnel) lists no nodes. When you continue, run it with `desiredSize=2` (why this value lives outside the stack: "Time and cost" in [01 Cluster and images](01_cluster_and_images.md)). When you finish the hands-on, run [99 Cleanup](99_cleanup.md).

## Next step

To compare with Kata, continue with [03 Kata sandboxes (CLH, QEMU)](03_kata.md); for the gVisor-only minimal path, go to [04 Deploy and verify sandbox pools](04_sandbox_pools.md).

??? note "References"
    | Topic | Link |
    |---|---|
    | Accelerated computing instance types (g5, g6, g4dn) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
    | gVisor GPU support (nvproxy, driver policy, CDI) | https://gvisor.dev/docs/user_guide/gpu/ |
    | Kubernetes RuntimeClass | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
    | NVIDIA k8s-device-plugin | https://github.com/NVIDIA/k8s-device-plugin |
    | GPU stack and gVisor install script (04_install_gpu_stack.sh) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/04_install_gpu_stack.sh |

    All sources: [this page in All references](../reference/references.md#ref-handson-02-gvisor)
