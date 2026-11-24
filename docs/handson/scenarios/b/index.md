---
hide:
  - footer
---

# HyperPod 학습 경로 고르기 (시나리오 B)

<span id="07-hyperpod-시나리오"></span>

두 경로 모두 SageMaker HyperPod에서 GRPO 모델을 학습합니다. **모델이 만든 코드를 어디서 채점할지**에 따라 경로를 고르세요.

| | B1 (EC2에서 채점) | B2 (HyperPod에서 채점) |
|---|---|---|
| 시스템 노드 | EKS의 EC2 노드 | HyperPod `system` 그룹 |
| 학습 노드 | HyperPod `ml.g5.2xlarge` 1대 | HyperPod `ml.g5.2xlarge` 1대 |
| 채점 노드 | EC2 `g5.xlarge` 2대 | HyperPod `ml.g5.xlarge` 2대 |
| 시작 방법 | CDK로 EKS와 EC2 노드를 만든 뒤 HyperPod 학습 노드를 연결합니다. | HyperPod 마법사로 EKS와 세 인스턴스 그룹을 함께 만듭니다. |

- **[B1 실습 시작하기](b1.md)**　EC2에 채점 pool을 두고 HyperPod에서 학습 한 스텝을 실행합니다.
- **[B2 실습 시작하기](b2.md)**　시스템, 학습, 채점 노드를 모두 HyperPod에 배치하고 학습과 벤치마크를 실행합니다.

[다른 시나리오 보기](../../index.md#단계-순서)
