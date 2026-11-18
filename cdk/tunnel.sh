#!/usr/bin/env bash
# Reach the private EKS API endpoint from your workstation (CDK path): cdk/tunnel.sh [local_port]
#
# The CDK stack creates the cluster with the public endpoint off. This script forwards
# 127.0.0.1:<local_port> on your workstation to the private endpoint through an SSM Session
# Manager session on the stack's access instance (no inbound ports, no public IP), and points a
# kubeconfig context at it. Keep it running in its own terminal while you use kubectl or helm.
# Needs the Session Manager plugin for the AWS CLI.
source "$(dirname "$0")/../scripts/lib.sh"
require_tools aws kubectl session-manager-plugin
require_vars CLUSTER_NAME AWS_REGION

port="${1:-8443}"
stack="${CLUSTER_NAME}-cdk"
output() {
  aws cloudformation describe-stacks --region "${AWS_REGION}" --stack-name "${stack}" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}
endpoint="$(output ClusterEndpoint)"
instance="$(output AccessInstanceId)"
[[ -n "${endpoint}" && "${instance}" != "None" ]] || die "stack ${stack} has no outputs; run cdk/deploy.sh first"
host="${endpoint#https://}"

aws eks update-kubeconfig --region "${AWS_REGION}" --name "${CLUSTER_NAME}" --alias "${CLUSTER_NAME}-tunnel" >/dev/null
cluster_arn="$(aws eks describe-cluster --region "${AWS_REGION}" --name "${CLUSTER_NAME}" --query cluster.arn --output text)"
# Talk to the local end of the tunnel but verify the API server certificate for its real name.
kubectl config set-cluster "${cluster_arn}" --server "https://127.0.0.1:${port}" --tls-server-name "${host}" >/dev/null
log "kubectl context ${CLUSTER_NAME}-tunnel -> 127.0.0.1:${port} -> ${host} (via ${instance}); Ctrl-C closes it"
exec aws ssm start-session --region "${AWS_REGION}" --target "${instance}" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "host=${host},portNumber=443,localPortNumber=${port}"
