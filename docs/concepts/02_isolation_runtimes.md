# 격리 런타임 비교

**TL;DR** GPU 샌드박스 런타임은 syscall과 GPU ioctl을 처리하는 계층과 NVIDIA 드라이버의 위치로 구분됩니다. AWS에서 Kata + GPU는 이 저장소의 x86 구성 기준으로 `g4dn.metal`에서만 실행되고, gVisor + GPU는 일반 G/P 계열 VM에서 실행됩니다.

## 기존 Pain Point

gVisor와 Kata는 GPU 연결 방식이 다릅니다. gVisor는 허용된 ioctl만 host 드라이버로 전달하고, Kata는 GPU를 VM에 직접 할당해 guest 드라이버를 씁니다. "Kata에는 `.metal`이 필요하다"는 설명은 이제 GPU passthrough에만 해당합니다. 2026-02부터 CPU 샌드박스는 EC2 nested virtualization을 켠 일반 VM에서 실행할 수 있습니다. 또 Cloud Hypervisor는 QEMU와 달리 upstream에서 GPU를 지원하지 않습니다.

![세 열을 비교한 그림입니다. gVisor + GPU는 허용된 ioctl만 host 드라이버로 전달하고 /dev/kvm이 필요 없어서, g5.xlarge 같은 일반 GPU VM에서 동작합니다. Kata + GPU는 GPU를 VM에 직접 할당(VFIO)해 guest 드라이버를 쓰고, /dev/kvm, IOMMU, GPU를 소유한 host가 필요해 g4dn.metal에서만 동작합니다. 이 조합에서 upstream이 지원하는 hypervisor는 QEMU뿐이고 Cloud Hypervisor는 지원하지 않습니다(두 칸은 빨간색). Kata CPU 전용은 GPU를 쓰지 않고, nested virtualization이 /dev/kvm을 제공하므로 2026-02부터 c8i.2xlarge 같은 VM에서 Cloud Hypervisor와 QEMU 모두로 동작합니다.](../images/figures/concepts-02_isolation_runtimes.svg)

*그림 요약: gVisor와 Kata는 GPU를 연결하는 방식이 다릅니다. `.metal` 인스턴스가 필요한 조합은 Kata + GPU뿐이고, 이 조합에서 upstream이 지원하는 hypervisor는 QEMU입니다.*


## Why

- **런타임마다 syscall 처리 위치, 드라이버 위치, GPU 접근 경로, `/dev/kvm` 필요 여부가 다릅니다.** 이 차이가 AWS에서 쓸 수 있는 인스턴스를 정합니다.
- **boot 시간은 upstream CI 값입니다.** AWS에서 측정한 pod 생성부터 Ready까지의 시간과 평가 지연은 [08 런타임 벤치마크](../handson/08_benchmark.md)에 있습니다.

**사전 지식:** Kubernetes pod와 컨테이너를 알면 충분합니다. [01 GPU 샌드박스가 필요한 경우](01_why_gpu_sandbox.md)를 먼저 읽으면 좋습니다. 처음 보는 용어는 아래 "용어" 상자와 [용어 사전](../reference/glossary.md)에서 확인할 수 있습니다.

??? note "용어 (처음 보는 단어가 있으면 펼치세요)"
    - **런타임(container runtime)**: pod의 컨테이너를 실제로 만들고 실행하는 프로그램입니다. 기본값은 runc입니다.
    - **RuntimeClass**: pod가 어떤 런타임으로 실행될지 지정하는 Kubernetes 객체입니다. pod 스펙의 `runtimeClassName`으로 지정합니다.
    - **containerd shim**: containerd와 실제 런타임(runsc, Kata) 사이를 연결하는 작은 프로세스입니다. RuntimeClass의 `handler`가 어떤 shim을 쓸지 정합니다.
    - **syscall**: 프로그램이 커널에 파일 열기, 메모리 할당 같은 일을 요청하는 호출입니다.
    - **gVisor Sentry**: gVisor가 사용자 공간에서 실행하는 커널입니다. 컨테이너의 syscall을 host 커널 대신 처리합니다.
    - **systrap**: Sentry가 syscall을 가로채는 방식(플랫폼) 중 하나로, `/dev/kvm` 없이 일반 VM에서 동작합니다.
    - **ioctl**: 프로그램이 장치 드라이버에 명령을 보내는 syscall입니다. CUDA 라이브러리는 ioctl로 GPU 드라이버에 명령을 보냅니다.
    - **nvproxy**: gVisor가 GPU ioctl 중 허용 목록에 있는 것만 host NVIDIA 드라이버로 전달하는 기능입니다.
    - **KVM, `/dev/kvm`**: Linux 커널의 하드웨어 가상화 기능과 그 장치 파일입니다. Kata는 이것으로 VM을 만듭니다.
    - **IOMMU**: 장치가 메모리에 직접 접근(DMA)할 수 있는 범위를 제한하는 하드웨어입니다.
    - **VFIO, GPU passthrough**: 물리 GPU를 host 드라이버에서 분리해 VM에 직접 할당하는 Linux 기능과 그 방식입니다.
    - **cold-plug**: VM을 시작하기 전에 장치를 연결하는 방식입니다. VM 실행 중에 연결하는 hot-plug와 다릅니다.
    - **nested virtualization**: VM 안에서 다시 VM을 실행할 수 있게 하는 기능입니다. EC2에서 이 기능을 켜면 일반 VM에서도 `/dev/kvm`을 사용할 수 있습니다.
    - **bare metal (`.metal`)**: hypervisor 없이 물리 서버 전체를 쓰는 EC2 인스턴스입니다.
    - **CDI, device plugin**: CDI는 컨테이너에 장치를 연결하는 방법을 정의한 표준 명세입니다. device plugin은 노드의 GPU를 Kubernetes 리소스(`nvidia.com/gpu`)로 등록하는 구성 요소입니다.
    - **NodeConfig, nodeadm**: NodeConfig는 EKS AL2023 노드의 설정 문서이고, nodeadm은 이 설정을 부팅할 때마다 적용하는 도구입니다.

## 네 런타임의 구조

runc에서는 컨테이너가 host 커널을 공유합니다. gVisor에서는 사용자 공간 커널(Sentry)이 syscall을 먼저 처리합니다. Kata는 pod마다 별도의 VM(guest 커널)을 실행합니다.

| 항목 | runc | gVisor (runsc) | Kata (QEMU, Cloud Hypervisor) | Firecracker |
|---|---|---|---|---|
| syscall을 처리하는 곳 | host kernel | Sentry(사용자 공간 커널). VM에서는 systrap 플랫폼, KVM 플랫폼은 bare metal에서만 | VM 안의 guest kernel | microVM 안의 guest kernel |
| 격리 경계 | namespace, cgroup, seccomp | 사용자 공간 커널 | 하드웨어 가상화 (KVM) | 하드웨어 가상화 (KVM), 최소 장치 모델 |
| NVIDIA 드라이버 위치 | host | host | guest (host에는 NVIDIA 드라이버를 설치하지 않음) | 해당 없음 |
| GPU 경로 | device node 직접 접근 | nvproxy가 허용된 ioctl만 host 드라이버로 전달 | VFIO passthrough (cold-plug) | 없음 |
| `/dev/kvm` | 불필요 | 불필요 (systrap) | 필요 | 필요 |
| 이 에셋에서 | trainer와 시스템 pod | `gvisor` RuntimeClass (handler `runsc`) | `kata-qemu-nvidia-gpu`, `kata-qemu`, `kata-clh` | 사용하지 않음 (Kata의 hypervisor로도 쓰임) |

세 런타임 모두 같은 샌드박스 이미지를 씁니다. 이미지에는 NVIDIA 커널 드라이버가 없고, PyTorch wheel에 포함된 CUDA 사용자 공간 라이브러리만 들어 있습니다.

## GPU 경로 두 가지

![같은 다섯 줄 구조로 그린 두 패널입니다. a gVisor + nvproxy(g5.xlarge): pod(gVisor) 경계 안에 후보 코드(CUDA 사용자 공간 라이브러리), Sentry(사용자 공간 커널, systrap 플랫폼), nvproxy(드라이버 버전별 ioctl allowlist)가 있습니다. 그 아래 host에는 host NVIDIA 드라이버 580.178.04(proprietary, GSP off)와 A10G가 있습니다. b Kata + QEMU(g4dn.metal): guest VM 경계 안에 후보 코드와 guest kernel + guest NVIDIA 드라이버(kata-deploy 제공, open 615.71.09)가 있습니다. host 쪽에서는 VFIO passthrough(IOMMU가 DMA를 VM 안으로 제한)를 거쳐 T4에 바로 연결되고(host는 vfio-pci만 bind), host에는 NVIDIA 드라이버가 없습니다.](../images/figures/concepts-02_isolation_runtimes--gpu-paths.svg)

*그림 요약: gVisor에서는 후보 코드의 GPU 명령이 허용 목록을 거쳐 host 드라이버로 전달되므로 host 드라이버를 공유합니다. Kata에서는 GPU가 VM에 직접 할당되어 VM 안의 guest 드라이버만 사용합니다.*


### gVisor + nvproxy

- **설정:** `runsc.toml`의 `[runsc_config]`에 `nvproxy = "true"`를 설정합니다. 기본 capabilities는 `compute,utility`이고, shim은 runtime option의 `ConfigPath` 파일만 읽습니다. OCI spec에 NVIDIA 장치가 있으면 GPU 지원이 자동으로 활성화됩니다.
- **드라이버 정책:** host 드라이버 버전이 지원 목록과 정확히 일치해야 합니다. 상태는 supported, unsupported(`--nvproxy-allow-unsupported-driver`가 있어야 동작), unknown(플래그와 관계없이 실패) 세 가지입니다. 드라이버 상태는 `runsc nvproxy list-supported-drivers`로 확인합니다. 580.178.04는 release-20260831.0부터 supported이고, 595.91.07은 release-20261109.0 기준 unknown입니다.
- **문서화된 GPU:** T4, A100/A10G, L4, H100입니다. 같은 아키텍처의 다른 GPU는 문서에 "will likely work"로 표시돼 있습니다.
- **장치 주입:** gVisor 문서는 "runsc is fully CDI-compatible"이라고 설명하며, NVIDIA k8s-device-plugin의 `deviceListStrategy: cdi-cri`를 문서화된 설정 방법으로 제시합니다. host에는 nvidia-container-toolkit이 여전히 필요하지만, runsc가 장치를 직접 구성하므로 prestart hook은 필요 없습니다.
- **containerd 등록:** containerd 2.x(AMI는 2.3.7) config v3의 `[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runsc]`에 `runtime_type = 'io.containerd.runsc.v1'`과 `TypeUrl`, `ConfigPath` option을 설정합니다. 이 블록을 NodeConfig `spec.containerd.config`에 넣으면 nodeadm이 부팅할 때마다 containerd 설정에 병합합니다. RuntimeClass의 `handler`는 `runtimes.<name>` 키(`runsc`)와 같아야 합니다.

!!! warning "gVisor 노드의 드라이버 조건"
    EKS AL2023 NVIDIA AMI는 `g4dn`, `g5`, `g5g`에서 GSP를 끈 proprietary 커널 모듈을, `g6`에서는 open 모듈을 로드합니다(`g5`와 `g6` 모두 드라이버 580.178.04). gVisor 문서는 NVIDIA open 드라이버를 기준으로 nvproxy를 설명하고 proprietary 드라이버는 언급하지 않습니다. 다만 580.178.04는 runsc `release-20261109.0`의 지원 목록에 있고, 실습 계정에서 `g5.xlarge`(A10G)로 smoke test(`cuda ok: NVIDIA A10G 2048.0`)와 `scripts/ops/verify.sh gvisor v1`이 통과했습니다. 이 에셋의 기본값은 `g5.xlarge`입니다. 이 조합은 gVisor가 문서화한 것이 아니라 이 저장소가 검증한 것이므로, 드라이버, AMI, gVisor 버전을 바꾸면 다시 확인하세요. smoke test는 GPU 하나를 요청하는 pod를 따로 만들므로 gVisor 노드에 빈 GPU가 있을 때 실행하고, 이미 배포한 풀은 `scripts/ops/verify.sh gvisor v1`로 확인합니다.

    `g6.xlarge`(L4)는 지원하는 대안이고, open 모듈이라 gVisor 문서가 다루는 조합입니다. T4(`g4dn`)는 드라이버 조건이 `g5`와 같지만 이 에셋에서 테스트하지 않아 미검증입니다. 자세한 내용은 [04 플랫폼과 인스턴스 선택](04_platforms_and_instances.md)에 있습니다.

### Kata + VFIO passthrough

- **host 조건:** `/dev/kvm`, IOMMU, GPU를 소유한 host가 필요합니다. AL2023 커널은 `CONFIG_INTEL_IOMMU_DEFAULT_ON`이 꺼져 있어 `intel_iommu=on`을 지정해야 합니다. 그래서 이 에셋은 커널 인자 `intel_iommu=on iommu=pt`를 포함한 AMI를 AL2023 표준 EKS AMI에서 빌드합니다(`infra/kata/build-iommu-ami.sh`).
- **지원 모드:** upstream 문서에는 "Cold-plug is by design the only supported mode for NVIDIA GPU passthrough"라고 명시돼 있습니다.
- **guest 스택:** kata-deploy가 NVIDIA guest kernel, rootfs, NVRC, open kernel module 615.71.09(README에 Tesla T4 포함)를 함께 배포합니다. host에는 NVIDIA 드라이버를 설치하면 안 됩니다.
- **shim 선택:** Kata 4.0.0부터 기본값인 runtime-rs에서 GPU cold-plug를 쓰려면 iommufd가 필요합니다. AL2023 커널은 `CONFIG_IOMMUFD`가 꺼져 있어서 이 에셋은 Go shim 기반 `kata-qemu-nvidia-gpu`를 씁니다. Go runtime은 deprecated 상태지만 계속 지원됩니다 (Kata 4.3.1 기준).
- **GPU Operator v26.7.2:** `sandboxWorkloads.enabled=true`, `sandboxWorkloads.mode=kata`, `ccManager.defaultMode=off`(T4에서 `on`이면 cc-manager가 종료됨), 노드 라벨 `nvidia.com/gpu.workload.config=vm-passthrough`, 리소스 이름 `nvidia.com/pgpu`를 씁니다. 공식 문서에 "A node can only run one container runtime at a time"이라고 명시돼 있으므로 한 노드에서 컨테이너 GPU 작업과 VM passthrough를 함께 실행하지 않습니다.

??? info "제3자 보고 (참고용)"
    Ubuntu 24.04를 쓰는 `g4dn.metal`에 `intel_iommu=on iommu=pt`를 지정하자 T4 8개가 모두 vfio-pci에 bind되고 IOMMU group도 passthrough 조건에 맞았다는 보고가 있습니다. warm reboot 후 인스턴스가 다시 부팅되지 않았다는 보고도 있습니다.

## Kata의 hypervisor: QEMU와 Cloud Hypervisor

| 항목 | QEMU | Cloud Hypervisor (CLH) |
|---|---|---|
| CPU 샌드박스 | 지원 (`kata-qemu`) | 지원 (`kata-clh`) |
| GPU passthrough | upstream 지원 (`kata-qemu-nvidia-gpu`) | upstream 미지원. 이 에셋은 실험용 `kata-clh-nvidia-gpu`만 제공 |
| RuntimeClass `overhead.podFixed` (Kata 4.3.1) | 320Mi, 250m. GPU class는 10240Mi, 1 CPU | 130Mi, 250m. 실험용 `kata-clh-nvidia-gpu`는 10240Mi, 1 CPU |
| boot to workload (Kata metrics CI, 3.28.0) | 0.71 s | 0.39 s |

`overhead.podFixed`는 RuntimeClass에 지정된 설정값이며 측정값이 아닙니다. 스케줄러는 이 값을 VM 자체가 사용하는 메모리와 CPU로 보고 pod 요청량에 합산합니다.

upstream `docs/hypervisors.md`는 Cloud Hypervisor의 GPU 지원을 not supported로 표시하고, maintainer도 2025-08에 "You should use the QEMU GPU runtime class. I haven't done any work on CLH to enable proper GPU support."라고 답했습니다. Go `kata-clh` shim에는 3.29.0부터 VFIO cold-plug 코드가 있지만, upstream 테스트가 없고 배포 설정에서는 비활성화돼 있습니다. runtime-rs의 CLH 설정에는 VFIO 키가 없습니다. 그래서 Kata에서 upstream이 GPU를 지원하는 hypervisor는 QEMU뿐입니다. 이 에셋은 CLH + GPU를 `infra/kata/experimental-clh-gpu/`에서 평가용(CI 없음)으로만 제공합니다. CLH는 CPU 샌드박스에서는 지원되며, CPU 계층(`kata-clh-cpu` 프로필)이 이 조합을 사용합니다.

!!! warning "오버헤드 수치를 읽는 법"
    위 boot 시간은 Kata metrics CI(3.28.0)가 서로 다른 머신에서 넓은 허용 오차로 측정한 값이며 AWS 측정값이 아닙니다. AWS China 블로그의 "CLH 약 130 MB, QEMU 약 160 MB"는 Kata 3.31.0의 `podFixed` 기본값과 같아서 측정값이 아닐 가능성이 높습니다(추론). 같은 글에 실린 측정값은 cold start 약 3 s, 미리 시작해 둔 pool에서 가져올 때 약 230 ms입니다. AWS 실습 계정에서 측정한 값은 [08 런타임 벤치마크](../handson/08_benchmark.md)에 있습니다. 그 표의 cold start는 pod 생성부터 Ready까지의 시간이라 위 표의 boot to workload와 측정 구간이 다르고, `g4dn.metal`에서 GPU 프로필 `kata-qemu`(RuntimeClass `kata-qemu-nvidia-gpu`)로 띄운 pod 4개는 중앙값 30.5초였습니다.

`kata-qemu-nvidia-gpu`의 VM 크기는 `default_memory` 8192 MiB에 컨테이너 limit을 더한 값입니다. VFIO type1은 guest RAM 전체를 pin하므로 메모리를 overcommit할 수 없습니다. 이 에셋의 프로필은 T4 pod마다 8 CPU, 16 GiB를 할당합니다. 8 x (16 + 10) GiB = 208 GiB이므로 `g4dn.metal`의 384 GiB 안에 들어갑니다.

## 격리 강도와 남는 위험

| 런타임 | 신뢰할 수 없는 코드와 host 사이 | 남는 위험 | 이 에셋의 보완 |
|---|---|---|---|
| runc | host kernel과 드라이버를 공유 | kernel이나 드라이버 취약점이 그대로 노출 | 샌드박스에 쓰지 않음 |
| gVisor + nvproxy | syscall은 Sentry, GPU는 ioctl allowlist | gVisor 문서 기준 nvproxy는 "much less effective at mitigating vulnerabilities within the NVIDIA GPU drivers themselves"이고 "no validation of things like DMA buffers". VM 경계보다 약함 | pod마다 GPU 1개(time-sharing 없음), 노드당 샌드박스 1개, egress 차단을 확인한 뒤 Ready, node guard iptables |
| Kata + VFIO | VM 경계 + IOMMU | hypervisor와 GPU 장치 자체. DMA는 IOMMU가 VM 안으로 제한(unsafe noiommu 모드는 켜지 않음). vfio-pci는 해제 시 function(또는 bus)을 reset하며, T4는 `reset_method=bus`로 보고됨(제3자 보고, NVIDIA 보증 아님). T4에는 confidential computing이 없음 | v2는 200회 평가 후 pod를 draining으로 바꾸고, Production gateway의 recycler가 그 pod를 삭제하고 새 pod(Kata에서는 새 VM)로 교체 |
| Kata (CPU 전용) | VM 경계 | hypervisor | 같은 네트워크 통제 |

GKE Sandbox 문서도 "Don't use GPU time-sharing in sandboxed Pods"라고 권고합니다. 보안 경계 전체와 위협 모델은 [Production 02 보안](../production/02_security.md)에서 다룹니다.

## AWS에서 각 런타임을 실행할 수 있는 위치

| 위치 | Kata + GPU | Kata CPU 전용 | gVisor + GPU |
|---|---|---|---|
| EC2 `.metal` (`g4dn.metal`) | 가능 (VFIO passthrough) | 가능 | 가능 (이 에셋에서는 쓰지 않음) |
| EC2 nested virtualization (C8i, M8i, R8i 등) | 불가: 해당 계열에 GPU 없음 | 가능, `.metal` 불필요 | 해당 없음 |
| EC2 GPU VM (`g5.xlarge` 등) | 불가: `/dev/kvm` 없음 | 불가 | 가능 (systrap 플랫폼) |
| HyperPod 노드 (`ml.g5` 등) | 불가 | 불가로 판단 (미검증) | 기본 AMI는 불가 (드라이버 595.91.07). B2는 580.178.04를 넣은 custom AMI로 구성 (AWS 미검증) |

표의 근거는 세 가지입니다.

1. **Kata는 `/dev/kvm`이 필요합니다.** QEMU와 Cloud Hypervisor 모두 KVM을 씁니다. GPU passthrough에는 IOMMU와, 물리 GPU를 소유해 vfio-pci에 bind할 수 있는 host도 필요합니다.
2. **EC2 nested virtualization을 켜면 일반 VM에서도 `/dev/kvm`을 사용할 수 있습니다.** 2026-02-16에 C8i, M8i, R8i를 대상으로 출시됐고, 현재 User Guide에는 M7i, M7i-flex, M8i, M8id, M8i-flex, C7i, C7i-flex, C8i, C8id, C8i-flex, R7i, R7iz, R8i, R8id, R8i-flex, X8i, I7i, I7ie가 나열돼 있습니다. L1 hypervisor로는 KVM과 Hyper-V를 지원하고, G나 P 계열은 목록에 없습니다. AWS는 성능에 민감한 가상화 작업에는 bare metal을 권장합니다.
3. **NVIDIA GPU를 탑재한 x86 `.metal` 인스턴스는 `g4dn.metal`뿐입니다.** EC2의 NVIDIA GPU bare metal 인스턴스는 이것(T4 8개, 96 vCPU, 384 GiB)과 arm64인 `g5g.metal`(T4G 2개) 두 가지입니다. HyperPod에는 `ml.*.metal`이 없고, CreateCluster에는 nested virtualization CPU 옵션이 없습니다. G와 P 계열은 nested virtualization을 지원하지 않습니다.

nested virtualization은 `run-instances`의 `--cpu-options "NestedVirtualization=enabled"`, launch template `CpuOptions`의 `NestedVirtualization`, Karpenter v1.15.2 EC2NodeClass의 `spec.cpuOptions.nestedVirtualization`으로 켭니다. 이 에셋의 CDK 스택([`cdk/gpusandbox_cdk/stack.py`](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/cdk/gpusandbox_cdk/stack.py))은 c8i 노드 그룹의 launch template `CpuOptions`에 `NestedVirtualization: enabled`를 `CoreCount`, `ThreadsPerCore`와 함께 지정합니다. EKS 관리형 노드 그룹이 이 옵션을 노드에 전달한다는 문서는 없습니다. 다만 실습 계정 배포(2026-11-14)에서는 옵션이 전달됐습니다(노드에 `/dev/kvm` 있음).

아래는 읽기 전용 확인 명령입니다.

```bash
# Instance types that support nested virtualization in the current Region
aws ec2 describe-instance-types \
  --filters "Name=processor-info.supported-features,Values=nested-virtualization" \
  --query 'InstanceTypes[].InstanceType' --output text
```

**확인할 것:** 인스턴스 타입 이름이 공백으로 구분되어 출력됩니다. 핸즈온에서 쓰는 `c8i.2xlarge`가 포함돼 있는지 확인하세요. 출력이 비어 있으면 그 리전에는 지원하는 타입이 없으므로 `--region`을 바꿔 다른 리전을 확인하세요.

**문제가 생기면:** [문제 해결](../reference/troubleshooting.md)의 "Kata" 항목에 nested virtualization 점검 명령이 있습니다.

!!! question "❓ 오해: Kata를 쓰려면 `.metal` 인스턴스가 필요하다"
    2026-02 이전에는 대체로 맞았지만 지금은 GPU passthrough에만 해당합니다. CPU 샌드박스라면 nested virtualization을 켠 `c8i.2xlarge` 같은 일반 VM에서 `kata-clh`와 `kata-qemu`를 실행할 수 있습니다(이 에셋의 Kata CPU 노드 추가 스크립트 `scripts/kata/cpu_nodes.sh`).

!!! tip "관리형 CPU 대안"
    AWS Nitro Sandboxes와 EKS isolated pods(2026-11-09 출시)는 `runtimeClassName`으로 `isolated-sandbox` 또는 `confidential-sandbox`를 지정하며 Kubernetes 1.36 이상이 필요합니다. 문서에 "GPU and other device passthrough are not supported at launch"라고 명시돼 있으므로 CPU 샌드박스용 대안입니다. 선택 기준은 [05 상황별 선택 가이드](05_decision_guide.md)에 있습니다.

!!! tip "런타임 위의 오케스트레이션: Agent Sandbox"
    샌드박스를 언제 만들고 어느 요청에 할당할지는 런타임 위의 오케스트레이터가 결정합니다. [06 Agent Sandbox로 확장](06_agent_sandbox.md)에서는 kubernetes-sigs/agent-sandbox로 미리 만들어 둔 warm pool에서 에피소드마다 샌드박스를 하나씩 할당받아 씁니다. 이 방식은 기존 RuntimeClass를 그대로 사용하므로 gVisor와 Kata에 모두 적용할 수 있습니다.

## 적용 범위와 한계

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
    | 이 에셋의 런타임 설정 | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/gvisor/install-gvisor.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/kata-deploy-values.yaml , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/infra/kata/gpu-operator-values.yaml |

    전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-concepts-02-isolation-runtimes)
