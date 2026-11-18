# 03 GPU까지 격리하려면

**TL;DR** GPU 코드는 커널 안의 드라이버에 명령을 보내므로, GPU를 샌드박스에 연결하는 방식에 따라 격리 수준이 달라집니다. gVisor는 드라이버로 가는 명령을 검사해 전달하고, Kata는 GPU를 VM에 직접 할당합니다.

## 기존 Pain Point

코드 채점용 샌드박스는 보통 CPU만 있으면 되므로, 널리 쓰이는 microVM 샌드박스(Firecracker 기반 등)에는 GPU를 VM에 연결하는 장치가 없습니다. 하지만 GPU 커널이 얼마나 빨라졌는지를 점수로 주려면 채점 환경에 실제 GPU가 있어야 해요. GPU 드라이버는 커널 안에서 실행되므로 드라이버의 버그는 커널의 버그와 같습니다. 컨테이너 격리만으로는 코드가 드라이버에 명령을 보내는 경로를 막을 수 없어요.

![a: GPU 커널 채점에는 실제 GPU가 필요합니다. Firecracker 기반 microVM에는 GPU를 연결할 장치가 없어 채점할 수 없고, 일반 컨테이너(runc)에서는 드라이버 버그가 서버 커널에 영향을 줍니다. b: gVisor + nvproxy(g5.xlarge)는 ioctl을 검사해 허용 목록에 있는 명령만 서버의 드라이버로 전달합니다. Kata + VFIO(g4dn.metal)는 GPU를 VM에 직접 할당하므로 드라이버 버그의 영향이 VM 안으로 한정됩니다.](../images/figures/beginner-03_gpu_sandbox.svg)

*그림 요약: GPU가 없는 microVM에서는 채점할 수 없고, 일반 컨테이너에서는 드라이버 버그가 서버 커널에 영향을 줍니다. gVisor + nvproxy는 허용 목록의 명령만 서버 드라이버로 전달하고, Kata + VFIO는 GPU와 드라이버를 VM 안에 격리합니다.*


## Why

- **코드가 GPU에 명령을 보내는 경로를 단계별로 설명하고, 각 방식이 어느 지점에 격리 경계를 두는지 정리합니다.**
- **두 방식의 장단점을 표로 비교합니다.** 격리 수준, 필요한 서버, 쓸 수 있는 GPU가 방식마다 달라요.
- **방식별로 AWS에서 쓸 인스턴스도 정리합니다.**

**사전 지식:** [02편](02_container_vs_sandbox.md)의 세 가지 격리 방식(runc, gVisor, Kata)을 먼저 보세요.

??? note "용어 (처음 보는 단어가 있으면 펼치세요)"
    - **GPU 드라이버:** 운영체제가 GPU를 제어할 수 있게 해 주는 프로그램입니다. NVIDIA 드라이버는 커널 안에서 실행돼요.
    - **ioctl:** 프로그램이 장치 드라이버에 명령을 보낼 때 쓰는 시스템 호출입니다. CUDA 라이브러리도 GPU에 작업을 시킬 때 ioctl로 드라이버에 명령을 보내요.
    - **nvproxy:** gVisor가 GPU 명령(ioctl)을 검사해서, 허용 목록에 있는 것만 서버의 드라이버로 전달하는 기능입니다.
    - **VFIO passthrough:** GPU 한 장을 VM에 직접 할당해, VM 안에서 그 GPU를 쓰게 하는 방식입니다.
    - **IOMMU:** 장치(GPU)가 접근할 수 있는 메모리 범위를 하드웨어로 제한하는 기능입니다. passthrough에 꼭 필요해요.
    - **bare metal(`.metal`):** 물리 서버 전체를 VM 없이 쓰는 EC2 인스턴스입니다.
    - **nested virtualization:** VM 안에서 다시 VM을 띄우는 기능입니다. EC2에서는 일부 인스턴스 계열에서 켤 수 있어요.

## GPU 접근 경로

![GPU 접근 경로는 PyTorch 코드, CUDA 라이브러리, ioctl(장치 명령), 커널 안의 NVIDIA 드라이버, GPU 순서로 이어집니다. gVisor + nvproxy는 드라이버 앞의 ioctl 단계에 격리 경계를 두고, 명령을 검사해 허용 목록에 있는 것만 전달합니다. 아래 괄호는 Kata + VFIO passthrough의 범위로, 코드부터 드라이버와 GPU까지 모두 pod의 VM 안에 있습니다.](../images/figures/beginner-03_gpu_sandbox--gpu-path.svg)

*그림 요약: GPU로 보내는 모든 명령은 커널 안의 드라이버를 거칩니다. gVisor는 드라이버 앞에서 명령을 검사하고, Kata는 코드부터 GPU까지 전체 경로를 VM 안에 둡니다.*


## 두 가지 방식

**gVisor: GPU 명령(ioctl)을 검사하기 (nvproxy)**

gVisor 안의 프로그램이 GPU 명령(ioctl)을 보내면, nvproxy가 드라이버 버전별 허용 목록과 비교해 목록에 있는 명령만 서버의 드라이버로 전달하고 나머지는 거절합니다. PyTorch 코드는 바꿀 필요가 없어요.

- **좋은 점:** 일반 GPU 인스턴스(예: `g5.xlarge`)에서 실행할 수 있고, 오버헤드가 작으며 pod가 빨리 시작됩니다.
- **약점:** 서버의 드라이버가 허용 목록에 없는 버전이면 GPU를 쓸 수 없고, 검사를 통과한 명령은 서버의 드라이버가 그대로 처리합니다. gVisor 문서도 nvproxy가 "NVIDIA 드라이버 자체의 취약점을 막는 데는 훨씬 덜 효과적"이라고 설명합니다.

**Kata: GPU를 VM에 직접 할당하기 (VFIO passthrough)**

Kata는 GPU 한 장을 그 pod의 VM에 직접 할당합니다. 드라이버도 VM 안에서 실행되므로 드라이버에 문제가 생겨도 영향이 그 VM 안으로 한정돼요. IOMMU는 GPU가 접근할 수 있는 메모리를 그 VM의 메모리로 제한합니다.

- **좋은 점:** 두 방식 중 격리 수준이 더 높습니다.
- **약점:** 서버가 GPU를 직접 제어해야 해서 서버 조건이 까다롭습니다. `/dev/kvm`과 IOMMU가 필요하고, 서버에서는 NVIDIA 드라이버를 로드하지 않아요. 업스트림 Kata가 공식 지원하는 GPU 구성은 QEMU 하이퍼바이저를 쓰는 구성이고, Cloud Hypervisor의 GPU 지원은 아직 실험 단계입니다.

| 항목 | gVisor + nvproxy | Kata + VFIO |
|---|---|---|
| 격리 경계 | 드라이버로 가는 명령을 검사 | GPU와 드라이버를 모두 VM 안에 둠 |
| 드라이버 버그 | 서버 드라이버의 버그가 영향을 줄 수 있음 | 영향이 VM 안으로 한정됨 |
| 필요한 서버 | 일반 GPU 인스턴스 | GPU를 직접 제어할 수 있는 bare metal |
| 드라이버 버전 | 허용 목록과 정확히 맞아야 함 | VM 안의 드라이버를 따로 고름 |
| 이 저장소의 선택 | `g5.xlarge`(A10G) 노드당 샌드박스 하나 | `g4dn.metal`(T4 8장)에서 VM마다 T4 한 장 |

!!! question "❓ 오해: gVisor로 GPU를 쓰면 VM만큼 안전하다"
    nvproxy의 검사를 통과한 명령은 서버의 드라이버로 전달됩니다. 검사는 드라이버 버그를 악용할 수 있는 명령의 종류를 줄일 뿐 없애지는 못합니다. VM 수준의 격리가 필요하면 Kata + GPU를 고려합니다.

## AWS에서 고르는 인스턴스

| 하고 싶은 것 | 인스턴스 | 이유 |
|---|---|---|
| gVisor로 GPU 샌드박스 | `g5.xlarge` 같은 일반 GPU VM | gVisor는 KVM이 필요 없고, 서버의 드라이버가 nvproxy가 지원하는 버전이면 됩니다 |
| Kata로 GPU 샌드박스 | `g4dn.metal` | GPU를 VM에 할당하려면 서버가 GPU를 직접 제어해야 해서 bare metal이 필요합니다. AWS의 x86 NVIDIA 인스턴스 중 bare metal은 `g4dn.metal`뿐입니다 |
| Kata로 CPU 샌드박스 | `c8i.2xlarge` 같은 nested virtualization 지원 VM | GPU 없이 VM만 띄우면 되니 `/dev/kvm`만 있으면 됩니다. 2026-02부터 일부 VM 계열에서 nested virtualization을 켤 수 있어요 |

!!! question "❓ 오해: Kata를 쓰려면 무조건 `.metal`이 필요하다"
    `.metal`은 Kata에 GPU를 할당할 때만 필요합니다. CPU만 쓰는 Kata는 nested virtualization을 켠 VM(예: [05편](05_hands_on.md)에서 세 런타임을 띄우는 `c8i.2xlarge`)에서 실행할 수 있어요. 반대로 GPU 인스턴스(G, P 계열)는 nested virtualization을 지원하지 않으므로 GPU VM에서는 Kata를 쓸 수 없습니다.

## GPU 샌드박스에서 하나 더 조심할 것

GPU 커널(GPU에서 실행되는 계산 함수)을 실행하면 GPU에 상태가 남습니다. 한 번의 실행이 GPU 상태를 망가뜨리면 다음 실행의 결과도 틀릴 수 있어요. 그래서 이 저장소는 채점마다 별도 프로세스에서 코드를 실행하고, 샌드박스 버전에 따라 일정 횟수마다 pod를 새로 띄웁니다. 채점이 왜 이렇게 정확해야 하는지는 다음 편에서 설명해요.

## 한 줄 정리

- GPU를 격리하는 방식은 두 가지입니다. GPU로 가는 명령을 검사하거나(gVisor), GPU를 VM에 직접 할당합니다(Kata).
- gVisor는 일반 GPU 인스턴스에서 실행할 수 있고, Kata + GPU는 격리 수준이 높은 대신 AWS에서 `g4dn.metal`이 필요합니다.

## 다음 편

[04 강화학습과 샌드박스](04_rl_and_sandbox.md)에서는 강화학습 중에 샌드박스가 모델의 코드를 채점하는 과정을 설명합니다.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | gVisor GPU 지원 (nvproxy) | https://gvisor.dev/docs/user_guide/gpu/ |
    | Kata Containers GPU passthrough | https://github.com/kata-containers/kata-containers/tree/main/docs/use-cases |
    | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
    | Accelerated computing 인스턴스 | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |

    전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-beginner-03-gpu-sandbox)
