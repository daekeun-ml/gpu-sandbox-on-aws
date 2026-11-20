# 자주 하는 오해

!!! info "TL;DR"
    런타임이나 학습 동작에 관해 헷갈리기 쉬운 질문을 모았습니다. 실행 중 발생한 오류는 [문제 해결](troubleshooting.md)에서 찾아보세요.

- [Kata를 실행할 노드와 GPU](#런타임과-인스턴스)
- [HyperPod와 관리형 서비스](#플랫폼과-관리형-서비스)
- [네트워크와 인증](#네트워크와-인증)
- [보상 점수와 학습 중 버전 교체](#학습과-reward)
- [Agent Sandbox와 에피소드](#agent-sandbox)
- [모델, 데모, 검증 상태](#모델-데모-검증-상태)

## 런타임과 인스턴스

??? question "Kata를 쓰려면 `.metal` 인스턴스가 필요하다"
    **실제:** `.metal`이 필요한 경우는 Kata VM에 GPU를 직접 할당할 때(GPU passthrough)뿐입니다. CPU 샌드박스는 EC2 nested virtualization을 켠 C8i, M8i, R8i 같은 일반 VM 인스턴스에서 실행됩니다(2026-02-16 출시).

    Kata는 `/dev/kvm`만 있으면 VM을 실행할 수 있지만, GPU passthrough에는 호스트가 물리 GPU와 IOMMU를 직접 쓸 수 있어야 합니다. nested virtualization을 지원하는 G나 P 계열은 없습니다. x86 NVIDIA GPU가 달린 bare metal은 `g4dn.metal`뿐이라, Kata에서 GPU를 쓰려면 여전히 `.metal`이 필요합니다.

    아래 명령은 현재 리전에서 nested virtualization을 지원하는 인스턴스 타입을 나열합니다.

    ```bash
    # Instance types that support nested virtualization in the current Region
    aws ec2 describe-instance-types \
      --filters "Name=processor-info.supported-features,Values=nested-virtualization" \
      --query 'InstanceTypes[].InstanceType' --output text
    ```

    **확인할 것:** 목록에 `c8i.2xlarge` 같은 타입이 있으면 그 리전에서 Kata CPU 노드를 만들 수 있습니다.

    **문제가 생기면:** [문제 해결](troubleshooting.md)의 Kata 표를 보세요.

    자세히: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md), [03 Kata 샌드박스](../handson/03_kata.md)

??? question "gVisor의 GPU 격리는 VM 격리와 같은 수준이다"
    **실제:** gVisor는 호스트의 NVIDIA 드라이버를 그대로 공유하므로 GPU 격리가 VM보다 약합니다.

    nvproxy는 드라이버 버전별 ioctl allowlist로 드라이버에 전달되는 호출을 제한합니다. 그래도 gVisor 문서는 드라이버 내부 취약점을 완화하는 데는 "much less effective"하고, DMA buffer 같은 내용은 검증하지 않는다고 적습니다. GKE Sandbox 문서도 sandbox pod에서 GPU time-sharing을 쓰지 말라고 권합니다. 드라이버까지 분리해야 한다면 guest VM 안에서 별도의 드라이버를 쓰는 Kata + VFIO를 선택하세요. 자세히: [02 격리 런타임 비교](../concepts/02_isolation_runtimes.md), [02 보안](../production/02_security.md)

??? question "Firecracker로도 GPU를 VM에 직접 할당할 수 있다"
    **실제:** Firecracker는 GPU passthrough를 제공하지 않습니다.

    Firecracker는 virtio 장치 중심의 최소 장치 모델을 씁니다. 1.13.0에서 PCI 지원이 추가됐지만 변경 이력에 VFIO GPU passthrough는 없습니다. E2B 같은 Firecracker 기반 샌드박스가 CPU 위주인 것도 이 때문입니다. 이 저장소은 GPU 샌드박스에 gVisor(nvproxy)나 Kata + QEMU(VFIO)를 씁니다. 자세히: [01 GPU 샌드박스가 필요한 경우](../concepts/01_why_gpu_sandbox.md)

??? question "Kata + Cloud Hypervisor도 QEMU처럼 GPU를 VM에 직접 할당할 수 있다"
    **실제:** upstream은 Cloud Hypervisor의 GPU passthrough를 지원하지 않습니다. 지원되는 Kata GPU 경로는 QEMU(`kata-qemu-nvidia-gpu`)입니다.

    Kata `docs/hypervisors.md`는 Cloud Hypervisor의 GPU 지원을 not supported로 표시하고, maintainer도 2025-08에 QEMU GPU runtime class를 쓰라고 답했습니다(issue #11687). 이 저장소의 `kata-clh-nvidia-gpu`는 평가용 실험 구성이고, Kata + Cloud Hypervisor는 CPU 샌드박스(`kata-clh-cpu`)로 씁니다. 자세히: [03 Kata 샌드박스](../handson/03_kata.md)

??? question "Kata GPU 풀(T4)에서도 Triton 커널은 당연히 동작한다"
    **실제:** T4(`g4dn.metal`)에서 Triton 커널이 동작하는지는 여러분의 노드에서 golden 커널로 확인해야 합니다. 이 가이드는 Triton의 공식 지원 GPU 범위를 단정하지 않습니다.

    T4와 Kata 조합은 NVIDIA Kata CI의 검증 범위(A100, H100)에도 포함되지 않습니다. 아래 명령은 Kata GPU 풀에 golden 세트를 보내 verdict를 확인합니다.

    ```bash
    scripts/ops/verify.sh kata-qemu v1
    ```

    **확인할 것:** 3단계 출력에서 `vector_add_triton`과 `relu_bias_triton`이 `PASS`면 그 풀에서 Triton 커널이 컴파일, 실행되고 커스텀 커널로 판정된 것입니다.

    **문제가 생기면:** [문제 해결](troubleshooting.md)의 Kata 표와 "샌드박스 풀과 readiness" 표를 보세요.

    자세히: [04 Reward 무결성](../production/04_reward_integrity.md)

## 플랫폼과 관리형 서비스

??? question "HyperPod 기본 AMI 노드에 이 샌드박스를 바로 올릴 수 있다"
    **실제:** 기본 AMI(Kubernetes 1.36)로는 HyperPod 노드에 gVisor GPU 샌드박스도, Kata GPU 샌드박스도 올릴 수 없습니다. 기본 시나리오 B1은 학습만 HyperPod에서 하고 샌드박스는 같은 EKS 클러스터의 EC2 노드에 둡니다. B2는 지원 목록에 있는 드라이버를 넣은 custom AMI로 HyperPod 노드에서 gVisor 샌드박스를 실행하도록 구성했지만, AWS에서는 아직 실행하지 않았습니다.

    - **기본 AMI의 gVisor GPU 샌드박스**: HyperPod EKS AMI(1.34~1.36)의 NVIDIA 드라이버 595.91.07이 gVisor release-20261109.0의 nvproxy 지원 목록에 없어서 쓸 수 없습니다(목록에 없는 unknown 버전은 플래그와 관계없이 실패).
    - **B2가 이 조건을 맞추는 방법**: HyperPod 공개 base AMI의 드라이버를 580.178.04로 바꾸고 고정한 gVisor를 설치한 custom AMI를 빌드합니다. 노드가 시작할 때 lifecycle 스크립트가 `runsc`를 containerd에 등록합니다([07 HyperPod 시나리오의 B2](../handson/07_hyperpod.md#b2)).
    - **Kata GPU 샌드박스**: Kubernetes 버전이나 AMI와 관계없이 HyperPod 노드에서 실행할 수 없습니다. `ml.*.metal`이 없고, CreateCluster에 nested virtualization CPU 옵션이 없으며, G와 P 계열은 nested virtualization을 지원하지 않기 때문입니다.
    - **GPU 없는 Kata**: 같은 `/dev/kvm` 조건 때문에 어렵다고 보지만 검증하지 않았고(추론), 이 저장소에는 HyperPod용 Kata 구성이 없습니다.

    아래 명령은 HyperPod 노드마다 debug pod를 띄워 드라이버와 gVisor 지원 여부를 출력합니다. 끝나면 `default` namespace에서 이름이 `node-debugger-`로 시작하는 pod를 모두 삭제하므로, 다른 사람이 `kubectl debug node`로 노드를 점검하는 중이면 그 작업이 끝난 뒤 실행하세요.

    ```bash
    scripts/hyperpod/check_gvisor.sh
    ```

    **확인할 것:**

    - **기본 AMI 노드**: `NOT supported by gVisor ...: keep sandboxes on EC2 (mode B1)`가 출력됩니다.
    - **B2 custom AMI 노드**: `driver 580.178.04: SUPPORTED ...`가 출력됩니다.

    새 AMI나 gVisor 릴리스가 나오면 다시 실행하세요.

    **문제가 생기면:** [문제 해결](troubleshooting.md)의 HyperPod 표를 보세요.

    자세히: [04 플랫폼과 인스턴스 선택](../concepts/04_platforms_and_instances.md), [07 HyperPod 시나리오](../handson/07_hyperpod.md)

??? question "EKS Auto Mode 노드에 gVisor나 Kata를 설치하면 된다"
    **실제:** EKS 문서는 "You can't directly access or install software on instances managed by EKS Auto Mode"라고 적습니다. Auto Mode 노드에는 runsc나 kata-deploy의 런타임을 등록할 수 없습니다.

    그래서 이 저장소은 핸즈온에서 managed node group을, Production에서 Karpenter NodePool을 씁니다. AWS 기술 블로그 1부도 EKS Auto Mode에서는 runsc를 등록할 수 없다고 설명합니다. 자세히: [01 용량과 노드 관리](../production/01_capacity_and_nodes.md)

??? question "관리형 code interpreter나 샌드박스 서비스로 GPU 샌드박스를 쓸 수 있다"
    **실제:** 이 가이드가 확인한 AWS 관리형 샌드박스는 CPU 샌드박스의 대안으로만 쓸 수 있습니다.

    Amazon Bedrock AgentCore Code Interpreter 문서는 실행 환경을 containerized environment로 설명하고 GPU를 언급하지 않습니다. AWS Nitro Sandboxes와 EKS isolated pods(2026-11-09 출시, `runtimeClassName` `isolated-sandbox` 또는 `confidential-sandbox`, Kubernetes 1.36 이상)의 문서에는 "GPU and other device passthrough are not supported at launch"라고 적혀 있습니다. reward를 GPU에서 측정해야 한다면 이 저장소처럼 gVisor나 Kata를 직접 운영하세요. 자세히: [05 상황별 선택 가이드](../concepts/05_decision_guide.md)

## 네트워크와 인증

??? question "NetworkPolicy를 default deny로 두면 pod가 노드 IP에도 연결할 수 없다"
    **실제:** VPC CNI network policy agent는 kubelet probe가 차단되지 않도록 pod와 자기 노드 IP 사이의 통신을 정책과 관계없이 허용합니다(aws-network-policy-agent 소스 기준).

    그래서 이 저장소은 샌드박스 노드에 iptables node guard(`GPUSANDBOX-GUARD`)를 둡니다. 또 readiness 검사에서 IMDS, API 서버, `$(NODE_IP):10250`에 연결할 수 없음을 확인한 뒤에만 pod가 Ready가 됩니다. 아래 명령은 풀의 pod에서 이 대상들이 실제로 차단되는지 확인합니다.

    ```bash
    scripts/ops/verify.sh gvisor v1
    ```

    **확인할 것:** 2단계 출력에서 `instance metadata`, `kubernetes api`, `node kubelet`, `internet (S3 endpoint)`가 모두 `blocked (...)`입니다.

    **문제가 생기면:** [문제 해결](troubleshooting.md)의 "샌드박스 풀과 readiness" 표를 보세요.

    자세히: [02 보안](../production/02_security.md), [04 샌드박스 풀 배포와 검증](../handson/04_sandbox_pools.md)

??? question "정적 정책(AST 검사)이 샌드박스의 보안 경계다"
    **실제:** 정적 정책은 reward 무결성을 위한 검사이고, 노드를 보호하는 보안 경계는 gVisor나 Kata, 그리고 네트워크 통제입니다.

    이 저장소은 후보 코드가 pod 안에서 임의의 Python을 실행할 수 있다고 가정합니다. 정적 정책은 timer 교체나 harness 내부 접근처럼 측정을 조작하는 간단한 방법만 차단합니다. 자세히: [04 Reward 무결성](../production/04_reward_integrity.md), [02 보안](../production/02_security.md)

??? question "TokenReview를 통과한 토큰이면 호출을 허용해도 된다"
    **실제:** TokenReview는 토큰이 유효한지만 증명하고, 그 subject에게 호출 권한이 있는지는 알려 주지 않습니다.

    AWS 기술 블로그 2부는 Agent Sandbox의 sandbox-router를 분석하며 이 점과 기본 인가가 allow-all이라는 점을 함께 지적했습니다. 이 저장소의 gateway는 TokenReview 다음에 `GATEWAY_ALLOWED_SUBJECTS` allowlist를 따로 확인합니다. 샌드박스 pod는 audience(`gpu-sandbox`)와 `SANDBOX_ALLOWED_SUBJECTS`를 함께 검사하고, 일치하지 않으면 요청을 거부합니다. 자세히: [03 Gateway와 샌드박스 풀](../production/03_gateway_and_pools.md), [02 보안](../production/02_security.md)

## 학습과 reward

??? question "샌드박스 Deployment를 rolling update로 바꾸면 학습 중에도 안전하다"
    **실제:** rolling update 동안에는 구버전과 신버전 pod가 함께 응답해서, 같은 GRPO group의 completion이 서로 다른 채점 규칙으로 점수를 받을 수 있습니다. 그러면 group 기준 advantage가 잘못 계산됩니다.

    이 저장소은 (runtime, version)마다 blue/green 풀을 따로 배포합니다.

    - **전환 시점**: 격리 검증과 golden parity를 통과하면 스크립트가 routing 표를 갱신합니다. trainer는 샌드박스를 부를 때마다 routing 표를 읽으므로, 변경이 반영된 뒤 샌드박스에 보내는 요청부터 새 버전 풀이 응답합니다.
    - **한 batch는 한 버전**: 한 batch의 점수는 항상 한 버전에서 나옵니다. 채점 도중 풀이 바뀌면 다른 풀에서 받은 결과를 새 풀에서 다시 채점합니다.
    - **결과가 모두 한 풀의 캐시에 있는 batch**: 샌드박스를 부르지 않고 그 풀의 결과를 씁니다.
    - **TRL 기본 설정**: batch 경계가 step 경계와 같습니다.

    아래 명령이 그 절차(배포, 검증, parity, 전환)를 차례로 실행합니다. 기본 시나리오 A에서는 v1이 `sandbox-gvisor` 노드 두 대의 GPU를 이미 쓰고 있으므로, 먼저 이 노드 그룹을 4대로 늘리고 노드가 `Ready`인지 확인합니다. 늘리지 않으면 v2 pod가 GPU를 받지 못해 1단계가 최대 30분 기다린 뒤 실패합니다(노드 수를 늘리는 명령은 [06 학습 중 샌드박스 업데이트](../handson/06_sandbox_update.md)의 준비 절에 있습니다).

    ```bash
    scripts/ops/rollout.sh gvisor v1 v2
    ```

    **확인할 것:**

    - golden 항목별 `PASS` 줄과 `{"event": "parity", ..., "passed": true}`가 출력됩니다.
    - routing 변경이 pod에 반영된 뒤(kubelet 동기화로 1분 안팎) trainer가 직전과 다른 풀에서 batch 응답을 받으면 `sandbox_version_switch` 이벤트를 출력합니다.
    - **batch의 결과가 모두 한 풀의 캐시에 있을 때**: 샌드박스를 부르지 않으므로 그 batch에서는 이 이벤트가 나오지 않습니다.

    **문제가 생기면:** [문제 해결](troubleshooting.md)의 "버전 전환 (routing)" 표를 보세요.

    자세히: [05 샌드박스 버전 관리](../production/05_sandbox_updates.md), [06 학습 중 샌드박스 업데이트](../handson/06_sandbox_update.md)

??? question "인프라 오류에 reward 0을 주면 보수적이라 안전하다"
    **실제:** 0점은 "이 completion은 나쁘다"는 학습 신호라서, 채점하지 못한 샘플에 0을 주면 reward가 왜곡됩니다.

    - **정답을 낸 샘플이 pod 장애 때문에 0점을 받을 때**: 그 행동이 억제됩니다.
    - **오류가 특정 노드에 몰릴 때**: reward에 체계적인 오차가 생깁니다.

    학습 경로마다 처리 방식이 다릅니다.

    - **TRL 경로**: `sandbox_error`일 때 세 reward 함수가 모두 `None`을 반환해, 그 샘플을 group baseline에서 제외합니다.
    - **veRL 경로**: 샘플을 제외하는 신호가 없어서 format 점수 0.1과 `sandbox_error: 1`을 기록합니다. 그러니 그 비율을 모니터링하세요.

    자세히: [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md), [04 Reward 무결성](../production/04_reward_integrity.md)

??? question "parity를 통과하면 reward도 바뀌지 않는다"
    **실제:** parity는 golden 제출물만 확인합니다. 통과 조건은 다음과 같습니다.

    - 두 버전 모두 golden마다 정해 둔 status(지정된 경우 `custom_kernel` 여부도)를 내야 합니다.
    - **양쪽이 `ok`이고 speedup이 있을 때**: 신버전과 구버전의 speedup 비율도 기본 0.65~1.35 범위에 들어야 합니다.

    v2처럼 seed를 3에서 5로 늘리고 speedup 상한을 10배로 두면, golden은 그대로 통과해도 통과 기준에 가까웠던 policy 샘플의 verdict와 speedup은 달라질 수 있습니다. 의도한 reward 변화는 버전 교체가 아니라 reward 함수 변경으로 기록하세요. 자세히: [05 샌드박스 버전 관리](../production/05_sandbox_updates.md)

??? question "speedup은 어떤 GPU에서 측정해도 비슷하다"
    **실제:** speedup은 측정한 GPU에서만 의미가 있는 값입니다. gVisor 풀(A10G)과 Kata 풀(T4)의 speedup은 서로 다른 reward 함수로 다뤄야 합니다.

    `scripts/ops/bench.sh`도 GPU 종류가 다른 풀의 speedup은 GPU별로 따로 비교하라고 안내합니다. 배포할 GPU가 정해져 있다면 그와 같거나 가까운 GPU로 reward를 측정하는 편이 좋습니다. 자세히: [01 GPU 샌드박스가 필요한 경우](../concepts/01_why_gpu_sandbox.md), [08 런타임 벤치마크](../handson/08_benchmark.md)

## Agent Sandbox

??? question "Agent Sandbox는 gVisor만 지원한다"
    **실제:** Agent Sandbox는 RuntimeClass로 지정한 런타임에 격리를 맡기므로 Kata도 쓸 수 있습니다.

    upstream README는 "Agent Sandbox is a sandbox orchestrator. It delegates low-level container isolation to secure Sandbox Runtimes (like gVisor or Kata Containers) by managing Pods configured to use these runtimes (via RuntimeClass)."라고 적습니다. 저장소에는 Kata 예시(kata-aks, kata-gke)와 GKE의 gVisor + L4 GPU 예시가 있습니다. 이 저장소의 확장도 같은 SandboxTemplate을 gvisor, kata-qemu, kata-clh-cpu 같은 런타임 프로필마다 렌더링합니다. 다만 SandboxTemplate 안에서 Kata GPU(`kata-qemu-nvidia-gpu`와 `nvidia.com/pgpu`)를 쓰는 조합은 검증하지 않았습니다. 자세히: [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

??? question "Agent Sandbox의 기본 SandboxTemplate 정책이 인터넷 egress를 차단한다"
    **실제:** AWS 기술 블로그 2부에 따르면 기본 정책은 인터넷 egress를 허용합니다.

    기본 정책은 sandbox-router에서 오는 ingress만 허용하고, egress는 0.0.0.0/0에서 RFC1918과 169.254.0.0/16을 뺀 범위로 허용합니다. 내부망과 IMDS 대역은 제외되지만 인터넷은 허용되므로, 이 정책으로는 데이터 유출, C2 통신, 채굴을 차단할 수 없습니다.

    같은 글은 다음 두 가지도 보고했습니다.

    - VPC CNI NetworkPolicy를 켜기 전에는 샌드박스가 IMDS와 Kubernetes API에 접근할 수 있었습니다.
    - 기본 DNS 주입(`dnsPolicy: None`에 8.8.8.8, 1.1.1.1)이 Route 53 Resolver를 우회합니다.

    이 저장소의 확장은 `networkPolicy.egress: []`(전부 차단)와 nameserver 127.0.0.1을 명시해 이 기본값을 쓰지 않습니다. 자세히: [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

??? question "warm pool의 GPU 샌드박스는 요청이 없는 동안 비용이 들지 않는다"
    **실제:** warm 샌드박스는 claim을 기다리는 동안에도 GPU를 점유하고 있으므로, 그 GPU 노드의 비용이 계속 발생합니다.

    warm pool 크기(`replicas`)는 동시에 진행할 episode 수에 맞춰 필요한 만큼만 두세요. 노드 비용과 정리 방법은 [08 비용](../production/08_cost.md)과 [99 정리](../handson/99_cleanup.md)에 있습니다. 자세히: [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)

## 모델, 데모, 검증 상태

??? question "Qwen2.5-Coder 계열은 모두 Apache-2.0이다"
    **실제:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`와 `Qwen/Qwen2.5-Coder-7B-Instruct`는 Apache-2.0이고 gate가 없지만, `Qwen2.5-Coder-3B-Instruct`는 qwen-research 라이선스(비상업)입니다.

    이 저장소은 3B를 쓰지 않습니다. 모델을 바꿀 때는 Hugging Face 모델 카드의 license 항목을 직접 확인하고, 데이터셋 라이선스도 함께 보세요. 자세히: [홈](../index.md)

??? question "데모 사이트는 실제 GPU 클러스터에 연결된다"
    **실제:** 데모는 정적 사이트(HTML, CSS, JS, 외부 스크립트 없음)입니다. `python -m gpusandbox.tools record`가 만든 채점 녹화(`recording.json`)를 재생하고, `demo/build_extras.py`로 만든 `extras.json`이 있으면 벤치마크와 학습 기록도 보여 줍니다. 방문자는 클러스터나 GPU에 접속하지 않습니다.

    - **사이트 위치**: Block Public Access를 켠 private S3 bucket에 있고, CloudFront만 Origin Access Control로 이 bucket을 읽습니다.
    - **기본으로 올리는 채점 녹화**(`demo/site/data/recording.json`): 노트북 CPU 풀에서 만들었고, GPU 클러스터에서 만든 녹화로 교체해 쓰도록 되어 있습니다.
    - **GPU 풀의 녹화**: 2026-11-18 EKS의 gVisor A10G 풀과 Kata QEMU T4 풀에서 만든 녹화는 `demo/recordings/2026-11-18-eks-gpu.json`에 있습니다.

    자세히: [09 데모 사이트 (CloudFront)](../handson/09_demo_site.md)

??? question "이 가이드의 수치는 이 저장소가 AWS에서 측정한 값이다"
    **실제:** 일부만 그렇습니다. 가격과 지원 버전은 공식 문서와 공개 자료를 인용했고, AWS 단계 전체를 end-to-end로 실행하지는 않았습니다.

    실습 계정에서 실행한 것은 다음과 같습니다.

    - 시나리오 A의 gVisor 경로(`03`부터 `08`까지)를 `g5`로 실행했습니다.
    - 다섯 개 풀(gVisor A10G, Kata QEMU T4, CPU 런타임 세 개)을 배포 직후와 풀 재시작 뒤에 한 번씩 `ops/bench.sh`로 측정했습니다. [08 런타임 벤치마크](../handson/08_benchmark.md)의 결과 표는 두 번째 측정값이고 측정 조건과 함께 있습니다.
    - A10G와 T4 풀에서 golden 제출물을 채점한 녹화는 `demo/recordings/2026-11-18-eks-gpu.json`에 있습니다.

    날짜별 실행 기록은 [검증된 사실과 출처](sources.md#aws-실행-기록)에 있습니다. 그 밖의 수치는 여전히 공식 문서와 공개 자료의 값입니다.

    로컬에서 확인한 것은 CPU에서 실행하는 pytest 테스트와 TRL GRPO dry run(2 step)입니다. 런타임별 지연과 speedup이 필요하면 `scripts/ops/bench.sh`로 직접 측정하세요. 출처와 검증 수준은 [검증된 사실과 출처](sources.md)에 모았습니다. 자세히: [홈](../index.md), [08 런타임 벤치마크](../handson/08_benchmark.md)

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | EC2 nested virtualization (User Guide, What's New) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html , https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
    | EC2 가속 컴퓨팅 인스턴스 (`g4dn.metal`, `g5g.metal`) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
    | AWS Nitro Sandboxes, EKS sandboxing 제한 | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
    | gVisor GPU 지원 (nvproxy, 보안 범위) | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
    | Kata 4.3.1 NVIDIA GPU passthrough, hypervisor 지원 표, issue #11687 | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md , https://github.com/kata-containers/kata-containers/issues/11687 |

    전체 출처: [참고 자료 모음의 이 페이지 절](references.md#ref-reference-faq)
