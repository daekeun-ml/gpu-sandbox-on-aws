"""Level 2: RMSNorm with a weight vector."""

import torch
from torch import nn

from gpusandbox.tasks._common import generator, pick

TASK_ID = "rms_norm"
LEVEL = 2
DESCRIPTION = (
    "Compute RMSNorm over the last dimension: x * rsqrt(mean(x**2) + eps) * w, with eps passed "
    "to the constructor."
)
INPUT_SPEC = "__init__(eps: float = 1e-6); x: float32[4096, 1024], w: float32[1024]"
ATOL = 1e-5
RTOL = 1e-4


class Model(nn.Module):
    def __init__(self, eps: float) -> None:
        super().__init__()
        self.eps = eps

    def forward(self, x: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
        return x * torch.rsqrt(x.pow(2).mean(dim=-1, keepdim=True) + self.eps) * w


def get_init_inputs() -> list:
    return [1e-6]


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    rows, cols = pick(size, (4096, 1024), (64, 128))
    g = generator(seed, device)
    return [
        torch.randn(rows, cols, generator=g, device=device),
        torch.randn(cols, generator=g, device=device),
    ]
