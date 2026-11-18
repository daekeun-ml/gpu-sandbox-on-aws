#!/usr/bin/env bash
# Watch the reward path without a GPU (scenario C): scripts/ops/simulate.sh [steps] [interval_s]
# This is not training: there is no model. A Job in the trainer namespace scores the golden
# submissions batch by batch through the sandbox-routing ConfigMap, the same way the GRPO
# reward functions do, and prints the same reward_batch and sandbox_version_switch events.
# Run scripts/ops/rollout.sh in a second terminal to see a switch land between batches.
source "$(dirname "$0")/../lib.sh"
source "$(dirname "$0")/../lib_jobs.sh"
require_tools kubectl

steps="${1:-30}"
interval="${2:-20}"
active="$(kubectl -n rl-trainer get configmap sandbox-routing -o jsonpath='{.data.routing\.json}' \
  | python3 -c 'import json, sys; a = json.load(sys.stdin)["active"]; print(a["runtime"], a["version"])')" \
  || die "no routing table: run scripts/05_setup_namespaces_auth.sh first"
read -r runtime version <<<"${active}"
device="cuda"
[[ "${runtime}" == *-cpu ]] && device="cpu"

log "active pool ${runtime}/${version}: ${steps} batches, one every ${interval}s (device ${device})"
run_tool_job "simulate" simulate --steps "${steps}" --interval-s "${interval}" --device "${device}"
