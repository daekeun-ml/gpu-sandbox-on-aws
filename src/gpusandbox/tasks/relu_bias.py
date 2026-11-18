"""Level 0: fused bias-add + ReLU."""

import torch
from torch import nn

from gpusandbox.tasks._common import generator, pick

TASK_ID = "relu_bias"
LEVEL = 0
DESCRIPTION = "Add a per-column bias vector to a 2-D activation and apply ReLU."
INPUT_SPEC = "x: float32[4096, 4096], b: float32[4096]"
ATOL = 1e-6
RTOL = 1e-6


class Model(nn.Module):
    def forward(self, x: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return torch.relu(x + b)


def get_init_inputs() -> list:
    return []


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    rows, cols = pick(size, (4096, 4096), (64, 128))
    g = generator(seed, device)
    return [
        torch.randn(rows, cols, generator=g, device=device),
        torch.randn(cols, generator=g, device=device),
    ]
