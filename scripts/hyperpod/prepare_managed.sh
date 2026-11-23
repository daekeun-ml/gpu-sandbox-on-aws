#!/usr/bin/env bash
# Configure the EKS add-ons used by the B2 lab after the HyperPod wizard stack is ready.
source "$(dirname "$0")/../lib.sh"
require_tools aws kubectl jq
require_vars AWS_REGION CLUSTER_NAME HYPERPOD_CLUSTER_NAME
export AWS_DEFAULT_OUTPUT=json
cluster="$(aws eks describe-cluster --region "${AWS_REGION}" --name "${CLUSTER_NAME}")"
orchestrator="$(aws sagemaker describe-cluster --region "${AWS_REGION}" --cluster-name "${HYPERPOD_CLUSTER_NAME}" \
  --query Orchestrator.Eks.ClusterArn --output text)"
issuer="$(kubectl get --raw /.well-known/openid-configuration | jq -r .issuer)"
[[ "${orchestrator}" == "$(jq -r .cluster.arn <<<"${cluster}")" &&
   "${issuer}" == "$(jq -r .cluster.identity.oidc.issuer <<<"${cluster}")" ]] \
  || die "the current kubectl context and the HyperPod orchestrator must both refer to ${CLUSTER_NAME}"

eks() { aws eks "$@" --region "${AWS_REGION}" --cluster-name "${CLUSTER_NAME}"; }
set_addon_config() {
  local name="$1" filter="$2" current wanted
  current="$(eks describe-addon --addon-name "${name}" | jq -c '(.addon.configurationValues // "{}") | fromjson')"
  wanted="$(jq -c "${filter}" <<<"${current}")"
  if ! jq -en --argjson a "${current}" --argjson b "${wanted}" '$a == $b' >/dev/null; then
    eks update-addon --addon-name "${name}" --configuration-values "${wanted}" --resolve-conflicts PRESERVE >/dev/null
  fi
  eks wait addon-active --addon-name "${name}"
}

set_addon_config vpc-cni '.enableNetworkPolicy = "true"'
set_addon_config coredns '.nodeSelector["gpusandbox/role"] = "system"'
kubectl -n kube-system rollout status ds/aws-node --timeout=10m
kubectl -n kube-system rollout status deployment/coredns --timeout=10m

if ! kubectl get crd certificates.cert-manager.io >/dev/null 2>&1; then
  if ! eks list-addons | jq -e '.addons | index("cert-manager") != null' >/dev/null; then
    eks create-addon --addon-name cert-manager >/dev/null
  fi
  eks wait addon-active --addon-name cert-manager
  kubectl -n cert-manager rollout status deployment/cert-manager-webhook --timeout=5m
fi
kubectl wait --for=condition=Established crd/certificates.cert-manager.io --timeout=5m

operator=amazon-sagemaker-hyperpod-training-operator
addon="$(eks describe-addon --addon-name "${operator}")"
if jq -e '.addon.status == "CREATE_FAILED" and any(.addon.health.issues[]?;
    .code == "K8sResourceNotFound" and (.message | contains("cert-manager")))' <<<"${addon}" >/dev/null; then
  # The wizard sets up the operator's Pod Identity as a separate association.
  # Keep custom associations on installations that assigned them directly to the add-on.
  options=(--addon-version "$(jq -r .addon.addonVersion <<<"${addon}")")
  config="$(jq -r '.addon.configurationValues // empty' <<<"${addon}")"
  role="$(jq -r '.addon.serviceAccountRoleArn // empty' <<<"${addon}")"
  namespace="$(jq -r '.addon.namespaceConfig.namespace // empty' <<<"${addon}")"
  [[ -z "${config}" ]] || options+=(--configuration-values "${config}")
  [[ -z "${role}" ]] || options+=(--service-account-role-arn "${role}")
  [[ -z "${namespace}" ]] || options+=(--namespace-config "namespace=${namespace}")
  eks delete-addon --addon-name "${operator}" --preserve >/dev/null
  eks wait addon-deleted --addon-name "${operator}"
  eks create-addon --addon-name "${operator}" --resolve-conflicts OVERWRITE "${options[@]}" >/dev/null
fi
eks wait addon-active --addon-name "${operator}"
eks describe-addon --addon-name "${operator}" --query 'addon.[addonVersion,status]' --output text
