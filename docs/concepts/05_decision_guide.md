# 상황별 선택 가이드

!!! info "TL;DR"
    GPU가 필요 없으면 CPU 샌드박스로 충분합니다. GPU가 필요하면 격리 요구와 측정 GPU에 따라 "VM 경계 + T4"(`g4dn.metal`의 Kata + QEMU)와 "최신 GPU + 사용자 공간 커널 경계"(G/P 계열 VM의 gVisor) 중 하나를 선택합니다.

## 기존 Pain Point

GPU 종류, 격리 강도, 운영 부담, 비용은 서로 영향을 주므로 한 가지 기준만 보고 선택하면 다른 조건을 충족하지 못할 수 있습니다. VM 경계와 H100 같은 최신 GPU가 모두 필요해도, EC2에서 VM에 직접 할당할 수 있는 x86 NVIDIA GPU는 `g4dn.metal`의 T4뿐입니다. 새로 출시된 관리형 격리 서비스로 GPU 샌드박스도 운영할 수 있을 것 같지만, 이 서비스는 출시 시점에 CPU만 지원합니다.

![격리 경계와 측정 GPU를 두 축으로 한 표입니다. VM 경계와 T4 조합은 g4dn.metal의 Kata + QEMU(VFIO)로 가능합니다. VM 경계와 최신 GPU(L4, L40S, H100) 조합은 EC2에 없습니다(빨간색). 사용자 공간 커널 경계와 T4 조합은 g4dn의 gVisor이며, 이 에셋에서는 검증하지 않았습니다. 사용자 공간 커널 경계와 최신 GPU 조합은 G/P 계열 VM(g5, g6, g6e, p5)의 gVisor + nvproxy로 가능합니다. AWS 관리형 격리인 Nitro Sandboxes와 EKS isolated pods는 출시 시점에 CPU 전용이라 두 GPU 열 모두에서 쓸 수 없습니다(GPU passthrough 미지원, 빨간색).](../images/figures/concepts-05_decision_guide.svg)

*그림 요약: GPU 샌드박스로 바로 쓸 수 있는 조합은 `g4dn.metal`의 Kata + QEMU와 G/P 계열 VM의 gVisor + nvproxy 두 가지입니다. VM 경계와 최신 GPU 조합은 EC2에 없고, Nitro Sandboxes와 EKS isolated pods는 출시 시점에 GPU를 지원하지 않습니다.*


## Why

- **정해진 순서대로 조건을 확인합니다.** GPU 필요 여부, 관리형 서비스 선호, VM 경계 필요 여부, 측정 GPU 순으로 선택지를 줄입니다.

**사전 지식:** [02 격리 런타임 비교](02_isolation_runtimes.md)와 [04 플랫폼과 인스턴스 선택](04_platforms_and_instances.md)을 먼저 읽으면 표를 이해하기 쉽습니다. 처음 보는 용어는 아래 "용어" 상자와 [용어 사전](../reference/glossary.md)에서 확인할 수 있습니다.

??? note "용어 (처음 보는 단어가 있으면 펼치세요)"
    - **VM 경계**: 신뢰할 수 없는 코드를 하드웨어 가상화로 만든 별도 VM 안에서 실행하는 격리 방식입니다. VM 밖으로 탈출하려면 hypervisor의 취약점을 이용해야 합니다.
    - **사용자 공간 커널 경계**: gVisor처럼 host 커널 대신 사용자 공간 프로그램이 syscall을 처리하는 격리 방식입니다. VM을 사용하지 않습니다.
    - **멀티테넌트**: 서로 다른 고객이나 팀의 작업이 같은 풀을 함께 쓰는 구성입니다.
    - **적대적 코드**: 의도적으로 격리를 우회하려고 시도할 수 있다고 가정하는 코드입니다.
    - **측정 GPU**: reward의 timing을 측정하는 GPU입니다. policy는 이 GPU에서 빠르게 실행되는 커널을 학습합니다.
    - **T4**: NVIDIA의 GPU 모델입니다. EC2에서는 `g4dn` 인스턴스에 들어 있고, `g4dn.metal`에는 8개가 있습니다. EC2에서 VM에 직접 할당할 수 있는 x86 NVIDIA GPU는 이 T4뿐입니다. 따라서 Kata로 GPU를 쓰면 측정 GPU는 T4가 됩니다.
    - **보완 통제**: 격리 경계가 약한 부분을 다른 수단(GPU 독점, egress 차단, pod 재활용 등)으로 보강하는 조치입니다.
    - **Nitro Sandboxes, EKS isolated pods**: AWS가 2026-11-09에 출시한 관리형 격리 런타임입니다. 출시 시점에는 GPU를 지원하지 않습니다.
    - **AgentCore Code Interpreter**: Amazon Bedrock AgentCore가 제공하는 관리형 코드 실행 도구입니다.
    - **warm pool**: 요청이 오기 전에 미리 만들어 둔 샌드박스 묶음입니다. 요청이 오면 샌드박스를 할당하는 시간이 짧아집니다.

## 결정 트리

![왼쪽에 위에서 아래로 이어지는 결정 단계가 있고, 오른쪽에 결과 여섯 개가 있습니다. 샌드박스 안에서 GPU가 필요 없을 때 관리형 서비스를 선호하면 AgentCore Code Interpreter 또는 Nitro Sandboxes, EKS isolated pods(CPU 전용)를 쓰고, 선호하지 않으면 c8i의 Kata + CLH(nested virtualization)를 씁니다. GPU가 필요하고 관리형 GPU 샌드박스를 선호하면 서드파티 서비스(예: Modal, gVisor 기반, 이 에셋 범위 밖)를 씁니다. 관리형을 선호하지 않고 VM 경계(서로 다른 고객의 적대적 코드)가 필요 없으면 G/P 계열 VM의 gVisor + nvproxy(g5 A10G, g6 L4, g6e L40S, p5 H100)를 씁니다. VM 경계가 필요하고 T4에서 측정한 timing으로 충분하면 g4dn.metal의 Kata + QEMU(VM 경계 + VFIO)를 씁니다. 충분하지 않으면 EC2에 VM 경계와 최신 GPU 조합이 없으므로, gVisor와 보완 통제로 위험을 수용하거나 요구 사항을 다시 검토합니다(빨간색). 이 에셋이 구성하는 세 조합은 파란색입니다.](../images/figures/concepts-05_decision_guide--decision-tree.svg)

*그림 요약: GPU와 VM 경계가 모두 필요할 때 EC2에서 Kata로 쓸 수 있는 GPU는 `g4dn.metal`의 T4뿐입니다. reward에 쓰는 timing을 T4에서 측정해도 되면 Kata를 쓰고, 배포할 GPU(L4, H100 등)에서 측정해야 하면 EC2에는 맞는 조합이 없으므로, gVisor와 보완 통제로 위험을 수용하거나 요구 사항을 다시 검토합니다.*


배포할 GPU가 정해져 있다면 측정 GPU도 같은 GPU나 비슷한 GPU로 선택하세요. policy는 reward를 측정한 GPU에 맞춰 최적화됩니다([01](01_why_gpu_sandbox.md)의 오해 노트).

## 상황별 선택

| 상황 | 이렇게 고르세요 | 근거 | 감수할 점 |
|---|---|---|---|
| 샌드박스 안의 코드 실행과 측정에 GPU가 필요 없고 직접 운영하려 할 때 | Kata + CLH on `c8i` (nested virtualization) | VM 경계, `.metal` 불필요, upstream 지원 조합 | AWS는 성능에 민감한 가상화 작업에 bare metal을 권장. `c8i.2xlarge`는 시간당 0.37484 USD |
| CPU 샌드박스를 관리형으로 쓰고 싶을 때 | AWS Nitro Sandboxes, EKS isolated pods 또는 AgentCore Code Interpreter | 런타임을 직접 운영하지 않음 | Nitro Sandboxes는 2026-11-09 출시, Kubernetes 1.36 이상, GPU passthrough 미지원. AgentCore Code Interpreter는 문서상 containerized environment이며 GPU 언급 없음 |
| 서로 다른 고객의 적대적 코드를 GPU로 채점하고 T4에서 측정해도 될 때 | Kata + QEMU on `g4dn.metal` | VM + IOMMU 경계, Kata에서 upstream이 지원하는 GPU 구성 | T4는 upstream 미검증(NVIDIA CI는 A100, H100). 7.824 USD/시간, VM마다 T4 1개로 최대 8개 |
| 배포 대상 GPU가 L4, L40S, H100이라 그 GPU에서 timing을 측정해야 할 때 | gVisor + nvproxy on `g6`, `g6e`, `p5` | nvproxy 문서화 GPU는 T4, A100/A10G, L4, H100. L40S는 L4와 같은 아키텍처라 문서상 "will likely work" | host 드라이버가 nvproxy 지원 목록과 정확히 일치해야 함. GPU 드라이버 경로의 격리는 VM 경계보다 약함 |
| 적대적 코드인데 최신 GPU도 꼭 필요할 때 | gVisor + 보완 통제 (pod마다 GPU 1개, time-sharing 금지, egress 차단 확인 후 Ready, node guard, pod 재활용)와 위험 수용 기록 | EC2에서 VM에 직접 할당할 수 있는 x86 NVIDIA GPU는 T4뿐 | 잔여 위험: 드라이버 취약점, DMA 버퍼 미검증 |
| 멀티턴 에이전트 학습에서 에피소드마다 새 샌드박스가 필요할 때 | [Agent Sandbox 확장](06_agent_sandbox.md): warm pool에서 에피소드마다 샌드박스를 claim하고 끝나면 반납 | RuntimeClass를 그대로 쓰므로 gVisor, Kata 어느 쪽에도 적용 | warm GPU 샌드박스는 대기 중에도 GPU를 점유. Kata GPU 템플릿은 미검증. 클러스터에서 실행하지 않음 |
| HyperPod에서 학습하고 싶을 때 | B1: trainer는 HyperPod, 샌드박스는 같은 EKS 클러스터의 EC2 | HyperPod AMI 드라이버 595.91.07은 gVisor에서 unknown이고, HyperPod에는 `.metal`이 없음 | 샌드박스 노드에도 HyperPod 노드 복구를 적용하려면 B2(실험): 드라이버를 바꾼 custom AMI로 `sandbox` 인스턴스 그룹 구성 |
| GPU 샌드박스를 관리형으로 쓰고 싶을 때 | 서드파티 서비스 검토 (이 에셋 범위 밖) | Modal 문서: "GPU Sandboxes are only supported with `runtime="gvisor"`". Northflank는 GPU에 Kata를 쓰고 nested virtualization을 쓸 수 없으면 gVisor로 대체한다는 공개 자료가 있음 (원출처 URL 미확인) | 서비스마다 격리 방식, GPU 종류, 리전을 직접 확인 |
| Cloud Hypervisor로 GPU를 쓰고 싶을 때 | 평가 목적의 실험으로만 (`infra/kata/experimental-clh-gpu/`) | upstream 미지원, CI 없음 | 중요한 작업에는 `kata-qemu-nvidia-gpu` |

## 고객 상황 예시

| 고객 상황 | 조합 | 이유 |
|---|---|---|
| 사내 연구팀이 자체 모델로 L4 서빙용 Triton 커널을 학습 | `g6.xlarge`의 gVisor (이 에셋이 지원하는 대안. 기본값은 `g5.xlarge`) | 한 팀만 쓰는 풀이라 VM 경계까지는 요구하지 않고, 측정 GPU를 배포 GPU(L4)에 맞출 수 있음 |
| 여러 고객의 학습 작업이 같은 GPU 노드를 쓰고, T4 기준 순위로 충분 | `g4dn.metal`의 Kata + QEMU, 고객별 풀 | Kata는 pod마다 VM을 만들지만 풀은 요청마다 빈 pod를 고르므로, 하나의 공유 풀에서는 여러 고객의 요청이 같은 VM을 차례로 씀. 고객별로 풀을 나누고 요청도 그 풀로 보내야 고객 간 작업이 VM 경계로 나뉨. T4에서 측정하는 조건을 수용 |
| 여러 고객이 공유하는 풀에서 H100 서빙용 커널을 학습 | `p5`의 gVisor + 보완 통제, 고객별 노드 분리 검토, 위험 수용 기록 | EC2에 VM 경계 + H100 조합이 없음 |
| 단위 테스트로 채점하는 code RL | `c8i`의 Kata + CLH 또는 관리형 CPU 샌드박스 | reward 계산에 GPU가 필요 없음 |
| nvcc 컴파일 단계와 측정 단계를 나누고 싶음 | CPU 계층(`c8i`의 Kata + CLH) + GPU 계층(gVisor 또는 Kata + QEMU) | 컴파일과 정적 검사에 GPU 시간을 쓰지 않음 |

두 번째와 세 번째 예시는 둘 다 멀티테넌트 상황이고 측정 GPU 요구만 다릅니다. T4에서 측정해도 되면 Kata로 VM 경계를 쓸 수 있고, H100에서 측정해야 하면 VM 경계를 쓸 수 없습니다.

## 비교표

| 항목 | gVisor + nvproxy | Kata + QEMU (GPU) | Kata + CLH (CPU) | Kata + CLH (GPU, 실험) | Nitro Sandboxes, EKS isolated pods |
|---|---|---|---|---|---|
| 격리 경계 | 사용자 공간 커널. GPU는 ioctl allowlist라 VM보다 약함 | VM + IOMMU | VM | VM + IOMMU (upstream 미검증) | AWS 관리형 (세부는 문서 확인) |
| AWS에서 쓸 수 있는 GPU | G/P 계열 VM. 이 에셋은 A10G (`g5`, 기본)와 L4 (`g6`, 대안) | T4 (`g4dn.metal`)만 | 없음 | T4 (`g4dn.metal`) | 없음 (출시 시점) |
| 설치 난이도 | 중간: user data로 runsc 설치, containerd handler, RuntimeClass, device plugin `cdi-cri` | 높음: IOMMU AMI 빌드, GPU Operator, kata-deploy, `.metal` 노드 | 중간: nested virtualization launch template, kata-deploy | 높음: QEMU 구성 외에 실험용 values 적용. 4.3.1용 values에는 guest 커널과 이미지 경로가 들어 있고, 다른 버전에서는 경로를 확인. 이 저장소의 실습에서는 VM이 시작되지 않음 | 낮음: Kubernetes 1.36 이상 |
| 밀도 (이 에셋 구성) | `g5.xlarge` 노드당 1개 | `g4dn.metal`당 VM 최대 8개, guest RAM 전체 pin | pod당 CPU 1.25개(요청 1 + overhead 250m)와 메모리 2 GiB + 130Mi. 노드의 할당 가능 CPU와 메모리 중 먼저 소진되는 쪽이 상한 | `kata-qemu`와 노드 공유 | 문서 확인 |
| upstream 지원 | 지원 (nvproxy 문서) | 지원 (NVIDIA CI는 A100, H100) | 지원 | 미지원 | AWS 지원 (2026-11-09 출시) |
| 드라이버 의존성 | host 드라이버 버전이 nvproxy 지원 목록과 정확히 일치해야 함 | guest 드라이버 (kata-deploy, open 615.71.09). host에는 드라이버를 설치하지 않음 | 없음 | guest 드라이버 | 없음 |
| GPU 1개의 온디맨드 요금 (시간당) | 1.006 (A10G, `g5.xlarge`) | 약 0.978 (7.824 / 8, 8개를 모두 쓸 때) | 해당 없음 | 약 0.978 | 해당 없음 |

가격은 us-east-1과 us-west-2의 온디맨드 요금으로 계산한 값입니다. `g4dn.metal`의 T4를 일부만 쓰면 GPU 1개당 비용이 올라갑니다.

## 선택 후 바로 확인할 것

실행 방법과 출력 예시는 해당 핸즈온 페이지에 있습니다. gVisor 조합(`04_install_gpu_stack.sh`, `scripts/ops/verify.sh gvisor v1`)은 실습 계정에서 `g5.xlarge`로 실행했습니다. Kata + QEMU(GPU)도 `g4dn.metal`에서 `scripts/ops/verify.sh kata-qemu v1`으로 T4 인식과 golden verdict를 확인했습니다([실행 기록](../reference/sources.md#aws-실행-기록)). NVIDIA upstream CI의 검증 대상은 A100과 H100입니다. 기대 결과와 비교해 직접 검증하세요.

| 조합 | 확인 스크립트 | 기대 결과 | 핸즈온 |
|---|---|---|---|
| gVisor | `scripts/04_install_gpu_stack.sh` | smoke pod 안의 `dmesg` 출력에 host kernel 대신 gVisor Sentry 메시지가 나오고, torch가 GPU를 인식해 커널을 실행함(`cuda ok:` 뒤에 GPU 이름과 `2048.0`. 기본 `g5.xlarge`에서는 `cuda ok: NVIDIA A10G 2048.0`). 노드 드라이버가 nvproxy 지원 목록에 없으면 노드 부팅 로그에 `install-gvisor.sh`의 경고가 기록됨 | [02 gVisor](../handson/02_gvisor.md) |
| Kata CPU (`kata-clh`, `kata-qemu`) | `scripts/kata/cpu_nodes.sh` | runtime class 두 개가 있고, smoke pod가 출력한 guest kernel 버전이 스크립트가 출력한 host kernel 버전과 다름 | [03 Kata](../handson/03_kata.md) |
| Kata + QEMU (GPU) | `scripts/kata/gpu_nodes.sh` | 노드의 allocatable `nvidia.com/pgpu`가 0보다 크고 `kata-qemu-nvidia-gpu` runtime class가 있음 | [03 Kata](../handson/03_kata.md) |
| Deployment 풀 | `scripts/ops/verify.sh <runtime> [version]` | pod별 격리 증거, IMDS, API server, kubelet, 인터넷 접근 차단, golden verdict, 다른 namespace의 접근 거부 | [04 샌드박스 풀](../handson/04_sandbox_pools.md) |
| Agent Sandbox warm pool | claim을 하나 만든 뒤 `status.sandbox.serviceFQDN` 주소로 probe Job 실행. warm pod에는 `gpusandbox/version` 라벨이 없어 `verify.sh`가 찾지 못하고, 같은 런타임의 Deployment 풀이 있으면 그 풀을 검사함 | 할당받은 샌드박스의 golden verdict | [06 Agent Sandbox](06_agent_sandbox.md)의 "평가까지 확인하기" |

**문제가 생기면:** 기대 결과와 다르면 [문제 해결](../reference/troubleshooting.md)에서 런타임 이름(gVisor, Kata)이나 "샌드박스 풀과 readiness" 항목을 먼저 보세요.

## 결정을 다시 검토할 조건

아래 사실 중 하나가 바뀌면 런타임 선택을 다시 검토하세요.

| 바뀌는 사실 | 영향 | 확인 방법 |
|---|---|---|
| gVisor 새 릴리스가 HyperPod 기본 AMI의 드라이버를 지원 | B2에서 드라이버 교체를 생략할 수 있음. 기본 AMI를 그대로 쓰려면 lifecycle script에 gVisor 설치 단계도 넣어야 함(`on_create_sandbox.sh`는 `runsc`가 없으면 실패) | `GVISOR_RELEASE`를 새 릴리스로 바꾼 뒤 `scripts/hyperpod/check_gvisor.sh` |
| EKS NVIDIA AMI, NVIDIA 드라이버, gVisor 버전이 바뀜 | 기본값 `g5`(GSP를 끈 proprietary 모듈)의 gVisor는 gVisor 문서가 아니라 이 저장소의 검증에 근거하므로 다시 확인해야 함 | 노드의 `/proc/driver/nvidia/version`과 `runsc nvproxy list-supported-drivers`, 이어서 빈 GPU가 있을 때 `04_install_gpu_stack.sh` smoke test(GPU 1개를 쓰는 pod를 따로 만듦), 배포한 풀은 `scripts/ops/verify.sh gvisor v1` |
| 사용할 가용 영역에서 `g6` On-Demand 용량을 확보할 수 있음 | open 드라이버를 써서 gVisor 문서와 맞고 요금도 낮은 `g6`를 선택할 수 있음 | 인스턴스를 시작했다가 바로 종료해 확인한 뒤 `scripts/config.env`의 `GVISOR_INSTANCE_TYPE`, `TRAINER_INSTANCE_TYPE` 변경 |
| nested virtualization 지원 목록에 G나 P 계열이 추가 | `.metal` 없는 Kata + GPU 배치를 검토할 수 있음 (VFIO 지원은 따로 확인) | nested virtualization User Guide, `describe-instance-types` 필터 |
| NVIDIA GPU를 탑재한 새 x86 `.metal` 타입 출시 | VM 경계 + 최신 GPU 조합 가능 | EC2 가속 컴퓨팅 인스턴스 사양 |
| Nitro Sandboxes가 GPU passthrough를 지원 | 관리형 GPU 계층 검토 가능 | Nitro Sandboxes 문서, EKS sandboxing 제한 사항 |
| NVIDIA CI가 T4를 테스트하거나 Kata가 CLH GPU를 지원 | `g4dn.metal`의 검증 상태나 CLH GPU 지원 여부가 바뀜 | Kata 릴리스 노트, upstream `docs/hypervisors.md` |

!!! question "❓ 오해: gVisor를 쓰면 GPU 코드도 VM만큼 격리된다"
    gVisor는 syscall을 사용자 공간 커널(Sentry)에서 처리하지만, GPU 요청은 ioctl allowlist를 거쳐 host 드라이버로 전달됩니다. gVisor 문서도 nvproxy가 "much less effective at mitigating vulnerabilities within the NVIDIA GPU drivers themselves"이며 "no validation of things like DMA buffers"라고 설명합니다. 서로 다른 고객의 적대적 코드를 실행한다면 VM 경계(Kata + VFIO)를 먼저 검토하세요. 최신 GPU 때문에 gVisor를 쓴다면 보완 통제와 잔여 위험을 문서로 기록하세요.

!!! question "❓ 오해: Nitro Sandboxes가 나왔으니 GPU 샌드박스도 관리형으로 해결된다"
    AWS Nitro Sandboxes와 EKS isolated pods(2026-11-09 출시) 문서에는 "GPU and other device passthrough are not supported at launch"라고 명시돼 있습니다. 현재는 CPU 계층에 쓸 수 있는 관리형 대안입니다. GPU 계층은 이 에셋의 gVisor나 Kata + QEMU로 운영하세요.

!!! tip "다음에 읽을 페이지"
    - 런타임 구조와 AWS 배치 조건: [02 격리 런타임 비교](02_isolation_runtimes.md)
    - 인스턴스, quota, 시간당 비용: [04 플랫폼과 인스턴스 선택](04_platforms_and_instances.md)
    - 에피소드마다 warm pool에서 샌드박스 할당받기: [06 Agent Sandbox로 확장](06_agent_sandbox.md)
    - 직접 구축: [핸즈온 00 전체 흐름](../handson/00_overview.md)
    - 운영 설계와 위협 모델: [Production 00 아키텍처](../production/00_architecture.md), [Production 02 보안](../production/02_security.md)

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | AWS Nitro Sandboxes, EKS sandboxing 제한 사항 | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
    | Amazon Bedrock AgentCore Code Interpreter | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html |
    | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
    | gVisor GPU 지원, GitHub | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
    | Kata NVIDIA GPU passthrough (4.3.1), GitHub | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers |

    전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-concepts-05-decision-guide)
