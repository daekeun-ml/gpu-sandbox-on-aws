#!/bin/bash
# Stage the GPU driver on the root volume of a dedicated HyperPod sandbox worker.
# The operator reboots the worker through HyperPod after its lifecycle hook has completed.
set -euo pipefail
: "${B2_NVIDIA_DRIVER_VERSION:?}" "${B2_NVIDIA_RUNFILE_SHA256:?}"
target="${B2_NVIDIA_DRIVER_VERSION}"
exec 9>/run/gpusandbox-driver.lock
flock 9
installed="$(modinfo -F version nvidia 2>/dev/null || true)"
kernel="$(uname -r)"
state=/var/lib/gpusandbox/driver-install
if [[ "${installed}" == "${target}" && ! -e "${state}.pending" ]]; then exit 0; fi
if [[ ! -e "${state}.pending" && ( ! -x /usr/bin/nvidia-uninstall || ! -x /usr/bin/nvidia-installer ) ]]; then
  echo "expected the HyperPod AL2023 NVIDIA runfile installation" >&2; exit 1;
fi
[[ -d "/lib/modules/${kernel}/build" ]] || dnf install -y "kernel-devel-uname-r = ${kernel}"
work="$(mktemp -d /var/tmp/gpusandbox-driver.XXXXXXXX)"
trap 'rm -rf "${work}"' EXIT
file="NVIDIA-Linux-$(uname -m)-${target}.run"
cd "${work}"
curl -fsSL --retry 3 -o "${file}" "https://download.nvidia.com/XFree86/Linux-$(uname -m)/${target}/${file}"
printf '%s  %s\n' "${B2_NVIDIA_RUNFILE_SHA256}" "${file}" | sha256sum -c -
# HyperPod monitoring can keep nvidia_uvm open. NVIDIA supports installing the replacement
# on disk while keeping the running modules loaded until the managed worker reboots.
echo "staging NVIDIA ${target} for kernel ${kernel} (current module on disk: ${installed})"
install -d -m 0755 /var/lib/gpusandbox
printf '%s %s\n' "${target}" "${kernel}" > "${state}.pending"
if [[ -x /usr/bin/nvidia-uninstall ]]; then /usr/bin/nvidia-uninstall --silent --skip-module-unload; fi
sh "${file}" --silent --kernel-module-type=open --dkms --allow-installation-with-running-driver \
  --skip-module-load --rebuild-initramfs
depmod -a "${kernel}"
installed="$(modinfo -F version nvidia)"
[[ "${installed}" == "${target}" ]] || { echo "driver on disk is ${installed}, expected ${target}" >&2; exit 1; }
rm -f "${state}.pending"
echo "NVIDIA ${target} is installed on disk"
