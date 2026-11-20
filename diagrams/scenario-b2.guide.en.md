[한국어](scenario-b2.guide.md) | **English**

# Scenario B2 — HyperPod trainer and sandbox groups (experimental)

The trainer and gVisor sandboxes run in separate HyperPod instance groups attached to one EKS cluster. The sandbox group boots from a custom AMI with an NVIDIA driver that the pinned gVisor release supports.

![Scenario B2 architecture](scenario-b2.drawio.png)

## Reading the diagram

Solid arrows show synchronous calls. Dashed arrows mark asynchronous, conditional, or supporting relationships. Arrow labels identify what moves between components.

## Request flow

1. (1 to 3) The operator opens cdk/tunnel.sh (SSM port forwarding from 127.0.0.1:8443 through the access instance to the private API on 443). 04_install_gpu_stack.sh and 05_setup_namespaces_auth.sh run through it while EKS has only the system nodes; 05_setup_namespaces_auth.sh sets the active runtime to gvisor-hyperpod.
2. (4, 5) scripts/hyperpod/build_b2_ami.sh launches an m6i.large from the newest HyperPod EKS 1.36 public base AMI in an EKS private subnet. Its user data replaces NVIDIA 595.91.07 (unknown to gVisor release-20261109.0 nvproxy) with 580.178.04, the driver of the EC2 gVisor nodes, installs gVisor, and powers off; the script images the stopped instance and terminates it (20 to 40 minutes, estimate). Building the kernel module needs no GPU.
3. (6, 7) scripts/hyperpod/create.sh --b2 adds instance group sandbox (2x ml.g5.xlarge, ImageId = the custom AMI, label and taint gpusandbox/role=sandbox-hyperpod). On each node on_create_sandbox.sh from the bucket checks that the loaded driver is on runsc's nvproxy list, registers the runsc handler with containerd and installs the node guard; it fails the node instead of joining it without gVisor.
4. (8, 9) The trainer instance group runs the minimal on_create.sh; scripts/hyperpod/run_grpo.sh applies the HyperPodPyTorchJob, the training operator starts it on the HyperPod trainer node and the kubelet mounts ConfigMap sandbox-routing.
5. (10, 11) The trainer downloads the policy model from the Hugging Face Hub through the NAT gateway.
6. (12, 13) Reward path as in scenarios A and B1, now to sandbox-gvisor-hyperpod-v1 on the HyperPod sandbox nodes; during a rollout v2 runs on the second sandbox node (one replica per version) and the trainer switches at the next batch boundary after parity and the ConfigMap patch.
7. (14 to 18) HyperPod nodes pull images with the execution role (ECR pull actions); the operator pushes the images and syncs the lifecycle scripts. The control plane logs to CloudWatch Logs and encrypts Secrets with the KMS key; VPC flow logs (REJECT) go to a second log group.
8. Sandbox egress has no edge on purpose: default-deny NetworkPolicy, readiness that requires IMDS, the API server and the kubelet to be unreachable, and the node guard installed by the lifecycle script. Node failures are handled by HyperPod NodeRecovery (reboot or replace) instead of the EKS managed node group.

## Services

| Service | Role |
|---|---|
| Operator workstation (`client`, resource) | Runs cdk/deploy.sh, the numbered and HyperPod scripts, kubectl and helm through the tunnel, builds and pushes the images (HYPERPOD=1) |
| SSM Session Manager (`systems_manager_session_manager`, resource) | Port forwarding session (AWS-StartPortForwardingSessionToRemoteHost) from 127.0.0.1:8443 on the workstation to the API endpoint on 443 |
| Access instance t4g.nano (`t4g_instance`, resource) | SSM-only host in a private subnet: no inbound rules, HTTPS egress only, IMDSv2, AmazonSSMManagedInstanceCore |
| EKS 1.36 private API (`eks`) | Control plane, private endpoint only, access entries (API_AND_CONFIG_MAP), add-ons vpc-cni with NetworkPolicy, kube-proxy, pod identity agent, CoreDNS, and the HyperPod training operator |
| KMS secrets key (`key_management_service`) | Customer-managed key with rotation; EKS envelope-encrypts Kubernetes Secrets with it |
| HyperPod GRPO trainer (`sagemaker`) | HyperPodPyTorchJob in ns rl-trainer (hyperpodrun, the same train_grpo.py) on HyperPod instance group trainer, 1x ml.g5.2xlarge; NodeRecovery Automatic, job retries and log-based hang detection |
| gvisor-hyperpod pool v1 (`container_1`, resource) | Active pool: Deployment and headless Service sandbox-gvisor-hyperpod-v1 in ns sandbox, RuntimeClass gvisor-hyperpod (runsc + nvproxy), 1 replica per version, default-deny NetworkPolicy |
| gvisor-hyperpod pool v2 (`container_1`, resource) | Next version sandbox-gvisor-hyperpod-v2 on the second sandbox node (blue/green); no traffic until parity passes and the routing switch |
| AMI builder m6i.large (`ec2_m6i_instance`, resource) | Plain EC2 instance from the newest HyperPod EKS 1.36 AL2023 public base AMI in an EKS private subnet; user data swaps NVIDIA 595.91.07 for 580.178.04, installs the pinned gVisor, powers off; terminated after imaging |
| Custom AMI, NVIDIA 580.178.04 (`ami`, resource) | hyperpod-eks-1.36-gvisor-nv580.178.04 image: ImageId of the HyperPod sandbox instance group; deregistered by 08_cleanup.sh |
| ECR repositories (`ecr`) | Private repositories gpu-sandbox/sandbox, trainer and control (scan on push, immutable tags), created by scripts/03_build_push_images.sh from the workstation, outside the CDK stack |
| CloudWatch Logs (`cloudwatch_2`) | Log group /aws/eks/CLUSTER_NAME/cluster for five control plane log types and the VPC flow log group (REJECT), one-month retention |
| NAT gateway (`nat_gateway`, resource) | The single egress of the private subnets, which both HyperPod instance groups and the builder use |
| S3 lifecycle scripts (`s3`) | Private bucket sagemaker-...-lcs (Block Public Access on) holding on_create.sh, on_create_sandbox.sh, register_runsc.sh and node-guard.sh |
| Hugging Face Hub (`internet`, resource) | External source of the policy model weights |
| VPC (`vpc`), not drawn | 2 AZs, public /24 subnets holding only the NAT, private /19 subnets; the HyperPod instance groups get one private subnet and the EKS cluster security group |
| System node group m6i.large x2 (`ec2_m6i_instance`, resource), not drawn | The only EKS node group in B2: CoreDNS, the add-ons, the HyperPod dependency chart and the operator tool Jobs (probe, parity, bench) |
| IAM roles (`role`, resource), not drawn | Cluster, node and access roles from CDK; HyperPod execution role with AmazonSageMakerClusterInstanceRolePolicy, ENI and ECR pull, and lifecycle bucket read |
| Kubernetes ConfigMap sandbox-routing, not drawn | Active runtime gvisor-hyperpod and version plus the pool addresses; written by 05_setup_namespaces_auth.sh and ops/rollout.sh, mounted into the trainer pod |
| HyperPod dependency chart and training operator add-on (`eks`), not drawn | Helm release hyperpod-dependencies and EKS add-on amazon-sagemaker-hyperpod-training-operator; RuntimeClass gvisor-hyperpod is applied in the same script |
| HyperPod EKS public base AMI (`ami`, resource), not drawn | Owner amazon, named HyperPod EKS 1.36 x86_64 AMI Amazon Linux 2023 with a timestamp; HyperPod accepts custom AMIs only when built from it |

## Design decisions

The custom AMI and sandbox group are specific to B2. The trainer group keeps the default AMI. B2 is experimental and was not verified on AWS.

See the [architecture brief](scenario-b2.brief.md) for the component evidence and arrow labels.

## Outside the diagram

- WITH_KATA_GPU=1 and WITH_KATA_CPU=1 node groups (stack.py:233-255); Kata on HyperPod nodes is not possible (docs/handson/07_hyperpod.md:495).
- Demo site (hands-on page 09): private S3 + CloudFront, demo/infra/site.yaml; no path to the cluster.
- Agent Sandbox extension: scripts/extensions/agent_sandbox.sh, k8s/extensions/agent-sandbox/.
- Production reference (docs/production/): gateway, jwks-sync CronJob, Karpenter NodePools, veRL RayCluster.
- EKS_PUBLIC_ACCESS_CIDR: optional public endpoint for one /32 (cdk/gpusandbox_cdk/config.py:78-83), off by default.
