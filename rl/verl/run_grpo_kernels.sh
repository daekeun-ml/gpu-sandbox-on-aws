#!/usr/bin/env bash
# Submit veRL GRPO (production track) to the RayCluster in rl-trainer.
# Run from a shell that reaches the Ray dashboard, e.g. after
#   kubectl -n rl-trainer port-forward svc/verl-head-svc 8265:8265   (binds 127.0.0.1)
#
# Config keys follow veRL 0.9.1 (reward settings live under reward.*). Re-verify against the
# release you install; older examples use top-level custom_reward_function.* keys.
set -euo pipefail

RAY_ADDRESS="${RAY_ADDRESS:-http://127.0.0.1:8265}"
MODEL_PATH="${MODEL_PATH:-Qwen/Qwen2.5-Coder-7B-Instruct}"   # Apache-2.0, ungated
DATA_DIR="${DATA_DIR:-/fsx/verl/data/kernels}"
CKPT_DIR="${CKPT_DIR:-/fsx/verl/ckpts/kernels-grpo}"
NNODES="${NNODES:-1}"
GPUS_PER_NODE="${GPUS_PER_NODE:-8}"

ray job submit --address "${RAY_ADDRESS}" --no-wait -- \
  python3 -m verl.trainer.main_ppo \
  algorithm.adv_estimator=grpo \
  algorithm.use_kl_in_reward=False \
  data.train_files="${DATA_DIR}/train.parquet" \
  data.val_files="${DATA_DIR}/val.parquet" \
  data.train_batch_size="${TRAIN_BATCH_SIZE:-64}" \
  data.max_prompt_length=1536 \
  data.max_response_length=1536 \
  data.filter_overlong_prompts=True \
  actor_rollout_ref.model.path="${MODEL_PATH}" \
  actor_rollout_ref.model.enable_gradient_checkpointing=True \
  actor_rollout_ref.actor.optim.lr=1e-6 \
  actor_rollout_ref.actor.ppo_mini_batch_size=32 \
  actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=2 \
  actor_rollout_ref.actor.use_kl_loss=True \
  actor_rollout_ref.actor.kl_loss_coef=0.001 \
  actor_rollout_ref.actor.kl_loss_type=low_var_kl \
  actor_rollout_ref.rollout.name=vllm \
  actor_rollout_ref.rollout.n="${N_RESP_PER_PROMPT:-8}" \
  actor_rollout_ref.rollout.gpu_memory_utilization=0.5 \
  actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
  actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=8 \
  actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=8 \
  reward.custom_reward_function.path=/opt/gpusandbox/rl/verl/reward_fn.py \
  reward.custom_reward_function.name=compute_score \
  reward.num_workers=8 \
  trainer.logger='["console"]' \
  trainer.project_name=gpu-sandbox \
  trainer.experiment_name=kernels-grpo \
  trainer.n_gpus_per_node="${GPUS_PER_NODE}" \
  trainer.nnodes="${NNODES}" \
  trainer.default_local_dir="${CKPT_DIR}" \
  trainer.resume_mode=auto \
  trainer.save_freq=20 \
  trainer.test_freq=20 \
  trainer.total_training_steps="${TOTAL_STEPS:-200}"
