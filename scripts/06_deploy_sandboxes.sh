#!/usr/bin/env bash
# Deploy one sandbox pool: scripts/06_deploy_sandboxes.sh <runtime> [version] [replicas]
#   runtime: gvisor | gvisor-hyperpod (B2) | kata-qemu | kata-clh (experimental GPU) | gvisor-cpu |
#            kata-clh-cpu | kata-qemu-cpu
#   version: v1 (default) | v2
source "$(dirname "$0")/lib.sh"
require_tools kubectl
require_vars SANDBOX_IMAGE_URI SANDBOX_AUDIENCE

runtime="${1:?usage: $0 <runtime> [version] [replicas]}"
version="${2:-v1}"
profile="${REPO_ROOT}/k8s/sandbox/profiles/${runtime}.env"
version_file="${REPO_ROOT}/k8s/sandbox/versions/${version}.env"
[[ -f "${profile}" ]] || die "unknown runtime profile ${runtime}"
[[ -f "${version_file}" ]] || die "unknown version ${version}"
# shellcheck disable=SC1090
source "${profile}"
# shellcheck disable=SC1090
source "${version_file}"
[[ -n "${3:-}" ]] && REPLICAS="$3"

OIDC_ISSUER="$(oidc_issuer)"
# The trainer and the verification jobs may call the sandbox API; nothing else.
SANDBOX_ALLOWED_SUBJECTS="${SANDBOX_ALLOWED_SUBJECTS:-system:serviceaccount:rl-trainer:grpo-trainer,system:serviceaccount:rl-trainer:sandbox-probe,system:serviceaccount:sandbox-gateway:gateway}"
export OIDC_ISSUER SANDBOX_ALLOWED_SUBJECTS

log "deploying sandbox-${RUNTIME}-${VERSION}: ${REPLICAS} replica(s), runtimeClass ${RUNTIME_CLASS}"
render k8s/sandbox/deployment.yaml.tpl | kubectl apply -f -
kubectl -n sandbox rollout status "deployment/sandbox-${RUNTIME}-${VERSION}" --timeout=30m
kubectl -n sandbox get pods -l "gpusandbox/runtime=${RUNTIME},gpusandbox/version=${VERSION}" -o wide
