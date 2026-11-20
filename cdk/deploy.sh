#!/usr/bin/env bash
# Provision the EKS infrastructure with CDK: cdk/deploy.sh [A|B1|B2|C] [--with-kata-cpu]
#   A   system + trainer (g5.2xlarge) + gVisor GPU nodes (g5.xlarge x GVISOR_NODES)
#   B1  system + gVisor GPU nodes (the trainer runs on HyperPod)
#   B2  system only (trainer and sandboxes run on HyperPod instance groups)
#   C   system + the nested-virtualization CPU node (c8i.2xlarge)
# Without an argument the scenario comes from SCENARIO in scripts/config.env. WITH_KATA_CPU=1 adds
# the c8i node and WITH_KATA_GPU=1 (with KATA_IOMMU_AMI_ID) adds g4dn.metal to any scenario.
#
# Reads scripts/config.env, so instance types and pinned versions match the script path.
# The EKS API endpoint is private; reach it with cdk/tunnel.sh. Set EKS_PUBLIC_ACCESS_CIDR to a
# single /32 only if you accept a public endpoint (some account security checks flag that).
# cdk-nag (AwsSolutions) runs on every synth and fails the deploy on unacknowledged findings, and
# --require-approval broadening stops for review before any IAM or security group change.
source "$(dirname "$0")/../scripts/lib.sh"
require_tools aws cdk python3
require_cdk_lib
require_vars CLUSTER_NAME AWS_REGION K8S_VERSION GVISOR_RELEASE

export SCENARIO="${1:-${SCENARIO:-A}}"
export WITH_KATA_CPU="${WITH_KATA_CPU:-0}" WITH_KATA_GPU="${WITH_KATA_GPU:-0}"
[[ "${2:-}" == "--with-kata-cpu" ]] && WITH_KATA_CPU=1

if [[ -z "${ADMIN_PRINCIPAL_ARN:-}" ]]; then
  # The operator's IAM role (not the temporary session) gets the cluster admin access entry.
  caller="$(aws sts get-caller-identity --query Arn --output text)"
  if [[ "${caller}" =~ ^arn:(aws[a-z-]*):sts::([0-9]{12}):assumed-role/([^/]+)/ ]]; then
    ADMIN_PRINCIPAL_ARN="arn:${BASH_REMATCH[1]}:iam::${BASH_REMATCH[2]}:role/${BASH_REMATCH[3]}"
    warn "using ${ADMIN_PRINCIPAL_ARN}; if the role has a path, set ADMIN_PRINCIPAL_ARN from: aws iam get-role --role-name ${BASH_REMATCH[3]} --query Role.Arn --output text"
  else
    ADMIN_PRINCIPAL_ARN="${caller}"
  fi
fi
export ADMIN_PRINCIPAL_ARN
if [[ "${WITH_KATA_GPU}" == "1" ]]; then
  confirm "metal" "This adds ${KATA_GPU_INSTANCE_TYPE:-g4dn.metal} (about 7.8 USD/hour) to the stack."
fi
export AWS_REGION CDK_DEFAULT_REGION="${AWS_REGION}"

# A different scenario replaces node groups (C -> A removes the c8i node and adds GPU nodes), and
# --require-approval broadening does not ask about that. Refuse unless it is deliberate.
deployed="$(aws cloudformation describe-stacks --region "${AWS_REGION}" --stack-name "${CLUSTER_NAME}-cdk" \
  --query "Stacks[0].Outputs[?OutputKey=='Scenario'].OutputValue" --output text 2>/dev/null || true)"
if [[ -n "${deployed}" && "${deployed}" != "None" && "${deployed}" != "${SCENARIO}" \
      && "${CHANGE_SCENARIO:-0}" != "1" ]]; then
  die "the stack runs scenario ${deployed}, not ${SCENARIO}. Set SCENARIO=${deployed} in scripts/config.env (or pass the matching option to scripts/02_create_cluster.sh); to switch on purpose, run with CHANGE_SCENARIO=1"
fi

cd "$(dirname "$0")" || die "cannot enter the cdk directory"
log "deploying ${CLUSTER_NAME}-cdk (scenario ${SCENARIO}) to ${AWS_REGION}: 20-30 min"
cdk deploy "${CLUSTER_NAME}-cdk" --require-approval broadening
cat <<EOF

Next:
  cdk/tunnel.sh                       # in a second terminal; keep it running
  kubectl get nodes -L gpusandbox/role
  then the in-cluster steps of the hands-on (04_install_gpu_stack.sh or kata/cpu_nodes.sh,
  05_setup_namespaces_auth.sh, 06_deploy_sandboxes.sh, ops/verify.sh, ...)
EOF
