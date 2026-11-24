# 플랫폼과 인스턴스 선택

!!! info "TL;DR"
    trainer는 모델을 학습시키고 샌드박스는 모델의 답을 실행해 채점합니다. 두 역할의 노드는 따로 고를 수 있습니다. HyperPod가 필요한지 판단하려면 먼저 학습 노드에 장애가 났을 때 어떻게 복구할지 살펴보세요.

## 한 클러스터에서 역할을 나누는 이유

학습과 채점에서 GPU가 하는 일이 다릅니다. trainer는 모델을 메모리에 올리고 답안 생성과 모델 업데이트를 반복합니다. 샌드박스는 제출물을 실행합니다. 여기서는 작업의 격리 방식과 측정할 GPU가 중요합니다. 노드를 분리하면 학습 쪽을 바꿀 때 샌드박스 런타임도 함께 바꿀 필요가 줄어듭니다.

**Amazon EKS**는 Kubernetes 클러스터를 운영하는 서비스입니다. **EC2** 인스턴스는 그 클러스터에 연결하는 실행 노드로 쓸 수 있습니다. B1에서는 **HyperPod**가 학습 노드를 관리하고, EC2 노드는 같은 EKS 클러스터에서 샌드박스를 실행합니다. 관리형 B2에서는 시스템, 학습, 채점 노드를 모두 HyperPod 인스턴스 그룹에 둡니다.

## 시나리오 A, B1, B2, C 비교

| 시나리오 | 학습 | 샌드박스 | 사용 목적 |
|---|---|---|---|
| A | EC2 GPU trainer | EC2 GPU | EKS에서 학습과 GPU 채점 연결 |
| B1 | HyperPod trainer | EC2 GPU | trainer 노드 복구와 Job 재시작 |
| B2 | HyperPod `trainer` | HyperPod `sandbox` | 시스템 Pod, 학습, 채점을 각각의 HyperPod 그룹에 배치 |
| C | 모델 없이 시뮬레이터 실행 | EC2 `c8i.2xlarge`의 CPU pool | GPU 없이 런타임 비교, 채점, 버전 교체 |

A, B1, C는 `us-west-2`에서, [관리형 B2](../handson/scenarios/b/b2.md)는 `us-east-1`에서 실행했습니다.

B1에서는 학습과 채점에 필요한 조건을 각각 맞출 수 있습니다. 학습 노드에는 HyperPod의 Job 재시작 기능을 적용하고, EC2 채점 노드에는 gVisor가 지원하는 드라이버나 Kata에 필요한 가상화 환경을 그대로 둡니다. 관리형 B2는 등록된 채점 노드에 gVisor가 지원하는 드라이버를 설치하고 HyperPod API로 재부팅합니다.

## 시나리오별 아키텍처

아래 탭에서 시나리오를 선택하세요.

=== "A: EC2 GPU"

    ![같은 EKS 클러스터에서 trainer와 GPU 샌드박스가 별도의 EC2 노드 그룹에 배치됩니다.](../images/architecture/scenario-a.drawio.png)

    **그림 설명**　운영 PC는 SSM 터널을 통해 EKS의 프라이빗 API에 접속합니다(그림의 `kubectl tunnel`). 학습 중에는 `GRPO trainer Job`이 모델이 생성한 코드를 gVisor pool에 보냅니다(`kernel code` 화살표). pool은 GPU에서 코드를 실행해 결과가 맞는지, 얼마나 빠른지 확인합니다. trainer는 이 채점 결과로 reward를 계산합니다.

    **차이점**　학습과 채점 모두 EC2에서 직접 운영하는 기본 GPU 구성입니다. [시나리오 A 실습](../handson/scenarios/a/index.md)

=== "B1: HyperPod 학습"

    ![HyperPod trainer와 EC2 GPU 샌드박스가 같은 EKS 클러스터에 연결됩니다.](../images/architecture/scenario-b1.drawio.png)

    **그림 설명**　EKS에 `HyperPodPyTorchJob`을 제출하면 training operator가 HyperPod 학습 노드에서 trainer를 실행합니다. trainer는 같은 EKS 클러스터의 EC2 샌드박스 pool에 코드를 보내고(`kernel code` 화살표), 샌드박스는 GPU에서 코드를 실행해 채점 결과를 돌려줍니다.

    **차이점**　A와 달리 학습 노드를 HyperPod에서 관리하므로 노드 복구와 Job 재시작 기능을 이용할 수 있습니다. [시나리오 B1 실습](../handson/scenarios/b/b1.md)

=== "B2 (CPU와 GPU 모두 HyperPod)"

    [![Amazon EKS가 Pod를 배치하고 HyperPod의 system, trainer, sandbox 그룹이 실행하는 B2 구성도](../images/architecture/scenario-b2.drawio.png?layout=aws)](../images/architecture/scenario-b2.drawio.png?layout=aws)

    `system`은 CoreDNS를, `trainer`는 GRPO Job을, `sandbox`는 gVisor 채점을 맡습니다. Kubernetes API는 EKS에서 제공합니다. [B2 배포 실습](../handson/scenarios/b/b2.md)

=== "C: CPU 전용"

    ![시스템 노드의 시뮬레이터가 c8i 노드의 CPU 샌드박스 pool에 평가를 요청합니다.](../images/architecture/scenario-c.drawio.png)

    **그림 설명**　시스템 노드의 `simulate and probe Jobs`는 예상 채점 결과를 아는 테스트 코드(`golden code`)를 c8i 노드의 Kata CPU v1 pool에 보냅니다. 라우팅을 v2로 바꾸면 시뮬레이터 로그에서도 v2의 채점 결과를 확인할 수 있습니다. 같은 노드의 gVisor와 Kata + QEMU CPU pool은 검증과 벤치마크에 쓰입니다.

    **차이점**　모델 학습과 GPU 없이 gVisor와 Kata의 채점 및 버전 교체를 실습합니다. [시나리오 C 실습](../handson/scenarios/c/index.md)

## 복구 기능과 체크포인트는 각각 필요합니다

HyperPod는 문제가 생긴 노드를 복구하고 training operator가 Job을 다시 시작할 수 있게 합니다. 이전 학습 상태에서 이어가려면 새 pod에서도 체크포인트를 읽을 수 있어야 합니다. 실습에서 체크포인트를 보관한 `emptyDir`는 pod를 삭제하면 함께 사라집니다. B1 실습에서는 노드 교체 후 체크포인트로 학습을 재개하는 과정까지 시험하지는 않았습니다.

[HyperPod 핸즈온](../handson/scenarios/b/b1.md)에 배치 절차가 있습니다. 샌드박스에 어떤 노드가 필요한지는 [런타임 비교](02_isolation_runtimes.md)에서 확인하세요.

## B1에서 학습 GPU와 채점 GPU 구분하기

B1에서는 HyperPod 학습 노드(`ml.g5.2xlarge`)의 A10G 한 장으로 모델의 답안을 생성하고 가중치를 업데이트했습니다. 학습 Job의 `Completed`는 GRPO 한 스텝을 마쳤다는 뜻입니다. 답안별 채점 결과는 `reward_batch` 로그에 남습니다. EC2 `g5.xlarge` 두 대의 gVisor 샌드박스가 채점한 코드 12개 중 정답은 1개였습니다. [학습 노드 배치와 완료 로그](../handson/scenarios/b/b1.md#확인-방법)

학습이 끝난 뒤에는 같은 EC2 pool에 채점을 요청하는 노드만 바꿔 비교했습니다. 먼저 EKS 시스템 노드에서 테스트 커널(`relu_bias_triton`)의 채점을 32회 요청했습니다. 이어서 HyperPod 학습 노드에서도 같은 커널로 32회 요청했습니다. 채점 시간의 중앙값은 각각 9.918초와 9.937초였고, pool 처리량은 두 경우 모두 초당 0.199건이었습니다. [B1 클라이언트 비교](../handson/benchmarks/index.md#hyperpod-b1)

<a id="더-살펴보기"></a>

## HyperPod가 trainer에 제공하는 기능

- **노드 복구:** 클러스터를 `NodeRecovery: Automatic`으로 생성합니다(`infra/hyperpod/cluster.json.tpl`). 노드 상태는 `sagemaker.amazonaws.com/node-health-status` 라벨(`Schedulable`, `Unschedulable` 등)에서 확인할 수 있습니다. trainer Job은 `Schedulable`인 노드에서만 실행됩니다.
- **deep health check:** 인스턴스 그룹의 `OnStartDeepHealthChecks`로 `InstanceStress`(GPU/NVLink 개수, DCGM 진단, EFA 등)와 `InstanceConnectivity`(NCCL 등)를 켤 수 있습니다. 실습 템플릿에서는 이 검사를 켜지 않습니다. 켜려면 아래 표에서 노드에 taint를 지정할 때의 제약을 먼저 확인하세요.
- **학습 정지 감지와 Job 재시작:** training operator add-on(`amazon-sagemaker-hyperpod-training-operator`)은 `HyperPodPyTorchJob`의 로그를 감시합니다. 실습에서는 `jobMaxRetryCount: 3`과 `restartPolicy`(`numRestartBeforeFullJobRestart: 1`, `evalPeriodSeconds: 3600`, `maxFullJobRestarts: 2`)를 설정합니다. 로그에서 다음 두 이벤트가 제때 나타나는지 확인합니다.
    - **`JobStart`**: 1200초 안에 `"event": "routing"` 줄이 출력돼야 합니다.
    - **`RewardStalled`**: 1800초마다 `"event": "reward_batch"` 줄이 출력돼야 합니다.

    HyperPod용 trainer 이미지는 `hyperpod-elastic-agent` 1.1.3을 설치합니다. Job은 `hyperpodrun`으로 학습을 시작합니다.

- **체크포인트에서 학습 재개:** `train_grpo.py`를 다시 시작하면 출력 디렉터리의 최신 체크포인트를 불러와 학습을 이어갑니다. 핸즈온의 `/outputs`는 emptyDir 임시 볼륨이라 pod를 삭제하면 체크포인트도 사라집니다. 노드를 교체한 뒤에도 이어서 학습하려면 `/outputs`에 공유 스토리지(FSx for Lustre PVC 등)를 마운트해야 합니다.
- **그 밖의 기능:** CLI `hyp`(`pip install sagemaker-hyperpod`), task governance와 observability add-on, Karpenter 기반 autoscaling(`AutoScalerType: Karpenter`, `NodeProvisioningMode: Continuous`)이 있습니다.

!!! warning "training operator와 Kubernetes 버전"
    HyperPod는 실습에 사용한 EKS의 Kubernetes 버전 1.36을 지원합니다. 클러스터를 만들기 전에 아래 읽기 전용 명령으로 이 버전과 호환되는 add-on을 확인하세요.

    ```bash
    aws eks describe-addon-versions \
      --addon-name amazon-sagemaker-hyperpod-training-operator \
      --kubernetes-version 1.36
    ```

    **확인할 것:**

    - **JSON의 `addons[0].addonVersions` 목록**: 여기에 나온 버전이 1.36과 호환되는 add-on 버전입니다.
    - **목록이 비어 있으면**: `K8S_VERSION`을 낮추는 것을 검토하세요.

??? info "HyperPod (EKS) 사전 요구 사항 요약"
    - EKS 인증 모드 `API` 또는 `API_AND_CONFIG_MAP`, VPC CNI 1.18.3 이상, private subnet이 필요합니다.
    - **API로 클러스터를 만들 때**: 먼저 HyperPod 의존성 Helm 차트(`sagemaker-hyperpod-cli`의 `helm_chart/HyperPodHelmChart`)를 설치하세요. 이 차트에는 health monitoring agent, deep health check RBAC, job auto-restart, MPI operator, nvidia-device-plugin, Neuron과 EFA plugin, Kueue가 포함됩니다.
    - **IAM role**: HyperPod 노드와 EKS 노드에는 서로 다른 IAM role을 연결합니다. execution role에는 `AmazonSageMakerClusterInstanceRolePolicy`와 EC2 ENI, ECR inline policy가 연결됩니다.

## HyperPod에서 채점 노드를 구성할 때 확인할 조건 { #hyperpod가-샌드박스-계층에-제공하지-않는-기능 }

| 항목 | HyperPod에서 고려할 조건 | 실습에서 적용한 방법 |
|---|---|---|
| 샌드박스 런타임 | nvproxy로 GPU에 접근하려면 노드의 드라이버와 gVisor 버전이 호환돼야 합니다. 이 실습의 HyperPod 인스턴스는 Kata GPU에 필요한 가상화 장치를 제공하지 않습니다 | B1은 EC2에서 gVisor를 실행합니다. B2는 HyperPod `sandbox` 그룹에 gVisor가 지원하는 드라이버를 설치합니다 |
| 전용 노드 taint | "You cannot add custom taints to nodes in instance groups with DeepHealthChecks turned on." | B1은 EC2 샌드박스 노드에, 관리형 B2는 HyperPod 샌드박스 노드에 `gpusandbox/role` taint를 지정합니다 |
| 격리 검증 | deep health check는 GPU와 NVLink, EFA, NCCL 등을 점검합니다. 샌드박스의 외부 통신을 차단했는지는 따로 확인해야 합니다 | 샌드박스는 egress 차단을 확인한 뒤에만 Ready 상태가 됩니다. 배포 후 `scripts/ops/verify.sh`로 검증합니다 |
| pod 밀도 | B1의 `ml.g5.2xlarge` 노드가 보고한 pod 한도는 14개였습니다. ENI를 추가할 수 있는지는 AMI와 VPC CNI 버전에 따라 달라집니다. | B1에서는 학습용 워크로드만 HyperPod에 배치합니다. B2의 `sandbox` 그룹은 노드당 샌드박스 pod 1개 |
| CPU 노드 교체 | "Node auto-replacement is not supported for CPU instances." | B2의 `system`은 HyperPod CPU 노드입니다. 시나리오 C의 CPU 채점은 EC2 `c8i`에서 실행합니다 |
| 버전 고정, parity, gateway | HyperPod에서 별도로 제공하지 않습니다 | 샌드박스 운영 코드에서 버전과 라우팅을 관리합니다 |

HyperPod 노드에서는 기본적으로 hostNetwork pod만 IMDS에 접근할 수 있습니다. 이 기본 설정은 샌드박스에서 IMDS로 연결하는 것을 제한합니다. 다른 목적지로 나가는 트래픽도 차단됐는지는 별도로 점검하세요.

## B2에서 채점 노드의 드라이버를 맞추는 이유

gVisor의 GPU 연결 기능인 nvproxy에는 드라이버 버전별 지원 목록이 있습니다. B2의 기본 이미지에 들어 있던 `595.112.07`은 gVisor `20261109.0`의 목록에 없었습니다. 채점 노드 두 대에 `580.178.04`를 설치하고 HyperPod API로 재부팅한 뒤, 각 노드의 gVisor Pod에서 A10G로 코드를 실행했습니다. GPU를 직접 쓰는 학습 노드는 기본 드라이버를 유지했습니다.

[채점 노드 준비와 CUDA 실행 화면](../handson/scenarios/b/b2.md), [같은 커널로 측정한 채점 성능](../handson/benchmarks/index.md#hyperpod-b2)

## 인스턴스 선택

| 역할 | 선택 | 이유 | 온디맨드 요금 (USD/시간) |
|---|---|---|---|
| trainer (A) | `g5.2xlarge` (1 x A10G 24 GB, 8 vCPU, 32 GiB) | 1.5B 모델 + LoRA + vLLM colocate를 A10G 하나에서 실행하도록 설정 (`vllm_gpu_memory_utilization` 0.35). 실습 계정에서 GRPO 5 step 완료 | 1.212 |
| trainer (B) | `ml.g5.2xlarge` | 같은 하드웨어를 HyperPod에서 사용. 온디맨드 요금 기준 약 25% 높음 (1.515 / 1.212 = 1.25) | 1.515 |
| gVisor 샌드박스 | `g5.xlarge` (1 x A10G), 노드당 샌드박스 1개 | 실습에서 A10G로 CUDA 실행과 채점을 확인 | 1.006 |
| Kata GPU 샌드박스 | `g4dn.metal` (8 x T4, 96 vCPU, 384 GiB), VM마다 T4 1개 | NVIDIA GPU를 탑재한 유일한 x86 `.metal` 타입 | 7.824 (서울 9.624) |
| Kata CPU 샌드박스 | `c8i.2xlarge` (nested virtualization) | `.metal` 없이 `/dev/kvm` 사용 가능. Kata 연습과 CPU 계층용 | 0.37484 |
| system | `m6i.large` x 2 | CoreDNS와 컨트롤러 | 0.096 (대당) |

가격은 us-east-1과 us-west-2의 온디맨드 요금입니다.

L4 GPU가 필요하면 `g6`를 선택하세요. [g5와 g6 드라이버 호환성 확인](../handson/common/02_runtimes/gvisor.md#g5-노드의-드라이버와-검증-범위)

??? info "다른 후보의 가격과 GPU"
    | EC2 | GPU | USD/시간 |
    |---|---|---|
    | `g4dn.xlarge` | 1 x T4 | 0.526 |
    | `g4dn.2xlarge` | 1 x T4 | 0.752 |
    | `g6.xlarge` | 1 x L4 | 0.8048 |
    | `g6.2xlarge` | 1 x L4 | 0.9776 |
    | `g6e.xlarge` | 1 x L40S | 1.861 |
    | `g6e.12xlarge` | 4 x L40S | 10.49264 |
    | `g6e.48xlarge` | 8 x L40S | 30.13118 |
    | `p4d.24xlarge` | 8 x A100 | 21.95764 |
    | `p5.48xlarge` | 8 x H100 | 55.04 |
    | `g5g.metal` | 2 x T4g (arm64) | 2.744 |
    | `c5.metal` | 없음 | 4.08 |
    | `t3.large` | 없음 | 0.0832 |

    | HyperPod | USD/시간 |
    |---|---|
    | `ml.g4dn.xlarge` | 0.7364 |
    | `ml.g6.xlarge` | 1.127 |
    | `ml.g6.2xlarge` | 1.222 |
    | `ml.g6.4xlarge` | 1.654 |
    | `ml.g5.xlarge` | 1.408 |
    | `ml.g5.8xlarge` | 3.06 |
    | `ml.g6e.xlarge` | 2.61 |

    Production의 trainer NodePool 후보(`infra/karpenter/nodepools.yaml`)는 `g6e.12xlarge`, `g6e.48xlarge`, `p5.48xlarge`입니다.

## 리전별 vCPU 쿼터

| quota (vCPU 기준) | 핸즈온 필요량 | 비고 |
|---|---|---|
| Running On-Demand G and VT instances | A: 16 (`g5.2xlarge` 8 + `g5.xlarge` 4 x 2), B1: 8 (`g5.xlarge` 4 x 2), B2: 0. Kata GPU를 실습하면 `g4dn.metal` 96 추가 | 문서상 기본값 0일 수 있음 |
| Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances | A/B1/C: 6 (`m6i.large` 2 x 2 + SSM 접속용 `t4g.nano` 2). 추가 필요량은 표 아래 목록 | 문서상 기본값 5 |
| `ml.m5.xlarge for cluster usage` | 1 (B2) | HyperPod `system` 그룹. 관리형 B2에 필요한 일반 EC2 워커 쿼터는 0 |
| `ml.g5.2xlarge for cluster usage` | 1 (B) | HyperPod 인스턴스에는 `ml.<type> for cluster usage` 쿼터가 적용됨 |
| `ml.g5.xlarge for cluster usage` | 2 (B2) | B2의 `sandbox` 인스턴스 그룹(`HYPERPOD_SANDBOX_COUNT`) |

Standard quota가 더 필요한 경우는 다음과 같습니다.

- **Kata CPU를 실습하면**: 추가 필요량은 `c8i.2xlarge` 8(합계 14)입니다.
- **기존 CDK B2 또는 Kata GPU용 AMI를 만드는 동안에는**: builder `m6i.large` 2가 더 필요합니다(8, Kata CPU 노드가 있으면 16).

`scripts/01_check_prereqs.sh`가 G and VT quota, `c8i.2xlarge`의 nested virtualization 지원, GPU 타입의 AZ별 제공 여부를 읽기 전용으로 조회해 출력합니다. 실행 방법과 확인할 내용은 [시작하기](../handson/start.md)의 5장에 있습니다.

## 핸즈온 구성의 시간당 비용 (추정)

| 구성 | 포함 노드 | 노드 소계 (USD/시간) |
|---|---|---|
| A 기본 (gVisor + trainer) | `m6i.large` x 2 + `g5.xlarge` x 2 + `g5.2xlarge` | 0.192 + 2.012 + 1.212 = 약 3.42 |
| A + Kata CPU | A 기본 + `c8i.2xlarge` x 1 | 약 3.79 |
| A + Kata GPU | A 기본 + `g4dn.metal` x 1 | 3.416 + 7.824 = 약 11.24 |
| B1 (HyperPod trainer) | `m6i.large` x 2 + `g5.xlarge` x 2 + `ml.g5.2xlarge` | 0.192 + 2.012 + 1.515 = 약 3.72 |

온디맨드 요금으로 계산한 추정치이며, EKS 컨트롤 플레인, NAT gateway, SSM 접속용 `t4g.nano`, EBS, 데이터 전송, ECR, CloudWatch 비용은 포함하지 않았습니다.

!!! warning "`g4dn.metal` 노드 그룹은 쓰지 않을 때 0으로 줄이세요"
    A + Kata GPU 구성에서는 `g4dn.metal` 한 대가 노드 비용의 약 70%를 차지합니다(7.824 / 11.24). 쓰지 않을 때는 아래 명령으로 노드 그룹 크기를 0으로 줄이고, 실습이 끝나면 [정리](../handson/cleanup.md)를 실행하세요.

    ```bash
    aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu \
      --scaling-config minSize=0,maxSize=1,desiredSize=0
    ```

    **확인할 것:**

    - 몇 분 후 `cdk/tunnel.sh`를 실행한 상태에서 `kubectl get nodes -l gpusandbox/kata-gpu=true`를 실행했을 때 노드가 하나도 출력되지 않으면 축소가 끝난 것입니다.
    - **셸에 `CLUSTER_NAME` 변수가 없다면**: 먼저 `source scripts/config.env`를 실행하세요.

!!! question "❓ 오해: HyperPod를 쓰면 샌드박스도 HyperPod가 관리한다"
    HyperPod는 deep health check로 노드 상태를 검사하고, 장애가 나면 노드를 복구하거나 job을 재시작할 수 있습니다. 노드 복구는 클러스터 단위로 설정하므로 B2의 `sandbox` 그룹에도 적용됩니다. 샌드박스 런타임 설치, 격리 검증, 버전 고정은 별도로 구성해야 합니다.

!!! question "❓ 오해: T4가 더 저렴하니 gVisor 노드도 `g4dn`을 쓰면 된다"
    `g4dn.xlarge`(0.526)는 `g5.xlarge`(1.006)보다 요금이 낮습니다. `g4dn`의 드라이버 조건은 `g5`와 같습니다(AMI가 GSP를 끈 proprietary 커널 모듈을 로드). 이번 실습에서 T4로 검증한 조합은 `g4dn.metal`의 Kata + QEMU입니다. T4에서 gVisor를 실행하려면 드라이버 호환성을 별도로 확인하세요.

<span id="적용-범위와-한계"></span>

[시나리오별 AWS 실행 기록](../reference/sources.md#aws-실행-기록)

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | HyperPod 복원력, deep health check | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html |
    | HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
    | EC2 가속 컴퓨팅 인스턴스 사양, quota | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html , https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
    | 가격 (EC2, SageMaker AI) | https://aws.amazon.com/ec2/pricing/on-demand/ , https://aws.amazon.com/sagemaker/ai/pricing/ |
    | HyperPod 배포 템플릿과 점검 스크립트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/cluster.json.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh |

    [관련 대표 자료](../reference/references.md#ref-concepts-04-platforms-and-instances)
