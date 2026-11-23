# 스크립트 레퍼런스

!!! info "TL;DR"
    표에서 하려는 작업을 고르세요. 각 항목에서 실행 방법과 성공했을 때의 출력을 확인할 수 있습니다. 같은 명령을 다시 실행하면 어떻게 동작하는지도 설명합니다.

명령은 저장소 루트에서 실행하세요. CDK로 만든 클러스터에 `kubectl`이나 Helm으로 접속할 때는 별도 터미널에서 `cdk/tunnel.sh`를 실행하고 터널을 열어 두세요. 처음부터 실습한다면 [핸즈온 전체 흐름](../handson/00_overview.md)에서 시나리오를 고르세요.

| 하려는 작업 | 스크립트 |
|---|---|
| AWS 설정 확인, EKS 생성, 이미지 준비 | [01~03과 터널](#기본-순서) |
| 런타임 설치와 채점 pool 배포 | [04~06](#scripts04_install_gpu_stacksh), [Kata](#kata) |
| EKS에서 GRPO 실행 (A) | [07_run_grpo.sh](#scripts07_run_grposh) |
| HyperPod에서 GRPO 실행 (B1과 B2) | [hyperpod/run_grpo.sh](#scriptshyperpodrun_grposh) |
| pool 검증, GPU 없는 시뮬레이션 (C), 버전 전환, 지연 측정 | [검증과 운영](#검증과-운영) |
| 에피소드마다 샌드박스 할당 | [Agent Sandbox 확장](#확장) |
| 평가 기록을 웹에 공개 | [데모 사이트](#데모-사이트) |
| 실습 리소스 삭제 | [정리 실습](../handson/99_cleanup.md) |

## 기본 순서

### `scripts/01_check_prereqs.sh`

- **하는 일**: 로컬 도구, AWS identity, G and VT와 Standard vCPU 쿼터, `KATA_CPU_INSTANCE_TYPE`의 nested virtualization 지원, GPU 인스턴스 유형의 AZ별 제공 여부를 조회합니다. 아무것도 만들거나 바꾸지 않습니다.
- **사용법**: `scripts/01_check_prereqs.sh` (인자 없음)
- **실행 시점**: CDK 경로(A, B1, 기존 B2, C)에서는 `02_create_cluster.sh` 전에 실행하세요. 관리형 B2의 인스턴스 쿼터는 [B2 실습](../handson/07_hyperpod_b2.md)에서 안내하는 대로 별도로 조회합니다.
- **시간과 과금**: 짧음(조회만). 과금되는 리소스는 없습니다.
- **다시 실행할 때**: 읽기 전용이라 몇 번을 실행해도 결과에 영향이 없습니다. 쿼터 증가를 요청한 뒤 다시 실행해 값을 확인하세요.
- **성공 여부 확인**: 마지막 로그가 `Done. Request quota increases before 02_create_cluster.sh if any value above is too low.`입니다. 쿼터가 충분한지는 스크립트가 판정하지 않으니 출력된 값을 필요한 값과 직접 비교하세요.
- **막히면**: [문제 해결: 설정과 스크립트](troubleshooting.md#설정과-스크립트), [01 클러스터와 이미지](../handson/01_cluster_and_images.md)

### `scripts/02_create_cluster.sh`

- **하는 일**: `cdk/deploy.sh`를 실행해 CDK 스택 `<CLUSTER_NAME>-cdk`(VPC, private endpoint EKS, add-on, 시나리오별 노드 그룹, access instance)를 배포합니다.
- **사용법**: `scripts/02_create_cluster.sh` (A, 또는 `config.env`의 `SCENARIO`), `--hyperpod` (B1), `--hyperpod-b2` (기존 CDK 방식의 B2), `--cpu-only` (C). Kata 노드 그룹은 `scripts/config.env`의 `WITH_KATA_CPU=1`, `WITH_KATA_GPU=1`(`KATA_IOMMU_AMI_ID` 필요)로 추가합니다.
- **실행 시점**: CDK 경로에서는 `01_check_prereqs.sh` 다음에 실행합니다. 나중에 Kata 노드 그룹을 추가할 때는 처음과 같은 옵션으로 다시 실행하세요.
- **시간과 과금**: 스크립트의 예상 시간은 20~30분입니다. 실습 계정에서 시나리오 C는 약 20분 걸렸습니다. EKS 컨트롤 플레인, NAT gateway, `m6i.large` x2, `t4g.nano`에 더해 A와 B1은 `g5.xlarge` x2, A는 `g5.2xlarge`, C나 `WITH_KATA_CPU=1`은 `c8i.2xlarge`, `WITH_KATA_GPU=1`은 `g4dn.metal`의 과금이 시작됩니다.
- **다시 실행할 때**: CDK가 달라진 부분만 바꾸므로 설정이 같으면 변경이 없고, `WITH_KATA_*`를 바꾸면 그 노드 그룹만 바뀝니다. 배포된 시나리오와 다르면 `the stack runs scenario <X>, not <Y>`로 멈추며, 의도한 전환이라면 `CHANGE_SCENARIO=1`을 붙입니다(노드 그룹이 교체됨). `WITH_KATA_GPU=1`이면 실행할 때마다 `metal` 입력을 요구하고, CDK 밖에서 바꾼 노드 수는 먼저 되돌려야 합니다([06](../handson/06_sandbox_update.md)).
- **성공 여부 확인**: CDK `Outputs`에 `EndpointPublicAccess = false`와 `Next:` 안내가 나옵니다. 터널을 연 뒤 `kubectl get nodes`에 system 2대와 시나리오의 노드(A: trainer 1대와 sandbox-gvisor 2대, C: sandbox-kata 1대)가 `Ready`입니다.
- **막히면**: [문제 해결: CDK와 터널](troubleshooting.md#cdk와-터널), [문제 해결: 클러스터와 노드](troubleshooting.md#클러스터와-노드)

### `cdk/tunnel.sh`

- **하는 일**: SSM Session Manager 세션으로 작업 PC의 `127.0.0.1:<port>`를 private EKS API endpoint에 연결하고, kubectl context `<CLUSTER_NAME>-tunnel`이 그 포트를 쓰게 합니다. Ctrl-C를 누를 때까지 실행됩니다.
- **사용법**: `cdk/tunnel.sh [local_port]` (기본 8443). 두 번째 터미널에서 실행하고 열어 둡니다.
- **실행 시점**: CDK 경로에서는 `02_create_cluster.sh`를 마치고 `03_build_push_images.sh`로 넘어가기 전에 터널을 여세요. 이후 kubectl이나 Helm으로 작업하는 동안(04 이후, Kata, 운영, HyperPod, 확장)에는 터널을 유지합니다.
- **시간과 과금**: 짧음. 새로 만드는 리소스는 없습니다(access instance는 `02_create_cluster.sh`가 만듦).
- **다시 실행할 때**: 실행할 때마다 kubeconfig의 context와 cluster 항목을 다시 쓰고 새 세션을 엽니다. 세션이 끊기면 다시 실행하면 되고, 예전 터널이 같은 포트를 쓰고 있으면 그 터미널을 먼저 닫으세요.
- **성공 여부 확인**: `kubectl context <CLUSTER_NAME>-tunnel -> 127.0.0.1:8443 -> <endpoint> (via i-...); Ctrl-C closes it` 로그 뒤에 `Waiting for connections...`가 나옵니다.
- **막히면**: [문제 해결: CDK와 터널](troubleshooting.md#cdk와-터널)

### `scripts/03_build_push_images.sh`

- **하는 일**: sandbox, trainer, control 이미지를 `linux/amd64`로 빌드해 ECR의 `<ECR_REPO_PREFIX>/<이름>:<IMAGE_TAG>`로 push하고, `config.env`에 넣을 `export` 줄을 출력합니다. ECR 저장소가 없으면 IMMUTABLE 태그와 scan on push로 만듭니다.
- **사용법**: `scripts/03_build_push_images.sh`, trainer 이미지를 건너뛰려면 `--no-trainer`. 시나리오 B는 `HYPERPOD=1 scripts/03_build_push_images.sh`로 trainer에 `hyperpodrun`을 넣습니다.
- **실행 시점**: CDK 경로에서는 `02_create_cluster.sh` 다음에, 관리형 B2에서는 클러스터를 만드는 동안 이미지를 준비할 수 있습니다. `04_install_gpu_stack.sh`를 실행하는 시나리오는 그 전에 빌드를 마치세요. A는 기본 설정으로, B1과 B2는 `HYPERPOD=1`로, C는 `--no-trainer`로 빌드합니다.
- **시간과 과금**: 빌드 호스트와 네트워크에 따라 다릅니다. ECR 저장 용량이 과금됩니다.
- **다시 실행할 때**: 태그가 IMMUTABLE이라 같은 `IMAGE_TAG`로 실행하면 첫 이미지(sandbox)의 push가 실패하고 멈춥니다. `scripts/config.env`의 `IMAGE_TAG`를 새 값으로 바꾼 뒤(명령 앞에 붙인 값은 `config.env`가 덮어씀) 다시 실행하고, 출력된 URI로 `config.env`를 갱신하세요.
- **성공 여부 확인**: `Add to scripts/config.env:` 뒤에 `SANDBOX_IMAGE_URI`, `TRAINER_IMAGE_URI`, `CONTROL_IMAGE_URI`의 export 줄 3개(`--no-trainer`는 `TRAINER_IMAGE_URI`가 빠진 2개)가 나옵니다.
- **막히면**: [문제 해결: 설정과 스크립트](troubleshooting.md#설정과-스크립트), [01 클러스터와 이미지](../handson/01_cluster_and_images.md)

### `scripts/04_install_gpu_stack.sh`

- **하는 일**: NVIDIA device plugin(CDI 모드)을 Helm으로 설치하고 `CDI_DISABLE_HOOKS` env를 설정합니다. 이어서 `gvisor` RuntimeClass를 등록하고 smoke pod 하나로 gVisor 커널과 CUDA 동작을 확인합니다.
- **사용법**: `scripts/04_install_gpu_stack.sh` (인자 없음). 시나리오가 B2나 C이면 RuntimeClass 등록과 smoke pod 검사를 건너뜁니다.
- **실행 시점**: `03_build_push_images.sh` 다음, `05_setup_namespaces_auth.sh` 전에 실행합니다. A와 B1은 전체 단계를 실행하고, B2에서는 device plugin만 설치합니다. C는 이 단계 대신 `kata/cpu_nodes.sh`를 실행합니다.
- **시간과 과금**: device plugin은 Helm `--wait`, smoke pod timeout은 15분입니다. 새로 과금되는 리소스는 없습니다.
- **다시 실행할 때**: `helm upgrade --install`과 `kubectl apply`로 다시 적용하고, smoke pod는 새 이름으로 만든 뒤 끝나면 지웁니다. sandbox-gvisor 노드의 GPU가 모두 쓰이고 있으면(`06_deploy_sandboxes.sh`의 pool) smoke pod를 만들기 전에 `every GPU on the sandbox-gvisor nodes is in use`로 멈추니, 안내된 `kubectl -n sandbox scale ... --replicas=0`으로 GPU를 비운 뒤 실행하고 `06_deploy_sandboxes.sh gvisor v1`로 pool을 되돌리세요.
- **성공 여부 확인**: `gpusandbox/device-plugin=cdi` 노드마다 GPU 1(재시작 직후에는 잠시 `0`), 이어서 smoke pod 로그의 `cuda ok: NVIDIA A10G 2048.0`이 나옵니다. smoke pod가 실패해도 스크립트는 경고만 내고 끝나므로 이 줄을 직접 확인하세요(B2와 C는 `skipping the gvisor RuntimeClass and the smoke pod`로 끝남).
- **막히면**: [문제 해결: gVisor](troubleshooting.md#gvisor), [02 gVisor GPU 샌드박스](../handson/02_gvisor.md)

### `scripts/05_setup_namespaces_auth.sh`

- **하는 일**: 네임스페이스(Pod Security), trainer RBAC, NetworkPolicy를 적용하고, `ops/sync_jwks.sh`로 JWKS ConfigMap을 만든 뒤 `rl-trainer`에 라우팅 설정을 담은 `sandbox-routing` ConfigMap을 저장합니다.
- **사용법**: `scripts/05_setup_namespaces_auth.sh`. 처음 쓸 pool은 `ACTIVE_RUNTIME`과 `ACTIVE_VERSION`(기본 `gvisor`, `v1`)으로 정합니다. 예: C는 `ACTIVE_RUNTIME=kata-clh-cpu`, B2는 `ACTIVE_RUNTIME=gvisor-hyperpod`.
- **실행 시점**: 모든 시나리오에서 `04_install_gpu_stack.sh`(C는 `kata/cpu_nodes.sh`)를 마친 뒤 `06_deploy_sandboxes.sh` 전에 실행합니다.
- **시간과 과금**: 짧음. 과금되는 리소스는 없습니다.
- **다시 실행할 때**: 모두 `kubectl apply`지만, routing 표의 active pool을 `ACTIVE_RUNTIME`과 `ACTIVE_VERSION`(없으면 `gvisor/v1`)으로 다시 쓰고 `sandbox`의 NetworkPolicy를 핸즈온 규칙으로 되돌립니다. 버전 교체 뒤나 시나리오 C에서는 지금 쓰는 값을 지정해 실행하고, 서명 키만 갱신할 때는 `ops/sync_jwks.sh`를 쓰세요(production gateway를 쓰면 gateway 매니페스트도 다시 적용).
- **성공 여부 확인**: 마지막에 출력되는 routing.json 앞부분의 `"active"`가 처음 쓸 pool입니다. A와 B1은 `{"runtime": "gvisor", "version": "v1"}`입니다.
- **막히면**: [문제 해결: 401, 403 응답](troubleshooting.md#401-403-응답), [문제 해결: NetworkPolicy](troubleshooting.md#networkpolicy), [04 샌드박스 pool 배포와 검증](../handson/04_sandbox_pools.md)

### `scripts/06_deploy_sandboxes.sh`

- **하는 일**: 런타임 프로필(`k8s/sandbox/profiles/<runtime>.env`)과 버전 파일(`k8s/sandbox/versions/<version>.env`)로 샌드박스 pool `sandbox-<runtime>-<version>`(Deployment와 headless Service)을 배포하고 rollout이 끝나기를 기다립니다.
- **사용법**: `scripts/06_deploy_sandboxes.sh <runtime> [version] [replicas]`. runtime은 `gvisor`, `gvisor-hyperpod`, `kata-qemu`, `kata-clh`(실험), `gvisor-cpu`, `kata-clh-cpu`, `kata-qemu-cpu`이고, version은 `v1`(기본) 또는 `v2`, replicas를 생략하면 프로필에 지정한 수만큼 pod를 배포합니다.
- **실행 시점**: `05_setup_namespaces_auth.sh` 다음에 pool마다 실행합니다. A와 B1은 `gvisor`, B2는 `gvisor-hyperpod`, C는 CPU pool 세 개를 배포합니다.
- **시간과 과금**: rollout timeout은 30분입니다. 기존 노드를 쓰므로 새로 과금되는 리소스는 없습니다.
- **다시 실행할 때**: `kubectl apply`라 매니페스트가 같으면 바뀌지 않고, 이미지나 설정이 바뀌었으면 Deployment가 pod를 새로 만듭니다. replica 수가 인자나 프로필 값으로 돌아가므로, 0으로 줄인 pool(`ops/rollout.sh --finish`, `04_install_gpu_stack.sh`의 안내)을 다시 시작할 때도 같은 명령을 실행할 수 있습니다.
- **성공 여부 확인**: rollout이 끝나고 pod가 `1/1 Running`입니다.
- **막히면**: [문제 해결: 샌드박스 pool과 readiness](troubleshooting.md#샌드박스-pool과-readiness), [04 샌드박스 pool 배포와 검증](../handson/04_sandbox_pools.md)

### `scripts/07_run_grpo.sh`

- **하는 일**: GRPO 학습 Job `grpo-<RUN_ID>`를 `rl-trainer`에 만들고, pod가 Ready가 되면 로그를 한 줄 요약으로 보여 줍니다. Ctrl-C는 로그 출력만 멈추고 학습은 계속됩니다.
- **사용법**: `scripts/07_run_grpo.sh [max_steps]` (기본 60). `RUN_ID`와 `MODEL_ID`(기본 `Qwen/Qwen2.5-Coder-1.5B-Instruct`)는 환경 변수로 바꾸고, 원본 JSON은 `GPUSANDBOX_LOG=json scripts/07_run_grpo.sh`로 봅니다.
- **실행 시점**: `06_deploy_sandboxes.sh`와 `ops/verify.sh` 다음에 실행합니다. 시나리오 A의 학습 단계입니다. B에서는 `hyperpod/run_grpo.sh`를, C에서는 `ops/simulate.sh`를 실행합니다.
- **시간과 과금**: 실습 계정의 `g5.2xlarge`에서 기본 60스텝은 약 50분, 5스텝은 약 12분 걸렸습니다. 이미지와 모델을 내려받는 시간도 포함합니다. 새로 과금되는 리소스는 없습니다.
- **다시 실행할 때**: `RUN_ID` 기본값이 실행 시각이라 실행할 때마다 새 Job이 생기고, 이전 Job은 끝난 뒤 하루 동안 남습니다. trainer 노드의 GPU는 하나이므로 이전 학습이 실행 중이면 새 pod는 Pending으로 남고, 스크립트는 30분 대기 뒤 실패합니다(Job은 남음).
- **성공 여부 확인**: `routing  mode direct  runtime gvisor  version v1 ...` 뒤에 `batch`와 `train` 줄이 이어지고, 끝에 `train done ...`과 `done  output /outputs/grpo/final  reward_batches <int>`가 나옵니다.
- **막히면**: [문제 해결: 학습](troubleshooting.md#학습), [05 On-policy GRPO 학습](../handson/05_grpo_training.md)

### `scripts/08_cleanup.sh`

- **하는 일**: 클러스터 이름을 입력받은 뒤 `cdk/destroy.sh --yes`로 pool, Job, CDK 스택을 지우고, `config.env`에 ID가 있는 AMI(`KATA_IOMMU_AMI_ID`, `HYPERPOD_B2_AMI_ID`)와 스냅샷을 하나씩 확인한 뒤 지웁니다. 마지막에 남은 인스턴스를 조회합니다.
- **사용법**: `scripts/08_cleanup.sh`, ECR 저장소까지 지우려면 `--images`. B1과 기존 CDK 방식의 B2는 먼저 `scripts/hyperpod/delete.sh`를 실행합니다.
- **실행 시점**: CDK로 만든 클러스터를 정리할 때 실행합니다. 터널을 켜 두면 클러스터 안의 워크로드부터 지웁니다. 관리형 B2는 [마법사 스택 정리 절차](../handson/07_hyperpod_b2.md#cleanup)를 따르세요.
- **시간과 과금**: 기록 없음(CloudFormation 삭제를 기다림). CDK 스택 리소스의 과금이 끝나고, secrets용 KMS 키는 7일 삭제 대기에 들어갑니다.
- **다시 실행할 때**: 실행할 때마다 확인 단어를 묻고 `cdk/destroy.sh`부터 다시 실행합니다. 이미 지운 AMI의 ID가 `config.env`에 남아 있으면 AMI 단계에서 멈출 수 있으니, `--images`로 다시 실행하기 전에 그 ID를 지우세요.
- **성공 여부 확인**: 마지막 표(`project=gpu-sandbox-on-aws` 태그가 붙은 인스턴스)가 비어 있습니다.
- **막히면**: [문제 해결: 정리와 비용](troubleshooting.md#정리와-비용), [99 정리](../handson/99_cleanup.md)

## CDK

### `cdk/deploy.sh`

- **하는 일**: `scripts/config.env`를 읽어 CDK 스택 `<CLUSTER_NAME>-cdk`를 `cdk deploy --require-approval broadening`으로 배포합니다. `02_create_cluster.sh`가 이 스크립트를 실행합니다.
- **사용법**: `cdk/deploy.sh [A|B1|B2|C] [--with-kata-cpu]` (인자가 없으면 `SCENARIO`). `ADMIN_PRINCIPAL_ARN`을 비우면 현재 IAM 사용자나 역할이 클러스터 관리자가 되고, 시나리오를 바꿀 때는 `CHANGE_SCENARIO=1`을 붙입니다.
- **실행 시점**: CDK로 클러스터를 만들 때는 보통 `02_create_cluster.sh`가 이 스크립트를 호출합니다.
- **시간과 과금**: `02_create_cluster.sh`와 같습니다.
- **다시 실행할 때**: 스택 출력 `Scenario`와 다른 시나리오면 `CHANGE_SCENARIO=1` 없이는 멈추고, 같으면 달라진 부분만 바꿉니다. IAM이나 security group 권한이 넓어지는 변경이 있으면 `cdk deploy`가 승인을 묻습니다.
- **성공 여부 확인**: CDK `Outputs`(`EndpointPublicAccess = false` 포함)와 `Next:` 안내가 나옵니다.
- **막히면**: [문제 해결: CDK와 터널](troubleshooting.md#cdk와-터널)

### `cdk/destroy.sh`

- **하는 일**: 클러스터 API에 접속되면 `rl-trainer`의 Job과 `sandbox`의 Deployment, Service를 먼저 지우고, `cdk destroy --force`로 스택을 지운 뒤 스택 밖에 남은 Lambda 로그 그룹을 지웁니다. ECR 저장소는 지우지 않고 삭제 명령만 안내합니다.
- **사용법**: `cdk/destroy.sh [--yes]` (`--yes`는 확인을 건너뜀). 보통은 `08_cleanup.sh`가 실행합니다.
- **실행 시점**: CDK로 만든 스택을 정리할 때 실행합니다.
- **시간과 과금**: 기록 없음(CloudFormation 삭제를 기다림). 스택 리소스의 과금이 끝납니다.
- **다시 실행할 때**: 클러스터 안의 삭제는 `--all`이라 지울 것이 없어도 안전하고, 터널이 꺼져 있으면 경고만 내고 스택 삭제로 넘어갑니다. 스택이 이미 없을 때 `cdk destroy`가 어떻게 끝나는지는 코드로 알 수 없습니다.
- **성공 여부 확인**: 인스턴스 표가 비어 있고 `ECR repositories are kept. To delete them:` 안내가 나옵니다.
- **막히면**: [문제 해결: 정리와 비용](troubleshooting.md#정리와-비용), [99 정리](../handson/99_cleanup.md)

## Kata

### `scripts/kata/cpu_nodes.sh`

- **하는 일**: `sandbox-kata-cpu` 노드 그룹이 있는지 확인하고 kata-deploy(Helm)와 `gvisor-cpu` RuntimeClass를 설치합니다. 이어서 `gvisor-cpu`, `kata-clh`, `kata-qemu` smoke pod로 샌드박스 안에서 보이는 커널을 출력합니다.
- **사용법**: `scripts/kata/cpu_nodes.sh` (인자 없음). 노드 그룹은 `02_create_cluster.sh --cpu-only`(C)나 `WITH_KATA_CPU=1`로 만듭니다.
- **실행 시점**: C는 `03_build_push_images.sh` 다음(04 대신), 다른 시나리오는 `04_install_gpu_stack.sh` 다음에 Kata CPU 노드를 쓸 때 실행합니다.
- **시간과 과금**: 실습에서는 약 14분 걸렸고, 대부분은 kata-deploy 설치 시간이었습니다. kata-deploy의 대기 한도는 20분입니다. 새로 과금되는 리소스는 없습니다(`c8i.2xlarge`는 `02_create_cluster.sh`에서 생김).
- **다시 실행할 때**: `helm upgrade --install`과 `kubectl apply`로 다시 적용하고, smoke pod는 새 이름으로 만든 뒤 지웁니다. kata-deploy release를 `kata/gpu_nodes.sh`와 함께 쓰므로, 다시 실행하면 실험용 CLH GPU 값(`ENABLE_EXPERIMENTAL_CLH_GPU=1`)이 빠진 기본 값으로 돌아갑니다.
- **성공 여부 확인**: `gvisor-cpu`, `kata-clh`, `kata-qemu`의 `kernel seen inside: ...` 커널이 모두 마지막 줄의 호스트 커널과 다릅니다. smoke pod가 실패해도 경고만 내므로 세 줄을 직접 확인하세요.
- **막히면**: [문제 해결: Kata](troubleshooting.md#kata), [문제 해결: 설정과 스크립트](troubleshooting.md#설정과-스크립트), [03 Kata 샌드박스](../handson/03_kata.md)

### `scripts/kata/gpu_nodes.sh`

- **하는 일**: `KATA_IOMMU_AMI_ID`가 비어 있으면 IOMMU를 켠 AMI를 빌드하고 멈춥니다. 값이 있으면 `sandbox-kata-gpu` 노드 그룹을 확인하고 GPU Operator와 kata-deploy를 설치한 뒤 `nvidia.com/pgpu`가 나타나기를 기다립니다.
- **사용법**: `scripts/kata/gpu_nodes.sh`. 첫 실행이 출력한 `KATA_IOMMU_AMI_ID`와 `WITH_KATA_GPU=1`을 `config.env`에 넣고 `02_create_cluster.sh`, 이 스크립트 순으로 다시 실행합니다. 실험용 `kata-clh-nvidia-gpu`는 `ENABLE_EXPERIMENTAL_CLH_GPU=1`로 켭니다.
- **실행 시점**: `kata/cpu_nodes.sh`로 리허설한 뒤, Kata GPU가 필요할 때(전체 경로) 실행합니다. 시나리오에 상관없이 추가할 수 있습니다.
- **시간과 과금**: AMI 약 10분(안내값), pgpu 대기는 최대 20분입니다. AMI 빌더 `m6i.large`(잠시)와 AMI 스냅샷이 과금되고, `g4dn.metal`(시간당 7.824 USD)은 `02_create_cluster.sh`를 다시 실행할 때 시작됩니다.
- **다시 실행할 때**: `KATA_IOMMU_AMI_ID`가 빈 채로 실행할 때마다 AMI를 새로 빌드하고, `08_cleanup.sh`는 `config.env`에 있는 AMI 하나만 지우니 첫 ID를 바로 넣으세요. ID가 있으면 두 Helm release를 `helm upgrade --install`로 다시 적용하며, `ENABLE_EXPERIMENTAL_CLH_GPU=1` 없이 실행하면 kata-deploy의 실험용 값이 빠집니다.
- **성공 여부 확인**: `pgpu=8  cc.ready.state=false`, 이어서 `kata-qemu-nvidia-gpu` RuntimeClass 한 줄이 나옵니다.
- **막히면**: [문제 해결: Kata](troubleshooting.md#kata), [문제 해결: 설정과 스크립트](troubleshooting.md#설정과-스크립트), [03 Kata 샌드박스](../handson/03_kata.md)

## 검증과 운영

### `scripts/ops/verify.sh`

- **하는 일**: pool 하나에 네 가지를 검사합니다. 샌드박스 안과 노드의 커널 비교, 샌드박스 안에서의 연결 차단(instance metadata, Kubernetes API, kubelet, 인터넷), 인증된 API의 golden verdict(probe Job), 다른 네임스페이스에서의 접속 차단입니다.
- **사용법**: `scripts/ops/verify.sh <runtime> [version]` (version 기본 `v1`)
- **실행 시점**: 모든 시나리오에서 `06_deploy_sandboxes.sh`로 pool을 배포한 뒤 실행하세요. `ops/rollout.sh`는 2단계에서 이 검사를 실행합니다.
- **시간과 과금**: 수 분(probe Job 포함). 과금되는 리소스는 없습니다.
- **다시 실행할 때**: 검사만 하므로 안전합니다. 실행할 때마다 probe Job(`probe-<runtime>-<version>-<시각>`, 끝나고 1시간 뒤 삭제)과 `default`의 임시 pod(`--rm`)를 새로 만듭니다.
- **성공 여부 확인**: 마지막 줄이 `pool sandbox-<runtime>-<version> verified`입니다. 1번 커널 비교는 스크립트가 판정하지 않으니 출력된 두 값이 다른지 직접 확인하세요.
- **막히면**: [문제 해결: 샌드박스 pool과 readiness](troubleshooting.md#샌드박스-pool과-readiness), [문제 해결: 401, 403 응답](troubleshooting.md#401-403-응답), [문제 해결: NetworkPolicy](troubleshooting.md#networkpolicy)

### `scripts/ops/rollout.sh`

- **하는 일**: 학습 중에 blue/green으로 샌드박스 버전을 바꿉니다. `<to>` pool 배포, 검증, `<from>`과의 parity 검사, routing 표 전환(`rl-trainer`와, 있으면 `sandbox-gateway`) 순서이고, `--finish`는 `<from>` pool을 0으로 줄입니다.
- **사용법**: `scripts/ops/rollout.sh <runtime> <from> <to> [--finish]`. 예: `scripts/ops/rollout.sh gvisor v1 v2`, 전환을 확인한 뒤 같은 명령에 `--finish`를 붙입니다. rollback은 `<from>`과 `<to>`를 바꿔 실행합니다.
- **실행 시점**: `07_run_grpo.sh`(A), `hyperpod/run_grpo.sh`(B), `ops/simulate.sh`(C)가 실행되는 동안 버전을 전환할 때 호출합니다.
- **시간과 과금**: [06](../handson/06_sandbox_update.md) 참고. gVisor는 v2용 `g5.xlarge` 2대(시간당 2.012 USD, 노드 그룹을 4대로 늘린 동안)가 더 필요하고, Kata QEMU는 추가 노드가 없습니다.
- **다시 실행할 때**: `--finish` 없이 다시 실행하면 1~4단계를 모두 다시 하며, 배포는 `kubectl apply`이고 전환 단계에서는 같은 라우팅 표를 다시 저장합니다. parity가 실패하면 전환하지 않아 `<from>`이 계속 요청을 받습니다. `--finish`는 배포와 전환을 건너뛰고 `<from>`을 0으로 줄이기만 하므로, trainer 로그에서 전환을 확인한 뒤에 실행하세요.
- **성공 여부 확인**: `1) deploying`부터 `4) switching the routing table to <runtime>/<to>`까지 순서대로 나오고 parity 줄이 모두 `PASS`입니다. 그 뒤 trainer(또는 simulate) 로그에 `SWITCH  <runtime>/<from> -> <runtime>/<to>`가, `--finish`에는 `deployment.apps/sandbox-<runtime>-<from> scaled`가 나옵니다.
- **막히면**: [문제 해결: 버전 전환 (routing)](troubleshooting.md#버전-전환-routing), [06 학습 중 샌드박스 업데이트](../handson/06_sandbox_update.md)

### `scripts/ops/simulate.sh`

- **하는 일**: 모델 없이, routing ConfigMap이 가리키는 pool에 golden 제출물을 배치 단위로 보내는 Job을 실행하고 `reward_batch`, `sandbox_version_switch` 이벤트를 보여 줍니다. 학습이 아닙니다.
- **사용법**: `scripts/ops/simulate.sh [steps] [interval_s]` (기본 30배치, 20초)
- **실행 시점**: 시나리오 C에서 pool 배포와 `ops/verify.sh` 다음에 실행하고, 다른 터미널에서 `ops/rollout.sh`로 버전을 전환합니다.
- **시간과 과금**: 기본 30배치에 배치 사이 20초 대기가 29회입니다. 2026-11-17 실행(`kata-clh-cpu`)은 약 16분 걸렸습니다. 과금되는 리소스는 없습니다.
- **다시 실행할 때**: 실행할 때마다 새 Job(`simulate-<시각>`)을 만들고 그 시점의 active pool을 읽습니다. 여러 개를 동시에 실행하면 같은 pool에 요청이 겹칩니다.
- **성공 여부 확인**: 배치마다 `batch <n>  <runtime>/<version>  ...` 줄이 나옵니다. 버전 교체 뒤에는 `SWITCH ...` 한 줄과 `MIXED VERSIONS`가 없는 `batch` 줄이 이어집니다.
- **막히면**: [문제 해결: 버전 전환 (routing)](troubleshooting.md#버전-전환-routing), [10 c8i 단독 저비용 경로](../handson/10_cpu_only.md)

### `scripts/ops/bench.sh`

- **하는 일**: v1 pod가 있는 pool마다 cold start(pod 생성부터 Ready까지)를 출력하고, 같은 golden kernel(GPU는 `relu_bias_triton`, CPU는 `relu_bias_torch_only`)로 지연 p50, p95, 처리량, speedup을 측정합니다. 결과는 `bench-<시각>.jsonl`에 기록합니다.
- **사용법**: `scripts/ops/bench.sh [requests]` (기본 32)
- **실행 시점**: pool을 배포하고 검증한 뒤, 학습이 실행 중이 아닐 때 실행합니다. 모든 시나리오에서 선택 단계입니다.
- **시간과 과금**: 2026-11-18 2차 측정에서 평가 구간은 pool마다 약 100~300 s, 다섯 pool 합계 약 13분이었습니다(Job 생성과 pool 재시작 제외). 새로 과금되는 리소스는 없고, 그동안의 노드 요금이 나갑니다.
- **다시 실행할 때**: 실행할 때마다 새 결과 파일과 pool마다 새 bench Job을 만듭니다. cold start는 지금 있는 pod의 생성 시각으로 계산하므로, pod를 재시작하지 않으면 같은 값이 다시 나옵니다([08](../handson/08_benchmark.md)의 재측정 방법).
- **성공 여부 확인**: pool마다 `bench  <runtime>  ok <n>/<requests>  p50 ...` 한 줄이 나오고, 끝에 `results: <파일>`이 나옵니다.
- **막히면**: [문제 해결: 샌드박스 pool과 readiness](troubleshooting.md#샌드박스-pool과-readiness), [08 런타임 벤치마크](../handson/08_benchmark.md)

EKS 실습에서 다섯 pool에 32건씩 보내 160건 모두 성공했습니다. [결과표와 실행 조건](../handson/08_benchmark.md#runtime-results)

### `scripts/ops/sync_jwks.sh`

- **하는 일**: 클러스터의 ServiceAccount issuer 공개 키(JWKS)와 issuer를 `sandbox` 네임스페이스의 ConfigMap `sandbox-auth-jwks`에 복사합니다. 비밀 값이 아닙니다.
- **사용법**: `scripts/ops/sync_jwks.sh` (인자 없음)
- **실행 시점**: 모든 시나리오에서 `05_setup_namespaces_auth.sh`가 이 스크립트를 호출합니다. API server가 서명 키를 교체하면 따로 실행해 키를 갱신하세요.
- **시간과 과금**: 짧음. 과금되는 리소스는 없습니다.
- **다시 실행할 때**: ConfigMap을 `kubectl apply`로 덮어쓰므로 안전하고, 샌드박스 pod는 바뀐 파일을 다시 읽습니다. 받은 JWKS가 비어 있으면 ConfigMap을 바꾸기 전에 멈춥니다.
- **성공 여부 확인**: `configmap/sandbox-auth-jwks` 적용 결과와 마지막 줄 `issuer: <issuer URL>`이 나옵니다.
- **막히면**: [문제 해결: 401, 403 응답](troubleshooting.md#401-403-응답)

## HyperPod

### 관리형 B2 · CPU와 GPU 워커를 모두 HyperPod에서 운영

| 명령 | 하는 일 |
|---|---|
| `scripts/hyperpod/create_managed.sh` | HyperPod EKS 생성 마법사의 AWS 템플릿으로 제어 영역과 `system`, `trainer`, `sandbox` HyperPod 그룹을 만듭니다. |
| `scripts/hyperpod/reboot_sandboxes.sh` | 채점 노드에 지원 드라이버를 설치하고, 전환이 필요한 노드만 HyperPod API로 재부팅해 실행 버전을 확인합니다. |
| `scripts/hyperpod/prepare_managed.sh` | VPC CNI NetworkPolicy를 켜고 CoreDNS를 `system`에 배치합니다. 학습 오퍼레이터와 인증서 웹훅도 확인합니다. |
| `scripts/hyperpod/bench_b2.sh 32` | `system`과 `trainer`에서 같은 Triton 평가를 차례로 실행하고 요청 위치별로 JSONL 파일을 남깁니다. |

리전 설정, 실행 화면과 정리 순서는 [B2 실습](../handson/07_hyperpod_b2.md)을 보세요. 아래 `create.sh`와 AMI 빌드 명령은 기존 CDK 경로에서 사용합니다.

### `scripts/hyperpod/create.sh`

- **하는 일**: HyperPod dependency Helm chart, lifecycle script 버킷(Block Public Access), execution role을 준비하고 `create-cluster`로 HyperPod 클러스터를 EKS에 연결한 뒤 training operator add-on을 설치합니다. `--b2`는 custom AMI로 부팅하는 `sandbox` 인스턴스 그룹과 `gvisor-hyperpod` RuntimeClass를 더합니다.
- **사용법**: `scripts/hyperpod/create.sh` (B1) 또는 `--b2` (기존 CDK 방식의 B2, `HYPERPOD_B2_AMI_ID` 필요). `git`과 `jq`가 있어야 합니다.
- **실행 시점**: B1은 `02_create_cluster.sh --hyperpod`, `HYPERPOD=1 03_build_push_images.sh`, `04_install_gpu_stack.sh` 다음에 실행합니다. 기존 CDK 방식의 B2에서는 `hyperpod/build_b2_ami.sh` 다음에 실행합니다.
- **시간과 과금**: InService까지 15~30분(안내값). HyperPod `ml.g5.2xlarge`(시간당 1.515 USD)의 과금이 시작되고, B2는 `ml.g5.xlarge` x2가 더해집니다.
- **다시 실행할 때**: 1, 2단계(Helm chart, Block Public Access, lifecycle 업로드)는 다시 적용되고, 버킷과 역할은 없을 때만 만듭니다. 4단계 `create-cluster`는 같은 이름의 클러스터가 있으면 실패할 것으로 보며(추론), 5단계 add-on 생성도 이미 있으면 실패하니 5단계만 실패했다면 [07](../handson/07_hyperpod.md)에 있는 두 명령만 실행하세요.
- **성공 여부 확인**: `status`가 `InService`이고 `failure`가 비어 있으며, 마지막 노드 표에 HyperPod 노드가 보입니다(B2는 `ml.g5.xlarge` 두 대가 `Schedulable`).
- **막히면**: [문제 해결: HyperPod](troubleshooting.md#hyperpod), [07 HyperPod 시나리오](../handson/07_hyperpod.md)

### `scripts/hyperpod/build_b2_ami.sh`

- **하는 일**: HyperPod EKS base AMI를 `m6i.large` 빌더로 띄워 NVIDIA 드라이버를 `B2_NVIDIA_DRIVER_VERSION`(580.178.04)으로 바꾸고 gVisor를 넣은 custom AMI를 만듭니다. 빌더 전용 security group(outbound HTTPS만)은 빌더와 함께 지웁니다.
- **사용법**: `scripts/hyperpod/build_b2_ami.sh` (인자 없음). base AMI는 `HYPERPOD_BASE_AMI_ID`로 직접 지정할 수 있습니다.
- **실행 시점**: 기존 CDK 방식의 B2에서 `02_create_cluster.sh --hyperpod-b2` 다음, `hyperpod/create.sh --b2` 전에 실행합니다.
- **시간과 과금**: 20~40분(추정). 빌드 중의 `m6i.large`와 그 뒤의 AMI 스냅샷이 과금됩니다.
- **다시 실행할 때**: 기존 `HYPERPOD_B2_AMI_ID`를 확인하지 않고 실행할 때마다 새 AMI를 만들며, `08_cleanup.sh`는 `config.env`에 있는 AMI 하나만 지우니 이전 AMI와 스냅샷은 직접 지우세요. 빌드가 실패하면 정지된 빌더가 남으므로(EBS 요금) 출력된 명령으로 정리한 뒤 다시 실행합니다.
- **성공 여부 확인**: `GPUSANDBOX-B2-BUILD: OK ...` 로그 뒤에 `export HYPERPOD_B2_AMI_ID="ami-..."`가 나옵니다.
- **막히면**: [문제 해결: HyperPod](troubleshooting.md#hyperpod), [07 HyperPod 시나리오의 B2](../handson/07_hyperpod.md#b2)

### `scripts/hyperpod/check_gvisor.sh`

- **하는 일**: CPU 시스템 그룹을 제외한 HyperPod 워커에서 NVIDIA 드라이버의 gVisor 지원 여부를 확인합니다. 검사할 때마다 임시 네임스페이스를 만들고 검사가 끝나면 지웁니다.
- **사용법**: `scripts/hyperpod/check_gvisor.sh` (인자 없음)
- **실행 시점**: pool을 배포하기 전에 드라이버를 확인할 때 실행합니다. 관리형 B2에서는 채점 노드를 재부팅한 뒤, 기존 CDK 방식에서는 `hyperpod/create.sh --b2` 다음에 확인하세요.
- **시간과 과금**: 소요 시간은 기록하지 않았습니다. 워커에 지정한 버전의 gVisor가 없으면 스크립트가 내려받습니다. 과금되는 리소스는 없습니다.
- **성공 여부 확인**: sandbox 노드 두 대에서 `driver 580.178.04: SUPPORTED by gVisor ...`이 나옵니다. trainer에서 `NOT supported`가 나와도 학습에는 문제가 없습니다. 예를 들어 595.91.07 드라이버는 이 gVisor 릴리스에서 지원하지 않습니다.
- **막히면**: [문제 해결: HyperPod](troubleshooting.md#hyperpod), [07 HyperPod 시나리오의 B2](../handson/07_hyperpod.md#b2)

### `scripts/hyperpod/run_grpo.sh` { #scriptshyperpodrun_grposh }

B1과 B2에서 **HyperPod trainer에 GRPO Job을 제출**합니다. 기존 샌드박스 pool은 모델이 생성한 코드를 채점하고, trainer는 그 점수로 모델을 업데이트합니다.

**준비**　[HyperPod 실습](../handson/07_hyperpod.md)에서 training operator, trainer 노드, 샌드박스 pool을 준비하세요. `HYPERPOD=1 scripts/03_build_push_images.sh`로 빌드한 이미지에는 Job의 실행 명령인 `hyperpodrun`이 들어 있습니다. `scripts/config.env`에 `TRAINER_IMAGE_URI`, `SANDBOX_AUDIENCE`, `HYPERPOD_TRAINER_INSTANCE_TYPE`이 필요합니다.

```bash
scripts/hyperpod/run_grpo.sh 5
```

`5`는 optimizer step 수입니다. 생략하면 60이고 기본 모델은 `Qwen/Qwen2.5-Coder-1.5B-Instruct`입니다. 스크립트는 설정을 `k8s/trainer/hyperpod-job-grpo.yaml.tpl`에 넣어 `rl-trainer`에 `grpo-<RUN_ID>`라는 `HyperPodPyTorchJob`을 제출합니다. operator가 스케줄 가능한 trainer 노드에 GPU 한 장을 요청하는 pod를 띄우고, 컨테이너는 라우팅 ConfigMap과 인증 토큰을 읽어 샌드박스 pool에 연결합니다.

| 확인할 것 | 출력으로 알 수 있는 것 |
|---|---|
| `HyperPodPyTorchJob grpo-<RUN_ID> submitted` | API가 Job을 받았습니다. pod 상태는 별도로 확인하세요. |
| `routing` 이벤트 | trainer가 샌드박스 경로를 읽었습니다. 템플릿은 시작 후 20분 안에 이 이벤트를 기대합니다. |
| `reward_batch` 이벤트와 학습 step | 샌드박스 평가 요청이 처리되고 학습이 진행되는지 확인할 수 있습니다. `sandbox_error`가 반복되면 pool을 점검하세요. |

B1 trainer가 GRPO 한 스텝을 완료했고, EC2 gVisor 샌드박스 두 개가 제출 코드 12개를 채점했습니다. [Job 상태와 학습 로그](../handson/07_hyperpod.md#확인-방법)

스크립트가 출력한 Job 이름을 `HPJob` 라벨 값에 넣으면 이번 실행의 pod를 찾을 수 있습니다.

```bash
kubectl -n rl-trainer get pods -l 'HPJob=grpo-<RUN_ID>' -o wide
kubectl -n rl-trainer logs -f <trainer-pod> -c pytorch
```

`RUN_ID`를 지정하지 않으면 실행 시각을 사용합니다. 새 ID로 실행하면 Job이 추가되므로 기존 Job이 GPU를 쓰는 동안 새 pod는 대기할 수 있습니다. `/outputs`는 pod의 `emptyDir`입니다. pod가 교체되면 여기에 저장한 체크포인트도 사라집니다.

Job 종류를 찾을 수 없으면 [HyperPod operator 설정](troubleshooting.md#hyperpod)을, pod는 실행되는데 평가 로그가 나오지 않으면 [학습 문제 해결](troubleshooting.md#학습)을 확인하세요.

### `scripts/hyperpod/delete.sh`

- **하는 일**: HyperPod 클러스터 이름을 입력받은 뒤 HyperPodPyTorchJob, HyperPod 클러스터(사라질 때까지 대기), execution role을 지우고, 한 번 더 확인한 뒤 lifecycle 버킷을 비우고 지웁니다. EKS 클러스터는 남습니다.
- **사용법**: `scripts/hyperpod/delete.sh` (인자 없음)
- **실행 시점**: B1과 기존 CDK 방식의 B2를 정리할 때 `08_cleanup.sh`보다 먼저 실행합니다. 관리형 B2는 [마법사 스택 정리 절차](../handson/07_hyperpod_b2.md#cleanup)를 따르세요.
- **시간과 과금**: 문서에 기록 없음([07](../handson/07_hyperpod.md) 참고). HyperPod 리소스의 과금이 끝납니다.
- **다시 실행할 때**: HyperPod 클러스터가 이미 없으면 `delete-cluster`가 실패해 역할과 버킷을 삭제하기 전에 멈춥니다. 첫 실행을 버킷 확인에서 멈췄다면 남은 버킷은 직접 지우세요.
- **성공 여부 확인**: `waiting for the cluster to disappear`, `deleted role <이름>-execution` 뒤에 마지막 줄 `HyperPod resources deleted`가 나옵니다.
- **막히면**: [문제 해결: 정리와 비용](troubleshooting.md#정리와-비용), [99 정리](../handson/99_cleanup.md)

## 확장

### `scripts/extensions/agent_sandbox.sh`

- **하는 일**: Agent Sandbox의 warm pool에서 에피소드마다 샌드박스를 하나씩 빌려 씁니다. `install`은 controller와 CRD(기본 v1.0.11), claim RBAC를, `pool`은 SandboxTemplate과 SandboxWarmPool을 만들고, `claim`은 샌드박스 하나를 빌려 주소를 출력한 뒤 돌려주며, `episodes`는 모델 없이 multi-turn 에피소드를 실행하는 Job을 만듭니다.
- **사용법**: `scripts/extensions/agent_sandbox.sh install`, `pool <runtime> [n]` (기본 1, 버전 파일은 `VERSION_FILE`, 기본 `v1`), `claim <runtime>`, `episodes <runtime> [episodes] [max_turns]` (기본 2와 3, `max_turns` 1은 single-turn). 버전은 `AGENT_SANDBOX_VERSION`으로 바꿉니다.
- **실행 시점**: 어느 시나리오에서든 pool을 검증한 뒤 선택해서 진행할 수 있습니다. 실습 기록은 시나리오 C의 `kata-clh-cpu`에서 얻었습니다([11](../handson/11_multi_turn.md)).
- **시간과 과금**: 시나리오 C의 `kata-clh-cpu`에서 에피소드 두 개를 각각 3턴씩 실행하는 데 약 25초 걸렸습니다. 새 노드는 없지만 대기 중인 warm sandbox도 가속기를 하나씩 점유합니다.
- **다시 실행할 때**: `install`은 `kubectl apply`라 안전합니다. `pool`은 템플릿을 다시 적용하지만 이미 떠 있는 warm sandbox는 시작할 때의 env를 유지하고(`OnReplenish`), 인자를 생략하면 replica 1과 `v1`로 다시 써집니다. `claim`과 `episodes`는 실행할 때마다 새 claim과 새 Job(`episodes-<시각>`)을 만들고, 쓴 샌드박스는 돌려주며 지워집니다.
- **성공 여부 확인**: `install`은 CRD 4개, `pool`은 `warm pool kernel-eval-<runtime>: <n> sandbox(es); ...` 로그, `claim`은 `sandbox: ...  address: ...`, `episodes`는 `summary  solved <n>/<n> ...` 줄과 종료 코드 0입니다.
- **막히면**: [문제 해결: Agent Sandbox와 multi-turn 에피소드](troubleshooting.md#agent-sandbox와-multi-turn-에피소드), [11 multi-turn 에피소드 실습](../handson/11_multi_turn.md)

## 데모 사이트

### `demo/deploy.sh`

- **하는 일**: 녹화 기록(`recording.json`과, 있으면 `extras.json`)에 IP, 노드 이름, 계정 ID, ARN, 토큰이 없는지 검사한 뒤 us-east-1에 private S3, CloudFront, WAF 스택을 배포하고 정적 사이트를 올립니다. 끝으로 WAF 연결, S3 직접 접근 403, CSP와 HSTS 헤더, `http://` 요청의 301 리다이렉트를 확인합니다.
- **사용법**: `demo/deploy.sh`. 다른 기록은 `RECORDING=<파일>`, `EXTRAS=<파일>`로, 스택 이름은 `DEMO_STACK_NAME`으로, custom domain은 `DEMO_DOMAIN`과 `DEMO_CERT_ARN`으로 지정합니다.
- **실행 시점**: 클러스터와 독립된 선택 단계입니다. 저장소에 있는 녹화 기록으로 바로 배포할 수 있습니다.
- **시간과 과금**: 대부분 스택 생성과 CloudFront 전파를 기다리는 시간이고, 200 응답 대기는 최대 약 10분입니다(실제 시간은 측정하지 않음). S3, CloudFront 요청과 전송, AWS WAF(방문자가 없어도 월 약 10 USD)가 과금됩니다.
- **다시 실행할 때**: 스택은 `aws cloudformation deploy`(바뀐 것이 없어도 실패하지 않음)로, 파일은 덮어쓰기와 `s3 sync --delete`로 다시 올리고 invalidation을 새로 만듭니다. `EXTRAS` 파일 없이 실행하면 이전에 올린 `data/extras.json`은 S3에 그대로 남습니다.
- **성공 여부 확인**: 마지막 줄이 `[demo] live: <URL>`입니다. 200 응답이 오지 않아도 헤더 검사로 넘어가므로 URL을 브라우저로 직접 열어 보세요.
- **막히면**: [09 데모 사이트 (CloudFront)](../handson/09_demo_site.md)

### `demo/teardown.sh`

- **하는 일**: 스택 이름을 입력받은 뒤 사이트 버킷을 비우고 데모 스택을 지웁니다. access log 버킷은 `DeletionPolicy Retain`이라 남깁니다.
- **사용법**: `demo/teardown.sh` (다른 스택 이름은 `DEMO_STACK_NAME`)
- **실행 시점**: 데모 사이트를 내릴 때 실행합니다.
- **시간과 과금**: 기록 없음(스택 삭제를 기다림). S3, CloudFront, WAF의 과금이 끝나고, 로그 버킷은 지울 때까지 남습니다(로그 객체는 90일 뒤 만료).
- **다시 실행할 때**: 스택이 이미 없으면 출력값 조회가 실패해 아무것도 지우지 않고 멈춥니다. 남은 로그 버킷은 첫 실행이 안내한 `aws s3 rb s3://<로그 버킷> --force`로 지웁니다.
- **성공 여부 확인**: `deleted gpu-sandbox-demo` 다음에 `kept the access log bucket <로그 버킷>; ...`이 나옵니다.
- **막히면**: [99 정리](../handson/99_cleanup.md), [09 데모 사이트 (CloudFront)](../handson/09_demo_site.md)

## 공통 파일

### `scripts/logview.py`

- **하는 일**: 표준 입력으로 받은 JSON 이벤트(`reward_batch`, `sandbox_version_switch`, parity, 에피소드, bench, trainer 지표)를 터미널에서 색을 입힌 한 줄 요약으로 바꿉니다. pod 로그와 metrics 파일은 바꾸지 않습니다.
- **사용법**: `... | python3 scripts/logview.py`. `GPUSANDBOX_LOG=json`이면 원본 JSON을 그대로 보여 주고, `NO_COLOR`가 있으면 색을 끕니다. 출력이 파이프나 파일이면 받은 줄을 바꾸지 않고 넘깁니다.
- **실행 시점**: `07_run_grpo.sh`와 `lib_jobs.sh`를 쓰는 스크립트(`ops/verify.sh`, `ops/rollout.sh`, `ops/simulate.sh`, `ops/bench.sh`, `agent_sandbox.sh episodes`)가 로그를 출력할 때 자동으로 호출합니다.
- **다시 실행할 때**: 상태를 저장하지 않는 필터라 언제든 다시 실행할 수 있습니다.
- **성공 여부 확인**: `batch`, `SWITCH`, `PARITY PASS`, `bench` 같은 요약 줄이 나옵니다. JSON이 아닌 줄은 그대로 나오고 PASS, FAIL, 오류에만 색이 붙습니다.
- **막히면**: [00 핸즈온 전체 흐름](../handson/00_overview.md)의 "확인 방법"

### `scripts/lib.sh`, `scripts/lib_jobs.sh`

- **하는 일**: `lib.sh`는 모든 스크립트가 처음에 읽는 공통 부분(`set -euo pipefail`, `scripts/config.env` 읽기, `log`, `die`, `require_vars`, `require_tools`, `render`, `confirm`)입니다. `lib_jobs.sh`는 `gpusandbox.tools`를 클러스터 안의 일회성 Job으로 실행하고 로그를 보여 주는 `run_tool_job`, `run_job_template`을 제공합니다.
- **사용법**: 직접 실행하지 않고 다른 스크립트가 `source`로 읽습니다.
- **실행 시점**: `demo/`를 뺀 모든 스크립트가 `lib.sh`를 읽고, `lib_jobs.sh`는 `ops/verify.sh`, `ops/rollout.sh`, `ops/simulate.sh`, `ops/bench.sh`, `agent_sandbox.sh`가 불러옵니다.
- **다시 실행할 때**: 스크립트를 실행할 때마다 `config.env`를 다시 읽으며, 거기서 `export`한 값은 명령 앞에 붙인 같은 이름의 값을 덮어씁니다(예: `IMAGE_TAG`, `WITH_KATA_CPU`). Job 이름에 실행 시각(초)을 붙이므로 실행할 때마다 새 Job이 생기고, 끝난 Job은 1시간 뒤 지워집니다.
- **성공 여부 확인**: Job이 성공했을 때만 0을 반환합니다. pod가 10분 안에 시작하지 않으면 `job <이름> did not start` 경고와 함께 실패합니다.
- **막히면**: [문제 해결: 설정과 스크립트](troubleshooting.md#설정과-스크립트)
