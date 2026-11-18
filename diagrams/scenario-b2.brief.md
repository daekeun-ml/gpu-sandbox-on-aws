# Scenario B2: HyperPod trainer and gVisor sandboxes on a HyperPod instance group (experimental)

Trainer and GPU sandboxes both run on SageMaker HyperPod instance groups attached to the private EKS cluster; the sandbox instance group boots from a custom AMI, baked once from the HyperPod public base AMI with an NVIDIA driver that gVisor nvproxy supports, and EKS keeps only its system node group. Not run on AWS by the authors (docs/handson/07_hyperpod.md:70). Audience: technical.
Language: ko
Repo: repository root (gpu-sandbox-on-aws)
Components: 21, Relationships: 18

## Scope
| Unit | Path | Deploys with | Region/account (if in code) | Diagram |
|---|---|---|---|---|
| Scenario A | cdk/ with SCENARIO=A, k8s/, scripts/ 20 to 80 | CDK stack CLUSTER_NAME-cdk (cdk/deploy.sh), then numbered scripts with kubectl and helm through cdk/tunnel.sh | us-west-2 by default (scripts/config.env.example:5) | scenario-a |
| Scenario B1 | cdk/ with SCENARIO=B1, scripts/hyperpod/, infra/hyperpod/ | same stack, plus sagemaker create-cluster | same | scenario-b1 |
| Scenario B2 (this diagram) | cdk/ with SCENARIO=B2 (scripts/02_create_cluster.sh --hyperpod-b2), infra/hyperpod/ami/, scripts/hyperpod/build_b2_ami.sh and create.sh --b2 | same stack (system node group only), plus scripts/hyperpod/build_b2_ami.sh (EC2 builder, create-image) and hyperpod/create.sh --b2 (two instance groups) | same | scenario-b2 |
| Scenario C (CPU only) | cdk/ with SCENARIO=C, scripts/kata/cpu_nodes.sh, ops/simulate.sh, ops/rollout.sh | same stack, only the c8i node group added | same | scenario-c |

Cross-unit: one CDK stack builds all four; for B2 it creates only the system node group (stack.py:218-232). The AMI build is a one-time step that runs before the HyperPod cluster exists; it is drawn because the custom AMI is what makes gVisor possible on HyperPod.

Out of scope (not drawn), one line each:
- WITH_KATA_GPU=1 and WITH_KATA_CPU=1 node groups (stack.py:233-255); Kata on HyperPod nodes is not possible (docs/handson/07_hyperpod.md:495).
- Demo site (hands-on page 09): private S3 + CloudFront, demo/infra/site.yaml; no path to the cluster.
- Agent Sandbox extension: scripts/extensions/agent_sandbox.sh, k8s/extensions/agent-sandbox/.
- Production reference (docs/production/): gateway, jwks-sync CronJob, Karpenter NodePools, veRL RayCluster.
- EKS_PUBLIC_ACCESS_CIDR: optional public endpoint for one /32 (cdk/gpusandbox_cdk/config.py:78-83), off by default.

## Components
| id | Service (stencil) | Role in this system | Group | Evidence | Provenance |
|---|---|---|---|---|---|
| operator | Operator workstation (`client`, resource) | Runs cdk/deploy.sh, the numbered and HyperPod scripts, kubectl and helm through the tunnel, builds and pushes the images (HYPERPOD=1) | outside | cdk/tunnel.sh:2-8, scripts/03_build_push_images.sh:20-40 | referenced |
| ssm | SSM Session Manager (`systems_manager_session_manager`, resource) | Port forwarding session (AWS-StartPortForwardingSessionToRemoteHost) from 127.0.0.1:8443 on the workstation to the API endpoint on 443 | Operator access | cdk/tunnel.sh:13-31 | referenced |
| access | Access instance t4g.nano (`t4g_instance`, resource) | SSM-only host in a private subnet: no inbound rules, HTTPS egress only, IMDSv2, AmazonSSMManagedInstanceCore | Operator access | cdk/gpusandbox_cdk/stack.py:75-92 | deployed |
| eks | EKS 1.36 private API (`eks`) | Control plane, private endpoint only, access entries (API_AND_CONFIG_MAP), add-ons vpc-cni with NetworkPolicy, kube-proxy, pod identity agent, CoreDNS, and the HyperPod training operator | EKS control plane | cdk/gpusandbox_cdk/stack.py:116-166, scripts/hyperpod/create.sh:96-104 | deployed |
| kms | KMS secrets key (`key_management_service`) | Customer-managed key with rotation; EKS envelope-encrypts Kubernetes Secrets with it | EKS control plane | cdk/gpusandbox_cdk/stack.py:100-109 | deployed |
| trainer | HyperPod GRPO trainer (`sagemaker`) | HyperPodPyTorchJob in ns rl-trainer (hyperpodrun, the same train_grpo.py) on HyperPod instance group trainer, 1x ml.g5.2xlarge; NodeRecovery Automatic, job retries and log-based hang detection | HyperPod trainer ml.g5.2xlarge | k8s/trainer/hyperpod-job-grpo.yaml.tpl:1-64, infra/hyperpod/cluster.json.tpl:1-22, scripts/config.env.example:45 | deployed |
| sbx_v1 | gvisor-hyperpod pool v1 (`container_1`, resource) | Active pool: Deployment and headless Service sandbox-gvisor-hyperpod-v1 in ns sandbox, RuntimeClass gvisor-hyperpod (runsc + nvproxy), 1 replica per version, default-deny NetworkPolicy | HyperPod sandbox ml.g5.xlarge x2 | k8s/sandbox/profiles/gvisor-hyperpod.env:1-14, k8s/runtimes/runtimeclass-gvisor-hyperpod.yaml, infra/hyperpod/instance-group-sandbox.json.tpl:1-16 | deployed |
| sbx_v2 | gvisor-hyperpod pool v2 (`container_1`, resource) | Next version sandbox-gvisor-hyperpod-v2 on the second sandbox node (blue/green); no traffic until parity passes and the routing switch | HyperPod sandbox ml.g5.xlarge x2 | k8s/sandbox/versions/v2.env:1-7, k8s/sandbox/profiles/gvisor-hyperpod.env:12-14, scripts/ops/rollout.sh:1-10 | deployed |
| builder | AMI builder m6i.large (`ec2_m6i_instance`, resource) | Plain EC2 instance from the newest HyperPod EKS 1.36 AL2023 public base AMI in an EKS private subnet; user data swaps NVIDIA 595.91.07 for 580.178.04, installs the pinned gVisor, powers off; terminated after imaging | AMI build (one time) | infra/hyperpod/ami/build-b2-ami.sh:16-59, infra/hyperpod/ami/customize-b2.sh:1-13 | deployed |
| ami | Custom AMI, NVIDIA 580.178.04 (`ami`, resource) | hyperpod-eks-1.36-gvisor-nv580.178.04 image: ImageId of the HyperPod sandbox instance group; deregistered by 08_cleanup.sh | AMI build (one time) | infra/hyperpod/ami/build-b2-ami.sh:70-86, scripts/config.env.example:49-59 | deployed |
| ecr | ECR repositories (`ecr`) | Private repositories gpu-sandbox/sandbox, trainer and control (scan on push, immutable tags), created by scripts/03_build_push_images.sh from the workstation, outside the CDK stack | Shared services | scripts/03_build_push_images.sh:24-40 | deployed |
| cw | CloudWatch Logs (`cloudwatch_2`) | Log group /aws/eks/CLUSTER_NAME/cluster for five control plane log types and the VPC flow log group (REJECT), one-month retention | Shared services | cdk/gpusandbox_cdk/stack.py:66-72, cdk/gpusandbox_cdk/stack.py:110-113 | deployed |
| nat | NAT gateway (`nat_gateway`, resource) | The single egress of the private subnets, which both HyperPod instance groups and the builder use | Egress | cdk/gpusandbox_cdk/stack.py:47-58, scripts/hyperpod/create.sh:74-81 | deployed |
| lcs | S3 lifecycle scripts (`s3`) | Private bucket sagemaker-...-lcs (Block Public Access on) holding on_create.sh, on_create_sandbox.sh, register_runsc.sh and node-guard.sh | Shared services | scripts/hyperpod/create.sh:39-52, infra/hyperpod/lifecycle/on_create_sandbox.sh:1-11 | deployed |
| hf | Hugging Face Hub (`internet`, resource) | External source of the policy model weights | outside | scripts/hyperpod/run_grpo.sh:11, rl/trl/train_grpo.py:30 | referenced |
| vpc | VPC (`vpc`), not drawn | 2 AZs, public /24 subnets holding only the NAT, private /19 subnets; the HyperPod instance groups get one private subnet and the EKS cluster security group | n/a | cdk/gpusandbox_cdk/stack.py:47-72, scripts/hyperpod/create.sh:74-81 | deployed |
| sysng | System node group m6i.large x2 (`ec2_m6i_instance`, resource), not drawn | The only EKS node group in B2: CoreDNS, the add-ons, the HyperPod dependency chart and the operator tool Jobs (probe, parity, bench) | n/a | cdk/gpusandbox_cdk/stack.py:218-232, k8s/probe/job-probe.yaml.tpl:1-35 | deployed |
| iam | IAM roles (`role`, resource), not drawn | Cluster, node and access roles from CDK; HyperPod execution role with AmazonSageMakerClusterInstanceRolePolicy, ENI and ECR pull, and lifecycle bucket read | n/a | cdk/gpusandbox_cdk/stack.py:149-170, scripts/hyperpod/create.sh:54-69 | deployed |
| routing | Kubernetes ConfigMap sandbox-routing, not drawn | Active runtime gvisor-hyperpod and version plus the pool addresses; written by 05_setup_namespaces_auth.sh and ops/rollout.sh, mounted into the trainer pod | n/a | k8s/base/routing.json.tpl, docs/handson/07_hyperpod.md:351-363 | deployed |
| hpaddon | HyperPod dependency chart and training operator add-on (`eks`), not drawn | Helm release hyperpod-dependencies and EKS add-on amazon-sagemaker-hyperpod-training-operator; RuntimeClass gvisor-hyperpod is applied in the same script | n/a | scripts/hyperpod/create.sh:33-37, scripts/hyperpod/create.sh:96-103 | deployed |
| baseami | HyperPod EKS public base AMI (`ami`, resource), not drawn | Owner amazon, named HyperPod EKS 1.36 x86_64 AMI Amazon Linux 2023 with a timestamp; HyperPod accepts custom AMIs only when built from it | n/a | infra/hyperpod/ami/build-b2-ami.sh:6-24 | referenced |

## Relationships
| # | From → To | What flows | Kind | Evidence |
|---|---|---|---|---|
| 1 | operator → ssm | kubectl tunnel | sync | cdk/tunnel.sh:29-31 |
| 2 | ssm → access | port forward | sync | cdk/tunnel.sh:20-31, cdk/gpusandbox_cdk/stack.py:79-80 |
| 3 | access → eks | HTTPS 443 | sync | cdk/gpusandbox_cdk/stack.py:78, cdk/gpusandbox_cdk/stack.py:94-97 |
| 4 | operator → builder | launch builder | aux (dashed) | infra/hyperpod/ami/build-b2-ami.sh:45-50 |
| 5 | builder → ami | create image | async, one time (dashed) | infra/hyperpod/ami/build-b2-ami.sh:61-79 |
| 6 | ami → sbx_v1 | node image | async, one time (dashed) | infra/hyperpod/instance-group-sandbox.json.tpl:5, scripts/hyperpod/create.sh:83-88 |
| 7 | sbx_v1 → lcs | runsc setup | async, boot time (dashed) | infra/hyperpod/instance-group-sandbox.json.tpl:6-9, infra/hyperpod/lifecycle/on_create_sandbox.sh:1-11 |
| 8 | trainer → lcs | boot script | async, boot time (dashed) | infra/hyperpod/cluster.json.tpl:9-12, scripts/hyperpod/create.sh:63-66 |
| 9 | eks → trainer | Job, active pool | async (dashed) | k8s/trainer/hyperpod-job-grpo.yaml.tpl:42-52, k8s/trainer/hyperpod-job-grpo.yaml.tpl:82-84, scripts/hyperpod/run_grpo.sh:13 |
| 10 | trainer → nat | model pull | sync | k8s/trainer/hyperpod-job-grpo.yaml.tpl:60-68, scripts/hyperpod/create.sh:76-81 |
| 11 | nat → hf | HTTPS | sync | scripts/hyperpod/run_grpo.sh:11 |
| 12 | trainer → sbx_v1 | kernel code | sync | k8s/trainer/hyperpod-job-grpo.yaml.tpl:36-38, src/gpusandbox/client/routing.py:1-17, k8s/base/networkpolicies.yaml:15-36 |
| 13 | trainer → sbx_v2 | after switch | sync, after switch (dashed) | scripts/ops/rollout.sh:42-48, src/gpusandbox/client/routing.py:3-6 |
| 14 | sbx_v1 → ecr | image pull | aux (dashed) | infra/hyperpod/execution-role-eks-policy.json:24-27 |
| 15 | operator → ecr | image push | aux (dashed) | scripts/03_build_push_images.sh:21-32 |
| 16 | operator → lcs | script upload | aux (dashed) | scripts/hyperpod/create.sh:50-52 |
| 17 | eks → cw | control plane logs | aux (dashed) | cdk/gpusandbox_cdk/stack.py:141-144 |
| 18 | eks → kms | encrypt secrets | aux (dashed) | cdk/gpusandbox_cdk/stack.py:137-140 |

## Flow
1. (1 to 3) The operator opens cdk/tunnel.sh (SSM port forwarding from 127.0.0.1:8443 through the access instance to the private API on 443). 04_install_gpu_stack.sh and 05_setup_namespaces_auth.sh run through it while EKS has only the system nodes; 05_setup_namespaces_auth.sh sets the active runtime to gvisor-hyperpod.
2. (4, 5) scripts/hyperpod/build_b2_ami.sh launches an m6i.large from the newest HyperPod EKS 1.36 public base AMI in an EKS private subnet. Its user data replaces NVIDIA 595.91.07 (unknown to gVisor release-20261109.0 nvproxy) with 580.178.04, the driver of the EC2 gVisor nodes, installs gVisor, and powers off; the script images the stopped instance and terminates it (20 to 40 minutes, estimate). Building the kernel module needs no GPU.
3. (6, 7) scripts/hyperpod/create.sh --b2 adds instance group sandbox (2x ml.g5.xlarge, ImageId = the custom AMI, label and taint gpusandbox/role=sandbox-hyperpod). On each node on_create_sandbox.sh from the bucket checks that the loaded driver is on runsc's nvproxy list, registers the runsc handler with containerd and installs the node guard; it fails the node instead of joining it without gVisor.
4. (8, 9) The trainer instance group runs the minimal on_create.sh; scripts/hyperpod/run_grpo.sh applies the HyperPodPyTorchJob, the training operator starts it on the HyperPod trainer node and the kubelet mounts ConfigMap sandbox-routing.
5. (10, 11) The trainer downloads the policy model from the Hugging Face Hub through the NAT gateway.
6. (12, 13) Reward path as in scenarios A and B1, now to sandbox-gvisor-hyperpod-v1 on the HyperPod sandbox nodes; during a rollout v2 runs on the second sandbox node (one replica per version) and the trainer switches at the next batch boundary after parity and the ConfigMap patch.
7. (14 to 18) HyperPod nodes pull images with the execution role (ECR pull actions); the operator pushes the images and syncs the lifecycle scripts. The control plane logs to CloudWatch Logs and encrypts Secrets with the KMS key; VPC flow logs (REJECT) go to a second log group.
8. Sandbox egress has no edge on purpose: default-deny NetworkPolicy, readiness that requires IMDS, the API server and the kubelet to be unreachable, and the node guard installed by the lifecycle script. Node failures are handled by HyperPod NodeRecovery (reboot or replace) instead of the EKS managed node group.

## Groups
Operator access; EKS control plane; HyperPod trainer ml.g5.2xlarge (HyperPod instance group trainer); HyperPod sandbox ml.g5.xlarge x2 (HyperPod instance group sandbox); AMI build (one time); Shared services; Egress

## Checks
- [x] Entry: no public entry; the operator reaches the API only through SSM Session Manager. No end users.
- [x] Auth: kubectl uses the IAM access entry; the sandbox API takes only a projected ServiceAccount token with audience gpu-sandbox and NetworkPolicy admits only labelled rl-trainer pods.
- [x] Async boundaries: none on the request path; version switch through the ConfigMap (edge 9); AMI build and lifecycle scripts are one-time or boot-time steps (edges 5 to 8).
- [x] State: ConfigMap sandbox-routing, ECR, lifecycle bucket (writer: operator; readers: both instance groups), custom AMI and its snapshot (writer: builder; reader: HyperPod; kept until 08_cleanup.sh), CloudWatch Logs. Assumption to raise: /outputs is emptyDir, so a node replacement loses checkpoints.
- [x] Networking: service level; HyperPod and builder egress through the NAT gateway is inferred from the private subnets the scripts select.
- [x] Observability: control plane and flow logs only; the builder reports its result on the serial console (build-b2-ami.sh:61-68). Finding to raise: no CloudWatch alarms.
- [x] Every stencil looked up in references/aws-icons-*.md; substitutions under Decisions.

## Layout notes (Drawer)
- Main lane left to right: operator (outside), ssm and access, eks, trainer, sbx_v1; sbx_v2 below sbx_v1, kms below eks.
- AMI build group (builder, ami) above the HyperPod sandbox group so that ami to sbx_v1 runs vertically; Shared services (ecr, cw, lcs) and Egress (nat) on the row below; hf outside on the right, level with nat.
- Primary phrases on seams between group boxes use words of at most 6 letters.

## Architecture review (skipped)
Skipped: no AWS documentation MCP server (`search_documentation` / `retrieve_skill`) was available in this environment, so no Well-Architected or service-documentation findings were produced and none were substituted from memory. To run Phase 2, add one with `claude mcp add --transport http aws-knowledge https://knowledge-mcp.global.api.aws` and rerun the Assessor. Note for the reader: the CDK stack already runs cdk-nag AwsSolutions checks on every synth and fails the deploy on unacknowledged findings (cdk/app.py:21-22); the findings it accepts, with their reasons, are in cdk/gpusandbox_cdk/stack.py:271-281. The HyperPod resources, the AMI builder and the custom AMI are created by AWS CLI calls and are not covered by cdk-nag.

## Decisions & assumptions
- Correction: no gateway; the trainer calls the pools directly and pins the version per reward batch (src/gpusandbox/client/routing.py:1-6). The gateway is production only (docs/production/00_architecture.md:103).
- Correction (repository docs disagree): docs/production/00_architecture.md:164 still says gVisor on HyperPod nodes (B2) is impossible because of driver 595.91.07, while docs/handson/07_hyperpod.md:312-349 and the code (infra/hyperpod/ami/) implement it with the custom AMI. This brief follows the code.
- The AMI build pipeline is drawn (builder and custom AMI, group AMI build) because it is what makes B2 possible; the public base AMI is a not-drawn row and is named in the builder's Role.
- Edge 6 (node image) ends on sbx_v1 because the HyperPod sandbox instance group is a role group, not a node; the AMI boots both sandbox nodes and therefore both pools.
- Edge 7 (runsc setup) is drawn from the sandbox side to the bucket because on_create_sandbox.sh is what registers runsc and the node guard on HyperPod; edge 8 is the trainer group's minimal on_create.sh.
- HyperPod has no stencil of its own: the trainer uses the `sagemaker` service icon (Amazon SageMaker AI), labelled HyperPod GRPO trainer, as in scenario B1. aws-icons-aliases.md:14 points SageMaker AI at `sagemaker_2`, but layout-and-style.md and the scaffold treat `sagemaker_2` as Unified Studio, so `sagemaker` is used.
- The sandbox pools keep `container_1` like every other scenario; the HyperPod placement is carried by the group title HyperPod sandbox ml.g5.xlarge x2.
- Substitutions shared with the other scenarios: node groups and instance groups are role groups, Hugging Face Hub uses `internet`, the operator uses `client`; the builder uses the M6i instance resource icon and the custom AMI the AMI resource icon.
- Not drawn: the gVisor download from storage.googleapis.com and the NVIDIA driver download during the build (infra/gvisor/install-gvisor.sh:16, infra/hyperpod/ami/customize-b2.sh:47-59); both leave through the NAT gateway.
- This diagram has 15 drawn components, the top of the budget; nothing else fits without a second page.
- Group titles are written as the node group or instance group name plus the instance type, without the words node group, so that each fits two lines of a one-column card (checked with the builder's title wrapping); the guide names them in full.
- The Architecture review heading is written "Architecture review (skipped)" because the guidebook style bans em dashes.
- All drawn text is English because one image serves the Korean and the English pages.
