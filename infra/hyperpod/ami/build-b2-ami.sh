#!/usr/bin/env bash
# Bake the custom HyperPod AMI for scenario B2: the HyperPod EKS base AMI for K8S_VERSION with
# its NVIDIA driver replaced by B2_NVIDIA_DRIVER_VERSION (one that gVisor nvproxy supports) and
# the pinned gVisor binaries added.
#
# HyperPod accepts custom AMIs only when they are built from a HyperPod public base AMI, so the
# builder launches that AMI on a plain EC2 instance, runs customize-b2.sh as user data, and
# images the stopped instance. Building a kernel module needs no GPU, so a cheap m6i.large is
# enough; the GPU check happens on the first HyperPod node (scripts/hyperpod/check_gvisor.sh).
#
# Output: prints HYPERPOD_B2_AMI_ID; add it to scripts/config.env.
source "$(dirname "$0")/../../../scripts/lib.sh"
require_vars AWS_REGION K8S_VERSION CLUSTER_NAME GVISOR_RELEASE B2_NVIDIA_DRIVER_VERSION B2_NVIDIA_RUNFILE_SHA256
require_tools aws python3

base_ami="${HYPERPOD_BASE_AMI_ID:-}"
if [[ -z "${base_ami}" ]]; then
  # Public HyperPod images are named "HyperPod EKS <version> x86_64 AMI Amazon Linux 2023 <timestamp>"
  # and owned by amazon (EC2 AMI Catalog, Community AMIs, checked 2026-11-14). Take the newest.
  base_ami="$(aws ec2 describe-images --region "${AWS_REGION}" --owners amazon \
    --filters "Name=name,Values=HyperPod EKS ${K8S_VERSION} x86_64 AMI Amazon Linux 2023 *" "Name=state,Values=available" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text)"
  [[ "${base_ami}" == ami-* ]] || die "no HyperPod EKS ${K8S_VERSION} AL2023 AMI found; set HYPERPOD_BASE_AMI_ID (EC2 AMI Catalog, Community AMIs, \"HyperPod EKS ${K8S_VERSION}\")"
fi
log "base AMI ${base_ami}"
subnet="$(aws eks describe-cluster --region "${AWS_REGION}" --name "${CLUSTER_NAME}" \
  --query 'cluster.resourcesVpcConfig.subnetIds[0]' --output text)"

user_data="$(python3 - "${REPO_ROOT}/infra/hyperpod/ami/customize-b2.sh" "${REPO_ROOT}/infra/gvisor/install-gvisor.sh" \
  "${B2_NVIDIA_DRIVER_VERSION}" "${B2_NVIDIA_RUNFILE_SHA256}" "${GVISOR_RELEASE}" <<'PY'
import sys
body_path, gvisor_path, driver, runfile_sha, gvisor = sys.argv[1:6]
body, installer = open(body_path).read(), open(gvisor_path).read()
assert "GPUSANDBOX_GVISOR_EOF" not in installer
# The pinned versions and the gVisor installer go first; customize-b2.sh carries no defaults.
print("#!/bin/bash\n"
      f'export B2_NVIDIA_DRIVER_VERSION="{driver}"\n'
      f'export B2_NVIDIA_RUNFILE_SHA256="{runfile_sha}"\n'
      f'export GVISOR_RELEASE="{gvisor}"\n'
      "cat > /tmp/install-gvisor.sh <<'GPUSANDBOX_GVISOR_EOF'\n" + installer + "GPUSANDBOX_GVISOR_EOF\n"
      + body)
PY
)"

instance_id="$(aws ec2 run-instances --region "${AWS_REGION}" \
  --image-id "${base_ami}" --instance-type m6i.large --subnet-id "${subnet}" \
  --metadata-options HttpTokens=required,HttpPutResponseHopLimit=1 \
  --user-data "${user_data}" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${CLUSTER_NAME}-b2-ami-builder},{Key=project,Value=gpu-sandbox-on-aws}]" \
  --query 'Instances[0].InstanceId' --output text)"
log "builder instance ${instance_id}: swapping the driver and installing gVisor, then it stops (20-40 min)"
state=""
for _ in $(seq 1 120); do  # up to 60 minutes
  state="$(aws ec2 describe-instances --region "${AWS_REGION}" --instance-ids "${instance_id}" \
    --query 'Reservations[0].Instances[0].State.Name' --output text)"
  [[ "${state}" == "stopped" ]] && break
  sleep 30
done
[[ "${state}" == "stopped" ]] || die "builder ${instance_id} did not stop within 60 minutes (state ${state}); inspect it, then terminate it"

# customize-b2.sh prints one result line to the serial console before it powers off.
console="$(aws ec2 get-console-output --region "${AWS_REGION}" --instance-id "${instance_id}" --latest \
  --query Output --output text)"
result="$(grep -o 'GPUSANDBOX-B2-BUILD: [A-Z]*.*' <<<"${console}" | tail -1 || true)"
log "${result:-no result line in the console output}"
# On failure the stopped builder is kept for inspection (EBS charges only).
[[ "${result}" == "GPUSANDBOX-B2-BUILD: OK"* ]] \
  || die "customization failed. Inspect: aws ec2 get-console-output --latest --region ${AWS_REGION} --instance-id ${instance_id}; then: aws ec2 terminate-instances --region ${AWS_REGION} --instance-ids ${instance_id}"

ami_name="hyperpod-eks-${K8S_VERSION}-gvisor-nv${B2_NVIDIA_DRIVER_VERSION}-$(date +%Y%m%d%H%M%S)"
ami_id="$(aws ec2 create-image --region "${AWS_REGION}" --instance-id "${instance_id}" \
  --name "${ami_name}" \
  --description "HyperPod EKS ${K8S_VERSION} base + NVIDIA ${B2_NVIDIA_DRIVER_VERSION} + gVisor ${GVISOR_RELEASE}" \
  --tag-specifications "ResourceType=image,Tags=[{Key=project,Value=gpu-sandbox-on-aws},{Key=base-ami,Value=${base_ami}}]" \
  --query ImageId --output text)"
log "creating ${ami_id} (${ami_name})"
# One waiter run lasts 10 minutes; a large root snapshot can take longer.
aws ec2 wait image-available --region "${AWS_REGION}" --image-ids "${ami_id}" \
  || aws ec2 wait image-available --region "${AWS_REGION}" --image-ids "${ami_id}"

log "terminating builder ${instance_id}"
aws ec2 terminate-instances --region "${AWS_REGION}" --instance-ids "${instance_id}" >/dev/null

echo
echo "Add to scripts/config.env:"
echo "export HYPERPOD_B2_AMI_ID=\"${ami_id}\""
