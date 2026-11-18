// Architecture patterns page: draws each deployment pattern as an SVG with AWS icons and replays
// its flows step by step (dots travel along the edges). Everything here is static data written in
// this file; the page makes no network request and inserts every string as text.
"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";
const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const ICON = 72;
const COLORS = { req: "#ff9900", res: "#1a7f37", ctl: "#2f6fde" };

const UI = {
  ko: {
    back: "← 데모로 돌아가기", navPatterns: "패턴별 아키텍처",
    eyebrow: "패턴별 아키텍처",
    title: "학습기와 샌드박스를 어디에 둘까",
    lede: "네 가지 패턴 모두 같은 CDK 스택(private EKS API, SSM 터널, KMS 암호화, CloudWatch 로그)을 씁니다. 달라지는 것은 학습기와 샌드박스가 올라가는 위치예요. 패턴을 고르고 흐름을 재생해 보세요. 그림에는 흐름에 필요한 구성 요소만 그렸습니다.",
    flows: "흐름", prev: "◀ 이전", next: "다음 ▶", play: "▶ 재생", pause: "❚❚ 일시정지", replay: "↻ 처음부터",
    train: "학습기 위치", sandbox: "샌드박스 위치", when: "이럴 때 씁니다", status: "AWS 실행",
    legendReq: "채점 요청", legendRes: "채점 결과", legendCtl: "배포, 설정, 이미지",
    legendSolid: "실선: 바로 호출", legendDashed: "점선: 배포나 설정", legendBlocked: "빨간 ✕: 막힌 연결",
    step: "단계",
    footer: "AWS 아이콘은 AWS Architecture Icons를 사용했습니다. 그림은 이해를 돕기 위한 단순화로, 노드 수와 세부 리소스는 문서를 보세요.",
    guide: "가이드북", repo: "GitHub 저장소",
  },
  en: {
    back: "← Back to the demo", navPatterns: "Architecture patterns",
    eyebrow: "Architecture patterns",
    title: "Where to put the trainer and the sandboxes",
    lede: "All four patterns use the same CDK stack (private EKS API, SSM tunnel, KMS encryption, CloudWatch logs). What changes is where the trainer and the sandboxes run. Pick a pattern and play a flow. The diagrams show only what each flow needs.",
    flows: "Flow", prev: "◀ Back", next: "Next ▶", play: "▶ Play", pause: "❚❚ Pause", replay: "↻ From the start",
    train: "Trainer runs on", sandbox: "Sandboxes run on", when: "Use it when", status: "On AWS",
    legendReq: "scoring request", legendRes: "scoring result", legendCtl: "deploy, config, images",
    legendSolid: "solid: direct call", legendDashed: "dashed: deploy or config", legendBlocked: "red ✕: blocked connection",
    step: "Step",
    footer: "AWS icons are from the AWS Architecture Icons. The diagrams are simplified; see the guide for node counts and every resource.",
    guide: "Guidebook", repo: "GitHub repository",
  },
};

const L = (ko, en) => ({ ko, en });
const N = (id, icon, x, y, label, sub) => ({ id, icon, x, y, label, sub });
const E = (id, pts, opts = {}) => ({ id, pts, ...opts });

// ---------- shared parts ----------
const COMMON_NODES = [
  N("operator", "client", 70, 360, L("운영자", "Operator"), L("작업 PC", "workstation")),
  N("ssm", "ssm", 260, 360, L("SSM 터널", "SSM tunnel"), L("Session Manager", "Session Manager")),
  N("access", "ec2", 430, 360, L("접속용 서버", "Access instance"), L("t4g.nano", "t4g.nano")),
  N("eks", "eks", 610, 360, L("EKS API", "EKS API"), L("private 전용", "private only")),
  N("ecr", "ecr", 610, 150, L("ECR", "ECR"), L("이미지 저장소", "image registry")),
  { id: "routing", icon: "doc", x: 800, y: 150, label: L("라우팅 표", "Routing table") },
];
const EGRESS_NODES = [
  N("nat", "nat", 1010, 600, L("NAT 게이트웨이", "NAT gateway"), L("유일한 출구", "the only way out")),
  N("hf", "internet", 1210, 600, L("Hugging Face", "Hugging Face"), L("모델 저장소", "model hub")),
];
const COMMON_EDGES = (sbxX) => [
  E("e_tunnel", [[106, 360], [224, 360]], { label: L("터널", "tunnel"), lx: 165, ly: 348 }),
  E("e_fwd", [[296, 360], [394, 360]], { label: L("포트 전달", "forward"), lx: 345, ly: 348 }),
  E("e_api", [[466, 360], [574, 360]], { label: L("HTTPS 443", "HTTPS 443"), lx: 520, ly: 348 }),
  E("e_push", [[70, 324], [70, 150], [574, 150]], { dashed: true, label: L("이미지 올리기", "image push"), lx: 330, ly: 138 }),
  E("e_job", [[646, 360], [764, 360]], { dashed: true, label: L("Job 배포", "deploy Job"), lx: 705, ly: 386 }),
  E("e_route", [[800, 190], [800, 324]], { dashed: true, label: L("현재 버전", "active version"), lx: 812, ly: 262, anchor: "start" }),
  E("e_cfg", [[646, 346], [702, 346], [702, 150], [740, 150]], { dashed: true }),
  E("e_pull", [[610, 114], [610, 40], [sbxX, 40], [sbxX, 62]], { dashed: true, label: L("이미지 받기", "image pull"), lx: (610 + sbxX) / 2, ly: 30 }),
];
const EGRESS_EDGES = [
  E("e_model", [[800, 452], [800, 600], [974, 600]], { label: L("모델 받기", "model pull"), lx: 812, ly: 530, anchor: "start" }),
  E("e_hf", [[1046, 600], [1174, 600]], { label: L("HTTPS", "HTTPS"), lx: 1110, ly: 588 }),
];
const GPU_POOL_EDGES = [
  E("e_req1", [[836, 360], [974, 360]], { label: L("채점 요청", "score"), lx: 905, ly: 386 }),
  E("e_req2", [[836, 346], [893, 346], [893, 150], [974, 150]], { dashed: true, needs: ["v2"] }),
];
const CORE_GROUPS = [
  { x: 188, y: 274, w: 324, h: 178, title: L("운영자 접속", "Operator access") },
  { x: 530, y: 274, w: 160, h: 178, title: L("EKS 클러스터", "EKS cluster") },
  { x: 530, y: 62, w: 160, h: 180, title: L("공용 서비스", "Shared") },
];
const BLOCKED_RIGHT = { line: [[1046, 360], [1140, 360]], x: 1140, y: 336, text: L("외부 연결 차단", "egress blocked") };

// ---------- flows (texts are per pattern; the motion is shared) ----------
const S = (ko, en, opts = {}) => ({ text: L(ko, en), ...opts });
const TUNNEL = [{ e: "e_tunnel", c: "ctl" }, { e: "e_fwd", c: "ctl" }, { e: "e_api", c: "ctl" }];

function scoringFlow(pool, poolEn) {
  return {
    id: "step", title: L("학습 한 step: 코드 채점", "One training step: scoring"),
    init: { hide: ["v2"], routing: "v1" },
    steps: [
      S("모델이 문제마다 GPU 코드를 여러 개 씁니다.", "The model writes several GPU kernels for each problem.",
        { light: ["trainer"], badge: { node: "trainer", text: L("코드 작성", "writing code") } }),
      S("라우팅 표에서 지금 쓸 샌드박스를 확인합니다. 지금은 v1입니다.", "It reads the routing table to see which sandbox to use. Right now it is v1.",
        { light: ["routing", "trainer"], moves: [{ e: "e_route", c: "ctl" }] }),
      S(`코드마다 인증 토큰을 붙여 ${pool} v1에 채점을 요청합니다.`, `Each kernel goes to ${poolEn} v1 with an auth token.`,
        { light: ["trainer", "v1"], moves: [{ e: "e_req1", c: "req", n: 3 }] }),
      S("샌드박스 안에서 코드를 실행하고 정답과 비교합니다. 밖으로 나가는 연결은 모두 막혀 있습니다.",
        "The sandbox runs the code and compares it with the reference. Every outbound connection is blocked.",
        { light: ["v1"], blocked: true, badge: { node: "v1", text: L("채점 중", "scoring") } }),
      S("채점 결과(정답 여부, 속도)가 학습기로 돌아옵니다.", "The result (correct or not, how fast) comes back to the trainer.",
        { light: ["v1", "trainer"], moves: [{ e: "e_req1", c: "res", n: 3, back: true }] }),
      S("결과를 점수로 바꿔 모델을 업데이트하고, 다음 step으로 넘어갑니다.", "The results become rewards, the model is updated, and the next step starts.",
        { light: ["trainer"], badge: { node: "trainer", text: L("모델 업데이트", "model update") } }),
    ],
  };
}

function switchFlow(pool, poolEn) {
  return {
    id: "switch", title: L("버전 바꾸기 (v1 → v2)", "Switching versions (v1 → v2)"),
    init: { hide: ["v2"], routing: "v1" },
    steps: [
      S(`운영자가 ${pool} v1 옆에 새 버전 v2를 띄웁니다. 아직 학습 요청은 받지 않습니다.`,
        `The operator starts the new version v2 next to ${poolEn} v1. It takes no training traffic yet.`,
        { light: ["operator", "eks", "v2"], show: ["v2"], moves: TUNNEL }),
      S("미리 준비한 코드로 v1과 v2의 채점 결과가 같은지 확인합니다.", "Prepared test code checks that v1 and v2 give the same results.",
        { light: ["v1", "v2"], badge: { node: "v2", text: L("결과 비교", "comparing") } }),
      S("결과가 같으면 라우팅 표를 v2로 바꿉니다.", "If they match, the routing table is switched to v2.",
        { light: ["eks", "routing"], routing: "v2", moves: [{ e: "e_cfg", c: "ctl" }] }),
      S("학습기는 지금 배치를 v1에서 마치고, 다음 배치부터 v2로 보냅니다. 한 배치가 두 버전으로 섞이지 않습니다.",
        "The trainer finishes the current batch on v1 and sends the next batch to v2. No batch is split across versions.",
        { light: ["trainer", "v2"], moves: [{ e: "e_req2", c: "req", n: 3 }] }),
      S("v1은 0개로 줄여 두었다가, 문제가 생기면 되돌릴 때 씁니다.", "v1 is scaled to zero and kept for a rollback.",
        { light: ["v1"], dim: ["v1"], badge: { node: "v1", text: L("0개로 대기", "scaled to 0") } }),
    ],
  };
}

// ---------- the four patterns ----------
const PATTERNS = [
  {
    id: "a", key: "A", name: L("EC2 GPU", "EC2 GPU"),
    oneLine: L("학습기와 샌드박스를 모두 EKS의 EC2 GPU 노드에 둡니다.", "The trainer and the sandboxes both run on EC2 GPU nodes in EKS."),
    facts: {
      train: L("EC2 g5.2xlarge (A10G 1장)", "EC2 g5.2xlarge (one A10G)"),
      sandbox: L("gVisor 풀, EC2 g5.xlarge 2대", "gVisor pool, two EC2 g5.xlarge"),
      when: L("모든 구성 요소를 직접 관리하고 싶을 때", "You want to manage every part yourself"),
      status: L("2026-11-18 실행 (GRPO 5 step까지)", "Run on 2026-11-18 (up to 5 GRPO steps)"),
    },
    cloudW: 960,
    nodes: [...COMMON_NODES, ...EGRESS_NODES,
      N("trainer", "container", 800, 360, L("GRPO 학습기", "GRPO trainer"), L("Qwen2.5-Coder 1.5B", "Qwen2.5-Coder 1.5B")),
      N("v1", "container", 1010, 360, L("gVisor 풀 v1", "gVisor pool v1"), L("runsc + nvproxy", "runsc + nvproxy")),
      N("v2", "container", 1010, 150, L("gVisor 풀 v2", "gVisor pool v2"), L("다음 버전", "next version"))],
    edges: [...COMMON_EDGES(1010), ...EGRESS_EDGES, ...GPU_POOL_EDGES],
    groups: [...CORE_GROUPS,
      { x: 715, y: 62, w: 170, h: 390, title: L("학습 노드", "Trainer node"), sub: L("EC2 g5.2xlarge", "EC2 g5.2xlarge") },
      { x: 925, y: 62, w: 170, h: 390, title: L("샌드박스 노드", "Sandbox nodes"), sub: L("EC2 g5.xlarge x2", "EC2 g5.xlarge x2") },
      { x: 925, y: 514, w: 170, h: 178, title: L("외부 출구", "Egress") }],
    blocked: BLOCKED_RIGHT,
    flows: [
      {
        id: "setup", title: L("준비와 배포", "Setup and deploy"), init: { hide: ["v2"], routing: "v1" },
        steps: [
          S("운영자가 SSM 터널로 private EKS API에 접속합니다. 인터넷에 열린 접속 경로는 없습니다.",
            "The operator reaches the private EKS API through an SSM tunnel. Nothing is open to the internet.",
            { light: ["operator", "ssm", "access", "eks"], moves: TUNNEL }),
          S("학습기와 샌드박스 이미지를 만들어 ECR에 올립니다.", "The trainer and sandbox images are built and pushed to ECR.",
            { light: ["operator", "ecr"], moves: [{ e: "e_push", c: "ctl" }] }),
          S("샌드박스 노드가 ECR에서 이미지를 받아 gVisor 풀을 띄웁니다.", "The sandbox nodes pull the image from ECR and start the gVisor pool.",
            { light: ["ecr", "v1"], moves: [{ e: "e_pull", c: "ctl" }] }),
          S("학습 Job을 배포하면 EKS가 학습 노드에 학습기를 띄우고 라우팅 표를 연결합니다.",
            "Deploying the training Job makes EKS start the trainer on its node and mount the routing table.",
            { light: ["eks", "trainer", "routing"], moves: [{ e: "e_job", c: "ctl" }, { e: "e_route", c: "ctl" }] }),
          S("학습기가 NAT를 거쳐 Hugging Face에서 모델을 받습니다.", "The trainer downloads the model from Hugging Face through the NAT gateway.",
            { light: ["trainer", "nat", "hf"], moves: [{ e: "e_model", c: "ctl" }, { e: "e_hf", c: "ctl" }] }),
        ],
      },
      scoringFlow("gVisor 풀", "gVisor pool"),
      switchFlow("gVisor 풀", "gVisor pool"),
    ],
  },
  {
    id: "b1", key: "B1", name: L("HyperPod 학습", "HyperPod training"),
    oneLine: L("학습기만 SageMaker HyperPod로 옮기고, 샌드박스는 A와 같은 EC2 노드에 둡니다.",
      "Only the trainer moves to SageMaker HyperPod; the sandboxes stay on the same EC2 nodes as in A."),
    facts: {
      train: L("HyperPod ml.g5.2xlarge", "HyperPod ml.g5.2xlarge"),
      sandbox: L("gVisor 풀, EC2 g5.xlarge 2대", "gVisor pool, two EC2 g5.xlarge"),
      when: L("긴 학습에서 노드 자동 교체와 Job 재시작이 필요할 때", "Long training runs need automatic node replacement and Job restarts"),
      status: L("AWS에서 아직 실행하지 않음", "Not run on AWS yet"),
    },
    cloudW: 960,
    nodes: [...COMMON_NODES, ...EGRESS_NODES,
      N("trainer", "sagemaker", 800, 360, L("HyperPod 학습기", "HyperPod trainer"), L("HyperPodPyTorchJob", "HyperPodPyTorchJob")),
      N("v1", "container", 1010, 360, L("gVisor 풀 v1", "gVisor pool v1"), L("runsc + nvproxy", "runsc + nvproxy")),
      N("v2", "container", 1010, 150, L("gVisor 풀 v2", "gVisor pool v2"), L("다음 버전", "next version")),
      N("s3", "s3", 430, 600, L("S3 시작 스크립트", "S3 lifecycle scripts"), L("비공개 버킷", "private bucket"))],
    edges: [...COMMON_EDGES(1010), ...EGRESS_EDGES, ...GPU_POOL_EDGES,
      E("e_s3up", [[70, 452], [70, 600], [394, 600]], { dashed: true, label: L("스크립트 올리기", "upload scripts"), lx: 232, ly: 588 }),
      E("e_boot", [[466, 600], [700, 600], [700, 476], [770, 476], [770, 456]], { dashed: true, label: L("부팅 스크립트", "boot scripts"), lx: 583, ly: 588 })],
    groups: [...CORE_GROUPS,
      { x: 715, y: 62, w: 170, h: 390, title: L("HyperPod 학습", "HyperPod trainer"), sub: L("ml.g5.2xlarge", "ml.g5.2xlarge") },
      { x: 925, y: 62, w: 170, h: 390, title: L("샌드박스 노드", "Sandbox nodes"), sub: L("EC2 g5.xlarge x2", "EC2 g5.xlarge x2") },
      { x: 925, y: 514, w: 170, h: 178, title: L("외부 출구", "Egress") },
      { x: 350, y: 514, w: 160, h: 178, title: L("HyperPod 설정", "HyperPod setup") }],
    blocked: BLOCKED_RIGHT,
    flows: [
      {
        id: "setup", title: L("준비와 배포", "Setup and deploy"), init: { hide: ["v2"], routing: "v1" },
        steps: [
          S("운영자가 SSM 터널로 private EKS API에 접속합니다.", "The operator reaches the private EKS API through an SSM tunnel.",
            { light: ["operator", "ssm", "access", "eks"], moves: TUNNEL }),
          S("이미지를 ECR에 올리고, HyperPod 시작 스크립트를 비공개 S3 버킷에 올립니다.",
            "Images go to ECR, and the HyperPod lifecycle scripts go to a private S3 bucket.",
            { light: ["operator", "ecr", "s3"], moves: [{ e: "e_push", c: "ctl" }, { e: "e_s3up", c: "ctl" }] }),
          S("HyperPod가 S3의 시작 스크립트로 학습 노드를 부팅합니다. 노드에 문제가 생기면 HyperPod가 바꿔 줍니다.",
            "HyperPod boots the trainer node with the scripts from S3, and replaces the node if it fails.",
            { light: ["s3", "trainer"], moves: [{ e: "e_boot", c: "ctl" }] }),
          S("샌드박스 노드(EC2)가 ECR에서 이미지를 받아 gVisor 풀을 띄웁니다.", "The sandbox nodes (EC2) pull the image from ECR and start the gVisor pool.",
            { light: ["ecr", "v1"], moves: [{ e: "e_pull", c: "ctl" }] }),
          S("학습 Job(HyperPodPyTorchJob)을 배포하면 HyperPod 노드에 학습기가 뜨고 라우팅 표가 연결됩니다.",
            "Deploying the HyperPodPyTorchJob starts the trainer on the HyperPod node with the routing table mounted.",
            { light: ["eks", "trainer", "routing"], moves: [{ e: "e_job", c: "ctl" }, { e: "e_route", c: "ctl" }] }),
          S("학습기가 NAT를 거쳐 Hugging Face에서 모델을 받습니다.", "The trainer downloads the model from Hugging Face through the NAT gateway.",
            { light: ["trainer", "nat", "hf"], moves: [{ e: "e_model", c: "ctl" }, { e: "e_hf", c: "ctl" }] }),
        ],
      },
      scoringFlow("gVisor 풀", "gVisor pool"),
      switchFlow("gVisor 풀", "gVisor pool"),
    ],
  },
  {
    id: "b2", key: "B2", name: L("HyperPod 학습과 샌드박스", "HyperPod for both"),
    oneLine: L("학습기와 샌드박스를 모두 HyperPod에 둡니다. 샌드박스 노드는 드라이버를 바꾼 custom AMI로 부팅합니다.",
      "The trainer and the sandboxes both run on HyperPod; the sandbox nodes boot from a custom AMI with a different driver."),
    facts: {
      train: L("HyperPod ml.g5.2xlarge", "HyperPod ml.g5.2xlarge"),
      sandbox: L("gVisor 풀, HyperPod ml.g5.xlarge 2대", "gVisor pool, two HyperPod ml.g5.xlarge"),
      when: L("샌드박스 노드에도 HyperPod의 노드 복구가 필요할 때", "The sandbox nodes also need HyperPod node recovery"),
      status: L("실험 경로, AWS에서 아직 실행하지 않음. 모델 다운로드(NAT)는 A와 같아서 그림에서 뺐습니다.",
        "Experimental, not run on AWS yet. The model download (NAT) is the same as in A and left out."),
    },
    cloudW: 960,
    nodes: [...COMMON_NODES,
      N("trainer", "sagemaker", 800, 360, L("HyperPod 학습기", "HyperPod trainer"), L("HyperPodPyTorchJob", "HyperPodPyTorchJob")),
      N("v1", "container", 1010, 360, L("gVisor 풀 v1", "gVisor pool v1"), L("HyperPod 노드", "HyperPod node")),
      N("v2", "container", 1010, 150, L("gVisor 풀 v2", "gVisor pool v2"), L("다음 버전", "next version")),
      N("s3", "s3", 260, 600, L("S3 시작 스크립트", "S3 lifecycle scripts"), L("비공개 버킷", "private bucket")),
      N("amib", "ec2", 610, 600, L("AMI 빌더", "AMI builder"), L("m6i.large", "m6i.large")),
      N("ami", "ami", 800, 600, L("custom AMI", "Custom AMI"), L("드라이버 580.178.04", "driver 580.178.04"))],
    edges: [...COMMON_EDGES(1010), ...GPU_POOL_EDGES,
      E("e_s3up", [[62, 452], [62, 600], [224, 600]], { dashed: true, label: L("스크립트", "scripts"), lx: 108, ly: 588 }),
      E("e_amib", [[80, 452], [80, 700], [610, 700], [610, 636]], { label: L("AMI 굽기 시작", "start the bake"), lx: 435, ly: 690 }),
      E("e_drv", [[646, 600], [764, 600]], { label: L("드라이버 교체", "swap driver"), lx: 705, ly: 588 }),
      E("e_amiboot", [[836, 600], [1010, 600], [1010, 452]], { dashed: true, label: L("이 AMI로 부팅", "boot from it"), lx: 998, ly: 530, anchor: "end" }),
      E("e_boot", [[260, 564], [260, 490], [770, 490], [770, 456]], { dashed: true, label: L("부팅 스크립트", "boot scripts"), lx: 500, ly: 478 }),
      E("e_boot2", [[770, 490], [940, 490], [940, 380], [974, 380]], { dashed: true })],
    groups: [...CORE_GROUPS.slice(0, 1),
      { x: 530, y: 274, w: 160, h: 178, title: L("EKS 클러스터", "EKS cluster"), sub: L("system 노드만", "system nodes only") },
      CORE_GROUPS[2],
      { x: 715, y: 62, w: 170, h: 390, title: L("HyperPod 학습", "HyperPod trainer"), sub: L("ml.g5.2xlarge", "ml.g5.2xlarge") },
      { x: 925, y: 62, w: 170, h: 390, title: L("HyperPod 샌드박스", "HyperPod sandbox"), sub: L("ml.g5.xlarge x2", "ml.g5.xlarge x2") },
      { x: 180, y: 514, w: 160, h: 178, title: L("HyperPod 설정", "HyperPod setup") },
      { x: 530, y: 514, w: 360, h: 178, title: L("AMI 굽기 (한 번)", "AMI bake (once)") }],
    blocked: BLOCKED_RIGHT,
    flows: [
      {
        id: "setup", title: L("준비와 배포", "Setup and deploy"), init: { hide: ["v2"], routing: "v1" },
        steps: [
          S("운영자가 SSM 터널로 private EKS API에 접속합니다. 이때 EKS에는 system 노드만 있습니다.",
            "The operator reaches the private EKS API through an SSM tunnel. EKS has only system nodes here.",
            { light: ["operator", "ssm", "access", "eks"], moves: TUNNEL }),
          S("AMI 빌더가 HyperPod 기본 AMI의 NVIDIA 드라이버를 gVisor가 지원하는 580.178.04로 바꿔 custom AMI를 만듭니다.",
            "An AMI builder swaps the NVIDIA driver of the HyperPod base AMI for 580.178.04, which gVisor supports, and saves a custom AMI.",
            { light: ["operator", "amib", "ami"], moves: [{ e: "e_amib", c: "ctl" }, { e: "e_drv", c: "ctl" }] }),
          S("HyperPod가 이 custom AMI로 샌드박스 노드를 띄웁니다.", "HyperPod starts the sandbox nodes from this custom AMI.",
            { light: ["ami", "v1"], moves: [{ e: "e_amiboot", c: "ctl" }] }),
          S("S3의 시작 스크립트가 학습 노드를 준비하고, 샌드박스 노드에서는 드라이버와 runsc 설정을 확인합니다.",
            "The lifecycle scripts in S3 prepare the trainer node, and on the sandbox nodes they check the driver and the runsc setup.",
            { light: ["operator", "s3", "trainer", "v1"], moves: [{ e: "e_s3up", c: "ctl" }, { e: "e_boot", c: "ctl" }, { e: "e_boot2", c: "ctl" }] }),
          S("이미지를 받고 학습 Job을 배포하면 HyperPod 노드에 학습기가 뜹니다.", "The images are pulled, and deploying the training Job starts the trainer on HyperPod.",
            { light: ["ecr", "v1", "eks", "trainer"], moves: [{ e: "e_push", c: "ctl" }, { e: "e_pull", c: "ctl" }, { e: "e_job", c: "ctl" }] }),
        ],
      },
      scoringFlow("gVisor 풀", "gVisor pool"),
      switchFlow("gVisor 풀", "gVisor pool"),
    ],
  },
  {
    id: "c", key: "C", name: L("CPU 전용", "CPU only"),
    oneLine: L("GPU 없이 c8i 서버 한 대에서 CPU 샌드박스 세 종류를 비교합니다. 모델 대신 미리 준비한 코드로 채점합니다.",
      "No GPU: three CPU sandbox runtimes on one c8i server, scored with prepared code instead of a model."),
    facts: {
      train: L("없음 (모의 학습 Job)", "None (a simulate Job)"),
      sandbox: L("EC2 c8i.2xlarge 1대: gVisor, Kata CLH, Kata QEMU", "One EC2 c8i.2xlarge: gVisor, Kata CLH, Kata QEMU"),
      when: L("GPU 할당량 없이 런타임 비교와 버전 교체를 먼저 익히고 싶을 때 (컴퓨트 시간당 약 0.57 USD)",
        "You want to learn runtime comparison and version switching first, without GPU quota (about 0.57 USD per compute hour)"),
      status: L("AWS에서 실행", "Run on AWS"),
    },
    cloudW: 1110, height: 640,
    nodes: [...COMMON_NODES,
      N("trainer", "container", 800, 360, L("모의 학습 Job", "Simulate Job"), L("모델 없음", "no model")),
      N("v1", "container", 990, 360, L("kata-clh-cpu v1", "kata-clh-cpu v1"), L("Kata + CLH", "Kata + CLH")),
      N("v2", "container", 990, 150, L("kata-clh-cpu v2", "kata-clh-cpu v2"), L("다음 버전", "next version")),
      N("gv", "container", 1170, 150, L("gvisor-cpu", "gvisor-cpu"), L("gVisor", "gVisor")),
      N("kq", "container", 1170, 360, L("kata-qemu-cpu", "kata-qemu-cpu"), L("Kata + QEMU", "Kata + QEMU"))],
    edges: [...COMMON_EDGES(1080),
      E("e_req1", [[836, 360], [954, 360]], { label: L("채점 요청", "score"), lx: 895, ly: 386 }),
      E("e_req2", [[836, 346], [900, 346], [900, 150], [954, 150]], { dashed: true, needs: ["v2"] }),
      E("e_probe_kq", [[800, 452], [800, 500], [1170, 500], [1170, 452]], { dashed: true, label: L("검증, 성능 측정", "verify, benchmark"), lx: 985, ly: 490 }),
      E("e_probe_gv", [[1080, 500], [1080, 150], [1134, 150]], { dashed: true })],
    groups: [...CORE_GROUPS,
      { x: 715, y: 62, w: 170, h: 390, title: L("system 노드", "System node"), sub: L("m6i.large", "m6i.large") },
      { x: 915, y: 62, w: 335, h: 390, title: L("c8i.2xlarge 노드", "c8i.2xlarge node"), sub: L("CPU 샌드박스 4개, nested virt", "four CPU sandboxes, nested virt") }],
    blocked: { x: 1080, y: 580, text: L("✕ 샌드박스에서 밖으로 나가는 연결은 모두 차단", "✕ every outbound connection from a sandbox is blocked") },
    flows: [
      {
        id: "setup", title: L("준비와 배포", "Setup and deploy"), init: { hide: ["v2"], routing: "v1" },
        steps: [
          S("운영자가 SSM 터널로 private EKS API에 접속합니다.", "The operator reaches the private EKS API through an SSM tunnel.",
            { light: ["operator", "ssm", "access", "eks"], moves: TUNNEL }),
          S("샌드박스 이미지와 도구 이미지 두 개만 ECR에 올립니다. 학습기 이미지는 필요 없습니다.",
            "Only the sandbox and tool images go to ECR. No trainer image is needed.",
            { light: ["operator", "ecr"], moves: [{ e: "e_push", c: "ctl" }] }),
          S("c8i 노드가 이미지를 받아 CPU 샌드박스를 띄웁니다. Kata는 VM 안에서 다시 VM을 띄웁니다.",
            "The c8i node pulls the image and starts the CPU sandboxes. Kata starts a VM inside the VM.",
            { light: ["ecr", "v1", "gv", "kq"], moves: [{ e: "e_pull", c: "ctl" }] }),
          S("모의 학습 Job을 system 노드에 배포합니다. 모델 대신 미리 준비한 코드로 채점을 요청합니다.",
            "The simulate Job is deployed on a system node. It sends prepared code instead of model output.",
            { light: ["eks", "trainer", "routing"], moves: [{ e: "e_job", c: "ctl" }, { e: "e_route", c: "ctl" }] }),
        ],
      },
      {
        id: "step", title: L("모의 학습 한 배치", "One simulated batch"), init: { hide: ["v2"], routing: "v1" },
        steps: [
          S("20초마다 라우팅 표에서 지금 쓸 샌드박스를 확인합니다. 지금은 kata-clh-cpu v1입니다.",
            "Every 20 seconds it reads the routing table. Right now it is kata-clh-cpu v1.",
            { light: ["routing", "trainer"], moves: [{ e: "e_route", c: "ctl" }] }),
          S("미리 준비한 코드 4개를 kata-clh-cpu v1에 보냅니다.", "Four prepared submissions go to kata-clh-cpu v1.",
            { light: ["trainer", "v1"], moves: [{ e: "e_req1", c: "req", n: 3 }] }),
          S("샌드박스가 채점해 결과를 돌려줍니다. 학습은 하지 않고 결과만 기록합니다.", "The sandbox scores them and returns the results. Nothing is trained; the results are logged.",
            { light: ["v1", "trainer"], blocked: true, moves: [{ e: "e_req1", c: "res", n: 3, back: true }] }),
          S("verify.sh와 bench.sh가 gvisor-cpu와 kata-qemu-cpu도 같은 방식으로 검증하고 성능을 측정합니다.",
            "verify.sh and bench.sh check and measure gvisor-cpu and kata-qemu-cpu the same way.",
            { light: ["trainer", "gv", "kq"], moves: [{ e: "e_probe_kq", c: "req" }, { e: "e_probe_gv", c: "req" }] }),
        ],
      },
      switchFlow("kata-clh-cpu", "kata-clh-cpu"),
    ],
  },
];

// ---------- helpers ----------
let lang = "ko";
const ui = { pattern: PATTERNS[0], flow: null, step: 0, playing: false, token: 0 };

function t(key) {
  return UI[lang][key] ?? key;
}

function tr(obj) {
  return obj ? obj[lang] ?? obj.ko : "";
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else node.setAttribute(k, v);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function sv(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, String(v));
  for (const child of children.flat()) {
    if (child === null || child === undefined) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function pathD(pts) {
  return pts.map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join(" ");
}

function pathLength(pts) {
  let len = 0;
  for (let i = 1; i < pts.length; i += 1) len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return len;
}

function pointAt(pts, dist) {
  for (let i = 1; i < pts.length; i += 1) {
    const seg = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    if (dist <= seg || i === pts.length - 1) {
      const p = seg ? Math.min(1, dist / seg) : 1;
      return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * p, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * p];
    }
    dist -= seg;
  }
  return pts[pts.length - 1];
}

// ---------- drawing ----------
function renderDiagram() {
  const p = ui.pattern;
  const svgEl = document.getElementById("ap-svg");
  const title = svgEl.querySelector("title");
  title.textContent = `${p.key}. ${tr(p.name)}`;
  const width = 150 + p.cloudW + (p.nodes.some((n) => n.id === "hf") ? 170 : 30);
  const height = p.height || 720;
  svgEl.setAttribute("viewBox", `0 0 ${Math.max(width, 1280)} ${height}`);
  const defs = sv("defs", {},
    sv("marker", { id: "ap-arrow", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" },
      sv("path", { d: "M0,0 L10,5 L0,10 z", class: "ap-arrowhead" })),
    sv("marker", { id: "ap-arrow-red", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto" },
      sv("path", { d: "M0,0 L10,5 L0,10 z", class: "ap-arrowhead-red" })));
  const layers = { groups: sv("g", {}), edges: sv("g", {}), nodes: sv("g", {}), labels: sv("g", {}), dots: sv("g", { id: "ap-dots" }) };

  layers.groups.append(
    sv("rect", { class: "ap-cloud", x: 150, y: 6, width: p.cloudW, height: height - 20 }),
    sv("image", { href: "icons/aws-cloud.svg", x: 150, y: 6, width: 34, height: 34 }),
    sv("text", { class: "ap-cloud-title", x: 192, y: 30 }, "AWS Cloud"));
  for (const g of p.groups) {
    layers.groups.append(sv("rect", { class: "ap-group", x: g.x, y: g.y, width: g.w, height: g.h }));
    layers.groups.append(sv("text", { class: "ap-group-title", x: g.x + 12, y: g.y + 24 }, tr(g.title)));
    if (g.sub) layers.groups.append(sv("text", { class: "ap-group-sub", x: g.x + 12, y: g.y + 44 }, tr(g.sub)));
  }

  for (const e of p.edges) {
    const g = sv("g", { class: "ap-edge", "data-id": e.id, "data-needs": (e.needs || []).join(" ") });
    g.append(sv("path", { d: pathD(e.pts), class: e.dashed ? "ap-line dashed" : "ap-line", "marker-end": "url(#ap-arrow)" }));
    if (e.label) {
      layers.labels.append(sv("text", { class: "ap-edge-label", x: e.lx, y: e.ly, "text-anchor": e.anchor || "middle",
        "data-edge": e.id }, tr(e.label)));
    }
    layers.edges.append(g);
  }

  if (p.blocked) {
    const b = sv("g", { id: "ap-blocked", class: "ap-blocked" });
    if (b && p.blocked.line) {
      const [[x1, y1], [x2, y2]] = p.blocked.line;
      b.append(sv("line", { class: "ap-blocked-line", x1, y1, x2: x2 - 12, y2 }));
      b.append(sv("line", { class: "ap-blocked-x", x1: x2 - 10, y1: y2 - 10, x2: x2 + 10, y2: y2 + 10 }));
      b.append(sv("line", { class: "ap-blocked-x", x1: x2 - 10, y1: y2 + 10, x2: x2 + 10, y2: y2 - 10 }));
    }
    b.append(sv("text", { class: "ap-blocked-text", x: p.blocked.x, y: p.blocked.y, "text-anchor": "middle" }, tr(p.blocked.text)));
    layers.labels.append(b);
  }

  for (const n of p.nodes) {
    const g = sv("g", { class: "ap-node", "data-id": n.id });
    if (n.icon === "doc") {
      g.append(sv("rect", { class: "ap-doc", x: n.x - 60, y: n.y - 40, width: 120, height: 80, rx: 8 }));
      g.append(sv("text", { class: "ap-doc-title", x: n.x, y: n.y - 12, "text-anchor": "middle" }, tr(n.label)));
      g.append(sv("text", { class: "ap-doc-version", id: "ap-routing-version", x: n.x, y: n.y + 26, "text-anchor": "middle" }, "v1"));
    } else {
      g.append(sv("rect", { class: "ap-halo", x: n.x - ICON / 2 - 8, y: n.y - ICON / 2 - 8, width: ICON + 16, height: ICON + 16, rx: 12 }));
      g.append(sv("image", { href: `icons/${n.icon}.svg`, x: n.x - ICON / 2, y: n.y - ICON / 2, width: ICON, height: ICON }));
      g.append(sv("text", { class: "ap-label", x: n.x, y: n.y + ICON / 2 + 26, "text-anchor": "middle" }, tr(n.label)));
      if (n.sub) g.append(sv("text", { class: "ap-sub", x: n.x, y: n.y + ICON / 2 + 46, "text-anchor": "middle" }, tr(n.sub)));
    }
    layers.nodes.append(g);
  }
  svgEl.replaceChildren(title, defs, layers.groups, layers.edges, layers.labels, layers.nodes, layers.dots);
}

// ---------- state and animation ----------
function stateFor(flow, upto) {
  const hidden = new Set(flow.init?.hide || []);
  const dimmed = new Set();
  let routing = flow.init?.routing || "v1";
  for (let i = 0; i <= upto; i += 1) {
    const s = flow.steps[i];
    for (const id of s.show || []) hidden.delete(id);
    for (const id of s.hide || []) hidden.add(id);
    for (const id of s.dim || []) dimmed.add(id);
    if (s.routing) routing = s.routing;
  }
  return { hidden, dimmed, routing };
}

function applyStep(index) {
  const flow = ui.flow;
  ui.step = index;
  const step = flow.steps[index];
  const { hidden, dimmed, routing } = stateFor(flow, index);
  const lit = new Set(step.light || []);
  const moving = new Set((step.moves || []).map((m) => m.e));
  for (const g of document.querySelectorAll(".ap-node")) {
    const id = g.dataset.id;
    g.classList.toggle("hidden", hidden.has(id));
    g.classList.toggle("dim", dimmed.has(id) && !lit.has(id));
    g.classList.toggle("lit", lit.has(id));
  }
  for (const g of document.querySelectorAll(".ap-edge")) {
    const needs = g.dataset.needs ? g.dataset.needs.split(" ") : [];
    g.classList.toggle("hidden", needs.some((id) => hidden.has(id)));
    g.classList.toggle("active", moving.has(g.dataset.id));
  }
  for (const label of document.querySelectorAll(".ap-edge-label")) {
    const edge = ui.pattern.edges.find((e) => e.id === label.dataset.edge);
    label.classList.toggle("hidden", (edge?.needs || []).some((id) => hidden.has(id)));
    label.classList.toggle("active", moving.has(label.dataset.edge));
  }
  document.getElementById("ap-blocked")?.classList.toggle("flash", Boolean(step.blocked));
  const version = document.getElementById("ap-routing-version");
  if (version) version.textContent = routing;
  drawBadge(step.badge);
  document.getElementById("ap-caption").replaceChildren(
    el("span", { class: "ap-step-no" }, `${t("step")} ${index + 1}/${flow.steps.length}`), " ", tr(step.text));
  for (const li of document.querySelectorAll("#ap-steps li")) {
    li.classList.toggle("current", Number(li.dataset.index) === index);
    li.classList.toggle("done", Number(li.dataset.index) < index);
  }
}

function drawBadge(badge) {
  document.getElementById("ap-badge")?.remove();
  if (!badge) return;
  const n = ui.pattern.nodes.find((x) => x.id === badge.node);
  if (!n) return;
  const text = tr(badge.text);
  const w = Math.max(90, text.length * 15 + 24);
  const y = n.y - ICON / 2 - 46;
  const g = sv("g", { id: "ap-badge", class: "ap-badge" },
    sv("rect", { x: n.x - w / 2, y, width: w, height: 32, rx: 16 }),
    sv("text", { x: n.x, y: y + 22, "text-anchor": "middle" }, text));
  document.getElementById("ap-svg").append(g);
}

function animateMove(move, token) {
  const edge = ui.pattern.edges.find((e) => e.id === move.e);
  if (!edge || REDUCED) return Promise.resolve();
  const pts = move.back ? [...edge.pts].reverse() : edge.pts;
  const len = pathLength(pts);
  const ms = Math.max(700, Math.min(1500, len * 2.2));
  const count = move.n || 1;
  const layer = document.getElementById("ap-dots");
  const runs = [];
  for (let k = 0; k < count; k += 1) {
    runs.push(new Promise((resolve) => {
      const dot = sv("circle", { r: 9, class: "ap-dot" });
      dot.style.fill = COLORS[move.c] || COLORS.req;
      const startAt = performance.now() + k * 220;
      const frame = (now) => {
        if (ui.token !== token) { dot.remove(); resolve(); return; }
        const p = Math.max(0, Math.min(1, (now - startAt) / ms));
        if (now >= startAt && !dot.isConnected) layer.append(dot);
        const [x, y] = pointAt(pts, len * p);
        dot.setAttribute("cx", x);
        dot.setAttribute("cy", y);
        if (p < 1) requestAnimationFrame(frame);
        else { setTimeout(() => dot.remove(), 120); resolve(); }
      };
      requestAnimationFrame(frame);
    }));
  }
  return Promise.all(runs);
}

async function playStep(index, token) {
  applyStep(index);
  for (const move of ui.flow.steps[index].moves || []) {
    if (ui.token !== token) return;
    await animateMove(move, token);
  }
}

async function play() {
  if (ui.playing) { stop(); return; }
  ui.playing = true;
  const token = ++ui.token;
  renderControls();
  let start = ui.step;
  if (start >= ui.flow.steps.length - 1) start = 0;
  try {
    for (let i = start; i < ui.flow.steps.length; i += 1) {
      if (ui.token !== token) return;
      const began = performance.now();
      await playStep(i, token);
      const rest = REDUCED ? 2600 : Math.max(1200, 2800 - (performance.now() - began));
      await sleep(rest);
    }
  } finally {
    if (ui.token === token) { ui.playing = false; renderControls(); }
  }
}

function stop() {
  ui.token += 1;
  ui.playing = false;
  document.getElementById("ap-dots")?.replaceChildren();
  renderControls();
}

function go(delta) {
  stop();
  const next = Math.max(0, Math.min(ui.flow.steps.length - 1, ui.step + delta));
  playStep(next, ui.token);
}

// ---------- page ----------
function renderControls() {
  if (!ui.flow) return;
  const atEnd = ui.step >= ui.flow.steps.length - 1;
  document.getElementById("ap-play").textContent = ui.playing ? t("pause") : atEnd && ui.step > 0 ? t("replay") : t("play");
  document.getElementById("ap-prev").disabled = ui.step === 0;
  document.getElementById("ap-next").disabled = atEnd;
}

function selectFlow(flow) {
  stop();
  ui.flow = flow;
  for (const b of document.querySelectorAll("#ap-flows .tab")) b.setAttribute("aria-selected", String(b.dataset.id === flow.id));
  document.getElementById("ap-steps").replaceChildren(...flow.steps.map((s, i) => {
    const li = el("li", { "data-index": String(i) }, el("button", { type: "button" }, el("span", { class: "n" }, String(i + 1)), tr(s.text)));
    li.firstChild.addEventListener("click", () => { stop(); playStep(i, ui.token); renderControls(); });
    return li;
  }));
  renderDiagram();
  applyStep(0);
  renderControls();
}

function selectPattern(p, flowId) {
  ui.pattern = p;
  for (const b of document.querySelectorAll("#ap-patterns .ap-pattern")) b.setAttribute("aria-selected", String(b.dataset.id === p.id));
  const f = p.facts;
  document.getElementById("ap-summary").replaceChildren(
    el("p", { class: "ap-oneline" }, tr(p.oneLine)),
    el("div", { class: "ap-facts" },
      [["train", f.train], ["sandbox", f.sandbox], ["when", f.when], ["status", f.status]].map(([k, v]) =>
        el("div", { class: `ap-fact ${k}` }, el("div", { class: "k" }, t(k)), el("div", { class: "v" }, tr(v))))));
  document.getElementById("ap-flows").replaceChildren(...p.flows.map((fl) => {
    const b = el("button", { type: "button", class: "tab", role: "tab", "data-id": fl.id }, tr(fl.title));
    b.addEventListener("click", () => selectFlow(fl));
    return b;
  }));
  selectFlow(p.flows.find((fl) => fl.id === flowId) || p.flows[0]);
}

function renderPage() {
  document.documentElement.lang = lang;
  for (const node of document.querySelectorAll("[data-i18n]")) node.textContent = t(node.dataset.i18n);
  document.getElementById("lang").textContent = lang === "ko" ? "EN" : "KO";
  for (const id of ["home-link", "back-link"]) document.getElementById(id).setAttribute("href", `index.html?lang=${lang}`);
  document.getElementById("ap-patterns").replaceChildren(...PATTERNS.map((p) => {
    const b = el("button", { type: "button", class: "ap-pattern", role: "tab", "data-id": p.id },
      el("span", { class: "key" }, p.key), el("span", { class: "name" }, tr(p.name)));
    b.addEventListener("click", () => selectPattern(p));
    return b;
  }));
  document.getElementById("ap-legend").replaceChildren(
    ...[["req", t("legendReq")], ["res", t("legendRes")], ["ctl", t("legendCtl")]].map(([c, label]) => {
      const sw = el("span", { class: "ap-sw" });
      sw.style.background = COLORS[c];
      return el("span", {}, sw, label);
    }),
    el("span", {}, t("legendSolid")), el("span", {}, t("legendDashed")), el("span", { class: "red" }, t("legendBlocked")));
  selectPattern(ui.pattern, ui.flow?.id);
}

function main() {
  const params = new URLSearchParams(window.location.search);
  const wanted = params.get("lang");
  if (wanted === "ko" || wanted === "en") lang = wanted;
  else if (navigator.language && !navigator.language.startsWith("ko")) lang = "en";
  const p = PATTERNS.find((x) => x.id === params.get("pattern"));
  if (p) ui.pattern = p;
  document.getElementById("lang").addEventListener("click", () => {
    stop();
    lang = lang === "ko" ? "en" : "ko";
    renderPage();
  });
  document.getElementById("ap-play").addEventListener("click", play);
  document.getElementById("ap-prev").addEventListener("click", () => go(-1));
  document.getElementById("ap-next").addEventListener("click", () => go(1));
  renderPage();
}

main();
