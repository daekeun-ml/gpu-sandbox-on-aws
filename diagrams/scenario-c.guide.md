# 시나리오 C: nested virtualization c8i 노드 하나의 CPU 전용 샌드박스

GPU가 전혀 없는 가장 싼 경로입니다. EC2 nested virtualization을 쓰는 c8i.2xlarge 노드 하나에서 CPU 샌드박스 runtime 세 가지(gVisor runsc, Cloud Hypervisor 위의 Kata, QEMU 위의 Kata)가 나란히 돌고, system 노드의 모델 없는 reward 루프 Job이 trainer 대신 routing과 v1에서 v2로의 rollout을 실제로 돌려 봐요. 학습은 하지 않습니다.

![시나리오 C](scenario-c.drawio.png)

## 다이어그램 읽는 법
- **Operator access**: 운영자가 클러스터 API에 닿는 유일한 길입니다. SSM Session Manager와 access instance를 묶었어요.
- **EKS control plane**: private endpoint만 있는 EKS control plane과 KMS key입니다.
- **system nodes m6i.large x2**(EKS node group system): reward 루프를 모는 simulate and probe Jobs가 여기서 돕니다. 다른 시나리오에서는 그리지 않는 node group인데, 이 시나리오에서는 trainer 자리를 대신하므로 그렸어요.
- **sandbox-kata-cpu node c8i.2xlarge**(EKS node group sandbox-kata-cpu): 활성 pool kata-clh-cpu v1과 v2, 그리고 비교용 gvisor-cpu와 kata-qemu-cpu pool이 한 노드에 있습니다.
- **Shared services**: CloudWatch Logs입니다. **Registry**: ECR repositories예요.
- **선**: 실선은 동기 호출, 점선은 비동기 또는 보조 관계입니다. 선 위의 글자가 그 홉에서 무엇이 흐르는지이고, 아래 단계마다 같은 글자를 `라벨`로 인용했어요. 단계 번호는 브리프 관계표의 `#` 순서입니다.
- Operator workstation은 AWS Cloud 상자 밖에 있습니다. 모델 다운로드가 없어서 Hugging Face Hub와 NAT gateway는 그림에 없어요.

## 단계별 흐름
1. **Operator workstation → SSM Session Manager**: 운영자가 cdk/tunnel.sh로 port forwarding 세션을 엽니다. scripts/kata/cpu_nodes.sh 이후의 kubectl과 helm이 이 터널로 실행돼요. (라벨 `kubectl tunnel`)
2. **SSM Session Manager → Access instance t4g.nano**: 세션은 inbound 규칙이 없는 private subnet의 access instance를 거칩니다. (라벨 `port forward`)
3. **Access instance t4g.nano → EKS 1.36 private API**: access instance가 private endpoint의 443 포트로 연결합니다. (라벨 `HTTPS 443`)
4. **EKS 1.36 private API → simulate and probe Jobs**: scripts/ops/simulate.sh가 k8s/probe/job-probe.yaml.tpl을 Job simulate로 렌더링해 ns rl-trainer에 넣습니다. node selector와 toleration이 없어서 taint 없는 system 노드만 이 Job을 받고, Job은 ConfigMap sandbox-routing과 audience gpu-sandbox인 projected token을 마운트해요. 워크스테이션이 아니라 클러스터 안에서 돌고, 스크립트는 로그만 따라갑니다. (라벨 `Job, active pool`)
5. **simulate and probe Jobs → kata-clh-cpu pool v1**: 20초마다(기본 30 batch) Job이 routing snapshot 하나를 잡고, completion 대신 CPU golden submission 4개를 headless Service로 활성 pool kata-clh-cpu v1에 보냅니다. trainer와 같은 KernelRewards 코드(require_triton off)로 reward를 계산해 reward_batch 이벤트로 출력해요. (라벨 `golden code`)
6. **simulate and probe Jobs → kata-clh-cpu pool v2**: 두 번째 터미널에서 scripts/ops/rollout.sh kata-clh-cpu v1 v2가 v2를 배포하고 검증하고 parity를 확인한 뒤 ConfigMap을 patch합니다. Job은 batch 경계에서 sandbox_version_switch를 출력하고, served_versions에 v1과 v2가 섞이지 않아요. (라벨 `after switch`)
7. **simulate and probe Jobs → gvisor-cpu pool v1**: ops/verify.sh의 probe(격리 증거, egress 차단, golden verdict)와 ops/bench.sh의 bench(cold start, latency)가 같은 Job 템플릿으로 gvisor-cpu pool도 검사합니다. 활성 pool이 아니라서 점선이지만, 세 runtime을 같은 노드에서 같은 조건으로 비교하는 데 꼭 필요한 선이에요. (라벨 `probe, bench`)
8. **simulate and probe Jobs → kata-qemu-cpu pool v1**: 같은 probe와 bench가 비교 기준선인 kata-qemu-cpu pool에도 돕니다. nested virtualization에서 잰 speedup은 reward 근거로 쓰지 않습니다. (라벨 `probe, bench`)
9. **kata-clh-cpu pool v1 → ECR repositories**: c8i 노드와 system 노드가 node role로 이미지를 당깁니다. pool v1의 왼쪽은 golden code, 아래쪽은 다른 pool이 차지해서 선이 오른쪽으로 나가 Registry로 내려가요. (라벨 `image pull`)
10. **Operator workstation → ECR repositories**: 운영자가 sandbox와 control 이미지 두 개만 빌드해 push합니다(scripts/03_build_push_images.sh --no-trainer). (라벨 `image push`)
11. **EKS 1.36 private API → CloudWatch Logs**: control plane 로그가 CloudWatch Logs로 갑니다. VPC flow log(REJECT)는 두 번째 log group으로 가요. (라벨 `control plane logs`)
12. **EKS 1.36 private API → KMS secrets key**: EKS가 KMS key로 Kubernetes Secret을 암호화합니다. (라벨 `encrypt secrets`)

## 서비스
| 서비스 | 이 시스템에서의 역할 | 비고 |
|---|---|---|
| Operator workstation | 스크립트를 실행하고 터널로 kubectl과 helm을 쓰며 두 이미지를 빌드해 올립니다 | AWS Cloud 밖 |
| SSM Session Manager | 워크스테이션에서 API endpoint까지 이어 주는 port forwarding 세션 | |
| Access instance t4g.nano | 세션만 받는 경유 호스트, 들어오는 규칙이 없음 | private subnet |
| EKS 1.36 private API | private endpoint만 있는 control plane과 기본 add-on | |
| KMS secrets key | Kubernetes Secret을 암호화하는 고객 관리 키 | rotation 켜짐 |
| simulate and probe Jobs | 템플릿 하나로 만드는 일회성 Job들(simulate, probe, parity, bench) | system 노드에서 실행 |
| kata-clh-cpu pool v1 | 지금 트래픽을 받는 pool, pod마다 Cloud Hypervisor 위의 Kata microVM 하나 | 기본 차단 NetworkPolicy |
| kata-clh-cpu pool v2 | 다음 버전 pool, 평가 200회마다 pod VM을 새로 만듦, 전환 전에는 트래픽 없음 | |
| gvisor-cpu pool v1 | nvproxy 없이 systrap으로 도는 gVisor pool | 노드 user data가 설치 |
| kata-qemu-cpu pool v1 | pod마다 QEMU 위의 Kata microVM 하나 | 비교 기준선 |
| ECR repositories | sandbox와 control 이미지의 비공개 저장소 | scripts/03_build_push_images.sh가 생성 |
| CloudWatch Logs | control plane 로그와 VPC flow log | 보존 한 달 |
| VPC | AZ 두 개, NAT만 있는 public subnet과 노드가 있는 private subnet | 그림에 없음 |
| NAT gateway | 여전히 배포되어 이미지 pull과 부팅 때 다운로드의 출구가 되지만, 그려진 선 중에는 필요로 하는 것이 없음 | 그림에 없음 |
| IAM roles | cluster, node, access instance 역할과 운영자 access entry | 그림에 없음 |
| Kubernetes ConfigMap sandbox-routing | 활성 runtime kata-clh-cpu와 버전, pool 주소를 담은 설정 | 그림에 없음, 4번 선이 실어 나름 |
| kata-deploy DaemonSet | c8i 노드에만 Kata를 설치하고 RuntimeClass를 만드는 Helm release | 그림에 없음 |

## 설계 결정
- reward 루프는 워크스테이션에서 터널로 도는 것이 아니라 system 노드의 ns rl-trainer에서 Job simulate로 돕니다(scripts/ops/simulate.sh:3-5, scripts/lib_jobs.sh:12-13). 워크스테이션은 Job을 적용하고 로그를 따라갈 뿐이에요.
- CPU pool 이름은 gvisor-cpu, kata-clh-cpu, kata-qemu-cpu이고 RuntimeClass는 gvisor-cpu, kata-clh, kata-qemu입니다. 활성 pool이자 v1에서 v2로 굴리는 pool은 kata-clh-cpu예요(docs/handson/10_cpu_only.md:191, docs/handson/10_cpu_only.md:224). node group sandbox-kata-cpu는 label gpusandbox/role=sandbox-kata를 답니다(stack.py:241).
- 이미지는 sandbox와 control 두 개만 빌드합니다(scripts/03_build_push_images.sh --no-trainer).
- 노드 `sim`은 모든 tool 실행(simulate, probe, parity, bench)이 쓰는 Job 템플릿 하나를 뜻합니다. 7번과 8번은 활성이 아닌 두 pool에 대한 probe와 bench 실행이고, 점선이지만 선이 없는 pool이 생기지 않도록 꼭 그렸어요.
- Kubernetes workload(Job, pool Deployment)는 Containers 카테고리의 `container_1`로 그리고 workload 이름을 붙였습니다. `eks` 아이콘은 control plane만 뜻해요.
- gVisor, Kata, Cloud Hypervisor, QEMU는 stencil이 없어서 pool 라벨(pool 이름이 곧 runtime)과 설명으로 드러냈습니다. c8i node group은 이름과 instance type을 제목에 단 role group이에요.
- system node group은 이 시나리오에서만 그룹으로 그렸습니다. reward driver가 그 위에 있기 때문이고, A, B1, B2에서는 그리지 않는 행이라는 점이 시나리오 차이예요.
- kata-deploy DaemonSet은 AWS 리소스가 아니라 kube-system의 Helm release이고 독자가 봐야 할 관계가 없어서 그리지 않았습니다.
- 그룹 제목은 node group 이름과 instance type만 적고 1열 카드에 두 줄로 들어가게 했습니다.
- 샌드박스 egress 선은 일부러 없습니다. default-deny NetworkPolicy, IMDS와 API server와 kubelet에 닿지 않아야 하는 readiness, c8i 노드 user data의 node guard가 그 자리를 지켜요.
- Architecture review는 건너뛰었습니다. AWS documentation MCP 서버가 없었고, CDK stack이 synth마다 cdk-nag AwsSolutions 검사를 돌립니다(cdk/app.py:21-22, 수용 finding은 cdk/gpusandbox_cdk/stack.py:271-281). 제목은 em dash 금지 때문에 "Architecture review (skipped)"로 적었어요.
- 브리프가 남긴 질문은 CloudWatch alarm이 없다는 점입니다. reward_batch와 sandbox_version_switch 이벤트는 Job의 stdout으로만 나가요.
- 그림의 글자는 모두 영어입니다. 이미지 하나를 한국어와 영어 페이지가 함께 씁니다.
- 리뷰 단계 결정: ECR repositories를 다른 시나리오처럼 CloudWatch Logs 아래 공유 열에 둘 수 없었습니다. pool v1의 왼쪽은 golden code가, 아래쪽은 gvisor-cpu와 kata-qemu-cpu가 차지해서 `image pull`은 오른쪽으로만 나갈 수 있고, `image push`는 왼쪽부터 비어 있는 lane을 따라 들어와야 하기 때문이에요. 그래서 ECR은 오른쪽 아래의 자기 상자에 두고, 두 번째 "Shared services" 대신 **Registry**라는 이름을 붙였습니다. 왼쪽 아래가 비어 보이는 것과 lane 하나에 아이콘 하나씩인 것은 이 배치의 결과이고, 대신 교차하는 선이 하나도 없어요.

## 이 다이어그램에 없는 것
VPC와 subnet, NAT gateway, IAM 역할, routing ConfigMap, kata-deploy DaemonSet은 위 서비스 표에만 있습니다. 브리프가 범위 밖으로 둔 것도 그리지 않았어요. GPU passthrough를 쓰는 Kata GPU node group, Agent Sandbox extension, 클러스터로 가는 길이 없는 demo site, production reference(c8i와 m8i와 r8i를 쓰는 Karpenter NodePool 포함), 기본으로 꺼진 public endpoint 옵션이 여기에 해당합니다.
