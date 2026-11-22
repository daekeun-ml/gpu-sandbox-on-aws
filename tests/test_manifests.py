"""Render every template with every profile and check the result is valid, safe YAML."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
PROFILES = sorted((ROOT / "k8s/sandbox/profiles").glob("*.env"))
VERSIONS = sorted((ROOT / "k8s/sandbox/versions").glob("*.env"))
COMMON = {
    "SANDBOX_IMAGE_URI": "123456789012.dkr.ecr.us-west-2.amazonaws.com/gpu-sandbox/sandbox:v1",
    "OIDC_ISSUER": "https://oidc.eks.us-west-2.amazonaws.com/id/EXAMPLE",
    "SANDBOX_AUDIENCE": "gpu-sandbox",
    "SANDBOX_ALLOWED_SUBJECTS": "system:serviceaccount:rl-trainer:grpo-trainer",
}


def _load_env_file(path: Path) -> dict[str, str]:
    out = subprocess.run(
        ["bash", "-c", f"set -a; source '{path}'; env -0"],
        check=True, capture_output=True, env={"PATH": os.environ["PATH"]},
    ).stdout.decode()
    return dict(item.split("=", 1) for item in out.split("\0") if "=" in item)


def _render(template: str, env: dict[str, str]) -> list[dict]:
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/render.py"), str(ROOT / template)],
        check=True, capture_output=True, env={**os.environ, **env},
    ).stdout.decode()
    return [d for d in yaml.safe_load_all(out) if d]


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.stem)
@pytest.mark.parametrize("version", VERSIONS, ids=lambda p: p.stem)
def test_sandbox_pool_manifest(profile: Path, version: Path):
    env = {**COMMON, **_load_env_file(profile), **_load_env_file(version)}
    deployment, service = _render("k8s/sandbox/deployment.yaml.tpl", env)
    pod = deployment["spec"]["template"]["spec"]
    container = pod["containers"][0]
    envs = {e["name"]: e.get("value") for e in container["env"]}

    # Isolation and least privilege.
    assert pod["runtimeClassName"] == env["RUNTIME_CLASS"]
    assert pod["automountServiceAccountToken"] is False
    assert pod["securityContext"]["runAsNonRoot"] is True
    assert container["securityContext"]["readOnlyRootFilesystem"] is True
    assert container["securityContext"]["capabilities"]["drop"] == ["ALL"]
    # Egress self-test targets survive templating (Kubernetes expands $(NODE_IP) itself).
    assert envs["SANDBOX_EGRESS_PROBE_TARGETS"] == "169.254.169.254:80,apiserver,$(NODE_IP):10250"
    # Exposure: headless ClusterIP only.
    assert service["spec"]["clusterIP"] == "None"
    assert "type" not in service["spec"]
    # Accelerators only on GPU profiles, and requests == limits (guaranteed QoS for Kata sizing).
    limits, requests = container["resources"]["limits"], container["resources"]["requests"]
    assert limits == requests
    gpu_keys = {k for k in limits if k.startswith("nvidia.com/")}
    assert bool(gpu_keys) == (env["SANDBOX_DEVICE"] == "cuda")


def test_static_manifests_parse():
    for path in list((ROOT / "k8s").rglob("*.yaml")):
        docs = [d for d in yaml.safe_load_all(path.read_text()) if d]
        assert docs, path
        for doc in docs:
            assert "kind" in doc and "apiVersion" in doc, path
            spec = doc.get("spec") or {}
            assert spec.get("type") not in ("LoadBalancer", "NodePort"), f"{path} exposes a Service"


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.stem)
def test_agent_sandbox_template_renders(profile: Path):
    env = {**COMMON, **_load_env_file(profile), **_load_env_file(ROOT / "k8s/sandbox/versions/v1.env"),
           "WARM_REPLICAS": "1"}
    template, pool = _render("k8s/extensions/agent-sandbox/template.yaml.tpl", env)
    assert template["kind"] == "SandboxTemplate" and pool["kind"] == "SandboxWarmPool"
    assert pool["spec"]["sandboxTemplateRef"]["name"] == template["metadata"]["name"]
    spec = template["spec"]
    assert spec["networkPolicy"]["egress"] == [], "sandboxes get no egress at all"
    pod = spec["podTemplate"]["spec"]
    assert pod["runtimeClassName"] == env["RUNTIME_CLASS"]
    assert pod["automountServiceAccountToken"] is False and pod["dnsPolicy"] == "None"


def test_karpenter_nodeclasses_and_nodepools():
    env = {"KARPENTER_NODE_ROLE": "KarpenterNodeRole-gpu-sandbox", "CLUSTER_NAME": "gpu-sandbox",
           "GVISOR_RELEASE": "20261109.0", "KATA_IOMMU_AMI_ID": "ami-0123456789abcdef0"}
    classes = {d["metadata"]["name"]: d for d in _render("infra/karpenter/nodeclasses.yaml.tpl", env)}
    assert set(classes) == {"sandbox-gvisor", "sandbox-kata-gpu", "sandbox-kata-cpu", "trainer"}
    # An AMI chosen by ID needs amiFamily; an alias implies it.
    for name, nc in classes.items():
        terms = nc["spec"]["amiSelectorTerms"]
        assert any("alias" in t for t in terms) or nc["spec"].get("amiFamily") == "AL2023", name
    assert classes["sandbox-kata-cpu"]["spec"]["cpuOptions"] == {"nestedVirtualization": "enabled"}
    gvisor_ud = classes["sandbox-gvisor"]["spec"]["userData"]
    assert "runtimes.runsc" in gvisor_ud and 'GVISOR_RELEASE="20261109.0"' in gvisor_ud
    for name in ("sandbox-gvisor", "sandbox-kata-gpu", "sandbox-kata-cpu"):
        assert "GPUSANDBOX-GUARD" in classes[name]["spec"]["userData"], name

    pools = {d["metadata"]["name"]: d for d in yaml.safe_load_all((ROOT / "infra/karpenter/nodepools.yaml").read_text()) if d}
    for name, pool in pools.items():
        ref = pool["spec"]["template"]["spec"]["nodeClassRef"]["name"]
        assert ref in classes, f"{name} references unknown EC2NodeClass {ref}"
        assert pool["spec"]["template"]["spec"]["taints"], f"{name} must be a dedicated, tainted pool"


def test_routing_table_has_v1_and_v2_for_every_profile():
    """Every deployable profile can be activated and rolled forward (06_deploy_sandboxes.sh, ops/rollout.sh)."""
    import json

    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/render.py"), str(ROOT / "k8s/base/routing.json.tpl")],
        check=True, capture_output=True,
        env={**os.environ, "ACTIVE_RUNTIME": "kata-clh-cpu", "ACTIVE_VERSION": "v1"},
    ).stdout.decode()
    pools = json.loads(out)["pools"]
    versions = {v.stem for v in VERSIONS}
    for profile in PROFILES:
        runtime = _load_env_file(profile)["RUNTIME"]
        assert set(pools.get(runtime, {})) == versions, runtime
        for version, address in pools[runtime].items():
            # Must match the Service name in k8s/sandbox/deployment.yaml.tpl.
            assert address == f"sandbox-{runtime}-{version}.sandbox.svc.cluster.local:8000"


def test_operator_job_reads_the_routing_table():
    (job,) = _render("k8s/probe/job-probe.yaml.tpl", {
        "JOB_NAME": "simulate-1", "CONTROL_IMAGE_URI": "example/control:v1",
        "TOOL_ARGS": '["simulate", "--steps", "2"]', "SANDBOX_AUDIENCE": "gpu-sandbox",
    })
    pod = job["spec"]["template"]["spec"]
    container = pod["containers"][0]
    envs = {e["name"]: e["value"] for e in container["env"]}
    mounts = {m["name"]: m for m in container["volumeMounts"]}
    volumes = {v["name"]: v for v in pod["volumes"]}
    assert envs["SANDBOX_ROUTING_FILE"] == "/etc/gpusandbox/routing/routing.json"
    assert mounts["routing"]["mountPath"] == "/etc/gpusandbox/routing" and "subPath" not in mounts["routing"]
    # probe, parity and bench do not need the table, so the Job must start without it.
    assert volumes["routing"]["configMap"] == {"name": "sandbox-routing", "optional": True}
    assert container["args"] == ["simulate", "--steps", "2"]
    # The GRPO trainer Job reads the same table (directory mount, so ConfigMap updates arrive) and
    # meets Pod Security "restricted", which the rl-trainer namespace warns on.
    (trainer,) = _render("k8s/trainer/job-grpo.yaml.tpl", {
        "RUN_ID": "test", "TRAINER_IMAGE_URI": "example/trainer:v1", "MAX_STEPS": "5",
        "MODEL_ID": "Qwen/Qwen2.5-Coder-1.5B-Instruct", "SANDBOX_AUDIENCE": "gpu-sandbox",
    })
    tpod = trainer["spec"]["template"]["spec"]
    (tcontainer,) = tpod["containers"]
    tmounts = {m["name"]: m for m in tcontainer["volumeMounts"]}
    assert tmounts["routing"]["mountPath"] == "/etc/gpusandbox/routing" and "subPath" not in tmounts["routing"]
    assert tpod["securityContext"] == {"runAsNonRoot": True, "runAsUser": 2000,
                                       "seccompProfile": {"type": "RuntimeDefault"}}
    assert tcontainer["securityContext"] == {"allowPrivilegeEscalation": False, "capabilities": {"drop": ["ALL"]}}


def _multiturn_job() -> dict:
    (job,) = _render("k8s/extensions/agent-sandbox/job-multiturn.yaml.tpl", {
        "JOB_NAME": "episodes-1", "CONTROL_IMAGE_URI": "example/control:v1",
        "TOOL_ARGS": '["multiturn", "--warm-pool", "kernel-eval-gvisor-cpu"]',
        "SANDBOX_AUDIENCE": "gpu-sandbox",
    })
    return job


def test_multiturn_job_has_an_api_token_and_stays_hardened():
    job = _multiturn_job()
    pod = job["spec"]["template"]["spec"]
    (container,) = pod["containers"]
    assert job["metadata"]["namespace"] == "rl-trainer" and job["spec"]["backoffLimit"] == 0
    # The sandbox NetworkPolicies admit only labelled clients from rl-trainer.
    assert job["spec"]["template"]["metadata"]["labels"]["gpusandbox/client"] == "true"
    # It creates and deletes SandboxClaims, so unlike the probe Job it mounts an API token.
    assert pod["serviceAccountName"] == "sandbox-episode" and pod["automountServiceAccountToken"] is True
    assert pod["securityContext"]["runAsNonRoot"] is True
    assert pod["securityContext"]["seccompProfile"] == {"type": "RuntimeDefault"}
    assert container["securityContext"] == {"allowPrivilegeEscalation": False, "readOnlyRootFilesystem": True,
                                            "capabilities": {"drop": ["ALL"]}}
    envs = {e["name"]: e["value"] for e in container["env"]}
    (token,) = pod["volumes"][0]["projected"]["sources"]
    assert token["serviceAccountToken"]["audience"] == "gpu-sandbox"
    assert envs["SANDBOX_TOKEN_FILE"] == "/var/run/secrets/gpusandbox/" + token["serviceAccountToken"]["path"]
    assert container["command"] == ["python", "-m", "gpusandbox.tools"]
    assert container["args"][0] == "multiturn"


def test_episode_account_may_manage_claims_and_nothing_else():
    role, binding = [d for d in yaml.safe_load_all(
        (ROOT / "k8s/extensions/agent-sandbox/trainer-claims-rbac.yaml").read_text()) if d]
    assert role["kind"] == "Role" and role["metadata"]["namespace"] == "sandbox"
    assert role["rules"] == [{"apiGroups": ["extensions.agents.x-k8s.io"], "resources": ["sandboxclaims"],
                              "verbs": ["create", "get", "list", "watch", "delete"]}]
    assert binding["roleRef"]["name"] == role["metadata"]["name"]
    subjects = {(s["namespace"], s["name"]) for s in binding["subjects"]}
    assert subjects == {("rl-trainer", "grpo-trainer"), ("rl-trainer", "sandbox-episode")}

    pod = _multiturn_job()["spec"]["template"]["spec"]
    accounts = {(d["metadata"]["namespace"], d["metadata"]["name"]): d for d in yaml.safe_load_all(
        (ROOT / "k8s/base/trainer-rbac.yaml").read_text()) if d}
    account = accounts[("rl-trainer", pod["serviceAccountName"])]
    assert ("rl-trainer", pod["serviceAccountName"]) in subjects
    # Off by default: only the episode Job's pod spec opts in to the API token.
    assert account["automountServiceAccountToken"] is False


def test_episode_account_is_on_the_warm_pool_allowlist():
    """The pool default must admit the Job's ServiceAccount, or every episode turn gets 403."""
    import re

    script = (ROOT / "scripts/extensions/agent_sandbox.sh").read_text()
    subject = re.search(r'^EPISODE_SUBJECT="([^"]+)"', script, re.MULTILINE).group(1)
    pod = _multiturn_job()["spec"]["template"]["spec"]
    assert subject == f"system:serviceaccount:rl-trainer:{pod['serviceAccountName']}"
    (default,) = [line for line in script.splitlines()
                  if 'SANDBOX_ALLOWED_SUBJECTS="${SANDBOX_ALLOWED_SUBJECTS:-' in line]
    assert "${EPISODE_SUBJECT}" in default
    assert "system:serviceaccount:rl-trainer:grpo-trainer" in default


def _userdata():
    sys.path.insert(0, str(ROOT / "infra/eks"))
    import userdata
    return userdata


def _parts(user_data: str) -> list[str]:
    return [p for p in user_data.split("--GPUSANDBOX") if p.strip() and p.strip() != "--"]


def test_nested_cpu_node_user_data():
    """c8i node (CDK launch template): kata-deploy drop-ins, runsc handler, gVisor without nvproxy, guard."""
    parts = _parts(_userdata().nested_cpu_node("20261109.0"))
    node_config = yaml.safe_load(parts[1].split("\n\n", 1)[1])
    containerd = node_config["spec"]["containerd"]["config"]
    assert 'imports = ["/etc/containerd/conf.d/*.toml"]' in containerd
    assert "runtimes.runsc]" in containerd and "ConfigPath = '/etc/containerd/runsc.toml'" in containerd
    gvisor_part = next(p for p in parts if "GVISOR_RELEASE=" in p)
    assert 'export GVISOR_RELEASE="20261109.0"' in gvisor_part and 'export GVISOR_NVPROXY="false"' in gvisor_part
    assert "sha512sum -c" in gvisor_part
    assert any("GPUSANDBOX-GUARD" in p for p in parts), "node guard missing"


def test_gvisor_gpu_node_user_data():
    parts = _parts(_userdata().gvisor_gpu_node("20261109.0"))
    node_config = yaml.safe_load(parts[1].split("\n\n", 1)[1])
    assert "runtimes.runsc]" in node_config["spec"]["containerd"]["config"]
    assert any('export GVISOR_NVPROXY="true"' in p for p in parts)
    assert any("GPUSANDBOX-GUARD" in p for p in parts)


def test_kata_gpu_node_user_data_carries_the_cluster_fields():
    """With a custom AMI EKS merges nothing, so nodeadm needs the cluster fields from us."""
    parts = _parts(_userdata().kata_gpu_node("gpu-sandbox", "https://X.eks.amazonaws.com", "Q0E=", "172.20.0.0/16"))
    node_config = yaml.safe_load(parts[1].split("\n\n", 1)[1])
    assert node_config["spec"]["cluster"] == {"name": "gpu-sandbox", "apiServerEndpoint": "https://X.eks.amazonaws.com",
                                              "certificateAuthority": "Q0E=", "cidr": "172.20.0.0/16"}
    assert node_config["spec"]["kubelet"]["config"]["runtimeRequestTimeout"] == "20m"
    assert any("GPUSANDBOX-GUARD" in p for p in parts)
    assert not any("runsc" in p for p in parts), "no gVisor on the Kata GPU node"


HYPERPOD_ENV = {
    "HYPERPOD_CLUSTER_NAME": "gpu-sandbox-hp", "EKS_CLUSTER_ARN": "arn:aws:eks:us-west-2:123456789012:cluster/gpu-sandbox",
    "HYPERPOD_TRAINER_INSTANCE_TYPE": "ml.g5.2xlarge", "HYPERPOD_LCS_BUCKET": "sagemaker-gpu-sandbox-lcs-test",
    "HYPERPOD_EXECUTION_ROLE_ARN": "arn:aws:iam::123456789012:role/gpu-sandbox-hp-execution",
    "HYPERPOD_SECURITY_GROUP_ID": "sg-0123456789abcdef0", "HYPERPOD_SUBNET_ID": "subnet-0123456789abcdef0",
    "HYPERPOD_SANDBOX_INSTANCE_TYPE": "ml.g5.xlarge", "HYPERPOD_SANDBOX_COUNT": "2",
    "HYPERPOD_B2_AMI_ID": "ami-0123456789abcdef0",
}


def test_hyperpod_trainer_leaves_room_for_the_operator_and_pod_manager():
    env = {**COMMON, **HYPERPOD_ENV, "RUN_ID": "smoke", "TRAINER_IMAGE_URI": "trainer:test",
           "MODEL_ID": "test", "MAX_STEPS": "1"}
    (job,) = _render("k8s/trainer/hyperpod-job-grpo.yaml.tpl", env)
    (container,) = job["spec"]["replicaSpecs"][0]["template"]["spec"]["containers"]
    assert container["resources"]["requests"] == {"nvidia.com/gpu": "1", "cpu": "5", "memory": "24Gi"}


def test_hyperpod_b2_sandbox_group_matches_runtimeclass_and_device_plugin():
    """The B2 instance group's label and taint are what the RuntimeClass and the CDI plugin expect."""
    (cluster,) = _render("infra/hyperpod/cluster.json.tpl", HYPERPOD_ENV)
    assert {"Key": "SageMaker", "Value": "true"} in cluster["Tags"]  # training operator's IAM policy
    (group,) = _render("infra/hyperpod/instance-group-sandbox.json.tpl", HYPERPOD_ENV)
    assert [g["InstanceGroupName"] for g in cluster["InstanceGroups"]] == ["trainer"]
    assert "ImageId" not in cluster["InstanceGroups"][0], "the trainer keeps the default HyperPod AMI"
    assert group["ImageId"] == "ami-0123456789abcdef0" and group["InstanceCount"] == 2
    assert (ROOT / "infra/hyperpod/lifecycle" / group["LifeCycleConfig"]["OnCreate"]).is_file()

    runtime_class = yaml.safe_load((ROOT / "k8s/runtimes/runtimeclass-gvisor-hyperpod.yaml").read_text())
    labels = group["KubernetesConfig"]["Labels"]
    (taint,) = group["KubernetesConfig"]["Taints"]
    assert runtime_class["handler"] == "runsc"
    assert runtime_class["scheduling"]["nodeSelector"].items() <= labels.items()
    (toleration,) = runtime_class["scheduling"]["tolerations"]
    assert (toleration["key"], toleration["value"], toleration["effect"]) == (taint["Key"], taint["Value"], taint["Effect"])
    plugin = yaml.safe_load((ROOT / "infra/gpu/nvidia-device-plugin-values.yaml").read_text())
    assert plugin["nodeSelector"].items() <= labels.items(), "the CDI device plugin must run on B2 nodes"
    assert any(t["key"] == taint["Key"] and t["operator"] == "Exists" for t in plugin["tolerations"])
    profile = _load_env_file(ROOT / "k8s/sandbox/profiles/gvisor-hyperpod.env")
    assert profile["RUNTIME_CLASS"] == runtime_class["metadata"]["name"]


@pytest.mark.parametrize("version,plugin", [
    ("3", "io.containerd.cri.v1.runtime"),
    ("2", "io.containerd.grpc.v1.cri"),
])
def test_register_runsc_writes_the_schema_of_the_config(tmp_path: Path, version: str, plugin: str):
    import tomllib

    config = tmp_path / "config.toml"
    config.write_text(f'version = {version}\nroot = "/var/lib/containerd"\n')
    script = ROOT / "infra/hyperpod/lifecycle/register_runsc.sh"
    env = {"PATH": "/usr/bin:/bin"}  # no containerd binary here, so the dump check is skipped
    for _ in range(2):  # idempotent
        subprocess.run(["bash", str(script), str(config)], check=True, capture_output=True, env=env)
    parsed = tomllib.loads(config.read_text())
    runsc = parsed["plugins"][plugin]["containerd"]["runtimes"]["runsc"]
    assert runsc["runtime_type"] == "io.containerd.runsc.v1"
    assert runsc["options"] == {"TypeUrl": "io.containerd.runsc.v1.options", "ConfigPath": "/etc/containerd/runsc.toml"}
    assert config.read_text().count("runtimes.runsc]") == 1


def test_register_runsc_refuses_an_unknown_config_version(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text('root = "/var/lib/containerd"\n')
    result = subprocess.run(["bash", str(ROOT / "infra/hyperpod/lifecycle/register_runsc.sh"), str(config)],
                            capture_output=True, env={"PATH": "/usr/bin:/bin"})
    assert result.returncode == 1 and b"unsupported or missing config version" in result.stderr
    assert "runsc" not in config.read_text()


def test_b2_ami_builder_user_data(tmp_path: Path):
    """Assemble the B2 builder's user data offline: pins first, valid bash, under the 16 KB limit."""
    import re

    script = (ROOT / "infra/hyperpod/ami/build-b2-ami.sh").read_text()
    builder = re.search(r"<<'PY'\n(.*?)\nPY\n", script, re.DOTALL).group(1)
    out = subprocess.run(
        [sys.executable, "-c", builder, str(ROOT / "infra/hyperpod/ami/customize-b2.sh"),
         str(ROOT / "infra/gvisor/install-gvisor.sh"), "580.178.04", "a" * 64, "20261109.0"],
        check=True, capture_output=True,
    ).stdout.decode()
    head = out.splitlines()[:4]
    assert head == ["#!/bin/bash", 'export B2_NVIDIA_DRIVER_VERSION="580.178.04"',
                    f'export B2_NVIDIA_RUNFILE_SHA256="{"a" * 64}"', 'export GVISOR_RELEASE="20261109.0"']
    assert "sha512sum -c gvisor.tar.bz2.sha512" in out and "GPUSANDBOX-B2-BUILD: OK" in out
    assert len(out.encode()) < 16 * 1024, "EC2 user data is limited to 16 KB before base64"
    user_data = tmp_path / "user-data.sh"
    user_data.write_text(out)
    subprocess.run(["bash", "-n", str(user_data)], check=True)


def test_b2_pins_agree():
    """The pinned driver is one the pinned gVisor supports, per the facts this repo was built on."""
    env = _load_env_file(ROOT / "scripts/config.env.example")
    assert env["B2_NVIDIA_DRIVER_VERSION"] == "580.178.04"
    assert env["GVISOR_RELEASE"] == "20261109.0"
    assert len(env["B2_NVIDIA_RUNFILE_SHA256"]) == 64
