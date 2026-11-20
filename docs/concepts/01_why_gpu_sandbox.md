# GPU 샌드박스가 필요한 경우

!!! info "TL;DR"
    모델이 만든 코드를 GPU에서 실행하거나 속도를 재야 할 때 GPU 샌드박스가 필요합니다. 문법 검사나 CPU 단위 테스트만으로 채점할 수 있다면 CPU로 충분합니다.

## 어떤 순간에 GPU가 필요할까요?

모델에 “행렬 곱을 더 빠르게 만드는 Triton 커널을 작성해 줘”라고 요청했다고 해 봅시다. 답을 읽으면 코드 형태는 확인할 수 있습니다. 하지만 실제로 실행되는지, 결과가 맞는지, 기준 구현보다 빠른지는 목표 GPU에서 돌려 봐야 압니다. 이때 GPU 샌드박스가 모델이 만든 코드를 받아 실행하고 결과를 돌려줍니다.

샌드박스를 두면 그 코드가 trainer나 다른 작업과 실행 환경을 공유하는 범위가 줄어듭니다. trainer는 코드 대신 채점 결과를 받아 학습에 씁니다.

## CPU로 확인할 수 있는 것부터

| 알고 싶은 것 | 어디서 확인하나요? |
|---|---|
| 코드 형식이 맞고 CPU 단위 테스트를 통과하는가? | CPU |
| CUDA에서 실행되고 답이 맞는가? | GPU |
| 배포할 GPU에서 기준 구현보다 빠른가? | 목표 GPU |

앞 단계에서 걸러진 답에는 GPU 시간을 쓰지 않아도 됩니다. GPU까지 도달한 답은 정확도를 먼저 봅니다. 틀린 답이 빨리 끝났더라도 성능 개선으로 볼 수 없기 때문입니다.

![CPU에서 형식과 기본 검사를 마친 답만 GPU에서 실행하고 측정하는 흐름](../images/figures/concepts-01_why_gpu_sandbox--two-tier.svg)

GPU 작업의 격리 방식은 [런타임 비교](02_isolation_runtimes.md), 점수가 학습에 들어가는 과정은 [On-policy RL과 샌드박스](03_onpolicy_rl_with_sandboxes.md)에서 이어집니다. GPU 없이 채점 흐름을 보려면 [CPU 핸즈온](../handson/10_cpu_only.md)부터 시작하세요.

## 더 살펴보기

??? note "샌드박스에 GPU가 필요한 네 가지 경우"
    | 경우 | 예 | GPU가 필요한 이유 |
    |---|---|---|
    | GPU 커널 RL | KernelBench, CUDA-L1, Kevin-32B, TritonRL 계열 | reward가 GPU에서 측정한 정확성과 speedup이라서 GPU 없이는 채점 불가 |
    | 샌드박스 안의 로컬 모델 | 에이전트가 작은 모델을 실행해 추론하거나 평가하는 과제 | 모델 실행 자체가 과제의 일부 |
    | GPU 시뮬레이터 | 물리 시뮬레이션이나 렌더링 결과를 reward로 쓰는 환경 | 시뮬레이터가 GPU를 사용 |
    | ML 엔지니어 에이전트 | 학습이나 튜닝 스크립트를 실제로 실행하고 그 결과로 채점하는 과제 | 학습 실행이 GPU를 사용 |

    !!! note "GPU가 필요 없는 경우"
        단위 테스트로 채점하는 코드 RL, SQL, 수학 정답 검증처럼 후보 코드 실행과 채점에 필요한 측정을 모두 CPU에서 할 수 있으면 CPU 샌드박스로 충분합니다. CPU 샌드박스 선택지는 [05 상황별 선택 가이드](05_decision_guide.md)에 정리돼 있습니다.

??? note "이 저장소의 시나리오"
    코드 모델(기본 `Qwen/Qwen2.5-Coder-1.5B-Instruct`, Apache-2.0)은 PyTorch 모듈을 Triton 커널을 사용하는 `ModelNew`로 다시 작성합니다. 샌드박스가 정확성과 속도를 측정해 결과를 보내면, trainer가 format, correctness, speedup 점수를 계산합니다. 과제 형식은 KernelBench와 비슷합니다. 각 과제 모듈은 다음을 정의합니다.

    - 신뢰할 수 있는 reference `Model`
    - `get_init_inputs()`
    - seed별 입력을 만드는 `get_inputs(seed, device, size)`
    - 허용 오차 `ATOL`과 `RTOL`

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

??? note "적용 범위와 한계"
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
