#!/usr/bin/env bash
# Check local tools, AWS identity and the quotas this asset needs. Read-only.
source "$(dirname "$0")/lib.sh"
require_tools aws cdk node kubectl helm docker python3 jq session-manager-plugin
require_vars AWS_REGION CLUSTER_NAME K8S_VERSION

log "AWS identity"
aws sts get-caller-identity --output table

log "Tool versions"
cdk --version
node --version
kubectl version --client=true | head -1
helm version --short
docker version --format '{{.Client.Version}}'

# Running On-Demand G and VT instances is counted in vCPUs. Defaults for new accounts can be 0.
#   trainer g5.2xlarge (8) + 2x g5.xlarge (8) = 16 vCPU; g4dn.metal adds 96.
log "On-Demand G/VT vCPU quota in ${AWS_REGION}"
aws service-quotas list-service-quotas --service-code ec2 --region "${AWS_REGION}" \
  --query "Quotas[?QuotaName=='Running On-Demand G and VT instances'].[QuotaName,Value]" --output table

# Standard vCPUs: 2x m6i.large (4) + the t4g.nano access instance (2) = 6, plus c8i.2xlarge (8) = 14
# for scenario C or WITH_KATA_CPU=1. Scenario C needs only this quota.
log "On-Demand Standard vCPU quota in ${AWS_REGION}"
aws service-quotas list-service-quotas --service-code ec2 --region "${AWS_REGION}" \
  --query "Quotas[?QuotaName=='Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances'].[QuotaName,Value]" \
  --output table

log "Nested virtualization support for ${KATA_CPU_INSTANCE_TYPE}"
aws ec2 describe-instance-types --region "${AWS_REGION}" --instance-types "${KATA_CPU_INSTANCE_TYPE}" \
  --query 'InstanceTypes[0].ProcessorInfo.SupportedFeatures' --output text

log "Offerings of the GPU instance types in ${AWS_REGION} (per AZ)"
for type in "${TRAINER_INSTANCE_TYPE}" "${GVISOR_INSTANCE_TYPE}" "${KATA_GPU_INSTANCE_TYPE}"; do
  zones="$(aws ec2 describe-instance-type-offerings --region "${AWS_REGION}" \
    --location-type availability-zone --filters "Name=instance-type,Values=${type}" \
    --query 'InstanceTypeOfferings[].Location' --output text)"
  printf '  %-14s %s\n' "${type}" "${zones:-NOT OFFERED}"
done
log "Done. Request quota increases before 02_create_cluster.sh if any value above is too low."
