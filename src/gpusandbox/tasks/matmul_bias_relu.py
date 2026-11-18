"""Level 3: fp16 GEMM fused with bias-add and ReLU."""

import torch
from torch import nn

from gpusandbox.tasks._common import generator, pick

TASK_ID = "matmul_bias_relu"
LEVEL = 3
DESCRIPTION = "Compute relu(x @ w + b) in float16 (accumulate in float32 inside the kernel)."
INPUT_SPEC = "x: float16[2048, 1024], w: float16[1024, 1024], b: float16[1024]"
# fp16 GEMM results depend on accumulation order and tiling.
ATOL = 2e-2
RTOL = 2e-2


class Model(nn.Module):
    def forward(self, x: torch.Tensor, w: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return torch.relu(x @ w + b)


def get_init_inputs() -> list:
    return []


def get_inputs(seed: int, device: str, size: str = "full") -> list[torch.Tensor]:
    m, k, n = pick(size, (2048, 1024, 1024), (64, 64, 64))
    # CPU matmul in fp16 is slow and unsupported on some builds; smoke runs use fp32.
    dtype = torch.float16 if device == "cuda" else torch.float32
    g = generator(seed, device)
    scale = k**-0.5
    return [
        (torch.randn(m, k, generator=g, device=device) * scale).to(dtype),
        (torch.randn(k, n, generator=g, device=device) * scale).to(dtype),
        torch.randn(n, generator=g, device=device).to(dtype),
    ]
