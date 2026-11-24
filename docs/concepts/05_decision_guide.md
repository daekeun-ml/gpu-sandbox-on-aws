# 상황별 선택 가이드

이 핸즈온에서는 모델이 만든 코드를 GPU에서 실행하고 그 결과를 학습 보상에 반영합니다. **클러스터와 워커를 어떻게 운영할지** 먼저 고른 뒤, **채점 GPU를 샌드박스에 어떻게 연결할지** 정하세요.

![EC2 자체 운영(A)과 혼합형(B1)은 EC2에서 gVisor 또는 Kata + QEMU로 채점합니다. HyperPod 관리형(B2)은 HyperPod에서 gVisor로 채점합니다.](../images/figures/concepts-05_decision_guide--exercise-path.ko.svg?v=2)

## 1. 클러스터와 워커를 어떻게 운영할까요? { #플랫폼-선택 }

세 구성 모두 Kubernetes 제어 영역은 Amazon EKS가 관리합니다. 달라지는 것은 클러스터를 만드는 절차와 학습 및 채점 워커를 관리하는 방식입니다.

- **EC2 자체 운영 (A)** — 학습 GPU와 채점 GPU의 인스턴스, 이미지, 노드 그룹을 직접 정하고 싶을 때 고르세요. CDK로 EKS 클러스터를 만들고, EC2의 학습 노드가 별도의 EC2 채점 노드에 코드를 보냅니다. [EC2 GPU 실습](../handson/scenarios/a/index.md)
- **EC2와 HyperPod 혼합형 (B1)** — EC2 채점 pool을 그대로 쓰면서 학습 노드의 장애 복구와 Job 재시작을 HyperPod에 맡기고 싶을 때 적합합니다. 기존 EKS 클러스터에 HyperPod 학습 그룹을 연결하므로 채점 환경까지 옮길 필요가 없습니다. [HyperPod 학습과 EC2 채점 실습](../handson/scenarios/b/b1.md)
- **HyperPod 관리형 (B2)** — EKS 클러스터를 새로 만들고 모든 워커를 HyperPod에서 운영하려면 B2를 고르세요. 배포 스크립트가 클러스터와 시스템, 학습, 채점용 인스턴스 그룹을 함께 만듭니다. 샌드박스 런타임은 채점 그룹에 직접 설치합니다. [HyperPod 관리형 실습](../handson/scenarios/b/b2.md)

## 2. GPU 샌드박스는 gVisor와 Kata 중 어느 쪽이 맞을까요? { #런타임-선택 }

**일반 GPU 인스턴스에서 시작한다면 gVisor**가 기본입니다. 샌드박스 안의 `nvproxy`가 허용한 요청을 노드의 NVIDIA 드라이버에 전달하므로 별도 VM을 띄울 필요가 없습니다. 채점에는 A와 B1에서 EC2의 A10G를, B2에서 HyperPod의 A10G를 사용합니다. 설치할 때는 노드 드라이버가 해당 gVisor 버전의 지원 목록에 있는지 확인하세요. [EC2에서 gVisor 준비하기](../handson/common/02_runtimes/gvisor.md) / [HyperPod 채점 워커 준비하기](../handson/common/02_runtimes/b2_workers.md)

**샌드박스마다 독립된 Linux 커널이 필요하다면 Kata + QEMU**를 고르세요. 샌드박스마다 가상 머신(VM)을 띄우고, VM 안의 NVIDIA 드라이버가 직접 할당받은 물리 GPU를 제어합니다. 이 실습에서는 A나 B1에 EC2 `g4dn.metal`을 추가해 VM마다 T4를 한 장씩 연결합니다. 이때는 베어메탈 인스턴스의 전체 요금과 새 VM을 띄우는 데 걸리는 시간도 고려하세요. [Kata VM에 GPU 연결하기](../handson/common/02_runtimes/kata.md#kata-gpu)

## 실습 시작하기 { #실습-경로별-확인-항목 }

구성을 골랐다면 [플랫폼별 인스턴스와 쿼터](04_platforms_and_instances.md)에서 필요한 워커 수를 확인하고, [클러스터 프로비저닝](../handson/common/01_provision/index.md)에서 같은 시나리오 탭을 따라가세요. 기본 채점 pool은 세 GPU 경로 모두 gVisor입니다. A와 B1에서는 Kata GPU pool을 추가해 두 방식을 비교할 수 있습니다.

??? note "GPU를 확보하기 어렵거나 비용이 부담된다면"
    시나리오 C에서는 준비된 답안을 CPU로 채점하고 샌드박스 버전을 교체합니다. 적은 비용으로 채점 흐름부터 익히고, 나중에 GPU 실습에서 CUDA 커널의 정확도와 속도를 확인하세요. [CPU로 실습하기](../handson/scenarios/c/index.md)
