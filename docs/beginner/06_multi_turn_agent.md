# 06 multi-turn 에이전트와 Agent Sandbox

**TL;DR** 이 에셋의 reward 채점은 completion 하나를 한 번 채점하는 single-turn 방식이고, 요청마다 reward 풀의 유휴 pod 하나가 채점합니다. multi-turn 에이전트는 한 에피소드의 모든 turn을 같은 샌드박스에서 채점해야 하므로, Agent Sandbox로 에피소드마다 샌드박스 하나를 할당합니다.

## 기존 Pain Point

reward 풀은 요청마다 유휴 pod 하나를 선택하고, 요청이 끝나면 그 pod의 상태를 삭제합니다. multi-turn 에이전트는 코드를 제출하고 verdict를 읽은 뒤 코드를 고쳐 다시 제출하므로, 한 에피소드의 모든 turn을 같은 샌드박스, 같은 GPU, 같은 샌드박스 버전에서 채점해야 합니다. 에피소드마다 샌드박스를 새로 만들면 매번 시작을 기다려야 하고, Kata GPU VM은 처음 Ready가 될 때까지 몇 분이 걸릴 수 있습니다.

![두 패널 그림입니다. a single-turn 채점: GRPO trainer가 completion 1개를 reward 풀에 제출하면, 풀은 요청마다 유휴 pod 하나를 새로 선택해 채점하고 verdict 1개를 반환합니다. 요청이 끝나면 pod의 상태를 삭제합니다. b multi-turn 에피소드: SandboxWarmPool에 미리 실행한 샌드박스 하나가 SandboxClaim으로 에피소드에 할당됩니다. 에이전트(모델)는 turn 1 코드를 제출하고, verdict를 피드백으로 읽고, 수정한 turn 2 코드를 제출한 뒤 다시 verdict를 받습니다. 모든 turn은 claim한 샌드박스 하나에서 같은 GPU와 같은 샌드박스 버전으로 채점되고, 이 샌드박스는 에피소드가 끝나면 삭제됩니다.](../images/figures/beginner-06_multi_turn_agent.svg)

*그림 요약: single-turn 채점에서는 completion마다 유휴 pod 하나가 한 번 채점하고 상태를 삭제합니다. multi-turn 에피소드에서는 warm pool에서 claim한 샌드박스 하나가 에피소드의 모든 turn을 같은 GPU와 같은 버전으로 채점합니다.*


## Why

- **single-turn 채점과 multi-turn 에이전트의 차이를 그림으로 설명합니다.** 두 방식에서 샌드박스가 언제 만들어지고 언제 삭제되는지 비교해요.
- **Agent Sandbox의 리소스와 수명 주기를 한 문장씩 정리합니다.** claim, 할당, 반납 순서로 설명합니다.
- **AI on EKS의 Agent Sandbox 솔루션과 이 에셋이 다루는 범위를 비교합니다.**

**사전 지식:** [04편](04_rl_and_sandbox.md)을 읽었다면 충분합니다. [05편](05_hands_on.md)의 실습은 하지 않아도 됩니다.

??? note "용어 (처음 보는 단어가 있으면 펼치세요)"
    - **single-turn 채점:** completion 하나를 샌드박스에 한 번 제출하고 verdict 하나를 받는 채점입니다. 이 에셋의 GRPO 학습이 이 방식입니다.
    - **multi-turn:** 모델이 도구를 호출하거나 코드를 제출하고, 결과를 읽은 뒤 다시 응답하는 과정을 여러 번 반복하는 방식입니다.
    - **turn:** multi-turn 에피소드에서 모델이 한 번 응답하는 단계입니다. 이 에셋의 과제에서는 코드를 한 번 제출하고 verdict를 받는 한 차례입니다.
    - **에피소드(episode):** 모델이 과제 하나를 여러 turn에 걸쳐 푸는 한 번의 시도입니다.
    - **verdict:** harness가 제출된 코드 하나를 채점해 반환하는 결과입니다. 상태(정답, 오답, 정책 위반 등)와 speedup이 들어 있어요.
    - **CRD (Custom Resource Definition):** Kubernetes에 새 리소스 종류를 추가하는 정의입니다.
    - **warm pool:** 요청이 오기 전에 미리 실행해 둔 샌드박스 묶음입니다.
    - **claim:** warm pool에서 샌드박스 하나를 할당받기 위한 요청입니다.

    더 많은 용어는 [용어 사전](../reference/glossary.md)에 있습니다.

## single-turn 채점: 이 에셋의 reward 풀

GRPO 학습에서는 completion 하나를 샌드박스에 한 번 제출하고 verdict 하나를 받습니다. 이 에셋의 reward 풀은 런타임과 버전마다 Deployment 하나로 실행하는 샌드박스 pod 묶음입니다.

- **요청마다 유휴 pod 하나가 채점합니다.** pod는 한 번에 평가 하나만 처리하고, 처리 중인 pod는 503을 반환합니다. 그러면 클라이언트가 다른 pod로 요청을 보냅니다.
- **요청이 끝나면 상태를 삭제합니다.** pod는 요청마다 새 프로세스 트리를 만들고, 평가가 끝나면 정리합니다. 그래서 다음 요청은 이전 요청의 파일이나 프로세스를 이어서 쓸 수 없습니다.
- **GPU 유휴 시간이 줄어듭니다.** 요청마다 비어 있는 pod를 선택하므로, 채점을 기다리는 GPU가 적습니다.

## multi-turn 에이전트: 에피소드 단위로 채점하기

multi-turn 에이전트는 한 에피소드 안에서 다음 순서를 반복합니다.

1. 코드를 작성해 제출합니다(turn 1).
2. verdict를 피드백으로 읽습니다. 예를 들어 상태, 오류 메시지의 끝부분, speedup을 모델에 돌려줍니다.
3. 코드를 고쳐 다시 제출합니다(turn 2). 과제가 끝날 때까지 2와 3을 반복합니다.

이때 한 에피소드의 모든 turn은 같은 샌드박스, 같은 GPU, 같은 샌드박스 버전에서 채점되어야 합니다. turn마다 GPU나 채점 버전이 바뀌면 turn 1과 turn 2의 verdict를 같은 기준으로 비교할 수 없습니다(추론). reward 풀은 요청마다 유휴 pod를 새로 선택하므로, 같은 에피소드의 turn이 서로 다른 pod와 GPU에서 채점될 수 있습니다.

그렇다고 에피소드마다 샌드박스를 새로 만들면 에피소드가 시작될 때마다 샌드박스가 준비되기를 기다려야 합니다. Kata GPU VM은 guest 메모리 전체를 고정하고 guest 안에서 CUDA를 초기화하므로, 처음 Ready가 될 때까지 몇 분이 걸릴 수 있습니다(deployment 템플릿 주석).

## Agent Sandbox

Agent Sandbox(kubernetes-sigs/agent-sandbox)는 Kubernetes SIG Apps에서 개발하는 오픈소스 프로젝트입니다. 샌드박스 pod를 미리 실행해 두고, 요청이 오면 하나를 할당하고, 사용이 끝나면 회수합니다. 이 작업은 Kubernetes CRD로 정의한 리소스로 관리해요.

| 리소스 | 하는 일 |
|---|---|
| `SandboxTemplate` | 샌드박스 pod를 만들 때 쓰는 설정입니다. 이미지, RuntimeClass, NetworkPolicy를 여기에 적습니다 |
| `SandboxWarmPool` | template으로 만든 샌드박스를 몇 개 미리 실행해 둘지 정합니다 |
| `SandboxClaim` | warm pool에서 샌드박스 하나를 할당받는 요청입니다. 에피소드마다 하나를 만듭니다 |

할당된 샌드박스 하나는 `Sandbox` 리소스이고, pod 하나를 관리합니다. `Sandbox`는 warm pool이 만들므로 직접 만들지 않아요. 네 리소스의 API 버전은 모두 `v1beta1`이고, 최신 릴리스는 v1.0.11입니다.

### 수명 주기: claim, 할당, 반납

1. **미리 실행:** SandboxWarmPool이 template으로 샌드박스를 정해진 수(`replicas`)만큼 실행합니다. 이 에셋의 샌드박스는 GPU 초기화와 egress 차단 확인이 끝나야 Ready가 됩니다.
2. **claim:** 에피소드가 시작되면 SandboxClaim을 하나 만듭니다.
3. **할당:** controller가 대기 중인 샌드박스 하나를 claim에 할당합니다. warm pool은 `replicas`를 맞추려고 새 샌드박스를 실행합니다.
4. **turn 반복:** 에피소드의 모든 평가 요청을 claim에 기록된 주소(`status.sandbox.serviceFQDN`)로 보냅니다.
5. **반납:** 에피소드가 끝나면 claim을 삭제합니다. 할당된 샌드박스와 pod도 함께 삭제되고, 다시 사용되지 않습니다. Kata라면 VM과 GPU도 반환됩니다.

trainer가 비정상 종료되어 claim을 삭제하지 못할 수도 있습니다. 이 에셋의 `EpisodeSandbox`는 claim에 만료 시각(`shutdownTime`)을 지정하므로, 그 시각이 지나면 controller가 claim과 샌드박스를 삭제하고 샌드박스가 점유하던 GPU가 해제됩니다.

!!! question "❓ 오해: Agent Sandbox가 샌드박스를 격리한다"
    격리는 pod의 RuntimeClass(gVisor 또는 Kata)가 담당합니다. Agent Sandbox는 샌드박스를 미리 준비하고, 할당하고, 회수하는 일만 합니다. 그래서 노드가 해당 RuntimeClass를 지원하면, 같은 template에서 RuntimeClass만 바꿔 gVisor와 Kata를 모두 쓸 수 있습니다.

## 방식 선택 기준

| 작업 | 쓰는 방식 | 이유 |
|---|---|---|
| single-turn reward 채점 (GRPO가 completion마다 한 번 채점) | 이 에셋의 reward 풀 | 요청마다 유휴 pod를 선택하므로 GPU 유휴 시간이 줄어듭니다 |
| multi-turn 에이전트 (verdict를 읽고 코드를 고쳐 다시 제출) | 에피소드 단위 샌드박스 (Agent Sandbox) | 한 에피소드의 모든 turn이 같은 GPU와 같은 샌드박스 버전에서 실행됩니다 |

!!! warning "대기 중인 GPU 샌드박스도 GPU를 점유합니다"
    warm pool의 샌드박스는 평가를 처리하지 않는 동안에도 GPU 하나를 계속 점유하므로, 그동안 비용이 발생합니다. 예를 들어 gVisor 프로필은 `g5.xlarge` 한 대에 샌드박스 하나를 실행하므로, 대기 샌드박스 하나가 시간당 1.006 USD인 노드 한 대를 점유합니다(us-east-1과 us-west-2 온디맨드 요금). `replicas`는 동시에 실행할 에피소드 수에 맞추고, 학습을 멈춘 동안에는 warm pool을 0으로 줄이세요.

    ```bash
    # Hold no idle GPU: scale the warm pool to zero (claimed sandboxes are not touched)
    scripts/extensions/agent_sandbox.sh pool gvisor 0
    ```

## AI on EKS의 Agent Sandbox 솔루션과 비교

awslabs의 [AI on EKS](https://github.com/awslabs/ai-on-eks) 프로젝트에는 [Agent Sandbox on EKS](https://awslabs.github.io/ai-on-eks/ko/docs/infra/agents/agent-sandbox) 솔루션이 있습니다. 이 솔루션과 이 에셋은 모두 kubernetes-sigs/agent-sandbox를 쓰지만, 다루는 워크로드가 다릅니다.

| 항목 | AI on EKS Agent Sandbox 솔루션 | 이 에셋 |
|---|---|---|
| 대상 | 모델이 생성한 코드를 실행하는 AI 에이전트. 페이지에 GPU 언급이 없습니다 | GPU 커널 채점 (reward) |
| 격리 런타임 | 계층 세 가지: `standard`(runc), `gvisor`(Standard EKS만), `isolated-sandbox`(Nitro Sandboxes) | gVisor + nvproxy (`g5.xlarge`, A10G) 또는 Kata + VFIO (`g4dn.metal`, T4) |
| Agent Sandbox 사용 | Sandbox, SandboxTemplate, SandboxWarmPool, SandboxClaim(`v1beta1`)으로 수명 주기를 관리하고, KRO로 여러 리소스를 `AgentSandbox` 리소스 하나로 묶습니다 | 선택 확장입니다. multi-turn 에피소드마다 GPU 샌드박스 하나를 claim합니다. 기본 채점은 Deployment 기반 reward 풀입니다 |
| egress | 허용한 도메인(FQDN)으로만 나가는 트래픽을 허용합니다. Standard EKS는 Cilium, EKS Auto Mode는 `ApplicationNetworkPolicy`를 씁니다 | 모든 egress를 차단합니다(`egress: []`). ingress는 trainer pod의 TCP 8000만 허용합니다 |
| 노드 | Karpenter와 gVisor 전용 NodePool(AL2023 user data로 `runsc` 설치) | CDK 스택의 EKS 관리형 노드 그룹과 Karpenter NodePool |

- **`isolated-sandbox` 계층:** pod마다 EC2 Nitro Sandbox 위의 Firecracker microVM 하나에서 실행됩니다. EKS Auto Mode(Kubernetes 1.36 이상) 또는 custom AMI를 쓰는 Standard EKS가 필요합니다. 이 가이드의 [출처 페이지](../reference/sources.md) 기준으로 Nitro Sandboxes는 출시 시점에 GPU passthrough를 지원하지 않습니다.
- **Kata + Firecracker:** 페이지에 향후 계층으로 적혀 있고, 이 솔루션에는 포함되어 있지 않습니다.
- **고르는 기준:** GPU가 필요 없고 허용한 도메인으로만 외부에 접속해야 하는 에이전트 샌드박스라면 AI on EKS 솔루션을, 샌드박스 안에서 GPU로 커널을 채점해야 한다면 이 에셋을 참고하세요.

## 이 에셋의 Agent Sandbox 확장

이 에셋은 Agent Sandbox를 선택 확장으로 제공합니다. 샌드박스 서버, 이미지, 인증은 reward 풀과 같고, pod를 만들고 삭제하는 주체와 시점만 다릅니다. 확장 파일은 `k8s/extensions/agent-sandbox/`, `scripts/extensions/agent_sandbox.sh`, `src/gpusandbox/agent_sandbox.py`(`EpisodeSandbox`)에 있습니다.

## 적용 범위와 한계

- **검증 상태:** 이 에셋의 Agent Sandbox 확장은 로컬 테스트만 통과했습니다. 클러스터와 AWS에서는 실행하지 않았습니다.
- 설치, template 설정, warm pool, claim 명령과 `EpisodeSandbox` 사용법은 [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)에 있습니다.
- AI on EKS 솔루션의 내용은 2026-11에 공개 페이지를 읽고 정리한 것이며, 이 에셋에서 실행하지 않았습니다.

## 한 줄 정리

- single-turn 채점에서는 completion마다 유휴 pod 하나가 한 번 채점하고, 요청이 끝나면 상태를 삭제합니다.
- multi-turn 에이전트는 에피소드마다 샌드박스 하나를 claim해 모든 turn을 같은 GPU와 같은 버전에서 채점하고, 에피소드가 끝나면 claim을 삭제합니다. 격리는 RuntimeClass가 담당합니다.

## 다음 단계

- 에피소드마다 샌드박스를 claim해 multi-turn 에피소드를 직접 실행해 보려면 [11 multi-turn 에피소드 실습](../handson/11_multi_turn.md)으로 가세요.
- Agent Sandbox 확장의 설치 명령과 코드는 [06 Agent Sandbox로 확장](../concepts/06_agent_sandbox.md)에서 확인하세요.
- 다른 코스는 [학습 코스 고르기](../learning_paths.md)에서 고릅니다.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | Agent Sandbox (kubernetes-sigs/agent-sandbox) | https://github.com/kubernetes-sigs/agent-sandbox |
    | Agent Sandbox on EKS | https://awslabs.github.io/ai-on-eks/ko/docs/infra/agents/agent-sandbox |
    | EKS sandboxing 제한 사항 | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
    | Amazon EC2 온디맨드 요금 | https://aws.amazon.com/ec2/pricing/on-demand/ |
    | 이 저장소의 Agent Sandbox 확장 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/extensions/agent-sandbox |

    전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-beginner-06-multi-turn-agent)
