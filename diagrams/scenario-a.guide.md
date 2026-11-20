**한국어** | [English](scenario-a.guide.en.md)

# 시나리오 A: 하나의 EKS 클러스터에서 EC2 trainer와 gVisor GPU 샌드박스

private EKS 클러스터 하나에서 on-policy GRPO post-training을 돌리는 구성입니다. 자기 EC2 GPU 노드에 있는 trainer Job이 모델이 쓴 kernel을 별도 GPU 노드의 gVisor(runsc + nvproxy) 샌드박스 pool로 보내고, 돌아온 verdict를 reward로 바꿔요. 운영자는 SSM 터널로만 클러스터에 닿고, 모델 weight는 NAT gateway를 거쳐 Hugging Face Hub에서 들어옵니다.

![시나리오 A](scenario-a.drawio.png)

## 다이어그램 읽는 법
- **Operator access**: 운영자가 클러스터 API에 닿는 유일한 길입니다. SSM Session Manager와 inbound 규칙이 없는 access instance를 묶었어요.
- **EKS control plane**: private endpoint만 있는 EKS control plane과, Secret을 암호화하는 KMS key입니다.
- **trainer node g5.2xlarge**(EKS node group trainer): GRPO trainer Job 하나만 올라가는 taint된 GPU 노드예요.
- **sandbox-gvisor nodes g5.xlarge x2**(EKS node group sandbox-gvisor): 활성 pool v1과, rollout 때 그 옆에 뜨는 pool v2입니다.
- **Shared services**: 여러 컴포넌트가 함께 쓰는 CloudWatch Logs와 ECR repositories입니다. **Egress**: private subnet의 유일한 출구인 NAT gateway예요.
- **선**: 실선은 동기 호출, 점선은 비동기 또는 보조 관계입니다. 선 위의 글자가 그 홉에서 무엇이 흐르는지이고, 아래 단계마다 같은 글자를 `라벨`로 인용했으니 그림에서 그 화살표를 찾으면 됩니다. 단계 번호는 브리프 관계표의 `#` 순서예요.
- Operator workstation과 Hugging Face Hub는 AWS Cloud 상자 밖에 있습니다. 샌드박스에서 밖으로 나가는 선은 일부러 없어요(아래 설계 결정 참고).

## 단계별 흐름
1. **Operator workstation → SSM Session Manager**: 운영자가 cdk/tunnel.sh를 실행하면 SSM Session Manager가 port forwarding 세션(AWS-StartPortForwardingSessionToRemoteHost)을 엽니다. 워크스테이션의 127.0.0.1:8443이 터널 입구가 되고, scripts/04_install_gpu_stack.sh 이후의 모든 kubectl과 helm 명령이 이 터널을 탑니다. (라벨 `kubectl tunnel`)
2. **SSM Session Manager → Access instance t4g.nano**: 세션은 private subnet의 access instance를 거쳐요. 이 인스턴스는 inbound 규칙이 없고 HTTPS egress만 허용하며 IMDSv2를 강제합니다. (라벨 `port forward`)
3. **Access instance t4g.nano → EKS 1.36 private API**: access instance가 EKS private endpoint의 443 포트로 연결하고, 터널은 실제 API server 이름으로 검증됩니다. public endpoint가 꺼져 있어서 클러스터 API에 닿는 길은 이 홉뿐이고, kubectl은 IAM access entry로 인증해요. (라벨 `HTTPS 443`)
4. **EKS 1.36 private API → GRPO trainer Job**: scripts/07_run_grpo.sh가 ns rl-trainer에 GRPO Job을 적용하면 EKS가 taint된 trainer 노드에 스케줄하고 ConfigMap sandbox-routing을 디렉터리로 마운트합니다. 디렉터리 마운트라서 나중의 patch가 실행 중인 pod에도 닿아요(kubelet sync, 최대 1분 정도). 호출이 아니라 비동기 스케줄링과 설정 전달이라 점선입니다. (라벨 `Job, active pool`)
5. **GRPO trainer Job → NAT gateway**: trainer가 policy 모델 Qwen/Qwen2.5-Coder-1.5B-Instruct를 내려받습니다. 노드가 private subnet에 있으므로 트래픽은 NAT gateway로 나가고, ns rl-trainer에는 egress policy가 없어요. (라벨 `model pull`)
6. **NAT gateway → Hugging Face Hub**: NAT gateway가 요청을 인터넷의 Hugging Face Hub로 내보냅니다. gateway가 한 AZ에 하나뿐이라 모델 다운로드와 이미지 pull의 단일 egress 지점이 된다는 점은 브리프가 질문으로 남겨 두었어요. (라벨 `HTTPS`)
7. **GRPO trainer Job → gvisor pool v1**: reward batch마다 trainer가 routing snapshot 하나를 잡고, headless Service sandbox-gvisor-v1을 CoreDNS로 풀어 ready pod IP를 얻은 뒤 후보 kernel을 8000 포트의 /v1/evaluate로 POST합니다. 요청에는 audience gpu-sandbox인 projected ServiceAccount token이 붙고, pod는 JWKS ConfigMap으로 토큰을 오프라인 검증한 다음 gVisor 아래 자기 A10G에서 harness를 돌려 같은 호출로 verdict(status, speedup)를 돌려줘요. 바쁜 pod는 503을 돌려주고 client가 다른 pod로 재시도합니다. (라벨 `kernel code`)
8. **GRPO trainer Job → gvisor pool v2**: scripts/ops/rollout.sh가 v1 옆에 v2를 배포하고 probe Job으로 검증하고 v1과 parity를 확인한 뒤 routing ConfigMap을 patch합니다. trainer는 다음 batch 경계에서 전환하므로 한 batch에 두 버전이 섞이지 않고, v1은 --finish로 0까지 줄인 채 rollback용으로 남아요. 전환 전에는 트래픽이 없어서 점선입니다. (라벨 `after switch`)
9. **gvisor pool v1 → ECR repositories**: 노드의 container runtime이 node role(AmazonEC2ContainerRegistryPullOnly)로 sandbox 이미지를 pull합니다. pod가 아니라 노드가 당기는 것이고, stack에 VPC endpoint가 없어서 실제 트래픽은 NAT gateway를 지나요. 보조 관계라 점선입니다. (라벨 `image pull`)
10. **Operator workstation → ECR repositories**: 운영자가 sandbox, trainer, control 이미지를 linux/amd64로 빌드해 push합니다. 이 호출은 터널이 아니라 public AWS endpoint로 바로 가고, 저장소 자체도 CDK stack이 아니라 scripts/03_build_push_images.sh가 만들어요. (라벨 `image push`)
11. **EKS 1.36 private API → CloudWatch Logs**: control plane이 api, audit, authenticator, controllerManager, scheduler 로그를 보존 기간 한 달인 log group으로 보냅니다. VPC flow log(REJECT)는 두 번째 log group으로 가지만 그림에는 대표 선 하나만 그렸어요. (라벨 `control plane logs`)
12. **EKS 1.36 private API → KMS secrets key**: EKS가 rotation이 켜진 customer-managed key로 Kubernetes Secret을 envelope encryption합니다. (라벨 `encrypt secrets`)

## 서비스
| 서비스 | 이 시스템에서의 역할 | 비고 |
|---|---|---|
| Operator workstation | 스크립트를 실행하고 터널로 kubectl과 helm을 쓰며 이미지를 빌드해 올립니다 | AWS Cloud 밖 |
| SSM Session Manager | 워크스테이션에서 API endpoint까지 이어 주는 port forwarding 세션 | |
| Access instance t4g.nano | 세션만 받는 경유 호스트, 들어오는 규칙이 없음 | private subnet |
| EKS 1.36 private API | private endpoint만 있는 control plane과 기본 add-on | |
| KMS secrets key | Kubernetes Secret을 암호화하는 고객 관리 키 | rotation 켜짐 |
| GRPO trainer Job | GRPO 학습을 돌리고 verdict를 reward로 바꾸는 Job, GPU 한 장 | ns rl-trainer |
| gvisor pool v1 | 지금 트래픽을 받는 gVisor 샌드박스 pool, GPU 한 장마다 pod 하나 | 기본 차단 NetworkPolicy |
| gvisor pool v2 | blue/green의 다음 버전, 검증과 전환 전에는 트래픽이 없음 | rollout 때 노드를 4대로 늘림 |
| ECR repositories | 세 이미지의 비공개 저장소 | scripts/03_build_push_images.sh가 생성 |
| CloudWatch Logs | control plane 로그와 VPC flow log | 보존 한 달 |
| NAT gateway | private subnet의 유일한 출구 | 한 AZ에 하나 |
| Hugging Face Hub | policy 모델 weight의 외부 출처 | AWS Cloud 밖 |
| VPC | AZ 두 개, NAT만 있는 public subnet과 모든 노드가 있는 private subnet | 그림에 없음 |
| System node group m6i.large x2 | CoreDNS, add-on, 운영자 도구 Job이 도는 노드 | 그림에 없음 |
| IAM roles | cluster, node, access instance 역할과 운영자 access entry | 그림에 없음 |
| Kubernetes ConfigMap sandbox-routing | 활성 runtime과 버전, pool 주소를 담은 설정 | 그림에 없음, 4번 선이 실어 나름 |

## 설계 결정
- hands-on 시나리오에는 gateway가 없습니다. trainer가 headless Service로 pool을 직접 부르고(client-side scheduling), reward batch마다 routing snapshot 하나로 버전을 고정해요. TokenReview와 group별 pin을 하는 gateway는 production 전용입니다(docs/production/00_architecture.md:103).
- control 이미지는 이 시나리오에서 ns rl-trainer의 운영자 tool Job(probe, parity, bench)만 씁니다. 같은 이미지에 production gateway도 들어 있어요.
- ECR 저장소는 CDK stack이 아니라 scripts/03_build_push_images.sh가 만들고, stack은 node role에 ECR pull 권한만 줍니다.
- Kubernetes workload(trainer Job, pool Deployment)는 EKS resource stencil이 없어서 Containers 카테고리의 `container_1`로 그리고 workload 이름을 붙였습니다. `eks` 아이콘은 control plane만 뜻해요.
- node group은 stencil이 없고 그룹마다 EC2 아이콘을 두면 노드 수가 두 배로 보이므로, 아이콘 대신 role group으로 그리고 제목에 node group 이름과 instance type을 적었습니다. 1열 카드에 두 줄로 들어가도록 "node group"이라는 단어는 뺐어요.
- Hugging Face Hub는 `internet`, 운영자는 `client` 아이콘을 씁니다. gVisor(runsc + nvproxy)는 stencil이 없어서 pool 라벨과 그룹 제목(sandbox-gvisor)으로 드러냈어요.
- ConfigMap sandbox-routing과 system node group은 그리지 않았습니다. ConfigMap은 4번 선이 실어 나르고, trainer의 DNS 조회는 7번 설명에 넣었어요.
- CloudWatch Logs에는 eks에서 오는 선 하나, ECR에는 sbx_v1의 pull과 운영자의 push만 대표로 그렸습니다. flow log와 trainer 자신의 이미지 pull은 그리지 않았어요.
- 샌드박스 egress 선은 일부러 없습니다. default-deny NetworkPolicy가 ns sandbox에서 DNS, IMDS, 인터넷, Kubernetes API로 나가는 길을 막고, pod는 IMDS와 API server와 node kubelet에 닿지 않을 때만 Ready가 되며, node guard가 pod에서 노드로 가는 새 연결을 버립니다.
- Architecture review는 건너뛰었습니다. AWS documentation MCP 서버가 없어서 Phase 2 결과는 없고, 대신 CDK stack이 synth마다 cdk-nag AwsSolutions 검사를 돌리며(cdk/app.py:21-22) 수용한 finding과 이유는 cdk/gpusandbox_cdk/stack.py:271-281에 있어요. 브리프 제목은 em dash 금지 때문에 "Architecture review (skipped)"로 적었습니다.
- 브리프가 남긴 질문은 세 가지입니다. trainer 출력과 HF cache가 emptyDir라서 pod가 끝나면 checkpoint가 사라지고, NAT gateway가 한 AZ에 하나뿐이며, alarm과 컨테이너 로그 수집과 CloudWatch 지표가 없어요.
- 그림의 글자는 모두 영어입니다. 이미지 하나를 한국어와 영어 페이지가 함께 씁니다.
- 리뷰 단계 결정: NAT gateway 상자는 원래 두 번째 "Shared services"였는데 **Egress**로 이름을 바꿨습니다. NAT는 trainer의 오른쪽 아래에 있어야 model pull이 꺾임 하나로 닿기 때문에 공유 열에 합칠 수 없어요. `image pull`과 `model pull`이 한 번 교차하는데, sbx_v1의 왼쪽은 kernel code가, 위쪽은 pool v2가 차지하고 ECR은 운영자도 닿아야 해서 아래쪽 경로만 남기 때문에 교차를 받아들였고 draw.io가 교차점에 작은 hop을 그립니다. "Shared services" 제목이 `control plane logs` 선 위에 흰 바탕으로 얹힌 것은 1열 카드의 정상 동작이에요.

## 이 다이어그램에 없는 것
VPC와 subnet, IAM 역할, system node group, routing ConfigMap은 위 서비스 표에만 있습니다. 브리프가 범위 밖으로 둔 것도 그리지 않았어요. GPU passthrough를 쓰는 Kata GPU node group, scenario-c에 따로 그린 c8i CPU node group, 클러스터로 가는 길이 없는 demo site, 단위 테스트만 있는 Agent Sandbox extension, 어떤 hands-on 시나리오도 배포하지 않는 production reference(gateway, Karpenter, veRL), 기본으로 꺼진 public endpoint 옵션이 여기에 해당합니다.
