# 플랫폼과 인스턴스 선택

!!! info "TL;DR"
    시나리오 A와 B1은 샌드박스를 EC2 노드에서 실행하고, trainer만 EC2(`g5.2xlarge`, Scenario A)나 HyperPod(`ml.g5.2xlarge`, Scenario B1)에서 실행합니다. 실험 구성인 B2는 gVisor 샌드박스를 custom AMI의 HyperPod 그룹 `sandbox`에 둡니다. 샌드박스 노드로 gVisor는 `g5.xlarge`, Kata GPU는 `g4dn.metal`, Kata CPU는 `c8i.2xlarge`를 씁니다.

## 기존 Pain Point

HyperPod를 쓰기로 하면 샌드박스도 HyperPod 노드에서 실행하면 될 것 같지만, 기본 HyperPod AMI에서는 드라이버와 `.metal` 제약 때문에 불가능합니다. 인스턴스 선택 기준도 헷갈리기 쉽습니다.

- **T4(`g4dn`)**: 요금이 낮지만 이 에셋의 gVisor 구성에서 검증되지 않았습니다.
- **Kata GPU에 필요한 `.metal`**: 시간당 요금이 높습니다.

새 계정에서는 GPU 계열 On-Demand quota가 0일 수 있어서 클러스터 생성이 노드 생성 단계에서 중단되기도 합니다.

![두 패널 그림입니다. a: EKS 클러스터의 기본 AMI HyperPod 인스턴스 그룹에 trainer(ml.g5.2xlarge)와 샌드박스를 함께 둡니다. gVisor 샌드박스는 드라이버 595.91.07을 nvproxy가 지원하지 않아(unknown) 실행되지 않고, Kata 샌드박스는 ml.*.metal과 nested virtualization이 없어 실행되지 않습니다(빨간색). b B1: 같은 EKS 클러스터에서 trainer만 HyperPod 인스턴스 그룹에 두고, gVisor 샌드박스(g5.xlarge)와 Kata 샌드박스(GPU는 g4dn.metal, CPU는 c8i.2xlarge)는 EC2 노드 그룹에 둡니다.](../images/figures/concepts-04_platforms_and_instances.svg)

*그림 요약: 기본 HyperPod AMI의 노드에서는 gVisor 샌드박스와 Kata 샌드박스를 모두 실행할 수 없습니다. 그래서 B1은 trainer만 HyperPod에 두고, 샌드박스는 같은 클러스터의 EC2 노드에 둡니다. 드라이버를 바꾼 custom AMI의 HyperPod 그룹에 gVisor 샌드박스를 두는 B2는 실험 구성입니다.*


## Why

- **trainer 노드 장애 대응을 맡는 쪽이 시나리오마다 다릅니다.** A는 직접 구성하고, B1과 B2에서는 HyperPod가 노드 복구와 health monitoring을 맡습니다.
- **샌드박스 런타임, 격리 검증, 채점 버전 관리는 HyperPod 기능이 아닙니다.** 이 에셋의 코드가 맡습니다. HyperPod의 노드 복구는 클러스터 설정이라 B2의 `sandbox` 그룹에도 적용됩니다.

**사전 지식:** [02 격리 런타임 비교](02_isolation_runtimes.md)의 "AWS에서 각 런타임을 실행할 수 있는 위치" 표를 먼저 보세요. 처음 보는 용어는 아래 "용어" 상자와 [용어 사전](../reference/glossary.md)에서 확인할 수 있습니다.

??? note "용어 (처음 보는 단어가 있으면 펼치세요)"
    - **SageMaker HyperPod**: 장시간 학습용 GPU 클러스터를 AWS가 관리해 주는 서비스입니다. 여기서는 기존 EKS 클러스터에 HyperPod 노드를 추가하는 EKS orchestrator 모드를 씁니다.
    - **인스턴스 그룹**: HyperPod 클러스터 안에서 같은 인스턴스 타입으로 묶인 노드 집합입니다.
    - **NodeRecovery, deep health check**: NodeRecovery는 장애 노드를 자동으로 교체하는 HyperPod 설정이고, deep health check는 GPU나 네트워크 같은 하드웨어를 정밀하게 점검하는 검사입니다.
    - **HyperPodPyTorchJob, training operator**: HyperPodPyTorchJob은 HyperPod에서 학습 job을 정의하는 Kubernetes 리소스이고, training operator는 이 job을 실행하고 재시작하는 EKS add-on입니다.
    - **lifecycle script**: HyperPod 노드가 처음 만들어질 때 실행되는 설정 스크립트입니다. S3 버킷에서 읽어 옵니다.
    - **execution role**: HyperPod 노드가 AWS API를 호출할 때 쓰는 IAM role입니다.
    - **taint, toleration**: taint는 노드에 설정하는 표시로, 이 taint에 맞는 toleration이 있는 pod만 그 노드에 배치되게 합니다. toleration은 pod가 특정 taint가 있는 노드에 배치될 수 있다고 선언하는 설정입니다.
    - **ENI**: EC2 인스턴스에 연결되는 가상 네트워크 인터페이스입니다. VPC CNI는 ENI의 IP 주소를 pod에 할당하므로 ENI 수에 따라 노드의 최대 pod 수가 정해집니다.
    - **IMDS, hostNetwork**: IMDS는 EC2 인스턴스 메타데이터 서비스(노드 자격 증명을 제공하는 엔드포인트)이고, hostNetwork pod는 노드의 네트워크를 그대로 사용하는 pod입니다.
    - **온디맨드 요금**: 약정 없이 사용하는 시간당 공개 요금입니다. 할인과 세금은 포함하지 않습니다.

## Scenario A, B1, B2 대조

| 항목 | A. EC2 자체 운영 | B1. HyperPod (기본) | B2. HyperPod (실험) |
|---|---|---|---|
| trainer 위치 | EKS의 EC2 GPU 노드 `g5.2xlarge` (A10G 24 GB, 8 vCPU, 32 GiB) | 같은 EKS 클러스터에 연결된 HyperPod 인스턴스 그룹 `ml.g5.2xlarge` (HyperPod EKS orchestrator) | B1과 같음 |
| GPU 샌드박스 위치 | 같은 클러스터의 EC2 노드 | 같은 클러스터의 EC2 노드 | HyperPod 인스턴스 그룹 `sandbox`(`ml.g5.xlarge`)에서 실행하는 gVisor |
| trainer 노드 장애 대응 | 직접 구성 (GPU 장애 감지, 노드 교체, job 재시작) | `NodeRecovery: Automatic`, health monitoring agent, deep health check(선택) | B1과 같음 |
| trainer job | Kubernetes Job (`k8s/trainer/job-grpo.yaml.tpl`) | `HyperPodPyTorchJob` (`k8s/trainer/hyperpod-job-grpo.yaml.tpl`) | B1과 같음 |
| 추가 구성 | 없음 | HyperPod 의존성 Helm 차트, execution role, lifecycle script 버킷, training operator add-on, `hyperpodrun`이 포함된 trainer 이미지 | B1 + 드라이버를 580.178.04로 바꾼 custom AMI(`scripts/hyperpod/build_b2_ami.sh`)와 `sandbox` 인스턴스 그룹 |
| 상태 | 사용 가능. 실습 계정에서 `g5`로 실행 | 사용 가능. AWS에서 실행하지 않아 미검증 | 실험: custom AMI로 가능하도록 구성했지만 AWS에서 실행하지 않음(미검증). 기본 AMI의 드라이버 595.91.07은 gVisor release-20261109.0에서 unknown |

## HyperPod가 trainer에 제공하는 기능

- **노드 복구:** 클러스터를 `NodeRecovery: Automatic`으로 생성합니다(`infra/hyperpod/cluster.json.tpl`). 노드 상태는 `sagemaker.amazonaws.com/node-health-status` 라벨(`Schedulable`, `Unschedulable` 등)로 표시되며, trainer job은 `Schedulable` 노드에만 배치됩니다.
- **deep health check:** 인스턴스 그룹의 `OnStartDeepHealthChecks`로 `InstanceStress`(GPU/NVLink 개수, DCGM 진단, EFA 등)와 `InstanceConnectivity`(NCCL 등)를 켤 수 있습니다. 이 에셋의 템플릿은 이 필드를 설정하지 않습니다. 이 필드를 추가할 때는 아래 taint 제약을 확인하세요.
- **job 재시작과 hang 감지:** training operator add-on(`amazon-sagemaker-hyperpod-training-operator`)의 `HyperPodPyTorchJob`을 쓰고, `jobMaxRetryCount: 3`과 `restartPolicy`(`numRestartBeforeFullJobRestart: 1`, `evalPeriodSeconds: 3600`, `maxFullJobRestarts: 2`)를 설정합니다. 로그 패턴 감지 규칙은 두 가지입니다.
    - **`JobStart`**: 1200초 안에 `"event": "routing"` 줄이 출력돼야 합니다.
    - **`RewardStalled`**: 1800초마다 `"event": "reward_batch"` 줄이 출력돼야 합니다.

    HyperPod용 trainer 이미지는 `hyperpod-elastic-agent`를 버전 고정 없이 설치하고, Job은 `hyperpodrun`으로 trainer를 시작합니다. 설치되는 버전은 빌드 시점에 따라 달라질 수 있습니다.

- **checkpoint 재개:** `train_grpo.py`는 재시작되면 출력 디렉터리의 최신 checkpoint에서 이어서 학습합니다. 핸즈온의 `/outputs`는 emptyDir(pod가 삭제되면 함께 삭제되는 임시 볼륨)이므로, 노드 교체 후에도 학습을 이어 가려면 공유 스토리지(FSx for Lustre PVC 등)를 마운트해야 합니다.
- **그 밖의 기능:** CLI `hyp`(`pip install sagemaker-hyperpod`), task governance와 observability add-on, Karpenter 기반 autoscaling(`AutoScalerType: Karpenter`, `NodeProvisioningMode: Continuous`)이 있습니다.

!!! warning "training operator와 Kubernetes 버전"
    이 에셋은 Kubernetes 1.36을 씁니다. HyperPod EKS AMI 릴리스 노트에는 1.36 AMI가 있지만, HyperPod 사전 요구 사항 페이지에는 1.30에서 1.35까지, training operator 문서에는 1.28부터 1.33까지가 명시돼 있습니다(문서가 갱신되지 않았을 수 있음). 클러스터를 만들기 전에 아래 읽기 전용 명령으로 add-on 호환 버전을 확인하세요.

    ```bash
    aws eks describe-addon-versions \
      --addon-name amazon-sagemaker-hyperpod-training-operator \
      --kubernetes-version 1.36
    ```

    **확인할 것:**

    - **JSON의 `addons[0].addonVersions` 목록에 버전이 하나 이상 있으면**: 1.36과 호환되는 add-on이 있다는 뜻입니다.
    - **목록이 비어 있으면**: `K8S_VERSION`을 낮추는 것을 검토하세요.

??? info "HyperPod (EKS) 사전 요구 사항 요약"
    - EKS 인증 모드 `API` 또는 `API_AND_CONFIG_MAP`, VPC CNI 1.18.3 이상, private subnet이 필요합니다.
    - **API로 클러스터를 만들 때**: health monitoring agent, deep health check RBAC, job auto-restart, MPI operator, nvidia-device-plugin, Neuron과 EFA plugin, Kueue를 설치하는 HyperPod 의존성 Helm 차트(`sagemaker-hyperpod-cli`의 `helm_chart/HyperPodHelmChart`)를 먼저 설치해야 합니다.
    - **IAM role**: HyperPod 노드와 EKS 노드는 서로 다른 IAM role을 씁니다. execution role에는 `AmazonSageMakerClusterInstanceRolePolicy`와 EC2 ENI, ECR inline policy가 연결됩니다.

## HyperPod가 샌드박스 계층에 제공하지 않는 기능

| 항목 | 사실 | 이 에셋의 대응 |
|---|---|---|
| 샌드박스 런타임 | HyperPod EKS AMI의 NVIDIA 드라이버 595.91.07은 gVisor release-20261109.0에서 unknown이라 nvproxy가 동작하지 않습니다. Kata는 `ml.*.metal`이 없고 CreateCluster에 nested virtualization CPU 옵션이 없어서 실행할 수 없습니다 | 샌드박스는 EC2 노드에서 실행 (B1). B2는 드라이버를 바꾼 custom AMI로 별도 인스턴스 그룹을 만듦 |
| 전용 노드 taint | "You cannot add custom taints to nodes in instance groups with DeepHealthChecks turned on." | 샌드박스 노드는 EC2 노드 그룹에서 `gpusandbox/role` taint로 분리 |
| 격리 검증 | deep health check는 GPU, NVLink, EFA, NCCL 같은 하드웨어 점검이며 샌드박스 격리(egress 차단 등)를 확인하지 않습니다 | egress 차단을 확인한 뒤에만 Ready, `scripts/ops/verify.sh` |
| pod 밀도 | 인스턴스당 ENI 1개라 `ml.g6.xlarge`, `ml.g6.2xlarge`는 최대 14 pod(기본값인 `ml.g5`의 한도는 확인하지 않음) | B1은 HyperPod 노드에 trainer만 배치. B2의 `sandbox` 그룹은 노드당 샌드박스 pod 1개 |
| CPU 노드 교체 | "Node auto-replacement is not supported for CPU instances." | CPU 계층은 EC2 (`c8i`) |
| 버전 고정, parity, gateway | HyperPod 기능이 아닙니다 | 이 저장소의 코드 |

HyperPod 노드에서는 기본적으로 hostNetwork pod만 IMDS에 접근할 수 있습니다. 샌드박스 격리에는 유리한 기본값이지만, 위 표의 제약을 해결하지는 않습니다.

## B1의 EC2 샌드박스와 B2의 custom AMI

gVisor는 드라이버 버전이 지원 목록과 정확히 일치해야 하고, unknown 버전은 우회 플래그를 써도 동작하지 않습니다. 그래서 B2는 드라이버를 580.178.04로 바꾼 custom AMI를 직접 빌드합니다([07 HyperPod 시나리오의 B2](../handson/07_hyperpod.md#b2)).

아래 스크립트는 노드의 드라이버 버전을 확인합니다(HyperPod 클러스터 필요). 노드마다 debug pod를 실행하고, 끝날 때 `default` 네임스페이스에서 이름이 `node-debugger-`로 시작하는 pod를 모두 삭제합니다. 다른 작업자의 디버깅 세션도 함께 삭제될 수 있습니다.

```bash
scripts/hyperpod/check_gvisor.sh
```

**확인할 것:**

- **기본 AMI를 쓰는 trainer 노드**: 아래 줄이 출력됩니다.

    ```text
      driver 595.91.07: NOT supported by gVisor 20261109.0: keep sandboxes on EC2 (mode B1)
    ```

- **B2 custom AMI를 쓰는 sandbox 노드**: `driver 580.178.04: SUPPORTED ...`가 출력됩니다.

B2에서도 위의 pod 수 제한은 그대로 적용됩니다. taint는 deep health check를 켜지 않은 인스턴스 그룹에만 추가할 수 있으므로 B2의 sandbox 그룹은 deep health check 없이 만듭니다. B1을 기본으로 둔 이유는 custom AMI를 직접 관리하지 않아도 되기 때문입니다. `ml.g5`의 B1과 B2는 AWS에서 실행하지 않아 미검증입니다.

B2에서는 `scripts/04_install_gpu_stack.sh`가 smoke pod를 만들지 않습니다. 다음 순서로 확인하고 배포하세요.

1. sandbox 노드의 `/proc/driver/nvidia/version`으로 어떤 모듈 종류가 로드됐는지 봅니다.
2. 위의 `scripts/hyperpod/check_gvisor.sh`로 그 드라이버가 지원 목록에 있는지 확인합니다.
3. `scripts/06_deploy_sandboxes.sh gvisor-hyperpod v1`로 풀을 배포합니다.
4. `scripts/ops/verify.sh gvisor-hyperpod v1`로 검증합니다.

**문제가 생기면:** `no HyperPod nodes found`는 HyperPod 노드가 아직 클러스터에 연결되지 않았다는 뜻입니다. [07 HyperPod 시나리오](../handson/07_hyperpod.md)와 [문제 해결](../reference/troubleshooting.md)의 "HyperPod" 항목을 보세요.

## 인스턴스 선택

| 역할 | 선택 | 이유 | 온디맨드 요금 (USD/시간) |
|---|---|---|---|
| trainer (A) | `g5.2xlarge` (1 x A10G 24 GB, 8 vCPU, 32 GiB) | 1.5B 모델 + LoRA + vLLM colocate를 A10G 하나에서 실행하도록 설정 (`vllm_gpu_memory_utilization` 0.35). 실습 계정에서 GRPO 5 step 완료 | 1.212 |
| trainer (B) | `ml.g5.2xlarge` | 같은 하드웨어를 HyperPod에서 사용. 온디맨드 요금 기준 약 25% 높음 (1.515 / 1.212 = 1.25) | 1.515 |
| gVisor 샌드박스 | `g5.xlarge` (1 x A10G), 노드당 샌드박스 1개 | AMI가 로드하는 드라이버 580.178.04가 nvproxy 지원 목록에 있음. 검증 조건은 아래 "`g5`의 드라이버와 검증 범위" | 1.006 |
| Kata GPU 샌드박스 | `g4dn.metal` (8 x T4, 96 vCPU, 384 GiB), VM마다 T4 1개 | NVIDIA GPU를 탑재한 유일한 x86 `.metal` 타입 | 7.824 (서울 9.624) |
| Kata CPU 샌드박스 | `c8i.2xlarge` (nested virtualization) | `.metal` 없이 `/dev/kvm` 사용 가능. Kata 연습과 CPU 계층용 | 0.37484 |
| system | `m6i.large` x 2 | CoreDNS와 컨트롤러 | 0.096 (대당) |

가격은 us-east-1과 us-west-2의 온디맨드 요금입니다.

!!! note "`g5`의 드라이버와 검증 범위"
    2026-11-18에 배포한 `g5.xlarge` 노드에서는 EKS AL2023 NVIDIA AMI가 GSP를 끈 proprietary 커널 모듈 580.178.04를 로드했습니다(`/proc/driver/nvidia/version`, `/proc/driver/nvidia/params`의 `EnableGpuFirmware: 0`). gVisor 문서는 NVIDIA open 드라이버를 기준으로 nvproxy를 설명하고 proprietary 드라이버는 언급하지 않습니다.

    - **이 저장소의 검증**: 580.178.04는 runsc `release-20261109.0`의 지원 목록(`runsc nvproxy list-supported-drivers`)에 있습니다. 실습 계정에서 `g5.xlarge`로 gVisor smoke test(`cuda ok: NVIDIA A10G 2048.0`)와 `scripts/ops/verify.sh gvisor v1`이 통과했고, `g5.2xlarge` trainer로 GRPO 5 step을 마쳤습니다. 즉 이 조합은 gVisor가 문서화한 것이 아니라 이 저장소가 검증한 것입니다.
    - **드라이버, AMI, gVisor 버전을 바꾸면**: 다시 확인하세요.
    - **`04_install_gpu_stack.sh`의 smoke test**: GPU 하나를 쓰는 pod를 따로 만들므로 gVisor 노드에 빈 GPU가 있을 때 실행하세요.
    - **이미 배포한 풀**: `scripts/ops/verify.sh gvisor v1`로 확인합니다.

    `g6`(L4)는 지원하는 대안입니다. AMI가 open 모듈 580.178.04를 로드하므로 gVisor 문서와 일치하고, 요금도 낮습니다(`g6.xlarge` 0.8048, `g6.2xlarge` 0.9776). 쓰려면 `scripts/config.env`에서 `GVISOR_INSTANCE_TYPE`과 `TRAINER_INSTANCE_TYPE`(HyperPod는 `HYPERPOD_*`)을 바꿔 쓰세요.

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

## Quota

| quota (vCPU 기준) | 핸즈온 필요량 | 비고 |
|---|---|---|
| Running On-Demand G and VT instances | A: 16 (`g5.2xlarge` 8 + `g5.xlarge` 4 x 2), B1: 8 (`g5.xlarge` 4 x 2), B2: 0. Kata GPU를 실습하면 `g4dn.metal` 96 추가 | 문서상 기본값 0일 수 있음 |
| Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances | 6 (`m6i.large` 2 x 2 + SSM 접속용 `t4g.nano` 2). 추가 필요량은 표 아래 목록 | 문서상 기본값 5 |
| `ml.g5.2xlarge for cluster usage` | 1 (B) | HyperPod는 `ml.<type> for cluster usage` quota를 씀 |
| `ml.g5.xlarge for cluster usage` | 2 (B2) | B2의 `sandbox` 인스턴스 그룹(`HYPERPOD_SANDBOX_COUNT`) |

Standard quota가 더 필요한 경우는 다음과 같습니다.

- **Kata CPU를 실습하면**: 추가 필요량은 `c8i.2xlarge` 8(합계 14)입니다.
- **B2나 Kata GPU용 AMI를 만드는 동안에는**: builder `m6i.large` 2가 더 필요합니다(8, Kata CPU 노드가 있으면 16).

`scripts/01_check_prereqs.sh`가 G and VT quota, `c8i.2xlarge`의 nested virtualization 지원, GPU 타입의 AZ별 제공 여부를 읽기 전용으로 조회해 출력합니다. 실행 방법과 확인할 내용은 [시작하기](../getting_started.md)의 5장에 있습니다.

## 핸즈온 구성의 시간당 비용 (추정)

| 구성 | 포함 노드 | 노드 소계 (USD/시간) |
|---|---|---|
| A 기본 (gVisor + trainer) | `m6i.large` x 2 + `g5.xlarge` x 2 + `g5.2xlarge` | 0.192 + 2.012 + 1.212 = 약 3.42 |
| A + Kata CPU | A 기본 + `c8i.2xlarge` x 1 | 약 3.79 |
| A + Kata GPU | A 기본 + `g4dn.metal` x 1 | 3.416 + 7.824 = 약 11.24 |
| B1 (HyperPod trainer) | `m6i.large` x 2 + `g5.xlarge` x 2 + `ml.g5.2xlarge` | 0.192 + 2.012 + 1.515 = 약 3.72 |

온디맨드 요금으로 계산한 추정치이며, EKS 컨트롤 플레인, NAT gateway, SSM 접속용 `t4g.nano`, EBS, 데이터 전송, ECR, CloudWatch 비용은 포함하지 않았습니다.

!!! warning "`g4dn.metal` 노드 그룹은 쓰지 않을 때 0으로 줄이세요"
    A + Kata GPU 구성에서는 `g4dn.metal` 한 대가 노드 비용의 약 70%를 차지합니다(7.824 / 11.24). 쓰지 않을 때는 아래 명령으로 노드 그룹 크기를 0으로 줄이고, 실습이 끝나면 [99 정리](../handson/99_cleanup.md)를 실행하세요.

    ```bash
    aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu \
      --scaling-config minSize=0,maxSize=1,desiredSize=0
    ```

    **확인할 것:**

    - 몇 분 후 `cdk/tunnel.sh`를 실행한 상태에서 `kubectl get nodes -l gpusandbox/kata-gpu=true`를 실행했을 때 노드가 하나도 출력되지 않으면 축소가 끝난 것입니다.
    - **셸에 `CLUSTER_NAME` 변수가 없다면**: 먼저 `source scripts/config.env`를 실행하세요.

!!! question "❓ 오해: HyperPod를 쓰면 샌드박스도 HyperPod가 관리한다"
    HyperPod의 노드 복구, deep health check, job 재시작은 노드와 job의 복원력 기능입니다. 노드 복구는 클러스터 설정이라 B2의 `sandbox` 그룹에도 적용되지만, 샌드박스 런타임 설치, 격리 검증, 버전 고정은 HyperPod가 제공하지 않습니다.

!!! question "❓ 오해: T4가 더 저렴하니 gVisor 노드도 `g4dn`을 쓰면 된다"
    `g4dn.xlarge`(0.526)는 `g5.xlarge`(1.006)보다 요금이 낮습니다. `g4dn`의 드라이버 조건은 `g5`와 같습니다(AMI가 GSP를 끈 proprietary 커널 모듈을 로드). 그래서 드라이버 종류 때문에 제외할 이유는 없지만, 이 에셋은 T4에서 실행하는 gVisor를 테스트하지 않아 미검증입니다. T4는 Kata + QEMU(`g4dn.metal`)의 GPU로 쓰고, gVisor에 쓰려면 직접 검증하세요.

## 적용 범위와 한계

- 시나리오 A의 `g5` 구성은 실습 계정에서 실행했습니다([실행 기록](../reference/sources.md#aws-실행-기록)). gVisor 샌드박스(1 replica)와 `scripts/ops/verify.sh gvisor v1`이 통과했고, trainer 설정(1.5B + LoRA + vLLM colocate on A10G 하나)으로 GRPO 5 step을 마쳤습니다.
- 다른 클러스터 구성에서는 `g4dn.metal`의 Kata + QEMU(`kata-qemu` replica 4, `scripts/ops/verify.sh kata-qemu v1`)를 실행했고, `scripts/ops/bench.sh 32`로 GPU 풀 2개와 CPU 풀 3개를 측정했습니다.
- HyperPod B1과 B2(`ml.g5`), 시나리오 A 학습 중의 `scripts/ops/rollout.sh` 버전 교체는 AWS에서 실행하지 않았습니다. 각 핸즈온 페이지의 확인 단계로 검증하세요.
- `c8i.2xlarge`는 us-east-1과 us-west-2에서 시간당 0.37484 USD, 서울 리전에서 0.42336 USD입니다. GPU 없이 이 노드만 쓰는 시나리오 C는 [10 c8i 단독 저비용 경로](../handson/10_cpu_only.md)에 있습니다.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | HyperPod 복원력, deep health check | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency.html , https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html |
    | HyperPod training operator | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html |
    | EC2 가속 컴퓨팅 인스턴스 사양, quota | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html , https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
    | 가격 (EC2, SageMaker AI) | https://aws.amazon.com/ec2/pricing/on-demand/ , https://aws.amazon.com/sagemaker/ai/pricing/ |
    | 이 에셋의 HyperPod 템플릿과 점검 스크립트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/hyperpod/cluster.json.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/trainer/hyperpod-job-grpo.yaml.tpl , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/hyperpod/check_gvisor.sh |

    전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-concepts-04-platforms-and-instances)
