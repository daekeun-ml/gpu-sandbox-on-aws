#!/usr/bin/env bash
# Namespaces (Pod Security), NetworkPolicies, identities, the sandbox auth key set and the
# routing table. Safe to re-run.
#
# Authentication: callers present a projected ServiceAccount token with audience
# ${SANDBOX_AUDIENCE}. Sandbox pods verify it offline against the cluster's ServiceAccount
# issuer public keys (JWKS), so they hold no secrets and need no Kubernetes API access.
source "$(dirname "$0")/lib.sh"
require_tools kubectl
require_vars CLUSTER_NAME AWS_REGION SANDBOX_AUDIENCE

kubectl apply -f "${REPO_ROOT}/k8s/base/namespaces.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/base/trainer-rbac.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/base/networkpolicies.yaml"

log "publishing the ServiceAccount issuer keys to the sandbox namespace"
"${REPO_ROOT}/scripts/ops/sync_jwks.sh"

log "routing table: active runtime ${ACTIVE_RUNTIME:-gvisor}, version ${ACTIVE_VERSION:-v1}"
render k8s/base/routing.json.tpl \
  ACTIVE_RUNTIME="${ACTIVE_RUNTIME:-gvisor}" ACTIVE_VERSION="${ACTIVE_VERSION:-v1}" \
  > "${REPO_ROOT}/.routing.json"
kubectl -n rl-trainer create configmap sandbox-routing \
  --from-file=routing.json="${REPO_ROOT}/.routing.json" --dry-run=client -o yaml | kubectl apply -f -
rm -f "${REPO_ROOT}/.routing.json"
kubectl -n rl-trainer get configmap sandbox-routing -o jsonpath='{.data.routing\.json}' | head -3
