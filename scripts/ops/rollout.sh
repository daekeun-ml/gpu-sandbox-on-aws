#!/usr/bin/env bash
# Update the sandbox while on-policy training keeps running (blue/green):
#   scripts/ops/rollout.sh <runtime> <from-version> <to-version> [--finish]
#
#   1. deploy <to> next to <from>         (no traffic yet)
#   2. verify <to>                         (isolation + golden verdicts)
#   3. parity <from> vs <to>               (same verdicts on the golden set, speedups close)
#   4. switch the routing table to <to>    (the trainer reads it on its next sandbox call;
#                                           each reward batch is still scored by one version)
#   5. --finish: scale <from> to zero      (keep the Deployment for a fast rollback)
# Rollback at any point: scripts/ops/rollout.sh <runtime> <to> <from>
source "$(dirname "$0")/../lib.sh"
source "$(dirname "$0")/../lib_jobs.sh"
require_tools kubectl

runtime="${1:?usage: $0 <runtime> <from> <to> [--finish]}"
from="${2:?}"
to="${3:?}"
finish="${4:-}"

if [[ "${finish}" == "--finish" ]]; then
  log "scaling sandbox-${runtime}-${from} to zero"
  kubectl -n sandbox scale "deployment/sandbox-${runtime}-${from}" --replicas=0
  exit 0
fi

log "1) deploying ${runtime}/${to}"
"${REPO_ROOT}/scripts/06_deploy_sandboxes.sh" "${runtime}" "${to}"

log "2) verifying ${runtime}/${to}"
"${REPO_ROOT}/scripts/ops/verify.sh" "${runtime}" "${to}"

log "3) parity ${from} -> ${to}"
device="cuda"
[[ "${runtime}" == *-cpu ]] && device="cpu"
run_tool_job "parity-${runtime}-${from}-${to}" parity \
  --baseline "sandbox-${runtime}-${from}.sandbox.svc.cluster.local:8000" \
  --candidate "sandbox-${runtime}-${to}.sandbox.svc.cluster.local:8000" \
  --device "${device}" \
  || die "parity failed: ${to} keeps no traffic, ${from} stays active"

log "4) switching the routing table to ${runtime}/${to}"
render k8s/base/routing.json.tpl ACTIVE_RUNTIME="${runtime}" ACTIVE_VERSION="${to}" > "${REPO_ROOT}/.routing.json"
for ns in rl-trainer sandbox-gateway; do
  kubectl get namespace "${ns}" >/dev/null 2>&1 || continue
  kubectl -n "${ns}" create configmap sandbox-routing \
    --from-file=routing.json="${REPO_ROOT}/.routing.json" --dry-run=client -o yaml | kubectl apply -f -
done
rm -f "${REPO_ROOT}/.routing.json"
cat <<EOF

The ConfigMap reaches mounted pods within about a minute (kubelet sync). Watch the trainer for
  SWITCH  ${runtime}/${from} -> ${runtime}/${to}   (raw JSON: "event": "sandbox_version_switch")
and a later batch line on ${runtime}/${to} with verdicts other than sandbox_error, then retire the old pool:
  scripts/ops/rollout.sh ${runtime} ${from} ${to} --finish
EOF
