from gpusandbox.harness.policy import check_source
from gpusandbox.prompts import FORMAT_EXAMPLE

TRITON_RELU_BIAS = """
import torch
import triton
import triton.language as tl
from torch import nn


@triton.autotune(configs=[triton.Config({"BLOCK": 1024})], key=["n_cols"])
@triton.jit
def relu_bias_kernel(x_ptr, b_ptr, out_ptr, n_cols, BLOCK: tl.constexpr):
    row = tl.program_id(0)
    cols = tl.program_id(1) * BLOCK + tl.arange(0, BLOCK)
    mask = cols < n_cols
    x = tl.load(x_ptr + row * n_cols + cols, mask=mask)
    b = tl.load(b_ptr + cols, mask=mask)
    tl.store(out_ptr + row * n_cols + cols, tl.maximum(x + b, 0.0), mask=mask)


class ModelNew(nn.Module):
    def forward(self, x, b):
        out = torch.empty_like(x)
        rows, cols = x.shape
        grid = lambda meta: (rows, triton.cdiv(cols, meta["BLOCK"]))
        relu_bias_kernel[grid](x, b, out, cols)
        return out
"""


def test_format_example_is_accepted_and_detected_as_triton():
    report = check_source(FORMAT_EXAMPLE)
    assert report.ok, report.violations
    assert report.uses_triton and report.defines_model_new


def test_autotuned_triton_kernel_is_accepted():
    report = check_source(TRITON_RELU_BIAS)
    assert report.ok, report.violations
    assert report.uses_triton


def test_input_parameter_shadowing_builtin_is_allowed():
    code = (
        "import torch\nfrom torch import nn\n"
        "class ModelNew(nn.Module):\n"
        "    def forward(self, input):\n"
        "        return torch.relu(input)\n"
        "if __name__ == '__main__':\n"
        "    print(ModelNew())\n"
    )
    assert check_source(code).ok


def test_rejects_forbidden_imports_and_builtins():
    for snippet in (
        "import os",
        "import subprocess",
        "from importlib import import_module",
        "import torch.utils.cpp_extension",
        "x = eval('1')",
        "f = open('/etc/passwd')",
        "g = globals()",
    ):
        code = f"{snippet}\nimport torch\nfrom torch import nn\nclass ModelNew(nn.Module):\n    def forward(self, x):\n        return x\n"
        assert not check_source(code).ok, snippet


def test_rejects_timer_monkeypatch_even_through_alias():
    direct = "import torch\ntorch.cuda.Event.elapsed_time = None\n"
    aliased = "import torch\nev = torch.cuda.Event\nev.elapsed_time = None\n"
    for prefix in (direct, aliased):
        code = prefix + "from torch import nn\nclass ModelNew(nn.Module):\n    def forward(self, x):\n        return x\n"
        report = check_source(code)
        assert not report.ok
        assert any("assignment to attribute" in v for v in report.violations)


def test_rejects_dunder_and_private_access():
    for body in ("return x.__class__", "return torch._C", "return __builtins__"):
        code = f"import torch\nfrom torch import nn\nclass ModelNew(nn.Module):\n    def forward(self, x):\n        {body}\n"
        assert not check_source(code).ok, body


def test_cuda_cpp_is_opt_in():
    code = (
        "import torch\nfrom torch.utils.cpp_extension import load_inline\nfrom torch import nn\n"
        "class ModelNew(nn.Module):\n    def forward(self, x):\n        return x\n"
    )
    assert not check_source(code).ok
    assert check_source(code, allow_cuda_cpp=True).ok


def test_missing_model_new_and_syntax_errors():
    assert not check_source("import torch\n").ok
    assert not check_source("class ModelNew(:\n").ok


def test_rejects_side_streams_graphs_and_tensor_subclasses():
    for body in (
        "s = torch.cuda.Stream()",
        "g = torch.cuda.CUDAGraph()",
        "torch.cuda.set_stream(None)",
    ):
        code = f"import torch\nfrom torch import nn\nclass ModelNew(nn.Module):\n    def forward(self, x):\n        {body}\n        return x\n"
        assert not check_source(code).ok, body
    lazy = "import torch\nfrom torch import nn\nclass Lazy(torch.Tensor):\n    pass\nclass ModelNew(nn.Module):\n    def forward(self, x):\n        return x\n"
    assert not check_source(lazy).ok
    # Type hints with torch.Tensor stay legal.
    hinted = "import torch\nfrom torch import nn\nclass ModelNew(nn.Module):\n    def forward(self, x: torch.Tensor) -> torch.Tensor:\n        return x\n"
    assert check_source(hinted).ok
