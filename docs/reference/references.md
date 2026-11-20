# 참고 자료 모음

!!! info "TL;DR"
    페이지별 전체 참고 링크가 왼쪽 메뉴 순서로 있습니다. 각 페이지 끝의 접힌 "참고 자료" 상자에는 핵심 링크만 있습니다.

어떤 사실을 어느 출처가 뒷받침하는지는 [검증된 사실과 출처](sources.md)에 정리되어 있습니다.

## 01 AI가 만든 코드를 격리하는 이유 { #ref-beginner-01-why-sandbox }

페이지: [01 AI가 만든 코드를 격리하는 이유](../beginner/01_why_sandbox.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 블로그 | AI 에이전트 샌드박스, EKS 격리 1부 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ |
| AWS 블로그 | 같은 시리즈 2부 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
| AWS 블로그 | 같은 시리즈 3부 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/ |
| AWS 문서 | EKS에서 네트워크 정책 켜기 | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| AWS 문서 | EC2 인스턴스 메타데이터(IMDSv2) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html |
| GitHub | Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |
| GitHub | 이 저장소 | https://github.com/daekeun-ml/gpu-sandbox-on-aws |

## 02 컨테이너와 샌드박스 { #ref-beginner-02-container-vs-sandbox }

페이지: [02 컨테이너와 샌드박스](../beginner/02_container_vs_sandbox.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 블로그 | AI 에이전트 샌드박스, EKS 격리 1부 (runc와 gVisor 비교 실험) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ |
| AWS 블로그 | 같은 시리즈 2부 (시스템 호출 비용 측정) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
| AWS 블로그 | 같은 시리즈 3부 (운영 사례) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/ |
| 공식 문서 | Kubernetes RuntimeClass | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
| 공식 문서 | gVisor 아키텍처 | https://gvisor.dev/docs/architecture_guide/intro/ |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |

## 03 GPU까지 격리하려면 { #ref-beginner-03-gpu-sandbox }

페이지: [03 GPU까지 격리하려면](../beginner/03_gpu_sandbox.md)

| 구분 | 주제 | URL |
|---|---|---|
| 공식 문서 | gVisor GPU 지원 (nvproxy) | https://gvisor.dev/docs/user_guide/gpu/ |
| GitHub | Kata Containers GPU passthrough | https://github.com/kata-containers/kata-containers/tree/main/docs/use-cases |
| AWS 문서 | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS 문서 | Accelerated computing 인스턴스 | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | 이 저장소 | https://github.com/daekeun-ml/gpu-sandbox-on-aws |

## 04 강화학습과 샌드박스 { #ref-beginner-04-rl-and-sandbox }

페이지: [04 강화학습과 샌드박스](../beginner/04_rl_and_sandbox.md)

| 구분 | 주제 | URL |
|---|---|---|
| 논문 | KernelBench | https://arxiv.org/abs/2502.10517 |
| 공식 문서 | TRL GRPO Trainer | https://huggingface.co/docs/trl/main/en/grpo_trainer |
| GitHub | KernelBench | https://github.com/ScalingIntelligence/KernelBench |
| GitHub | 이 저장소의 채점 프로그램(harness) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/src/gpusandbox/harness |

## 05 직접 해 보기 { #ref-beginner-05-hands-on }

페이지: [05 직접 해 보기](../beginner/05_hands_on.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 문서 | AWS CDK v2 개발자 가이드 | https://docs.aws.amazon.com/cdk/v2/guide/home.html |
| AWS 문서 | Session Manager 세션 시작 (포트 포워딩) | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html |
| AWS 문서 | EKS cluster endpoint access | https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html |
| AWS 문서 | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| GitHub | 이 저장소 | https://github.com/daekeun-ml/gpu-sandbox-on-aws |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | gVisor | https://github.com/google/gvisor |

## 06 multi-turn 에이전트와 Agent Sandbox { #ref-beginner-06-multi-turn-agent }

페이지: [06 multi-turn 에이전트와 Agent Sandbox](../beginner/06_multi_turn_agent.md)

| 구분 | 주제 | URL |
|---|---|---|
| GitHub | Agent Sandbox (kubernetes-sigs/agent-sandbox) | https://github.com/kubernetes-sigs/agent-sandbox |
| AI on EKS | Agent Sandbox on EKS | https://awslabs.github.io/ai-on-eks/ko/docs/infra/agents/agent-sandbox |
| GitHub | AI on EKS | https://github.com/awslabs/ai-on-eks |
| AWS 문서 | EKS sandboxing 제한 사항 | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| AWS 문서 | Amazon EC2 온디맨드 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| GitHub | 이 저장소의 Agent Sandbox 확장 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/extensions/agent-sandbox |

## 시작하기 { #ref-getting-started }

페이지: [시작하기](../getting_started.md)

| 주제 | 링크 |
|---|---|
| AWS CLI v2 설치 | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |
| EC2 instance type quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| EKS Kubernetes 버전 | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| HyperPod (EKS) 사전 요구 사항 | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| EC2 On-Demand 가격 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS CDK v2 개발자 가이드, bootstrapping | https://docs.aws.amazon.com/cdk/v2/guide/home.html , https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html |
| Session Manager plugin 설치 | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html |
| eksctl 클러스터 접근 (private 전용 생성 미지원) | https://docs.aws.amazon.com/eks/latest/eksctl/vpc-cluster-access.html |
| Kubernetes version skew policy | https://kubernetes.io/releases/version-skew-policy/ |
| TRL 문서, GitHub | https://huggingface.co/docs/trl , https://github.com/huggingface/trl |
| uv | https://github.com/astral-sh/uv |
| 테스트 워크플로 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/.github/workflows/tests.yml |
| 샌드박스 서버, 인증, reaper | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/auth.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/procs.py |
| GRPO trainer, 설정 예시 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/trl/train_grpo.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/config.env.example |

## GPU 샌드박스가 필요한 경우 { #ref-concepts-01-why-gpu-sandbox }

페이지: [GPU 샌드박스가 필요한 경우](../concepts/01_why_gpu_sandbox.md)

| 주제 | 링크 |
|---|---|
| AWS Nitro Sandboxes | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html |
| EKS sandboxing 제한 사항 | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| EC2 가속 컴퓨팅 인스턴스 사양 | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| GKE Sandbox (GPU time-sharing 권고) | https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods |
| Firecracker FAQ, CHANGELOG | https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md , https://github.com/firecracker-microvm/firecracker/blob/main/CHANGELOG.md |
| KernelBench GitHub, v0.1 블로그 | https://github.com/ScalingIntelligence/KernelBench , https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/ |
| CUDA-L1 | https://arxiv.org/abs/2507.14111 |
| Sakana AI CUDA Engineer | https://sakana.ai/ai-cuda-engineer/ |
| Kevin-32B | https://cognition.com/blog/kevin-32b |
| Triton | https://github.com/triton-lang/triton |
| agent-sandbox, SandboxFusion | https://github.com/kubernetes-sigs/agent-sandbox , https://github.com/bytedance/SandboxFusion |
| 과제, prompt, reward 코드 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tasks/__init__.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/prompts.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py |
| harness timing, 정책 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/timing.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/policy.py |

## 격리 런타임 비교 { #ref-concepts-02-isolation-runtimes }

페이지: [격리 런타임 비교](../concepts/02_isolation_runtimes.md)

| 주제 | 링크 |
|---|---|
| EC2 nested virtualization (User Guide, What's New) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html , https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
| EC2 가속 컴퓨팅 인스턴스 사양 | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS Nitro Sandboxes, EKS sandboxing 제한 사항 | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| AWS Containers 블로그 (Kata + Firecracker, i3.metal) | https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/ |
| AWS China 블로그 (Kata + CLH, c5.metal) | https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/ |
| gVisor 설치, GPU 지원, GitHub | https://gvisor.dev/docs/user_guide/install/ , https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
| GKE Sandbox | https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods |
| Kata NVIDIA GPU passthrough (4.3.1), CLH GPU 이슈 | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers/issues/11687 |
| NVIDIA GPU Operator (Kata), GitHub | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html , https://github.com/NVIDIA/gpu-operator |
| NVIDIA k8s-device-plugin | https://github.com/NVIDIA/k8s-device-plugin |
| EKS AL2023 AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| Cloud Hypervisor, Firecracker | https://github.com/cloud-hypervisor/cloud-hypervisor , https://github.com/firecracker-microvm/firecracker |
| Karpenter | https://karpenter.sh/docs/ , https://github.com/aws/karpenter-provider-aws |
| Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |
| 이 에셋의 런타임 설정 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/gvisor/install-gvisor.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/kata-deploy-values.yaml , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/gpu-operator-values.yaml |

## On-policy RL과 샌드박스 { #ref-concepts-03-onpolicy-rl-with-sandboxes }

페이지: [On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

| 주제 | 링크 |
|---|---|
| TRL GRPO trainer 문서, GitHub | https://huggingface.co/docs/trl/main/en/grpo_trainer , https://github.com/huggingface/trl |
| veRL | https://github.com/verl-project/verl |
| KubeRay | https://github.com/ray-project/kuberay |
| SageMaker HyperPod의 Ray | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html |
| HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
| veRL on HyperPod 예제 | https://github.com/awslabs/awsome-distributed-ai |
| INTELLECT-3 | https://arxiv.org/abs/2512.16144 |
| Kubernetes ConfigMap (마운트 갱신, subPath) | https://kubernetes.io/docs/concepts/configuration/configmap/ |
| 클라이언트, routing, pool | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/__init__.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/routing.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/pool.py |
| reward, gateway, veRL reward | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/reward_fn.py |
| blue/green 스크립트, 버전 파일 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/rollout.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/versions/v2.env |

## 플랫폼과 인스턴스 선택 { #ref-concepts-04-platforms-and-instances }

페이지: [플랫폼과 인스턴스 선택](../concepts/04_platforms_and_instances.md)

| 주제 | 링크 |
|---|---|
| HyperPod (EKS) 사전 요구 사항, IAM | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html |
| HyperPod 복원력, deep health check | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html |
| HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
| ClusterInstanceGroupSpecification (API) | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ClusterInstanceGroupSpecification.html |
| SageMaker HyperPod의 Ray | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html |
| EKS Kubernetes 버전 | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| EC2 가속 컴퓨팅 인스턴스 사양, quota | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html , https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| 가격 (EC2, SageMaker AI) | https://aws.amazon.com/ec2/pricing/on-demand/ , https://aws.amazon.com/sagemaker/ai/pricing/ |
| HyperPod CLI와 의존성 차트 | https://github.com/aws/sagemaker-hyperpod-cli |
| EKS AL2023 AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| gVisor GPU 지원, GitHub | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
| awsome-distributed-ai (veRL on HyperPod) | https://github.com/awslabs/awsome-distributed-ai |
| 이 에셋의 HyperPod 템플릿과 점검 스크립트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/cluster.json.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh |

## 상황별 선택 가이드 { #ref-concepts-05-decision-guide }

페이지: [상황별 선택 가이드](../concepts/05_decision_guide.md)

| 주제 | 링크 |
|---|---|
| AWS Nitro Sandboxes, EKS sandboxing 제한 사항 | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| Amazon Bedrock AgentCore Code Interpreter | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html |
| EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| EC2 가속 컴퓨팅 인스턴스 사양 | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| EC2 On-Demand 가격 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| gVisor GPU 지원, GitHub | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
| Kata NVIDIA GPU passthrough (4.3.1), GitHub | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers |
| NVIDIA GPU Operator (Kata) | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html |
| Cloud Hypervisor | https://github.com/cloud-hypervisor/cloud-hypervisor |
| Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |
| Modal Sandboxes (서드파티) | https://modal.com/docs/guide/sandbox |
| 이 에셋의 런타임 프로필 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/gvisor.env , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-qemu.env , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-clh-cpu.env |

## 06 Agent Sandbox로 확장 { #ref-concepts-06-agent-sandbox }

페이지: [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

공식 문서와 공식 저장소:

| 주제 | 링크 |
|---|---|
| Agent Sandbox 저장소, 릴리스 (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox , https://github.com/kubernetes-sigs/agent-sandbox/releases |
| SandboxClaim, SandboxTemplate, SandboxWarmPool, Sandbox 타입 (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxclaim_types.go , https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxtemplate_types.go , https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxwarmpool_types.go , https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/api/v1beta1/sandbox_types.go |
| controller의 DNS 주입 조건 (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/controllers/utils.go |
| upstream 예제 (`kata-aks`, `kata-gke-sandbox`, `gpu-l4-snapshot-sandbox`) | https://github.com/kubernetes-sigs/agent-sandbox/tree/main/examples |
| AWS 기술 블로그 1부: 개념과 구성 (gVisor on EKS, 격리 계층 4개) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ |
| AWS 기술 블로그 2부: 이 페이지가 인용한 기본 정책, DNS, router 점검과 warm pool 측정 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
| AWS 기술 블로그 3부: 에이블리의 Amazon EKS 기반 Agent Sandbox 운영 사례 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/ |
| AI on EKS: Agent Sandbox on EKS (gVisor, agent-sandbox CRD, FQDN egress, 런타임 계층) | https://awslabs.github.io/ai-on-eks/ko/docs/infra/agents/agent-sandbox , https://github.com/awslabs/ai-on-eks |
| Amazon EKS NetworkPolicy (VPC CNI), policy agent | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html , https://github.com/aws/aws-network-policy-agent |
| EKS Best Practices: 노드 인스턴스 프로필 접근 제한 (IMDSv2, hop limit 1) | https://docs.aws.amazon.com/eks/latest/best-practices/identity-and-access-management.html |
| Kubernetes NetworkPolicy (허용 규칙의 합집합) | https://kubernetes.io/docs/concepts/services-networking/network-policies/ |
| Karpenter | https://karpenter.sh/docs/ , https://github.com/aws/karpenter-provider-aws |
| veRL `BaseTool` (v0.9.1) | https://github.com/verl-project/verl/blob/v0.9.1/verl/tools/base_tool.py |
| veRL `ToolAgentLoop` (v0.9.1, tool 호출마다 create, execute, release) | https://github.com/verl-project/verl/blob/v0.9.1/verl/experimental/agent_loop/tool_agent_loop.py |
| gVisor, Kata Containers | https://github.com/google/gvisor , https://github.com/kata-containers/kata-containers |
| Amazon EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |

이 페이지가 설명하는 저장소 파일:

- [k8s/extensions/agent-sandbox/template.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/template.yaml.tpl), [trainer-claims-rbac.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/trainer-claims-rbac.yaml), [job-multiturn.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/job-multiturn.yaml.tpl)
- [k8s/base/trainer-rbac.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/trainer-rbac.yaml)
- [scripts/extensions/agent_sandbox.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/extensions/agent_sandbox.sh)
- [src/gpusandbox/agent_sandbox.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/agent_sandbox.py), [src/gpusandbox/multiturn.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/multiturn.py)
- [rl/verl/sandbox_tool.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/sandbox_tool.py), [rl/verl/sandbox_tool_config.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/sandbox_tool_config.yaml)
- [tests/test_agent_sandbox.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_agent_sandbox.py), [tests/test_multiturn.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_multiturn.py), [tests/test_manifests.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_manifests.py)
- [k8s/base/networkpolicies.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/networkpolicies.yaml), [infra/karpenter/nodepools.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/karpenter/nodepools.yaml)

## 00 핸즈온 전체 흐름 { #ref-handson-00-overview }

페이지: [00 핸즈온 전체 흐름](../handson/00_overview.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 문서 | EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS 문서 | SageMaker AI 요금 (HyperPod) | https://aws.amazon.com/sagemaker/ai/pricing/ |
| AWS 문서 | Amazon EKS 요금 | https://aws.amazon.com/eks/pricing/ |
| AWS 문서 | Amazon VPC 요금 (NAT gateway) | https://aws.amazon.com/vpc/pricing/ |
| AWS 문서 | EC2 instance type quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| AWS 문서 | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS 문서 | Accelerated computing instance types | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS 문서 | EKS Kubernetes versions | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| AWS 문서 | EKS cluster API server endpoint (private) | https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html |
| AWS 문서 | AWS CDK v2 개발자 가이드 | https://docs.aws.amazon.com/cdk/v2/guide/home.html |
| AWS 문서 | Session Manager plugin 설치 | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html |
| AWS 문서 | HyperPod EKS prerequisites | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| AWS 문서 | CloudFront Origin Access Control (09 데모 사이트) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html |
| GitHub | 이 저장소 | https://github.com/daekeun-ml/gpu-sandbox-on-aws |
| GitHub | 이 저장소의 CDK 앱 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/cdk |
| GitHub | AWS CDK | https://github.com/aws/aws-cdk |
| GitHub | Amazon EKS AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | NVIDIA GPU Operator | https://github.com/NVIDIA/gpu-operator |
| GitHub | NVIDIA k8s-device-plugin | https://github.com/NVIDIA/k8s-device-plugin |

## 01 클러스터와 이미지 { #ref-handson-01-cluster-and-images }

페이지: [01 클러스터와 이미지](../handson/01_cluster_and_images.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 문서 | EKS cluster API server endpoint (public, private, CIDR) | https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html |
| AWS 문서 | EKS managed node group launch templates (user data 병합, hop limit) | https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html |
| AWS 문서 | EKS access entries | https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html |
| AWS 문서 | EC2 instance metadata options (hop limit) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html |
| AWS 문서 | VPC CNI network policy 설정 | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| AWS 문서 | ECR image tag mutability | https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html |
| AWS 문서 | EKS Kubernetes versions | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| AWS 문서 | HyperPod EKS prerequisites | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| AWS 문서 | AWS CDK 시작하기 (CLI 설치) | https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html |
| AWS 문서 | AWS CDK prerequisites (Node.js) | https://docs.aws.amazon.com/cdk/v2/guide/prerequisites.html |
| AWS 문서 | CDK bootstrapping | https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html |
| AWS 문서 | Session Manager plugin 설치 | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html |
| AWS 문서 | Security Hub EKS 컨트롤 (EKS.1) | https://docs.aws.amazon.com/securityhub/latest/userguide/eks-controls.html |
| AWS 문서 | AWS CLI `update-nodegroup-config` | https://docs.aws.amazon.com/cli/latest/reference/eks/update-nodegroup-config.html |
| AWS 문서 | eksctl cluster access (private만 활성화한 클러스터 생성 미지원, CDK로 바꾼 이유) | https://docs.aws.amazon.com/eks/latest/eksctl/vpc-cluster-access.html |
| 공식 문서 | gVisor installation | https://gvisor.dev/docs/user_guide/install/ |
| GitHub | AWS CDK | https://github.com/aws/aws-cdk |
| GitHub | cdk-nag | https://github.com/cdklabs/cdk-nag |
| GitHub | Amazon EKS AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| GitHub | Amazon VPC CNI | https://github.com/aws/amazon-vpc-cni-k8s |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | TRL | https://github.com/huggingface/trl |
| GitHub | vLLM | https://github.com/vllm-project/vllm |
| GitHub | CDK 스택 (stack.py) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py |
| GitHub | 터널 스크립트 (tunnel.sh) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/tunnel.sh |
| GitHub | user data 모듈 (userdata.py) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/eks/userdata.py |
| GitHub | install-gvisor.sh | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/gvisor/install-gvisor.sh |
| GitHub | node-guard.sh | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/eks/node-guard.sh |

## 02 gVisor GPU 샌드박스 { #ref-handson-02-gvisor }

페이지: [02 gVisor GPU 샌드박스](../handson/02_gvisor.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 문서 | Accelerated computing instance types (g5, g6, g4dn) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS 문서 | EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS 문서 | EKS sandboxing limitations (isolated pods) | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| 공식 문서 | gVisor GPU support (nvproxy, 드라이버 정책, CDI) | https://gvisor.dev/docs/user_guide/gpu/ |
| 공식 문서 | gVisor installation | https://gvisor.dev/docs/user_guide/install/ |
| 공식 문서 | GKE Sandbox pods | https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods |
| 공식 문서 | Kubernetes RuntimeClass | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | gVisor가 보고하는 커널 버전 (version.go) | https://github.com/google/gvisor/blob/master/pkg/sentry/kernel/version/version.go |
| GitHub | NVIDIA k8s-device-plugin | https://github.com/NVIDIA/k8s-device-plugin |
| GitHub | NVIDIA Container Toolkit | https://github.com/NVIDIA/nvidia-container-toolkit |
| GitHub | Amazon EKS AMI v20261107 | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| GitHub | device plugin values | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/gpu/nvidia-device-plugin-values.yaml |
| GitHub | gVisor RuntimeClass | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/runtimes/runtimeclass-gvisor.yaml |
| GitHub | GPU 스택과 gVisor 설치 스크립트 (04_install_gpu_stack.sh) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/04_install_gpu_stack.sh |

## 03 Kata 샌드박스 (CLH, QEMU) { #ref-handson-03-kata }

페이지: [03 Kata 샌드박스 (CLH, QEMU)](../handson/03_kata.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 문서 | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS 문서 | What's New: EC2 nested virtualization (2026-02) | https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
| AWS 문서 | Accelerated computing instance types (g4dn.metal) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS 문서 | EKS managed node group launch templates | https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html |
| AWS 문서 | EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS 블로그 | Kata Containers로 EKS 워크로드 격리 (2024) | https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/ |
| 공식 문서 | NVIDIA GPU Operator with Kata Containers | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html |
| 공식 문서 | Kubernetes RuntimeClass (scheduling, overhead) | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | Kata 4.3.1 NVIDIA GPU passthrough (QEMU) | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md |
| GitHub | Kata 4.3.1 hypervisors.md | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md |
| GitHub | Kata issue 11687 (CLH GPU) | https://github.com/kata-containers/kata-containers/issues/11687 |
| GitHub | NVIDIA GPU Operator | https://github.com/NVIDIA/gpu-operator |
| GitHub | Cloud Hypervisor | https://github.com/cloud-hypervisor/cloud-hypervisor |
| GitHub | kata-deploy values | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/kata-deploy-values.yaml |
| GitHub | GPU Operator values | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/gpu-operator-values.yaml |
| GitHub | IOMMU AMI 빌드 스크립트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/build-iommu-ami.sh |
| GitHub | CDK 스택 (Kata 노드 그룹과 launch template) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py |
| GitHub | user data 모듈 (userdata.py) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/eks/userdata.py |
| GitHub | 실험용 CLH GPU values | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/experimental-clh-gpu/values-clh-gpu.yaml |

## 04 샌드박스 풀 배포와 검증 { #ref-handson-04-sandbox-pools }

페이지: [04 샌드박스 풀 배포와 검증](../handson/04_sandbox_pools.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 문서 | VPC CNI network policy 설정 (standard, strict 모드) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| AWS 문서 | EKS 클러스터의 OIDC issuer | https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html |
| AWS 문서 | EC2 instance metadata options | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html |
| 공식 문서 | Kubernetes ServiceAccount token projection, issuer discovery | https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/ |
| 공식 문서 | Kubernetes Pod Security Standards | https://kubernetes.io/docs/concepts/security/pod-security-standards/ |
| 공식 문서 | Kubernetes Service (headless Service) | https://kubernetes.io/docs/concepts/services-networking/service/ |
| GitHub | AWS network policy agent (노드 IP 허용) | https://github.com/aws/aws-network-policy-agent |
| GitHub | Amazon VPC CNI | https://github.com/aws/amazon-vpc-cni-k8s |
| GitHub | 샌드박스 Deployment 템플릿 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/deployment.yaml.tpl |
| GitHub | NetworkPolicy | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/networkpolicies.yaml |
| GitHub | 인증 모듈 (auth.py) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/auth.py |
| GitHub | 샌드박스 서버 (readiness, egress 점검) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py |
| GitHub | golden 제출물 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/golden.py |
| GitHub | 풀 검증 스크립트 (ops/verify.sh) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/verify.sh |

## 05 On-policy GRPO 학습 { #ref-handson-05-grpo-training }

페이지: [05 On-policy GRPO 학습](../handson/05_grpo_training.md)

공식 문서와 공식 저장소:

| 주제 | 링크 |
|---|---|
| TRL GRPO Trainer (지표, colocate, sleep mode, None reward) | https://huggingface.co/docs/trl/grpo_trainer |
| TRL 저장소 | https://github.com/huggingface/trl |
| vLLM 저장소 | https://github.com/vllm-project/vllm |
| 기본 모델 (Apache-2.0) | https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct |
| KernelBench (ModelNew 계약) | https://github.com/ScalingIntelligence/KernelBench |
| Amazon EKS NetworkPolicy (VPC CNI) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| Amazon EC2 가속 컴퓨팅 인스턴스 (A10G, L4, T4) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| Amazon EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| Kubernetes ConfigMap (마운트 갱신, subPath) | https://kubernetes.io/docs/concepts/configuration/configmap/ |

이 페이지가 설명하는 저장소 파일:

- [scripts/07_run_grpo.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/07_run_grpo.sh)
- [k8s/trainer/job-grpo.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/job-grpo.yaml.tpl)
- [rl/trl/train_grpo.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/trl/train_grpo.py)
- [src/gpusandbox/rewards.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py)
- [src/gpusandbox/prompts.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/prompts.py)
- [src/gpusandbox/tasks/__init__.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tasks/__init__.py)

## 06 학습 중 샌드박스 업데이트 { #ref-handson-06-sandbox-update }

페이지: [06 학습 중 샌드박스 업데이트](../handson/06_sandbox_update.md)

공식 문서와 공식 저장소:

| 주제 | 링크 |
|---|---|
| Kubernetes ConfigMap (마운트 갱신 지연, subPath는 갱신 안 됨) | https://kubernetes.io/docs/concepts/configuration/configmap/ |
| AWS CLI `update-nodegroup-config` (관리형 노드 그룹 크기 변경) | https://docs.aws.amazon.com/cli/latest/reference/eks/update-nodegroup-config.html |
| Amazon EKS NetworkPolicy (VPC CNI) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| Amazon EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| KernelBench (`excessive_speedup_threshold`) | https://github.com/ScalingIntelligence/KernelBench |
| KernelBench v0.1 블로그 (reward hacking 사례) | https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/ |
| INTELLECT-3 (trainer와 독립적인 환경 버전 관리) | https://arxiv.org/abs/2512.16144 |
| TRL 저장소 | https://github.com/huggingface/trl |

이 페이지가 설명하는 저장소 파일:

- [scripts/ops/rollout.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/rollout.sh)
- [k8s/sandbox/versions/v1.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/versions/v1.env), [v2.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/versions/v2.env)
- [k8s/sandbox/deployment.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/deployment.yaml.tpl), [k8s/base/routing.json.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/routing.json.tpl)
- [src/gpusandbox/client/routing.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/routing.py), [src/gpusandbox/rewards.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py)
- [src/gpusandbox/tools.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py), [src/gpusandbox/golden.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/golden.py)

운영 환경에서 veRL처럼 completion을 하나씩 채점하는 trainer는 batch 단위로 버전을 맞출 수 없어서, gateway가 `group_key` 단위로 버전을 고정합니다([Production 05 샌드박스 버전 관리](../production/05_sandbox_updates.md)).

## 07 HyperPod 시나리오 { #ref-handson-07-hyperpod }

페이지: [07 HyperPod 시나리오](../handson/07_hyperpod.md)

공식 문서와 공식 저장소:

| 주제 | 링크 |
|---|---|
| HyperPod EKS 전제조건 | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| HyperPod IAM (execution role) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html |
| HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
| training operator 설치 (cert-manager, Pod Identity) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html |
| training operator 사용 (runPolicy, logMonitoringConfiguration) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-usage.html |
| HyperPod EKS AMI 릴리스 (드라이버 버전) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-release-ami-eks.html |
| CreateCluster API (NodeRecovery, Orchestrator) | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateCluster.html |
| ClusterInstanceGroupSpecification (인스턴스 유형, OnStartDeepHealthChecks) | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ClusterInstanceGroupSpecification.html |
| S3 Block Public Access | https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html |
| EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| Amazon EKS Kubernetes 버전 (표준 지원) | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html |
| SageMaker AI 요금 (HyperPod) | https://aws.amazon.com/sagemaker/ai/pricing/ |
| gVisor GPU 지원 (nvproxy, 드라이버 정책) | https://gvisor.dev/docs/user_guide/gpu/ |
| HyperPod CLI와 dependency Helm chart | https://github.com/aws/sagemaker-hyperpod-cli |
| gVisor 저장소 | https://github.com/google/gvisor |
| Kata Containers 저장소 | https://github.com/kata-containers/kata-containers |
| AWS 분산 학습 예제 (HyperPod EKS) | https://github.com/awslabs/awsome-distributed-ai |

이 페이지가 설명하는 저장소 파일:

- [scripts/hyperpod/create.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/create.sh), [run_grpo.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/run_grpo.sh), [check_gvisor.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh), [delete.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/delete.sh)
- [infra/hyperpod/cluster.json.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/cluster.json.tpl), [execution-role-eks-policy.json](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/execution-role-eks-policy.json)
- [infra/hyperpod/lifecycle/on_create.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/lifecycle/on_create.sh), [on_create_sandbox.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/lifecycle/on_create_sandbox.sh), [register_runsc.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/lifecycle/register_runsc.sh) (B2 노드 시작 시 `runsc` 등록)
- [infra/hyperpod/ami/build-b2-ami.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/ami/build-b2-ami.sh), [customize-b2.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/ami/customize-b2.sh) (B2 이미지의 드라이버 교체와 gVisor 설치)
- [k8s/trainer/hyperpod-job-grpo.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl)
- [scripts/config.env.example](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/config.env.example)

## 08 런타임 벤치마크 { #ref-handson-08-benchmark }

페이지: [08 런타임 벤치마크](../handson/08_benchmark.md)

공식 문서와 공식 저장소:

| 주제 | 링크 |
|---|---|
| EC2 nested virtualization (bare metal 권장) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| Amazon EC2 가속 컴퓨팅 인스턴스 (A10G, L4, T4) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| Amazon EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS China 블로그 (Kata + CLH, OpenSandbox) | https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/ |
| AWS Containers 블로그 (Kata + Firecracker, i3.metal) | https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/ |
| Kata NVIDIA GPU passthrough (QEMU) | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md |
| Kata CLH GPU 지원 논의 | https://github.com/kata-containers/kata-containers/issues/11687 |
| Kata Containers 저장소 | https://github.com/kata-containers/kata-containers |
| gVisor GPU 지원 | https://gvisor.dev/docs/user_guide/gpu/ |
| gVisor 저장소 | https://github.com/google/gvisor |
| KernelBench (timing 방식) | https://github.com/ScalingIntelligence/KernelBench |

이 페이지가 설명하는 저장소 파일:

- [scripts/ops/bench.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/bench.sh), [scripts/lib_jobs.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib_jobs.sh)
- [src/gpusandbox/tools.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py)
- [src/gpusandbox/server/app.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py)
- [k8s/sandbox/deployment.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/deployment.yaml.tpl)
- [k8s/sandbox/profiles/gvisor.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/gvisor.env), [kata-qemu.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-qemu.env), [kata-clh-cpu.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-clh-cpu.env), [kata-qemu-cpu.env](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/profiles/kata-qemu-cpu.env)

## 09 데모 사이트 (CloudFront) { #ref-handson-09-demo-site }

페이지: [09 데모 사이트 (CloudFront)](../handson/09_demo_site.md)

공식 문서와 공식 저장소:

| 주제 | 링크 |
|---|---|
| CloudFront: S3 origin 접근 제한 (OAC, 버킷 정책 예시) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html |
| CloudFront 배포 설정 (security policy, 기본 인증서의 TLSv1, default root object, price class) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesGeneral.html |
| CloudFront 응답 헤더 정책 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-response-headers-policies.html |
| CloudFront 대체 도메인 이름 (DNS 레코드, SAN) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/CNAMEs.html |
| CloudFront 인증서 요건 (us-east-1) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html |
| viewer와 CloudFront 사이 프로토콜과 cipher | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html |
| S3 Block Public Access ("public" 정의 포함) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html |
| S3 Object Ownership | https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html |
| CloudFront, S3 요금 | https://aws.amazon.com/cloudfront/pricing/ , https://aws.amazon.com/s3/pricing/ |
| Amazon EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| cfn-lint | https://github.com/aws-cloudformation/cfn-lint |

이 페이지가 설명하는 저장소 파일:

- [demo/deploy.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/deploy.sh), [demo/teardown.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/teardown.sh), [demo/infra/site.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/infra/site.yaml)
- [demo/site/index.html](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/site/index.html), [demo/site/app.js](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/site/app.js), [demo/record_local.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/record_local.py)
- [src/gpusandbox/tools.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py) (`record`), [tests/test_demo.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_demo.py)
- [k8s/trainer/job-grpo.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/job-grpo.yaml.tpl), [k8s/probe/job-probe.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/probe/job-probe.yaml.tpl)

## 10 c8i 단독 저비용 경로 (시나리오 C) { #ref-handson-10-cpu-only }

페이지: [10 c8i 단독 저비용 경로 (시나리오 C)](../handson/10_cpu_only.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 문서 | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS 문서 | What's New: EC2 nested virtualization (2026-02) | https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
| AWS 문서 | EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| AWS 문서 | Amazon EKS 요금 | https://aws.amazon.com/eks/pricing/ |
| AWS 문서 | Amazon VPC 요금 (NAT gateway) | https://aws.amazon.com/vpc/pricing/ |
| AWS 문서 | EC2 instance type quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| AWS 문서 | EKS launch template 지원 | https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html |
| GitHub | 이 저장소 | https://github.com/daekeun-ml/gpu-sandbox-on-aws |
| GitHub | reward 루프 시뮬레이터 (`simulate`) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py |
| GitHub | CDK 스택 (c8i 노드 그룹과 launch template) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py |
| GitHub | 터널 스크립트 (tunnel.sh) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/tunnel.sh |
| GitHub | gVisor | https://github.com/google/gvisor |
| GitHub | Kata Containers | https://github.com/kata-containers/kata-containers |
| GitHub | Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox |

## 11 multi-turn 에피소드 실습 { #ref-handson-11-multi-turn }

페이지: [11 multi-turn 에피소드 실습](../handson/11_multi_turn.md)

| 구분 | 주제 | URL |
|---|---|---|
| GitHub | Agent Sandbox 저장소와 릴리스 (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox , https://github.com/kubernetes-sigs/agent-sandbox/releases |
| GitHub | SandboxClaim, SandboxWarmPool 타입 (v1.0.11) | https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxclaim_types.go , https://github.com/kubernetes-sigs/agent-sandbox/blob/v1.0.11/extensions/api/v1beta1/sandboxwarmpool_types.go |
| GitHub | veRL v0.9.1 소스 트리 | https://github.com/verl-project/verl/tree/v0.9.1 |
| GitHub | veRL `ToolAgentLoop`, `BaseTool`, tool registry (v0.9.1) | https://github.com/verl-project/verl/blob/v0.9.1/verl/experimental/agent_loop/tool_agent_loop.py , https://github.com/verl-project/verl/blob/v0.9.1/verl/tools/base_tool.py , https://github.com/verl-project/verl/blob/v0.9.1/verl/tools/tool_registry.py |
| Kubernetes 문서 | 완료된 Job의 자동 삭제 (`ttlSecondsAfterFinished`) | https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/ |
| AWS 문서 | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| AWS 문서 | EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| GitHub | 이 저장소 | https://github.com/daekeun-ml/gpu-sandbox-on-aws |

이 페이지가 설명하는 저장소 파일:

- [scripts/extensions/agent_sandbox.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/extensions/agent_sandbox.sh), [scripts/lib_jobs.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib_jobs.sh)
- [k8s/extensions/agent-sandbox/job-multiturn.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/job-multiturn.yaml.tpl), [template.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/template.yaml.tpl), [trainer-claims-rbac.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/extensions/agent-sandbox/trainer-claims-rbac.yaml), [k8s/base/trainer-rbac.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/trainer-rbac.yaml)
- [src/gpusandbox/multiturn.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/multiturn.py), [src/gpusandbox/agent_sandbox.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/agent_sandbox.py), [src/gpusandbox/tools.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py), [src/gpusandbox/rewards.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py)
- [rl/verl/sandbox_tool.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/sandbox_tool.py), [rl/verl/sandbox_tool_config.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/sandbox_tool_config.yaml)
- [tests/test_multiturn.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_multiturn.py)

## 99 정리 { #ref-handson-99-cleanup }

페이지: [99 정리](../handson/99_cleanup.md)

공식 문서와 공식 저장소:

| 주제 | 링크 |
|---|---|
| Amazon EKS 클러스터 삭제 | https://docs.aws.amazon.com/eks/latest/userguide/delete-cluster.html |
| AWS CLI `update-nodegroup-config` (관리형 노드 그룹 크기 변경) | https://docs.aws.amazon.com/cli/latest/reference/eks/update-nodegroup-config.html |
| AWS CDK `cdk destroy` | https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-destroy.html |
| AWS KMS 키 삭제 (대기 기간) | https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html |
| EC2 AMI 등록 해제와 snapshot | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/deregister-ami.html |
| ECR 리포지토리 삭제 | https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-delete.html |
| S3 버킷 삭제 | https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html |
| CloudFormation stack 삭제 (`DELETE_FAILED`, 재시도) | https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-delete-stack.html |
| CloudFront 배포 삭제 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/HowToDeleteDistribution.html |
| HyperPod DeleteCluster API | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DeleteCluster.html |
| ClusterInstanceGroupSpecification (`InstanceCount` 범위) | https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ClusterInstanceGroupSpecification.html |
| Amazon EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| SageMaker AI 요금 (HyperPod) | https://aws.amazon.com/sagemaker/ai/pricing/ |
| AWS CDK 저장소 | https://github.com/aws/aws-cdk |
| HyperPod CLI와 dependency Helm chart | https://github.com/aws/sagemaker-hyperpod-cli |
| Agent Sandbox 저장소 (SandboxClaim, SandboxWarmPool, SandboxTemplate) | https://github.com/kubernetes-sigs/agent-sandbox |

이 페이지가 설명하는 저장소 파일:

- [scripts/08_cleanup.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/08_cleanup.sh)
- [scripts/hyperpod/delete.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/delete.sh)
- [demo/teardown.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/teardown.sh), [demo/infra/site.yaml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/infra/site.yaml)
- [scripts/extensions/agent_sandbox.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/extensions/agent_sandbox.sh)
- [infra/kata/build-iommu-ami.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/build-iommu-ami.sh)
- [cdk/destroy.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/destroy.sh)
- 노드 그룹 크기(min, max, desired): [cdk/gpusandbox_cdk/stack.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py)

## Production 레퍼런스 아키텍처 { #ref-production-00-architecture }

페이지: [Production 레퍼런스 아키텍처](../production/00_architecture.md)

| 주제 | 출처 |
|---|---|
| EKS 버전 지원 | [Amazon EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) |
| VPC CNI NetworkPolicy | [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
| EC2 nested virtualization | [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) |
| GPU bare metal 인스턴스 | [Accelerated computing instance types](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html) |
| HyperPod EKS 요구 사항 | [SageMaker HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html) |
| warm capacity 패턴 | [AWS China 블로그: EKS + Kata + Cloud Hypervisor](https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/) |
| Karpenter | [Karpenter 문서](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws) |
| 런타임 | [google/gvisor](https://github.com/google/gvisor), [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers) |
| NetworkPolicy agent | [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent) |
| 에피소드 단위 샌드박스 | [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) |
| 대규모 운영 사례 | [INTELLECT-3 (arXiv 2512.16144)](https://arxiv.org/abs/2512.16144) |

## 용량과 노드 관리 { #ref-production-01-capacity-and-nodes }

페이지: [용량과 노드 관리](../production/01_capacity_and_nodes.md)

| 주제 | 출처 |
|---|---|
| Karpenter 설치 | [Getting Started with Karpenter](https://karpenter.sh/docs/getting-started/getting-started-with-karpenter/) |
| NodeClass (alias 고정, amiFamily, capacity reservation) | [Karpenter NodeClasses](https://karpenter.sh/docs/concepts/nodeclasses/) |
| consolidation, drift, expiration | [Karpenter Disruption](https://karpenter.sh/docs/concepts/disruption/) |
| EC2NodeClass CRD (v1.15.2) | [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws) |
| EKS AMI ID 조회 | [Retrieve recommended Amazon Linux AMI IDs](https://docs.aws.amazon.com/eks/latest/userguide/retrieve-ami-id.html) |
| EKS AMI 릴리스 | [awslabs/amazon-eks-ami v20261107](https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107) |
| AMI 파이프라인 | [What is EC2 Image Builder](https://docs.aws.amazon.com/imagebuilder/latest/userguide/what-is-image-builder.html) |
| quota | [Amazon EC2 instance type quotas](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html) |
| Capacity Reservation | [EC2 On-Demand Capacity Reservations](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-capacity-reservations.html) |
| nested virtualization | [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) |
| nvproxy 드라이버 정책 | [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor) |
| Kata, GPU Operator | [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers), [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator) |
| warm capacity 패턴 | [AWS China 블로그: EKS + Kata + Cloud Hypervisor](https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/) |
| PDB 동작 | [Kubernetes: Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) |

## 보안 { #ref-production-02-security }

페이지: [보안](../production/02_security.md)

| 주제 | 출처 |
|---|---|
| VPC CNI NetworkPolicy (standard, strict) | [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
| IMDS 접근 차단 | [EKS Best Practices: Identity and Access Management](https://docs.aws.amazon.com/eks/latest/best-practices/identity-and-access-management.html) |
| GuardDuty | [GuardDuty Runtime Monitoring](https://docs.aws.amazon.com/guardduty/latest/ug/runtime-monitoring.html) |
| EKS isolated pods | [Sandboxing limitations (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html), [Amazon EC2 Nitro Sandboxes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html) |
| 노드 IP 예외 | [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent) |
| gVisor GPU 보안 | [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor) |
| Kata GPU passthrough | [NVIDIA GPU passthrough and Kata QEMU (4.3.1)](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md) |
| GPU Operator와 Kata | [Deploy Kata Containers (NVIDIA)](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html), [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator) |
| sandboxed pod의 GPU time-sharing | [GKE Sandbox](https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods) |
| Kubernetes 개념 | [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/), [Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/) |

## Gateway와 샌드박스 풀 { #ref-production-03-gateway-and-pools }

페이지: [Gateway와 샌드박스 풀](../production/03_gateway_and_pools.md)

| 주제 | 출처 |
|---|---|
| gateway를 쓰는 대규모 운영 사례 | [INTELLECT-3 (arXiv 2512.16144)](https://arxiv.org/abs/2512.16144) |
| VPC CNI NetworkPolicy | [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
| HyperPod에서 Ray | [Ray on SageMaker HyperPod](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html) |
| projected token, TokenReview | [Kubernetes Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/) |
| 직접 삭제와 PDB | [Kubernetes: Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) |
| trainer | [verl-project/verl](https://github.com/verl-project/verl), [huggingface/trl](https://github.com/huggingface/trl), [TRL 문서](https://huggingface.co/docs/trl) |
| 코드 | [`gateway/app.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py), [`client/pool.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/pool.py), [`gateway.yaml.tpl`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/gateway.yaml.tpl) |

## 04 Reward 무결성 { #ref-production-04-reward-integrity }

페이지: [04 Reward 무결성](../production/04_reward_integrity.md)

| 주제 | 링크 |
|---|---|
| KernelBench (MIT, 과제 계약, timing 방식, `excessive_speedup_threshold`) | https://github.com/ScalingIntelligence/KernelBench |
| KernelBench v0.1 블로그 (reward hacking 사례) | https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/ |
| Sakana AI CUDA Engineer | https://sakana.ai/ai-cuda-engineer/ |
| Kevin-32B (Cognition) | https://cognition.com/blog/kevin-32b |
| CUDA-L1 (arXiv 2507.14111) | https://arxiv.org/abs/2507.14111 |
| TRL 문서 (reward 함수, `None` 처리), GitHub | https://huggingface.co/docs/trl , https://github.com/huggingface/trl |
| veRL (custom reward function) | https://github.com/verl-project/verl |
| Triton | https://github.com/triton-lang/triton |
| EC2 가속 컴퓨팅 인스턴스 (speedup은 GPU마다 다름) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| EKS VPC CNI network policy (샌드박스 egress 차단) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| gVisor GPU 지원 (nvproxy 보안 범위) | https://gvisor.dev/docs/user_guide/gpu/ |
| harness: 부모, 자식, 측정, 정책 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/evaluate.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/runner.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/timing.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/policy.py |
| reward 변환 (TRL, veRL) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/reward_fn.py |
| golden 세트와 probe 도구 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/golden.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py |
| 로컬 테스트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_harness_cpu.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_policy.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/tests/test_routing_and_rewards.py |

## 05 샌드박스 버전 관리 { #ref-production-05-sandbox-updates }

페이지: [05 샌드박스 버전 관리](../production/05_sandbox_updates.md)

| 주제 | 링크 |
|---|---|
| ECR tag immutability | https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html |
| EKS 최적화 Amazon Linux AMI | https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html |
| EKS AMI 릴리스 v20261107 (드라이버 580.178.04) | https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107 |
| Karpenter disruption (drift, consolidation) | https://karpenter.sh/docs/concepts/disruption/ |
| Karpenter (AWS provider) | https://github.com/aws/karpenter-provider-aws |
| Kubernetes ConfigMap (subPath 마운트는 갱신 안 됨) | https://kubernetes.io/docs/concepts/configuration/configmap/ |
| gVisor GPU 지원 (nvproxy 드라이버 정책) | https://gvisor.dev/docs/user_guide/gpu/ |
| TRL GRPO | https://github.com/huggingface/trl |
| veRL | https://github.com/verl-project/verl |
| KernelBench (`excessive_speedup_threshold`) | https://github.com/ScalingIntelligence/KernelBench |
| INTELLECT-3 기술 보고서 (environment 버전 관리) | https://arxiv.org/abs/2512.16144 |
| Prime Intellect verifiers (Environments Hub 연동) | https://github.com/PrimeIntellect-ai/verifiers |
| 롤아웃 스크립트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/rollout.sh |
| probe, parity 도구 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tools.py |
| golden 세트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/golden.py |
| gateway (group 고정) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py |
| 버전 파일 v1, v2 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/sandbox/versions |

## 06 veRL로 확장 { #ref-production-06-scaling-with-verl }

페이지: [06 veRL로 확장](../production/06_scaling_with_verl.md)

| 주제 | 링크 |
|---|---|
| Ray on SageMaker HyperPod | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html |
| HyperPod EKS에 KubeRay 설치 | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray-install-kuberay.html |
| HyperPod 자동 노드 복구 | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-node-recovery.html |
| EKS에서 FSx for Lustre 사용 | https://docs.aws.amazon.com/eks/latest/userguide/fsx-csi.html |
| EC2 가속 컴퓨팅 인스턴스 사양 | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| Ray on EKS (GPU 클러스터, Ray 문서) | https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/aws-eks-gpu-cluster.html |
| KubeRay v1.7.2 | https://github.com/kuberay-project/kuberay/releases/tag/v1.7.2 |
| veRL | https://github.com/verl-project/verl |
| veRL 0.9.1 reward config | https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/reward/reward.yaml |
| AWS veRL 샘플 (v0.6.1) | https://github.com/awslabs/awsome-distributed-ai/tree/main/examples/training/verl/hyperpod-eks/rlvr |
| FSx for Lustre CSI driver | https://github.com/kubernetes-sigs/aws-fsx-csi-driver |
| Qwen2.5-Coder-7B-Instruct (Apache-2.0) | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct |
| veRL 이미지 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/Dockerfile |
| reward 함수 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/reward_fn.py |
| 데이터 준비 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/prepare_data.py |
| 제출 스크립트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/run_grpo_kernels.sh |
| RayCluster 템플릿 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/raycluster-verl.yaml.tpl |

## 07 Observability와 운영 { #ref-production-07-observability-and-operations }

페이지: [07 Observability와 운영](../production/07_observability_and_operations.md)

| 주제 | 링크 |
|---|---|
| CloudWatch Container Insights | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html |
| Container Insights Prometheus 모니터링 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights-Prometheus.html |
| Amazon Managed Service for Prometheus | https://docs.aws.amazon.com/prometheus/latest/userguide/what-is-Amazon-Managed-Service-Prometheus.html |
| EKS NetworkPolicy 설정 (VPC CNI) | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| HyperPod training operator (hang 감지, 재시작) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
| HyperPod EKS 복원력 기능 | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html |
| VPC CNI network policy agent (노드 IP 허용 동작) | https://github.com/aws/aws-network-policy-agent |
| Prometheus Python client | https://github.com/prometheus/client_python |
| gVisor GPU 지원 (nvproxy) | https://gvisor.dev/docs/user_guide/gpu/ |
| Kata NVIDIA GPU passthrough (4.3.1) | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md |
| 샌드박스 서버 지표 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py |
| gateway 지표와 인증 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py |
| trainer 이벤트 (`reward_batch`) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py |
| JWKS 동기화 CronJob | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/jwks-sync.yaml.tpl |
| HyperPod job 로그 패턴 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl |

## 08 비용 { #ref-production-08-cost }

페이지: [08 비용](../production/08_cost.md)

| 주제 | 링크 |
|---|---|
| EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| SageMaker AI 요금 (HyperPod `ml.*`) | https://aws.amazon.com/sagemaker/ai/pricing/ |
| EKS 요금 (control plane) | https://aws.amazon.com/eks/pricing/ |
| VPC 요금 (NAT gateway) | https://aws.amazon.com/vpc/pricing/ |
| EC2 인스턴스 유형 한도 (On-Demand vCPU 한도) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
| EC2 가속 컴퓨팅 인스턴스 사양 | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
| HyperPod EKS 사전 요구 사항 | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html |
| HyperPod 자동 노드 복구 | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-node-recovery.html |
| Karpenter disruption (consolidation) | https://karpenter.sh/docs/concepts/disruption/ |
| Karpenter (AWS provider) | https://github.com/aws/karpenter-provider-aws |
| HyperPod CLI와 의존성 Helm chart | https://github.com/aws/sagemaker-hyperpod-cli |
| NodePool 설정 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/karpenter/nodepools.yaml |
| warm placeholder | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/warm-capacity.yaml |
| 풀 한도 (PriorityClass, PDB, ResourceQuota) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/production/pool-hardening.yaml |
| 정리 스크립트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/08_cleanup.sh |

## 09 CDK로 프로비저닝하고 삭제하기 { #ref-production-09-cdk }

페이지: [09 CDK로 프로비저닝하고 삭제하기](../production/09_cdk.md)

| 구분 | 주제 | URL |
|---|---|---|
| AWS 문서 | AWS CDK v2 개발자 가이드 | https://docs.aws.amazon.com/cdk/v2/guide/home.html |
| AWS 문서 | CDK bootstrapping | https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html |
| AWS 문서 | EKS cluster endpoint access | https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html |
| AWS 문서 | EKS access entries | https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html |
| AWS 문서 | Session Manager 세션 시작 (포트 포워딩) | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html |
| AWS 문서 | Security Hub EKS 컨트롤 | https://docs.aws.amazon.com/securityhub/latest/userguide/eks-controls.html |
| AWS 문서 | eksctl 클러스터 접근 (private 전용 생성 미지원) | https://docs.aws.amazon.com/eks/latest/eksctl/vpc-cluster-access.html |
| GitHub | 이 저장소의 CDK 앱 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/cdk |
| GitHub | AWS CDK | https://github.com/aws/aws-cdk |
| GitHub | cdk-nag | https://github.com/cdklabs/cdk-nag |

## 용어 사전 { #ref-reference-glossary }

페이지: [용어 사전](glossary.md)

**AWS 문서**

- [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html)
- [Accelerated computing instance types](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html)
- [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [SageMaker HyperPod EKS 사전 요구사항](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)
- [CloudFront: Restrict access to an Amazon S3 origin (OAC)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [CloudFront: Understand response headers policies (CSP, HSTS)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-response-headers-policies.html)

**GitHub와 프로젝트 문서**

- [gVisor GPU 지원](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor)
- [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md), [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers)
- [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)
- [Karpenter 문서](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws)
- [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin), [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent)
- [aws/sagemaker-hyperpod-cli](https://github.com/aws/sagemaker-hyperpod-cli)
- [TRL 문서](https://huggingface.co/docs/trl), [huggingface/trl](https://github.com/huggingface/trl), [verl-project/verl](https://github.com/verl-project/verl)
- [ScalingIntelligence/KernelBench](https://github.com/ScalingIntelligence/KernelBench)
- [Kubernetes: Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/), [Kubernetes: Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)

## 저장소 구조 { #ref-reference-repository-map }

페이지: [저장소 구조](repository_map.md)

**AWS 문서**

- [Amazon EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)
- [Amazon VPC CNI network policy 설정](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html)
- [SageMaker HyperPod EKS 사전 요구사항](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)

**GitHub와 프로젝트 문서**

- [AWS CDK v2 개발자 가이드](https://docs.aws.amazon.com/cdk/v2/guide/home.html), [aws/aws-cdk](https://github.com/aws/aws-cdk), [cdklabs/cdk-nag](https://github.com/cdklabs/cdk-nag)
- [awslabs/amazon-eks-ami v20261107](https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107)
- [Karpenter 문서](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws)
- [gVisor 설치](https://gvisor.dev/docs/user_guide/install/), [google/gvisor](https://github.com/google/gvisor)
- [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md)
- [NVIDIA GPU Operator with Kata](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html), [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator), [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [aws/sagemaker-hyperpod-cli](https://github.com/aws/sagemaker-hyperpod-cli)

**이 저장소**

- [daekeun-ml/gpu-sandbox-on-aws](https://github.com/daekeun-ml/gpu-sandbox-on-aws): [scripts/render.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/render.py), [scripts/lib.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib.sh), [k8s/sandbox/deployment.yaml.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/deployment.yaml.tpl), [pyproject.toml](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/pyproject.toml)

## 설정 값 { #ref-reference-configuration }

페이지: [설정 값](configuration.md)

**AWS 문서**

- [Amazon EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)
- [Amazon VPC CNI network policy 설정](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [SageMaker HyperPod EKS 사전 요구사항](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)
- [SageMaker HyperPod IAM 사전 요구사항](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html)

**GitHub와 프로젝트 문서**

- [TRL 문서](https://huggingface.co/docs/trl), [huggingface/trl](https://github.com/huggingface/trl)
- [gVisor GPU 지원](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor)
- [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md)
- [aws/sagemaker-hyperpod-cli](https://github.com/aws/sagemaker-hyperpod-cli)

**이 저장소의 해당 파일**

- [src/gpusandbox/server/app.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py), [src/gpusandbox/auth.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/auth.py), [src/gpusandbox/harness/evaluate.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/evaluate.py)
- [src/gpusandbox/client/routing.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/routing.py), [src/gpusandbox/client/pool.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/pool.py), [src/gpusandbox/gateway/app.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py)
- [rl/trl/train_grpo.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/trl/train_grpo.py), [scripts/config.env.example](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/config.env.example), [cdk/gpusandbox_cdk/config.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/config.py), [k8s/sandbox/profiles](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/sandbox/profiles), [k8s/sandbox/versions](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/sandbox/versions), [k8s/base/routing.json.tpl](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/base/routing.json.tpl)

## 문제 해결 { #ref-reference-troubleshooting }

페이지: [문제 해결](troubleshooting.md)

**AWS 문서**

- [Amazon VPC CNI network policy 설정](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html)
- [Amazon EC2 가속 컴퓨팅 인스턴스 유형](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html)
- [SageMaker HyperPod EKS 사전 요구사항](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)
- [SageMaker HyperPod 자동 노드 복구](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-node-recovery.html), [deep health checks](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html)

**GitHub와 프로젝트 문서**

- [gVisor GPU 지원](https://gvisor.dev/docs/user_guide/gpu/), [gVisor 설치](https://gvisor.dev/docs/user_guide/install/), [google/gvisor](https://github.com/google/gvisor)
- [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md), [Kata issue #11687](https://github.com/kata-containers/kata-containers/issues/11687)
- [NVIDIA GPU Operator with Kata](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html), [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent), [awslabs/amazon-eks-ami v20261107](https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107)
- [CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping-env.html), [cdklabs/cdk-nag](https://github.com/cdklabs/cdk-nag), [TRL 문서](https://huggingface.co/docs/trl)

**이 저장소의 해당 파일**

- [scripts/ops/verify.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/verify.sh), [scripts/lib_jobs.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib_jobs.sh), [scripts/kata/gpu_nodes.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/kata/gpu_nodes.sh)
- [src/gpusandbox/server/app.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py), [src/gpusandbox/auth.py](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/auth.py), [infra/eks/node-guard.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/eks/node-guard.sh)

## 자주 하는 오해 { #ref-reference-faq }

페이지: [자주 하는 오해](faq.md)

| 주제 | 링크 |
|---|---|
| EC2 nested virtualization (User Guide, What's New) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html , https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
| EC2 가속 컴퓨팅 인스턴스 (`g4dn.metal`, `g5g.metal`) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
| AWS Nitro Sandboxes, EKS sandboxing 제한 | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
| EKS Auto Mode managed instances | https://docs.aws.amazon.com/eks/latest/userguide/automode-learn-instances.html |
| Amazon Bedrock AgentCore Code Interpreter | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html |
| HyperPod EKS 사전 요구사항, AMI 릴리스 노트 (Kubernetes 버전별 드라이버) | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-release-ami-eks.html |
| VPC CNI network policy | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
| aws-network-policy-agent (노드 IP 허용) | https://github.com/aws/aws-network-policy-agent |
| gVisor GPU 지원 (nvproxy, 보안 범위) | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
| GKE Sandbox (GPU time-sharing 권고) | https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods |
| Kata 4.3.1 NVIDIA GPU passthrough, hypervisor 지원 표, issue #11687 | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md , https://github.com/kata-containers/kata-containers/issues/11687 |
| NVIDIA GPU Operator with Kata (검증 범위) | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html |
| Firecracker FAQ, CHANGELOG | https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md , https://github.com/firecracker-microvm/firecracker/blob/main/CHANGELOG.md |
| kubernetes-sigs/agent-sandbox | https://github.com/kubernetes-sigs/agent-sandbox |
| AWS 기술 블로그 "AWS에서 AI 에이전트 실행 환경 격리하기" 1부, 2부 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ , https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
| Qwen2.5-Coder 모델 카드 (라이선스) | https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct , https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct , https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct |
| TRL 문서 (reward 함수의 `None`) | https://huggingface.co/docs/trl |
| 이 저장소: 검증 스크립트, 롤아웃, HyperPod 점검, 정책 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/verify.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/rollout.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/policy.py |
