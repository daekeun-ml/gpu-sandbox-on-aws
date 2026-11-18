#!/usr/bin/env bash
# Scenario B: run the GRPO trainer as a HyperPodPyTorchJob on the HyperPod node.
#   scripts/hyperpod/run_grpo.sh [max_steps]
# The trainer image must contain hyperpodrun: build it with HYPERPOD=1 scripts/03_build_push_images.sh
source "$(dirname "$0")/../lib.sh"
require_tools kubectl
require_vars TRAINER_IMAGE_URI SANDBOX_AUDIENCE HYPERPOD_TRAINER_INSTANCE_TYPE

export RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
export MAX_STEPS="${1:-60}"
export MODEL_ID="${MODEL_ID:-Qwen/Qwen2.5-Coder-1.5B-Instruct}"

render k8s/trainer/hyperpod-job-grpo.yaml.tpl | kubectl apply -f -
log "HyperPodPyTorchJob grpo-${RUN_ID} submitted"
kubectl -n rl-trainer get hyperpodpytorchjob "grpo-${RUN_ID}"
log "follow: kubectl -n rl-trainer logs -f -l app=grpo-trainer | grep --line-buffered '\"event\"'"
