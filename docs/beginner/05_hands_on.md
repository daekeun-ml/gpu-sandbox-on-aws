# 05 직접 해 보기

일부러 틀린 답을 제출했는데 테스트 화면에 `PASSED`가 뜨면 성공일까요? 이번에는 **채점기가 답안을 제대로 구별하는지** 내 PC에서 확인합니다. AWS 계정이나 GPU 없이 진행합니다.

## 내 PC에서 바로 실행하기 { #1-설치하기 }

Git과 [uv](https://docs.astral.sh/uv/getting-started/installation/)를 준비하고 아래 명령을 실행하세요. 이미 코드를 내려받았다면 프로젝트 폴더에서 마지막 줄만 실행하면 됩니다.

```bash
git clone https://github.com/daekeun-ml/gpu-sandbox-on-aws.git
cd gpu-sandbox-on-aws
./scripts/quickstart.sh local
```

스크립트는 Python 환경을 준비하고 테스트를 실행합니다. 테스트는 내 PC에 CPU 채점 서버 두 개를 띄워 준비된 답안을 보내고, 끝나면 서버를 종료합니다. 마지막에 `1 passed`가 나오면 됩니다.

![틀린 답안을 보냈을 때 채점기가 돌려준 wrong_answer와 기대한 판정이 일치하는 예](../images/figures/beginner-05_hands_on--local-scoring.ko.svg?v=2)

??? note "설치 과정을 직접 따라가거나 테스트만 다시 실행하려면"
    [로컬 Python 환경 설정](../handson/start.md#2-로컬-python-환경)에서 운영체제별 설치 순서를 보세요. 설치 후에는 프로젝트 폴더에서 다음 명령으로 같은 테스트를 다시 실행합니다.

    ```bash
    source .venv/bin/activate
    python -m pytest -q tests/test_server_and_client.py::test_golden_probe_and_parity_on_cpu_pools
    ```

## 오답을 보냈는데 테스트가 통과한 이유 { #2-시험용-답을-채점하기 }

이 테스트에서 사용하는 `relu_bias`는 3편에서 본 덧셈 문제입니다. `[-3, 2]`에 `[1, 1]`을 더하면 `[-2, 3]`이고, 마지막에 음수를 0으로 바꾼 `[0, 3]`이 정답입니다. 어떤 코드가 마지막 단계를 빠뜨렸다면 채점기는 `wrong_answer`를 돌려줘야 합니다.

| 준비된 답안 | 테스트가 기대하는 판정 |
|---|---|
| 정확히 계산한 답안 | `ok` |
| 결과가 틀린 답안 | `wrong_answer` |
| 실행 시간을 측정할 때 결과가 달라지는 답안 | `wrong_answer` |
| 허용되지 않은 파일 접근을 시도하는 답안 | `policy_violation` (실행 전 거절) |

**`wrong_answer`는 제출한 코드의 결과이고, `PASSED`는 채점기를 검사한 결과입니다.** 아래 화면의 `1 passed`는 시험용 답안들이 예상한 판정을 받았고 두 서버도 일관된 결과를 냈다는 뜻입니다.

![로컬 CPU 채점기 테스트 한 개가 통과한 pytest 출력](../images/learning/local-cpu-grading.png)

<span id="서버-두-개-띄우기"></span><span id="시험용-답안-채점하기"></span>

??? note "macOS에서 답안별 출력을 보고 싶다면"
    서버 두 개를 서로 다른 포트에 띄우고 `probe`로 시험용 답안을 보내면 `PASS … status=wrong_answer`처럼 답안마다 한 줄씩 볼 수 있습니다. 위 기본 테스트에서는 `pytest`가 이 출력을 모아 확인합니다. [서버를 직접 띄우는 절차](../handson/start.md#4-loopback-smoke-run-macos)

## AWS에서 세 런타임 비교하기 (선택) { #aws-cpu }

여기서부터는 AWS 리소스 요금이 발생합니다. 내 PC에서 실행한 두 서버는 모두 같은 운영체제를 사용합니다. AWS에서는 2편에서 본 것처럼 한 `c8i.2xlarge` 노드에 gVisor와 두 가지 Kata를 띄워 각 환경에서 보이는 커널 버전을 확인합니다.

<span id="설정과-클러스터-준비"></span><span id="터널을-열고-노드-확인"></span>

1. [공통 절차 01의 C 탭](../handson/common/01_provision/index.md#__tabbed_1_4)을 따라 CPU 클러스터를 준비하세요. 기본 구성에는 Standard 온디맨드 vCPU 14개가 필요합니다. 두 번째 터미널의 터널을 열어 두고 `sandbox-kata` 역할의 `c8i.2xlarge`가 `Ready`인지 확인하세요.
2. [공통 절차 02의 C 탭](../handson/common/02_runtimes/index.md#__tabbed_1_4)에서 `scripts/kata/cpu_nodes.sh`를 실행하세요. 스크립트가 각 런타임에서 `uname -r`로 커널 버전을 확인합니다.

<span id="세-런타임의-출력-해석"></span>

아래 화면의 `gvisor-cpu`에는 `4.19.0-gvisor`, 두 Kata 줄에는 같은 게스트 버전 `6.18.56`이 보입니다. `host kernel`은 노드 자체의 커널입니다. 맨 아래 `runc`는 일반 컨테이너를 별도로 실행해서 비교한 줄입니다. [2편에서 결과 해설 보기](02_container_vs_sandbox.md)

![같은 CPU 노드에서 gVisor, Kata, 일반 컨테이너가 출력한 커널 버전](../images/learning/aws-runtime-kernels.png)

??? example "같은 노드에서 일반 컨테이너(runc)로도 확인하기"
    아래 pod에는 `runtimeClassName`이 없어 노드의 기본 런타임을 사용합니다. `kubectl logs`의 출력과 위의 `host kernel` 줄을 비교합니다.

    ```bash
    cat <<'EOF' | kubectl apply -f -
    apiVersion: v1
    kind: Pod
    metadata: {name: runc-smoke, namespace: default}
    spec:
      restartPolicy: Never
      automountServiceAccountToken: false
      nodeSelector: {gpusandbox/kata-gpu: "false"}
      tolerations: [{key: gpusandbox/role, operator: Equal, value: sandbox-kata, effect: NoSchedule}]
      containers:
        - name: smoke
          image: public.ecr.aws/amazonlinux/amazonlinux:2023
          command: ["/bin/sh", "-c", "echo kernel seen inside: $(uname -r) $(uname -v)"]
    EOF
    kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/runc-smoke --timeout=180s
    kubectl logs runc-smoke
    kubectl delete pod runc-smoke
    ```

### AWS 리소스 정리 { #실습-리소스-정리 }

계속하려면 이 클러스터에서 [CPU pool 배포와 버전 교체](../handson/scenarios/c/index.md)로 이어가세요. 여기서 마치려면 배포할 때 사용한 방식에 맞는 [실습 리소스 정리](../handson/cleanup.md) 절차를 따르세요.

다음 편에서는 에이전트가 오답 판정을 받아 같은 문제에 다시 도전합니다. [06 에이전트가 답을 고쳐 제출하는 과정](06_multi_turn_agent.md)
