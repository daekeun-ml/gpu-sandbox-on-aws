# Scenario C: CPU-only sandboxes on one nested-virtualization c8i node

The cheapest path: no GPU anywhere. One c8i.2xlarge node with EC2 nested virtualization runs three CPU sandbox runtimes side by side (gVisor runsc, Kata with Cloud Hypervisor, Kata with QEMU), and a model-free reward loop Job on the system nodes replaces the trainer to exercise routing and the v1 to v2 rollout. This is not training. Audience: technical.
Language: ko
Repo: repository root (gpu-sandbox-on-aws)
Components: 17, Relationships: 12

## Scope
| Unit | Path | Deploys with | Region/account (if in code) | Diagram |
|---|---|---|---|---|
| Scenario A | cdk/ with SCENARIO=A, k8s/, scripts/ 20 to 80 | CDK stack CLUSTER_NAME-cdk (cdk/deploy.sh), then numbered scripts with kubectl and helm through cdk/tunnel.sh | us-west-2 by default (scripts/config.env.example:5) | scenario-a |
| Scenario B1 | cdk/ with SCENARIO=B1, scripts/hyperpod/, infra/hyperpod/ | same stack, plus sagemaker create-cluster | same | scenario-b1 |
| Scenario B2 (experimental) | cdk/ with SCENARIO=B2, infra/hyperpod/ami/, scripts/hyperpod/ | same stack, plus an EC2 AMI builder and create-cluster with a second instance group | same | scenario-b2 |
| Scenario C (this diagram) | cdk/ with SCENARIO=C (scripts/02_create_cluster.sh --cpu-only), scripts/03_build_push_images.sh --no-trainer, kata/cpu_nodes.sh, 05_setup_namespaces_auth.sh, 06_deploy_sandboxes.sh, ops/verify.sh, ops/simulate.sh, ops/rollout.sh | same stack: system node group plus sandbox-kata-cpu, then the scripts above through the tunnel | same | scenario-c |

Cross-unit: one CDK stack builds all four; SCENARIO=C turns on the sandbox-kata-cpu node group and drops every GPU node group (cdk/gpusandbox_cdk/config.py:95, stack.py:224-242). The same c8i node group is the optional CPU tier of the other scenarios (WITH_KATA_CPU=1).

Out of scope (not drawn), one line each:
- WITH_KATA_GPU=1: sandbox-kata-gpu node group (g4dn.metal, Kata QEMU with GPU passthrough), stack.py:243-255.
- Agent Sandbox extension (docs/handson/10_cpu_only.md:262): scripts/extensions/agent_sandbox.sh, k8s/extensions/agent-sandbox/ (unit tested only).
- Demo site (hands-on page 09): private S3 + CloudFront, demo/infra/site.yaml; no path to the cluster.
- Production reference (docs/production/): gateway, jwks-sync CronJob, Karpenter NodePools (sandbox-kata-cpu NodePool with c8i, m8i, r8i), veRL RayCluster.
- EKS_PUBLIC_ACCESS_CIDR: optional public endpoint for one /32 (cdk/gpusandbox_cdk/config.py:78-83), off by default.

## Components
| id | Service (stencil) | Role in this system | Group | Evidence | Provenance |
|---|---|---|---|---|---|
| operator | Operator workstation (`client`, resource) | Runs cdk/deploy.sh and the numbered scripts, kubectl and helm through the tunnel, builds and pushes the sandbox and control images | outside | cdk/tunnel.sh:2-8, scripts/03_build_push_images.sh:8-40 | referenced |
| ssm | SSM Session Manager (`systems_manager_session_manager`, resource) | Port forwarding session (AWS-StartPortForwardingSessionToRemoteHost) from 127.0.0.1:8443 on the workstation to the API endpoint on 443 | Operator access | cdk/tunnel.sh:13-31 | referenced |
| access | Access instance t4g.nano (`t4g_instance`, resource) | SSM-only host in a private subnet: no inbound rules, HTTPS egress only, IMDSv2, AmazonSSMManagedInstanceCore | Operator access | cdk/gpusandbox_cdk/stack.py:75-92 | deployed |
| eks | EKS 1.36 private API (`eks`) | Control plane, private endpoint only, access entries, add-ons vpc-cni with NetworkPolicy, kube-proxy, pod identity agent, CoreDNS | EKS control plane | cdk/gpusandbox_cdk/stack.py:116-166, scripts/config.env.example:9 | deployed |
| kms | KMS secrets key (`key_management_service`) | Customer-managed key with rotation; EKS envelope-encrypts Kubernetes Secrets with it | EKS control plane | cdk/gpusandbox_cdk/stack.py:100-109 | deployed |
| sim | simulate and probe Jobs (`container_1`, resource) | One-shot Jobs from one template in ns rl-trainer (control image, label gpusandbox/client=true): simulate (71) scores golden submissions batch by batch through the routing table with the trainer's reward code; probe (61), parity (80) and bench (90) use the same template | system nodes m6i.large x2 | k8s/probe/job-probe.yaml.tpl:1-56, scripts/ops/simulate.sh:1-21, src/gpusandbox/tools.py:229-259, cdk/gpusandbox_cdk/stack.py:218-220 | deployed |
| sbx_v1 | kata-clh-cpu pool v1 (`container_1`, resource) | Active pool sandbox-kata-clh-cpu-v1 in ns sandbox: one Kata microVM per pod on Cloud Hypervisor (RuntimeClass kata-clh), CPU only, default-deny NetworkPolicy | sandbox-kata-cpu node c8i.2xlarge | k8s/sandbox/profiles/kata-clh-cpu.env:1-12, docs/handson/10_cpu_only.md:186-194, cdk/gpusandbox_cdk/stack.py:233-242 | deployed |
| sbx_v2 | kata-clh-cpu pool v2 (`container_1`, resource) | Next version sandbox-kata-clh-cpu-v2 beside v1 (blue/green, recycles each pod VM every 200 evaluations); no traffic until parity passes and the routing switch | sandbox-kata-cpu node c8i.2xlarge | k8s/sandbox/versions/v2.env:1-7, docs/handson/10_cpu_only.md:211-225 | deployed |
| sbx_gvisor | gvisor-cpu pool v1 (`container_1`, resource) | Pool sandbox-gvisor-cpu-v1: gVisor runsc on the systrap platform without nvproxy (RuntimeClass gvisor-cpu), installed by the node's user data | sandbox-kata-cpu node c8i.2xlarge | k8s/sandbox/profiles/gvisor-cpu.env:1-12, k8s/runtimes/runtimeclass-gvisor-cpu.yaml, infra/eks/userdata.py:78-86 | deployed |
| sbx_qemu | kata-qemu-cpu pool v1 (`container_1`, resource) | Pool sandbox-kata-qemu-cpu-v1: one Kata microVM per pod on QEMU (RuntimeClass kata-qemu), the comparison baseline | sandbox-kata-cpu node c8i.2xlarge | k8s/sandbox/profiles/kata-qemu-cpu.env:1-11, scripts/kata/cpu_nodes.sh:16-27 | deployed |
| ecr | ECR repositories (`ecr`) | Private repositories gpu-sandbox/sandbox and control (scan on push, immutable tags); the trainer image is skipped with --no-trainer | Registry | scripts/03_build_push_images.sh:8-46 | deployed |
| cw | CloudWatch Logs (`cloudwatch_2`) | Log group /aws/eks/CLUSTER_NAME/cluster for five control plane log types and the VPC flow log group (REJECT), one-month retention | Shared services | cdk/gpusandbox_cdk/stack.py:66-72, cdk/gpusandbox_cdk/stack.py:110-113 | deployed |
| vpc | VPC (`vpc`), not drawn | 2 AZs, public /24 subnets holding only the NAT, private /19 subnets for every node, REJECT flow logs | n/a | cdk/gpusandbox_cdk/stack.py:47-72 | deployed |
| nat | NAT gateway (`nat_gateway`, resource), not drawn | Still deployed (the single egress for image pulls, the gVisor download at boot and the kata-deploy chart), but C has no model download, so no drawn edge needs it | n/a | cdk/gpusandbox_cdk/stack.py:47-58 | deployed |
| iam | IAM roles (`role`, resource), not drawn | Cluster role (with KMS grants), node role (EKS worker, CNI, ECR pull only), access instance role, operator access entry | n/a | cdk/gpusandbox_cdk/stack.py:149-170 | deployed |
| routing | Kubernetes ConfigMap sandbox-routing, not drawn | Active runtime kata-clh-cpu (05_setup_namespaces_auth.sh with ACTIVE_RUNTIME=kata-clh-cpu) and version plus the pool addresses; written by 05_setup_namespaces_auth.sh and ops/rollout.sh, mounted into the Jobs as a directory | n/a | k8s/base/routing.json.tpl, scripts/05_setup_namespaces_auth.sh:19-25 | deployed |
| katadeploy | kata-deploy DaemonSet (Helm release in kube-system), not drawn | Installs Kata on the c8i node only and creates RuntimeClasses kata-clh and kata-qemu; scripts/kata/cpu_nodes.sh adds RuntimeClass gvisor-cpu | n/a | scripts/kata/cpu_nodes.sh:16-27, infra/kata/kata-deploy-values.yaml | deployed |

## Relationships
| # | From → To | What flows | Kind | Evidence |
|---|---|---|---|---|
| 1 | operator → ssm | kubectl tunnel | sync | cdk/tunnel.sh:29-31 |
| 2 | ssm → access | port forward | sync | cdk/tunnel.sh:20-31, cdk/gpusandbox_cdk/stack.py:79-80 |
| 3 | access → eks | HTTPS 443 | sync | cdk/gpusandbox_cdk/stack.py:78, cdk/gpusandbox_cdk/stack.py:94-97 |
| 4 | eks → sim | Job, active pool | async (dashed) | scripts/lib_jobs.sh:6-13, k8s/probe/job-probe.yaml.tpl:45-49, scripts/ops/simulate.sh:13-21 |
| 5 | sim → sbx_v1 | golden code | sync | src/gpusandbox/tools.py:229-259, k8s/base/networkpolicies.yaml:15-36, docs/handson/10_cpu_only.md:211-218 |
| 6 | sim → sbx_v2 | after switch | sync, after switch (dashed) | scripts/ops/rollout.sh:36-48, docs/handson/10_cpu_only.md:220-240 |
| 7 | sim → sbx_gvisor | probe, bench | sync, test runs (dashed) | scripts/ops/verify.sh:52, scripts/ops/bench.sh:30 |
| 8 | sim → sbx_qemu | probe, bench | sync, test runs (dashed) | scripts/ops/verify.sh:52, scripts/ops/bench.sh:30 |
| 9 | sbx_v1 → ecr | image pull | aux (dashed) | k8s/sandbox/deployment.yaml.tpl:66, cdk/gpusandbox_cdk/stack.py:169 |
| 10 | operator → ecr | image push | aux (dashed) | scripts/03_build_push_images.sh:21-40 |
| 11 | eks → cw | control plane logs | aux (dashed) | cdk/gpusandbox_cdk/stack.py:141-144 |
| 12 | eks → kms | encrypt secrets | aux (dashed) | cdk/gpusandbox_cdk/stack.py:137-140 |

## Flow
1. (1 to 3) The operator opens cdk/tunnel.sh (SSM port forwarding from 127.0.0.1:8443 through the access instance to the private API on 443); kubectl and helm from scripts/kata/cpu_nodes.sh onward run through it.
2. (4) scripts/ops/simulate.sh renders k8s/probe/job-probe.yaml.tpl as Job simulate in ns rl-trainer. The Job has no node selector or toleration, so only the untainted system nodes take it; it mounts ConfigMap sandbox-routing as a directory and a projected token (audience gpu-sandbox). It runs inside the cluster, not on the workstation; the script only follows its logs.
3. (5) Every 20 seconds (30 batches by default) the Job takes one routing snapshot, sends the golden submissions (4 CPU goldens, standing in for completions) to the active pool kata-clh-cpu v1 through its headless Service, and prints reward_batch events computed by the trainer's own KernelRewards code (require_triton off).
4. (6) In a second terminal scripts/ops/rollout.sh kata-clh-cpu v1 v2 deploys v2, verifies it, checks parity and patches the ConfigMap; the Job prints sandbox_version_switch at a batch boundary and served_versions never mixes v1 and v2.
5. (7, 8) ops/verify.sh (probe: isolation evidence, egress blocked, golden verdicts) and ops/bench.sh (bench: cold start and latency) run the same Job template against gvisor-cpu and kata-qemu-cpu as well, so all three runtimes are checked on one node under the same conditions. Speedups measured on nested virtualization are not used as reward evidence.
6. (9, 10) The operator pushes the sandbox and control images; the c8i and system nodes pull them with the node role.
7. (11, 12) The control plane logs to CloudWatch Logs and encrypts Secrets with the KMS key; VPC flow logs (REJECT) go to a second log group.
8. Sandbox egress has no edge on purpose: default-deny NetworkPolicy in ns sandbox, readiness that requires IMDS, the API server and the kubelet to be unreachable, and the node guard from the c8i node's user data.

## Groups
Operator access; EKS control plane; system nodes m6i.large x2 (EKS node group system); sandbox-kata-cpu node c8i.2xlarge (EKS node group sandbox-kata-cpu); Shared services; Registry

## Checks
- [x] Entry: no public entry; the operator reaches the API only through SSM Session Manager. No end users.
- [x] Auth: kubectl uses the IAM access entry; the sandbox API takes only a projected ServiceAccount token with audience gpu-sandbox and NetworkPolicy admits only labelled rl-trainer pods, which the Job carries (k8s/probe/job-probe.yaml.tpl:22).
- [x] Async boundaries: none on the request path; the version switch is asynchronous through the ConfigMap (edge 4).
- [x] State: ConfigMap sandbox-routing (writer: operator; reader: the Jobs), ECR, CloudWatch Logs. No model, no checkpoints.
- [x] Networking: service level; NAT is a not-drawn row because no drawn edge leaves the VPC.
- [x] Observability: control plane and flow logs only; reward_batch and sandbox_version_switch events go to the Job's stdout. Finding to raise: no CloudWatch alarms.
- [x] Every stencil looked up in references/aws-icons-*.md; substitutions under Decisions.

## Layout notes (Drawer)
- Main lane left to right: operator (outside), ssm and access, eks, sim, sbx_v1; sbx_v2 below sbx_v1; sbx_gvisor and sbx_qemu in the second column of the sandbox group; kms below eks.
- sim is a hub (5 edges): keep its column free above and below.
- Shared services (cw) on the row below; Registry (ecr) at the bottom right, because sbx_v1 reaches it only from its right side.
- Primary phrases on seams between group boxes use words of at most 6 letters (golden code, probe, bench).

## Architecture review (skipped)
Skipped: no AWS documentation MCP server (`search_documentation` / `retrieve_skill`) was available in this environment, so no Well-Architected or service-documentation findings were produced and none were substituted from memory. To run Phase 2, add one with `claude mcp add --transport http aws-knowledge https://knowledge-mcp.global.api.aws` and rerun the Assessor. Note for the reader: the CDK stack already runs cdk-nag AwsSolutions checks on every synth and fails the deploy on unacknowledged findings (cdk/app.py:21-22); the findings it accepts, with their reasons, are in cdk/gpusandbox_cdk/stack.py:271-281.

## Decisions & assumptions
- Correction: the reward loop runs in the cluster, as Job simulate in ns rl-trainer on the system nodes (scripts/ops/simulate.sh:3-5, scripts/lib_jobs.sh:12-13), not from the workstation through the tunnel; the workstation only applies it and follows its logs.
- Correction: the three CPU pools are named gvisor-cpu, kata-clh-cpu and kata-qemu-cpu; their RuntimeClasses are gvisor-cpu, kata-clh and kata-qemu. The active pool, and the one rolled from v1 to v2, is kata-clh-cpu (docs/handson/10_cpu_only.md:191, docs/handson/10_cpu_only.md:224). The node group sandbox-kata-cpu carries label gpusandbox/role=sandbox-kata (stack.py:241).
- Correction: only two images are built (sandbox and control, scripts/03_build_push_images.sh --no-trainer).
- The node `sim` stands for the one Job template that every tool run uses (simulate, probe, parity, bench); edges 7 and 8 are its probe and bench runs against the two pools that are not active. They are dashed but required, so no pool is left without an edge.
- Substitution: Kubernetes workloads (the Jobs, the pool Deployments) use the Containers category resource icon `container_1`, labelled with the workload name; the `eks` service icon is the control plane only.
- Substitution: gVisor, Kata, Cloud Hypervisor and QEMU have no stencil; they are named in the pool labels (pool name = runtime) and in the Role column. The c8i node group is a role group whose title carries its name and instance type.
- The system node group is drawn here as a role group (it hosts the reward driver) while it is a not-drawn row in scenarios A, B1 and B2; that is the scenario difference.
- The kata-deploy DaemonSet is a not-drawn row: it is a Helm release in kube-system, not an AWS resource, and has no relationship the reader must see.
- Group titles are written as the node group or instance group name plus the instance type, without the words node group, so that each fits two lines of a one-column card (checked with the builder's title wrapping); the guide names them in full.
- The Architecture review heading is written "Architecture review (skipped)" because the guidebook style bans em dashes.
- All drawn text is English because one image serves the Korean and the English pages.
