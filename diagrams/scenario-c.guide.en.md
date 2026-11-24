[한국어](scenario-c.guide.md) | **English**

# Scenario C — CPU sandboxes on one c8i node

A c8i node runs gVisor, Kata with Cloud Hypervisor, and Kata with QEMU. A simulator Job on the system nodes submits prepared answers and exercises routing and version switching without a model or GPU.

![Scenario C architecture](scenario-c.drawio.png)

## Reading the diagram

Solid arrows show synchronous calls. Dashed arrows mark asynchronous, conditional, or supporting relationships. Arrow labels identify what moves between components.

## Request flow

1. (1 to 3) The operator opens cdk/tunnel.sh (SSM port forwarding from 127.0.0.1:8443 through the access instance to the private API on 443); kubectl and helm from scripts/kata/cpu_nodes.sh onward run through it.
2. (4) scripts/ops/simulate.sh renders k8s/probe/job-probe.yaml.tpl as Job simulate in ns rl-trainer. The Job has no node selector or toleration, so only the untainted system nodes take it; it mounts ConfigMap sandbox-routing as a directory and a projected token (audience gpu-sandbox). It runs inside the cluster, not on the workstation; the script only follows its logs.
3. (5) Every 20 seconds (30 batches by default) the Job takes one routing snapshot, sends the golden submissions (4 CPU goldens, standing in for completions) to the active pool kata-clh-cpu v1 through its headless Service, and prints reward_batch events computed by the trainer's own KernelRewards code (require_triton off).
4. (6) In a second terminal scripts/ops/rollout.sh kata-clh-cpu v1 v2 deploys v2, verifies it, checks parity and patches the ConfigMap; the Job prints sandbox_version_switch at a batch boundary and served_versions never mixes v1 and v2.
5. (7, 8) ops/verify.sh (probe: isolation evidence, egress blocked, golden verdicts) and ops/bench.sh (bench: cold start and latency) run the same Job template against gvisor-cpu and kata-qemu-cpu as well, so all three runtimes are checked on one node under the same conditions. Speedups measured on nested virtualization are not used as reward evidence.
6. (9, 10) The operator pushes the sandbox and control images; the c8i and system nodes pull them with the node role.
7. (11, 12) The control plane logs to CloudWatch Logs and encrypts Secrets with the KMS key; VPC flow logs (REJECT) go to a second log group.
8. Sandbox egress has no edge on purpose: default-deny NetworkPolicy in ns sandbox, readiness that requires IMDS, the API server and the kubelet to be unreachable, and the node guard from the c8i node's user data.

## Services

| Service | Role |
|---|---|
| Operator workstation (`client`, resource) | Runs cdk/deploy.sh and the numbered scripts, kubectl and helm through the tunnel, builds and pushes the sandbox and control images |
| SSM Session Manager (`systems_manager_session_manager`, resource) | Port forwarding session (AWS-StartPortForwardingSessionToRemoteHost) from 127.0.0.1:8443 on the workstation to the API endpoint on 443 |
| Access instance t4g.nano (`t4g_instance`, resource) | SSM-only host in a private subnet: no inbound rules, HTTPS egress only, IMDSv2, AmazonSSMManagedInstanceCore |
| EKS 1.36 private API (`eks`) | Control plane, private endpoint only, access entries, add-ons vpc-cni with NetworkPolicy, kube-proxy, pod identity agent, CoreDNS |
| KMS secrets key (`key_management_service`) | Customer-managed key with rotation; EKS envelope-encrypts Kubernetes Secrets with it |
| simulate and probe Jobs (`container_1`, resource) | One-shot Jobs from one template in ns rl-trainer (control image, label gpusandbox/client=true): simulate (71) scores golden submissions batch by batch through the routing table with the trainer's reward code; probe (61), parity (80) and bench (90) use the same template |
| kata-clh-cpu pool v1 (`container_1`, resource) | Active pool sandbox-kata-clh-cpu-v1 in ns sandbox: one Kata microVM per pod on Cloud Hypervisor (RuntimeClass kata-clh), CPU only, default-deny NetworkPolicy |
| kata-clh-cpu pool v2 (`container_1`, resource) | Next version sandbox-kata-clh-cpu-v2 beside v1 (blue/green, recycles each pod VM every 200 evaluations); no traffic until parity passes and the routing switch |
| gvisor-cpu pool v1 (`container_1`, resource) | Pool sandbox-gvisor-cpu-v1: gVisor runsc on the systrap platform without nvproxy (RuntimeClass gvisor-cpu), installed by the node's user data |
| kata-qemu-cpu pool v1 (`container_1`, resource) | Pool sandbox-kata-qemu-cpu-v1: one Kata microVM per pod on QEMU (RuntimeClass kata-qemu), the comparison baseline |
| ECR repositories (`ecr`) | Private repositories gpu-sandbox/sandbox and control (scan on push, immutable tags); the trainer image is skipped with --no-trainer |
| CloudWatch Logs (`cloudwatch_2`) | Log group /aws/eks/CLUSTER_NAME/cluster for five control plane log types and the VPC flow log group (REJECT), one-month retention |
| VPC (`vpc`), not drawn | 2 AZs, public /24 subnets holding only the NAT, private /19 subnets for every node, REJECT flow logs |
| NAT gateway (`nat_gateway`, resource), not drawn | Still deployed (the single egress for image pulls, the gVisor download at boot and the kata-deploy chart), but C has no model download, so no drawn edge needs it |
| IAM roles (`role`, resource), not drawn | Cluster role (with KMS grants), node role (EKS worker, CNI, ECR pull only), access instance role, operator access entry |
| Kubernetes ConfigMap sandbox-routing, not drawn | Active runtime kata-clh-cpu (05_setup_namespaces_auth.sh with ACTIVE_RUNTIME=kata-clh-cpu) and version plus the pool addresses; written by 05_setup_namespaces_auth.sh and ops/rollout.sh, mounted into the Jobs as a directory |
| kata-deploy DaemonSet (Helm release in kube-system), not drawn | Installs Kata on the c8i node only and creates RuntimeClasses kata-clh and kata-qemu; scripts/kata/cpu_nodes.sh adds RuntimeClass gvisor-cpu |

## Design decisions

The simulator runs in the cluster. The workstation submits the Job and follows its logs. The sandbox and control images are sufficient for this path.

See the [architecture brief](scenario-c.brief.md) for the component evidence and arrow labels.

## Outside the diagram

- WITH_KATA_GPU=1: sandbox-kata-gpu node group (g4dn.metal, Kata QEMU with GPU passthrough), stack.py:243-255.
- Agent Sandbox extension (docs/handson/scenarios/c/index.md): scripts/extensions/agent_sandbox.sh, k8s/extensions/agent-sandbox/ (unit tested only).
- Demo site (hands-on page 09): private S3 + CloudFront, demo/infra/site.yaml; no path to the cluster.
- Production reference (docs/production/): gateway, jwks-sync CronJob, Karpenter NodePools (sandbox-kata-cpu NodePool with c8i, m8i, r8i), veRL RayCluster.
- EKS_PUBLIC_ACCESS_CIDR: optional public endpoint for one /32 (cdk/gpusandbox_cdk/config.py:78-83), off by default.
