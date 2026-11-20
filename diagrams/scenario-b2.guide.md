**한국어** | [English](scenario-b2.guide.en.md)

# 시나리오 B2: HyperPod instance group 위의 HyperPod trainer와 gVisor 샌드박스 (실험)

trainer와 GPU 샌드박스가 모두 private EKS 클러스터에 붙은 SageMaker HyperPod instance group에서 돌고, EKS에는 system node group만 남는 구성입니다. 샌드박스 instance group은 custom AMI로 부팅하는데, 이 AMI는 HyperPod public base AMI에서 gVisor nvproxy가 지원하는 NVIDIA 드라이버로 바꿔 한 번 구운 것이에요. 저자들이 AWS에서 직접 돌려 보지 않은 실험 경로입니다(docs/handson/07_hyperpod.md:70).

![시나리오 B2](scenario-b2.drawio.png)

## 다이어그램 읽는 법
- **Operator access**: 운영자가 클러스터 API에 닿는 유일한 길입니다. SSM Session Manager와 access instance를 묶었어요.
- **EKS control plane**: private endpoint만 있는 EKS control plane과 KMS key입니다.
- **HyperPod trainer ml.g5.2xlarge**(HyperPod instance group trainer): HyperPod GRPO trainer가 도는 instance group이에요.
- **HyperPod sandbox ml.g5.xlarge x2**(HyperPod instance group sandbox): custom AMI로 부팅한 노드 두 대에 pool v1과 v2가 하나씩 올라갑니다.
- **AMI build (one time)**: 클러스터를 만들기 전에 한 번 도는 AMI builder와 그 결과물인 custom AMI입니다. B2를 가능하게 하는 것이 이 AMI라서 그렸어요.
- **Shared services**: CloudWatch Logs, S3 lifecycle scripts, ECR repositories입니다. **Egress**: private subnet의 유일한 출구인 NAT gateway예요.
- **선**: 실선은 동기 호출, 점선은 비동기 또는 보조 관계(한 번만 일어나는 빌드와 부팅 단계 포함)입니다. 선 위의 글자가 그 홉에서 무엇이 흐르는지이고, 아래 단계마다 같은 글자를 `라벨`로 인용했어요. 단계 번호는 브리프 관계표의 `#` 순서입니다.
- Operator workstation과 Hugging Face Hub는 AWS Cloud 상자 밖에 있습니다.

## 단계별 흐름
1. **Operator workstation → SSM Session Manager**: 운영자가 cdk/tunnel.sh로 port forwarding 세션을 엽니다. EKS에 system 노드만 있는 동안 scripts/04_install_gpu_stack.sh와 05_setup_namespaces_auth.sh가 이 터널로 실행되고, 05_setup_namespaces_auth.sh가 활성 runtime을 gvisor-hyperpod로 정해요. (라벨 `kubectl tunnel`)
2. **SSM Session Manager → Access instance t4g.nano**: 세션은 inbound 규칙이 없는 private subnet의 access instance를 거칩니다. (라벨 `port forward`)
3. **Access instance t4g.nano → EKS 1.36 private API**: access instance가 private endpoint의 443 포트로 연결합니다. (라벨 `HTTPS 443`)
4. **Operator workstation → AMI builder m6i.large**: scripts/hyperpod/build_b2_ami.sh가 최신 HyperPod EKS 1.36 public base AMI로 m6i.large 한 대를 EKS private subnet에 띄웁니다. 커널 모듈 빌드에는 GPU가 필요 없어서 CPU 인스턴스로 충분해요. (라벨 `launch builder`)
5. **AMI builder m6i.large → Custom AMI, NVIDIA 580.178.04**: user data가 NVIDIA 595.91.07(gVisor release-20261109.0 nvproxy가 모르는 드라이버)을 EC2 gVisor 노드와 같은 580.178.04로 바꾸고 고정 버전 gVisor를 설치한 뒤 전원을 끕니다. 스크립트가 멈춘 인스턴스로 이미지를 만들고 builder를 terminate해요. 브리프의 추정으로는 20분에서 40분이 걸립니다. (라벨 `create image`)
6. **Custom AMI, NVIDIA 580.178.04 → gvisor-hyperpod pool v1**: scripts/hyperpod/create.sh --b2가 instance group sandbox(ml.g5.xlarge 2대, ImageId는 custom AMI, label과 taint gpusandbox/role=sandbox-hyperpod)를 추가합니다. instance group은 아이콘이 아니라 그룹이라 선이 pool v1에서 끝나지만, AMI는 두 sandbox 노드를 모두 부팅하므로 두 pool에 다 해당해요. (라벨 `node image`)
7. **gvisor-hyperpod pool v1 → S3 lifecycle scripts**: 각 sandbox 노드에서 bucket의 on_create_sandbox.sh가 로드된 드라이버가 runsc nvproxy 목록에 있는지 확인하고, containerd에 runsc handler를 등록하고, node guard를 설치합니다. 조건이 맞지 않으면 gVisor 없이 합류시키는 대신 노드를 실패시켜요. 부팅 때 한 번이라 점선입니다. (라벨 `runsc setup`)
8. **HyperPod GRPO trainer → S3 lifecycle scripts**: trainer instance group은 최소한의 on_create.sh만 실행합니다. (라벨 `boot script`)
9. **EKS 1.36 private API → HyperPod GRPO trainer**: scripts/hyperpod/run_grpo.sh가 HyperPodPyTorchJob을 적용하면 training operator가 HyperPod trainer 노드에서 시작하고, kubelet이 ConfigMap sandbox-routing을 마운트합니다. (라벨 `Job, active pool`)
10. **HyperPod GRPO trainer → NAT gateway**: trainer가 policy 모델을 내려받고, 트래픽은 private subnet에서 NAT gateway로 나갑니다. (라벨 `model pull`)
11. **NAT gateway → Hugging Face Hub**: NAT gateway가 요청을 인터넷의 Hugging Face Hub로 내보내요. (라벨 `HTTPS`)
12. **HyperPod GRPO trainer → gvisor-hyperpod pool v1**: reward 경로는 시나리오 A, B1과 같고, 목적지만 HyperPod sandbox 노드의 sandbox-gvisor-hyperpod-v1입니다. (라벨 `kernel code`)
13. **HyperPod GRPO trainer → gvisor-hyperpod pool v2**: rollout 동안 v2는 두 번째 sandbox 노드에서 돌고(버전마다 replica 하나), trainer는 parity와 ConfigMap patch 뒤 다음 batch 경계에서 전환합니다. (라벨 `after switch`)
14. **gvisor-hyperpod pool v1 → ECR repositories**: HyperPod 노드가 execution role의 ECR pull 권한으로 이미지를 당깁니다. (라벨 `image pull`)
15. **Operator workstation → ECR repositories**: 운영자가 이미지를 빌드해 push합니다(HYPERPOD=1). (라벨 `image push`)
16. **Operator workstation → S3 lifecycle scripts**: 운영자가 on_create.sh, on_create_sandbox.sh, register_runsc.sh, node-guard.sh를 bucket에 sync합니다. (라벨 `script upload`)
17. **EKS 1.36 private API → CloudWatch Logs**: control plane 로그가 CloudWatch Logs로 갑니다. VPC flow log(REJECT)는 두 번째 log group으로 가요. (라벨 `control plane logs`)
18. **EKS 1.36 private API → KMS secrets key**: EKS가 KMS key로 Kubernetes Secret을 암호화합니다. (라벨 `encrypt secrets`)

## 서비스
| 서비스 | 이 시스템에서의 역할 | 비고 |
|---|---|---|
| Operator workstation | 스크립트를 실행하고 터널로 kubectl과 helm을 쓰며 이미지를 빌드해 올립니다 | AWS Cloud 밖 |
| SSM Session Manager | 워크스테이션에서 API endpoint까지 이어 주는 port forwarding 세션 | |
| Access instance t4g.nano | 세션만 받는 경유 호스트, 들어오는 규칙이 없음 | private subnet |
| EKS 1.36 private API | private endpoint만 있는 control plane, HyperPod training operator도 add-on으로 설치됨 | |
| KMS secrets key | Kubernetes Secret을 암호화하는 고객 관리 키 | rotation 켜짐 |
| HyperPod GRPO trainer | trainer instance group 위의 학습 Job, 노드 자동 복구 포함 | `sagemaker` 아이콘 |
| gvisor-hyperpod pool v1 | 지금 트래픽을 받는 gVisor 샌드박스 pool, 버전마다 replica 하나 | 기본 차단 NetworkPolicy |
| gvisor-hyperpod pool v2 | 두 번째 sandbox 노드의 다음 버전, 검증과 전환 전에는 트래픽이 없음 | |
| AMI builder m6i.large | base AMI로 띄워 드라이버를 바꾸고 gVisor를 설치한 뒤 꺼지는 임시 인스턴스 | 이미지를 만든 뒤 종료 |
| Custom AMI, NVIDIA 580.178.04 | sandbox instance group이 부팅하는 이미지 | scripts/08_cleanup.sh가 등록 해제 |
| ECR repositories | 세 이미지의 비공개 저장소 | scripts/03_build_push_images.sh가 생성 |
| CloudWatch Logs | control plane 로그와 VPC flow log | 보존 한 달 |
| NAT gateway | private subnet의 유일한 출구, 두 instance group과 builder가 사용 | |
| S3 lifecycle scripts | 두 instance group이 부팅 때 실행할 스크립트를 담은 비공개 bucket | 공개 접근 차단 |
| Hugging Face Hub | policy 모델 weight의 외부 출처 | AWS Cloud 밖 |
| VPC | AZ 두 개, NAT만 있는 public subnet과 노드가 있는 private subnet | 그림에 없음 |
| System node group m6i.large x2 | B2에 남는 유일한 EKS node group, CoreDNS와 add-on과 도구 Job | 그림에 없음 |
| IAM roles | CDK가 만든 역할들과 HyperPod execution role | 그림에 없음 |
| Kubernetes ConfigMap sandbox-routing | 활성 runtime gvisor-hyperpod와 버전, pool 주소를 담은 설정 | 그림에 없음, 9번 선이 실어 나름 |
| HyperPod dependency chart and training operator add-on | HyperPodPyTorchJob을 실행하는 Helm release와 EKS add-on | 그림에 없음 |
| HyperPod EKS public base AMI | AWS가 배포하는 HyperPod 기본 이미지, custom AMI는 반드시 이것에서 만들어야 함 | 그림에 없음, builder 설명에 이름 |

## 설계 결정
- gateway는 없습니다. trainer가 pool을 직접 부르고 reward batch마다 버전을 고정해요(src/gpusandbox/client/routing.py:1-6). gateway는 production 전용입니다(docs/production/00_architecture.md:103).
- 저장소 문서끼리 어긋납니다. docs/production/00_architecture.md:164는 드라이버 595.91.07 때문에 HyperPod 노드의 gVisor(B2)가 불가능하다고 적지만, docs/handson/07_hyperpod.md:312-349와 infra/hyperpod/ami/ 코드는 custom AMI로 이를 구현해요. 브리프와 이 그림은 코드를 따릅니다.
- AMI 빌드 파이프라인(builder와 custom AMI, 그룹 AMI build)은 B2를 가능하게 하는 부분이라 그렸고, public base AMI는 그리지 않고 builder 설명에 이름을 적었습니다.
- 6번(node image)은 pool v1에서 끝납니다. HyperPod sandbox instance group이 노드가 아니라 그룹이기 때문이고, AMI는 두 sandbox 노드와 두 pool을 모두 부팅해요.
- 7번(runsc setup)은 샌드박스 쪽에서 bucket으로 그렸습니다. HyperPod에서 runsc와 node guard를 등록하는 것이 on_create_sandbox.sh이기 때문이에요. 8번은 trainer 그룹의 최소 on_create.sh입니다.
- HyperPod 전용 stencil이 없어서 trainer는 Amazon SageMaker AI 아이콘 `sagemaker`에 HyperPod GRPO trainer 라벨을 붙였습니다(B1과 같음). aws-icons-aliases.md는 `sagemaker_2`를 안내하지만 layout-and-style.md와 scaffold가 그것을 Unified Studio로 다뤄서 `sagemaker`를 썼어요.
- 샌드박스 pool은 다른 시나리오처럼 `container_1`을 쓰고, HyperPod 배치는 그룹 제목 HyperPod sandbox ml.g5.xlarge x2가 보여 줍니다. node group과 instance group은 role group, Hugging Face Hub는 `internet`, 운영자는 `client`, builder는 M6i instance 아이콘, custom AMI는 AMI 아이콘이에요.
- 빌드 중 storage.googleapis.com에서 받는 gVisor와 NVIDIA 드라이버 다운로드는 그리지 않았습니다(infra/gvisor/install-gvisor.sh:16, infra/hyperpod/ami/customize-b2.sh:47-59). 둘 다 NAT gateway로 나가요.
- 이 그림은 컴포넌트 15개로 diagram budget의 끝입니다. 더 넣으려면 두 번째 페이지가 필요해요.
- 그룹 제목은 instance group 이름과 instance type만 적고 1열 카드에 두 줄로 들어가게 했습니다.
- 노드 장애는 EKS managed node group 대신 HyperPod NodeRecovery(reboot 또는 replace)가 처리합니다. 샌드박스 egress 선은 일부러 없고, default-deny NetworkPolicy, IMDS와 API server와 kubelet에 닿지 않아야 하는 readiness, lifecycle 스크립트가 설치한 node guard가 그 자리를 지켜요.
- Architecture review는 건너뛰었습니다. AWS documentation MCP 서버가 없었고, CDK stack의 cdk-nag 검사(cdk/app.py:21-22, 수용 finding은 cdk/gpusandbox_cdk/stack.py:271-281)는 AWS CLI로 만든 HyperPod 리소스, AMI builder, custom AMI를 다루지 않아요. 제목은 em dash 금지 때문에 "Architecture review (skipped)"로 적었습니다.
- 브리프가 남긴 질문은 /outputs가 emptyDir라서 노드 교체 때 checkpoint가 사라진다는 점과 CloudWatch alarm이 없다는 점입니다. builder는 결과를 serial console에 남겨요.
- 그림의 글자는 모두 영어입니다. 이미지 하나를 한국어와 영어 페이지가 함께 씁니다.
- 리뷰 단계 결정: NAT gateway 상자를 두 번째 "Shared services" 대신 **Egress**로 이름을 바꿨습니다. `model pull`이 점선 세 개(`runsc setup`, `image pull`, `node image`)와 교차하는데, 이 세 선은 모두 pool v1의 아래쪽으로 드나들어야 해요. pool v1의 왼쪽은 kernel code, 위쪽은 pool v2가 차지하고, 공유 열과 AMI 그룹은 왼쪽 아래, NAT는 오른쪽에 있어서 어떤 배치로도 교차를 셋보다 줄일 수 없었습니다. NAT나 AMI 그룹을 맨 위로 올리면 cloud 위쪽에 빈 띠가 생기고 네 그림의 공통 배치가 깨져서 교차를 받아들였고, 교차점마다 hop이 그려집니다. 브리프의 배치 메모는 AMI 그룹을 샌드박스 그룹 위에 두라고 했지만 pool v2가 pool v1 바로 위에 있어서 불가능했고, Operator access 아래에 두었어요.

## 이 다이어그램에 없는 것
VPC와 subnet, IAM 역할, system node group, routing ConfigMap, HyperPod add-on, public base AMI는 위 서비스 표에만 있습니다. 브리프가 범위 밖으로 둔 것도 그리지 않았어요. Kata GPU와 Kata CPU node group(HyperPod 노드 위의 Kata는 불가능), 클러스터로 가는 길이 없는 demo site, Agent Sandbox extension, production reference, 기본으로 꺼진 public endpoint 옵션이 여기에 해당합니다.
