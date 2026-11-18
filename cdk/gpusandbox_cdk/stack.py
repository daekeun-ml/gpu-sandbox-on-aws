"""EKS infrastructure for scenarios A, B1, B2 and C, with private-by-default settings.

L1 (Cfn*) EKS resources only: no kubectl Lambda and no in-cluster manifests. Everything inside
the cluster (device plugin, gVisor RuntimeClass, kata-deploy, sandbox pools) stays with the
numbered scripts, which reach the private API endpoint through cdk/tunnel.sh.

Security defaults (each one is asserted in cdk/tests):
  * EKS API endpoint private only; public access is opt-in for a single /32
  * no security group ingress from 0.0.0.0/0; the operator reaches the API through SSM
  * IMDSv2 only with hop limit 1 on every node and on the access instance
  * encrypted EBS, KMS-encrypted Kubernetes secrets, control plane audit logs, VPC flow logs
  * nodes in private subnets; public subnets do not map public IPs (they hold only the NAT)
"""

from __future__ import annotations

import sys
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_logs as logs
from constructs import Construct

from gpusandbox_cdk.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "infra/eks"))
import userdata  # noqa: E402  (infra/eks/userdata.py, standard library only)

TAINT = "NO_SCHEDULE"
# Set explicitly: the Kata GPU node's NodeConfig needs it, and CloudFormation exposes no IPv4 attribute.
SERVICE_CIDR = "172.20.0.0/16"
LOG_RETENTION = logs.RetentionDays.ONE_MONTH


class GpuSandboxStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, *, settings: Settings, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        s = settings
        cdk.Tags.of(self).add("project", "gpu-sandbox-on-aws")

        # --- network ---------------------------------------------------------------------
        vpc = ec2.Vpc(
            self, "Vpc",
            max_azs=2,
            nat_gateways=1,
            restrict_default_security_group=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24,
                                        map_public_ip_on_launch=False),
                ec2.SubnetConfiguration(name="private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                                        cidr_mask=19),
            ],
        )
        for subnet in vpc.public_subnets:
            cdk.Tags.of(subnet).add("kubernetes.io/role/elb", "1")
        for subnet in vpc.private_subnets:
            # scripts/hyperpod/create.sh picks a private subnet by this tag.
            cdk.Tags.of(subnet).add("kubernetes.io/role/internal-elb", "1")
            # Karpenter EC2NodeClasses (infra/karpenter) select subnets by this tag.
            cdk.Tags.of(subnet).add("karpenter.sh/discovery", s.cluster_name)
        vpc.add_flow_log(
            "FlowLog",
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(
                logs.LogGroup(self, "FlowLogGroup", retention=LOG_RETENTION,
                              removal_policy=cdk.RemovalPolicy.DESTROY)),
            traffic_type=ec2.FlowLogTrafficType.REJECT,
        )
        private_ids = [sn.subnet_id for sn in vpc.private_subnets]

        # --- operator access: SSM-only instance, no inbound rules -----------------------------
        access_sg = ec2.SecurityGroup(self, "AccessSg", vpc=vpc, allow_all_outbound=False,
                                      description="SSM access instance: no ingress, HTTPS egress only")
        access_sg.add_egress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "SSM and the EKS API endpoint")
        access_policies = ("AmazonSSMManagedInstanceCore",)
        access_role = self._role("AccessRole", "ec2.amazonaws.com", access_policies)
        access = ec2.Instance(
            self, "AccessInstance",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            instance_type=ec2.InstanceType("t4g.nano"),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(cpu_type=ec2.AmazonLinuxCpuType.ARM_64),
            security_group=access_sg,
            role=access_role,
            require_imdsv2=True,
            block_devices=[ec2.BlockDevice(device_name="/dev/xvda",
                                           volume=ec2.BlockDeviceVolume.ebs(8, encrypted=True))],
        )

        # The control plane accepts HTTPS from the access instance; nodes use the cluster SG.
        control_plane_sg = ec2.SecurityGroup(self, "ControlPlaneSg", vpc=vpc, allow_all_outbound=False,
                                             description="Extra EKS control plane SG: API from the access instance")
        control_plane_sg.add_ingress_rule(access_sg, ec2.Port.tcp(443), "kubectl through the SSM tunnel")

        # --- cluster -----------------------------------------------------------------------
        secrets_key = kms.Key(self, "SecretsKey", enable_key_rotation=True,
                              pending_window=cdk.Duration.days(7), removal_policy=cdk.RemovalPolicy.DESTROY,
                              description=f"EKS secrets encryption for {s.cluster_name}")
        cluster_policies = ("AmazonEKSClusterPolicy",)
        cluster_role = self._role("ClusterRole", "eks.amazonaws.com", cluster_policies)
        cluster_role.add_to_policy(iam.PolicyStatement(
            actions=["kms:Encrypt", "kms:Decrypt", "kms:DescribeKey", "kms:CreateGrant", "kms:ListGrants",
                     "kms:GenerateDataKey"],
            resources=[secrets_key.key_arn],
        ))
        # Created up front so that the control plane logs get a retention period.
        control_log_group = logs.LogGroup(self, "ControlPlaneLogs",
                                          log_group_name=f"/aws/eks/{s.cluster_name}/cluster",
                                          retention=LOG_RETENTION, removal_policy=cdk.RemovalPolicy.DESTROY)

        public = s.public_access_cidr is not None
        cluster = eks.CfnCluster(
            self, "Cluster",
            name=s.cluster_name,
            version=s.k8s_version,
            role_arn=cluster_role.role_arn,
            # The four add-ons below are installed as EKS add-ons; skip the self-managed copies.
            bootstrap_self_managed_addons=False,
            kubernetes_network_config=eks.CfnCluster.KubernetesNetworkConfigProperty(service_ipv4_cidr=SERVICE_CIDR),
            resources_vpc_config=eks.CfnCluster.ResourcesVpcConfigProperty(
                subnet_ids=private_ids,
                security_group_ids=[control_plane_sg.security_group_id],
                endpoint_private_access=True,
                endpoint_public_access=public,
                public_access_cidrs=[s.public_access_cidr] if public else None,
            ),
            # HyperPod needs API or API_AND_CONFIG_MAP. The CloudFormation role gets no cluster
            # admin; the operator gets an explicit access entry below.
            access_config=eks.CfnCluster.AccessConfigProperty(
                authentication_mode="API_AND_CONFIG_MAP",
                bootstrap_cluster_creator_admin_permissions=False,
            ),
            # EKS 1.28+ envelope-encrypts all Kubernetes API data by default, so CloudFormation
            # deprecates EncryptionConfig.Resources (lint W9009); only the KMS key is set here.
            encryption_config=[eks.CfnCluster.EncryptionConfigProperty(
                provider=eks.CfnCluster.ProviderProperty(key_arn=secrets_key.key_arn),
            )],
            logging=eks.CfnCluster.LoggingProperty(cluster_logging=eks.CfnCluster.ClusterLoggingProperty(
                enabled_types=[eks.CfnCluster.LoggingTypeConfigProperty(type=t)
                               for t in ("api", "audit", "authenticator", "controllerManager", "scheduler")],
            )),
        )
        cluster.node.add_dependency(control_log_group)
        cluster.node.add_dependency(cluster_role)

        for i, principal in enumerate(s.admin_principal_arns):
            eks.CfnAccessEntry(
                self, "OperatorAccess" if i == 0 else f"OperatorAccess{i}",
                cluster_name=cluster.ref,
                principal_arn=principal,
                access_policies=[eks.CfnAccessEntry.AccessPolicyProperty(
                    policy_arn="arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy",
                    access_scope=eks.CfnAccessEntry.AccessScopeProperty(type="cluster"),
                )],
            )

        def addon(name: str, config: str | None = None) -> eks.CfnAddon:
            return eks.CfnAddon(self, f"Addon-{name}", cluster_name=cluster.ref, addon_name=name,
                                configuration_values=config, resolve_conflicts="OVERWRITE")

        # NetworkPolicy enforcement (eBPF) needs VPC CNI 1.21+; the add-on default is newer.
        network_addons = [addon("vpc-cni", '{"enableNetworkPolicy": "true"}'), addon("kube-proxy"),
                          addon("eks-pod-identity-agent")]

        # --- nodes -------------------------------------------------------------------------
        node_policies = ("AmazonEKSWorkerNodePolicy", "AmazonEKS_CNI_Policy", "AmazonEC2ContainerRegistryPullOnly")
        node_role = self._role("NodeRole", "ec2.amazonaws.com", node_policies)

        def launch_template(name: str, volume_gb: int, user_data: str = "",
                            cpu_options: ec2.CfnLaunchTemplate.CpuOptionsProperty | None = None,
                            image_id: str | None = None) -> ec2.CfnLaunchTemplate:
            return ec2.CfnLaunchTemplate(
                self, f"Lt-{name}",
                launch_template_data=ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
                    # Pods cannot reach node credentials.
                    metadata_options=ec2.CfnLaunchTemplate.MetadataOptionsProperty(
                        http_endpoint="enabled", http_tokens="required", http_put_response_hop_limit=1),
                    block_device_mappings=[ec2.CfnLaunchTemplate.BlockDeviceMappingProperty(
                        device_name="/dev/xvda",
                        ebs=ec2.CfnLaunchTemplate.EbsProperty(volume_size=volume_gb, volume_type="gp3",
                                                              encrypted=True, delete_on_termination=True))],
                    user_data=cdk.Fn.base64(user_data) if user_data else None,
                    cpu_options=cpu_options,
                    image_id=image_id,
                    tag_specifications=[ec2.CfnLaunchTemplate.TagSpecificationProperty(
                        resource_type="instance",
                        tags=[cdk.CfnTag(key="project", value="gpu-sandbox-on-aws")])],
                ),
            )

        def nodegroup(name: str, instance_type: str, ami_type: str, lt: ec2.CfnLaunchTemplate, *,
                      desired: int, minimum: int, maximum: int, labels: dict[str, str],
                      taint: str | None = None) -> eks.CfnNodegroup:
            ng = eks.CfnNodegroup(
                self, f"Ng-{name}",
                cluster_name=cluster.ref,
                nodegroup_name=name,
                node_role=node_role.role_arn,
                subnets=private_ids,
                instance_types=[instance_type],
                ami_type=ami_type,
                scaling_config=eks.CfnNodegroup.ScalingConfigProperty(
                    desired_size=desired, min_size=minimum, max_size=maximum),
                labels=labels,
                taints=[eks.CfnNodegroup.TaintProperty(key="gpusandbox/role", value=taint, effect=TAINT)]
                if taint else None,
                launch_template=eks.CfnNodegroup.LaunchTemplateSpecificationProperty(
                    id=lt.ref, version=lt.attr_latest_version_number),
            )
            for dep in network_addons:
                ng.node.add_dependency(dep)
            return ng

        gpu = {"gpusandbox/device-plugin": "cdi", "nvidia.com/gpu.deploy.operands": "false"}
        system = nodegroup("system", s.system_instance_type, "AL2023_x86_64_STANDARD",
                           launch_template("system", 50), desired=2, minimum=2, maximum=3,
                           labels={"gpusandbox/role": "system"})
        # CoreDNS needs schedulable nodes to become active.
        addon("coredns").node.add_dependency(system)

        if s.scenario == "A":
            nodegroup("trainer", s.trainer_instance_type, "AL2023_x86_64_NVIDIA",
                      launch_template("trainer", 200), desired=1, minimum=0, maximum=1,
                      labels={"gpusandbox/role": "trainer", **gpu}, taint="trainer")
        if s.scenario in ("A", "B1"):
            nodegroup("sandbox-gvisor", s.gvisor_instance_type, "AL2023_x86_64_NVIDIA",
                      launch_template("sandbox-gvisor", 100, userdata.gvisor_gpu_node(s.gvisor_release)),
                      desired=s.gvisor_nodes, minimum=0, maximum=4,
                      labels={"gpusandbox/role": "sandbox-gvisor", **gpu}, taint="sandbox-gvisor")
        if s.with_kata_cpu:
            cores, threads = s.kata_cpu_topology
            nodegroup("sandbox-kata-cpu", s.kata_cpu_instance_type, "AL2023_x86_64_STANDARD",
                      launch_template("sandbox-kata-cpu", 100, userdata.nested_cpu_node(s.gvisor_release),
                                      cpu_options=ec2.CfnLaunchTemplate.CpuOptionsProperty(
                                          core_count=cores, threads_per_core=threads,
                                          nested_virtualization="enabled")),
                      desired=1, minimum=0, maximum=2,
                      labels={"gpusandbox/role": "sandbox-kata", "gpusandbox/kata-gpu": "false"},
                      taint="sandbox-kata")
        if s.kata_iommu_ami_id:
            # g4dn.metal on the IOMMU AMI. EKS does not merge its bootstrap into user data when the
            # launch template sets an AMI, so the NodeConfig carries the cluster fields (as tokens).
            gpu_user_data = userdata.kata_gpu_node(
                s.cluster_name, cluster.attr_endpoint, cluster.attr_certificate_authority_data,
                SERVICE_CIDR)
            nodegroup("sandbox-kata-gpu", s.kata_gpu_instance_type, "CUSTOM",
                      launch_template("sandbox-kata-gpu", 200, gpu_user_data, image_id=s.kata_iommu_ami_id),
                      desired=1, minimum=0, maximum=1,
                      labels={"gpusandbox/role": "sandbox-kata", "gpusandbox/kata-gpu": "true",
                              # The NVIDIA GPU Operator binds this node's GPUs to vfio-pci.
                              "nvidia.com/gpu.workload.config": "vm-passthrough"},
                      taint="sandbox-kata")

        cdk.CfnOutput(self, "ClusterName", value=cluster.ref)
        cdk.CfnOutput(self, "ClusterEndpoint", value=cluster.attr_endpoint)
        cdk.CfnOutput(self, "AccessInstanceId", value=access.instance_id)
        cdk.CfnOutput(self, "EndpointPublicAccess", value=str(public).lower())
        # cdk/deploy.sh compares this with the requested scenario before changing node groups.
        cdk.CfnOutput(self, "Scenario", value=s.scenario)

        self._suppress(access, [(access_role, access_policies), (cluster_role, cluster_policies),
                                (node_role, node_policies)])

    def _role(self, construct_id: str, service: str, policies: tuple[str, ...]) -> iam.Role:
        return iam.Role(self, construct_id, assumed_by=iam.ServicePrincipal(service),
                        managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name(n) for n in policies])

    def _suppress(self, access: ec2.Instance, roles: list[tuple[iam.Role, tuple[str, ...]]]) -> None:
        """cdk-nag findings accepted on purpose, each with its reason (cdk-nag v3 acknowledgements)."""
        managed = "AwsSolutions-IAM4[Policy::arn:<AWS::Partition>:iam::aws:policy/{}]"
        reason = "AWS managed policy that the EKS or SSM documentation prescribes for this role"
        for role, names in roles:
            for name in names:
                cdk.Validations.of(role).acknowledge(cdk.Acknowledgment(id=managed.format(name), reason=reason))
        cdk.Validations.of(access).acknowledge(
            cdk.Acknowledgment(id="AwsSolutions-EC28", reason="Disposable SSM tunnel host; detailed monitoring not needed"))
        cdk.Validations.of(access).acknowledge(
            cdk.Acknowledgment(id="AwsSolutions-EC29", reason="Disposable SSM tunnel host; replaced by redeploying the stack"))
