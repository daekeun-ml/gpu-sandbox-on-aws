"""Level 1: row-wise sum of squares (a reduction)."""

import torch
from torch import nn

from gpusandbox.tasks._common import generator, pick

TASK_ID = "row_sum_sq"
LEVEL = 1
DESCRIPTION = "Return the sum of squares of each row of a 2-D tensor (output shape [rows])."
INPUT_SPEC = "x: float32[8192, 1024]"
# Reduction order differs between implementations, so compare with a relative tolerance.
ATOL = 1e-3
RTOL = 1e-4


class Model(nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return (x * x).sum(dim=-1)


def get_init_inputs() -> list:
    return []


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    rows, cols = pick(size, (8192, 1024), (64, 128))
    g = generator(seed, device)
    return [torch.randn(rows, cols, generator=g, device=device)]
