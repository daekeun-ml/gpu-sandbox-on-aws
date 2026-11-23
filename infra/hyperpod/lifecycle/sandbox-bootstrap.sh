#!/bin/bash
# The worker joins HyperPod with matching stock kernel and user-space drivers. The operator
# activates the supported driver after the worker is Ready, as in the B2 hands-on.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
source "${here}/b2.env"
GVISOR_NVPROXY=true bash "${here}/install-gvisor.sh"
runsc nvproxy list-supported-drivers | grep -wF -- "${B2_NVIDIA_DRIVER_VERSION}" >/dev/null
destination=/usr/local/libexec/gpusandbox/managed-b2
install -d -m 0755 "${destination}"
install -m 0644 "${here}/b2.env" "${destination}/"
for script in prepare-sandbox-worker.sh install-sandbox-driver.sh register_runsc.sh node-guard.sh; do
  install -m 0755 "${here}/${script}" "${destination}/"
done
echo "B2 sandbox bootstrap complete, current NVIDIA $(cat /sys/module/nvidia/version)"
