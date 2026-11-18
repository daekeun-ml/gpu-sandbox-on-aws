"""Level 1: GELU with the tanh approximation."""

import torch
from torch import nn
from torch.nn import functional as F

from gpusandbox.tasks._common import generator, pick

TASK_ID = "gelu_tanh"
LEVEL = 1
DESCRIPTION = "Apply GELU with approximate='tanh' elementwise."
INPUT_SPEC = "x: float32[4096, 4096]"
ATOL = 1e-5
RTOL = 1e-4


class Model(nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.gelu(x, approximate="tanh")


def get_init_inputs() -> list:
    return []


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    rows, cols = pick(size, (4096, 4096), (64, 128))
    g = generator(seed, device)
    return [torch.randn(rows, cols, generator=g, device=device)]
