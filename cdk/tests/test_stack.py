"""Synthesize the stack offline and assert its security defaults (no AWS calls)."""

from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION", "1")
cdk = pytest.importorskip("aws_cdk")
from aws_cdk.assertions import Match, Template  # noqa: E402
from cdk_nag import AwsSolutionsChecks  # noqa: E402

from gpusandbox_cdk.config import Settings  # noqa: E402
from gpusandbox_cdk.stack import GpuSandboxStack  # noqa: E402

BASE = {
    "CLUSTER_NAME": "gpu-sandbox", "K8S_VERSION": "1.36", "GVISOR_RELEASE": "20261109.0",
    "ADMIN_PRINCIPAL_ARN": "arn:aws:iam::123456789012:role/Admin",
}


def synth(monkeypatch, **env) -> tuple[Template, cdk.Stack]:
    for key in ("EKS_PUBLIC_ACCESS_CIDR", "WITH_KATA_CPU", "WITH_KATA_GPU", "KATA_IOMMU_AMI_ID", "SCENARIO"):
        monkeypatch.delenv(key, raising=False)
    for key, value in {**BASE, **env}.items():
        monkeypatch.setenv(key, value)
    app = cdk.App()
    stack = GpuSandboxStack(app, "test", settings=Settings.from_env())
    return Template.from_stack(stack), stack


@pytest.mark.parametrize("scenario,groups", [
    ("A", {"system", "trainer", "sandbox-gvisor"}),
    ("B1", {"system", "sandbox-gvisor"}),
    ("B2", {"system"}),
    ("C", {"system", "sandbox-kata-cpu"}),
])
def test_scenarios_create_the_expected_node_groups(monkeypatch, scenario, groups):
    template, _ = synth(monkeypatch, SCENARIO=scenario)
    names = {ng["Properties"]["NodegroupName"] for ng in template.find_resources("AWS::EKS::Nodegroup").values()}
    assert names == groups


def test_api_endpoint_is_private_by_default(monkeypatch):
    template, _ = synth(monkeypatch, SCENARIO="C")
    template.has_resource_properties("AWS::EKS::Cluster", {
        "Version": "1.36",
        "BootstrapSelfManagedAddons": False,
        "ResourcesVpcConfig": {"EndpointPublicAccess": False, "EndpointPrivateAccess": True,
                               "PublicAccessCidrs": Match.absent()},
        "AccessConfig": {"AuthenticationMode": "API_AND_CONFIG_MAP", "BootstrapClusterCreatorAdminPermissions": False},
        "EncryptionConfig": [{"Resources": Match.absent(), "Provider": Match.any_value()}],
        "Logging": {"ClusterLogging": {"EnabledTypes": Match.array_with([{"Type": "audit"}])}},
    })


def test_public_endpoint_is_opt_in_and_single_address(monkeypatch):
    template, _ = synth(monkeypatch, SCENARIO="C", EKS_PUBLIC_ACCESS_CIDR="203.0.113.10/32")
    template.has_resource_properties("AWS::EKS::Cluster", {
        "ResourcesVpcConfig": {"EndpointPublicAccess": True, "PublicAccessCidrs": ["203.0.113.10/32"]}})
    for wide in ("0.0.0.0/0", "203.0.113.0/24"):
        monkeypatch.setenv("EKS_PUBLIC_ACCESS_CIDR", wide)
        with pytest.raises(ValueError):
            Settings.from_env()


def test_no_ingress_from_anywhere(monkeypatch):
    template, _ = synth(monkeypatch, SCENARIO="A", WITH_KATA_CPU="1")
    rendered = json.dumps(template.to_json())
    for sg in template.find_resources("AWS::EC2::SecurityGroup").values():
        for rule in sg["Properties"].get("SecurityGroupIngress", []):
            assert rule.get("CidrIp") not in ("0.0.0.0/0",) and rule.get("CidrIpv6") != "::/0", rule
    for rule in template.find_resources("AWS::EC2::SecurityGroupIngress").values():
        assert rule["Properties"].get("CidrIp") != "0.0.0.0/0", rule
    assert '"AssociatePublicIpAddress": true' not in rendered


def test_every_launch_template_requires_imdsv2_and_encrypts(monkeypatch):
    template, _ = synth(monkeypatch, SCENARIO="A", WITH_KATA_CPU="1")
    lts = template.find_resources("AWS::EC2::LaunchTemplate")
    assert len(lts) >= 4  # system, trainer, sandbox-gvisor, sandbox-kata-cpu (+ access instance)
    for lt in lts.values():
        data = lt["Properties"]["LaunchTemplateData"]
        assert data["MetadataOptions"]["HttpTokens"] == "required"
        if "HttpPutResponseHopLimit" in data["MetadataOptions"]:
            assert data["MetadataOptions"]["HttpPutResponseHopLimit"] == 1
        for bdm in data.get("BlockDeviceMappings", []):
            assert bdm["Ebs"]["Encrypted"] is True


def test_nested_virtualization_node(monkeypatch):
    template, _ = synth(monkeypatch, SCENARIO="C")
    template.has_resource_properties("AWS::EC2::LaunchTemplate", {"LaunchTemplateData": {
        "CpuOptions": {"CoreCount": 4, "ThreadsPerCore": 2, "NestedVirtualization": "enabled"}}})


def test_public_subnets_do_not_map_public_ips_and_flow_logs_exist(monkeypatch):
    template, _ = synth(monkeypatch, SCENARIO="C")
    for subnet in template.find_resources("AWS::EC2::Subnet").values():
        assert subnet["Properties"].get("MapPublicIpOnLaunch") in (False, None)
    template.resource_count_is("AWS::EC2::FlowLog", 1)


@pytest.mark.parametrize("scenario", ["A", "B1", "B2", "C"])
def test_cdk_nag_passes_with_only_documented_acknowledgements(monkeypatch, tmp_path, scenario):
    """Policy validation fails synth on any unacknowledged AwsSolutions error (as cdk deploy would)."""
    synth(monkeypatch, SCENARIO=scenario, WITH_KATA_CPU="1")  # sets the environment
    app = cdk.App(outdir=str(tmp_path))
    GpuSandboxStack(app, "test", settings=Settings.from_env())
    cdk.Validations.of(app).add_plugins(AwsSolutionsChecks(app))
    app.synth()  # raises ValidationFailed on an unacknowledged finding


def test_settings_reject_an_assumed_role_session_arn(monkeypatch):
    for key, value in BASE.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("ADMIN_PRINCIPAL_ARN", "arn:aws:sts::123456789012:assumed-role/Admin/me")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_each_listed_principal_gets_one_access_entry(monkeypatch):
    arns = "arn:aws:iam::123456789012:role/Admin, arn:aws:iam::123456789012:user/operator"
    template, _ = synth(monkeypatch, SCENARIO="C", ADMIN_PRINCIPAL_ARN=arns)
    entries = template.find_resources("AWS::EKS::AccessEntry")
    assert sorted(e["Properties"]["PrincipalArn"] for e in entries.values()) == [
        "arn:aws:iam::123456789012:role/Admin", "arn:aws:iam::123456789012:user/operator"]


def test_kata_gpu_node_group_on_the_iommu_ami(monkeypatch):
    """With a custom AMI EKS merges no bootstrap, so the user data must carry the cluster fields."""
    template, _ = synth(monkeypatch, SCENARIO="A", WITH_KATA_GPU="1", KATA_IOMMU_AMI_ID="ami-0123456789abcdef0")
    groups = {ng["Properties"]["NodegroupName"]: ng["Properties"]
              for ng in template.find_resources("AWS::EKS::Nodegroup").values()}
    gpu = groups["sandbox-kata-gpu"]
    assert gpu["AmiType"] == "CUSTOM" and gpu["InstanceTypes"] == ["g4dn.metal"]
    assert gpu["Labels"]["nvidia.com/gpu.workload.config"] == "vm-passthrough"
    lts = [lt["Properties"]["LaunchTemplateData"] for lt in template.find_resources("AWS::EC2::LaunchTemplate").values()]
    (data,) = [d for d in lts if d.get("ImageId") == "ami-0123456789abcdef0"]
    rendered = json.dumps(data["UserData"])
    for needle in ("apiServerEndpoint", "certificateAuthority", "cidr: 172.20.0.0/16", "runtimeRequestTimeout: 20m",
                   "GPUSANDBOX-GUARD", "Fn::GetAtt"):
        assert needle in rendered, needle
    template.has_resource_properties("AWS::EKS::Cluster", {
        "KubernetesNetworkConfig": {"ServiceIpv4Cidr": "172.20.0.0/16"}})


def test_kata_gpu_requires_the_iommu_ami(monkeypatch):
    for key, value in {**BASE, "SCENARIO": "A", "WITH_KATA_GPU": "1"}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("KATA_IOMMU_AMI_ID", raising=False)
    with pytest.raises(ValueError):
        Settings.from_env()
