"""Level 2: LayerNorm with weight and bias passed as inputs."""

import torch
from torch import nn
from torch.nn import functional as F

from gpusandbox.tasks._common import generator, pick

TASK_ID = "layer_norm"
LEVEL = 2
DESCRIPTION = (
    "Apply LayerNorm over the last dimension with weight w, bias b and eps passed to the "
    "constructor."
)
INPUT_SPEC = (
    "__init__(eps: float = 1e-5); x: float32[4096, 1024], w: float32[1024], b: float32[1024]"
)
ATOL = 1e-5
RTOL = 1e-4


class Model(nn.Module):
    def __init__(self, eps: float) -> None:
        super().__init__()
        self.eps = eps

    def forward(self, x: torch.Tensor, w: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return F.layer_norm(x, (x.shape[-1],), w, b, self.eps)


def get_init_inputs() -> list:
    return [1e-5]


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    rows, cols = pick(size, (4096, 1024), (64, 128))
    g = generator(seed, device)
    return [
        torch.randn(rows, cols, generator=g, device=device),
        torch.randn(cols, generator=g, device=device),
        torch.randn(cols, generator=g, device=device),
    ]
