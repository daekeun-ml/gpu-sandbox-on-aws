[한국어](scenario-b1.guide.md) | **English**

# Scenario B1 — HyperPod trainer and EC2 sandboxes

The trainer runs on a HyperPod instance group attached to the same EKS cluster. The gVisor sandbox pool stays on EC2. HyperPod manages the trainer node and the training operator schedules the training Job.

![Scenario B1 architecture](scenario-b1.drawio.png)

## Reading the diagram

Solid arrows show synchronous calls. Dashed arrows mark asynchronous, conditional, or supporting relationships. Arrow labels identify what moves between components.

## Request flow

1. (1 to 3) The operator runs cdk/tunnel.sh: an SSM Session Manager port forwarding session from 127.0.0.1:8443 through the access instance to the private EKS endpoint on 443. Every kubectl and helm step rides it, including the HyperPod dependency chart and the routing switch. The AWS API calls (CloudFormation, ECR push, S3 sync, iam, sagemaker create-cluster, eks create-addon) go to public AWS endpoints directly.
2. (4) scripts/hyperpod/create.sh uploads the lifecycle scripts (edge 12), creates the execution role and calls CreateCluster with the EKS cluster as orchestrator, one private subnet of the stack and the EKS cluster security group. HyperPod runs on_create.sh from the bucket when the trainer node is created; the node joins the EKS cluster.
3. (5) scripts/hyperpod/run_grpo.sh applies the HyperPodPyTorchJob; the training operator add-on starts the pod on the HyperPod node (affinity on instance type and node health Schedulable) and the kubelet mounts ConfigMap sandbox-routing as a directory.
4. (6, 7) The trainer downloads the policy model from the Hugging Face Hub; the HyperPod node sits in the stack's private subnet, so the traffic leaves through the NAT gateway.
5. (8) The reward path is the same as in scenario A: one routing snapshot per reward batch, headless Service DNS through CoreDNS, POST /v1/evaluate on 8000 with a projected token (audience gpu-sandbox), verdict back on the same call. HyperPod and EC2 nodes share the VPC pod network and the cluster security group, and the NetworkPolicy admits the pod by namespace and label, not by node.
6. (9) scripts/ops/rollout.sh deploys v2 beside v1, verifies it, checks parity and patches the routing ConfigMap; the trainer switches at its next batch boundary.
7. (10 to 14) Nodes pull images from ECR (EKS nodes with the node role, HyperPod nodes with the execution role); the operator pushes them and uploads the lifecycle scripts. The control plane logs to CloudWatch Logs and encrypts Secrets with the KMS key; VPC flow logs (REJECT) go to a second log group.
8. Sandbox egress has no edge on purpose: default-deny NetworkPolicy in ns sandbox, readiness that requires IMDS, the API server and the kubelet to be unreachable, and the node guard on the gVisor nodes.

## Services

| Service | Role |
|---|---|
| Operator workstation (`client`, resource) | Runs cdk/deploy.sh, the numbered and HyperPod scripts, kubectl and helm through the tunnel, builds and pushes the images (HYPERPOD=1 adds hyperpodrun to the trainer image) |
| SSM Session Manager (`systems_manager_session_manager`, resource) | Port forwarding session (AWS-StartPortForwardingSessionToRemoteHost) from 127.0.0.1:8443 on the workstation to the API endpoint on 443 |
| Access instance t4g.nano (`t4g_instance`, resource) | SSM-only host in a private subnet: no inbound rules, HTTPS egress only, IMDSv2, AmazonSSMManagedInstanceCore |
| EKS 1.36 private API (`eks`) | Control plane, private endpoint only, access entries (API_AND_CONFIG_MAP, which HyperPod needs), add-ons vpc-cni with NetworkPolicy, kube-proxy, pod identity agent, CoreDNS, and the HyperPod training operator |
| KMS secrets key (`key_management_service`) | Customer-managed key with rotation; EKS envelope-encrypts Kubernetes Secrets with it |
| HyperPod GRPO trainer (`sagemaker`) | HyperPodPyTorchJob in ns rl-trainer (hyperpodrun, the same train_grpo.py) on HyperPod instance group trainer, 1x ml.g5.2xlarge; NodeRecovery Automatic, job retries and log-based hang detection |
| gvisor pool v1 (`container_1`, resource) | Active pool: Deployment and headless Service sandbox-gvisor-v1 in ns sandbox, RuntimeClass gvisor (runsc + nvproxy), one pod per A10G, 2 replicas, default-deny NetworkPolicy |
| gvisor pool v2 (`container_1`, resource) | Next version sandbox-gvisor-v2 beside v1 (blue/green: 5 seeds, speedup cap 10x); no traffic until parity passes and the routing switch; the node group is scaled to 4 for it |
| ECR repositories (`ecr`) | Private repositories gpu-sandbox/sandbox, trainer and control (scan on push, immutable tags), created by scripts/03_build_push_images.sh from the workstation, outside the CDK stack |
| CloudWatch Logs (`cloudwatch_2`) | Log group /aws/eks/CLUSTER_NAME/cluster for five control plane log types and the VPC flow log group (REJECT), one-month retention |
| NAT gateway (`nat_gateway`, resource) | The single egress of the private subnets, which the HyperPod instance group also uses |
| S3 lifecycle scripts (`s3`) | Private bucket sagemaker-...-lcs (Block Public Access on) holding lifecycle/on_create.sh for the trainer instance group |
| Hugging Face Hub (`internet`, resource) | External source of the policy model weights |
| VPC (`vpc`), not drawn | 2 AZs, public /24 subnets holding only the NAT, private /19 subnets for every node; the HyperPod instance group gets one private subnet and the EKS cluster security group |
| System node group m6i.large x2 (`ec2_m6i_instance`, resource), not drawn | Untainted nodes for CoreDNS, the add-ons, the HyperPod dependency chart and the operator tool Jobs (probe, parity, bench) |
| IAM roles (`role`, resource), not drawn | Cluster, node and access roles from CDK; HyperPod execution role with AmazonSageMakerClusterInstanceRolePolicy, ENI and ECR pull, and lifecycle bucket read |
| Kubernetes ConfigMap sandbox-routing, not drawn | Active runtime and version plus the pool addresses; written by 05_setup_namespaces_auth.sh and ops/rollout.sh, mounted into the trainer pod as a directory |
| HyperPod dependency chart and training operator add-on (`eks`), not drawn | Helm release hyperpod-dependencies in kube-system and EKS add-on amazon-sagemaker-hyperpod-training-operator, which runs the HyperPodPyTorchJob |

## Design decisions

Training recovery and sandbox runtime requirements can be configured independently. The exercise uses temporary pod storage for checkpoints. B1 was not verified in the AWS exercise account.

See the [architecture brief](scenario-b1.brief.md) for the component evidence and arrow labels.

## Outside the diagram

- WITH_KATA_GPU=1: sandbox-kata-gpu node group (g4dn.metal, Kata QEMU with GPU passthrough), optional Kata pools for B1 (stack.py:243-255, docs/handson/07_hyperpod.md:57).
- WITH_KATA_CPU=1: adds the c8i sandbox-kata-cpu node group drawn in scenario-c (stack.py:233-242).
- Kata on HyperPod nodes: not possible (docs/handson/07_hyperpod.md:495).
- Demo site (hands-on page 09): private S3 + CloudFront replaying recorded verdicts, demo/infra/site.yaml; no path to the cluster.
- Agent Sandbox extension: scripts/extensions/agent_sandbox.sh and k8s/extensions/agent-sandbox/ (unit tested only).
- Production reference (docs/production/): sandbox gateway (k8s/production/gateway.yaml.tpl), jwks-sync CronJob, Karpenter NodePools (infra/karpenter/nodepools.yaml), veRL RayCluster.
- EKS_PUBLIC_ACCESS_CIDR: optional public endpoint for one /32 (cdk/gpusandbox_cdk/config.py:78-83), off by default.
