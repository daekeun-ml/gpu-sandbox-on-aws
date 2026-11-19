# 문제 해결

**TL;DR** 설치와 운영 중에 자주 생기는 문제를 단계별 "증상, 원인, 해결" 표로 정리하고, 단계마다 바로 실행할 수 있는 진단 명령을 붙였습니다.

## 기존 Pain Point

증상은 원인이 생긴 단계보다 한참 뒤에 나타나는 경우가 많습니다. 예를 들어 노드 user data 오류가 몇 단계 뒤에 "pod Pending"이나 "GPU 없음"으로 나타납니다. gVisor와 Kata pod 안에서 보이는 커널, 장치, 네트워크는 노드와 달라서, 노드에서 확인할 것과 pod 안에서 확인할 것을 구분해야 합니다. 인증 실패나 NetworkPolicy 차단은 그 샘플을 `sandbox_error`로 만들 뿐 학습을 멈추지 않습니다. TRL은 세 reward를 모두 `None`으로 반환해 group baseline에서 빼고, veRL은 format 점수 0.1과 `sandbox_error: 1`을 기록하므로, 학습 로그에는 `sandbox_error` 개수로만 나타나요.

## Why

- **진단 명령의 namespace, 라벨, 경로는 저장소 스크립트가 만드는 이름 그대로입니다.**
- **"(추정)"으로 표시한 원인은 코드나 문서로 확인하지 못한 것입니다.** pod 이벤트와 노드 로그로 직접 확인하세요.

!!! warning "이 페이지의 근거"
    2026-11-14에 저자는 시나리오 C의 CDK 배포, 터널, Kata CPU 노드 추가(`kata/cpu_nodes.sh`), 삭제를 실습 계정에서 실행했습니다. 실습 계정에서 2026-11-18에는 us-west-2의 시나리오 A를 `g5`로 실행했어요. 클러스터는 GPU 노드 그룹 없이 만든 뒤 update로 추가했고(아래 "GPU 용량이 없을 때"), `03_build_push_images.sh`, `04_install_gpu_stack.sh`, `05_setup_namespaces_auth.sh`, `06_deploy_sandboxes.sh gvisor v1`(1 replica)과 `ops/verify.sh gvisor v1`, `07_run_grpo.sh 5`, `08_cleanup.sh --images`를 실행했어요. 같은 날 다른 클러스터 구성(system 전용으로 만든 뒤 `CHANGE_SCENARIO=1`로 Kata CPU, Kata GPU, gVisor 노드 그룹 추가)에서 Kata GPU(`g4dn.metal`), `ops/bench.sh`, 데모 사이트(us-east-1)도 실행했습니다. 아래 Kata GPU의 `vfio_iommu_type1` 행과 AMI 빌더 행은 이 실행에서 나왔어요. 시나리오 A의 `ops/rollout.sh`, 기본값 60 step 학습, HyperPod B1과 B2는 실행하지 않았고, 실험용 CLH GPU는 VM이 시작되지 않았습니다([검증 상태](../index.md)). 증상과 원인은 스크립트 오류 메시지, 코드 동작, 공식 문서에서 가져왔습니다. 에러 문구는 도구 버전마다 다를 수 있어요.

??? note "용어"
    - **readiness**: kubelet이 pod가 요청을 받을 준비가 됐는지 확인하는 검사입니다. 이 저장소에서는 GPU probe와 egress 차단 확인이 모두 통과해야 Ready가 됩니다.
    - **`kubectl debug node`**: 노드에 특권 디버그 pod를 실행해, 노드의 파일 시스템(`/host`)과 프로세스를 볼 수 있게 해 주는 명령입니다.
    - **user data, cloud-init**: user data는 EC2 인스턴스가 처음 부팅할 때 실행하는 스크립트이고, cloud-init은 그 스크립트를 실행하는 도구입니다. 출력은 `/var/log/cloud-init-output.log`에 기록됩니다.
    - **nodeadm, NodeConfig**: EKS AL2023 노드를 클러스터에 등록하는 부트스트랩 도구와 그 설정입니다. containerd 런타임 설정도 NodeConfig를 통해 병합됩니다.
    - **EndpointSlice**: Service에 연결된 pod 주소와 각 주소의 Ready 여부를 담은 목록입니다. headless Service의 DNS는 Ready인 주소만 반환합니다.
    - **SSM Session Manager**: SSH 없이 IAM 권한으로 인스턴스 셸을 여는 AWS Systems Manager 기능입니다.

    더 많은 용어는 [용어 사전](glossary.md)에 있습니다.

## 진단 도구

### pod 상태, 이벤트, 로그

아래 명령은 샌드박스 pod 목록(runtime, version 라벨 포함), pod 하나의 이벤트와 로그, 클러스터 전체의 최근 이벤트를 차례로 보여 줍니다.

```bash
source scripts/config.env      # CLUSTER_NAME and AWS_REGION for the AWS commands on this page
kubectl -n sandbox get pods -o wide -L gpusandbox/runtime,gpusandbox/version
kubectl -n sandbox describe pod <pod>          # Events: scheduling, RuntimeClass, probe failures
kubectl -n sandbox logs <pod>                  # "device probe ok=..." and "egress is open, refusing work: ..."
kubectl -n sandbox logs <pod> --previous       # after a restart (for example a gpu_fault)
kubectl get events -A --sort-by=.lastTimestamp | tail -30
```

readiness 문제는 서버 로그의 두 줄로 대부분 분류할 수 있습니다. 샌드박스 서버는 시작할 때 `device probe ok=<True|False> info=<...>`를 남기고, egress 대상에 연결되면 `egress is open, refusing work: <대상 목록>`을 ERROR 로그로 남겨요.

### 샌드박스 안에서 확인 (kubectl exec)

아래 명령은 gVisor v1 풀의 pod 하나를 선택해 샌드박스 안과 노드의 커널 버전을 비교하고, 새 프로세스에서 GPU가 보이는지와 첫 CUDA 연산이 되는지 확인합니다. GPU가 보여도 첫 연산이나 동기화에서 실패할 수 있어요.

```bash
pod="$(kubectl -n sandbox get pods -l gpusandbox/runtime=gvisor,gpusandbox/version=v1 \
  -o jsonpath='{.items[0].metadata.name}')"
# Kernel seen inside the sandbox (gVisor Sentry or Kata guest kernel) vs the node's kernel
kubectl -n sandbox exec "$pod" --\
  uname -r
kubectl get node "$(kubectl -n sandbox get pod "$pod" -o jsonpath='{.spec.nodeName}')" \
  -o jsonpath='{.status.nodeInfo.kernelVersion}{"\n"}'
# GPU visibility from a fresh process inside the sandbox
kubectl -n sandbox exec "$pod" --\
  python -c "import torch; ok = torch.cuda.is_available(); print('cuda', ok, torch.version.cuda); print(torch.cuda.get_device_name(0) if ok else 'no device')"
# The first CUDA operation the server's startup device probe runs (readiness needs it to pass)
kubectl -n sandbox exec "$pod" --\
  python -c "import torch; torch.ones(1, device='cuda').add_(1); torch.cuda.synchronize(); print('cuda op ok')"
```

두 커널 값이 같으면 pod가 runc로 실행되고 있다는 뜻이니 RuntimeClass를 먼저 확인하세요. `exec`로 실행한 프로세스도 샌드박스 안에서 실행되므로 NetworkPolicy와 node guard가 똑같이 적용됩니다. 줄 끝의 `--\`는 kubectl 인자 구분자 `--` 뒤에서 줄을 이은 것입니다.

### probe 도구로 /info 보기

`/info`는 인증이 필요합니다. audience가 `SANDBOX_AUDIENCE`인, 허용 목록에 있는 ServiceAccount의 토큰을 Bearer로 보내야 하고, 연결도 NetworkPolicy가 허용한 pod에서만 됩니다. 그래서 내 PC에서 `curl`로 바로 볼 수는 없어요. 대신 control 이미지의 probe 도구를 `rl-trainer` namespace의 Job으로 실행하면(ServiceAccount `sandbox-probe`, 라벨 `gpusandbox/client: "true"`) pod마다 `/info` 요약과 golden verdict가 출력돼요. 아래 첫 명령은 Ready pod 전체를, 두 번째 명령은 Ready가 아닌 pod 하나를 IP로 직접 점검합니다.

```bash
# Ready pods behind the headless Service: /info summary per pod and golden verdicts
scripts/ops/verify.sh gvisor v1

# A pod that is not Ready is not in DNS: point the probe tool at its pod IP (run from the repo root)
pod_ip="$(kubectl -n sandbox get pod "$pod" -o jsonpath='{.status.podIP}')"
bash -c "source scripts/lib.sh && source scripts/lib_jobs.sh && run_tool_job probe-debug probe --address ${pod_ip}:8000 --device cuda"
```

출력 앞부분에는 pod마다 `{"endpoint": ..., "pod": ..., "runtime": ..., "version": ..., "kernel_release": ..., "gpu": ..., "egress_blocked": ...}` 한 줄이 나오고, 그 뒤에 golden마다 `PASS` 또는 `FAIL` 줄이 이어집니다. Ready가 아닌 pod는 평가 요청에 503을 반환하므로 golden 줄이 `sandbox_error`로 FAIL 하는 것이 정상이에요. probe 도구는 `/info`의 `egress_open_targets`를 출력하지 않으니, 어느 대상이 열려 있는지는 서버 로그의 `egress is open` 줄에서 확인하세요. CPU 풀이면 `--device cpu`를 씁니다.

### 노드에서 확인 (kubectl debug node)

아래 명령은 pod가 실행 중인 노드에 특권 디버그 pod를 실행하고 그 안의 셸을 엽니다. 셸 프롬프트가 나오면 성공입니다.

```bash
node="$(kubectl -n sandbox get pod "$pod" -o jsonpath='{.spec.nodeName}')"
kubectl debug "node/$node" -it --profile=sysadmin \
  --image=public.ecr.aws/amazonlinux/amazonlinux:2023
```

디버그 셸 안에서는 노드의 루트 파일 시스템이 `/host`에 마운트됩니다.

```bash
chroot /host
cat /proc/cmdline                                 # Kata GPU node: intel_iommu=on iommu=pt
ls -l /dev/kvm                                    # Kata nodes (CPU and GPU) need it
cat /proc/driver/nvidia/version                   # gVisor and trainer nodes: loaded driver
/usr/local/bin/runsc nvproxy list-supported-drivers | grep -wF <driver-version>
grep -n -A3 runsc /etc/containerd/config.toml     # runsc handler merged by nodeadm
cat /etc/containerd/runsc.toml                    # nvproxy settings read by the shim
iptables -w -S GPUSANDBOX-GUARD                   # node guard chain on sandbox nodes
systemctl status gpusandbox-node-guard --no-pager
tail -n 100 /var/log/cloud-init-output.log        # user data output (gVisor install, node guard)
journalctl -u containerd -u kubelet --since "30 min ago" --no-pager | tail -50
exit
```

끝나면 `default` namespace에 남은 디버그 pod를 지웁니다.

```bash
kubectl get pods -n default -o name | grep node-debugger-
kubectl -n default delete pod <node-debugger-pod>
```

### AWS 쪽 확인 (노드 그룹, 인스턴스)

아래 명령은 노드 그룹의 상태와 health 문제, 그 노드 그룹이 쓰는 Auto Scaling group의 최근 활동 5개를 보여 줍니다.

```bash
ng=sandbox-gvisor      # system, trainer, sandbox-gvisor, sandbox-kata-cpu, sandbox-kata-gpu
aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "$ng" \
  --region "$AWS_REGION" --query 'nodegroup.{status: status, health: health}'
asg="$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "$ng" \
  --region "$AWS_REGION" --query 'nodegroup.resources.autoScalingGroups[0].name' --output text)"
aws autoscaling describe-scaling-activities --auto-scaling-group-name "$asg" \
  --region "$AWS_REGION" --max-items 5 --query 'Activities[].[StatusCode,StatusMessage]' --output text
```

노드가 클러스터에 등록되지 않으면 `health`에 나온 인스턴스 ID로 접속해 user data 로그를 봅니다. Session Manager plugin이 로컬에 있어야 하고, 노드 IAM 역할에 SSM 권한(`AmazonSSMManagedInstanceCore`)이 있어야 세션이 열려요. CDK 스택의 노드 역할에는 이 정책이 없습니다(`cdk/gpusandbox_cdk/stack.py`의 `node_policies`). SSM 세션이 필요하면 디버깅하는 동안만 이 정책을 노드 역할에 연결하고, 그렇지 않으면 아래 콘솔 출력을 보세요.

```bash
aws ssm start-session --target <instance-id> --region "$AWS_REGION"
# on the instance
sudo tail -n 200 /var/log/cloud-init-output.log
sudo journalctl -u nodeadm-config -u nodeadm-run --no-pager | tail -100
```

SSM을 쓸 수 없으면 콘솔 출력으로도 user data 오류를 볼 수 있는 경우가 많습니다(추정).

```bash
aws ec2 get-console-output --instance-id <instance-id> --latest --output text --region "$AWS_REGION" | tail -100
```

## 설정과 스크립트

| 증상 | 원인 | 해결 |
|---|---|---|
| `scripts/config.env not found. Copy scripts/config.env.example and edit it.` | 설정 파일이 없음 | `cp scripts/config.env.example scripts/config.env` 후 값 채우기 |
| `[error] set CLUSTER_NAME in scripts/config.env` 같은 메시지 | 값이 비었거나 `__SET_ME__`가 남음(`require_vars`) | 값 채우기. 이미지 URI처럼 스크립트가 출력하는 값은 그 스크립트(`03_build_push_images.sh`, `kata/gpu_nodes.sh`)를 먼저 실행 |
| `[error] missing tool: <tool>` | 필요한 CLI가 PATH에 없음(`require_tools`) | 설치 후 `scripts/01_check_prereqs.sh` 재실행 |
| `render: <template>: missing variable 'X'` | 템플릿의 `${X}`에 값이 없음. `render.py`는 빈 값으로 대체하지 않음 | config.env나 셸에서 `export X=...` |
| Kata CPU 노드 추가(`scripts/kata/cpu_nodes.sh`)가 `no sandbox-kata-cpu node group: set WITH_KATA_CPU=1 in scripts/config.env and run scripts/02_create_cluster.sh again`로 멈춤 | 노드 그룹 조회가 실패하면 원인과 관계없이 나옴. 시나리오 C가 아닌데 `WITH_KATA_CPU=1` 없이 스택을 만들었거나, `CLUSTER_NAME`, `AWS_REGION`이 다르거나, `eks:DescribeNodegroup` 권한이 없음 | `aws eks describe-nodegroup --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-cpu`를 직접 실행해 오류를 확인. `AccessDeniedException`이면 권한을 확인. `ResourceNotFoundException`이면 `CLUSTER_NAME`과 `AWS_REGION`을 확인하고, 맞다면 config.env에 `WITH_KATA_CPU=1`을 넣고 `02_create_cluster.sh` 재실행(CDK가 c8i 노드 그룹만 추가함), 그다음 `kata/cpu_nodes.sh` 재실행 |
| Kata GPU 노드 추가(`scripts/kata/gpu_nodes.sh`)가 `add KATA_IOMMU_AMI_ID and WITH_KATA_GPU=1 to scripts/config.env, run scripts/02_create_cluster.sh again, then re-run this script`로 끝남 | 정상 동작: 첫 실행은 AMI만 빌드(스크립트 안내 기준 약 10분) | 출력된 AMI ID와 `WITH_KATA_GPU=1`을 넣고 `02_create_cluster.sh` 재실행(`metal` 입력), 그다음 `kata/gpu_nodes.sh` 재실행 |
| Kata GPU 노드 추가의 첫 실행(`infra/kata/build-iommu-ami.sh`)이 `Waiter InstanceStopped failed ... "pending"`으로 바로 실패 | 이전 스크립트의 `aws ec2 wait instance-stopped`는 `pending` 상태를 terminal failure로 처리함. 빌더가 아직 running이 되기 전에 waiter가 시작되면 바로 실패하고, 이전 스크립트는 이때 빌더를 terminate하지 않음(2026-11-18 실측) | 스크립트에서 고쳤습니다: waiter 대신 15초 간격으로 상태를 조회(최대 30분, shutting-down이나 terminated면 실패)하고, EXIT trap이 항상 빌더를 terminate함. 이전 버전으로 실패했다면 `<CLUSTER_NAME>-iommu-ami-builder` 인스턴스를 terminate한 뒤 최신 스크립트로 다시 실행 |
| `scripts/kata/gpu_nodes.sh`가 `no sandbox-kata-gpu node group: set WITH_KATA_GPU=1 in scripts/config.env and run scripts/02_create_cluster.sh again`로 멈춤 | AMI는 있지만 `WITH_KATA_GPU=1`로 `02_create_cluster.sh`를 다시 실행하지 않음 | `WITH_KATA_GPU=1`을 넣고 `02_create_cluster.sh` 재실행, 그다음 `kata/gpu_nodes.sh` 재실행 |
| `03_build_push_images.sh`를 다시 실행하자 push가 태그 중복으로 실패 | ECR 저장소를 IMMUTABLE 태그로 만듦 | `IMAGE_TAG`를 새 값(예: `v1-hp`)으로 바꾸고 재실행, 출력된 URI로 config.env 갱신 |
| `03_build_push_images.sh`의 빌드가 매우 느리거나 디스크가 부족함 | arm64 PC에서 linux/amd64를 에뮬레이션, 큰 베이스 이미지(PyTorch, vLLM) | x86_64 호스트에서 디스크 100 GB 이상으로 빌드(스크립트 주석 기준) |

## CDK와 터널

| 증상 | 원인 | 해결 |
|---|---|---|
| `cdk deploy`가 `SSM parameter /cdk-bootstrap/hnb659fds/version not found. Has the environment been bootstrapped?`로 실패 | 그 계정과 리전에 CDK bootstrap을 하지 않음 | `cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/$AWS_REGION"`를 한 번 실행 |
| synth 중 cdk-nag `AwsSolutions-...` 지적과 함께 `ValidationFailed`로 배포가 멈춤 | 예외 처리되지 않은 cdk-nag 지적이 있음(스택 코드나 cdk-nag 버전이 바뀜) | 출력의 규칙 ID와 리소스를 보고 고칩니다. 의도적으로 따르지 않는 규칙이라면 `cdk/gpusandbox_cdk/stack.py`의 `_suppress`에 이유를 적어 예외 처리하고, 이유 없이 예외 처리하지 않기 |
| `Cloud assembly schema version mismatch` | CDK CLI가 `cdk/requirements.txt`의 `aws-cdk-lib`보다 오래됨 | `npm install -g aws-cdk`로 CLI를 2.1148.1 이상으로 올리기. 이 저장소는 CLI 2.1148.2가 필요한 `aws-cdk-lib` 2.277.0 대신 2.276.0에 고정(2026-11-14 기준) |
| `ADMIN_PRINCIPAL_ARN must list IAM role or user ARNs, not sts assumed-role ARNs` | STS 세션 ARN(`arn:aws:sts::...:assumed-role/...`)을 넣음 | `aws iam get-role --role-name <역할> --query Role.Arn --output text`로 얻은 역할 ARN을 넣거나 비워 두기 |
| `EKS_PUBLIC_ACCESS_CIDR must be a single IPv4 address in /32 form` | `0.0.0.0/0`이나 /24 같은 범위를 넣음 | 비워 두거나(private만) 작업 PC 주소 하나를 `/32`로 |
| `cdk/tunnel.sh`가 `stack <CLUSTER_NAME>-cdk has no outputs; run cdk/deploy.sh first`로 멈춤 | 스택이 아직 없거나, `CLUSTER_NAME`, `AWS_REGION`이 배포할 때와 다름 | config.env 값을 확인하고 `02_create_cluster.sh` 실행 |
| `cdk/tunnel.sh`가 `TargetNotConnected`로 끝남 | access instance의 SSM agent가 아직 Systems Manager에 등록되지 않음(배포 직후) | 몇 분 기다렸다 다시 실행 |
| `cdk/tunnel.sh`가 `[error] missing tool: session-manager-plugin`으로 멈춤 | AWS CLI용 Session Manager plugin이 없음 | [Session Manager plugin 설치](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) 후 `session-manager-plugin --version`으로 확인 |
| `cdk/destroy.sh`가 `cluster API not reachable (is cdk/tunnel.sh running?)` 경고를 냄 | 터널이 꺼져 있어 풀과 Job을 먼저 지우지 못함 | 그대로 두어도 스택 삭제가 노드를 지웁니다. 풀부터 지우려면 터널을 켜고 다시 실행 |

**오래 쉰 터널이 끊길 때:** 긴 작업 중에는 `cdk/tunnel.sh` 세션이 끊길 수 있습니다(2026-11-18 실행에서 두 번). `kubectl`이 연결 오류로 실패하면 터널 터미널을 확인하고 `cdk/tunnel.sh`를 다시 실행하세요. 오래 기다리는 작업 중에는 다른 터미널에서 1분에 한 번쯤 가벼운 요청을 보내면 유휴 터널이 유지됩니다.

```bash
# Keep an idle tunnel alive with one cheap API request per minute (Ctrl-C stops it)
while sleep 60; do kubectl get --raw /healthz >/dev/null || echo "$(date +%T) API unreachable: rerun cdk/tunnel.sh"; done
```

## 클러스터와 노드

| 증상 | 원인 | 해결 |
|---|---|---|
| 노드 그룹 생성 실패, health나 scaling activity에 vCPU 한도 오류(`VcpuLimitExceeded` 류) | "Running On-Demand G and VT instances" quota(vCPU 기준) 부족. 신규 계정은 기본값이 0일 수 있음 | Service Quotas에서 증가 요청. trainer 8 + gVisor 2 x 4 = 16 vCPU, `g4dn.metal`은 96 vCPU 추가. HyperPod는 "ml.<type> for cluster usage" quota가 따로 있음 |
| 노드 그룹 생성 실패, 요청한 AZ에서 인스턴스 유형을 지원하지 않는다는 오류 | 클러스터 서브넷의 AZ가 그 유형(특히 `g4dn.metal`)을 제공하지 않음 | `scripts/01_check_prereqs.sh`의 AZ별 offering 확인. CDK 스택은 리전의 AZ 두 개(`max_azs=2`)에 private subnet을 만들고 모든 노드 그룹이 둘 다 씁니다. 선택된 AZ가 그 유형을 제공하지 않으면 다른 리전을 쓰거나 `cdk/gpusandbox_cdk/stack.py`의 subnet 선택을 고쳐야 합니다(이 저장소에는 그 옵션이 없음) |
| 노드 그룹 생성이 용량 부족 오류(`InsufficientInstanceCapacity` 류)로 실패 | 그 AZ에 On-Demand 용량이 일시적으로 부족함(일반적인 EC2 동작) | 다른 AZ를 쓰거나 시간을 두고 재시도. 용량이 있는 인스턴스 유형으로 바꾸려면 아래 "GPU 용량이 없을 때" 참고 |
| 첫 클러스터 생성이 약 30분 동안 멈춘 뒤 전체가 롤백됨 | GPU 노드 그룹을 시작하지 못하면(`InsufficientInstanceCapacity`) CloudFormation이 약 30분을 기다린 뒤 첫 생성 전체를 롤백함 | GPU 노드 그룹 없이 클러스터를 먼저 만들고 update로 추가(아래 "GPU 용량이 없을 때"). 실패한 update는 그 update만 롤백됨 |
| 노드 그룹은 있는데 노드가 `kubectl get nodes`에 나타나지 않음(health에 노드 생성 실패) | user data(`infra/eks/userdata.py`가 만든 NodeConfig와 셸 part) 오류, gVisor tarball 다운로드나 sha512 검사 실패, 잘못된 커스텀 AMI | 위 "AWS 쪽 확인"으로 인스턴스를 찾아 `/var/log/cloud-init-output.log`와 `journalctl -u nodeadm-config -u nodeadm-run` 확인 |
| `kubectl`이나 `helm`이 `Unable to connect to the server`, timeout, `127.0.0.1:8443` 연결 거부로 실패 | EKS API endpoint는 private만이라 터널 없이는 접속할 수 없음. 터널 터미널이 닫혔거나 다른 kubectl 컨텍스트를 씀 | 두 번째 터미널에서 `cdk/tunnel.sh`를 다시 실행하고, `kubectl config current-context`가 `<CLUSTER_NAME>-tunnel`인지 확인 |

**GPU 용량이 없을 때:** GPU 노드 그룹이 포함된 첫 생성은 용량 부족 하나로 전체가 롤백됩니다. GPU 노드 그룹 없는 구성으로 클러스터를 먼저 만들고, update로 노드 그룹을 하나씩 추가하세요. 실패한 update는 그 update만 롤백돼요.

```bash
scripts/02_create_cluster.sh --hyperpod-b2                  # no EC2 GPU node groups
CHANGE_SCENARIO=1 scripts/02_create_cluster.sh --hyperpod   # adds the gVisor nodes (B1)
CHANGE_SCENARIO=1 scripts/02_create_cluster.sh              # adds the trainer (A)
```

용량은 인스턴스를 하나 시작했다가 바로 종료해서 확인합니다. On-Demand Capacity Reservation 요청은 실제 시작이 성공하는 상황에서도 용량이 없다고 응답할 수 있어요. 인스턴스 유형은 실행마다 `scripts/config.env`에서 바꿀 수 있습니다. 예를 들어 `g6`에 용량이 있으면 `GVISOR_INSTANCE_TYPE`과 `TRAINER_INSTANCE_TYPE`을 `g6.xlarge`, `g6.2xlarge`로 지정하세요.

## gVisor

| 증상 | 원인 | 해결 |
|---|---|---|
| pod가 `ContainerCreating`에 머물고 이벤트에 `no runtime for "runsc" is configured` 류 메시지(문구는 containerd 버전마다 다름) | RuntimeClass `handler`(`runsc`)와 containerd `runtimes.<이름>` 키가 다름, 또는 NodeConfig 병합 실패 | `kubectl get runtimeclass gvisor -o yaml`의 `handler`와 노드 `/etc/containerd/config.toml`의 `runtimes.runsc` 비교. 이름을 바꿨다면 두 곳을 같게 |
| 이벤트에 `containerd-shim-runsc-v1`을 찾거나 실행할 수 없다는 류의 오류(추정) | user data의 gVisor 설치 실패(다운로드, sha512 검사) | 노드에서 `ls -l /usr/local/bin/runsc /usr/local/bin/containerd-shim-runsc-v1`과 `cloud-init-output.log` 확인. 원인을 고친 뒤 노드 교체 |
| `04_install_gpu_stack.sh`의 gVisor smoke pod에 `cuda ok:` 줄이 없고 torch 오류, 또는 샌드박스 로그에 `torch.cuda.is_available() is False` | device plugin이 그 노드에 없거나 `cdi-cri` 모드가 아님. OCI spec에 NVIDIA 장치가 없으면 nvproxy가 켜지지 않음 | 아래 명령으로 노드의 `nvidia.com/gpu` allocatable, device plugin pod, `deviceListStrategy: cdi-cri` 확인 |
| gVisor GPU pod가 `StartError`로 끝나고 이벤트에 `OCI runtime start failed: starting container: reading mounts file: error unmarshaling mounts: unexpected end of JSON input` | AMI의 nvidia-container-toolkit 1.20.1이 `disable-device-node-modification` CDI hook을 추가하고, 이 hook은 `<rootfs>/proc/driver/nvidia/params`를 읽음. runsc는 CDI hook을 컨테이너에 `/proc`이 생기기 전에 gofer에서 실행하므로 hook이 실패함. runsc debug 로그에는 `error opening nvidia driver params file: openat proc/driver/nvidia/params: no such file or directory`가 남음. GPU 종류와 무관하고(`g6`도 해당), 같은 노드의 GPU 없는 gVisor pod는 정상 | `04_install_gpu_stack.sh`가 `helm upgrade --install nvdp ...` 뒤에 `kubectl -n kube-system set env ds/nvdp-nvidia-device-plugin CDI_DISABLE_HOOKS=disable-device-node-modification`을 실행하고 rollout을 기다림(chart v0.20.1에 값이 없는 plugin의 `--cdi-disable-hooks` 플래그를 env로 설정). 아래 명령의 마지막 줄로 확인하고, 설정이 없으면 위 `kubectl set env` 명령과 `kubectl -n kube-system rollout status ds/nvdp-nvidia-device-plugin`을 직접 실행. A와 B1에서 `04_install_gpu_stack.sh`를 통째로 다시 실행하면 설정 뒤에 GPU 하나를 요청하는 smoke pod도 띄우므로, 기존 풀이 GPU를 모두 쓰고 있으면 smoke pod가 최대 15분 기다린 뒤 스크립트가 실패함(그 전에 GPU 하나를 비우기). runc pod(trainer)는 이 hook만 빠지며, `CAP_MKNOD`가 없어 어차피 장치 노드를 만들 수 없음 |
| `nvidia.com/gpu`는 보이는데 CUDA 초기화가 실패하고, 노드 `cloud-init-output.log`에 `WARNING: NVIDIA driver ... is not supported by gVisor ... nvproxy` | 노드 드라이버가 고정한 gVisor 릴리스의 nvproxy 목록에 없음. 목록에 없는 unknown 버전은 항상 실패 | 노드에서 `runsc nvproxy list-supported-drivers`로 확인. 지원 드라이버의 AMI를 쓰거나, 그 드라이버를 지원 목록에 포함한 릴리스로 `GVISOR_RELEASE`를 올림 |
| `g4dn` 같은 T4 노드에서 gVisor GPU가 동작하지 않음 | gVisor에서 T4 사용은 이 저장소에서 테스트하지 않아 미검증. 드라이버 조건(EKS AL2023 NVIDIA AMI가 GSP를 끈 proprietary 모듈을 로드)은 기본값 g5와 같으므로 드라이버 종류 때문에 제외할 이유는 없음 | 이 저장소의 기본값인 g5(A10G)나 대안인 g6(L4)를 사용. T4를 쓰려면 노드에서 `runsc nvproxy list-supported-drivers`, smoke test, `scripts/ops/verify.sh`로 직접 검증 |
| `runsc.toml`을 고쳤는데 반영되지 않음 | shim은 runtime 옵션의 `ConfigPath` 파일만 읽고, 이미 실행 중인 pod는 이전 설정을 씀 | NodeConfig의 `ConfigPath = '/etc/containerd/runsc.toml'` 확인 후 pod를 다시 만듦 |

아래 명령은 device plugin 라벨이 붙은 노드의 GPU allocatable, device plugin pod, 설치된 chart 값, CDI hook 설정을 차례로 보여 줍니다. `04_install_gpu_stack.sh`가 device plugin을 재시작한 직후에는 gVisor 노드의 GPU 열이 잠시 `0`일 수 있고, smoke pod는 그래도 GPU를 받습니다. 다시 조회해도 비어 있거나 `0`이면 device plugin이 그 노드에서 GPU를 등록하지 못한 것입니다.

```bash
kubectl get nodes -l gpusandbox/device-plugin=cdi \
  -o custom-columns='NODE:.metadata.name,ROLE:.metadata.labels.gpusandbox/role,GPU:.status.allocatable.nvidia\.com/gpu'
kubectl -n kube-system get pods -o wide | grep nvdp
helm get values nvdp -n kube-system
kubectl -n kube-system get ds nvdp-nvidia-device-plugin -o yaml | grep -A1 CDI_DISABLE_HOOKS
```

마지막 명령은 `name: CDI_DISABLE_HOOKS`와 그다음 줄의 `value: disable-device-node-modification`을 출력해야 합니다.

## Kata

| 증상 | 원인 | 해결 |
|---|---|---|
| Kata CPU smoke pod가 실패하고 이벤트나 로그에 KVM을 열 수 없다는 류의 오류, 노드에 `/dev/kvm` 없음 | 노드에 nested virtualization이 적용되지 않음(CDK 스택은 launch template `CpuOptions`에 넣지만, 관리형 노드 그룹이 이 옵션을 전달한다는 문서는 없음), 그 리전에서 인스턴스 유형이 nested virtualization을 지원하지 않음 | 아래 명령으로 실행 중인 인스턴스의 `CpuOptions`와 인스턴스 유형의 `SupportedFeatures`(`nested-virtualization`) 확인 |
| `scripts/kata/cpu_nodes.sh`가 `kata runtime classes missing`으로 멈춤 | kata-deploy DaemonSet이 Kata 노드에서 실행되지 않음(nodeSelector `gpusandbox/role=sandbox-kata`, taint toleration) 또는 설치 실패 | kata-deploy pod 상태와 로그, `kubectl get runtimeclass` |
| 나중에 추가한 Kata 노드에 런타임이 설치되지 않음 | kata-deploy chart의 기본 `deploymentMode: job`은 설치 시점의 노드만 처리 | 이 저장소 값처럼 `deploymentMode: daemonset` |
| 노드 재부팅 뒤 Kata pod가 시작되지 않음(추정) | nodeadm이 부팅할 때마다 `/etc/containerd/config.toml`을 다시 써서 kata-deploy가 추가한 handler가 사라짐 | NodeConfig의 `imports = ["/etc/containerd/conf.d/*.toml"]` 유지(`infra/eks/userdata.py`에 포함, 효과는 미검증) |
| `scripts/kata/gpu_nodes.sh`가 `no passthrough GPUs advertised; see docs/reference/troubleshooting.md`로 멈춤, `nvidia.com/pgpu` 없음 | (1) IOMMU 꺼짐: AMI에 `intel_iommu=on`이 없음 (2) 노드 라벨 `nvidia.com/gpu.workload.config=vm-passthrough` 없음 (3) 호스트가 NVIDIA 드라이버를 로드함(NVIDIA AMI 사용) (4) GPU Operator operand나 NFD에 그 taint의 toleration이 없어 실행되지 않음 (5) `ccManager.defaultMode`가 `on`이면 T4에서 cc-manager가 종료됨(pgpu 광고에 주는 영향은 추정) | 아래 명령으로 `/proc/cmdline`, IOMMU group 수, `lsmod`, `lspci -nnk`, 노드 라벨, `gpu-operator` pod 확인. `KATA_IOMMU_AMI_ID`가 `build-iommu-ami.sh`가 만든 AMI인지 확인 |
| Kata GPU pod가 Pending, 이벤트에 node affinity나 selector 불일치 | RuntimeClass `kata-qemu-nvidia-gpu`의 `scheduling.nodeSelector`(`nvidia.com/cc.ready.state=false`)가 pod에 합쳐짐. 노드에 이 라벨이 없음(cc-manager가 설정하지 않았거나 `ccManager.defaultMode`가 `on`) | 노드 라벨 확인. GPU Operator 값 `ccManager.defaultMode: "off"` 확인 후 `kata/gpu_nodes.sh` 재실행 |
| Kata GPU pod가 Pending, `Insufficient memory` 또는 `Insufficient nvidia.com/pgpu` | RuntimeClass overhead(10240Mi, CPU 1)가 pod 요청에 추가됨: pod당 16Gi + 10Gi | `scripts/06_deploy_sandboxes.sh kata-qemu v1 2`처럼 replica를 줄이거나 `kubectl describe node <node>`의 Allocated resources 확인. 실험용 kata-clh 풀과 같은 노드를 함께 쓴다는 점도 계산에 포함하기 |
| `kata-clh` 풀의 pod가 만들어지지 않고 ReplicaSet 이벤트에 RuntimeClass `kata-clh-nvidia-gpu`가 없다는 오류 | 실험용 RuntimeClass는 `ENABLE_EXPERIMENTAL_CLH_GPU=1`로 `kata/gpu_nodes.sh`를 실행해야 생김 | `kubectl -n sandbox describe rs -l gpusandbox/runtime=kata-clh`로 확인. 쓰려면 `ENABLE_EXPERIMENTAL_CLH_GPU=1 scripts/kata/gpu_nodes.sh`, 이어서 `infra/kata/experimental-clh-gpu/check-clh-gpu.sh`(values 파일의 artifact 경로는 kata-deploy 4.3.1 기준으로 채워져 있음). 업스트림이 지원하지 않는 경로이고, 2026-11-18에는 이 경로를 채운 뒤에도 VM이 시작되지 않음(`create container timeout`) |
| Kata GPU pod가 `ContainerCreating`에 머물고 이벤트에 `failed to create shim task: create container timeout`. 노드 로그에 QEMU 오류 `vfio 0000:e7:00.0: failed to setup container for group 87: No available IOMMU models`(PCI 주소와 group 번호는 노드마다 다름) | AL2023 커널은 VFIO type1 IOMMU backend를 모듈(`CONFIG_VFIO_IOMMU_TYPE1=m`)로 빌드하고, 아무것도 이 모듈을 로드하지 않음. `lsmod`에 `vfio`, `vfio_pci`, `vfio_pci_core`만 있음. IOMMU(group 257개), T4 8개의 vfio-pci 바인딩, `nvidia.com/pgpu=8`은 정상이라 pgpu 확인으로는 드러나지 않음(2026-11-18 실측) | (1) AMI 다시 빌드: 지금의 `infra/kata/build-iommu-ami.sh`는 `/etc/modules-load.d/vfio-iommu-type1.conf`(`vfio_iommu_type1`)를 AMI에 넣음. 새 `KATA_IOMMU_AMI_ID`로 config.env를 바꾸고 `02_create_cluster.sh` 재실행 (2) 이전 AMI의 노드에서 바로 고치기: `kubectl debug node/<node>` 셸에서 `chroot /host` 뒤 `modprobe vfio_iommu_type1`(재부팅하면 다시 필요). 자세한 절차는 [03 Kata 샌드박스](../handson/03_kata.md)의 2단계 |
| Kata GPU pod 생성이 시간 초과로 실패하고, 노드 로그에 위 `No available IOMMU models`가 없음(추정) | VFIO가 VM을 시작하기 전에 게스트 메모리 전체를 고정하느라 시간이 걸림 | kubelet `runtimeRequestTimeout: 20m`(`infra/eks/userdata.py`의 Kata GPU NodeConfig에 포함) 유지, 메모리 limits를 필요 이상으로 키우지 않기 |
| `g4dn.metal` 노드가 재부팅 뒤 다시 시작되지 않음(제3자 보고) | metal 인스턴스 warm reboot 문제 보고가 있음 | user data에서 재부팅하지 않도록 커널 인자를 AMI에 포함(`build-iommu-ami.sh`). 다시 시작되지 않으면 인스턴스 교체 |

아래 명령은 CPU 노드의 nested virtualization 설정, Kata 런타임 구성 요소, GPU 노드의 라벨과 pgpu 광고를 차례로 확인합니다. `CpuOptions`에 `"NestedVirtualization": "enabled"`가, pgpu 줄에 `8`이 나오면 정상입니다.

```bash
# CPU node: nested virtualization on the running instance and support for the instance type
aws ec2 describe-instances --region "$AWS_REGION" \
  --filters "Name=tag:eks:cluster-name,Values=$CLUSTER_NAME" "Name=tag:eks:nodegroup-name,Values=sandbox-kata-cpu" \
            "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].CpuOptions'
aws ec2 describe-instance-types --instance-types "$KATA_CPU_INSTANCE_TYPE" --region "$AWS_REGION" \
  --query 'InstanceTypes[0].ProcessorInfo.SupportedFeatures'
# Kata runtime pieces
kubectl -n kube-system get pods -o wide | grep kata-deploy
kubectl get runtimeclass
# GPU node: labels the GPU Operator and the RuntimeClass depend on
node="$(kubectl get nodes -l gpusandbox/kata-gpu=true -o jsonpath='{.items[0].metadata.name}')"
kubectl get node "$node" -L nvidia.com/gpu.workload.config,nvidia.com/cc.ready.state
kubectl get node "$node" -o jsonpath='{.status.allocatable.nvidia\.com/pgpu}{"\n"}'
kubectl -n gpu-operator get pods -o wide
kubectl get runtimeclass kata-qemu-nvidia-gpu -o yaml
```

Kata GPU 노드의 디버그 셸에서는 `chroot` 하기 전에 PCI 바인딩을 먼저 확인합니다.

```bash
dnf install -y -q pciutils && lspci -nnk -d 10de:   # every T4 should show "Kernel driver in use: vfio-pci"
chroot /host
cat /proc/cmdline                                    # must contain intel_iommu=on iommu=pt
ls /sys/kernel/iommu_groups | wc -l                  # 0 means the IOMMU is off
lsmod | grep -E 'vfio|nvidia'                        # vfio_pci and vfio_iommu_type1 loaded, nvidia not loaded
```

## 샌드박스 풀과 readiness

| 증상 | 원인 | 해결 |
|---|---|---|
| `06_deploy_sandboxes.sh`의 rollout이 `exceeded its progress deadline`으로 실패(진행 없이 30분, Deployment `progressDeadlineSeconds` 1800초), pod는 Running인데 `0/1` | readiness 실패. `/readyz`는 GPU probe 성공, egress 차단 확인, draining 아님이 모두 참이어야 200 | `kubectl -n sandbox logs <pod>`의 `device probe ok=` 줄과 `egress is open, refusing work:` 줄로 원인을 구분한 뒤 해당하는 아래 행을 참고 |
| 로그에 `egress is open, refusing work: 169.254.169.254:80 (connected)` | pod가 IMDS에 접근할 수 있음: NetworkPolicy가 적용되지 않음 | 아래 명령으로 NetworkPolicy가 실제로 적용되는지 확인. 노드 그룹 launch template의 IMDS 설정(IMDSv2 필수, hop limit 1)도 확인 |
| 로그에 `<노드 IP>:10250 (refused: reachable)` 또는 `(connected)` | VPC CNI policy agent는 pod와 자기 노드 IP 사이 트래픽을 항상 허용함. node guard(iptables)가 없거나 아직 적용되지 않음 | 노드에서 `iptables -w -S GPUSANDBOX-GUARD`, `systemctl status gpusandbox-node-guard`. 노드 템플릿에 node guard include가 있는지 확인 |
| 로그에 API 서버 주소(`<IP>:443`)가 열려 있음 | default deny가 아직 적용되지 않음. standard 모드는 새 pod를 정책이 적용될 때까지 허용함 | 서버가 5초마다 다시 점검하므로 잠시 기다림. 계속되면 `kubectl -n sandbox get networkpolicy`와 vpc-cni 설정 확인 |
| 로그에 `device probe ok=False info={'error': ...}` | GPU가 보이지 않음(gVisor, Kata 표 참고), CUDA 초기화 오류, 120초 timeout | 오류 문자열 확인. "샌드박스 안에서 확인"의 두 `python -c` 명령(GPU 확인, 첫 CUDA 연산)으로 재현 |
| 샌드박스 검증(`scripts/ops/verify.sh`)이 2단계에서 `a denial check failed: see docs/reference/troubleshooting.md`로 멈춤 | (1) 출력에서 `REACHABLE`로 표시된 대상(IMDS, Kubernetes API, 노드 kubelet, 인터넷)이 열려 있음 (2) 대상별 결과 줄이 하나도 없음: `kubectl exec` 자체가 실패함. 같은 문구로 끝남 | (1) 대상별로 위 행을 따름. 인터넷이 열려 있으면 default deny NetworkPolicy가 적용되지 않은 것 (2) 바로 위에 출력된 `kubectl exec` 오류와 pod 상태부터 확인 |
| `scripts/ops/verify.sh`가 4단계에서 `NetworkPolicy did not block an outside caller`로 멈춤 | (1) 출력에 `connect from default ns: REACHABLE`이 있음: 외부 pod의 연결이 성공함. NetworkPolicy 적용 기능이 꺼져 있거나 허용 정책이 넓음 (2) 접속 결과 줄이 없음: 점검 pod(`kubectl run`) 자체가 실패함. 같은 문구로 끝남 | (1) vpc-cni add-on의 `enableNetworkPolicy`와 `kubectl -n sandbox get networkpolicy` 확인 (2) 점검 pod의 생성, 이미지 다운로드(`public.ecr.aws`), 실행 오류부터 확인 |
| 결과가 `sandbox_error`이고 오류가 `no free sandbox in sandbox-<runtime>-<version>.sandbox.svc.cluster.local:8000` | Ready pod가 없음(headless Service DNS가 비어 있음), 또는 600초 동안 모든 pod가 평가 중 | 아래 EndpointSlice 명령으로 Ready 주소 확인, replica 늘리기 |
| v2로 전환한 뒤 pod가 하나씩 NotReady가 되다가 `no free sandbox` 오류가 남 | v2의 `SANDBOX_MAX_EVALS=200`: pod가 200번 평가한 뒤 draining. 지우는 주체는 Production gateway(`GATEWAY_RECYCLE_PODS=1`)뿐이라 direct 모드에서는 NotReady로 남음 | `kubectl -n sandbox delete pod <pod>`로 지우면 Deployment가 새로 만듦. 핸즈온에서는 버전 파일의 값을 `0`으로 두거나 gateway를 사용 |
| 평가 직후 pod가 재시작되고 verdict에 `gpu_fault` 플래그 | 레퍼런스 경로에서 CUDA 오류가 나면 서버가 GPU 장치 이상으로 판단해 fatal 상태로 전환하고, liveness probe가 재시작함(의도된 동작) | `kubectl -n sandbox logs <pod> --previous`. 같은 노드에서 반복되면 `kubectl cordon <node>` 후 노드 교체 |
| `sandbox_error`의 오류가 `harness exceeded outer timeout` | harness 전체가 `2 x SANDBOX_EVAL_TIMEOUT_S + 30`초(기본 210초)를 넘음. 레퍼런스 실행이나 GPU가 응답하지 않음 | 노드와 GPU 상태 점검, 반복되면 pod 삭제 |

아래 명령은 vpc-cni add-on의 설정(`enableNetworkPolicy`), `sandbox` namespace의 NetworkPolicy 목록, 풀 Service의 EndpointSlice를 보여 줍니다. EndpointSlice에서 Ready인 주소 수가 요청을 받을 수 있는 pod 수입니다.

```bash
aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name vpc-cni --region "$AWS_REGION" \
  --query 'addon.{version: addonVersion, config: configurationValues}'
kubectl -n sandbox get networkpolicy
kubectl -n sandbox get endpointslices -l kubernetes.io/service-name=sandbox-gvisor-v1 -o wide
```

## 401, 403 응답

실제 오류 문자열(`HTTP 401: {"detail": ...}`)은 probe 도구의 `FAIL` 줄에서 확인하세요. trainer 로그의 `reward_batch` 이벤트에는 상태별 개수만 나옵니다. 클라이언트는 4xx를 다른 pod에서 재시도하지 않습니다. 아래 표에서 `06_deploy_sandboxes.sh`를 다시 실행할 때는 문제가 난 풀의 runtime, 버전, 현재 replica 수를 모두 넘기세요. runtime을 빼면 스크립트가 멈추고, 버전과 replica 수를 빼면 v1과 프로필 기본 replica 수로 배포해요.

| 응답과 detail | 원인 | 해결 |
|---|---|---|
| 401 `authentication is not configured on this service` | `SANDBOX_AUTH_*` 네 값 중 빈 값이 있음(pod 로그에 `authentication not configured (missing ...)`) | 아래 명령으로 pod env 확인, 문제가 난 풀의 값으로 `scripts/06_deploy_sandboxes.sh <runtime> <version> <replicas>` 재실행 |
| 401 `missing bearer token` | 호출자가 토큰을 보내지 않음: `SANDBOX_TOKEN_FILE`이 없거나 projected volume이 마운트되지 않음 | Job 템플릿의 `sandbox-token` volume과 `SANDBOX_TOKEN_FILE` env 확인 |
| 401 `token verification keys unavailable` | JWKS 파일을 읽지 못함: ConfigMap `sandbox-auth-jwks`가 없거나 내용이 잘못됨 | `scripts/ops/sync_jwks.sh` |
| 401 `unknown signing key` | 토큰의 `kid`가 JWKS에 없음: API 서버 서명 키가 바뀐 뒤 동기화하지 않음 | `scripts/ops/sync_jwks.sh`(Production은 jwks-sync CronJob) |
| 401 `invalid token: Audience doesn't match` | audience가 다른 토큰: 기본 API 토큰을 보냈거나 gateway용(`gpu-sandbox-gateway`) 토큰을 샌드박스로 보냄 | projected token의 `audience: gpu-sandbox` 확인 |
| 401 `invalid token: Invalid issuer` | `SANDBOX_AUTH_ISSUER`가 클러스터 issuer와 다름 | `aws eks describe-cluster`의 issuer와 비교, 문제가 난 풀의 값으로 `06_deploy_sandboxes.sh <runtime> <version> <replicas>` 재실행 |
| 401 `invalid token: Signature has expired` | 만료된 토큰: 토큰을 한 번만 읽어 오래 캐시한 클라이언트 | `read_token`처럼 요청마다 파일을 다시 읽기 |
| 403 `subject '...' is not allowed` | ServiceAccount가 허용 목록에 없음 | 기본 목록에 해당 ServiceAccount를 더한 값을 `SANDBOX_ALLOWED_SUBJECTS`로 지정(이 값은 기본 목록을 대체함)하고, 문제가 난 풀의 값으로 `06_deploy_sandboxes.sh <runtime> <version> <replicas>` 재실행(Deployment env가 바뀜) |
| 401 `token not authenticated for this audience`(gateway) | gateway 호출 토큰의 audience가 `gpu-sandbox-gateway`가 아니거나 TokenReview 실패 | 호출 pod의 projected token audience 확인 |
| 403 `subject '...' is not allowed`(gateway) | `GATEWAY_ALLOWED_SUBJECTS`에 없음 | gateway Deployment env 수정 |

`invalid token:` 뒤의 문구는 PyJWT 메시지라 버전에 따라 조금 다를 수 있습니다.

아래 명령은 pod가 실제로 받은 인증 설정, 클러스터와 ConfigMap의 issuer와 key ID, 허용된 subject로 만든 유효 기간이 짧은 토큰의 claim을 차례로 보여 줍니다. 두 `kid` 목록이 같고, 토큰의 `iss`와 `aud`가 pod 설정과 같으면 정상입니다.

```bash
# Auth settings the sandbox pod actually received
kubectl -n sandbox get pod "$pod" \
  -o jsonpath='{range .spec.containers[0].env[*]}{.name}={.value}{"\n"}{end}' | grep SANDBOX_AUTH
# Issuer and key IDs: cluster vs ConfigMap
aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" \
  --query cluster.identity.oidc.issuer --output text
kubectl get --raw /openid/v1/jwks \
  | python3 -c "import json,sys; print(sorted(k['kid'] for k in json.load(sys.stdin)['keys']))"
kubectl -n sandbox get configmap sandbox-auth-jwks -o jsonpath='{.data.jwks\.json}' \
  | python3 -c "import json,sys; print(sorted(k['kid'] for k in json.load(sys.stdin)['keys']))"
# Claims of a short-lived token for an allowed subject (do not paste the token anywhere)
kubectl -n rl-trainer create token sandbox-probe --audience gpu-sandbox --duration 10m \
  | python3 -c "import sys,json,base64; p=sys.stdin.read().split('.')[1]; print(json.dumps(json.loads(base64.urlsafe_b64decode(p + '=' * (-len(p) % 4))), indent=2))"
```

## NetworkPolicy

| 증상 | 원인 | 해결 |
|---|---|---|
| probe Job이나 trainer 요청이 연결 timeout(`ConnectTimeout`)으로 실패하고 probe에 FAIL | 호출 pod에 `gpusandbox/client: "true"` 라벨이 없음, 또는 `rl-trainer` 밖의 namespace에서 호출 | `kubectl -n rl-trainer get pods --show-labels`. 직접 만든 Job이면 pod template에 라벨 추가 |
| Production에서 gateway를 배포한 뒤 `ops/verify.sh`의 probe와 `ops/rollout.sh`의 parity가 실패 | `k8s/production/gateway.yaml.tpl`이 같은 이름의 `allow-clients-to-sandbox-api`를 gateway만 허용하도록 덮어씀 | 아래처럼 `rl-trainer`에서 `app: sandbox-probe` 라벨이 붙은 pod만 허용하는 정책을 추가(저장소에 없는 예시). probe, parity, bench, simulate Job이 모두 이 라벨을 씀. 검증할 때만 적용하고 끝나면 지우는 방법도 있음 |
| 다른 namespace에서 gateway로 연결되지 않음 | `allow-trainers-to-gateway`는 `rl-trainer` namespace의 pod만 TCP 8080에 허용 | 호출 위치를 `rl-trainer`로 옮기거나 정책 추가 |

```yaml
# Example, not in the repository: lets the operator probe Jobs reach sandbox pods
# next to the production policy that admits the gateway only (policies are additive).
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-probe-to-sandbox-api
  namespace: sandbox
spec:
  podSelector:
    matchLabels: {app.kubernetes.io/name: gpu-sandbox}
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels: {kubernetes.io/metadata.name: rl-trainer}
          podSelector:
            matchLabels: {app: sandbox-probe}
      ports: [{protocol: TCP, port: 8000}]
```

## 학습

| 증상 | 원인 | 해결 |
|---|---|---|
| trainer 로그에 CUDA out of memory(A10G 24 GB) | vLLM colocate가 GPU를 학습과 나눠 씀: `--vllm-gpu-memory-utilization` 0.35에 학습 메모리(1.5B, LoRA, 활성값)가 추가로 필요함 | 하나씩 줄여 보기: `--per-device-batch 2 --grad-accum 8`(곱 16 유지), `--max-completion-length 512`, `--vllm-gpu-memory-utilization 0.3`, `--vllm-max-model-length 1536`. 플래그는 Job 템플릿 `args`에 추가 |
| vLLM이 KV cache를 할당하지 못한다는 류의 오류로 시작 실패(문구는 vLLM 버전마다 다름, 추정) | `--vllm-gpu-memory-utilization`이 낮아 `--vllm-max-model-length` 길이를 담을 KV cache가 없음 | 값을 조금 올리거나 `--vllm-max-model-length`를 줄임 |
| 시작할 때 generation batch가 `num_generations`로 나누어떨어지지 않는다는 류의 오류(TRL 1.18.0 기준) | `--per-device-batch` x `--grad-accum`이 `--num-generations`(8)의 배수가 아님 | 곱을 8의 배수로 맞춤 |
| 학습은 진행되는데 `reward_batch`의 `status`에 `sandbox_error`가 많음 | 인증, NetworkPolicy, 풀 소진(위 표) | probe 도구로 실제 오류 문자열 확인: `scripts/ops/verify.sh <runtime> <version>` |
| 학습이 끝난 뒤 체크포인트, `final` 어댑터, `sandbox_metrics.jsonl`이 남지 않음 | Job 템플릿의 `/outputs`가 emptyDir: 컨테이너가 종료되면 파일을 가져올 방법이 없고 pod와 함께 삭제됨 | `reward_batch` 이벤트는 `kubectl logs`로 확인할 수 있음. 결과를 보존하려면 `/outputs`에 PVC(예: FSx for Lustre)를 마운트([06 veRL로 확장](../production/06_scaling_with_verl.md) 참고) |

```yaml
# k8s/trainer/job-grpo.yaml.tpl: extra flags go into args
          args:
            - --output-dir=/outputs/grpo
            - --max-steps=${MAX_STEPS}
            - --model=${MODEL_ID}
            - --metrics-file=/outputs/grpo/sandbox_metrics.jsonl
            # Example: lower memory use on a 24 GB A10G
            - --per-device-batch=2
            - --grad-accum=8
            - --max-completion-length=512
```

## 버전 전환 (routing)

| 증상 | 원인 | 해결 |
|---|---|---|
| 버전 교체(`scripts/ops/rollout.sh`)의 4단계 뒤 trainer에 `sandbox_version_switch`가 나오지 않음 | (0) 정상 동작: 이 이벤트는 샌드박스 요청의 응답 풀이 직전 요청과 다를 때만 나옴. trainer가 시작한 뒤 첫 응답이거나, 변경 뒤 batch가 한 풀의 캐시만 써서 요청이 없으면 나오지 않음 (1) ConfigMap을 `subPath`로 마운트해 갱신이 전달되지 않음 (2) kubelet 동기화 지연(스크립트 안내 기준 약 1분) (3) 다른 namespace의 ConfigMap을 바꿈 (4) gateway 모드에서는 gateway에 마운트된 routing 표가 기준인데 `sandbox-gateway`의 ConfigMap이 갱신되지 않음. TRL trainer는 gateway가 응답한 버전이 이전 batch와 다를 때 이 이벤트를 남김 (5) JSON 오류로 마지막 정상 표를 유지 | 먼저 아래 명령의 마지막 줄로 변경 전후에 `reward_batch`(샌드박스 요청이 있었던 batch)가 있는지 확인. 요청이 있었는데도 전환이 보이지 않으면 마운트 방식과 pod 안 파일 확인(direct 모드는 trainer, gateway 모드는 gateway). 이 저장소 템플릿은 디렉터리로 마운트하므로 템플릿을 고쳤다면 되돌림 |
| trainer가 `RoutingError: no pool for runtime=... version=...`로 멈춤 | active 버전이 그 runtime의 `pools`에 없음. 예: `--runtime`에 표에 없는 이름을 줌, 또는 새 버전을 `routing.json.tpl`에 넣지 않음. 기본 표에는 7개 런타임의 `v1`, `v2`가 모두 있음. 주소는 있는데 Ready pod가 없으면 이 오류가 아니라 `no free sandbox`가 나옴 | `--runtime`의 오타라면 trainer 인자를 고침. 배포한 풀의 주소가 표에 없다면 `routing.json.tpl`의 `pools`에 추가하고, 현재 active 런타임과 버전으로 렌더링한 표를 ConfigMap에 적용(`python3 scripts/render.py k8s/base/routing.json.tpl ACTIVE_RUNTIME=<runtime> ACTIVE_VERSION=<version> > /tmp/routing.json` 뒤 `kubectl -n rl-trainer create configmap sandbox-routing --from-file=routing.json=/tmp/routing.json --dry-run=client -o yaml > /tmp/cm.yaml`, `kubectl apply -f /tmp/cm.yaml`. gateway 모드면 `-n sandbox-gateway`로도 같은 작업). 로컬에서 렌더링만 하면 클러스터의 ConfigMap은 바뀌지 않음. 이전 버전으로 되돌리려면 `scripts/ops/rollout.sh <runtime> <to> <from>` |
| trainer pod가 `ContainerCreating`에 머물고 이벤트에 ConfigMap `sandbox-routing`이 없다는 마운트 오류 | `rl-trainer`에 routing ConfigMap이 없음 | 초기 설치라면 `scripts/05_setup_namespaces_auth.sh`. 운영 중이면 `05`가 routing 표를 기본 active 값으로 쓰고 NetworkPolicy도 다시 적용하므로, ConfigMap만 복구: `python3 scripts/render.py k8s/base/routing.json.tpl ACTIVE_RUNTIME=<runtime> ACTIVE_VERSION=<version> > /tmp/routing.json` 뒤 `kubectl -n rl-trainer create configmap sandbox-routing --from-file=routing.json=/tmp/routing.json` |
| veRL(gateway)에서 전환 뒤에도 일부 요청이 이전 버전으로 채점됨 | 정상 동작: 이미 시작된 group은 첫 요청부터 TTL(900초) 동안 그 버전에 고정 | `GATEWAY_GROUP_PIN_TTL_S` 확인. 이전 풀은 고정이 끝날 때까지 지우지 않기 |
| parity가 `speedup moved <old> -> <new>`로 실패 | 두 버전의 speedup 비율이 허용 범위(`--speedup-tolerance`, 기본 0.35)를 넘음 | 의도한 변화면 `scripts/ops/rollout.sh`의 parity 호출에 `--speedup-tolerance`를 추가해 조정, 아니면 원인 조사. `ops/rollout.sh`는 parity가 실패하면 전환하지 않음 |

아래 명령은 direct 모드(trainer가 표를 직접 읽음)에서 확인할 실행의 `RUN_ID`(Job 이름 `grpo-<RUN_ID>`)를 받아 routing ConfigMap 내용, trainer pod의 마운트 방식, pod 안의 routing 파일, 최근 전환과 batch 이벤트를 차례로 보여 줍니다. ConfigMap과 pod 안 파일의 `active`가 같아야 합니다.

```bash
kubectl -n rl-trainer get configmap sandbox-routing -o jsonpath='{.data.routing\.json}' | python3 -m json.tool
RUN_ID="<RUN_ID>"   # the run to check (finished Jobs stay for a day)
trainer="$(kubectl -n rl-trainer get pods -l job-name=grpo-${RUN_ID} --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}')"
kubectl -n rl-trainer get pod "$trainer" -o jsonpath='{.spec.containers[0].volumeMounts}{"\n"}'   # no subPath
kubectl -n rl-trainer exec "$trainer" --\
  cat /etc/gpusandbox/routing/routing.json
kubectl -n rl-trainer logs "$trainer" | grep -E '"event": "(sandbox_version_switch|reward_batch)"' | tail -5
```

gateway 모드에서는 gateway가 읽는 표를 같은 방식으로 비교합니다.

```bash
kubectl -n sandbox-gateway get configmap sandbox-routing -o jsonpath='{.data.routing\.json}' | python3 -m json.tool
kubectl -n sandbox-gateway exec deploy/gateway -- cat /etc/gpusandbox/routing/routing.json
```

## Agent Sandbox와 multi-turn 에피소드

multi-turn 에피소드 실행(`scripts/extensions/agent_sandbox.sh episodes <runtime>`)은 Job을 제출하기 전에 CRD, ServiceAccount, warm pool 상태를 확인하고, 확인에 실패하면 아래 메시지를 출력하고 멈춥니다. 이 경로는 로컬 테스트로만 확인했고 클러스터에서는 실행하지 않았습니다. 실행 방법은 [11 multi-turn 에피소드 실습](../handson/11_multi_turn.md)에 있습니다.

| 증상 | 원인 | 해결 |
|---|---|---|
| `agent-sandbox CRDs not found: run scripts/extensions/agent_sandbox.sh install` | Agent Sandbox controller와 CRD(`sandboxclaims`, `sandboxwarmpools`)가 클러스터에 없음 | `scripts/extensions/agent_sandbox.sh install` 실행 후 `episodes`를 다시 실행 |
| `ServiceAccount rl-trainer/sandbox-episode not found: run scripts/extensions/agent_sandbox.sh install` 또는 `system:serviceaccount:rl-trainer:sandbox-episode may not create SandboxClaims: run scripts/extensions/agent_sandbox.sh install` | multi-turn Job이 쓰는 ServiceAccount `sandbox-episode`가 없거나, 이 계정에 claim 권한을 주는 RoleBinding `sandbox-claims`에 이 계정이 없음. 이 계정이 저장소에 추가되기 전에 `05_setup_namespaces_auth.sh`나 `install`을 실행한 경우에 생김 | `install`을 다시 실행. `k8s/base/trainer-rbac.yaml`과 `trainer-claims-rbac.yaml`을 다시 적용하며, 여러 번 실행해도 안전함 |
| `warm pool kernel-eval-<runtime> not found: run scripts/extensions/agent_sandbox.sh pool <runtime>` | 그 런타임의 SandboxTemplate과 SandboxWarmPool을 만들지 않음 | `scripts/extensions/agent_sandbox.sh pool <runtime> [n]` 실행 |
| `warm pool kernel-eval-<runtime> has no Ready sandbox (kubectl -n sandbox get sandboxwarmpool kernel-eval-<runtime>)` | warm pool의 `status.readyReplicas`가 0: 샌드박스 pod가 아직 시작 중이거나 readiness(GPU probe, egress 차단 확인)를 통과하지 못함 | 메시지의 명령과 `kubectl -n sandbox get pods -l gpusandbox/managed-by=agent-sandbox`로 상태 확인. pod가 `0/1`에 머물면 위 "샌드박스 풀과 readiness" 표를 따름 |
| `sandboxes started without system:serviceaccount:rl-trainer:sandbox-episode in their allowlist: <이름 목록>. Run scripts/extensions/agent_sandbox.sh pool <runtime>, then delete them ...` | warm 샌드박스는 시작할 때 받은 env를 계속 씀(`updateStrategy` `OnReplenish`). `sandbox-episode`가 allowlist에 들어가기 전에 시작한 샌드박스는 에피소드 요청에 403(`subject '...' is not allowed`)으로 응답함. 셸이나 config.env에서 `SANDBOX_ALLOWED_SUBJECTS`를 `sandbox-episode` 없이 지정한 채 `pool`을 실행해도 같음 | `SANDBOX_ALLOWED_SUBJECTS`를 직접 지정했다면 기존 항목을 유지한 채 `system:serviceaccount:rl-trainer:sandbox-episode`를 추가. 그다음 기존 warm replica 수와 버전을 그대로 지정해 `pool`을 다시 실행하고 템플릿을 갱신(`VERSION_FILE=<버전> scripts/extensions/agent_sandbox.sh pool <runtime> <replica 수>`. 인자를 생략하면 replica 1, 버전 파일 `v1`로 다시 써짐). 그 뒤 메시지에 나온 pod가 속한 Sandbox를 확인. `kubectl -n sandbox get sandboxclaims -o yaml`의 `status.sandbox.name`에 있는 Sandbox는 에피소드가 사용 중이므로 에피소드가 끝난 뒤 정리하고, 대기 중인 Sandbox만 `kubectl -n sandbox delete sandboxes.agents.x-k8s.io <name>`으로 삭제. pool이 새 env로 대체 샌드박스를 시작함 |

## HyperPod

| 증상 | 원인 | 해결 |
|---|---|---|
| `scripts/hyperpod/check_gvisor.sh`가 `NOT supported by gVisor ...: keep sandboxes on EC2 (mode B1)` 출력 | trainer 노드라면 예상 결과: 기본 HyperPod EKS AMI의 드라이버 595.91.07이 gVisor release-20261109.0의 nvproxy 지원 목록에 없음. sandbox 노드에서 나오면 custom AMI가 적용되지 않은 것 | trainer 노드는 그대로 둠. sandbox 노드라면 `HYPERPOD_B2_AMI_ID`와 인스턴스 그룹의 `ImageId` 확인 |
| B2 `create-cluster`가 `Failed`, lifecycle 로그에 `runsc missing` 또는 `NVIDIA driver ... is not supported` | sandbox 그룹이 custom AMI로 시작되지 않았거나, AMI를 다른 `B2_NVIDIA_DRIVER_VERSION`이나 `GVISOR_RELEASE`로 빌드함 | `scripts/hyperpod/build_b2_ami.sh`를 다시 실행해 새 `HYPERPOD_B2_AMI_ID`로 클러스터를 만듦 |
| B2 lifecycle 로그에 `unsupported or missing config version` 또는 `containerd rejected the edited` | containerd 설정 파일 위치나 schema가 예상과 다름 | 노드에서 `ps -o args= -C containerd`로 `--config` 경로를 확인하고, `on_create_sandbox.sh`의 `HYPERPOD_CONTAINERD_CONFIG`를 그 값으로 고친 뒤 lifecycle 스크립트를 다시 업로드 |
| `scripts/hyperpod/build_b2_ami.sh`가 `customization failed` | 드라이버 교체나 gVisor 확인이 builder에서 실패 | 출력된 `get-console-output` 명령으로 `GPUSANDBOX-B2-BUILD: FAILED ...` 줄과 그 앞 로그를 보고, 정지된 builder를 `terminate-instances`로 종료 |
| CreateCluster 뒤 상태가 `Failed` | 스크립트가 출력하는 `FailureMessage` 참고. 사전 요구사항(EKS 인증 모드 API 또는 API_AND_CONFIG_MAP, VPC CNI 1.18.3 이상, private subnet, 지원 Kubernetes 버전), lifecycle 스크립트 S3 읽기 권한 | [HyperPod EKS 사전 요구사항](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)과 비교. 버킷 이름의 `sagemaker-` 접두사 유지 |
| HyperPodPyTorchJob pod가 Pending | 노드 라벨 `sagemaker.amazonaws.com/node-health-status`가 `Schedulable`이 아님(deep health check 중 등), instance type 불일치 | `kubectl get nodes -L sagemaker.amazonaws.com/node-health-status,node.kubernetes.io/instance-type` |
| pod가 `hyperpodrun`을 찾지 못하고 실패 | trainer 이미지를 `HYPERPOD=1` 없이 빌드함 | `HYPERPOD=1 scripts/03_build_push_images.sh`. ECR 태그가 IMMUTABLE이라 새 `IMAGE_TAG`가 필요 |
| HyperPod 노드에 pod가 더 배치되지 않음(`Too many pods`) | 인스턴스당 ENI 1개: ml.g6.xlarge와 ml.g6.2xlarge는 pod 최대 14개(기본값인 ml.g5의 한도는 확인하지 않음) | 그 노드에서 실행되는 DaemonSet 수 확인, 불필요한 DaemonSet을 HyperPod 노드에서 제외 |
| job 재시작 뒤 처음부터 다시 학습 | `/outputs`가 emptyDir라 새 노드의 pod에는 체크포인트가 없음 | 공유 스토리지(FSx for Lustre PVC)를 `/outputs`에 마운트 |

## 정리와 비용

| 증상 | 원인 | 해결 |
|---|---|---|
| `08_cleanup.sh`를 실행했는데 과금이 남음 | HyperPod를 먼저 지우지 않음, AMI와 스냅샷 확인 단계에서 건너뜀, `--images` 없이 실행해 ECR이 남음, 다른 리전에서 실행 | `scripts/hyperpod/delete.sh` 먼저, `08_cleanup.sh` 마지막에 출력되는 남은 인스턴스 표 확인. ECR이 남았다면 `cdk/destroy.sh`가 출력한 ECR 삭제 명령(`for r in sandbox trainer control; do aws ecr delete-repository ... --force; done`)의 대상 리포지토리를 확인한 뒤 실행. `08_cleanup.sh --images`를 다시 실행하면 매번 `cdk/destroy.sh`부터 실행하고, 이미 지운 AMI의 ID가 `config.env`에 남아 있으면 ECR 단계 전에 멈출 수 있음 |
| `g4dn.metal`을 잠시 쓰지 않는데 비용이 계속 발생함 | 노드가 있으면 계속 과금(약 7.8 USD/시간) | `aws eks update-nodegroup-config --cluster-name "$CLUSTER_NAME" --nodegroup-name sandbox-kata-gpu --scaling-config minSize=0,maxSize=1,desiredSize=0` |
| `cdk destroy`가 오래 걸리거나 `DELETE_FAILED`로 실패(추정) | 스택 밖에서 만든 리소스가 VPC를 계속 사용 중임(HyperPod ENI, Karpenter가 시작한 노드 등) | HyperPod를 먼저 삭제(`scripts/hyperpod/delete.sh`)하고 `scripts/08_cleanup.sh`를 재시도. CloudFormation 콘솔의 스택 이벤트에서 실패한 리소스 확인 |

> ❓ **오해: pod가 Running이면 샌드박스가 준비된 것이다.**
> 이 저장소에서 Running은 컨테이너가 시작됐다는 뜻일 뿐입니다. readiness는 GPU probe와 egress 차단 확인까지 통과해야 하고, Ready가 아닌 pod는 headless Service DNS에 나타나지 않아 요청을 받지 않아요. "Running인데 요청이 가지 않는다"는 증상은 대부분 readiness 문제이니, `kubectl -n sandbox get pods`의 READY 열(`0/1`)과 서버 로그를 먼저 보세요.

> ❓ **오해: 학습이 계속 진행되면 샌드박스도 정상이다.**
> 인프라 오류(`sandbox_error`)는 학습을 멈추지 않습니다. TRL은 그 샘플의 세 reward를 모두 `None`으로 반환해 group baseline에서 빼고, veRL은 format 점수 0.1과 `sandbox_error: 1`을 기록해요. 오류가 계속돼도 학습은 진행됩니다. TRL에서는 점수를 받는 샘플이 줄어드니, `reward_batch` 이벤트가 기록된 batch에서 `status.sandbox_error / n`을 주기적으로 확인하세요. veRL에서는 오류 샘플도 0.1점을 받으므로 `reward_extra_info`의 `sandbox_error`를 집계합니다.

??? note "참고 자료"
    | 주제 | 링크 |
    |---|---|
    | Amazon VPC CNI network policy 설정 | [Amazon VPC CNI network policy 설정](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
    | Amazon EC2 nested virtualization | [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) |
    | gVisor GPU 지원 | [gVisor GPU 지원](https://gvisor.dev/docs/user_guide/gpu/), [gVisor 설치](https://gvisor.dev/docs/user_guide/install/), [google/gvisor](https://github.com/google/gvisor) |
    | Kata Containers 4.3.1 NVIDIA GPU passthrough | [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md), [Kata issue #11687](https://github.com/kata-containers/kata-containers/issues/11687) |
    | scripts/ops/verify.sh | [scripts/ops/verify.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/verify.sh), [scripts/lib_jobs.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/lib_jobs.sh), [scripts/kata/gpu_nodes.sh](https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/kata/gpu_nodes.sh) |

    전체 출처: [참고 자료 모음의 이 페이지 절](references.md#ref-reference-troubleshooting)
