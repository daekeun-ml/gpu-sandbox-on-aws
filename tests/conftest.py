"""Shared fixtures. Everything here runs on CPU without AWS or a GPU."""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

# PyTorch-only candidates. On CPU there is no Triton, so the harness runs with
# require_triton disabled on the trainer side; these exercise verdict plumbing only.
CORRECT_RELU_BIAS = """
import torch
from torch import nn

class ModelNew(nn.Module):
    def forward(self, x, b):
        return torch.clamp_min(x + b, 0.0)
"""

WRONG_RELU_BIAS = """
import torch
from torch import nn

class ModelNew(nn.Module):
    def forward(self, x, b):
        return x + b
"""

CRASHING = """
import torch
from torch import nn

class ModelNew(nn.Module):
    def forward(self, x, b):
        return torch.matmul(x, torch.ones(3, 3))
"""

SYNTAX_ERROR = """
import torch
class ModelNew(nn.Module)
    pass
"""

# Correct for the first calls (the correctness check), wrong once the benchmark starts.
BENCHMARK_CHEAT = """
import torch
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
"""

INFINITE_LOOP = """
import torch
from torch import nn

class ModelNew(nn.Module):
    def forward(self, x, b):
        while True:
            x = x + 0
"""

MONKEYPATCH = """
import torch
from torch import nn

torch.relu = lambda t: t

class ModelNew(nn.Module):
    def forward(self, x, b):
        return torch.relu(x + b)
"""


@pytest.fixture(scope="session", autouse=True)
def _no_reaping_outside_a_pod() -> Iterator[None]:
    """Turn off the server's post-evaluation reaper for the whole test session.

    reap_strays() SIGKILLs every process in /proc except the server and its ancestors. In a pod
    that is the container's PID namespace, but under pytest on a Linux host it is every other
    process of the same user (editor, shells, long-running jobs). The tests also run two
    loopback servers in one process, so one server's reaper would kill the other's harness
    mid-evaluation. macOS has no /proc, so this is what the tests always saw there.

    Session scope, not function scope: a server thread that outlives its test (ServerThread
    only waits 10 s on exit) must not find the real reaper restored when its evaluation ends.
    """
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("gpusandbox.server.app.reap_strays", lambda: 0)
        yield


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServerThread:
    """Run a real uvicorn sandbox server on loopback in a background thread."""

    def __init__(self, app, port: int) -> None:
        import uvicorn

        self.port = port
        self.server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        )
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def __enter__(self) -> ServerThread:
        self.thread.start()
        deadline = time.time() + 60
        while not self.server.started:
            if time.time() > deadline:
                raise RuntimeError("server did not start")
            time.sleep(0.05)
        return self

    def __exit__(self, *exc) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=10)


@pytest.fixture
def cpu_settings(tmp_path: Path):
    from gpusandbox.server.app import Settings

    return Settings(
        version="test",
        runtime="local",
        device="cpu",
        size="smoke",
        work_root=tmp_path / "work",
        eval_timeout_s=30,
        seeds=2,
        warmup=1,
        iters=3,
        pod_name="local-pod",
    )


@pytest.fixture
def bypass_auth():
    from gpusandbox.auth import AuthConfig

    return AuthConfig(
        audience="", issuer="", allowed_subjects=frozenset(), jwks_file=None, test_bypass=True
    )


@pytest.fixture
def sandbox_servers(cpu_settings, bypass_auth) -> Iterator[list[str]]:
    """Two loopback sandbox servers, as a stand-in for two pods behind a headless Service."""
    from dataclasses import replace

    from gpusandbox.server.app import create_app

    ports = [free_port(), free_port()]
    servers = [
        ServerThread(
            create_app(replace(cpu_settings, pod_name=f"pod-{i}",
                               work_root=cpu_settings.work_root / str(i)), bypass_auth),
            port,
        )
        for i, port in enumerate(ports)
    ]
    for s in servers:
        s.__enter__()
    try:
        yield [f"127.0.0.1:{p}" for p in ports]
    finally:
        for s in servers:
            s.__exit__(None, None, None)
