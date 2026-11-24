# Scenario B1: HyperPod trainer with gVisor GPU sandboxes on EKS nodes

The same on-policy GRPO loop as scenario A, but the trainer runs as a HyperPodPyTorchJob on a SageMaker HyperPod instance group attached to the same private EKS cluster, while the gVisor (runsc + nvproxy) sandbox pools stay on the EC2 node group. Audience: technical.
Language: ko
Repo: repository root (gpu-sandbox-on-aws)
Components: 18, Relationships: 14

## Scope
| Unit | Path | Deploys with | Region/account (if in code) | Diagram |
|---|---|---|---|---|
| Scenario A | cdk/ with SCENARIO=A, k8s/, scripts/ 20 to 80 | CDK stack CLUSTER_NAME-cdk (cdk/deploy.sh), then numbered scripts with kubectl and helm through cdk/tunnel.sh | us-west-2 by default (scripts/config.env.example:5) | scenario-a |
| Scenario B1 (this diagram) | cdk/ with SCENARIO=B1 (scripts/02_create_cluster.sh --hyperpod), scripts/hyperpod/, infra/hyperpod/ | same stack, plus scripts/hyperpod/create.sh (Helm chart, S3 bucket, IAM role, sagemaker create-cluster, EKS add-on) | same | scenario-b1 |
| Scenario B2 | `scripts/hyperpod/create_managed.sh` | CloudFormation template for HyperPod on EKS, three HyperPod instance groups | us-east-1 | scenario-b2 |
| Scenario C (CPU only) | cdk/ with SCENARIO=C, scripts/kata/cpu_nodes.sh, ops/simulate.sh, ops/rollout.sh | same stack, only the c8i node group added | same | scenario-c |

Cross-unit: one CDK stack (cdk/gpusandbox_cdk/stack.py) builds A, B1 and C; for B1 it creates the system and sandbox-gvisor node groups and no trainer node group (stack.py:224-232). The HyperPod cluster is created outside CDK by scripts/hyperpod/create.sh with the EKS cluster as its orchestrator (infra/hyperpod/cluster.json.tpl:3).

Out of scope (not drawn), one line each:
- WITH_KATA_GPU=1: sandbox-kata-gpu node group (g4dn.metal, Kata QEMU with GPU passthrough), optional Kata pools for B1 (stack.py:243-255, docs/handson/scenarios/b/index.md).
- WITH_KATA_CPU=1: adds the c8i sandbox-kata-cpu node group drawn in scenario-c (stack.py:233-242).
- Kata on HyperPod nodes: not possible (docs/handson/scenarios/b/index.md).
- Demo site (hands-on page 09): private S3 + CloudFront replaying recorded verdicts, demo/infra/site.yaml; no path to the cluster.
- Agent Sandbox extension: scripts/extensions/agent_sandbox.sh and k8s/extensions/agent-sandbox/ (unit tested only).
- Production reference (docs/production/): sandbox gateway (k8s/production/gateway.yaml.tpl), jwks-sync CronJob, Karpenter NodePools (infra/karpenter/nodepools.yaml), veRL RayCluster.
- EKS_PUBLIC_ACCESS_CIDR: optional public endpoint for one /32 (cdk/gpusandbox_cdk/config.py:78-83), off by default.

## Components
| id | Service (stencil) | Role in this system | Group | Evidence | Provenance |
|---|---|---|---|---|---|
| operator | Operator workstation (`client`, resource) | Runs cdk/deploy.sh, the numbered and HyperPod scripts, kubectl and helm through the tunnel, builds and pushes the images (HYPERPOD=1 adds hyperpodrun to the trainer image) | outside | cdk/tunnel.sh:2-8, scripts/03_build_push_images.sh:20-40 | referenced |
| ssm | SSM Session Manager (`systems_manager_session_manager`, resource) | Port forwarding session (AWS-StartPortForwardingSessionToRemoteHost) from 127.0.0.1:8443 on the workstation to the API endpoint on 443 | Operator access | cdk/tunnel.sh:13-31 | referenced |
| access | Access instance t4g.nano (`t4g_instance`, resource) | SSM-only host in a private subnet: no inbound rules, HTTPS egress only, IMDSv2, AmazonSSMManagedInstanceCore | Operator access | cdk/gpusandbox_cdk/stack.py:75-92 | deployed |
| eks | EKS 1.36 private API (`eks`) | Control plane, private endpoint only, access entries (API_AND_CONFIG_MAP, which HyperPod needs), add-ons vpc-cni with NetworkPolicy, kube-proxy, pod identity agent, CoreDNS, and the HyperPod training operator | EKS control plane | cdk/gpusandbox_cdk/stack.py:116-166, scripts/hyperpod/create.sh:96-100 | deployed |
| kms | KMS secrets key (`key_management_service`) | Customer-managed key with rotation; EKS envelope-encrypts Kubernetes Secrets with it | EKS control plane | cdk/gpusandbox_cdk/stack.py:100-109 | deployed |
| trainer | HyperPod GRPO trainer (`sagemaker`) | HyperPodPyTorchJob in ns rl-trainer (hyperpodrun, the same train_grpo.py) on HyperPod instance group trainer, 1x ml.g5.2xlarge; NodeRecovery Automatic, job retries and log-based hang detection | HyperPod trainer ml.g5.2xlarge | k8s/trainer/hyperpod-job-grpo.yaml.tpl:1-64, infra/hyperpod/cluster.json.tpl:1-22, scripts/config.env.example:45 | deployed |
| sbx_v1 | gvisor pool v1 (`container_1`, resource) | Active pool: Deployment and headless Service sandbox-gvisor-v1 in ns sandbox, RuntimeClass gvisor (runsc + nvproxy), one pod per A10G, 2 replicas, default-deny NetworkPolicy | sandbox-gvisor nodes g5.xlarge x2 | k8s/sandbox/deployment.yaml.tpl:1-40, k8s/sandbox/profiles/gvisor.env:1-11, cdk/gpusandbox_cdk/stack.py:228-232 | deployed |
| sbx_v2 | gvisor pool v2 (`container_1`, resource) | Next version sandbox-gvisor-v2 beside v1 (blue/green: 5 seeds, speedup cap 10x); no traffic until parity passes and the routing switch; the node group is scaled to 4 for it | sandbox-gvisor nodes g5.xlarge x2 | k8s/sandbox/versions/v2.env:1-7, scripts/ops/rollout.sh:1-10, docs/handson/scenarios/a/pool_update.md:53 | deployed |
| ecr | ECR repositories (`ecr`) | Private repositories gpu-sandbox/sandbox, trainer and control (scan on push, immutable tags), created by scripts/03_build_push_images.sh from the workstation, outside the CDK stack | Shared services | scripts/03_build_push_images.sh:24-40 | deployed |
| cw | CloudWatch Logs (`cloudwatch_2`) | Log group /aws/eks/CLUSTER_NAME/cluster for five control plane log types and the VPC flow log group (REJECT), one-month retention | Shared services | cdk/gpusandbox_cdk/stack.py:66-72, cdk/gpusandbox_cdk/stack.py:110-113 | deployed |
| nat | NAT gateway (`nat_gateway`, resource) | The single egress of the private subnets, which the HyperPod instance group also uses | Egress | cdk/gpusandbox_cdk/stack.py:47-58, scripts/hyperpod/create.sh:74-81 | deployed |
| lcs | S3 lifecycle scripts (`s3`) | Private bucket sagemaker-...-lcs (Block Public Access on) holding lifecycle/on_create.sh for the trainer instance group | Shared services | scripts/hyperpod/create.sh:39-52, infra/hyperpod/lifecycle/on_create.sh | deployed |
| hf | Hugging Face Hub (`internet`, resource) | External source of the policy model weights | outside | scripts/hyperpod/run_grpo.sh:11, rl/trl/train_grpo.py:30 | referenced |
| vpc | VPC (`vpc`), not drawn | 2 AZs, public /24 subnets holding only the NAT, private /19 subnets for every node; the HyperPod instance group gets one private subnet and the EKS cluster security group | n/a | cdk/gpusandbox_cdk/stack.py:47-72, scripts/hyperpod/create.sh:74-81 | deployed |
| sysng | System node group m6i.large x2 (`ec2_m6i_instance`, resource), not drawn | Untainted nodes for CoreDNS, the add-ons, the HyperPod dependency chart and the operator tool Jobs (probe, parity, bench) | n/a | cdk/gpusandbox_cdk/stack.py:218-222, k8s/probe/job-probe.yaml.tpl:1-35 | deployed |
| iam | IAM roles (`role`, resource), not drawn | Cluster, node and access roles from CDK; HyperPod execution role with AmazonSageMakerClusterInstanceRolePolicy, ENI and ECR pull, and lifecycle bucket read | n/a | cdk/gpusandbox_cdk/stack.py:149-170, scripts/hyperpod/create.sh:54-69 | deployed |
| routing | Kubernetes ConfigMap sandbox-routing, not drawn | Active runtime and version plus the pool addresses; written by 05_setup_namespaces_auth.sh and ops/rollout.sh, mounted into the trainer pod as a directory | n/a | k8s/base/routing.json.tpl, scripts/05_setup_namespaces_auth.sh:19-25 | deployed |
| hpaddon | HyperPod dependency chart and training operator add-on (`eks`), not drawn | Helm release hyperpod-dependencies in kube-system and EKS add-on amazon-sagemaker-hyperpod-training-operator, which runs the HyperPodPyTorchJob | n/a | scripts/hyperpod/create.sh:33-37, scripts/hyperpod/create.sh:96-100 | deployed |

## Relationships
| # | From → To | What flows | Kind | Evidence |
|---|---|---|---|---|
| 1 | operator → ssm | kubectl tunnel | sync | cdk/tunnel.sh:29-31 |
| 2 | ssm → access | port forward | sync | cdk/tunnel.sh:20-31, cdk/gpusandbox_cdk/stack.py:79-80 |
| 3 | access → eks | HTTPS 443 | sync | cdk/gpusandbox_cdk/stack.py:78, cdk/gpusandbox_cdk/stack.py:94-97 |
| 4 | trainer → lcs | boot script | async, boot time (dashed) | infra/hyperpod/cluster.json.tpl:9-12, scripts/hyperpod/create.sh:63-66 |
| 5 | eks → trainer | Job, active pool | async (dashed) | k8s/trainer/hyperpod-job-grpo.yaml.tpl:42-52, k8s/trainer/hyperpod-job-grpo.yaml.tpl:82-84, scripts/hyperpod/run_grpo.sh:13, infra/hyperpod/cluster.json.tpl:3 |
| 6 | trainer → nat | model pull | sync | k8s/trainer/hyperpod-job-grpo.yaml.tpl:60-68, scripts/hyperpod/create.sh:76-81 |
| 7 | nat → hf | HTTPS | sync | scripts/hyperpod/run_grpo.sh:11 |
| 8 | trainer → sbx_v1 | kernel code | sync | k8s/trainer/hyperpod-job-grpo.yaml.tpl:36-38, src/gpusandbox/client/routing.py:1-17, k8s/base/networkpolicies.yaml:15-36 |
| 9 | trainer → sbx_v2 | after switch | sync, after switch (dashed) | scripts/ops/rollout.sh:42-48, src/gpusandbox/client/routing.py:3-6 |
| 10 | sbx_v1 → ecr | image pull | aux (dashed) | k8s/sandbox/deployment.yaml.tpl:66, cdk/gpusandbox_cdk/stack.py:169 |
| 11 | operator → ecr | image push | aux (dashed) | scripts/03_build_push_images.sh:21-32 |
| 12 | operator → lcs | script upload | aux (dashed) | scripts/hyperpod/create.sh:39-52 |
| 13 | eks → cw | control plane logs | aux (dashed) | cdk/gpusandbox_cdk/stack.py:141-144 |
| 14 | eks → kms | encrypt secrets | aux (dashed) | cdk/gpusandbox_cdk/stack.py:137-140 |

## Flow
1. (1 to 3) The operator runs cdk/tunnel.sh: an SSM Session Manager port forwarding session from 127.0.0.1:8443 through the access instance to the private EKS endpoint on 443. Every kubectl and helm step rides it, including the HyperPod dependency chart and the routing switch. The AWS API calls (CloudFormation, ECR push, S3 sync, iam, sagemaker create-cluster, eks create-addon) go to public AWS endpoints directly.
2. (4) scripts/hyperpod/create.sh uploads the lifecycle scripts (edge 12), creates the execution role and calls CreateCluster with the EKS cluster as orchestrator, one private subnet of the stack and the EKS cluster security group. HyperPod runs on_create.sh from the bucket when the trainer node is created; the node joins the EKS cluster.
3. (5) scripts/hyperpod/run_grpo.sh applies the HyperPodPyTorchJob; the training operator add-on starts the pod on the HyperPod node (affinity on instance type and node health Schedulable) and the kubelet mounts ConfigMap sandbox-routing as a directory.
4. (6, 7) The trainer downloads the policy model from the Hugging Face Hub; the HyperPod node sits in the stack's private subnet, so the traffic leaves through the NAT gateway.
5. (8) The reward path is the same as in scenario A: one routing snapshot per reward batch, headless Service DNS through CoreDNS, POST /v1/evaluate on 8000 with a projected token (audience gpu-sandbox), verdict back on the same call. HyperPod and EC2 nodes share the VPC pod network and the cluster security group, and the NetworkPolicy admits the pod by namespace and label, not by node.
6. (9) scripts/ops/rollout.sh deploys v2 beside v1, verifies it, checks parity and patches the routing ConfigMap; the trainer switches at its next batch boundary.
7. (10 to 14) Nodes pull images from ECR (EKS nodes with the node role, HyperPod nodes with the execution role); the operator pushes them and uploads the lifecycle scripts. The control plane logs to CloudWatch Logs and encrypts Secrets with the KMS key; VPC flow logs (REJECT) go to a second log group.
8. Sandbox egress has no edge on purpose: default-deny NetworkPolicy in ns sandbox, readiness that requires IMDS, the API server and the kubelet to be unreachable, and the node guard on the gVisor nodes.

## Groups
Operator access; EKS control plane; HyperPod trainer ml.g5.2xlarge (HyperPod instance group trainer); sandbox-gvisor nodes g5.xlarge x2 (EKS node group sandbox-gvisor); Shared services; Egress

## Checks
- [x] Entry: no public entry; the operator reaches the API only through SSM Session Manager (stack.py:127-129). No end users.
- [x] Auth: kubectl uses the IAM access entry; the sandbox API takes only a projected ServiceAccount token with audience gpu-sandbox and NetworkPolicy admits only labelled rl-trainer pods (k8s/trainer/hyperpod-job-grpo.yaml.tpl:38).
- [x] Async boundaries: none on the request path; the version switch is asynchronous through the ConfigMap (edge 5); lifecycle scripts are read once at node creation (edge 4).
- [x] State: ConfigMap sandbox-routing, ECR, the lifecycle bucket (writer: operator; reader: HyperPod), CloudWatch Logs. Assumption to raise: /outputs is emptyDir, so a HyperPod node replacement loses checkpoints unless shared storage (FSx for Lustre PVC) is mounted (k8s/trainer/hyperpod-job-grpo.yaml.tpl:77-80).
- [x] Networking: service level; the HyperPod path through the NAT gateway is inferred from the private subnet the script selects, not from a separate resource.
- [x] Observability: control plane and flow logs only; the HyperPod log monitoring (JobStart, RewardStalled) watches the trainer's JSON events. Finding to raise: no CloudWatch alarms.
- [x] Every stencil looked up in references/aws-icons-*.md; substitutions under Decisions.

## Layout notes (Drawer)
- Main lane left to right: operator (outside), ssm and access, eks, trainer, sbx_v1; sbx_v2 below sbx_v1, kms below eks.
- Shared services (ecr, cw, lcs) and Egress (nat) on the row below; lcs under the trainer if the layout allows; hf outside on the right, level with nat.
- Primary phrases on seams between group boxes use words of at most 6 letters.

## Architecture review (skipped)
Skipped: no AWS documentation MCP server (`search_documentation` / `retrieve_skill`) was available in this environment, so no Well-Architected or service-documentation findings were produced and none were substituted from memory. To run Phase 2, add one with `claude mcp add --transport http aws-knowledge https://knowledge-mcp.global.api.aws` and rerun the Assessor. Note for the reader: the CDK stack already runs cdk-nag AwsSolutions checks on every synth and fails the deploy on unacknowledged findings (cdk/app.py:21-22); the findings it accepts, with their reasons, are in cdk/gpusandbox_cdk/stack.py:271-281. The HyperPod resources (bucket, execution role, cluster) are created by AWS CLI calls and are not covered by cdk-nag.

## Decisions & assumptions
- Correction: no gateway. The HyperPod trainer calls the pools directly and pins the version per reward batch, exactly as in scenario A (src/gpusandbox/client/routing.py:1-6, k8s/trainer/hyperpod-job-grpo.yaml.tpl:66). The gateway is production only (docs/production/00_architecture.md:103).
- Correction: HyperPod nodes reach the sandbox pods without any gateway or extra rule: the instance group uses one private subnet of the CDK VPC and the EKS cluster security group (scripts/hyperpod/create.sh:74-81), the pods share the VPC CNI pod network, and the NetworkPolicy selects by namespace and pod label.
- HyperPod has no stencil of its own: the trainer uses the `sagemaker` service icon (Amazon SageMaker AI, aws-icons-artificial-intelligence.md:37), labelled HyperPod GRPO trainer, and stands for the HyperPod instance group plus the HyperPodPyTorchJob on it. aws-icons-aliases.md:14 maps SageMaker AI to `sagemaker_2`, but layout-and-style.md and the scaffold treat `sagemaker_2` as SageMaker Unified Studio (it renders blank in draw.io 26.x and older), so `sagemaker` is used.
- Same id `trainer` as in scenario A with a different icon and label, so the set shows that only the trainer moved.
- Substitutions shared with scenario A: Kubernetes workloads use `container_1`; node groups and instance groups are role groups, not icons; Hugging Face Hub uses `internet`; the operator uses `client`.
- ConfigMap sandbox-routing, the system node group, the HyperPod dependency chart and the training operator add-on are not-drawn rows; edge 5 carries the ConfigMap on the picture.
- Edge 4 (boot script) is drawn from the HyperPod trainer node to the bucket because the node's execution role reads it (lifecycle-bucket-read policy); HyperPod runs the script at node creation.
- Group titles are written as the node group or instance group name plus the instance type, without the words node group, so that each fits two lines of a one-column card (checked with the builder's title wrapping); the guide names them in full.
- The Architecture review heading is written "Architecture review (skipped)" because the guidebook style bans em dashes.
- All drawn text is English because one image serves the Korean and the English pages.
