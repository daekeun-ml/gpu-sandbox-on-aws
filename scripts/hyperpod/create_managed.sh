#!/usr/bin/env bash
# Create B2 using the same regional CloudFormation template as the HyperPod EKS wizard.
# Use a dedicated lifecycle bucket and ECR prefix for each lab.
source "$(dirname "$0")/../lib.sh"
require_tools aws python3 jq
require_vars AWS_REGION CLUSTER_NAME K8S_VERSION HYPERPOD_CLUSTER_NAME HYPERPOD_LCS_BUCKET \
  HYPERPOD_TRAINER_INSTANCE_TYPE HYPERPOD_SANDBOX_INSTANCE_TYPE HYPERPOD_SANDBOX_COUNT HYPERPOD_AZ_IDS \
  GVISOR_RELEASE B2_NVIDIA_DRIVER_VERSION B2_NVIDIA_RUNFILE_SHA256

stack="${HYPERPOD_MANAGED_STACK:-${CLUSTER_NAME}-hyperpod}"
template="https://aws-sagemaker-hyperpod-cluster-setup-${AWS_REGION}-prod.s3.${AWS_REGION}.amazonaws.com/templates/main-stack-eks-based-template.yaml"
work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT
python3 "${REPO_ROOT}/infra/hyperpod/managed-parameters.py" > "${work}/parameters.json"

existing=0
if aws cloudformation describe-stacks --region "${AWS_REGION}" --stack-name "${stack}" --output json \
    > "${work}/stack.json" 2> "${work}/describe.err"; then
  existing=1
  jq -e --slurpfile requested "${work}/parameters.json" '
    .Stacks[0] as $s | ($s.Parameters | map({key:.ParameterKey,value:.ParameterValue}) | from_entries) as $params |
    any($s.Tags[]?; .Key=="project" and .Value=="gpu-sandbox-on-aws") and
    all($requested[0][]; $params[.ParameterKey] == .ParameterValue)' "${work}/stack.json" >/dev/null \
    || die "stack ${stack} already exists with a different configuration"
  status="$(jq -r '.Stacks[0].StackStatus' "${work}/stack.json")"
  case "${status}" in
    CREATE_IN_PROGRESS|CREATE_COMPLETE|UPDATE_COMPLETE) ;;
    *) die "stack ${stack} is ${status}; check its CloudFormation events" ;;
  esac
elif ! grep -F 'does not exist' "${work}/describe.err" >/dev/null; then
  cat "${work}/describe.err" >&2
  exit 1
fi

account="$(account_id)"
if aws s3api head-bucket --bucket "${HYPERPOD_LCS_BUCKET}" --expected-bucket-owner "${account}" >/dev/null 2>&1; then
  location="$(aws s3api get-bucket-location --bucket "${HYPERPOD_LCS_BUCKET}" --query LocationConstraint --output text)"
  [[ "${location}" == "None" ]] && location="us-east-1"
  [[ "${location}" == "${AWS_REGION}" ]] || die "lifecycle bucket is in ${location}, expected ${AWS_REGION}"
else
  options=()
  [[ "${AWS_REGION}" == "us-east-1" ]] || options+=(--create-bucket-configuration "LocationConstraint=${AWS_REGION}")
  aws s3api create-bucket --bucket "${HYPERPOD_LCS_BUCKET}" --region "${AWS_REGION}" "${options[@]}" >/dev/null
fi
aws s3api put-public-access-block --bucket "${HYPERPOD_LCS_BUCKET}" --expected-bucket-owner "${account}" \
  --public-access-block-configuration 'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true'

mkdir "${work}/lifecycle"
cp "${REPO_ROOT}"/infra/hyperpod/lifecycle/*.sh \
  "${REPO_ROOT}/infra/gvisor/install-gvisor.sh" "${REPO_ROOT}/infra/eks/node-guard.sh" "${work}/lifecycle/"
for key in GVISOR_RELEASE B2_NVIDIA_DRIVER_VERSION B2_NVIDIA_RUNFILE_SHA256; do
  printf 'export %s=%q\n' "${key}" "${!key}"
done > "${work}/lifecycle/b2.env"
aws s3 sync "${work}/lifecycle/" "s3://${HYPERPOD_LCS_BUCKET}/lifecycle/" --region "${AWS_REGION}"
if ((existing)); then
  log "stack ${stack} is ${status}; new workers will use the uploaded lifecycle scripts"
  exit 0
fi
aws cloudformation create-stack --region "${AWS_REGION}" --stack-name "${stack}" --template-url "${template}" \
  --parameters "file://${work}/parameters.json" --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --tags Key=project,Value=gpu-sandbox-on-aws
log "track ${stack} in CloudFormation: aws cloudformation describe-stack-events --region ${AWS_REGION} --stack-name ${stack}"
