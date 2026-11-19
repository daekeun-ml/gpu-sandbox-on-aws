# GPU 샌드박스가 필요한 경우

**TL;DR** GPU 샌드박스는 reward를 GPU에서 측정하거나 샌드박스 안의 작업이 GPU를 사용할 때만 필요합니다. 이 에셋은 Triton 커널의 speedup 측정값을 reward로 쓰는 on-policy GRPO를 다룹니다.

## 기존 Pain Point

코드 실행 RL용 샌드박스는 대부분 CPU 전용이라 GPU에서 커널의 정확성과 속도를 측정하는 과제는 채점하지 못합니다. 샌드박스에 GPU를 연결하면 신뢰할 수 없는 코드가 GPU 드라이버를 직접 호출할 수 있습니다. 평가 여러 개가 한 GPU를 차례로 사용하면 이전 평가의 상태가 다음 평가에 남고, 샌드박스마다 GPU를 하나씩 할당하면 비용이 커집니다. reward가 speedup 측정값이면 policy가 커널을 빠르게 만드는 대신 측정 방식을 속이는 방법을 학습할 수도 있습니다.

![두 패널 그림입니다. a: 후보 커널 코드를 CPU 전용 샌드박스로 보내면 GPU에서 측정하는 과제를 채점할 수 없습니다. GPU 샌드박스로 보내면 네 가지 위험이 생깁니다. 신뢰할 수 없는 코드가 GPU 드라이버에 접근하고, 이전 평가의 상태가 다음 평가에 남고, 샌드박스마다 GPU 1개가 필요해 비용이 늘고, 측정을 속여 reward를 얻을 수 있습니다. b: 이 에셋은 CPU에서 형식과 AST 정책을 먼저 검사해, 위반은 GPU 실행 전에 판정합니다. GPU 샌드박스 pod는 pod당 GPU 1개와 평가 1개를 쓰고, gVisor 또는 Kata가 노드를 보호합니다. 실행마다 새 프로세스 트리와 캐시를 쓰고, GPU로는 정확성과 timing만 측정하며, host clock timing과 출력 checksum 비교로 측정 조작을 막습니다.](../images/figures/concepts-01_why_gpu_sandbox.svg)

*그림 요약: CPU 샌드박스로는 GPU 과제를 채점할 수 없고, GPU를 연결하면 드라이버 노출, 상태 오염, 비용 증가, 측정 조작의 위험이 생깁니다. 이 에셋은 CPU에서 먼저 검사하고, 네 가지 위험마다 대응 방법을 둡니다.*


## Why

- **reward 계산에 GPU가 필요한지가 첫 기준입니다.** GPU가 필요 없는 작업에 GPU 샌드박스를 쓰면 비용과 격리 부담만 늘어납니다.
- **GPU 시간은 정책을 통과한 코드에만 씁니다.** 코드 블록이 없거나 정책을 어긴 completion은 샌드박스를 부르지 않고 CPU에서 판정됩니다.
- **이 저장소의 과제는 10개이고 reward는 세 요소로 나뉩니다.** 측정을 속이는 시도는 AST 정책과 측정 harness가 함께 막습니다.

**사전 지식:** 필요 없습니다. 저장소가 만드는 것은 [홈](../index.md)에서, 처음 보는 용어는 아래 "용어" 상자와 [용어 사전](../reference/glossary.md)에서 확인할 수 있습니다.

??? note "용어 (처음 보는 단어가 있으면 펼치세요)"
    - **on-policy RL**: 지금 학습 중인 모델이 방금 생성한 completion으로만 다음 업데이트를 하는 강화학습 방식입니다.
    - **GRPO**: prompt 하나에 completion을 여러 개(group) 만들고, group 평균보다 나은 completion의 확률을 높이는 RL 알고리즘입니다.
    - **advantage**: 어떤 completion의 reward가 같은 group 평균보다 얼마나 높은지를 나타내는 값입니다. GRPO는 이 값으로 업데이트 방향을 정합니다.
    - **reward hacking**: 모델이 과제를 실제로 풀지 않고 채점 방식의 빈틈을 이용해 점수를 얻는 현상입니다.
    - **Triton 커널**: Python과 비슷한 문법으로 작성하는 GPU 프로그램입니다. 이 에셋에서는 모델이 Triton 커널을 작성합니다.
    - **CUDA stream**: GPU 작업이 순서대로 실행되는 대기열입니다. stream을 여러 개 쓰면 작업이 병렬로 실행될 수 있습니다.
    - **AST 정책**: 코드를 실행하기 전에 구문 트리(AST)를 읽어 금지된 API나 패턴을 찾는 정적 검사입니다.
    - **GPU passthrough (VFIO)**: 물리 GPU 장치를 VM에 직접 할당해 guest가 쓰게 하는 방식입니다.
    - **nvproxy**: gVisor가 GPU 요청(ioctl) 중 허용된 것만 host NVIDIA 드라이버로 전달하는 기능입니다.
    - **LoRA**: 모델 가중치 전체 대신 작은 어댑터 행렬만 학습하는 방법입니다.

## 샌드박스에 GPU가 필요한 네 가지 경우

| 경우 | 예 | GPU가 필요한 이유 |
|---|---|---|
| GPU 커널 RL | KernelBench, CUDA-L1, Kevin-32B, TritonRL 계열 | reward가 GPU에서 측정한 정확성과 speedup이라서 GPU 없이는 채점 불가 |
| 샌드박스 안의 로컬 모델 | 에이전트가 작은 모델을 실행해 추론하거나 평가하는 과제 | 모델 실행 자체가 과제의 일부 |
| GPU 시뮬레이터 | 물리 시뮬레이션이나 렌더링 결과를 reward로 쓰는 환경 | 시뮬레이터가 GPU를 사용 |
| ML 엔지니어 에이전트 | 학습이나 튜닝 스크립트를 실제로 실행하고 그 결과로 채점하는 과제 | 학습 실행이 GPU를 사용 |

!!! note "GPU가 필요 없는 경우"
    단위 테스트로 채점하는 코드 RL, SQL, 수학 정답 검증처럼 후보 코드 실행과 채점에 필요한 측정을 모두 CPU에서 할 수 있으면 CPU 샌드박스로 충분합니다. CPU 샌드박스 선택지는 [05 상황별 선택 가이드](05_decision_guide.md)에 정리돼 있습니다.

## 대부분의 샌드박스가 CPU 전용인 이유

| 이유 | 설명 |
|---|---|
| Firecracker에 GPU passthrough가 없음 | Firecracker는 virtio 장치 중심의 최소 장치 모델을 씁니다(FAQ 기준 에뮬레이션 장치 6개). 1.13.0에서 PCI 지원이 추가됐지만, 변경 이력에 VFIO GPU passthrough는 없습니다. Firecracker 기반 샌드박스 서비스(E2B 등)가 주로 CPU 위주인 배경 중 하나입니다. |
| 관리형 격리도 출시 시점에는 CPU 전용 | AWS Nitro Sandboxes(EKS isolated pods, 2026-11-09 출시) 문서에는 "GPU and other device passthrough are not supported at launch"라고 명시돼 있습니다. |
| CUDA 상태 오염 | 신뢰할 수 없는 코드 실행 여러 개가 한 GPU를 차례로 사용하면 남은 프로세스, Triton과 CUDA 컴파일 캐시, 드라이버 상태가 다음 평가에 영향을 줄 수 있습니다. 실행마다 프로세스 트리와 캐시를 새로 만들어야 합니다. 장치 리셋은 Kata에서 기존 VM이 GPU를 반납할 때 VFIO가 하고, gVisor에서는 pod를 바꿔도 같은 호스트 드라이버와 GPU를 계속 씁니다. GKE Sandbox 문서도 "Don't use GPU time-sharing in sandboxed Pods"라고 권고합니다. |
| 비용과 밀도 | timing을 신뢰하려면 평가 하나가 GPU 하나를 독점해야 합니다. 이 에셋은 pod당 GPU 1개, 한 번에 평가 1개(처리 중이면 503)로 운영하므로 CPU 샌드박스처럼 한 노드에 샌드박스를 많이 배치할 수 없습니다. |
| 드라이버 버전 의존성 | gVisor는 host 드라이버 버전이 nvproxy 지원 목록과 정확히 일치해야 하고, Kata는 guest VM 안에 드라이버를 따로 설치해야 합니다. 그만큼 관리할 버전 조합이 늘어납니다. |

## 두 계층 패턴: CPU에서 거르고 GPU에서 측정합니다

GPU 노드는 CPU 노드보다 시간당 요금이 높으므로(예: `g5.xlarge` 1.006 USD, `m6i.large` 0.096 USD, 온디맨드 요금), GPU 없이 판정할 수 있는 검사는 GPU 샌드박스로 보내기 전에 끝냅니다.

![trainer 프로세스(CPU) 안에서 completion이 KernelRewards로 전달되고, KernelRewards가 코드 블록을 추출해 AST 정책 검사(check_source)를 합니다. 코드 블록이 없거나 정책을 위반하면 샌드박스를 호출하지 않고 no_code 또는 policy_violation verdict가 됩니다. 검사를 통과한 코드는 GPU 계층(정확성 + timing, gVisor 또는 Kata + QEMU)으로 가고, GPU 계층이 verdict를 냅니다. 선택 사항인 CPU 계층(c8i의 Kata + CLH, 점선 테두리)은 따로 떨어져 있고, GPU 계층 앞 단계로 자동 연결되지 않습니다.](../images/figures/concepts-01_why_gpu_sandbox--two-tier.svg)

*그림 요약: 코드가 없거나 정책을 위반한 completion은 GPU 샌드박스를 호출하기 전에 CPU에서 판정되고, GPU 샌드박스는 정확성과 timing만 측정합니다.*


첫 단계는 trainer 프로세스 안의 `KernelRewards`입니다. `KernelRewards`는 코드 블록을 추출해 `check_source`로 AST 정책을 검사합니다. 정책 위반이면 샌드박스를 호출하지 않고, 샌드박스가 반환하는 것과 같은 `policy_violation` verdict를 기록합니다. 샌드박스 harness도 같은 정책을 다시 검사합니다. 이 정책은 reward 무결성을 위한 검사이고, 노드를 보호하는 보안 경계는 gVisor나 Kata입니다.

CPU 계층은 `kata-clh-cpu` 프로필과 Kata + Cloud Hypervisor 노드 그룹으로 구성됩니다. 이 노드 그룹은 nested virtualization(일반 EC2 VM 안에서 다시 VM을 실행하는 기능)을 켠 `c8i.2xlarge` 노드를 씁니다. 핸즈온에서는 `g4dn.metal` 비용이 발생하기 전에 이 계층에서 Kata를 적은 비용으로 연습합니다. Production에서는 nvcc 컴파일처럼 GPU가 필요 없는 단계를 이 계층에 둘 수 있습니다. harness에는 컴파일만 하는 모드가 없으므로 그 단계는 직접 만들어야 합니다.

## 이 에셋의 시나리오

코드 모델(기본 `Qwen/Qwen2.5-Coder-1.5B-Instruct`, Apache-2.0)은 PyTorch 모듈을 Triton 커널을 사용하는 `ModelNew`로 다시 작성합니다. 샌드박스가 정확성과 속도를 측정해 결과를 보내면, trainer가 format, correctness, speedup 점수를 계산합니다. 과제 형식은 KernelBench와 비슷합니다. 각 과제 모듈은 신뢰할 수 있는 reference `Model`, `get_init_inputs()`, seed별 입력을 만드는 `get_inputs(seed, device, size)`, 허용 오차 `ATOL`과 `RTOL`을 정의합니다.

### 과제 10개 (`src/gpusandbox/tasks/`)

| level | task_id | 내용 |
|---|---|---|
| 0 | `vector_add` | 1-D float32 텐서 두 개의 elementwise 덧셈 |
| 0 | `relu_bias` | 2-D activation에 열 단위 bias를 더한 뒤 ReLU |
| 0 | `scaled_residual` | `x + alpha * y` (alpha는 생성자 인자) |
| 1 | `silu_mul` | `silu(a) * b` (SwiGLU의 gate) |
| 1 | `gelu_tanh` | `approximate='tanh'` GELU |
| 1 | `row_sum_sq` | 행마다 제곱합 (출력 shape `[rows]`) |
| 2 | `row_softmax` | 마지막 차원 softmax (수치 안정) |
| 2 | `rms_norm` | 마지막 차원 RMSNorm |
| 2 | `layer_norm` | weight, bias를 쓰는 마지막 차원 LayerNorm |
| 3 | `matmul_bias_relu` | float16 `relu(x @ w + b)`, 커널 안에서 float32 누산 |

`train_grpo.py`는 기본값으로 `--max-level 2`(9개 과제)를 쓰고 과제마다 64행(`--repeats`)을 만듭니다. prompt에는 system prompt, 규칙, 과제에 없는 연산(`y = 2 * x`)의 Triton 예시, reference 소스가 들어갑니다. 과제 집합은 샌드박스 버전의 일부라서 과제를 바꾸면 새 샌드박스 버전으로 배포합니다.

### Reward 3요소

| 구성 | 값 | 가중치 (`--reward-weights`) |
|---|---|---|
| format | `ModelNew`를 정의하는 모듈로 파싱되면 1.0, 아니면 0.0 | 0.1 |
| correctness | `policy_violation`, `compile_error`, `timeout` 0.0 / `runtime_error` 0.05 / `wrong_answer` 0.2 / 정답이지만 Triton 커널 없음 0.3 / 정답 + 커스텀 커널 1.0 | 1.0 |
| speedup | log2 스케일: 0.5x 0.0, 1x 0.5, 2x 1.0, 4x 이상 1.5에서 상한. 정답이고 커스텀 커널일 때만 | 0.5 |

가중 합의 최댓값은 0.1 + 1.0 + 0.5 x 1.5 = 1.85입니다. 인프라 오류(`sandbox_error`)는 policy가 만든 오류가 아니므로 TRL에서는 세 요소 모두 `None`을 반환해 그 샘플을 학습에서 제외합니다(이유는 [03 On-policy RL과 샌드박스](03_onpolicy_rl_with_sandboxes.md)).

### RL 루프

![시계 방향 루프입니다. 데이터셋의 과제 prompt마다 vLLM이 completion 8개를 생성합니다. trainer가 CPU에서 코드 추출과 AST 정책 검사를 한 뒤, GPU 1개가 할당된 샌드박스 pod로 보냅니다. pod 안에서는 untrusted child가 후보 코드를 실행하고, trusted parent가 그 출력을 reference와 timing으로 판정해 verdict를 냅니다. 이어서 reward 3요소(format, correctness, speedup) 계산, GRPO의 group 기준 advantage 계산, LoRA 업데이트(optimizer step 1회)를 거치고, 점선 화살표의 가중치 동기화로 생성 단계로 돌아갑니다.](../images/figures/concepts-01_why_gpu_sandbox--rl-loop.svg)

*그림 요약: 샌드박스는 생성 단계와 업데이트 단계 사이에 있습니다. 그래서 채점이 느리면 학습 전체가 느려지고, 채점이 틀리면 학습이 잘못된 방향으로 진행됩니다.*


## 측정이 공격 표면이 되는 이유

speedup을 reward로 쓰면 policy는 측정 방식의 허점을 이용하는 방법을 학습할 수 있습니다.

| 공개된 reward hacking | 이 harness의 대응 |
|---|---|
| 추가 CUDA stream에서 연산을 실행해 timing을 속임 (CUDA-L1: 250건 중 82건, 32.8%) | host clock으로 `torch.cuda.synchronize()`를 감싸 모든 stream을 기다림. AST 정책이 stream과 graph API를 금지 |
| 결과 캐싱 | timed iteration마다 다른 입력 |
| 벤치마크 때만 틀리기, 메모리 재사용 no-op 커널 | 모든 timed 출력의 checksum을 reference와 비교 |
| lazy evaluation | 출력 텐서는 모두 정확히 `torch.Tensor` 타입이어야 함(subclass 불가). 리스트나 튜플로 반환하면 각 원소를 검사 |
| reference 복사, PyTorch나 cuBLAS 호출로 대체 | 정답이어도 Triton 커널이 없거나 정확성 검사 중 launch 횟수가 0이면 correctness 0.3, speedup 0. 횟수를 셀 수 없으면 AST의 Triton 커널 정의로 판정 |
| monkeypatch, harness 내부 접근, 메모리 조작으로 정확성 검사 우회 | 후보는 별도 프로세스에서 실행되고, 정확성은 trusted parent가 매 요청 새 seed로 직접 비교. AST 정책이 `__init__` 외의 밑줄 속성 접근과 `self` 밖의 속성 대입을 금지 |

KernelBench의 기본 timing인 CUDA event(L2 flush 포함)는 추가 stream에서 실행된 작업을 측정에 포함하지 못할 수 있습니다(host_time 모드는 모든 stream을 포함해 측정합니다). KernelBench는 10배를 넘는 speedup을 의심 대상으로 표시하고(`excessive_speedup_threshold 10`), 이 에셋의 샌드박스 v2는 10배를 넘는 측정값에 `implausible_speedup` 플래그를 달고 speedup을 1배로 채점합니다.

??? info "기존 샌드박스 프로젝트 대신 작은 서버를 쓴 이유"
    GPU timing을 측정하려면 샌드박스마다 독점 GPU 하나와 신뢰할 수 있는 측정 harness가 필요합니다. 그래서 이 두 기능만 제공하는 작은 서버(`src/gpusandbox/server/app.py`)를 씁니다. 기존 프로젝트로는 kubernetes-sigs/agent-sandbox(v1.0.11), OpenSandbox(release-1.2.1), GPU 실행을 직렬화하는 ByteDance SandboxFusion이 있습니다. 이 서버를 Agent Sandbox의 warm pool에서 실행하는 방법은 [06 Agent Sandbox로 확장](06_agent_sandbox.md)에서 설명합니다.

!!! question "❓ 오해: trainer GPU에서 바로 채점하면 된다"
    그렇게 하면 신뢰할 수 없는 코드가 trainer와 같은 드라이버와 노드를 사용합니다. vLLM 생성과 역전파도 같은 GPU를 사용하므로 timing 측정값이 불안정해집니다. 이 에셋은 GPU 하나를 독점하는 별도 샌드박스 pod에서 채점합니다.

!!! question "❓ 오해: speedup은 어떤 GPU에서 측정해도 비슷하다"
    speedup은 GPU 종류마다 다르고, policy는 reward를 측정한 GPU에 맞춰 최적화됩니다. 런타임 벤치마크(`scripts/ops/bench.sh`)도 gVisor 풀(A10G)과 Kata 풀(T4)의 speedup을 따로 비교하라고 안내합니다. 배포할 GPU가 정해져 있다면 같은 GPU나 비슷한 GPU에서 측정하세요. GPU 종류와 런타임 선택의 관계는 [05 상황별 선택 가이드](05_decision_guide.md)에서 설명합니다.

## 적용 범위와 한계

- CPU 계층에서 GPU 계층으로 작업을 자동으로 전달하는 파이프라인은 없습니다. 두 계층 패턴은 trainer 안의 사전 검사와 별도 CPU 풀로 구현돼 있습니다.
- harness 방어는 위 표의 공개 사례를 대상으로 합니다. 그 밖의 위험과 운영 대책은 [Production 04 Reward 무결성](../production/04_reward_integrity.md)에서 다룹니다.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | AWS Nitro Sandboxes | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html |
    | EKS sandboxing 제한 사항 | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
    | KernelBench GitHub, v0.1 블로그 | https://github.com/ScalingIntelligence/KernelBench , https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/ |
    | 과제, prompt, reward 코드 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tasks/__init__.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/prompts.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py |
    | harness timing, 정책 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/timing.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/policy.py |

    전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-concepts-01-why-gpu-sandbox)
