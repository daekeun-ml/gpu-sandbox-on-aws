#!/usr/bin/env bash
# Install a pinned gVisor release for containerd on an EKS AL2023 node.
#
# Runs as user data between nodeadm-config and nodeadm-run, so containerd starts with the
# runsc shim already on disk. The runsc runtime handler itself is declared in the node's
# NodeConfig (infra/eks/*), which nodeadm re-applies on every boot.
#
# Since release-20260831 gVisor ships tarballs only (runsc + containerd-shim-runsc-v1 +
# gvisor-bin/, which must stay next to runsc).
set -euo pipefail

GVISOR_RELEASE="${GVISOR_RELEASE:?set GVISOR_RELEASE, e.g. 20261109.0}"
# "false" on CPU-only nodes (the c8i nested-virtualization node): no NVIDIA devices exist there.
GVISOR_NVPROXY="${GVISOR_NVPROXY:-true}"
ARCH="$(uname -m)"
URL="https://storage.googleapis.com/gvisor/releases/release/${GVISOR_RELEASE}/${ARCH}"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

command -v bzip2 >/dev/null 2>&1 || dnf install -y -q bzip2
cd "${WORK}"
curl -fsSLO "${URL}/gvisor.tar.bz2"
curl -fsSLO "${URL}/gvisor.tar.bz2.sha512"
sha512sum -c gvisor.tar.bz2.sha512
tar -xjf gvisor.tar.bz2 -C /usr/local/bin
/usr/local/bin/runsc --version

install -d -m 0755 /etc/containerd
if [[ "${GVISOR_NVPROXY}" == "true" ]]; then
  cat > /etc/containerd/runsc.toml <<'EOF'
# Read by containerd-shim-runsc-v1 through the runtime's ConfigPath option.
[runsc_config]
  # GPU support turns on automatically when NVIDIA devices are in the OCI spec; being explicit
  # documents intent and is harmless.
  nvproxy = "true"
  # compute,utility is the default. Do not add profiling, rdma or graphics for reward sandboxes.
  nvproxy-allowed-driver-capabilities = "compute,utility"
EOF
else
  cat > /etc/containerd/runsc.toml <<'EOF'
# Read by containerd-shim-runsc-v1 through the runtime's ConfigPath option.
# CPU-only node: no GPU proxying.
[runsc_config]
EOF
fi

# nvproxy only accepts driver versions it knows. Warn early if the loaded driver is not one of
# them; the sandbox pod's GPU probe will fail closed in that case.
if [[ -r /sys/module/nvidia/version ]]; then
  driver="$(< /sys/module/nvidia/version)"
  if ! /usr/local/bin/runsc nvproxy list-supported-drivers 2>/dev/null | grep -wF -- "${driver}" >/dev/null; then
    echo "WARNING: NVIDIA driver ${driver} is not supported by gVisor ${GVISOR_RELEASE} nvproxy" >&2
  fi
fi
