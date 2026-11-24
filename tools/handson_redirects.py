"""Publish redirects for hands-on URLs shared before the guide was reorganized."""

import json
import posixpath
from html import escape
from pathlib import Path


# Paths are relative to each language's site root. Data files retain their original URLs.
PAGES = {
    "getting_started": "handson/start/",
    "handson/00_overview": "handson/",
    "handson/01_cluster_and_images": "handson/common/01_provision/cdk/",
    "handson/02_gvisor": "handson/common/02_runtimes/gvisor/",
    "handson/03_kata": "handson/common/02_runtimes/kata/",
    "handson/04_sandbox_pools": "handson/common/03_pools/details/",
    "handson/05_grpo_training": "handson/scenarios/a/grpo/",
    "handson/06_sandbox_update": "handson/scenarios/a/pool_update/",
    "handson/07_hyperpod": "handson/scenarios/b/",
    "handson/07_hyperpod_b1": "handson/scenarios/b/b1/",
    "handson/07_hyperpod_b2": "handson/scenarios/b/b2/",
    "handson/scenario_a": "handson/scenarios/a/",
    "handson/10_cpu_only": "handson/scenarios/c/",
    "handson/08_benchmark": "handson/benchmarks/",
    "handson/11_multi_turn": "handson/extensions/multi_turn/",
    "handson/99_cleanup": "handson/cleanup/",
    "handson/09_demo_site": "reference/demo_site/",
}

# Some sections moved from a scenario walkthrough into one of the three shared steps.
# Group the old bookmark names by their new destination.
SECTIONS = {
    "handson/07_hyperpod_b2": {
        "handson/common/01_provision/hyperpod/#{anchor}": (
            "시작-전에-확인할-쿼터",
            "hyperpod에서-클러스터-만들기",
            "워커가-등록됐는지-확인하기",
            "check-regional-quotas",
            "create-the-cluster-through-hyperpod",
            "check-the-four-workers",
        ),
        "handson/common/02_runtimes/b2_workers/#{anchor}": (
            "채점-노드의-드라이버와-학습-오퍼레이터-준비하기",
            "prepare-the-sandbox-drivers-and-training-operator",
        ),
        "handson/common/03_pools/#__tabbed_1_3": (
            "두-노드에-채점-pool-배포하기",
            "두-노드에-채점-풀-배포하기",
            "deploy-two-graders",
        ),
    },
    "handson/07_hyperpod_b1": {
        "handson/common/01_provision/#__tabbed_1_2": (
            "시작-전-확인",
            "b1-단계",
            "1-클러스터",
            "before-you-begin",
            "b1-steps",
            "1-cluster",
        ),
        "handson/common/01_provision/cdk/#__tabbed_2_2": (
            "2-이미지",
            "2-images",
        ),
        "handson/common/02_runtimes/#__tabbed_1_2": (
            "3-gpu-stack과-런타임",
            "3-gpu-stack-and-runtimes",
        ),
        "handson/common/02_runtimes/b1_trainer/": (
            "4-hyperpod-클러스터",
            "4-hyperpod-cluster",
        ),
        "handson/common/03_pools/#__tabbed_1_2": (
            "5-namespace와-샌드박스-pool",
            "5-namespace와-샌드박스-풀",
            "5-namespaces-and-sandbox-pools",
        ),
    },
    "handson/10_cpu_only": {
        "handson/common/01_provision/#__tabbed_1_4": (
            "준비",
            "1단계-사전-확인-01_check_prereqssh",
            "2단계-gpu-없는-클러스터와-c8i-노드-02_create_clustersh",
            "preparation",
            "step-1-prerequisites-01_check_prereqssh",
            "step-2-a-cluster-without-gpus-with-the-c8i-node-02_create_clustersh",
        ),
        "handson/common/01_provision/cdk/#__tabbed_2_3": (
            "3단계-이미지-두-개만-빌드-03_build_push_imagessh",
            "step-3-build-only-two-images-03_build_push_imagessh",
        ),
        "handson/common/02_runtimes/kata/#kata-cpu": (
            "4단계-c8i-노드에-세-런타임-설치-katacpu_nodessh",
            "step-4-three-runtimes-on-the-c8i-node-katacpu_nodessh",
        ),
        "handson/common/03_pools/#__tabbed_1_4": (
            "5단계-네임스페이스와-routing-표-05_setup_namespaces_authsh",
            "6단계-pool-세-개-배포와-검증-06_deploy_sandboxessh-opsverifysh",
            "6단계-풀-세-개-배포와-검증-06_deploy_sandboxessh-opsverifysh",
            "cpu-pools",
            "step-5-namespaces-and-the-routing-table-05_setup_namespaces_authsh",
            "step-6-deploy-and-verify-three-pools-06_deploy_sandboxessh-opsverifysh",
        ),
    },
    "handson/scenario_a": {
        "handson/common/01_provision/#__tabbed_1_1": ("prepare",),
        "handson/common/01_provision/cdk/#__tabbed_1_1": ("cluster",),
        "handson/common/02_runtimes/#__tabbed_1_1": ("gpu",),
        "handson/common/03_pools/#__tabbed_1_1": ("pool",),
    },
    "handson/07_hyperpod": {
        "handson/scenarios/b/b2/": ("b2",),
        "reference/hyperpod_custom_ami/#{anchor}": (
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
            "managing-the-custom-ami",
        ),
        "handson/scenarios/b/b1/#{anchor}": (
            "구성",
            "소요-시간과-비용",
            "6-학습",
            "hyperpodpytorchjob-템플릿",
            "확인-방법",
            "kata를-hyperpod-노드에서-쓸-수-없는-이유",
            "적용-범위와-한계",
            "정리",
            "layout",
            "time-and-cost",
            "6-training",
            "the-hyperpodpytorchjob-template",
            "how-to-verify",
            "why-kata-cannot-run-on-hyperpod-nodes",
            "scope-and-limits",
            "cleanup",
        ),
        "handson/common/01_provision/#__tabbed_1_2": (
            "시작-전-확인",
            "b1-단계",
            "1-클러스터",
            "before-you-begin",
            "b1-steps",
            "1-cluster",
        ),
        "handson/common/01_provision/cdk/#__tabbed_2_2": (
            "2-이미지",
            "2-images",
        ),
        "handson/common/02_runtimes/#__tabbed_1_2": (
            "3-gpu-stack과-런타임",
            "3-gpu-stack-and-runtimes",
        ),
        "handson/common/02_runtimes/b1_trainer/": (
            "4-hyperpod-클러스터",
            "4-hyperpod-cluster",
        ),
        "handson/common/03_pools/#__tabbed_1_2": (
            "5-namespace와-샌드박스-pool",
            "5-namespace와-샌드박스-풀",
            "5-namespaces-and-sandbox-pools",
        ),
    },
    "handson/09_demo_site": {
        "reference/demo_site/": (
            "데모-배포-가이드",
            "demo-deployment-guide",
        ),
    },
}


def on_post_build(config):
    i18n = config.plugins["i18n"]
    root = Path(config.site_dir)
    if not i18n.is_default_language_build:
        root /= i18n.current_language
    for old, new in PAGES.items():
        relative = posixpath.relpath(new, old) + "/"
        sections = {}
        for target, bookmarks in SECTIONS.get(old, {}).items():
            path, sep, fragment = target.partition("#")
            dest = posixpath.relpath(path, old) + "/" + sep + fragment
            for bookmark in bookmarks:
                sections[bookmark] = dest.replace("{anchor}", bookmark)
        target_dir = root / old
        target_dir.mkdir(parents=True, exist_ok=True)
        link_text = "새 페이지 열기" if i18n.current_language == "ko" else "Open the new page"
        href = escape(relative, quote=True)
        page = f'''<!doctype html><html lang="{i18n.current_language}"><head><meta charset="utf-8">
<title>{link_text}</title><meta name="robots" content="noindex"><link rel="canonical" href="{href}">
<noscript><meta http-equiv="refresh" content="0;url={href}"></noscript></head>
<body><a href="{href}">{link_text}</a><script>
const moved = {json.dumps(sections, ensure_ascii=False)};
let anchor = location.hash.slice(1);
try {{ anchor = decodeURIComponent(anchor); }} catch {{ /* Keep malformed bookmarks as supplied. */ }}
const url = new URL(document.querySelector("a").href);
if (Object.hasOwn(moved, anchor)) {{ url.href = new URL(moved[anchor], document.baseURI).href; }}
else {{ url.hash = location.hash; }}
url.search = location.search;
location.replace(url.href);
</script></body></html>'''
        (target_dir / "index.html").write_text(page, encoding="utf-8")
