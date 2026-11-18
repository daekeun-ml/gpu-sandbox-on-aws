# All references

**TL;DR** The collapsed "References" box at the end of each page keeps only the key links; the full list for every page is collected here.

Pages appear in the same order as the left menu, and the first line of each section links back to the page that uses the links. Which source supports which fact is in [Verified facts and sources](sources.md).

## 01 Why AI-generated code needs isolation { #ref-beginner-01-why-sandbox }

Page: [01 Why AI-generated code needs isolation](../beginner/01_why_sandbox.md)

| Kind | Topic | URL |
|---|---|---|
| AWS blog | AI agent sandbox, EKS isolation part 1 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ |
| AWS blog | Same series, part 2 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
| AWS blog | Same series, part 3 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/ |
| AWS docs | Turning on network policy in EKS | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| AWS docs | EC2 instance metadata (IMDSv2) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html |
| GitHub | Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |
| GitHub | This repository | https://github.com/daekeun-ml/gpu-sandbox-on-aws |

## 02 Containers and sandboxes { #ref-beginner-02-container-vs-sandbox }

Page: [02 Containers and sandboxes](../beginner/02_container_vs_sandbox.md)

| Kind | Topic | URL |
|---|---|---|
| AWS blog | AI agent sandbox, EKS isolation part 1 (experiment comparing runc and gVisor) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ |
| AWS blog | Same series, part 2 (system call cost measurements) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
| AWS blog | Same series, part 3 (production case) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/ |
| Official docs | Kubernetes RuntimeClass | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
| Official docs | gVisor architecture | https://gvisor.dev/docs/architecture_guide/intro/ |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |

## 03 Isolating the GPU too { #ref-beginner-03-gpu-sandbox }

Page: [03 Isolating the GPU too](../beginner/03_gpu_sandbox.md)

| Kind | Topic | URL |
|---|---|---|
| Official docs | gVisor GPU support (nvproxy) | https://gvisor.dev/docs/user_guide/gpu/ |
| GitHub | Kata Containers GPU passthrough | https://github.com/kata-containers/kata-containers/tree/main/docs/use-cases |
| AWS docs | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS docs | Accelerated computing instances | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | This repository | https://github.com/daekeun-ml/gpu-sandbox-on-aws |

## 04 Reinforcement learning and sandboxes { #ref-beginner-04-rl-and-sandbox }

Page: [04 Reinforcement learning and sandboxes](../beginner/04_rl_and_sandbox.md)

| Kind | Topic | URL |
|---|---|---|
| Paper | KernelBench | https://arxiv.org/abs/2502.10517 |
| Official docs | TRL GRPO Trainer | https://huggingface.co/docs/trl/main/en/grpo_trainer |
| GitHub | KernelBench | https://github.com/ScalingIntelligence/KernelBench |
| GitHub | This repository's grading program (harness) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/src/gpusandbox/harness |

## 05 Try it yourself { #ref-beginner-05-hands-on }

Page: [05 Try it yourself](../beginner/05_hands_on.md)

| Kind | Topic | URL |
|---|---|---|
| AWS docs | AWS CDK v2 Developer Guide | https://docs.aws.amazon.com/cdk/v2/guide/home.html |
| AWS docs | Starting a Session Manager session (port forwarding) | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html |
| AWS docs | EKS cluster endpoint access | https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html |
| AWS docs | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| GitHub | This repository | https://github.com/daekeun-ml/gpu-sandbox-on-aws |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | gVisor | https://github.com/google/gvisor |

## 06 Multi-turn agents and Agent Sandbox { #ref-beginner-06-multi-turn-agent }

Page: [06 Multi-turn agents and Agent Sandbox](../beginner/06_multi_turn_agent.md)

| Kind | Topic | URL |
|---|---|---|
| GitHub | Agent Sandbox (kubernetes-sigs/agent-sandbox) | https://github.com/kubernetes-sigs/agent-sandbox |
| AI on EKS | Agent Sandbox on EKS | https://awslabs.github.io/ai-on-eks/docs/infra/agents/agent-sandbox |
| GitHub | AI on EKS | https://github.com/awslabs/ai-on-eks |
| AWS docs | EKS sandboxing limitations | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| AWS docs | Amazon EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| GitHub | This repository's Agent Sandbox extension | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/extensions/agent-sandbox |

## Getting started { #ref-getting-started }

Page: [Getting started](../getting_started.md)

| Topic | Link |
|---|---|
| Install AWS CLI v2 | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |
| EC2 instance type quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| EKS Kubernetes versions | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| HyperPod (EKS) prerequisites | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS CDK v2 Developer Guide, bootstrapping | https://docs.aws.amazon.com/cdk/v2/guide/home.html , https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html |
| Install the Session Manager plugin | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html |
| eksctl cluster access (no private-only creation) | https://docs.aws.amazon.com/eks/latest/eksctl/vpc-cluster-access.html |
| Kubernetes version skew policy | https://kubernetes.io/releases/version-skew-policy/ |
| TRL docs, GitHub | https://huggingface.co/docs/trl , https://github.com/huggingface/trl |
| uv | https://github.com/astral-sh/uv |
| Test workflow | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/.github/workflows/tests.yml |
| Sandbox server, auth, reaper | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/auth.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/procs.py |
| GRPO trainer, example settings | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/trl/train_grpo.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/config.env.example |

## When the sandbox needs a GPU { #ref-concepts-01-why-gpu-sandbox }

Page: [When the sandbox needs a GPU](../concepts/01_why_gpu_sandbox.md)

| Topic | Link |
|---|---|
| AWS Nitro Sandboxes | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html |
| EKS sandboxing limitations | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| EC2 accelerated computing instance specifications | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| GKE Sandbox (GPU time-sharing advice) | https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods |
| Firecracker FAQ, CHANGELOG | https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md , https://github.com/firecracker-microvm/firecracker/blob/main/CHANGELOG.md |
| KernelBench GitHub, v0.1 blog | https://github.com/ScalingIntelligence/KernelBench , https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/ |
| CUDA-L1 | https://arxiv.org/abs/2507.14111 |
| Sakana AI CUDA Engineer | https://sakana.ai/ai-cuda-engineer/ |
| Kevin-32B | https://cognition.com/blog/kevin-32b |
| Triton | https://github.com/triton-lang/triton |
| agent-sandbox, SandboxFusion | https://github.com/kubernetes-sigs/agent-sandbox , https://github.com/bytedance/SandboxFusion |
| Tasks, prompts, reward code | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tasks/__init__.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/prompts.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py |
| Harness timing, policy | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/timing.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/policy.py |

## Isolation runtimes { #ref-concepts-02-isolation-runtimes }

Page: [Isolation runtimes](../concepts/02_isolation_runtimes.md)

| Topic | Link |
|---|---|
| EC2 nested virtualization (User Guide, What's New) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html , https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
| EC2 accelerated computing instance specifications | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS Nitro Sandboxes, EKS sandboxing limitations | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| AWS Containers blog (Kata + Firecracker, i3.metal) | https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/ |
| AWS China blog (Kata + CLH, c5.metal) | https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/ |
| gVisor installation, GPU support, GitHub | https://gvisor.dev/docs/user_guide/install/ , https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
| GKE Sandbox | https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods |
| Kata NVIDIA GPU passthrough (4.3.1), CLH GPU issue | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers/issues/11687 |
| NVIDIA GPU Operator (Kata), GitHub | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html , https://github.com/NVIDIA/gpu-operator |
| NVIDIA k8s-device-plugin | https://github.com/NVIDIA/k8s-device-plugin |
| EKS AL2023 AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| Cloud Hypervisor, Firecracker | https://github.com/cloud-hypervisor/cloud-hypervisor , https://github.com/firecracker-microvm/firecracker |
| Karpenter | https://karpenter.sh/docs/ , https://github.com/aws/karpenter-provider-aws |
| Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |
| This asset's runtime settings | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/gvisor/install-gvisor.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/kata-deploy-values.yaml , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/gpu-operator-values.yaml |

## On-policy RL with sandboxes { #ref-concepts-03-onpolicy-rl-with-sandboxes }

Page: [On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

| Topic | Link |
|---|---|
| TRL GRPO trainer docs, GitHub | https://huggingface.co/docs/trl/main/en/grpo_trainer , https://github.com/huggingface/trl |
| veRL | https://github.com/verl-project/verl |
| KubeRay | https://github.com/ray-project/kuberay |
| Ray on SageMaker HyperPod | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html |
| HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
| veRL on HyperPod example | https://github.com/awslabs/awsome-distributed-ai |
| INTELLECT-3 | https://arxiv.org/abs/2512.16144 |
| Kubernetes ConfigMap (mounted updates, subPath) | https://kubernetes.io/docs/concepts/configuration/configmap/ |
| Client, routing, pool | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/__init__.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/routing.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/pool.py |
| Rewards, gateway, veRL reward | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/reward_fn.py |
| Blue/green script, version file | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/rollout.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/versions/v2.env |

## Platforms and instances { #ref-concepts-04-platforms-and-instances }

Page: [Platforms and instances](../concepts/04_platforms_and_instances.md)

| Topic | Link |
|---|---|
| HyperPod (EKS) prerequisites, IAM | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html |
| HyperPod resiliency, deep health checks | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html |
| HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
| ClusterInstanceGroupSpecification (API) | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ClusterInstanceGroupSpecification.html |
| Ray on SageMaker HyperPod | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html |
| EKS Kubernetes versions | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| EC2 accelerated computing instance specifications, quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html , https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| Pricing (EC2, SageMaker AI) | https://aws.amazon.com/ec2/pricing/on-demand/ , https://aws.amazon.com/sagemaker/ai/pricing/ |
| HyperPod CLI and dependency chart | https://github.com/aws/sagemaker-hyperpod-cli |
| EKS AL2023 AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| gVisor GPU support, GitHub | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
| awsome-distributed-ai (veRL on HyperPod) | https://github.com/awslabs/awsome-distributed-ai |
| This asset's HyperPod template and check script | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/cluster.json.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh |

## Decision guide { #ref-concepts-05-decision-guide }

Page: [Decision guide](../concepts/05_decision_guide.md)

| Topic | Link |
|---|---|
| AWS Nitro Sandboxes, EKS sandboxing limitations | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| Amazon Bedrock AgentCore Code Interpreter | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html |
| EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| EC2 accelerated computing instance specifications | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| gVisor GPU support, GitHub | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
| Kata NVIDIA GPU passthrough (4.3.1), GitHub | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers |
| NVIDIA GPU Operator (Kata) | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html |
| Cloud Hypervisor | https://github.com/cloud-hypervisor/cloud-hypervisor |
| Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |
| Modal Sandboxes (third party) | https://modal.com/docs/guide/sandbox |
| This asset's runtime profiles | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/gvisor.env , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-qemu.env , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-clh-cpu.env |

## 06 Extending with Agent Sandbox { #ref-concepts-06-agent-sandbox }

Page: [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

Official documentation and repositories:

| Topic | Link |
|---|---|
| Agent Sandbox repository, releases (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox , https://github.com/kubernetes-sigs/agent-sandbox/releases |
| SandboxClaim, SandboxTemplate, SandboxWarmPool and Sandbox types (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxclaim_types.go , https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxtemplate_types.go , https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxwarmpool_types.go , https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/api/v1beta1/sandbox_types.go |
| The controller's DNS injection condition (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/controllers/utils.go |
| Upstream examples (`kata-aks`, `kata-gke-sandbox`, `gpu-l4-snapshot-sandbox`) | https://github.com/kubernetes-sigs/agent-sandbox/tree/main/examples |
| AWS Tech Blog part 1: concepts and setup (gVisor on EKS, four isolation layers) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ |
| AWS Tech Blog part 2: the default policy, DNS and router checks and the warm pool measurements cited on this page | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
| AWS Tech Blog part 3: Ably's Agent Sandbox operation on Amazon EKS | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/ |
| AI on EKS: Agent Sandbox on EKS (gVisor, agent-sandbox CRDs, FQDN egress, runtime tiers) | https://awslabs.github.io/ai-on-eks/docs/infra/agents/agent-sandbox , https://github.com/awslabs/ai-on-eks |
| Amazon EKS NetworkPolicy (VPC CNI), policy agent | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html , https://github.com/aws/aws-network-policy-agent |
| EKS Best Practices: restricting access to the node instance profile (IMDSv2, hop limit 1) | https://docs.aws.amazon.com/eks/latest/best-practices/identity-and-access-management.html |
| Kubernetes NetworkPolicy (allow rules add up) | https://kubernetes.io/docs/concepts/services-networking/network-policies/ |
| Karpenter | https://karpenter.sh/docs/ , https://github.com/aws/karpenter-provider-aws |
| veRL `BaseTool` (v0.9.1) | https://github.com/verl-project/verl/blob/v0.9.1/verl/tools/base_tool.py |
| veRL `ToolAgentLoop` (v0.9.1, create, execute and release for every tool call) | https://github.com/verl-project/verl/blob/v0.9.1/verl/experimental/agent_loop/tool_agent_loop.py |
| gVisor, Kata Containers | https://github.com/google/gvisor , https://github.com/kata-containers/kata-containers |
| Amazon EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |

Repository files described on this page:

- [k8s/extensions/agent-sandbox/template.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/template.yaml.tpl), [trainer-claims-rbac.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/trainer-claims-rbac.yaml), [job-multiturn.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/job-multiturn.yaml.tpl)
- [k8s/base/trainer-rbac.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/trainer-rbac.yaml)
- [scripts/extensions/agent_sandbox.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/extensions/agent_sandbox.sh)
- [src/gpusandbox/agent_sandbox.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/agent_sandbox.py), [src/gpusandbox/multiturn.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/multiturn.py)
- [rl/verl/sandbox_tool.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/sandbox_tool.py), [rl/verl/sandbox_tool_config.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/sandbox_tool_config.yaml)
- [tests/test_agent_sandbox.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_agent_sandbox.py), [tests/test_multiturn.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_multiturn.py), [tests/test_manifests.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_manifests.py)
- [k8s/base/networkpolicies.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/networkpolicies.yaml), [infra/karpenter/nodepools.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/karpenter/nodepools.yaml)

## 00 Hands-on overview { #ref-handson-00-overview }

Page: [00 Hands-on overview](../handson/00_overview.md)

| Kind | Topic | URL |
|---|---|---|
| AWS docs | EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS docs | SageMaker AI pricing (HyperPod) | https://aws.amazon.com/sagemaker/ai/pricing/ |
| AWS docs | Amazon EKS pricing | https://aws.amazon.com/eks/pricing/ |
| AWS docs | Amazon VPC pricing (NAT gateway) | https://aws.amazon.com/vpc/pricing/ |
| AWS docs | EC2 instance type quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| AWS docs | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS docs | Accelerated computing instance types | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS docs | EKS Kubernetes versions | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| AWS docs | EKS cluster API server endpoint (private) | https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html |
| AWS docs | AWS CDK v2 Developer Guide | https://docs.aws.amazon.com/cdk/v2/guide/home.html |
| AWS docs | Install the Session Manager plugin | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html |
| AWS docs | HyperPod EKS prerequisites | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| AWS docs | CloudFront Origin Access Control (09 demo site) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html |
| GitHub | This repository | https://github.com/daekeun-ml/gpu-sandbox-on-aws |
| GitHub | CDK app of this repository | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/cdk |
| GitHub | AWS CDK | https://github.com/aws/aws-cdk |
| GitHub | Amazon EKS AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | NVIDIA GPU Operator | https://github.com/NVIDIA/gpu-operator |
| GitHub | NVIDIA k8s-device-plugin | https://github.com/NVIDIA/k8s-device-plugin |

## 01 Cluster and images { #ref-handson-01-cluster-and-images }

Page: [01 Cluster and images](../handson/01_cluster_and_images.md)

| Kind | Topic | URL |
|---|---|---|
| AWS docs | EKS cluster API server endpoint (public, private, CIDR) | https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html |
| AWS docs | EKS managed node group launch templates (user data merge, hop limit) | https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html |
| AWS docs | EKS access entries | https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html |
| AWS docs | EC2 instance metadata options (hop limit) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html |
| AWS docs | VPC CNI network policy configuration | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| AWS docs | ECR image tag mutability | https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html |
| AWS docs | EKS Kubernetes versions | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| AWS docs | HyperPod EKS prerequisites | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| AWS docs | Getting started with the AWS CDK (CLI install) | https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html |
| AWS docs | AWS CDK prerequisites (Node.js) | https://docs.aws.amazon.com/cdk/v2/guide/prerequisites.html |
| AWS docs | CDK bootstrapping | https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html |
| AWS docs | Install the Session Manager plugin | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html |
| AWS docs | Security Hub EKS controls (EKS.1) | https://docs.aws.amazon.com/securityhub/latest/userguide/eks-controls.html |
| AWS docs | AWS CLI `update-nodegroup-config` | https://docs.aws.amazon.com/cli/latest/reference/eks/update-nodegroup-config.html |
| AWS docs | eksctl cluster access (no private-only creation; why this moved to CDK) | https://docs.aws.amazon.com/eks/latest/eksctl/vpc-cluster-access.html |
| Official docs | gVisor installation | https://gvisor.dev/docs/user_guide/install/ |
| GitHub | AWS CDK | https://github.com/aws/aws-cdk |
| GitHub | cdk-nag | https://github.com/cdklabs/cdk-nag |
| GitHub | Amazon EKS AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| GitHub | Amazon VPC CNI | https://github.com/aws/amazon-vpc-cni-k8s |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | TRL | https://github.com/huggingface/trl |
| GitHub | vLLM | https://github.com/vllm-project/vllm |
| GitHub | CDK stack (stack.py) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py |
| GitHub | Tunnel script (tunnel.sh) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/tunnel.sh |
| GitHub | User data module (userdata.py) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/eks/userdata.py |
| GitHub | install-gvisor.sh | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/gvisor/install-gvisor.sh |
| GitHub | node-guard.sh | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/eks/node-guard.sh |

## 02 gVisor GPU sandboxes { #ref-handson-02-gvisor }

Page: [02 gVisor GPU sandboxes](../handson/02_gvisor.md)

| Kind | Topic | URL |
|---|---|---|
| AWS docs | Accelerated computing instance types (g5, g6, g4dn) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS docs | EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS docs | EKS sandboxing limitations (isolated pods) | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| Official docs | gVisor GPU support (nvproxy, driver policy, CDI) | https://gvisor.dev/docs/user_guide/gpu/ |
| Official docs | gVisor installation | https://gvisor.dev/docs/user_guide/install/ |
| Official docs | GKE Sandbox pods | https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods |
| Official docs | Kubernetes RuntimeClass | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | Kernel version reported by gVisor (version.go) | https://github.com/google/gvisor/blob/master/pkg/sentry/kernel/version/version.go |
| GitHub | NVIDIA k8s-device-plugin | https://github.com/NVIDIA/k8s-device-plugin |
| GitHub | NVIDIA Container Toolkit | https://github.com/NVIDIA/nvidia-container-toolkit |
| GitHub | Amazon EKS AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| GitHub | Device plugin values | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/gpu/nvidia-device-plugin-values.yaml |
| GitHub | gVisor RuntimeClass | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/runtimes/runtimeclass-gvisor.yaml |
| GitHub | GPU stack and gVisor install script (04_install_gpu_stack.sh) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/04_install_gpu_stack.sh |

## 03 Kata sandboxes (CLH, QEMU) { #ref-handson-03-kata }

Page: [03 Kata sandboxes (CLH, QEMU)](../handson/03_kata.md)

| Kind | Topic | URL |
|---|---|---|
| AWS docs | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS docs | What's New: EC2 nested virtualization (2026-02) | https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
| AWS docs | Accelerated computing instance types (g4dn.metal) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS docs | EKS managed node group launch templates | https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html |
| AWS docs | EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS blog | Workload isolation on EKS with Kata Containers (2024) | https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/ |
| Official docs | NVIDIA GPU Operator with Kata Containers | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html |
| Official docs | Kubernetes RuntimeClass (scheduling, overhead) | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | Kata 4.3.1 NVIDIA GPU passthrough (QEMU) | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md |
| GitHub | Kata 4.3.1 hypervisors.md | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md |
| GitHub | Kata issue 11687 (CLH GPU) | https://github.com/kata-containers/kata-containers/issues/11687 |
| GitHub | NVIDIA GPU Operator | https://github.com/NVIDIA/gpu-operator |
| GitHub | Cloud Hypervisor | https://github.com/cloud-hypervisor/cloud-hypervisor |
| GitHub | kata-deploy values | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/kata-deploy-values.yaml |
| GitHub | GPU Operator values | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/gpu-operator-values.yaml |
| GitHub | IOMMU AMI build script | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/build-iommu-ami.sh |
| GitHub | CDK stack (Kata node groups and launch templates) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py |
| GitHub | User data module (userdata.py) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/eks/userdata.py |
| GitHub | Experimental CLH GPU values | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/experimental-clh-gpu/values-clh-gpu.yaml |

## 04 Deploy and verify sandbox pools { #ref-handson-04-sandbox-pools }

Page: [04 Deploy and verify sandbox pools](../handson/04_sandbox_pools.md)

| Kind | Topic | URL |
|---|---|---|
| AWS docs | VPC CNI network policy configuration (standard and strict modes) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| AWS docs | OIDC issuer of an EKS cluster | https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html |
| AWS docs | EC2 instance metadata options | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html |
| Official docs | Kubernetes ServiceAccount token projection, issuer discovery | https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/ |
| Official docs | Kubernetes Pod Security Standards | https://kubernetes.io/docs/concepts/security/pod-security-standards/ |
| Official docs | Kubernetes Service (headless Service) | https://kubernetes.io/docs/concepts/services-networking/service/ |
| GitHub | AWS network policy agent (node IP allowance) | https://github.com/aws/aws-network-policy-agent |
| GitHub | Amazon VPC CNI | https://github.com/aws/amazon-vpc-cni-k8s |
| GitHub | Sandbox Deployment template | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/deployment.yaml.tpl |
| GitHub | NetworkPolicies | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/networkpolicies.yaml |
| GitHub | Authentication module (auth.py) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/auth.py |
| GitHub | Sandbox server (readiness, egress check) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py |
| GitHub | Golden submissions | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/golden.py |
| GitHub | Pool verification script (ops/verify.sh) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/verify.sh |

## 05 On-policy GRPO training { #ref-handson-05-grpo-training }

Page: [05 On-policy GRPO training](../handson/05_grpo_training.md)

Official documentation and repositories:

| Topic | Link |
|---|---|
| TRL GRPO Trainer (metrics, colocate, sleep mode, None rewards) | https://huggingface.co/docs/trl/grpo_trainer |
| TRL repository | https://github.com/huggingface/trl |
| vLLM repository | https://github.com/vllm-project/vllm |
| Base model (Apache-2.0) | https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct |
| KernelBench (ModelNew contract) | https://github.com/ScalingIntelligence/KernelBench |
| Amazon EKS NetworkPolicy (VPC CNI) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| Amazon EC2 accelerated computing instances (A10G, L4, T4) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| Amazon EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| Kubernetes ConfigMap (mounted updates, subPath) | https://kubernetes.io/docs/concepts/configuration/configmap/ |

Repository files this page describes:

- [scripts/07_run_grpo.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/07_run_grpo.sh)
- [k8s/trainer/job-grpo.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/job-grpo.yaml.tpl)
- [rl/trl/train_grpo.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/trl/train_grpo.py)
- [src/gpusandbox/rewards.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py)
- [src/gpusandbox/prompts.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/prompts.py)
- [src/gpusandbox/tasks/__init__.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tasks/__init__.py)

## 06 Updating the sandbox during training { #ref-handson-06-sandbox-update }

Page: [06 Updating the sandbox during training](../handson/06_sandbox_update.md)

Official documentation and repositories:

| Topic | Link |
|---|---|
| Kubernetes ConfigMap (mounted update delay, no updates with subPath) | https://kubernetes.io/docs/concepts/configuration/configmap/ |
| AWS CLI `update-nodegroup-config` (resizing a managed node group) | https://docs.aws.amazon.com/cli/latest/reference/eks/update-nodegroup-config.html |
| Amazon EKS NetworkPolicy (VPC CNI) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| Amazon EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| KernelBench (`excessive_speedup_threshold`) | https://github.com/ScalingIntelligence/KernelBench |
| KernelBench v0.1 blog (reward hacking cases) | https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/ |
| INTELLECT-3 (environments versioned independently of the trainer) | https://arxiv.org/abs/2512.16144 |
| TRL repository | https://github.com/huggingface/trl |

Repository files this page describes:

- [scripts/ops/rollout.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/rollout.sh)
- [k8s/sandbox/versions/v1.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/versions/v1.env), [v2.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/versions/v2.env)
- [k8s/sandbox/deployment.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/deployment.yaml.tpl), [k8s/base/routing.json.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/routing.json.tpl)
- [src/gpusandbox/client/routing.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/routing.py), [src/gpusandbox/rewards.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py)
- [src/gpusandbox/tools.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py), [src/gpusandbox/golden.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/golden.py)

In production, trainers that score answers one at a time, such as veRL, cannot use a batch snapshot, so the gateway pins the version per `group_key` ([Production 05 Sandbox versioning](../production/05_sandbox_updates.md)).

## 07 HyperPod scenario { #ref-handson-07-hyperpod }

Page: [07 HyperPod scenario](../handson/07_hyperpod.md)

Official documentation and repositories:

| Topic | Link |
|---|---|
| HyperPod EKS prerequisites | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| HyperPod IAM (execution role) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html |
| HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
| Installing the training operator (cert-manager, Pod Identity) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html |
| Using the training operator (runPolicy, logMonitoringConfiguration) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-usage.html |
| HyperPod EKS AMI releases (driver versions) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-release-ami-eks.html |
| CreateCluster API (NodeRecovery, Orchestrator) | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateCluster.html |
| ClusterInstanceGroupSpecification (instance types, OnStartDeepHealthChecks) | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ClusterInstanceGroupSpecification.html |
| S3 Block Public Access | https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html |
| EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| Amazon EKS Kubernetes versions (standard support) | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| SageMaker AI pricing (HyperPod) | https://aws.amazon.com/sagemaker/ai/pricing/ |
| gVisor GPU support (nvproxy, driver policy) | https://gvisor.dev/docs/user_guide/gpu/ |
| HyperPod CLI and dependency Helm chart | https://github.com/aws/sagemaker-hyperpod-cli |
| gVisor repository | https://github.com/google/gvisor |
| Kata Containers repository | https://github.com/kata-containers/kata-containers |
| AWS distributed training samples (HyperPod EKS) | https://github.com/awslabs/awsome-distributed-ai |

Repository files this page describes:

- [scripts/hyperpod/create.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/create.sh), [run_grpo.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/run_grpo.sh), [check_gvisor.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh), [delete.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/delete.sh)
- [infra/hyperpod/cluster.json.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/cluster.json.tpl), [execution-role-eks-policy.json](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/execution-role-eks-policy.json)
- [infra/hyperpod/lifecycle/on_create.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/lifecycle/on_create.sh), [install_gvisor_hyperpod.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/lifecycle/install_gvisor_hyperpod.sh)
- [k8s/trainer/hyperpod-job-grpo.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl)
- [scripts/config.env.example](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/config.env.example)

## 08 Runtime benchmark { #ref-handson-08-benchmark }

Page: [08 Runtime benchmark](../handson/08_benchmark.md)

Official documentation and repositories:

| Topic | Link |
|---|---|
| EC2 nested virtualization (bare metal recommended) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| Amazon EC2 accelerated computing instances (A10G, L4, T4) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| Amazon EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS China blog (Kata + CLH, OpenSandbox) | https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/ |
| AWS Containers blog (Kata + Firecracker, i3.metal) | https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/ |
| Kata NVIDIA GPU passthrough (QEMU) | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md |
| Kata CLH GPU support discussion | https://github.com/kata-containers/kata-containers/issues/11687 |
| Kata Containers repository | https://github.com/kata-containers/kata-containers |
| gVisor GPU support | https://gvisor.dev/docs/user_guide/gpu/ |
| gVisor repository | https://github.com/google/gvisor |
| KernelBench (timing method) | https://github.com/ScalingIntelligence/KernelBench |

Repository files this page describes:

- [scripts/ops/bench.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/bench.sh), [scripts/lib_jobs.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib_jobs.sh)
- [src/gpusandbox/tools.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py)
- [src/gpusandbox/server/app.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py)
- [k8s/sandbox/deployment.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/deployment.yaml.tpl)
- [k8s/sandbox/profiles/gvisor.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/gvisor.env), [kata-qemu.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-qemu.env), [kata-clh-cpu.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-clh-cpu.env), [kata-qemu-cpu.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-qemu-cpu.env)

## 09 Demo site (CloudFront) { #ref-handson-09-demo-site }

Page: [09 Demo site (CloudFront)](../handson/09_demo_site.md)

Official documentation and repositories:

| Topic | Link |
|---|---|
| CloudFront: restricting access to an S3 origin (OAC, bucket policy examples) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html |
| CloudFront distribution settings (security policy, TLSv1 with the default certificate, default root object, price class) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesGeneral.html |
| CloudFront response headers policies | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-response-headers-policies.html |
| CloudFront alternate domain names (DNS records, SAN) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/CNAMEs.html |
| CloudFront certificate requirements (us-east-1) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html |
| Protocols and ciphers between viewers and CloudFront | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html |
| S3 Block Public Access (including the definition of "public") | https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html |
| S3 Object Ownership | https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html |
| CloudFront and S3 pricing | https://aws.amazon.com/cloudfront/pricing/ , https://aws.amazon.com/s3/pricing/ |
| Amazon EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| cfn-lint | https://github.com/aws-cloudformation/cfn-lint |

Repository files described on this page:

- [demo/deploy.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/deploy.sh), [demo/teardown.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/teardown.sh), [demo/infra/site.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/infra/site.yaml)
- [demo/site/index.html](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/site/index.html), [demo/site/app.js](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/site/app.js), [demo/record_local.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/record_local.py)
- [src/gpusandbox/tools.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py) (`record`), [tests/test_demo.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_demo.py)
- [k8s/trainer/job-grpo.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/job-grpo.yaml.tpl), [k8s/probe/job-probe.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/probe/job-probe.yaml.tpl)

## 10 CPU-only path on c8i (scenario C) { #ref-handson-10-cpu-only }

Page: [10 CPU-only path on c8i (scenario C)](../handson/10_cpu_only.md)

| Kind | Topic | URL |
|---|---|---|
| AWS docs | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS docs | What's New: EC2 nested virtualization (2026-02) | https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
| AWS docs | EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS docs | Amazon EKS pricing | https://aws.amazon.com/eks/pricing/ |
| AWS docs | Amazon VPC pricing (NAT gateway) | https://aws.amazon.com/vpc/pricing/ |
| AWS docs | EC2 instance type quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| AWS docs | EKS managed node group launch templates | https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html |
| GitHub | This repository | https://github.com/daekeun-ml/gpu-sandbox-on-aws |
| GitHub | Reward loop simulator (`simulate`) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py |
| GitHub | CDK stack (c8i node group and launch template) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py |
| GitHub | Tunnel script (tunnel.sh) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/tunnel.sh |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |

## 11 Multi-turn episodes { #ref-handson-11-multi-turn }

Page: [11 Multi-turn episodes](../handson/11_multi_turn.md)

| Kind | Topic | URL |
|---|---|---|
| GitHub | Agent Sandbox repository and releases (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox , https://github.com/kubernetes-sigs/agent-sandbox/releases |
| GitHub | SandboxClaim and SandboxWarmPool types (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxclaim_types.go , https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxwarmpool_types.go |
| GitHub | veRL v0.9.1 source tree | https://github.com/verl-project/verl/tree/v0.9.1 |
| GitHub | veRL `ToolAgentLoop`, `BaseTool`, tool registry (v0.9.1) | https://github.com/verl-project/verl/blob/v0.9.1/verl/experimental/agent_loop/tool_agent_loop.py , https://github.com/verl-project/verl/blob/v0.9.1/verl/tools/base_tool.py , https://github.com/verl-project/verl/blob/v0.9.1/verl/tools/tool_registry.py |
| Kubernetes docs | Automatic cleanup of finished Jobs (`ttlSecondsAfterFinished`) | https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/ |
| AWS docs | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS docs | EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| GitHub | This repository | https://github.com/daekeun-ml/gpu-sandbox-on-aws |

Repository files this page describes:

- [scripts/extensions/agent_sandbox.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/extensions/agent_sandbox.sh), [scripts/lib_jobs.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib_jobs.sh)
- [k8s/extensions/agent-sandbox/job-multiturn.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/job-multiturn.yaml.tpl), [template.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/template.yaml.tpl), [trainer-claims-rbac.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/trainer-claims-rbac.yaml), [k8s/base/trainer-rbac.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/trainer-rbac.yaml)
- [src/gpusandbox/multiturn.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/multiturn.py), [src/gpusandbox/agent_sandbox.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/agent_sandbox.py), [src/gpusandbox/tools.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py), [src/gpusandbox/rewards.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py)
- [rl/verl/sandbox_tool.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/sandbox_tool.py), [rl/verl/sandbox_tool_config.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/sandbox_tool_config.yaml)
- [tests/test_multiturn.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_multiturn.py)

## 99 Cleanup { #ref-handson-99-cleanup }

Page: [99 Cleanup](../handson/99_cleanup.md)

Official documentation and repositories:

| Topic | Link |
|---|---|
| Deleting an Amazon EKS cluster | https://docs.aws.amazon.com/eks/latest/userguide/delete-cluster.html |
| AWS CLI `update-nodegroup-config` (resizing a managed node group) | https://docs.aws.amazon.com/cli/latest/reference/eks/update-nodegroup-config.html |
| AWS CDK `cdk destroy` | https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-destroy.html |
| Deleting an AWS KMS key (waiting period) | https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html |
| Deregistering EC2 AMIs and snapshots | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/deregister-ami.html |
| Deleting ECR repositories | https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-delete.html |
| Deleting S3 buckets | https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html |
| Deleting a CloudFormation stack (`DELETE_FAILED`, retry) | https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-delete-stack.html |
| Deleting a CloudFront distribution | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/HowToDeleteDistribution.html |
| HyperPod DeleteCluster API | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DeleteCluster.html |
| ClusterInstanceGroupSpecification (`InstanceCount` range) | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ClusterInstanceGroupSpecification.html |
| Amazon EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| SageMaker AI pricing (HyperPod) | https://aws.amazon.com/sagemaker/ai/pricing/ |
| AWS CDK repository | https://github.com/aws/aws-cdk |
| HyperPod CLI and dependency Helm chart | https://github.com/aws/sagemaker-hyperpod-cli |
| Agent Sandbox repository (SandboxClaim, SandboxWarmPool, SandboxTemplate) | https://github.com/kubernetes-sigs/agent-sandbox |

Repository files this page describes:

- [scripts/08_cleanup.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/08_cleanup.sh)
- [scripts/hyperpod/delete.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/delete.sh)
- [demo/teardown.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/teardown.sh), [demo/infra/site.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/infra/site.yaml)
- [scripts/extensions/agent_sandbox.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/extensions/agent_sandbox.sh)
- [infra/kata/build-iommu-ami.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/build-iommu-ami.sh)
- [cdk/destroy.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/destroy.sh)
- Node group sizes (min, max, desired): [cdk/gpusandbox_cdk/stack.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py)

## Production reference architecture { #ref-production-00-architecture }

Page: [Production reference architecture](../production/00_architecture.md)

| Topic | Source |
|---|---|
| EKS version support | [Amazon EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) |
| VPC CNI NetworkPolicy | [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
| EC2 nested virtualization | [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) |
| GPU bare metal instances | [Accelerated computing instance types](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html) |
| HyperPod EKS prerequisites | [SageMaker HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html) |
| Warm capacity pattern | [AWS China blog: EKS + Kata + Cloud Hypervisor](https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/) |
| Karpenter | [Karpenter documentation](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws) |
| Runtimes | [google/gvisor](https://github.com/google/gvisor), [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers) |
| NetworkPolicy agent | [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent) |
| Per-episode sandboxes | [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) |
| Operating at scale | [INTELLECT-3 (arXiv 2512.16144)](https://arxiv.org/abs/2512.16144) |

## Capacity and nodes { #ref-production-01-capacity-and-nodes }

Page: [Capacity and nodes](../production/01_capacity_and_nodes.md)

| Topic | Source |
|---|---|
| Installing Karpenter | [Getting Started with Karpenter](https://karpenter.sh/docs/getting-started/getting-started-with-karpenter/) |
| NodeClasses (alias pinning, amiFamily, capacity reservations) | [Karpenter NodeClasses](https://karpenter.sh/docs/concepts/nodeclasses/) |
| Consolidation, drift, expiration | [Karpenter Disruption](https://karpenter.sh/docs/concepts/disruption/) |
| EC2NodeClass CRD (v1.15.2) | [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws) |
| Looking up EKS AMI IDs | [Retrieve recommended Amazon Linux AMI IDs](https://docs.aws.amazon.com/eks/latest/userguide/retrieve-ami-id.html) |
| EKS AMI release | [awslabs/amazon-eks-ami v20261107](https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107) |
| AMI pipelines | [What is EC2 Image Builder](https://docs.aws.amazon.com/imagebuilder/latest/userguide/what-is-image-builder.html) |
| Quotas | [Amazon EC2 instance type quotas](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html) |
| Capacity Reservations | [EC2 On-Demand Capacity Reservations](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-capacity-reservations.html) |
| Nested virtualization | [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) |
| nvproxy driver policy | [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor) |
| Kata, GPU Operator | [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers), [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator) |
| Warm capacity pattern | [AWS China blog: EKS + Kata + Cloud Hypervisor](https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/) |
| PDB behavior | [Kubernetes: Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) |

## Security { #ref-production-02-security }

Page: [Security](../production/02_security.md)

| Topic | Source |
|---|---|
| VPC CNI NetworkPolicy (standard, strict) | [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
| Blocking IMDS access | [EKS Best Practices: Identity and Access Management](https://docs.aws.amazon.com/eks/latest/best-practices/identity-and-access-management.html) |
| GuardDuty | [GuardDuty Runtime Monitoring](https://docs.aws.amazon.com/guardduty/latest/ug/runtime-monitoring.html) |
| EKS isolated pods | [Sandboxing limitations (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html), [Amazon EC2 Nitro Sandboxes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html) |
| Node IP exception | [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent) |
| gVisor GPU security | [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor) |
| Kata GPU passthrough | [NVIDIA GPU passthrough and Kata QEMU (4.3.1)](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md) |
| GPU Operator and Kata | [Deploy Kata Containers (NVIDIA)](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html), [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator) |
| GPU time-sharing in sandboxed pods | [GKE Sandbox](https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods) |
| Kubernetes concepts | [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/), [Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/) |

## Gateway and sandbox pools { #ref-production-03-gateway-and-pools }

Page: [Gateway and sandbox pools](../production/03_gateway_and_pools.md)

| Topic | Source |
|---|---|
| Large-scale operation with a gateway | [INTELLECT-3 (arXiv 2512.16144)](https://arxiv.org/abs/2512.16144) |
| VPC CNI NetworkPolicy | [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
| Ray on HyperPod | [Ray on SageMaker HyperPod](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html) |
| Projected tokens, TokenReview | [Kubernetes Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/) |
| Direct deletion and PDBs | [Kubernetes: Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) |
| Trainers | [verl-project/verl](https://github.com/verl-project/verl), [huggingface/trl](https://github.com/huggingface/trl), [TRL docs](https://huggingface.co/docs/trl) |
| Code | [`gateway/app.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py), [`client/pool.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/pool.py), [`gateway.yaml.tpl`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/gateway.yaml.tpl) |

## 04 Reward integrity { #ref-production-04-reward-integrity }

Page: [04 Reward integrity](../production/04_reward_integrity.md)

| Topic | Link |
|---|---|
| KernelBench (MIT, task contract, timing, `excessive_speedup_threshold`) | https://github.com/ScalingIntelligence/KernelBench |
| KernelBench v0.1 blog (reward hacking cases) | https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/ |
| Sakana AI CUDA Engineer | https://sakana.ai/ai-cuda-engineer/ |
| Kevin-32B (Cognition) | https://cognition.com/blog/kevin-32b |
| CUDA-L1 (arXiv 2507.14111) | https://arxiv.org/abs/2507.14111 |
| TRL docs (reward functions, `None` handling), GitHub | https://huggingface.co/docs/trl , https://github.com/huggingface/trl |
| veRL (custom reward function) | https://github.com/verl-project/verl |
| Triton | https://github.com/triton-lang/triton |
| EC2 accelerated computing instances (speedups differ per GPU) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| EKS VPC CNI network policy (sandbox egress denial) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| gVisor GPU support (nvproxy security scope) | https://gvisor.dev/docs/user_guide/gpu/ |
| Harness: parent, child, timing, policy | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/evaluate.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/runner.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/timing.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/policy.py |
| Reward conversion (TRL, veRL) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/reward_fn.py |
| Golden set and probe tool | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/golden.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py |
| Local tests | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_harness_cpu.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_policy.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_routing_and_rewards.py |

## 05 Sandbox versioning { #ref-production-05-sandbox-updates }

Page: [05 Sandbox versioning](../production/05_sandbox_updates.md)

| Topic | Link |
|---|---|
| ECR tag immutability | https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html |
| EKS optimized Amazon Linux AMIs | https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html |
| EKS AMI release v20261107 (driver 580.178.04) | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| Karpenter disruption (drift, consolidation) | https://karpenter.sh/docs/concepts/disruption/ |
| Karpenter (AWS provider) | https://github.com/aws/karpenter-provider-aws |
| Kubernetes ConfigMap (subPath mounts get no updates) | https://kubernetes.io/docs/concepts/configuration/configmap/ |
| gVisor GPU support (nvproxy driver policy) | https://gvisor.dev/docs/user_guide/gpu/ |
| TRL GRPO | https://github.com/huggingface/trl |
| veRL | https://github.com/verl-project/verl |
| KernelBench (`excessive_speedup_threshold`) | https://github.com/ScalingIntelligence/KernelBench |
| INTELLECT-3 technical report (environment versioning) | https://arxiv.org/abs/2512.16144 |
| Prime Intellect verifiers (Environments Hub integration) | https://github.com/PrimeIntellect-ai/verifiers |
| Rollout script | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/rollout.sh |
| probe and parity tools | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py |
| Golden set | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/golden.py |
| Gateway (group pinning) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py |
| Version files v1, v2 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/sandbox/versions |

## 06 Scaling with veRL { #ref-production-06-scaling-with-verl }

Page: [06 Scaling with veRL](../production/06_scaling_with_verl.md)

| Topic | Link |
|---|---|
| Ray on SageMaker HyperPod | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html |
| Installing KubeRay on HyperPod EKS | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray-install-kuberay.html |
| HyperPod automatic node recovery | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-node-recovery.html |
| FSx for Lustre on EKS | https://docs.aws.amazon.com/eks/latest/userguide/fsx-csi.html |
| EC2 accelerated computing instance specs | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| Ray on EKS (GPU cluster, Ray docs) | https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/aws-eks-gpu-cluster.html |
| KubeRay v1.7.2 | https://github.com/kuberay-project/kuberay/releases/tag/v1.7.2 |
| veRL | https://github.com/verl-project/verl |
| veRL 0.9.1 reward config | https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/reward/reward.yaml |
| AWS veRL sample (v0.6.1) | https://github.com/awslabs/awsome-distributed-ai/tree/main/examples/training/verl/hyperpod-eks/rlvr |
| FSx for Lustre CSI driver | https://github.com/kubernetes-sigs/aws-fsx-csi-driver |
| Qwen2.5-Coder-7B-Instruct (Apache-2.0) | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct |
| veRL image | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/Dockerfile |
| Reward function | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/reward_fn.py |
| Data preparation | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/prepare_data.py |
| Submission script | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/run_grpo_kernels.sh |
| RayCluster template | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/raycluster-verl.yaml.tpl |

## 07 Observability and operations { #ref-production-07-observability-and-operations }

Page: [07 Observability and operations](../production/07_observability_and_operations.md)

| Topic | Link |
|---|---|
| CloudWatch Container Insights | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html |
| Container Insights Prometheus monitoring | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights-Prometheus.html |
| Amazon Managed Service for Prometheus | https://docs.aws.amazon.com/prometheus/latest/userguide/what-is-Amazon-Managed-Service-Prometheus.html |
| EKS NetworkPolicy configuration (VPC CNI) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| HyperPod training operator (hang detection, restarts) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
| HyperPod EKS resiliency features | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html |
| VPC CNI network policy agent (node IP allowance) | https://github.com/aws/aws-network-policy-agent |
| Prometheus Python client | https://github.com/prometheus/client_python |
| gVisor GPU support (nvproxy) | https://gvisor.dev/docs/user_guide/gpu/ |
| Kata NVIDIA GPU passthrough (4.3.1) | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md |
| Sandbox server metrics | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py |
| Gateway metrics and auth | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py |
| Trainer events (`reward_batch`) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py |
| JWKS sync CronJob | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/jwks-sync.yaml.tpl |
| HyperPod job log patterns | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl |

## 08 Cost { #ref-production-08-cost }

Page: [08 Cost](../production/08_cost.md)

| Topic | Link |
|---|---|
| EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| SageMaker AI pricing (HyperPod `ml.*`) | https://aws.amazon.com/sagemaker/ai/pricing/ |
| EKS pricing (control plane) | https://aws.amazon.com/eks/pricing/ |
| VPC pricing (NAT gateway) | https://aws.amazon.com/vpc/pricing/ |
| EC2 instance type quotas (On-Demand vCPU quotas) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| EC2 accelerated computing instance specs | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| HyperPod EKS prerequisites | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| HyperPod automatic node recovery | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-node-recovery.html |
| Karpenter disruption (consolidation) | https://karpenter.sh/docs/concepts/disruption/ |
| Karpenter (AWS provider) | https://github.com/aws/karpenter-provider-aws |
| HyperPod CLI and dependency Helm chart | https://github.com/aws/sagemaker-hyperpod-cli |
| NodePool settings | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/karpenter/nodepools.yaml |
| Warm placeholder | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/warm-capacity.yaml |
| Pool limits (PriorityClass, PDB, ResourceQuota) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/pool-hardening.yaml |
| Cleanup script | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/08_cleanup.sh |

## 09 Provisioning and tearing down with CDK { #ref-production-09-cdk }

Page: [09 Provisioning and tearing down with CDK](../production/09_cdk.md)

| Kind | Topic | URL |
|---|---|---|
| AWS docs | AWS CDK v2 Developer Guide | https://docs.aws.amazon.com/cdk/v2/guide/home.html |
| AWS docs | CDK bootstrapping | https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html |
| AWS docs | EKS cluster endpoint access | https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html |
| AWS docs | EKS access entries | https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html |
| AWS docs | Start a Session Manager session (port forwarding) | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html |
| AWS docs | Security Hub EKS controls | https://docs.aws.amazon.com/securityhub/latest/userguide/eks-controls.html |
| AWS docs | eksctl cluster access (no private-only creation) | https://docs.aws.amazon.com/eks/latest/eksctl/vpc-cluster-access.html |
| GitHub | This repository's CDK app | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/cdk |
| GitHub | AWS CDK | https://github.com/aws/aws-cdk |
| GitHub | cdk-nag | https://github.com/cdklabs/cdk-nag |

## Glossary { #ref-reference-glossary }

Page: [Glossary](glossary.md)

**AWS documentation**

- [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html)
- [Accelerated computing instance types](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html)
- [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [SageMaker HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)
- [CloudFront: Restrict access to an Amazon S3 origin (OAC)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [CloudFront: Understand response headers policies (CSP, HSTS)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-response-headers-policies.html)

**GitHub and project documentation**

- [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor)
- [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md), [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers)
- [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)
- [Karpenter documentation](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws)
- [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin), [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent)
- [aws/sagemaker-hyperpod-cli](https://github.com/aws/sagemaker-hyperpod-cli)
- [TRL documentation](https://huggingface.co/docs/trl), [huggingface/trl](https://github.com/huggingface/trl), [verl-project/verl](https://github.com/verl-project/verl)
- [ScalingIntelligence/KernelBench](https://github.com/ScalingIntelligence/KernelBench)
- [Kubernetes: Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/), [Kubernetes: Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)

## Repository map { #ref-reference-repository-map }

Page: [Repository map](repository_map.md)

**AWS documentation**

- [Amazon EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)
- [Configure Amazon VPC CNI network policy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html)
- [SageMaker HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)

**GitHub and project documentation**

- [AWS CDK v2 Developer Guide](https://docs.aws.amazon.com/cdk/v2/guide/home.html), [aws/aws-cdk](https://github.com/aws/aws-cdk), [cdklabs/cdk-nag](https://github.com/cdklabs/cdk-nag)
- [awslabs/amazon-eks-ami v20261107](https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107)
- [Karpenter documentation](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws)
- [gVisor installation](https://gvisor.dev/docs/user_guide/install/), [google/gvisor](https://github.com/google/gvisor)
- [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md)
- [NVIDIA GPU Operator with Kata](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html), [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator), [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [aws/sagemaker-hyperpod-cli](https://github.com/aws/sagemaker-hyperpod-cli)

**This repository**

- [daekeun-ml/gpu-sandbox-on-aws](https://github.com/daekeun-ml/gpu-sandbox-on-aws): [scripts/render.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/render.py), [scripts/lib.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib.sh), [k8s/sandbox/deployment.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/deployment.yaml.tpl), [pyproject.toml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/pyproject.toml)

## Configuration { #ref-reference-configuration }

Page: [Configuration](configuration.md)

**AWS documentation**

- [Amazon EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)
- [Configure Amazon VPC CNI network policy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [SageMaker HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)
- [SageMaker HyperPod IAM prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html)

**GitHub and project documentation**

- [TRL documentation](https://huggingface.co/docs/trl), [huggingface/trl](https://github.com/huggingface/trl)
- [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor)
- [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md)
- [aws/sagemaker-hyperpod-cli](https://github.com/aws/sagemaker-hyperpod-cli)

**Files in this repository**

- [src/gpusandbox/server/app.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py), [src/gpusandbox/auth.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/auth.py), [src/gpusandbox/harness/evaluate.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/evaluate.py)
- [src/gpusandbox/client/routing.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/routing.py), [src/gpusandbox/client/pool.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/pool.py), [src/gpusandbox/gateway/app.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py)
- [rl/trl/train_grpo.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/trl/train_grpo.py), [scripts/config.env.example](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/config.env.example), [cdk/gpusandbox_cdk/config.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/config.py), [k8s/sandbox/profiles](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/sandbox/profiles), [k8s/sandbox/versions](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/sandbox/versions), [k8s/base/routing.json.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/routing.json.tpl)

## Troubleshooting { #ref-reference-troubleshooting }

Page: [Troubleshooting](troubleshooting.md)

**AWS documentation**

- [Configure Amazon VPC CNI network policy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html)
- [Amazon EC2 accelerated computing instance types](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html)
- [SageMaker HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)
- [SageMaker HyperPod automatic node recovery](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-node-recovery.html), [deep health checks](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html)

**GitHub and project documentation**

- [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/), [gVisor installation](https://gvisor.dev/docs/user_guide/install/), [google/gvisor](https://github.com/google/gvisor)
- [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md), [Kata issue #11687](https://github.com/kata-containers/kata-containers/issues/11687)
- [NVIDIA GPU Operator with Kata](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html), [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent), [awslabs/amazon-eks-ami v20261107](https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107)
- [CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping-env.html), [cdklabs/cdk-nag](https://github.com/cdklabs/cdk-nag), [TRL docs](https://huggingface.co/docs/trl)

**Related files in this repository**

- [scripts/ops/verify.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/verify.sh), [scripts/lib_jobs.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib_jobs.sh), [scripts/kata/gpu_nodes.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/kata/gpu_nodes.sh)
- [src/gpusandbox/server/app.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py), [src/gpusandbox/auth.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/auth.py), [infra/eks/node-guard.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/eks/node-guard.sh)

## Misconceptions { #ref-reference-faq }

Page: [Misconceptions](faq.md)

| Topic | Link |
|---|---|
| EC2 nested virtualization (User Guide, What's New) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html , https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
| EC2 accelerated computing instances (`g4dn.metal`, `g5g.metal`) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS Nitro Sandboxes, EKS sandboxing limitations | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| EKS Auto Mode managed instances | https://docs.aws.amazon.com/eks/latest/userguide/automode-learn-instances.html |
| Amazon Bedrock AgentCore Code Interpreter | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html |
| HyperPod EKS prerequisites, AMI release notes (driver per Kubernetes version) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-release-ami-eks.html |
| VPC CNI network policy | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| aws-network-policy-agent (node IP allowed) | https://github.com/aws/aws-network-policy-agent |
| gVisor GPU support (nvproxy, security scope) | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
| GKE Sandbox (GPU time-sharing advice) | https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods |
| Kata 4.3.1 NVIDIA GPU passthrough, hypervisor support table, issue #11687 | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md , https://github.com/kata-containers/kata-containers/issues/11687 |
| NVIDIA GPU Operator with Kata (validated range) | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html |
| Firecracker FAQ, CHANGELOG | https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md , https://github.com/firecracker-microvm/firecracker/blob/main/CHANGELOG.md |
| kubernetes-sigs/agent-sandbox | https://github.com/kubernetes-sigs/agent-sandbox |
| AWS Korea tech blog "AWS에서 AI 에이전트 실행 환경 격리하기" (Isolating AI agent execution environments on AWS), parts 1 and 2 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ , https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
| Qwen2.5-Coder model cards (licenses) | https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct , https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct , https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct |
| TRL docs (`None` from reward functions) | https://huggingface.co/docs/trl |
| This repository: verification script, rollout, HyperPod check, policy | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/verify.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/rollout.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/policy.py |
