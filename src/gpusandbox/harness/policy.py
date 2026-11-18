"""Static policy for candidate code.

This is not the security boundary. gVisor or Kata isolates the node from candidate code. The
policy protects reward integrity: it rejects the cheap ways an RL policy can game a measurement
from inside the evaluated process, such as monkeypatching timers, introspecting the harness
through frames or dunder attributes, or importing the trusted reference.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

MAX_SOURCE_BYTES = 32 * 1024
MAX_AST_NODES = 25_000

ALLOWED_IMPORT_ROOTS = frozenset({"torch", "triton", "math", "typing", "functools", "itertools"})

# Submodules that bypass the "write a kernel" contract or reach into the harness, plus the
# CUDA stream and graph APIs used by known timing hacks (work on a side stream, replaying a
# captured graph). Triton kernels launch on the current stream and need none of these.
DENIED_MODULE_PREFIXES = (
    "torch.utils.cpp_extension",
    "torch.compile",
    "torch.jit",
    "torch.hub",
    "torch.distributed",
    "torch.multiprocessing",
    "torch.package",
    "torch.library",
    "torch.cuda.Stream",
    "torch.cuda.ExternalStream",
    "torch.cuda.stream",
    "torch.cuda.set_stream",
    "torch.cuda.CUDAGraph",
    "torch.cuda.graph",
    "torch.cuda.graphs",
)
CUDA_CPP_PREFIX = "torch.utils.cpp_extension"

DENIED_BUILTINS = frozenset(
    {
        "__import__",
        "breakpoint",
        "compile",
        "delattr",
        "eval",
        "exec",
        "exit",
        "getattr",
        "globals",
        "help",
        "input",
        "locals",
        "open",
        "quit",
        "setattr",
        "vars",
    }
)

# Underscore attributes are denied (frames, __dict__, __subclasses__, torch._C, ...).
# super().__init__() is the only dunder a normal nn.Module needs.
ALLOWED_DUNDER_ATTRS = frozenset({"__init__"})
# Generated code often ends with `if __name__ == "__main__":`; other dunder names
# (__builtins__, __loader__, __spec__) give access to the import system.
ALLOWED_DUNDER_NAMES = frozenset({"__name__"})

TRITON_JIT_NAMES = frozenset({"triton.jit"})


@dataclass
class PolicyReport:
    ok: bool
    violations: list[str] = field(default_factory=list)
    uses_triton: bool = False
    defines_model_new: bool = False


def _bound_names(tree: ast.AST) -> set[str]:
    """Names the candidate binds itself (arguments, assignments, loop targets, defs).

    A parameter called ``input`` is common in PyTorch code; it shadows the builtin and must
    not be reported as a use of ``input()``.
    """
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            bound.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
    return bound


class _Checker(ast.NodeVisitor):
    def __init__(self, allow_cuda_cpp: bool, bound: set[str]) -> None:
        self.allow_cuda_cpp = allow_cuda_cpp
        self.bound = bound
        self.violations: list[str] = []
        self.aliases: dict[str, str] = {}  # local name -> fully qualified module or symbol
        self.uses_triton = False
        self.defines_model_new = False

    # --- helpers -----------------------------------------------------------------------
    def _deny(self, node: ast.AST, message: str) -> None:
        line = getattr(node, "lineno", "?")
        self.violations.append(f"line {line}: {message}")

    def _qualname(self, node: ast.AST) -> str | None:
        """Resolve a Name/Attribute chain to a dotted name using import aliases."""
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        root = self.aliases.get(node.id, node.id)
        return ".".join([root, *reversed(parts)])

    def _check_module(self, node: ast.AST, module: str) -> None:
        root = module.split(".")[0]
        if root not in ALLOWED_IMPORT_ROOTS:
            self._deny(node, f"import of '{module}' is not allowed")
            return
        if module.startswith(CUDA_CPP_PREFIX) and self.allow_cuda_cpp:
            return
        if any(module == p or module.startswith(p + ".") for p in DENIED_MODULE_PREFIXES):
            self._deny(node, f"use of '{module}' is not allowed")
        if any(part.startswith("_") for part in module.split(".")):
            self._deny(node, f"private module '{module}' is not allowed")

    # --- imports -----------------------------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_module(node, alias.name)
            local = alias.asname or alias.name.split(".")[0]
            self.aliases[local] = alias.name if alias.asname else alias.name.split(".")[0]
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level:
            self._deny(node, "relative imports are not allowed")
        module = node.module or ""
        self._check_module(node, module)
        for alias in node.names:
            if alias.name == "*":
                self._deny(node, "star imports are not allowed")
                continue
            full = f"{module}.{alias.name}"
            self._check_module(node, full)
            self.aliases[alias.asname or alias.name] = full
        self.generic_visit(node)

    # --- names, attributes and calls ---------------------------------------------------
    def visit_Name(self, node: ast.Name) -> None:
        if node.id.startswith("__") and node.id not in ALLOWED_DUNDER_NAMES:
            self._deny(node, f"name '{node.id}' is not allowed")
        elif node.id in DENIED_BUILTINS and node.id not in self.bound:
            self._deny(node, f"builtin '{node.id}' is not allowed")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("_") and node.attr not in ALLOWED_DUNDER_ATTRS:
            self._deny(node, f"private attribute '.{node.attr}' is not allowed")
        qual = self._qualname(node)
        if qual:
            if qual.startswith(CUDA_CPP_PREFIX) and self.allow_cuda_cpp:
                pass
            elif any(qual == p or qual.startswith(p + ".") for p in DENIED_MODULE_PREFIXES):
                self._deny(node, f"use of '{qual}' is not allowed")
        self.generic_visit(node)

    def _check_store_target(self, target: ast.AST) -> None:
        if isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._check_store_target(elt)
            return
        if isinstance(target, ast.Attribute):
            root = target
            while isinstance(root, ast.Attribute):
                root = root.value
            # Attribute writes are limited to the module's own state (self.alpha = ...).
            # Writing anything else (torch.cuda.Event.elapsed_time = ..., or the same through
            # a local alias) is how a candidate would replace the timer or the reference op.
            if not (isinstance(root, ast.Name) and root.id == "self"):
                name = self._qualname(target) or ast.unparse(target)
                self._deny(target, f"assignment to attribute '{name}' is not allowed")

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._check_store_target(target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._check_store_target(node.target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._check_store_target(node.target)
        self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> None:
        for target in node.targets:
            self._check_store_target(target)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        self._deny(node, "global statements are not allowed")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self._deny(node, "nonlocal statements are not allowed")

    # --- definitions -------------------------------------------------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for deco in node.decorator_list:
            target = deco.func if isinstance(deco, ast.Call) else deco
            if self._qualname(target) in TRITON_JIT_NAMES:
                self.uses_triton = True
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for base in node.bases:
            # A Tensor subclass can defer work until the result is read (lazy tensor hack).
            if self._qualname(base) == "torch.Tensor":
                self._deny(node, "subclassing torch.Tensor is not allowed")
        if node.name == "ModelNew":
            has_forward = any(
                isinstance(item, ast.FunctionDef) and item.name == "forward" for item in node.body
            )
            if has_forward:
                self.defines_model_new = True
            else:
                self._deny(node, "class ModelNew must define forward()")
        self.generic_visit(node)


def check_source(source: str, *, allow_cuda_cpp: bool = False) -> PolicyReport:
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        return PolicyReport(ok=False, violations=[f"source exceeds {MAX_SOURCE_BYTES} bytes"])
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return PolicyReport(ok=False, violations=[f"syntax error: {exc.msg} (line {exc.lineno})"])
    if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
        return PolicyReport(ok=False, violations=[f"source exceeds {MAX_AST_NODES} AST nodes"])

    checker = _Checker(allow_cuda_cpp=allow_cuda_cpp, bound=_bound_names(tree))
    checker.visit(tree)
    if not checker.defines_model_new and not any("ModelNew" in v for v in checker.violations):
        checker.violations.append("no top-level class ModelNew found")
    return PolicyReport(
        ok=not checker.violations,
        violations=checker.violations,
        uses_triton=checker.uses_triton,
        defines_model_new=checker.defines_model_new,
    )
