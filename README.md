**한국어** | [English](README.en.md)

# GPU Sandbox on AWS

**TL;DR** 모델이 작성한 GPU 커널을 격리된 GPU 샌드박스에서 실행해 reward를 매기는 on-policy RL post-training을, Amazon EKS(EC2 자체 운영)와 SageMaker HyperPod에서 gVisor, Kata + QEMU, Kata + Cloud Hypervisor로 구축하는 코드와 가이드북입니다.

**가이드북:** https://daekeun-ml.github.io/gpu-sandbox-on-aws/ (English: https://daekeun-ml.github.io/gpu-sandbox-on-aws/en/)

처음이라면 [학습 코스 고르기](https://daekeun-ml.github.io/gpu-sandbox-on-aws/learning_paths/)에서 목적과 예산에 맞는 코스를 고르세요(무료인 읽기, 로컬 실행 코스가 먼저).

**바로 가기:** [아키텍처](#아키텍처) | [시나리오와 런타임](#시나리오와-런타임) | [시작하기](#시작하기) | [가이드북의 주요 페이지](#가이드북의-주요-페이지)

## 아키텍처

![만드는 것: 학습 노드의 policy 모델과 vLLM이 버전을 고정한 채 세 런타임의 GPU 샌드박스 풀에 커널 코드를 보내고, 정확성과 speedup을 reward로 받는 구성](docs/images/figures/index--what-we-build.ko.svg)

*그림 요약: policy 모델이 쓴 커널 코드는 group 단위로 버전을 고정한 상태로 세 런타임의 GPU 샌드박스 풀에 전달되고, 풀이 측정한 정확성과 speedup이 reward로 쓰입니다.*

네 시나리오는 같은 CDK 스택(private EKS API, SSM 터널, KMS 키, 로그)을 쓰고, trainer와 샌드박스가 배치되는 위치만 다릅니다.

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

*그림 요약: 샌드박스도 HyperPod 인스턴스 그룹(ml.g5.xlarge x2)에 올라가고, 이 노드는 한 번 빌드하는 custom AMI(드라이버 580.178.04)로 부팅해요. AWS에서 실행해 보지 않은 실험 경로입니다.*

</details>

<details>
<summary><b>시나리오 C: CPU 전용</b></summary>

![시나리오 C: GPU 없이 c8i.2xlarge 한 대에 세 런타임의 CPU 풀이 있는 구성](docs/images/architecture/scenario-c.drawio.png)

*그림 요약: GPU 노드 없이 c8i.2xlarge 한 대에 세 런타임의 풀이 서고, system 노드의 simulate Job이 trainer 대신 golden 코드를 보냅니다.*

</details>

### 요청 경로

- reward batch마다 trainer가 routing ConfigMap(`sandbox-routing`)의 snapshot 하나로 런타임과 버전을 고정합니다. 학습 중에 v2로 바꿔도 한 batch 안에서는 버전이 섞이지 않아요.
- trainer는 headless Service를 CoreDNS로 풀어 Ready 상태인 pod에 `POST /v1/evaluate`를 직접 보냅니다. 바쁜 pod는 `503`을 돌려주고, trainer는 다른 pod로 다시 시도합니다.
- 요청에는 audience가 `gpu-sandbox`인 projected ServiceAccount 토큰이 붙고, pod는 JWKS로 토큰을 오프라인 검증합니다. `sandbox` 네임스페이스는 default-deny라서 `rl-trainer`에서 label이 붙은 pod만 접속할 수 있어요.

Production 구성(Karpenter NodePool, sandbox gateway, veRL on KubeRay)은 [Production 00 아키텍처](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/00_architecture/)에, 노드 그룹과 네임스페이스, 화살표별 설명은 [핸즈온 00 전체 흐름](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/00_overview/)에 있습니다. 그림 원본(`.drawio`)은 [`diagrams/`](diagrams/)에 있어요.

## 시나리오와 런타임

| 시나리오 | 학습 위치 | GPU 샌드박스 위치 | 언제 |
|---|---|---|---|
| A. EC2 자체 운영 | EKS의 EC2 GPU 노드 (`g5.2xlarge`) | 같은 클러스터의 EC2 노드 | 모든 구성 요소를 직접 제어하고 싶을 때 |
| B1. HyperPod (기본) | HyperPod 인스턴스 그룹 (`ml.g5.2xlarge`) | HyperPod가 붙은 같은 EKS 클러스터의 EC2 노드 | 장시간 학습에 HyperPod의 노드 자동 교체와 job 재시작이 필요할 때 |
| B2. HyperPod (실험) | HyperPod 인스턴스 그룹 | 드라이버를 바꾼 custom AMI로 만든 HyperPod 인스턴스 그룹 위 gVisor | 샌드박스 노드에도 HyperPod 노드 복구가 필요할 때 (custom AMI를 직접 관리, AWS에서 미실행) |
| C. c8i 단독 (GPU 없음) | 없음 (모델 없는 reward 루프) | `c8i.2xlarge` 한 대의 CPU 샌드박스 (gVisor, Kata + CLH, Kata + QEMU) | GPU 쿼터 없이, 컴퓨트 시간당 약 0.57 USD로 런타임 비교와 버전 교체를 먼저 익히고 싶을 때 ([핸즈온 10](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/10_cpu_only/)) |

| 런타임 (RuntimeClass) | 격리 경계 | GPU 경로 | 노드 | 상태 |
|---|---|---|---|---|
| gVisor (`gvisor`) | 사용자 공간 커널(Sentry) | nvproxy가 드라이버 버전별 ioctl allowlist로 호스트 드라이버에 전달 | `g5.xlarge` (A10G) | 기본 GPU 경로. VM 경계보다 약함 |
| Kata + QEMU (`kata-qemu-nvidia-gpu`) | VM (KVM) | VFIO GPU passthrough, guest 드라이버 | `g4dn.metal` (T4 8개, VM마다 1개) | upstream이 지원하는 Kata GPU 경로. T4는 upstream CI 범위 밖 |
| Kata + Cloud Hypervisor (`kata-clh`) | VM (KVM) | 없음 (CPU 계층) | `c8i.2xlarge` (nested virtualization) | CPU 샌드박스. GPU(`kata-clh-nvidia-gpu`)는 upstream 미지원, 실험용 |
| Kata + QEMU CPU (`kata-qemu`) | VM (KVM) | 없음 | `c8i.2xlarge` | CPU 샌드박스 |

샌드박스 이미지와 서버는 하나이고 `RuntimeClass`만 바꿔 런타임을 고르며, 선택 기준은 가이드북의 [05 상황별 선택 가이드](https://daekeun-ml.github.io/gpu-sandbox-on-aws/concepts/05_decision_guide/)에 있습니다.

## 시작하기

로컬 테스트(AWS 비용 없음)부터 스크립트 순서대로 진행합니다. 단계별 설명과 확인할 것은 가이드북의 [시작하기](https://daekeun-ml.github.io/gpu-sandbox-on-aws/getting_started/)에 있어요.

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

**확인할 것:** 마지막 줄에 실패 없이 `94 passed`가 나옵니다. 테스트는 AST 정책, 2-프로세스 harness, 토큰 인증, readiness, 클라이언트와 gateway, 매니페스트와 노드 user data 렌더링을 CPU에서 확인해요. CDK 스택 테스트 18개는 `cdk/tests`에 따로 있고, CDK 라이브러리를 설치한 뒤 `cd cdk && python -m pytest -q tests`로 실행합니다.

> [!WARNING]
> **Linux 호스트에서 서버를 직접 띄울 때:** 샌드박스 서버는 평가가 끝날 때마다 `/proc`에 보이는 프로세스 중 자신과 조상을 뺀 모두에 SIGKILL을 보냅니다. pod 안에서는 컨테이너 범위로 한정되지만, Linux 호스트에서 `gpusandbox-server`를 직접 띄우면 같은 사용자의 다른 프로세스도 대상이 되니 별도 컨테이너에서 실행하세요. pytest는 `tests/conftest.py`에서 이 동작을 끄므로 Linux 호스트에서도 위 명령을 그대로 실행할 수 있어요([시작하기](https://daekeun-ml.github.io/gpu-sandbox-on-aws/getting_started/)).

### 2. 스크립트를 번호 순서대로 (AWS, 과금 발생)

먼저 `cp scripts/config.env.example scripts/config.env`로 설정 파일을 만듭니다. `SCENARIO`(A, B1, B2, C)는 `02_create_cluster.sh`의 옵션으로도 고를 수 있고, `ADMIN_PRINCIPAL_ARN`을 비워 두면 지금 쓰는 IAM 역할이 클러스터 관리자가 돼요. 모든 스크립트는 이 파일을 읽고, 값이 비었거나 `__SET_ME__`로 남아 있으면 멈춥니다.

인프라는 CDK 앱이 만들므로 `02_create_cluster.sh`를 실행하기 전에 한 번 준비합니다. Node.js 22 또는 24, AWS CDK CLI 2.1148.1 이상, AWS CLI용 Session Manager plugin을 설치하고, 가상 환경에 CDK 라이브러리를 넣은 뒤 계정과 리전마다 bootstrap을 한 번 실행하세요.

```bash
npm install -g aws-cdk                 # AWS CDK CLI 2.1148.1 or later
uv pip install -r cdk/requirements.txt # into the activated .venv
source scripts/config.env              # exports AWS_REGION
cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"
```

번호가 붙은 01~08이 기본 순서이고, `scripts/kata/`는 선택 단계, `scripts/ops/`는 검증과 운영용 스크립트입니다.

| 순서 | 명령 | 하는 일 |
|---|---|---|
| 01 | `scripts/01_check_prereqs.sh` | 도구(aws, cdk, node, kubectl, helm, docker, python3, jq, session-manager-plugin), AWS identity, G and VT vCPU quota, nested virtualization 지원, GPU 인스턴스의 AZ별 제공 여부 확인 (읽기 전용) |
| 02 | `scripts/02_create_cluster.sh` | CDK 스택(`cdk/deploy.sh`)으로 VPC, EKS(private API endpoint), 시나리오별 노드 그룹, SSM access instance 생성 (기본 A, `--hyperpod`면 B1, `--hyperpod-b2`면 B2, `--cpu-only`면 C). 실습 계정에서 약 20분 |
| 터널 | `cdk/tunnel.sh` | 두 번째 터미널에서 켜 두는 SSM 포트 포워딩. private API endpoint를 `127.0.0.1:8443`으로 이어 주고 kubectl 컨텍스트 `<CLUSTER_NAME>-tunnel`을 만듦. kubectl과 helm을 쓰는 모든 단계에 필요 |
| 03 | `scripts/03_build_push_images.sh` | sandbox, trainer, control 이미지를 `linux/amd64`로 빌드해 ECR에 push |
| 04 | `scripts/04_install_gpu_stack.sh` | NVIDIA device plugin(CDI 모드)을 설치한 뒤 `gvisor` RuntimeClass를 등록하고 GPU smoke pod를 실행. 시나리오 B2에서는 device plugin만 설치 (시나리오 C는 이 단계를 실행하지 않음) |
| 선택 | `scripts/kata/cpu_nodes.sh` | Kata CPU 노드(`c8i.2xlarge`, nested virtualization)에 kata-deploy, `gvisor-cpu` RuntimeClass, smoke pod. 노드 그룹은 시나리오 C이거나 `WITH_KATA_CPU=1`로 `02_create_cluster.sh`를 다시 실행했을 때 생김 |
| 선택 | `scripts/kata/gpu_nodes.sh` | 첫 실행은 IOMMU AMI를 빌드하고 멈춤. `KATA_IOMMU_AMI_ID`와 `WITH_KATA_GPU=1`을 넣고 `02_create_cluster.sh`를 다시 실행해 `g4dn.metal`(시간당 약 7.8 USD)을 추가한 뒤, 다시 실행하면 GPU Operator와 kata-deploy 설치 |
| 05 | `scripts/05_setup_namespaces_auth.sh` | namespace, NetworkPolicy, ServiceAccount, JWKS, routing ConfigMap |
| 06 | `scripts/06_deploy_sandboxes.sh gvisor v1` | 샌드박스 풀(Deployment + headless Service) 배포 |
| 운영 | `scripts/ops/verify.sh gvisor v1` | 격리 증거, egress 차단, golden verdict, NetworkPolicy 확인 |
| 07 | `scripts/07_run_grpo.sh` | TRL GRPO 학습 Job (기본 60 step) |
| 운영 | `scripts/ops/simulate.sh` | (시나리오 C) 모델 없이 golden 제출물로 reward 배치를 차례로 보내는 루프. 학습이 아님 |
| 운영 | `scripts/ops/rollout.sh gvisor v1 v2` | 학습 중 샌드박스를 v1에서 v2로 blue/green 교체 |
| 운영 | `scripts/ops/bench.sh` | (선택) 배포된 풀의 cold start, 지연, speedup 비교 |
| 08 | `scripts/08_cleanup.sh` | 클러스터 이름을 확인한 뒤 `cdk/destroy.sh`로 스택 전체 삭제, AMI는 하나씩 물어봄, `--images`면 ECR 저장소까지 (HyperPod를 만들었다면 `scripts/hyperpod/delete.sh` 먼저) |

인프라(VPC, 클러스터, 노드 그룹)는 CDK 앱 하나가, 클러스터 안쪽 설치는 `scripts/`의 스크립트가 터널을 거쳐 실행합니다. eksctl은 private endpoint만 있는 클러스터를 만들 수 없어서(eksctl 문서), 계정 보안 점검에 걸리지 않도록 eksctl 경로를 없앴어요. 스택 구성과 보안 기본값은 [Production 09 CDK로 프로비저닝](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/09_cdk/)에 있습니다.

GPU 없이 시작하려면 시나리오 C(`--cpu-only`, `c8i.2xlarge` 한 대)를 [핸즈온 10](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/10_cpu_only/)대로 따라가세요. HyperPod 시나리오(B1)는 `scripts/02_create_cluster.sh --hyperpod` 뒤에 `scripts/hyperpod/create.sh`를 실행하고, `07_run_grpo.sh` 대신 `scripts/hyperpod/run_grpo.sh`를 씁니다. 단계별 설명과 확인 방법은 [핸즈온 00 전체 흐름](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/00_overview/)에 있고, 막히면 [문제 해결](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/)을 보세요.

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

[kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) v1.0.11로 multi-turn episode마다 미리 띄운 샌드박스 하나를 빌려 쓰는 확장입니다. `k8s/extensions/agent-sandbox/`의 SandboxTemplate과 SandboxWarmPool이 이 저장소의 샌드박스 서버를 런타임 프로필(gvisor, kata-qemu, kata-clh-cpu 등)마다 감싸고, `src/gpusandbox/agent_sandbox.py`의 `EpisodeSandbox`가 SandboxClaim으로 하나를 받아 쓴 뒤 반납해요. 설치와 풀 생성은 `scripts/extensions/agent_sandbox.sh install`, `scripts/extensions/agent_sandbox.sh pool <runtime> [n]`입니다.

template은 label이 붙은 trainer pod의 8000번 ingress만 허용하고 egress는 전부 막으며(`egress: []`), `dnsPolicy: None`에 nameserver 127.0.0.1을 명시해 controller가 공개 resolver를 넣지 못하게 합니다. 가짜 API를 쓰는 단위 테스트는 통과하지만 클러스터에서는 실행하지 않았고, SandboxTemplate 안의 Kata GPU는 미검증입니다. warm GPU 샌드박스는 쉬는 동안에도 GPU를 쥐고 있어 과금됩니다. 자세한 내용은 [06 Agent Sandbox로 확장](https://daekeun-ml.github.io/gpu-sandbox-on-aws/concepts/06_agent_sandbox/)에 있어요.

## 리플레이 데모 사이트

`demo/`는 실행 기록을 재생할 뿐인 정적 리플레이 사이트(HTML, CSS, JS, 외부 스크립트 없음)라서, 방문자는 클러스터나 GPU에 닿지 않아요. 클릭해 보는 아키텍처 그림, gVisor와 Kata에서 같은 코드를 채점하는 재생, 샌드박스 안에서 시도한 접근이 막히는 실제 터미널 출력, GRPO 학습과 버전 전환 차트, 벤치마크 차트, 약 2분짜리 둘러보기 영상을 담고 있습니다. 데이터는 `python -m gpusandbox.tools record`의 녹화와, `demo/build_extras.py`가 클러스터 로그에서 만든 `extras.json`이에요. 로그의 IP 주소와 노드 이름은 가리고, 배포 전에 한 번 더 검사합니다. 2026-11-18에 공개한 GPU 녹화는 `demo/recordings/`에 있습니다.

사이트는 Block Public Access를 켠 private S3 bucket에 두고 CloudFront가 Origin Access Control로만 읽습니다. bucket policy는 `AWS:SourceArn` 조건을 건 CloudFront 서비스 주체만 허용하고 TLS가 아닌 요청을 거부하며, 응답에는 엄격한 Content-Security-Policy, HSTS, nosniff, `frame-ancestors 'none'`, referrer policy를 붙여요. AWS WAF(IP별 rate limit과 관리형 규칙)를 붙이고 접근 로그를 비공개 로그 버킷에 남깁니다. 배포는 `demo/deploy.sh`(us-east-1 고정), 삭제는 `demo/teardown.sh`입니다. 기본 `*.cloudfront.net` 인증서로는 viewer TLS 정책을 올릴 수 없으니, TLSv1.2_2021이 필요하면 custom domain과 us-east-1의 ACM 인증서를 쓰세요. 절차는 [09 데모 사이트 (CloudFront)](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/09_demo_site/)에 있어요.

## 검증 상태

- **AWS에서 실행한 것:** 시나리오 C만 끝까지 실행했습니다(2026-11-14, 실습 계정 us-west-2에서 CDK 배포, Kata CPU 노드 추가(`kata/cpu_nodes.sh`), 삭제). 실습 계정에서 2026-11-18에는 시나리오 A의 gVisor 경로도 실행했어요(us-west-2). 이미지 빌드, `04_install_gpu_stack.sh`, `05_setup_namespaces_auth.sh`, `06_deploy_sandboxes.sh gvisor v1`과 `ops/verify.sh gvisor v1`, `g5.2xlarge`에서 5 step GRPO, `08_cleanup.sh --images`입니다.
- **AWS에서 실행한 것 (2026-11-18, 계속):** Kata GPU(`g4dn.metal`의 Kata + QEMU, T4)와 Kata CPU, 다섯 개 풀의 `ops/bench.sh`, 공개 데모 사이트(CloudFront, WAF) 배포도 실행했습니다. 측정값은 [08 런타임 벤치마크](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/08_benchmark/)에 있어요.
- **AWS에서 실행하지 않은 것:** 학습 중의 `ops/rollout.sh`(시나리오 A), 60 step 기본 학습, HyperPod B1과 B2, 실험용 Kata CLH GPU(시도했지만 VM이 시작되지 않음). 이 단계는 각 핸즈온 페이지의 확인 단계로 직접 검증하세요.
- **수치:** 가격과 버전 같은 수치는 측정값이 아니라 공식 문서와 공개 자료의 값입니다.

## 비용

GPU 노드는 노드 그룹을 지울 때까지 과금됩니다. 핸즈온의 gVisor 최소 경로는 컴퓨트만 시간당 약 3.42 USD(온디맨드 요금을 더한 추정)이고, `g4dn.metal`은 한 대에 시간당 7.824 USD입니다(us-east-1과 us-west-2 On-Demand, 2026-11 기준, 배포 전 재확인). 쉬는 동안에는 노드 그룹을 0으로 줄이고(예: `aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu --scaling-config minSize=0,maxSize=1,desiredSize=0`), 끝나면 `scripts/08_cleanup.sh`를 실행하세요. NAT gateway, EBS, ECR 같은 항목은 위 합계에 들어 있지 않아요.

## 보안

- **사설 바인딩:** 샌드박스 서버는 기본으로 `127.0.0.1`에만 바인딩합니다. pod 매니페스트만 pod 네트워크 안에서 `0.0.0.0`을 쓰고, Service는 headless ClusterIP뿐이며 NetworkPolicy allowlist가 호출자를 제한해요.
- **audience로 묶인 토큰:** 샌드박스 pod는 audience가 `gpu-sandbox`인 projected ServiceAccount 토큰을 클러스터 issuer의 JWKS(공개 키)로 오프라인 검증하고, 설정이 비어 있으면 모든 요청을 거부합니다(fail closed). pod 안에 시크릿이 없고 Kubernetes API에도 접근하지 않습니다. gateway는 TokenReview와 subject allowlist로 호출자를 확인해요.
- **공개 endpoint 없음:** 클러스터의 서비스는 인터넷에 공개하지 않고, 설계상 공개되는 것은 녹화 JSON과 정적 파일만 담은 데모 사이트뿐입니다. EKS API endpoint는 private만 열려 있고, 운영자는 inbound 규칙이 없는 SSM access instance를 거치는 `cdk/tunnel.sh`로 접속해요.
- **egress 차단 확인:** 샌드박스는 IMDS, API 서버, 노드 kubelet에 닿지 않는 것을 확인한 뒤에만 Ready가 되고, 샌드박스 노드에는 iptables node guard가 있습니다.
- **로컬 전용 설정:** `SANDBOX_AUTH_TEST_BYPASS=1`은 loopback 테스트 전용이니 `0.0.0.0` 바인딩과 함께 쓰지 마세요. `scripts/config.env`에는 계정별 값이 들어가므로 커밋하지 않습니다(`.gitignore`에 포함).

위협 모델과 남는 위험은 [02 보안](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/02_security/)에 있습니다.

## License

코드와 문서는 [MIT](LICENSE)이고, 모델 라이선스는 별개입니다. 기본 모델 `Qwen/Qwen2.5-Coder-1.5B-Instruct`와 Production 예시의 `Qwen/Qwen2.5-Coder-7B-Instruct`는 Apache-2.0이고, `Qwen2.5-Coder-3B-Instruct`는 비상업 라이선스(qwen-research)라 이 저장소에서 쓰지 않습니다. 모델과 데이터셋을 바꿀 때는 각각의 라이선스를 직접 확인하세요.

이 저장소는 저자의 개인 견해와 조사 결과를 정리한 것으로, 저자가 재직 중인 회사의 공식 문서나 입장을 대변하지 않습니다.
