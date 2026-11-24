---
hide:
  - footer
---

# 02 샌드박스 런타임 준비

[공통 절차 01](../01_provision/index.md)에서 이미지 URI를 `scripts/config.env`에 저장한 뒤 프로젝트 폴더에서 진행하세요. A, B1, C는 SSM 터널을 열어 두고 원래 작업 터미널에서 실행합니다. B2는 01에서 연결한 EKS 컨텍스트를 사용합니다.

=== "A (EC2 GPU)"

    설치 과정과 CUDA 검사 출력 예시는 [EC2 gVisor 상세 가이드](gvisor.md)에서 확인하세요.

    `gvisor` v1 pool을 배포하기 전에 EC2 채점 노드에서 GPU 한 장을 비워 두고 실행하세요.

    ```bash
    scripts/04_install_gpu_stack.sh
    ```

    기본 A10G 노드에서는 `Starting gVisor...`로 gVisor 시작을, `cuda ok: NVIDIA A10G 2048.0`으로 CUDA 연산 결과를 확인하세요. [GPU 검사 출력 예시](gvisor.md#gpu-smoke)

    [03 채점 pool 배포와 검증 (A)](../03_pools/index.md#__tabbed_1_1)

=== "B1 (HyperPod + EC2)"

    단계별 설명은 [EC2에서 gVisor와 GPU 확인하기](gvisor.md)와 [HyperPod 학습 노드를 EKS에 연결하기](b1_trainer.md)를 순서대로 보세요.

    1. **EC2 채점 노드에서 GPU 확인**

        ```bash
        scripts/04_install_gpu_stack.sh
        ```

        기본 A10G 노드에서는 `Starting gVisor...`로 gVisor 시작을, `cuda ok: NVIDIA A10G 2048.0`으로 CUDA 연산 결과를 확인하세요. [GPU 검사 출력 예시](gvisor.md#gpu-smoke)

    2. **HyperPod 학습 노드를 EKS에 연결**

        다음 명령으로 HyperPod 학습 인스턴스를 만들면 요금이 발생합니다.

        ```bash
        scripts/hyperpod/create.sh
        ```

        마지막 노드 목록에서 trainer가 `Ready`이고 상태 레이블이 `Schedulable`인지 확인하세요. 아래 명령이 `ACTIVE`를 반환하면 채점 pool을 배포하세요.

        ```bash
        source scripts/config.env
        aws eks describe-addon --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
          --addon-name amazon-sagemaker-hyperpod-training-operator --query 'addon.status' --output text
        ```

    [03 채점 pool 배포와 검증 (B1)](../03_pools/index.md#__tabbed_1_2)

=== "B2 (HyperPod)"

    채점 워커의 드라이버를 바꾸는 이유와 학습 오퍼레이터 설치에 실패했을 때의 조치는 [HyperPod 워커 상세 가이드](b2_workers.md)에서 확인하세요.

    1. **채점 워커 두 대의 드라이버 준비**

        두 워커가 `Ready`이면 Bash 4 이상에서 실행하세요. 드라이버 교체가 필요한 채점 워커를 재부팅하고 새 드라이버가 로드됐는지 확인합니다.

        ```bash
        scripts/hyperpod/reboot_sandboxes.sh
        ```

    2. **학습 오퍼레이터와 GPU 플러그인 준비**

        ```bash
        scripts/hyperpod/prepare_managed.sh
        ```

        오퍼레이터가 `ACTIVE`이면 GPU 플러그인을 설치하세요.

        ```bash
        scripts/04_install_gpu_stack.sh
        ```

    3. **HyperPod 채점용 RuntimeClass 등록**

        ```bash
        kubectl apply -f k8s/runtimes/runtimeclass-gvisor-hyperpod.yaml
        kubectl get runtimeclass gvisor-hyperpod
        ```

        `gvisor-hyperpod` 행의 `HANDLER`가 `runsc`인지 확인하세요. GPU 채점은 03에서 두 pod를 배포한 뒤 검증합니다.

    [03 채점 pool 배포와 검증 (B2)](../03_pools/index.md#__tabbed_1_3)

=== "C (CPU)"

    CPU에서 세 런타임을 설치하고 각각의 커널 버전을 비교하는 과정은 [Kata CPU 상세 가이드](kata.md#kata-cpu)를 참고하세요.

    01에서 만든 `c8i.2xlarge` 노드에 CPU 런타임을 설치하고 시험용 pod를 실행하세요.

    ```bash
    scripts/kata/cpu_nodes.sh
    ```

    스크립트가 출력하는 `gvisor-cpu`, `kata-clh`, `kata-qemu`의 커널 버전을 마지막 호스트 커널과 비교하세요. gVisor는 자체 커널을, Kata는 VM의 게스트 커널을 보고합니다. [세 런타임의 실행 결과](kata.md#cpu-run)

    [03 채점 pool 배포와 검증 (C)](../03_pools/index.md#__tabbed_1_4)

EC2에서 VM에 GPU를 직접 연결하는 추가 구성은 [Kata GPU 실습](kata.md#kata-gpu)에 있습니다.
