"""Operator tools that run inside the cluster (image: control).

  python -m gpusandbox.tools probe  --address <svc:port> [--device cuda]
      isolation evidence (/info of every pod) + golden verdicts; exit 1 on any surprise
  python -m gpusandbox.tools parity --baseline <svc:port> --candidate <svc:port>
      a new sandbox version must reproduce the baseline's verdicts before it takes traffic
  python -m gpusandbox.tools bench  --address <svc:port> --requests 32
      evaluation latency and measured speedup for one golden kernel, as JSON
  python -m gpusandbox.tools record --pool gvisor=<svc:port> [--pool kata-qemu=<svc:port>] --out rec.json
      run the golden set on each pool and write a recording for the replay demo (demo/site)
  python -m gpusandbox.tools simulate --steps 30 --interval-s 20 [--device cpu]
      a reward loop without a model or a GPU: golden submissions stand in for completions and
      are scored batch by batch through the routing table, so a sandbox version switch shows
      up exactly as it would during training (scenario C)
  python -m gpusandbox.tools multiturn --warm-pool kernel-eval-<runtime> --episodes 2 --max-turns 3
      multi-turn episodes without a model: each episode claims one warm sandbox (Agent Sandbox),
      submits golden kernels turn by turn with feedback in between, and is scored by its final
      submission; needs a Kubernetes API token with the sandbox-claims Role
  python -m gpusandbox.tools sync-jwks --namespace sandbox
      copy the ServiceAccount issuer public keys into the sandbox-auth-jwks ConfigMap
      (run as a CronJob so that sandbox pods follow signing-key rotation)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import statistics
import sys
import time
from types import SimpleNamespace
from typing import Any

import httpx

from gpusandbox.auth import read_token
from gpusandbox.client.pool import EndpointResolver, SandboxPool
from gpusandbox.golden import GOLDEN_SET, Golden, golden_for


def _token_headers() -> dict[str, str]:
    token = read_token(os.environ.get("SANDBOX_TOKEN_FILE"))
    return {"Authorization": f"Bearer {token}"} if token else {}


async def _run_golden(address: str, goldens: tuple[Golden, ...]) -> dict[str, dict[str, Any]]:
    pool = SandboxPool(address, token_file=os.environ.get("SANDBOX_TOKEN_FILE"))
    try:
        results = await asyncio.gather(
            *(pool.evaluate({"task_id": g.task_id, "code": g.code, "request_id": g.name}) for g in goldens)
        )
    finally:
        await pool.aclose()
    return {g.name: r for g, r in zip(goldens, results)}


def _check(golden: Golden, result: dict[str, Any]) -> str | None:
    status = result.get("status")
    if status != golden.expect_status:
        return f"expected {golden.expect_status}, got {status}: {str(result.get('error', ''))[:200]}"
    if golden.expect_custom_kernel is not None and status == "ok":
        if bool(result.get("custom_kernel")) != golden.expect_custom_kernel:
            return f"expected custom_kernel={golden.expect_custom_kernel}"
    return None


async def probe(address: str, device: str) -> int:
    failures = 0
    endpoints = await EndpointResolver(address).endpoints()
    if not endpoints:
        print(f"no ready endpoints behind {address}")
        return 1
    async with httpx.AsyncClient(timeout=30) as http:
        for ep in endpoints:
            info = (await http.get(f"http://{ep}/info", headers=_token_headers())).json()
            device_info = info.get("device", {})
            print(json.dumps({
                "endpoint": ep,
                "pod": info.get("pod"),
                "runtime": info.get("runtime"),
                "version": info.get("sandbox_version"),
                "kernel_release": info.get("kernel_release"),
                "gpu": device_info.get("name"),
                "egress_blocked": info.get("egress_blocked"),
            }))
            if not info.get("egress_blocked"):
                failures += 1
    results = await _run_golden(address, golden_for(device))
    for golden in golden_for(device):
        problem = _check(golden, results[golden.name])
        mark = "PASS" if problem is None else "FAIL"
        failures += problem is not None
        speed = results[golden.name].get("speedup")
        print(f"{mark} {golden.name:28s} status={results[golden.name].get('status'):17s} "
              f"speedup={speed} {problem or ''}")
    return 1 if failures else 0


async def parity(baseline: str, candidate: str, device: str, tolerance: float) -> int:
    goldens = golden_for(device)
    base, cand = await asyncio.gather(_run_golden(baseline, goldens), _run_golden(candidate, goldens))
    failures = 0
    for golden in goldens:
        b, c = base[golden.name], cand[golden.name]
        problems = [p for p in (_check(golden, b), _check(golden, c)) if p]
        if b.get("status") != c.get("status"):
            problems.append(f"status changed {b.get('status')} -> {c.get('status')}")
        if b.get("status") == c.get("status") == "ok" and b.get("speedup") and c.get("speedup"):
            ratio = float(c["speedup"]) / float(b["speedup"])
            if abs(ratio - 1.0) > tolerance:
                problems.append(f"speedup moved {b['speedup']} -> {c['speedup']}")
        failures += bool(problems)
        print(f"{'PASS' if not problems else 'FAIL'} {golden.name:28s} "
              f"{b.get('sandbox_version')}={b.get('status')} {c.get('sandbox_version')}={c.get('status')} "
              f"{'; '.join(problems)}")
    print(json.dumps({"event": "parity", "baseline": baseline, "candidate": candidate,
                      "passed": failures == 0}))
    return 1 if failures else 0


async def bench(address: str, requests: int, name: str) -> int:
    golden = next(g for g in GOLDEN_SET if g.name == name)
    pool = SandboxPool(address, token_file=os.environ.get("SANDBOX_TOKEN_FILE"))
    item = {"task_id": golden.task_id, "code": golden.code}
    started = time.monotonic()
    try:
        results = await asyncio.gather(*(pool.evaluate(dict(item)) for _ in range(requests)))
    finally:
        await pool.aclose()
    wall = time.monotonic() - started
    ok = [r for r in results if r.get("status") == "ok"]
    durations = sorted(float(r["duration_s"]) for r in ok if r.get("duration_s"))
    speedups = [float(r["speedup"]) for r in ok if r.get("speedup")]
    report = {
        "address": address,
        "golden": name,
        "runtime": ok[0].get("runtime") if ok else None,
        "requests": requests,
        "ok": len(ok),
        "throughput_eval_per_s": round(len(ok) / wall, 3),
        "eval_p50_s": round(statistics.median(durations), 3) if durations else None,
        "eval_p95_s": round(durations[max(0, int(len(durations) * 0.95) - 1)], 3) if durations else None,
        "speedup_median": round(statistics.median(speedups), 3) if speedups else None,
        "ref_ms_median": round(statistics.median(float(r["ref_ms"]) for r in ok), 4) if ok else None,
    }
    print(json.dumps(report))
    return 0 if ok else 1


def _short(value: Any, limit: int = 400) -> Any:
    return value[-limit:] if isinstance(value, str) else value


async def record(
    pools: list[tuple[str, str]],
    *,
    device: str,
    source: str,
    out: str,
    training_events: str | None = None,
) -> int:
    """Run the golden set on every pool and write a JSON recording for the replay demo.

    Only verdict fields, isolation evidence and reward components are kept; error text is
    truncated. The demo renders every string as text, never as HTML.
    """
    from datetime import datetime, timezone

    from gpusandbox.rewards import score_verdict
    from gpusandbox.tasks import get_task

    goldens = golden_for(device)
    keep = ("status", "correct", "custom_kernel", "uses_triton", "speedup", "ref_ms", "cand_ms",
            "flags", "violations", "error", "duration_s", "sandbox_version", "harness_version", "runtime")
    recorded_pools = []
    async with httpx.AsyncClient(timeout=30) as http:
        for runtime, address in pools:
            endpoints = await EndpointResolver(address).endpoints()
            info = {}
            if endpoints:
                raw = (await http.get(f"http://{endpoints[0]}/info", headers=_token_headers())).json()
                info = {
                    "runtime": raw.get("runtime"),
                    "sandbox_version": raw.get("sandbox_version"),
                    "kernel_release": raw.get("kernel_release"),
                    "gpu": (raw.get("device") or {}).get("name"),
                    "egress_blocked": raw.get("egress_blocked"),
                }
            verdicts = await _run_golden(address, goldens)
            results = {}
            for golden in goldens:
                verdict = {k: _short(verdicts[golden.name].get(k)) for k in keep}
                verdict["violations"] = (verdict.get("violations") or [])[:3]
                verdict["reward"] = score_verdict(verdicts[golden.name], golden.code)
                verdict["expected_status"] = golden.expect_status
                results[golden.name] = verdict
            recorded_pools.append({"runtime": runtime, "info": info, "results": results})

    events = []
    if training_events:
        with open(training_events) as fh:
            for line in fh:
                event = json.loads(line)
                if event.get("event") in ("reward_batch", "sandbox_version_switch"):
                    events.append(event)
    task_ids = sorted({g.task_id for g in goldens})
    document = {
        "schema": 1,
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "device": device,
        "tasks": {
            t: {"description": get_task(t).description, "input_spec": get_task(t).input_spec,
                "reference": get_task(t).reference_source}
            for t in task_ids
        },
        "goldens": [
            {"name": g.name, "task_id": g.task_id, "code": g.code, "expect_status": g.expect_status}
            for g in goldens
        ],
        "pools": recorded_pools,
        "training": events,
    }
    with open(out, "w") as fh:
        json.dump(document, fh, indent=1)
    print(json.dumps({"event": "recorded", "out": out, "pools": [p for p, _ in pools],
                      "goldens": len(goldens), "training_events": len(events)}))
    return 0


def simulate(*, steps: int, interval_s: float, device: str, runtime: str | None = None,
             routing: Any = None) -> int:
    """Score golden submissions batch by batch through the live routing table.

    Not training: there is no model and no gradient. It exercises the same reward path as the
    trainer (KernelRewards, one routing snapshot per batch) so that the reward_batch and
    sandbox_version_switch events can be watched on a cluster without GPUs.
    """
    from gpusandbox.client import RoutingTable, SandboxClient
    from gpusandbox.rewards import KernelRewards

    table = routing or RoutingTable.from_env()
    rewards = KernelRewards(SandboxClient(table), require_triton=(device == "cuda"), runtime=runtime)
    goldens = golden_for(device)
    prompts = [[{"role": "user", "content": g.task_id}] for g in goldens]
    task_ids = [g.task_id for g in goldens]
    print(json.dumps({"event": "simulate", "steps": steps, "device": device,
                      "note": "golden submissions stand in for model completions; this is not training"}),
          flush=True)

    state = SimpleNamespace(global_step=0)  # stands in for TRL's trainer_state
    for step in range(1, steps + 1):
        state.global_step = step
        # A per-step comment gives every batch fresh cache keys, as new completions would.
        completions = [
            [{"role": "assistant", "content": f"```python\n{g.code.rstrip()}\n# step {step}\n```"}]
            for g in goldens
        ]
        rewards.correctness_reward(prompts, completions, task_id=task_ids, trainer_state=state)
        if step < steps:
            time.sleep(interval_s)
    return 0


def multiturn(*, warm_pool: str, episodes: int, max_turns: int, device: str, task: str,
              run_id: str | None = None, api: Any = None) -> int:
    """Scripted multi-turn episodes, each in its own claimed sandbox, then a summary event.

    Exit 1 if a turn did not return the verdict its golden expects, a sandbox_error occurred,
    or an episode's turns were answered by more than one pod.
    """
    from gpusandbox.agent_sandbox import EpisodeSandbox
    from gpusandbox.client import BackgroundLoop
    from gpusandbox.multiturn import ScriptedPolicy, emit_json, run_episode, summarize

    policy = ScriptedPolicy(device)
    script = policy.script(task)
    loop = BackgroundLoop()  # one loop thread for all episodes
    # The run label lets the caller delete leftover claims if this process is killed.
    labels = {"gpusandbox/run": run_id} if run_id else {}

    def open_sandbox() -> EpisodeSandbox:
        return EpisodeSandbox(warm_pool, token_file=os.environ.get("SANDBOX_TOKEN_FILE"),
                              labels=labels, api=api, loop=loop)

    emit_json({"event": "multiturn", "warm_pool": warm_pool, "episodes": episodes,
               "max_turns": max_turns, "device": device, "task_id": task, "policy": policy.name,
               "script": [g.name for g in script],
               "note": "golden submissions stand in for an agent; this is not training"})
    results = [
        run_episode(open_sandbox, policy, episode=i, task_id=task, max_turns=max_turns,
                    require_triton=(device == "cuda"))
        for i in range(1, episodes + 1)
    ]
    unexpected = [
        {"episode": r.episode, "turn": t.turn, "golden": policy.entry(task, t.turn).name,
         "problem": problem}
        for r in results for t in r.turns
        if (problem := _check(policy.entry(task, t.turn), t.verdict))
    ]
    summary = {**summarize(results), "unexpected": unexpected}
    emit_json(summary)
    ok = not unexpected and not summary["sandbox_errors"] and summary["one_sandbox_per_episode"]
    return 0 if ok else 1


def sync_jwks(namespace: str, name: str = "sandbox-auth-jwks") -> int:
    """Refresh the JWKS ConfigMap from the API server's issuer discovery endpoint."""
    from kubernetes import client, config

    config.load_incluster_config()
    api_client = client.ApiClient()
    response = api_client.call_api(
        "/openid/v1/jwks", "GET", auth_settings=["BearerToken"], _preload_content=False
    )[0]
    document = json.loads(response.data)
    if not document.get("keys"):
        print("refusing to publish an empty key set")
        return 1
    body = {"data": {"jwks.json": json.dumps(document)}}
    client.CoreV1Api().patch_namespaced_config_map(name, namespace, body)
    print(json.dumps({"event": "jwks_synced", "keys": [k.get("kid") for k in document["keys"]]}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gpusandbox.tools")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe")
    p.add_argument("--address", required=True)
    p.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    q = sub.add_parser("parity")
    q.add_argument("--baseline", required=True)
    q.add_argument("--candidate", required=True)
    q.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    q.add_argument("--speedup-tolerance", type=float, default=0.35)
    b = sub.add_parser("bench")
    b.add_argument("--address", required=True)
    b.add_argument("--requests", type=int, default=32)
    b.add_argument("--golden", default="relu_bias_triton")
    r = sub.add_parser("record")
    r.add_argument("--pool", action="append", required=True, help="runtime=host:port (repeatable)")
    r.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    r.add_argument("--source", default="cluster recording")
    r.add_argument("--out", required=True)
    r.add_argument("--training-events", help="sandbox_metrics.jsonl from a training run")
    m = sub.add_parser("simulate")
    m.add_argument("--steps", type=int, default=30)
    m.add_argument("--interval-s", type=float, default=20.0)
    m.add_argument("--device", default="cpu", choices=["cuda", "cpu"])
    m.add_argument("--runtime", default=None, help="override the active runtime")
    e = sub.add_parser("multiturn")
    e.add_argument("--warm-pool", required=True, help="SandboxWarmPool name, kernel-eval-<runtime>")
    e.add_argument("--episodes", type=int, default=2)
    e.add_argument("--max-turns", type=int, default=3)
    e.add_argument("--device", default="cpu", choices=["cuda", "cpu"])
    e.add_argument("--task", default="relu_bias", help="task with a scripted episode")
    e.add_argument("--run-id", default=None, help="label value gpusandbox/run on every claim")
    j = sub.add_parser("sync-jwks")
    j.add_argument("--namespace", default="sandbox")
    args = parser.parse_args(argv)
    if args.cmd == "sync-jwks":
        return sync_jwks(args.namespace)
    if args.cmd == "multiturn":
        from gpusandbox.multiturn import ScriptedPolicy

        if args.episodes < 1 or args.max_turns < 1:
            parser.error("--episodes and --max-turns must be at least 1")
        if args.task not in ScriptedPolicy(args.device).scripts:
            parser.error(f"no scripted episode for {args.task} on {args.device}; "
                         f"choose from {sorted(ScriptedPolicy(args.device).scripts)}")
        # Job deletion and pod eviction send SIGTERM. Leaving through SystemExit runs the
        # EpisodeSandbox context managers, so claims are deleted now, not at shutdownTime.
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(128 + signal.SIGTERM))
        return multiturn(warm_pool=args.warm_pool, episodes=args.episodes, max_turns=args.max_turns,
                         device=args.device, task=args.task, run_id=args.run_id)
    if args.cmd == "simulate":
        return simulate(steps=args.steps, interval_s=args.interval_s, device=args.device,
                        runtime=args.runtime)
    if args.cmd == "record":
        pools = [tuple(p.split("=", 1)) for p in args.pool]
        return asyncio.run(record(pools, device=args.device, source=args.source, out=args.out,
                                  training_events=args.training_events))
    if args.cmd == "probe":
        return asyncio.run(probe(args.address, args.device))
    if args.cmd == "parity":
        return asyncio.run(parity(args.baseline, args.candidate, args.device, args.speedup_tolerance))
    return asyncio.run(bench(args.address, args.requests, args.golden))


if __name__ == "__main__":
    sys.exit(main())
