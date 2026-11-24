# 03 샌드박스에서 GPU를 쓰는 방법 { #03-gpu까지-격리하려면 }

두 숫자 목록 `[-3, 2]`와 `[1, 1]`에서 같은 자리에 있는 수끼리 더하고, 음수는 0으로 바꾸는 문제를 생각해 봅시다. 기대하는 답은 `[0, 3]`입니다. CPU에서도 정답을 계산할 수 있습니다. 그런데 과제가 **GPU에서 이 계산을 더 빨리 끝내는 코드를 만드는 것**이라면, 샌드박스 안에서도 GPU로 코드를 실행해야 합니다.

## 같은 GPU에서 두 코드의 실행 시간을 측정합니다 { #gpu-커널과-드라이버 }

GPU가 실행하는 계산 코드를 **GPU 커널**이라고 합니다. 2편에서 본 **운영체제 커널**은 파일과 장치에 대한 요청을 처리합니다. 여기서 모델에게 작성해 달라는 것은 두 목록을 더하는 GPU 커널입니다.

예를 들어 같은 A10G GPU에 같은 입력을 주었을 때 기존 코드가 4밀리초(ms), 모델이 만든 코드가 2밀리초 걸렸다고 해 봅시다. 두 코드의 답이 모두 맞다면 새 코드는 이 조건에서 **2배** 빠릅니다(4 ÷ 2). 이 숫자는 계산 방법을 보여 주는 예입니다. 다른 GPU에서 쓸 코드라면 그 GPU에서 두 코드의 실행 시간을 다시 측정합니다.

<span id="eks에서-샌드박스-구성-고르기"></span>

## 샌드박스에서 GPU까지 어떻게 연결할까요? { #gpu-요청을-전달하는-경로 }

**드라이버**는 프로그램이 장치를 사용하도록 운영체제에서 요청을 처리하는 소프트웨어입니다. 이 실습에서 gVisor와 Kata는 서로 다른 위치의 NVIDIA 드라이버를 사용합니다.

![gVisor의 nvproxy는 요청을 노드 드라이버로 전달하고, Kata의 가상 머신은 자체 드라이버로 배정받은 GPU를 사용합니다.](../images/figures/beginner-03_gpu_sandbox--gpu-path.ko.svg?v=2)

- **gVisor**에서는 `nvproxy`가 샌드박스 안에서 보낸 GPU 요청을 검사합니다. 허용된 요청은 GPU가 장착된 노드의 NVIDIA 드라이버로 전달합니다. 이 실습에서는 `g5.xlarge`의 A10G를 사용합니다. [gVisor에서 GPU 확인하기](../handson/common/02_runtimes/gvisor.md)
- **Kata + QEMU**에서는 물리 GPU 한 장을 가상 머신(VM)에 직접 할당합니다. 이를 **GPU passthrough**라고 합니다. 실습에서는 VM 안의 NVIDIA 드라이버가 `g4dn.metal`의 T4 한 장을 사용합니다. [Kata VM에 GPU 연결하기](../handson/common/02_runtimes/kata.md#kata-gpu)

## 샌드박스에서 GPU가 보이는지 확인하기 { #gpu-한-장에-답-하나를-보내면 }

아래는 Kata VM에서 확인한 화면입니다. 마지막 명령은 PyTorch에 첫 번째 GPU의 이름을 묻습니다. `Tesla T4`가 출력됐으므로 **VM 안에서도 배정된 GPU가 보입니다.** 그 GPU에서 실제 코드가 올바르게 실행되는지는 시험용 답안을 보내 확인합니다. [GPU 샌드박스의 실행 결과](../handson/common/03_pools/details.md#gpu-verdicts)

![Kata VM에서 uname -r로 확인한 게스트 커널과 PyTorch가 출력한 GPU 이름 Tesla T4](../images/terminal/kata-gpu-replay.png)

<span id="드라이버가-있는-위치가-중요한-이유"></span>

??? note "GPU를 요청했는데 작업이 시작되지 않는다면"
    먼저 비어 있는 GPU가 있는지 확인하세요. 기본 `g5.xlarge`에는 A10G가 한 장입니다. 이미 다른 샌드박스가 쓰고 있다면 다음 샌드박스는 기다립니다. 실행은 시작됐는데 첫 연산에서 실패한다면 gVisor는 노드 드라이버의 지원 버전을, Kata는 VM에 장치가 배정됐는지와 VM 안의 드라이버를 확인합니다.

<span id="cloud-hypervisor의-gpu-지원-범위"></span>

??? note "Kata의 CPU 실습에서는 무엇이 달라지나요?"
    QEMU와 Cloud Hypervisor는 가상 머신을 실행하는 프로그램입니다. 이 가이드의 CPU 실습에서는 둘 다 `c8i` 노드에서 GPU 없이 비교합니다. NVIDIA GPU를 연결하는 Kata 실습에는 QEMU를 사용합니다. [CPU로 실습하기](../handson/scenarios/c/index.md) / [Kata의 GPU 지원 범위와 실험 기록](../handson/common/02_runtimes/kata.md#clh-gpu)

??? note "코드 한 번의 실행 시간과 여러 요청의 처리량"
    실행 시간은 한 답안의 코드가 얼마나 빨리 계산하는지 알려 줍니다. **처리량**은 샌드박스 여러 개가 함께 초당 몇 건의 채점을 끝내는지 나타냅니다. 이 실습의 gVisor 구성은 A10G 두 장으로 초당 0.198건, Kata + QEMU 구성은 T4 네 장으로 초당 0.349건을 처리했습니다. GPU 종류와 동시에 일한 샌드박스 수가 달라 이 값만으로 코드나 런타임의 속도를 비교하기는 어렵습니다. [벤치마크 조건과 결과](../handson/benchmarks/index.md#runtime-results)

다음 편에서는 두 코드가 모두 정답이더라도 학습 프로그램이 왜 서로 다른 점수를 주는지 살펴봅니다. [04 강화학습과 샌드박스](04_rl_and_sandbox.md)
