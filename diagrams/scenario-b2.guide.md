**한국어** | [English](scenario-b2.guide.en.md)

# 시나리오 B2 · 시스템, 학습, 채점을 모두 HyperPod에서 실행하기

EKS는 Kubernetes API와 스케줄러를 제공합니다. `us-east-1`에서 이 클러스터에 등록된 워커 네 대는 모두 SageMaker HyperPod 인스턴스 그룹 소속입니다.

[![EKS 제어 영역과 HyperPod의 system, trainer, sandbox 그룹](scenario-b2.drawio.png)](scenario-b2.drawio.png)

## 구성도 읽기

1. **위쪽의 CloudFormation과 EKS**. SageMaker HyperPod의 EKS 생성 마법사가 쓰는 리전별 템플릿으로 VPC, EKS 제어 영역과 HyperPod 클러스터를 함께 만듭니다. 운영자 PC에서 `aws eks update-kubeconfig`로 접속합니다.
2. **아래쪽의 세 그룹**. `system`의 `ml.m5.xlarge` 한 대에서 CoreDNS와 CPU 벤치마크 Job이 실행됩니다. `trainer`의 `ml.g5.2xlarge` 한 대는 GRPO 학습을 맡습니다. `sandbox`의 `ml.g5.xlarge` 두 대에는 각각 A10G 한 장과 gVisor v1 채점 Pod 한 개가 있습니다.
3. **학습과 채점 사이의 화살표**. 모델이 생성한 코드를 트레이너가 v1 풀에 보냅니다. 채점 Pod가 코드의 판정과 실행 시간을 돌려주면 트레이너가 이를 보상으로 사용합니다. 한 스텝에서 제출한 코드 12개 모두 같은 버전의 풀에서 채점했습니다.

## 노드에서 확인한 것

기본 HyperPod 이미지의 NVIDIA 드라이버 `595.112.07`은 gVisor `20261109.0`의 지원 목록에 없었습니다. 채점 노드 두 대에 `580.178.04`를 설치하고 HyperPod API로 재부팅했습니다. 재부팅 후 gVisor Pod 안에서 A10G의 CUDA 연산을 확인했습니다. 학습 워커는 기본 드라이버를 사용했습니다.

학습이 끝난 뒤 `system`과 `trainer`가 같은 고정 커널을 각각 32번씩 제출해 모두 성공했습니다. 두 번 모두 같은 채점 풀을 사용했습니다. [배포 순서와 실행 화면](../docs/handson/07_hyperpod_b2.md) · [요청별 채점 시간과 처리량](../docs/handson/08_benchmark.md#hyperpod-b2) · [편집용 draw.io 파일](scenario-b2.drawio)
