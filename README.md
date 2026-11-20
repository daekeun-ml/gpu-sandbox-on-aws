**한국어** | [English](README.en.md)

# GPU Sandbox on AWS

> [!NOTE]
> **TL;DR** 모델이 작성한 GPU 커널을 격리된 GPU 샌드박스에서 채점하고, 그 점수를 reward로 삼아 on-policy RL post-training을 진행합니다. 이 환경을 Amazon EKS(EC2 자체 운영)와 SageMaker HyperPod에서 gVisor, Kata + QEMU, Kata + Cloud Hypervisor로 구축하는 코드와 가이드북입니다.

**가이드북:** https://daekeun-ml.github.io/gpu-sandbox-on-aws/ (English: https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/)

처음이라면 [학습 코스 고르기](https://daekeun-ml.github.io/gpu-sandbox-on-aws/learning_paths/)에서 목적과 예산에 맞는 코스를 고르세요(무료인 읽기, 로컬 실행 코스가 먼저).

**바로 가기:** [아키텍처](#아키텍처) | [시나리오와 런타임](#시나리오와-런타임) | [시작하기](#시작하기) | [가이드북의 주요 페이지](#가이드북의-주요-페이지) | [문제 해결](TROUBLESHOOTING.md)

## 아키텍처

![만드는 것: 학습 노드의 policy 모델과 vLLM이 버전을 고정한 채 gVisor, Kata + QEMU, Kata + Cloud Hypervisor(CPU 계층) 중 선택한 샌드박스 풀에 커널 코드를 보내고, 정확성과 speedup을 reward로 받는 구성](docs/images/figures/index--what-we-build.ko.svg)

*그림 요약: policy 모델이 쓴 커널 코드는 group 단위로 버전을 고정한 상태로 선택한 런타임의 샌드박스 풀에 전달되고, 풀이 측정한 정확성과 speedup이 reward로 쓰입니다. GPU 채점은 gVisor와 Kata + QEMU 풀이 맡고, Kata + Cloud Hypervisor는 기본적으로 CPU에서 실행합니다.*

네 시나리오는 같은 CDK 스택(private EKS API, SSM 터널, KMS 키, 로그)을 씁니다. A, B1, B2는 trainer와 샌드박스가 배치되는 위치가 다르고, C는 trainer와 모델 없이 CPU 샌드박스에서 채점과 버전 교체를 실습합니다.

### 시나리오 A: EC2 GPU (기본)

![시나리오 A: SSM 터널로 private EKS API에 접속하고, g5.2xlarge의 trainer가 g5.xlarge 두 대의 gVisor 풀에 커널 코드를 보내는 구성](docs/images/architecture/scenario-a.drawio.png)

*그림 요약: trainer와 gVisor 풀이 모두 EKS의 EC2 노드에 있고, 모델은 NAT를 거쳐 Hugging Face Hub에서 받습니다.*

<details>
<summary><b>시나리오 B1: HyperPod 학습</b></summary>

![시나리오 B1: trainer는 HyperPod 인스턴스 그룹에, gVisor 풀은 EC2 노드에 있는 구성](docs/images/architecture/scenario-b1.drawio.png)

*그림 요약: trainer만 HyperPod 인스턴스 그룹(ml.g5.2xlarge)으로 옮겨 S3의 lifecycle 스크립트로 부팅하고, 샌드박스는 A와 같은 EC2 gVisor 노드에 남습니다.*

</details>

<details>
<summary><b>시나리오 B2: HyperPod 학습과 샌드박스</b></summary>

![시나리오 B2: trainer와 gVisor 풀이 모두 HyperPod 인스턴스 그룹에 있고, 샌드박스 노드는 custom AMI로 부팅하는 구성](docs/images/architecture/scenario-b2.drawio.png)

*그림 요약: 샌드박스도 HyperPod 인스턴스 그룹(ml.g5.xlarge x2)에 올라가고, 이 노드는 한 번 빌드하는 custom AMI(드라이버 580.178.04)로 부팅합니다. AWS에서 실행해 보지 않은 실험 경로입니다.*

</details>

<details>
<summary><b>시나리오 C: CPU 전용</b></summary>

![시나리오 C: GPU 없이 c8i.2xlarge 한 대에 세 런타임의 CPU 풀이 있는 구성](docs/images/architecture/scenario-c.drawio.png)

*그림 요약: GPU 노드 없이 c8i.2xlarge 한 대에 세 런타임의 풀이 서고, system 노드의 simulate Job이 trainer 대신 golden 코드를 보냅니다.*

</details>

### 요청 경로

- trainer는 샌드박스에 요청을 보낼 때마다 routing ConfigMap(`sandbox-routing`)의 snapshot으로 런타임과 버전을 정하고, 한 reward batch의 결과는 한 풀에서 받습니다.
    - **학습 중에 v2로 바꾸면**: batch에 새로 채점할 답안이 있으면, 같은 batch에 든 이전 풀의 캐시 결과도 v2 풀에서 다시 채점합니다.
    - **batch 전체가 한 풀의 캐시로 채워지면**: 전환 뒤에도 샌드박스를 부르지 않고 그 결과를 씁니다.
    - **한 batch 안에서 전환이 거듭되면**: 세 번째 요청에서 batch 전체를 한 풀에 보내므로, 한 batch는 항상 한 버전으로 채점됩니다.
- trainer는 headless Service를 CoreDNS로 풀어 Ready 상태인 pod에 `POST /v1/evaluate`를 직접 보냅니다. 바쁜 pod는 `503`을 돌려주고, trainer는 다른 pod로 다시 시도합니다.
- 요청에는 audience가 `gpu-sandbox`인 projected ServiceAccount 토큰이 붙고, pod는 JWKS로 토큰을 오프라인 검증합니다. `sandbox` 네임스페이스는 default-deny라서 `rl-trainer`에서 label이 붙은 pod만 접속할 수 있습니다.

Production 구성(Karpenter NodePool, sandbox gateway, veRL on KubeRay)은 [Production 00 아키텍처](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/00_architecture/)에, 노드 그룹과 네임스페이스, 화살표별 설명은 [핸즈온 00 전체 흐름](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/00_overview/)에 있습니다. 그림 원본(`.drawio`)은 [`diagrams/`](diagrams/)에서 볼 수 있습니다.

## 시나리오와 런타임

| 시나리오 | 학습 위치 | 샌드박스 위치 | 언제 |
|---|---|---|---|
| A. EC2 자체 운영 (기본) | EKS의 EC2 GPU 노드 (`g5.2xlarge`) | 같은 클러스터의 EC2 노드 | 모든 구성 요소를 직접 제어하고 싶을 때 |
| B1. HyperPod (HyperPod 기본) | HyperPod 인스턴스 그룹 (`ml.g5.2xlarge`) | HyperPod가 붙은 같은 EKS 클러스터의 EC2 노드 | 장시간 학습에 HyperPod의 노드 자동 교체와 job 재시작이 필요할 때 |
| B2. HyperPod (실험) | HyperPod 인스턴스 그룹 | 드라이버를 바꾼 custom AMI로 만든 HyperPod 인스턴스 그룹 위 gVisor | 샌드박스 노드에도 HyperPod 노드 복구가 필요할 때 (custom AMI를 직접 관리, AWS에서 미실행) |
| C. c8i 단독 (GPU 없음) | 없음 (모델 없는 reward 루프) | `c8i.2xlarge` 한 대의 CPU 샌드박스 (gVisor, Kata + CLH, Kata + QEMU) | GPU 쿼터 없이, 컴퓨트 시간당 약 0.57 USD로 런타임 비교와 버전 교체를 먼저 익히고 싶을 때 ([핸즈온 10](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/10_cpu_only/)) |

| 런타임 (RuntimeClass) | 격리 경계 | GPU 경로 | 노드 | 상태 |
|---|---|---|---|---|
| gVisor (`gvisor`) | 사용자 공간 커널(Sentry) | nvproxy가 드라이버 버전별 ioctl allowlist로 호스트 드라이버에 전달 | `g5.xlarge` (A10G) | 기본 GPU 경로. VM 경계보다 약함 |
| Kata + QEMU (`kata-qemu-nvidia-gpu`) | VM (KVM) | VFIO GPU passthrough, guest 드라이버 | `g4dn.metal` (T4 8개, VM마다 1개) | upstream이 지원하는 Kata GPU 경로. T4는 upstream CI 범위 밖 |
| Kata + Cloud Hypervisor (`kata-clh`) | VM (KVM) | 없음 (CPU 계층) | `c8i.2xlarge` (nested virtualization) | CPU 샌드박스. GPU(`kata-clh-nvidia-gpu`)는 upstream 미지원, 실험용 |
| Kata + QEMU CPU (`kata-qemu`) | VM (KVM) | 없음 | `c8i.2xlarge` | CPU 샌드박스 |

샌드박스 이미지와 서버는 하나이고, 런타임 프로필(`k8s/sandbox/profiles/`)이 `RuntimeClass`와 노드 선택 조건, GPU 요청을 함께 정합니다. 선택 기준은 가이드북의 [05 상황별 선택 가이드](https://daekeun-ml.github.io/gpu-sandbox-on-aws/concepts/05_decision_guide/)에 있습니다.

## 시작하기

로컬 테스트(AWS 비용 없음)부터 스크립트 순서대로 진행합니다. 단계별 설명과 확인할 것은 가이드북의 [시작하기](https://daekeun-ml.github.io/gpu-sandbox-on-aws/getting_started/)에 있습니다.

### 1. 로컬 테스트부터 (AWS 비용 없음)

CPU 전용 PyTorch와 개발 의존성을 설치하고 로컬 테스트 전체를 실행합니다(AWS 계정과 GPU 불필요).

```bash
git clone https://github.com/daekeun-ml/gpu-sandbox-on-aws.git
cd gpu-sandbox-on-aws
uv venv --python 3.14
source .venv/bin/activate
# Linux: CPU-only wheels, as in .github/workflows/tests.yml
uv pip install --index-url https://download.pytorch.org/whl/cpu torch numpy
# macOS: the default PyPI wheels have no CUDA, so this is enough instead
# uv pip install torch numpy
uv pip install -e ".[dev]"
python -m pytest -q
```

**확인할 것:** 마지막 줄에 실패 없이 `109 passed`가 나옵니다.

- **테스트 범위**: AST 정책, 2-프로세스 harness, 토큰 인증, readiness, 클라이언트와 gateway, 매니페스트와 노드 user data 렌더링을 CPU에서 확인합니다.
- **CDK 스택 테스트**: 18개는 `cdk/tests`에 따로 있고, CDK 라이브러리를 설치한 뒤 `cd cdk && python -m pytest -q tests`로 실행합니다.

> [!WARNING]
> **Linux 호스트에서 서버를 직접 띄울 때:** 샌드박스 서버는 평가가 끝날 때마다 `/proc`에 보이는 프로세스 중 자신과 조상을 뺀 모두에 SIGKILL을 보냅니다.
>
> - **pod 안에서**: 컨테이너 범위로 한정됩니다.
> - **Linux 호스트에서 `gpusandbox-server`를 직접 띄우면**: 같은 사용자의 다른 프로세스도 대상이 되니 별도 컨테이너에서 실행하세요.
> - **pytest**: `tests/conftest.py`에서 이 동작을 끄므로 Linux 호스트에서도 위 명령을 그대로 실행할 수 있습니다([시작하기](https://daekeun-ml.github.io/gpu-sandbox-on-aws/getting_started/)).

### 2. AWS에서 실행 (과금 발생)

시나리오를 하나 고르고 아래 명령을 위에서부터 차례로 실행합니다. 처음이라면 **시나리오 C**부터 시작하세요. GPU 없이 시간당 약 0.57 USD로 클러스터 생성부터 정리까지 해 볼 수 있습니다. 단계별 확인 방법은 [핸즈온 00 전체 흐름](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/00_overview/)에 있습니다.

#### 공통 준비 (한 번만)

1. 설정 파일을 만듭니다. 모든 스크립트가 이 파일을 읽으며, 필요한 값이 비어 있으면 그 자리에서 멈춥니다.
    - **`ADMIN_PRINCIPAL_ARN`을 비워 두면**: 지금 쓰는 IAM 역할이 클러스터 관리자가 됩니다.
    - **역할 ARN에 경로가 있으면**: 경로를 포함한 ARN을 직접 넣으세요.

    ```bash
    cp scripts/config.env.example scripts/config.env
    ```

2. CDK를 준비합니다. Node.js 22 또는 24와 AWS CLI용 Session Manager plugin을 먼저 설치하세요.

    ```bash
    npm install -g aws-cdk                 # AWS CDK CLI 2.1148.1 or later
    uv pip install -r cdk/requirements.txt # into the activated .venv
    source scripts/config.env              # exports AWS_REGION
    cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"
    ```

3. 아래 명령을 실행할 때 세 가지를 꼭 지키세요.
    - **새 작업 터미널을 열면 먼저 `source .venv/bin/activate`를 실행합니다.** 클러스터를 만들고 지우는 CDK 앱(`02`, `08`)이 가상 환경의 CDK 라이브러리를 씁니다.
    - **`cdk/tunnel.sh`는 두 번째 터미널에서 계속 켜 둡니다.** 클러스터 API가 비공개라서 kubectl과 helm은 이 터널로만 접속합니다.
    - **`03_build_push_images.sh`가 마지막에 출력하는 `export` 줄은 `scripts/config.env`에 붙여 넣습니다.** 이미지 주소가 없으면 다음 단계가 멈춥니다.

#### 시나리오 C: GPU 없이 시작 (추천)

`c8i.2xlarge` 한 대에 세 런타임(gVisor, Kata + Cloud Hypervisor, Kata + QEMU)의 CPU 샌드박스를 띄우고, 모델 없이 채점과 버전 교체를 실습합니다. 첫 명령은 풀마다 pod를 1개로 줄이는 설정을 `scripts/config.env`에 추가합니다. 이 설정이 없으면 버전 교체 때 v2 풀이 노드에 들어가지 않습니다.

```bash
printf '\nexport KATA_CPU_REPLICAS="1"\n' >> scripts/config.env  # one pod per pool, so v2 fits on the node
scripts/01_check_prereqs.sh                        # tools, identity, quotas (read-only)
scripts/02_create_cluster.sh --cpu-only            # VPC, private EKS, nodes (about 20 min)
cdk/tunnel.sh                                      # second terminal, keep it open
scripts/03_build_push_images.sh --no-trainer       # paste the printed export lines into config.env
scripts/kata/cpu_nodes.sh                          # Kata and gVisor runtimes on the c8i node
ACTIVE_RUNTIME=kata-clh-cpu scripts/05_setup_namespaces_auth.sh
for rt in gvisor-cpu kata-clh-cpu kata-qemu-cpu; do
  scripts/06_deploy_sandboxes.sh "${rt}" v1        # one sandbox pool per runtime
  scripts/ops/verify.sh "${rt}" v1                 # isolation, blocked egress, expected verdicts
done
scripts/ops/simulate.sh 30 20                      # reward batches without a model (about 16 min)
scripts/ops/rollout.sh kata-clh-cpu v1 v2          # another terminal, while simulate.sh runs
scripts/08_cleanup.sh                              # delete everything
```

단계별 설명은 [핸즈온 10 c8i 단독 저비용 경로](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/10_cpu_only/)에 있습니다.

#### 시나리오 A: EC2 GPU (기본)

trainer(`g5.2xlarge`)가 GRPO로 학습하고, reward는 gVisor GPU 샌드박스(`g5.xlarge` 두 대)가 채점합니다. `Running On-Demand G and VT instances` 쿼터가 16 vCPU 이상 필요합니다.

```bash
scripts/01_check_prereqs.sh                        # tools, identity, quotas (read-only)
scripts/02_create_cluster.sh                       # VPC, private EKS, GPU nodes (20-30 min)
cdk/tunnel.sh                                      # second terminal, keep it open
scripts/03_build_push_images.sh                    # paste the printed export lines into config.env
scripts/04_install_gpu_stack.sh                    # NVIDIA device plugin, gVisor, smoke pod
scripts/05_setup_namespaces_auth.sh                # namespaces, auth, NetworkPolicy, routing
scripts/06_deploy_sandboxes.sh gvisor v1           # gVisor sandbox pool
scripts/ops/verify.sh gvisor v1                    # isolation, blocked egress, expected verdicts
scripts/07_run_grpo.sh                             # GRPO training Job (60 steps by default)
scripts/08_cleanup.sh                              # delete everything
```

학습 중에 샌드박스 버전을 바꾸려면(`scripts/ops/rollout.sh`) 먼저 노드를 4대로 늘려야 합니다. 절차는 [핸즈온 06](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/06_sandbox_update/)에 있습니다.

**Kata 런타임 추가 (선택):** 04와 05 사이에 실행합니다.

- **Kata CPU:**
    1. `scripts/config.env`에서 `WITH_KATA_CPU`를 `"1"`로 바꿉니다.
    2. `02_create_cluster.sh`를 다시 실행합니다.
    3. `scripts/kata/cpu_nodes.sh`를 실행합니다.
- **Kata GPU (`g4dn.metal`, 시간당 약 7.8 USD):**
    1. `scripts/kata/gpu_nodes.sh`를 처음 실행하면 AMI를 만들고 멈춥니다.
    2. 출력된 `KATA_IOMMU_AMI_ID` 줄을 넣고 `WITH_KATA_GPU`를 `"1"`로 바꿉니다.
    3. `02_create_cluster.sh`와 `scripts/kata/gpu_nodes.sh`를 다시 실행합니다.

    자세한 내용은 [핸즈온 03](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/03_kata/)에 있습니다.

#### 시나리오 B1, B2: HyperPod

AWS에서 아직 실행하지 않은 경로입니다. `scripts/hyperpod/create.sh`를 실행하기 전에 HyperPod 전용 값(`HYPERPOD_LCS_BUCKET` 등)을 채우고 training operator 전제조건을 준비하세요. 자세한 내용은 [핸즈온 07](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/07_hyperpod/)에 있습니다.

<details>
<summary><b>B1: trainer만 HyperPod에</b></summary>

```bash
scripts/01_check_prereqs.sh
scripts/02_create_cluster.sh --hyperpod            # EKS with the gVisor nodes, no trainer node
cdk/tunnel.sh                                      # second terminal, keep it open
HYPERPOD=1 scripts/03_build_push_images.sh         # paste the printed export lines into config.env
scripts/04_install_gpu_stack.sh
scripts/hyperpod/create.sh                         # HyperPod trainer group (15-30 min)
scripts/05_setup_namespaces_auth.sh
scripts/06_deploy_sandboxes.sh gvisor v1
scripts/ops/verify.sh gvisor v1
scripts/hyperpod/run_grpo.sh                       # instead of 07_run_grpo.sh
scripts/hyperpod/delete.sh                         # delete HyperPod first
scripts/08_cleanup.sh
```

</details>

<details>
<summary><b>B2: trainer와 샌드박스 모두 HyperPod에 (실험)</b></summary>

```bash
scripts/01_check_prereqs.sh
scripts/02_create_cluster.sh --hyperpod-b2         # EKS with system nodes only
cdk/tunnel.sh                                      # second terminal, keep it open
HYPERPOD=1 scripts/03_build_push_images.sh         # paste the printed export lines into config.env
scripts/04_install_gpu_stack.sh
ACTIVE_RUNTIME=gvisor-hyperpod scripts/05_setup_namespaces_auth.sh
scripts/hyperpod/build_b2_ami.sh                   # custom AMI (20-40 min), paste HYPERPOD_B2_AMI_ID
scripts/hyperpod/create.sh --b2                    # trainer and sandbox groups
scripts/hyperpod/check_gvisor.sh                   # driver and gVisor support per node
scripts/06_deploy_sandboxes.sh gvisor-hyperpod v1
scripts/ops/verify.sh gvisor-hyperpod v1
scripts/hyperpod/run_grpo.sh
scripts/hyperpod/delete.sh                         # delete HyperPod first
scripts/08_cleanup.sh
```

</details>

#### 스크립트 폴더

스크립트마다 사용법, 다시 실행할 때의 동작, 성공 신호는 가이드북의 [스크립트 레퍼런스](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/scripts/)에 있습니다.

| 위치 | 용도 |
|---|---|
| `scripts/01_*.sh` ~ `08_*.sh` | 번호 순서대로 실행하는 기본 단계 |
| `scripts/kata/` | Kata 런타임 설치 |
| `scripts/ops/` | 풀 검증(`verify.sh`), 버전 교체(`rollout.sh`), 모델 없는 채점 루프(`simulate.sh`), 벤치마크(`bench.sh`) |
| `scripts/hyperpod/` | HyperPod 클러스터 생성, 학습, 삭제 |
| `scripts/extensions/` | Agent Sandbox 확장 |
| `cdk/` | 인프라(VPC, EKS, 노드 그룹)를 만드는 CDK 앱과 터널 |

<details>
<summary><b>스크립트별 역할 (펼치기)</b></summary>

| 스크립트 | 하는 일 |
|---|---|
| `scripts/01_check_prereqs.sh` | 로컬 도구, AWS 계정, 쿼터, nested virtualization 지원, GPU 인스턴스의 AZ별 제공 여부를 확인합니다. 조회만 하고 아무것도 만들지 않습니다. |
| `scripts/02_create_cluster.sh` | CDK로 VPC, 비공개 EKS 클러스터, 시나리오별 노드 그룹, SSM 접속 인스턴스를 만듭니다. 설정을 바꿔 다시 실행하면 노드 그룹을 추가하거나 바꿉니다. |
| `cdk/tunnel.sh` | 두 번째 터미널에 켜 두는 통로입니다. 클러스터를 만든 뒤 kubectl과 helm을 쓰는 동안 계속 켜 둡니다. |
| `scripts/03_build_push_images.sh` | sandbox, trainer, control 이미지를 `linux/amd64`로 빌드해 ECR에 올리고, 이미지 주소를 `export` 줄로 출력합니다. `--no-trainer`는 trainer를 건너뛰고, `HYPERPOD=1`은 trainer 이미지에 `hyperpodrun`을 넣습니다. |
| `scripts/04_install_gpu_stack.sh` | NVIDIA device plugin(CDI 모드)을 설치합니다. 이어서 `gvisor` RuntimeClass를 등록하고, smoke pod로 gVisor 안에서 GPU 연산이 되는지 확인합니다. B2와 C에서는 device plugin만 설치하고 나머지를 건너뜁니다. |
| `scripts/05_setup_namespaces_auth.sh` | namespace, NetworkPolicy, ServiceAccount, routing ConfigMap을 만들고, 클러스터의 토큰 서명 공개 키(JWKS)를 `sandbox` namespace로 복사합니다. 처음 쓸 런타임은 `ACTIVE_RUNTIME`으로 정합니다. |
| `scripts/06_deploy_sandboxes.sh <runtime> [version] [replicas]` | 샌드박스 풀 하나(Deployment와 headless Service)를 배포하고, pod가 모두 Ready가 될 때까지 기다립니다. |
| `scripts/07_run_grpo.sh [max_steps]` | GRPO 학습 Job(기본 60 step)을 제출하고 로그를 보여 줍니다. Ctrl-C는 로그 보기만 멈추고, 학습은 계속됩니다. |
| `scripts/08_cleanup.sh [--images]` | 클러스터 이름을 입력해 확인하면 Job과 풀, CDK 스택을 차례로 지웁니다. 설정에 적힌 AMI는 하나씩 따로 묻고, `--images`를 붙이면 ECR 저장소까지 지웁니다. |
| `cdk/deploy.sh`, `cdk/destroy.sh` | CDK 스택을 배포하고 지웁니다. 각각 `02_create_cluster.sh`와 `08_cleanup.sh`가 불러 씁니다. |
| `scripts/kata/cpu_nodes.sh` | c8i 노드에 kata-deploy를 설치하고 `gvisor-cpu` RuntimeClass를 등록한 뒤, 세 런타임(gVisor, Kata + Cloud Hypervisor, Kata + QEMU)의 smoke pod를 실행합니다. |
| `scripts/kata/gpu_nodes.sh` | 첫 실행은 IOMMU를 켠 AMI를 만들고 멈춥니다. `g4dn.metal` 노드가 생긴 뒤 다시 실행하면 GPU Operator와 kata-deploy를 설치하고, GPU passthrough(`nvidia.com/pgpu`)를 확인합니다. |
| `scripts/ops/verify.sh <runtime> [version]` | 풀 하나를 검증합니다. IMDS와 API 서버와 인터넷이 막혔는지, 미리 준비한 코드가 예상 결과를 받는지, 다른 namespace의 접속이 막히는지 검사합니다. |
| `scripts/ops/rollout.sh <runtime> <from> <to> [--finish]` | 학습 중에 샌드박스 버전을 바꿉니다(blue/green). 새 버전을 띄워 검증하고, 이전 버전과 결과가 같은지 확인한 뒤 routing을 전환합니다. |
| `scripts/ops/simulate.sh [steps] [interval_s]` | 시나리오 C에서 모델 없이 미리 준비한 코드를 배치마다 채점해, 어느 배치부터 새 버전을 쓰는지 보여 줍니다. 학습은 하지 않습니다. |
| `scripts/ops/bench.sh [requests]` | 배포된 v1 풀마다 cold start, 평가 지연, 처리량, speedup을 측정합니다. |
| `scripts/ops/sync_jwks.sh` | 클러스터의 토큰 서명 공개 키를 샌드박스 namespace로 다시 복사합니다. API 서버 키가 바뀌어 401 `unknown signing key`가 나올 때 실행합니다. |
| `scripts/hyperpod/create.sh [--b2]` | HyperPod 클러스터(trainer 그룹)를 만들어 EKS 클러스터에 연결합니다. `--b2`는 sandbox 그룹을 추가합니다. |
| `scripts/hyperpod/build_b2_ami.sh` | B2 sandbox 그룹용 custom AMI(gVisor가 지원하는 NVIDIA 드라이버와 gVisor 포함)를 만듭니다. `create.sh --b2` 전에 실행합니다. |
| `scripts/hyperpod/check_gvisor.sh` | HyperPod 노드마다 디버그 pod를 띄워 NVIDIA 드라이버 버전과 gVisor 지원 여부를 출력합니다. 끝나면 `default` namespace에서 이름이 `node-debugger-`로 시작하는 pod를 모두 지웁니다. |
| `scripts/hyperpod/run_grpo.sh [max_steps]` | 시나리오 B에서 `07_run_grpo.sh` 대신 HyperPod 노드에서 GRPO 학습을 실행합니다. |
| `scripts/hyperpod/delete.sh` | HyperPod 클러스터, 실행 역할, lifecycle 버킷을 지웁니다. `08_cleanup.sh`보다 먼저 실행합니다. |
| `scripts/extensions/agent_sandbox.sh` | Agent Sandbox 확장입니다. `install`은 controller를 설치하고, `pool`은 warm pool을 만듭니다. |
| `demo/deploy.sh`, `demo/teardown.sh` | 데모 사이트를 비공개 S3와 CloudFront로 배포하고(us-east-1), 지웁니다. |
| `scripts/logview.py` | Job 로그의 JSON 이벤트를 터미널에서 색을 입힌 한 줄 요약으로 보여 줍니다. `07_run_grpo.sh`, `ops/`의 검증과 측정 스크립트, `agent_sandbox.sh episodes`가 이 필터를 거칩니다. |
| `scripts/lib.sh`, `scripts/lib_jobs.sh` | 다른 스크립트가 불러 쓰는 공통 함수입니다. 직접 실행하지 않습니다. |

- **`02_create_cluster.sh`의 시나리오 선택**: 옵션이 없으면 `scripts/config.env`의 `SCENARIO`(기본값 A)를 쓰고, `--hyperpod`는 B1, `--hyperpod-b2`는 B2, `--cpu-only`는 C입니다.
- **`cdk/tunnel.sh`가 하는 일**: SSM 포트 포워딩으로 내 PC의 `127.0.0.1:8443`을 비공개 EKS API에 이어 주고, kubectl context `<CLUSTER_NAME>-tunnel`을 만듭니다.
- **`verify.sh`의 커널 출력**: 샌드박스 안의 커널과 노드 커널도 출력하니, 두 값이 다른지(격리)는 직접 확인하세요.
- **`rollout.sh`의 `--finish`**: 전환 뒤 새 버전의 `batch` 줄에 `sandbox_error` 외의 판정이 나오면, 같은 명령에 `--finish`를 붙여 이전 버전을 0으로 줄입니다.
- **`agent_sandbox.sh`의 `claim`과 `episodes`**: `claim`은 샌드박스 하나를 빌려 주소를 출력한 뒤 반납하고, `episodes`는 모델 없이 multi-turn 에피소드를 실행합니다.
- **HyperPod의 `run_grpo.sh` 로그**: `run_grpo.sh`는 로그를 볼 명령을 출력하니 그 명령을 따로 실행하세요.
- **원본 JSON을 보려면**: 명령 앞에 `GPUSANDBOX_LOG=json`을 붙이세요.

</details>

막히면 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)에서 단계별로 자주 생기는 문제를 확인하세요. 전체 목록은 가이드북의 [문제 해결](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/)에 있습니다.

## 가이드북의 주요 페이지

| 페이지 | 내용 |
|---|---|
| [시작하기](https://daekeun-ml.github.io/gpu-sandbox-on-aws/getting_started/) | 로컬 테스트, loopback smoke run, `scripts/config.env`, 경로 고르기 |
| [02 격리 런타임 비교](https://daekeun-ml.github.io/gpu-sandbox-on-aws/concepts/02_isolation_runtimes/) | gVisor와 Kata의 GPU 경로, AWS에서 각 런타임이 돌 수 있는 위치 |
| [05 상황별 선택 가이드](https://daekeun-ml.github.io/gpu-sandbox-on-aws/concepts/05_decision_guide/) | 격리 요구와 측정 GPU에 따른 런타임과 인스턴스 선택 |
| [핸즈온 00 전체 흐름](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/00_overview/) | 스크립트 순서, 최소 경로와 전체 경로, 시간당 비용 추정 |
| [Production 00 아키텍처](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/00_architecture/) | Karpenter NodePool, sandbox gateway, veRL on KubeRay |
| [04 Reward 무결성](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/04_reward_integrity/) | 2-프로세스 harness, 측정 계약, 공개된 reward hacking 사례별 대응 |
| [자주 하는 오해](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/faq/) | ".metal이 필요하다", "HyperPod 노드에 올릴 수 있다" 같은 오해 바로잡기 |
| [검증된 사실과 출처](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/sources/) | 출처 목록과 배포 전 재확인 체크리스트 |

## Agent Sandbox 확장

multi-turn episode마다 미리 띄워 둔 샌드박스를 하나씩 빌려 쓰는 확장입니다. [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) v1.0.11을 씁니다.

- 런타임 프로필(gvisor, kata-qemu, kata-clh-cpu 등)마다 샌드박스를 미리 띄워 둡니다(warm pool). episode가 시작되면 하나를 받아 쓰고, 끝나면 돌려줍니다(`src/gpusandbox/agent_sandbox.py`의 `EpisodeSandbox`).
- 샌드박스는 label이 붙은 trainer pod의 8000번 포트 접속만 받고, 밖으로 나가는 연결은 모두 막습니다. DNS 서버도 127.0.0.1로 고정해 controller가 공개 DNS 서버를 넣지 못하게 합니다.
- 설치, warm pool, claim, multi-turn 에피소드(`episodes`)를 시나리오 C 클러스터(`kata-clh-cpu`)에서 실행해 확인했습니다. GPU 런타임과 함께 쓰는 경우는 아직 클러스터에서 확인하지 않았습니다.
- warm pool의 GPU 샌드박스는 쉬는 동안에도 GPU를 잡고 있어 계속 과금됩니다.

```bash
scripts/extensions/agent_sandbox.sh install                 # controller, CRDs, claim RBAC
scripts/extensions/agent_sandbox.sh pool gvisor-cpu 2       # warm pool of two sandboxes
scripts/extensions/agent_sandbox.sh episodes gvisor-cpu 2 3 # 2 episodes of 3 turns, no model
```

개념은 [06 Agent Sandbox로 확장](https://daekeun-ml.github.io/gpu-sandbox-on-aws/concepts/06_agent_sandbox/)에, 실습 순서는 [핸즈온 11 multi-turn 에피소드 실습](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/11_multi_turn/)에 있습니다.

## 리플레이 데모 사이트

https://dohbsn4kn34ya.cloudfront.net/ (영어판은 주소 뒤에 `?lang=en`)

- 클러스터에서 녹화한 실행 기록을 브라우저에서 재생하는 정적 사이트입니다. 방문자는 클러스터나 GPU에 접속하지 않습니다.
- gVisor와 Kata가 같은 코드를 채점하는 과정, 샌드박스 안의 접근 시도가 막히는 터미널 출력, GRPO 학습과 버전 전환 차트, 벤치마크, 시나리오별 아키텍처 흐름을 보여 줍니다. 약 2분짜리 둘러보기 영상도 있습니다.
- 녹화 파일은 `demo/recordings/`에 있습니다. IP 주소와 노드 이름은 가리고, 올리기 전에 한 번 더 검사합니다.
- 사이트는 비공개 S3 버킷에 두고 CloudFront로만 읽으며, AWS WAF와 보안 헤더(CSP, HSTS 등)를 붙였습니다.
- 직접 배포하려면 `demo/deploy.sh`를, 지우려면 `demo/teardown.sh`를 실행합니다. 절차는 [09 데모 사이트 (CloudFront)](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/09_demo_site/)에 있습니다.

## 검증 상태

- **AWS에서 실행한 것:** 시나리오 A(gVisor GPU, `g5`, 기본 60 step 학습 포함), 시나리오 C(CPU 런타임 세 개)와 버전 교체, Kata GPU(`g4dn.metal`), 다섯 개 풀의 런타임 벤치마크, 공개 데모 사이트를 실습 계정에서 실행했습니다. 실험용 Kata CLH GPU는 VM이 시작되지 않았습니다. 측정값은 [08 런타임 벤치마크](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/08_benchmark/), 날짜별 실행 기록은 [검증된 사실과 출처](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/sources/#aws-실행-기록)에 있습니다.
- **AWS에서 실행하지 않은 것:** 학습 중의 `ops/rollout.sh`(시나리오 A), HyperPod B1과 B2. 이 단계는 각 핸즈온 페이지의 확인 단계로 직접 검증하세요.
- **수치:** 가격과 버전 같은 수치는 측정값이 아니라 공식 문서와 공개 자료의 값입니다.

## 비용

GPU 인스턴스는 켜져 있는 동안 계속 과금됩니다. 아래 금액은 컴퓨트의 온디맨드 요금만 더한 추정입니다(us-east-1과 us-west-2, 2026-11 기준이니 배포 전에 다시 확인하세요).

- 시나리오 C(system 노드 두 대와 `c8i.2xlarge` 한 대): 시간당 약 0.57 USD
- 시나리오 A의 gVisor 최소 경로: 시간당 약 3.42 USD
- Kata GPU용 `g4dn.metal`: 한 대에 시간당 7.824 USD
- EKS 컨트롤 플레인, NAT gateway, EBS, ECR 같은 항목은 위 금액에 들어 있지 않습니다.
- 쉬는 동안에는 노드 그룹을 0으로 줄이고, 실습이 끝나면 `scripts/08_cleanup.sh`로 모두 지우세요.

Kata GPU 노드를 0으로 줄이는 예시입니다.

```bash
aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu \
  --scaling-config minSize=0,maxSize=1,desiredSize=0
```

## 보안

- **사설 바인딩:** 샌드박스 서버는 기본으로 `127.0.0.1`에만 바인딩합니다. pod 매니페스트만 pod 네트워크 안에서 `0.0.0.0`을 쓰고, Service는 headless ClusterIP뿐이며 NetworkPolicy allowlist가 호출자를 제한합니다.
- **audience로 묶인 토큰:** 샌드박스 pod는 audience가 `gpu-sandbox`인 projected ServiceAccount 토큰을 클러스터 issuer의 JWKS(공개 키)로 오프라인 검증하고, 인증 설정이 비어 있으면 `/v1/evaluate`, `/info`, `/metrics` 요청을 거부합니다(fail closed).
    - **`/healthz`와 `/readyz`**: kubelet이 쓰는 이 두 경로는 토큰 없이 응답하므로 Ready 상태만으로 인증 설정을 확인할 수는 없습니다.
    - **pod 안**: 시크릿이 없고 Kubernetes API에도 접근하지 않습니다.
    - **gateway**: TokenReview와 subject allowlist로 호출자를 확인합니다.
- **공개 endpoint 없음:** 클러스터의 서비스는 인터넷에 공개하지 않고, 설계상 공개되는 것은 녹화 JSON과 정적 파일만 담은 데모 사이트뿐입니다. EKS API endpoint는 private만 열려 있고, 운영자는 inbound 규칙이 없는 SSM access instance를 거치는 `cdk/tunnel.sh`로 접속합니다.
- **egress 차단 확인:** 샌드박스는 IMDS, API 서버, 노드 kubelet에 닿지 않는 것을 확인한 뒤에만 Ready가 되고, 샌드박스 노드에는 iptables node guard가 있습니다.
- **로컬 전용 설정:** `SANDBOX_AUTH_TEST_BYPASS=1`은 loopback 테스트 전용이니 `0.0.0.0` 바인딩과 함께 쓰지 마세요. `scripts/config.env`에는 계정별 값이 들어가므로 커밋하지 않습니다(`.gitignore`에 포함).

위협 모델과 남는 위험은 [02 보안](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/02_security/)에 있습니다.

## License

코드와 문서는 [MIT](LICENSE)이고, 모델 라이선스는 별개입니다. 기본 모델 `Qwen/Qwen2.5-Coder-1.5B-Instruct`와 Production 예시의 `Qwen/Qwen2.5-Coder-7B-Instruct`는 Apache-2.0이고, `Qwen2.5-Coder-3B-Instruct`는 비상업 라이선스(qwen-research)라 이 저장소에서 쓰지 않습니다. 모델과 데이터셋을 바꿀 때는 각각의 라이선스를 직접 확인하세요.

이 저장소는 저자의 개인 견해와 조사 결과를 정리한 것으로, 저자가 재직 중인 회사의 공식 문서나 입장을 대변하지 않습니다.
