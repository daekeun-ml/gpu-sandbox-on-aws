# GPU Sandbox on AWS

!!! info "TL;DR"
    모델이 쓴 GPU 코드를 격리된 GPU 샌드박스에서 실행해 reward를 매기는 on-policy RL post-training 환경을 구축하는 가이드입니다. Amazon EKS와 SageMaker HyperPod에서 세 가지 격리 런타임으로 구성하는 핸즈온과 Production 설계를 다룹니다.

<div class="grid cards" markdown>

-   :material-sprout:{ .lg .middle } **처음 시작한다면**

    ---

    샌드박스, 격리 런타임, 강화학습을 처음 접하는 분을 위한 가이드입니다. 각 개념이 무엇이고 왜 필요한지 그림으로 먼저 설명하고, 실제 화면을 보며 샌드박스를 직접 띄워 봅니다.

    [:octicons-arrow-right-24: 초심자 가이드로 시작](beginner/index.md)

-   :material-rocket-launch:{ .lg .middle } **경험이 있다면**

    ---

    Kubernetes, gVisor나 Kata, GRPO를 다뤄 본 분을 위한 코스 안내입니다. 목적과 예산에 맞는 코스를 골라 바로 핸즈온이나 Production 설계를 시작합니다.

    [:octicons-arrow-right-24: 학습 코스 고르기](learning_paths.md)

</div>

## 기존 Pain Point

코드를 실행해 채점하는 RL(RLVR)은 대부분 CPU 샌드박스로 충분하지만, **reward 자체를 GPU에서 측정하는 과제**(CUDA나 Triton 커널이 얼마나 빨라졌는지를 보상으로 삼는 경우)는 샌드박스 안에 GPU가 필요합니다. 이 경우 policy(학습 중인 모델)가 쓴 신뢰할 수 없는 코드가 GPU 드라이버를 호출하는데, 일반 컨테이너(runc)는 호스트 커널과 드라이버를 그대로 공유합니다. Firecracker 기반 샌드박스(E2B 등)에는 GPU를 VM에 연결할 장치가 없고, gVisor와 Kata는 GPU를 연결하는 방식이 서로 달라서 쓸 수 있는 AWS 인스턴스부터 확인해야 합니다. 며칠씩 진행되는 on-policy 학습 도중 샌드박스 이미지나 채점 harness를 고치다가 같은 GRPO group 안에 버전이 섞이면 advantage가 잘못 계산됩니다.

![a: 서로 다른 두 문제입니다. 위 줄에서는 policy가 쓴 커널 코드가 runc 컨테이너에서 실행되어 host 커널과 GPU 드라이버를 그대로 공유합니다. 아래 줄에서는 학습 중에 이미지나 harness를 바꾸면, 런타임과 관계없이 한 GRPO group 안에 v1과 v2의 reward가 섞여 advantage가 잘못 계산됩니다. b: 위 줄은 RuntimeClass로 선택한 gVisor 또는 Kata가 코드와 host 커널 사이에 들어갑니다. 아래 줄은 배치(또는 group) 단위로 한 버전만 채점하므로 reward가 일관되게 유지됩니다.](images/figures/index.svg)

*그림 요약: (a) 일반 컨테이너에서는 모델이 쓴 코드가 host 커널과 드라이버를 공유합니다. 이와 별개로, 학습 중 버전을 바꾸면 런타임과 관계없이 두 버전의 reward가 한 group에 섞일 수 있습니다. (b) RuntimeClass로 고른 gVisor나 Kata가 코드와 host 커널 사이에 들어가고, trainer는 배치(또는 group)마다 한 버전의 풀로 채점합니다.*


## Why

- **세 런타임을 같은 이미지, 같은 API로 비교합니다.** 런타임 프로필 하나가 `RuntimeClass`와 노드, GPU 요청을 함께 정해 gVisor(nvproxy), Kata + QEMU(VFIO GPU passthrough), Kata + Cloud Hypervisor(기본은 CPU)를 선택합니다. Kata + GPU에 `g4dn.metal`이 필요한 이유, `.metal` 없이 nested virtualization으로 실행할 수 있는 범위, HyperPod 노드의 custom AMI는 표로 정리했습니다.
- **on-policy 학습을 멈추지 않고 샌드박스를 업데이트합니다.** blue/green 풀, golden 제출물 parity 검사, 배치(또는 group) 단위 버전 고정으로 reward 일관성을 유지합니다.
- **reward 무결성까지 다룹니다.** KernelBench 계열에서 보고된 reward hacking 중 추가 CUDA stream, 결과 캐싱, lazy tensor는 harness 설계로 막고, "벤치마크 때만 틀리기"에 대비해 측정 구간 출력의 합과 절댓값 합을 검사합니다. 두 값이 모두 허용 오차 안에 들면 일부 원소가 틀려도 통과할 수 있습니다.

## 아키텍처

### 만드는 것

![왼쪽은 학습 노드(EC2 GPU 노드 또는 HyperPod 노드)이고, 그 안에서 policy 모델과 vLLM이 GRPO로 on-policy 학습을 합니다(g5.2xlarge 또는 ml.g5.2xlarge). 오른쪽은 EC2 노드의 샌드박스 풀입니다. gVisor + nvproxy(g5.xlarge, A10G), Kata + QEMU(g4dn.metal, T4), Kata + Cloud Hypervisor(CPU 계층, c8i, nested virt, GPU는 실험적)의 세 풀이 같은 이미지를 쓰고, 풀마다 프로필이 RuntimeClass와 노드를 정합니다. 커널 코드는 group 단위로 버전을 고정해 풀로 보내고, 풀은 정확성과 speedup을 돌려줍니다.](images/figures/index--what-we-build.svg)

*그림 요약: policy 모델이 쓴 커널 코드는 group 단위로 버전을 고정한 상태로 선택한 런타임의 샌드박스 풀에 전달되고, 풀이 측정한 정확성과 speedup이 reward로 쓰입니다. GPU 채점은 gVisor와 Kata + QEMU 풀이 맡고, Kata + Cloud Hypervisor는 기본적으로 CPU에서 실행합니다.*

| 시나리오 | 학습 위치 | 샌드박스 위치 | 언제 |
|---|---|---|---|
| A. EC2 자체 운영 (기본) | EKS의 EC2 GPU 노드 (`g5.2xlarge`) | 같은 클러스터의 EC2 노드 | 모든 구성 요소를 직접 제어하고 싶을 때 |
| B1. HyperPod (HyperPod 기본) | HyperPod 인스턴스 그룹 (`ml.g5.2xlarge`) | HyperPod를 연결한 같은 EKS 클러스터의 EC2 노드 | 장시간 학습에 HyperPod의 노드 자동 교체와 job 재시작이 필요할 때 |
| B2. HyperPod (실험) | HyperPod 인스턴스 그룹 | 드라이버를 바꾼 custom AMI로 만든 HyperPod 인스턴스 그룹에서 실행하는 gVisor | 샌드박스 노드에도 HyperPod 노드 복구가 필요할 때 (custom AMI를 직접 관리, AWS에서 미실행) |
| C. c8i 단독 (GPU 없음) | 없음 (모델 없는 reward 루프) | `c8i.2xlarge` 한 대의 CPU 샌드박스 (gVisor, Kata + CLH, Kata + QEMU) | GPU 쿼터 없이, 컴퓨트 시간당 약 0.57 USD로 런타임 비교와 버전 교체를 먼저 익히고 싶을 때 ([핸즈온 10](handson/10_cpu_only.md)) |

### 시나리오별 구성

네 시나리오는 같은 CDK 스택(private EKS API, SSM 터널, KMS 키, 로그)을 씁니다. A, B1, B2는 trainer와 샌드박스가 배치되는 위치가 다르고, C는 trainer와 모델 없이 CPU 샌드박스에서 채점과 버전 교체를 실습합니다.

=== "A: EC2 GPU"

    [![시나리오 A: SSM 터널로 private EKS API에 접속하고, g5.2xlarge의 trainer가 g5.xlarge 두 대의 gVisor 풀에 커널 코드를 보내는 구성](images/architecture/scenario-a.drawio.png)](images/architecture/scenario-a.drawio.png)

    *그림 요약: trainer와 gVisor 풀이 모두 EKS의 EC2 노드에 있고, 모델은 NAT를 거쳐 Hugging Face Hub에서 받습니다.*

=== "B1: HyperPod 학습"

    [![시나리오 B1: trainer는 HyperPod 인스턴스 그룹에, gVisor 풀은 EC2 노드에 있는 구성](images/architecture/scenario-b1.drawio.png)](images/architecture/scenario-b1.drawio.png)

    *그림 요약: trainer만 HyperPod 인스턴스 그룹(ml.g5.2xlarge)으로 옮겨 S3의 lifecycle 스크립트로 부팅하고, 샌드박스는 A와 같은 EC2 gVisor 노드에 남습니다.*

=== "B2: HyperPod 학습과 샌드박스"

    [![시나리오 B2: trainer와 gVisor 풀이 모두 HyperPod 인스턴스 그룹에 있고, 샌드박스 노드는 custom AMI로 부팅하는 구성](images/architecture/scenario-b2.drawio.png)](images/architecture/scenario-b2.drawio.png)

    *그림 요약: 샌드박스도 HyperPod 인스턴스 그룹(ml.g5.xlarge x2)에 올라가고, 이 노드는 한 번 빌드하는 custom AMI(드라이버 580.178.04)로 부팅합니다. AWS에서 실행해 보지 않은 실험 경로입니다.*

=== "C: CPU 전용"

    [![시나리오 C: GPU 없이 c8i.2xlarge 한 대에 세 런타임의 CPU 풀이 있는 구성](images/architecture/scenario-c.drawio.png)](images/architecture/scenario-c.drawio.png)

    *그림 요약: GPU 노드 없이 c8i.2xlarge 한 대에 세 런타임의 풀이 서고, system 노드의 simulate Job이 trainer 대신 golden 코드를 보냅니다.*

### 요청 경로

- trainer는 샌드박스에 요청을 보낼 때마다 routing ConfigMap(`sandbox-routing`)의 snapshot으로 런타임과 버전을 정하고, 한 reward batch의 결과는 한 풀에서 받습니다. 학습 중에 v2로 바꾸면 같은 batch에 든 이전 풀의 캐시 결과도 v2 풀에서 다시 채점합니다. batch 전체가 한 풀의 캐시로 채워지면 샌드박스를 부르지 않고 그 결과를 씁니다. 한 batch 안에서 전환이 거듭되면 세 번째 요청에서 batch 전체를 한 풀에 보내므로, 한 batch는 항상 한 버전으로 채점됩니다.
- trainer는 headless Service를 CoreDNS로 풀어 Ready 상태인 pod에 `POST /v1/evaluate`를 직접 보냅니다. 바쁜 pod는 `503`을 돌려주고, trainer는 다른 pod로 다시 시도합니다.
- 요청에는 audience가 `gpu-sandbox`인 projected ServiceAccount 토큰이 붙고, pod는 JWKS로 토큰을 오프라인 검증합니다. `sandbox` 네임스페이스는 default-deny라서 `rl-trainer`에서 label이 붙은 pod만 접속할 수 있습니다.

노드 그룹과 네임스페이스, 화살표별 설명은 [핸즈온 00 전체 흐름](handson/00_overview.md)에, Production 구성(Karpenter NodePool, sandbox gateway, veRL on KubeRay)은 [Production 00 아키텍처](production/00_architecture.md)에 있습니다. 그림 원본(`.drawio`)은 저장소의 `diagrams/`에서 볼 수 있습니다.

## 시작하기

- **무엇부터 할지 모르겠다면** → [학습 코스 고르기](learning_paths.md)에서 질문 몇 개로 코스를 고르세요(무료 코스부터 안내합니다).
- **바로 실습하려면** → [시작하기](getting_started.md)의 로컬 smoke test를 마친 뒤 [핸즈온 00 전체 흐름](handson/00_overview.md)으로 진행하세요.
- **런타임 차이가 헷갈린다면** → [02 격리 런타임 비교](concepts/02_isolation_runtimes.md)의 [AWS에서 각 런타임을 실행할 수 있는 위치](concepts/02_isolation_runtimes.md#aws에서-각-런타임을-실행할-수-있는-위치) 표
- **고객 상황에 맞는 조합을 골라야 한다면** → [05 상황별 선택 가이드](concepts/05_decision_guide.md)
- **용어가 낯설다면** → [용어 사전](reference/glossary.md)

## 트랙 구성

| 트랙 | 목적 | 범위 |
|---|---|---|
| [핸즈온 (Getting Started)](handson/00_overview.md) | 하루 안에 세 런타임과 on-policy 루프를 직접 확인 | CDK 스택(private API endpoint)과 SSM 터널, TRL GRPO(1.5B, LoRA, vLLM colocate), 샌드박스 v1에서 v2로 무중단 교체 |
| [Production Ready](production/00_architecture.md) | 운영 환경 설계와 확장 | Karpenter NodePool, sandbox gateway, 보안 위협 모델, reward 무결성, veRL on KubeRay, observability, 비용 |
| [Agent Sandbox 확장](concepts/06_agent_sandbox.md) | multi-turn 에피소드마다 전용 샌드박스 | kubernetes-sigs/agent-sandbox의 SandboxTemplate, SandboxWarmPool, SandboxClaim. gVisor와 Kata 모두 RuntimeClass로 선택 |
| [데모 사이트](handson/09_demo_site.md) | 실행 기록을 브라우저에서 재생 | 비공개 S3 + CloudFront(OAC, HTTPS, 보안 헤더). 방문자 요청은 클러스터나 GPU로 전달되지 않음 |

## 검증 상태

!!! warning "직접 확인해야 하는 범위"
    실습 계정에서 시나리오 A(gVisor GPU, `g5`), 시나리오 C(CPU 런타임 세 개)와 버전 교체, Kata GPU(`g4dn.metal`), 다섯 개 풀의 런타임 벤치마크([08 런타임 벤치마크](handson/08_benchmark.md)), 공개 데모 사이트를 실행했습니다. 실험용 Kata CLH GPU는 VM이 시작되지 않았고, 학습 중의 `ops/rollout.sh`, `rollout.sh --finish`, HyperPod B1과 B2는 아직 실행하지 않았습니다. 날짜별 실행 기록은 [검증된 사실과 출처](reference/sources.md#aws-실행-기록)에 있습니다. 실행하지 않은 단계는 각 핸즈온 페이지의 확인 단계로 직접 검증하세요. 가격과 버전 같은 수치는 직접 측정한 값이 아니라 공식 문서와 공개 자료에서 가져온 값입니다. 로컬 테스트의 확인 범위는 [시작하기](getting_started.md)에 있습니다.

!!! warning "비용"
    GPU 인스턴스는 실행되는 동안 과금되고, `g4dn.metal`은 시간당 약 7.8 USD입니다(us-east-1과 us-west-2 온디맨드 요금). 쉬는 동안에는 GPU 노드 수를 0으로 줄이고, 실습을 마치면 [99 정리](handson/99_cleanup.md)를 반드시 실행하세요.

!!! note "기준 시점: 2026-11"
    이 가이드의 가격(온디맨드 요금), 버전(gVisor 릴리스, Kata, NVIDIA 드라이버 지원 목록, EKS와 HyperPod 지원 버전), 리전과 서비스 지원 범위는 2026-11 기준입니다. 이 값들은 자주 바뀌므로 배포 전에 공식 문서에서 다시 확인하세요. 확인할 항목과 링크는 [검증된 사실과 출처](reference/sources.md)에 모았습니다.

## Disclaimer

이 가이드는 저자의 개인 견해와 조사 결과를 정리한 것으로, 저자가 재직 중인 회사의 공식 문서나 입장을 대변하지 않습니다. 내용이 공식 문서와 다르면 공식 문서가 우선합니다.

## License

코드와 문서는 [MIT](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/LICENSE)이고, 모델 라이선스는 별개입니다. 기본 모델 `Qwen/Qwen2.5-Coder-1.5B-Instruct`와 Production 예시의 `Qwen/Qwen2.5-Coder-7B-Instruct`는 Apache-2.0이고, `Qwen2.5-Coder-3B-Instruct`는 비상업 라이선스라 이 에셋에서 쓰지 않습니다.
