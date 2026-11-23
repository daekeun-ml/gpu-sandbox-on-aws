# 03 GPU까지 격리하려면

모델에게 두 배열을 더하는 함수를 작성하게 했다고 해 봅시다. CPU용 함수라면 샌드박스에서 단위 테스트로 답을 확인할 수 있습니다. 같은 계산을 GPU에서 얼마나 빠르게 끝내는지가 과제라면, 코드를 실행하는 샌드박스에도 GPU가 필요합니다.

## GPU 커널과 드라이버

**GPU 커널**은 GPU에서 실행되는 계산 코드입니다. [앞 편](02_container_vs_sandbox.md)에서 파일 접근을 처리하던 운영체제 커널과는 이름만 같습니다. Python 프로그램이 GPU에 계산을 요청하면 **GPU 드라이버**가 해당 요청을 장치에 전달합니다.

두 구현이 같은 정답을 냈다고 가정해 봅시다. A10G에서 기존 코드가 4 ms, 새 코드가 2 ms 걸렸다면 그 조건에서 새 코드가 2배 빠릅니다. 배포할 GPU가 L4라면 같은 입력으로 두 구현을 L4에서 다시 측정합니다. GPU에 따라 계산 속도와 메모리 접근 속도가 달라져 두 구현의 순위도 바뀔 수 있기 때문입니다.

## EKS에서 샌드박스 구성 고르기

EKS에서는 Kubernetes가 pod를 실행할 노드를 고릅니다. **Kata**를 런타임으로 지정하면 그 노드에 가상 머신(VM)을 띄우고 그 안에서 pod의 컨테이너를 실행합니다. VM을 띄우는 프로그램을 **hypervisor**라고 합니다. Kata는 이 역할을 QEMU나 Cloud Hypervisor에 맡깁니다.

| 구성 | 이 저장소에서 실습하는 내용 |
|---|---|
| gVisor | `nvproxy`가 지원하는 GPU 요청만 노드의 NVIDIA 드라이버에 전달합니다. 드라이버 버전이 맞으면 일반 GPU 인스턴스에서 시작할 수 있습니다. [gVisor GPU 실습](../handson/02_gvisor.md) |
| Kata + QEMU | 물리 GPU를 VM에 직접 할당합니다. 이 방식을 **GPU passthrough**라고 합니다. 실습에서는 VM 안의 드라이버가 `g4dn.metal`의 T4 한 장을 제어합니다. [Kata GPU 실습](../handson/03_kata.md) |
| Kata + Cloud Hypervisor | GPU 없이 `c8i`에서 pod마다 VM을 띄워 격리를 확인합니다. [CPU 전용 실습](../handson/10_cpu_only.md) |

### Cloud Hypervisor의 GPU 지원 범위

Cloud Hypervisor로 VM을 직접 관리할 때는 운영자가 물리 GPU를 지정해 VM에 연결할 수 있습니다. EKS에서 Kata로 GPU pod를 띄울 때는 Kata가 그 pod에 할당된 GPU를 VM에 연결하고 컨테이너가 쓸 수 있게 해야 합니다. Kata가 지원하는 NVIDIA GPU 구성은 QEMU를 사용합니다. 이 저장소의 Kata + Cloud Hypervisor GPU 실험은 VM 부팅에서 타임아웃이 났습니다. [Cloud Hypervisor 문서](https://github.com/cloud-hypervisor/cloud-hypervisor/blob/v55.0/docs/vfio.md) [Kata 지원표](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md#types) [GPU 실험 기록](../handson/03_kata.md#3단계-선택-실험-kata--cloud-hypervisor-gpu)

## GPU 요청을 전달하는 경로

![gVisor는 GPU 요청을 노드 드라이버로 전달하고, Kata + QEMU는 VM 내부 드라이버로 GPU를 사용합니다.](../images/figures/beginner-03_gpu_sandbox--gpu-path.ko.svg)

`ioctl`은 프로그램이 드라이버에 장치 관련 요청을 보내는 시스템 호출입니다. 여기서는 gVisor가 그 요청을 확인하는 위치를 보면 됩니다.

### 드라이버가 있는 위치가 중요한 이유

| 질문 | gVisor + nvproxy | Kata + QEMU |
|---|---|---|
| 누가 GPU 요청을 처리하나요? | nvproxy가 허용한 요청을 노드의 NVIDIA 드라이버가 처리합니다. | 게스트의 NVIDIA 드라이버가 할당받은 GPU를 제어합니다. |
| 어떤 조건을 먼저 확인하나요? | 노드 드라이버 버전이 설치한 gVisor에서 지원되는지 확인합니다. | 노드가 VM을 띄울 수 있고 IOMMU를 통해 물리 GPU를 게스트에 할당할 수 있어야 합니다. |
| pod를 하나 더 띄우려면? | 기본 `g5.xlarge`에는 A10G가 한 장이어서 이미 사용 중이면 노드가 더 필요합니다. | `g4dn.metal`의 T4 중 한 장과 VM용 CPU·메모리가 비어 있어야 합니다. |

그래서 GPU 요청이 `Pending`이면 어떤 런타임을 골랐는지와 남은 장치 수를 함께 봅니다. 반대로 `Running`인 pod에서 첫 GPU 연산이 실패했다면, 어느 쪽 드라이버와 장치 연결을 살필지가 위 표에서 달라집니다.

## GPU 한 장에 답 하나를 보내면

`g5.xlarge`에서는 gVisor가 GPU 장치 요청을 검사하고 노드의 NVIDIA 드라이버에 전달합니다. 노드의 드라이버 버전이 `nvproxy`의 지원 목록에 있는지 확인하세요. `g4dn.metal`에서 Kata + QEMU를 쓰면 물리 GPU 한 장을 게스트 VM에 연결하고, 게스트 안의 드라이버가 연산을 실행합니다. VM에서 어떤 GPU가 보이는지, 그 GPU에서 첫 연산이 끝나는지 확인합니다. IOMMU는 그 장치가 접근할 수 있는 메모리 주소 범위를 제한합니다.

![Kata 게스트 안에서 확인한 T4와 GPU 연산 결과](../images/terminal/kata-gpu-replay.png)

같은 커널을 두 pool에 보내도 처리량은 달라질 수 있습니다. EKS 실습에서 gVisor pool은 A10G 두 장으로 초당 0.198건, Kata QEMU pool은 T4 네 장으로 초당 0.349건을 처리했습니다. Kata QEMU pool은 gVisor pool보다 동시에 채점할 수 있는 답안 수가 두 배였습니다. **코드 자체의 속도**를 비교하려면 같은 GPU에서 기준 구현과 제출 코드를 돌려 보고, **pool 용량**을 정하려면 전체 처리량과 Ready pod 수를 함께 보세요. [측정 조건과 원본 결과](../handson/08_benchmark.md#runtime-results)

다른 GPU 작업의 예는 [GPU 샌드박스가 필요한 경우](../concepts/01_why_gpu_sandbox.md), 노드별 GPU 연결 조건은 [격리 런타임 비교](../concepts/02_isolation_runtimes.md)에서 볼 수 있습니다. [다음 편](04_rl_and_sandbox.md)에서는 실행 결과를 학습 점수로 바꿉니다.
