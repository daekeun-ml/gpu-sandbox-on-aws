#!/usr/bin/env bash
# Mode B2 preflight: can gVisor sandboxes run on the HyperPod nodes themselves?
# Prints, for every HyperPod node, the NVIDIA driver version and whether the pinned gVisor
# release's nvproxy supports it. Read-only apart from short-lived debug pods.
# As of 2026-11 the default HyperPod EKS AMI ships 595.91.07 ("no"); the B2 custom AMI from
# scripts/hyperpod/build_b2_ami.sh ships 580.178.04 ("yes"). Run it after scripts/hyperpod/create.sh --b2.
source "$(dirname "$0")/../lib.sh"
require_tools kubectl
require_vars GVISOR_RELEASE

nodes="$(kubectl get nodes -l sagemaker.amazonaws.com/node-health-status -o jsonpath='{.items[*].metadata.name}')"
[[ -n "${nodes}" ]] || die "no HyperPod nodes found"
for node in ${nodes}; do
  log "${node}"
  kubectl debug "node/${node}" -q --attach=true --profile=sysadmin --image=public.ecr.aws/amazonlinux/amazonlinux:2023 -- \
    bash -c "
      set -euo pipefail
      driver=\$(chroot /host nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
      dnf install -y -q bzip2 tar >/dev/null
      cd /tmp
      url=https://storage.googleapis.com/gvisor/releases/release/${GVISOR_RELEASE}/\$(uname -m)
      curl -fsSLO \$url/gvisor.tar.bz2 && curl -fsSLO \$url/gvisor.tar.bz2.sha512
      sha512sum -c gvisor.tar.bz2.sha512 >/dev/null && tar -xjf gvisor.tar.bz2
      if ./runsc nvproxy list-supported-drivers | grep -qwF \"\$driver\"; then
        echo \"  driver \$driver: SUPPORTED by gVisor ${GVISOR_RELEASE}: mode B2 is possible\"
      else
        echo \"  driver \$driver: NOT supported by gVisor ${GVISOR_RELEASE}: keep sandboxes on EC2 (mode B1)\"
      fi"
done
log "removing debug pods"
for pod in $(kubectl get pods -n default -o name | grep '/node-debugger-'); do
  kubectl delete -n default "${pod}" --wait=false
done
