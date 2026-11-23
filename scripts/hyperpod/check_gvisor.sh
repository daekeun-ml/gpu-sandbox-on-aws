#!/usr/bin/env bash
# Mode B2 preflight: can gVisor sandboxes run on the HyperPod nodes themselves?
# Compare the NVIDIA drivers on the HyperPod GPU nodes with the pinned gVisor release.
# The CPU system group does not need an NVIDIA driver. Debug pods run in a temporary namespace.
source "$(dirname "$0")/../lib.sh"
require_tools kubectl
require_vars GVISOR_RELEASE

nodes="$(kubectl get nodes -l 'sagemaker.amazonaws.com/node-health-status,gpusandbox/role!=system' -o jsonpath='{.items[*].metadata.name}')"
[[ -n "${nodes}" ]] || die "no HyperPod worker nodes found outside the CPU system group"
namespace="$(kubectl create -f - -o jsonpath='{.metadata.name}' <<'YAML'
apiVersion: v1
kind: Namespace
metadata:
  generateName: gpusandbox-gvisor-check-
  labels:
    pod-security.kubernetes.io/enforce: privileged
YAML
)"
trap 'kubectl delete namespace "${namespace}" --wait=false >/dev/null' EXIT
for node in ${nodes}; do
  log "${node}"
  kubectl -n "${namespace}" debug "node/${node}" --attach=false --profile=sysadmin --image=public.ecr.aws/amazonlinux/amazonlinux:2023 -- \
    bash -c "
      set -euo pipefail
      driver=\$(chroot /host nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
      if chroot /host /usr/local/bin/runsc --version 2>/dev/null | grep -Fx 'runsc version release-${GVISOR_RELEASE}' >/dev/null; then
        supported=\$(chroot /host /usr/local/bin/runsc nvproxy list-supported-drivers)
      else
        dnf install -y -q bzip2 tar >/dev/null
        cd /tmp
        url=https://storage.googleapis.com/gvisor/releases/release/${GVISOR_RELEASE}/\$(uname -m)
        curl -fsSLO \$url/gvisor.tar.bz2 && curl -fsSLO \$url/gvisor.tar.bz2.sha512
        sha512sum -c gvisor.tar.bz2.sha512 >/dev/null && tar -xjf gvisor.tar.bz2
        supported=\$(./runsc nvproxy list-supported-drivers)
      fi
      if grep -wF -- \"\$driver\" <<<\"\$supported\" >/dev/null; then
        echo \"  driver \$driver: SUPPORTED by gVisor ${GVISOR_RELEASE}\"
      else
        echo \"  driver \$driver: NOT supported by gVisor ${GVISOR_RELEASE}\"
      fi" >/dev/null
  pod="$(kubectl -n "${namespace}" get pods --field-selector "spec.nodeName=${node}" -o name)"
  if ! kubectl -n "${namespace}" wait --for=jsonpath='{.status.phase}'=Succeeded "${pod}" --timeout=5m >/dev/null; then
    kubectl -n "${namespace}" logs "${pod}" >&2
    die "could not inspect ${node}"
  fi
  kubectl -n "${namespace}" logs "${pod}"
done
