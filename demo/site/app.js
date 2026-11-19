// Replay demo: renders data/recording.json (golden verdicts) and data/extras.json (benchmark,
// training, terminal transcripts). No network calls other than those two same-origin fetches.
// Every value from the data files is inserted as text (never as HTML), because they contain
// strings produced by evaluated code and by cluster logs.
"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";
const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const WEIGHTS = { format: 0.1, correctness: 1.0, speedup: 0.5 };
const MAX_REWARD = 0.1 + 1.0 + 0.5 * 1.5;

const TEXT = {
  ko: {
    navArch: "구조", navTry: "채점해 보기", navDefense: "공격 차단", navTrain: "학습", navBench: "성능 비교",
    navPatterns: "패턴별 아키텍처", patternsLink: "패턴별 아키텍처 자세히 보기 →",
    ctaPatterns: "▶ 패턴별 아키텍처 보기",
    bannerTitle: "패턴별 아키텍처: 움직이는 구성도",
    bannerDesc: "학습기와 샌드박스를 어디에 두는지 네 가지 패턴(A, B1, B2, C)으로 보여 줍니다. 요청과 결과가 선을 따라 움직여요.",
    bannerGo: "구성도 열기 →",
    eyebrow: "강화학습용 GPU 코드 채점 샌드박스",
    title: "AI가 쓴 GPU 코드를 안전하게 채점합니다",
    lede: "강화학습을 하는 동안 모델은 계속 새로운 GPU 코드(Triton, CUDA)를 만듭니다. 믿을 수 없는 코드라서 격리된 환경에서 실행해야 해요. 이 페이지는 Amazon EKS에서 gVisor와 Kata Containers로 실제 채점한 기록을 다시 보여 줍니다. 클러스터나 GPU에 직접 연결하지는 않습니다.",
    ctaTry: "채점 장면 보기", ctaDefense: "공격 차단 결과 보기",
    sourceLabel: "기록 출처:",
    videoCaption: "2분 소개 영상입니다. 이 페이지의 기능을 순서대로 보여 줍니다(소리 없음).",
    kpiGpu: "GPU 격리 방식 (gVisor, Kata)", kpiGolden: "예상대로 나온 채점 결과",
    kpiBlocked: "샌드박스 안에서 막힌 접근 시도", kpiBench: "성능 측정 요청 중 성공",
    sArch: "구조: 채점 요청 하나가 지나가는 길",
    sArchHint: "상자를 누르면 설명이 나옵니다. 재생 버튼을 누르면 채점 요청 하나가 어디를 거치는지 차례로 보여 줍니다.",
    flowPlay: "▶ 요청 흐름 보기", flowStop: "■ 멈춤", evidence: "실제 기록 보기",
    zoneTrainer: "학습 영역 (rl-trainer)", zoneSandbox: "샌드박스 영역 (기본 차단)", zoneOut: "샌드박스에서 접근 불가",
    sTry: "채점해 보기: 같은 코드, 두 가지 샌드박스",
    sTryHint: "제출 코드를 고르고 재생을 누르세요. gVisor(A10G GPU)와 Kata(T4 GPU)가 같은 코드를 채점한 기록이 나란히 재생됩니다.",
    showTask: "문제와 정답 코드 보기", candidate: "제출된 코드",
    run: "▶ 채점 재생", running: "재생 중...",
    speed: "속도", speed1: "실제 속도", speed4: "4배 빠르게", speed0: "결과만 보기",
    laneNote: "막대가 차는 시간은 실제 채점에 걸린 시간입니다. 단계별 시간은 기록하지 않아서, 단계 표시는 채점이 끝난 뒤 한꺼번에 채워집니다.",
    stAuth: "요청 확인 (인증 토큰, 네트워크 정책)", stPolicy: "코드 사전 검사 (금지된 기능 사용 여부)",
    stRun: "격리된 프로세스에서 실행", stCorrect: "정답 코드와 결과 비교 (무작위 입력)",
    stBench: "속도 측정, 측정 중에도 결과 확인", stReward: "점수(reward) 계산",
    idle: "대기 중", evaluating: "채점 중",
    expected: "예상 결과", speedupL: "속도 향상", msL: "정답/제출 실행 시간 (ms)", violationsL: "금지된 사용", flagsL: "감지된 문제",
    rewardTotal: "점수 합계", rewardMax: "만점", rFormat: "형식 x0.1", rCorrect: "정확도 x1.0", rSpeed: "속도 x0.5",
    excluded: "샌드박스 오류: 이 결과는 점수 비교에서 뺍니다",
    why_ok_custom: "정답이고, 직접 작성한 GPU 커널입니다. 정답 코드보다 빠른 만큼 속도 점수도 받습니다.",
    why_ok_plain: "정답이지만 PyTorch 기본 연산만 썼습니다. 직접 만든 커널이 아니라서 정확도 점수는 0.3만 받고 속도 점수는 없어요.",
    why_policy: "실행하기 전 사전 검사에서 막혔습니다. 코드는 한 줄도 실행되지 않았어요.",
    why_wrong: "결과가 정답과 다릅니다.",
    why_cheat: "처음 확인할 때는 정답을 냈지만, 속도를 재는 동안 결과가 달라져서 잡혔습니다.",
    why_runtime: "실행 중에 오류가 났습니다.",
    why_infra: "샌드박스 쪽 문제라서 점수를 매기지 않습니다.",
    sDefense: "공격 차단: 샌드박스 안에서 해 본 시도",
    sDefenseHint: "검증 스크립트(verify.sh)가 샌드박스 안에서 실제로 시도한 결과입니다. 카드를 누르면 아래 터미널 기록에서 해당 줄을 찾아 표시합니다.",
    attacks: "시도한 공격과 결과",
    termPlay: "▶ 재생", termPause: "❚❚ 일시정지", termAll: "전체 보기",
    runtime: "런타임", version: "샌드박스 버전", kernel: "샌드박스 커널", nodeKernel: "서버 커널",
    gpu: "GPU", egress: "외부 연결 차단", yes: "확인됨", no: "열려 있음", none: "없음 (CPU)",
    sTrain: "학습: 채점 결과가 점수가 되기까지",
    sTrainHint: "위 그래프는 실제 모델을 GPU에서 5 step 학습한 기록입니다. 아래 그래프는 학습 도중 샌드박스 버전을 바꾼 기록이에요.",
    grpoTitle: "GRPO 학습 5 step: 모델이 쓴 코드를 gVisor(A10G)가 채점",
    stepPlay: "▶ step 순서대로 보기",
    grpoNote: "동작 확인용으로 5 step만 돌렸기 때문에, 모델이 좋아지는지를 보여 주는 결과는 아닙니다. 모델이 쓴 코드가 어떤 채점 결과를 받고 점수가 어떻게 나오는지를 보여 줍니다.",
    lPass: "통과율 (오른쪽 눈금, 0~1)", lReward: "평균 점수 (오른쪽 눈금)",
    st_ok: "통과", st_wrong_answer: "오답", st_compile_error: "컴파일 오류", st_runtime_error: "실행 오류",
    st_timeout: "시간 초과", st_policy_violation: "사전 검사 위반", st_sandbox_error: "샌드박스 오류",
    flag_timed_output_mismatch: "측정 중 결과가 달라짐", flag_gpu_fault: "GPU 오류", blockedChip: "차단",
    batch: "배치", step: "step", evals: "채점 수", passRate: "통과율", customRate: "직접 만든 커널 비율",
    meanSpeedup: "평균 속도 향상", evalTimes: "채점 시간 (중앙값 / p95)", evalMedian: "채점 시간 중앙값", wall: "배치 전체 시간",
    rewardMean: "평균 점수", rewardStd: "점수 표준편차", loss: "loss", compLen: "평균 답변 길이 (token)",
    stepTime: "step 시간", sec: "초", model: "모델", sandboxSide: "샌드박스", trainerSide: "학습기 (trainer)",
    switchTitle: "학습 중 샌드박스 버전 바꾸기 (v1 → v2)",
    switchNote: "모의 실행입니다. 모델 대신 미리 준비한 코드로 채점했고, 실제 학습은 하지 않았습니다. 채점 방식과 버전을 바꾸는 방식은 실제 학습과 같아요.",
    showRollout: "버전 전환 터미널 기록 보기",
    simSummary: "배치 {n}개가 하나도 빠지지 않고 채점됐습니다. step {s}에서 {from}에서 {to}로 바뀌었고, 채점 시간 중앙값은 바꾸기 전 {a}초, 바꾼 뒤 {b}초입니다.",
    sBench: "성능 비교: 런타임별 측정 결과",
    sBenchHint: "샌드박스마다 같은 코드를 32번씩 채점했습니다. 막대에 마우스를 올리면 자세한 값이 나옵니다.",
    mP50: "채점 시간 중앙값 (초)", mP95: "채점 시간 p95 (초)", mCold: "시작 시간 (초, pod 중앙값)",
    mTput: "pod 하나의 초당 채점 수", mSpeed: "속도 향상 중앙값 (GPU)",
    pass2: "이미지를 받아 둔 뒤 (기준)", pass1: "처음 배포했을 때",
    notMeasured: "측정 못 함: VM이 시작되지 않음", na: "해당 없음",
    pods: "준비된 pod", requests: "요청", throughput: "처리량", refMs: "정답 코드 실행 시간 (ms)",
    benchNoteGpu: "GPU 샌드박스 두 개는 GPU 종류가 다릅니다(A10G와 T4). 그래서 이 차이를 gVisor와 Kata의 성능 차이로 보면 안 됩니다. CPU 샌드박스 세 개는 같은 서버(c8i.2xlarge)에서 같은 조건으로 측정했습니다.",
    benchNotePass1: "처음 배포했을 때의 시작 시간에는 다른 시간이 섞여 있습니다. kata-qemu의 약 1235초에는 설정을 고치기 전 VM 시작에 실패하던 약 20분이 들어 있고, gvisor-cpu의 141초에는 이미지를 처음 내려받은 시간이 들어 있어요.",
    benchNoteSpeed: "CPU 샌드박스는 속도 향상을 비교하지 않아서 표시하지 않습니다.",
    noData: "이 기록에는 이 부분의 데이터가 없습니다.",
    footer: "실제 실행 기록을 다시 보여 주는 데모입니다. 수치는 위에 적힌 환경에서 나온 값이라 다른 환경에서는 달라질 수 있습니다. 로그에 있던 IP 주소와 서버 이름은 가렸습니다.",
    guide: "가이드북", repo: "GitHub 저장소",
  },
  en: {
    navArch: "Architecture", navTry: "Try scoring", navDefense: "Attacks blocked", navTrain: "Training", navBench: "Benchmark",
    navPatterns: "Architecture patterns", patternsLink: "See the architecture patterns →",
    ctaPatterns: "▶ See the architecture patterns",
    bannerTitle: "Architecture patterns: animated diagrams",
    bannerDesc: "Four ways (A, B1, B2, C) to place the trainer and the sandboxes. Requests and results move along the lines.",
    bannerGo: "Open the diagrams →",
    eyebrow: "GPU reward sandboxes for on-policy RL",
    title: "Score model-written GPU code in isolated sandboxes",
    lede: "During reinforcement learning, a model writes untrusted Triton and CUDA code at every step. This page replays real records of that code being scored on Amazon EKS with gVisor and Kata Containers. Your browser never connects to a cluster or a GPU.",
    ctaTry: "Try scoring", ctaDefense: "See blocked attacks",
    sourceLabel: "Recording source:",
    videoCaption: "Tour video: this page playing its features automatically (no sound).",
    kpiGpu: "GPU isolation runtimes (gVisor, Kata)", kpiGolden: "golden verdicts matching the expected one",
    kpiBlocked: "access attempts from inside a sandbox, blocked", kpiBench: "benchmark requests answered ok",
    sArch: "Architecture: the path of one reward request",
    sArchHint: "Click a component to open its description. The play button shows the order in which one reward request travels.",
    flowPlay: "▶ Play request flow", flowStop: "■ Stop", evidence: "See evidence",
    zoneTrainer: "rl-trainer namespace", zoneSandbox: "sandbox namespace (default deny)", zoneOut: "Blocked from sandboxes",
    sTry: "Try scoring: the same code in two sandboxes",
    sTryHint: "Pick a submission and press play: the records of gVisor (A10G) and Kata QEMU (T4) scoring the same code replay side by side.",
    showTask: "Show the task and reference", candidate: "Submitted code",
    run: "▶ Replay scoring in both sandboxes", running: "Replaying...",
    speed: "Speed", speed1: "real time", speed4: "4x", speed0: "result only",
    laneNote: "The progress bar replays the recorded total evaluation time (duration_s). Per-stage times were not recorded, so the stages are filled in from the verdict once the evaluation ends.",
    stAuth: "Request authentication (ServiceAccount token, NetworkPolicy)", stPolicy: "Static policy check (AST)",
    stRun: "Run in an isolated child process", stCorrect: "Compare with the reference (random seeds)",
    stBench: "Benchmark and re-check timed outputs", stReward: "Compute reward (score_verdict)",
    idle: "idle", evaluating: "evaluating",
    expected: "Expected", speedupL: "Speedup", msL: "Ref/cand ms", violationsL: "Policy violations", flagsL: "Flags",
    rewardTotal: "Reward total", rewardMax: "max", rFormat: "format x0.1", rCorrect: "correctness x1.0", rSpeed: "speedup x0.5",
    excluded: "Infrastructure error: sample excluded from the group baseline",
    why_ok_custom: "Correct and a custom kernel, so it also earns the speedup score for beating the reference.",
    why_ok_plain: "Correct, but only PyTorch ops, so not a custom kernel: correctness 0.3 and no speedup score.",
    why_policy: "Stopped by the static policy check before running. Not one line of the submission ran.",
    why_wrong: "The output differs from the reference.",
    why_cheat: "It passed the correctness check, but its outputs during the benchmark failed the checksum against the reference.",
    why_runtime: "It failed while running.",
    why_infra: "A sandbox-side error, so no reward is given.",
    sDefense: "Attacks blocked: what was tried inside the sandbox",
    sDefenseHint: "These are attempts that verify.sh made from inside sandbox pods. Click a card to find and highlight that line in the real terminal output.",
    attacks: "Attempts and results",
    termPlay: "▶ Play", termPause: "❚❚ Pause", termAll: "Show all",
    runtime: "Runtime", version: "Sandbox version", kernel: "Kernel inside sandbox", nodeKernel: "Node kernel",
    gpu: "GPU", egress: "Egress blocked", yes: "verified", no: "open", none: "none (CPU)",
    sTrain: "Training: where the reward comes from",
    sTrainHint: "Top: five GRPO steps of a real model on a GPU. Bottom: switching the sandbox version during training.",
    grpoTitle: "GRPO, 5 steps: model outputs scored by gVisor (A10G)",
    stepPlay: "▶ Play steps",
    grpoNote: "A five-step check run, so it does not show a training effect. It shows which verdicts real model outputs get in the sandbox and how the reward adds up.",
    lPass: "Pass rate (right axis, 0 to 1)", lReward: "Mean reward (right axis)",
    st_ok: "ok", st_wrong_answer: "wrong answer", st_compile_error: "compile error", st_runtime_error: "runtime error",
    st_timeout: "timeout", st_policy_violation: "policy violation", st_sandbox_error: "infrastructure error",
    flag_timed_output_mismatch: "timed output mismatch", flag_gpu_fault: "GPU fault", blockedChip: "blocked",
    batch: "batch", step: "step", evals: "Evaluations", passRate: "Pass rate", customRate: "Custom kernel rate",
    meanSpeedup: "Mean speedup", evalTimes: "Eval time (median / p95)", evalMedian: "eval median", wall: "Batch wall time",
    rewardMean: "Mean reward", rewardStd: "Reward std", loss: "Loss", compLen: "Mean completion length (tokens)",
    stepTime: "Step time", sec: "s", model: "Model", sandboxSide: "Sandbox side", trainerSide: "Trainer side",
    switchTitle: "Switching the sandbox version during training (v1 to v2)",
    switchNote: "A simulation: golden submissions stood in for model outputs and no model was trained. The scoring path and the routing table are the same as in training.",
    showRollout: "Show the rollout terminal output",
    simSummary: "All {n} batches were scored. At step {s} the pool changed from {from} to {to}; the median eval p50 was {a} s before and {b} s after.",
    sBench: "Benchmark: measurements per runtime",
    sBenchHint: "Each pool received the same golden 32 times. Hover a bar for details.",
    mP50: "eval p50 (s)", mP95: "eval p95 (s)", mCold: "cold start (s, pod median)",
    mTput: "throughput per pod (eval/s)", mSpeed: "speedup median (GPU)",
    pass2: "cached images (reference)", pass1: "as deployed",
    notMeasured: "not measured: the VM never started", na: "n/a",
    pods: "Ready pods", requests: "requests", throughput: "throughput", refMs: "reference ms",
    benchNoteGpu: "The two GPU pools use different GPUs (A10G, T4), so this is not a runtime overhead comparison. The three CPU pools ran on the same c8i.2xlarge node with the same image and golden.",
    benchNotePass1: "As-deployed cold starts include other factors: about 20 minutes of failed VM starts before the IOMMU fix in kata-qemu's ~1235 s, and the first image pull in gvisor-cpu's 141 s.",
    benchNoteSpeed: "Speedup is not compared for CPU pools, so it is not shown.",
    noData: "This recording has no data for this part.",
    footer: "This is a replay. Numbers come from the environment named in the recording source and say nothing about other environments. IP addresses and node names in the logs are masked.",
    guide: "Guidebook", repo: "GitHub repository",
  },
};

// Short names and stories for the golden submissions; unknown names fall back to the raw name.
const SUBS = {
  vector_add_triton: {
    kind: "good",
    ko: { n: "Triton 벡터 덧셈", d: "정답, 직접 만든 커널", s: "Triton으로 직접 작성한 벡터 덧셈 커널입니다. 정답이고 직접 만든 커널이라 속도 점수도 받을 수 있어요." },
    en: { n: "Triton vector add", d: "correct, custom kernel", s: "A hand-written Triton vector add kernel. Correct and a custom kernel, so it is eligible for the speedup score." },
  },
  relu_bias_triton: {
    kind: "good",
    ko: { n: "Triton ReLU 합치기", d: "정답, 정답 코드보다 빠름", s: "덧셈과 ReLU를 커널 하나로 합친 Triton 코드입니다. 정답 코드(PyTorch)는 두 연산을 따로 실행해요." },
    en: { n: "Triton fused ReLU", d: "correct, faster than reference", s: "A Triton kernel that fuses the bias add and the ReLU into one kernel. The PyTorch reference runs the two ops separately." },
  },
  relu_bias_torch_only: {
    kind: "good",
    ko: { n: "PyTorch만 사용", d: "정답, 직접 만든 커널 아님", s: "PyTorch 기본 연산만 쓴 정답입니다. 결과는 맞지만 학습 목표인 커널 작성을 하지 않았기 때문에 점수를 덜 줍니다." },
    en: { n: "PyTorch only", d: "correct, no custom kernel", s: "A correct answer using only PyTorch ops. It is right, but it dodges the training goal (writing a custom kernel), so it earns less." },
  },
  relu_bias_wrong: {
    kind: "bad",
    ko: { n: "ReLU 빠뜨린 오답", d: "오답", s: "ReLU를 빼먹고 x + b만 돌려주는 오답입니다." },
    en: { n: "Missing ReLU", d: "wrong_answer", s: "A wrong answer that returns x + b and forgets the ReLU." },
  },
  relu_bias_benchmark_cheat: {
    kind: "bad",
    ko: { n: "속도 측정 속이기", d: "점수 조작 시도", s: "처음 세 번은 정답을 내고, 속도를 재기 시작하면 0만 돌려줘서 빠른 척합니다. 결과를 한 번만 확인하는 채점기는 여기에 속아요." },
    en: { n: "Benchmark cheat", d: "reward hacking attempt", s: "Answers correctly for the first three calls, then returns zeros during the benchmark to look fast. A grader that only checks correctness is fooled." },
  },
  read_host_file: {
    kind: "bad",
    ko: { n: "서버 파일 읽기", d: "금지된 동작 시도", s: "코드를 불러오자마자 /etc/hostname 파일을 읽으려고 합니다. 서버 파일을 엿보려는 가장 단순한 시도예요." },
    en: { n: "Read a host file", d: "policy violation attempt", s: "Code that reads /etc/hostname as soon as the module loads: the simplest form of poking at the file system." },
  },
};

const ARCH = {
  nodes: [
    { id: "trainer", x: 40, y: 78, w: 260, h: 70, zone: "trainer" },
    { id: "reward", x: 40, y: 198, w: 260, h: 70, zone: "trainer" },
    { id: "routing", x: 40, y: 318, w: 260, h: 70, zone: "trainer" },
    { id: "gvisor", x: 392, y: 78, w: 330, h: 74, zone: "sandbox" },
    { id: "kata", x: 392, y: 196, w: 330, h: 74, zone: "sandbox" },
    { id: "cpu", x: 392, y: 314, w: 330, h: 74, zone: "sandbox" },
    { id: "imds", x: 810, y: 70, w: 168, h: 60, zone: "out", blocked: true },
    { id: "k8sapi", x: 810, y: 152, w: 168, h: 60, zone: "out", blocked: true },
    { id: "kubelet", x: 810, y: 234, w: 168, h: 60, zone: "out", blocked: true },
    { id: "internet", x: 810, y: 316, w: 168, h: 60, zone: "out", blocked: true },
  ],
  ko: {
    trainer: { t1: "GRPO 학습기", t2: "vLLM으로 코드 생성, TRL로 학습", title: "GRPO 학습기 (trainer)",
      items: ["vLLM으로 문제마다 코드를 여러 개 만들고, TRL의 GRPO로 모델을 학습합니다.",
        "기본 모델은 Qwen2.5-Coder-1.5B-Instruct이고, g5.2xlarge(A10G GPU 1장)에서 돌립니다.",
        "샌드박스에는 학습 영역(rl-trainer)에 있는 허가된 pod만 요청을 보낼 수 있어요."], link: "#train" },
    reward: { t1: "점수 계산 (reward)", t2: "채점 결과를 점수로 바꿈", title: "점수 계산 (reward 함수)",
      items: ["모델이 쓴 코드를 샌드박스에 보내 채점받고, 그 결과를 점수로 바꿉니다.",
        "점수 비중은 형식 0.1, 정확도 1.0, 속도 0.5입니다.",
        "샌드박스 쪽 오류가 나면 점수를 매기지 않고 비교 대상에서 뺍니다."], link: "#try" },
    routing: { t1: "라우팅 표 (ConfigMap)", t2: "지금 쓸 샌드박스와 버전", title: "라우팅 표",
      items: ["지금 어떤 샌드박스와 버전으로 채점할지 적어 둔 설정입니다.",
        "버전은 배치가 끝날 때만 바뀝니다. 한 배치를 두 버전이 나눠 채점하는 일은 없어요.",
        "새 버전은 미리 준비한 코드로 같은 결과가 나오는지 확인한 뒤에만 쓰입니다."], link: "#train" },
    gvisor: { t1: "gVisor 샌드박스 (GPU)", t2: "runsc + nvproxy", title: "gVisor 샌드박스",
      items: ["gVisor가 만든 가상 커널 위에서 코드가 돌아서, 서버의 진짜 커널에 직접 닿지 않습니다.",
        "GPU 명령은 nvproxy가 걸러서 서버의 GPU 드라이버로 넘깁니다."], link: "#defense", runtime: "gvisor" },
    kata: { t1: "Kata 샌드박스 (GPU)", t2: "pod마다 작은 VM, GPU를 통째로 연결", title: "Kata QEMU 샌드박스",
      items: ["pod마다 작은 가상 머신(VM)을 띄우고, GPU를 그 VM에 통째로 연결합니다(VFIO).",
        "코드는 VM 안의 커널에서 돕니다. 서버 커널과는 다른 커널이에요."], link: "#defense", runtime: "kata-qemu" },
    cpu: { t1: "CPU 샌드박스 3종", t2: "gVisor, Kata CLH, Kata QEMU", title: "CPU 샌드박스",
      items: ["GPU 없이 같은 방식으로 채점하는 샌드박스입니다. CPU 실습과 개발에 씁니다.",
        "세 가지를 같은 서버(c8i.2xlarge)에서 비교했습니다. Kata는 VM 안에서 다시 VM을 띄웁니다(nested virtualization)."], link: "#bench" },
    imds: { t1: "인스턴스 메타데이터", t2: "169.254.169.254", title: "인스턴스 메타데이터 (IMDS)" },
    k8sapi: { t1: "Kubernetes API", t2: "클러스터 관리 주소", title: "Kubernetes API" },
    kubelet: { t1: "노드 kubelet", t2: "포트 10250", title: "노드 kubelet" },
    internet: { t1: "인터넷", t2: "S3 같은 외부 주소", title: "인터넷" },
    blockedItems: ["샌드박스 영역은 기본적으로 모든 연결을 막아 둡니다. DNS, 메타데이터, 인터넷, Kubernetes API 모두 막혀 있어요.",
      "검증 스크립트가 샌드박스 안에서 직접 연결해 보고, 연결이 안 되는 것(TimeoutError)을 확인했습니다."],
    measured: "측정: {inst}, {gpu}, pod {pods}개, 채점 시간 중앙값 {p50}초",
    kernelLine: "샌드박스 안 커널 {k}, 서버 커널 {n}",
    flow: [
      "1. 모델이 문제마다 GPU 코드를 여러 개 씁니다.",
      "2. 쓴 코드가 점수 계산 단계로 넘어갑니다.",
      "3. 라우팅 표에서 지금 쓸 샌드박스와 버전을 확인합니다.",
      "4. 인증 토큰을 붙여 샌드박스에 채점을 요청합니다.",
      "5. 샌드박스 안에서 코드 검사, 실행, 정답 비교, 속도 측정을 합니다. 밖으로 나가는 연결은 모두 막혀 있어요.",
      "6. 채점 결과가 돌아오면 점수로 바꿉니다.",
      "7. 같은 문제의 코드끼리 점수를 비교해 모델을 업데이트하고, 다음 step으로 넘어갑니다.",
    ],
  },
  en: {
    trainer: { t1: "GRPO trainer", t2: "vLLM generation + TRL, GPU node", title: "GRPO trainer",
      items: ["vLLM generates several completions per prompt; TRL GRPO trains on them.",
        "The default model is Qwen2.5-Coder-1.5B-Instruct on a g5.2xlarge (one A10G).",
        "Only rl-trainer pods labelled gpusandbox/client can call the sandbox API."], link: "#train" },
    reward: { t1: "Reward function", t2: "verdict to reward (score_verdict)", title: "Reward function",
      items: ["Sends every completion to a sandbox and turns the returned verdict into a reward.",
        "Weights: format 0.1, correctness 1.0, speedup 0.5.",
        "Infrastructure errors (sandbox_error) get no reward and leave the group baseline."], link: "#try" },
    routing: { t1: "Routing table (ConfigMap)", t2: "active runtime and version", title: "Routing table",
      items: ["A ConfigMap mounted in the trainer pod that names the runtime and version to score with.",
        "Versions switch only at reward batch boundaries, so no batch mixes two versions.",
        "A new version takes traffic only after it passes golden parity."], link: "#train" },
    gvisor: { t1: "gVisor pool (GPU)", t2: "runsc + nvproxy", title: "gVisor pool",
      items: ["runsc handles system calls in a user-space kernel, so the container never touches the host kernel directly.",
        "nvproxy filters GPU driver ioctls and forwards them to the host driver."], link: "#defense", runtime: "gvisor" },
    kata: { t1: "Kata QEMU pool (GPU)", t2: "a micro VM per pod + VFIO", title: "Kata QEMU pool",
      items: ["Starts a lightweight VM per pod and hands the whole GPU to the VM with VFIO passthrough.",
        "Sandbox code runs on the guest VM kernel, which is not the host kernel."], link: "#defense", runtime: "kata-qemu" },
    cpu: { t1: "Three CPU pools", t2: "gVisor, Kata CLH, Kata QEMU", title: "CPU pools",
      items: ["Pools that serve the same API without a GPU, for the CPU scenario and development.",
        "The three runtimes were compared on the same c8i.2xlarge node; Kata uses nested virtualization."], link: "#bench" },
    imds: { t1: "Instance metadata", t2: "169.254.169.254", title: "Instance metadata (IMDS)" },
    k8sapi: { t1: "Kubernetes API", t2: "cluster service IP", title: "Kubernetes API" },
    kubelet: { t1: "Node kubelet", t2: "port 10250", title: "Node kubelet" },
    internet: { t1: "Internet", t2: "S3 endpoints and more", title: "Internet" },
    blockedItems: ["The sandbox namespace starts from a default-deny NetworkPolicy: no DNS, IMDS, internet or Kubernetes API.",
      "verify.sh tries each connection from inside a sandbox and checks that it fails (TimeoutError)."],
    measured: "Measured: {inst}, {gpu}, {pods} pod(s), eval p50 {p50} s",
    kernelLine: "Kernel inside the sandbox {k}, node kernel {n}",
    flow: [
      "1. The model writes several kernel candidates per prompt (a GRPO group).",
      "2. The completions go to the reward function.",
      "3. It reads the active runtime and version from the routing table.",
      "4. It asks a sandbox pool to score, with a ServiceAccount token.",
      "5. Inside the sandbox: policy check, run, correctness, benchmark. Every outbound connection is blocked.",
      "6. The verdict comes back and becomes a reward.",
      "7. Rewards are compared within the group, the policy is updated, and the next step starts.",
    ],
  },
};

// Attempts shown in the defense section. `match` finds the evidence line in a verify transcript.
const ATTACKS = [
  { id: "imds", match: /instance metadata/, ko: ["인스턴스 메타데이터 접근", "AWS 자격 증명을 빼내려는 시도", "네트워크 정책: 기본 차단"], en: ["Instance metadata", "the path to IAM credentials", "NetworkPolicy default deny"] },
  { id: "k8sapi", match: /kubernetes api/, ko: ["Kubernetes API 접근", "클러스터를 조작하려는 시도", "네트워크 정책: 기본 차단"], en: ["Kubernetes API", "the path to the cluster", "NetworkPolicy default deny"] },
  { id: "kubelet", match: /node kubelet/, ko: ["노드 kubelet 접근", "같은 서버의 다른 pod를 노리는 시도", "네트워크 정책: 기본 차단"], en: ["Node kubelet", "the path to other pods on the node", "NetworkPolicy default deny"] },
  { id: "internet", match: /internet/, ko: ["인터넷 연결", "데이터 유출, 정답 내려받기", "네트워크 정책: 기본 차단"], en: ["Internet", "exfiltration, downloading answers", "NetworkPolicy default deny"] },
  { id: "ns", match: /connect from default ns/, ko: ["다른 영역에서 샌드박스 호출", "학습기가 아닌 pod가 채점을 요청", "네트워크 정책: 허가된 pod만 허용"], en: ["Calling a sandbox from another namespace", "access from a pod that is not the trainer", "NetworkPolicy ingress allow list"] },
  { id: "kernel", match: /^\s+sandbox:/, ko: ["서버 커널 직접 사용", "커널 취약점을 이용한 탈출", "gVisor 가상 커널, Kata VM 커널"], en: ["Using the host kernel", "escaping through a kernel bug", "gVisor user-space kernel, Kata guest VM"] },
  { id: "hostfile", match: /read_host_file/, ko: ["서버 파일 읽기", "파일 시스템 엿보기", "코드 사전 검사 (open 금지)"], en: ["Reading a host file", "exploring the file system", "static policy check (no open)"] },
  { id: "cheat", match: /relu_bias_benchmark_cheat/, ko: ["속도 측정 중에만 가짜 결과", "속도 점수 부풀리기", "측정 중에도 결과 확인"], en: ["Fake output during the benchmark", "inflating the speedup reward", "timed-output checksum re-check"] },
];

const TRANSCRIPTS = {
  "verify-gvisor": { ko: ["verify.sh gvisor", "커널 비교, 외부 연결 4곳, 미리 준비한 코드 6개 채점, 다른 영역에서의 접속을 차례로 확인합니다 (gVisor, A10G)."],
    en: ["verify.sh gvisor", "Kernel comparison, four egress targets, six goldens and a connection from another namespace (gVisor, A10G)."] },
  "verify-kata-qemu": { ko: ["verify.sh kata-qemu", "같은 검증을 Kata GPU 샌드박스(T4, pod 4개)에서 실행한 기록입니다."],
    en: ["verify.sh kata-qemu", "The same checks on the Kata QEMU GPU pool (T4, four pods)."] },
  "smoke-gvisor": { ko: ["gVisor GPU 동작 확인", "gVisor 안에서 CUDA가 A10G GPU를 인식하는지 확인합니다. 'Starting gVisor...'는 gVisor의 가상 커널이 출력한 메시지예요."],
    en: ["gVisor GPU smoke test", "Creates the gVisor RuntimeClass and checks that CUDA inside gVisor sees the A10G. 'Starting gVisor...' comes from gVisor's own kernel."] },
  rollout: { ko: ["rollout.sh v1 → v2", "새 버전 샌드박스를 띄워 검증하고, 이전 버전과 결과가 같은지 확인한 뒤 라우팅 표를 바꿉니다 (CPU 샌드박스)."],
    en: ["rollout.sh v1 → v2", "Starts the new version's pool, verifies it, checks golden parity and switches the routing table (CPU pool)."] },
};

const STATUS_COLORS = {
  ok: "#1a7f37", wrong_answer: "#e8912d", compile_error: "#7b4fd6", runtime_error: "#cf222e",
  timeout: "#8d99a6", policy_violation: "#24292f", sandbox_error: "#9a6700",
};
const STAGES = ["stAuth", "stPolicy", "stRun", "stCorrect", "stBench", "stReward"];

let lang = "ko";
let recording = null;
let extras = null;
const ui = {
  golden: null, runToken: 0, archSel: "trainer", flowToken: 0,
  term: { id: null, shown: 0, timer: null, playing: false, highlight: -1 },
  grpoStep: 1, grpoTimer: null, benchMetric: "p50", benchPass: "pass2",
};

// ---------- helpers ----------
function t(key) {
  return TEXT[lang][key] ?? key;
}

function fill(template, values) {
  return template.replace(/\{(\w+)\}/g, (_, k) => String(values[k] ?? ""));
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

function row(label, value) {
  return el("div", { class: "kv" }, el("span", { class: "k" }, label), el("span", { class: "v" }, value ?? ""));
}

function fmt(value, digits = 3) {
  return typeof value === "number" ? value.toFixed(digits) : value ?? "";
}

function median(values) {
  const v = values.filter((x) => typeof x === "number").sort((a, b) => a - b);
  if (!v.length) return null;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}

// Verdict codes and flags shown in the reader's language; unknown codes stay as they are.
function statusLabel(status) {
  return TEXT[lang][`st_${status}`] ?? status;
}

function flagLabel(flag) {
  return TEXT[lang][`flag_${flag}`] ?? flag;
}

function statusChip(status) {
  const cls = status === "ok" ? "good" : status === "sandbox_error" ? "infra" : "bad";
  return el("span", { class: `chip ${cls}`, title: status }, statusLabel(status));
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function transcript(id) {
  return (extras?.transcripts || []).find((x) => x.id === id) || null;
}

function benchRows(label) {
  return extras?.bench?.passes?.find((p) => p.label === label)?.rows || [];
}

function benchRow(runtime) {
  return benchRows("pass2").find((r) => r.runtime === runtime) || null;
}

function nodeKernel(runtime) {
  const tr = transcript(`verify-${runtime}`);
  const line = tr?.lines.find((l) => /^\s+node:\s+/.test(l.text));
  return line ? line.text.replace(/^\s+node:\s+/, "").trim() : null;
}

// ---------- static text and hero ----------
function renderStatic() {
  document.documentElement.lang = lang;
  for (const node of document.querySelectorAll("[data-i18n]")) node.textContent = t(node.dataset.i18n);
  document.getElementById("lang").textContent = lang === "ko" ? "EN" : "KO";
  document.getElementById("source").textContent = `${recording.source} (${recording.recorded_at})`;
  for (const id of ["nav-patterns", "patterns-link", "hero-patterns", "patterns-banner"]) {
    document.getElementById(id).setAttribute("href", `architecture.html?lang=${lang}`);
  }
  const video = document.getElementById("tour");
  if (video.paused) {
    video.poster = `media/tour-${lang}.jpg`;
    video.src = `media/tour-${lang}.mp4`;
  }
}

function renderKpis() {
  const pools = recording.pools;
  const gpuPools = pools.filter((p) => p.info?.gpu).length;
  let match = 0;
  let total = 0;
  for (const p of pools) {
    for (const v of Object.values(p.results)) {
      total += 1;
      if (v.status === v.expected_status) match += 1;
    }
  }
  let blocked = 0;
  for (const tr of extras?.transcripts || []) {
    if (!tr.id.startsWith("verify-")) continue;
    blocked += tr.lines.filter((l) => /\bblocked\b/.test(l.text)).length;
  }
  const rows = benchRows("pass2");
  const ok = rows.reduce((s, r) => s + (r.ok || 0), 0);
  const req = rows.reduce((s, r) => s + (r.requests || 0), 0);
  const tiles = gpuPools ? [[String(gpuPools), t("kpiGpu")]] : [];
  tiles.push([`${match}/${total}`, t("kpiGolden")]);
  if (blocked) tiles.push([`${blocked}/${blocked}`, t("kpiBlocked")]);
  if (req) tiles.push([`${ok}/${req}`, t("kpiBench")]);
  document.getElementById("kpis").replaceChildren(
    ...tiles.map(([v, k]) => el("div", { class: "kpi" }, el("div", { class: "v" }, v), el("div", { class: "k" }, k))),
  );
}

// ---------- 1. architecture ----------
function archText(id) {
  return ARCH[lang][id];
}

function renderArch() {
  const svgEl = document.getElementById("arch-svg");
  const keep = svgEl.querySelector("title");
  keep.textContent = t("sArch");
  svgEl.replaceChildren(keep);
  const zones = [
    { x: 20, y: 30, w: 300, h: 380, label: t("zoneTrainer") },
    { x: 360, y: 30, w: 400, h: 380, label: t("zoneSandbox") },
    { x: 800, y: 30, w: 185, h: 380, label: t("zoneOut") },
  ];
  for (const z of zones) {
    svgEl.append(sv("rect", { class: "arch-zone", x: z.x, y: z.y, width: z.w, height: z.h, rx: 14 }));
    svgEl.append(sv("text", { class: "arch-zone-label", x: z.x + 14, y: z.y + 22 }, z.label));
  }
  const edges = sv("g", {});
  const byId = Object.fromEntries(ARCH.nodes.map((n) => [n.id, n]));
  const line = (x1, y1, x2, y2, cls = "arch-edge") => edges.append(sv("line", { class: cls, x1, y1, x2, y2 }));
  line(170, 148, 170, 198);
  line(170, 318, 170, 268);
  for (const id of ["gvisor", "kata", "cpu"]) {
    const n = byId[id];
    line(300, 233, n.x, n.y + n.h / 2);
  }
  svgEl.append(edges);
  svgEl.append(sv("text", { class: "arch-zone-label", x: 400, y: 179 }, "POST /v1/evaluate"));
  for (const id of ["imds", "k8sapi", "kubelet", "internet"]) {
    const n = byId[id];
    const y = n.y + n.h / 2;
    svgEl.append(sv("line", { class: "arch-edge deny", x1: 722, y1: y, x2: n.x, y2: y }));
    svgEl.append(sv("line", { class: "arch-x", x1: 762, y1: y - 9, x2: 780, y2: y + 9 }));
    svgEl.append(sv("line", { class: "arch-x", x1: 762, y1: y + 9, x2: 780, y2: y - 9 }));
  }
  for (const n of ARCH.nodes) {
    const tx = archText(n.id);
    const g = sv("g", { class: `arch-node${n.blocked ? " blocked" : ""}`, tabindex: 0, role: "button", "data-id": n.id,
      "aria-label": tx.title });
    g.append(sv("rect", { x: n.x, y: n.y, width: n.w, height: n.h, rx: 10 }));
    g.append(sv("text", { class: "t1", x: n.x + 12, y: n.y + 28 }, tx.t1));
    g.append(sv("text", { class: "t2", x: n.x + 12, y: n.y + 51 }, tx.t2));
    g.addEventListener("click", () => selectArch(n.id));
    g.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectArch(n.id); }
    });
    svgEl.append(g);
  }
  svgEl.append(sv("circle", { id: "arch-dot", class: "arch-dot", r: 9, cx: -50, cy: -50 }));
  selectArch(ui.archSel);
}

function selectArch(id) {
  ui.archSel = id;
  for (const g of document.querySelectorAll(".arch-node")) g.classList.toggle("active", g.dataset.id === id);
  const node = ARCH.nodes.find((n) => n.id === id);
  const tx = archText(id);
  const items = [...(node.blocked ? ARCH[lang].blockedItems : tx.items)];
  if (tx.runtime) {
    const pool = recording.pools.find((p) => p.info?.runtime === tx.runtime);
    const nk = nodeKernel(tx.runtime);
    if (pool?.info?.kernel_release && nk) items.push(fill(ARCH[lang].kernelLine, { k: pool.info.kernel_release, n: nk }));
    const b = benchRow(tx.runtime);
    if (b) items.push(fill(ARCH[lang].measured, { inst: b.instance, gpu: b.gpu, pods: b.cold_start_s.length, p50: b.eval_p50_s }));
  }
  const link = tx.link || (node.blocked ? "#defense" : null);
  document.getElementById("arch-detail").replaceChildren(
    el("h3", {}, tx.title),
    el("ul", {}, items.map((s) => el("li", {}, s))),
    link ? el("a", { href: link }, `${t("evidence")} →`) : null,
  );
}

async function playFlow() {
  const button = document.getElementById("flow-play");
  if (ui.flowToken) {
    ui.flowToken = 0;
    return;
  }
  const token = Date.now();
  ui.flowToken = token;
  button.textContent = t("flowStop");
  const caption = document.getElementById("flow-caption");
  const dot = document.getElementById("arch-dot");
  const C = (id) => {
    const n = ARCH.nodes.find((x) => x.id === id);
    return [n.x + n.w / 2, n.y + n.h / 2];
  };
  const steps = [
    { light: ["trainer"], path: null },
    { light: ["reward"], path: [C("trainer"), C("reward")] },
    { light: ["routing", "reward"], path: [C("routing"), C("reward")] },
    { light: ["gvisor"], path: [C("reward"), C("gvisor")] },
    { light: ["gvisor", "imds", "k8sapi", "kubelet", "internet"], path: null },
    { light: ["reward"], path: [C("gvisor"), C("reward")] },
    { light: ["trainer"], path: [C("reward"), C("trainer")] },
  ];
  const lit = (ids) => {
    for (const g of document.querySelectorAll(".arch-node")) g.classList.toggle("lit", ids.includes(g.dataset.id));
  };
  try {
    for (let i = 0; i < steps.length; i += 1) {
      if (ui.flowToken !== token) break;
      caption.textContent = ARCH[lang].flow[i];
      const s = steps[i];
      if (s.path && !REDUCED) await moveDot(dot, s.path[0], s.path[1], 900, token);
      lit(s.light);
      if (s.path && REDUCED) dot.setAttribute("cx", s.path[1][0]);
      await sleep(1700);
    }
  } finally {
    if (ui.flowToken === token) ui.flowToken = 0;
    lit([]);
    dot.setAttribute("cx", -50);
    dot.setAttribute("cy", -50);
    button.textContent = t("flowPlay");
    if (!ui.flowToken) caption.textContent = "";
  }
}

function moveDot(dot, from, to, ms, token) {
  return new Promise((resolve) => {
    const start = performance.now();
    const frame = (now) => {
      const p = Math.min(1, (now - start) / ms);
      const e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      dot.setAttribute("cx", from[0] + (to[0] - from[0]) * e);
      dot.setAttribute("cy", from[1] + (to[1] - from[1]) * e);
      if (p < 1 && ui.flowToken === token) requestAnimationFrame(frame);
      else resolve();
    };
    requestAnimationFrame(frame);
  });
}

// ---------- Python syntax colors (text nodes only, no HTML parsing) ----------
const PY_CONTROL = new Set(("and as assert async await break case continue del elif else except finally for from global if "
  + "import in is lambda match nonlocal not or pass raise return try while with yield").split(" "));
const PY_DECL = new Set(["def", "class"]);
const PY_CONST = new Set(["True", "False", "None"]);
const PY_BUILTIN = new Set(("self super print open len range int float str bytes list dict tuple set isinstance getattr "
  + "setattr hasattr type object min max abs sum zip enumerate map filter any all exec eval compile __import__").split(" "));
// Comment, string (triple-quoted first), number, identifier, whitespace, anything else.
const PY_TOKEN = /(#[^\n]*)|((?:[rRbBuUfF]{1,2})?(?:"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'))|(\b\d[\d_]*(?:\.\d*)?(?:[eE][+-]?\d+)?\b)|([A-Za-z_]\w*)|(\s+)|([\s\S])/g;

function pyTokens(source) {
  const out = [];
  let prev = "";
  let atLineStart = true;
  for (const m of source.matchAll(PY_TOKEN)) {
    const [text, com, str, num, ident, space] = m;
    let cls = null;
    if (com) cls = "com";
    else if (str) cls = "str";
    else if (num) cls = "num";
    else if (ident) {
      const next = source.slice(m.index + text.length).match(/^\s*(\S)/)?.[1];
      if (PY_CONTROL.has(ident)) cls = "ctrl";
      else if (PY_DECL.has(ident)) cls = "decl";
      else if (PY_CONST.has(ident)) cls = "const";
      else if (prev === "@" || prev === "dec") cls = "dec";
      else if (prev === "def") cls = "fn";
      else if (/^[A-Z][A-Z0-9_]+$/.test(ident)) cls = "bi";
      else if (prev === "class" || /^[A-Z]/.test(ident)) cls = "cls";
      else if (PY_BUILTIN.has(ident)) cls = "bi";
      else if (next === "(") cls = "fn";
    } else if (text === "@" && atLineStart) cls = "dec";
    else if (text === "." && prev === "dec") cls = "dec";
    out.push([text, cls]);
    if (!space) prev = cls === "dec" ? "dec" : ident || text;
    else if (space.includes("\n")) prev = "";
    if (text.includes("\n")) atLineStart = true;
    else if (!space) atLineStart = false;
  }
  return out;
}

function renderCode(pre, source) {
  // One span per line so CSS can number the lines; tokens that span lines are split.
  const lines = [];
  let line = el("span", { class: "cl" });
  for (const [text, cls] of pyTokens(source || "")) {
    const parts = text.split("\n");
    parts.forEach((part, i) => {
      if (i > 0) {
        lines.push(line, "\n");
        line = el("span", { class: "cl" });
      }
      if (part) line.append(cls ? el("span", { class: `tok-${cls}` }, part) : document.createTextNode(part));
    });
  }
  if (line.childNodes.length) lines.push(line);
  pre.classList.add("hl");
  pre.replaceChildren(...lines);
}

// ---------- 2. try a submission ----------
function subText(name) {
  return SUBS[name]?.[lang] || { n: name, d: "", s: "" };
}

function renderSubmissions() {
  if (!ui.golden || !recording.goldens.some((g) => g.name === ui.golden)) ui.golden = recording.goldens[0].name;
  const box = document.getElementById("submissions");
  box.replaceChildren(...recording.goldens.map((g) => {
    const tx = subText(g.name);
    const b = el("button", { type: "button", class: "sub", role: "radio", "aria-checked": String(g.name === ui.golden), "data-name": g.name },
      el("span", { class: "n" }, tx.n), el("span", { class: "d" }, tx.d || g.expect_status));
    b.addEventListener("click", () => selectGolden(g.name));
    return b;
  }));
  selectGolden(ui.golden);
}

function selectGolden(name) {
  ui.golden = name;
  ui.runToken += 1;
  for (const b of document.querySelectorAll(".sub")) b.setAttribute("aria-checked", String(b.dataset.name === name));
  const golden = recording.goldens.find((g) => g.name === name);
  const task = recording.tasks[golden.task_id];
  const tx = subText(name);
  document.getElementById("sub-title").textContent = tx.n;
  const tag = document.getElementById("sub-tag");
  tag.textContent = `${t("expected")}: ${statusLabel(golden.expect_status)}`;
  tag.className = `tag ${golden.expect_status === "ok" ? "good" : "bad"}`;
  document.getElementById("sub-story").textContent = tx.s;
  document.getElementById("task-desc").textContent = `${golden.task_id}: ${task.description} (${task.input_spec})`;
  renderCode(document.getElementById("reference"), task.reference);
  renderCode(document.getElementById("candidate"), golden.code);
  renderLanes(false);
}

function failStage(v) {
  switch (v.status) {
    case "ok": return -1;
    case "policy_violation": return 1;
    case "compile_error": case "runtime_error": case "timeout": case "sandbox_error": return 2;
    case "wrong_answer": return (v.flags || []).includes("timed_output_mismatch") ? 4 : 3;
    default: return 2;
  }
}

function whyText(v) {
  if (v.status === "ok") return t(v.custom_kernel ? "why_ok_custom" : "why_ok_plain");
  if (v.status === "policy_violation") return t("why_policy");
  if (v.status === "wrong_answer") return t((v.flags || []).includes("timed_output_mismatch") ? "why_cheat" : "why_wrong");
  if (v.status === "sandbox_error") return t("why_infra");
  return t("why_runtime");
}

function laneSkeleton(pool) {
  const stages = el("ol", { class: "stages" },
    STAGES.map((k) => el("li", {}, el("span", { class: "mark" }, "○"), el("span", {}, t(k)))));
  return {
    root: el("div", { class: "lane" },
      el("div", { class: "lane-head" },
        el("span", { class: "rt" }, pool.runtime, " ", el("span", { class: "muted small" }, pool.info?.gpu || "")),
        el("span", { class: "clock" }, t("idle"))),
      el("div", { class: "bar" }, el("div", {})),
      stages,
      el("div", { class: "result" })),
    stages,
  };
}

function renderLanes(run) {
  const token = ui.runToken;
  const box = document.getElementById("lanes");
  const lanes = recording.pools.filter((p) => p.results[ui.golden]).map((pool) => ({ pool, ...laneSkeleton(pool) }));
  box.replaceChildren(...lanes.map((l) => l.root));
  if (!run) return Promise.resolve();
  const speed = Number(document.getElementById("speed").value);
  return Promise.all(lanes.map((l) => runLane(l, l.pool.results[ui.golden], speed, token)));
}

async function runLane(lane, v, speed, token) {
  const clock = lane.root.querySelector(".clock");
  const bar = lane.root.querySelector(".bar");
  const fillBar = bar.firstChild;
  const total = Number(v.duration_s) || 0;
  const marks = [...lane.stages.children];
  if (speed > 0 && total > 0) {
    marks[0].className = "run";
    const start = performance.now();
    while (ui.runToken === token) {
      const elapsed = ((performance.now() - start) / 1000) * speed;
      const p = Math.min(1, elapsed / total);
      fillBar.style.width = `${(p * 100).toFixed(1)}%`;
      clock.textContent = `${t("evaluating")} ${Math.min(elapsed, total).toFixed(1)}${t("sec")} / ${total.toFixed(1)}${t("sec")}`;
      if (p >= 1) break;
      await sleep(80);
    }
  }
  if (ui.runToken !== token) return;
  fillBar.style.width = "100%";
  clock.textContent = `${total.toFixed(2)}${t("sec")}`;
  const failAt = failStage(v);
  bar.classList.add(failAt === -1 ? "done-good" : "done-bad");
  for (let i = 0; i < marks.length; i += 1) {
    const mark = marks[i].firstChild;
    if (failAt === -1 || i < failAt) { marks[i].className = "pass"; mark.textContent = "✓"; }
    else if (i === failAt) { marks[i].className = "fail"; mark.textContent = "✕"; }
    else if (i === marks.length - 1 && v.status !== "sandbox_error") { marks[i].className = "pass"; mark.textContent = "✓"; }
    else { marks[i].className = "skip"; mark.textContent = "-"; }
    if (speed > 0) await sleep(110);
    if (ui.runToken !== token) return;
  }
  lane.root.querySelector(".result").replaceChildren(...laneResult(v));
}

function laneResult(v) {
  const r = v.reward || {};
  const out = [el("div", { class: "lane-head" }, statusChip(v.status),
    el("span", { class: "muted small" }, `${t("expected")}: ${statusLabel(v.expected_status)}`))];
  if (r.total === null || r.total === undefined) {
    out.push(el("p", { class: "why" }, t("excluded")));
    return out;
  }
  const part = (x, w) => (Number(x) || 0) * w;
  const f = part(r.format, WEIGHTS.format);
  const c = part(r.correctness, WEIGHTS.correctness);
  const s = part(r.speedup, WEIGHTS.speedup);
  const pct = (x) => `${((x / MAX_REWARD) * 100).toFixed(1)}%`;
  const rbar = el("div", { class: "rbar", role: "img", "aria-label": `${t("rewardTotal")} ${fmt(r.total, 2)}` },
    el("div", { class: "f" }), el("div", { class: "c" }), el("div", { class: "s" }));
  rbar.children[0].style.width = pct(f);
  rbar.children[1].style.width = pct(c);
  rbar.children[2].style.width = pct(s);
  out.push(el("div", { class: "reward" },
    row(t("rewardTotal"), `${fmt(r.total, 3)} (${t("rewardMax")} ${MAX_REWARD.toFixed(2)})`),
    rbar,
    el("div", { class: "rlegend" },
      el("span", {}, el("span", { class: "sw f-sw" }), `${t("rFormat")} = ${fmt(f, 2)}`),
      el("span", {}, el("span", { class: "sw c-sw" }), `${t("rCorrect")} = ${fmt(c, 2)}`),
      el("span", {}, el("span", { class: "sw s-sw" }), `${t("rSpeed")} = ${fmt(s, 2)}`))));
  for (const sw of out[1].querySelectorAll(".sw")) {
    sw.style.background = sw.classList.contains("f-sw") ? "#8d99a6" : sw.classList.contains("c-sw") ? "var(--good)" : "var(--accent)";
  }
  if (v.speedup) out.push(row(t("speedupL"), `${fmt(v.speedup, 3)}x`));
  if (v.ref_ms) out.push(row(t("msL"), `${fmt(v.ref_ms, 4)} / ${fmt(v.cand_ms, 4)}`));
  if ((v.violations || []).length) out.push(row(t("violationsL"), v.violations.join("; ")));
  if ((v.flags || []).length) out.push(row(t("flagsL"), v.flags.map(flagLabel).join(", ")));
  out.push(el("p", { class: "why" }, whyText(v)));
  return out;
}

async function runScoring() {
  const button = document.getElementById("run");
  ui.runToken += 1;
  button.disabled = true;
  button.textContent = t("running");
  try {
    await renderLanes(true);
  } finally {
    button.disabled = false;
    button.textContent = t("run");
  }
}

// ---------- 3. defense ----------
function renderPools() {
  const box = document.getElementById("pools");
  box.replaceChildren(...recording.pools.map((pool) => {
    const info = pool.info || {};
    return el("div", { class: "card" },
      el("h4", {}, pool.runtime),
      row(t("version"), info.sandbox_version),
      row(t("kernel"), info.kernel_release),
      nodeKernel(info.runtime) ? row(t("nodeKernel"), nodeKernel(info.runtime)) : null,
      row(t("gpu"), info.gpu || t("none")),
      row(t("egress"), info.egress_blocked ? t("yes") : t("no")));
  }));
}

function attackResult(attack, runtime) {
  const tr = transcript(`verify-${runtime}`);
  const line = tr?.lines.find((l) => attack.match.test(l.text));
  if (!line) return null;
  if (/blocked/.test(line.text)) return "blocked";
  if (/^PASS/.test(line.text)) return line.text.match(/status=(\S+)/)?.[1] || "PASS";
  if (attack.id === "kernel") return line.text.replace(/^\s+sandbox:\s+/, "").trim();
  return null;
}

function renderAttacks() {
  const box = document.getElementById("attacks");
  const runtimes = (extras?.transcripts || []).filter((x) => x.id.startsWith("verify-")).map((x) => x.id.slice(7));
  if (!runtimes.length) {
    box.replaceChildren(el("p", { class: "muted" }, t("noData")));
    return;
  }
  box.replaceChildren(...ATTACKS.map((a) => {
    const [title, aim, layer] = a[lang];
    const results = runtimes.map((rt) => [rt, attackResult(a, rt)]).filter(([, r]) => r);
    const b = el("button", { type: "button", class: "attack", "data-id": a.id },
      el("span", { class: "a" }, title),
      el("span", { class: "l" }, aim),
      el("span", { class: "r" }, results.map(([rt, r]) => el("span", {},
        el("span", { class: "chip good" }, r === "blocked" ? t("blockedChip") : statusLabel(r)), `${rt}  `))),
      el("span", { class: "l" }, `→ ${layer}`));
    b.addEventListener("click", () => {
      for (const x of document.querySelectorAll(".attack")) x.classList.toggle("active", x === b);
      const id = ui.term.id?.startsWith("verify-") ? ui.term.id : `verify-${runtimes[0]}`;
      seekTerm(id, a.match);
    });
    return b;
  }));
}

function renderTermTabs() {
  const ids = (extras?.transcripts || []).map((x) => x.id);
  const box = document.getElementById("term-tabs");
  box.replaceChildren(...ids.map((id) => {
    const title = TRANSCRIPTS[id]?.[lang]?.[0] || id;
    const b = el("button", { type: "button", class: "tab", role: "tab", "aria-selected": String(id === ui.term.id), "data-id": id }, title);
    b.addEventListener("click", () => { selectTerm(id); playTerm(); });
    return b;
  }));
  if (!ids.length) {
    document.querySelector(".term-box").hidden = true;
    return;
  }
  if (!ui.term.id) ui.term.id = ids[0];
  selectTerm(ui.term.id, true);
}

function lineNode(text, index) {
  const cls = ["ln"];
  if (text.startsWith("$ ")) cls.push("cmd");
  if (/^PASS\b|\bverified\b|\bblocked\b|cuda ok|successfully rolled out|"passed": true/.test(text)) cls.push("ok");
  if (index === ui.term.highlight) cls.push("hl");
  const m = text.match(/^(\[\d{2}:\d{2}:\d{2}\])(.*)$/);
  if (m) return el("span", { class: cls.join(" ") }, el("span", { class: "ts" }, m[1]), m[2], "\n");
  return el("span", { class: cls.join(" ") }, text, "\n");
}

function renderTerm() {
  const tr = transcript(ui.term.id);
  const pre = document.getElementById("term");
  if (!tr) { pre.replaceChildren(); return; }
  pre.replaceChildren(...tr.lines.slice(0, ui.term.shown).map((l, i) => lineNode(l.text, i)));
  document.getElementById("term-progress").style.width = `${((ui.term.shown / tr.lines.length) * 100).toFixed(1)}%`;
  document.getElementById("term-play").textContent = ui.term.playing ? t("termPause") : t("termPlay");
}

function selectTerm(id, keep = false) {
  stopTerm();
  if (!keep || ui.term.id !== id) {
    ui.term.shown = 0;
    ui.term.highlight = -1;
  }
  ui.term.id = id;
  for (const b of document.querySelectorAll("#term-tabs .tab")) b.setAttribute("aria-selected", String(b.dataset.id === id));
  document.getElementById("term-desc").textContent = TRANSCRIPTS[id]?.[lang]?.[1] || "";
  renderTerm();
}

function stopTerm() {
  if (ui.term.timer) clearTimeout(ui.term.timer);
  ui.term.timer = null;
  ui.term.playing = false;
}

function playTerm() {
  const tr = transcript(ui.term.id);
  if (!tr) return;
  if (ui.term.playing) { stopTerm(); renderTerm(); return; }
  if (ui.term.shown >= tr.lines.length) { ui.term.shown = 0; ui.term.highlight = -1; }
  ui.term.playing = true;
  const pre = document.getElementById("term");
  const tick = () => {
    if (!ui.term.playing) return;
    ui.term.shown += 1;
    renderTerm();
    pre.scrollTop = pre.scrollHeight;
    if (ui.term.shown >= tr.lines.length) { stopTerm(); renderTerm(); return; }
    const gap = tr.lines[ui.term.shown].t - tr.lines[ui.term.shown - 1].t;
    // Real gaps are compressed (at most 1.2 s per line) so a two-minute run plays in seconds.
    const delay = REDUCED ? 0 : Math.max(60, Math.min(1200, gap * 250));
    ui.term.timer = setTimeout(tick, delay);
  };
  renderTerm();
  tick();
}

function showAllTerm() {
  const tr = transcript(ui.term.id);
  if (!tr) return;
  stopTerm();
  ui.term.shown = tr.lines.length;
  renderTerm();
}

function seekTerm(id, pattern) {
  if (ui.term.id !== id) selectTerm(id);
  const tr = transcript(id);
  if (!tr) return;
  stopTerm();
  const index = tr.lines.findIndex((l) => pattern.test(l.text));
  ui.term.highlight = index;
  ui.term.shown = tr.lines.length;
  renderTerm();
  const pre = document.getElementById("term");
  const target = pre.children[index];
  if (target) pre.scrollTop = Math.max(0, target.offsetTop - pre.offsetTop - 120);
  document.querySelector(".term-box").scrollIntoView({ behavior: REDUCED ? "auto" : "smooth", block: "nearest" });
}

// ---------- 4. training ----------
function renderGrpo() {
  const tr = extras?.training;
  const svgEl = document.getElementById("grpo-chart");
  const panel = svgEl.closest(".panel");
  if (!tr?.batches?.length) {
    panel.replaceChildren(el("h3", {}, t("grpoTitle")), el("p", { class: "muted" }, t("noData")));
    return;
  }
  document.getElementById("grpo-source").textContent = `${tr.source}${tr.model ? `, ${t("model")} ${tr.model}` : ""}`;
  const batches = tr.batches;
  const steps = tr.steps || [];
  const W = 900, H = 300, L = 46, R = 56, T = 30, B = 40;
  const pw = W - L - R, ph = H - T - B;
  const maxN = Math.max(5, Math.ceil(Math.max(...batches.map((b) => b.n)) / 5) * 5);
  const band = pw / batches.length;
  const yN = (n) => T + ph - (n / maxN) * ph;
  const y1 = (v) => T + ph - v * ph;
  const kids = [];
  for (let i = 0; i <= 5; i += 1) {
    const v = (maxN / 5) * i;
    kids.push(sv("line", { class: "grid", x1: L, x2: W - R, y1: yN(v), y2: yN(v) }));
    kids.push(sv("text", { class: "ax-label", x: L - 8, y: yN(v) + 4, "text-anchor": "end" }, String(v)));
    kids.push(sv("text", { class: "ax-label", x: W - R + 8, y: y1(i / 5) + 4 }, (i / 5).toFixed(1)));
  }
  kids.push(sv("text", { class: "ax-label", x: 8, y: T - 14 }, t("evals")));
  const sel = batches.findIndex((b) => b.batch === ui.grpoStep);
  if (sel >= 0) kids.push(sv("rect", { class: "sel-band", x: L + band * sel, y: T, width: band, height: ph }));
  const order = Object.keys(STATUS_COLORS);
  batches.forEach((b, i) => {
    let acc = 0;
    const x = L + band * i + band * 0.28;
    const w = band * 0.44;
    for (const s of order) {
      const n = b.status?.[s] || 0;
      if (!n) continue;
      kids.push(sv("rect", { x, y: yN(acc + n), width: w, height: yN(acc) - yN(acc + n), fill: STATUS_COLORS[s] },
        sv("title", {}, `${t("batch")} ${b.batch}: ${t(`st_${s}`)} ${n}`)));
      acc += n;
    }
    kids.push(sv("text", { class: "ax-label", x: L + band * i + band / 2, y: H - B + 18, "text-anchor": "middle" },
      `${t("batch")} ${b.batch}`));
    const hit = sv("rect", { class: "bar-hit", x: L + band * i, y: T, width: band, height: ph });
    hit.style.cursor = "pointer";
    hit.addEventListener("click", () => setGrpoStep(b.batch));
    kids.push(hit);
  });
  const pts = (vals) => vals.map((v, i) => `${L + band * i + band / 2},${y1(v)}`).join(" ");
  const pass = batches.map((b) => b.pass_rate || 0);
  kids.push(sv("polyline", { class: "line-pass", points: pts(pass) }));
  pass.forEach((v, i) => kids.push(sv("circle", { class: "dot-pass", cx: L + band * i + band / 2, cy: y1(v), r: 4 })));
  if (steps.length === batches.length) {
    const rew = steps.map((s) => Math.min(1, s.reward || 0));
    kids.push(sv("polyline", { class: "line-reward", points: pts(rew) }));
    rew.forEach((v, i) => kids.push(sv("circle", { class: "dot-reward", cx: L + band * i + band / 2, cy: y1(v), r: 4 })));
  }
  kids.push(sv("line", { class: "axis", x1: L, x2: W - R, y1: T + ph, y2: T + ph }));
  svgEl.replaceChildren(...kids);

  const used = order.filter((s) => batches.some((b) => b.status?.[s]));
  const sw = (color) => { const x = el("span", { class: "sw" }); x.style.background = color; return x; };
  document.getElementById("grpo-legend").replaceChildren(
    ...used.map((s) => el("span", {}, sw(STATUS_COLORS[s]), t(`st_${s}`))),
    el("span", {}, sw("var(--blue)"), t("lPass")),
    steps.length === batches.length ? el("span", {}, sw("var(--violet)"), t("lReward")) : null);
  const range = document.getElementById("grpo-step");
  range.min = String(batches[0].batch);
  range.max = String(batches[batches.length - 1].batch);
  range.value = String(ui.grpoStep);
  renderGrpoDetail();
}

function setGrpoStep(n) {
  ui.grpoStep = n;
  renderGrpo();
}

function renderGrpoDetail() {
  const tr = extras.training;
  const b = tr.batches.find((x) => x.batch === ui.grpoStep) || tr.batches[0];
  const idx = tr.batches.indexOf(b);
  const s = (tr.steps || [])[idx];
  document.getElementById("grpo-step-label").textContent =
    `${t("batch")} ${b.batch} / ${tr.batches.length} (${t("step")} ${b.global_step})`;
  const order = Object.keys(STATUS_COLORS).filter((k) => b.status?.[k]);
  const cards = [
    el("div", { class: "card" },
      el("h4", {}, `${t("sandboxSide")}: ${b.runtime}/${b.version}`),
      row(t("passRate"), fmt(b.pass_rate, 2)),
      row(t("customRate"), fmt(b.custom_kernel_rate, 2)),
      row(t("meanSpeedup"), b.mean_speedup === null ? "-" : `${fmt(b.mean_speedup, 3)}x`),
      row(t("evalTimes"), `${b.eval_p50_s} / ${b.eval_p95_s} ${t("sec")}`),
      row(t("wall"), `${b.batch_wall_s} ${t("sec")}`)),
    el("div", { class: "card" },
      el("h4", {}, `${t("evals")}: ${b.n}`),
      order.map((k) => row(t(`st_${k}`), b.status[k]))),
  ];
  if (s) {
    cards.push(el("div", { class: "card" },
      el("h4", {}, t("trainerSide")),
      row(t("rewardMean"), fmt(s.reward, 4)),
      row(t("rewardStd"), fmt(s.reward_std, 4)),
      row(t("loss"), fmt(s.loss, 4)),
      row(t("compLen"), s["completions/mean_length"]),
      row(t("stepTime"), `${s.step_time} ${t("sec")}`)));
  }
  document.getElementById("grpo-detail").replaceChildren(...cards);
}

async function playGrpo() {
  const button = document.getElementById("grpo-play");
  const tr = extras?.training;
  if (!tr?.batches?.length) return;
  if (ui.grpoTimer) { clearTimeout(ui.grpoTimer); ui.grpoTimer = null; button.textContent = t("stepPlay"); return; }
  let i = 0;
  button.textContent = t("termPause");
  const next = () => {
    setGrpoStep(tr.batches[i].batch);
    i += 1;
    if (i < tr.batches.length) ui.grpoTimer = setTimeout(next, 1300);
    else { ui.grpoTimer = null; button.textContent = t("stepPlay"); }
  };
  next();
}

function renderSim() {
  // The version switch comes from extras.simulation, or from the recording's own training events.
  const sim = extras?.simulation?.events?.length
    ? extras.simulation
    : { source: recording.source, events: recording.training || [] };
  const svgEl = document.getElementById("sim-chart");
  const panel = svgEl.closest(".panel");
  const batches = sim.events.filter((e) => e.event === "reward_batch");
  const sw = sim.events.find((e) => e.event === "sandbox_version_switch");
  panel.hidden = !batches.length;
  if (!batches.length) return;
  document.getElementById("sim-source").textContent = sim.source || "";
  const W = 900, H = 220, L = 46, R = 20, T = 30, B = 34;
  const pw = W - L - R, ph = H - T - B;
  const maxY = Math.ceil(Math.max(...batches.map((b) => b.eval_p50_s)) + 1);
  const band = pw / batches.length;
  const y = (v) => T + ph - (v / maxY) * ph;
  const versions = [...new Set(batches.map((b) => b.version))];
  const kids = [];
  for (let i = 0; i <= maxY; i += Math.max(1, Math.round(maxY / 4))) {
    kids.push(sv("line", { class: "grid", x1: L, x2: W - R, y1: y(i), y2: y(i) }));
    kids.push(sv("text", { class: "ax-label", x: L - 8, y: y(i) + 4, "text-anchor": "end" }, `${i}${t("sec")}`));
  }
  kids.push(sv("text", { class: "ax-label", x: 8, y: 16 }, `${t("evalMedian")} (${t("sec")})`));
  batches.forEach((b, i) => {
    const x = L + band * i + band * 0.15;
    kids.push(sv("rect", { x, y: y(b.eval_p50_s), width: band * 0.7, height: T + ph - y(b.eval_p50_s),
      class: `sim-v${versions.indexOf(b.version) % 3}` },
    sv("title", {}, `${t("step")} ${b.global_step}: ${b.runtime}/${b.version}, ${t("evalMedian")} ${b.eval_p50_s}${t("sec")}, ${t("passRate")} ${fmt(b.pass_rate, 2)}`)));
    if (i % 5 === 0 || i === batches.length - 1) {
      kids.push(sv("text", { class: "ax-label", x: L + band * i + band / 2, y: H - B + 16, "text-anchor": "middle" }, String(b.global_step)));
    }
  });
  let a = null;
  let bAfter = null;
  if (sw) {
    const i = batches.findIndex((b) => b.global_step >= sw.global_step);
    const x = L + band * i;
    kids.push(sv("line", { class: "switch-line", x1: x, x2: x, y1: T - 8, y2: T + ph }));
    kids.push(sv("text", { class: "val-label", x: x + 6, y: T - 12 }, `${sw.from} → ${sw.to} (${t("step")} ${sw.global_step})`));
    a = median(batches.slice(0, i).map((b) => b.eval_p50_s));
    bAfter = median(batches.slice(i).map((b) => b.eval_p50_s));
  }
  kids.push(sv("line", { class: "axis", x1: L, x2: W - R, y1: T + ph, y2: T + ph }));
  svgEl.replaceChildren(...kids);
  const steps = batches.map((b) => b.global_step);
  const contiguous = steps.every((s, i) => i === 0 || s === steps[i - 1] + 1);
  const summary = sw && contiguous
    ? fill(t("simSummary"), { n: batches.length, s: sw.global_step, from: sw.from, to: sw.to, a: fmt(a, 2), b: fmt(bAfter, 2) })
    : "";
  const p = document.getElementById("sim-summary");
  p.replaceChildren(summary, " ");
  if (transcript("rollout")) {
    const link = el("a", { href: "#defense" }, t("showRollout"));
    link.addEventListener("click", (e) => { e.preventDefault(); seekTerm("rollout", /switching the routing table/); });
    p.append(link);
  }
}

// ---------- 5. benchmark ----------
const METRICS = [
  { id: "p50", key: "mP50", get: (r) => r.eval_p50_s },
  { id: "p95", key: "mP95", get: (r) => r.eval_p95_s },
  { id: "cold", key: "mCold", get: (r) => median(r.cold_start_s || []) },
  { id: "tput", key: "mTput", get: (r) => (r.cold_start_s?.length ? r.throughput_eval_per_s / r.cold_start_s.length : r.throughput_eval_per_s) },
  { id: "speed", key: "mSpeed", get: (r) => (r.gpu ? r.speedup_median : null) },
];

function renderBenchTabs() {
  const passes = extras?.bench?.passes || [];
  const section = document.getElementById("bench");
  if (!passes.length) { section.hidden = true; return; }
  const mk = (boxId, items, current, onPick) => {
    document.getElementById(boxId).replaceChildren(...items.map(([id, label]) => {
      const b = el("button", { type: "button", class: "tab", role: "tab", "aria-selected": String(id === current) }, label);
      b.addEventListener("click", () => onPick(id));
      return b;
    }));
  };
  mk("bench-metric", METRICS.map((m) => [m.id, t(m.key)]), ui.benchMetric, (id) => { ui.benchMetric = id; renderBench(); });
  mk("bench-pass", ["pass2", "pass1"].filter((p) => passes.some((x) => x.label === p)).map((p) => [p, t(p)]), ui.benchPass,
    (id) => { ui.benchPass = id; renderBench(); });
}

function renderBench() {
  const passes = extras?.bench?.passes || [];
  if (!passes.length) return;
  renderBenchTabs();
  const metric = METRICS.find((m) => m.id === ui.benchMetric);
  const rows = [...benchRows(ui.benchPass)];
  for (const u of extras.bench.unmeasured || []) rows.splice(2, 0, { ...u, unmeasured: true });
  const W = 900, L = 210, R = 90, T = 10, rowH = 40;
  const H = T + rows.length * rowH + 10;
  const svgEl = document.getElementById("bench-chart");
  svgEl.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const values = rows.map((r) => (r.unmeasured ? null : metric.get(r)));
  const maxV = Math.max(...values.filter((v) => typeof v === "number"), 0.001);
  const pw = W - L - R;
  const kids = [];
  rows.forEach((r, i) => {
    const y = T + i * rowH;
    kids.push(sv("text", { class: "val-label", x: 10, y: y + 17 }, r.runtime));
    kids.push(sv("text", { class: "ax-label", x: 10, y: y + 33 }, [r.instance, r.gpu].filter(Boolean).join(", ") || "CPU"));
    const v = values[i];
    if (r.unmeasured) {
      kids.push(sv("rect", { class: "bar-na", x: L, y: y + 8, width: pw * 0.35, height: 22, rx: 3 }));
      kids.push(sv("text", { class: "ax-label", x: L + 10, y: y + 24 }, t("notMeasured")));
      return;
    }
    if (typeof v !== "number") {
      kids.push(sv("text", { class: "ax-label", x: L + 4, y: y + 24 }, t("na")));
      return;
    }
    const w = Math.max(2, (v / maxV) * pw);
    const details = [`${r.runtime}: ${t(metric.key)} ${fmt(v, 3)}`,
      `${t("pods")} ${r.cold_start_s?.length ?? "-"}, cold start ${(r.cold_start_s || []).join(", ")} ${t("sec")}`,
      `${t("evalTimes")} ${r.eval_p50_s} / ${r.eval_p95_s} ${t("sec")}`,
      `${t("throughput")} ${r.throughput_eval_per_s} eval/s, ${r.ok}/${r.requests} ok`,
      r.gpu ? `speedup ${r.speedup_median}, ${t("refMs")} ${r.ref_ms_median}` : `${t("refMs")} ${r.ref_ms_median}`].join("\n");
    kids.push(sv("rect", { class: r.gpu ? "bar-gpu" : "bar-cpu", x: L, y: y + 8, width: w, height: 22, rx: 3 }, sv("title", {}, details)));
    kids.push(sv("text", { class: "val-label", x: L + w + 8, y: y + 24 }, fmt(v, metric.id === "tput" ? 3 : metric.id === "cold" ? 1 : 3)));
  });
  svgEl.replaceChildren(...kids);
  const notes = [t("benchNoteGpu")];
  if (ui.benchPass === "pass1" && metric.id === "cold") notes.unshift(t("benchNotePass1"));
  if (metric.id === "speed") notes.push(t("benchNoteSpeed"));
  document.getElementById("bench-note").textContent = notes.join(" ");
}

// ---------- wiring ----------
function renderAll() {
  renderStatic();
  renderKpis();
  renderArch();
  renderSubmissions();
  renderPools();
  renderAttacks();
  renderTermTabs();
  renderGrpo();
  renderSim();
  renderBench();
}

async function loadJson(response) {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function main() {
  recording = await loadJson(await fetch("data/recording.json", { cache: "no-cache" }));
  try {
    extras = await loadJson(await fetch("data/extras.json", { cache: "no-cache" }));
  } catch {
    extras = null;
  }
  const wanted = new URLSearchParams(window.location.search).get("lang");
  if (wanted === "ko" || wanted === "en") lang = wanted;
  else if (navigator.language && !navigator.language.startsWith("ko")) lang = "en";
  document.getElementById("lang").addEventListener("click", () => {
    lang = lang === "ko" ? "en" : "ko";
    renderAll();
  });
  document.getElementById("flow-play").addEventListener("click", playFlow);
  document.getElementById("run").addEventListener("click", runScoring);
  document.getElementById("term-play").addEventListener("click", playTerm);
  document.getElementById("term-all").addEventListener("click", showAllTerm);
  document.getElementById("grpo-play").addEventListener("click", playGrpo);
  document.getElementById("grpo-step").addEventListener("input", (e) => setGrpoStep(Number(e.target.value)));
  renderAll();
}

main().catch((err) => {
  document.getElementById("source").textContent = `failed to load recording: ${err}`;
});
