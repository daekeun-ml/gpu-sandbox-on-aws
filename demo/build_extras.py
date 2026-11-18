"""Build demo/site/data/extras.json from the logs of a real cluster run, and check public data.

The replay demo shows, next to the golden recording (data/recording.json):
  - a benchmark comparison, parsed from the stdout of scripts/ops/bench.sh
  - reward batches and trainer metrics of a GRPO run, parsed from `kubectl logs` of the job
  - a sandbox version switch, parsed from the output of `python -m gpusandbox.tools simulate`
  - terminal transcripts (verify.sh, rollout.sh, the gVisor smoke test) replayed line by line

Every string is redacted (IP addresses, node host names, account IDs, ARNs, resource IDs)
and the result is scanned again before it is written. `--check FILE...` runs only the scan,
and demo/deploy.sh runs it on everything it uploads.

Usage (paths are examples):
  python3 demo/build_extras.py --out demo/site/data/extras.json \
      --source "Amazon EKS, us-west-2, 2026-11-18" \
      --bench-log pass1=bench.log --bench-pass pass2 \
      --node 'gvisor=g5.2xlarge|NVIDIA A10G' --node 'kata-qemu=g4dn.metal|Tesla T4' \
      --training-log grpo.log --training-source "..." --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
      --simulation-log simulate.log --simulation-source "..." \
      --transcript verify-gvisor=verify-gvisor.txt
  python3 demo/build_extras.py --check demo/site/data/recording.json demo/site/data/extras.json
"""

from __future__ import annotations

import argparse
import ast
import ipaddress
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[()][A-Za-z0-9]")
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?!\.?\d)")
# IPv6 candidates are validated with ipaddress, so clock times such as 13:37:42 are left alone.
IPV6 = re.compile(r"(?<![\w:])(?=[0-9A-Fa-f:]*:[0-9A-Fa-f:]*:)[0-9A-Fa-f:]{2,39}(?![\w:])")
NODE_NAME = re.compile(r"\bip-\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3}(?:\.[a-z0-9-]+)*(?:\.internal)?\b")
DASHED_IP = re.compile(r"(?<![\w-])\d{1,3}(?:-\d{1,3}){3}(?![\w-]*\d)")  # pod DNS: 10-0-12-34.ns.pod
AWS_HOST = re.compile(r"\b[\w.-]+\.amazonaws\.com(?:\.cn)?\b")  # EKS API, OIDC, ELB, ECR, S3 hosts
ACCOUNT = re.compile(r"(?<!\d)\d{12}(?!\d)")
ARN = re.compile(r"\barn:aws[a-z-]*:[^\s\"',)]+")
RESOURCE_ID = re.compile(
    r"\b(?:i|vol|vpc|subnet|sg|eni|ami|snap|nat|eipalloc|lt|cr|rtb|igw|vpce|acl|pcx|tgw|fs|lb)-[0-9a-f]{8,17}\b")
HEX_ID = re.compile(r"\b[0-9A-F]{32}\b")  # EKS OIDC issuer IDs
TOKEN = re.compile(r"\b(?:hf_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|(?:AKIA|ASIA)[A-Z0-9]{16})\b")
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(?:\.[A-Za-z0-9_-]*)?")
PROMPT = re.compile(r"^\S*\s*\S+@\S+:[^$#]*[$#]\s?")
# Well-known, non-identifying addresses that a reader needs to see.
ALLOWED_IPS = {"169.254.169.254", "127.0.0.1", "0.0.0.0"}

# What must never reach the public site, even after redaction.
FORBIDDEN = (
    (re.compile(r"\.internal\b"), "internal host name"),
    (NODE_NAME, "node host name"),
    (DASHED_IP, "IP address in a host name"),
    (re.compile(r"amazonaws\.com"), "AWS endpoint host name"),
    (re.compile(r"\barn:aws"), "ARN"),
    (ACCOUNT, "12-digit number (account ID?)"),
    (re.compile(r"[\w.-]+@[\w-]+"), "user@host or e-mail address"),
    (re.compile(r"/home/[^/\s]+|/root\b|/Users/[^/\s]+"), "home directory path"),
    (TOKEN, "access key ID or API token"),
    (JWT, "JWT"),
    (RESOURCE_ID, "AWS resource ID"),
    (HEX_ID, "32-character hex ID (EKS OIDC issuer?)"),
)

TIME_PREFIX = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\]")


def _mask_ip(match: re.Match[str]) -> str:
    text = match.group(0)
    if text in ALLOWED_IPS:
        return text
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return text
    return "<private-ip>" if ip.is_private else "<public-ip>"


def _ipv6(text: str) -> bool:
    try:
        ipaddress.IPv6Address(text)
    except ValueError:
        return False
    return True


def redact(text: str) -> str:
    text = ANSI.sub("", text).replace("\r", "")
    text = ARN.sub("<arn>", text)
    text = JWT.sub("<token>", text)
    text = TOKEN.sub("<token>", text)
    text = AWS_HOST.sub("<aws-endpoint>", text)
    text = NODE_NAME.sub("<node>", text)
    text = DASHED_IP.sub("<private-ip>", text)
    text = IPV4.sub(_mask_ip, text)
    text = IPV6.sub(lambda m: "<ipv6>" if _ipv6(m.group(0)) else m.group(0), text)
    text = ACCOUNT.sub("<account-id>", text)
    text = HEX_ID.sub("<id>", text)
    return RESOURCE_ID.sub("<resource-id>", text)


def _strings(value: Any, path: str = "$"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _strings(k, f"{path}.<key>")
            yield from _strings(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _strings(v, f"{path}[{i}]")


def problems(document: Any) -> list[str]:
    """Every string that still looks like an address, host name, account ID or secret."""
    found = []
    for path, text in _strings(document):
        for ip in IPV4.findall(text):
            if ip not in ALLOWED_IPS:
                found.append(f"{path}: IP address {ip}")
        for ip in IPV6.findall(text):
            if _ipv6(ip):
                found.append(f"{path}: IPv6 address {ip}")
        for pattern, what in FORBIDDEN:
            if pattern.search(text):
                found.append(f"{path}: {what}")
    return found


def _json_lines(path: str) -> list[dict[str, Any]]:
    events = []
    for line in Path(path).read_text(errors="replace").splitlines():
        line = ANSI.sub("", line).replace("\r", "").strip()
        if line.startswith("{\""):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def parse_bench(text: str) -> list[dict[str, Any]]:
    """Rows from the stdout of scripts/ops/bench.sh: cold start lines, then one JSON line per pool."""
    rows, cold, current = [], {}, None
    for raw in text.splitlines():
        line = ANSI.sub("", raw).replace("\r", "")
        m = re.search(r"\] ([\w-]+): cold start", line)
        if m:
            current = m.group(1)
            cold[current] = []
            continue
        m = re.match(r"^\s+\S+: (\d+)s$", line)
        if m and current:
            cold[current].append(int(m.group(1)))
            continue
        if line.strip().startswith("{\""):
            try:
                row = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            if "eval_p50_s" in row:
                row.pop("address", None)
                row["cold_start_s"] = cold.get(row["runtime"], [])
                rows.append(row)
    return rows


def split_bench_passes(path: str, labels: list[str]) -> dict[str, list[dict[str, Any]]]:
    """bench.log may hold several passes (`=== run N`); map them, in order, to labels."""
    text = ANSI.sub("", Path(path).read_text(errors="replace"))
    chunks = re.split(r"^=== run \d+.*$", text, flags=re.MULTILINE)[1:] or [text]
    return {label: parse_bench(chunk) for label, chunk in zip(labels, chunks)}


def parse_training_log(path: str) -> dict[str, Any]:
    """`kubectl logs` of a GRPO job: JSON events from the reward function plus trainer dicts."""
    batches, switches, steps = [], [], []
    for raw in Path(path).read_text(errors="replace").splitlines():
        line = ANSI.sub("", raw).replace("\r", "").strip()
        if line.startswith("{\""):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") == "reward_batch":
                batches.append(event)
            elif event.get("event") == "sandbox_version_switch":
                switches.append(event)
        elif line.startswith("{'loss'"):
            try:
                metrics = ast.literal_eval(line)
            except (ValueError, SyntaxError):
                continue
            keep = ("loss", "reward", "reward_std", "rewards/format_reward/mean",
                    "rewards/correctness_reward/mean", "rewards/speedup_reward/mean",
                    "completions/mean_length", "step_time")
            steps.append({k: float(metrics[k]) for k in keep if k in metrics})
    for i, step in enumerate(steps):
        step["step"] = i + 1
    return {"batches": batches, "switches": switches, "steps": steps}


def parse_transcript(path: str, *, line_gap_s: float = 0.12) -> list[dict[str, Any]]:
    """Lines with a time offset. `[HH:MM:SS]` prefixes set the clock; other lines follow closely."""
    lines, start, clock = [], None, 0.0
    for raw in Path(path).read_text(errors="replace").splitlines():
        text = ANSI.sub("", raw).replace("\r", "").rstrip()
        if PROMPT.match(text):
            command = PROMPT.sub("", text).strip()
            if not command:
                continue
            text = f"$ {command}"
        m = TIME_PREFIX.match(text)
        if m:
            seconds = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            start = seconds if start is None else start
            clock = max(clock + line_gap_s, float(seconds - start))
        else:
            clock += line_gap_s
        lines.append({"t": round(clock, 2), "text": redact(text)})
    return lines


def _redact_tree(value: Any) -> Any:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {k: _redact_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_tree(v) for v in value]
    return value


def _pairs(values: list[str], what: str) -> dict[str, str]:
    out = {}
    for item in values:
        if "=" not in item:
            raise SystemExit(f"{what} must be key=value: {item}")
        k, v = item.split("=", 1)
        out[k] = v
    return out


def build(args: argparse.Namespace) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema": "extras-1",
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": args.source,
    }
    nodes = {}
    for runtime, value in _pairs(args.node, "--node").items():
        instance, _, gpu = value.partition("|")
        nodes[runtime] = {"instance": instance, "gpu": gpu or None}
    if args.bench_log:
        label, _, path = args.bench_log.partition("=")
        labels = [label, *args.bench_pass]
        passes = split_bench_passes(path, labels)
        document["bench"] = {
            "requests": args.bench_requests,
            "passes": [{"label": k, "rows": [{**r, **nodes.get(r["runtime"], {})} for r in v]}
                       for k, v in passes.items()],
            "unmeasured": [],
        }
        for runtime, value in _pairs(args.unmeasured, "--unmeasured").items():
            instance, _, gpu = value.partition("|")
            document["bench"]["unmeasured"].append({"runtime": runtime, "instance": instance, "gpu": gpu or None})
    if args.training_log:
        document["training"] = {
            "source": args.training_source,
            "model": args.model,
            **parse_training_log(args.training_log),
        }
    if args.simulation_log:
        events = [e for e in _json_lines(args.simulation_log)
                  if e.get("event") in ("reward_batch", "sandbox_version_switch")]
        document["simulation"] = {"source": args.simulation_source, "events": events}
    transcripts = []
    for key, path in _pairs(args.transcript, "--transcript").items():
        transcripts.append({"id": key, "lines": parse_transcript(path)})
    document["transcripts"] = transcripts
    return _redact_tree(document)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="demo/build_extras.py", description=__doc__.splitlines()[0])
    p.add_argument("--check", nargs="+", metavar="FILE", help="only scan these JSON files")
    p.add_argument("--out")
    p.add_argument("--source", default="cluster run")
    p.add_argument("--bench-log", help="LABEL=path to the stdout of scripts/ops/bench.sh")
    p.add_argument("--bench-pass", action="append", default=[], help="label of a later pass in the same log")
    p.add_argument("--bench-requests", type=int, default=32)
    p.add_argument("--node", action="append", default=[], help="runtime=instance|gpu (repeatable)")
    p.add_argument("--unmeasured", action="append", default=[],
                   help="runtime=instance|gpu of a pool that was attempted but not measured")
    p.add_argument("--training-log", help="kubectl logs of the GRPO job")
    p.add_argument("--training-source", default="")
    p.add_argument("--model", default="")
    p.add_argument("--simulation-log", help="stdout of python -m gpusandbox.tools simulate")
    p.add_argument("--simulation-source", default="")
    p.add_argument("--transcript", action="append", default=[], help="id=path (repeatable)")
    args = p.parse_args(argv)

    if args.check:
        bad = []
        for path in args.check:
            bad += [f"{path}: {msg}" for msg in problems(json.loads(Path(path).read_text()))]
        for msg in bad:
            print(f"[check] {msg}", file=sys.stderr)
        print(f"[check] {len(args.check)} file(s), {len(bad)} problem(s)")
        return 1 if bad else 0

    if not args.out:
        p.error("--out is required unless --check is given")
    document = build(args)
    bad = problems(document)
    if bad:
        for msg in bad:
            print(f"[build] {msg}", file=sys.stderr)
        print("[build] refusing to write: fix the redaction rules or the input", file=sys.stderr)
        return 1
    Path(args.out).write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n")
    counts = {k: len(v) if isinstance(v, list) else 1 for k, v in document.items() if k in ("transcripts",)}
    print(json.dumps({"event": "extras", "out": args.out, **counts,
                      "bench": "bench" in document, "training": "training" in document,
                      "simulation": "simulation" in document}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
