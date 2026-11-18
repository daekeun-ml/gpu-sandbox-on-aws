#!/usr/bin/env bash
# Compare runtimes with the same golden kernel: scripts/ops/bench.sh [requests]
# For every deployed v1 pool: pod cold start (pod creation -> Ready), evaluation latency
# p50/p95, throughput and the measured speedup. Writes bench-<timestamp>.jsonl.
# GPU types differ between pools (gVisor on A10G, Kata on T4), so compare latency overhead
# within a GPU type and treat speedups as per-GPU numbers.
source "$(dirname "$0")/../lib.sh"
source "$(dirname "$0")/../lib_jobs.sh"
require_tools kubectl

requests="${1:-32}"
out="${REPO_ROOT}/bench-$(date +%Y%m%d-%H%M%S).jsonl"
for runtime in gvisor gvisor-hyperpod kata-qemu kata-clh gvisor-cpu kata-clh-cpu kata-qemu-cpu; do
  pods="$(kubectl -n sandbox get pods -l "gpusandbox/runtime=${runtime},gpusandbox/version=v1" -o name)"
  [[ -n "${pods}" ]] || continue
  log "${runtime}: cold start (creationTimestamp -> Ready)"
  kubectl -n sandbox get pods -l "gpusandbox/runtime=${runtime},gpusandbox/version=v1" -o json | python3 -c '
import json, sys
from datetime import datetime
fmt = "%Y-%m-%dT%H:%M:%SZ"
for p in json.load(sys.stdin)["items"]:
    ready = [c for c in p["status"].get("conditions", []) if c["type"] == "Ready" and c["status"] == "True"]
    if ready:
        name = p["metadata"]["name"]
        dt = datetime.strptime(ready[0]["lastTransitionTime"], fmt) - datetime.strptime(p["metadata"]["creationTimestamp"], fmt)
        print(f"  {name}: {dt.total_seconds():.0f}s")'
  golden="relu_bias_triton"
  [[ "${runtime}" == *-cpu ]] && golden="relu_bias_torch_only"
  log "${runtime}: ${requests} evaluations of ${golden}"
  run_tool_job "bench-${runtime}" bench \
    --address "sandbox-${runtime}-v1.sandbox.svc.cluster.local:8000" \
    --requests "${requests}" --golden "${golden}" | tee -a "${out}"
done
log "results: ${out}"
