// Architecture patterns page: draws each deployment pattern as an SVG with AWS icons and replays
// its flows step by step (dots travel along the edges). Everything here is static data written in
// this file; the page makes no network request and inserts every string as text.
"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";
const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const ICON = 72;
const COLORS = { req: "#ff9900", res: "#1a7f37", ctl: "#2f6fde" };
// Arrowheads have one size (14 units long and wide) whatever the line width. The drawn line stops
// TRIM units before the tip, inside the arrowhead, so its square end never shows past the point.
const HEAD = 14;
const TRIM = 6;

const UI = {
  ko: {
    back: "← 데모로 돌아가기", navPatterns: "배포 구성도",
    eyebrow: "Amazon EKS · SageMaker HyperPod",
    title: "학습 노드와 샌드박스 배치",
    lede: "시나리오를 고르면 학습 노드와 채점 풀의 위치를 볼 수 있습니다. 재생 버튼으로 배포 순서와 채점 요청의 경로를 따라가 보세요.",
    flows: "흐름", prev: "◀ 이전", next: "다음 ▶", play: "▶ 재생", pause: "❚❚ 일시정지", replay: "↻ 처음부터",
    train: "trainer 위치", sandbox: "샌드박스 위치", when: "이럴 때 씁니다", status: "AWS 실행",
    legendReq: "채점 요청", legendRes: "채점 결과", legendCtl: "배포, 설정, 이미지",
    legendSolid: "실선: 바로 호출", legendDashed: "점선: 배포나 설정", legendBlocked: "빨간 ✕: 막힌 연결",
    step: "단계",
    footer: "아이콘은 AWS Architecture Icons를 썼습니다. 노드 수와 세부 리소스는 가이드북을 보세요.",
    guide: "가이드북", repo: "GitHub 저장소",
  },
  en: {
    back: "← Back to the demo", navPatterns: "Architecture patterns",
    eyebrow: "Amazon EKS · SageMaker HyperPod",
    title: "Four ways to place the trainer and the sandboxes",
    lede: "Choose a scenario to see where training and scoring run. Play a sequence to follow deployment, a training step, or a sandbox version change.",
    flows: "Flow", prev: "◀ Back", next: "Next ▶", play: "▶ Play", pause: "❚❚ Pause", replay: "↻ From the start",
    train: "Trainer runs on", sandbox: "Sandboxes run on", when: "Use it when", status: "On AWS",
    legendReq: "scoring request", legendRes: "scoring result", legendCtl: "deploy, config, images",
    legendSolid: "solid: direct call", legendDashed: "dashed: deploy or config", legendBlocked: "red ✕: blocked connection",
    step: "Step",
    footer: "Icons are from the AWS Architecture Icons. See the guidebook for node counts and every resource.",
    guide: "Guidebook", repo: "GitHub repository",
  },
};

const L = (ko, en) => ({ ko, en });
const N = (id, icon, x, y, label, sub) => ({ id, icon, x, y, label, sub });
// An edge runs from the edge of one icon to the edge of another. `label` is drawn at (lx, ly), the
// baseline of its last line ("\n" splits lines); `top: true` makes ly the baseline of the first line.
const E = (id, from, to, pts, opts = {}) => ({ id, from, to, pts, ...opts });

// ---------- layout (viewBox units) ----------
// Rows and columns are shared by the four patterns, so the common part stays put when the pattern
// changes. Arrows end on the top, left or right edge of the box around an icon (the one that lights
// up), never under its name, and every label sits where no line or box border runs. Node names
// take the space below that box down to y + 104, which is also where a step's status badge appears.
const W = 1540;
const R = ICON / 2;
const PAD = 8;                                      // the highlight box reaches PAD beyond the icon
const B = R + PAD;                                  // lines start and end on that box, never inside it
const YT = 170, YM = 400, YB = 640;                 // top, main and bottom rows
const X_OP = 70, X_SSM = 271, X_ACC = 430, X_ECR = 370, X_EKS = 667, X_TR = 927, X_SB = 1197, X_SB2 = 1387;
const X_HF = 1459;
const C1 = 787, C2 = 1064;                          // corridors: EKS | trainer and trainer | sandboxes
const BUS = 46;                                     // the image pull line, above every box
const X_PULL = 1301;                                // where it comes down, right of the sandbox nodes
const X_FORK = 1292;                                // pattern C: between the two sandbox columns

// ---------- shared parts ----------
const COMMON_NODES = [
  N("operator", "client", X_OP, YM, L("운영자", "Operator"), L("작업 PC", "workstation")),
  N("ssm", "ssm", X_SSM, YM, L("SSM 터널", "SSM tunnel"), L("Session Manager", "Session Manager")),
  N("access", "ec2", X_ACC, YM, L("접속용 서버", "Access instance"), L("t4g.nano", "t4g.nano")),
  N("eks", "eks", X_EKS, YM, L("EKS API", "EKS API"), L("private 전용", "private only")),
  N("ecr", "ecr", X_ECR, YT, L("ECR", "ECR"), L("이미지 저장소", "image registry")),
  { id: "routing", icon: "doc", x: X_EKS, y: YT, label: L("라우팅 표", "Routing table") },
];
const EGRESS_NODES = [
  N("nat", "nat", X_SB, YB, L("NAT 게이트웨이", "NAT gateway"), L("유일한 출구", "the only way out")),
  N("hf", "internet", X_HF, YB, L("Hugging Face", "Hugging Face"), L("모델 저장소", "model hub")),
];
const PULL_TO_V1 = [[X_ECR + 26, YT - B], [X_ECR + 26, BUS], [X_PULL, BUS], [X_PULL, YM - 20], [X_SB + B, YM - 20]];
const COMMON_EDGES = (pull = { to: "v1", pts: PULL_TO_V1 }) => [
  E("e_tunnel", "operator", "ssm", [[X_OP + B, YM], [X_SSM - B, YM]], { label: L("터널", "tunnel"), lx: 147, ly: YM - 12 }),
  E("e_fwd", "ssm", "access", [[X_SSM + B, YM], [X_ACC - B, YM]], { label: L("포트 전달", "forward"), lx: 351, ly: YM - 16 }),
  E("e_api", "access", "eks", [[X_ACC + B, YM], [X_EKS - B, YM]], { label: L("HTTPS\n443", "HTTPS\n443"), lx: 555, ly: YM - 12 }),
  E("e_push", "operator", "ecr", [[X_OP, YM - B], [X_OP, YT], [X_ECR - B, YT]],
    { dashed: true, label: L("이미지 올리기", "image push"), lx: 231, ly: YT - 12 }),
  E("e_job", "eks", "trainer", [[X_EKS + B, YM], [X_TR - B, YM]], { dashed: true, label: L("Job 배포", "deploy\nJob"), lx: C1, ly: YM - 12 }),
  E("e_cfg", "eks", "routing", [[X_EKS, YM - B], [X_EKS, YT + 40]], { dashed: true }),
  E("e_route", "routing", "trainer", [[X_EKS + 60, YT + 20], [X_TR - 18, YT + 20], [X_TR - 18, YM - B]],
    { dashed: true, label: L("현재 버전", "active\nversion"), lx: C1, ly: YT + 8 }),
  E("e_pull", "ecr", pull.to, pull.pts, { dashed: true, label: L("이미지 받기", "image pull"), lx: 850, ly: BUS - 12 }),
  E("e_req1", "trainer", "v1", [[X_TR + B, YM], [X_SB - B, YM]], { label: L("채점 요청", "score"), lx: C2, ly: YM - 12 }),
  E("e_req2", "trainer", "v2", [[X_TR + 18, YM - B], [X_TR + 18, YT], [X_SB - B, YT]], { dashed: true, needs: ["v2"] }),
];
const EGRESS_EDGES = [
  E("e_model", "trainer", "nat", [[X_TR + B, YM + 16], [C2, YM + 16], [C2, YB], [X_SB - B, YB]],
    { label: L("모델 받기", "model pull"), lx: C2 - 8, ly: 560, anchor: "end" }),
  E("e_hf", "nat", "hf", [[X_SB + B, YB], [X_HF - B, YB]], { label: L("HTTPS", "HTTPS"), lx: 1326, ly: YB - 12 }),
];
// HyperPod patterns: lifecycle scripts uploaded to S3 and read when a node boots.
const S3_NODE = N("s3", "s3", C1, YB, L("S3 시작 스크립트", "S3 lifecycle scripts"), L("비공개 버킷", "private bucket"));
const S3_EDGES = [
  E("e_s3up", "operator", "s3", [[X_OP + B, YM + 18], [136, YM + 18], [136, YB], [C1 - B, YB]],
    { dashed: true, label: L("스크립트 올리기", "upload scripts"), lx: 460, ly: YB - 12 }),
  E("e_boot", "s3", "trainer", [[C1, YB - B], [C1, YM + 20], [X_TR - B, YM + 20]],
    { dashed: true, label: L("부팅 스크립트", "boot scripts"), lx: C1 + 8, ly: 560, anchor: "start" }),
];
const G_SHARED = { x: 290, y: 66, w: 160, h: 216, title: L("공용 서비스", "Shared") };
const G_ACCESS = { x: 196, y: 296, w: 326, h: 216, title: L("운영자 접속", "Operator access") };
const G_EKS = { x: 587, y: 66, w: 160, h: 446, title: L("EKS 클러스터", "EKS cluster") };
const G_EGRESS = { x: 1101, y: 536, w: 180, h: 216, title: L("외부 출구", "Egress") };
const trainerGroup = (title, sub) => ({ x: 827, y: 66, w: 200, h: 446, title, sub });
const sandboxGroup = (title, sub) => ({ x: 1101, y: 66, w: 180, h: 446, title, sub });
const BLOCKED_RIGHT = { line: [[X_SB + B, YM + 20], [1321, YM + 20]], x: 1321, y: YM + 52, top: true,
  text: L("외부 연결\n차단", "egress\nblocked") };

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
      S("채점 결과(정답 여부, 속도)가 trainer로 돌아옵니다.", "The result (correct or not, how fast) comes back to the trainer.",
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
      S("trainer는 지금 배치를 v1에서 마치고, 다음 배치부터 v2로 보냅니다. 한 배치가 두 버전으로 섞이지 않습니다.",
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
    oneLine: L("trainer와 샌드박스를 모두 EKS의 EC2 GPU 노드에 둡니다.", "The trainer and the sandboxes both run on EC2 GPU nodes in EKS."),
    facts: {
      train: L("EC2 g5.2xlarge (A10G 1장)", "EC2 g5.2xlarge (one A10G)"),
      sandbox: L("gVisor 풀, EC2 g5.xlarge 2대", "gVisor pool, two EC2 g5.xlarge"),
      when: L("모든 구성 요소를 직접 관리하고 싶을 때", "You want to manage every part yourself"),
      status: L("GRPO 60스텝 완료. 데모 차트는 별도로 진행한 5스텝 학습을 보여 줍니다.", "60 GRPO steps completed. The replay chart covers a separate five-step run."),
    },
    cloud: { x: 180, w: 1191 }, height: 780,
    nodes: [...COMMON_NODES, ...EGRESS_NODES,
      N("trainer", "container", X_TR, YM, L("GRPO trainer", "GRPO trainer"), L("Qwen2.5-Coder 1.5B", "Qwen2.5-Coder 1.5B")),
      N("v1", "container", X_SB, YM, L("gVisor 풀 v1", "gVisor pool v1"), L("runsc + nvproxy", "runsc + nvproxy")),
      N("v2", "container", X_SB, YT, L("gVisor 풀 v2", "gVisor pool v2"), L("다음 버전", "next version"))],
    edges: [...COMMON_EDGES(), ...EGRESS_EDGES],
    groups: [G_SHARED, G_ACCESS, G_EKS,
      trainerGroup(L("학습 노드", "Trainer node"), L("EC2 g5.2xlarge", "EC2 g5.2xlarge")),
      sandboxGroup(L("샌드박스 노드", "Sandbox nodes"), L("EC2 g5.xlarge x2", "EC2 g5.xlarge x2")),
      G_EGRESS],
    blocked: BLOCKED_RIGHT,
    flows: [
      {
        id: "setup", title: L("준비와 배포", "Setup and deploy"), init: { hide: ["v2"], routing: "v1" },
        steps: [
          S("운영자가 SSM 터널로 private EKS API에 접속합니다. 인터넷에 열린 접속 경로는 없습니다.",
            "The operator reaches the private EKS API through an SSM tunnel. Nothing is open to the internet.",
            { light: ["operator", "ssm", "access", "eks"], moves: TUNNEL }),
          S("trainer와 샌드박스 이미지를 만들어 ECR에 올립니다.", "The trainer and sandbox images are built and pushed to ECR.",
            { light: ["operator", "ecr"], moves: [{ e: "e_push", c: "ctl" }] }),
          S("샌드박스 노드가 ECR에서 이미지를 받아 gVisor 풀을 띄웁니다.", "The sandbox nodes pull the image from ECR and start the gVisor pool.",
            { light: ["ecr", "v1"], moves: [{ e: "e_pull", c: "ctl" }] }),
          S("학습 Job을 배포하면 EKS가 학습 노드에 trainer를 띄우고 라우팅 표를 연결합니다.",
            "Deploying the training Job makes EKS start the trainer on its node and mount the routing table.",
            { light: ["eks", "trainer", "routing"], moves: [{ e: "e_job", c: "ctl" }, { e: "e_route", c: "ctl" }] }),
          S("trainer가 NAT를 거쳐 Hugging Face에서 모델을 받습니다.", "The trainer downloads the model from Hugging Face through the NAT gateway.",
            { light: ["trainer", "nat", "hf"], moves: [{ e: "e_model", c: "ctl" }, { e: "e_hf", c: "ctl" }] }),
        ],
      },
      scoringFlow("gVisor 풀", "gVisor pool"),
      switchFlow("gVisor 풀", "gVisor pool"),
    ],
  },
  {
    id: "b1", key: "B1", name: L("HyperPod 학습", "HyperPod training"),
    oneLine: L("trainer만 SageMaker HyperPod로 옮기고, 샌드박스는 A와 같은 EC2 노드에 둡니다.",
      "Only the trainer moves to SageMaker HyperPod; the sandboxes stay on the same EC2 nodes as in A."),
    facts: {
      train: L("HyperPod ml.g5.2xlarge", "HyperPod ml.g5.2xlarge"),
      sandbox: L("gVisor 풀, EC2 g5.xlarge 2대", "gVisor pool, two EC2 g5.xlarge"),
      when: L("긴 학습에서 노드 자동 교체와 Job 재시작이 필요할 때", "Long training runs need automatic node replacement and Job restarts"),
      status: L("GRPO 1스텝, 생성 코드 12개 채점", "1 GRPO step, 12 generated submissions scored"),
    },
    cloud: { x: 180, w: 1191 }, height: 780,
    nodes: [...COMMON_NODES, ...EGRESS_NODES, S3_NODE,
      N("trainer", "sagemaker", X_TR, YM, L("HyperPod trainer", "HyperPod trainer"), L("HyperPodPyTorchJob", "HyperPodPyTorchJob")),
      N("v1", "container", X_SB, YM, L("gVisor 풀 v1", "gVisor pool v1"), L("runsc + nvproxy", "runsc + nvproxy")),
      N("v2", "container", X_SB, YT, L("gVisor 풀 v2", "gVisor pool v2"), L("다음 버전", "next version"))],
    edges: [...COMMON_EDGES(), ...EGRESS_EDGES, ...S3_EDGES],
    groups: [G_SHARED, G_ACCESS, G_EKS,
      trainerGroup(L("HyperPod 학습", "HyperPod trainer"), L("ml.g5.2xlarge", "ml.g5.2xlarge")),
      sandboxGroup(L("샌드박스 노드", "Sandbox nodes"), L("EC2 g5.xlarge x2", "EC2 g5.xlarge x2")),
      G_EGRESS],
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
          S("HyperPod가 S3의 시작 스크립트로 학습 노드를 부팅합니다. 노드가 작업을 받을 준비를 마치면 training operator가 시작됩니다.",
            "HyperPod boots the trainer node with the scripts from S3. The training operator starts once the node is schedulable.",
            { light: ["s3", "trainer"], moves: [{ e: "e_boot", c: "ctl" }] }),
          S("샌드박스 노드(EC2)가 ECR에서 이미지를 받아 gVisor 풀을 띄웁니다.", "The sandbox nodes (EC2) pull the image from ECR and start the gVisor pool.",
            { light: ["ecr", "v1"], moves: [{ e: "e_pull", c: "ctl" }] }),
          S("학습 Job(HyperPodPyTorchJob)을 배포하면 HyperPod 노드에 trainer가 뜨고 라우팅 표가 연결됩니다.",
            "Deploying the HyperPodPyTorchJob starts the trainer on the HyperPod node with the routing table mounted.",
            { light: ["eks", "trainer", "routing"], moves: [{ e: "e_job", c: "ctl" }, { e: "e_route", c: "ctl" }] }),
          S("trainer가 NAT를 거쳐 Hugging Face에서 모델을 받습니다.", "The trainer downloads the model from Hugging Face through the NAT gateway.",
            { light: ["trainer", "nat", "hf"], moves: [{ e: "e_model", c: "ctl" }, { e: "e_hf", c: "ctl" }] }),
        ],
      },
      scoringFlow("gVisor 풀", "gVisor pool"),
      switchFlow("gVisor 풀", "gVisor pool"),
    ],
  },
  {
    id: "b2", key: "B2", name: L("CPU와 GPU 모두 HyperPod", "All workers on HyperPod"),
    oneLine: L("EKS가 Pod를 배치하고, HyperPod의 세 인스턴스 그룹이 시스템 작업과 모델 학습, 코드 채점을 나눠 맡습니다.",
      "EKS schedules the pods. Three HyperPod instance groups run cluster services, model training and code grading."),
    facts: {
      train: L("HyperPod ml.g5.2xlarge", "HyperPod ml.g5.2xlarge"),
      sandbox: L("gVisor 풀, HyperPod ml.g5.xlarge 2대", "gVisor pool, two HyperPod ml.g5.xlarge"),
      when: L("시스템 CPU와 GPU 워커를 모두 HyperPod에서 운영할 때", "Manage both CPU and GPU workers through HyperPod"),
      status: L("GRPO 한 스텝 완료 · 벤치마크 64/64 성공", "One GRPO step completed · 64/64 benchmark requests passed"),
    },
    cloud: { x: 180, w: 1320 }, height: 800,
    nodes: [...COMMON_NODES.filter((n) => ["operator", "ecr", "routing"].includes(n.id)), S3_NODE,
      N("eks", "eks", X_EKS, YM, L("EKS API", "EKS API"), L("제어 영역", "control plane")),
      N("system", "sagemaker", X_ACC, YM, L("시스템 CPU", "System CPU"), L("CoreDNS", "CoreDNS")),
      N("trainer", "sagemaker", X_TR, YM, L("HyperPod trainer", "HyperPod trainer"), L("HyperPodPyTorchJob", "HyperPodPyTorchJob")),
      N("v1", "container", X_SB, YM, L("gVisor 풀 v1", "gVisor pool v1"), L("A10G × 2", "2 × A10G")),
      N("v2", "container", X_SB, YT, L("gVisor 풀 v2", "gVisor pool v2"), L("다음 버전", "next version"))],
    edges: [...COMMON_EDGES().filter((e) => !["e_tunnel", "e_fwd", "e_api"].includes(e.id)), ...S3_EDGES,
      E("e_managed_api", "operator", "eks", [[X_OP + B, YM], [155, YM], [155, 558], [565, 558], [565, YM + 18], [X_EKS - B, YM + 18]],
        { dashed: true, label: L("IAM 인증", "IAM authentication"), lx: 356, ly: 547 }),
      E("e_system", "eks", "system", [[X_EKS - B, YM - 12], [X_ACC + B, YM - 12]], { dashed: true }),
      E("e_boot2", "s3", "v1", [[C1 + B, YB - 18], [C2, YB - 18], [C2, YM + 20], [X_SB - B, YM + 20]], { dashed: true })],
    groups: [G_SHARED, { x: 324, y: 296, w: 215, h: 216, title: L("HyperPod system", "HyperPod system"), sub: L("ml.m5.xlarge", "ml.m5.xlarge") }, G_EKS,
      trainerGroup(L("HyperPod 학습", "HyperPod trainer"), L("ml.g5.2xlarge", "ml.g5.2xlarge")),
      sandboxGroup(L("HyperPod 채점", "HyperPod graders"), L("ml.g5.xlarge × 2", "2 × ml.g5.xlarge"))],
    blocked: BLOCKED_RIGHT,
    flows: [
      {
        id: "setup", title: L("준비와 배포", "Setup and deploy"), init: { hide: ["v2"], routing: "v1" },
        steps: [
          S("HyperPod EKS 마법사가 EKS와 세 워커 그룹을 만듭니다. CoreDNS는 시스템 CPU에서 실행됩니다.",
            "The HyperPod wizard provisions EKS and three worker groups. CoreDNS runs on the system CPU worker.",
            { light: ["operator", "eks", "system", "trainer", "v1"], moves: [{ e: "e_managed_api", c: "ctl" }, { e: "e_system", c: "ctl" }] }),
          S("S3의 시작 스크립트가 gVisor를 준비합니다. 지원 드라이버를 설치한 채점 노드는 HyperPod에서 재부팅합니다.",
            "The S3 lifecycle scripts prepare gVisor. The grading workers reboot through HyperPod to activate the supported driver.",
            { light: ["operator", "s3", "v1"], moves: [{ e: "e_s3up", c: "ctl" }, { e: "e_boot2", c: "ctl" }] }),
          S("학습과 채점 Pod가 ECR 이미지를 받아 시작합니다. 두 채점 Pod에는 A10G가 한 장씩 배정됩니다.",
            "The trainer and graders start from ECR images. Each grading pod gets one A10G.",
            { light: ["ecr", "v1", "eks", "trainer"], moves: [{ e: "e_pull", c: "ctl" }, { e: "e_job", c: "ctl" }] }),
        ],
      },
      scoringFlow("HyperPod 채점 풀", "HyperPod grading pool"),
      {
        id: "bench", title: L("벤치마크", "Benchmark"), init: { hide: ["v2"], routing: "v1" },
        steps: [
          S("학습이 끝나면 시스템 CPU가 Triton 커널 32개를 두 채점 Pod에 보냅니다. 32건 모두 성공했습니다.",
            "After training, the CPU worker sends 32 evaluations to the two grading pods. All 32 succeeded.",
            { light: ["system", "v1"] }),
          S("학습 노드에서도 같은 요청 32건을 보냅니다. 두 Job의 실행 시간은 겹치지 않습니다.",
            "The trainer node then sends the same 32 evaluations. The two benchmark jobs run in sequence.",
            { light: ["trainer", "v1"], moves: [{ e: "e_req1", c: "req" }] }),
        ],
      },
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
      status: L("v1↔v2 전환, Kata CLH CPU에서 3턴 에피소드 2개 완료", "v1↔v2 rollout and two three-turn episodes on Kata CLH CPU"),
    },
    cloud: { x: 180, w: 1317 }, height: 650,
    nodes: [...COMMON_NODES,
      N("trainer", "container", X_TR, YM, L("모의 학습 Job", "Simulate Job"), L("모델 없음", "no model")),
      N("v1", "container", X_SB, YM, L("kata-clh-cpu v1", "kata-clh-cpu v1"), L("Kata + CLH", "Kata + CLH")),
      N("v2", "container", X_SB, YT, L("kata-clh-cpu v2", "kata-clh-cpu v2"), L("다음 버전", "next version")),
      N("gv", "container", X_SB2, YT, L("gvisor-cpu", "gvisor-cpu"), L("gVisor", "gVisor")),
      N("kq", "container", X_SB2, YM, L("kata-qemu-cpu", "kata-qemu-cpu"), L("Kata + QEMU", "Kata + QEMU"))],
    edges: [...COMMON_EDGES({ to: "gv", pts: [[X_ECR + 26, YT - B], [X_ECR + 26, BUS], [X_SB2, BUS], [X_SB2, YT - B]] }),
      // verify.sh and bench.sh: one line that splits between the two sandbox columns.
      E("e_probe_kq", "trainer", "kq", [[X_TR + B, YM + 16], [C2, YM + 16], [C2, 530], [X_FORK, 530], [X_FORK, YM + 16], [X_SB2 - B, YM + 16]],
        { dashed: true, label: L("검증, 성능 측정", "verify, benchmark"), lx: 1180, ly: 552, top: true }),
      E("e_probe_gv", "trainer", "gv", [[X_TR + B, YM + 16], [C2, YM + 16], [C2, 530], [X_FORK, 530], [X_FORK, YT + 16], [X_SB2 - B, YT + 16]],
        { dashed: true, fork: "e_probe_kq" })],
    groups: [G_SHARED, G_ACCESS, G_EKS,
      trainerGroup(L("system 노드", "System node"), L("m6i.large", "m6i.large")),
      { x: 1101, y: 66, w: 376, h: 446, title: L("c8i.2xlarge 노드", "c8i.2xlarge node"), sub: L("CPU 샌드박스 4개, nested virt", "four CPU sandboxes, nested virt") }],
    blocked: { x: 1260, y: 600, text: L("✕ 샌드박스에서 밖으로 나가는 연결은 모두 차단", "✕ every outbound connection from a sandbox is blocked") },
    flows: [
      {
        id: "setup", title: L("준비와 배포", "Setup and deploy"), init: { hide: ["v2"], routing: "v1" },
        steps: [
          S("운영자가 SSM 터널로 private EKS API에 접속합니다.", "The operator reaches the private EKS API through an SSM tunnel.",
            { light: ["operator", "ssm", "access", "eks"], moves: TUNNEL }),
          S("샌드박스 이미지와 도구 이미지만 ECR에 올립니다.", "Only the sandbox and tool images go to ECR.",
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

// A text element whose "\n"-separated lines are tspans 18 units apart. By default (x, y) is the
// baseline of the last line, so a label above a line grows upward; with top it is the first line.
function lines(attrs, text, top = false) {
  const parts = text.split("\n");
  const node = sv("text", attrs);
  parts.forEach((part, i) => node.append(sv("tspan", { x: attrs.x, dy: i ? 18 : top ? 0 : -18 * (parts.length - 1) }, part)));
  return node;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function pathD(pts) {
  return pts.map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join(" ");
}

// The same polyline with its last point moved `by` units back along the last segment.
function trimEnd(pts, by) {
  const out = pts.map((pt) => [...pt]);
  const [ax, ay] = out[out.length - 2], end = out[out.length - 1];
  const len = Math.hypot(end[0] - ax, end[1] - ay);
  end[0] -= ((end[0] - ax) / len) * by;
  end[1] -= ((end[1] - ay) / len) * by;
  return out;
}

// Dashes of about 8 on, 6 off, stretched a little so the line starts and ends with a dash: the
// arrowhead then always sits on a dash instead of floating after a gap.
function dashesFor(len) {
  const n = Math.max(1, Math.round((len - 8) / 14));
  const period = len / (n + 8 / 14);
  return `${((period * 8) / 14).toFixed(2)} ${((period * 6) / 14).toFixed(2)}`;
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
  const height = p.height;
  svgEl.setAttribute("viewBox", `0 0 ${W} ${height}`);
  // The arrowhead tip lands on the edge of the target icon: the line ends TRIM units short of it.
  const marker = (id, cls) => sv("marker", { id, viewBox: "0 0 10 10", refX: 10 - (TRIM * 10) / HEAD, refY: 5,
    markerUnits: "userSpaceOnUse", markerWidth: HEAD, markerHeight: HEAD, orient: "auto-start-reverse" },
  sv("path", { d: "M0,0 L10,5 L0,10 z", class: cls }));
  // A second, darker arrowhead for the line that is moving (style.css switches marker-end).
  const defs = sv("defs", {}, marker("ap-arrow", "ap-arrowhead"), marker("ap-arrow-active", "ap-arrowhead active"));
  // Halos sit under the lines, so a highlighted node never covers the arrowheads that reach it.
  const layers = { groups: sv("g", {}), halos: sv("g", {}), edges: sv("g", {}), nodes: sv("g", {}), labels: sv("g", {}),
    dots: sv("g", { id: "ap-dots" }) };

  const c = p.cloud;
  layers.groups.append(
    sv("rect", { class: "ap-cloud", x: c.x, y: 6, width: c.w, height: height - 20 }),
    sv("image", { href: "icons/aws-cloud.svg", x: c.x, y: 6, width: 34, height: 34 }),
    sv("text", { class: "ap-cloud-title", x: c.x + 42, y: 30 }, "AWS Cloud"));
  for (const g of p.groups) {
    layers.groups.append(sv("rect", { class: "ap-group", x: g.x, y: g.y, width: g.w, height: g.h }));
    layers.groups.append(sv("text", { class: "ap-group-title", x: g.x + 12, y: g.y + 24 }, tr(g.title)));
    if (g.sub) layers.groups.append(sv("text", { class: "ap-group-sub", x: g.x + 12, y: g.y + 44 }, tr(g.sub)));
  }

  for (const e of p.edges) {
    const g = sv("g", { class: "ap-edge", "data-id": e.id, "data-needs": (e.needs || []).join(" ") });
    const pts = trimEnd(e.pts, TRIM);
    const line = sv("path", { d: pathD(pts), class: e.dashed ? "ap-line dashed" : "ap-line", "marker-end": "url(#ap-arrow)" });
    if (e.dashed) line.style.strokeDasharray = dashesFor(pathLength(pts));
    g.append(line);
    if (e.label) {
      layers.labels.append(lines({ class: "ap-edge-label", x: e.lx, y: e.ly, "text-anchor": e.anchor || "middle",
        "data-edge": e.id }, tr(e.label), e.top));
    }
    layers.edges.append(g);
  }

  if (p.blocked) {
    const b = sv("g", { id: "ap-blocked", class: "ap-blocked" });
    if (p.blocked.line) {
      const [[x1, y1], [x2, y2]] = p.blocked.line;
      b.append(sv("line", { class: "ap-blocked-line", x1, y1, x2: x2 - 12, y2 }));
      b.append(sv("line", { class: "ap-blocked-x", x1: x2 - 10, y1: y2 - 10, x2: x2 + 10, y2: y2 + 10 }));
      b.append(sv("line", { class: "ap-blocked-x", x1: x2 - 10, y1: y2 + 10, x2: x2 + 10, y2: y2 - 10 }));
    }
    b.append(lines({ class: "ap-blocked-text", x: p.blocked.x, y: p.blocked.y, "text-anchor": "middle" }, tr(p.blocked.text), p.blocked.top));
    layers.labels.append(b);
  }

  for (const n of p.nodes) {
    const g = sv("g", { class: "ap-node", "data-id": n.id });
    if (n.icon === "doc") {
      g.append(sv("rect", { class: "ap-doc", x: n.x - 60, y: n.y - 40, width: 120, height: 80, rx: 8 }));
      g.append(sv("text", { class: "ap-doc-title", x: n.x, y: n.y - 12, "text-anchor": "middle" }, tr(n.label)));
      g.append(sv("text", { class: "ap-doc-version", id: "ap-routing-version", x: n.x, y: n.y + 26, "text-anchor": "middle" }, "v1"));
    } else {
      layers.halos.append(sv("rect", { class: "ap-halo", "data-id": n.id, x: n.x - B, y: n.y - B, width: 2 * B, height: 2 * B, rx: 12 }));
      g.append(sv("image", { href: `icons/${n.icon}.svg`, x: n.x - R, y: n.y - R, width: ICON, height: ICON }));
      g.append(sv("text", { class: "ap-label", x: n.x, y: n.y + B + 26, "text-anchor": "middle" }, tr(n.label)));
      if (n.sub) g.append(sv("text", { class: "ap-sub", x: n.x, y: n.y + B + 46, "text-anchor": "middle" }, tr(n.sub)));
    }
    layers.nodes.append(g);
  }
  svgEl.replaceChildren(title, defs, layers.groups, layers.halos, layers.edges, layers.labels, layers.nodes, layers.dots);
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
  for (const g of document.querySelectorAll(".ap-node, .ap-halo")) {
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

// The status badge takes the place of the node's second line (under its name), the one spot that
// no line ever crosses.
function drawBadge(badge) {
  document.getElementById("ap-badge")?.remove();
  for (const g of document.querySelectorAll(".ap-node.badged")) g.classList.remove("badged");
  if (!badge) return;
  const n = ui.pattern.nodes.find((x) => x.id === badge.node);
  const host = document.querySelector(`.ap-node[data-id="${badge.node}"]`);
  if (!n || !host) return;
  host.classList.add("badged");
  const y = n.y + B + 35;
  const text = sv("text", { x: n.x, y: y + 17, "text-anchor": "middle" }, tr(badge.text));
  const g = sv("g", { id: "ap-badge", class: "ap-badge" }, text);
  host.append(g);
  const w = text.getComputedTextLength() + 26;
  g.prepend(sv("rect", { x: n.x - w / 2, y, width: w, height: 24, rx: 12 }));
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
  syncAddress();
  for (const b of document.querySelectorAll("#ap-patterns .ap-pattern")) b.setAttribute("aria-selected", String(b.dataset.id === p.id));
  const f = p.facts;
  document.getElementById("ap-summary").replaceChildren(
    el("p", { class: "ap-oneline" }, tr(p.oneLine)),
    el("div", { class: "ap-facts" },
      [["train", f.train], ["sandbox", f.sandbox], ["when", f.when], ["status", f.status]].map(([k, v]) =>
        el("div", { class: `ap-fact ${k}` }, el("div", { class: "k" }, t(k)), el("div", { class: "v" }, tr(v))))));
  if (p.id === "b1") {
    const url = `index.html${lang === "en" ? "?lang=en" : ""}#hyperpod-b1`;
    document.querySelector("#ap-summary .status").append(
      el("a", { href: url }, tr(L("B1 벤치마크 보기 →", "View the B1 benchmark →"))));
  }
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
  for (const id of ["home-link", "back-link"]) document.getElementById(id).setAttribute("href", lang === "en" ? "index.html?lang=en" : "index.html");
  document.getElementById("self-link").setAttribute("href", lang === "en" ? "architecture.html?lang=en" : "architecture.html");
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

// Korean is the default; ?lang=en (or the EN button) switches to English. The language and the
// pattern on screen are kept in the address, so a reload or a shared link opens the same view.
function syncAddress() {
  const url = new URL(window.location.href);
  if (lang === "ko") url.searchParams.delete("lang");
  else url.searchParams.set("lang", lang);
  if (ui.pattern === PATTERNS[0]) url.searchParams.delete("pattern");
  else url.searchParams.set("pattern", ui.pattern.id);
  if (url.href !== window.location.href) window.history.replaceState(null, "", url);
}

function main() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("lang") === "en") lang = "en";
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
