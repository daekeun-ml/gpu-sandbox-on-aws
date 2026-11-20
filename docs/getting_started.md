# 시작하기

!!! info "TL;DR"
    AWS 없이 로컬 CPU에서 파이프라인을 먼저 확인한 다음, `scripts/config.env`를 채우고 시나리오를 고릅니다.

## GPU 노드를 띄우기 전에

로컬 CPU 테스트로 설치와 채점을 먼저 확인하세요. 그다음 AWS 실습 경로를 고릅니다. 이미지 URI와 AMI ID는 앞 단계에서 만든 값을 사용합니다.

![a: GPU 노드를 시작한 뒤에야 import 오류나 설정 누락을 발견합니다. 오류를 고치고 다시 실행하는 동안에도 GPU 노드 요금이 계속 나갑니다. b: 먼저 로컬 CPU에서 pytest 109개와 GRPO dry run 2 step으로 파이프라인을 확인합니다(AWS 비용 없음). 다음으로 scripts/config.env를 채우고(그 단계에 필요한 값이 비었거나 __SET_ME__면 스크립트가 그 자리에서 멈춥니다), 경로(A, B1, B2, C, Production)를 고릅니다. GPU 노드는 그다음에 시작하므로 과금도 그때부터 시작됩니다.](images/figures/getting_started.ko.svg)

*그림 요약: (a)는 GPU 노드부터 띄우는 순서이고, (b)는 로컬 CPU에서 pytest와 dry run을 마치고 설정 파일을 채운 뒤 경로를 고르는 순서입니다. AWS 노드는 그다음에 띄우고, 시나리오 C에서는 GPU 노드 없이 CPU 샌드박스를 실행합니다.*


## 로컬에서 확인할 수 있는 것

- **AWS 비용 없이 파이프라인부터 확인합니다.** 샌드박스 서버, 2-프로세스 harness, 인증, 라우팅, reward 함수는 CPU에서도 같은 코드로 실행됩니다.
- **저자가 확인한 범위를 같은 명령으로 재현합니다.** pytest와 GRPO dry run 2 step은 macOS(CPU 전용)에서 실행해 확인했습니다(당시 테스트 94개, 현재는 109개).
- **설정은 한 파일에 모읍니다.** 모든 스크립트가 `scripts/lib.sh`를 거쳐 `scripts/config.env`를 읽습니다. 필요한 값이 비어 있거나 `__SET_ME__` 그대로이면 스크립트가 그 자리에서 멈춥니다.

**읽기 전에**　터미널, `git`, Python 가상 환경을 다룰 수 있으면 충분하고, 로컬 단계(1~4장)에는 Kubernetes와 AWS 지식이 필요 없습니다. 시작할 코스는 [학습 코스 고르기](learning_paths.md), 전체 구성은 [홈](index.md)의 "만드는 것", GPU 샌드박스가 필요한 이유는 [01 GPU 샌드박스가 필요한 경우](concepts/01_why_gpu_sandbox.md)에 있습니다.

??? note "용어 (처음 보는 단어가 있으면 펼치세요)"
    - **샌드박스(sandbox)**: 신뢰할 수 없는 코드를 격리해서 실행하는 환경입니다. 이 저장소에서는 모델이 쓴 커널 코드를 실행해 채점하는 HTTP 서버를 말합니다.
    - **harness**: 후보 코드를 실행하고 정확성과 속도를 측정해 verdict(채점 결과)를 내리는 채점 프로그램입니다.
    - **golden**: 기대 verdict가 미리 정해진 시험용 제출물입니다. 서버가 올바르게 채점하는지 확인할 때 씁니다.
    - **loopback**: 자기 컴퓨터 안에서만 접속할 수 있는 주소(`127.0.0.1`)입니다. 다른 컴퓨터에서는 이 주소로 접속할 수 없습니다.
    - **smoke run**: 본 실행 전에 파이프라인이 제대로 연결됐는지만 짧게 확인하는 실행입니다.
    - **GRPO**: 같은 prompt에 completion(모델이 생성한 답)을 여러 개 생성하고, 그 group 안에서 평균보다 나은 completion을 강화하는 RL 알고리즘입니다.
    - **dry run**: 실제 학습 대신 아주 짧게(여기서는 2 step) 학습해 연결만 확인하는 실행입니다.
    - **reward**: RL에서 completion 하나에 주는 점수입니다. 이 저장소에서는 형식, 정확성, speedup 세 요소의 가중 합입니다.
    - **quota**: AWS 계정에서 동시에 쓸 수 있는 자원의 상한입니다. EC2 GPU quota는 인스턴스 수가 아니라 vCPU 수로 셉니다.
    - **fail closed**: 설정이 빠졌거나 검증할 수 없을 때 허용하지 않고 거부하는 동작입니다.

    더 자세한 설명은 [용어 사전](reference/glossary.md)에 있습니다.

## 준비물

### 로컬 도구

| 도구 | 쓰는 곳 | 비고 |
|---|---|---|
| AWS CLI v2 | 모든 AWS 단계 | `aws sts get-caller-identity`가 동작해야 함 |
| AWS CDK CLI | VPC, 클러스터, 노드 그룹 생성(`02_create_cluster.sh`)과 삭제(`08_cleanup.sh`) | 2.1148.1 이상, `npm install -g aws-cdk` |
| Node.js | CDK CLI 실행 | 22 또는 24 LTS (jsii가 지원하는 버전) |
| Session Manager plugin | `cdk/tunnel.sh`로 private API endpoint에 접속 | AWS CLI용 plugin. `session-manager-plugin --version`으로 확인 |
| kubectl | 배포와 검증 | 클러스터 버전(1.36)과 마이너 버전 차이 1 이내 |
| helm | device plugin, kata-deploy(OCI 차트), GPU Operator, HyperPod 의존성 차트 | Helm 3 |
| docker (buildx) | 이미지 3개를 `linux/amd64`로 빌드해 ECR에 push | arm64 워크스테이션이라면 디스크 100 GB 이상의 x86_64 호스트 권장 |
| python3 | 매니페스트 템플릿 렌더링 (`scripts/render.py`), CDK 앱 | CDK 앱은 저장소의 가상 환경에서 실행 |
| jq | JSON 처리 | |
| git | HyperPod 의존성 차트 clone (Scenario B) | |
| uv | 로컬 Python 환경 | 로컬 테스트에만 필요 |

`scripts/01_check_prereqs.sh`는 이 중 `aws cdk node kubectl helm docker python3 jq session-manager-plugin`의 설치 여부를 확인합니다. eksctl은 private endpoint만 있는 클러스터를 만들 수 없어서 쓰지 않습니다.

### AWS 계정과 quota

| quota (vCPU 기준) | 핸즈온 필요량 | 비고 |
|---|---|---|
| Running On-Demand G and VT instances | 시나리오 A 16, B1 8, B2와 C는 0 | 새 계정은 기본값이 0일 수 있음 |
| Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances | 6 (system `m6i.large` 2 x 2 + SSM 접속 인스턴스 `t4g.nano` 2) | 문서상 기본값 5 |
| `ml.g5.2xlarge for cluster usage` (SageMaker) | 1 (Scenario B) | HyperPod 전용 quota |
| `ml.g5.xlarge for cluster usage` (SageMaker) | 2 (Scenario B2) | B2의 `sandbox` 인스턴스 그룹(`HYPERPOD_SANDBOX_COUNT`) |

- **G and VT, 시나리오 A**: 16은 trainer `g5.2xlarge` 8 + gVisor `g5.xlarge` 4 x 2입니다.
- **G and VT, B1**: trainer가 HyperPod에서 실행되므로 필요량이 gVisor 노드 몫인 8로 줄어듭니다.
- **G and VT, B2와 C**: EC2 GPU 노드가 없어서 G and VT 쿼터 없이 시작할 수 있습니다.
- **Kata GPU까지 하면**: G and VT에 `g4dn.metal` 96을 더합니다.
- **Standard, 시나리오 C이거나 Kata CPU까지 하면**: `c8i.2xlarge` 8을 더해 14입니다.
- **Standard, B2와 Kata GPU**: custom AMI를 빌드하는 동안 빌더 `m6i.large` 2가 더 필요해 8(c8i와 함께 쓰면 16)입니다.
- **B1과 B2**: 위의 SageMaker 쿼터를 따로 확인하세요.

quota 증가는 처리에 시간이 걸릴 수 있으니 클러스터를 만들기 전에 신청하세요.

## 1. 저장소 받기

저장소를 내려받고 그 폴더로 이동합니다.

```bash
git clone https://github.com/daekeun-ml/gpu-sandbox-on-aws.git
cd gpu-sandbox-on-aws
```

**확인할 것:** `ls`를 실행하면 `docs`, `scripts`, `src`, `tests` 폴더가 보입니다.

## 2. 로컬 Python 환경

가상 환경을 만들고 CPU 전용 PyTorch를 먼저 설치한 뒤, 이 패키지를 `dev` extra와 함께 editable 모드(소스를 고치면 재설치 없이 반영)로 설치합니다. 순서는 GitHub Actions 테스트 워크플로와 같습니다.

=== "macOS"

    ```bash
    uv venv --python 3.14
    source .venv/bin/activate
    # macOS: the default PyPI wheels have no CUDA, so this is enough
    uv pip install torch numpy
    uv pip install -e ".[dev]"
    ```

=== "Linux"

    ```bash
    uv venv --python 3.14
    source .venv/bin/activate
    # Linux: CPU-only wheels, as in .github/workflows/tests.yml
    uv pip install --index-url https://download.pytorch.org/whl/cpu torch numpy
    uv pip install -e ".[dev]"
    ```

`.[dev]`에는 pytest, FastAPI, uvicorn, httpx, PyJWT, PyYAML, kubernetes가 들어 있습니다. CI는 여기에 `gateway` extra와 `shellcheck-py`를 추가로 설치하고, pytest 다음에 셸 스크립트를 shellcheck로 검사합니다.

설치를 확인합니다.

```bash
python -c "import torch, gpusandbox; print(torch.__version__, torch.cuda.is_available())"
```

**확인할 것:** PyTorch 버전 뒤에 `False`가 출력됩니다(CPU 전용 설치라 정상).

## 3. 테스트 실행

저장소의 테스트 전체를 실행합니다.

```bash
python -m pytest -q
```

**확인할 것:** 마지막 줄이 `109 passed`로 시작합니다(뒤에 붙는 소요 시간은 환경마다 다름).

- **구성**: 109개는 핵심 68개, [Agent Sandbox 확장](concepts/06_agent_sandbox.md)과 [multi-turn 에피소드](handson/11_multi_turn.md) 30개, [데모 사이트](handson/09_demo_site.md) 11개로 구성됩니다.
- **범위**: AST 정책, CPU 2-프로세스 harness(정답, 오답, 크래시, timeout, 벤치마크 치팅, monkeypatch), fail closed 인증, egress 차단 확인 뒤의 readiness, 클라이언트, gateway의 group 단위 버전 고정, 운영 도구, 매니페스트와 노드 user data(`infra/eks/userdata.py`)와 Karpenter 템플릿 렌더링, 데모 사이트의 보안 속성입니다. 파일별 범위는 [저장소 구조](reference/repository_map.md#tests)에 있습니다.
- **CDK 스택 테스트**: 18개는 `cdk/tests`에 따로 있고, 5장의 CDK 준비를 마친 뒤 `cd cdk && python -m pytest -q tests`로 실행합니다.

**문제가 생기면:** `ModuleNotFoundError`는 대개 가상 환경이 비활성화됐거나 2장의 설치가 빠진 경우이니, `source .venv/bin/activate`를 다시 실행하고 2장을 반복하세요.

!!! warning "Linux 호스트에서 서버를 띄우는 단계"
    샌드박스 서버는 평가가 끝날 때마다 `/proc`에 보이는 프로세스 중 자신과 상위 프로세스를 뺀 모든 프로세스에 SIGKILL을 보냅니다([`procs.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/procs.py)).

    - **pod 안에서**: 대상이 컨테이너의 PID namespace 안으로 한정됩니다.
    - **Linux 호스트에서 직접 실행하면**: 같은 사용자의 다른 프로세스(편집기, 다른 서버, trainer)도 종료되고, root로 실행하면 시스템 프로세스도 종료됩니다.
    - **macOS에서**: `/proc`가 없어서 이 동작이 실행되지 않습니다.

    안전하게 실행하는 방법은 다음과 같습니다.

    - **pytest**: `tests/conftest.py`의 autouse fixture가 이 동작을 끄기 때문에, Linux 호스트에서도 위의 `python -m pytest -q`를 그대로 실행해도 됩니다.
    - **4장처럼 서버를 직접 띄우는 단계**: Linux 호스트가 아니라 서버마다 별도 컨테이너(별도 PID namespace)에서 실행하세요.
    - **컨테이너가 자기 네트워크 namespace를 쓰면**: 서버의 기본 bind가 `127.0.0.1`(`SANDBOX_HOST`)이라 호스트에서 보낸 4.2와 4.3의 요청이 닿지 않습니다.
    - **호스트 네트워크를 함께 쓰는 컨테이너로 띄우면**: (예: `docker run --network host`, PID namespace는 따로 유지) 기본 bind 그대로 접근할 수 있습니다.

    서버를 띄우지 않는 테스트만 빠르게 확인하려면 `slow`를 제외합니다.

    ```bash
    # Skips the tests marked "slow" (harness subprocesses and in-process servers)
    python -m pytest -q -m "not slow"
    ```

    **확인할 것:** `91 passed, 18 deselected`가 출력됩니다.

## 4. Loopback smoke run (macOS)

클러스터의 샌드박스 pod 두 개 대신 loopback에 CPU 샌드박스 서버 두 개를 띄워 golden probe와 GRPO dry run을 실행합니다.

### 4.1 샌드박스 서버 두 개 띄우기

터미널 두 개에서 하나씩 실행합니다. 두 서버는 포트와 작업 디렉터리만 다릅니다.

```bash
# Terminal 1
source .venv/bin/activate
SANDBOX_DEVICE=cpu SANDBOX_SIZE=smoke SANDBOX_AUTH_TEST_BYPASS=1 \
SANDBOX_RUNTIME=local SANDBOX_VERSION=v1 \
SANDBOX_WORK_ROOT=/tmp/gpusandbox/18001 SANDBOX_PORT=18001 \
gpusandbox-server
```

```bash
# Terminal 2
source .venv/bin/activate
SANDBOX_DEVICE=cpu SANDBOX_SIZE=smoke SANDBOX_AUTH_TEST_BYPASS=1 \
SANDBOX_RUNTIME=local SANDBOX_VERSION=v1 \
SANDBOX_WORK_ROOT=/tmp/gpusandbox/18002 SANDBOX_PORT=18002 \
gpusandbox-server
```

| 변수 | 값 | 의미 |
|---|---|---|
| `SANDBOX_DEVICE` | `cpu` | harness를 CPU에서 실행 (기본값 `cuda`) |
| `SANDBOX_SIZE` | `smoke` | 작은 입력 shape (기본값 `full`) |
| `SANDBOX_AUTH_TEST_BYPASS` | `1` | 토큰 검증을 끔. 로컬 loopback 전용이며 기본값은 꺼짐 |
| `SANDBOX_RUNTIME`, `SANDBOX_VERSION` | `local`, `v1` | 응답과 로그에 표시되는 라벨 |
| `SANDBOX_WORK_ROOT` | `/tmp/gpusandbox/<port>` | 요청별 작업 디렉터리의 루트. 기본값 `/work`는 컨테이너 기준이라 로컬에서는 바꿔야 함 |
| `SANDBOX_PORT` | `18001`, `18002` | 기본값 `8000` |

**확인할 것:** 각 터미널에 아래와 같은 기동 로그가 나옵니다(macOS 실행 예시, 버전과 프로세스 번호는 환경마다 다름).

```text
WARNING:gpusandbox.auth:authentication TEST BYPASS is enabled; use only on loopback
WARNING:gpusandbox.server:egress self-test disabled (SANDBOX_EGRESS_PROBE_TARGETS is empty)
INFO:gpusandbox.server:device probe ok=True info={'torch': '2.15.0', 'cuda_runtime': None}
INFO:     Uvicorn running on http://127.0.0.1:18001 (Press CTRL+C to quit)
```

두 경고는 로컬에서 실행할 때 정상적으로 나오는 메시지입니다. 서버는 기본으로 `127.0.0.1`에만 바인딩합니다(`SANDBOX_HOST`).

??? note "클러스터에서의 bind와 접근 제한"
    클러스터에서는 pod 매니페스트가 `SANDBOX_HOST=0.0.0.0`을 설정합니다. trainer는 headless ClusterIP Service(가상 IP 없이 pod 주소를 DNS로 알려 줌)로 샌드박스 pod 주소를 조회하고, NetworkPolicy(pod 사이의 방화벽 규칙)는 trainer namespace에서 오는 연결만 허용합니다.

**문제가 생기면:** `address already in use`는 다른 프로세스가 그 포트를 쓰고 있다는 뜻이니, 다른 포트(예: `18011`)로 바꾸고 4.2와 4.3의 주소도 맞추세요.

!!! warning "테스트 bypass는 loopback에서만"
    `SANDBOX_AUTH_TEST_BYPASS=1`은 `/v1/evaluate`, `/info`, `/metrics`의 토큰 검증을 모두 끕니다.

    - **bypass와 `SANDBOX_HOST=0.0.0.0`**: 서버 코드는 둘을 함께 설정해도 거부하지 않으므로 두 설정을 함께 쓰지 마세요.
    - **클러스터에서**: 저장소의 매니페스트는 이 변수를 설정하지 않습니다. 클러스터의 샌드박스 pod는 audience 기반 ServiceAccount 토큰을 검증하고, 인증 설정이 비어 있으면 평가, 서버 정보, 지표 요청(`/v1/evaluate`, `/info`, `/metrics`)을 401로 거부(fail closed)합니다.
    - **`/healthz`와 `/readyz`**: 인증 없이 서버 상태만 알려 주므로, 아래 `/readyz` 응답은 인증 설정과 관계없습니다.

### 4.2 서버 확인 (golden probe)

세 번째 터미널에서 readiness를 확인하고 golden probe를 두 서버에 보냅니다. probe는 golden 제출물의 verdict를 기대값과 비교하는 운영 도구입니다.

```bash
source .venv/bin/activate
curl -s http://127.0.0.1:18001/readyz
python -m gpusandbox.tools probe --address 127.0.0.1:18001,127.0.0.1:18002 --device cpu
```

**확인할 것:**

- 아래와 비슷하게 나오고 종료 코드가 0이면 됩니다(macOS 실행 예시).
- 서버는 device probe를 마친 뒤에 요청을 받으므로 두 터미널에 `Uvicorn running`이 나온 뒤 실행하세요. 그 전에는 연결이 거부되어 `curl -s`가 아무것도 출력하지 않습니다.
- `pod`, `kernel_release`, `speedup` 값은 환경과 실행마다 다릅니다.

```text
{"status":"ready"}
{"endpoint": "127.0.0.1:18001", "pod": "842f578ca5a5", "runtime": "local", "version": "v1", "kernel_release": "25.6.0", "gpu": null, "egress_blocked": true}
{"endpoint": "127.0.0.1:18002", "pod": "842f578ca5a5", "runtime": "local", "version": "v1", "kernel_release": "25.6.0", "gpu": null, "egress_blocked": true}
PASS relu_bias_torch_only         status=ok                speedup=0.9474
PASS relu_bias_wrong              status=wrong_answer      speedup=None
PASS relu_bias_benchmark_cheat    status=wrong_answer      speedup=None
PASS read_host_file               status=policy_violation  speedup=None
```

CPU에서는 Triton 커널이 필요한 golden을 제외하고 아래 4개만 실행됩니다.

| golden | 기대 verdict |
|---|---|
| `relu_bias_torch_only` | `ok` |
| `relu_bias_wrong` | `wrong_answer` |
| `relu_bias_benchmark_cheat` | `wrong_answer` (벤치마크가 시작되면 틀린 결과를 내는 코드) |
| `read_host_file` | `policy_violation` |

로컬에서 `egress_blocked`가 `true`로 나오는 이유는 self-test 대상(`SANDBOX_EGRESS_PROBE_TARGETS`)이 비어 있기 때문입니다. 클러스터에서는 샌드박스 서버가 IMDS, API server, 노드 kubelet으로 가는 연결이 차단됐는지 확인한 뒤에만 Ready 상태가 됩니다. IMDS는 노드 자격 증명을 제공하는 EC2 인스턴스 메타데이터 서비스입니다.

**문제가 생기면:**

- **`FAIL` 줄이 있거나 연결 오류가 나면**: 두 서버의 기동 로그에 `device probe ok=True`가 있는지 먼저 확인하세요.
- **클러스터에서 실패하면**: [문제 해결](reference/troubleshooting.md)의 "샌드박스 풀과 readiness" 항목을 보세요.

### 4.3 TRL GRPO dry run

trainer 이미지와 같은 버전의 TRL 스택을 설치한 뒤 dry run을 실행합니다. Hugging Face Hub에서 `HuggingFaceTB/SmolLM2-135M-Instruct`를 내려받습니다.

```bash
# Same pins as trainer/Dockerfile (as of 2026-11, re-verify)
uv pip install "trl==1.18.0" "peft==0.21.3" "datasets>=4.7"

SANDBOX_ADDRESS="127.0.0.1:18001,127.0.0.1:18002" SANDBOX_RUNTIME=local \
python rl/trl/train_grpo.py --dry-run \
  --model HuggingFaceTB/SmolLM2-135M-Instruct \
  --output-dir /tmp/grpo-dry-run \
  --allow-torch-only
```

- `--dry-run`은 vLLM 없이 CPU에서 2 step만 실행하고 completion을 32 token으로 자릅니다.
- `--output-dir`는 쓰기 가능한 경로여야 합니다(기본값 `/outputs/grpo`는 pod 기준).
- `--allow-torch-only`는 Triton 커널이 없어도 정답이면 correctness 점수 1.0을 주는 옵션입니다. 끄면 PyTorch만 쓴 정답은 0.3을 받습니다. CPU에서는 Triton 커널을 실행할 수 없어서 이 dry run에서는 켭니다.
- 로컬에서는 `SANDBOX_ADDRESS`에 쉼표로 나열한 두 서버 주소를 그대로 사용합니다. 클러스터 Job은 이 변수 대신 `SANDBOX_ROUTING_FILE`이 가리키는 routing 표(ConfigMap)에서 현재 풀의 Service 주소를 읽습니다.
- LoRA는 모델 가중치 전체 대신 작은 어댑터 행렬만 학습하는 방법이고, trainer가 기본으로 씁니다.

**확인할 것:**

- 처음에 `{"event": "routing", "mode": "direct", "runtime": "local", "version": "v1", "address": "127.0.0.1:18001,127.0.0.1:18002"}`가 출력됩니다.
- TRL 로그가 2 step 나오고, reward 함수별 값(`rewards/format_reward` 등)이 함께 출력됩니다.
- 마지막에 `{"event": "done", "output": "/tmp/grpo-dry-run/final", "reward_batches": ...}`가 출력됩니다.

**문제가 생기면:**

- **모델 다운로드 오류**: 네트워크나 Hugging Face Hub 접근 문제입니다.
- **클러스터 학습 중 오류가 나면**: [문제 해결](reference/troubleshooting.md)의 "학습" 항목을 보세요.

!!! note "`reward_batches`가 0이어도 정상"
    135M 모델이 32 token 안에 코드 블록을 닫지 못하면 trainer가 `no_code`로 처리해 샌드박스를 호출하지 않습니다. 이 단계는 TRL과 reward 함수의 연결(라우팅, 함수 시그니처, LoRA, 저장)을 확인하는 용도이고, 샌드박스 호출 경로는 4.2의 probe와 pytest로 확인합니다.

## 5. `scripts/config.env` 만들기

예시 파일을 복사해 설정 파일을 만듭니다.

```bash
cp scripts/config.env.example scripts/config.env
```

**확인할 것:** `scripts/config.env`가 생깁니다. 아래 표의 "처음" 값부터 채우세요.

| 변수 | 채우는 시점 | 값 |
|---|---|---|
| `AWS_REGION` | 처음 | 기본 `us-west-2`. 이 문서의 가격은 us-east-1과 us-west-2 기준 |
| `CLUSTER_NAME` | 처음 | 기본 `gpu-sandbox` |
| `K8S_VERSION` | 처음 | `1.36`. EKS standard support(2027-08-02까지)와 HyperPod EKS AMI 릴리스 노트의 지원 버전 안 |
| `SCENARIO` | 처음 | `A`(기본), `B1`, `B2`, `C`. `scripts/02_create_cluster.sh`의 옵션이 그 실행에서만 이 값을 덮어씀(표 아래 참고) |
| `ADMIN_PRINCIPAL_ARN` | 처음 (선택) | 클러스터 관리자 access entry를 받을 IAM 역할이나 사용자 ARN(쉼표로 여러 개) |
| `HYPERPOD_LCS_BUCKET` | Scenario B 전 (필수) | `__SET_ME__`를 바꾼 고유 이름. HyperPod managed policy가 `sagemaker-` 접두사를 기대함 |
| `SANDBOX_IMAGE_URI`, `TRAINER_IMAGE_URI`, `CONTROL_IMAGE_URI` | `scripts/03_build_push_images.sh` 실행 후 | 스크립트가 출력하는 `export` 줄을 붙여 넣음 |
| `WITH_KATA_CPU` | Kata CPU 노드 추가(`scripts/kata/cpu_nodes.sh`) 전 | `1`로 두고 `02_create_cluster.sh`를 다시 실행하면 `sandbox-kata-cpu`(`c8i.2xlarge`) 노드 그룹이 생김. 시나리오 C에는 처음부터 있음 |
| `KATA_IOMMU_AMI_ID`, `WITH_KATA_GPU` | Kata GPU 노드 추가(`scripts/kata/gpu_nodes.sh`) 첫 실행 후 | AMI ID는 `infra/kata/build-iommu-ami.sh`가 출력. `WITH_KATA_GPU=1`과 함께 넣고 `02_create_cluster.sh`를 다시 실행하면 `sandbox-kata-gpu`(`g4dn.metal`) 노드 그룹이 생김 |
| 인스턴스 타입, 버전 고정 값 | 보통 그대로 | `GVISOR_RELEASE=20261109.0`, `KATA_VERSION=4.3.1`, `GPU_OPERATOR_VERSION=v26.7.2`, `NVIDIA_DEVICE_PLUGIN_VERSION=0.20.1` |

- **`K8S_VERSION`과 HyperPod 전제조건 페이지**: 이 페이지는 아직 1.35까지로 적혀 있습니다.
- **`SCENARIO`를 덮어쓰는 옵션**: `--hyperpod`, `--hyperpod-b2`, `--cpu-only`입니다. 옵션으로 배포했다면 이 값을 배포한 시나리오로 바꿔 두거나, 노드 그룹을 추가하려고 다시 실행할 때도 같은 옵션을 붙이세요(다르면 `cdk/deploy.sh`가 멈춤).
- **`ADMIN_PRINCIPAL_ARN`을 비우면**: `cdk/deploy.sh`가 현재 역할을 씁니다.
- **역할에 path가 있으면**: `ADMIN_PRINCIPAL_ARN`을 직접 적으세요.

!!! note "알아 두면 좋은 점"
    - ECR 저장소는 tag immutable로 만들어집니다. 이미지를 다시 빌드할 때는 `IMAGE_TAG`를 바꾸세요.
    - Scenario B의 trainer 이미지는 `hyperpodrun`이 필요하므로 `HYPERPOD=1 scripts/03_build_push_images.sh`로 빌드합니다.
    - `scripts/config.env`에는 계정별 값이 들어가므로 커밋하지 마세요.

`scripts/02_create_cluster.sh`는 CDK 앱으로 인프라를 만드므로 AWS 단계 전에 CDK를 한 번 준비합니다. 도구 표의 AWS CDK CLI, Node.js, Session Manager plugin을 설치한 뒤 아래 명령을 실행하세요. `cdk bootstrap`은 CDK가 배포에 쓰는 S3 버킷과 IAM 역할을 계정과 리전마다 한 번 만듭니다.

```bash
# One-time CDK setup (in the activated .venv)
uv pip install -r cdk/requirements.txt
source scripts/config.env              # exports AWS_REGION
cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"
```

**확인할 것:** 명령이 오류 없이 끝나고, CloudFormation에 bootstrap 스택 `CDKToolkit`이 생깁니다. 권한을 좁히는 법은 [Production 09 CDK로 프로비저닝](production/09_cdk.md)에 있습니다.

값을 채웠으면 사전 점검 스크립트를 실행합니다(읽기 전용).

```bash
scripts/01_check_prereqs.sh
```

**확인할 것:** AWS identity 표, 도구 버전, G and VT quota, `c8i.2xlarge`의 nested virtualization 지원 여부, GPU 인스턴스 타입의 AZ별 제공 여부가 차례로 출력됩니다. 스크립트는 후보 인스턴스 타입을 모두 조회하므로, 고른 시나리오에서 만들 노드만 확인하세요.

- **G and VT quota**: quota 표의 `Running On-Demand G and VT instances` 값이 시나리오 A는 16, B1은 8 이상인지 (B2와 C는 0). Kata GPU를 추가하면 어느 시나리오든 96을 더하고, gVisor 풀을 v1에서 v2로 교체하는 동안에는 `g5.xlarge` 두 대분 8이 더 필요합니다
- **Standard quota**: 값이 6 이상인지 (시나리오 C이거나 Kata CPU까지 하면 14 이상. custom AMI를 빌드하는 B2와 Kata GPU는 2를 더해 8, c8i와 함께 쓰면 16 이상)
- **c8i를 쓴다면(시나리오 C, Kata CPU)**: nested virtualization 줄에 `nested-virtualization`이 들어 있는지
- **GPU 노드의 AZ**: 만들 GPU 노드의 인스턴스 타입(A는 `g5.2xlarge`와 `g5.xlarge`, B1은 `g5.xlarge`, Kata GPU는 `g4dn.metal`) 옆의 AZ 목록에, CDK 스택이 쓰는 두 AZ(CDK가 조회한 리전 AZ 목록의 앞 두 곳) 중 한 곳 이상이 있는지. 스크립트는 리전 전체를 조회하므로 다른 AZ 이름만 나와도 노드를 만들 수 없습니다

**문제가 생기면:**

- **`[error] set CLUSTER_NAME in scripts/config.env`처럼 멈추면**: 그 값을 채우고 다시 실행하세요.
- **`missing tool` 같은 메시지**: [문제 해결](reference/troubleshooting.md)의 "설정과 스크립트" 항목을 보세요.

## 6. 경로 고르기

| 경로 | 이런 경우 | 첫 명령 | 다음 페이지 |
|---|---|---|---|
| Scenario A (EC2 자체 운영) | 모든 구성 요소를 직접 제어하고 싶을 때 | `scripts/02_create_cluster.sh` | [핸즈온 00 전체 흐름](handson/00_overview.md) |
| Scenario B1 (HyperPod, 기본) | 장시간 학습에 HyperPod의 노드 자동 교체와 job 재시작이 필요할 때 | `scripts/02_create_cluster.sh --hyperpod` 다음 `scripts/hyperpod/create.sh` | [07 HyperPod 시나리오](handson/07_hyperpod.md) |
| Scenario B2 (HyperPod, 실험) | 샌드박스 노드까지 HyperPod 인스턴스 그룹에 두고 싶을 때 | `scripts/02_create_cluster.sh --hyperpod-b2` 다음 `scripts/hyperpod/build_b2_ami.sh` | [07 HyperPod 시나리오의 B2](handson/07_hyperpod.md#b2). custom AMI를 직접 관리 |
| Scenario C (c8i 단독, GPU 없음) | GPU 쿼터가 없거나, 시간당 약 0.57 USD로 런타임 비교와 버전 교체를 먼저 익히고 싶을 때 | `scripts/02_create_cluster.sh --cpu-only` | [핸즈온 10 c8i 단독 저비용 경로](handson/10_cpu_only.md) |
| Production | Karpenter NodePool, sandbox gateway, veRL로 확장할 때 | 핸즈온을 마친 뒤 | [Production 00 아키텍처](production/00_architecture.md) |

`02_create_cluster.sh`가 끝나면 두 번째 터미널에서 `cdk/tunnel.sh`를 실행하고 그대로 두세요. EKS API endpoint는 private 접근만 허용하므로, kubectl과 helm을 쓰는 모든 단계는 이 SSM 포트 포워딩(`127.0.0.1:8443`, kubectl 컨텍스트 `<CLUSTER_NAME>-tunnel`)으로 API에 접속합니다.

런타임과 인스턴스를 아직 정하지 않았다면 [05 상황별 선택 가이드](concepts/05_decision_guide.md)와 [04 플랫폼과 인스턴스 선택](concepts/04_platforms_and_instances.md)을 먼저 보세요.

## 적용 범위와 한계

- 1~4장의 로컬 단계는 저자가 macOS(CPU 전용)에서 확인했고(당시 테스트 94개, 현재는 109개), Linux 호스트에서 서버를 띄우는 테스트는 확인하지 않았습니다.
- 5장의 `scripts/01_check_prereqs.sh`는 저자가 실행하지 않았습니다.
- 그 뒤 단계 가운데 시나리오 A의 gVisor 경로(`02`부터 `08`까지), 시나리오 C, Kata GPU(`g4dn.metal`), 런타임 벤치마크는 실습 계정에서 실행했습니다. 날짜별 실행 기록은 [검증된 사실과 출처](reference/sources.md#aws-실행-기록)에 있습니다.
- 시나리오 A의 학습 중 `ops/rollout.sh`와 HyperPod B1, B2는 실행하지 않았습니다. 실행하지 않은 단계는 각 핸즈온 페이지의 확인 단계로 검증하세요.
- dry run은 학습 효과를 보여 주지 않으며, 실제 학습은 [05 On-policy GRPO 학습](handson/05_grpo_training.md)에서 GPU로 실행합니다.

## 소요 시간과 비용

- **로컬 단계(1~4장):** AWS 비용이 없고, 시간은 PyTorch wheel과 모델 다운로드 속도에 따라 대략 15~30분입니다(측정값이 아닌 추정).
- **AWS 단계:**
    - **클러스터 생성**: `02_create_cluster.sh`의 CDK 배포는 실습 계정에서 약 20분 걸렸습니다(시나리오 C).
    - **GPU 노드 그룹이 `InsufficientInstanceCapacity`로 인스턴스를 시작하지 못하면**: CloudFormation이 약 30분을 기다린 뒤 처음 생성 전체를 롤백합니다. 대처 순서는 [01 클러스터와 이미지](handson/01_cluster_and_images.md)의 클러스터 생성 절을 보세요.
    - **GRPO Job**: 실습 계정에서 2026-11-18에 실행한 5 step GRPO Job(`g5.2xlarge`)은 이미지 pull과 모델 다운로드를 포함해 약 12분 걸렸습니다.
    - **비용**: GPU 인스턴스는 실행되는 동안 과금되고, 시나리오 A의 gVisor 최소 경로는 컴퓨트만 시간당 약 3.42 USD입니다(추정). 구성별 시간당 추정은 [04 플랫폼과 인스턴스 선택](concepts/04_platforms_and_instances.md)에 있습니다.

## 정리

두 서버를 각 터미널에서 Ctrl-C로 멈춘 뒤, 로컬 작업 디렉터리를 지웁니다.

```bash
# Stop both servers with Ctrl-C first, then remove the local work directories
rm -rf /tmp/gpusandbox /tmp/grpo-dry-run
```

**확인할 것:** 아무것도 출력되지 않습니다.

- **dry run을 처음부터 하려면**: `train_grpo.py`는 출력 디렉터리의 `checkpoint-*`에서 이어 학습하므로 `/tmp/grpo-dry-run`을 지워야 합니다.
- **AWS 리소스**: [99 정리](handson/99_cleanup.md)를 따라 지우세요.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | AWS CLI v2 설치 | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |
    | EC2 instance type quotas | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html |
    | AWS CDK v2 개발자 가이드, bootstrapping | https://docs.aws.amazon.com/cdk/v2/guide/home.html , https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html |
    | uv | https://github.com/astral-sh/uv |
    | GRPO trainer, 설정 예시 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/trl/train_grpo.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/config.env.example |

    전체 출처: [참고 자료 모음의 이 페이지 절](reference/references.md#ref-getting-started)
