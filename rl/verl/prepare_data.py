"""Write the kernel tasks as veRL parquet files (train/val).

Row schema veRL expects: data_source, prompt (chat messages), ability, reward_model
{style, ground_truth}, extra_info. ground_truth carries the task_id; the sandbox holds the
trusted reference, so no answer leaves the sandbox image.

    python rl/verl/prepare_data.py --out /fsx/verl/data/kernels --repeats 64
"""

from __future__ import annotations

import argparse
from pathlib import Path

from gpusandbox.prompts import build_messages
from gpusandbox.tasks import list_tasks


def rows(max_level: int, repeats: int) -> list[dict]:
    out = []
    for r in range(repeats):
        for spec in list_tasks(max_level):
            index = len(out)
            out.append(
                {
                    "data_source": "gpusandbox/kernels",
                    "prompt": build_messages(spec),
                    "ability": "code",
                    "reward_model": {"style": "rule", "ground_truth": spec.task_id},
                    "extra_info": {"index": index, "task_id": spec.task_id, "level": spec.level, "repeat": r},
                }
            )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-level", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=64)
    args = parser.parse_args()

    import pandas as pd  # installed with veRL

    args.out.mkdir(parents=True, exist_ok=True)
    train = rows(args.max_level, args.repeats)
    val = rows(args.max_level, 1)
    pd.DataFrame(train).to_parquet(args.out / "train.parquet")
    pd.DataFrame(val).to_parquet(args.out / "val.parquet")
    print(f"wrote {len(train)} train / {len(val)} val rows to {args.out}")


if __name__ == "__main__":
    main()
