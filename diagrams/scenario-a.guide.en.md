[한국어](scenario-a.guide.md) | **English**

# Scenario A — EC2 trainer and gVisor GPU sandboxes

The trainer and gVisor pools run on separate EC2 node groups in one private EKS cluster. The trainer requests a verdict from the active pool and uses it for GRPO. The operator connects to the API through SSM.

![Scenario A architecture](scenario-a.drawio.png)

## Reading the diagram

Solid arrows show synchronous calls. Dashed arrows mark asynchronous, conditional, or supporting relationships. Arrow labels identify what moves between components.

## Request flow

1. (1 to 3) The operator runs cdk/tunnel.sh: an SSM Session Manager port forwarding session from 127.0.0.1:8443 through the access instance (no inbound rules) to the private EKS endpoint on 443, verified against the real API server name. Every kubectl and helm step (04_install_gpu_stack.sh onward, including the routing switch of ops/rollout.sh) rides this tunnel. The scripts' AWS API calls (CloudFormation, ECR push) go to public AWS endpoints directly.
2. (4) scripts/07_run_grpo.sh applies the GRPO Job in ns rl-trainer; EKS schedules it on the tainted trainer node and mounts ConfigMap sandbox-routing as a directory, so a later patch reaches the running pod (kubelet sync, up to about a minute).
3. (5, 6) The trainer downloads the policy model from the Hugging Face Hub through the NAT gateway; ns rl-trainer has no egress policy.
4. (7) For every reward batch the trainer takes one routing snapshot (active runtime and version), resolves the headless Service sandbox-gvisor-v1 through CoreDNS to the IPs of ready pods, and POSTs each candidate kernel to /v1/evaluate on port 8000 with a projected ServiceAccount token (audience gpu-sandbox). The pod checks the token offline against the JWKS ConfigMap, runs the harness under gVisor on its own A10G and answers with a verdict (status, speedup) on the same call, or 503 busy so the client retries another pod. The trainer turns verdicts into rewards.
5. (8) scripts/ops/rollout.sh deploys v2 beside v1, verifies it with a probe Job, checks parity against v1 and then patches the routing ConfigMap; the trainer switches at its next batch boundary, so no batch mixes versions. v1 is scaled to zero with --finish and kept for rollback.
6. (9, 10) The operator builds the sandbox, trainer and control images (linux/amd64) and pushes them to ECR; nodes pull them with the node role (AmazonEC2ContainerRegistryPullOnly), through the NAT gateway since the stack has no VPC endpoints.
7. (11, 12) The control plane writes api, audit, authenticator, controllerManager and scheduler logs to CloudWatch Logs and envelope-encrypts Secrets with the KMS key. VPC flow logs (REJECT) go to a second CloudWatch log group (the VPC itself is a not-drawn row).
8. Sandbox egress has no edge on purpose: the default-deny NetworkPolicy blocks DNS, IMDS, the internet and the Kubernetes API out of ns sandbox; a pod is Ready only when IMDS, the API server and the node kubelet are unreachable (k8s/sandbox/deployment.yaml.tpl:89-92), and the node guard drops new pod-to-node connections (infra/eks/userdata.py:69-75). The image pull of edge 9 is made by the node's container runtime, not by the pod.

## Services

| Service | Role |
|---|---|
| Operator workstation (`client`, resource) | Runs cdk/deploy.sh and the numbered scripts, kubectl and helm through the tunnel, builds and pushes the images |
| SSM Session Manager (`systems_manager_session_manager`, resource) | Port forwarding session (AWS-StartPortForwardingSessionToRemoteHost) from 127.0.0.1:8443 on the workstation to the API endpoint on 443 |
| Access instance t4g.nano (`t4g_instance`, resource) | SSM-only host in a private subnet: no inbound rules, HTTPS egress only, IMDSv2, AmazonSSMManagedInstanceCore |
| EKS 1.36 private API (`eks`) | Control plane, private endpoint only, access entries (API_AND_CONFIG_MAP), add-ons vpc-cni with NetworkPolicy, kube-proxy, pod identity agent, CoreDNS |
| KMS secrets key (`key_management_service`) | Customer-managed key with rotation; EKS envelope-encrypts Kubernetes Secrets with it |
| GRPO trainer Job (`container_1`, resource) | TRL GRPOTrainer with vLLM colocate and LoRA, policy Qwen/Qwen2.5-Coder-1.5B-Instruct; Job in ns rl-trainer with label gpusandbox/client=true, runc, 1x A10G, tainted node gpusandbox/role=trainer |
| gvisor pool v1 (`container_1`, resource) | Active pool: Deployment and headless Service sandbox-gvisor-v1 in ns sandbox, RuntimeClass gvisor (runsc + nvproxy), one pod per A10G, 2 replicas, default-deny NetworkPolicy |
| gvisor pool v2 (`container_1`, resource) | Next version sandbox-gvisor-v2 beside v1 (blue/green: 5 seeds, speedup cap 10x); no traffic until parity passes and the routing switch; the node group is scaled to 4 for it |
| ECR repositories (`ecr`) | Private repositories gpu-sandbox/sandbox, trainer and control (scan on push, immutable tags), created by scripts/03_build_push_images.sh from the workstation, outside the CDK stack |
| CloudWatch Logs (`cloudwatch_2`) | Log group /aws/eks/CLUSTER_NAME/cluster for five control plane log types and the VPC flow log group (REJECT), one-month retention |
| NAT gateway (`nat_gateway`, resource) | The single egress of the private subnets (one gateway, one AZ) |
| Hugging Face Hub (`internet`, resource) | External source of the policy model weights |
| VPC (`vpc`), not drawn | 2 AZs, public /24 subnets holding only the NAT (no public IPs), private /19 subnets for every node, REJECT flow logs |
| System node group m6i.large x2 (`ec2_m6i_instance`, resource), not drawn | Untainted nodes for CoreDNS, the add-ons and the operator tool Jobs (probe, parity, bench) that ops/verify.sh, ops/rollout.sh and ops/bench.sh run |
| IAM roles (`role`, resource), not drawn | Cluster role (with KMS grants), node role (EKS worker, CNI, ECR pull only), access instance role, operator access entry |
| Kubernetes ConfigMap sandbox-routing, not drawn | Active runtime and version plus the pool addresses; written by 05_setup_namespaces_auth.sh and ops/rollout.sh, mounted into the trainer as a directory |

## Design decisions

The trainer calls ready pool pods directly. The gateway, Karpenter pools, and veRL belong to the production reference. Trainer artifacts and the model cache in `emptyDir` are removed with the pod.

See the [architecture brief](scenario-a.brief.md) for the component evidence and arrow labels.

## Outside the diagram

- WITH_KATA_GPU=1: sandbox-kata-gpu node group (g4dn.metal on the IOMMU AMI, Kata QEMU with GPU passthrough), stack.py:243-255 and scripts/kata/gpu_nodes.sh.
- WITH_KATA_CPU=1 on A: adds the c8i sandbox-kata-cpu node group drawn in scenario-c (stack.py:233-242).
- Demo site (hands-on page 09): private S3 + CloudFront replaying recorded verdicts, demo/infra/site.yaml; it has no path to the cluster.
- Agent Sandbox extension: scripts/extensions/agent_sandbox.sh and k8s/extensions/agent-sandbox/ (unit tested only).
- Production reference (docs/production/): sandbox gateway (k8s/production/gateway.yaml.tpl), jwks-sync CronJob, Karpenter NodePools (infra/karpenter/nodepools.yaml), veRL RayCluster. None of them is deployed by any hands-on scenario.
- EKS_PUBLIC_ACCESS_CIDR: optional public endpoint for one /32 (cdk/gpusandbox_cdk/config.py:78-83), off by default.
