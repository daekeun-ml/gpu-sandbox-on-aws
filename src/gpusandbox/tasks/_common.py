"""Helpers for deterministic input generation."""

from __future__ import annotations

import torch


def generator(seed: int, device: str) -> torch.Generator:
    # A device-local generator keeps input creation on the GPU (fast) and deterministic per
    # device type. Reference and candidate always run on the same device type.
    return torch.Generator(device=device).manual_seed(seed)


def pick(size: str, full: tuple[int, ...], smoke: tuple[int, ...]) -> tuple[int, ...]:
    # "smoke" shapes keep CPU-only smoke tests fast; "full" shapes make GPU timing meaningful.
    if size == "full":
        return full
    if size == "smoke":
        return smoke
    raise ValueError(f"unknown size: {size!r}")
