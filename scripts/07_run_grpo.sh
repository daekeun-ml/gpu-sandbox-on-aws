#!/usr/bin/env bash
# Start on-policy GRPO training (scenario A): scripts/07_run_grpo.sh [max_steps]
# The active sandbox runtime and version come from the sandbox-routing ConfigMap; change it
# with scripts/ops/rollout.sh while training runs.
source "$(dirname "$0")/lib.sh"
require_tools kubectl
require_vars TRAINER_IMAGE_URI SANDBOX_AUDIENCE

export RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
export MAX_STEPS="${1:-60}"
export MODEL_ID="${MODEL_ID:-Qwen/Qwen2.5-Coder-1.5B-Instruct}"

render k8s/trainer/job-grpo.yaml.tpl | kubectl apply -f -
log "job grpo-${RUN_ID} submitted; following logs (Ctrl-C stops following, not training)"
kubectl -n rl-trainer wait --for=condition=Ready pod -l "job-name=grpo-${RUN_ID}" --timeout=30m
kubectl -n rl-trainer logs -f "job/grpo-${RUN_ID}" | grep --line-buffered -E '"event"|loss|Error|Traceback'
