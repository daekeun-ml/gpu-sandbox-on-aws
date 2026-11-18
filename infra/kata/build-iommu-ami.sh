#!/usr/bin/env bash
# Bake an EKS AL2023 standard (non-NVIDIA) AMI with the Intel IOMMU enabled, for the Kata GPU
# node (g4dn.metal).
#
# Why bake instead of rebooting from user data: AL2023 kernels ship with
# CONFIG_INTEL_IOMMU_DEFAULT_ON unset, so intel_iommu=on must be on the kernel command line
# before VFIO can pass a GPU through. Rebooting a metal instance inside user data works in
# principle (nodeadm-run starts kubelet only after cloud-final), but there are reports of
# g4dn.metal warm reboots not coming back. Kernel arguments are instance-type independent, so
# a cheap m6i.large is enough to build the image.
#
# Output: prints KATA_IOMMU_AMI_ID; add it to scripts/config.env.
source "$(dirname "$0")/../../scripts/lib.sh"
require_vars AWS_REGION K8S_VERSION CLUSTER_NAME
require_tools aws

param="/aws/service/eks/optimized-ami/${K8S_VERSION}/amazon-linux-2023/x86_64/standard/recommended/image_id"
base_ami="$(aws ssm get-parameter --region "${AWS_REGION}" --name "${param}" --query Parameter.Value --output text)"
subnet="$(aws eks describe-cluster --region "${AWS_REGION}" --name "${CLUSTER_NAME}" \
  --query 'cluster.resourcesVpcConfig.subnetIds[0]' --output text)"
log "base AMI ${base_ami} (${param}), builder subnet ${subnet}"

user_data="$(cat <<'EOF'
#!/bin/bash
set -euo pipefail
grubby --update-kernel=ALL --args="intel_iommu=on iommu=pt"
# The AL2023 kernel builds the VFIO type1 IOMMU backend as a module (CONFIG_VFIO_IOMMU_TYPE1=m)
# and nothing loads it, so QEMU fails with "failed to setup container for group N: No available
# IOMMU models". Load it on every boot.
echo vfio_iommu_type1 > /etc/modules-load.d/vfio-iommu-type1.conf
# Remove per-instance state so instances launched from the image bootstrap from scratch.
cloud-init clean --logs
shutdown -h now
EOF
)"

instance_id="$(aws ec2 run-instances --region "${AWS_REGION}" \
  --image-id "${base_ami}" --instance-type m6i.large --subnet-id "${subnet}" \
  --metadata-options HttpTokens=required,HttpPutResponseHopLimit=1 \
  --user-data "${user_data}" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${CLUSTER_NAME}-iommu-ami-builder},{Key=project,Value=gpu-sandbox-on-aws}]" \
  --query 'Instances[0].InstanceId' --output text)"
# Whatever happens next, do not leave the builder behind.
trap 'aws ec2 terminate-instances --region "${AWS_REGION}" --instance-ids "${instance_id}" >/dev/null 2>&1 || true' EXIT
log "builder instance ${instance_id}: waiting for it to apply kernel args and stop"
# Poll instead of "aws ec2 wait instance-stopped": that waiter treats "pending" as a terminal
# failure, so it gives up when it starts before the instance is running.
state=""
for _ in $(seq 1 120); do
  state="$(aws ec2 describe-instances --region "${AWS_REGION}" --instance-ids "${instance_id}" \
    --query 'Reservations[0].Instances[0].State.Name' --output text)"
  [[ "${state}" == "stopped" ]] && break
  [[ "${state}" == "shutting-down" || "${state}" == "terminated" ]] && die "builder ${instance_id} ended in state ${state}"
  sleep 15
done
[[ "${state}" == "stopped" ]] || die "builder ${instance_id} did not stop within 30 minutes (state ${state})"

ami_name="eks-al2023-${K8S_VERSION}-iommu-$(date +%Y%m%d%H%M%S)"
ami_id="$(aws ec2 create-image --region "${AWS_REGION}" --instance-id "${instance_id}" \
  --name "${ami_name}" --description "EKS AL2023 ${K8S_VERSION} standard + intel_iommu=on iommu=pt" \
  --tag-specifications "ResourceType=image,Tags=[{Key=project,Value=gpu-sandbox-on-aws},{Key=base-ami,Value=${base_ami}}]" \
  --query ImageId --output text)"
log "creating ${ami_id} (${ami_name})"
aws ec2 wait image-available --region "${AWS_REGION}" --image-ids "${ami_id}"

log "terminating builder ${instance_id}"   # also done by the EXIT trap

echo
echo "Add to scripts/config.env:"
echo "export KATA_IOMMU_AMI_ID=\"${ami_id}\""
