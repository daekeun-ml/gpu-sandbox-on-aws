# 격리 런타임 비교

!!! info "TL;DR"
    gVisor는 애플리케이션의 시스템 호출을 사용자 공간 커널에서 처리합니다. Kata는 pod마다 별도의 커널이 있는 VM을 띄웁니다. GPU를 붙이는 방식도 달라서 필요한 AWS 노드가 달라집니다.

## 코드가 운영체제에 일을 부탁할 때

파일을 열거나 GPU를 사용하려면 프로그램이 운영체제에 요청을 보냅니다. 모델이 만든 코드도 마찬가지입니다. 격리 런타임을 고를 때는 그 요청을 어디서 받아 처리할지 정합니다.

| 런타임 | 요청을 처음 받는 곳 | 이 저장소에서 쓰는 곳 |
|---|---|---|
| runc | 노드의 Linux 커널 | trainer와 시스템 pod |
| gVisor | 사용자 공간 커널(Sentry) | CPU 및 GPU 샌드박스 |
| Kata | pod마다 띄운 VM의 Linux 커널 | CPU 샌드박스, QEMU 기반 GPU 샌드박스 |

## GPU 경로 두 가지

### gVisor + nvproxy

`nvproxy`는 GPU에 보내는 요청 가운데 자신이 지원하는 요청만 노드의 NVIDIA 드라이버로 전달합니다. 일반 GPU VM에서도 쓸 수 있지만 드라이버 버전이 `nvproxy` 지원 목록과 맞아야 합니다.

### Kata + VFIO passthrough

GPU를 작은 VM에 직접 연결하고 VM 안의 NVIDIA 드라이버가 장치를 제어합니다. 이 저장소의 x86 GPU 실습에서는 T4가 있는 `g4dn.metal`을 씁니다. CPU만 쓰는 Kata는 `c8i`의 중첩 가상화로 실습할 수 있습니다.

![gVisor는 노드 드라이버로 GPU 요청을 전달하고, Kata의 VM은 연결된 GPU를 자체 드라이버로 사용합니다.](../images/figures/concepts-02_isolation_runtimes--gpu-paths.svg)

## AWS에서 각 런타임을 실행할 수 있는 위치

| 실습 | 노드 | 확인할 조건 |
|---|---|---|
| gVisor GPU | EC2 `g5.xlarge` | 노드 드라이버가 nvproxy 지원 목록에 있음 |
| Kata GPU | EC2 `g4dn.metal` | GPU passthrough용 AMI와 IOMMU 설정 |
| Kata CPU | EC2 `c8i.2xlarge` | 중첩 가상화 활성화 |

격리 경계는 실행 경로의 일부입니다. 풀 접근 권한과 네트워크 제어도 함께 확인해야 합니다. 직접 비교하려면 [gVisor 핸즈온](../handson/02_gvisor.md)과 [Kata 핸즈온](../handson/03_kata.md)을 보세요.

## 더 살펴보기

??? note "네 런타임의 구조"
    runc에서는 컨테이너가 host 커널을 공유합니다. gVisor에서는 사용자 공간 커널(Sentry)이 syscall을 먼저 처리합니다. Kata는 pod마다 별도의 VM(guest 커널)을 실행합니다.

    | 항목 | runc | gVisor (runsc) | Kata (QEMU, Cloud Hypervisor) | Firecracker |
    |---|---|---|---|---|
    | syscall을 처리하는 곳 | host kernel | Sentry(사용자 공간 커널). VM에서는 systrap 플랫폼, KVM 플랫폼은 bare metal에서만 | VM 안의 guest kernel | microVM 안의 guest kernel |
    | 격리 경계 | namespace, cgroup, seccomp | 사용자 공간 커널 | 하드웨어 가상화 (KVM) | 하드웨어 가상화 (KVM), 최소 장치 모델 |
    | NVIDIA 드라이버 위치 | host | host | guest (host에는 NVIDIA 드라이버를 설치하지 않음) | 해당 없음 |
    | GPU 경로 | device node 직접 접근 | nvproxy가 허용된 ioctl만 host 드라이버로 전달 | VFIO passthrough (cold-plug) | 없음 |
    | `/dev/kvm` | 불필요 | 불필요 (systrap) | 필요 | 필요 |
    | 이 저장소에서 | trainer와 시스템 pod | `gvisor` RuntimeClass (handler `runsc`) | `kata-qemu-nvidia-gpu`, `kata-qemu`, `kata-clh` | 사용하지 않음 (Kata의 hypervisor로도 쓰임) |

    세 런타임 모두 같은 샌드박스 이미지를 씁니다. 이미지에는 NVIDIA 커널 드라이버가 없고, PyTorch wheel에 포함된 CUDA 사용자 공간 라이브러리만 들어 있습니다.

??? note "Kata의 hypervisor: QEMU와 Cloud Hypervisor"
    | 항목 | QEMU | Cloud Hypervisor (CLH) |
    |---|---|---|
    | CPU 샌드박스 | 지원 (`kata-qemu`) | 지원 (`kata-clh`) |
    | GPU passthrough | upstream 지원 (`kata-qemu-nvidia-gpu`) | upstream 미지원. 이 저장소은 실험용 `kata-clh-nvidia-gpu`만 제공 |
    | RuntimeClass `overhead.podFixed` (Kata 4.3.1) | 320Mi, 250m. GPU class는 10240Mi, 1 CPU | 130Mi, 250m. 실험용 `kata-clh-nvidia-gpu`는 10240Mi, 1 CPU |
    | boot to workload (Kata metrics CI, 3.28.0) | 0.71 s | 0.39 s |

    `overhead.podFixed`는 RuntimeClass에 지정된 설정값이며 측정값이 아닙니다. 스케줄러는 이 값을 VM 자체가 사용하는 메모리와 CPU로 보고 pod 요청량에 합산합니다.

    Cloud Hypervisor의 GPU 지원 상태는 다음과 같습니다.

    - **upstream 문서**: `docs/hypervisors.md`는 Cloud Hypervisor의 GPU 지원을 not supported로 표시합니다.
    - **maintainer 답변**: 2025-08에 "You should use the QEMU GPU runtime class. I haven't done any work on CLH to enable proper GPU support."라고 답했습니다.
    - **Go `kata-clh` shim**: 3.29.0부터 VFIO cold-plug 코드가 있지만, upstream 테스트가 없고 배포 설정에서는 비활성화돼 있습니다.
    - **runtime-rs**: CLH 설정에는 VFIO 키가 없습니다.

    그래서 Kata에서 upstream이 GPU를 지원하는 hypervisor는 QEMU뿐입니다. 이 저장소은 CLH + GPU를 `infra/kata/experimental-clh-gpu/`에서 평가용(CI 없음)으로만 제공합니다. CLH는 CPU 샌드박스에서는 지원되며, CPU 계층(`kata-clh-cpu` 프로필)이 이 조합을 사용합니다.

    !!! warning "오버헤드 수치를 읽는 법"
        - **위 boot 시간**: Kata metrics CI(3.28.0)가 서로 다른 머신에서 넓은 허용 오차로 측정한 값이며 AWS 측정값이 아닙니다.
        - **AWS China 블로그의 "CLH 약 130 MB, QEMU 약 160 MB"**: Kata 3.31.0의 `podFixed` 기본값과 같아서 측정값이 아닐 가능성이 높습니다(추론). 같은 글에 실린 측정값은 cold start 약 3 s, 미리 시작해 둔 pool에서 가져올 때 약 230 ms입니다.
        - **AWS 실습 계정에서 측정한 값**: [08 런타임 벤치마크](../handson/08_benchmark.md)에 있습니다. 그 표의 cold start는 pod 생성부터 Ready까지의 시간이라 위 표의 boot to workload와 측정 구간이 다릅니다. `g4dn.metal`에서 GPU 프로필 `kata-qemu`(RuntimeClass `kata-qemu-nvidia-gpu`)로 띄운 pod 4개는 중앙값 30.5초였습니다.

    `kata-qemu-nvidia-gpu`의 VM 크기는 `default_memory` 8192 MiB에 컨테이너 limit을 더한 값입니다. VFIO type1은 guest RAM 전체를 pin하므로 메모리를 overcommit할 수 없습니다. 이 저장소의 프로필은 T4 pod마다 8 CPU, 16 GiB를 할당합니다. 8 x (16 + 10) GiB = 208 GiB이므로 `g4dn.metal`의 384 GiB 안에 들어갑니다.

??? note "격리 강도와 남는 위험"
    | 런타임 | 신뢰할 수 없는 코드와 host 사이 | 남는 위험 | 이 저장소의 보완 |
    |---|---|---|---|
    | runc | host kernel과 드라이버를 공유 | kernel이나 드라이버 취약점이 그대로 노출 | 샌드박스에 쓰지 않음 |
    | gVisor + nvproxy | syscall은 Sentry, GPU는 ioctl allowlist | VM 경계보다 약함(표 아래 목록) | pod마다 GPU 1개(time-sharing 없음), 노드당 샌드박스 1개, egress 차단을 확인한 뒤 Ready, node guard iptables |
    | Kata + VFIO | VM 경계 + IOMMU | hypervisor와 GPU 장치 자체(표 아래 목록) | v2는 200회 평가 후 pod를 draining으로 바꾸고, Production gateway의 recycler가 그 pod를 삭제하고 새 pod(Kata에서는 새 VM)로 교체 |
    | Kata (CPU 전용) | VM 경계 | hypervisor | 같은 네트워크 통제 |

    - **gVisor + nvproxy의 남는 위험**: gVisor 문서 기준 nvproxy는 "much less effective at mitigating vulnerabilities within the NVIDIA GPU drivers themselves"이고 "no validation of things like DMA buffers"입니다.
    - **Kata + VFIO의 남는 위험**:
        - DMA는 IOMMU가 VM 안으로 제한합니다(unsafe noiommu 모드는 켜지 않음).
        - vfio-pci는 해제 시 function(또는 bus)을 reset하며, T4는 `reset_method=bus`로 보고됩니다(제3자 보고, NVIDIA 보증 아님).
        - T4에는 confidential computing이 없습니다.

    GKE Sandbox 문서도 "Don't use GPU time-sharing in sandboxed Pods"라고 권고합니다. 보안 경계 전체와 위협 모델은 [Production 02 보안](../production/02_security.md)에서 다룹니다.

??? note "적용 범위와 한계"
    - **T4 on gVisor:** 위 AMI 조건 때문에 검증하지 않은 조합입니다.
    - **Kata + GPU on `g4dn.metal`:** upstream에서 검증되지 않은 구성입니다. NVIDIA CI는 A100과 H100을 테스트하고 T4는 테스트하지 않습니다. NVIDIA가 검증한 EKS 구성은 Ubuntu 기반입니다(AL2023 없음).
    - **HyperPod 노드의 Kata CPU:** 불가로 판단하지만 직접 확인하지 않았습니다.

    ??? note "참고 자료"
        | 주제 | 링크 |
        |---|---|
        | EC2 nested virtualization (User Guide, What's New) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html , https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
        | EC2 가속 컴퓨팅 인스턴스 사양 | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
        | gVisor 설치, GPU 지원, GitHub | https://gvisor.dev/docs/user_guide/install/ , https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
        | Kata NVIDIA GPU passthrough (4.3.1), CLH GPU 이슈 | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers/issues/11687 |
        | 이 저장소의 런타임 설정 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/gvisor/install-gvisor.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/kata-deploy-values.yaml , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/gpu-operator-values.yaml |

        전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-concepts-02-isolation-runtimes)
