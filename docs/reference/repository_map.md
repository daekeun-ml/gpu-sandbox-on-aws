# 프로젝트 구조

<a id="저장소-구조"></a>

실행할 명령은 [스크립트 레퍼런스](scripts.md)에서 확인하세요. 환경 변수는 [설정 값](configuration.md)에 정리했습니다. 아래 표에서 살펴보거나 바꾸려는 기능의 소스 파일을 찾으세요.

## 작업별 시작 위치

| 하려는 일 | 먼저 열어 볼 파일 |
|---|---|
| 샌드박스 요청이 어디서 처리되는지 보기 | [`server/app.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/server/app.py) |
| 정확성 검사와 속도 측정 바꾸기 | [`harness/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/src/gpusandbox/harness) |
| GRPO의 reward 계산과 로그 확인 | [`rewards.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py), [`rl/trl/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/rl/trl) |
| gateway가 요청을 pool에 배정하는 방식 보기 | [`gateway/app.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py), [`client/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/src/gpusandbox/client) |
| 런타임, 리소스, 채점 버전 바꾸기 | [`k8s/sandbox/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/sandbox) |
| AWS 노드와 클러스터 배치 바꾸기 | [`cdk/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/cdk), [`infra/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/infra) |
| multi-turn 에피소드 또는 데모 확인 | [`agent_sandbox.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/agent_sandbox.py), [`demo/`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/demo) |

## 설정값이 매니페스트에 반영되는 과정

<span id="값과-템플릿이-합쳐지는-흐름"></span>

`scripts/06_deploy_sandboxes.sh`는 `scripts/config.env`의 계정별 값, `k8s/sandbox/profiles/`의 런타임별 값, `k8s/sandbox/versions/`의 버전별 값을 읽습니다. `scripts/render.py`가 이 값으로 템플릿을 채우면 배포 스크립트가 완성된 매니페스트를 `kubectl apply`에 전달합니다. CDK 경로에서는 `cdk/deploy.sh`가 같은 `config.env`를 읽어 VPC와 EKS 클러스터를 배포합니다.

## 평가 요청을 따라 읽는 순서

1. `rl/trl/train_grpo.py`가 답을 생성하고, `src/gpusandbox/rewards.py`가 채점 결과를 reward로 바꿉니다. 분산 학습을 시작하는 코드는 `rl/verl/`에 있습니다.
2. `src/gpusandbox/client/`의 클라이언트가 라우팅 설정을 읽습니다. 운영 구성에서는 `src/gpusandbox/gateway/app.py`가 pool과 버전을 고릅니다.
3. `src/gpusandbox/server/app.py`가 평가 요청을 받고, `harness/evaluate.py`가 `harness/runner.py`를 별도 프로세스에서 시작해 제출된 코드를 실행합니다. `evaluate.py`가 기준 결과와 비교해 verdict를 반환합니다.

## 테스트 { #tests }

`tests/`는 AWS 없이 실행하는 테스트입니다. 로컬 채점은 `test_harness_cpu.py`와 `test_server_and_client.py`, 버전 전환과 reward는 `test_routing_and_rewards.py`, 매니페스트는 `test_manifests.py`부터 보세요. CDK 스택 테스트는 `cdk/tests/`에 있습니다.

문서 원본은 `docs/`에 있고 메뉴 순서는 `mkdocs.yml`에서 정합니다. 루트의 `SCRIPTS.md`는 [스크립트 레퍼런스](scripts.md)를 고친 뒤 `python3 tools/sync_scripts_md.py`로 갱신합니다.
