#!/bin/bash
# Stage the driver after HyperPod has registered this sandbox worker.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
# Generated from scripts/config.env by the B2 creation script.
source "${here}/b2.env"
runsc nvproxy list-supported-drivers | grep -wF -- "${B2_NVIDIA_DRIVER_VERSION}" >/dev/null
bash "${here}/install-sandbox-driver.sh"

# The managed AMI starts containerd before the lifecycle hook. Register the handler again
# before each subsequent containerd start, including the reboot that activates the driver.
config="$(ps -o args= -C containerd | sed -n 's/.*\(--config\|-c\)[ =]\([^ ]*\).*/\2/p' | head -1)"
config="${config:-/etc/containerd/config.toml}"
install -d -m 0755 /usr/local/libexec/gpusandbox /etc/systemd/system/containerd.service.d
install -m 0755 "${here}/register_runsc.sh" /usr/local/libexec/gpusandbox/register_runsc.sh
printf '[Service]\nExecStartPre=/usr/local/libexec/gpusandbox/register_runsc.sh %s\n' "${config}" \
  > /etc/systemd/system/containerd.service.d/30-gpusandbox-runsc.conf
bash "${here}/node-guard.sh"
systemctl daemon-reload
if [[ "$(cat /sys/module/nvidia/version)" == "${B2_NVIDIA_DRIVER_VERSION}" ]]; then
  nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
  systemctl restart containerd
else
  echo "HyperPod sandbox requires a managed reboot to activate NVIDIA ${B2_NVIDIA_DRIVER_VERSION}"
fi
