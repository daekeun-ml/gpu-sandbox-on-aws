"""On-policy GRPO with TRL, scored by GPU sandboxes.

Each optimizer step:
  1. vLLM (colocated on the trainer GPU) samples ``num_generations`` kernels per prompt with
     the current policy weights.
  2. KernelRewards pins one sandbox routing snapshot (runtime + version) for the whole batch
     and evaluates every completion in a sandbox pod (compile, correctness, timing).
  3. GRPO turns group-relative rewards into advantages and updates the LoRA adapter; TRL
     syncs the merged weights back into vLLM before the next generation.

steps_per_generation is left at its default (= gradient_accumulation_steps), so every
generation batch is used for exactly one optimizer step: strictly on-policy.

Usage (inside the trainer pod; see k8s/trainer/job-grpo.yaml.tpl):
    python rl/trl/train_grpo.py --output-dir /outputs/grpo --max-steps 60
Local plumbing check without a GPU (tiny model, no vLLM, CPU sandboxes on loopback):
    python rl/trl/train_grpo.py --dry-run --model HuggingFaceTB/SmolLM2-135M-Instruct
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--model", default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    p.add_argument("--output-dir", default="/outputs/grpo")
    p.add_argument("--max-steps", type=int, default=60)
    p.add_argument("--max-level", type=int, default=2, help="hardest task level to include")
    p.add_argument("--repeats", type=int, default=64, help="dataset rows per task")
    p.add_argument("--num-generations", type=int, default=8)
    p.add_argument("--per-device-batch", type=int, default=4, help="completions per micro-batch")
    p.add_argument("--grad-accum", type=int, default=4)
    p.add_argument("--max-completion-length", type=int, default=768)
    p.add_argument("--learning-rate", type=float, default=1e-5)
    p.add_argument("--lora-r", type=int, default=32)
    p.add_argument("--lora-alpha", type=int, default=64)
    p.add_argument("--vllm-gpu-memory-utilization", type=float, default=0.35)
    p.add_argument("--vllm-max-model-length", type=int, default=2048)
    p.add_argument("--runtime", default=None, help="override the routing table's active runtime")
    p.add_argument("--allow-torch-only", action="store_true",
                   help="give full correctness credit without a Triton kernel")
    p.add_argument("--reward-weights", default="0.1,1.0,0.5", help="format,correctness,speedup")
    p.add_argument("--metrics-file", default=None, help="JSONL file for per-batch sandbox metrics")
    p.add_argument("--save-steps", type=int, default=20)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dry-run", action="store_true",
                   help="CPU plumbing check: no vLLM, 2 steps, short completions")
    return p.parse_args()


def latest_checkpoint(output_dir: Path) -> str | None:
    # Resume after a pod or node replacement (HyperPod restarts the job on a healthy node).
    checkpoints = sorted(output_dir.glob("checkpoint-*"), key=lambda p: int(p.name.split("-")[-1]))
    return str(checkpoints[-1]) if checkpoints else None


def main() -> None:
    args = parse_args()

    # Imported here so that `--help` works without the training stack installed.
    from datasets import Dataset
    from peft import LoraConfig
    from trl import GRPOConfig, GRPOTrainer

    from gpusandbox.client import SandboxClient
    from gpusandbox.prompts import build_rows
    from gpusandbox.rewards import KernelRewards

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = Dataset.from_list(build_rows(max_level=args.max_level, repeats=args.repeats))
    dataset = dataset.shuffle(seed=args.seed)

    client = SandboxClient.from_env()
    if client.routing is not None:
        first = client.routing.snapshot(args.runtime)
        print(json.dumps({"event": "routing", "mode": "direct", "runtime": first.runtime,
                          "version": first.version, "address": first.address}), flush=True)
    else:
        print(json.dumps({"event": "routing", "mode": "gateway", "gateway": client.gateway}),
              flush=True)

    rewards = KernelRewards(
        client,
        require_triton=not args.allow_torch_only,
        runtime=args.runtime,
        metrics_file=args.metrics_file or output_dir / "sandbox_metrics.jsonl",
    )

    weights = [float(w) for w in args.reward_weights.split(",")]
    common = dict(
        output_dir=str(output_dir),
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.per_device_batch,
        gradient_accumulation_steps=args.grad_accum,
        num_generations=args.num_generations,
        max_completion_length=args.max_completion_length,
        reward_weights=weights,
        logging_steps=1,
        save_steps=args.save_steps,
        save_total_limit=2,
        report_to="none",
        seed=args.seed,
    )
    if args.dry_run:
        config = GRPOConfig(
            **{**common, "max_completion_length": 32, "save_steps": 1000},
            max_steps=2,
            use_vllm=False,
            bf16=False,
            gradient_checkpointing=False,
            use_cpu=True,
        )
    else:
        config = GRPOConfig(
            **common,
            max_steps=args.max_steps,
            use_vllm=True,
            vllm_mode="colocate",
            vllm_gpu_memory_utilization=args.vllm_gpu_memory_utilization,
            vllm_enable_sleep_mode=True,
            vllm_max_model_length=args.vllm_max_model_length,
        )

    trainer = GRPOTrainer(
        model=args.model,
        reward_funcs=rewards.reward_funcs,
        args=config,
        train_dataset=dataset,
        peft_config=LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            target_modules="all-linear",
            task_type="CAUSAL_LM",
        ),
    )
    trainer.train(resume_from_checkpoint=latest_checkpoint(output_dir))
    trainer.save_model(str(output_dir / "final"))
    print(json.dumps({"event": "done", "output": str(output_dir / "final"),
                      "reward_batches": rewards.batches}), flush=True)


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
