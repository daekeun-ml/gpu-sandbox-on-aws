#!/usr/bin/env bash
# Scenario B: attach a SageMaker HyperPod cluster (trainer instance group) to the EKS cluster.
#   scripts/hyperpod/create.sh        B1: trainer only; sandboxes stay on EC2 nodes
#   scripts/hyperpod/create.sh --b2   B2: also a "sandbox" instance group that boots from the
#                                     custom AMI of scripts/hyperpod/build_b2_ami.sh and runs
#                                     gVisor sandboxes
# Prerequisite: scripts/02_create_cluster.sh --hyperpod (B1) or --hyperpod-b2 (B2).
#
#   1. HyperPod dependency Helm chart (required when creating through the API)
#   2. lifecycle-script bucket (private, Block Public Access on)
#   3. HyperPod execution role
#   4. CreateCluster with the EKS cluster as orchestrator
#   5. HyperPod training operator add-on (for HyperPodPyTorchJob)
# Billable: the HyperPod instances (ml.g5.2xlarge by default; B2 adds 2x ml.g5.xlarge).
source "$(dirname "$0")/../lib.sh"
require_tools aws helm kubectl git jq
require_vars CLUSTER_NAME AWS_REGION HYPERPOD_CLUSTER_NAME HYPERPOD_TRAINER_INSTANCE_TYPE HYPERPOD_LCS_BUCKET

b2=0
case "${1:-}" in
  "") ;;
  --b2) b2=1 ;;
  *) die "unknown option ${1}; use --b2" ;;
esac
if (( b2 )); then
  require_vars HYPERPOD_B2_AMI_ID HYPERPOD_SANDBOX_INSTANCE_TYPE HYPERPOD_SANDBOX_COUNT
fi

account="$(account_id)"
work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

log "1) HyperPod dependency chart"
git clone --depth 1 https://github.com/aws/sagemaker-hyperpod-cli.git "${work}/hp-cli"
helm dependencies update "${work}/hp-cli/helm_chart/HyperPodHelmChart"
# The resource monitor needs the HyperPod AMI's log directory and exits on ordinary EKS nodes.
helm upgrade --install hyperpod-dependencies "${work}/hp-cli/helm_chart/HyperPodHelmChart" \
  --namespace kube-system --set-string "global.region=${AWS_REGION}" \
  --set-json 'hyperpod-kubernetes-resource-monitor.nodeSelector={"sagemaker.amazonaws.com/compute-type":"hyperpod"}' \
  --wait --timeout 15m

log "2) lifecycle scripts in s3://${HYPERPOD_LCS_BUCKET}"
if ! aws s3api head-bucket --bucket "${HYPERPOD_LCS_BUCKET}" 2>/dev/null; then
  if [[ "${AWS_REGION}" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "${HYPERPOD_LCS_BUCKET}" --region "${AWS_REGION}"
  else
    aws s3api create-bucket --bucket "${HYPERPOD_LCS_BUCKET}" --region "${AWS_REGION}" \
      --create-bucket-configuration "LocationConstraint=${AWS_REGION}"
  fi
fi
aws s3api put-public-access-block --bucket "${HYPERPOD_LCS_BUCKET}" --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
aws s3 sync "${REPO_ROOT}/infra/hyperpod/lifecycle/" "s3://${HYPERPOD_LCS_BUCKET}/lifecycle/"
# The B2 sandbox nodes install the same node guard as the EC2 sandbox nodes.
aws s3 cp "${REPO_ROOT}/infra/eks/node-guard.sh" "s3://${HYPERPOD_LCS_BUCKET}/lifecycle/node-guard.sh"

log "3) execution role"
role="${HYPERPOD_CLUSTER_NAME}-execution"
if ! aws iam get-role --role-name "${role}" >/dev/null 2>&1; then
  aws iam create-role --role-name "${role}" \
    --assume-role-policy-document "file://${REPO_ROOT}/infra/hyperpod/execution-role-trust.json" >/dev/null
  aws iam attach-role-policy --role-name "${role}" \
    --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerClusterInstanceRolePolicy
  aws iam put-role-policy --role-name "${role}" --policy-name hyperpod-eks \
    --policy-document "file://${REPO_ROOT}/infra/hyperpod/execution-role-eks-policy.json"
  aws iam put-role-policy --role-name "${role}" --policy-name lifecycle-bucket-read --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{\"Effect\": \"Allow\", \"Action\": [\"s3:GetObject\", \"s3:ListBucket\"],
      \"Resource\": [\"arn:aws:s3:::${HYPERPOD_LCS_BUCKET}\", \"arn:aws:s3:::${HYPERPOD_LCS_BUCKET}/*\"]}]}"
  sleep 15  # IAM propagation
fi
export HYPERPOD_EXECUTION_ROLE_ARN="arn:aws:iam::${account}:role/${role}"

log "4) CreateCluster"
cluster_json="$(aws eks describe-cluster --name "${CLUSTER_NAME}" --region "${AWS_REGION}" --output json)"
EKS_CLUSTER_ARN="$(jq -r .cluster.arn <<<"${cluster_json}")"
# The EKS cluster security group lets HyperPod nodes, EC2 nodes and the control plane talk.
HYPERPOD_SECURITY_GROUP_ID="$(jq -r .cluster.resourcesVpcConfig.clusterSecurityGroupId <<<"${cluster_json}")"
# HyperPod needs a private subnet; take one of the CDK stack's private subnets (tagged internal-elb).
vpc_id="$(jq -r .cluster.resourcesVpcConfig.vpcId <<<"${cluster_json}")"
HYPERPOD_SUBNET_ID="$(aws ec2 describe-subnets --region "${AWS_REGION}" \
  --filters "Name=vpc-id,Values=${vpc_id}" "Name=tag:kubernetes.io/role/internal-elb,Values=1" \
  --query 'Subnets[0].SubnetId' --output text)"
export EKS_CLUSTER_ARN HYPERPOD_SECURITY_GROUP_ID HYPERPOD_SUBNET_ID
render infra/hyperpod/cluster.json.tpl > "${work}/cluster.json"
if (( b2 )); then
  render infra/hyperpod/instance-group-sandbox.json.tpl > "${work}/sandbox-group.json"
  jq --slurpfile g "${work}/sandbox-group.json" '.InstanceGroups += $g' "${work}/cluster.json" \
    > "${work}/cluster-b2.json"
  mv "${work}/cluster-b2.json" "${work}/cluster.json"
fi
aws sagemaker create-cluster --region "${AWS_REGION}" --cli-input-json "file://${work}/cluster.json"
log "waiting for InService (15-30 min)"
while true; do
  status="$(aws sagemaker describe-cluster --region "${AWS_REGION}" --cluster-name "${HYPERPOD_CLUSTER_NAME}" \
    --query '{status: ClusterStatus, failure: FailureMessage}' --output json)"
  case "$(jq -r .status <<<"${status}")" in
    InService) echo "${status}"; break ;;
    Creating|Pending) sleep 30 ;;
    *) die "HyperPod creation stopped: ${status}" ;;
  esac
done

log "5) HyperPod training operator add-on"
# The EKS add-on selects a HyperPod node. The cluster itself can already be InService
# while its first trainer instance is still booting and absent from Kubernetes.
trainer_selector="sagemaker.amazonaws.com/cluster-name=${HYPERPOD_CLUSTER_NAME}"
trainer_selector+=",node.kubernetes.io/instance-type=${HYPERPOD_TRAINER_INSTANCE_TYPE}"
trainer_selector+=",sagemaker.amazonaws.com/node-health-status=Schedulable"
kubectl wait --for=create nodes -l "${trainer_selector}" --timeout=30m
kubectl wait --for=condition=Ready nodes -l "${trainer_selector}" --timeout=5m
aws eks create-addon --region "${AWS_REGION}" --cluster-name "${CLUSTER_NAME}" \
  --addon-name amazon-sagemaker-hyperpod-training-operator >/dev/null
aws eks wait addon-active --region "${AWS_REGION}" --cluster-name "${CLUSTER_NAME}" \
  --addon-name amazon-sagemaker-hyperpod-training-operator
if (( b2 )); then
  kubectl apply -f "${REPO_ROOT}/k8s/runtimes/runtimeclass-gvisor-hyperpod.yaml"
fi
kubectl get nodes -L sagemaker.amazonaws.com/node-health-status,node.kubernetes.io/instance-type,gpusandbox/role
