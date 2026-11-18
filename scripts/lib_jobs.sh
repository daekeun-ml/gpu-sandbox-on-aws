#!/usr/bin/env bash
# Run gpusandbox.tools inside the cluster as a one-shot Job and stream its output.
# Usage (after sourcing lib.sh):
#   run_tool_job <name-prefix> <tool> [args...]       operator Job (k8s/probe/job-probe.yaml.tpl)
#   run_job_template <template> <job-name> <tool> [args...]   any Job template with the same
#                                                     JOB_NAME and TOOL_ARGS variables
# Both return 0 only if the Job succeeded.

run_job_template() {
  local template="$1" name="$2"; shift 2
  require_vars CONTROL_IMAGE_URI SANDBOX_AUDIENCE
  local args_json phase=""
  args_json="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "$@")"
  render "${template}" JOB_NAME="${name}" TOOL_ARGS="${args_json}" \
    | kubectl apply -f - >/dev/null || return 1

  # Wait until the pod has started (or already finished) before following its logs.
  for _ in $(seq 1 120); do
    phase="$(kubectl -n rl-trainer get pods -l "job-name=${name}" -o jsonpath='{.items[0].status.phase}' 2>/dev/null)"
    [[ "${phase}" == "Running" || "${phase}" == "Succeeded" || "${phase}" == "Failed" ]] && break
    sleep 5
  done
  [[ -n "${phase}" && "${phase}" != "Pending" ]] || { warn "job ${name} did not start"; return 1; }

  kubectl -n rl-trainer logs -f "job/${name}"
  kubectl -n rl-trainer wait --for=condition=Complete "job/${name}" --timeout=30s >/dev/null 2>&1
}

run_tool_job() {
  local prefix="$1"; shift
  run_job_template k8s/probe/job-probe.yaml.tpl "${prefix}-$(date +%s)" "$@"
}
