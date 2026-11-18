"""Prompt construction for the kernel-writing task. Shared by the TRL and veRL trainers."""

from __future__ import annotations

from typing import Any

from gpusandbox.tasks import TaskSpec, list_tasks

SYSTEM_PROMPT = (
    "You are an expert GPU kernel engineer. You write correct, fast Triton kernels and "
    "answer with a single complete Python module."
)

# A worked example for an op that is not in the task set. Small models produce far more
# valid Triton when they see the launch pattern once.
FORMAT_EXAMPLE = '''import torch
import triton
import triton.language as tl
from torch import nn


@triton.jit
def double_kernel(x_ptr, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    pid = tl.program_id(axis=0)
    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask=mask)
    tl.store(out_ptr + offsets, x * 2.0, mask=mask)


class ModelNew(nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = torch.empty_like(x)
        n = x.numel()
        grid = lambda meta: (triton.cdiv(n, meta["BLOCK_SIZE"]),)
        double_kernel[grid](x, out, n, BLOCK_SIZE=1024)
        return out
'''

USER_TEMPLATE = """Rewrite the PyTorch module below as a new module named `ModelNew` that returns the same outputs, using one or more custom Triton kernels for the computation.

Task: {description}
Inputs: {input_spec}. All tensors are contiguous and already on a CUDA device.

Rules:
- Keep the constructor and forward() signatures of the reference module.
- Import only torch, torch.nn, torch.nn.functional, triton, triton.language and math.
- Launch your own Triton kernel for the main computation instead of calling the PyTorch op.
- Return tensors with the same shape and dtype as the reference.
- Answer with one ```python code block that contains the complete module.

Example of the expected format (for y = 2 * x):
```python
{example}```

Reference module:
```python
{reference}```
"""


def build_messages(spec: TaskSpec) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_TEMPLATE.format(
                description=spec.description,
                input_spec=spec.input_spec,
                example=FORMAT_EXAMPLE,
                reference=spec.reference_source,
            ),
        },
    ]


def build_rows(*, max_level: int | None = None, repeats: int = 1) -> list[dict[str, Any]]:
    """One row per task (times ``repeats``) with a chat ``prompt`` and the ``task_id``."""
    rows = []
    for _ in range(repeats):
        for spec in list_tasks(max_level):
            rows.append({"prompt": build_messages(spec), "task_id": spec.task_id, "level": spec.level})
    return rows
