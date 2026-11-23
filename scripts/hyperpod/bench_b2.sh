#!/usr/bin/env bash
# Compare two clients against the same B2 grading pool, one at a time.
# scripts/hyperpod/bench_b2.sh [requests]
source "$(dirname "$0")/../lib.sh"
require_tools kubectl jq
require_vars CONTROL_IMAGE_URI SANDBOX_AUDIENCE
requests="${1:-32}"
[[ "${requests}" =~ ^[1-9][0-9]*$ ]] || die "requests must be a positive integer"
run="${BENCH_RUN_ID:-$(date +%Y%m%d%H%M%S)}"
out="${BENCH_OUT_DIR:-${REPO_ROOT}}"
mkdir -p "${out}"
args="$(jq -nc --arg n "${requests}" '["bench","--address","sandbox-gvisor-hyperpod-v1.sandbox.svc.cluster.local:8000",
  "--requests",$n,"--golden","relu_bias_triton"]')"
for role in system trainer; do
  job="b2-bench-${role}-${run}"
  selector="$(jq -nc --arg role "${role}" --arg run "${run}" '{
    metadata:{labels:{"gpusandbox/experiment":"b2-bench","gpusandbox/bench-run":$run}},
    spec:{template:{spec:{nodeSelector:{"gpusandbox/role":$role},
    tolerations:[{key:"nvidia.com/gpu",operator:"Exists",effect:"NoSchedule"}]}}}}')"
  render k8s/probe/job-probe.yaml.tpl JOB_NAME="${job}" TOOL_ARGS="${args}" \
    | kubectl patch --local -f - --type=merge -p "${selector}" -o yaml | kubectl create -f -
  if ! kubectl -n rl-trainer wait --for=condition=Complete "job/${job}" --timeout=25m; then
    kubectl -n rl-trainer logs "job/${job}" >&2 || true
    die "benchmark job ${job} did not complete"
  fi
  node="$(kubectl -n rl-trainer get pods -l "job-name=${job}" -o json | jq -er \
    '.items[]|select(.status.phase=="Succeeded")|.spec.nodeName')"
  log "${role} client on ${node}"
  kubectl -n rl-trainer logs "job/${job}" | tee "${out}/${job}.jsonl"
done
