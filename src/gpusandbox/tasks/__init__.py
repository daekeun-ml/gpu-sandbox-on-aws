"""Task registry shared by the trainer (prompt building) and the sandbox (trusted reference).

Every task module follows a KernelBench-like contract:
  * ``Model``: the trusted PyTorch reference implementation.
  * ``get_init_inputs()``: constructor arguments for both ``Model`` and the candidate ``ModelNew``.
  * ``get_inputs(seed, device, size)``: deterministic forward inputs for a given seed.
  * ``TASK_ID``, ``LEVEL``, ``DESCRIPTION``, ``INPUT_SPEC``, ``ATOL``, ``RTOL``: metadata.

The task set is part of the sandbox version. Changing a task changes rewards, so it must ship
as a new sandbox version (see docs/production/05_sandbox_updates.md).
"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from functools import lru_cache
from types import ModuleType

# Ordered by difficulty. Level 0 is a sanity level that small models can usually solve.
TASK_MODULES: tuple[str, ...] = (
    "vector_add",
    "relu_bias",
    "scaled_residual",
    "silu_mul",
    "gelu_tanh",
    "row_sum_sq",
    "row_softmax",
    "rms_norm",
    "layer_norm",
    "matmul_bias_relu",
)


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    level: int
    description: str
    input_spec: str
    atol: float
    rtol: float
    reference_source: str
    module: ModuleType


def _load(name: str) -> TaskSpec:
    module = importlib.import_module(f"{__name__}.{name}")
    return TaskSpec(
        task_id=module.TASK_ID,
        level=module.LEVEL,
        description=module.DESCRIPTION,
        input_spec=module.INPUT_SPEC,
        atol=module.ATOL,
        rtol=module.RTOL,
        reference_source=inspect.getsource(module.Model),
        module=module,
    )


@lru_cache(maxsize=None)
def list_tasks(max_level: int | None = None) -> tuple[TaskSpec, ...]:
    specs = tuple(_load(name) for name in TASK_MODULES)
    if max_level is None:
        return specs
    return tuple(spec for spec in specs if spec.level <= max_level)


def get_task(task_id: str) -> TaskSpec:
    for spec in list_tasks():
        if spec.task_id == task_id:
            return spec
    raise KeyError(f"unknown task_id: {task_id!r}")
