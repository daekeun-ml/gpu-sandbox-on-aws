#!/usr/bin/env bash
# Delete the HyperPod cluster, its execution role and its lifecycle bucket. EKS is removed separately.
source "$(dirname "$0")/../lib.sh"
require_tools aws kubectl
require_vars AWS_REGION HYPERPOD_CLUSTER_NAME HYPERPOD_LCS_BUCKET

# A partially provisioned or previously deleted cluster can still have a role and a bucket.
# Only a missing cluster is equivalent to a completed deletion. Propagate other errors.
cluster_status() {
  local result
  if result=$(aws sagemaker describe-cluster --region "$AWS_REGION" --cluster-name "$HYPERPOD_CLUSTER_NAME" \
      --query ClusterStatus --output text 2>&1); then
    echo "$result"
  elif [[ "$result" == *ResourceNotFound* || "$result" == *ValidationException*'does not exist'* ]]; then
    echo absent
  else
    die "$result"
  fi
}
confirm "$HYPERPOD_CLUSTER_NAME" "Delete HyperPod cluster $HYPERPOD_CLUSTER_NAME and its dedicated resources?"
status=$(cluster_status)
if [[ "$status" != absent ]]; then
  if [[ "$status" != Deleting ]]; then
    if kubectl get crd hyperpodpytorchjobs.sagemaker.amazonaws.com >/dev/null 2>&1; then
      kubectl -n rl-trainer delete hyperpodpytorchjobs --all --wait=true
    fi
    aws sagemaker delete-cluster --region "$AWS_REGION" --cluster-name "$HYPERPOD_CLUSTER_NAME"
  fi
  log 'waiting for the cluster to disappear'
  while true; do
    status=$(cluster_status)
    [[ "$status" != absent ]] || break
    [[ "$status" != DeleteFailed ]] || die "deletion of $HYPERPOD_CLUSTER_NAME failed; check its status message"
    sleep 30
  done
fi

role="${HYPERPOD_CLUSTER_NAME}-execution"
if result=$(aws iam get-role --role-name "$role" 2>&1); then
  policy_arn=arn:aws:iam::aws:policy/AmazonSageMakerClusterInstanceRolePolicy
  attached=$(aws iam list-attached-role-policies --role-name "$role" \
    --query "AttachedPolicies[?PolicyArn=='$policy_arn'].PolicyArn" --output text)
  if [[ "$attached" == "$policy_arn" ]]; then
    aws iam detach-role-policy --role-name "$role" --policy-arn "$policy_arn"
  fi
  policies=$(aws iam list-role-policies --role-name "$role" --query PolicyNames --output text)
  for policy in $policies; do
    case "$policy" in hyperpod-eks|lifecycle-bucket-read) aws iam delete-role-policy --role-name "$role" --policy-name "$policy" ;; esac
  done
  aws iam delete-role --role-name "$role"
  log "deleted role $role"
elif [[ "$result" != *NoSuchEntity* ]]; then
  die "$result"
fi

account=$(account_id)
if result=$(aws s3api head-bucket --bucket "$HYPERPOD_LCS_BUCKET" --expected-bucket-owner "$account" 2>&1); then
  confirm bucket "Empty and delete s3://$HYPERPOD_LCS_BUCKET?"
  aws s3 rm "s3://$HYPERPOD_LCS_BUCKET" --recursive --region "$AWS_REGION"
  aws s3api delete-bucket --bucket "$HYPERPOD_LCS_BUCKET" --region "$AWS_REGION" --expected-bucket-owner "$account"
elif [[ "$result" != *'(404)'* && "$result" != *NoSuchBucket* ]]; then
  die "$result"
fi
log 'HyperPod resources deleted'
