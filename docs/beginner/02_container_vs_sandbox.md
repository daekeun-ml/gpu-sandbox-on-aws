# 02 컨테이너와 샌드박스

**TL;DR** 샌드박스 런타임은 컨테이너와 서버 커널 사이에 격리 계층을 하나 더 둡니다. gVisor는 pod마다 사용자 공간 커널(Sentry)을 실행해 시스템 호출을 대신 처리하고, Kata는 pod마다 작은 VM을 띄워 그 VM의 커널이 시스템 호출을 처리합니다.

## 기존 Pain Point

컨테이너는 파일과 프로세스를 다른 컨테이너와 분리해서 보여 줄 뿐, 커널은 서버와 공유합니다. 그래서 커널에 취약점이 하나 있으면 같은 서버의 모든 컨테이너가 영향을 받아요. 관련 이름도 runc, gVisor, Kata, Firecracker, QEMU, Cloud Hypervisor처럼 많아서, 어느 것이 서로 대체 관계이고 어느 것이 다른 것의 구성 요소인지 헷갈립니다. 격리를 강하게 하면 속도, 호환성, 쓸 수 있는 서버 면에서 무엇을 포기해야 하는지도 알아야 런타임을 고를 수 있습니다.

![a: 컨테이너 A, B, C가 서버 커널 하나를 함께 씁니다. 커널 취약점 하나로 A, B, C가 모두 위험해집니다. b: 컨테이너마다 Sentry 또는 VM 커널이 컨테이너와 서버 커널 사이에 있습니다. 그래서 A, B, C 앞에 격리 계층이 하나 더 생깁니다.](../images/figures/beginner-02_container_vs_sandbox.svg)

*그림 요약: 일반 컨테이너는 서버 커널 하나를 함께 쓰므로 커널 취약점 하나가 모든 컨테이너에 영향을 줍니다. 샌드박스 런타임은 pod마다 Sentry나 VM 커널을 두어 컨테이너와 서버 커널 사이에 격리 계층을 하나 더 만듭니다.*


## Why

- **커널의 역할부터 설명합니다.** 세 런타임은 코드가 커널에 보내는 요청(시스템 호출)의 경로에 무엇을 두는지가 다릅니다.
- **세 방식을 같은 항목으로 비교합니다.** 격리 경계, 필요한 서버 조건, 느려지는 곳, GPU 사용 방식을 한 표에 정리했어요.
- **격리에 따른 성능 비용을 측정값으로 확인합니다.** 블로그 2부가 같은 노드에서 일반 컨테이너와 gVisor를 비교한 측정값입니다.

**사전 지식:** [01편](01_why_sandbox.md)의 위험 목록을 먼저 읽으면 격리 계층이 어떤 위험을 막는지 이해하기 쉽습니다.

??? note "용어 (처음 보는 단어가 있으면 펼치세요)"
    - **커널:** 운영체제의 핵심 프로그램입니다. 파일, 메모리, 네트워크, 장치를 관리해요.
    - **시스템 호출(syscall):** 프로그램이 커널에 파일 열기, 메모리 할당 같은 작업을 요청하는 방법입니다.
    - **컨테이너, runc:** 컨테이너는 프로세스가 볼 수 있는 파일, 프로세스, 네트워크를 다른 프로세스와 분리해서 실행하는 방식입니다. runc는 Kubernetes가 기본으로 쓰는 컨테이너 런타임이에요.
    - **namespace, cgroup:** 프로세스가 볼 수 있는 범위(namespace)와 쓸 수 있는 양(cgroup)을 제한하는 리눅스 기능입니다.
    - **VM(가상 머신), microVM:** 소프트웨어로 만든 가상의 컴퓨터로, 자기 커널을 따로 실행합니다. microVM은 꼭 필요한 장치만 넣어 빨리 부팅되는 작은 VM이에요.
    - **하이퍼바이저:** VM을 만들고 실행하는 프로그램입니다(QEMU, Cloud Hypervisor, Firecracker).
    - **KVM:** 리눅스가 CPU의 가상화 기능을 쓸 수 있게 해 주는 커널 기능입니다. 서버에서는 `/dev/kvm` 장치 파일로 나타나요.
    - **RuntimeClass:** pod를 실행할 런타임을 지정하는 Kubernetes 설정입니다.

## 커널을 함께 쓴다는 것

프로그램이 파일을 읽거나 네트워크로 데이터를 보내려면 커널에 요청(시스템 호출)해야 합니다. 일반 컨테이너(runc)는 namespace와 cgroup으로 볼 수 있는 범위와 쓸 수 있는 양을 제한할 뿐이고, 요청을 처리하는 커널은 서버의 커널 하나예요.

블로그 1부에서 같은 노드의 컨테이너 안에서 `uname -r`(커널 버전 확인)을 실행하자, runc에서는 노드의 커널 버전(`6.18.51-120.162.amzn2023`)이, gVisor에서는 `4.19.0-gvisor`가 출력됐어요(블로그 측정, EKS 1.36). gVisor 안의 프로그램은 서버 커널이 아니라 gVisor가 구현한 커널(Sentry)에 시스템 호출을 보낸다는 뜻입니다.

## 세 가지 격리 방식

![같은 구조로 그린 세 패널입니다. a runc: pod 안의 코드가 시스템 호출로 서버 커널을 직접 호출합니다(격리 경계: namespace, cgroup). b gVisor: pod마다 하나씩 있는 Sentry가 pod 안에서 시스템 호출을 받아 처리하고, 꼭 필요한 일부만 서버 커널로 보냅니다. c Kata: pod마다 VM이 하나씩 있고, VM 안의 커널이 시스템 호출을 받습니다. 서버 커널에는 KVM 경계를 거쳐야 접근합니다(격리 경계: 하드웨어 가상화).](../images/figures/beginner-02_container_vs_sandbox--three-walls.svg)

*그림 요약: runc에서는 코드가 서버 커널을 직접 호출합니다. gVisor에서는 pod마다 있는 Sentry가 시스템 호출을 대신 처리하고, Kata에서는 pod마다 있는 VM과 그 안의 커널이 처리합니다.*


- **runc:** namespace와 cgroup으로 컨테이너마다 볼 수 있는 범위와 쓸 수 있는 양만 나누고, 시스템 호출은 모두 서버 커널이 직접 처리합니다. 서버 커널에 취약점이 있으면 같은 서버의 모든 컨테이너가 영향을 받아요.
- **gVisor:** pod마다 Sentry라는 사용자 공간 커널을 실행합니다. 프로그램의 시스템 호출 대부분은 Sentry가 처리하고 꼭 필요한 일부만 서버 커널로 보내므로, 서버 커널이 직접 처리하는 호출이 크게 줄어요.
- **Kata:** pod마다 작은 VM을 띄우고, 그 VM 안의 커널이 시스템 호출을 처리합니다. VM과 서버는 하드웨어 가상화(KVM)로 분리돼요.

gVisor와 Kata도 위험을 완전히 없애지는 않습니다. gVisor도 일부 호출은 서버 커널로 보내고, Kata의 VM도 같은 서버에서 실행되므로 하이퍼바이저에 취약점이 있으면 영향을 받을 수 있어요.

| 항목 | runc | gVisor | Kata |
|---|---|---|---|
| 시스템 호출을 처리하는 커널 | 서버 커널 | pod마다 둔 Sentry (사용자 공간 커널) | pod마다 띄운 VM의 커널 |
| 격리 경계 | namespace, cgroup | Sentry가 시스템 호출을 대신 처리 | 하드웨어 가상화(KVM) 경계 |
| 필요한 서버 조건 | 없음 | 없음(일반 VM에서 실행 가능) | `/dev/kvm`: bare metal이나 nested virtualization을 켠 인스턴스 |
| 느려지는 곳 | 거의 없음 | 시스템 호출이 많은 작업 | VM을 띄우는 시간, 장치 연결 |
| GPU | 그대로 사용 | 드라이버 호출을 검사해 전달 | GPU를 VM에 직접 할당 ([03편](03_gpu_sandbox.md)) |

## 격리의 비용: 실제 숫자

블로그 2부는 같은 노드(EKS 1.36, `m7i.xlarge`)에서 runc와 gVisor를 비교했습니다. 아래는 블로그의 측정값이고, 이 저장소가 측정한 값이 아니에요.

| 작업 | runc | gVisor | 차이 |
|---|---|---|---|
| CPU만 쓰는 반복 계산 | 0.144초 | 0.146초 | 거의 같음 |
| 시스템 호출 20만 번(`getppid`) | 0.035초 | 0.444초 | 약 12.5배 |
| 파일 1,000개 만들기 | 0.041초 | 0.195초 | 약 4.7배 |
| Python 5번 실행 | 0.206초 | 0.399초 | 약 1.9배 |

시스템 호출이 많은 코드일수록 느려지며, 블로그는 시스템 호출 한 번에 걸리는 시간이 약 0.18 µs에서 2.2 µs로 늘었다고 적었어요. 이 저장소의 GPU 커널 채점은 실행 시간의 대부분이 GPU 계산이라 이 영향이 상대적으로 작을 것으로 봅니다(추론).

## pod마다 런타임 고르기

Kubernetes에서는 `RuntimeClass`로 pod마다 런타임을 지정하므로, 한 클러스터 안에서 runc, gVisor, Kata를 pod별로 다르게 쓸 수 있어요. 이 저장소는 같은 샌드박스 이미지와 서버 코드를 쓰고 `RuntimeClass` 이름만 바꿔 세 런타임을 비교합니다.

!!! question "❓ 오해: Agent Sandbox를 쓰면 격리가 강해진다"
    Agent Sandbox는 샌드박스를 미리 띄워 두고(warm pool) 요청이 오면 할당하는 관리 도구입니다. 격리 수준은 샌드박스 pod에 지정한 `RuntimeClass`가 결정합니다. 블로그 3부의 운영 사례(Ably)도 Agent Sandbox를 일반 컨테이너(runc)로 운영하며, microVM은 앞으로 평가할 계획이라고 적었어요.

!!! question "❓ 오해: 서버의 `ps`에 안 보이면 안전하다"
    gVisor 안의 프로세스는 서버에서 `ps`로 보이지 않습니다. 하지만 블로그 1부는 컨테이너 탈출 공격은 시험하지 않았다고 밝혔어요. 서버에서 프로세스가 보이지 않는다고 해서 컨테이너 밖으로 빠져나올 수 없다는 뜻은 아닙니다.

## 한 줄 정리

- 일반 컨테이너는 서버 커널을 함께 쓰고, 샌드박스 런타임은 그 사이에 격리 계층을 하나 더 둡니다.
- gVisor는 pod마다 실행하는 Sentry로, Kata는 pod마다 띄우는 VM으로 격리 계층을 만듭니다. 격리 수준이 높을수록 필요한 서버 조건과 비용이 늘어납니다.

## 다음 편

[03 GPU까지 격리하려면](03_gpu_sandbox.md)에서는 GPU를 쓰는 코드를 격리하기가 더 어려운 이유를 설명합니다.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | AI 에이전트 샌드박스, EKS 격리 1부 (runc와 gVisor 비교 실험) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ |
    | 같은 시리즈 2부 (시스템 호출 비용 측정) | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/ |
    | Kubernetes RuntimeClass | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
    | gVisor | https://github.com/google/gvisor |
    | Kata Containers | https://github.com/kata-containers/kata-containers |

    전체 출처: [참고 자료 모음의 이 페이지 절](../reference/references.md#ref-beginner-02-container-vs-sandbox)
