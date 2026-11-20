#!/usr/bin/env bash
# Delete everything this asset created, in dependency order. Asks before each destructive step.
#   scripts/08_cleanup.sh            sandbox pools, jobs, the CDK stack, AMIs (asks)
#   scripts/08_cleanup.sh --images   also the ECR repositories
# Run scripts/hyperpod/delete.sh first if you created scenario B.
source "$(dirname "$0")/lib.sh"
require_tools aws cdk kubectl
require_vars CLUSTER_NAME AWS_REGION

require_cdk_lib   # check before anything is deleted; cdk/destroy.sh needs it
confirm "${CLUSTER_NAME}" "This deletes EKS cluster ${CLUSTER_NAME} in ${AWS_REGION} and its node groups."

# Sandbox pools, jobs, the CDK stack (cluster, node groups, VPC, access instance) and the
# custom-resource log group. Keep cdk/tunnel.sh running so that the workloads go first.
"${REPO_ROOT}/cdk/destroy.sh" --yes

if [[ -n "${KATA_IOMMU_AMI_ID:-}" ]]; then
  confirm "ami" "Deregister AMI ${KATA_IOMMU_AMI_ID} and delete its snapshot?"
  snapshot="$(aws ec2 describe-images --region "${AWS_REGION}" --image-ids "${KATA_IOMMU_AMI_ID}" \
    --query 'Images[0].BlockDeviceMappings[0].Ebs.SnapshotId' --output text)"
  aws ec2 deregister-image --region "${AWS_REGION}" --image-id "${KATA_IOMMU_AMI_ID}"
  [[ "${snapshot}" == snap-* ]] && aws ec2 delete-snapshot --region "${AWS_REGION}" --snapshot-id "${snapshot}"
fi

if [[ -n "${HYPERPOD_B2_AMI_ID:-}" ]]; then
  confirm "ami" "Deregister the B2 HyperPod AMI ${HYPERPOD_B2_AMI_ID} and delete its snapshot?"
  snapshot="$(aws ec2 describe-images --region "${AWS_REGION}" --image-ids "${HYPERPOD_B2_AMI_ID}" \
    --query 'Images[0].BlockDeviceMappings[0].Ebs.SnapshotId' --output text)"
  aws ec2 deregister-image --region "${AWS_REGION}" --image-id "${HYPERPOD_B2_AMI_ID}"
  [[ "${snapshot}" == snap-* ]] && aws ec2 delete-snapshot --region "${AWS_REGION}" --snapshot-id "${snapshot}"
fi

if [[ "${1:-}" == "--images" ]]; then
  confirm "images" "Delete the ECR repositories ${ECR_REPO_PREFIX}/{sandbox,trainer,control} and all images?"
  for name in sandbox trainer control; do
    aws ecr delete-repository --region "${AWS_REGION}" --repository-name "${ECR_REPO_PREFIX}/${name}" --force >/dev/null \
      && log "deleted ${ECR_REPO_PREFIX}/${name}"
  done
fi

log "remaining instances tagged project=gpu-sandbox-on-aws (should be none):"
aws ec2 describe-instances --region "${AWS_REGION}" \
  --filters "Name=tag:project,Values=gpu-sandbox-on-aws" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name]' --output table
