# 용어 사전

!!! info "TL;DR"
    이 가이드북에 나오는 격리 런타임, Kubernetes와 AWS 인프라, RL 용어를 한두 문장으로 정의하고, 그 용어를 자세히 다루는 페이지를 링크합니다.

## 기존 Pain Point

격리 런타임(gVisor, Kata), Kubernetes와 AWS 인프라, on-policy RL 용어가 한 페이지 안에 섞여 나옵니다. "rollout"과 "warm"처럼 문맥마다 뜻이 다른 단어도 있습니다(아래 ❓ 오해 노트). 정의는 용어를 처음 설명한 페이지에 흩어져 있어서, 뜻을 알려면 그 페이지를 찾아가야 합니다.

## Why

- **rollout은 문맥에 따라 뜻이 다릅니다.** RL에서는 policy가 completion을 생성하는 단계이고, Kubernetes에서는 Deployment를 새 버전으로 바꾸는 일입니다.
- **warm도 두 가지입니다.** Production의 warm placeholder는 GPU를 요청하지 않고, Agent Sandbox의 SandboxWarmPool은 GPU 프로필로 만들면 대기 중에도 GPU를 점유합니다.

**사전 지식:** 없습니다. 항목은 영어 용어의 알파벳순이고, 항목 끝의 "쓰는 곳"이 그 용어를 자세히 다루는 페이지입니다.

## A

**Advantage**
:   GRPO에서 completion 하나가 같은 group의 다른 completion보다 얼마나 나은지를 나타내는 값입니다. policy는 advantage가 양수인 completion을 더 자주 생성하고 음수인 completion을 덜 생성하도록 업데이트됩니다. 계산 방식은 아래 Group-relative advantage 항목을 보세요. 쓰는 곳: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

**Agent Sandbox (kubernetes-sigs/agent-sandbox)**
:   샌드박스 pod를 미리 생성하고, 요청에 할당하고, 사용이 끝나면 회수하는 작업을 Kubernetes CRD로 관리하는 오픈소스 sandbox orchestrator입니다. 격리 자체는 pod의 RuntimeClass(gVisor, Kata 등)에 맡깁니다. 최신 릴리스는 v1.0.11이고 CRD는 v1beta1입니다. 쓰는 곳: [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

**Audience (`aud`)**
:   토큰을 받을 대상(수신자)을 지정한 claim입니다. 이 저장소는 샌드박스용 `gpu-sandbox`와 gateway용 `gpu-sandbox-gateway`를 구분해, 한쪽용 토큰을 다른 쪽에서 사용할 수 없게 합니다. 쓰는 곳: [02 보안](../production/02_security.md)

**AWS CDK, cdk-nag**
:   AWS CDK는 코드(여기서는 Python)로 AWS 인프라를 정의하고 CloudFormation 스택으로 배포하는 도구이고, cdk-nag는 그 코드를 AWS 모범 사례 규칙으로 검사하는 오픈소스 도구입니다. 이 저장소는 VPC, EKS 클러스터, 노드 그룹을 CDK 스택 하나로 만듭니다(`scripts/02_create_cluster.sh`가 `cdk/deploy.sh`를 호출). synth할 때마다 cdk-nag가 실행되고, 이유를 적어 예외 처리하지 않은 지적이 있으면 배포가 중단됩니다. 쓰는 곳: [09 CDK로 프로비저닝](../production/09_cdk.md)

## B

**Bare metal (`.metal`)**
:   가상 머신이 아니라 물리 서버 전체를 직접 사용하는 EC2 인스턴스입니다. 호스트가 `/dev/kvm`과 IOMMU, 물리 GPU를 직접 쓸 수 있으므로 Kata GPU passthrough에 필요합니다. NVIDIA GPU가 달린 EC2 bare metal은 `g4dn.metal`과 `g5g.metal`(arm64)뿐입니다. 쓰는 곳: [04 플랫폼과 인스턴스 선택](../concepts/04_platforms_and_instances.md)

**Blue/green**
:   기존 버전(blue)을 그대로 둔 채 새 버전(green)을 별도로 배포하고, 검증이 끝나면 트래픽을 한 번에 전환하는 배포 방식입니다. 이 저장소는 (runtime, version)마다 Deployment를 따로 두고 routing ConfigMap으로 전환합니다. 쓰는 곳: [05 샌드박스 버전 관리](../production/05_sandbox_updates.md)

## C

**CDI (Container Device Interface)**
:   컨테이너에 어떤 장치 파일과 라이브러리를 넣을지 기술하는 표준 형식입니다. 이 저장소는 NVIDIA device plugin을 `deviceListStrategy: cdi-cri`로 설치하고, gVisor(runsc)는 CDI로 전달된 GPU 장치를 그대로 씁니다. 쓰는 곳: [02 gVisor GPU 샌드박스](../handson/02_gvisor.md)

**Checksum**
:   데이터 내용으로 계산한 짧은 값으로, 두 데이터의 내용이 같은지 비교하는 데 씁니다. harness는 타이밍 반복마다 후보 출력의 checksum을 레퍼런스와 비교해서, 측정 구간에서만 틀리는 출력("벤치마크 때만 틀리기")을 검출합니다. 쓰는 곳: [04 Reward 무결성](../production/04_reward_integrity.md)

**Cloud Hypervisor (CLH)**
:   Kata가 쓸 수 있는 가벼운 하이퍼바이저입니다. 이 저장소는 장치가 없는 Kata CPU 풀에 씁니다. Kata upstream은 CLH의 GPU passthrough를 지원하지 않습니다.

    - **CPU 풀을 만들 때**: 배포 스크립트에 넘기는 프로필은 `kata-clh-cpu`입니다. v1 Deployment 이름은 `sandbox-kata-clh-cpu-v1`이고, 프로필이 지정하는 RuntimeClass는 `kata-clh`입니다.
    - **배포 스크립트에 `kata-clh`를 줄 때**: 실험용 GPU 프로필이 선택됩니다.

    쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

**Completion**
:   RL에서 모델이 prompt 하나를 받아 생성한 답입니다. 이 저장소의 GRPO는 prompt마다 completion 8개(group 하나)를 생성하고, completion 안의 코드 블록을 샌드박스에서 채점합니다. 쓰는 곳: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

**Consolidation**
:   Karpenter가 비어 있거나 사용률이 낮은 노드를 회수하는 동작입니다. 이 저장소의 GPU NodePool은 빈 노드만 회수하는 `WhenEmpty`를 써서, 평가 중인 샌드박스 pod를 다른 노드로 옮기지 않습니다. 쓰는 곳: [01 용량과 노드 관리](../production/01_capacity_and_nodes.md)

**containerd shim**
:   containerd가 pod(샌드박스)마다 실행하는 작은 중개 프로세스로, 특정 런타임에 명령을 전달합니다. gVisor는 `containerd-shim-runsc-v1`을 쓰고, Kata는 Go shim이나 runtime-rs shim을 씁니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

**CSP (Content-Security-Policy)**
:   브라우저가 페이지에서 불러와도 되는 스크립트와 리소스의 출처를 제한하는 HTTP 응답 헤더입니다. 데모 사이트는 CloudFront response headers policy로 엄격한 CSP와 HSTS 등 보안 헤더를 붙입니다. 쓰는 곳: [09 데모 사이트 (CloudFront)](../handson/09_demo_site.md)

## D

**Deep health check**
:   SageMaker HyperPod가 GPU 인스턴스의 결함을 찾으려고 실행하는 검사(InstanceStress, InstanceConnectivity)입니다. 검사하는 동안 노드에 taint가 붙고, 이 검사를 켠 인스턴스 그룹의 노드에는 사용자 taint를 붙일 수 없습니다. 쓰는 곳: [07 HyperPod 시나리오](../handson/07_hyperpod.md)

**Device plugin**
:   노드의 장치(GPU 등)를 `nvidia.com/gpu` 같은 리소스 이름으로 kubelet에 알리는 Kubernetes 구성 요소입니다. pod가 이 리소스를 요청하면 scheduler가 장치가 남은 노드에 배치합니다. Kata passthrough용 GPU는 GPU Operator가 `nvidia.com/pgpu`로 광고합니다. 쓰는 곳: [02 gVisor GPU 샌드박스](../handson/02_gvisor.md)

**Draining, recycling**
:   draining은 샌드박스가 정해진 평가 횟수(`SANDBOX_MAX_EVALS`)를 채우거나 GPU 오류를 낸 뒤 Ready 상태에서 제외된 상태입니다. recycling은 gateway가 그 pod를 지워 Deployment가 새 pod를 만들게 하는 동작이고, Kata에서는 새 pod마다 새 VM이 만들어집니다. 쓰는 곳: [03 Gateway와 샌드박스 풀](../production/03_gateway_and_pools.md)

**Drift**
:   Karpenter가 NodePool이나 EC2NodeClass 설정(예: AMI)과 달라진 노드를 찾아 교체하는 동작입니다. 쓰는 곳: [01 용량과 노드 관리](../production/01_capacity_and_nodes.md)

## E

**EC2NodeClass**
:   K의 Karpenter NodePool, EC2NodeClass 항목을 보세요.

**Episode (에피소드)**
:   agentic RL에서 모델이 과제 하나를 여러 turn에 걸쳐 푸는 한 번의 시도입니다. 이 저장소의 Agent Sandbox 확장은 에피소드마다 SandboxClaim 하나로 샌드박스 하나를 할당하고, 에피소드가 끝나면 claim을 삭제해 샌드박스를 반납합니다. 쓰는 곳: [06 multi-turn 에이전트와 Agent Sandbox](../beginner/06_multi_turn_agent.md), [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

## F

**Fail closed**
:   설정이 빠지거나 검증할 수 없을 때 허용하지 않고 거부하는 동작입니다. 샌드박스 서버는 audience, issuer, allowlist, JWKS 중 하나라도 없으면 보호된 경로를 모두 401로 거부합니다. 쓰는 곳: [02 보안](../production/02_security.md)

## G

**Golden submission (golden 제출물)**
:   verdict를 미리 아는 후보 코드입니다. 이 저장소의 golden 세트는 6개(Triton 정답 2개, torch 전용 정답, 오답, 벤치마크 치팅, 호스트 파일 읽기)입니다. 샌드박스가 정상인지, 새 버전이 구버전과 같은 verdict를 내는지 확인하는 기준으로 씁니다. 쓰는 곳: [05 샌드박스 버전 관리](../production/05_sandbox_updates.md)

**GPU passthrough**
:   물리 GPU를 VFIO로 VM에 직접 할당해, VM 안의 드라이버가 GPU를 직접 다루게 하는 방식입니다. 호스트가 IOMMU와 물리 GPU를 직접 쓸 수 있어야 해서 이 저장소의 x86 구성은 AWS에서 `g4dn.metal`이 필요합니다. Kata에서는 QEMU의 cold-plug 방식만 공식 지원됩니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

**Group (GRPO group)**
:   GRPO에서 prompt 하나로 생성한 completion 묶음입니다(이 저장소는 8개). advantage를 group 안에서 상대적으로 계산하므로, 한 group은 하나의 샌드박스 버전으로 채점해야 합니다. 노드 그룹이나 HyperPod 인스턴스 그룹과는 다른 뜻입니다. 쓰는 곳: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

**Group pin (`group_key`)**
:   gateway가 같은 `group_key`(GRPO group 하나)의 샘플을 첫 샘플을 받을 때 정한 routing snapshot으로 계속 채점하도록 고정하는 기능입니다. 기본 TTL은 900초입니다. 고정 정보는 gateway 메모리에만 저장되므로 gateway가 재시작하면 사라집니다. 쓰는 곳: [03 Gateway와 샌드박스 풀](../production/03_gateway_and_pools.md)

**Group-relative advantage**
:   GRPO의 advantage 계산 방식입니다. 같은 prompt에서 나온 completion들의 reward를 group 평균과 표준편차로 정규화하므로(TRL 기본 `scale_rewards="group"`), group 안에서 다른 completion과 비교한 reward가 학습 신호가 됩니다. 그래서 한 group은 하나의 샌드박스 버전으로 채점해야 합니다. 쓰는 곳: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

**GRPO (Group Relative Policy Optimization)**
:   prompt 하나에서 completion 여러 개(group, 이 저장소는 8개)를 생성해 채점하고, group 안에서 reward가 상대적으로 높은 completion의 생성 확률을 높이는 RL 알고리즘입니다. 이 저장소는 TRL(핸즈온)과 veRL(Production)의 GRPO를 씁니다. 쓰는 곳: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

**gVisor**
:   컨테이너에 직접 노출되는 호스트 커널의 범위를 줄이는 격리 런타임입니다. 사용자 공간 커널(Sentry)이 system call을 대신 받아 처리합니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

**gVisor Sentry**
:   gVisor의 사용자 공간 커널입니다. 컨테이너가 호출하는 system call을 호스트 커널 대신 받아 처리하고, VM 위에서는 systrap platform으로 동작합니다. 그래서 샌드박스 안에서 `uname -r`을 실행하면 노드와 다른 값이 나옵니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

## H

**Harness**
:   후보 코드를 실행하고 정답 여부와 속도를 측정해서 verdict를 내는 평가 코드입니다. 이 저장소의 harness는 신뢰하는 부모 프로세스(정책 검사, 레퍼런스, 타이밍, verdict)와 신뢰하지 않는 자식 프로세스(후보 실행)로 나뉩니다. 쓰는 곳: [04 Reward 무결성](../production/04_reward_integrity.md)

**Headless Service**
:   가상 IP 없이(`clusterIP: None`) DNS 조회에 Ready 상태인 pod의 IP 목록을 그대로 반환하는 Kubernetes Service입니다. 클라이언트나 gateway가 pod를 직접 선택해 pod마다 평가를 하나씩 보낼 수 있습니다. 쓰는 곳: [04 샌드박스 풀 배포와 검증](../handson/04_sandbox_pools.md)

**HyperPod instance group**
:   SageMaker HyperPod 클러스터 안에서 같은 인스턴스 유형과 설정을 공유하는 노드 묶음입니다. 이 저장소의 시나리오 B는 trainer를 `ml.g5.2xlarge` 인스턴스 그룹에 두고, 그 노드를 샌드박스와 같은 EKS 클러스터에 연결합니다. 쓰는 곳: [07 HyperPod 시나리오](../handson/07_hyperpod.md)

**HyperPodPyTorchJob**
:   HyperPod training operator add-on이 제공하는 학습 job 리소스입니다. `hyperpodrun` 런처로 시작하고, `jobMaxRetryCount`에 따른 재시작과 로그 패턴 기반 정지 감지(`logMonitoringConfiguration`)를 지원합니다. 쓰는 곳: [07 HyperPod 시나리오](../handson/07_hyperpod.md)

## I

**IMDS (Instance Metadata Service)**
:   EC2 인스턴스 안에서 `169.254.169.254`로 접근하는 메타데이터 서비스입니다. 노드 IAM role의 임시 자격 증명도 IMDS에서 받으므로, 이 저장소는 hop limit 1과 egress 차단으로 샌드박스 pod가 IMDS에 접근하지 못하게 합니다. 쓰는 곳: [02 보안](../production/02_security.md)

**ioctl**
:   프로그램이 장치 드라이버에 장치별 명령을 보내는 system call입니다. GPU 작업도 NVIDIA 장치 파일에 대한 ioctl로 드라이버에 전달되고, gVisor nvproxy는 이 ioctl을 허용 목록으로 필터링합니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

**IOMMU**
:   장치가 DMA로 접근할 수 있는 메모리 범위를 제한하는 하드웨어입니다. VFIO passthrough에서 GPU의 메모리 접근을 VM 안으로 제한합니다. AL2023 커널에서는 `intel_iommu=on` 커널 인자가 있어야 켜집니다. 쓰는 곳: [03 Kata 샌드박스 (CLH, QEMU)](../handson/03_kata.md)

## J

**JWKS (JSON Web Key Set)**
:   토큰 서명을 검증하는 데 쓰는 공개 키 집합입니다. 클러스터의 ServiceAccount issuer가 `/openid/v1/jwks`로 제공하고, 이 저장소는 그 값을 ConfigMap `sandbox-auth-jwks`에 복사해 샌드박스가 API 접근 없이 토큰을 검증하게 합니다. 공개 키라서 비밀 값이 아닙니다. 쓰는 곳: [02 보안](../production/02_security.md)

## K

**Karpenter NodePool, EC2NodeClass**
:   Karpenter는 pod 수요에 맞춰 EC2 노드를 생성하고 필요 없어진 노드를 회수하는 Kubernetes 노드 autoscaler입니다. NodePool은 생성할 노드의 조건(인스턴스 유형, taint, label, 상한, 회수 정책)이고, EC2NodeClass는 AWS 쪽 실행 설정(AMI, subnet, security group, 디스크, user data, nested virtualization)입니다. 쓰는 곳: [01 용량과 노드 관리](../production/01_capacity_and_nodes.md)

**Kata Containers**
:   pod마다 경량 VM을 실행하고 그 VM 안에서 컨테이너를 실행하는 런타임입니다. 하이퍼바이저로 QEMU나 Cloud Hypervisor를 쓰고, pod마다 별도의 guest 커널을 씁니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

**KernelBench**
:   GPU 커널을 작성하는 능력을 측정하는 공개 벤치마크(MIT 라이선스)입니다. 이 저장소는 과제 형식(`Model`, `ModelNew`), 정확성 허용 오차, 타이밍 방식, `excessive_speedup_threshold` 10을 참고합니다. 쓰는 곳: [01 GPU 샌드박스가 필요한 경우](../concepts/01_why_gpu_sandbox.md)

**KL penalty (`beta`)**
:   학습 중인 policy가 reference model과 크게 달라지지 않도록 loss에 더하는 KL divergence 항과 그 계수입니다. TRL 1.18.0 GRPO의 기본값은 `beta` 0.0이라 KL 항이 없고 reference model도 메모리에 로드하지 않습니다. 이 저장소는 이 기본값을 그대로 씁니다. 쓰는 곳: [05 On-policy GRPO 학습](../handson/05_grpo_training.md)

**KVM**
:   Linux 커널에 들어 있는 하드웨어 가상화 기능으로, `/dev/kvm` 장치를 통해 씁니다. Kata의 QEMU와 Cloud Hypervisor가 KVM을 사용해 VM을 실행하므로, Kata 노드에는 `/dev/kvm`이 있어야 합니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

## L

**Lifecycle script**
:   HyperPod가 노드를 만들 때 S3에서 내려받아 실행하는 설정 스크립트입니다. 이 저장소의 trainer 그룹용 `infra/hyperpod/lifecycle/on_create.sh`는 아무것도 설치하지 않고, B2의 sandbox 그룹용 `on_create_sandbox.sh`는 드라이버를 확인한 뒤 `runsc` 등록과 node guard를 설치합니다. 버킷 이름은 `sagemaker-` 접두사를 유지합니다. 쓰는 곳: [07 HyperPod 시나리오](../handson/07_hyperpod.md)

**LoRA**
:   모델 가중치 전체 대신 작은 저랭크(low-rank) 행렬만 학습하는 미세 조정 방식입니다. 학습할 파라미터와 optimizer 상태가 줄어들어, 핸즈온은 A10G 한 장에서 1.5B 모델을 학습하도록 설정되어 있습니다. 기본값은 `r` 32, `lora_alpha` 64, 모든 linear 층입니다. 쓰는 곳: [05 On-policy GRPO 학습](../handson/05_grpo_training.md)

## M

**Multi-turn**
:   모델이 도구를 호출하거나 코드를 제출하고, 결과를 읽은 뒤 다시 응답하는 과정을 여러 번 반복하는 방식입니다. completion마다 따로 채점하고 그 결과로 다시 응답하지 않는 single-turn 채점과 구분합니다. 이 저장소의 GRPO 학습은 single-turn 채점을 쓰고, multi-turn 에이전트는 Agent Sandbox 확장의 에피소드 단위 샌드박스를 씁니다. 쓰는 곳: [06 multi-turn 에이전트와 Agent Sandbox](../beginner/06_multi_turn_agent.md), [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

## N

**Nested virtualization**
:   가상 EC2 인스턴스 안에서 다시 하이퍼바이저(KVM)를 쓰는 기능입니다. 2026-02에 C8i, M8i, R8i부터 출시됐고, GPU가 달린 G, P 계열은 지원하지 않습니다. 이 저장소는 GPU 없는 Kata CPU 계층에 씁니다. 쓰는 곳: [04 플랫폼과 인스턴스 선택](../concepts/04_platforms_and_instances.md)

**NetworkPolicy**
:   pod가 주고받을 수 있는 트래픽을 namespace와 label로 정하는 Kubernetes 규칙입니다. EKS에서는 VPC CNI가 적용하고(`enableNetworkPolicy`), standard 모드에서는 정책이 적용되기 전까지 새 pod가 default allow로 시작합니다. 쓰는 곳: [02 보안](../production/02_security.md)

**NodeConfig, nodeadm**
:   nodeadm은 EKS AL2023 노드를 클러스터에 등록하는 부트스트랩 도구이고, NodeConfig는 user data로 전달하는 nodeadm 설정입니다. 이 저장소는 NodeConfig로 containerd에 `runsc` 런타임을 등록합니다. nodeadm은 부팅할 때마다 `/etc/containerd/config.toml`을 다시 씁니다. 쓰는 곳: [02 gVisor GPU 샌드박스](../handson/02_gvisor.md)

**nvproxy**
:   gVisor 샌드박스 안에서 NVIDIA GPU를 쓸 수 있게 하는 gVisor 구성 요소입니다. GPU 드라이버로 보내는 ioctl을 드라이버 버전별 허용 목록으로 필터링해 호스트 드라이버에 전달합니다. 호스트의 드라이버 버전이 지원 목록에 정확히 있어야 동작합니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

## O

**OAC (Origin Access Control)**
:   CloudFront가 S3 origin에 서명된 요청을 보내게 하는 기능입니다. bucket policy가 CloudFront 서비스 principal과 특정 배포(`AWS:SourceArn` 조건)만 허용하므로, bucket을 비공개로 둔 채 CloudFront를 통해서만 내용을 제공할 수 있습니다. CloudFront 문서는 예전 방식(OAI) 대신 OAC를 권장합니다. 쓰는 곳: [09 데모 사이트 (CloudFront)](../handson/09_demo_site.md)

**On-policy**
:   학습 데이터(completion)를 지금 업데이트하는 바로 그 policy가 생성하는 학습 방식입니다. TRL 핸즈온은 생성한 batch 하나로 optimizer step을 한 번만 실행해서(TRL `steps_per_generation` 기본값) strictly on-policy로 학습합니다. veRL 구성은 학습 batch(prompt 64개)를 PPO mini-batch(prompt 32개)로 나눠 여러 번 업데이트합니다. 쓰는 곳: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

## P

**Parity check**
:   새 샌드박스 버전이 구버전과 같은 verdict를 내는지 golden 제출물로 비교하는 검사입니다. 두 버전의 결과가 모두 golden의 기대 status(지정된 경우 기대 `custom_kernel`도)를 만족하고 status가 서로 같아야 합니다. 양쪽이 `ok`이고 speedup 값이 있으면 신버전 speedup을 구버전 speedup으로 나눈 비율도 1에서 허용 범위(기본 0.35) 이내여야 합니다. 통과한 경우에만 트래픽이 새 버전으로 전환됩니다. 쓰는 곳: [05 샌드박스 버전 관리](../production/05_sandbox_updates.md)

**PDB (PodDisruptionBudget)**
:   drain 같은 자발적 중단 때 동시에 종료될 수 있는 pod 수의 상한입니다. PDB는 eviction API에만 적용되므로, gateway가 recycling으로 pod를 직접 지우는 것은 제한하지 않습니다. 쓰는 곳: [01 용량과 노드 관리](../production/01_capacity_and_nodes.md)

**Plausibility cap**
:   비현실적으로 큰 speedup을 제한하는 상한값입니다(`HARNESS_MAX_SPEEDUP`). v2 버전 파일은 KernelBench의 `excessive_speedup_threshold`와 같은 10을 쓰고, 상한을 넘으면 `implausible_speedup` 플래그를 달고 speedup을 1.0으로 기록합니다. 쓰는 곳: [04 Reward 무결성](../production/04_reward_integrity.md)

**Policy**
:   RL에서 학습 중인 모델입니다. prompt를 받아 completion을 생성하고, 그 completion이 받은 reward로 업데이트됩니다. harness의 정적 정책(`harness/policy.py`)이나 IAM 정책, NetworkPolicy와는 다른 뜻입니다. 쓰는 곳: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

**PriorityClass, preemption**
:   PriorityClass는 pod의 우선순위 값이고, preemption은 우선순위가 높은 pod를 배치하려고 scheduler가 우선순위가 낮은 pod를 제거하는 동작입니다. 이 저장소의 warm placeholder는 우선순위가 -10이라, 샌드박스 pod를 배치할 자원이 필요하면 가장 먼저 제거됩니다. 쓰는 곳: [01 용량과 노드 관리](../production/01_capacity_and_nodes.md)

**Private endpoint (EKS API)**
:   VPC 안에서만 접근할 수 있는 EKS API server 주소입니다. 이 저장소의 클러스터는 public endpoint를 끄고 private endpoint만 켜므로, 작업 PC의 kubectl과 helm은 `cdk/tunnel.sh`의 SSM 포트 포워딩으로 API에 접근합니다. 쓰는 곳: [09 CDK로 프로비저닝](../production/09_cdk.md)

**Projected ServiceAccount token**
:   kubelet이 pod 볼륨에 파일로 넣어 주는 ServiceAccount 토큰입니다. audience와 만료 시간(`expirationSeconds`)을 정할 수 있고, kubelet이 같은 경로에서 주기적으로 교체합니다. 이 저장소는 3600초 토큰을 쓰고 요청마다 파일을 다시 읽습니다. 쓰는 곳: [02 보안](../production/02_security.md)

## Q

**QEMU**
:   Kata가 쓰는 하이퍼바이저 가운데 하나입니다. Kata에서 NVIDIA GPU passthrough를 공식 지원하는 하이퍼바이저는 QEMU뿐이라서, 이 저장소의 Kata GPU 풀은 `kata-qemu-nvidia-gpu` RuntimeClass를 씁니다. 쓰는 곳: [03 Kata 샌드박스 (CLH, QEMU)](../handson/03_kata.md)

## R

**ResourceQuota**
:   namespace 하나가 요청할 수 있는 자원의 총량 상한입니다. Production용 `k8s/production/pool-hardening.yaml`을 적용하면 `sandbox` namespace의 요청 합계가 `nvidia.com/gpu` 16, `nvidia.com/pgpu` 8, pod 64로 제한됩니다. 핸즈온 기본 설치에는 이 quota가 없습니다. 쓰는 곳: [01 용량과 노드 관리](../production/01_capacity_and_nodes.md)

**Reward hacking**
:   policy가 과제를 실제로 풀지 않고 reward 측정의 허점을 이용해 점수만 올리는 현상입니다. KernelBench 계열에서는 추가 CUDA stream으로 타이밍 속이기, 결과 캐싱, 벤치마크 때만 틀리기, lazy tensor 같은 사례가 보고됐습니다. 쓰는 곳: [04 Reward 무결성](../production/04_reward_integrity.md)

**Rollout**
:   RL에서 현재 policy로 prompt의 completion을 생성하는 단계입니다. GRPO에서는 prompt마다 group 하나 분량을 생성합니다. Kubernetes의 Deployment rollout(`kubectl rollout`)과는 다른 뜻입니다. 쓰는 곳: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

**Routing table (`sandbox-routing`)**
:   어느 (runtime, version) 풀이 active인지와 풀마다의 주소를 적은 `routing.json`입니다. ConfigMap `sandbox-routing`으로 배포되고, trainer와 gateway가 읽습니다. 쓰는 곳: [05 샌드박스 버전 관리](../production/05_sandbox_updates.md)

**runc**
:   Kubernetes의 기본 컨테이너 런타임입니다. runc로 실행한 컨테이너는 호스트 커널과 드라이버를 직접 공유합니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

**RuntimeClass**
:   pod가 쓸 컨테이너 런타임을 지정하는 Kubernetes 객체입니다. pod의 `runtimeClassName`이 RuntimeClass를 가리키고, RuntimeClass의 `handler`는 containerd 설정의 `runtimes.<이름>` 키와 같아야 합니다. scheduling 규칙과 pod overhead도 함께 정할 수 있습니다. 쓰는 곳: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md)

## S

**SandboxClaim**
:   Agent Sandbox에서 warm pool의 샌드박스 하나를 할당받는 요청 리소스입니다. `spec.warmPoolRef`로 pool을 가리키고, Ready가 되면 `status.sandbox.serviceFQDN`에 주소가 기록됩니다. claim을 지우면 샌드박스를 반납합니다. 쓰는 곳: [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

**sandbox_error**
:   후보 코드가 원인이 아닌 인프라 실패(인증 실패, 통신 실패, 레퍼런스 실패 등)를 뜻하는 verdict입니다. TRL 경로에서는 reward로 `None`을 반환해 그 샘플을 학습에서 제외하고, veRL 경로에서는 format 점수만 주고 `sandbox_error` 플래그를 기록합니다. 쓰는 곳: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)

**sandbox-router**
:   Agent Sandbox가 제공하는 선택 구성 요소로, 클라이언트 요청을 claim한 샌드박스로 전달하는 HTTP reverse proxy입니다. AWS Korea 블로그는 기본 인가 설정이 모든 요청을 허용한다는 점을 지적했습니다. 이 저장소의 확장은 router를 쓰지 않고 claim의 `serviceFQDN`으로 직접 요청합니다. 쓰는 곳: [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

**SandboxTemplate**
:   Agent Sandbox에서 샌드박스 pod의 구성(pod template, NetworkPolicy, Service, 환경 변수 주입 정책)을 정의하는 리소스입니다. 이 저장소는 런타임 profile마다 `kernel-eval-<runtime>` 템플릿을 만듭니다. 쓰는 곳: [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

**SandboxWarmPool**
:   SandboxTemplate으로 샌드박스를 정해진 수만큼 미리 실행해 두는 Agent Sandbox 리소스입니다. claim이 생성되면 이미 준비된 샌드박스를 할당하므로 시작 대기 시간이 줄어듭니다. warm GPU 샌드박스는 요청이 없는 동안에도 GPU를 점유합니다. 쓰는 곳: [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

**Speedup**
:   레퍼런스 구현의 실행 시간을 후보 커널의 실행 시간으로 나눈 값입니다. 기본 설정에서는 정답인 custom kernel에만 speedup 점수를 주고, `--allow-torch-only`를 켜면 PyTorch만 쓴 정답도 같은 척도로 채점합니다. 점수는 log2 척도라 0.5배는 0, 1배는 0.5, 2배는 1.0이고 1.5(4배)가 상한입니다. 쓰는 곳: [05 On-policy GRPO 학습](../handson/05_grpo_training.md)

**SSM Session Manager 포트 포워딩**
:   SSM agent가 있는 인스턴스를 거쳐 내 PC의 로컬 포트를 VPC 안의 주소로 연결하는 AWS Systems Manager 기능입니다. 인스턴스에 inbound 포트나 공인 IP가 없어도 되고, 로컬에는 AWS CLI용 Session Manager plugin이 필요합니다. 이 저장소의 `cdk/tunnel.sh`는 `127.0.0.1:8443`을 private API endpoint로 연결합니다. 쓰는 곳: [09 CDK로 프로비저닝](../production/09_cdk.md)

## T

**T4**
:   NVIDIA의 GPU 모델입니다. EC2에서는 `g4dn` 인스턴스에 들어 있고, `g4dn.metal`에는 8개가 있습니다. EC2에서 VM에 직접 할당할 수 있는 x86 NVIDIA GPU는 이 T4뿐이라, 이 에셋의 Kata GPU 샌드박스는 T4에서 reward를 측정합니다. 쓰는 곳: [상황별 선택 가이드](../concepts/05_decision_guide.md), [03 Kata 샌드박스 (CLH, QEMU)](../handson/03_kata.md)

**Taint, toleration**
:   taint는 노드에 붙여 그 taint를 허용하지 않는 pod가 스케줄되지 못하게 하는 표시이고, toleration은 pod가 특정 taint가 있는 노드에도 스케줄될 수 있게 하는 설정입니다. 이 저장소는 `gpusandbox/role=<역할>:NoSchedule` taint로 샌드박스 노드를 전용 노드로 지정합니다. 쓰는 곳: [01 용량과 노드 관리](../production/01_capacity_and_nodes.md)

**TokenReview**
:   토큰이 유효한지, 누구의 토큰인지 Kubernetes API server에서 확인하는 API입니다. gateway가 호출자 인증에 쓰고 성공 결과는 60초 캐시합니다. TokenReview는 유효성만 알려 주고 권한은 알려 주지 않으므로, gateway는 allowlist를 함께 확인합니다. 쓰는 곳: [02 보안](../production/02_security.md)

**Triton**
:   Python으로 GPU 커널을 작성하는 언어이자 컴파일러입니다. 이 저장소의 과제는 policy가 Triton 커널을 작성하도록 요구하고, harness는 정확성 검사가 끝날 때까지 Triton 실행 함수가 몇 번 호출됐는지 기록합니다. 호출 횟수이므로 커널이 성공한 횟수와는 다릅니다. 쓰는 곳: [01 GPU 샌드박스가 필요한 경우](../concepts/01_why_gpu_sandbox.md)

**Turn**
:   multi-turn 에피소드에서 모델이 한 번 응답하는 단계입니다. 이 저장소의 커널 과제에서는 코드를 한 번 제출하고 verdict를 받는 한 차례이고, 한 에피소드의 모든 turn은 같은 샌드박스에서 채점합니다. 쓰는 곳: [06 multi-turn 에이전트와 Agent Sandbox](../beginner/06_multi_turn_agent.md)

## V

**Verdict**
:   harness가 후보 코드 하나를 채점해 반환하는 JSON 결과입니다. `status`(`ok`, `wrong_answer`, `policy_violation` 등), `speedup`, `flags`가 들어 있고, trainer가 이 값을 reward로 바꿉니다. 쓰는 곳: [04 Reward 무결성](../production/04_reward_integrity.md)

**VFIO**
:   GPU 같은 PCI 장치를 사용자 공간이나 VM에 직접 할당하는 Linux 커널 기능입니다(`vfio-pci` 드라이버). Kata GPU passthrough가 이 경로를 씁니다. VFIO는 VM 메모리 전체를 고정하므로 메모리 overcommit을 할 수 없습니다. 쓰는 곳: [03 Kata 샌드박스 (CLH, QEMU)](../handson/03_kata.md)

**vLLM colocate mode**
:   TRL GRPO에서 vLLM 생성 엔진을 학습 프로세스 안에 두고 같은 GPU를 나눠 쓰는 방식입니다(`vllm_mode="colocate"`). 이 저장소는 vLLM에 GPU 메모리의 35%를 할당하고(`--vllm-gpu-memory-utilization 0.35`), sleep mode로 optimizer step 동안 그 메모리를 해제합니다. 쓰는 곳: [05 On-policy GRPO 학습](../handson/05_grpo_training.md)

## W

**Warm pool, warm placeholder**
:   시작 지연을 피하려고 자원을 미리 준비해 두는 방식입니다. Production의 warm placeholder는 작업 없이 metal 노드 한 대를 점유하는 pod이고, Agent Sandbox의 SandboxWarmPool은 샌드박스 pod 자체를 미리 실행해 둡니다. 쓰는 곳: [01 용량과 노드 관리](../production/01_capacity_and_nodes.md)

## ❓ 오해

!!! question "❓ 오해: rollout은 Kubernetes 배포 용어다"
    이 가이드북에서는 두 뜻으로 씁니다. 주변 문장이 학습을 설명하는지 배포를 설명하는지로 구분하세요.

    - **RL 문맥(GRPO, veRL)**: rollout은 policy가 completion을 생성하는 단계입니다.
    - **배포 문맥**: rollout은 명령마다 하는 일이 다릅니다.
        - `kubectl rollout status`는 지정한 Deployment의 배포가 끝날 때까지 기다립니다.
        - `scripts/ops/rollout.sh`는 새 버전의 풀을 별도 Deployment로 배포해 검증한 뒤 routing 표를 바꿔 트래픽을 옮깁니다.

!!! question "❓ 오해: warm placeholder도 GPU를 미리 점유한다"
    - **Production의 warm placeholder**: CPU와 메모리만 요청하고 GPU는 요청하지 않습니다. 노드를 점유하기만 하고, 샌드박스 pod를 배치해야 하면 제거됩니다.
    - **Agent Sandbox의 SandboxWarmPool**: 프로필에 지정한 자원으로 샌드박스 pod를 미리 실행합니다. GPU 프로필이면 요청이 없는 동안에도 GPU를 점유하고, CPU 프로필(예: `kata-clh-cpu`)이면 GPU를 요청하지 않습니다.

!!! question "❓ 오해: Kata는 `.metal` 인스턴스에서만 실행된다"
    GPU passthrough를 할 때만 그렇습니다. 장치를 할당하지 않는 Kata는 EC2 nested virtualization이 제공하는 `/dev/kvm`을 사용해 `.metal` 없이 실행됩니다. GPU를 VM에 할당하려면 호스트가 물리 GPU와 IOMMU를 직접 쓸 수 있어야 해서 이 저장소의 x86 구성에서는 `g4dn.metal`이 필요합니다.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | Amazon EC2 nested virtualization | [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) |
    | Configure network policy (Amazon EKS) | [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
    | gVisor GPU 지원 | [gVisor GPU 지원](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor) |
    | Kata Containers 4.3.1 NVIDIA GPU passthrough | [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md), [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers) |
    | Karpenter 문서 | [Karpenter 문서](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws) |

    전체 출처: [참고 자료 모음의 이 페이지 절](references.md#ref-reference-glossary)

전체 출처 목록은 [검증된 사실과 출처](sources.md)에 있습니다.
