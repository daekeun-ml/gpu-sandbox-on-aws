# shellcheck shell=bash
# User data body for the B2 AMI builder (infra/hyperpod/ami/build-b2-ami.sh prepends the
# shebang, the pinned versions and /tmp/install-gvisor.sh). Runs once on a plain EC2 instance
# launched from the HyperPod EKS base AMI, then powers the instance off for imaging.
#
#   1. replace the NVIDIA driver with B2_NVIDIA_DRIVER_VERSION (open kernel module), using the
#      same mechanism the base AMI used (dnf packages or the NVIDIA .run installer)
#   2. install the pinned gVisor release (runsc, shim, gvisor-bin) and check nvproxy support
#   3. reset cloud-init so instances launched from the image bootstrap from scratch
#
# The last line on the serial console is "GPUSANDBOX-B2-BUILD: OK ..." or "... FAILED ...";
# the builder reads it with ec2 get-console-output.
set -euo pipefail
: "${B2_NVIDIA_DRIVER_VERSION:?}" "${B2_NVIDIA_RUNFILE_SHA256:?}" "${GVISOR_RELEASE:?}"

report() { echo "GPUSANDBOX-B2-BUILD: $*" | tee /dev/console; }
trap 'report "FAILED at line ${LINENO} (see /var/log/cloud-init-output.log)"; poweroff' ERR
fail() { report "FAILED: $*"; poweroff; exit 1; }

target="${B2_NVIDIA_DRIVER_VERSION}"
kernel="$(uname -r)"
current="$(modinfo -F version nvidia 2>/dev/null || true)"
echo "[b2] kernel ${kernel}, NVIDIA module on disk: ${current:-none}, target ${target}"
rpm -qa | grep -Ei '^(kmod-nvidia|nvidia-|libnvidia-|cuda-drivers)' | sort || true

# Kernel headers for DKMS. AL2023 kernel-devel packages provide "kernel-devel-uname-r".
if [[ ! -d "/lib/modules/${kernel}/build" ]]; then
  dnf install -y "kernel-devel-uname-r = ${kernel}" || dnf install -y "kernel*-devel-${kernel}"
fi

if [[ -d /opt/nvidia/current || -n "$(ls /etc/eks/nvidia-open-supported-devices-*.txt 2>/dev/null)" ]]; then
  # amazon-eks-ami style prebuilt driver trees with a boot-time resolver: not handled here.
  fail "driver trees under /opt/nvidia (EKS AMI layout); this builder expects a dnf or .run install"
elif rpm -qa --qf '%{NAME}\n' | grep -qE '^(kmod-nvidia|nvidia-driver)'; then
  method="dnf"
  # Every installed package that carries the current driver version, moved to the target
  # version in one transaction so that dependents (for example DCGM) stay satisfied. The
  # open kernel module replaces the proprietary one if the base AMI used that.
  [[ -n "${current}" ]] || fail "dnf-managed driver but no nvidia kernel module found"
  mapfile -t names < <(rpm -qa --qf '%{NAME} %{VERSION}\n' | awk -v v="${current}" '$2 == v {print $1}' | sort -u)
  [[ ${#names[@]} -gt 0 ]] || fail "no packages at driver version ${current}"
  targets=()
  for name in "${names[@]}"; do
    [[ "${name}" == "kmod-nvidia-latest-dkms" ]] && name="kmod-nvidia-open-dkms"
    targets+=("${name}-${target}")
  done
  repo="https://developer.download.nvidia.com/compute/cuda/repos/amzn2023/$(uname -m)/cuda-amzn2023.repo"
  dnf repolist | grep -qi cuda || dnf config-manager --add-repo "${repo}"
  echo "[b2] dnf: ${targets[*]}"
  dnf install -y --allowerasing "${targets[@]}" || dnf downgrade -y --allowerasing "${targets[@]}"
  dnf install -y python3-dnf-plugin-versionlock
  dnf versionlock add "${targets[@]}"
elif [[ -x /usr/bin/nvidia-uninstall ]]; then
  method="runfile"
  run="NVIDIA-Linux-$(uname -m)-${target}.run"
  url="https://download.nvidia.com/XFree86/Linux-$(uname -m)/${target}"
  cd /tmp
  curl -fsSLO "${url}/${run}"
  curl -fsSLO "${url}/${run}.sha256sum"
  # Two independent pins: NVIDIA's published checksum and the one in scripts/config.env.
  sha256sum -c "${run}.sha256sum"
  echo "${B2_NVIDIA_RUNFILE_SHA256}  ${run}" | sha256sum -c -
  /usr/bin/nvidia-uninstall --silent
  sh "${run}" --silent --kernel-module-type=open --dkms
  rm -f "${run}" "${run}.sha256sum"
else
  fail "cannot tell how the base AMI installed the NVIDIA driver"
fi

depmod -a "${kernel}"
installed="$(modinfo -F version nvidia)"
[[ "${installed}" == "${target}" ]] || fail "nvidia module is ${installed}, expected ${target}"
modinfo -F license nvidia | grep -q "Dual MIT/GPL" || fail "nvidia module is not the open kernel module"

# gVisor: same pinned install as the EC2 sandbox nodes (runsc.toml with nvproxy). The runsc
# handler is registered at node creation by on_create_sandbox.sh, where containerd's final
# config is known.
GVISOR_NVPROXY="true" bash /tmp/install-gvisor.sh
/usr/local/bin/runsc nvproxy list-supported-drivers | grep -qwF "${target}" \
  || fail "gVisor ${GVISOR_RELEASE} does not support driver ${target}"

install -d -m 0755 /etc/gpusandbox
cat > /etc/gpusandbox/b2-ami.env <<EOF
B2_NVIDIA_DRIVER_VERSION=${target}
B2_DRIVER_METHOD=${method}
GVISOR_RELEASE=${GVISOR_RELEASE}
BUILT_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

dnf clean all
rm -f /tmp/install-gvisor.sh
cloud-init clean --logs
report "OK driver=${target} method=${method} gvisor=${GVISOR_RELEASE} kernel=${kernel}"
trap - ERR
poweroff
