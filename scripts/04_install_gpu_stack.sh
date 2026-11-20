#!/usr/bin/env bash
# GPU stack and the gVisor runtime, in this order:
#   1. NVIDIA device plugin (CDI mode) for container-mode GPU nodes: the EC2 trainer and gVisor
#      nodes, and the B2 HyperPod sandbox instance group. The Kata GPU node is handled by the GPU
#      Operator in scripts/kata/gpu_nodes.sh; the HyperPod trainer nodes by the HyperPod chart.
#   2. Register the gVisor RuntimeClass and prove, on one gVisor node, that:
#        a. the pod runs under gVisor (dmesg shows the gVisor Sentry, not the host kernel)
#        b. the GPU is usable through nvproxy (torch sees the GPU and runs a kernel)
# Part 2 is skipped when the CDK stack runs scenario B2 or C, which have no EC2 gVisor GPU nodes:
# B2 registers gvisor-hyperpod in scripts/hyperpod/create.sh --b2, C uses scripts/kata/cpu_nodes.sh.
source "$(dirname "$0")/lib.sh"
require_tools aws helm kubectl python3
require_vars AWS_REGION CLUSTER_NAME NVIDIA_DEVICE_PLUGIN_VERSION

# The scenario the stack was deployed with (the output cdk/deploy.sh checks too). Empty without
# the CDK stack, and then both parts run.
deployed="$(aws cloudformation describe-stacks --region "${AWS_REGION}" --stack-name "${CLUSTER_NAME}-cdk" \
  --query "Stacks[0].Outputs[?OutputKey=='Scenario'].OutputValue" --output text 2>/dev/null || true)"
with_gvisor=1
if [[ "${deployed}" == "B2" || "${deployed}" == "C" ]]; then
  with_gvisor=0
fi
if (( with_gvisor )); then
  require_vars SANDBOX_IMAGE_URI
fi

helm repo add nvdp https://nvidia.github.io/k8s-device-plugin >/dev/null
helm repo update nvdp >/dev/null
helm upgrade --install nvdp nvdp/nvidia-device-plugin \
  --version "${NVIDIA_DEVICE_PLUGIN_VERSION}" --namespace kube-system \
  -f "${REPO_ROOT}/infra/gpu/nvidia-device-plugin-values.yaml" --wait
# nvidia-container-toolkit 1.20 (EKS AL2023 NVIDIA AMI) adds a "disable-device-node-modification"
# CDI hook that reads <rootfs>/proc/driver/nvidia/params. runsc runs CDI hooks in the gofer before
# the container has a /proc, so the hook fails and every gVisor GPU pod ends in StartError
# ("reading mounts file: ... unexpected end of JSON input"). The chart has no value for the
# plugin's --cdi-disable-hooks flag, so set its env var here (re-applied after every helm upgrade).
# runc pods (the trainer) lose only this hook; they cannot create device nodes without CAP_MKNOD.
kubectl -n kube-system set env ds/nvdp-nvidia-device-plugin CDI_DISABLE_HOOKS=disable-device-node-modification
kubectl -n kube-system rollout status ds/nvdp-nvidia-device-plugin --timeout=5m

log "allocatable GPUs per node"
kubectl get nodes -l gpusandbox/device-plugin=cdi \
  -o custom-columns='NODE:.metadata.name,ROLE:.metadata.labels.gpusandbox/role,GPU:.status.allocatable.nvidia\.com/gpu'

if (( ! with_gvisor )); then
  log "scenario ${deployed} has no EC2 gVisor GPU nodes: skipping the gvisor RuntimeClass and the smoke pod"
  exit 0
fi

kubectl apply -f "${REPO_ROOT}/k8s/runtimes/runtimeclass-gvisor.yaml"
kubectl get runtimeclass gvisor

# The smoke pod needs one free GPU on a sandbox-gvisor node. When a sandbox pool (06) already
# holds them all, the pod would sit Pending for the whole 15-minute wait; stop here instead.
nodes_json="$(mktemp)" pods_json="$(mktemp)"
kubectl get nodes -l gpusandbox/role=sandbox-gvisor -o json > "${nodes_json}"
kubectl get pods -A --field-selector=status.phase!=Succeeded,status.phase!=Failed -o json > "${pods_json}"
free_gpus="$(python3 - "${nodes_json}" "${pods_json}" <<'PY'
import json, sys
nodes = {n["metadata"]["name"]: int(n["status"].get("capacity", {}).get("nvidia.com/gpu") or 1)
         for n in json.load(open(sys.argv[1]))["items"]}
used = 0
for pod in json.load(open(sys.argv[2]))["items"]:
    if pod["spec"].get("nodeName") in nodes:
        for c in pod["spec"]["containers"]:
            res = c.get("resources", {})
            used += int((res.get("limits") or res.get("requests") or {}).get("nvidia.com/gpu", 0))
print(sum(nodes.values()) - used)
PY
)"
rm -f "${nodes_json}" "${pods_json}"
if (( free_gpus <= 0 )); then
  kubectl get pods -A -o wide --field-selector=status.phase=Running | grep -E "NAME|sandbox-gvisor" || true
  die "every GPU on the sandbox-gvisor nodes is in use, so the smoke pod cannot start. Free one with
  kubectl -n sandbox scale deployment -l gpusandbox/runtime=gvisor --replicas=0
then run this script again; scripts/06_deploy_sandboxes.sh gvisor v1 brings the pool back."
fi

pod="gvisor-smoke-$RANDOM"
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: ${pod}
  namespace: default
spec:
  runtimeClassName: gvisor
  restartPolicy: Never
  automountServiceAccountToken: false
  containers:
    - name: smoke
      image: ${SANDBOX_IMAGE_URI}
      command: ["/bin/sh", "-c"]
      args:
        - |
          echo "kernel (gVisor reports its own): \$(uname -r)"
          dmesg 2>/dev/null | head -3
          python -c "import torch; x = torch.ones(1024, device='cuda'); print('cuda ok:', torch.cuda.get_device_name(0), float((x * 2).sum()))"
      resources:
        limits: {nvidia.com/gpu: "1", cpu: "2", memory: 8Gi}
EOF
# Remove the smoke pod however this script ends, so a failed check does not leave it
# holding a GPU in the default namespace.
trap 'kubectl delete pod "${pod}" --wait=false --ignore-not-found >/dev/null 2>&1 || true' EXIT
if ! kubectl wait --for=jsonpath='{.status.phase}'=Succeeded "pod/${pod}" --timeout=15m; then
  warn "smoke pod did not succeed; its state and events follow (the pod is deleted when this script exits)"
  kubectl describe pod "${pod}" | tail -n 25 || true
fi
kubectl logs "${pod}" || warn "no logs from ${pod}: the container did not start"
