"""Level 0: residual add with a constructor-time scale."""

import torch
from torch import nn

from gpusandbox.tasks._common import generator, pick

TASK_ID = "scaled_residual"
LEVEL = 0
DESCRIPTION = "Compute x + alpha * y where alpha is a float passed to the constructor."
INPUT_SPEC = "__init__(alpha: float = 0.5); x: float32[8192, 2048], y: float32[8192, 2048]"
ATOL = 1e-6
RTOL = 1e-6


class Model(nn.Module):
    def __init__(self, alpha: float) -> None:
        super().__init__()
        self.alpha = alpha

    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return x + self.alpha * y


def get_init_inputs() -> list:
    return [0.5]


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    rows, cols = pick(size, (8192, 2048), (64, 128))
    g = generator(seed, device)
    return [
        torch.randn(rows, cols, generator=g, device=device),
        torch.randn(rows, cols, generator=g, device=device),
    ]
