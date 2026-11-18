"""MIME user data for the sandbox node groups, shared by the shell path and the CDK app.

EKS merges its own bootstrap into MIME multipart user data when the launch template sets no
AMI, so these documents carry only what the sandbox nodes add: a NodeConfig part (containerd
runtime handlers, merged by nodeadm on every boot) and shell parts that run once per instance
between nodeadm-config and nodeadm-run.

Used by the CDK stack (cdk/gpusandbox_cdk/stack.py) and its tests.
Standard library only.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = "GPUSANDBOX"

# containerd 2.x (config schema v3). The handler name must match the RuntimeClass handler.
RUNSC_HANDLER = """[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runsc]
  runtime_type = 'io.containerd.runsc.v1'
[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runsc.options]
  TypeUrl = 'io.containerd.runsc.v1.options'
  ConfigPath = '/etc/containerd/runsc.toml'"""


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.splitlines())


def node_config(containerd_config: str) -> str:
    return (
        "apiVersion: node.eks.aws/v1alpha1\n"
        "kind: NodeConfig\n"
        "spec:\n"
        "  containerd:\n"
        "    config: |\n"
        f"{_indent(containerd_config, 6)}\n"
    )


def gvisor_install(release: str, nvproxy: bool, root: Path = REPO_ROOT) -> str:
    installer = (root / "infra/gvisor/install-gvisor.sh").read_text()
    return (
        "#!/bin/bash\n"
        f'export GVISOR_RELEASE="{release}"\n'
        f'export GVISOR_NVPROXY="{"true" if nvproxy else "false"}"\n'
        f"{installer}"
    )


def node_guard(root: Path = REPO_ROOT) -> str:
    return (root / "infra/eks/node-guard.sh").read_text()


def mime(parts: list[tuple[str, str]]) -> str:
    """parts: (content type, body). Shell parts use text/x-shellscript."""
    out = ["MIME-Version: 1.0", f'Content-Type: multipart/mixed; boundary="{BOUNDARY}"', ""]
    for content_type, body in parts:
        if content_type == "text/x-shellscript":
            content_type = 'text/x-shellscript; charset="us-ascii"'
        out += [f"--{BOUNDARY}", f"Content-Type: {content_type}", "", body.rstrip("\n"), ""]
    out.append(f"--{BOUNDARY}--")
    return "\n".join(out) + "\n"


def gvisor_gpu_node(gvisor_release: str, root: Path = REPO_ROOT) -> str:
    """g5 or g6 sandbox node: runsc handler, pinned gVisor with nvproxy, node guard."""
    return mime([
        ("application/node.eks.aws", node_config(RUNSC_HANDLER)),
        ("text/x-shellscript", gvisor_install(gvisor_release, nvproxy=True, root=root)),
        ("text/x-shellscript", node_guard(root)),
    ])


def nested_cpu_node(gvisor_release: str, root: Path = REPO_ROOT) -> str:
    """c8i nested-virtualization node: kata-deploy drop-in imports plus runsc (no nvproxy)."""
    containerd = 'imports = ["/etc/containerd/conf.d/*.toml"]\n' + RUNSC_HANDLER
    return mime([
        ("application/node.eks.aws", node_config(containerd)),
        ("text/x-shellscript", "#!/bin/bash\nset -euo pipefail\ninstall -d -m 0755 /etc/containerd/conf.d\n"),
        ("text/x-shellscript", gvisor_install(gvisor_release, nvproxy=False, root=root)),
        ("text/x-shellscript", node_guard(root)),
    ])


def kata_gpu_node(cluster_name: str, api_endpoint: str, certificate_authority: str, service_cidr: str,
                  root: Path = REPO_ROOT) -> str:
    """g4dn.metal on the IOMMU AMI. With a custom AMI, EKS does not merge its bootstrap, so the
    NodeConfig carries the cluster fields itself. The values may be CDK tokens."""
    config = (
        "apiVersion: node.eks.aws/v1alpha1\n"
        "kind: NodeConfig\n"
        "spec:\n"
        "  cluster:\n"
        f"    name: {cluster_name}\n"
        f"    apiServerEndpoint: {api_endpoint}\n"
        f"    certificateAuthority: {certificate_authority}\n"
        f"    cidr: {service_cidr}\n"
        "  containerd:\n"
        "    # nodeadm rewrites config.toml on every boot; the drop-in import keeps kata-deploy's handlers.\n"
        "    config: |\n"
        '      imports = ["/etc/containerd/conf.d/*.toml"]\n'
        "  kubelet:\n"
        "    config:\n"
        "      # VFIO pins all guest memory before a GPU VM boots, which can take minutes.\n"
        "      runtimeRequestTimeout: 20m\n"
    )
    return mime([
        ("application/node.eks.aws", config),
        ("text/x-shellscript", "#!/bin/bash\nset -euo pipefail\ninstall -d -m 0755 /etc/containerd/conf.d\n"),
        ("text/x-shellscript", node_guard(root)),
    ])


if __name__ == "__main__":
    # python3 infra/eks/userdata.py nested-cpu <gvisor release>
    kind, release = sys.argv[1], sys.argv[2]
    builders = {"nested-cpu": nested_cpu_node, "gvisor-gpu": gvisor_gpu_node}
    sys.stdout.write(builders[kind](release))
