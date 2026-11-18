"""Routing table: which sandbox pool (runtime, version) the trainer should use right now.

The table is a JSON document, normally a ConfigMap mounted as a directory (a subPath mount
does not receive updates). Operators switch versions by patching the ConfigMap; the trainer
re-reads it and takes one snapshot per reward batch, so every completion of a GRPO group is
scored by the same sandbox version.

Example::

    {
      "active": {"runtime": "gvisor", "version": "v1"},
      "pools": {
        "gvisor":    {"v1": "sandbox-gvisor-v1.sandbox.svc.cluster.local:8000"},
        "kata-clh":  {"v1": "sandbox-kata-clh-v1.sandbox.svc.cluster.local:8000"},
        "kata-qemu": {"v1": "sandbox-kata-qemu-v1.sandbox.svc.cluster.local:8000"}
      }
    }
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RoutingSnapshot:
    runtime: str
    version: str
    address: str
    revision: int  # increases every time the table content changes
    taken_at: float


class RoutingError(RuntimeError):
    pass


class RoutingTable:
    """Thread-safe view of the routing document with change detection (``revision``)."""

    def __init__(
        self,
        path: str | os.PathLike[str] | None = None,
        *,
        document: dict[str, Any] | None = None,
        min_reload_interval_s: float = 2.0,
    ) -> None:
        if (path is None) == (document is None):
            raise ValueError("pass exactly one of path or document")
        self._path = Path(path) if path is not None else None
        self._document = document
        self._min_reload = min_reload_interval_s
        self._lock = threading.Lock()
        self._loaded_raw: str | None = None
        self._revision = 0
        self._last_check = 0.0

    @classmethod
    def from_env(cls) -> RoutingTable:
        path = os.environ.get("SANDBOX_ROUTING_FILE")
        if path:
            return cls(path)
        address = os.environ.get("SANDBOX_ADDRESS")
        if address:
            runtime = os.environ.get("SANDBOX_RUNTIME", "gvisor")
            version = os.environ.get("SANDBOX_VERSION", "v1")
            return cls(
                document={
                    "active": {"runtime": runtime, "version": version},
                    "pools": {runtime: {version: address}},
                }
            )
        raise RoutingError("set SANDBOX_ROUTING_FILE or SANDBOX_ADDRESS")

    def _current_document(self) -> dict[str, Any]:
        if self._document is not None:
            if self._loaded_raw is None:
                self._loaded_raw = json.dumps(self._document, sort_keys=True)
                self._revision = 1
            return self._document
        assert self._path is not None
        now = time.monotonic()
        if self._loaded_raw is not None and now - self._last_check < self._min_reload:
            return json.loads(self._loaded_raw)
        self._last_check = now
        try:
            raw = self._path.read_text()
            parsed = json.loads(raw)
        except (OSError, ValueError) as exc:
            if self._loaded_raw is None:
                raise RoutingError(f"cannot read routing table {self._path}: {exc}") from exc
            # Keep the last good table while a ConfigMap update is being written.
            return json.loads(self._loaded_raw)
        normalized = json.dumps(parsed, sort_keys=True)
        if normalized != self._loaded_raw:
            self._loaded_raw = normalized
            self._revision += 1
        return parsed

    def snapshot(self, runtime: str | None = None) -> RoutingSnapshot:
        with self._lock:
            doc = self._current_document()
            revision = self._revision
        active = doc.get("active") or {}
        rt = runtime or active.get("runtime")
        version = active.get("version")
        if not rt or not version:
            raise RoutingError("routing table has no active runtime/version")
        pools = doc.get("pools") or {}
        address = (pools.get(rt) or {}).get(version)
        if not address:
            raise RoutingError(f"no pool for runtime={rt!r} version={version!r}")
        return RoutingSnapshot(
            runtime=rt, version=version, address=address, revision=revision, taken_at=time.time()
        )
