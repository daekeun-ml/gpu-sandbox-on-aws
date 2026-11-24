# GPU Sandbox on AWS

모델이 작성한 코드를 학습 서버와 분리된 GPU 샌드박스에서 실행합니다. 이 가이드에서는 Amazon EKS에서 코드의 정확도와 실행 속도를 확인하고, 그 결과를 강화학습 보상에 반영하는 과정을 따라갑니다.

<a id="aws-network" href="images/figures/index--aws-architecture.svg?v=2">
<picture>
  <source media="(max-width: 34em)" srcset="images/figures/index--aws-architecture-compact.svg?v=2" width="360" height="716">
  <img class="off-glb" src="images/figures/index--aws-architecture.svg?v=2" width="824" height="521" alt="A와 B1은 접속용 EC2를 거쳐 EKS API에 접속하고 EC2에서 코드를 채점합니다. B2는 EKS API에 직접 접속하며 시스템 CPU 한 대, 학습 GPU 한 대, 채점 GPU 두 대를 모두 HyperPod에 배치합니다.">
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

## 시나리오별 구성

=== "A EC2 GPU"

    EC2의 GPU 노드 한 대에서 모델을 학습하고, 별도 GPU 노드에서 코드를 채점합니다. [EC2 GPU 실습](handson/scenarios/a/index.md)

    [![EKS 클러스터에서 EC2 학습 노드가 별도의 gVisor GPU 샌드박스 두 대에 코드를 보내는 구성](images/architecture/scenario-a.drawio.png)](images/architecture/scenario-a.drawio.png)

=== "B1 혼합형"

    SageMaker HyperPod에서 모델을 학습하고, 같은 EKS 클러스터의 EC2 GPU 노드에서 코드를 채점합니다. [HyperPod 학습과 EC2 채점 실습](handson/scenarios/b/b1.md)

    [![HyperPod의 학습 노드와 EC2의 채점 노드를 연결한 EKS 구성](images/architecture/scenario-b1.drawio.png)](images/architecture/scenario-b1.drawio.png)

=== "B2 HyperPod"

    모든 워커를 HyperPod에 배치합니다. CPU 한 대가 클러스터 서비스를 맡고, GPU 한 대에서 모델을 학습합니다. 나머지 GPU 두 대에서 코드를 채점합니다. [HyperPod에서 학습과 채점하기](handson/scenarios/b/b2.md)

    [![HyperPod 인스턴스 그룹에 시스템, 학습, 채점 워커를 배치한 EKS 구성](images/architecture/scenario-b2.drawio.png?layout=aws)](images/architecture/scenario-b2.drawio.png)

=== "C CPU"

    GPU 없이 EC2 `c8i` 한 대에서 gVisor, Kata + QEMU, Kata + Cloud Hypervisor로 같은 답안을 채점합니다. 채점 도중 샌드박스 버전을 바꾸는 실습도 진행합니다. [CPU로 실습하기](handson/scenarios/c/index.md)

    [![c8i CPU 노드 하나에서 세 가지 샌드박스 런타임을 비교하는 구성](images/architecture/scenario-c.drawio.png)](images/architecture/scenario-c.drawio.png)

## 시작하기

- **AWS에서 직접 실행하려면** 빠른 시작 스크립트에서 시나리오를 고르세요. 클러스터와 채점 pool을 준비하는 공통 절차부터 시작합니다. [핸즈온 빠른 시작](handson/index.md#quickstart)
- **실행 화면을 먼저 보려면** 공개 데모에서 답안을 골라 채점 기록을 재생해 보세요. [데모 열기](https://dohbsn4kn34ya.cloudfront.net/#try)

??? note "벤치마크, 선택 실습, 운영 가이드"

    - [런타임별 벤치마크 결과와 측정 조건](handson/benchmarks/index.md#runtime-results)
    - [학습 도중 채점 pool을 교체하는 실습](handson/scenarios/a/pool_update.md#switch-batches)
    - [Agent Sandbox로 여러 턴에 걸쳐 답안 채점하기](handson/extensions/multi_turn.md)
    - [운영 환경에서 샌드박스와 GPU 노드 확장하기](production/00_architecture.md)

??? note "이 가이드에 관하여 / 라이선스"
    이 가이드는 저자의 개인 견해와 조사 결과를 정리한 것으로, 저자가 재직 중인 회사의 공식 문서나 입장을 대변하지 않습니다. 내용이 공식 문서와 다르면 공식 문서가 우선합니다.

    코드와 문서는 [MIT](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/LICENSE)이고, 모델 라이선스는 별개입니다. 기본 모델 `Qwen/Qwen2.5-Coder-1.5B-Instruct`와 Production 예시의 `Qwen/Qwen2.5-Coder-7B-Instruct`는 Apache-2.0이고, `Qwen2.5-Coder-3B-Instruct`는 비상업 라이선스여서 실습 모델에서 제외했습니다.
