#!/usr/bin/env bash
# Delete the CDK stack: cdk/destroy.sh [--yes]   (--yes skips the prompt; scripts/08_cleanup.sh asks first)
# Removes sandbox pools and jobs first if the tunnel is up, then the whole stack (cluster,
# node groups, VPC, access instance, log groups). The secrets KMS key enters its 7-day
# deletion window. ECR repositories from scripts/03_build_push_images.sh are not part of the stack.
source "$(dirname "$0")/../scripts/lib.sh"
require_tools aws cdk
require_vars CLUSTER_NAME AWS_REGION

[[ "${1:-}" == "--yes" ]] \
  || confirm "${CLUSTER_NAME}" "This deletes the CDK stack ${CLUSTER_NAME}-cdk in ${AWS_REGION} (cluster, nodes, VPC)."
if kubectl get namespace sandbox --request-timeout=5s >/dev/null 2>&1; then
  log "deleting sandbox pools and training jobs first"
  kubectl -n rl-trainer delete jobs --all --wait=true
  kubectl -n sandbox delete deployments,services --all --wait=true
else
  warn "cluster API not reachable (is cdk/tunnel.sh running?); the stack deletion removes the nodes anyway"
fi

# Settings are only needed for synth; destroy reads the deployed stack. The Kata switches are off
# here so that an incomplete GPU setting (WITH_KATA_GPU=1 without an AMI) cannot block deletion.
export SCENARIO="${SCENARIO:-A}" ADMIN_PRINCIPAL_ARN="${ADMIN_PRINCIPAL_ARN:-arn:aws:iam::000000000000:role/unused}"
export WITH_KATA_CPU=0 WITH_KATA_GPU=0
export AWS_REGION CDK_DEFAULT_REGION="${AWS_REGION}"
cd "$(dirname "$0")" || die "cannot enter the cdk directory"
cdk destroy "${CLUSTER_NAME}-cdk" --force
# The default-SG custom resource Lambda writes its own log group at run time, outside the stack.
for group in $(aws logs describe-log-groups --region "${AWS_REGION}" \
    --log-group-name-prefix "/aws/lambda/${CLUSTER_NAME}-cdk-" --query 'logGroups[].logGroupName' --output text); do
  log "deleting leftover log group ${group}"
  aws logs delete-log-group --region "${AWS_REGION}" --log-group-name "${group}"
done
log "remaining instances tagged project=gpu-sandbox-on-aws (should be none):"
aws ec2 describe-instances --region "${AWS_REGION}" \
  --filters "Name=tag:project,Values=gpu-sandbox-on-aws" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name]' --output table
log "ECR repositories are kept. To delete them:"
echo "  for r in sandbox trainer control; do aws ecr delete-repository --region ${AWS_REGION} --repository-name ${ECR_REPO_PREFIX:-gpu-sandbox}/\$r --force; done"
