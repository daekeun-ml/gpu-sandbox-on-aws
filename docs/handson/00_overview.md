# 00 핸즈온 전체 흐름

샌드박스가 코드를 채점하고 그 결과가 모델 학습에 쓰이는 과정을 따라갑니다. GPU가 없어도 채점과 pool 교체를 연습할 수 있습니다.

## 실습 경로 고르기

- **[A · EC2에서 GPU 학습](01_cluster_and_images.md)**　모델이 만든 코드를 gVisor에서 채점하고 그 점수로 모델을 학습합니다.
- **[B1 · HyperPod에서 GPU 학습](07_hyperpod.md)**　HyperPod에서 모델을 학습하고 EC2의 gVisor pool이 코드를 채점합니다.
- **[B2 · CPU와 GPU를 모두 HyperPod에 배치](07_hyperpod_b2.md)**　HyperPod로 EKS를 구성하고, 학습 GPU에서 생성한 코드를 두 채점 GPU에 보냅니다.
- **[C · GPU 없이 pool 교체 연습](10_cpu_only.md)**　CPU 런타임 세 개를 비교하고, 시뮬레이터가 답안을 보내는 동안 v1을 v2로 바꿉니다.

경로를 정했다면 **노드와 채점 pool을 차례로 확인**하세요. 노드의 `Ready`는 Kubernetes가 pod를 배치할 수 있다는 뜻입니다. 그 노드에 띄운 pool의 `verified`는 시험 답안이 기대한 판정을 받았다는 뜻입니다. 두 결과는 실습 중 서로 다른 시점에 확인합니다.

## 배포 전 확인 { #사전-준비 }

[시작하기](../getting_started.md)에서 로컬 테스트와 `scripts/config.env` 설정을 마쳤다면, 저장소 루트에서 아래 명령을 실행하세요. 도구와 AWS 계정 설정을 조회합니다.

```bash
scripts/01_check_prereqs.sh
```

출력에서 **AWS 계정과 리전**이 맞는지, EC2 쿼터가 선택한 경로에 충분한지 확인하세요. HyperPod를 쓰려면 Service Quotas에서 SageMaker 쿼터도 별도로 확인합니다.

<div id="소요-시간과-비용" markdown>

??? note "경로별 쿼터, 시간당 비용, 예상 소요 시간"
    클러스터 생성에는 보통 20~30분을 잡습니다. `g5.2xlarge`에서 이미지와 모델을 받는 시간까지 포함해 GRPO 5스텝은 약 12분, 60스텝은 약 50분 걸렸습니다. CPU에서 시뮬레이션 30배치를 실행한 예는 약 16분입니다.

    | 기본 구성 | 필요한 EC2 쿼터 (vCPU) | 노드 비용 (USD/시간) |
    |---|---|---:|
    | A · EC2 GPU | G/VT 16, Standard 6 | 3.42 |
    | B1 · HyperPod trainer | G/VT 8, Standard 6 | 3.72 |
    | B2 · HyperPod 전체 | 0 (워커 쿼터는 SageMaker에서 확인) | 4.56 |
    | C · CPU 전용 | Standard 14 | 0.57 |

    B1은 SageMaker의 `ml.g5.2xlarge for cluster usage`도 1대분 필요합니다. 쿼터는 실습할 리전에서 확인하세요.

    `us-west-2`와 `us-east-1` 온디맨드 요금으로 계산한 추정치입니다. EKS 컨트롤 플레인(표준 지원 0.10 USD/시간), 접속 인스턴스, NAT gateway, 디스크, 로그와 전송 요금은 별도입니다.

    - **gVisor 버전 교체** 시나리오 A에서 v1과 v2를 함께 띄우는 동안 `g5.xlarge` 두 대가 더 필요합니다. G/VT 쿼터는 24 vCPU, 추가 노드 비용은 약 2.01 USD/시간입니다.
    - <span id="최소-경로와-전체-경로"></span>**Kata 비교 실습** A에 `c8i.2xlarge`와 `g4dn.metal`을 모두 추가하면 노드 합계는 약 11.61 USD/시간입니다. G/VT 쿼터는 112 vCPU, gVisor 버전 교체 중에는 120 vCPU입니다. CPU 노드와 임시 AMI 빌더까지 함께 띄울 때 Standard는 16 vCPU입니다. [인스턴스별 비용과 쿼터](../concepts/04_platforms_and_instances.md)

</div>

??? note "도구 설치, 설정 파일, 쿼터 확인 위치"
    - AWS CLI, CDK CLI 2.1148.1 이상, Node.js 22 또는 24, `kubectl`, Helm, Docker, Python, `jq`, Session Manager plugin을 준비합니다. `docker buildx version`도 확인하세요. HyperPod에는 `git`이 필요합니다. CDK 라이브러리 설치와 계정·리전별 bootstrap은 [01 클러스터와 이미지](01_cluster_and_images.md)에 있습니다.
    - 설정 파일이 없으면 `scripts/config.env.example`을 `scripts/config.env`로 복사합니다. `AWS_REGION`, `CLUSTER_NAME`, `SCENARIO`를 확인하고, 기본 경로에서는 `WITH_KATA_CPU`와 `WITH_KATA_GPU`를 `0`으로 둡니다. 이미지를 빌드할 x86_64 호스트에는 여유 디스크 100 GB 이상을 권장합니다.
    - Service Quotas에서 실습 리전을 고른 뒤 EC2의 `Running On-Demand G and VT instances`와 `Running On-Demand Standard` 적용값을 봅니다. C에서는 `c8i.2xlarge`의 지원 기능에 `nested-virtualization`이 있는지도 확인합니다.

## 경로별 진행 순서 { #단계-순서 }

클러스터를 만들면 노드와 NAT gateway 등의 요금이 발생합니다. 각 탭에서 <span id="필수-경로">실행 순서</span>와 <span id="시나리오별-aws-구성">구성도</span>를 볼 수 있습니다. CDK로 만든 A·B1·C에 접속할 때는 `cdk/tunnel.sh`를 별도 터미널에서 계속 실행해 두세요.

=== "A · EC2 GPU"

    1. **[클러스터와 이미지 준비](01_cluster_and_images.md)**　`SCENARIO=A`에서 `scripts/02_create_cluster.sh`를 실행합니다. 터널을 연 뒤 `kubectl get nodes`에서 trainer 한 대와 gVisor 노드 두 대가 `Ready`인지 확인합니다. `scripts/03_build_push_images.sh`가 출력한 이미지 URI 세 개를 설정 파일에 넣습니다.
    2. **[GPU 확인](02_gvisor.md)**　`scripts/04_install_gpu_stack.sh`로 gVisor와 GPU 연결을 확인합니다. 시험용 pod가 `cuda ok:`와 GPU 이름을 출력해야 합니다.
    3. **[채점 pool 배포와 검증](04_sandbox_pools.md)**　`scripts/05_setup_namespaces_auth.sh`로 네임스페이스와 인증을 준비하고 `scripts/06_deploy_sandboxes.sh gvisor v1`로 pool을 만듭니다. `scripts/ops/verify.sh gvisor v1`의 마지막 줄이 `pool sandbox-gvisor-v1 verified`인지 확인합니다.
    4. **[GRPO 학습](05_grpo_training.md)**　`scripts/07_run_grpo.sh`를 실행합니다. `routing`은 trainer가 사용할 pool을 읽었다는 신호입니다. `batch` 줄(원본 JSON에서는 `reward_batch`)에 제출물의 판정이 나오고 학습 스텝이 진행되는지 봅니다.
    5. **[학습 중 v2로 전환](06_sandbox_update.md)**　v1과 v2가 동시에 GPU를 쓸 수 있게 샌드박스 노드를 먼저 네 대로 늘립니다. 학습이 진행되는 동안 다른 작업 터미널에서 `scripts/ops/rollout.sh gvisor v1 v2`를 실행합니다. 새 배치가 v2에서 채점된 뒤 `--finish`로 v1을 줄입니다.

    ??? note "A 구성도 · 학습 노드와 채점 노드"
        trainer의 `g5.2xlarge`는 모델을 업데이트합니다. 제출 코드를 실행하는 A10G는 `g5.xlarge` 두 대에 한 장씩 있습니다. 그림을 누르면 확대할 수 있습니다.

        [![EC2 trainer가 두 gVisor 샌드박스에 채점을 요청하는 시나리오 A](../images/architecture/scenario-a.drawio.png)](../images/architecture/scenario-a.drawio.png)

=== "B1 · HyperPod + EC2"

    1. **[B1 클러스터와 이미지 준비](07_hyperpod.md)**　`scripts/02_create_cluster.sh --hyperpod`로 EKS와 EC2 채점 노드를 만듭니다. 터널을 열고 `HYPERPOD=1 scripts/03_build_push_images.sh`로 trainer에 `hyperpodrun`을 포함합니다. 출력된 이미지 URI를 설정 파일에 넣습니다.
    2. **학습 노드 연결**　`scripts/04_install_gpu_stack.sh`로 EC2 GPU를 확인한 뒤 `scripts/hyperpod/create.sh`를 실행합니다. HyperPod trainer 노드가 `Ready`이고 `node-health-status`가 `Schedulable`인지 확인합니다.
    3. **채점 pool 검증**　`scripts/05_setup_namespaces_auth.sh`를 실행하고 `scripts/06_deploy_sandboxes.sh gvisor v1`로 EC2 pool을 배포합니다. `scripts/ops/verify.sh gvisor v1`에서 `verified`를 확인합니다.
    4. **[한 스텝의 학습 결과 확인](07_hyperpod.md#확인-방법)**　`scripts/hyperpod/run_grpo.sh 1`로 Job을 제출합니다. trainer pod가 HyperPod 노드에 배치되고 `reward_batch`에 EC2 pool의 판정이 남는지, Job이 `Completed`로 끝나는지 봅니다.

    ??? note "B1 구성도 · HyperPod trainer와 EC2 채점 pool"
        trainer는 `ml.g5.2xlarge`, gVisor 샌드박스는 EC2 `g5.xlarge` 두 대에 있습니다.

        [![HyperPod 학습 노드에서 같은 EKS 클러스터의 EC2 채점 pool을 호출하는 구성](../images/architecture/scenario-b1.drawio.png)](../images/architecture/scenario-b1.drawio.png)

=== "B2 · HyperPod"

    1. **[세 그룹과 쿼터 확인](07_hyperpod_b2.md)**　`us-east-1`에서 CPU 한 대, 학습 GPU 한 대, 채점 GPU 두 대분의 SageMaker 쿼터를 확인합니다.
    2. **워커 준비**　`scripts/hyperpod/create_managed.sh`로 EKS와 HyperPod를 함께 만들고 네 노드가 `Ready`인지 봅니다. 채점 노드의 드라이버를 맞춘 뒤 v1 pool을 배포합니다.
    3. **학습과 벤치마크**　GRPO Job이 `Completed`가 되면 `scripts/hyperpod/bench_b2.sh 32`로 같은 pool에 고정 커널을 보냅니다. [두 클라이언트의 결과](08_benchmark.md#hyperpod-b2)

    [![B2의 EKS 제어 영역과 세 HyperPod 인스턴스 그룹](../images/architecture/scenario-b2.drawio.png?layout=aws)](../images/architecture/scenario-b2.drawio.png?layout=aws)

=== "C · CPU"

    1. **[CPU 클러스터 준비](10_cpu_only.md)**　`scripts/02_create_cluster.sh --cpu-only`로 EKS와 `c8i.2xlarge` 노드를 만들고 터널을 엽니다. `scripts/03_build_push_images.sh --no-trainer`가 출력한 sandbox와 control 이미지 URI를 설정 파일에 넣습니다.
    2. **런타임 확인**　`scripts/kata/cpu_nodes.sh`로 같은 노드에 gVisor, Kata + Cloud Hypervisor, Kata + QEMU 시험용 pod를 띄웁니다. 각 pod에서 본 커널과 마지막 줄의 호스트 커널을 비교합니다.
    3. **세 pool 배포와 검증**　`KATA_CPU_REPLICAS=1`을 설정 파일에 넣고 `ACTIVE_RUNTIME=kata-clh-cpu scripts/05_setup_namespaces_auth.sh`를 실행합니다. 세 CPU pool을 v1으로 배포한 뒤 각각 `scripts/ops/verify.sh`로 검증합니다. [pool별 배포 명령](10_cpu_only.md)
    4. **채점 버전 전환**　한 터미널에서 `scripts/ops/simulate.sh 30 20`으로 준비된 답안을 보냅니다. 다른 터미널에서 `scripts/ops/rollout.sh kata-clh-cpu v1 v2`를 실행합니다. 전환 전후의 배치 로그에 v1과 v2가 차례로 나오고 한 배치 안에 두 버전이 섞이지 않으면 됩니다.

    ??? note "C 구성도 · 모델 없이 세 런타임 비교"
        시스템 노드의 시뮬레이터가 CPU 채점 pool에 답안을 보냅니다. 세 런타임은 모두 같은 `c8i.2xlarge`를 사용합니다.

        [![GPU 없이 c8i 노드에서 세 CPU pool을 실행하는 시나리오 C](../images/architecture/scenario-c.drawio.png)](../images/architecture/scenario-c.drawio.png)

## 목적에 맞춰 더 해 볼 실습 { #선택-기능과-운영 }

- **[03 · Kata에서 GPU 확인](03_kata.md)**　gVisor와 VM 격리를 비교하려면 Kata + QEMU 게스트 안에서 T4를 확인하세요. 먼저 IOMMU용 AMI를 만든 뒤 `WITH_KATA_GPU=1`로 `g4dn.metal` 노드를 추가합니다. CPU만 비교할 때는 `WITH_KATA_CPU=1`과 `c8i.2xlarge`를 사용합니다.
- **[08 · 런타임 벤치마크](08_benchmark.md#runtime-results)**　비교할 v1 pool을 검증하고 학습이 끝난 뒤 같은 코드를 반복 채점합니다. 요청 한 건의 채점 시간과 pool 전체의 초당 처리량을 비교합니다.
- **[11 · 여러 턴에 걸쳐 코드 고치기](11_multi_turn.md)**　C 경로에서 에피소드마다 샌드박스를 하나씩 빌립니다. 같은 에피소드의 턴들이 같은 pod에서 실행되고 종료 시 claim이 반납되는지 확인합니다.
- **[09 · 채점 기록 재생](09_demo_site.md)**　클러스터를 띄우기 전에 결과를 보고 싶으면 [공개 데모](https://dohbsn4kn34ya.cloudfront.net/)를 열어 보세요. 내 기록을 S3와 CloudFront로 배포하는 절차는 09편에 있습니다.

## 실습 리소스 정리 { #다음-단계 }

**B2는 [HyperPod 마법사 스택 정리](07_hyperpod_b2.md#cleanup)를 따르세요.** 워커와 EKS 제어 영역을 함께 삭제한 뒤 실습 전용 버킷과 ECR 저장소를 정리합니다.

A·B1·C는 터널을 열어 둔 채 [99 정리](99_cleanup.md)를 진행합니다. B1은 `scripts/hyperpod/delete.sh`로 HyperPod를 먼저 삭제합니다. Agent Sandbox를 사용했다면 claim과 warm pool부터 정리하세요. 이어서 `scripts/08_cleanup.sh`로 EKS 스택을 삭제하고 남은 노드를 확인합니다. 직접 배포한 데모 사이트는 별도로 정리합니다.

ECR 이미지까지 삭제하려면 정리할 때 `--images`를 붙입니다. 샌드박스 pod를 0개로 줄여도 EC2 노드 요금은 계속 발생합니다. 잠시 쉬었다 이어갈 때는 [노드 그룹 일시 정지](99_cleanup.md#일시-정지-노드-그룹을-0으로-줄이기)를 참고하세요.

## 구성과 로그 찾아보기 { #아키텍처 }

[배포 구성도 데모](https://dohbsn4kn34ya.cloudfront.net/architecture.html)에서 시나리오를 고르면 채점 요청이 어느 노드를 지나는지 볼 수 있습니다.

??? note "<span id='노드-그룹과-네임스페이스'>노드 그룹과 네임스페이스</span>"
    `rl-trainer`의 학습 Job과 `sandbox`의 채점 pod는 서로 다른 노드에 배치합니다. 샌드박스 노드의 `gpusandbox/role` taint는 해당 toleration이 있는 pod만 받습니다. GPU 장치를 관리하는 DaemonSet도 이 노드에서 실행됩니다.

    | 기본 노드 그룹 | 역할과 런타임 |
    |---|---|
    | `system` | `m6i.large` 두 대에서 CoreDNS와 add-on 실행 |
    | `trainer` | A의 `g5.2xlarge`에서 모델 학습 |
    | `sandbox-gvisor` | A·B1의 `g5.xlarge` 두 대에서 `gvisor` GPU pool 실행 |
    | `sandbox-kata-cpu` | `c8i.2xlarge`에서 `gvisor-cpu`, `kata-clh-cpu`, `kata-qemu-cpu` pool 실행 |
    | `sandbox-kata-gpu` | `g4dn.metal`에서 `kata-qemu-nvidia-gpu` RuntimeClass로 `kata-qemu` pool 실행 |

??? note "작업 PC의 접속 경로와 trainer의 채점 요청"
    <span id="인프라와-접속-cdk-터널"></span>**클러스터 접속.** `cdk/tunnel.sh`는 작업 PC의 `127.0.0.1:8443`을 SSM 접속 인스턴스를 거쳐 private EKS API에 연결합니다. `kubectl config current-context`에서 `<CLUSTER_NAME>-tunnel`을 확인할 수 있습니다.

    <span id="요청-경로"></span>**채점 요청.** trainer가 `sandbox-routing` ConfigMap에서 배치에 쓸 버전을 읽습니다. 해당 headless Service의 DNS에서 Ready pod 주소를 얻어 `/v1/evaluate`로 요청합니다. pod는 토큰 서명을 JWKS로 확인하고 판정을 돌려줍니다. 이미 채점 중인 pod가 `503 busy`를 반환하면 클라이언트가 다른 pod로 재시도합니다. [pool 배포와 인증](04_sandbox_pools.md)

??? note "<span id='확인-방법'>Ready, verified, reward_batch를 로그에서 읽는 법</span>"
    - 노드의 `Ready`는 Kubernetes가 워크로드를 배치할 준비가 됐다는 뜻입니다. `ops/verify.sh`의 `verified`는 샌드박스 pool의 자동 검사를 통과했다는 뜻입니다. 첫 번째 커널 비교는 출력된 두 값을 직접 봅니다.
    - `reward_batch`는 trainer가 채점한 제출 수와 판정을 보여 줍니다. `sandbox_error`가 반복되면 학습 스텝과 함께 [pool 상태와 인증](../reference/troubleshooting.md)을 확인하세요.
    - 원본 이벤트를 보려면 실행할 명령 앞에 `GPUSANDBOX_LOG=json`을 붙입니다. 실행 중인 일반 Kubernetes Job은 `kubectl -n rl-trainer logs -f job/<Job 이름>`으로도 확인할 수 있습니다.

??? note "스크립트가 오래 기다릴 때 확인할 것"
    - gVisor 시험용 pod는 최대 15분, 샌드박스 pool 배포는 최대 30분까지 기다립니다. 이 값은 대기 한도입니다. 채점 pod가 `Pending`이면 `kubectl -n sandbox describe pod <pod-name>`의 이벤트에서 배치되지 않은 이유를 확인하세요.
    - Kata CPU 설치는 실습 계정에서 약 14분 걸렸고, 대부분은 kata-deploy 설치 시간이었습니다. Kata GPU는 `KATA_IOMMU_AMI_ID`가 비어 있을 때 첫 실행에서 AMI를 만듭니다. 출력된 ID를 저장하고 `WITH_KATA_GPU=1`로 원래 시나리오의 클러스터 생성 명령을 다시 실행하세요. 두 번째 `scripts/kata/gpu_nodes.sh` 실행에서 metal 노드의 `nvidia.com/pgpu`를 확인합니다.
    - HyperPod 클러스터가 `InService`여도 trainer 인스턴스는 준비 중일 수 있습니다. 학습을 제출하기 전에 노드가 `Ready`이고 `Schedulable`인지 확인하세요. [HyperPod 확인 방법](07_hyperpod.md#확인-방법)

스크립트별 인자, 대기 시간, 재실행 동작은 [스크립트 레퍼런스](../reference/scripts.md)에 있습니다. [런타임 비교](../concepts/02_isolation_runtimes.md) · [용어 사전](../reference/glossary.md) · [실행 기록](../reference/sources.md#aws-실행-기록) · [참고 자료](../reference/references.md#ref-handson-00-overview)
