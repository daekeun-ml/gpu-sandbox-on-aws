#!/usr/bin/env bash
# Copy the cluster's ServiceAccount issuer public keys (JWKS) into the sandbox namespace.
# Public keys, not secrets. Re-run if the API server rotates its signing keys; sandbox pods
# re-read the mounted file when it changes and reject all tokens while it is missing.
source "$(dirname "$0")/../lib.sh"
require_tools kubectl aws

issuer="$(oidc_issuer)"
jwks="$(mktemp)"
trap 'rm -f "${jwks}"' EXIT
kubectl get --raw /openid/v1/jwks > "${jwks}"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['keys'], 'empty JWKS'" "${jwks}"

kubectl -n sandbox create configmap sandbox-auth-jwks \
  --from-file=jwks.json="${jwks}" --from-literal=issuer="${issuer}" \
  --dry-run=client -o yaml | kubectl apply -f -
echo "issuer: ${issuer}"
