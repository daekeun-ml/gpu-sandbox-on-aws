"""Level 0: elementwise vector addition (pipeline sanity task)."""

import torch
from torch import nn

from gpusandbox.tasks._common import generator, pick

TASK_ID = "vector_add"
LEVEL = 0
DESCRIPTION = "Add two 1-D float32 tensors elementwise."
INPUT_SPEC = "x: float32[16777216], y: float32[16777216]"
ATOL = 1e-6
RTOL = 1e-6


class Model(nn.Module):
    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return x + y


def get_init_inputs() -> list:
    return []


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    (n,) = pick(size, (16_777_216,), (4096,))
    g = generator(seed, device)
    return [
        torch.randn(n, generator=g, device=device),
        torch.randn(n, generator=g, device=device),
    ]
