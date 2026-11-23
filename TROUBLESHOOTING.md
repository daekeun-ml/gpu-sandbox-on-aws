**한국어** | [English](TROUBLESHOOTING.en.md)

# 문제 해결

아래 표에서 화면에 나타난 증상을 찾으세요. 로그를 더 확인해야 한다면 가이드북의 [문제 해결](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/)을 참고하세요.

| 증상 | 먼저 볼 곳 |
|---|---|
| `set ... in scripts/config.env`, `missing tool` | [설정과 스크립트](#설정과-스크립트) |
| `kubectl` 연결 실패, 노드가 나타나지 않음 | [CDK, 터널, 클러스터](#cdk-터널-클러스터) |
| GPU smoke test 실패 | [gVisor](#gvisor), [Kata](#kata) |
| `Pending`, `ContainerCreating`, `Running`인데 `0/1` | [샌드박스 pool](#샌드박스-pool) |
| 인증 요청이 `401` 또는 `403`으로 실패 | [인증 오류별 진단](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#401-403-응답) |
| `CUDA out of memory`, `sandbox_error` 반복 | [학습](#학습) |
| `hyperpodrun` 누락, HyperPod 생성 실패 | [HyperPod](#hyperpod) |
| 새 pool로 전환했는데 이전 버전으로 채점됨 | [버전 전환](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#버전-전환-routing) |
| 정리 후에도 리소스가 남아 있거나 요금이 계속 발생함 | [정리와 비용](#정리와-비용) |

## 먼저 확인할 것

1. A·B1·C에서 `kubectl`이 연결되지 않으면 `cdk/tunnel.sh`와 `<CLUSTER_NAME>-tunnel` 컨텍스트를 확인하세요. 관리형 B2는 [B2 접속 단계](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/07_hyperpod_b2/)에서 설정한 `$CLUSTER_NAME` 컨텍스트를 사용합니다.
2. 연결되면 아래 명령으로 pod 상태를 봅니다. `<pod>`에는 첫 명령에 나온 이름을 넣으세요.

```bash
kubectl -n sandbox get pods -o wide -L gpusandbox/runtime,gpusandbox/version
kubectl -n sandbox describe pod <pod>
kubectl -n sandbox logs <pod>
```

- `Pending`이나 `ContainerCreating`이면 `describe`의 `Events`에서 pod를 배치하거나 시작하지 못한 이유를 확인하세요.
- `Running`인데 `0/1`이면 로그의 `device probe ok=`와 `egress is open`을 확인하세요. Ready가 되기 전에는 새 평가 요청을 받지 않습니다.
- 학습이 진행 중이어도 채점이 실패할 수 있습니다. TRL은 `reward_batch`, veRL은 `reward_extra_info`에서 `sandbox_error`가 반복되는지 확인하세요.

## 설정과 스크립트

- **`[error] set <이름> in scripts/config.env`**: 그 값이 비어 있거나 `__SET_ME__`가 남아 있습니다. 이미지 주소(`SANDBOX_IMAGE_URI` 등)는 `03_build_push_images.sh`가 마지막에 출력하는 `export` 줄을 붙여 넣으면 됩니다.
- **`[error] missing tool: <도구>`**: 그 도구를 설치한 뒤 `scripts/01_check_prereqs.sh`를 다시 실행하세요.
- **`03_build_push_images.sh`를 다시 실행했더니 같은 태그가 있어 이미지를 push할 수 없음**: 실습용 ECR 리포지토리에서는 기존 태그를 덮어쓸 수 없습니다. `IMAGE_TAG`를 새 값으로 바꿔 다시 실행하고, 새로 출력된 주소로 `config.env`를 고치세요.
- **이미지 빌드가 매우 느리거나 디스크가 부족**: arm64 PC에서 amd64 이미지를 만들면 에뮬레이션 때문에 느립니다. 디스크가 100 GB 이상인 x86_64 호스트에서 빌드하세요.

자세히: [설정과 스크립트](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#설정과-스크립트)

## CDK, 터널, 클러스터

- **`SSM parameter /cdk-bootstrap/hnb659fds/version not found`**: 그 계정과 리전에서 CDK bootstrap을 하지 않았습니다. README의 「공통 준비」에 있는 `cdk bootstrap` 명령을 한 번 실행하세요.
- **`python3 cannot import aws_cdk` 또는 `ModuleNotFoundError: No module named 'aws_cdk'`**: 가상 환경이 활성화되지 않은 터미널입니다. `source .venv/bin/activate`를 실행한 뒤 다시 실행하세요. 가상 환경이 없으면 README의 「공통 준비」대로 `uv pip install -r cdk/requirements.txt`를 먼저 실행합니다.
- **`Cloud assembly schema version mismatch`**: CDK CLI가 오래됐습니다. `npm install -g aws-cdk`로 2.1148.1 이상으로 올리세요.
- **`ADMIN_PRINCIPAL_ARN must list IAM role or user ARNs, not sts assumed-role ARNs`**: 넣은 값 중에 IAM 역할이나 사용자 ARN 형식이 아닌 것이 있습니다. STS 세션 ARN(`arn:aws:sts::...:assumed-role/...`)을 넣었다면 그 역할의 ARN으로 바꾸거나 값을 비워 두세요.
- **`cdk/tunnel.sh`가 `TargetNotConnected`로 끝남**: 배포 직후에는 접속 인스턴스가 아직 준비되지 않았을 수 있습니다.
    1. 몇 분 뒤 다시 실행하세요.
    2. 10분이 지나도 같으면 접속 인스턴스의 SSM 상태(`PingStatus`)를 확인하세요.
    3. `ConnectionLost`이면 `aws ec2 reboot-instances --instance-ids <instance-id>`로 재부팅하고, `Online`으로 돌아온 뒤 다시 실행합니다. 인스턴스 ID는 `tunnel.sh`가 출력하는 `via i-...` 값입니다.
- **kubectl이 `TLS handshake timeout`으로 실패**: 이전 클러스터의 터널이 아직 `127.0.0.1:8443`을 쓰고 있을 수 있습니다. 예전 터널을 띄운 터미널을 Ctrl-C로 닫고 `cdk/tunnel.sh`를 다시 실행하세요.
- **노드 그룹 생성이 vCPU 한도 오류로 실패**:
    - **GPU 노드 그룹이면**: Service Quotas에서 `Running On-Demand G and VT instances`를 올리세요. 시나리오 A는 trainer 8과 gVisor 노드 두 대의 4씩, 합쳐서 16 vCPU가 필요합니다.
    - **system 노드나 CPU 노드가 실패했다면**: `Running On-Demand Standard` 쿼터를 확인하세요.
- **노드 그룹 생성이 `InsufficientInstanceCapacity`로 실패하거나, 첫 생성이 30분쯤 멈춘 뒤 전체가 롤백됨**: 먼저 노드 그룹의 실패 사유를 확인하세요. `InsufficientInstanceCapacity`는 그 AZ에서 요청한 유형의 인스턴스를 필요한 수만큼 확보하지 못했다는 뜻입니다.
    - **기존 클러스터에 GPU 노드 그룹을 추가하다 실패했다면**: 그 업데이트만 롤백되니, 잠시 뒤 실패한 단계만 다시 실행하세요.
    - **GPU 용량 부족으로 첫 클러스터 생성 전체가 롤백됐다면**: 아래 명령으로 GPU 노드 그룹 없이 클러스터를 먼저 만들고 노드 그룹을 하나씩 추가하세요(`scripts/config.env`의 `SCENARIO`가 `A`이고 `WITH_KATA_GPU`가 `"0"`일 때).

```bash
scripts/02_create_cluster.sh --hyperpod-b2                  # no EC2 GPU node groups
CHANGE_SCENARIO=1 scripts/02_create_cluster.sh --hyperpod   # adds the gVisor nodes (B1)
CHANGE_SCENARIO=1 scripts/02_create_cluster.sh              # adds the trainer (A)
```

자세히: [CDK와 터널](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#cdk와-터널), [클러스터와 노드](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#클러스터와-노드)

## gVisor

- **smoke pod에 `cuda ok:` 줄 대신 PyTorch 오류가 나오거나, 샌드박스 로그에 `torch.cuda.is_available() is False`**: 샌드박스 안에서 GPU 동작 확인에 실패했습니다.
    1. 노드의 `nvidia.com/gpu` 수와 NVIDIA device plugin pod 상태를 확인하세요.
    2. GPU 수가 보이면 device plugin 설정이 `deviceListStrategy: cdi-cri`인지와 PyTorch 오류 문구를 함께 확인하세요.
- **GPU pod가 `StartError`로 끝나고 이벤트에 `reading mounts file:`**: NVIDIA toolkit의 CDI hook 하나가 gVisor와 맞지 않아 생기는 문제입니다. `04_install_gpu_stack.sh`가 이 hook을 끕니다. device plugin DaemonSet의 `CDI_DISABLE_HOOKS` 값이 `disable-device-node-modification`인지 확인하세요.
- **`04_install_gpu_stack.sh`가 `every GPU on the sandbox-gvisor nodes is in use`로 멈춤**: 이미 배포한 샌드박스 pool이 gVisor 노드의 GPU를 모두 쓰고 있어서 smoke pod가 GPU를 받을 수 없습니다. 출력된 명령으로 pool을 0으로 줄이고 다시 실행한 뒤, `scripts/06_deploy_sandboxes.sh gvisor v1`로 pool을 되돌리세요.
- **노드 로그에 `NVIDIA driver ... is not supported by gVisor`**: 노드의 드라이버 버전이 고정한 gVisor 버전의 지원 목록에 없습니다. 지원 드라이버가 들어 있는 AMI를 쓰거나, 그 드라이버를 지원하는 버전으로 `GVISOR_RELEASE`를 바꾸세요.
    - **CDK로 만든 EC2 노드 그룹**: 새 노드가 처음 부팅할 때 gVisor를 설치합니다. 이 노드 그룹에서 `GVISOR_RELEASE`를 바꿨다면 같은 시나리오로 `scripts/02_create_cluster.sh`를 다시 실행하세요.

자세히: [gVisor](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#gvisor)

## Kata

- **Kata CPU pod가 KVM을 열지 못함(노드에 `/dev/kvm` 없음)**: 노드에 nested virtualization이 켜져 있지 않습니다. 실행 중인 인스턴스의 `CpuOptions`와, 그 인스턴스 유형이 nested virtualization을 지원하는지(`SupportedFeatures`) 확인하세요.
- **`scripts/kata/gpu_nodes.sh`가 `add KATA_IOMMU_AMI_ID and WITH_KATA_GPU=1 ...`로 끝남**: 정상입니다. 첫 실행은 AMI만 만듭니다. 출력된 `KATA_IOMMU_AMI_ID`를 `scripts/config.env`에 넣고 `WITH_KATA_GPU`를 `"1"`로 바꾼 뒤, `scripts/02_create_cluster.sh`와 `scripts/kata/gpu_nodes.sh`를 차례로 다시 실행하세요.
- **`no passthrough GPUs advertised`**: IOMMU가 꺼져 있거나 GPU Operator가 노드를 준비하지 못했습니다. 먼저 `KATA_IOMMU_AMI_ID`가 Kata용 AMI 빌드 스크립트로 만든 이미지인지 확인하세요. AMI가 맞다면 노드의 `nvidia.com/gpu.workload.config=vm-passthrough` 라벨과 GPU Operator pod 상태를 확인하세요.
- **Kata GPU pod가 `ContainerCreating`에 머물고 노드 로그에 `No available IOMMU models`**: 이전 AMI에서 `vfio_iommu_type1` 모듈이 로드되지 않은 경우입니다.
    - **새 노드를 만들 때**: 지금 스크립트로 AMI를 다시 만들어 `KATA_IOMMU_AMI_ID`를 바꾸고 `scripts/02_create_cluster.sh`를 다시 실행하세요.
    - **현재 노드에서는**: `modprobe vfio_iommu_type1`을 실행하세요. 재부팅하면 다시 실행해야 합니다.

자세히: [Kata](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#kata)

## 샌드박스 pool

<span id="샌드박스-풀"></span>

- **`06_deploy_sandboxes.sh`가 `exceeded its progress deadline`으로 실패**: pod의 STATUS부터 보세요.
    - **`Pending`이나 `ContainerCreating`이면**: `kubectl -n sandbox describe pod <pod>`의 Events를 확인하세요.
    - **`Running`인데 `0/1`이면**: `kubectl -n sandbox logs <pod>`를 보세요. `device probe ok=False` 줄이 있으면 같은 줄의 `info`에서 장치 확인 실패 사유를 보고, `egress is open, refusing work:` 줄이 있으면 외부 연결 차단 설정을 확인하세요.
- **로그에 `egress is open, refusing work: 169.254.169.254:80 (connected)`**: pod에서 EC2 인스턴스 메타데이터 서비스(IMDS)에 연결할 수 있는 상태입니다. NetworkPolicy가 적용되지 않은 것입니다. `kubectl -n sandbox get networkpolicy`로 정책 목록을 보고, VPC CNI 애드온의 `enableNetworkPolicy`가 켜져 있는지 확인하세요.
- **`sandbox_error`와 `no free sandbox in sandbox-<runtime>-<version>...`**: 600초 동안 평가를 맡길 pod를 찾지 못했습니다. 먼저 Ready인 pod가 있는지 확인하세요.
    - **모든 pod가 계속 평가 중이라면**: replica 수를 늘리세요. GPU pool은 pod 하나가 GPU 하나를 쓰므로, 남는 GPU가 없으면 노드 수도 함께 늘려야 합니다.
- **401, 403 응답**: 토큰, JWKS, 허용 목록 설정 문제입니다. 오류 문구별 해결 방법은 [401, 403 응답](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#401-403-응답)에 있습니다.

자세히: [샌드박스 pool과 readiness](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#샌드박스-pool과-readiness)

## 학습

- **TRL trainer 로그에 `CUDA out of memory`**: vLLM의 답안 생성과 모델 학습이 같은 GPU 메모리를 공유합니다. Job 템플릿의 `args`에 `--per-device-batch=2`와 `--grad-accum=8`을 지정하세요. 이렇게 하면 배치 크기와 누적 횟수를 곱한 값은 16으로 유지됩니다. 그래도 부족하면 `--max-completion-length=512`, `--vllm-gpu-memory-utilization=0.3`을 차례로 넣어 보세요.
- **`reward_batch`에 `sandbox_error`가 많음**: `scripts/ops/verify.sh <runtime> <version>`으로 같은 pool을 점검하세요. 실패한 단계와 오류 문구에 따라 인증, 네트워크, pod 부족, 평가 시간 초과 중 해당 항목부터 점검하세요.

자세히: [학습](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#학습)

## HyperPod

### 관리형 B2에서 확인한 문제

| 실습에서 본 증상 | 해결 방법 |
|---|---|
| 그룹은 `InService`인데 `CurrentCount`가 `TargetCount`보다 작음 | `list-cluster-nodes --include-node-logical-ids`로 각 요청을 확인합니다. 이번에는 `INSUFFICIENT_CAPACITY_ERROR`가 발생했고 HyperPod가 `Continuous` 모드에서 다시 요청해 GPU 세 대를 확보했습니다. |
| 마법사 스택은 `CREATE_COMPLETE`인데 학습 애드온이 cert-manager 관련 `K8sResourceNotFound`를 반환 | 워커가 준비된 뒤 `scripts/hyperpod/prepare_managed.sh`를 실행합니다. 인증서 웹훅이 준비될 때까지 기다린 뒤 실패한 애드온을 같은 버전으로 다시 설치합니다. |
| 채점 노드에 `595.112.07`이 표시되거나 `nvidia_uvm` 모듈이 사용 중 | 두 채점 워커가 `Ready`가 되면 `scripts/hyperpod/reboot_sandboxes.sh`로 `580.178.04`를 디스크에 설치하고 HyperPod API로 재부팅합니다. 마지막에 실행 중인 커널 모듈의 버전을 확인합니다. |

[재현 명령과 실행 화면, 정리 절차](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/07_hyperpod_b2/)

- **클러스터는 `InService`인데 trainer 인스턴스가 `Pending`입니다.** B1 실습에서는 클러스터가 먼저 준비됐습니다. `source scripts/config.env`를 실행하고 `aws sagemaker list-cluster-nodes --region "$AWS_REGION" --cluster-name "$HYPERPOD_CLUSTER_NAME"`로 인스턴스 상태를 보세요. 이어서 `kubectl get nodes -L sagemaker.amazonaws.com/node-health-status`에서 `Ready`와 `Schedulable`을 확인하세요. [B1 실행 화면](https://daekeun-ml.github.io/gpu-sandbox-on-aws/handson/07_hyperpod_b1/#확인-방법)
- **Worker가 `Pending`이고 이벤트에 `Insufficient cpu` 또는 `Insufficient memory`가 나옵니다.** `kubectl describe node <trainer-node>`에서 이미 할당된 자원을 확인하세요. B1의 `ml.g5.2xlarge`에서는 operator와 시스템 pod도 같은 노드를 사용했습니다. 템플릿이 worker에 요청하는 자원은 CPU 5개와 메모리 24 GiB입니다.

- **pod가 `hyperpodrun`을 찾지 못함**: trainer 이미지를 `HYPERPOD=1` 없이 빌드했습니다. 새 `IMAGE_TAG`로 `HYPERPOD=1 scripts/03_build_push_images.sh`를 실행하고, 출력된 `TRAINER_IMAGE_URI`를 `scripts/config.env`에 넣은 뒤 학습을 다시 시작하세요.
- **`check_gvisor.sh`가 `NOT supported`를 출력함**:
    - **trainer 노드에서 나오면**: 정상입니다. trainer 노드에서는 샌드박스를 실행하지 않습니다.
    - **sandbox 노드에서 나오면**: 인스턴스 그룹의 `ImageId`가 `HYPERPOD_B2_AMI_ID`와 같은지, 그 AMI의 드라이버를 `GVISOR_RELEASE`가 지원하는지 확인하세요.
- **CreateCluster 뒤 상태가 `Failed`**: 스크립트 출력의 `failure` 항목에서 실패 사유를 보고, HyperPod EKS 사전 요구사항과 비교하세요.

자세히: [HyperPod](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#hyperpod)

## 정리와 비용

리전을 확인하거나 아래 AWS CLI 명령을 쓰기 전에 프로젝트 최상위 폴더에서 `source scripts/config.env`를 실행하세요.

- **`08_cleanup.sh`를 실행한 뒤에도 요금이 계속 발생함**: 실행한 리전이 맞는지, AMI와 스냅샷이 남았는지 확인하세요.
    - **HyperPod를 만들었다면**: `08_cleanup.sh`는 HyperPod를 지우지 않습니다. `scripts/08_cleanup.sh`보다 먼저 `scripts/hyperpod/delete.sh`를 실행해야 합니다.
    - **ECR만 남았다면**: `cdk/destroy.sh`가 출력한 ECR 삭제 명령이 가리키는 리포지토리 이름을 확인한 뒤 실행하세요.
    - **ECR까지 한 번에 지우려면**: 처음 정리할 때 `scripts/08_cleanup.sh --images`로 실행하세요.
- **`g4dn.metal`을 쓰지 않는 동안에도 과금됨**: 노드 그룹을 0으로 줄이세요(아래 명령).

```bash
aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu \
  --scaling-config minSize=0,maxSize=1,desiredSize=0
```

자세히: [정리와 비용](https://daekeun-ml.github.io/gpu-sandbox-on-aws/reference/troubleshooting/#정리와-비용)
