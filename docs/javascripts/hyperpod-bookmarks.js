// The HyperPod overview used to contain both the B1 lab and the custom AMI reference.
// Follow published section links while keeping the overview as the scenario selector.
function followLegacyHyperPodLink() {
  const hash = location.hash.slice(1);
  if (!hash) return;
  let section;
  try {
    section = decodeURIComponent(hash);
  } catch {
    return;
  }
  const legacyAmiSections = new Set([
    "기존-b2-custom-ami-경로",
    "custom-ami가-필요한-이유",
    "1단계-클러스터-만들기",
    "2단계-custom-ami-빌드-hyperpodbuild_b2_amish",
    "3단계-sandbox-인스턴스-그룹-추가-hyperpodcreatesh---b2",
    "4단계-노드-확인-hyperpodcheck_gvisorsh",
    "5단계-pool-배포-검증-학습",
    "5단계-풀-배포-검증-학습",
    "custom-ami-관리",
    "earlier-b2-custom-ami-path",
    "why-a-custom-ami-is-needed",
    "step-1-create-the-cluster",
    "step-2-bake-the-custom-ami-hyperpodbuild_b2_amish",
    "step-3-attach-the-sandbox-instance-group-hyperpodcreatesh---b2",
    "step-4-check-the-nodes-hyperpodcheck_gvisorsh",
    "step-5-deploy-verify-and-train",
    "managing-the-custom-ami"
  ]);
  const legacyTrainingSections = new Set([
    "구성",
    "시작-전-확인",
    "소요-시간과-비용",
    "b1-단계",
    "1-클러스터",
    "2-이미지",
    "3-gpu-stack과-런타임",
    "4-hyperpod-클러스터",
    "5-namespace와-샌드박스-pool",
    "5-namespace와-샌드박스-풀",
    "6-학습",
    "hyperpodpytorchjob-템플릿",
    "확인-방법",
    "kata를-hyperpod-노드에서-쓸-수-없는-이유",
    "적용-범위와-한계",
    "정리",
    "layout",
    "before-you-begin",
    "time-and-cost",
    "b1-steps",
    "1-cluster",
    "2-images",
    "3-gpu-stack-and-runtimes",
    "4-hyperpod-cluster",
    "5-namespaces-and-sandbox-pools",
    "6-training",
    "the-hyperpodpytorchjob-template",
    "how-to-verify",
    "why-kata-cannot-run-on-hyperpod-nodes",
    "scope-and-limits",
    "cleanup"
  ]);
  let page;
  if (section === "b2") page = "../07_hyperpod_b2/";
  else if (legacyAmiSections.has(section)) page = "../../reference/hyperpod_custom_ami/";
  else if (legacyTrainingSections.has(section)) page = "../07_hyperpod_b1/";
  else return;
  const target = new URL(page, location.href);
  target.search = location.search;
  if (section !== "b2") target.hash = location.hash;
  location.replace(target.href);
}

followLegacyHyperPodLink();
window.addEventListener("hashchange", followLegacyHyperPodLink);
