# 08 비용

!!! info "TL;DR"
    비용은 trainer GPU, 샌드박스 GPU, 빈 bare metal 노드의 대기 시간, EKS control plane과 NAT gateway로 나뉩니다. 비용을 줄이는 주요 방법은 샌드박스 풀 크기를 reward 구간에 맞추고 빈 노드를 빨리 반납하는 것입니다(금액은 온디맨드 요금으로 계산한 추정치).

## 기존 Pain Point

실습을 마치고 `g4dn.metal`을 그대로 두면 시간당 7.824 USD, 주말 48시간이면 375.552 USD가 과금됩니다. 풀 크기를 넉넉하게 고정해 두면, 샌드박스 GPU는 reward 구간에만 사용되고 생성과 업데이트 구간에는 사용되지 않는데도 계속 과금됩니다. 노드 단위로 과금되므로 metal 노드의 T4 8개 중 4개만 쓰면 사용하는 T4당 단가가 두 배가 됩니다. pod마다 노드 하나를 쓰는 gVisor 풀은 blue/green 전환 때 두 풀을 오래 함께 실행하면 그동안 샌드박스 GPU 비용도 두 배가 됩니다.

![a: trainer가 생성, reward 채점, 업데이트를 반복하는 동안 샌드박스 GPU는 reward 구간에만 사용되지만, 과금은 노드 단위로 계속됩니다. run이 끝난 뒤 풀을 그대로 두면 g4dn.metal이 시간당 7.824 USD로 계속 과금됩니다(주말 48시간이면 375.552 USD). g4dn.metal의 T4 8개 중 4개만 쓰면 사용한 T4당 1.956 USD/시간입니다. b: 풀 크기를 reward 구간에 몰리는 요청에 맞추고, run이 끝나면 replicas를 0으로 줄입니다. 빈 노드는 consolidateAfter 30분이 지나면 반납 절차에 들어가므로 빈 기간마다 약 3.912 USD가 들고, 과금은 노드가 종료될 때까지 이어집니다. T4 8개를 모두 쓰면 T4당 0.978 USD/시간입니다.](../images/figures/production-08_cost.svg)

*그림 요약: 샌드박스 노드는 사용 여부와 관계없이 노드 단위로 과금되고, run이 끝난 뒤 그대로 두어도 계속 과금됩니다. 풀 크기를 reward 구간에 맞추고 run이 끝나면 0으로 줄여 빈 노드를 빨리 반납하며, metal 노드의 T4 8개를 모두 쓰면 T4당 비용이 절반이 됩니다.*


## Why

- **비용을 네 항목으로 나눕니다.** 풀 크기 조정은 샌드박스 GPU를, consolidation은 빈 metal 노드의 대기 시간을 줄이는 식으로 방법마다 줄이는 항목이 다릅니다.
- **공개된 온디맨드 요금으로만 계산합니다.** 측정한 사용량이 없으므로 금액은 단가와 시간을 곱한 추정치입니다.
- **trainer를 HyperPod로 옮길 때는 같은 GPU의 시간당 차액과 노드 복구 기능을 함께 비교합니다.**

**사전 지식:** [04 플랫폼과 인스턴스 선택](../concepts/04_platforms_and_instances.md)의 인스턴스 선택 이유와 [01 용량과 노드 관리](01_capacity_and_nodes.md)의 NodePool 설정을 먼저 보세요.

??? note "용어"
    - **온디맨드 요금**: 약정이나 할인 없이 쓴 만큼 시간 단위로 내는 공개 가격입니다. 이 페이지의 모든 금액은 이 값으로 계산합니다.
    - **Savings Plans, Spot**: Savings Plans는 사용량을 약정하고 할인받는 요금제이고, Spot은 AWS의 남는 용량을 적은 비용으로 쓰는 대신 AWS가 회수할 수 있는 인스턴스입니다.
    - **노드 단위 과금**: pod가 GPU를 몇 개 쓰든 노드 전체 시간이 과금된다는 뜻입니다. `g4dn.metal`에서 T4 4개만 써도 8개분 비용이 과금됩니다.
    - **consolidateAfter**: Karpenter가 빈 노드를 반납하기 전에 새 작업을 기다리는 시간입니다.
    - **warm placeholder**: 부팅이 느린 metal 노드를 미리 확보해 두는 빈 pod입니다. 노드 한 대 비용이 계속 과금됩니다.
    - **NAT gateway**: private subnet의 노드가 인터넷(이미지 pull, 모델 다운로드)에 접속할 때 거치는 관리형 서비스입니다. 시간당 요금과 처리량 요금이 있습니다.

    더 많은 용어는 [용어 사전](../reference/glossary.md)에 있습니다.

## 비용 모델

```text
hourly cost ≈ trainer GPU nodes
            + sandbox GPU nodes running sandbox pods (whole nodes, billed whether the GPUs are busy or idle)
            + idle bare-metal time (g4dn.metal with no sandbox pod, waiting for consolidation)
            + EKS control plane + NAT gateway (hourly + per GB processed)
            + smaller items (EBS volumes, FSx, ECR storage, CloudWatch)
```

- **trainer**: 시나리오 A는 `g5.2xlarge`, 시나리오 B는 `ml.g5.2xlarge`, Production veRL 예시는 8 GPU 노드입니다.
- **샌드박스**: gVisor는 `g5.xlarge` 노드 하나에 샌드박스 하나, Kata GPU는 `g4dn.metal` 하나에 T4 8개입니다.
- **metal 대기 시간**: Karpenter `sandbox-kata-gpu` NodePool은 metal 노드가 빈 뒤 30분이 지나면 회수를 검토합니다. 요금은 노드가 실제로 종료될 때까지 붙습니다.
- **control plane과 NAT**: CDK 스택은 노드를 private subnet에 두고 NAT gateway를 한 대 만듭니다. 이미지 pull과 모델 다운로드 트래픽이 이 NAT gateway를 거치므로 시간당 요금과 처리 GB당 요금이 부과됩니다. 샌드박스 pod는 egress가 차단되어 있어 NAT를 쓰지 않습니다.

## 단가 (온디맨드 요금)

| 인스턴스 | 이 저장소에서의 용도 | USD/시간 |
|---|---|---|
| `m6i.large` | system 노드 (2대) | 0.096 |
| `g5.xlarge` | gVisor 샌드박스 (A10G 1개) | 1.006 |
| `g5.2xlarge` | 시나리오 A trainer (A10G 1개), gVisor NodePool 대체 후보 | 1.212 |
| `g6.xlarge`, `g6.2xlarge` | 대체 인스턴스 (L4 1개). `GVISOR_INSTANCE_TYPE`, `TRAINER_INSTANCE_TYPE`로 지정 | 0.8048, 0.9776 |
| `g4dn.metal` | Kata GPU 샌드박스 (T4 8개) | 7.824 (서울 9.624) |
| `c8i.2xlarge` | Kata CPU (nested virtualization) | 0.37484 |
| `g6e.12xlarge`, `g6e.48xlarge`, `p5.48xlarge` | Production trainer NodePool 후보 | 10.49264, 30.13118, 55.04 |
| `ml.g5.2xlarge` | 시나리오 B trainer (HyperPod) | 1.515 |

!!! warning "추정용 단가입니다"
    us-east-1과 us-west-2의 온디맨드 요금이며, Savings Plans, Spot, 다른 리전에서는 달라집니다. EKS control plane, NAT gateway, EBS, FSx for Lustre, ECR, CloudWatch 요금은 각 요금 페이지에서 확인하세요.

## 비용을 줄이는 방법

### 샌드박스 풀을 reward 구간에 맞추기

풀 크기는 reward 구간에 몰리는 요청 수에 맞추고, run 사이에는 0으로 줄이는 편이 현실적입니다. GPU 노드가 클러스터에 합류하는 데 몇 분이 걸리고 bare metal은 더 오래 걸리므로, step마다 노드를 늘렸다 줄이기는 어렵습니다.

```text
step_time_s(P)   ≈ t_generate + t_update + ceil(N / P) × t_eval        (seconds)
cost_per_step(P) ≈ (C_trainer + C_sandbox(P) + C_fixed) × step_time_s(P) / 3600
```

`C_*`는 USD/시간이고 `t_*`는 초이므로(`scripts/ops/bench.sh`의 `eval_p50_s`, `eval_p95_s`도 초) 3600으로 나눕니다. `C_sandbox(P)`는 pod `P`개가 차지하는 노드의 시간당 요금입니다. 노드 하나에 pod 하나인 gVisor는 `P × C_node`입니다. `g4dn.metal` 한 대에 pod 8개까지 들어가는 Kata GPU는 최소 `ceil(P / 8) × C_metal`이지만, 템플릿의 topology spread가 pod를 여러 노드에 나눠 놓는 쪽을 선호하고 placeholder와 빈 노드도 과금되므로, 청구액은 실제로 실행된 metal 노드별 가동 시간에 단가를 곱해 더하세요.

`P`는 `cost_per_step`이 줄어드는 동안만 늘리세요. `t_eval`은 `scripts/ops/bench.sh`로, step 시간은 trainer 로그로, pod가 평가를 처리한 시간의 비율은 `avg_over_time(sandbox_busy[1h])`로 측정합니다. `sandbox_busy`는 평가 하나를 처리하는 동안(CPU 작업과 하위 프로세스 대기 포함) 1이므로 GPU 자체의 사용률과는 다릅니다. 예를 들어 핸즈온 최소 경로(EC2 소계 3.416 USD/시간)에 `g5.xlarge` 한 대를 추가하면 시간당 4.422 USD가 됩니다. 이때 step 시간이 약 23% 넘게 줄어야 step당 비용이 내려갑니다(3.416 ÷ 4.422 ≈ 0.773). control plane 같은 고정비를 포함하면 이 기준은 조금 낮아집니다.

### 빈 노드를 빨리 반납하기

| NodePool | consolidation | 설정한 대기 시간의 노드 비용 |
|---|---|---|
| `sandbox-gvisor` | `WhenEmpty`, 10분 | `g5.xlarge` 0.1677 USD |
| `sandbox-kata-gpu` | `WhenEmpty`, 30분 | `g4dn.metal` 3.912 USD |
| `sandbox-kata-cpu` | `WhenEmptyOrUnderutilized`, 5분 | `c8i.2xlarge` 0.0312 USD |
| `trainer` | `WhenEmpty`, 15분 | 예: `g6e.48xlarge` 7.5328 USD |

`consolidateAfter`는 회수를 검토하기 전에 기다리는 시간이므로, 실제 과금은 노드가 종료될 때까지 이어집니다. `WhenEmpty`는 workload pod가 없는 노드만 대상으로 합니다(karpenter.sh 문서). 핸즈온의 EKS 관리형 노드 그룹(CDK 스택)에는 consolidation이 없으므로, 노드 수를 줄이거나 노드 그룹을 삭제할 때까지 과금됩니다. 노드 수를 직접 줄이세요(예: `aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu --scaling-config minSize=0,maxSize=1,desiredSize=0`).

### metal의 30분 대기와 warm placeholder

metal 노드는 클러스터에 합류하는 데 몇 분, kata-deploy 설치에 다시 몇 분이 걸립니다. 노드가 빈 채로 30분을 채우면 약 3.912 USD(10분 만에 다시 쓰면 1.304 USD)가 들고, 30분이 지난 뒤에도 노드가 종료될 때까지 요금이 이어집니다. 대신 30분 안에 풀을 다시 띄울 때(blue/green, 롤백 대기) cold start를 피할 수 있습니다. run이 끝나 풀을 다시 띄우지 않는다면 노드 그룹이나 `consolidateAfter`를 줄이세요.

`k8s/production/warm-capacity.yaml`의 placeholder는 낮은 priority의 pause pod(CPU 60, 메모리 200 GiB)로 예비 metal 노드 하나를 확보해 둡니다. 샌드박스 pod를 배치할 자리가 필요하면 placeholder가 몇 초 만에 선점되고, Karpenter가 새 예비 노드를 백그라운드에서 띄웁니다. placeholder가 샌드박스 pod와 다른 노드에 있으면 그 예비 노드 한 대분이 시간당 7.824 USD, 하루 187.776 USD 더 듭니다. placeholder는 CPU와 메모리만 요청하므로 샌드박스 pod가 적어 자리가 남는 노드에 함께 배치될 수 있고, 그 시간에는 노드 요금을 한 번만 계산하세요. 풀이 metal 노드 여러 대를 쓰거나, 노드 장애로 reward 계산이 멈추면 안 되는 run에서만 쓰세요. 그 밖에는 `kubectl -n sandbox scale deployment/kata-metal-warm-placeholder --replicas=0`으로 꺼 두세요. pod 4개짜리 Kata 풀 두 개(blue/green)는 metal 한 대(pod 8개의 메모리 합 208 GiB, 노드 384 GiB)에 모두 배치되므로 placeholder 없이도 전환할 수 있습니다.

### 런타임과 GPU 선택

| 구성 | 노드 단가 | GPU 하나의 시간당 단가 | 조건 |
|---|---|---|---|
| gVisor, `g5.xlarge` | 1.006 | 1.006 (A10G) | 노드 하나에 샌드박스 하나 |
| gVisor, `g5.2xlarge` | 1.212 | 1.212 (A10G) | NodePool이 `g5.xlarge` 용량을 확보하지 못할 때, 약 20% 더 비쌈 |
| gVisor, `g6.xlarge` (대체) | 0.8048 | 0.8048 (L4) | `g5.xlarge`보다 20% 저렴 |
| Kata, `g4dn.metal`, 8개 사용 | 7.824 | 0.978 (T4) | T4 8개를 모두 사용 |
| Kata, `g4dn.metal`, 4개 사용 | 7.824 | 1.956 (사용한 T4) | `KATA_QEMU_REPLICAS` 기본값 4 |
| Kata, 서울 `g4dn.metal`, 8개 사용 | 9.624 | 1.203 (T4) | |

GPU당 단가만으로 고르지는 마세요. A10G와 T4는 speedup을 서로 비교할 수 없고 격리 수준도 다릅니다. gVisor nvproxy는 드라이버 ioctl을 허용 목록으로 필터링하지만, 드라이버 자체의 취약점에 대한 방어는 VM 경계보다 약합니다. Kata는 GPU를 VM에 직접 할당합니다. 격리 요구 사항으로 런타임을 먼저 정하고, Kata를 쓴다면 metal 노드의 T4 8개를 모두 쓰도록 풀 크기를 맞추세요.

### CPU 계층과 Spot

- **Kata CPU 계층 (c8i)**: nested virtualization으로 `.metal` 없이 Kata를 실행합니다. 핸즈온에서는 `g4dn.metal`을 띄우기 전에 적은 비용으로 Kata를 연습하는 용도로 쓰고, Production에서는 GPU가 필요 없는 작업(정적 검사, nvcc 컴파일)을 GPU 계층보다 먼저 처리할 수 있습니다. CPU 풀(`gvisor-cpu`, `kata-*-cpu`)은 routing 표에 있고 시나리오 C의 reward 루프([10 c8i 단독 저비용 경로](../handson/10_cpu_only.md))가 사용하지만, CPU 계층과 GPU 계층을 잇는 2단 구성은 구현하지 않았습니다.
- **이미 구현된 절감 방법**: `KernelRewards`의 세 reward 함수는 샌드박스 평가 결과를 공유합니다. 이미 캐시에 있는 completion과, 코드가 없거나 정적 정책을 위반한 completion은 샌드박스로 보내지 않습니다. 한 호출 안에서 동일한 completion은 한 번만 전송됩니다. batch 전체가 한 풀의 캐시에 있으면 버전 전환 뒤에도 전송이 없습니다. 결과가 여러 풀에 걸쳐 있으면 이번 풀로 다시 보내고, 채점 도중 풀이 또 바뀌면 세 번째 호출에 batch 전체를 담으므로 전송 건수가 잠시 늘 수 있습니다.
- **Spot은 CPU 계층에만**: `infra/karpenter/nodepools.yaml`에서 Spot을 허용하는 NodePool은 `sandbox-kata-cpu`뿐입니다. CPU 계층에서는 중단되어도 다른 pod로 재시도하면 됩니다. GPU 노드가 평가 도중 회수되어 연결이 끊기면 gateway가 다른 Ready pod로 재시도하고, 끝내 처리하지 못한 요청은 `sandbox_error`가 됩니다(TRL은 제외, veRL은 format 점수만). GPU 용량을 다시 확보하는 몇 분 동안은 처리량도 줄어듭니다. GPU 계층에 Spot을 쓰려면 `sandbox_error` 경보와 공유 스토리지 checkpoint를 먼저 준비하세요.

### trainer: HyperPod `ml.*`와 EC2

| EC2 | USD/시간 | HyperPod | USD/시간 | 차액 | 배수 |
|---|---|---|---|---|---|
| `g4dn.xlarge` | 0.526 | `ml.g4dn.xlarge` | 0.7364 | 0.2104 | 1.40 |
| `g5.xlarge` | 1.006 | `ml.g5.xlarge` | 1.408 | 0.402 | 약 1.40 |
| `g5.2xlarge` | 1.212 | `ml.g5.2xlarge` | 1.515 | 0.303 | 1.25 |
| `g6.xlarge` | 0.8048 | `ml.g6.xlarge` | 1.127 | 0.3222 | 약 1.40 |
| `g6.2xlarge` | 0.9776 | `ml.g6.2xlarge` | 1.222 | 0.2444 | 1.25 |
| `g6e.xlarge` | 1.861 | `ml.g6e.xlarge` | 2.61 | 0.749 | 약 1.40 |

차액으로 얻는 것은 관리형 노드 수명 주기입니다. health monitoring agent, deep health check(InstanceStress, InstanceConnectivity), 문제 노드를 재부팅하거나 교체하는 `NodeRecovery: Automatic`, training operator의 job 재시작과 로그 기반 hang 감지가 여기에 포함됩니다.

EC2(시나리오 A)에서도 노드 교체 자체는 managed node group이나 Karpenter로 구성할 수 있습니다. 차이는 GPU 수준의 deep health check와 job 재시작을 관리형 기능으로 제공받는지 여부입니다. "차액 × run 시간"과 "예상 장애 횟수 × (마지막 checkpoint 뒤 잃는 진행 + 복구 시간) × 클러스터 시간당 비용 + 운영자 시간"을 비교해 판단하세요. 핸즈온 단일 노드(`g5.2xlarge`와 `ml.g5.2xlarge`)라면 차액이 시간당 0.303 USD, 24시간 run에 7.272 USD입니다.

HyperPod는 EC2와 별도인 "ml.<type> for cluster usage" 한도를 씁니다. EC2의 "Running On-Demand G and VT instances" 한도는 vCPU 기준이고 기본값이 0일 수 있으니 두 한도를 함께 확인하세요(`g4dn.metal`은 96 vCPU 필요).

!!! question "❓ 오해: Kata + g4dn.metal은 GPU당 훨씬 비싸다"
    T4 8개를 모두 사용하면 T4당 0.978 USD/시간으로 `g5.xlarge`의 A10G(1.006 USD/시간)와 큰 차이가 없습니다. 비용을 늘리는 요인은 노드 단위 과금(4개만 쓰면 사용한 T4당 1.956 USD)과, 여기에 추가되는 빈 노드의 30분 대기와 placeholder입니다.

!!! question "❓ 오해: HyperPod를 쓰면 클러스터 전체에 프리미엄이 붙는다"
    `ml.*` 단가는 HyperPod 인스턴스 그룹에만 적용됩니다. B1에서는 trainer만 HyperPod에 있고, 샌드박스는 같은 EKS 클러스터의 EC2 노드에서 실행되므로 EC2 단가로 과금됩니다. B2에서는 샌드박스도 HyperPod 인스턴스 그룹(기본 `ml.g5.xlarge` 2대)에서 실행되므로 `ml.*` 단가가 붙습니다. system 노드는 두 시나리오 모두 EC2 단가입니다. control plane에는 EKS 요금이, NAT와 스토리지에는 각 서비스의 요금이 적용됩니다.

## 시간당 추정: 핸즈온 경로

최소 경로는 `scripts/02_create_cluster.sh`가 만드는 구성(시나리오 A, gVisor만)이고, 전체 경로는 여기에 Kata CPU 노드(`WITH_KATA_CPU=1`, `scripts/kata/cpu_nodes.sh`)와 Kata GPU 노드(`WITH_KATA_GPU=1`, `scripts/kata/gpu_nodes.sh`)를 추가합니다. Kata CPU 노드 그룹은 `WITH_KATA_CPU=1`을 설정하고 `02_create_cluster.sh`를 다시 실행하면 CDK 스택에 추가됩니다. Kata GPU 노드 그룹은 IOMMU AMI를 먼저 만들고(`scripts/kata/gpu_nodes.sh`) `KATA_IOMMU_AMI_ID`와 `WITH_KATA_GPU=1`을 설정한 뒤 다시 실행해야 합니다. AMI ID 없이 `WITH_KATA_GPU=1`만 설정하면 CDK 설정 단계에서 중단됩니다.

| 항목 | 수량 | 단가 (USD/시간) | 시간당 USD |
|---|---|---|---|
| `m6i.large` (system) | 2 | 0.096 | 0.192 |
| `g5.xlarge` (gVisor 샌드박스) | 2 | 1.006 | 2.012 |
| `g5.2xlarge` (trainer, 시나리오 A) | 1 | 1.212 | 1.212 |
| **최소 경로 EC2 소계** | | | **3.416** |
| `c8i.2xlarge` (Kata CPU) | 1 | 0.37484 | 0.37484 |
| `g4dn.metal` (Kata GPU) | 1 | 7.824 | 7.824 |
| **전체 경로 EC2 소계** | | | **11.61484** |
| EKS control plane, NAT gateway, EBS gp3, SSM access instance(`t4g.nano`), KMS 키 | | 각 요금 페이지 | 별도 |

- 시나리오 B1은 `g5.2xlarge` 대신 `ml.g5.2xlarge`를 쓰므로 최소 경로 3.719, 전체 경로 11.91784 USD/시간입니다.
- 시나리오 B2는 EC2 gVisor 노드 대신 HyperPod `ml.g5.xlarge`(1.408) 2대에서 샌드박스를 실행합니다. 최소 경로는 0.192 + 1.515 + 2.816 = 4.523, Kata 노드를 더한 전체 경로는 12.72184 USD/시간입니다.
- 계산 예시: 최소 경로 8시간에 `g4dn.metal` 2시간을 더하면 3.416 × 8 + 7.824 × 2 = 42.976 USD입니다(EC2만, 소요 시간은 가정).
- 클러스터를 삭제한 뒤에도 Kata용 AMI의 EBS snapshot과 ECR 이미지는 남아 과금될 수 있습니다. `scripts/08_cleanup.sh`는 AMI 등록 해제 여부를 묻고, `--images`를 지정하면 ECR 저장소도 삭제합니다.

Production veRL 예시에서 `g6e.48xlarge` trainer(30.13118 USD/시간)와 함께 gVisor 샌드박스 16개를 쓰면, 샌드박스 비용만 16.096 USD/시간으로 trainer 비용의 약 53%입니다. 8개면 8.048 USD/시간(약 27%)입니다. 비중이 작지 않으므로 풀 크기는 위의 step당 비용 기준으로 정하세요.

## 확인 방법

첫 명령은 클러스터의 노드를 인스턴스 유형, NodePool, 역할 label과 함께 출력하고, 두 번째 명령은 태그 `project=gpu-sandbox-on-aws`가 붙은 EC2 인스턴스를 표로 출력합니다. `AWS_REGION`이 필요하니 먼저 `source scripts/config.env`를 실행하세요.

```bash
# what is running now, and from which NodePool or node group
kubectl get nodes -L node.kubernetes.io/instance-type,karpenter.sh/nodepool,gpusandbox/role
# instances tagged by this asset (the same check scripts/08_cleanup.sh prints at the end)
aws ec2 describe-instances --region "${AWS_REGION}" \
  --filters "Name=tag:project,Values=gpu-sandbox-on-aws" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name]' --output table
```

**확인할 것:**

- 첫 명령의 INSTANCE-TYPE 열에서 GPU 노드(`g4dn.metal`, `g5.*`, `g6.*`, `g6e.*`, `p5.*`)가 현재 몇 대인지 확인합니다. 그 수에 위 단가를 곱한 값이 대략적인 시간당 EC2 비용입니다.
- 실습을 마친 뒤라면 두 번째 명령의 표가 비어 있어야 합니다.

**문제가 생기면:** 정리한 뒤에도 과금이 계속되면 [문제 해결](../reference/troubleshooting.md)의 "정리와 비용" 표를 보세요.

실습을 마치면 [99 정리](../handson/99_cleanup.md)를 실행하세요(시나리오 B라면 `scripts/hyperpod/delete.sh`를 먼저). 관련 페이지: [04 플랫폼과 인스턴스 선택](../concepts/04_platforms_and_instances.md), [01 용량과 노드 관리](01_capacity_and_nodes.md), [06 veRL로 확장](06_scaling_with_verl.md).

## 적용 범위와 한계

- **모든 금액은 계산입니다.** 이 저장소에는 AWS에서 측정한 사용량이나 청구 금액이 없습니다.
- **빠진 항목이 있습니다.** EKS control plane, NAT gateway, EBS, FSx for Lustre, ECR, CloudWatch 요금은 계산에 넣지 않았습니다.
- **step 시간은 직접 측정해야 합니다.** "비용을 줄이는 방법"의 step당 비용 식은 `t_generate`, `t_update`, `t_eval`을 알고 있다고 가정합니다. 이 값들은 run마다 다릅니다.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | EC2 On-Demand 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
    | SageMaker AI 요금 (HyperPod `ml.*`) | https://aws.amazon.com/sagemaker/ai/pricing/ |
    | EKS 요금 (control plane) | https://aws.amazon.com/eks/pricing/ |
    | Karpenter (AWS provider) | https://github.com/aws/karpenter-provider-aws |
    | 정리 스크립트 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/08_cleanup.sh |

    전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-production-08-cost)
