"""Golden submissions with known verdicts.

Used to verify a fresh sandbox pool (scripts/ops/verify.sh) and as the parity set
for a sandbox version rollout (scripts/ops/rollout.sh): a new version must return the
same verdict for every entry before traffic moves to it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Golden:
    name: str
    task_id: str
    code: str
    expect_status: str
    expect_custom_kernel: bool | None = None  # None: do not check (e.g. CPU pools)
    gpu_only: bool = False


VECTOR_ADD_TRITON = '''import torch
import triton
import triton.language as tl
from torch import nn


@triton.jit
def add_kernel(x_ptr, y_ptr, out_ptr, n, BLOCK: tl.constexpr):
    offs = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    mask = offs < n
    tl.store(out_ptr + offs, tl.load(x_ptr + offs, mask=mask) + tl.load(y_ptr + offs, mask=mask), mask=mask)


class ModelNew(nn.Module):
    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        out = torch.empty_like(x)
        n = x.numel()
        add_kernel[(triton.cdiv(n, 1024),)](x, y, out, n, BLOCK=1024)
        return out
'''

RELU_BIAS_TRITON = '''import torch
import triton
import triton.language as tl
from torch import nn


@triton.jit
def relu_bias_kernel(x_ptr, b_ptr, out_ptr, n_cols, BLOCK: tl.constexpr):
    row = tl.program_id(0)
    cols = tl.program_id(1) * BLOCK + tl.arange(0, BLOCK)
    mask = cols < n_cols
    x = tl.load(x_ptr + row * n_cols + cols, mask=mask)
    b = tl.load(b_ptr + cols, mask=mask)
    tl.store(out_ptr + row * n_cols + cols, tl.maximum(x + b, 0.0), mask=mask)


class ModelNew(nn.Module):
    def forward(self, x: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        out = torch.empty_like(x)
        rows, cols = x.shape
        relu_bias_kernel[(rows, triton.cdiv(cols, 1024))](x, b, out, cols, BLOCK=1024)
        return out
'''

RELU_BIAS_TORCH = '''import torch
from torch import nn


class ModelNew(nn.Module):
    def forward(self, x, b):
        return torch.clamp_min(x + b, 0.0)
'''

RELU_BIAS_WRONG = '''import torch
from torch import nn


class ModelNew(nn.Module):
    def forward(self, x, b):
        return x + b
'''

RELU_BIAS_BENCHMARK_CHEAT = '''import torch
from torch import nn


class ModelNew(nn.Module):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def forward(self, x, b):
        self.calls += 1
        if self.calls > 3:
            return torch.zeros_like(x)
        return torch.relu(x + b)
'''

READ_HOST_FILE = '''import torch
from torch import nn

SECRET = open("/etc/hostname").read()


class ModelNew(nn.Module):
    def forward(self, x, b):
        return torch.relu(x + b)
'''

GOLDEN_SET: tuple[Golden, ...] = (
    Golden("vector_add_triton", "vector_add", VECTOR_ADD_TRITON, "ok", True, gpu_only=True),
    Golden("relu_bias_triton", "relu_bias", RELU_BIAS_TRITON, "ok", True, gpu_only=True),
    Golden("relu_bias_torch_only", "relu_bias", RELU_BIAS_TORCH, "ok", False),
    Golden("relu_bias_wrong", "relu_bias", RELU_BIAS_WRONG, "wrong_answer"),
    Golden("relu_bias_benchmark_cheat", "relu_bias", RELU_BIAS_BENCHMARK_CHEAT, "wrong_answer"),
    Golden("read_host_file", "relu_bias", READ_HOST_FILE, "policy_violation"),
)


def golden_for(device: str) -> tuple[Golden, ...]:
    return tuple(g for g in GOLDEN_SET if device == "cuda" or not g.gpu_only)
