#!/bin/bash
# Add the gVisor runtime handler (runsc) to a containerd config file, in the schema that file
# uses: version 3 (containerd 2.x) or version 2. Idempotent. Usage: register_runsc.sh <config>
# The handler name must match the RuntimeClass handler (k8s/runtimes/runtimeclass-gvisor-hyperpod.yaml).
set -euo pipefail

config="${1:?usage: $0 <containerd config.toml>}"
[[ -f "${config}" ]] || { echo "[gpu-sandbox] ${config} not found" >&2; exit 1; }
if grep -q 'runtimes\.runsc\]' "${config}"; then
  echo "[gpu-sandbox] runsc handler already present in ${config}"
  exit 0
fi

version="$(sed -n 's/^[[:space:]]*version[[:space:]]*=[[:space:]]*\([0-9][0-9]*\).*/\1/p' "${config}" | head -1)"
case "${version}" in
  3) plugin="plugins.'io.containerd.cri.v1.runtime'" ;;
  2) plugin='plugins."io.containerd.grpc.v1.cri"' ;;
  *) echo "[gpu-sandbox] ${config}: unsupported or missing config version '${version}'" >&2; exit 1 ;;
esac

cp -a "${config}" "${config}.pre-runsc"
cat >> "${config}" <<TOML

[${plugin}.containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"
[${plugin}.containerd.runtimes.runsc.options]
  TypeUrl = "io.containerd.runsc.v1.options"
  ConfigPath = "/etc/containerd/runsc.toml"
TOML

# containerd parses the file in "config dump"; restore the original if it does not.
if command -v containerd >/dev/null 2>&1 && ! containerd --config "${config}" config dump >/dev/null; then
  mv "${config}.pre-runsc" "${config}"
  echo "[gpu-sandbox] containerd rejected the edited ${config}; restored the original" >&2
  exit 1
fi
echo "[gpu-sandbox] runsc handler added to ${config} (config version ${version})"
