# 09 데모 사이트 (CloudFront)

**TL;DR** 클러스터의 실행 기록(JSON)을 재생하는 정적 데모를 private S3 버킷과 CloudFront로 공개합니다. 방문자는 클러스터나 GPU에 접근할 수 없어요.

## 기존 Pain Point

방문자 입력을 GPU 샌드박스로 보내는 라이브 데모는 신뢰할 수 없는 코드를 실행하는 경로를 인터넷에 노출합니다. 또 GPU 노드를 켜 두면 요금이 계속 발생하고, 노드를 줄이면 데모가 동작하지 않아요. 정적 호스팅에서도 버킷을 공개하거나 S3 website endpoint(OAC 불가, CloudFront 문서 기준)를 쓰면 CloudFront를 우회하는 경로가 생깁니다. 기록에 들어 있는 오류 메시지와 정책 위반 내용은 평가된 코드가 만든 문자열입니다. 이 문자열을 HTML로 삽입하면 그 안의 스크립트가 실행됩니다.

![두 패널 그림입니다. a: 라이브 데모에서는 방문자가 인터넷에 열린 API를 통해 GPU 샌드박스를 호출하고, 이 샌드박스는 켜 둔 동안 계속 과금됩니다. 공개 버킷이나 website endpoint를 쓰면 방문자가 CloudFront를 거치지 않고 S3 버킷에 직접 접근합니다. 기록 속 오류 메시지와 정책 위반 문자열을 HTML로 넣으면 데모 페이지에서 스크립트로 실행됩니다. b: 기록 재생 방식에서는 방문자가 CloudFront까지만 접근하고, GPU 샌드박스는 기록을 만들 때만 필요합니다. OAC와 AWS:SourceArn 조건 때문에 버킷에 직접 접근하면 403이 반환됩니다. 기록의 문자열은 텍스트로만 삽입하고, CSP는 자기 origin만 허용합니다.](../images/figures/handson-09_demo_site.svg)

*그림 요약: 라이브 데모에서는 방문자가 GPU 샌드박스를 직접 호출하고, 잘못 설정한 정적 호스팅에서는 CloudFront 우회와 기록 문자열의 스크립트 실행이 가능합니다. 기록 재생, OAC와 AWS:SourceArn, 텍스트로만 삽입하는 방식이 이 세 경로를 각각 차단합니다.*


## Why

- **기록을 재생합니다.** 방문자의 요청은 CloudFront까지만 전달되고, 클러스터와 GPU는 기록을 만들 때만 필요해요.
- **버킷은 비공개로 두고 이 CloudFront 배포만 읽을 수 있게 합니다.** 버킷 정책에 OAC와 `AWS:SourceArn` 조건을 설정하고, `deploy.sh`가 버킷에 직접 접근하면 403이 반환되는지 확인해요.
- **브라우저에서 실행되는 내용도 제한합니다.** CSP는 같은 origin의 스크립트, 스타일, 연결만 허용합니다. 페이지는 기록의 문자열을 텍스트로만 삽입해요.

**사전 지식:** 로컬 Python 환경([시작하기](../getting_started.md) 2장)이 필요합니다. GPU 기록에는 [04](04_sandbox_pools.md)에서 배포한 풀이 필요하고, 3절(학습 이벤트)까지 채우려면 [05](05_grpo_training.md), [06](06_sandbox_update.md)의 학습도 필요합니다. verdict와 reward의 의미는 [03 On-policy RL과 샌드박스](../concepts/03_onpolicy_rl_with_sandboxes.md)에 있어요.

??? note "용어 (처음 보는 단어가 있으면 펼치세요)"
    - **정적 사이트**: 서버 쪽 코드 없이 HTML, CSS, JavaScript 파일만 제공하는 사이트입니다.
    - **Amazon CloudFront**: 전 세계 edge location에서 파일을 캐시해 제공하는 CDN입니다. 배포(distribution) 하나가 도메인 하나를 담당합니다.
    - **OAC (Origin Access Control)**: CloudFront가 S3에 서명된 요청을 보내는 방식입니다. 버킷을 공개하지 않고 CloudFront만 버킷을 읽도록 설정할 수 있어요.
    - **S3 Block Public Access**: 버킷 정책이나 ACL로 버킷이 공개되는 것을 막는 설정 네 가지입니다.
    - **service principal**: AWS 서비스가 권한 주체로 쓰는 이름입니다. CloudFront는 `cloudfront.amazonaws.com`입니다.
    - **`AWS:SourceArn`**: 요청을 보낸 AWS 리소스의 ARN을 조건으로 거는 정책 키입니다. 여기서는 이 CloudFront 배포가 보낸 요청만 허용하는 조건으로 씁니다.
    - **CSP (Content-Security-Policy)**: 페이지가 어디서 스크립트, 스타일, 데이터를 불러올 수 있는지 브라우저에 알려 주는 응답 헤더입니다.
    - **HSTS (Strict-Transport-Security)**: 브라우저가 정해진 기간 동안 그 도메인에 HTTPS로만 접속하게 하는 응답 헤더입니다.
    - **ACM (AWS Certificate Manager)**: TLS 인증서를 발급하고 관리하는 서비스입니다.
    - **invalidation**: CloudFront 캐시를 지워 새 파일을 제공하게 하는 요청입니다.
    - **golden**: 기대 verdict가 미리 정해진 시험용 제출물입니다.

    더 자세한 설명은 [용어 사전](../reference/glossary.md)에 있습니다.

## 데모가 보여 주는 것

| 절 | 보여 주는 것 | 기록의 출처 |
|---|---|---|
| 1. 격리 런타임과 증거 | 풀마다 샌드박스 안에서 확인한 커널 버전, GPU 이름, egress 차단 여부. gVisor는 자체 커널 버전을, Kata는 guest VM의 커널 버전을 보고합니다 | 풀마다 첫 Ready pod의 `/info` |
| 2. 제출물 채점 재생 | golden 제출물(정답, 오답, 벤치마크가 시작되면 틀리는 코드, 호스트 파일 읽기 등)을 선택하면 풀마다 verdict와 reward 구성 요소(format, correctness, speedup, 합계) | golden 평가 결과와, trainer와 같은 `score_verdict`로 계산한 reward |
| 3. 학습 중 샌드박스 업데이트 | reward 배치마다 채점한 샌드박스 버전과 통과율, 버전 전환 시점 | `--training-events`로 지정한 `sandbox_metrics.jsonl` |

공개되는 것은 HTML, CSS, JavaScript와 완료된 실행의 기록 JSON 하나뿐입니다. 저장소의 샘플은 노트북의 CPU 풀에서 만든 기록이니, 클러스터에서 만든 GPU 기록으로 교체해 쓰세요.

```mermaid
flowchart LR
    V["방문자 브라우저"] -->|"HTTPS (HTTP는 HTTPS로 redirect)<br/>GET, HEAD만"| CF["CloudFront 배포 + AWS WAF web ACL<br/>응답 헤더 정책<br/>CSP, HSTS, nosniff, frame DENY"]
    CF -->|"OAC (SigV4 서명 요청)"| S3["private S3 버킷<br/>Block Public Access 4개, SSE-S3"]
    V -.->|"버킷 직접 접근은 403"| S3
    CF -.->|"표준 로깅 v2"| LOG["private 로그 버킷<br/>90일 만료, 스택 삭제 뒤에도 유지"]
    S3 -.->|"S3 서버 액세스 로그"| LOG
    OP["운영자 워크스테이션<br/>demo/deploy.sh"] -->|"정적 파일과 recording.json 업로드"| S3
    K["EKS 클러스터와 GPU 샌드박스"] -.->|"기록을 만들 때만 (record)"| OP
```

*그림 요약: 방문자의 요청은 CloudFront에서 끝나고, 클러스터와 GPU는 운영자가 기록을 만들 때만 쓰입니다.*

## 소요 시간과 비용

- **로컬 미리보기와 샘플 재생성**은 AWS 비용이 들지 않습니다.
- **배포** 시간은 대부분 스택 생성과 CloudFront 전파를 기다리는 시간입니다. 스크립트가 200 응답을 기다리는 시간은 최대 약 10분입니다(4절 7번 단계). 실제 소요 시간은 측정하지 않았어요.
- **사이트 비용**: 작은 정적 사이트의 비용은 보통 크지 않지만 트래픽에 따라 달라지므로 [CloudFront 요금](https://aws.amazon.com/cloudfront/pricing/)과 [S3 요금](https://aws.amazon.com/s3/pricing/)을 확인하세요.
- **WAF 비용**: web ACL 월 약 5 USD, 규칙마다 월 1 USD(규칙 4개), 요청 100만 건마다 0.60 USD입니다([AWS WAF 요금](https://aws.amazon.com/waf/pricing/)). 스택이 있는 동안은 트래픽이 없어도 고정 비용(월 약 9 USD)이 나와요.
- **로그 비용**: 로그 버킷의 S3 저장 요금만 듭니다. 객체는 90일 뒤 만료되고, 버킷은 정리 뒤에도 남습니다(6절).
- **GPU 기록 비용**: 기록하는 동안 GPU 샌드박스 노드가 실행 중이어야 합니다(`g5.2xlarge` 시간당 1.212 USD, `g5.xlarge` 1.006 USD, `g4dn.metal` 7.824 USD, us-east-1과 us-west-2 온디맨드 요금). recorder pod는 system 노드에서 GPU 없이 실행되고, trainer pod로 기록하면 trainer 노드도 실행 중이어야 합니다. 기록을 만든 뒤에는 [99 정리](99_cleanup.md)에 따라 GPU 노드를 줄이세요.

## 1. 로컬에서 미리 보기

저장소 루트에서 실행합니다. 서버가 loopback 주소에만 bind하므로 다른 컴퓨터에서는 접속할 수 없어요.

```bash
# Serve demo/site on loopback only (Ctrl-C stops it)
python3 -m http.server 8080 --bind 127.0.0.1 -d demo/site
```

브라우저에서 http://127.0.0.1:8080 을 엽니다. 파일을 직접 열면(`file://`) 브라우저가 `fetch`를 차단해 기록을 불러오지 못할 수 있어요.

**확인할 것:**

- 제목 "GPU Sandbox on AWS 재생 데모" 아래 "기록 출처:" 줄에 `Local CPU smoke run on a laptop (127.0.0.1, no gVisor or Kata, no GPU).`로 시작하는 문구와 기록 시각이 보입니다.
- 1절에 `local-cpu v1`, `local-cpu v2` 카드 두 개가 있고, GPU는 "없음 (CPU)", egress 차단은 "확인됨"입니다.
- 2절의 제출물 목록에 `relu_bias_torch_only`, `relu_bias_wrong`, `relu_bias_benchmark_cheat`, `read_host_file` 네 개가 있습니다.
- 3절에 reward 배치 6개와, step 4에서 `local-cpu/v1`이 `local-cpu/v2`로 바뀌는 버전 전환 줄이 보입니다.
- 오른쪽 위 `EN` 버튼을 누르면 영어 화면으로 바뀝니다. 터미널에는 파일마다 200 응답 로그가 출력돼요.

**문제가 생기면:** `Address already in use`가 나오면 다른 포트(예: `8081`)로 실행하고 브라우저에서도 그 포트의 주소를 여세요. "기록 출처" 자리에 `failed to load recording:`이 나오면 `demo/site/data/recording.json`이 있는지, 올바른 JSON인지 확인하세요. 그 밖의 경우에는 [문제 해결](../reference/troubleshooting.md)을 보세요.

## 2. 클러스터에서 GPU 기록 만들기

`python -m gpusandbox.tools record`는 풀마다 다음 정보를 모아 JSON 파일 하나에 저장합니다.

- 첫 Ready pod의 `/info`: runtime, 샌드박스 버전, 커널 버전, GPU 이름, egress 차단 여부
- golden set의 verdict(`--device cuda`면 6개): status, correct, custom_kernel, speedup, 기준과 후보의 ms, flags, 정책 위반(최대 3개), 오류(끝 400자), 소요 시간, 버전
- trainer와 같은 `score_verdict`로 계산한 reward 구성 요소
- `--training-events`를 주면 그 파일의 `reward_batch`, `sandbox_version_switch` 이벤트

pod IP, endpoint 주소, 토큰은 기록에 넣지 않습니다(`record`가 저장하는 필드 목록 기준). 이 명령은 클러스터 안에서, 다음 조건을 모두 갖춘 pod에서 실행해야 해요.

| 조건 | 이유 |
|---|---|
| `rl-trainer` 네임스페이스와 label `gpusandbox/client: "true"` | 샌드박스의 NetworkPolicy가 이 pod의 연결만 허용합니다 |
| audience `gpu-sandbox`인 projected token과 `SANDBOX_TOKEN_FILE` | 샌드박스 API 인증 |
| 허용 목록에 있는 ServiceAccount (`grpo-trainer` 또는 `sandbox-probe`) | 샌드박스가 토큰의 subject를 확인합니다 |
| torch와 httpx가 있는 이미지 | `record`는 태스크 설명과 기준 구현을 기록에 넣기 위해 태스크 모듈을 불러오고, 태스크 모듈은 torch를 import합니다 |

네 조건을 갖춘 pod는 두 가지입니다.

| pod | 쓰는 경우 | 3절 (학습 이벤트) |
|---|---|---|
| recorder pod (`demo/recorder-pod.yaml.tpl`) | 실행 중인 학습 Job 없이 기록할 때 | 비어 있음 |
| 학습 중인 trainer pod | 학습 이벤트까지 기록할 때. 이벤트 파일 `/outputs/grpo/sandbox_metrics.jsonl`이 이 pod 안에 있음 | 채워짐 |

recorder pod는 trainer 이미지(`rl-trainer`)로 `sleep`만 실행하는 pod입니다. label `gpusandbox/client: "true"`, ServiceAccount `grpo-trainer`, audience `gpu-sandbox`인 projected token, Pod Security restricted(uid 2000) 설정을 갖추고, GPU 없이 system 노드에서 실행돼요. golden set은 샌드박스 풀에서 실행됩니다.

??? info "probe Job 템플릿(`k8s/probe/job-probe.yaml.tpl`)으로 기록하지 않는 이유"
    probe Job은 `rl-trainer` 네임스페이스, client label, audience 토큰 조건은 갖췄지만, 기록 파일을 만들거나 밖으로 복사할 수 없습니다.

    - control 이미지(`gateway/Dockerfile`, `python:3.14-slim` 기반)에는 torch가 없습니다. 로컬 환경에서 torch import를 차단하고 실행하자 같은 코드 경로가 `get_task`의 `ModuleNotFoundError`로 실패했어요.
    - root filesystem이 읽기 전용이고 쓸 수 있는 볼륨이 없어 `--out` 파일을 저장할 위치가 없습니다.
    - `kubectl cp`는 실행 중인 컨테이너 안의 `tar`를 사용합니다. Job이 끝나면 pod가 종료되므로 파일을 복사할 수 없습니다.

    `probe`, `parity`, `bench`는 태스크 모듈을 불러오지 않으므로 control 이미지에서 그대로 실행됩니다.

### 2.1 기록할 시점 고르기

- **학습 Job이 없으면 recorder pod로 기록합니다(2.2).** 이때 기록에 학습 이벤트가 들어가지 않아, 3절에 "이 기록에는 학습 이벤트가 없습니다."가 표시됩니다.
- **trainer pod로 기록할 때는 학습 Job이 Running인 동안 실행합니다.** Job이 끝나면 컨테이너가 종료되어 emptyDir에 있는 이벤트 파일을 복사할 수 없어요([05 On-policy GRPO 학습](05_grpo_training.md)).
- **3절에 버전 전환을 표시하려면** [06](06_sandbox_update.md)의 `scripts/ops/rollout.sh gvisor v1 v2`로 routing을 바꾼 뒤, `--finish`로 v1을 줄이기 전에 기록하세요. 그래야 v1과 v2 풀이 모두 기록에 포함됩니다.
- **학습이 잠깐 느려질 수 있습니다.** 기록과 학습이 같은 풀을 쓰고 pod는 한 번에 평가를 하나만 처리하므로, golden 평가가 reward 평가 사이에 추가로 실행됩니다.

### 2.2 trainer pod 찾기

실행 중인 trainer pod의 이름을 변수에 저장합니다.

```bash
# Name of the running trainer pod (scenarios A and B both label it app=grpo-trainer)
POD="$(kubectl -n rl-trainer get pods -l app=grpo-trainer \
  --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}')"
echo "${POD}"
```

**확인할 것:** pod 이름 한 줄이 출력됩니다(시나리오 A에서는 `grpo-<RUN_ID>-<접미사>` 형태). 비어 있으면 학습이 실행 중이 아닌 것이니 [05](05_grpo_training.md)부터 실행하거나, 아래 recorder pod를 쓰세요.

**학습 Job 없이 기록하려면** recorder pod를 만듭니다. `scripts/config.env`의 `TRAINER_IMAGE_URI`와 `SANDBOX_AUDIENCE`로 템플릿을 렌더링해요.

```bash
# Recorder pod: trainer image, client label, grpo-trainer ServiceAccount, no GPU (runs on a system node)
source scripts/config.env
python3 scripts/render.py demo/recorder-pod.yaml.tpl | kubectl apply -f -
kubectl -n rl-trainer wait --for=condition=Ready pod/demo-recorder --timeout=10m
POD=demo-recorder
```

**확인할 것:** `pod/demo-recorder created`와 `pod/demo-recorder condition met`이 나옵니다. recorder pod의 컨테이너 이름은 `recorder`이므로 2.3과 2.4의 `-c trainer`를 `-c recorder`로 바꾸고, 2.3에서 `--training-events` 줄을 빼세요. pod는 3시간(`sleep 10800`) 뒤 종료되며, 기록을 복사한 뒤 `kubectl -n rl-trainer delete pod demo-recorder`로 지웁니다.

### 2.3 trainer pod 안에서 record 실행

GPU 풀마다 golden set을 실행하고 결과를 pod의 `/tmp/rec.json`에 저장합니다. `--pool`은 `라벨=주소` 형식이며, 라벨은 페이지의 카드 제목으로 그대로 쓰여요.

```bash
# Run the golden set on each GPU pool and write the recording inside the trainer pod.
# Container name: trainer in scenario A, pytorch in scenario B (HyperPod).
kubectl -n rl-trainer exec "${POD}" -c trainer --\
  python -m gpusandbox.tools record \
  --pool gvisor=sandbox-gvisor-v1.sandbox.svc.cluster.local:8000 \
  --pool kata-qemu=sandbox-kata-qemu-v1.sandbox.svc.cluster.local:8000 \
  --device cuda \
  --source "EKS us-west-2, gVisor on g5.xlarge (A10G), Kata QEMU on g4dn.metal (T4)" \
  --training-events /outputs/grpo/sandbox_metrics.jsonl \
  --out /tmp/rec.json
```

- 첫 줄 끝의 `--\`는 kubectl 인자 구분자 `--` 뒤에서 줄을 이은 표기입니다([문제 해결](../reference/troubleshooting.md)과 같은 방식).
- **배포한 풀만 넣으세요.** Ready pod가 없는 주소를 넣으면 golden마다 최대 600초(클라이언트의 acquire timeout)를 기다린 뒤 `sandbox_error`로 기록됩니다. `/info`도 비어 있어서 페이지에 egress가 "열림"으로 표시됩니다.
- **v1과 v2를 함께 넣으려면** 라벨에 버전을 붙입니다. 예: `--pool "gvisor v1=sandbox-gvisor-v1.sandbox.svc.cluster.local:8000" --pool "gvisor v2=sandbox-gvisor-v2.sandbox.svc.cluster.local:8000"`.
- **`--source`는 "기록 출처" 줄에 그대로 나옵니다.** 리전, 인스턴스, 날짜 같은 기록 조건을 적으세요.

**확인할 것:** 마지막 줄에 다음과 같은 JSON이 나옵니다. `training_events`는 그 시점까지 기록된 배치 수에 따라 달라요. recorder pod에서는 `training_events`가 0입니다(2026-11-18 기록: `goldens: 6`, `training_events: 0`).

```text
{"event": "recorded", "out": "/tmp/rec.json", "pools": ["gvisor", "kata-qemu"], "goldens": 6, "training_events": <N>}
```

**문제가 생기면:** `HTTP 401`이나 `HTTP 403`이 포함된 `sandbox_error`는 토큰이나 허용 목록 설정 때문에 생깁니다. [문제 해결](../reference/troubleshooting.md)의 "401, 403 응답" 항목을 보세요. 연결 자체가 되지 않으면 같은 페이지의 "NetworkPolicy" 항목을 보세요.

### 2.4 기록 파일 복사하기

기록 파일을 워크스테이션으로 복사하고, `deploy.sh`와 같은 스키마 검사를 실행합니다.

```bash
# Copy the recording to your workstation (kubectl cp runs tar inside the container)
# Recorder pod: use -c recorder instead of -c trainer
kubectl -n rl-trainer cp -c trainer "${POD}:/tmp/rec.json" /tmp/rec.json
# The same schema check that deploy.sh runs first
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['schema'] == 1 and d['pools']" /tmp/rec.json
```

**확인할 것:** `kubectl cp`가 `tar` 경고를 한 줄 출력할 수 있지만 복사는 정상적으로 됩니다. 스키마 검사는 아무것도 출력하지 않고 종료 코드 0으로 끝나요.

### 2.5 공개하기 전에 검토하기

페이지는 기록을 그대로 보여 주므로 공개 전에 다음을 확인하세요.

| 항목 | 확인할 것 |
|---|---|
| `source` | 직접 쓴 설명입니다. 계정 정보나 사람 이름이 들어 있지 않은지 |
| `pools[].info.egress_blocked` | 모든 풀이 `true`인지. 값이 없거나 `false`면 페이지에 "열림"으로 나옵니다. 그대로 공개하지 말고 풀부터 고치세요 |
| `pools[].results[].status`와 `expected_status` | golden마다 같은지. 다르면 verdict가 기대값과 다른 것이니 [04](04_sandbox_pools.md)의 풀 검증(`scripts/ops/verify.sh`)으로 원인부터 찾습니다 |
| `pools[].results[].error`, `violations` | 평가된 코드가 만든 문자열(오류 끝 400자, 위반 최대 3개)입니다. 내부 경로나 호스트 이름이 들어 있지 않은지 |
| `training` | `reward_batch`와 `sandbox_version_switch` 이벤트만 들어갑니다. 버전 이름과 routing revision을 공개해도 되는지 |

다음 스크립트가 요약을 출력합니다.

```bash
python3 - /tmp/rec.json <<'PY'
import json, sys
rec = json.load(open(sys.argv[1]))
print("source:", rec["source"])
for pool in rec["pools"]:
    info = pool["info"]
    print(pool["runtime"], "egress_blocked:", info.get("egress_blocked"), "gpu:", info.get("gpu"))
    for name, v in pool["results"].items():
        mark = "as expected" if v["status"] == v["expected_status"] else "DIFFERS FROM EXPECTED"
        print("   ", name, v["status"], mark)
print("training events:", len(rec["training"]))
PY
```

**확인할 것:** 풀마다 `egress_blocked: True`이고, golden 줄이 모두 `as expected`입니다. 2026-11-18 기록에서는 두 풀 모두 `egress_blocked: True`였고, verdict 12개가 모두 `expected_status`와 같았으며, 파일에 IP, 계정 ID, 호스트 이름이 없었습니다. 저장소의 샘플 기록으로 실행하면 `local-cpu v1`, `local-cpu v2`와 golden 4개씩, `training events: 7`이 나와요(로컬 확인).

브라우저로 확인하려면 사이트를 임시 폴더에 복사한 뒤 로컬 서버로 실행합니다.

```bash
# Preview your recording without overwriting the shipped sample
mkdir -p /tmp/demo-preview && cp -R demo/site/. /tmp/demo-preview/
cp /tmp/rec.json /tmp/demo-preview/data/recording.json
python3 -m http.server 8080 --bind 127.0.0.1 -d /tmp/demo-preview
```

## 3. 샘플 기록 다시 만들기 (로컬, AWS 없음)

샘플 `demo/site/data/recording.json`을 GPU 없이 노트북에서 다시 만듭니다.

```bash
# Regenerate the shipped sample (run from the repo root inside the local venv)
python demo/record_local.py
```

스크립트는 다음 작업을 실행합니다.

- `127.0.0.1`에 CPU 샌드박스 서버 두 개(v1, v2)를 띄웁니다. v2 harness는 seed 5개와 speedup 상한 10배를 쓰고, 인증에는 loopback 전용 test bypass를 씁니다.
- 클러스터와 같은 코드 경로로 golden set(CPU에서는 4개)을 두 서버에 보냅니다.
- 모델 completion 대신 golden 제출물을 써서 reward 배치 6개를 `KernelRewards`로 계산하고, 3번째 배치 뒤에 routing을 v1에서 v2로 바꿉니다.
- 결과를 `demo/site/data/recording.json`(기본 `--out`)에 저장합니다. 출처 문구 "Local CPU smoke run on a laptop"으로 노트북에서 만든 기록임을 표시합니다.

**확인할 것:** 배치마다 `{"event": "reward_batch", ...}` 줄이 나오고, 마지막 줄은 다음과 같습니다(로컬 macOS에서 확인).

```text
{"event": "recorded", "out": "demo/site/data/recording.json", "pools": ["local-cpu v1", "local-cpu v2"], "goldens": 4, "training_events": 7}
```

다시 만든 뒤에는 `python -m pytest -q tests/test_demo.py`로 스키마와 reward 일관성을 확인하세요.

!!! warning "Linux 호스트에서는 컨테이너 안에서 실행하세요"
    `record_local.py`가 같은 프로세스 안에서 실행하는 샌드박스 서버는 평가마다 `/proc`에 보이는 프로세스 중 자신과 조상 프로세스를 제외한 모든 프로세스에 SIGKILL을 보냅니다. 그래서 Linux 호스트에서는 같은 사용자의 다른 프로세스까지 종료될 수 있습니다([시작하기](../getting_started.md)의 경고와 같은 이유). 별도 PID namespace를 쓰는 컨테이너에서 실행하세요. `/proc`가 없는 macOS에서는 이 동작이 꺼집니다.

**문제가 생기면:** `ModuleNotFoundError`가 나오면 가상 환경을 활성화하지 않았거나 패키지 설치를 빠뜨린 것이니 [시작하기](../getting_started.md) 2장을 다시 실행하세요.

## 4. 배포 (demo/deploy.sh)

`demo/deploy.sh`는 CloudFormation 스택 하나(사이트 버킷, 로그 버킷, OAC, 응답 헤더 정책, WAF web ACL, CloudFront 배포와 로그 전송, 버킷 정책)를 만들고 정적 파일과 기록을 업로드한 뒤 공개 상태를 확인합니다.

```bash
# Publish the shipped sample recording (always us-east-1)
demo/deploy.sh
# Publish your GPU recording instead
RECORDING=/tmp/rec.json demo/deploy.sh
```

**리전은 us-east-1로 고정됩니다.** CloudFront용 WAF web ACL과 CloudFront 로그 전송이 us-east-1 리소스이기 때문이에요. 스크립트는 `AWS_REGION`과 `scripts/config.env`를 읽지 않고, 템플릿의 `Rules`도 다른 리전의 배포를 거부합니다(`Deploy the demo stack in us-east-1 ...`). 클러스터가 다른 리전에 있어도 됩니다(2026-11-18에는 클러스터 us-west-2, 데모 us-east-1). CloudFormation, S3, CloudFront, AWS WAF, CloudWatch Logs(로그 전송) 리소스를 만들 권한이 필요합니다. 공유 계정이나 production 계정이라면 데모 전용 계정이나 최소 권한 역할을 쓰는 편이 안전합니다.

| 변수 | 기본값 | 의미 |
|---|---|---|
| 리전 | `us-east-1` (고정) | 스택, 버킷, WAF web ACL을 만드는 리전. `AWS_REGION`은 무시합니다 |
| `RECORDING` | `demo/site/data/recording.json` | 업로드할 기록. S3에는 `data/recording.json`으로 업로드됩니다 |
| `DEMO_STACK_NAME` | `gpu-sandbox-demo` | CloudFormation 스택 이름 |
| `DEMO_DOMAIN`, `DEMO_CERT_ARN` | 비어 있음 | custom domain과 us-east-1의 ACM 인증서. 둘 다 있어야 적용됩니다 |

| 순서 | 스크립트 동작 |
|---|---|
| 1 | 기록을 검사합니다(`schema`가 1이고 `pools`가 비어 있지 않음) |
| 2 | `aws cloudformation deploy`로 `demo/infra/site.yaml`을 us-east-1에 배포합니다(바뀐 것이 없어도 실패하지 않음) |
| 3 | 스택 출력 `BucketName`, `DistributionId`, `DistributionDomainName`을 읽습니다 |
| 4 | `demo/site`를 `aws s3 sync --delete`로 버킷에 업로드하고(`data/*` 제외), 기록을 `data/recording.json`으로 업로드합니다(`application/json`, `no-cache`) |
| 5 | CloudFront invalidation(`/*`)을 만들고, 배포의 `WebACLId`가 WAF web ACL ARN인지 확인합니다. 아니면 오류를 내고 멈춥니다 |
| 6 | `https://<bucket>.s3.us-east-1.amazonaws.com/index.html`에 익명 요청을 보내고, 응답이 403이 아니면 오류를 내고 멈춥니다 |
| 7 | 공개 URL이 200을 반환할 때까지 20초 간격으로 최대 30번 확인합니다. 그 뒤 응답에 CSP와 HSTS 헤더가 없거나, `http://` 요청이 301을 반환하지 않으면 오류를 내고 멈춥니다 |
| 8 | `[demo] live: <URL>`을 출력합니다 |

**확인할 것:** 다음 줄이 순서대로 나옵니다. 그 사이에 AWS CLI 출력도 함께 나옵니다.

```text
[demo] deploying stack gpu-sandbox-demo in us-east-1
[demo] uploading site to s3://<bucket>
[demo] checking that the distribution has the WAF web ACL
[demo] checking that the bucket itself is not readable anonymously
[demo] checking the public URL and its security headers (the distribution may take minutes)
[demo] live: https://<id>.cloudfront.net/
```

7번 단계는 정해진 횟수만큼 확인하는 동안 200 응답이 오지 않아도 헤더 검사로 넘어갑니다. 그러니 마지막에 출력된 URL을 브라우저로 열어 페이지를 직접 확인하세요.

**문제가 생기면:**

- `no WAF web ACL on <distribution>. Fix before sharing.`: 배포에 web ACL이 연결되지 않았습니다. 스택 이벤트에서 `WebAcl` 리소스를 확인하고, 고칠 때까지 URL을 공유하지 마세요.
- `direct S3 access returned <code>, expected 403`: 버킷 정책이나 Block Public Access 설정이 바뀌었는지 확인하고, 설정을 고칠 때까지 URL을 공유하지 마세요.
- `CSP header missing` 또는 `HSTS header missing`: 배포가 아직 전파되는 중일 수 있으니 몇 분 뒤 같은 명령을 다시 실행하세요. 다시 실행해도 안전합니다.
- `http:// returned <code>, expected a 301 redirect to https`: 배포의 `ViewerProtocolPolicy`가 `redirect-to-https`인지 확인하세요. 전파 중이라면 몇 분 뒤 다시 실행합니다.
- 스택 생성 실패: `aws cloudformation describe-stack-events --region us-east-1 --stack-name gpu-sandbox-demo`로 실패한 리소스와 이유를 확인합니다. 정리와 비용 문제는 [문제 해결](../reference/troubleshooting.md)의 "정리와 비용" 항목에 있어요.

## 5. custom domain (선택)

기본 `*.cloudfront.net` 인증서를 쓰면 viewer security policy가 TLSv1로 고정되고 더 높은 버전으로 바꿀 수 없습니다(CloudFront 문서 기준). 2026-11-18 배포의 기본 도메인도 TLS 1.0과 1.1 handshake를 받아들였어요(TLS 1.2와 1.3도 제공). TLS 1.2 이상의 연결만 허용하려면 custom domain과 ACM 인증서를 쓰세요. 두 값을 모두 지정하면 템플릿이 `sni-only`와 `TLSv1.2_2021`을 적용합니다.

```bash
# Custom domain with an ACM certificate in us-east-1 (required by CloudFront)
DEMO_DOMAIN=demo.example.com \
DEMO_CERT_ARN=arn:aws:acm:us-east-1:<account-id>:certificate/<certificate-id> \
demo/deploy.sh
```

- **인증서는 us-east-1에 있어야 합니다.** US East (N. Virginia)에서 요청하거나 가져온 ACM 인증서여야 하고, SAN이 `DEMO_DOMAIN`을 포괄해야 해요(CloudFront 문서 기준).
- **DNS 레코드는 직접 만듭니다.** `DEMO_DOMAIN`을 스택 출력의 `DistributionDomainName`으로 연결하는 CNAME(또는 Route 53 alias)이 없으면 7번 단계의 헤더 검사가 실패합니다. 레코드를 만든 뒤 같은 명령을 다시 실행하세요.
- **전용 하위 도메인을 쓰세요(예: `demo.example.com`).** 이 템플릿의 HSTS는 `max-age`가 2년(63072000초)이고 `includeSubDomains`를 포함합니다. 그래서 apex 도메인(`example.com`)에 적용하면 모든 하위 도메인에 2년 동안 HTTPS가 강제됩니다.

스택 출력은 다음 명령으로 확인합니다.

```bash
aws cloudformation describe-stacks --region us-east-1 --stack-name gpu-sandbox-demo \
  --query "Stacks[0].Outputs" --output table
```

**확인할 것:** `BucketName`, `DistributionId`, `DistributionDomainName`, `LogBucketName`, `WebAclArn` 다섯 행이 나옵니다.

## 보안 설계

설정은 [`demo/infra/site.yaml`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/demo/infra/site.yaml)과 [`demo/site`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/demo/site)에 있습니다.

| 계층 | 설정 | 방지하는 것 |
|---|---|---|
| 버킷 | Block Public Access 네 가지(`BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets`)를 모두 켬 | 버킷이나 객체가 정책이나 ACL로 공개되는 것 |
| 버킷 | Object Ownership `BucketOwnerEnforced` (ACL 비활성) | ACL을 통해 의도하지 않은 권한이 부여되는 경로. OAC 문서가 권장하는 설정입니다 |
| 버킷 | SSE-S3(`AES256`) 기본 암호화 | 저장된 객체가 암호화되지 않은 채 남는 것 |
| 버킷 정책 | `s3:GetObject`를 `cloudfront.amazonaws.com`에만 허용하고, `AWS:SourceArn`이 이 배포의 ARN일 때만 허용 | 다른 CloudFront 배포(다른 계정의 배포 포함)가 이 버킷을 읽는 것 |
| 버킷 정책 | `aws:SecureTransport`가 `false`인 모든 `s3:*` 요청 거부 | 평문 HTTP로 버킷에 접근하는 것 |
| OAC | `SigningBehavior: always`, `sigv4` | 서명 없는 origin 요청. 모든 origin 요청에 서명하도록(`always`) 설정하면 CloudFront와 S3 사이도 HTTPS로만 통신합니다(CloudFront 문서) |
| CloudFront | `ViewerProtocolPolicy: redirect-to-https` | 평문 HTTP로 페이지에 접속하는 것 |
| CloudFront | `AllowedMethods: [GET, HEAD]` | PUT, POST, DELETE 같은 쓰기 요청 |
| CloudFront | `DefaultRootObject: index.html` | 루트 URL을 요청했을 때 배포의 내용이 노출되는 것 |
| WAF | 배포에 연결한 web ACL(scope `CLOUDFRONT`, 기본 동작 Allow): IP마다 5분에 1000건을 넘는 요청 차단(rate limit), AWS managed rule group `AWSManagedRulesAmazonIpReputationList`, `AWSManagedRulesCommonRuleSet`, `AWSManagedRulesKnownBadInputsRuleSet` | 한 IP의 과도한 요청, 평판 목록에 있는 IP, 일반적인 웹 공격 패턴과 알려진 악성 입력 |
| 접근 로그 | CloudFront 표준 로깅 v2(CloudWatch Logs vended delivery: `AWS::Logs::DeliverySource`, `DeliveryDestination`, `Delivery`)를 로그 버킷으로 전송 | 공개 엔드포인트의 접근 기록이 남지 않는 것 |
| 접근 로그 | 사이트 버킷의 S3 서버 액세스 로그를 같은 로그 버킷의 `s3-access/` 접두사로 전송 | 버킷 접근 기록이 남지 않는 것 |
| 로그 버킷 | Block Public Access 네 가지, `BucketOwnerEnforced`, SSE-S3, 90일 뒤 만료, TLS가 아닌 요청 거부, 쓰기는 이 계정의 로그 전송 서비스(`logging.s3.amazonaws.com`, `delivery.logs.amazonaws.com`)만 허용, `DeletionPolicy: Retain` | 로그가 공개되거나 무기한 쌓이는 것, 스택을 지울 때 로그가 함께 사라지는 것 |
| 응답 헤더 | CSP `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'` | 외부 스크립트, 스타일, 연결, 폼 전송, 다른 사이트의 프레임 삽입 |
| 응답 헤더 | HSTS `max-age` 63072000, `includeSubDomains` | HTTPS 대신 HTTP로 접속하는 것 |
| 응답 헤더 | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()` | MIME sniffing, clickjacking, referrer 유출, 브라우저 기능 사용 |
| 페이지 | `index.html`은 `style.css`와 `app.js`만 불러오고, `app.js`는 같은 origin의 `data/recording.json` 하나만 `fetch`합니다. 기록의 값은 모두 text node로 삽입하고 `innerHTML` 같은 HTML 삽입을 쓰지 않습니다 | 기록 안의 문자열(평가된 코드가 만든 오류 메시지의 끝부분, 정책 위반)이 HTML이나 스크립트로 실행되는 것 |

응답 헤더는 모두 `Override: true`로 설정되어 있어서, origin이 보낸 같은 이름의 헤더보다 정책 값이 우선합니다. 버킷 정책의 `AWS:SourceArn` 조건은 고정값이므로 S3는 이 정책을 public으로 판단하지 않습니다. 그래서 `BlockPublicPolicy`를 켠 상태에서도 이 정책을 적용할 수 있습니다(S3 문서의 "public" 정의).

!!! warning "누구나 볼 수 있는 공개 페이지입니다"
    이 데모는 의도적으로 공개하므로 템플릿에 인증이나 접근 제어가 없습니다. WAF는 rate limit과 managed rule로 비정상 요청만 차단해요. URL을 아는 사람은 누구나 볼 수 있으니, 업로드하기 전에 2.5의 검토 항목을 확인하세요.

!!! warning "남은 위험: 기본 인증서의 TLS 1.0과 1.1"
    기본 `*.cloudfront.net` 인증서에서는 viewer security policy가 TLSv1로 고정됩니다. 2026-11-18 배포에서 이 엔드포인트는 TLS 1.0과 1.1 handshake를 받아들였습니다(TLS 1.2와 1.3도 제공). `TLSv1.2_2021`은 us-east-1의 ACM 인증서를 쓰는 custom domain(`DEMO_DOMAIN`, `DEMO_CERT_ARN`)에서만 적용할 수 있으니 5절을 보세요. 이 실습 계정에는 Route 53 hosted zone이 없어 기본 인증서로 배포했습니다.

!!! note "검증 상태"
    로컬에서 `tests/test_demo.py`의 테스트 4개, `cfn-lint demo/infra/site.yaml`, `node --check demo/site/app.js`가 통과했습니다. 로컬 미리보기에서도 모든 파일이 정상적으로 제공됐습니다. 테스트가 확인하는 항목은 다음과 같습니다.

    - 버킷의 Block Public Access 네 가지 설정
    - 허용 문(statement)이 CloudFront service principal 하나뿐이고 `AWS:SourceArn` 조건이 있는지
    - TLS가 아닌 요청 거부, `redirect-to-https`, GET과 HEAD만 허용
    - CSP 지시문과 1년 이상의 HSTS
    - 외부 리소스와 `innerHTML` 같은 HTML 삽입이 없고, `fetch` 대상이 `data/recording.json` 하나뿐인지
    - 기록의 verdict가 기대값과 같고, reward가 `score_verdict`의 계산 결과와 같은지

    2026-11-18에 us-east-1에 실제로 배포했고, 배포 뒤 외부에서 다음을 확인했습니다.

    - **헤더:** CSP, HSTS(max-age 63072000, includeSubDomains), `X-Frame-Options: DENY`, nosniff, `Referrer-Policy: strict-origin-when-cross-origin`, Permissions-Policy
    - **요청:** POST, PUT, DELETE는 403, 없는 경로는 403, `http://`는 301. GET과 HEAD만 허용
    - **버킷:** 두 버킷 모두 Block Public Access가 켜져 있고 policy status가 public이 아니며, 둘 다 SSE-S3
    - **로깅:** S3로 가는 로그 전송(delivery)이 있음

## 확인 방법

배포한 뒤 다음을 순서대로 확인합니다.

1. `deploy.sh`의 마지막 줄이 `[demo] live: https://...`입니다.
2. 그 URL을 브라우저로 열면 "기록 출처" 줄에 직접 쓴 `--source` 문구가 보이고, 1절의 모든 카드에서 egress 차단이 "확인됨"입니다.
3. 응답에 보안 헤더 여섯 개가 있습니다.

    ```bash
    # Security headers on the public URL
    curl -sI https://<distribution-domain>/ \
      | grep -iE '^(content-security-policy|strict-transport-security|x-content-type-options|x-frame-options|referrer-policy|permissions-policy):'
    ```

4. 버킷에 직접 요청하면 거부됩니다.

    ```bash
    # Direct bucket access must be refused
    curl -s -o /dev/null -w '%{http_code}\n' https://<bucket>.s3.us-east-1.amazonaws.com/index.html
    ```

    **확인할 것:** `403`이 출력됩니다.

5. `http://`로 요청하면 `Location`이 `https://`로 시작하는 301 응답이 옵니다(`curl -sI http://<distribution-domain>/`).
6. 쓰기 요청은 거부되고, 배포에 WAF web ACL이 연결되어 있습니다.

    ```bash
    # Write methods are refused (403), and the distribution has a web ACL (an ARN)
    curl -s -o /dev/null -w '%{http_code}\n' -X POST https://<distribution-domain>/
    aws cloudfront get-distribution-config --id <distribution-id> \
      --query 'DistributionConfig.WebACLId' --output text
    ```

    **확인할 것:** 첫 명령은 `403`을, 둘째 명령은 `arn:aws:wafv2:us-east-1:`로 시작하는 ARN을 출력합니다.

## 6. 정리 (demo/teardown.sh)

이 스크립트는 `aws s3 rm --recursive`로 사이트 버킷을 비우고 us-east-1의 CloudFormation 스택을 삭제한 뒤, 삭제가 끝날 때까지 기다립니다. 사이트 버킷의 파일, CloudFront 배포, WAF web ACL이 삭제되고 URL은 더 이상 동작하지 않아요. CloudFront 배포 삭제에는 시간이 걸릴 수 있습니다. **로그 버킷은 `DeletionPolicy: Retain`이라 남습니다.**

```bash
demo/teardown.sh
```

**확인할 것:** `Delete demo stack gpu-sandbox-demo and all files in its bucket? Type 'gpu-sandbox-demo':` 질문에 스택 이름을 그대로 입력해야 삭제가 진행됩니다. 삭제 출력 뒤에 다음 두 줄이 나옵니다. 다른 스택 이름을 썼다면 `DEMO_STACK_NAME`도 함께 지정하세요.

```text
deleted gpu-sandbox-demo
kept the access log bucket <log-bucket>; when you no longer need the logs: aws s3 rb s3://<log-bucket> --force
```

로그 객체는 90일 뒤 만료되지만 버킷은 남습니다. 로그가 더 필요 없으면 출력된 `aws s3 rb` 명령으로 로그 버킷을 지우세요.

GPU 노드와 클러스터 정리는 [99 정리](99_cleanup.md)에 있습니다.

## 적용 범위와 한계

- **2026-11-18에 AWS에서 실행했습니다.** recorder pod에서 `record`로 GPU 기록(gVisor A10G, Kata QEMU T4)을 만들고, `deploy.sh`로 us-east-1에 공개한 뒤 외부 점검까지 했어요("보안 설계"의 검증 상태). 공개한 기록은 실제 GPU 풀의 기록이며, 학습 이벤트는 들어 있지 않습니다.
- **`record`는 trainer 이미지로 만든 pod에서 실행합니다.** 학습 이벤트(3절)는 학습 중인 trainer pod에서 기록할 때만 들어갑니다(2절).
- **200 응답 대기가 시간 초과되어도 실패로 처리하지 않습니다**(`deploy.sh`의 7번 단계).
- **custom domain의 DNS는 자동으로 만들지 않습니다**(5절).
- **기본 `*.cloudfront.net` 인증서에서는 viewer TLS 정책이 TLSv1로 고정됩니다.** 2026-11-18 배포에서 TLS 1.0과 1.1 handshake가 성공했어요. `TLSv1.2_2021`은 custom domain에서만 적용됩니다(5절).
- **리전은 us-east-1로 고정됩니다**(4절).
- **WAF는 트래픽이 없어도 고정 비용이 듭니다**("소요 시간과 비용"). 로그 버킷은 정리 뒤에도 남습니다(6절).
- **`PriceClass_100`을 씁니다.** 기본값(모든 edge location)보다 범위가 좁으므로, 방문자가 많은 지역에 맞는 price class를 [CloudFront 요금](https://aws.amazon.com/cloudfront/pricing/)에서 확인하세요.
- **저장소의 샘플 기록(`demo/site/data/recording.json`)은 여전히 노트북의 CPU 풀에서 만든 기록입니다.** 샘플의 수치는 GPU 샌드박스 성능과 관계가 없으며, 페이지 footer에도 이 내용이 적혀 있어요.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | CloudFront: S3 origin 접근 제한 (OAC, 버킷 정책 예시) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html |
    | CloudFront 배포 설정 (security policy, 기본 인증서의 TLSv1, default root object, price class) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesGeneral.html |
    | CloudFront 응답 헤더 정책 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-response-headers-policies.html |
    | S3 Block Public Access ("public" 정의 포함) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html |
    | cfn-lint | https://github.com/aws-cloudformation/cfn-lint |

    전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-handson-09-demo-site)
