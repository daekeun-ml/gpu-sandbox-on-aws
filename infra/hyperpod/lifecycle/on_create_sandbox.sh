#!/bin/bash
# Lifecycle script of the HyperPod sandbox instance group (scenario B2).
#
# The instance group boots from the custom AMI built by scripts/hyperpod/build_b2_ami.sh,
# which already carries an NVIDIA driver that gVisor nvproxy supports and the pinned gVisor
# binaries. This script wires them into the node:
#   1. checks that the loaded driver is on runsc's nvproxy supported list (fails otherwise)
#   2. writes /etc/containerd/runsc.toml and registers the runsc handler with containerd
#   3. installs the node guard (drops new pod-to-node connections, as on the EC2 sandbox nodes)
#   4. restarts containerd
# It fails loudly instead of skipping: a sandbox node without gVisor must not join silently.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
echo "[gpu-sandbox] on_create_sandbox start: $(date -Is)"

command -v runsc >/dev/null || { echo "[gpu-sandbox] runsc missing: is this the B2 custom AMI?" >&2; exit 1; }
driver="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
if ! runsc nvproxy list-supported-drivers | grep -qwF "${driver}"; then
  echo "[gpu-sandbox] NVIDIA driver ${driver} is not supported by $(runsc --version | head -1)" >&2
  exit 1
fi

# The config containerd was started with, else the containerd default path.
config="${HYPERPOD_CONTAINERD_CONFIG:-}"
if [[ -z "${config}" ]]; then
  config="$(ps -o args= -C containerd | sed -n 's/.*\(--config\|-c\)[ =]\([^ ]*\).*/\2/p' | head -1)"
fi
config="${config:-/etc/containerd/config.toml}"

cat > /etc/containerd/runsc.toml <<'TOML'
# Read by containerd-shim-runsc-v1 through the runtime's ConfigPath option.
[runsc_config]
  nvproxy = "true"
  # compute,utility is the default. Do not add profiling, rdma or graphics for reward sandboxes.
  nvproxy-allowed-driver-capabilities = "compute,utility"
TOML
"${here}/register_runsc.sh" "${config}"
bash "${here}/node-guard.sh"
systemctl restart containerd

echo "[gpu-sandbox] gVisor ready for driver ${driver} (${config}): $(date -Is)"
