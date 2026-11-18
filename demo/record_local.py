"""Produce the sample recording shipped with the replay demo, on a laptop, without AWS.

What it runs (all on 127.0.0.1, CPU only, no isolation runtime):
  * two sandbox servers, v1 and v2 (the v2 harness uses 5 seeds and a 10x speedup cap);
  * the golden set against both, through the same code path the cluster uses;
  * six reward batches through KernelRewards with golden submissions standing in for model
    completions, switching the routing table from v1 to v2 after batch three.

Every number in the output is real for this setup and labelled as such; replace the file with
`python -m gpusandbox.tools record ...` output from your cluster to show GPU results.

    python demo/record_local.py --out demo/site/data/recording.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import tempfile
import threading
import time
from dataclasses import replace
from pathlib import Path


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start(app, port: int):
    import uvicorn

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    return server, thread


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="demo/site/data/recording.json")
    args = parser.parse_args()

    from gpusandbox.auth import AuthConfig
    from gpusandbox.client import RoutingTable, SandboxClient
    from gpusandbox.golden import golden_for
    from gpusandbox.rewards import KernelRewards
    from gpusandbox.server.app import Settings, create_app
    from gpusandbox.tools import record

    work = Path(tempfile.mkdtemp(prefix="gsb-demo-"))
    # Loopback-only smoke servers: the test bypass never leaves this process.
    bypass = AuthConfig(audience="", issuer="", allowed_subjects=frozenset(), jwks_file=None, test_bypass=True)
    base = Settings(runtime="local-cpu", device="cpu", size="smoke", work_root=work, seeds=3,
                    warmup=1, iters=5, eval_timeout_s=30, pod_name="laptop")
    versions = {
        "v1": replace(base, version="v1", work_root=work / "v1"),
        "v2": replace(base, version="v2", work_root=work / "v2", seeds=5, max_speedup=10.0),
    }
    servers, addresses = [], {}
    for name, settings in versions.items():
        port = _free_port()
        servers.append(_start(create_app(settings, bypass), port))
        addresses[name] = f"127.0.0.1:{port}"

    routing_file = work / "routing.json"

    def route(version: str) -> None:
        routing_file.write_text(json.dumps({
            "active": {"runtime": "local-cpu", "version": version},
            "pools": {"local-cpu": addresses},
        }))
        future = time.time() + 5
        os.utime(routing_file, (future, future))

    route("v1")
    metrics = work / "metrics.jsonl"
    rewards = KernelRewards(SandboxClient(RoutingTable(routing_file, min_reload_interval_s=0)),
                            require_triton=False, metrics_file=metrics)
    goldens = golden_for("cpu")
    prompts = [[{"role": "user", "content": g.task_id}] for g in goldens]
    task_ids = [g.task_id for g in goldens]

    class Step:  # stands in for TRL's trainer_state
        global_step = 0

    for batch in range(6):
        if batch == 3:
            route("v2")
        Step.global_step = batch + 1
        # A distinct trailing comment per batch keeps the reward cache from short-circuiting.
        completions = [[{"role": "assistant", "content": f"```python\n{g.code}# batch {batch}\n```"}]
                       for g in goldens]
        rewards.correctness_reward(prompts, completions, task_id=task_ids, trainer_state=Step)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(record(
        [("local-cpu v1", addresses["v1"]), ("local-cpu v2", addresses["v2"])],
        device="cpu",
        source="Local CPU smoke run on a laptop (127.0.0.1, no gVisor or Kata, no GPU). "
               "Golden submissions stand in for model completions.",
        out=str(out),
        training_events=str(metrics),
    ))
    for server, thread in servers:
        server.should_exit = True
        thread.join(timeout=10)


if __name__ == "__main__":
    main()
