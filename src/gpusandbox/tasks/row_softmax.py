"""Level 2: numerically stable row-wise softmax."""

import torch
from torch import nn

from gpusandbox.tasks._common import generator, pick

TASK_ID = "row_softmax"
LEVEL = 2
DESCRIPTION = "Compute softmax over the last dimension of a 2-D tensor (numerically stable)."
INPUT_SPEC = "x: float32[4096, 1024]"
ATOL = 1e-6
RTOL = 1e-4


class Model(nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.softmax(x, dim=-1)


def get_init_inputs() -> list:
    return []


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    rows, cols = pick(size, (4096, 1024), (64, 128))
    g = generator(seed, device)
    # Scale up so that a naive exp() without max-subtraction overflows.
    return [torch.randn(rows, cols, generator=g, device=device) * 30.0]
