"""Level 1: SwiGLU-style gate, silu(a) * b."""

import torch
from torch import nn
from torch.nn import functional as F

from gpusandbox.tasks._common import generator, pick

TASK_ID = "silu_mul"
LEVEL = 1
DESCRIPTION = "Compute silu(a) * b elementwise (the gate used in SwiGLU MLPs)."
INPUT_SPEC = "a: float32[4096, 4096], b: float32[4096, 4096]"
# Triton's exp differs slightly from ATen's, so allow a small tolerance.
ATOL = 1e-5
RTOL = 1e-4


class Model(nn.Module):
    def forward(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return F.silu(a) * b


def get_init_inputs() -> list:
    return []


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    rows, cols = pick(size, (4096, 4096), (64, 128))
    g = generator(seed, device)
    return [
        torch.randn(rows, cols, generator=g, device=device),
        torch.randn(rows, cols, generator=g, device=device),
    ]
