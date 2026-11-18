"""Settings for the CDK app, read from the same variables as scripts/config.env.

cdk/deploy.sh sources scripts/config.env and exports the scenario, so the numbered in-cluster
scripts and the CDK stack cannot drift apart on instance types or pinned versions.
"""

from __future__ import annotations

import ipaddress
import os
import re
from dataclasses import dataclass

# A: EC2 trainer + gVisor GPU nodes. B1: gVisor GPU nodes (trainer on HyperPod). B2: no EC2 GPU
# nodes (trainer and sandboxes on HyperPod). C: CPU only (the c8i node).
SCENARIOS = ("A", "B1", "B2", "C")

# CoreCount and ThreadsPerCore accompany NestedVirtualization in CpuOptions. Add other types after
# checking:
#   aws ec2 describe-instance-types --instance-types <type> \
#     --query 'InstanceTypes[0].VCpuInfo.[DefaultCores,DefaultThreadsPerCore]'
CPU_TOPOLOGY = {
    "c8i.2xlarge": (4, 2),  # 8 vCPUs; checked in us-west-2 on 2026-11-14
}


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None or value == "" or "__SET_ME__" in value:
        raise ValueError(f"set {name} in scripts/config.env (cdk/deploy.sh exports it)")
    return value


@dataclass(frozen=True)
class Settings:
    scenario: str
    cluster_name: str
    k8s_version: str
    admin_principal_arns: tuple[str, ...]
    gvisor_release: str
    system_instance_type: str
    trainer_instance_type: str
    gvisor_instance_type: str
    gvisor_nodes: int
    kata_cpu_instance_type: str
    with_kata_cpu: bool
    kata_gpu_instance_type: str
    kata_iommu_ami_id: str | None
    public_access_cidr: str | None

    @property
    def kata_cpu_topology(self) -> tuple[int, int]:
        if self.kata_cpu_instance_type not in CPU_TOPOLOGY:
            raise ValueError(
                f"add {self.kata_cpu_instance_type} (cores, threads per core) to CPU_TOPOLOGY in cdk/gpusandbox_cdk/config.py"
            )
        return CPU_TOPOLOGY[self.kata_cpu_instance_type]

    @staticmethod
    def _kata_gpu_ami() -> str | None:
        if os.environ.get("WITH_KATA_GPU", "0") != "1":
            return None
        ami = _env("KATA_IOMMU_AMI_ID")  # baked by infra/kata/build-iommu-ami.sh (scripts/kata/gpu_nodes.sh)
        if not re.fullmatch(r"ami-[0-9a-f]{8,17}", ami):
            raise ValueError("KATA_IOMMU_AMI_ID must be an AMI ID (ami-...)")
        return ami

    @classmethod
    def from_env(cls) -> Settings:
        scenario = _env("SCENARIO", "A").upper()
        if scenario not in SCENARIOS:
            raise ValueError(f"SCENARIO must be one of {SCENARIOS}")
        # Comma-separated: every listed IAM role or user gets the cluster admin access entry.
        principals = tuple(p.strip() for p in _env("ADMIN_PRINCIPAL_ARN").split(",") if p.strip())
        for principal in principals:
            if not re.fullmatch(r"arn:aws[a-z-]*:iam::\d{12}:(role|user)/.+", principal):
                raise ValueError("ADMIN_PRINCIPAL_ARN must list IAM role or user ARNs, not sts assumed-role ARNs")
        cidr = os.environ.get("EKS_PUBLIC_ACCESS_CIDR") or None
        if cidr is not None:
            network = ipaddress.ip_network(cidr, strict=True)
            # Opt-in only, and only for a single address (your workstation).
            if network.version != 4 or network.prefixlen != 32:
                raise ValueError("EKS_PUBLIC_ACCESS_CIDR must be a single IPv4 address in /32 form")
        return cls(
            scenario=scenario,
            cluster_name=_env("CLUSTER_NAME"),
            k8s_version=_env("K8S_VERSION"),
            admin_principal_arns=principals,
            gvisor_release=_env("GVISOR_RELEASE"),
            system_instance_type=_env("SYSTEM_INSTANCE_TYPE", "m6i.large"),
            trainer_instance_type=_env("TRAINER_INSTANCE_TYPE", "g5.2xlarge"),
            gvisor_instance_type=_env("GVISOR_INSTANCE_TYPE", "g5.xlarge"),
            gvisor_nodes=int(_env("GVISOR_NODES", "2")),
            kata_cpu_instance_type=_env("KATA_CPU_INSTANCE_TYPE", "c8i.2xlarge"),
            with_kata_cpu=scenario == "C" or os.environ.get("WITH_KATA_CPU", "0") == "1",
            kata_gpu_instance_type=_env("KATA_GPU_INSTANCE_TYPE", "g4dn.metal"),
            kata_iommu_ami_id=cls._kata_gpu_ami(),
            public_access_cidr=cidr,
        )
