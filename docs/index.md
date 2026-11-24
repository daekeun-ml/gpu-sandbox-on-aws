# GPU Sandbox on AWS

Amazon EKS에서 모델 학습과 코드 채점을 별도 GPU 노드에 배치합니다. 아래 그림의 A와 B1은 각각 EC2와 HyperPod에서 학습하고, 둘 다 EC2에서 채점합니다. [B2](handson/scenarios/b/b2.md)는 시스템 CPU와 학습용 GPU와 채점용 GPU를 모두 HyperPod에서 운영합니다.

<a href="images/figures/index--aws-architecture.svg">
<picture>
  <source media="(max-width: 34em)" srcset="images/figures/index--aws-architecture-compact.svg" width="360" height="613">
  <img class="off-glb" src="images/figures/index--aws-architecture.svg" width="824" height="464" alt="운영자 PC는 Systems Manager 세션과 접속용 EC2를 거쳐 프라이빗 EKS API에 연결합니다. VPC의 프라이빗 서브넷에서 EC2 또는 HyperPod 학습 노드가 별도 EC2 채점 pool에 코드를 보내고 판정과 속도를 받습니다. 워커 노드는 ECR에서 컨테이너 이미지를 가져옵니다.">
</picture>
</a>

<div class="grid cards" markdown>

-   :material-sprout:{ .lg .middle } **처음 시작한다면**

    ---

    샌드박스, 격리 런타임, 강화학습을 처음 접하는 분을 위한 가이드입니다. 짧은 예시로 개념을 익힌 뒤 내 PC의 CPU에서 답안을 직접 채점해 봅니다.

    [:octicons-arrow-right-24: 초심자 가이드로 시작](beginner/index.md)

-   :material-rocket-launch:{ .lg .middle } **경험이 있다면**

    ---

    Kubernetes, gVisor나 Kata, GRPO를 다뤄 본 분을 위한 코스 안내입니다. 목적과 예산에 맞는 코스를 골라 바로 핸즈온이나 Production 설계를 시작합니다.

    [:octicons-arrow-right-24: 학습 코스 고르기](learning_paths.md)

</div>

## GPU 샌드박스가 필요한 이유

CPU 단위 테스트로 채점할 수 있는 과제라면 CPU 샌드박스로 충분합니다. 이 프로젝트에서는 모델이 작성한 GPU 커널의 정확도와 성능을 reward에 반영합니다. 실제 GPU에서 코드를 실행해야 하므로 샌드박스에도 GPU를 연결합니다. [GPU 샌드박스가 필요한 경우](concepts/01_why_gpu_sandbox.md)

- **일반 컨테이너(runc)**: 호스트 커널과 드라이버를 그대로 공유합니다.
- **Firecracker**　물리 GPU를 VM에 붙이는 GPU passthrough를 지원하지 않습니다. E2B는 CPU 샌드박스를 제공합니다. [E2B GPU 지원 범위](https://docs.e2b.dev/faq/gpu-support)
- **gVisor와 Kata**: GPU를 연결하는 방식이 서로 달라서 쓸 수 있는 AWS 인스턴스부터 확인해야 합니다.
- **학습 도중 버전을 고칠 때**: 며칠씩 진행되는 on-policy 학습 도중 샌드박스 이미지나 채점 harness를 고치다가 같은 GRPO group 안에 버전이 섞이면 advantage가 잘못 계산됩니다.

![a: 서로 다른 두 문제입니다. 위 줄에서는 policy가 쓴 커널 코드가 runc 컨테이너에서 실행되어 host 커널과 GPU 드라이버를 그대로 공유합니다. 아래 줄에서는 학습 중에 이미지나 harness를 바꾸면, 런타임과 관계없이 한 GRPO group 안에 v1과 v2의 reward가 섞여 advantage가 잘못 계산됩니다. b: 위 줄은 RuntimeClass로 선택한 gVisor 또는 Kata가 코드와 host 커널 사이에 들어갑니다. 아래 줄은 배치(또는 group) 단위로 한 버전만 채점하므로 reward가 일관되게 유지됩니다.](images/figures/index.ko.svg)

*그림 요약: (a) 일반 컨테이너에서는 모델이 쓴 코드가 host 커널과 드라이버를 공유합니다. 이와 별개로, 학습 중 버전을 바꾸면 런타임과 관계없이 두 버전의 reward가 한 group에 섞일 수 있습니다. (b) RuntimeClass로 고른 gVisor나 Kata가 코드와 host 커널 사이에 들어가고, trainer는 배치(또는 group)마다 한 버전의 pool로 채점합니다.*


## 이 프로젝트가 다루는 것

- **세 런타임을 같은 이미지와 API로 비교합니다.** 런타임 프로필이 `RuntimeClass`와 노드, GPU 요청을 정합니다. GPU 채점은 gVisor와 Kata + QEMU로 실습하고, CPU 전용 실습에서는 Kata + Cloud Hypervisor도 비교합니다. [격리 런타임 비교](concepts/02_isolation_runtimes.md)
- **on-policy 학습을 멈추지 않고 샌드박스를 업데이트합니다.** blue/green pool, golden 제출물 parity 검사, 배치(또는 group) 단위 버전 고정으로 reward 일관성을 유지합니다.
- **reward 무결성까지 다룹니다.** KernelBench 계열에서 보고된 reward hacking 중 추가 CUDA stream, 결과 캐싱, lazy tensor는 harness 설계로 막고, "벤치마크 때만 틀리기"에 대비해 측정 구간 출력의 합과 절댓값 합을 검사합니다. 두 값이 모두 허용 오차 안에 들면 일부 원소가 틀려도 통과할 수 있습니다.

## 아키텍처

### 만드는 것

![왼쪽은 학습 노드(EC2 GPU 노드 또는 HyperPod 노드)이고, 그 안에서 policy 모델과 vLLM이 GRPO로 on-policy 학습을 합니다(g5.2xlarge 또는 ml.g5.2xlarge). 오른쪽은 EC2 노드의 샌드박스 pool입니다. gVisor + nvproxy(g5.xlarge, A10G), Kata + QEMU(g4dn.metal, T4), Kata + Cloud Hypervisor(CPU 계층, c8i, nested virt, GPU는 실험적)의 세 pool이 같은 이미지를 쓰고, pool마다 프로필이 RuntimeClass와 노드를 정합니다. 커널 코드는 group 단위로 버전을 고정해 pool로 보내고, pool은 정확성과 speedup을 돌려줍니다.](images/figures/index--what-we-build.ko.svg)

*policy 모델이 쓴 커널 코드는 group 단위로 버전을 고정해 샌드박스 pool에 보냅니다. pool에서 측정한 정확성과 speedup을 reward로 씁니다. 그림의 Kata + Cloud Hypervisor pool은 CPU 전용 실습에 사용합니다.*

| 시나리오 | 학습 위치 | 샌드박스 위치 | 언제 |
|---|---|---|---|
| A. EC2 자체 운영 (기본) | EKS의 EC2 GPU 노드 (`g5.2xlarge`) | 같은 클러스터의 EC2 노드 | 모든 구성 요소를 직접 제어하고 싶을 때 |
| B1. HyperPod (HyperPod 기본) | HyperPod 인스턴스 그룹 (`ml.g5.2xlarge`) | HyperPod를 연결한 같은 EKS 클러스터의 EC2 노드 | 장시간 학습에 HyperPod의 노드 자동 교체와 job 재시작이 필요할 때 |
| B2. HyperPod | HyperPod `trainer` | HyperPod `sandbox` 그룹의 `ml.g5.xlarge` 2대에서 gVisor 실행 | CPU 워커도 HyperPod에서 운영할 때. [B2 실습](handson/scenarios/b/b2.md) |
| C. c8i 단독 (GPU 없음) | 없음 (모델 없는 reward 루프) | `c8i.2xlarge` 한 대의 CPU 샌드박스 (gVisor, Kata + CLH, Kata + QEMU) | GPU 쿼터 없이, 컴퓨트 시간당 약 0.57 USD로 런타임 비교와 버전 교체를 먼저 익히고 싶을 때 ([CPU 실습 (C)](handson/scenarios/c/index.md)) |

### 시나리오별 구성

A, B1, C는 프라이빗 EKS API를 제공하는 CDK 스택을 사용합니다. 관리형 B2는 HyperPod EKS 생성 마법사에서 제어 영역과 워커를 함께 구성합니다. C는 CPU 샌드박스에서 채점과 버전 교체를 실습합니다.

=== "A: EC2 GPU"

    [![시나리오 A: SSM 터널로 private EKS API에 접속하고, g5.2xlarge의 trainer가 g5.xlarge 두 대의 gVisor pool에 커널 코드를 보내는 구성](images/architecture/scenario-a.drawio.png)](images/architecture/scenario-a.drawio.png)

    *그림 요약: trainer와 gVisor pool이 모두 EKS의 EC2 노드에 있고, 모델은 NAT를 거쳐 Hugging Face Hub에서 받습니다.*

=== "B1: HyperPod 학습"

    [![시나리오 B1: trainer는 HyperPod 인스턴스 그룹에, gVisor pool은 EC2 노드에 있는 구성](images/architecture/scenario-b1.drawio.png)](images/architecture/scenario-b1.drawio.png)

    *그림 요약: trainer만 HyperPod 인스턴스 그룹(ml.g5.2xlarge)으로 옮겨 S3의 lifecycle 스크립트로 부팅하고, 샌드박스는 A와 같은 EC2 gVisor 노드에 남습니다.*

=== "B2 (CPU와 GPU 모두 HyperPod)"

    [![EKS 제어 영역과 HyperPod 시스템, 학습, 채점 워커](images/architecture/scenario-b2.drawio.png?layout=aws)](images/architecture/scenario-b2.drawio.png?layout=aws)

    CPU 한 대가 공용 Pod를 맡고, GPU 한 대가 모델을 학습합니다. 나머지 GPU 두 대에서는 모델이 만든 코드를 채점합니다. [B2 따라 하기](handson/scenarios/b/b2.md), [B1과 B2 비교 슬라이드 (PPTX)](slides/gpu-sandbox-theory.pptx)

=== "C: CPU 전용"

    [![시나리오 C: GPU 없이 c8i.2xlarge 한 대에 세 런타임의 CPU pool이 있는 구성](images/architecture/scenario-c.drawio.png)](images/architecture/scenario-c.drawio.png)

    *그림 요약: GPU 노드 없이 c8i.2xlarge 한 대에 세 런타임의 pool이 서고, system 노드의 simulate Job이 trainer 대신 golden 코드를 보냅니다.*

### 요청 경로

- trainer는 샌드박스에 요청할 때 routing ConfigMap(`sandbox-routing`)의 snapshot을 읽어 런타임과 버전을 정합니다. 한 reward batch의 답안은 모두 같은 pool에서 채점합니다.
    - **학습 중에 v2로 바꾸면**: batch에 새로 채점할 답안이 있으면 같은 batch에서 이전 pool의 결과가 캐시된 답안도 v2 pool에 다시 보냅니다.
    - **배치의 모든 답안에 같은 pool의 채점 결과가 캐시돼 있으면**: 전환 뒤에도 샌드박스에 재요청할 필요 없이 캐시된 결과를 그대로 반환합니다.
    - **한 batch 안에서 전환이 거듭되면**: 세 번째 요청에서 batch 전체를 한 pool에 보내므로, 한 batch는 항상 한 버전으로 채점됩니다.
- trainer는 headless Service를 CoreDNS로 풀어 Ready 상태인 pod에 `POST /v1/evaluate`를 직접 보냅니다. 바쁜 pod는 `503`을 돌려주고, trainer는 다른 pod로 다시 시도합니다.
- 요청에는 audience가 `gpu-sandbox`인 projected ServiceAccount 토큰이 붙고, pod는 JWKS로 토큰을 오프라인 검증합니다. `sandbox` 네임스페이스는 default-deny라서 `rl-trainer`에서 label이 붙은 pod만 접속할 수 있습니다.

노드 그룹과 네임스페이스, 화살표별 설명은 [전체 흐름](handson/index.md)에, Production 구성(Karpenter NodePool, sandbox gateway, veRL on KubeRay)은 [Production 00 아키텍처](production/00_architecture.md)에 있습니다. 그림 원본(`.drawio`)은 `diagrams/` 폴더에 있습니다.

## 시작하기

- **무엇부터 할지 모르겠다면** → [학습 코스 고르기](learning_paths.md)에서 질문 몇 개로 코스를 고르세요(무료 코스부터 안내합니다).
- **바로 실습하려면** → [시작하기](handson/start.md)의 로컬 smoke test를 마친 뒤 [전체 흐름](handson/index.md)으로 진행하세요.
- **런타임 차이가 헷갈린다면** → [02 격리 런타임 비교](concepts/02_isolation_runtimes.md)의 [AWS에서 각 런타임을 실행할 수 있는 위치](concepts/02_isolation_runtimes.md#aws에서-각-런타임을-실행할-수-있는-위치) 표
- **고객 상황에 맞는 조합을 골라야 한다면** → [05 상황별 선택 가이드](concepts/05_decision_guide.md)
- **용어가 낯설다면** → [용어 사전](reference/glossary.md)

## 트랙 구성

| 트랙 | 목적 | 범위 |
|---|---|---|
| [핸즈온 (Getting Started)](handson/index.md) | 하루 안에 세 런타임과 on-policy 루프를 직접 확인 | CDK 스택(private API endpoint)과 SSM 터널, TRL GRPO(1.5B, LoRA, vLLM colocate), 샌드박스 v1에서 v2로 무중단 교체 |
| [Production Ready](production/00_architecture.md) | 운영 환경 설계와 확장 | Karpenter NodePool, sandbox gateway, 보안 위협 모델, reward 무결성, veRL on KubeRay, observability, 비용 |
| [Agent Sandbox 확장](concepts/06_agent_sandbox.md) | multi-turn 에피소드마다 전용 샌드박스 | kubernetes-sigs/agent-sandbox의 SandboxTemplate, SandboxWarmPool, SandboxClaim. gVisor와 Kata 모두 RuntimeClass로 선택 |
| [CloudFront 데모 배포](reference/demo_site.md) | 실행 기록을 브라우저에서 재생 | 비공개 S3 + CloudFront(OAC, HTTPS, 보안 헤더). 방문자 요청은 클러스터나 GPU로 전달되지 않음 |

## 검증 상태

!!! warning "직접 확인해야 하는 범위"
    - **실행한 것**: 실습 계정에서 시나리오 A(gVisor GPU, `g5`), 시나리오 C(CPU 런타임 세 개)와 버전 교체, Kata GPU(`g4dn.metal`), 다섯 개 pool의 런타임 벤치마크([런타임 벤치마크](handson/benchmarks/index.md))를 실행하고 데모 사이트를 공개했습니다. 실험용 Kata CLH GPU는 VM이 시작되지 않았습니다. 날짜별 실행 기록은 [검증된 사실과 출처](reference/sources.md#aws-실행-기록)에 있습니다.
    - **검증 범위**. 시나리오 A의 [학습 중 전환과 롤백](handson/scenarios/a/pool_update.md#switch-batches)과 `--finish`까지 실행했습니다. 관리형 B2에서도 HyperPod 워커로 GRPO 한 스텝을 완료했습니다.
    - **수치의 출처**: 가격과 버전 같은 수치는 직접 측정한 값이 아니라 공식 문서와 공개 자료에서 가져온 값입니다.
    - **로컬 테스트**: 확인 범위는 [시작하기](handson/start.md)에 있습니다.

!!! warning "비용"
    GPU 인스턴스는 실행되는 동안 과금되고, `g4dn.metal`은 시간당 약 7.8 USD입니다(us-east-1과 us-west-2 온디맨드 요금). 쉬는 동안에는 GPU 노드 수를 0으로 줄이고, 실습을 마치면 [정리](handson/cleanup.md)를 반드시 실행하세요.

!!! note "기준 시점: 2026-11"
    가격과 소프트웨어 버전, 리전별 서비스 지원 범위는 2026-11 기준입니다. 배포 전에는 공식 문서에서 온디맨드 요금, gVisor 릴리스와 Kata 버전, NVIDIA 드라이버 지원 목록, EKS와 HyperPod 지원 버전을 다시 확인하세요. 확인할 항목과 링크는 [검증된 사실과 출처](reference/sources.md)에 모았습니다.

## Disclaimer

이 가이드는 저자의 개인 견해와 조사 결과를 정리한 것으로, 저자가 재직 중인 회사의 공식 문서나 입장을 대변하지 않습니다. 내용이 공식 문서와 다르면 공식 문서가 우선합니다.

## License

코드와 문서는 [MIT](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/LICENSE)이고, 모델 라이선스는 별개입니다. 기본 모델 `Qwen/Qwen2.5-Coder-1.5B-Instruct`와 Production 예시의 `Qwen/Qwen2.5-Coder-7B-Instruct`는 Apache-2.0이고, `Qwen2.5-Coder-3B-Instruct`는 비상업 라이선스여서 실습 모델에서 제외했습니다.
