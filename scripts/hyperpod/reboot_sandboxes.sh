#!/usr/bin/env bash
# Stage and activate the driver on registered managed B2 sandbox workers, before deploying the pool.
source "$(dirname "$0")/../lib.sh"
require_tools aws kubectl jq
require_vars AWS_REGION HYPERPOD_CLUSTER_NAME HYPERPOD_SANDBOX_COUNT B2_NVIDIA_DRIVER_VERSION
selector="sagemaker.amazonaws.com/cluster-name=${HYPERPOD_CLUSTER_NAME},sagemaker.amazonaws.com/instance-group-name=sandbox,gpusandbox/role=sandbox-hyperpod"
nodes="$(kubectl get nodes -l "${selector}" -o json)"
if ! jq -e --argjson n "${HYPERPOD_SANDBOX_COUNT}" \
  '(.items|length) == $n and all(.items[]; any(.status.conditions[]; .type=="Ready" and .status=="True"))' \
  <<<"${nodes}" >/dev/null; then
  kubectl get nodes -l "${selector}"
  die "wait for ${HYPERPOD_SANDBOX_COUNT} Ready sandbox workers, then rerun"
fi
namespace="$(kubectl create -f - -o jsonpath='{.metadata.name}' <<'YAML'
apiVersion: v1
kind: Namespace
metadata:
  generateName: b2-driver-check-
  labels:
    pod-security.kubernetes.io/enforce: privileged
YAML
)"
trap 'kubectl delete namespace "${namespace}" --wait=false >/dev/null' EXIT

driver_versions() {
  local node="$1" mode="${2:-check}" pod phase
  kubectl -n "${namespace}" debug "node/${node}" --attach=false --profile=sysadmin \
    --image=public.ecr.aws/amazonlinux/amazonlinux:2023 -- chroot /host /bin/bash -ec \
    'disk=$(modinfo -F version nvidia 2>/dev/null || true)
     if [[ "$2" == prepare && ( "$disk" != "$1" || -e /var/lib/gpusandbox/driver-install.pending || ! -f /etc/systemd/system/containerd.service.d/30-gpusandbox-runsc.conf ) ]]; then
       systemd-run --quiet --wait --collect --unit=gpusandbox-b2-prepare \
         /bin/bash /usr/local/libexec/gpusandbox/managed-b2/prepare-sandbox-worker.sh ||
         { journalctl -u gpusandbox-b2-prepare -n 35 --no-pager >&2; exit 1; }
     fi
     cat /sys/module/nvidia/version; modinfo -F version nvidia' \
    bash "${B2_NVIDIA_DRIVER_VERSION}" "${mode}" >/dev/null || return 1
  pod="$(kubectl -n "${namespace}" get pods --field-selector "spec.nodeName=${node}" -o name)"
  for _ in {1..240}; do
    phase="$(kubectl -n "${namespace}" get "${pod}" -o jsonpath='{.status.phase}')"
    case "${phase}" in Succeeded|Failed) break ;; esac
    sleep 5
  done
  if [[ "${phase}" != Succeeded ]]; then kubectl -n "${namespace}" logs "${pod}" >&2; return 1; fi
  kubectl -n "${namespace}" logs "${pod}" | paste -sd ' ' -
  kubectl -n "${namespace}" delete "${pod}" --wait=true >/dev/null
}

ids=()
declare -A boots=()
work="$(mktemp -d)"
trap 'rm -rf "${work}"; kubectl delete namespace "${namespace}" --wait=false >/dev/null' EXIT
pids=()
busy_nodes="$(kubectl get pods -A --field-selector 'metadata.namespace=sandbox,status.phase=Running' \
  -o json | jq -r '.items[].spec.nodeName')"
while read -r node; do
  mode=prepare
  if grep -Fx -- "${node}" <<<"${busy_nodes}" >/dev/null; then
    mode=check
  fi
  driver_versions "${node}" "${mode}" > "${work}/${node}" &
  pids+=("$!")
done < <(jq -r '.items[].metadata.name' <<<"${nodes}")
for pid in "${pids[@]}"; do wait "${pid}" || die "failed to prepare a HyperPod sandbox worker"; done
while read -r node provider boot; do
  versions="$(< "${work}/${node}")"
  read -r running installed <<<"${versions}"
  log "${node}: running ${running}, on disk ${installed}"
  [[ "${installed}" == "${B2_NVIDIA_DRIVER_VERSION}" ]] || die "check the preparation log and running sandbox pods on ${node}"
  [[ "${running}" != "${installed}" ]] || continue
  if kubectl get pods -A --field-selector "metadata.namespace=sandbox,spec.nodeName=${node},status.phase=Running" \
    -o name | grep . >/dev/null; then
    die "finish grading and drain the sandbox workloads on ${node} before rebooting it"
  fi
  [[ "${provider}" =~ (i-[0-9a-f]+)$ ]] || die "no HyperPod instance ID in ${provider}"
  ids+=("${BASH_REMATCH[1]}")
  boots["${node}"]="${boot}"
done < <(jq -r '.items[] | [.metadata.name,.spec.providerID,.status.nodeInfo.bootID] | @tsv' <<<"${nodes}")
((${#ids[@]})) || { log "the sandbox workers already run the target driver"; exit 0; }
result="$(aws sagemaker batch-reboot-cluster-nodes --region "${AWS_REGION}" --cluster-name "${HYPERPOD_CLUSTER_NAME}" \
  --node-ids "${ids[@]}" --output json)"
echo "${result}"
jq -e --argjson n "${#ids[@]}" '(.Successful|length) == $n' <<<"${result}" >/dev/null || die "HyperPod did not accept every reboot"

for node in "${!boots[@]}"; do
  for _ in {1..120}; do
    current="$(kubectl get node "${node}" --ignore-not-found -o json | jq -r \
      'select(any(.status.conditions[]; .type=="Ready" and .status=="True")) | .status.nodeInfo.bootID')"
    [[ -n "${current}" && "${current}" != "${boots[${node}]}" ]] && break
    sleep 10
  done
  [[ -n "${current}" && "${current}" != "${boots[${node}]}" ]] || die "did not see a new Ready boot for ${node}"
  versions="$(driver_versions "${node}")"
  [[ "${versions}" == "${B2_NVIDIA_DRIVER_VERSION} ${B2_NVIDIA_DRIVER_VERSION}" ]] || die "${node}: unexpected drivers ${versions}"
  log "${node}: NVIDIA ${B2_NVIDIA_DRIVER_VERSION} active after the HyperPod reboot"
done
