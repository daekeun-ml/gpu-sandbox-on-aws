// Replay demo: renders data/recording.json. No network calls other than that same-origin
// fetch, and every value from the recording is inserted as text (never as HTML), because
// recordings contain strings produced by evaluated code (error tails, violations).
"use strict";

const TEXT = {
  ko: {
    title: "GPU Sandbox on AWS 재생 데모",
    lede: "모델이 쓴 GPU 코드를 격리된 샌드박스에서 채점하는 on-policy RL의 한 장면을, 실제 실행 기록으로 다시 보여 줍니다. 이 페이지는 클러스터나 GPU에 접속하지 않습니다.",
    sourceLabel: "기록 출처:",
    s1: "1. 격리 런타임과 증거",
    s1hint: "샌드박스 안에서 본 커널 버전, GPU, egress 차단 여부입니다. gVisor는 자체 커널 버전을, Kata는 guest VM 커널을 보고합니다.",
    s2: "2. 제출물 채점 재생",
    s2hint: "정답, 오답, reward hacking 시도를 고르면 각 샌드박스 버전의 판정과 reward 구성 요소를 보여 줍니다.",
    pick: "제출물",
    task: "태스크와 기준 구현",
    candidate: "제출된 코드",
    verdicts: "판정",
    s3: "3. 학습 중 샌드박스 업데이트",
    s3hint: "reward 배치마다 어떤 샌드박스 버전이 채점했는지 보여 줍니다. 버전 전환은 배치 경계에서만 일어납니다.",
    footer: "기록 재생 데모입니다. 수치는 표시된 기록 출처의 환경에서 얻은 값이며 다른 환경의 성능을 뜻하지 않습니다.",
    guide: "가이드북",
    repo: "GitHub 저장소",
    runtime: "런타임", version: "샌드박스 버전", kernel: "샌드박스 안 커널", gpu: "GPU",
    egress: "egress 차단", yes: "확인됨", no: "열림", none: "없음 (CPU)",
    status: "판정", expected: "기대 판정", speedup: "speedup", ms: "기준/후보 ms",
    custom: "커스텀 커널", flags: "플래그", violations: "정책 위반", reward: "reward (format, correctness, speedup = 합계)",
    excluded: "인프라 오류: 이 샘플은 group baseline에서 제외",
    step: "step", batch: "배치", passRate: "통과율", served: "채점 버전", switchTo: "샌드박스 버전 전환",
    noTraining: "이 기록에는 학습 이벤트가 없습니다.",
  },
  en: {
    title: "GPU Sandbox on AWS replay demo",
    lede: "A replay of one moment of on-policy RL where model-written GPU code is scored in isolated sandboxes, built from a real execution record. This page never connects to a cluster or a GPU.",
    sourceLabel: "Recording source:",
    s1: "1. Isolation runtimes and evidence",
    s1hint: "Kernel version, GPU and egress status as seen from inside each sandbox. gVisor reports its own kernel version; Kata reports the guest VM kernel.",
    s2: "2. Replay a submission",
    s2hint: "Pick a correct, wrong or reward-hacking submission to see each sandbox version's verdict and reward components.",
    pick: "Submission",
    task: "Task and reference",
    candidate: "Submitted code",
    verdicts: "Verdicts",
    s3: "3. Updating the sandbox during training",
    s3hint: "Which sandbox version scored each reward batch. Versions switch only at batch boundaries.",
    footer: "This is a replay. Numbers come from the environment named in the recording source and say nothing about other environments.",
    guide: "Guidebook",
    repo: "GitHub repository",
    runtime: "Runtime", version: "Sandbox version", kernel: "Kernel inside sandbox", gpu: "GPU",
    egress: "Egress blocked", yes: "verified", no: "open", none: "none (CPU)",
    status: "Verdict", expected: "Expected", speedup: "Speedup", ms: "Ref/cand ms",
    custom: "Custom kernel", flags: "Flags", violations: "Policy violations", reward: "Reward (format, correctness, speedup = total)",
    excluded: "Infrastructure error: sample excluded from the group baseline",
    step: "step", batch: "batch", passRate: "Pass rate", served: "Scored by", switchTo: "Sandbox version switch",
    noTraining: "This recording has no training events.",
  },
};

let lang = "ko";
let recording = null;

function t(key) {
  return TEXT[lang][key] ?? key;
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else node.setAttribute(k, v);
  }
  for (const child of children) {
    node.append(child instanceof Node ? child : document.createTextNode(String(child ?? "")));
  }
  return node;
}

function row(label, value) {
  return el("div", { class: "kv" }, el("span", { class: "k" }, label), el("span", { class: "v" }, value));
}

function statusChip(status) {
  const good = status === "ok";
  const infra = status === "sandbox_error";
  return el("span", { class: `chip ${good ? "good" : infra ? "infra" : "bad"}` }, status);
}

function renderStatic() {
  document.documentElement.lang = lang;
  for (const node of document.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.dataset.i18n);
  }
  document.getElementById("lang").textContent = lang === "ko" ? "EN" : "KO";
}

function renderPools() {
  const box = document.getElementById("pools");
  box.replaceChildren();
  for (const pool of recording.pools) {
    const info = pool.info || {};
    box.append(el("div", { class: "card" },
      el("h3", {}, pool.runtime),
      row(t("version"), info.sandbox_version),
      row(t("kernel"), info.kernel_release),
      row(t("gpu"), info.gpu || t("none")),
      row(t("egress"), info.egress_blocked ? t("yes") : t("no")),
    ));
  }
}

function renderGoldenPicker() {
  const select = document.getElementById("golden");
  const current = select.value;
  select.replaceChildren();
  for (const g of recording.goldens) {
    select.append(el("option", { value: g.name }, `${g.name} (${g.task_id})`));
  }
  if (current) select.value = current;
}

function fmt(value, digits = 3) {
  return typeof value === "number" ? value.toFixed(digits) : value ?? "";
}

function renderGolden() {
  const name = document.getElementById("golden").value;
  const golden = recording.goldens.find((g) => g.name === name);
  if (!golden) return;
  const task = recording.tasks[golden.task_id];
  document.getElementById("task-desc").textContent = `${golden.task_id}: ${task.description} (${task.input_spec})`;
  document.getElementById("reference").textContent = task.reference;
  document.getElementById("candidate").textContent = golden.code;

  const box = document.getElementById("verdicts");
  box.replaceChildren();
  for (const pool of recording.pools) {
    const v = pool.results[name];
    if (!v) continue;
    const r = v.reward || {};
    const rewardText = r.total === null || r.total === undefined
      ? t("excluded")
      : `${fmt(r.format, 2)}, ${fmt(r.correctness, 2)}, ${fmt(r.speedup, 2)} = ${fmt(r.total, 2)}`;
    const card = el("div", { class: "card" },
      el("h3", {}, pool.runtime, " ", statusChip(v.status)),
      row(t("expected"), v.expected_status),
      row(t("speedup"), fmt(v.speedup, 3)),
      row(t("ms"), v.ref_ms ? `${fmt(v.ref_ms, 4)} / ${fmt(v.cand_ms, 4)}` : ""),
      row(t("custom"), String(Boolean(v.custom_kernel))),
      row(t("flags"), (v.flags || []).join(", ")),
      row(t("violations"), (v.violations || []).join("; ")),
      row(t("reward"), rewardText),
    );
    if (v.error) card.append(el("pre", { class: "code small" }, v.error));
    box.append(card);
  }
}

function renderTimeline() {
  const list = document.getElementById("timeline");
  list.replaceChildren();
  if (!recording.training.length) {
    list.append(el("li", {}, t("noTraining")));
    return;
  }
  for (const e of recording.training) {
    if (e.event === "sandbox_version_switch") {
      list.append(el("li", { class: "switch" }, `${t("switchTo")}: ${e.from} → ${e.to} (${t("step")} ${e.global_step})`));
      continue;
    }
    const served = Object.entries(e.served_versions || {}).map(([k, n]) => `${k} x${n}`).join(", ");
    list.append(el("li", {},
      el("strong", {}, `${t("step")} ${e.global_step}`), ` ${t("batch")} ${e.batch}: `,
      `${t("served")} ${served}, ${t("passRate")} ${fmt(e.pass_rate, 2)}`,
    ));
  }
}

function renderAll() {
  renderStatic();
  document.getElementById("source").textContent = `${recording.source} (${recording.recorded_at})`;
  renderPools();
  renderGoldenPicker();
  renderGolden();
  renderTimeline();
}

async function main() {
  const response = await fetch("data/recording.json", { cache: "no-cache" });
  recording = await response.json();
  document.getElementById("lang").addEventListener("click", () => {
    lang = lang === "ko" ? "en" : "ko";
    renderAll();
  });
  document.getElementById("golden").addEventListener("change", renderGolden);
  renderAll();
}

main().catch((err) => {
  document.getElementById("source").textContent = `failed to load recording: ${err}`;
});
