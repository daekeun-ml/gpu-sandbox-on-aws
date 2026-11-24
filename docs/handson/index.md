---
hide:
  - footer
---

# 핸즈온 전체 흐름

<span id="00-핸즈온-전체-흐름"></span>

## 터미널에서 바로 시작하기 { #quickstart }

```bash
git clone https://github.com/daekeun-ml/gpu-sandbox-on-aws.git
cd gpu-sandbox-on-aws
./scripts/quickstart.sh
```

이미 코드를 받았다면 프로젝트 폴더에서 마지막 줄만 실행하세요. AWS CLI에서 실습 계정을 확인하고 `A`, `B1`, `B2`, `C` 중 하나를 고르면 `init` 단계가 설정 파일을 만듭니다. `infra`에서 클러스터를 만들 때부터 요금이 발생합니다.

실행 순서만 보려면 `./scripts/quickstart.sh B2 plan`처럼 시나리오 이름 뒤에 `plan`을 붙이세요. [실습을 마친 뒤 리소스 정리하기](cleanup.md#quickstart)

## 실습 경로 고르기

가이드를 보며 직접 실행하려면 아래에서 구성을 고르고 **공통 절차 01~03**을 진행하세요. 채점 pool에서 `verified`를 확인하면 시나리오 실습을 시작합니다.

- **[EC2에서 GPU 학습 (A)](common/01_provision/index.md#__tabbed_1_1)**　모델이 만든 코드를 gVisor에서 채점하고 그 점수로 모델을 학습합니다.
- **[HyperPod에서 GPU 학습 (B1)](common/01_provision/index.md#__tabbed_1_2)**　HyperPod에서 모델을 학습하고 EC2의 gVisor pool이 코드를 채점합니다.
- **[CPU와 GPU를 모두 HyperPod에 배치 (B2)](common/01_provision/index.md#__tabbed_1_3)**　HyperPod로 EKS를 구성하고, 학습 GPU에서 생성한 코드를 두 채점 GPU에 보냅니다.
- **[GPU 없이 pool 교체 연습 (C)](common/01_provision/index.md#__tabbed_1_4)**　CPU 런타임 세 개를 비교하고, 시뮬레이터가 답안을 보내는 동안 v1을 v2로 바꿉니다.

경로를 정했다면 **노드와 채점 pool을 차례로 확인**하세요. 먼저 노드가 `Ready`인지 보세요. 이 상태가 되면 Kubernetes가 pod를 배치할 수 있습니다. 그다음 pool을 배포하고 검증 스크립트를 실행하세요. 시험 답안의 판정과 나머지 검사가 모두 통과하면 마지막 줄에 `verified`가 표시됩니다.

## 배포 전 확인 { #사전-준비 }

A, B1, C는 [시작하기](start.md)에서 환경을 준비한 뒤 `scripts/01_check_prereqs.sh`로 계정, 리전, EC2 vCPU 쿼터를 확인하세요. B1은 HyperPod 학습 노드 쿼터도 필요합니다. B2는 [SageMaker 쿼터 세 가지 확인](common/01_provision/hyperpod.md#시작-전에-확인할-쿼터)에서 시작하세요.

<div id="소요-시간과-비용" markdown>

??? note "경로별 쿼터, 시간당 비용, 예상 소요 시간"
    클러스터 생성에는 보통 20~30분을 잡습니다. `g5.2xlarge`에서 이미지와 모델을 받는 시간까지 포함해 GRPO 5스텝은 약 12분, 60스텝은 약 50분 걸렸습니다. CPU에서 시뮬레이션 30배치를 실행한 예는 약 16분입니다.

    | 기본 구성 | 필요한 EC2 쿼터 (vCPU) | 노드 비용 (USD/시간) |
    |---|---|---:|
    | A (EC2 GPU) | G/VT 16, Standard 6 | 3.42 |
    | B1 (HyperPod trainer) | G/VT 8, Standard 6 | 3.72 |
    | B2 (HyperPod 전체) | 0 (워커 쿼터는 SageMaker에서 확인) | 4.56 |
    | C (CPU 전용) | Standard 14 | 0.57 |

    B1은 SageMaker의 `ml.g5.2xlarge for cluster usage`도 1대분 필요합니다. 쿼터는 실습할 리전에서 확인하세요.

    `us-west-2`와 `us-east-1` 온디맨드 요금으로 계산한 추정치입니다. EKS 컨트롤 플레인(표준 지원 0.10 USD/시간), 접속 인스턴스, NAT gateway, 디스크, 로그와 전송 요금은 별도입니다.

    - **gVisor 버전 교체** 시나리오 A에서 v1과 v2를 함께 띄우는 동안 `g5.xlarge` 두 대가 더 필요합니다. G/VT 쿼터는 24 vCPU, 추가 노드 비용은 약 2.01 USD/시간입니다.
    - <span id="최소-경로와-전체-경로"></span>**Kata 비교 실습** A에 `c8i.2xlarge`와 `g4dn.metal`을 모두 추가하면 노드 합계는 약 11.61 USD/시간입니다. G/VT 쿼터는 112 vCPU, gVisor 버전 교체 중에는 120 vCPU입니다. CPU 노드와 임시 AMI 빌더까지 함께 띄울 때 Standard는 16 vCPU입니다. [인스턴스별 비용과 쿼터](../concepts/04_platforms_and_instances.md)

</div>

??? note "도구 설치, 설정 파일, 쿼터 확인 위치"
    - AWS CLI, CDK CLI 2.1148.1 이상, Node.js 22 또는 24, `kubectl`, Helm, Docker, Python, `jq`, Session Manager plugin을 준비합니다. `docker buildx version`도 확인하세요. HyperPod에는 `git`이 필요합니다. CDK 라이브러리 설치와 계정과 리전별 bootstrap은 [클러스터와 이미지](common/01_provision/cdk.md)에 있습니다.
    - 설정 파일이 없으면 `scripts/config.env.example`을 `scripts/config.env`로 복사합니다. `AWS_REGION`, `CLUSTER_NAME`, `SCENARIO`를 확인하고, 기본 경로에서는 `WITH_KATA_CPU`와 `WITH_KATA_GPU`를 `0`으로 둡니다. 이미지를 빌드할 x86_64 호스트에는 여유 디스크 100 GB 이상을 권장합니다.
    - Service Quotas에서 실습 리전을 고른 뒤 EC2의 `Running On-Demand G and VT instances`와 `Running On-Demand Standard` 적용값을 봅니다. C에서는 `c8i.2xlarge`의 지원 기능에 `nested-virtualization`이 있는지도 확인합니다.

## 경로별 진행 순서 { #단계-순서 }

클러스터를 만들면 노드와 NAT gateway 등의 요금이 발생합니다. 선택한 탭의 <span id="필수-경로">단계</span>를 따라가세요. 각 탭 끝에는 펼쳐 보는 <span id="시나리오별-aws-구성">구성도</span>가 있습니다. A, B1, C는 `cdk/tunnel.sh`를 별도 터미널에 열어 두고, 관리형 B2는 EKS API에 직접 접속합니다.

=== "A (EC2 GPU)"

    [01 클러스터 프로비저닝](common/01_provision/index.md#__tabbed_1_1) → [02 런타임 준비](common/02_runtimes/index.md#__tabbed_1_1) → [03 채점 pool 배포와 검증](common/03_pools/index.md#__tabbed_1_1)

    pool을 검증한 뒤 **[A 시나리오 실습](scenarios/a/index.md)**을 시작하세요.

    **완료 확인** `routing`에서 pool을, `batch`(원본 `reward_batch`)에서 채점 결과를, `train`에서 모델 업데이트를 확인하세요. 전환했다면 v2 판정이 기록된 뒤 `--finish`로 v1을 줄입니다.

    ??? note "A 구성도"
        학습은 `g5.2xlarge` 한 대, 기본 채점은 `g5.xlarge` 두 대가 맡습니다.

        [![EC2 trainer가 두 gVisor 샌드박스에 채점을 요청하는 시나리오 A](../images/architecture/scenario-a.drawio.png)](../images/architecture/scenario-a.drawio.png)

=== "B1 (HyperPod + EC2)"

    [01 클러스터 프로비저닝](common/01_provision/index.md#__tabbed_1_2) → [02 런타임 준비](common/02_runtimes/index.md#__tabbed_1_2) → [03 채점 pool 배포와 검증](common/03_pools/index.md#__tabbed_1_2)

    pool을 검증한 뒤 **[B1 시나리오 실습](scenarios/b/b1.md)**을 시작하세요.

    **완료 확인** `reward_batch`에는 EC2 pool의 채점 결과가 나오고 HyperPod Job은 `Completed`가 됩니다.

    ??? note "B1 구성도"
        HyperPod `ml.g5.2xlarge` 한 대가 학습하고 EC2 `g5.xlarge` 두 대가 채점합니다.

        [![HyperPod 학습 노드에서 같은 EKS 클러스터의 EC2 채점 pool을 호출하는 구성](../images/architecture/scenario-b1.drawio.png)](../images/architecture/scenario-b1.drawio.png)

=== "B2 (HyperPod)"

    [01 클러스터 프로비저닝](common/01_provision/index.md#__tabbed_1_3) → [02 런타임 준비](common/02_runtimes/index.md#__tabbed_1_3) → [03 채점 pool 배포와 검증](common/03_pools/index.md#__tabbed_1_3)

    pool을 검증한 뒤 **[B2 시나리오 실습](scenarios/b/b2.md)**을 시작하세요.

    **완료 확인** `reward_batch`에서 `gvisor-hyperpod` v1 판정을, [벤치마크 결과](benchmarks/index.md#hyperpod-b2)에서 시스템 노드와 학습 노드가 보낸 요청의 성공 건수와 채점 시간을 확인하세요.

    ??? note "B2 구성도"
        `system`은 `ml.m5.xlarge` 한 대, `trainer`는 `ml.g5.2xlarge` 한 대, `sandbox`는 `ml.g5.xlarge` 두 대입니다. 네 워커 모두 HyperPod에서 실행됩니다.

        [![B2의 EKS 제어 영역과 세 HyperPod 인스턴스 그룹](../images/architecture/scenario-b2.drawio.png?layout=aws)](../images/architecture/scenario-b2.drawio.png?layout=aws)

=== "C (CPU)"

    [01 클러스터 프로비저닝](common/01_provision/index.md#__tabbed_1_4) → [02 런타임 준비](common/02_runtimes/index.md#__tabbed_1_4) → [03 채점 pool 배포와 검증](common/03_pools/index.md#__tabbed_1_4)

    pool을 검증한 뒤 **[C 시나리오 실습](scenarios/c/index.md)**을 시작하세요.

    **완료 확인** `SWITCH` 뒤에 새로 채점한 `batch`에서 `kata-clh-cpu` v2 판정을 확인하세요. 한 배치에는 채점 버전이 하나만 나와야 합니다.

    ??? note "C 구성도"
        시스템 노드의 시뮬레이터가 답안을 보내고 `c8i.2xlarge` 한 대에 있는 세 CPU 런타임을 비교합니다.

        [![GPU 없이 c8i 노드에서 세 CPU pool을 실행하는 시나리오 C](../images/architecture/scenario-c.drawio.png)](../images/architecture/scenario-c.drawio.png)

## 시나리오 실습을 마친 뒤 { #선택-기능과-운영 }

- [런타임 벤치마크](benchmarks/index.md)에서 학습이나 CPU 시뮬레이션이 끝난 뒤 같은 답안을 반복 채점합니다. B2에서는 시스템 워커와 학습 워커가 보낸 요청을 비교합니다.
- 에피소드 하나의 답안을 여러 번 고쳐 제출하려면 [멀티턴 채점](extensions/multi_turn.md)을 진행하세요. C는 기존 CPU 노드를 사용하고 A는 여유 GPU 한 장이 필요합니다.


## 실습 리소스 정리 { #다음-단계 }

A, B1, C는 [정리](cleanup.md), 관리형 B2는 [HyperPod 마법사 스택 정리](scenarios/b/b2.md#cleanup)를 따르세요. pod를 0개로 줄여도 노드 요금은 계속 발생합니다. 잠시 쉬었다 이어갈 때는 [EC2 노드 그룹 일시 정지](cleanup.md#일시-정지-노드-그룹을-0으로-줄이기)를 참고하세요.

## 구성과 로그 찾아보기 { #아키텍처 }

[배포 구성도 데모](https://dohbsn4kn34ya.cloudfront.net/architecture.html)에서 시나리오를 골라 채점 요청이 어느 노드를 지나는지 따라가 보세요.

??? note "<span id='노드-그룹과-네임스페이스'>노드 그룹과 네임스페이스</span>"
    `rl-trainer`의 학습 Job과 `sandbox`의 채점 pod는 서로 다른 노드에 배치합니다. 샌드박스 노드의 `gpusandbox/role` taint는 해당 toleration이 있는 pod만 받습니다. GPU 장치를 관리하는 DaemonSet도 이 노드에서 실행됩니다.

    | 기본 노드 그룹 | 역할과 런타임 |
    |---|---|
    | `system` | `m6i.large` 두 대에서 CoreDNS와 add-on 실행 |
    | `trainer` | A의 `g5.2xlarge`에서 모델 학습 |
    | `sandbox-gvisor` | A와 B1의 `g5.xlarge` 두 대에서 `gvisor` GPU pool 실행 |
    | `sandbox-kata-cpu` | `c8i.2xlarge`에서 `gvisor-cpu`, `kata-clh-cpu`, `kata-qemu-cpu` pool 실행 |
    | `sandbox-kata-gpu` | `g4dn.metal`에서 `kata-qemu-nvidia-gpu` RuntimeClass로 `kata-qemu` pool 실행 |

??? note "작업 PC의 접속 경로와 trainer의 채점 요청"
    <span id="인프라와-접속-cdk-터널"></span>**클러스터 접속.** `cdk/tunnel.sh`는 작업 PC의 `127.0.0.1:8443`을 SSM 접속 인스턴스를 거쳐 private EKS API에 연결합니다. `kubectl config current-context`를 실행해 `<CLUSTER_NAME>-tunnel`인지 확인하세요.

    <span id="요청-경로"></span>**채점 요청.** trainer가 `sandbox-routing` ConfigMap에서 배치에 쓸 버전을 읽습니다. 해당 headless Service의 DNS에서 Ready pod 주소를 얻어 `/v1/evaluate`로 요청합니다. pod는 토큰 서명을 JWKS로 확인하고 판정을 돌려줍니다. 이미 채점 중인 pod가 `503 busy`를 반환하면 클라이언트가 다른 pod로 재시도합니다. [pool 배포와 인증](common/03_pools/details.md)

??? note "<span id='확인-방법'>Ready, verified, reward_batch를 로그에서 읽는 법</span>"
    - 노드의 `Ready`는 Kubernetes가 워크로드를 배치할 준비가 됐다는 뜻입니다. `ops/verify.sh`의 `verified`는 샌드박스 pool의 자동 검사를 통과했다는 뜻입니다. 첫 번째 커널 비교는 출력된 두 값을 직접 봅니다.
    - `reward_batch`는 trainer가 채점한 제출 수와 판정을 보여 줍니다. `sandbox_error`가 반복되면 학습 스텝과 함께 [pool 상태와 인증](../reference/troubleshooting.md)을 확인하세요.
    - 원본 이벤트를 보려면 실행할 명령 앞에 `GPUSANDBOX_LOG=json`을 붙입니다. 실행 중인 일반 Kubernetes Job의 로그는 `kubectl -n rl-trainer logs -f job/<Job 이름>`으로 확인하세요.

??? note "스크립트가 오래 기다릴 때 확인할 것"
    - gVisor 시험용 pod는 최대 15분, 샌드박스 pool 배포는 최대 30분까지 기다립니다. 이 값은 대기 한도입니다. 채점 pod가 `Pending`이면 `kubectl -n sandbox describe pod <pod-name>`의 이벤트에서 배치되지 않은 이유를 확인하세요.
    - Kata CPU 설치는 실습 계정에서 약 14분 걸렸고, 대부분은 kata-deploy 설치 시간이었습니다. Kata GPU는 `KATA_IOMMU_AMI_ID`가 비어 있을 때 첫 실행에서 AMI를 만듭니다. 출력된 ID를 저장하고 `WITH_KATA_GPU=1`로 원래 시나리오의 클러스터 생성 명령을 다시 실행하세요. 두 번째 `scripts/kata/gpu_nodes.sh` 실행에서 metal 노드의 `nvidia.com/pgpu`를 확인합니다.
    - HyperPod 클러스터가 `InService`여도 trainer 인스턴스는 준비 중일 수 있습니다. 학습을 제출하기 전에 노드가 `Ready`이고 `Schedulable`인지 확인하세요. [HyperPod 확인 방법](scenarios/b/b1.md#확인-방법)

스크립트별 인자, 대기 시간, 재실행 동작은 [스크립트 레퍼런스](../reference/scripts.md)에 있습니다. [런타임 비교](../concepts/02_isolation_runtimes.md), [용어 사전](../reference/glossary.md), [실행 기록](../reference/sources.md#aws-실행-기록), [참고 자료](../reference/references.md#ref-handson-00-overview)
