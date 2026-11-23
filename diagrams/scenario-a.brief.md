# Scenario A: EC2 trainer and gVisor GPU sandboxes on one EKS cluster

On-policy GRPO post-training on one private EKS cluster: a GPU trainer Job on its own EC2 node sends model-written kernels to gVisor (runsc + nvproxy) sandbox pools on separate GPU nodes, and the operator reaches the cluster only through an SSM tunnel. Audience: technical.
Language: ko
Repo: repository root (gpu-sandbox-on-aws)
Components: 16, Relationships: 12

## Scope
| Unit | Path | Deploys with | Region/account (if in code) | Diagram |
|---|---|---|---|---|
| Scenario A (this diagram) | cdk/ with SCENARIO=A, k8s/, scripts/ 20 to 80 | CDK stack CLUSTER_NAME-cdk (cdk/deploy.sh), then numbered scripts with kubectl and helm through cdk/tunnel.sh | us-west-2 by default (scripts/config.env.example:5) | scenario-a |
| Scenario B1 | cdk/ with SCENARIO=B1, scripts/hyperpod/, infra/hyperpod/ | same stack, plus AWS CLI sagemaker create-cluster | same | scenario-b1 |
| Scenario B2 | `scripts/hyperpod/create_managed.sh` | HyperPod EKS wizard template, three HyperPod instance groups | us-east-1 | scenario-b2 |
| Scenario C (CPU only) | cdk/ with SCENARIO=C, scripts/kata/cpu_nodes.sh, ops/simulate.sh, ops/rollout.sh | same stack, only the c8i node group added | same | scenario-c |

Cross-unit: one CDK stack (cdk/gpusandbox_cdk/stack.py) builds A, B1 and C; SCENARIO only selects the node groups (stack.py:224-255). The in-cluster parts (namespaces, NetworkPolicy, routing ConfigMap, sandbox pools) are the same scripts in every scenario, and can be reused in managed B2.

Out of scope (not drawn), one line each:
- WITH_KATA_GPU=1: sandbox-kata-gpu node group (g4dn.metal on the IOMMU AMI, Kata QEMU with GPU passthrough), stack.py:243-255 and scripts/kata/gpu_nodes.sh.
- WITH_KATA_CPU=1 on A: adds the c8i sandbox-kata-cpu node group drawn in scenario-c (stack.py:233-242).
- Demo site (hands-on page 09): private S3 + CloudFront replaying recorded verdicts, demo/infra/site.yaml; it has no path to the cluster.
- Agent Sandbox extension: scripts/extensions/agent_sandbox.sh and k8s/extensions/agent-sandbox/ (unit tested only).
- Production reference (docs/production/): sandbox gateway (k8s/production/gateway.yaml.tpl), jwks-sync CronJob, Karpenter NodePools (infra/karpenter/nodepools.yaml), veRL RayCluster. None of them is deployed by any hands-on scenario.
- EKS_PUBLIC_ACCESS_CIDR: optional public endpoint for one /32 (cdk/gpusandbox_cdk/config.py:78-83), off by default.

## Components
| id | Service (stencil) | Role in this system | Group | Evidence | Provenance |
|---|---|---|---|---|---|
| operator | Operator workstation (`client`, resource) | Runs cdk/deploy.sh and the numbered scripts, kubectl and helm through the tunnel, builds and pushes the images | outside | cdk/tunnel.sh:2-8, scripts/03_build_push_images.sh:20-32 | referenced |
| ssm | SSM Session Manager (`systems_manager_session_manager`, resource) | Port forwarding session (AWS-StartPortForwardingSessionToRemoteHost) from 127.0.0.1:8443 on the workstation to the API endpoint on 443 | Operator access | cdk/tunnel.sh:13-31 | referenced |
| access | Access instance t4g.nano (`t4g_instance`, resource) | SSM-only host in a private subnet: no inbound rules, HTTPS egress only, IMDSv2, AmazonSSMManagedInstanceCore | Operator access | cdk/gpusandbox_cdk/stack.py:75-92 | deployed |
| eks | EKS 1.36 private API (`eks`) | Control plane, private endpoint only, access entries (API_AND_CONFIG_MAP), add-ons vpc-cni with NetworkPolicy, kube-proxy, pod identity agent, CoreDNS | EKS control plane | cdk/gpusandbox_cdk/stack.py:116-166, scripts/config.env.example:9 | deployed |
| kms | KMS secrets key (`key_management_service`) | Customer-managed key with rotation; EKS envelope-encrypts Kubernetes Secrets with it | EKS control plane | cdk/gpusandbox_cdk/stack.py:100-109 | deployed |
| trainer | GRPO trainer Job (`container_1`, resource) | TRL GRPOTrainer with vLLM colocate and LoRA, policy Qwen/Qwen2.5-Coder-1.5B-Instruct; Job in ns rl-trainer with label gpusandbox/client=true, runc, 1x A10G, tainted node gpusandbox/role=trainer | trainer node g5.2xlarge | k8s/trainer/job-grpo.yaml.tpl:1-45, rl/trl/train_grpo.py:121-132, cdk/gpusandbox_cdk/stack.py:224-227 | deployed |
| sbx_v1 | gvisor pool v1 (`container_1`, resource) | Active pool: Deployment and headless Service sandbox-gvisor-v1 in ns sandbox, RuntimeClass gvisor (runsc + nvproxy), one pod per A10G, 2 replicas, default-deny NetworkPolicy | sandbox-gvisor nodes g5.xlarge x2 | k8s/sandbox/deployment.yaml.tpl:1-40, k8s/sandbox/profiles/gvisor.env:1-11, cdk/gpusandbox_cdk/stack.py:228-232 | deployed |
| sbx_v2 | gvisor pool v2 (`container_1`, resource) | Next version sandbox-gvisor-v2 beside v1 (blue/green: 5 seeds, speedup cap 10x); no traffic until parity passes and the routing switch; the node group is scaled to 4 for it | sandbox-gvisor nodes g5.xlarge x2 | k8s/sandbox/versions/v2.env:1-7, scripts/ops/rollout.sh:1-10, docs/handson/06_sandbox_update.md:51-58 | deployed |
| ecr | ECR repositories (`ecr`) | Private repositories gpu-sandbox/sandbox, trainer and control (scan on push, immutable tags), created by scripts/03_build_push_images.sh from the workstation, outside the CDK stack | Shared services | scripts/03_build_push_images.sh:24-40 | deployed |
| cw | CloudWatch Logs (`cloudwatch_2`) | Log group /aws/eks/CLUSTER_NAME/cluster for five control plane log types and the VPC flow log group (REJECT), one-month retention | Shared services | cdk/gpusandbox_cdk/stack.py:66-72, cdk/gpusandbox_cdk/stack.py:110-113 | deployed |
| nat | NAT gateway (`nat_gateway`, resource) | The single egress of the private subnets (one gateway, one AZ) | Egress | cdk/gpusandbox_cdk/stack.py:47-58 | deployed |
| hf | Hugging Face Hub (`internet`, resource) | External source of the policy model weights | outside | scripts/07_run_grpo.sh:11, rl/trl/train_grpo.py:30 | referenced |
| vpc | VPC (`vpc`), not drawn | 2 AZs, public /24 subnets holding only the NAT (no public IPs), private /19 subnets for every node, REJECT flow logs | n/a | cdk/gpusandbox_cdk/stack.py:47-72 | deployed |
| sysng | System node group m6i.large x2 (`ec2_m6i_instance`, resource), not drawn | Untainted nodes for CoreDNS, the add-ons and the operator tool Jobs (probe, parity, bench) that ops/verify.sh, ops/rollout.sh and ops/bench.sh run | n/a | cdk/gpusandbox_cdk/stack.py:218-222, k8s/probe/job-probe.yaml.tpl:1-35 | deployed |
| iam | IAM roles (`role`, resource), not drawn | Cluster role (with KMS grants), node role (EKS worker, CNI, ECR pull only), access instance role, operator access entry | n/a | cdk/gpusandbox_cdk/stack.py:149-170 | deployed |
| routing | Kubernetes ConfigMap sandbox-routing, not drawn | Active runtime and version plus the pool addresses; written by 05_setup_namespaces_auth.sh and ops/rollout.sh, mounted into the trainer as a directory | n/a | k8s/base/routing.json.tpl, scripts/05_setup_namespaces_auth.sh:19-25 | deployed |

## Relationships
| # | From → To | What flows | Kind | Evidence |
|---|---|---|---|---|
| 1 | operator → ssm | kubectl tunnel | sync | cdk/tunnel.sh:29-31 |
| 2 | ssm → access | port forward | sync | cdk/tunnel.sh:20-31, cdk/gpusandbox_cdk/stack.py:79-80 |
| 3 | access → eks | HTTPS 443 | sync | cdk/gpusandbox_cdk/stack.py:78, cdk/gpusandbox_cdk/stack.py:94-97 |
| 4 | eks → trainer | Job, active pool | async (dashed) | k8s/trainer/job-grpo.yaml.tpl:24-27, k8s/trainer/job-grpo.yaml.tpl:47-55, scripts/07_run_grpo.sh:13 |
| 5 | trainer → nat | model pull | sync | rl/trl/train_grpo.py:131-132, k8s/trainer/job-grpo.yaml.tpl:36-41, cdk/gpusandbox_cdk/stack.py:55 |
| 6 | nat → hf | HTTPS | sync | scripts/07_run_grpo.sh:11 |
| 7 | trainer → sbx_v1 | kernel code | sync | src/gpusandbox/client/routing.py:1-17, src/gpusandbox/client/pool.py:1-5, k8s/base/networkpolicies.yaml:15-36 |
| 8 | trainer → sbx_v2 | after switch | sync, after switch (dashed) | scripts/ops/rollout.sh:42-48, src/gpusandbox/client/routing.py:3-6 |
| 9 | sbx_v1 → ecr | image pull | aux (dashed) | k8s/sandbox/deployment.yaml.tpl:66, cdk/gpusandbox_cdk/stack.py:169 |
| 10 | operator → ecr | image push | aux (dashed) | scripts/03_build_push_images.sh:21-32 |
| 11 | eks → cw | control plane logs | aux (dashed) | cdk/gpusandbox_cdk/stack.py:141-144 |
| 12 | eks → kms | encrypt secrets | aux (dashed) | cdk/gpusandbox_cdk/stack.py:137-140 |

## Flow
1. (1 to 3) The operator runs cdk/tunnel.sh: an SSM Session Manager port forwarding session from 127.0.0.1:8443 through the access instance (no inbound rules) to the private EKS endpoint on 443, verified against the real API server name. Every kubectl and helm step (04_install_gpu_stack.sh onward, including the routing switch of ops/rollout.sh) rides this tunnel. The scripts' AWS API calls (CloudFormation, ECR push) go to public AWS endpoints directly.
2. (4) scripts/07_run_grpo.sh applies the GRPO Job in ns rl-trainer; EKS schedules it on the tainted trainer node and mounts ConfigMap sandbox-routing as a directory, so a later patch reaches the running pod (kubelet sync, up to about a minute).
3. (5, 6) The trainer downloads the policy model from the Hugging Face Hub through the NAT gateway; ns rl-trainer has no egress policy.
4. (7) For every reward batch the trainer takes one routing snapshot (active runtime and version), resolves the headless Service sandbox-gvisor-v1 through CoreDNS to the IPs of ready pods, and POSTs each candidate kernel to /v1/evaluate on port 8000 with a projected ServiceAccount token (audience gpu-sandbox). The pod checks the token offline against the JWKS ConfigMap, runs the harness under gVisor on its own A10G and answers with a verdict (status, speedup) on the same call, or 503 busy so the client retries another pod. The trainer turns verdicts into rewards.
5. (8) scripts/ops/rollout.sh deploys v2 beside v1, verifies it with a probe Job, checks parity against v1 and then patches the routing ConfigMap; the trainer switches at its next batch boundary, so no batch mixes versions. v1 is scaled to zero with --finish and kept for rollback.
6. (9, 10) The operator builds the sandbox, trainer and control images (linux/amd64) and pushes them to ECR; nodes pull them with the node role (AmazonEC2ContainerRegistryPullOnly), through the NAT gateway since the stack has no VPC endpoints.
7. (11, 12) The control plane writes api, audit, authenticator, controllerManager and scheduler logs to CloudWatch Logs and envelope-encrypts Secrets with the KMS key. VPC flow logs (REJECT) go to a second CloudWatch log group (the VPC itself is a not-drawn row).
8. Sandbox egress has no edge on purpose: the default-deny NetworkPolicy blocks DNS, IMDS, the internet and the Kubernetes API out of ns sandbox; a pod is Ready only when IMDS, the API server and the node kubelet are unreachable (k8s/sandbox/deployment.yaml.tpl:89-92), and the node guard drops new pod-to-node connections (infra/eks/userdata.py:69-75). The image pull of edge 9 is made by the node's container runtime, not by the pod.

## Groups
Operator access; EKS control plane; trainer node g5.2xlarge (EKS node group trainer); sandbox-gvisor nodes g5.xlarge x2 (EKS node group sandbox-gvisor); Shared services; Egress

## Checks
- [x] Entry: no public entry. The operator is the only caller from outside, through SSM Session Manager; the EKS public endpoint is off (stack.py:127-129). There are no end users.
- [x] Auth: kubectl uses the IAM access entry (stack.py:149-158). The sandbox API takes only a projected ServiceAccount token with audience gpu-sandbox, verified against public keys (scripts/05_setup_namespaces_auth.sh:5-7, scripts/ops/sync_jwks.sh), and NetworkPolicy admits only labelled rl-trainer pods on 8000.
- [x] Async boundaries: none on the request path; trainer to sandbox is one synchronous HTTP call per completion with client-side retry. The version switch is asynchronous through the ConfigMap (edge 4).
- [x] State: ConfigMap sandbox-routing (writer: operator through 05_setup_namespaces_auth.sh and ops/rollout.sh; reader: trainer), ECR (writer: operator; reader: nodes), CloudWatch Logs (writers: control plane, flow logs). Assumption to raise: trainer outputs and the HF cache are emptyDir, so a finished or failed pod loses its checkpoints (k8s/trainer/job-grpo.yaml.tpl:63-66).
- [x] Networking: service level only; VPC and subnets are not drawn. NAT is drawn because the model download path needs it. Question to raise: one NAT gateway in one AZ is a single egress point for image pulls and model downloads.
- [x] Observability: CloudWatch Logs for the control plane and flow logs only. Finding to raise: no alarms, no container log shipping and no metrics to CloudWatch; the trainer's sandbox metrics go to a JSONL file and stdout events (job-grpo.yaml.tpl:37).
- [x] Every stencil looked up in references/aws-icons-*.md; substitutions under Decisions.

## Layout notes (Drawer)
- Main lane left to right: operator (outside), ssm and access (Operator access), eks (EKS control plane), trainer, sbx_v1. sbx_v2 directly below sbx_v1 in the same group; kms below eks.
- Shared services (ecr, cw) and Egress (nat) on the row below; hf outside on the right, level with nat.
- Primary phrases that cross a seam between two group boxes are written with words of at most 6 letters (HTTPS 443, model pull, kernel code, HTTPS). kubectl tunnel is the first hop into the cloud (14 characters). port forward sits inside Operator access.

## Architecture review (skipped)
Skipped: no AWS documentation MCP server (`search_documentation` / `retrieve_skill`) was available in this environment, so no Well-Architected or service-documentation findings were produced and none were substituted from memory. To run Phase 2, add one with `claude mcp add --transport http aws-knowledge https://knowledge-mcp.global.api.aws` and rerun the Assessor. Note for the reader: the CDK stack already runs cdk-nag AwsSolutions checks on every synth and fails the deploy on unacknowledged findings (cdk/app.py:21-22); the findings it accepts, with their reasons, are in cdk/gpusandbox_cdk/stack.py:271-281.

## Decisions & assumptions
- Correction: the hands-on scenarios have no gateway. The trainer calls the pools directly (headless Service, client-side scheduling) and pins the version itself with one routing snapshot per reward batch (src/gpusandbox/client/routing.py:1-6, k8s/trainer/job-grpo.yaml.tpl:39). The gateway with TokenReview and per-group pins is production only (docs/production/00_architecture.md:103).
- Correction: the control image is used here only by the operator tool Jobs (probe, parity, bench) in ns rl-trainer (k8s/probe/job-probe.yaml.tpl:33); it also contains the production gateway (scripts/03_build_push_images.sh:5).
- Correction: the ECR repositories are created by scripts/03_build_push_images.sh:27-29, not by the CDK stack; the stack only grants the node role ECR pull (stack.py:169).
- Substitution: Kubernetes workloads (the trainer Job and the pool Deployments) have no EKS resource stencil, so they use the Containers category resource icon `container_1`, labelled with the workload name; the `eks` service icon stands for the control plane only, so the cluster reads as one service.
- Substitution: node groups are role groups whose titles carry the node group name and instance type, not icons; a node group has no stencil of its own and an EC2 icon per group would double the node count.
- Substitution: Hugging Face Hub (external SaaS) uses the general `internet` resource icon; the operator uses `client`.
- gVisor (runsc + nvproxy) has no stencil; it is named in the pool label and Role, and in the group title through the node group name sandbox-gvisor.
- ConfigMap sandbox-routing is a Kubernetes object, so it is a not-drawn row; edge 4 (Job, active pool) carries it on the picture.
- The system node group (CoreDNS, add-ons, tool Jobs) is a not-drawn row to stay in budget; the trainer's DNS lookup is described in Flow step 4 instead of drawn.
- One representative edge each into CloudWatch Logs (from eks) and ECR (pull from sbx_v1, push from operator); flow logs and the trainer's own image pull are described in Flow.
- Group titles are written as the node group or instance group name plus the instance type, without the words node group, so that each fits two lines of a one-column card (checked with the builder's title wrapping); the guide names them in full.
- The Architecture review heading is written "Architecture review (skipped)" because the guidebook style bans em dashes.
- All drawn text (labels, group titles, What flows) is English because one image serves the Korean and the English pages.
