**한국어** | [English](README.en.md)

# GPU Sandbox on AWS

GPU Sandbox on AWS는 AI가 만든 코드를 GPU에서 실행해야 하는 팀을 위한 예제 코드와 실습 가이드입니다. 학습 서버와 분리된 실행 환경을 AWS에 직접 구축할 수 있도록 만들었습니다.

Amazon EKS의 EC2 노드에서 학습과 샌드박스를 함께 운영하는 구성부터 SageMaker HyperPod에서 학습을 실행하는 구성까지 다룹니다. 샌드박스는 gVisor와 Kata의 격리 방식, 지원 GPU, 필요한 노드를 비교해 고를 수 있습니다.

GRPO 실습에서는 모델이 작성한 코드를 GPU 샌드박스에서 채점하고, 정확도와 실행 속도를 reward로 써서 모델을 업데이트합니다. GPU 없이 채점 흐름부터 확인할 수 있는 CPU 실습도 있습니다.

[가이드북](https://daekeun-ml.github.io/gpu-sandbox-on-aws/) | [리플레이 데모](https://dohbsn4kn34ya.cloudfront.net/) | [이론 슬라이드 (PPTX)](slides/gpu-sandbox-theory.pptx) | [스크립트](SCRIPTS.md) | [문제 해결](TROUBLESHOOTING.md)

| 하고 싶은 일 | 어디서 시작할까요? |
|---|---|
| 샌드박스와 학습의 관계 이해하기 | [초심자 가이드](https://daekeun-ml.github.io/gpu-sandbox-on-aws/beginner/) |
| 내 PC에서 채점해 보기 | [로컬 실습](https://daekeun-ml.github.io/gpu-sandbox-on-aws/beginner/05_hands_on/) (AWS 계정과 GPU 불필요) |
| AWS에서 런타임 비교하기 | [CPU 전용 핸즈온](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/10_cpu_only/) (과금 발생) |
| GPU 채점과 모델 학습 연결하기 | [핸즈온 전체 흐름](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/00_overview/) (시나리오 A부터) |

## 아키텍처

![만드는 것: 학습 노드의 policy 모델과 vLLM이 버전을 고정한 채 gVisor, Kata + QEMU, Kata + Cloud Hypervisor(CPU 계층) 중 선택한 샌드박스 풀에 커널 코드를 보내고, 정확성과 speedup을 reward로 받는 구성](docs/images/figures/index--what-we-build.ko.svg)

*그림 요약: policy 모델이 쓴 커널 코드는 group 단위로 버전을 고정한 상태로 선택한 런타임의 샌드박스 풀에 전달되고, 풀이 측정한 정확성과 speedup이 reward로 쓰입니다. GPU 채점은 gVisor와 Kata + QEMU 풀이 맡고, Kata + Cloud Hypervisor는 기본적으로 CPU에서 실행합니다.*

A, B1, C는 프라이빗 EKS API를 제공하는 CDK 스택을 사용합니다. 관리형 B2는 HyperPod EKS 생성 마법사에서 제어 영역과 워커를 함께 구성합니다. C는 CPU 샌드박스에서 채점과 버전 교체를 실습합니다.

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

![Amazon EKS가 Pod를 배치하고 HyperPod의 system, trainer, sandbox 그룹이 실행하는 B2 구성도](docs/images/architecture/scenario-b2.drawio.png)

시스템용 CPU 워커와 학습·채점용 GPU 워커를 모두 HyperPod에 배치합니다. [B2 실습](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/07_hyperpod_b2/)

</details>

<details>
<summary><b>시나리오 C: CPU 전용</b></summary>

![시나리오 C: GPU 없이 c8i.2xlarge 한 대에 세 런타임의 CPU 풀이 있는 구성](docs/images/architecture/scenario-c.drawio.png)

*그림 요약: GPU 노드 없이 c8i.2xlarge 한 대에 세 런타임의 풀이 서고, system 노드의 simulate Job이 trainer 대신 golden 코드를 보냅니다.*

</details>

### 요청 경로

- trainer는 샌드박스에 요청을 보낼 때마다 routing ConfigMap(`sandbox-routing`)의 snapshot으로 런타임과 버전을 정하고, 한 reward batch의 결과는 한 풀에서 받습니다.
    - **학습 중에 v2로 바꾸면**: batch에 새로 채점할 답안이 있으면, 같은 batch에 든 이전 풀의 캐시 결과도 v2 풀에서 다시 채점합니다.
    - **batch 전체가 한 풀의 캐시로 채워지면**: 전환 뒤에도 샌드박스를 부르지 않고 그 결과를 씁니다.
    - **한 batch 안에서 전환이 거듭되면**: 세 번째 요청에서 batch 전체를 한 풀에 보내므로, 한 batch는 항상 한 버전으로 채점됩니다.
- trainer는 headless Service를 CoreDNS로 풀어 Ready 상태인 pod에 `POST /v1/evaluate`를 직접 보냅니다. 바쁜 pod는 `503`을 돌려주고, trainer는 다른 pod로 다시 시도합니다.
- 요청에는 audience가 `gpu-sandbox`인 projected ServiceAccount 토큰이 붙고, pod는 JWKS로 토큰을 오프라인 검증합니다. `sandbox` 네임스페이스는 default-deny라서 `rl-trainer`에서 label이 붙은 pod만 접속할 수 있습니다.

Production 구성(Karpenter NodePool, sandbox gateway, veRL on KubeRay)은 [Production 00 아키텍처](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/00_architecture/)에, 노드 그룹과 네임스페이스, 화살표별 설명은 [핸즈온 00 전체 흐름](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/00_overview/)에 있습니다. 그림 원본(`.drawio`)은 [`diagrams/`](diagrams/)에서 볼 수 있습니다.

## 시작하기

로컬 실습은 준비한 답안을 CPU로 채점하고, 정답, 오답, 정책 위반에 예상한 판정이 나오는지 확인합니다. 구성을 설치할 준비가 됐다면 [환경 설정](https://daekeun-ml.github.io/gpu-sandbox-on-aws/getting_started/)을 따라가세요.

AWS에서는 목적에 맞춰 경로를 고를 수 있습니다.

- **C (CPU 전용)**　모델 없이 채점 흐름을 실행해 보고 gVisor와 Kata를 비교합니다. [CPU 실습](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/10_cpu_only/)
- **A (EC2 GPU)**　GPU에서 커널을 채점하고 그 결과로 GRPO 학습을 실행합니다. [클러스터 준비](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/01_cluster_and_images/)
- **HyperPod B1과 B2**. B1은 HyperPod에서 학습하고 EC2에서 채점합니다. B2는 CPU 워커와 GPU 워커 세 대를 모두 HyperPod에 배치합니다. [B2 실습](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/07_hyperpod_b2/)

AWS 리소스는 사용하지 않는 동안에도 과금될 수 있습니다. 배포 전에 [비용 추정](https://daekeun-ml.github.io/gpu-sandbox-on-aws/concepts/04_platforms_and_instances/)을 확인하고, 실습이 끝나면 [정리 절차](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/99_cleanup/)를 따르세요.

## 더 살펴보기

- **격리 방식**　[gVisor와 Kata 비교](https://daekeun-ml.github.io/gpu-sandbox-on-aws/concepts/02_isolation_runtimes/)에서 GPU 연결 방식과 필요한 노드를 확인합니다.
- **Multi-turn 채점**　[Agent Sandbox 실습](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/11_multi_turn/)은 한 에피소드의 여러 제출을 같은 샌드박스로 보냅니다.
- **운영 구성**　[운영 아키텍처](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/00_architecture/)와 [보안 설계](https://daekeun-ml.github.io/gpu-sandbox-on-aws/production/02_security/)에 배포 경계와 운영 고려사항이 있습니다.

## 검증 상태

AWS 실습 계정에서 EC2 GPU 학습(A), CPU 채점과 버전 전환(C), Kata + QEMU의 GPU passthrough를 확인했습니다. Kata + Cloud Hypervisor는 C의 CPU 풀에서 검증했고, 별도 GPU 실험에서는 VM 부팅이 타임아웃으로 끝났습니다. HyperPod B1에서는 GRPO 한 스텝을 실행해 EC2 gVisor 샌드박스 2개로 제출 코드 12개를 채점했습니다. 관리형 B2는 CPU와 GPU 워커를 모두 HyperPod에 두고 GRPO 한 스텝과 벤치마크 64건을 완료했습니다. [실행 기록과 측정 범위](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/sources/#aws-실행-기록)

## License

코드와 문서는 [MIT](LICENSE)입니다. 모델과 데이터셋에는 각각의 라이선스가 적용됩니다.

이 저장소는 저자의 개인 견해와 조사 결과를 정리한 것으로, 저자가 재직 중인 회사의 공식 문서나 입장을 대변하지 않습니다.
