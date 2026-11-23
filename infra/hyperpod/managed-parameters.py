"""Render parameters for the SageMaker HyperPod EKS creation template."""

import json
import os


def instance_group(name, instance_type, count, role, lifecycle_uri):
    labels = {"gpusandbox/role": role}
    kubernetes = {"Labels": labels}
    on_create = "on_create.sh"
    if name == "sandbox":
        labels["gpusandbox/device-plugin"] = "cdi"
        kubernetes["Taints"] = [{"Key": "gpusandbox/role", "Value": role, "Effect": "NoSchedule"}]
        on_create = "sandbox-bootstrap.sh"
    return {
        "InstanceGroupName": name,
        "InstanceType": instance_type,
        "InstanceCount": count,
        "ThreadsPerCore": 2,
        "KubernetesConfig": kubernetes,
        "LifeCycleConfig": {"SourceS3Uri": lifecycle_uri, "OnCreate": on_create},
    }


def parameters(env):
    # The AWS template joins ResourceNamePrefix and EKSClusterName with a hyphen.
    prefix, sep, suffix = env["CLUSTER_NAME"].rpartition("-")
    if not sep or not prefix or not suffix:
        raise ValueError("CLUSTER_NAME needs a prefix and suffix, for example gpu-sandbox-b2-eks")
    bucket = env["HYPERPOD_LCS_BUCKET"]
    lifecycle = f"s3://{bucket}/lifecycle/"
    groups = [
        instance_group("system", env.get("HYPERPOD_SYSTEM_INSTANCE_TYPE", "ml.m5.xlarge"),
                       1, "system", lifecycle),
        instance_group("trainer", env["HYPERPOD_TRAINER_INSTANCE_TYPE"], 1, "trainer", lifecycle),
        instance_group("sandbox", env["HYPERPOD_SANDBOX_INSTANCE_TYPE"],
                       int(env["HYPERPOD_SANDBOX_COUNT"]), "sandbox-hyperpod", lifecycle),
    ]
    return {
        "ResourceNamePrefix": prefix,
        "ResourceNameShortPrefix": prefix.replace("-", "")[:12],
        "AvailabilityZoneIds": env["HYPERPOD_AZ_IDS"],
        "EKSClusterName": suffix,
        "KubernetesVersion": env["K8S_VERSION"],
        "HyperPodClusterName": env["HYPERPOD_CLUSTER_NAME"],
        "InstanceGroupSettings1": json.dumps(groups, separators=(",", ":")),
        "S3BucketName": bucket,
        "OnCreatePath": "lifecycle/on_create.sh",
        "CreateVPCStack": "true",
        "CreateSecurityGroupStack": "true",
        "CreateEKSClusterStack": "true",
        "CreateSageMakerIAMRoleStack": "true",
        "CreateHelmChartStack": "true",
        "CreateHyperPodClusterStack": "true",
        "CreateS3BucketStack": "false",
        "CreateLifeCycleScriptStack": "false",
        "EnableHPTrainingOperatorFeature": "true",
        "EnableHPInferenceFeature": "false",
        "EnableHPInferenceAddonFeature": "false",
        "EnableObservabilityFeature": "false",
        "CreateTaskGovernanceClusterPolicyStack": "false",
        "CreateFsxStack": "false",
        "AutoScalerType": "None",
        "Tags": json.dumps([{"Key": "SageMaker", "Value": "true"},
                            {"Key": "project", "Value": "gpu-sandbox-on-aws"}], separators=(",", ":")),
        "SendUsageData": "false",
    }


if __name__ == "__main__":
    print(json.dumps([{"ParameterKey": key, "ParameterValue": value}
                      for key, value in parameters(os.environ).items()], indent=2))
