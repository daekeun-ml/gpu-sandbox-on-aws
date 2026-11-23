**한국어** | [English](scenario-b1.guide.en.md)

# 시나리오 B1: HyperPod trainer와 EKS 노드의 gVisor GPU 샌드박스

학습과 채점 순서는 시나리오 A의 on-policy GRPO 루프와 같습니다. 같은 private EKS 클러스터에 SageMaker HyperPod instance group을 연결해 trainer를 HyperPodPyTorchJob으로 실행합니다. gVisor(runsc + nvproxy) 샌드박스 pool은 EC2 node group에 그대로 둡니다. 그림에서는 학습 노드의 아이콘과 그룹이 바뀌고, HyperPod가 부팅할 때 lifecycle 스크립트를 읽는 S3 버킷이 추가됩니다.

![시나리오 B1](scenario-b1.drawio.png)

## 다이어그램 읽는 법
- **Operator access**: 운영자가 클러스터 API에 접속하는 유일한 경로입니다. SSM Session Manager와 inbound 규칙이 없는 접속 인스턴스를 거쳐요.
- **EKS control plane**: private endpoint만 있는 EKS control plane과 Secret을 암호화하는 KMS key입니다. 이 EKS 클러스터가 HyperPod의 orchestrator 역할을 합니다.
- **HyperPod trainer ml.g5.2xlarge**(HyperPod instance group trainer): GRPO trainer를 실행하는 HyperPod instance group이에요.
- **sandbox-gvisor nodes g5.xlarge x2**(EKS node group sandbox-gvisor): 시나리오 A와 마찬가지로 v1이 채점을 맡고 rollout 때 v2도 함께 실행해요.
- **Shared services**: CloudWatch Logs, S3 lifecycle scripts, ECR repositories입니다. **Egress**: private subnet의 유일한 출구인 NAT gateway예요.
- **선**: 실선은 동기 호출, 점선은 비동기 또는 보조 관계입니다. 화살표 라벨은 각 구간에서 오가는 요청이나 데이터를 나타냅니다. 아래 단계의 `라벨`로 그림에서 해당 화살표를 찾을 수 있습니다. 단계 번호는 브리프 관계표의 `#` 순서와 같아요.
- Operator workstation과 Hugging Face Hub는 AWS Cloud 상자 밖에 있습니다.

## 단계별 흐름
1. **Operator workstation → SSM Session Manager**: 운영자가 cdk/tunnel.sh로 port forwarding 세션(AWS-StartPortForwardingSessionToRemoteHost)을 엽니다. HyperPod dependency chart 설치와 routing 전환을 포함해 모든 kubectl과 helm 단계가 이 터널을 타요. (라벨 `kubectl tunnel`)
2. **SSM Session Manager → Access instance t4g.nano**: 세션은 private subnet의 access instance를 거칩니다. inbound 규칙 없이 HTTPS egress만 허용하는 호스트예요. (라벨 `port forward`)
3. **Access instance t4g.nano → EKS 1.36 private API**: access instance가 private endpoint의 443 포트로 연결합니다. 스크립트가 부르는 AWS API(CloudFormation, ECR push, HyperPod 생성 등)는 이 터널을 타지 않고 public AWS endpoint로 바로 가요. (라벨 `HTTPS 443`)
4. **HyperPod GRPO trainer → S3 lifecycle scripts**: HyperPod 생성 스크립트가 클러스터를 만들 때 이 bucket을 lifecycle 스크립트 위치로 지정하고, HyperPod는 trainer 노드를 만들 때 bucket의 on_create.sh를 실행합니다. 노드의 execution role이 bucket을 읽기 때문에 trainer에서 bucket 쪽으로 그렸고, 노드 생성 때 한 번만 일어나는 일이라 점선이에요. (라벨 `boot script`)
5. **EKS 1.36 private API → HyperPod GRPO trainer**: 학습 실행 스크립트가 HyperPodPyTorchJob을 적용하면 training operator add-on이 instance type과 노드 상태 조건에 맞는 HyperPod 노드에 pod를 띄웁니다. kubelet이 ConfigMap sandbox-routing을 디렉터리로 마운트하므로 나중의 routing 전환도 이 길로 전달돼요. (라벨 `Job, active pool`)
6. **HyperPod GRPO trainer → NAT gateway**: trainer가 policy 모델을 내려받습니다. HyperPod 노드는 stack의 private subnet에 있으므로 트래픽이 NAT gateway로 나가요. 이 경로는 별도 리소스가 아니라 스크립트가 고르는 private subnet에서 추론한 것입니다. (라벨 `model pull`)
7. **NAT gateway → Hugging Face Hub**: NAT gateway가 요청을 인터넷의 Hugging Face Hub로 내보냅니다. (라벨 `HTTPS`)
8. **HyperPod GRPO trainer → gvisor pool v1**: reward 경로는 시나리오 A와 같습니다. reward batch마다 routing snapshot 하나로 채점 버전을 고정하고, headless Service로 pod를 찾아 토큰을 붙인 평가 요청을 보내면, 같은 호출로 verdict가 돌아와요. HyperPod 노드와 EC2 노드는 VPC pod network와 cluster security group을 공유하고 NetworkPolicy는 노드가 아니라 namespace와 pod label로 허용하므로, gateway나 추가 규칙 없이 닿습니다. (라벨 `kernel code`)
9. **HyperPod GRPO trainer → gvisor pool v2**: scripts/ops/rollout.sh가 v1 옆에 v2를 배포하고 검증하고 parity를 확인한 뒤 routing ConfigMap을 patch합니다. trainer는 다음 batch 경계에서 전환하고, 그 전에는 트래픽이 없어서 점선이에요. (라벨 `after switch`)
10. **gvisor pool v1 → ECR repositories**: 노드가 이미지를 pull합니다. EKS 노드는 node role로, HyperPod 노드는 execution role로 당겨요. 보조 관계라 점선입니다. (라벨 `image pull`)
11. **Operator workstation → ECR repositories**: 운영자가 이미지를 빌드해 push합니다. HYPERPOD=1이면 trainer 이미지에 hyperpodrun이 더해져요. (라벨 `image push`)
12. **Operator workstation → S3 lifecycle scripts**: HyperPod 생성 스크립트가 lifecycle 스크립트를 공개 접근이 막힌 비공개 bucket에 올립니다. 4번에서 HyperPod가 읽는 바로 그 파일이에요. (라벨 `script upload`)
13. **EKS 1.36 private API → CloudWatch Logs**: control plane 로그 다섯 종류가 CloudWatch Logs로 갑니다. VPC flow log(REJECT)는 두 번째 log group으로 가지만 대표 선 하나만 그렸어요. (라벨 `control plane logs`)
14. **EKS 1.36 private API → KMS secrets key**: EKS가 customer-managed key로 Kubernetes Secret을 envelope encryption합니다. (라벨 `encrypt secrets`)

## 서비스
| 서비스 | 이 시스템에서의 역할 | 비고 |
|---|---|---|
| Operator workstation | 스크립트를 실행하고 터널로 kubectl과 helm을 쓰며 이미지를 빌드해 올립니다 | AWS Cloud 밖 |
| SSM Session Manager | 워크스테이션에서 API endpoint까지 이어 주는 port forwarding 세션 | |
| Access instance t4g.nano | 세션만 받는 경유 호스트, 들어오는 규칙이 없음 | private subnet |
| EKS 1.36 private API | private endpoint만 있는 control plane, HyperPod training operator도 add-on으로 설치됨 | |
| KMS secrets key | Kubernetes Secret을 암호화하는 고객 관리 키 | rotation 켜짐 |
| HyperPod GRPO trainer | trainer instance group 위의 학습 Job, 노드 자동 복구와 재시도와 멈춤 감지 포함 | `sagemaker` 아이콘 |
| gvisor pool v1 | 지금 트래픽을 받는 gVisor 샌드박스 pool | 기본 차단 NetworkPolicy |
| gvisor pool v2 | 다음 버전 pool, 검증과 전환 전에는 트래픽이 없음 | |
| ECR repositories | 세 이미지의 비공개 저장소 | scripts/03_build_push_images.sh가 생성 |
| CloudWatch Logs | control plane 로그와 VPC flow log | 보존 한 달 |
| NAT gateway | private subnet의 유일한 출구, HyperPod 노드도 이리로 나감 | |
| S3 lifecycle scripts | trainer 노드가 만들어질 때 실행할 스크립트를 담은 비공개 bucket | 공개 접근 차단 |
| Hugging Face Hub | policy 모델 weight의 외부 출처 | AWS Cloud 밖 |
| VPC | AZ 두 개, NAT만 있는 public subnet과 노드가 있는 private subnet | 그림에 없음 |
| System node group m6i.large x2 | CoreDNS, add-on, HyperPod 의존 chart, 운영자 도구 Job이 도는 노드 | 그림에 없음 |
| IAM roles | CDK가 만든 역할들과 HyperPod execution role | 그림에 없음 |
| Kubernetes ConfigMap sandbox-routing | 활성 runtime과 버전, pool 주소를 담은 설정 | 그림에 없음, 5번 선이 실어 나름 |
| HyperPod dependency chart and training operator add-on | HyperPodPyTorchJob을 실제로 실행하는 Helm release와 EKS add-on | 그림에 없음 |

## 설계 결정
- gateway는 없습니다. HyperPod trainer도 시나리오 A처럼 pool을 직접 부르고 reward batch마다 버전을 고정해요(src/gpusandbox/client/routing.py:1-6). gateway는 production 전용입니다(docs/production/00_architecture.md:103).
- HyperPod 노드는 별도 gateway나 추가 규칙 없이 샌드박스 pod에 연결할 수 있습니다. instance group이 CDK VPC의 private subnet 하나와 EKS cluster security group을 쓰고(scripts/hyperpod/create.sh:74-81), pod는 VPC CNI pod network를 공유하며, NetworkPolicy는 namespace와 pod label로 고르기 때문입니다.
- HyperPod에는 전용 stencil이 없어서 trainer를 Amazon SageMaker AI 서비스 아이콘 `sagemaker`로 그리고 HyperPod GRPO trainer라는 라벨을 붙였습니다. 이 아이콘은 HyperPod instance group과 그 위의 HyperPodPyTorchJob을 함께 뜻해요. aws-icons-aliases.md는 SageMaker AI를 `sagemaker_2`로 안내하지만, layout-and-style.md와 scaffold는 `sagemaker_2`를 SageMaker Unified Studio로 다루고 draw.io 26.x 이하에서 빈 칸으로 그려져서 `sagemaker`를 썼습니다.
- id `trainer`는 시나리오 A와 같고 아이콘과 라벨만 다릅니다. 네 그림을 나란히 보면 trainer만 옮겨 갔다는 것이 보여요.
- 시나리오 A와 같은 아이콘으로 표시했습니다. Kubernetes workload는 `container_1`, node group과 instance group은 아이콘 대신 role group, Hugging Face Hub는 `internet`, 운영자는 `client`예요.
- ConfigMap sandbox-routing, system node group, HyperPod dependency chart와 training operator add-on은 그리지 않았습니다. ConfigMap은 5번 선이 실어 나릅니다.
- 4번(boot script)은 HyperPod trainer 노드에서 bucket으로 그렸습니다. 노드의 execution role이 lifecycle bucket 읽기 권한으로 스크립트를 읽고, HyperPod가 노드 생성 때 실행하기 때문이에요.
- 그룹 제목은 node group 또는 instance group 이름과 instance type만 적고 "node group"이라는 단어는 뺐습니다. 1열 카드에 두 줄로 들어가도록 한 것이에요.
- Architecture review는 건너뛰었습니다. AWS documentation MCP 서버가 없었고, CDK stack의 cdk-nag AwsSolutions 검사(cdk/app.py:21-22, 수용 finding은 cdk/gpusandbox_cdk/stack.py:271-281)가 있지만 HyperPod 리소스(bucket, execution role, cluster)는 AWS CLI로 만들어서 cdk-nag 범위 밖이에요. 제목은 em dash 금지 때문에 "Architecture review (skipped)"로 적었습니다.
- 브리프가 남긴 질문은 두 가지입니다. /outputs가 emptyDir라서 HyperPod 노드 교체 때 shared storage(FSx for Lustre PVC)를 마운트하지 않으면 checkpoint가 사라지고, CloudWatch alarm이 없어요. HyperPod log monitoring(JobStart, RewardStalled)은 trainer의 JSON 이벤트를 봅니다.
- 한국어판과 영어판에 같은 그림을 실어 그림 속 라벨은 영어로 표기했습니다.
- 리뷰 단계 결정: NAT gateway 상자를 두 번째 "Shared services" 대신 **Egress**로 이름을 바꿨습니다. trainer의 아래쪽에 boot script와 model pull 두 꺾인 선이 이미 있어서 NAT를 공유 열 옆에 둘 수 없어요. `image pull`과 `model pull`이 한 번 교차하는 것은 시나리오 A와 같은 이유로 받아들였고 교차점에 hop이 그려집니다. 공유 열의 lane마다 아이콘이 하나씩인 것은 운영자의 `script upload`와 `image push`가 각자 비어 있는 lane을 따라 들어와야 하기 때문이에요.

## 이 다이어그램에 없는 것
VPC와 subnet, IAM 역할, system node group, routing ConfigMap, HyperPod add-on은 위 서비스 표에만 있습니다. 브리프가 범위 밖으로 둔 것도 그리지 않았어요. GPU passthrough를 쓰는 Kata GPU node group과 그 위의 Kata pool, scenario-c에 따로 그린 c8i CPU node group, 불가능한 HyperPod 노드 위의 Kata(docs/handson/07_hyperpod.md:495), 클러스터로 가는 길이 없는 demo site, 단위 테스트만 있는 Agent Sandbox extension, 어떤 hands-on 시나리오도 배포하지 않는 production reference, 기본으로 꺼진 public endpoint 옵션이 여기에 해당합니다.
