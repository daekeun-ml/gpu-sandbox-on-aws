---
hide:
  - footer
---

# EC2에서 GPU 학습과 채점하기 (시나리오 A)

<span id="ec2에서-gpu-학습과-채점하기-시나리오-a"></span>

<span id="시나리오-a--ec2에서-gpu-학습과-채점하기"></span>

EC2의 학습 노드에서 생성한 코드를 별도의 gVisor GPU 두 대가 채점합니다. [공통 절차 03의 A 탭](../../common/03_pools/index.md#__tabbed_1_1)에서 `sandbox-gvisor-v1` 검증을 마쳤다면 학습을 시작하세요.

## 1. GRPO 학습 시작하기 { #train }

처음에는 [5스텝 학습](grpo.md#__tabbed_1_1)을 실행하세요. `batch`에서 코드 판정을, 다음 `train` 줄에서 모델 업데이트를 확인합니다. 학습만 진행하면 [정리](#cleanup)로 가세요.

## 2. 선택 실습으로 채점 pool 교체하기 { #switch }

학습 중 v2로 전환하려면 **학습을 시작하기 전에** [채점 GPU 네 대를 준비](pool_update.md#준비-bluegreen에-필요한-gpu)한 뒤 [60스텝 학습](grpo.md#__tabbed_1_2)을 선택하세요. 첫 v1 배치가 나오면 다른 터미널에서 [v2로 전환](pool_update.md#실행)하고 `SWITCH` 다음 배치에서 v2 판정을 확인하세요. 그 뒤 v1을 줄입니다.

## 3. 결과 확인과 정리 { #cleanup }

Job의 `Complete` 상태와 `reward_batch`의 판정을 확인하세요. 성능도 비교하려면 학습을 마친 뒤 [런타임 벤치마크](../../benchmarks/index.md#run-benchmark)를 실행하세요. 실습이 끝나면 터널을 열어 둔 채 [리소스를 정리](../../cleanup.md#cleanup-cdk)합니다.
