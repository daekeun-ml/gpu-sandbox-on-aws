#!/usr/bin/env bash
# Agent Sandbox extension: per-episode sandboxes claimed from warm pools.
#   scripts/extensions/agent_sandbox.sh install            controller + CRDs (pinned release), claim RBAC
#   scripts/extensions/agent_sandbox.sh pool <runtime> [n] SandboxTemplate + SandboxWarmPool
#   scripts/extensions/agent_sandbox.sh claim <runtime>    one claim, print its address, release
#   scripts/extensions/agent_sandbox.sh episodes <runtime> [episodes] [max_turns]
#       multi-turn episodes without a model: a Job claims one sandbox per episode and submits
#       golden kernels turn by turn (defaults: 2 episodes, 3 turns; max_turns 1 is single-turn)
# <runtime> is a profile from k8s/sandbox/profiles (gvisor, kata-qemu, kata-clh-cpu, ...).
source "$(dirname "$0")/../lib.sh"
source "$(dirname "$0")/../lib_jobs.sh"
require_tools kubectl

AGENT_SANDBOX_VERSION="${AGENT_SANDBOX_VERSION:-v1.0.11}"
EPISODE_SUBJECT="system:serviceaccount:rl-trainer:sandbox-episode"
cmd="${1:?usage: $0 install|pool|claim|episodes ...}"

case "${cmd}" in
  install)
    log "installing agent-sandbox ${AGENT_SANDBOX_VERSION} (controller + extensions)"
    kubectl apply -f "https://github.com/kubernetes-sigs/agent-sandbox/releases/download/${AGENT_SANDBOX_VERSION}/sandbox-with-extensions.yaml"
    kubectl get crd | grep agents.x-k8s.io
    # scripts/05_setup_namespaces_auth.sh applies this file too; again here so that the
    # sandbox-episode account exists even if that script ran before it was added (idempotent).
    kubectl apply -f "${REPO_ROOT}/k8s/base/trainer-rbac.yaml"
    kubectl apply -f "${REPO_ROOT}/k8s/extensions/agent-sandbox/trainer-claims-rbac.yaml"
    ;;
  pool)
    runtime="${2:?runtime}"
    export WARM_REPLICAS="${3:-1}"
    require_vars SANDBOX_IMAGE_URI SANDBOX_AUDIENCE
    # shellcheck disable=SC1090
    source "${REPO_ROOT}/k8s/sandbox/profiles/${runtime}.env"
    # shellcheck disable=SC1090
    source "${REPO_ROOT}/k8s/sandbox/versions/${VERSION_FILE:-v1}.env"
    OIDC_ISSUER="$(oidc_issuer)"
    # The trainer, the verification jobs and the episode Job may call claimed sandboxes.
    SANDBOX_ALLOWED_SUBJECTS="${SANDBOX_ALLOWED_SUBJECTS:-system:serviceaccount:rl-trainer:grpo-trainer,system:serviceaccount:rl-trainer:sandbox-probe,${EPISODE_SUBJECT}}"
    export OIDC_ISSUER SANDBOX_ALLOWED_SUBJECTS
    render k8s/extensions/agent-sandbox/template.yaml.tpl | kubectl apply -f -
    log "warm pool kernel-eval-${RUNTIME}: ${WARM_REPLICAS} sandbox(es); each holds its accelerator while idle"
    kubectl -n sandbox get sandboxwarmpool "kernel-eval-${RUNTIME}"
    ;;
  claim)
    runtime="${2:?runtime}"
    name="episode-check-$RANDOM"
    cat <<YAML | kubectl apply -f -
apiVersion: extensions.agents.x-k8s.io/v1beta1
kind: SandboxClaim
metadata: {name: ${name}, namespace: sandbox}
spec:
  warmPoolRef: {name: kernel-eval-${runtime}}
YAML
    kubectl -n sandbox wait --for=condition=Ready "sandboxclaim/${name}" --timeout=10m
    kubectl -n sandbox get sandboxclaim "${name}" -o jsonpath='{"sandbox: "}{.status.sandbox.name}{"  address: "}{.status.sandbox.serviceFQDN}{"\n"}'
    kubectl -n sandbox delete sandboxclaim "${name}"
    ;;
  episodes)
    runtime="${2:?runtime}"
    episodes="${3:-2}"
    max_turns="${4:-3}"
    pool="kernel-eval-${runtime}"
    kubectl get crd sandboxclaims.extensions.agents.x-k8s.io sandboxwarmpools.extensions.agents.x-k8s.io \
      >/dev/null 2>&1 || die "agent-sandbox CRDs not found: run $0 install"
    kubectl -n rl-trainer get serviceaccount sandbox-episode >/dev/null 2>&1 \
      || die "ServiceAccount rl-trainer/sandbox-episode not found: run $0 install"
    [[ "$(kubectl auth can-i create sandboxclaims.extensions.agents.x-k8s.io -n sandbox \
          --as="${EPISODE_SUBJECT}" 2>/dev/null)" == "yes" ]] \
      || die "${EPISODE_SUBJECT} may not create SandboxClaims: run $0 install"
    ready="$(kubectl -n sandbox get sandboxwarmpool "${pool}" -o jsonpath='{.status.readyReplicas}' 2>/dev/null)" \
      || die "warm pool ${pool} not found: run $0 pool ${runtime}"
    (( ${ready:-0} >= 1 )) || die "warm pool ${pool} has no Ready sandbox (kubectl -n sandbox get sandboxwarmpool ${pool})"
    # Warm sandboxes keep the env they started with (updateStrategy OnReplenish), so one started
    # before the episode account was allowed answers every episode with 403.
    pods="$(kubectl -n sandbox get pods -l "gpusandbox/managed-by=agent-sandbox,gpusandbox/runtime=${runtime}" \
      -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.containers[0].env[?(@.name=="SANDBOX_AUTH_ALLOWED_SUBJECTS")].value}{"\n"}{end}')"
    stale="$(grep -v -- "${EPISODE_SUBJECT}" <<<"${pods}" | cut -d' ' -f1 | xargs || true)"
    [[ -z "${stale}" ]] || die "sandboxes started without ${EPISODE_SUBJECT} in their allowlist: ${stale}. Run $0 pool ${runtime}, then delete them (kubectl -n sandbox delete sandboxes.agents.x-k8s.io <name>) so that the pool replaces them"
    device="cuda"
    [[ "${runtime}" == *-cpu ]] && device="cpu"
    (( episodes <= ready )) || warn "${ready} sandbox(es) Ready: later episodes wait for the pool to start replacements"

    # The Job name doubles as the run label on every claim it creates.
    name="episodes-$(date +%s)"
    log "${pool}: ${episodes} episode(s), up to ${max_turns} turn(s) each, device ${device}"
    status=0
    run_job_template k8s/extensions/agent-sandbox/job-multiturn.yaml.tpl "${name}" \
      multiturn --warm-pool "${pool}" --episodes "${episodes}" --max-turns "${max_turns}" \
      --device "${device}" --run-id "${name}" || status=$?
    # The Job deletes its own claims; this covers a pod that was killed before it could.
    kubectl -n sandbox delete sandboxclaim -l "gpusandbox/run=${name}" --ignore-not-found
    exit "${status}"
    ;;
  *)
    die "unknown command ${cmd}"
    ;;
esac
