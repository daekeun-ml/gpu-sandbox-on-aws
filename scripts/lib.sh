#!/usr/bin/env bash
# Shared helpers. Source from the other scripts: source "$(dirname "$0")/lib.sh"
# (source "$(dirname "$0")/../lib.sh" from kata/, ops/, hyperpod/ and extensions/).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPO_ROOT

if [[ -f "${REPO_ROOT}/scripts/config.env" ]]; then
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/config.env"
else
  echo "scripts/config.env not found. Copy scripts/config.env.example and edit it." >&2
  exit 1
fi

log() { printf '\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

require_vars() {
  local name
  for name in "$@"; do
    [[ -n "${!name:-}" && "${!name}" != *__SET_ME__* ]] || die "set ${name} in scripts/config.env"
  done
}

require_tools() {
  local tool
  for tool in "$@"; do
    command -v "${tool}" >/dev/null 2>&1 || die "missing tool: ${tool}"
  done
}

# render <repo-relative template> [KEY=VALUE ...]: works from any working directory.
render() {
  local template="$1"; shift
  python3 "${REPO_ROOT}/scripts/render.py" "${REPO_ROOT}/${template}" "$@"
}

# Ask the operator to type a word before a destructive or expensive step.
confirm() {
  local expected="$1" prompt="$2" answer
  read -r -p "${prompt} Type '${expected}' to continue: " answer
  [[ "${answer}" == "${expected}" ]] || die "aborted"
}

account_id() { aws sts get-caller-identity --query Account --output text; }

ecr_registry() { echo "$(account_id).dkr.ecr.${AWS_REGION}.amazonaws.com"; }

oidc_issuer() {
  aws eks describe-cluster --name "${CLUSTER_NAME}" --region "${AWS_REGION}" \
    --query 'cluster.identity.oidc.issuer' --output text
}

wait_for_pods() {
  local ns="$1" selector="$2" timeout="${3:-600s}"
  kubectl -n "${ns}" wait --for=condition=Ready pod -l "${selector}" --timeout="${timeout}"
}
