"""Script reference (docs/reference/scripts): what the hands-on scripts do, in order, and where each one acts.

Every box and edge comes from docs/reference/scripts.md and docs/handson/index.md. Shared geometry draws
both languages.
"""

from __future__ import annotations

from figlib import ACCENT, ACCENT_FILL, INK, MUTED_STROKE, SMALL, Figure, text_width
from figures_fb import dot, mbox

T = {
    "ko": {
        "pc": "작업 PC", "aws": "AWS 계정", "cluster": "클러스터 안",
        "s01": ["01_check_prereqs.sh", "도구와 쿼터 조회, 만드는 것 없음"],
        "s02": ["02_create_cluster.sh", "CDK 스택: VPC, private EKS,", "노드 그룹, access instance"],
        "tunnel": ["cdk/tunnel.sh", "SSM 포트 포워딩 127.0.0.1:8443", "열어 두기, 이후 kubectl은 모두 이 터널로"],
        "s03": ["03_build_push_images.sh", "config.env에 넣을 export 줄 출력"],
        "ecr": ["ECR", "03이 push한 sandbox, trainer, control 이미지"],
        "s04": ["04_install_gpu_stack.sh", "NVIDIA device plugin, gvisor RuntimeClass, smoke pod"],
        "s05": ["05_setup_namespaces_auth.sh", "네임스페이스, NetworkPolicy, JWKS, routing ConfigMap"],
        "s06": ["06_deploy_sandboxes.sh", "샌드박스 pool: Deployment + headless Service"],
        "verify": ["ops/verify.sh", "격리, 연결 차단, golden verdict(probe Job) 확인"],
        "s07": ["07_run_grpo.sh", "GRPO 학습 Job (시나리오 A)"],
        "s08": ["08_cleanup.sh", "CDK 스택 삭제 (B는 hyperpod/delete.sh 먼저)"],
        "kata": ["kata/cpu_nodes.sh, kata/gpu_nodes.sh", "Kata 런타임 설치, 04와 05 사이"],
        "alt": ["07 대신", "ops/simulate.sh (시나리오 C)", "hyperpod/run_grpo.sh (시나리오 B)"],
        "rollout": ["ops/rollout.sh", "07 실행 중: v2 pool 배포, routing 전환"],
        "end": "끝", "legend": "점선 상자: 선택 단계",
    },
    "en": {
        "pc": "Workstation", "aws": "AWS account", "cluster": "In the cluster",
        "s01": ["01_check_prereqs.sh", "reads tools and quotas, creates nothing"],
        "s02": ["02_create_cluster.sh", "CDK stack: VPC, private EKS,", "node groups, access instance"],
        "tunnel": ["cdk/tunnel.sh", "SSM port forward on 127.0.0.1:8443", "keep it open: later kubectl goes through it"],
        "s03": ["03_build_push_images.sh", "prints export lines for config.env"],
        "ecr": ["ECR", "sandbox, trainer, control images pushed by 03"],
        "s04": ["04_install_gpu_stack.sh", "NVIDIA device plugin, gvisor RuntimeClass, smoke pod"],
        "s05": ["05_setup_namespaces_auth.sh", "namespaces, NetworkPolicy, JWKS, routing ConfigMap"],
        "s06": ["06_deploy_sandboxes.sh", "sandbox pool: Deployment + headless Service"],
        "verify": ["ops/verify.sh", "isolation, blocked egress, golden verdicts (probe Job)"],
        "s07": ["07_run_grpo.sh", "GRPO training Job (scenario A)"],
        "s08": ["08_cleanup.sh", "deletes the CDK stack (B: hyperpod/delete.sh first)"],
        "kata": ["kata/cpu_nodes.sh, kata/gpu_nodes.sh", "Kata runtimes, between 04 and 05"],
        "alt": ["instead of 07", "ops/simulate.sh (scenario C)", "hyperpod/run_grpo.sh (scenario B)"],
        "rollout": ["ops/rollout.sh", "while 07 runs: v2 pool, routing switch"],
        "end": "end", "legend": "dashed box: optional step",
    },
}

OPTIONAL = {"fill": "#FFFFFF", "stroke": MUTED_STROKE, "dash": "5 4"}


def reference_scripts(lang: str) -> Figure:
    """docs/reference/scripts: the main order 01, 02, tunnel, 03 to 07, verify and 08, where each script acts
    (workstation, AWS account, cluster), and the optional Kata, rollout, simulate and HyperPod steps."""
    t = T[lang]
    fig = Figure(760, 744)
    mx, mw = 32, 360            # main column (workstation boxes and in-cluster steps)
    ax, aw = 440, 288           # AWS account boxes and the optional in-cluster steps
    cx = mx + mw / 2            # vertical connectors of the main path
    h = 46

    # Workstation and AWS account, side by side
    fig.container(16, 16, 392, 246, t["pc"], icon="device-desktop")
    fig.container(424, 16, 320, 246, t["aws"], icon="cloud")
    y01, yt, y03 = 48, 112, 200
    mbox(fig, mx, y01, mw, h, t["s01"], gid="n:s01")
    mbox(fig, ax, y01, aw, yt + 62 - y01, t["s02"], gid="n:s02")
    mbox(fig, mx, yt, mw, 62, t["tunnel"], gid="n:tunnel")
    mbox(fig, mx, y03, mw, h, t["s03"], gid="n:s03")
    mbox(fig, ax, y03, aw, h, t["ecr"], gid="n:ecr")
    fig.arrow([(mx + mw, y01 + h / 2), (ax - 2, y01 + h / 2)])
    fig.arrow([(ax, yt + 31), (mx + mw + 2, yt + 31)])
    fig.arrow([(cx, yt + 62), (cx, y03 - 2)])
    fig.arrow([(mx + mw, y03 + h / 2), (ax - 2, y03 + h / 2)])

    # In the cluster: 04, 05, 06, verify, 07 down the main column, optional steps on the right
    top = 280
    # 04 to 05 gets a taller gap so the Kata junction sits clear of the arrowhead
    rows = {"s04": top + 32}
    rows.update({k: top + 32 + h + 36 + 68 * i for i, k in enumerate(("s05", "s06", "verify", "s07"))})
    zone_h = rows["s07"] + h + 16 - top
    fig.container(16, top, 728, zone_h, t["cluster"], icon="server")
    assert 46 + text_width(t["cluster"], SMALL) + 8 <= cx, "cluster title runs into the 03 -> 04 connector"
    for k, y in rows.items():
        style = {"fill": ACCENT_FILL, "stroke": ACCENT} if k == "s06" else {}
        mbox(fig, mx, y, mw, h, t[k], gid=f"n:{k}", **style)
    fig.arrow([(cx, y03 + h), (cx, rows["s04"] - 2)])
    keys = list(rows)
    for a, b in zip(keys, keys[1:]):
        fig.arrow([(cx, rows[a] + h), (cx, rows[b] - 2)])

    # Kata: joins the path between 04 and 05
    jy = rows["s04"] + h + 12
    mbox(fig, ax, jy - h / 2, aw, h, t["kata"], gid="n:kata", **OPTIONAL)
    dot(fig, cx, jy, MUTED_STROKE)
    fig.arrow([(cx + 3, jy), (ax - 2, jy)], color=MUTED_STROKE, dash="5 4")
    # simulate (C) or HyperPod training (B) instead of 07
    vy = rows["verify"] + h / 2
    mbox(fig, ax, vy - 31, aw, 62, t["alt"], gid="n:alt", **OPTIONAL)
    fig.arrow([(mx + mw, vy), (ax - 2, vy)], color=MUTED_STROKE, dash="5 4")
    # rollout while 07 runs
    ry = rows["s07"]
    assert vy + 31 + 10 <= ry, "the instead-of-07 box runs into the rollout box"
    mbox(fig, ax, ry, aw, h, t["rollout"], gid="n:rollout", **OPTIONAL)
    fig.arrow([(mx + mw, ry + h / 2), (ax - 2, ry + h / 2)], color=MUTED_STROKE, dash="5 4")

    # 08 closes the run
    y08 = top + zone_h + 22
    fig.arrow([(cx, rows["s07"] + h), (cx, y08 - 2)])
    mbox(fig, mx, y08, mw, h, t["s08"], gid="n:s08")
    ey = y08 + h / 2
    ex = mx + mw + 30
    fig.arrow([(mx + mw, ey), (ex - 11, ey)])
    fig.parts.append(f'<circle cx="{ex}" cy="{ey}" r="9" fill="#FFFFFF" stroke="{INK}" stroke-width="1.6"/>')
    fig.parts.append(f'<circle cx="{ex}" cy="{ey}" r="5" fill="{INK}"/>')
    fig.text(ex + 16, ey + 4.5, t["end"], size=SMALL, bold=True, anchor="start")

    # legend
    lx = 736 - text_width(t["legend"], SMALL) - 34
    assert lx >= ex + 16 + text_width(t["end"], SMALL, bold=True) + 24, "legend runs into the end mark"
    fig.rect(lx, ey - 7, 26, 14, rx=3, **{k: v for k, v in OPTIONAL.items()})
    fig.text(lx + 34, ey + 4.5, t["legend"], size=SMALL, anchor="start")
    return fig


FIGURES = {"reference-scripts": reference_scripts}
