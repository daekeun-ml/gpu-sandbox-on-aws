# 플랫폼과 인스턴스 선택

!!! info "TL;DR"
    **시나리오 A**는 학습과 채점을 모두 EC2에서 운영합니다. **시나리오 B1**은 EC2 채점 환경을 유지하고 학습만 HyperPod에 맡깁니다. **시나리오 B2**에서는 시스템용 CPU 워커와 학습 및 채점용 GPU 워커를 모두 HyperPod에서 운영합니다.

    HyperPod 워커는 AWS가 관리하는 별도 VPC에서 실행되며, 내 계정의 VPC와는 네트워크 인터페이스(ENI)로 연결됩니다. [AWS 공식 구성도](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks.html)

    학습 GPU는 모델에 필요한 메모리에 맞춰 고르세요. 채점 노드를 고를 때는 코드를 시험할 GPU와 샌드박스의 격리 방식을 먼저 정하세요.

## 시나리오별 아키텍처

=== "A (EC2 GPU)"

    학습과 채점을 모두 EC2에서 실행합니다. 학습 노드가 모델이 만든 코드를 같은 EKS 클러스터의 gVisor GPU 샌드박스에 보냅니다.

    ![같은 EKS 클러스터에서 EC2 학습 노드가 gVisor GPU 샌드박스에 코드를 보내고 채점 결과를 받는 구성](../images/architecture/scenario-a.drawio.png)

=== "B1 (혼합형)"

    모델은 HyperPod에서 학습하고, 코드는 EC2에서 채점합니다. 기존 EKS 클러스터에 HyperPod 학습 그룹을 연결하는 구성입니다.

    ![HyperPod에서 학습하고 같은 EKS 클러스터의 EC2 GPU 노드에서 채점합니다.](../images/architecture/scenario-b1.drawio.png)

=== "B2 (HyperPod)"

    EKS 제어 영역이 각 pod를 HyperPod 워커에 배치합니다. `system` 그룹은 클러스터 서비스를, `trainer`는 모델 학습을, `sandbox`는 GPU 채점을 맡습니다.

    ![EKS에 연결한 HyperPod의 system, trainer, sandbox 인스턴스 그룹이 시스템 서비스, 학습, 채점을 각각 맡습니다.](../images/architecture/scenario-b2.drawio.png?layout=aws)

=== "C (CPU 선택 실습)"

    GPU를 확보하기 어렵거나 비용이 부담될 때 고르는 구성입니다. 시스템 노드의 시뮬레이터가 준비된 답안을 보내면 `c8i` 노드의 CPU 샌드박스가 채점합니다.

    ![시스템 노드의 시뮬레이터가 c8i 노드에서 실행 중인 CPU 채점 pool에 답안을 보냅니다.](../images/architecture/scenario-c.drawio.png)

<span id="한-클러스터에서-역할을-나누는-이유"></span>

## GPU 실습의 기본 워커 구성 { #시나리오-a-b1-b2-c-비교 }

학습 노드에서는 모델이 답안을 만들고 가중치를 업데이트합니다. 채점 노드에서는 그 답안을 실행해 정확도와 속도를 확인합니다.

| 실습 | 모델을 학습하는 노드 | 코드를 채점하는 노드 |
|---|---|---|
| [A (EC2 GPU)](../handson/scenarios/a/index.md) | EC2 `g5.2xlarge` × 1 | EC2 `g5.xlarge` × 2 |
| [B1 (HyperPod와 EC2)](../handson/scenarios/b/b1.md) | HyperPod `ml.g5.2xlarge` × 1 | EC2 `g5.xlarge` × 2 |
| [B2 (HyperPod)](../handson/scenarios/b/b2.md) | HyperPod `ml.g5.2xlarge` × 1 | HyperPod `ml.g5.xlarge` × 2 |

**시스템 워커**에서는 CoreDNS 같은 클러스터 서비스가 실행됩니다. A와 B1은 EC2 `m6i.large` 인스턴스 2개를 시스템 워커로 사용합니다. B2의 `system` 그룹에는 `ml.m5.xlarge` 인스턴스가 1개 있습니다. 학습과 채점에 쓰는 GPU 워커까지 합하면 B2의 HyperPod 워커는 총 4개입니다.

<span id="더-살펴보기"></span>
<span id="b1에서-학습-gpu와-채점-gpu-구분하기"></span>

## B1과 B2에서 달라지는 것

두 경로 모두 HyperPod 학습 노드의 A10G에서 모델을 학습합니다. 차이는 **나머지 워커를 누가 관리하느냐**입니다.

![B1은 HyperPod가 학습 워커만 관리하고 EC2가 시스템과 채점을 맡습니다. B2는 세 역할 모두 HyperPod 인스턴스 그룹에 배치합니다.](../images/figures/concepts-04_platforms_and_instances.ko.svg?v=2)

- **B1**에서는 CDK로 만든 EKS 클러스터에 HyperPod 학습 그룹을 연결합니다. 기존 EC2 채점 pool을 계속 쓰거나 EC2에 Kata GPU 노드를 추가하려는 경우에 맞습니다. EKS API에는 SSM 터널을 통해 접속합니다. [B1 학습 노드 연결](../handson/common/02_runtimes/b1_trainer.md)
- **B2**에서는 `scripts/hyperpod/create_managed.sh`를 실행하면 CloudFormation이 EKS 클러스터와 HyperPod 인스턴스 그룹 세 개를 함께 만듭니다. `kubectl`은 EKS API에 직접 접속합니다. 두 채점 노드에는 각각 gVisor를 설치하고 A10G 한 장씩을 샌드박스에 배정합니다. [B2 클러스터와 워커 만들기](../handson/common/01_provision/hyperpod.md)

<span id="hyperpod가-trainer에-제공하는-기능"></span>
<span id="복구-기능과-체크포인트는-각각-필요합니다"></span>

??? question "학습 노드가 교체되면 중단된 지점부터 이어질까요?"
    HyperPod는 장애가 난 GPU 노드를 복구하고, 학습 오퍼레이터는 Job을 다시 시작합니다. 마지막 학습 단계부터 이어가려면 새 pod가 이전 체크포인트를 읽어야 합니다. 이 실습의 `/outputs`는 pod를 삭제하면 함께 사라지는 `emptyDir`입니다. 노드 교체 후에도 학습을 이어가려면 체크포인트를 공유 스토리지에 보관하세요. [HyperPod 학습 Job과 체크포인트](../handson/scenarios/b/b1.md)

<span id="hyperpod가-샌드박스-계층에-제공하지-않는-기능"></span>
<span id="b2에서-채점-노드의-드라이버를-맞추는-이유"></span>

??? question "B2에서 채점 워커의 드라이버만 바꾸는 이유는 뭔가요?"
    gVisor의 `nvproxy`는 지원하는 버전의 NVIDIA 드라이버에 GPU 요청을 전달합니다. 실습의 기본 HyperPod 이미지에 들어 있던 `595.112.07`은 사용한 gVisor 버전의 지원 목록에 없어, 두 채점 워커에 `580.178.04`를 설치한 뒤 HyperPod를 통해 재부팅했습니다. 학습 워커는 GPU를 직접 사용하므로 기본 드라이버를 유지했습니다. [채점 워커 준비와 CUDA 실행 화면](../handson/common/02_runtimes/b2_workers.md)

## 채점 런타임에 맞는 인스턴스 { #인스턴스-선택 }

- **A10G에서 GPU 코드를 채점하려면** A와 B1에서는 `g5.xlarge`, B2에서는 `ml.g5.xlarge`에 gVisor를 설치합니다. L4가 목표라면 EC2 `g6.xlarge`가 후보입니다. 노드의 드라이버 버전이 gVisor와 맞는지 먼저 확인하고, 기준 코드와 제출 코드 모두 L4에서 실행 시간을 측정하세요. [gVisor GPU 준비](../handson/common/02_runtimes/gvisor.md)
- **샌드박스마다 별도 Linux 커널과 GPU가 필요하다면** A 또는 B1의 EC2에 `g4dn.metal`을 추가합니다. Kata + QEMU가 띄운 가상 머신마다 이 서버의 T4를 한 장씩 직접 연결합니다. [Kata VM에 GPU 연결하기](../handson/common/02_runtimes/kata.md#kata-gpu)

<span id="리전별-vcpu-쿼터"></span>

## 배포 전 확인할 쿼터와 워커 비용 { #핸즈온-구성의-시간당-비용-추정 }

EC2 쿼터는 **vCPU 수**를 기준으로 하고, SageMaker HyperPod의 `for cluster usage` 쿼터는 **인스턴스 유형별 수량**을 기준으로 합니다. B1은 학습과 채점에 서로 다른 서비스를 사용하므로 두 쿼터를 모두 확인하세요.

| 기본 구성 | EC2 쿼터 여유분 | HyperPod 쿼터 여유분 | 워커 비용 (USD/시간) |
|---|---|---|---:|
| A | Standard 6, G/VT 16 | — | 3.416 |
| B1 | Standard 6, G/VT 8 | `ml.g5.2xlarge` × 1 | 3.719 |
| B2 | 별도 EC2 인스턴스 없음 | `ml.m5.xlarge` × 1, `ml.g5.2xlarge` × 1, `ml.g5.xlarge` × 2 | 4.561 |

워커 비용은 실습 요금표의 온디맨드 단가를 합한 추정치입니다(A와 B1은 `us-west-2`, B2는 `us-east-1`). A와 B1의 Standard 쿼터에는 SSM 접속용 `t4g.nano`의 2 vCPU가 포함됩니다. 비용 열에는 워커만 합산했으므로 접속 인스턴스, EKS 제어 영역, NAT 게이트웨이, 스토리지와 데이터 전송 요금은 별도입니다. [비용 계산 근거](../production/08_cost.md) / [실습 리소스 정리](../handson/cleanup.md)

??? note "기본 구성에 노드를 추가한다면"
    - **A에서 학습 중 gVisor 버전 교체** — 기존 pool과 새 pool을 함께 실행하려면 `g5.xlarge` 인스턴스 2개가 더 필요합니다. G/VT는 24 vCPU, 추가 워커 비용은 시간당 2.012 USD입니다. [학습 중 pool 교체](../handson/scenarios/a/pool_update.md)
    - **A 또는 B1에서 Kata GPU 추가** — `g4dn.metal` 인스턴스를 하나 추가하려면 G/VT 96 vCPU가 더 필요합니다. 실습 요금표에서 이 노드는 시간당 7.824 USD입니다. AMI를 만드는 동안에는 임시 빌더의 Standard 2 vCPU도 필요합니다. [Kata GPU 실습](../handson/common/02_runtimes/kata.md#kata-gpu)

[선택한 시나리오의 클러스터 준비하기](../handson/common/01_provision/index.md) / [B2의 SageMaker 쿼터 세 가지 확인하기](../handson/common/01_provision/hyperpod.md)

??? note "GPU 용량을 구하기 어렵거나 예산이 부족하다면"
    시나리오 C에서는 모델을 학습하지 않고 준비된 답안으로 채점과 pool 버전 교체를 연습합니다. 시스템 서비스는 `m6i.large` 인스턴스 2개에서, 채점은 `c8i.2xlarge` 인스턴스 1개에서 실행합니다. `c8i`에서 중첩 가상화를 켜면 gVisor, Kata + QEMU, Kata + Cloud Hypervisor를 GPU 없이 비교할 수 있습니다.

    접속 인스턴스를 포함해 EC2 Standard 14 vCPU가 필요합니다. 이 구성의 워커 비용은 온디맨드 기준 시간당 약 0.567 USD입니다. [CPU 실습과 비용 안내](../handson/scenarios/c/index.md)

<span id="적용-범위와-한계"></span>

??? note "실행 기록과 공식 문서"
    - [시나리오별 AWS 실행 기록](../reference/sources.md#aws-실행-기록) / [런타임 벤치마크](../handson/benchmarks/index.md#runtime-results)
    - [HyperPod의 노드 복구](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html) / [HyperPod 학습 오퍼레이터](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html)
    - [EC2 온디맨드 요금](https://aws.amazon.com/ec2/pricing/on-demand/) / [SageMaker AI 요금](https://aws.amazon.com/sagemaker/ai/pricing/)
