# 시나리오 A · EC2에서 GPU 학습과 채점하기

[시나리오 선택으로 돌아가기](00_overview.md)

한 EKS 클러스터에서 시스템 pod는 `m6i.large` 두 대, 모델 학습은 `g5.2xlarge` 한 대, GPU 채점은 `g5.xlarge` 두 대가 맡습니다. 학습 노드의 trainer가 코드를 만들면 채점 노드의 gVisor 샌드박스가 실행해 판정을 돌려줍니다. 처음이라면 5스텝 학습으로 이 흐름을 확인하세요. 학습 중 채점 버전까지 바꿔 보고 싶다면 5단계에서 60스텝 경로를 고르세요.

## 1. 실습 계정과 GPU 쿼터 확인 { #prepare }

[시작하기](../getting_started.md)에 따라 AWS CLI, CDK CLI, Session Manager plugin, Docker buildx, Helm, kubectl, jq, uv와 Python 가상 환경을 준비하세요. 이후 명령은 AWS 인증을 마친 작업 PC의 `gpu-sandbox-on-aws` 폴더에서 실행합니다.

```bash
test -f scripts/config.env || cp scripts/config.env.example scripts/config.env
source .venv/bin/activate
uv pip install -r cdk/requirements.txt
aws sts get-caller-identity
```

`scripts/config.env`에서 `AWS_REGION`(기본 `us-west-2`), `CLUSTER_NAME`, `SCENARIO="A"`를 확인하세요. 아래 구성은 `WITH_KATA_CPU="0"`, `WITH_KATA_GPU="0"`, `GVISOR_NODES="2"`를 기준으로 합니다. IAM Identity Center 등 경로가 있는 역할로 배포한다면 `ADMIN_PRINCIPAL_ARN`에 IAM 역할 전체 ARN을 지정하세요. [계정·도구 설정](01_cluster_and_images.md)

```bash
source scripts/config.env
scripts/01_check_prereqs.sh
cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"
```

**다음 단계로 가려면** 선택한 계정·리전에서 CDK bootstrap이 성공해야 합니다. 기본 구성에 필요한 여유분은 EC2 온디맨드 Standard 6 vCPU, G/VT 16 vCPU입니다. 버전을 전환하려면 G/VT 24 vCPU가 필요합니다. 이미 사용 중인 vCPU도 고려하세요.

## 2. 클러스터를 만들고 접속 { #cluster }

```bash
scripts/02_create_cluster.sh
```

배포가 끝나고 CDK 출력에 `ClusterEndpoint`와 `AccessInstanceId`가 보이면, **별도 터미널**에서 같은 프로젝트 폴더의 `cdk/tunnel.sh`를 실행하고 열어 두세요. SSM 터널을 통해 private EKS API에 접속합니다. 이후 명령은 원래 작업 터미널에서 실행하세요.

```bash
kubectl config current-context
kubectl get nodes -L gpusandbox/role,node.kubernetes.io/instance-type
```

컨텍스트는 `<CLUSTER_NAME>-tunnel`이어야 합니다. `Ready` 노드 목록에서 `system` 두 대, `trainer` 한 대, `sandbox-gvisor` 두 대를 확인하세요. 기본 구성의 컴퓨트 비용은 시간당 약 3.42 USD이며 EKS, NAT 등은 별도입니다. [배포 오류와 비용](01_cluster_and_images.md)

## 3. 이미지를 올리고 샌드박스에서 GPU 확인 { #gpu }

```bash
scripts/03_build_push_images.sh
```

마지막에 출력된 `export SANDBOX_IMAGE_URI=…`, `export TRAINER_IMAGE_URI=…`, `export CONTROL_IMAGE_URI=…` **세 줄의 실제 값**을 `scripts/config.env`에 저장하세요. **채점 pool을 배포하기 전**에 다음 GPU 검사를 실행합니다. 검사 pod가 사용할 GPU 한 장이 비어 있어야 합니다.

```bash
scripts/04_install_gpu_stack.sh
```

시험용 pod의 로그에서 `Starting gVisor...`를 찾아 gVisor가 시작됐는지 확인하세요. `cuda ok: NVIDIA A10G 2048.0`은 A10G에서 CUDA 연산을 마치고 기대한 합 2048을 얻었다는 뜻입니다. 스크립트가 경고와 함께 끝났다면 두 줄이 모두 있는지 확인하세요. [gVisor GPU 검사](02_gvisor.md)

## 4. v1 채점 pool 만들기 { #pool }

```bash
scripts/05_setup_namespaces_auth.sh
scripts/06_deploy_sandboxes.sh gvisor v1
scripts/ops/verify.sh gvisor v1
```

두 `sandbox-gvisor-v1` pod가 `1/1` Ready인지 확인하세요. `verify.sh`의 첫 검사에서 `sandbox:`에 나온 gVisor 커널 버전과 `node:`의 호스트 커널 버전이 다른지 직접 비교하세요. 이 단계는 두 값만 출력합니다. 외부 연결 차단과 시험 답안 판정 등 자동 검사를 통과하면 마지막 줄에 `pool sandbox-gvisor-v1 verified`가 나옵니다. [검사 결과 읽기](04_sandbox_pools.md)

**선택 · 벤치마크.** 시간을 재려면 다음 학습을 시작하기 전에 `scripts/ops/bench.sh 32`를 실행하세요. 이 스크립트는 v1 pool을 대상으로 합니다. `gvisor`에서 32건 중 몇 건이 성공했는지, 채점 시간의 p50·p95와 초당 처리 건수가 얼마인지 확인하세요. 결과는 마지막에 출력되는 `bench-*.jsonl`에 남습니다. [벤치마크 결과와 측정 조건](08_benchmark.md#runtime-results)

## 5. 학습 시작하기 { #train }

다음 두 경로 중 하나를 선택하세요. 학습 명령은 로그를 계속 표시합니다. `routing`에서 `gvisor/v1`을, 이어지는 `batch`에서 채점 결과를, `train`에서 모델 업데이트를 확인하세요. Job 이름 `grpo-…`도 기록해 두세요. [학습 로그 읽기](05_grpo_training.md)

=== "5스텝 · 학습만 확인"

    ```bash
    scripts/07_run_grpo.sh 5
    ```

    `done`을 확인하면 [7. 종료 확인과 정리](#cleanup)로 넘어가세요.

=== "60스텝 · 학습 중 버전 전환"

    v1이 채점하는 동안 v2도 실행해야 하므로 **학습을 시작하기 전에** `sandbox-gvisor` 노드를 네 대로 늘리세요. 기본 구성보다 `g5.xlarge` 두 대분의 비용이 추가됩니다(시간당 약 2.012 USD).

    ```bash
    source scripts/config.env
    aws eks update-nodegroup-config --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
      --nodegroup-name sandbox-gvisor --scaling-config minSize=0,maxSize=4,desiredSize=4
    kubectl get nodes -l gpusandbox/role=sandbox-gvisor
    ```

    목록을 다시 조회해 `Ready` 네 대를 확인한 뒤 실행하세요.

    ```bash
    scripts/07_run_grpo.sh
    ```

    trainer가 v1에서 첫 batch를 채점하면 학습 로그를 열어 둔 채 다른 작업 터미널에서 6단계로 넘어가세요. SSM 터널도 계속 열어 둡니다.

## 6. 선택 · 실행 중인 학습을 v2로 전환 { #switch }

```bash
scripts/ops/rollout.sh gvisor v1 v2
```

스크립트가 v2를 배포·검증하고 두 버전의 시험 답안을 비교합니다. `PARITY PASS` 뒤에 routing 설정이 바뀝니다. 학습 터미널에서 `SWITCH`(원래 JSON 이벤트는 `sandbox_version_switch`)가 나오고, **그 뒤 v2 배치에서 `sandbox_error` 이외의 판정**이 나올 때까지 기다리세요. 배치 전체가 한 pool의 캐시에 적중하면 새 `reward_batch` 로그가 나오지 않습니다.

v2 판정을 확인한 경우에만 아래 명령으로 v1 pod 수를 0으로 줄이세요. parity 검증이 실패하면 v1이 계속 채점합니다. routing을 바꾼 뒤 v2에서 오류만 나온다면 v1을 남겨 둔 채 [롤백 절차](06_sandbox_update.md)를 따르세요. 학습이 먼저 끝나면 그 실행에서 전환을 확인한 것으로 기록하지 않습니다.

```bash
scripts/ops/rollout.sh gvisor v1 v2 --finish
```

학습을 마칠 때까지 노드는 네 대로 유지하세요. 도중에 노드 그룹을 줄이면 v2 pod가 있는 노드가 종료될 수 있습니다. [실제로 버전이 바뀐 배치](06_sandbox_update.md#switch-batches)

## 7. 종료 확인과 정리 { #cleanup }

```bash
kubectl -n rl-trainer get jobs
aws sts get-caller-identity
kubectl config current-context
```

5단계에서 기록한 Job이 `Complete`인지 확인하세요. 정리 전에는 계정과 컨텍스트가 삭제하려는 실습 환경인지 확인합니다. 해당 클러스터를 더 사용하지 않으면 터널을 열어 둔 채 실행하세요.

```bash
scripts/08_cleanup.sh
```

프롬프트에서 클러스터 이름을 확인해 입력하세요. ECR 이미지와 리포지토리까지 지우려면 위 명령 대신 `scripts/08_cleanup.sh --images`로 실행합니다. 마지막 인스턴스 표가 비고 EKS 클러스터와 CDK 스택이 사라졌는지 [99 정리](99_cleanup.md)에서 확인한 뒤 터널을 닫으세요.
