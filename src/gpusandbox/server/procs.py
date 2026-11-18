"""Process hygiene between evaluations.

Candidate code runs under the same UID as the server (there are no secrets in the pod to
protect). A candidate can still fork a daemon that outlives its evaluation and tampers with
the next one, so after every evaluation the server kills every process in the container's
PID namespace except itself and its ancestors (tini as PID 1).
"""

from __future__ import annotations

import logging
import os
import signal
from pathlib import Path

log = logging.getLogger(__name__)


def _ancestors(pid: int) -> set[int]:
    chain: set[int] = set()
    while pid > 0 and pid not in chain:
        chain.add(pid)
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
        except OSError:
            break
        # The command name may contain spaces; the parent PID is the second field after ')'.
        pid = int(stat.rsplit(")", 1)[1].split()[1])
    return chain


def reap_strays() -> int:
    """SIGKILL every process that is not this server or one of its ancestors.

    Returns the number of processes signalled. A no-op where /proc is unavailable (macOS).
    """
    proc = Path("/proc")
    if not proc.is_dir():
        return 0
    keep = _ancestors(os.getpid()) | {1}
    killed = 0
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid in keep:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except (ProcessLookupError, PermissionError):
            continue
    if killed:
        log.warning("reaped %d stray process(es) after evaluation", killed)
    return killed
