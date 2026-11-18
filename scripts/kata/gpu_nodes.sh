#!/usr/bin/env bash
# Kata + GPU passthrough on g4dn.metal (8x T4).
# COST: g4dn.metal is 7.824 USD/hour on demand in us-east-1/us-west-2 (as of 2026-11).
# Scale it to zero when you are not using it:
#   aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu \
#     --scaling-config minSize=0,maxSize=1,desiredSize=0
source "$(dirname "$0")/../lib.sh"
require_tools aws helm kubectl
require_vars CLUSTER_NAME AWS_REGION KATA_GPU_INSTANCE_TYPE KATA_VERSION GPU_OPERATOR_VERSION

if [[ -z "${KATA_IOMMU_AMI_ID:-}" ]]; then
  log "baking an AL2023 AMI with intel_iommu=on (about 10 minutes)"
  "${REPO_ROOT}/infra/kata/build-iommu-ami.sh"
  die "add KATA_IOMMU_AMI_ID and WITH_KATA_GPU=1 to scripts/config.env, run scripts/02_create_cluster.sh again, then re-run this script"
fi
# The g4dn.metal node group comes from the CDK stack (WITH_KATA_GPU=1 with KATA_IOMMU_AMI_ID).
aws eks describe-nodegroup --region "${AWS_REGION}" --cluster-name "${CLUSTER_NAME}" \
  --nodegroup-name sandbox-kata-gpu >/dev/null 2>&1 \
  || die "no sandbox-kata-gpu node group: set WITH_KATA_GPU=1 in scripts/config.env and run scripts/02_create_cluster.sh again (it starts ${KATA_GPU_INSTANCE_TYPE}, about 7.8 USD/hour)"

log "installing the NVIDIA GPU Operator ${GPU_OPERATOR_VERSION} in VM-passthrough mode"
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia >/dev/null
helm repo update nvidia >/dev/null
helm upgrade --install gpu-operator nvidia/gpu-operator --version "${GPU_OPERATOR_VERSION}" \
  --namespace gpu-operator --create-namespace \
  -f "${REPO_ROOT}/infra/kata/gpu-operator-values.yaml" --wait --timeout 20m

log "installing or upgrading kata-deploy ${KATA_VERSION}"
extra=()
if [[ "${ENABLE_EXPERIMENTAL_CLH_GPU:-0}" == "1" ]]; then
  warn "enabling the experimental kata-clh-nvidia-gpu runtime class"
  extra=(-f "${REPO_ROOT}/infra/kata/experimental-clh-gpu/values-clh-gpu.yaml")
fi
helm upgrade --install kata-deploy oci://ghcr.io/kata-containers/kata-deploy-charts/kata-deploy \
  --version "${KATA_VERSION}" --namespace kube-system \
  -f "${REPO_ROOT}/infra/kata/kata-deploy-values.yaml" "${extra[@]}" --wait --timeout 20m

node="$(kubectl get nodes -l gpusandbox/kata-gpu=true -o jsonpath='{.items[0].metadata.name}')"
log "waiting for the T4s to be advertised as nvidia.com/pgpu on ${node}"
for _ in $(seq 1 60); do
  pgpu="$(kubectl get node "${node}" -o jsonpath='{.status.allocatable.nvidia\.com/pgpu}')"
  [[ -n "${pgpu}" && "${pgpu}" != "0" ]] && break
  sleep 20
done
kubectl get node "${node}" -o jsonpath='{"pgpu="}{.status.allocatable.nvidia\.com/pgpu}{"  cc.ready.state="}{.metadata.labels.nvidia\.com/cc\.ready\.state}{"\n"}'
[[ -n "${pgpu:-}" && "${pgpu}" != "0" ]] || die "no passthrough GPUs advertised; see docs/reference/troubleshooting.md"
kubectl get runtimeclass kata-qemu-nvidia-gpu
