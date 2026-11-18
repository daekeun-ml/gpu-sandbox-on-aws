#!/usr/bin/env bash
# Verify one sandbox pool: scripts/ops/verify.sh <runtime> [version]
#   1. isolation evidence per pod (kernel seen inside the sandbox vs the node's kernel)
#   2. denial checks: instance metadata, Kubernetes API, the node's kubelet, the internet
#   3. golden verdicts through the authenticated API (from the trainer namespace)
#   4. an unauthenticated caller from another namespace is rejected by the NetworkPolicy
source "$(dirname "$0")/../lib.sh"
source "$(dirname "$0")/../lib_jobs.sh"
require_tools kubectl

runtime="${1:?usage: $0 <runtime> [version]}"
version="${2:-v1}"
selector="gpusandbox/runtime=${runtime},gpusandbox/version=${version}"
pod="$(kubectl -n sandbox get pods -l "${selector}" -o jsonpath='{.items[0].metadata.name}')"
[[ -n "${pod}" ]] || die "no pods for ${selector}"
node="$(kubectl -n sandbox get pod "${pod}" -o jsonpath='{.spec.nodeName}')"

log "1) kernel inside ${pod} vs node ${node}"
echo "  sandbox: $(kubectl -n sandbox exec "${pod}" -- uname -r)"
echo "  node:    $(kubectl get node "${node}" -o jsonpath='{.status.nodeInfo.kernelVersion}')"

log "2) egress from inside the sandbox must fail"
# A public AWS address, resolved here because the sandbox has no DNS.
public_ip="$(python3 -c "import socket; print(socket.gethostbyname('s3.${AWS_REGION}.amazonaws.com'))")"
kubectl -n sandbox exec "${pod}" -- env PUBLIC_IP="${public_ip}" python -c '
import os, socket
node_ip = os.environ.get("NODE_IP", "")
targets = [("169.254.169.254", 80, "instance metadata"),
           (os.environ.get("KUBERNETES_SERVICE_HOST", ""), 443, "kubernetes api"),
           (node_ip, 10250, "node kubelet"),
           (os.environ["PUBLIC_IP"], 443, "internet (S3 endpoint)")]
bad = 0
for host, port, label in targets:
    if not host:
        continue
    s = socket.socket(); s.settimeout(3)
    try:
        s.connect((host, port)); verdict = "REACHABLE"; bad += 1
    except ConnectionRefusedError:
        verdict = "REACHABLE (refused)"; bad += 1
    except OSError as exc:
        verdict = f"blocked ({type(exc).__name__})"
    finally:
        s.close()
    print(f"  {label:32s} {host}:{port:<6d} {verdict}")
raise SystemExit(1 if bad else 0)
' || die "a denial check failed: see docs/reference/troubleshooting.md"

log "3) golden verdicts via the authenticated API"
device="cuda"
[[ "${runtime}" == *-cpu ]] && device="cpu"
run_tool_job "probe-${runtime}-${version}" probe \
  --address "sandbox-${runtime}-${version}.sandbox.svc.cluster.local:8000" --device "${device}" \
  || die "probe reported failures"

log "4) a pod outside the trainer namespace cannot connect"
address="$(kubectl -n sandbox get pod "${pod}" -o jsonpath='{.status.podIP}')"
kubectl -n default run "np-check-$RANDOM" --rm -i --restart=Never --quiet \
  --image=public.ecr.aws/docker/library/python:3.14-slim -- \
  python -c "import socket; s=socket.socket(); s.settimeout(3); r=s.connect_ex(('${address}', 8000)); print('  connect from default ns:', 'REACHABLE' if r == 0 else f'blocked (errno {r})'); raise SystemExit(0 if r else 1)" \
  || die "NetworkPolicy did not block an outside caller"
log "pool sandbox-${runtime}-${version} verified"
