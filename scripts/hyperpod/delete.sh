#!/usr/bin/env bash
# Delete the HyperPod cluster, its execution role and the lifecycle-script bucket.
# The EKS cluster stays; delete it afterwards with scripts/08_cleanup.sh.
source "$(dirname "$0")/../lib.sh"
require_tools aws kubectl
require_vars AWS_REGION HYPERPOD_CLUSTER_NAME HYPERPOD_LCS_BUCKET

confirm "${HYPERPOD_CLUSTER_NAME}" "This deletes HyperPod cluster ${HYPERPOD_CLUSTER_NAME} and its instances."

# The training operator add-on may never have been installed (or is already gone).
if kubectl get crd hyperpodpytorchjobs.sagemaker.amazonaws.com >/dev/null 2>&1; then
  kubectl -n rl-trainer delete hyperpodpytorchjobs --all --wait=true
fi
aws sagemaker delete-cluster --region "${AWS_REGION}" --cluster-name "${HYPERPOD_CLUSTER_NAME}"
log "waiting for the cluster to disappear"
while aws sagemaker describe-cluster --region "${AWS_REGION}" --cluster-name "${HYPERPOD_CLUSTER_NAME}" >/dev/null 2>&1; do
  sleep 30
done

role="${HYPERPOD_CLUSTER_NAME}-execution"
if aws iam get-role --role-name "${role}" >/dev/null 2>&1; then
  aws iam detach-role-policy --role-name "${role}" --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerClusterInstanceRolePolicy
  for policy in hyperpod-eks lifecycle-bucket-read; do
    aws iam delete-role-policy --role-name "${role}" --policy-name "${policy}"
  done
  aws iam delete-role --role-name "${role}"
  log "deleted role ${role}"
fi

confirm "bucket" "Empty and delete s3://${HYPERPOD_LCS_BUCKET}?"
aws s3 rm "s3://${HYPERPOD_LCS_BUCKET}" --recursive
aws s3api delete-bucket --bucket "${HYPERPOD_LCS_BUCKET}" --region "${AWS_REGION}"
log "HyperPod resources deleted"
