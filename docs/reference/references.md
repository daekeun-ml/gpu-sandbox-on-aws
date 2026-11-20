# 참고 자료 모음

가이드에서 공통으로 쓰는 자료를 주제별로 모았습니다. 문서 속 수치와 AWS 실행 기록의 근거는 [검증된 사실과 출처](sources.md)에서 확인할 수 있습니다.

<span id="ref-beginner-02-container-vs-sandbox"></span>
<span id="ref-beginner-03-gpu-sandbox"></span>
<span id="ref-concepts-01-why-gpu-sandbox"></span>
<span id="ref-concepts-02-isolation-runtimes"></span>
<span id="ref-concepts-05-decision-guide"></span>
<span id="ref-handson-02-gvisor"></span>
<span id="ref-handson-03-kata"></span>

## 격리 런타임 { #runtimes }

- pod의 런타임 지정 방식. [Kubernetes RuntimeClass](https://kubernetes.io/docs/concepts/containers/runtime-class/)
- nvproxy가 지원하는 드라이버와 GPU. [gVisor GPU 지원](https://gvisor.dev/docs/user_guide/gpu/)
- QEMU와 Cloud Hypervisor의 기능 차이. [Kata hypervisor 지원 표](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md)
- Kata CPU에 쓸 수 있는 인스턴스 조건. [EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html)

<span id="ref-beginner-05-hands-on"></span>
<span id="ref-concepts-04-platforms-and-instances"></span>
<span id="ref-getting-started"></span>
<span id="ref-handson-00-overview"></span>
<span id="ref-handson-01-cluster-and-images"></span>
<span id="ref-handson-07-hyperpod"></span>
<span id="ref-handson-09-demo-site"></span>
<span id="ref-handson-10-cpu-only"></span>
<span id="ref-handson-99-cleanup"></span>
<span id="ref-production-00-architecture"></span>
<span id="ref-production-01-capacity-and-nodes"></span>
<span id="ref-production-07-observability-and-operations"></span>
<span id="ref-production-08-cost"></span>
<span id="ref-production-09-cdk"></span>
<span id="ref-reference-glossary"></span>
<span id="ref-reference-repository-map"></span>
<span id="ref-reference-configuration"></span>
<span id="ref-reference-troubleshooting"></span>
<span id="ref-reference-faq"></span>

## AWS 배포와 운영 { #aws }

- private 클러스터 접속 조건. [EKS API endpoint](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)
- 스택 준비, 배포, 삭제. [AWS CDK v2](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- 권한과 클러스터 준비 조건. [HyperPod EKS 사전 요구 사항](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)
- 학습 Job과 재시작 설정. [HyperPod training operator](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html)
- NodePool과 노드 회수. [Karpenter](https://karpenter.sh/docs/)
- 노드 비용 계산에 쓰는 단가. [EC2 On-Demand 요금](https://aws.amazon.com/ec2/pricing/on-demand/)

<span id="ref-beginner-01-why-sandbox"></span>
<span id="ref-beginner-06-multi-turn-agent"></span>
<span id="ref-concepts-06-agent-sandbox"></span>
<span id="ref-handson-04-sandbox-pools"></span>
<span id="ref-handson-11-multi-turn"></span>
<span id="ref-production-02-security"></span>
<span id="ref-production-03-gateway-and-pools"></span>

## 접근 제어와 에피소드 { #security-agents }

- VPC CNI의 네트워크 정책 활성화. [EKS NetworkPolicy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- 노드 자격 증명과 pod 권한. [EKS IAM 모범 사례](https://docs.aws.amazon.com/eks/latest/best-practices/identity-and-access-management.html)
- SandboxClaim과 warm pool. [Kubernetes Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox)

## AWS 기술 블로그 { #aws-technical-blogs }

**AWS에서 AI 에이전트 실행 환경 격리하기**는 EKS 기반 구성과 운영 사례에서 관리형 샌드박스 선택까지 이어지는 한국어 시리즈입니다.

- EKS와 Agent Sandbox의 격리 구조, pod와 노드에서 적용할 통제. [1부: EKS와 Agent Sandbox의 개념과 구성](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/)
- NetworkPolicy, sandbox-router 인가, warm pool 동작을 확인한 실험. [2부: 네트워크, 인가, warm pool 검증](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/)
- 프로젝트별 샌드박스와 전용 NodePool을 운영한 사례. [3부: 에이블리의 EKS 기반 운영 사례](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/)
- 관리형 실행 환경의 격리 방식, 수명 주기, 선택 기준. [4부: Amazon Bedrock AgentCore Runtime](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-4/)
- EKS에서 Kata로 VM 단위 격리를 적용하는 방법. [Kata Containers를 활용한 워크로드 격리](https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/)

<span id="ref-beginner-04-rl-and-sandbox"></span>
<span id="ref-concepts-03-onpolicy-rl-with-sandboxes"></span>
<span id="ref-handson-05-grpo-training"></span>
<span id="ref-handson-06-sandbox-update"></span>
<span id="ref-handson-08-benchmark"></span>
<span id="ref-production-04-reward-integrity"></span>
<span id="ref-production-05-sandbox-updates"></span>
<span id="ref-production-06-scaling-with-verl"></span>

## 학습과 채점 { #training }

- 생성, reward, optimizer 설정. [TRL GRPOTrainer](https://huggingface.co/docs/trl/main/en/grpo_trainer)
- 분산 RL 학습과 reward 연동. [veRL](https://github.com/verl-project/verl)
- GPU 커널 과제와 성능 평가. [KernelBench](https://arxiv.org/abs/2502.10517)
- 측정 과정에서 관찰한 reward hacking 사례. [KernelBench v0.1](https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/)
