# 검증된 사실과 출처

!!! info "TL;DR"
    실습 계정에서 실행한 결과와 공식 문서와 외부 사례에서 가져온 수치를 확인할 수 있습니다.

- **직접 실행한 범위**는 [AWS 실행 기록](#aws-실행-기록)에서 확인하세요.
- **비용, quota, 드라이버 호환성**은 [배포 전 재확인 체크리스트](#배포-전-재확인-체크리스트)로 확인하세요.
- **원문 링크**는 [참고 자료 모음](references.md)에 있습니다.

## 근거 수준 읽는 법

| 표시 | 뜻 | 이 가이드의 예 |
|---|---|---|
| 로컬 테스트로 확인 | 이 저장소의 pytest가 CPU에서 통과 | 2-프로세스 harness, AST 정책, audience 기반 인증, egress 차단 확인을 조건으로 하는 readiness |
| 공식 문서 기준 | docs.aws.amazon.com, upstream 문서와 코드 | nested virtualization 지원 계열, nvproxy 드라이버 정책, VPC CNI의 노드 IP 허용 |
| 제3자 보고 | 블로그, 이슈, 공개 사례 | `g4dn.metal` warm reboot 문제, T4의 `reset_method=bus` |
| 블로그의 측정값 | 다른 사람이 다른 환경에서 측정한 값 | AWS 기술 블로그 2부의 warm pool claim 약 55 ms, AWS China 블로그의 cold start 약 3 s |
| 추론 | 근거에서 이끌어 낸 판단, 미검증 | NodeConfig `imports`가 kata-deploy drop-in을 유지하는 효과 |
| AWS에서 저자가 실행 | 실습 계정에서 실제로 실행하고 출력을 확인 | 시나리오 A의 gVisor 경로, Kata GPU(`g4dn.metal`), 시나리오 C의 CPU 런타임 세 개, 런타임 벤치마크, 데모 사이트. 날짜별 기록은 [AWS 실행 기록](#aws-실행-기록)에 있습니다 |
| AWS에서 저자가 실행하지 않음 | 설계하고 템플릿까지 만들었지만 실행하지 않음 | 학습 중의 시나리오 A `ops/rollout.sh`, `ml.g5`의 HyperPod B1과 B2(HyperPod 생성 포함). 전체 목록은 [AWS 실행 기록](#aws-실행-기록)에 있습니다 |

## 이 저장소에서 확인한 것

아래 첫 명령은 AWS와 GPU 없이 로컬 테스트 전체를 실행하고, 두 번째 명령은 CDK 라이브러리를 설치한 가상 환경에서 CDK 스택 테스트를 따로 실행합니다. 환경 구성은 [시작하기](../getting_started.md)를 따르세요.

- **테스트를 실행할 때**: 테스트는 서버의 프로세스 정리 동작을 끈 채로 실행되므로 Linux 호스트에서도 안전합니다.
- **Linux 호스트에서 서버를 직접 띄울 때**: 같은 사용자의 다른 프로세스가 종료될 수 있으니, 그 전에 그 페이지의 경고를 읽으세요.

```bash
# Full local test suite on CPU (no AWS, no GPU)
python -m pytest -q
# CDK stack tests: offline synth with cdk-nag (after uv pip install -r cdk/requirements.txt)
(cd cdk && python -m pytest -q tests)
```

**확인할 것:**

- 실패 없이 `passed`로 끝납니다.
- 이 페이지를 쓰는 동안(2026-11-13) macOS(CPU 전용)에서 전체 테스트가 통과했습니다.
- 테스트 수는 저장소가 바뀌면 달라지므로 여기에 적지 않습니다. 현재 체크아웃의 테스트 수는 저장소 루트에서 `python -m pytest --collect-only -q`로 확인하세요(CDK 스택 테스트는 따로).

**문제가 생기면:** [문제 해결](troubleshooting.md)

| 테스트 파일 | 로컬 테스트로 확인한 것 |
|---|---|
| `tests/test_policy.py` | AST 정책의 허용(Triton 예시, autotune 커널, `input` 매개변수, 타입 힌트)과 거부(금지 import와 builtin, 별칭을 거친 monkeypatch, dunder와 private, stream과 graph, Tensor 상속) |
| `tests/test_harness_cpu.py` | CPU에서 실제 2-프로세스 harness: 정답, 오답, 크래시, 문법 오류, timeout, 벤치마크 치팅, monkeypatch, 과제 reference의 일관성 |
| `tests/test_routing_and_rewards.py` | routing 표 다시 읽기와 revision, 없는 풀의 `RoutingError`, 코드 추출, speedup 점수, verdict별 reward와 인프라 오류 제외, 버전 전환 뒤 다른 풀로 캐시된 결과를 이번 batch의 풀에서 다시 채점, 정책 위반 코드는 샌드박스로 보내지 않음 |
| `tests/test_server_and_client.py` | audience와 subject를 확인하는 fail-closed 인증, loopback 서버 2개를 쓰는 클라이언트, 평가 중인 pod의 503, egress 차단을 확인한 뒤의 Ready, CPU 풀의 probe와 parity, routing 전환 중에도 유지되는 gateway group pin |
| `tests/test_manifests.py` | 프로필과 버전 조합의 샌드박스 매니페스트, 정적 매니페스트, 노드 user data(`infra/eks/userdata.py`), Karpenter 템플릿, Agent Sandbox template 렌더링 |
| `tests/test_agent_sandbox.py` | 가짜 API로 SandboxClaim 본문, Ready 대기와 `serviceFQDN` 선택, claim과 해제, Ready가 되지 않을 때의 해제 |
| `tests/test_multiturn.py` | 가짜 API와 loopback CPU 샌드박스 서버로 에피소드 하나가 claim 하나를 쓰는지, 정답에서 멈추는지, 오류가 나도 claim을 삭제하는지, 이벤트와 episode reward, veRL tool 로직(veRL 미설치) |
| `tests/test_demo.py` | 데모 CloudFormation 템플릿(private bucket, `AWS:SourceArn` 조건이 붙은 CloudFront 허용, TLS가 아닌 요청 거부, HTTPS 리디렉션과 보안 헤더), 외부 리소스와 HTML 주입이 없는 정적 사이트, 녹화 스키마와 reward 일관성 |
| `cdk/tests/test_stack.py` | synth한 CDK 템플릿: private endpoint(public은 /32 opt-in만), `0.0.0.0/0` inbound 없음, 시나리오별 노드 그룹, 시나리오마다 cdk-nag 통과. 나머지는 표 아래 목록 |

`cdk/tests/test_stack.py`가 더 확인하는 것은 다음과 같습니다.

- **IMDSv2**: 시나리오 A에 Kata CPU를 추가해 synth한 모든 launch template의 IMDSv2 필수(hop limit과 EBS 볼륨은 템플릿에 명시된 경우에만 hop limit 1과 암호화를 확인)
- **노드 그룹 설정**: c8i의 nested virtualization, Kata GPU 노드 그룹의 IOMMU AMI와 user data(이 구성의 IMDSv2는 검사하지 않음)

TRL 1.18.0 GRPO dry run(SmolLM2-135M, CPU, vLLM 없음)은 2 step을 마쳤고, 셸 스크립트는 shellcheck 검사를 통과했습니다(저자 기록, 2026-11).

### AWS 실행 기록

모두 저자의 실습 계정에서 실행했습니다.

| 날짜 | 리전 | 대상 | 실행한 것 | 결과 |
|---|---|---|---|---|
| 2026-11-14 | us-west-2 | 시나리오 C(EKS 1.36) | `02_create_cluster.sh --cpu-only`(CDK 배포, 약 20분), `cdk/tunnel.sh`, `kata/cpu_nodes.sh`(약 14분, 대부분 kata-deploy 설치), 스택 삭제. 배포와 삭제를 두 번 함. [05 직접 해 보기](../beginner/05_hands_on.md)의 2부도 이 순서로 실행함(같은 노드의 runc 비교 컨테이너 포함) | 성공. 클러스터와 노드 상태, private endpoint, c8i 노드의 nested virtualization과 `/dev/kvm`, gVisor와 node guard, `127.0.0.1`에서만 열리는 터널, `gvisor-cpu` RuntimeClass, 세 런타임의 smoke pod, 삭제 뒤 남은 리소스를 확인 |
| 2026-11-17 | us-west-2 | 시나리오 C(c8i) | `ops/rollout.sh kata-clh-cpu v1 v2`, 함께 실행한 모델 없는 reward 루프 `ops/simulate.sh`(30배치, 약 16분) | 성공. 배포, 검증, parity, 전환 네 단계가 통과했고 8번째 배치에서 `sandbox_version_switch`가 기록됨. `rollout.sh --finish`는 실행하지 않음. 출력은 `demo/site/data/extras.json`에 있음 |
| 2026-11-18 | us-west-2 | 시나리오 A(gVisor) | `02_create_cluster.sh`: GPU 노드 그룹을 포함한 첫 생성이 `InsufficientInstanceCapacity`로 롤백되어, system 노드만 있는 `--hyperpod-b2`로 만든 뒤 `CHANGE_SCENARIO=1`로 B1(gVisor 노드 그룹 추가)과 A(trainer 추가)로 차례로 업데이트. 이어서 `03_build_push_images.sh`(이미지 세 개), `04_install_gpu_stack.sh`(`g5.xlarge`), `05_setup_namespaces_auth.sh`, `06_deploy_sandboxes.sh gvisor v1`(replica 1개), `ops/verify.sh gvisor v1`, `g5.2xlarge`에서 `07_run_grpo.sh 5`, `08_cleanup.sh --images` | 성공. smoke pod `cuda ok: NVIDIA A10G 2048.0`, 드라이버 580.178.04(proprietary, GSP 꺼짐). 풀 검증은 golden verdict 6개 PASS, egress 대상 4개 차단, `default` 네임스페이스 차단. GRPO Job은 Complete(약 12분, `train_runtime` 약 401초). `08_cleanup.sh`의 AMI 삭제 단계가 돌았는지는 기록에 없음 |
| 2026-11-18 | us-west-2 | Kata GPU와 Kata CPU(다른 클러스터, EKS 1.36) | system 노드만 있는 구성으로 만든 뒤 `CHANGE_SCENARIO=1`로 Kata CPU, Kata GPU, gVisor 노드 그룹 추가. `kata/gpu_nodes.sh`(IOMMU AMI 빌드, GPU Operator), `kata/cpu_nodes.sh`, `06_deploy_sandboxes.sh kata-qemu`(replica 4개), `kata-qemu`와 CPU 풀 세 개의 `ops/verify.sh` | 성공. `pgpu=8`, `kata-qemu` pod 4개 Ready(T4), 풀 검증 통과. 실행 중에 `vfio_iommu_type1` 모듈 문제와 AMI 빌더 문제를 찾아 스크립트를 고침([03 Kata 샌드박스](../handson/03_kata.md)) |
| 2026-11-18 | us-west-2 | 실험용 Kata CLH GPU(`kata-clh`) | `ENABLE_EXPERIMENTAL_CLH_GPU=1`로 실험용 풀 배포 | 실패. artifact 경로를 채운 뒤에도 VM이 시작되지 않음(`create container timeout`). 벤치마크에서 빠짐 |
| 2026-11-18 | us-west-2 | 런타임 벤치마크 | 위 Kata 클러스터에서 다섯 풀(`gvisor`, `kata-qemu`, CPU 풀 세 개)에 `ops/bench.sh 32`를 배포 직후와 풀 재시작 뒤 두 번. 이 클러스터의 gVisor 노드는 `g5.2xlarge` 한 대 | 성공. 다섯 풀 모두 32개 중 32개 `ok`. 결과 표는 [08 런타임 벤치마크](../handson/08_benchmark.md) |
| 2026-11-18 | us-east-1(클러스터는 us-west-2) | 데모 사이트 | recorder pod에서 `record`(gVisor A10G 풀, Kata QEMU T4 풀), 클러스터 로그로 `extras.json` 생성, `demo/deploy.sh`, 배포 뒤 외부 점검 | 성공. 보안 헤더, 허용 메서드, 버킷 설정, 로그 전송을 확인. 기본 인증서에서 TLS 1.0과 1.1 handshake가 받아들여짐([09 데모 사이트](../handson/09_demo_site.md)의 보안 설계) |
| 2026-11-20 | us-west-2 | 시나리오 C(c8i) | `ops/rollout.sh kata-clh-cpu`(v1에서 v2, v2에서 v1), 함께 실행한 `ops/simulate.sh`, `extensions/agent_sandbox.sh install`, `pool kata-clh-cpu 1`, `claim kata-clh-cpu`, `episodes kata-clh-cpu 2 3` | 성공. 전환이 배치 경계에서 한 번 일어났고 batch마다 버전이 하나였음. v2에서 v1 방향 한 번은 CPU 측정 노이즈로 parity가 speedup 조건에서 실패(0.8979에서 0.5365, 판정은 같음). Agent Sandbox는 claim이 샌드박스 주소를 받고 반납했으며 warm pool이 새 샌드박스를 채움. `episodes`는 에피소드 2개가 모두 3 turn에 solved, 에피소드마다 claim과 샌드박스가 하나, 끝난 뒤 남은 claim 없음 |
| 2026-11-20 | us-west-2 | 시나리오 A(gVisor) | `01_check_prereqs.sh`, `02_create_cluster.sh`(GPU 노드 그룹 포함 첫 생성, CDK 배포 약 15분), `03_build_push_images.sh`, `04_install_gpu_stack.sh`, `05_setup_namespaces_auth.sh`, `06_deploy_sandboxes.sh gvisor v1`, `ops/verify.sh gvisor v1`, `07_run_grpo.sh`(기본 60 step) | 성공. 이번에는 용량 부족 없이 첫 생성이 끝남. 접속 인스턴스의 SSM 연결이 등록 직후 끊겨(`ConnectionLost`) 재부팅 뒤 터널이 연결됨. 검증 6개 제출물 모두 PASS. 학습은 `reward_batch` 60개, `sandbox_error` 0건, 한 batch의 버전 혼합 0건, `train_runtime` 2697초, Job 약 50분 Complete. `ok` 비율은 처음 20 step 5.3%, 마지막 20 step 6.0% |

2026-11-14에는 ap-south-1 콘솔에서 Service Quotas 화면과 EC2 AMI Catalog의 HyperPod AMI 검색 결과도 캡처했습니다. 조회만 했고 스크립트는 실행하지 않았습니다.

**AWS에서 실행하지 않은 것:**

- 학습 중의 시나리오 A `ops/rollout.sh`와 `ops/rollout.sh --finish`(어느 시나리오에서도 실행하지 않음)
- HyperPod 단계(`hyperpod/create.sh`부터)와 `ml.g5`의 B1, B2. B1과 B2 CDK 스택은 2026-11-18 시나리오 A 클러스터를 만들 때 중간 단계로만 배포함
- `hyperpod/delete.sh`, `demo/teardown.sh`(shellcheck만 통과)
- [11 multi-turn 에피소드 실습](../handson/11_multi_turn.md)의 `gvisor-cpu` warm pool과 GPU 절(`kata-clh-cpu` warm pool로는 실행함)
- 운영 가이드가 핸즈온에 더하는 구성: Karpenter NodePool, gateway, jwks-sync CronJob, pool hardening, warm capacity

나머지는 각 핸즈온 페이지의 확인 단계로 직접 검증하세요.

## 배포 전 재확인 체크리스트

아래 값은 2026-11 기준이며, 배포나 공유 전에 하나씩 다시 확인하세요.

- [ ] **버전 고정 값:** 각 프로젝트의 릴리스 페이지에서 새 버전과 변경점을 확인합니다.
    - gVisor `GVISOR_RELEASE=20261109.0`, Kata `KATA_VERSION=4.3.1`
    - GPU Operator `v26.7.2`, NVIDIA device plugin `0.20.1`
    - Karpenter v1.15.2(LTS v1.14.3)
    - AWS CDK CLI 2.1148.1 이상과 `aws-cdk-lib` 2.276.0, cdk-nag 3.0.2
    - Agent Sandbox v1.0.11
    - TRL 1.18.0(trainer 이미지의 vLLM 0.33.0), veRL 0.9.1(veRL 이미지의 vLLM 0.24.0), KubeRay v1.7.2
- [ ] **노드 드라이버와 nvproxy 목록:** B2 custom AMI의 `B2_NVIDIA_DRIVER_VERSION`과 노드 드라이버가 고정한 gVisor 릴리스의 supported 목록에 있는지 확인합니다.
    - **EKS AL2023 NVIDIA AMI v20261107**: 기본 드라이버는 580.178.04입니다(g5에서는 proprietary 모듈에 GSP 꺼짐, g6에서는 open 모듈).
    - **HyperPod EKS AMI**: 1.34~1.36(2026-10-16)은 595.91.07, 1.33은 580.178.04입니다.
- [ ] **가격:** EC2 온디맨드 요금과 SageMaker AI(HyperPod `ml.*`) 요금. 이 가이드의 값(`c8i.2xlarge` 0.37484 USD/시간 등)은 2026-11 기준입니다.
- [ ] **quota:** Running On-Demand G and VT instances(vCPU 기준, 새 계정은 0일 수 있음), Running On-Demand Standard instances, HyperPod의 `ml.<type> for cluster usage`.
- [ ] **HyperPod가 지원하는 Kubernetes 버전:** 사전 요구사항 페이지는 1.30부터 1.35까지, AMI 릴리스 노트는 1.36까지 적습니다. 이 가이드는 1.36을 씁니다.
- [ ] **EKS 버전:** standard support 1.37, 1.36, 1.35, 1.34.
- [ ] **nested virtualization 지원 계열과 리전:** User Guide의 계열 목록과 리전별 지원 여부.
- [ ] **관리형 샌드박스의 GPU 지원:** Nitro Sandboxes와 EKS isolated pods의 "GPU and other device passthrough are not supported at launch", AgentCore Code Interpreter 문서의 실행 환경 설명.
- [ ] **Agent Sandbox CRD 필드:** 컨트롤러를 업그레이드하면 `SandboxClaim`, `SandboxTemplate`, `SandboxWarmPool` 필드 이름을 다시 확인합니다.
- [ ] **모델 라이선스:** 사용할 모델 카드의 license 항목.
- [ ] **데모 사이트 TLS:** 기본 `*.cloudfront.net` 인증서로는 viewer TLS 정책을 더 높은 버전으로 바꿀 수 없으므로, TLSv1.2_2021이 필요하면 custom domain과 us-east-1의 ACM 인증서를 씁니다.

아래 명령은 노드 드라이버가 고정한 gVisor 릴리스의 지원 목록에 있는지 확인합니다. 노드의 debug 셸(`kubectl debug node`, [문제 해결](troubleshooting.md)의 "노드에서 확인")에서 `chroot /host` 뒤에 실행하세요.

```bash
driver="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"; echo "$driver"   # loaded driver version
/usr/local/bin/runsc nvproxy list-supported-drivers | grep -wF "$driver"
```

**확인할 것:**

- **두 번째 명령이 그 드라이버 버전을 한 줄 출력하면**: 지원 목록에 있습니다.
- **아무것도 나오지 않으면**: 그 노드에서 gVisor GPU 샌드박스가 Ready가 되지 않습니다.
- **HyperPod 노드**: `scripts/hyperpod/check_gvisor.sh`가 같은 확인을 해 줍니다.

아래 명령은 quota와 nested virtualization 지원을 한 번에 출력합니다(읽기 전용).

```bash
scripts/01_check_prereqs.sh
```

**확인할 것:** G and VT vCPU quota 값, `c8i.2xlarge`의 `nested-virtualization` 지원, GPU 인스턴스의 AZ 목록이 나오고 `Done.`으로 끝납니다. **문제가 생기면:** [문제 해결](troubleshooting.md)의 "설정과 스크립트", "클러스터와 노드" 표를 보세요.

## 참고 자료

### AWS 문서와 What's New

| 출처 | 뒷받침하는 사실 |
|---|---|
| [What's New: EC2 nested virtualization (2026-02)](https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/) | 2026-02-16에 C8i, M8i, R8i 가상 인스턴스에서 nested virtualization 출시 |
| [EC2 User Guide: nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) | 지원 계열(M7i, M7i-flex, M8i, M8id, M8i-flex, C7i, C7i-flex, C8i, C8id, C8i-flex, R7i, R7iz, R8i, R8id, R8i-flex, X8i, I7i, I7ie), L1 hypervisor KVM과 Hyper-V, G와 P 계열 없음, `--cpu-options "NestedVirtualization=enabled"`, 성능에 민감한 가상화에는 bare metal 권장 |
| [EC2 가속 컴퓨팅 인스턴스](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html) | NVIDIA GPU bare metal은 `g4dn.metal`(T4 8개, 96 vCPU, 384 GiB)과 `g5g.metal`(arm64, T4G 2개) |
| [EC2 instance type quotas](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html) | "Running On-Demand G and VT instances" 같은 vCPU 기준 On-Demand quota |
| [EC2 On-Demand 요금](https://aws.amazon.com/ec2/pricing/on-demand/) | us-east-1과 us-west-2의 시간당 USD: `g4dn.xlarge` 0.526, `g4dn.2xlarge` 0.752, `g6.xlarge` 0.8048, `g6.2xlarge` 0.9776, `g5.xlarge` 1.006, `g5.2xlarge` 1.212, `g6e.xlarge` 1.861, `g6e.12xlarge` 10.49264, `g6e.48xlarge` 30.13118, `p4d.24xlarge` 21.95764, `p5.48xlarge` 55.04, `g4dn.metal` 7.824(서울 9.624), `g5g.metal` 2.744, `c5.metal` 4.08, `m6i.large` 0.096, `t3.large` 0.0832 |
| [AWS Nitro Sandboxes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html) | 2026-11-09 출시, `runtimeClassName` `isolated-sandbox`, `confidential-sandbox` |
| [EKS sandboxing 제한 사항](https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html) | Kubernetes 1.36 이상, "GPU and other device passthrough are not supported at launch" |
| [EKS Kubernetes 버전](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) | standard support 1.37, 1.36, 1.35, 1.34 (최신 1.37) |
| [VPC CNI network policy 설정](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) | `{"enableNetworkPolicy": "true"}`, VPC CNI 1.21 이상, standard 모드는 정책 적용 전까지 새 pod를 허용, strict 모드(`NETWORK_POLICY_ENFORCING_MODE`)는 CoreDNS까지 기본 거부 |
| [EKS Auto Mode managed instances](https://docs.aws.amazon.com/eks/latest/userguide/automode-learn-instances.html) | "You can't directly access or install software on instances managed by EKS Auto Mode" |
| [HyperPod EKS 사전 요구사항](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html) | 인증 모드 API 또는 API_AND_CONFIG_MAP, VPC CNI 1.18.3 이상, private subnet, Kubernetes 1.30부터 1.35까지, API로 만들 때 의존성 Helm chart 필요, HyperPod 노드와 EKS 노드의 IAM 역할 분리 |
| [HyperPod IAM 사전 요구사항](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html) | 실행 역할: `AmazonSageMakerClusterInstanceRolePolicy`와 EC2 ENI, ECR inline policy |
| [HyperPod EKS AMI 릴리스 노트](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-release-ami-eks.html) | 2026-10-16 릴리스: Kubernetes 1.34~1.36용 AMI는 NVIDIA 595.91.07, 1.33(x86_64)은 580.178.04. 1.36 AMI는 커널 6.12.111, containerd 2.3.5, CUDA 13.2 |
| [HyperPod custom AMI](https://docs.aws.amazon.com/sagemaker/latest/dg/hyperpod-custom-ami-support.html), [custom AMI 만들기](https://docs.aws.amazon.com/sagemaker/latest/dg/hyperpod-custom-ami-how-to.html), [custom AMI로 클러스터 관리](https://docs.aws.amazon.com/sagemaker/latest/dg/hyperpod-custom-ami-cluster-management.html) | HyperPod 공개 base AMI로 만든 이미지만 쓸 수 있음, 용도 목록에 "driver customizations", 인스턴스 그룹의 `ImageId`(EKS, Slurm), `UpdateClusterSoftware`로 교체 |
| [HyperPod 자동 노드 복구](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-node-recovery.html), [deep health checks](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html) | NodeRecovery Automatic, deep health check(InstanceStress, InstanceConnectivity), 점검 중 taint와 `node-health-status` label |
| [HyperPod training operator](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html) | `HyperPodPyTorchJob`, `hyperpodrun`, `jobMaxRetryCount`, 로그 패턴 기반 hang 감지 |
| [Ray on HyperPod](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html) | HyperPod에서 Ray를 쓰는 공식 문서 |
| [SageMaker AI 요금](https://aws.amazon.com/sagemaker/ai/pricing/) | HyperPod 시간당 USD(us-east-1과 us-west-2): `ml.g4dn.xlarge` 0.7364, `ml.g6.xlarge` 1.127, `ml.g6.2xlarge` 1.222, `ml.g6.4xlarge` 1.654, `ml.g5.xlarge` 1.408, `ml.g5.2xlarge` 1.515, `ml.g5.8xlarge` 3.06, `ml.g6e.xlarge` 2.61 |
| [Amazon Bedrock AgentCore Code Interpreter](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html) | 실행 환경을 "containerized environment"로 설명, GPU 언급 없음 |

### AWS 블로그

| 출처 | 뒷받침하는 사실 |
|---|---|
| [AWS Containers 블로그 (2024): Kata Containers로 워크로드 격리 강화](https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/) | i3.metal에서 Kata + Firecracker |
| [AWS China 블로그 (2026-07)](https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/) | c5.metal, Kata 3.31.0 + Cloud Hypervisor, OpenSandbox, Karpenter 1.12.1. 블로그 측정값: cold start 약 3 s, pool claim 약 230 ms. "CLH 약 130 MB, QEMU 약 160 MB"는 Kata 3.31.0의 `podFixed` 기본값과 같아 측정값이 아닐 가능성이 큼 |
| [AWS 기술 블로그 "AWS에서 AI 에이전트 실행 환경 격리하기" 1부](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/) | EKS 1.36의 Agent Sandbox v1.0.5 + gVisor release-20260928.0, 격리 4계층(Pod 보안 설정, gVisor, NetworkPolicy, 전용 노드 그룹의 IMDS 설정). 나머지는 표 아래 목록 |
| [같은 시리즈 2부](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/) | 기본 SandboxTemplate 정책의 인터넷 egress 허용과 공개 resolver DNS 주입, NetworkPolicy 활성화 전의 IMDS와 API 접근, sandbox-router 인가(기본 allow-all, TokenReview는 유효성만 증명, Tunnel mode는 NetworkPolicy 우회). 측정값은 표 아래 목록 |
| [같은 시리즈 3부](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/) | 에이블리(Ably) 운영 사례: 프로젝트마다 Sandbox 하나, 전용 on-demand Karpenter NodePool과 `karpenter.sh/do-not-disrupt`, Kyverno와 ExternalDNS, v1.0.8 `SandboxClaim.spec.env`는 warm pool 없이 새로 시작, 현재 runc이며 API는 유지한 채 Kata 평가 계획 |

- **1부의 나머지 내용**: NodeConfig로 runsc 등록, IMDSv2 필수와 hop limit 1, EKS Auto Mode는 runsc 등록 불가, RuntimeClass 스케줄링은 같은 taint에 toleration이 있는 다른 pod가 그 노드에 배치되는 것을 막지 못함
- **2부의 블로그 측정값(EKS 1.36, m7i.xlarge)**: SandboxClaim에서 Ready까지 cold 약 2 s, warm pool 약 55 ms, gVisor의 syscall 비용 약 0.18 us에서 2.2 us

### GitHub 저장소와 프로젝트 문서

| 출처 | 뒷받침하는 사실 |
|---|---|
| [gVisor 설치](https://gvisor.dev/docs/user_guide/install/) | 최신 release-20261109.0. release-20260831부터 tarball 배포(`runsc`, `containerd-shim-runsc-v1`, `runsc`와 같은 디렉터리에 두어야 하는 `gvisor-bin/`) |
| [gVisor 릴리스 tarball (고정 URL)](https://storage.googleapis.com/gvisor/releases/release/20261109.0/x86_64/gvisor.tar.bz2) | 고정한 릴리스를 URL로 받을 수 있음 (`.sha512`와 함께 검증) |
| [gVisor GPU 지원](https://gvisor.dev/docs/user_guide/gpu/) | `nvproxy = "true"`, 기본 capabilities `compute,utility`, 드라이버 정책(supported, unsupported, unknown), 580.178.04는 release-20260831.0부터 supported. 나머지는 표 아래 목록 |
| [gVisor nvproxy 드라이버 표 (release-20261109.0)](https://github.com/google/gvisor/blob/release-20261109.0/pkg/sentry/devices/nvproxy/version.go) | 580.159.04, 580.178.04는 `addDriverABI`(supported), 595.71.05는 `addUnsupportedDriverABI`, 595.91.07은 없음(unknown). 개발 브랜치에도 595.91.07 없음(2026-11-14) |
| [NVIDIA 580.178.04 .run 설치 파일](https://download.nvidia.com/XFree86/Linux-x86_64/580.178.04/), [CUDA repo (Amazon Linux 2023)](https://developer.download.nvidia.com/compute/cuda/repos/amzn2023/x86_64/) | `.run`의 sha256 `5975a86e...6d6f9`(NVIDIA `.sha256sum`, gVisor 표와 같음). repo에 `kmod-nvidia-open-dkms-580.178.04`, `nvidia-driver-580.178.04` 등 |
| [google/gvisor](https://github.com/google/gvisor) | gVisor 소스 저장소 |
| [GKE Sandbox](https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods) | "Don't use GPU time-sharing in sandboxed Pods" |
| [Kata 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md) | "Cold-plug is by design the only supported mode for NVIDIA GPU passthrough", QEMU 경로 |
| [Kata 4.3.1 hypervisors.md](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md) | Cloud Hypervisor의 GPU 지원은 not supported |
| [Kata issue #11687](https://github.com/kata-containers/kata-containers/issues/11687) | maintainer 답변(2025-08): "You should use the QEMU GPU runtime class." |
| [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers) | 4.3.1(2026-10-21), runtime-rs 기본(4.0.0부터), Go runtime은 deprecated지만 지원, Helm chart `oci://ghcr.io/kata-containers/kata-deploy-charts/kata-deploy`의 `deploymentMode` 기본 `job`, RuntimeClass `overhead.podFixed` |
| [Firecracker FAQ](https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md), [CHANGELOG](https://github.com/firecracker-microvm/firecracker/blob/main/CHANGELOG.md) | 최소 장치 모델, 1.13.0의 PCI 지원 추가, 변경 이력에 VFIO GPU passthrough 없음 |
| [Modal Sandboxes](https://modal.com/docs/guide/sandbox) | "GPU Sandboxes are only supported with `runtime="gvisor"`" |
| [NVIDIA GPU Operator with Kata](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html), [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator) | v26.7.2의 sandbox 모드 값, `nvidia.com/pgpu`, "A node can only run one container runtime at a time", EKS 검증은 Ubuntu(AL2023은 목록에 없음) |
| [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin), [NVIDIA/nvidia-container-toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) | `deviceListStrategy: cdi-cri`, 호스트에 필요한 container toolkit |
| [awslabs/amazon-eks-ami v20261107](https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107) | AL2023 NVIDIA AMI: 드라이버 580.178.04 기본(595.91.07은 g7 전용), toolkit 1.20.1, containerd 2.3.7, device plugin 없음, kubelet 1.32 이상에서 CDI, user data는 nodeadm-config와 nodeadm-run 사이에 실행 |
| [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent) | 노드 IP는 ingress와 egress 맵 모두에서 허용("ensures kubelet liveness/readiness probes are never blocked") |
| [Karpenter 문서](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws) | v1.15.2(LTS v1.14.3), `karpenter.sh/v1`, `karpenter.k8s.aws/v1`, IMDS hop limit 1 기본, user MIME part 병합, EC2NodeClass `spec.cpuOptions.nestedVirtualization` |
| [eksctl 문서: Cluster Access](https://docs.aws.amazon.com/eks/latest/eksctl/vpc-cluster-access.html) | "EKS does allow creating a configuration that allows only private access to be enabled, but eksctl doesn't support it during cluster creation": private endpoint만 있는 클러스터는 eksctl로 만들 수 없어서, 이 저장소은 인프라를 CDK로 만듦 |
| [aws/aws-cdk](https://github.com/aws/aws-cdk), [cdklabs/cdk-nag](https://github.com/cdklabs/cdk-nag) | `aws-cdk-lib` 2.276.0과 cdk-nag 3.0.2 고정. 2.276.0은 CDK CLI 2.1148.1과 호환되고, `aws-cdk-lib` 2.277.0으로 올리려면 CLI 2.1148.2 이상이 필요(저장소 `cdk/requirements.txt` 주석 기준) |
| [aws/sagemaker-hyperpod-cli](https://github.com/aws/sagemaker-hyperpod-cli) | HyperPod 의존성 Helm chart(`helm_chart/HyperPodHelmChart`): health monitoring agent, deep health check RBAC, job-auto-restart, MPI operator, device plugin, Kueue |
| [awslabs/awsome-distributed-ai veRL 예제](https://github.com/awslabs/awsome-distributed-ai/tree/main/examples/training/verl/hyperpod-eks/rlvr) | HyperPod EKS의 veRL RLVR 예제, veRL v0.6.1 고정(이전 키), 이전 aws-samples/awsome-distributed-training에서 이동 |
| [TRL 문서](https://huggingface.co/docs/trl), [huggingface/trl](https://github.com/huggingface/trl), [PyPI trl 1.18.0](https://pypi.org/project/trl/1.18.0/) | TRL 1.18.0(2026-11-13), vLLM 0.23부터 0.33.x 지원, GRPOConfig 기본값(`num_generations` 8, `beta` 0.0, `loss_type` "dapo", `scale_rewards` "group"), reward 함수의 `None` 처리, async reward 함수 |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | vLLM 0.33.0은 torch 2.14.0과 `transformers>=5.16.1,<5.21`을 고정, 이미지 `vllm/vllm-openai:v0.33.0` |
| [verl-project/verl](https://github.com/verl-project/verl) | veRL 0.9.1, `reward.*` 키, `compute_score` 시그니처와 반환 형식, sandbox 실행에는 async 권장, Parquet 열 |
| [kuberay-project/kuberay](https://github.com/kuberay-project/kuberay) | KubeRay v1.7.2, API `ray.io/v1` |
| [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct), [7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) | apache-2.0, gate 없음 |
| [Qwen2.5-Coder-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct) | qwen-research(비상업) 라이선스, 이 저장소에서 쓰지 않음 |
| [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) | v1.0.11(2026-11-12), CRD v1beta1(Sandbox, SandboxTemplate, SandboxWarmPool, SandboxClaim), RuntimeClass로 격리를 런타임에 맡김, Kata 예시와 GKE gVisor + L4 GPU 예시, SDK(Python `k8s-agent-sandbox`, Go, TypeScript), sandbox-router |
| [agent-sandbox v1.0.11 설치 매니페스트](https://github.com/kubernetes-sigs/agent-sandbox/releases/download/v1.0.11/sandbox-with-extensions.yaml) | controller와 extension을 한 번에 설치하는 매니페스트 |
| [AI on EKS: Agent Sandbox on EKS](https://awslabs.github.io/ai-on-eks/ko/docs/infra/agents/agent-sandbox), [awslabs/ai-on-eks](https://github.com/awslabs/ai-on-eks) | gVisor 커널 격리, agent-sandbox CRD(Sandbox, SandboxTemplate, SandboxWarmPool, SandboxClaim, v1beta1)로 수명 주기 관리, GPU 언급 없음(2026-11 확인). 나머지는 표 아래 목록 |
| [opensandbox-group/OpenSandbox](https://github.com/opensandbox-group/OpenSandbox) | release-1.2.1, Pool과 BatchSandbox(v1alpha1) |
| [bytedance/SandboxFusion](https://github.com/bytedance/SandboxFusion) | `POST /run_code`, GPU 실행은 직렬화 |

- **gVisor GPU 지원의 나머지 내용**: NVIDIA open 드라이버 기준 설명(proprietary 드라이버 언급 없음), 문서화된 GPU(T4, A100/A10G, L4, H100), CDI 호환, 보안 범위("much less effective ...", DMA buffer 미검증), VM에서는 systrap 플랫폼
- **AI on EKS의 egress와 노드 구성**: FQDN 기반 egress 제어(Standard EKS는 Cilium, EKS Auto Mode는 `ApplicationNetworkPolicy`), KRO의 `AgentSandbox` 리소스, Karpenter와 gVisor NodePool(`runsc`를 AL2023 user data로 설치)
- **AI on EKS의 런타임 계층**: `standard`(runc), `gvisor`(Auto Mode 미지원), `isolated-sandbox`(Nitro Sandboxes, EKS Auto Mode의 Kubernetes 1.36 이상 또는 custom AMI를 쓰는 Standard EKS), Kata + Firecracker는 향후 계층(미포함)

### 논문, 블로그, reward hacking 보고

| 출처 | 뒷받침하는 사실 |
|---|---|
| [KernelBench](https://github.com/ScalingIntelligence/KernelBench) | MIT, `ModelNew` 계약, allclose(fp32 1e-4, fp16/bf16 1e-2), 정확성 5회와 성능 100회, L2 flush를 포함한 cuda_event timing, `excessive_speedup_threshold` 10, 추가 stream으로 생기는 측정 허점과 모든 stream을 측정하는 host_time 모드 |
| [KernelBench v0.1 블로그](https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/) | reward hacking 유형: torch와 cuBLAS 호출, 커널을 호출하지 않음, 메모리를 재사용하는 no-op 커널, stream timing 불일치 |
| [Sakana AI CUDA Engineer](https://sakana.ai/ai-cuda-engineer/) | 메모리 exploit으로 정확성 검사를 건너뛴 사례 |
| [Kevin-32B (Cognition)](https://cognition.com/blog/kevin-32b) | reference 복사, try/except fallback, reference 클래스 상속, PyTorch만 쓴 completion에 0점 |
| [CUDA-L1 (arXiv 2507.14111)](https://arxiv.org/abs/2507.14111) | 추가 stream이 250건 중 82건(32.8%)에서 timing을 속임, lazy evaluation, caching |
| [INTELLECT-3 (arXiv 2512.16144)](https://arxiv.org/abs/2512.16144) | API를 거친 `kubectl exec`가 명령당 약 2.5 s, gateway + headless Service + sidecar 구성, environment를 trainer와 독립적으로 버전 관리 |

### 원출처 미확인

아래 자료는 1차 출처 URL을 확인하지 못했습니다. 인용하려면 원문을 직접 찾아 확인하세요.

- **Northflank**: GPU에 Kata를 쓰고, nested virtualization을 쓸 수 없으면 gVisor로 대체한다는 공개 자료
- **TritonRL**: 규칙 기반 linter와 LLM judge를 함께 쓰는 접근
- **KernelBench-Verified**: reward hacking 대응과 관련해 함께 언급되는 작업

관련 페이지: [자주 하는 오해](faq.md), [문제 해결](troubleshooting.md), [04 Reward 무결성](../production/04_reward_integrity.md), [04 플랫폼과 인스턴스 선택](../concepts/04_platforms_and_instances.md)
