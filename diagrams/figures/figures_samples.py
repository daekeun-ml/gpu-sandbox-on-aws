"""Pain point schematics. Each function draws one figure in one language from shared geometry.

Every box and edge comes from the page's own text (the source page is named in each docstring).
"""

from __future__ import annotations

from figlib import ACCENT, ACCENT_FILL, GREY_FILL, INK, MUTED_STROKE, RED, RED_FILL, Figure

T = {
    "ko": {
        "b01.a": "격리 없이 채점",
        "b01.b": "샌드박스에서 채점: 위험별 방어 층",
        "b01.code": "모델이 쓴 코드", "b01.code_sub": "채점하려고 실행",
        "b01.server": "내 서버 (노드)", "b01.pod": "샌드박스 pod",
        "b01.r1": "파일", "b01.r1s": "서버의 파일 시스템",
        "b01.r2": "자격 증명", "b01.r2s": "노드의 AWS 권한 (IMDS)",
        "b01.r3": "인터넷", "b01.r3s": "외부 서버",
        "b01.a1": "/etc/shadow 열기", "b01.a2": "169.254.169.254 접속", "b01.a3": "결과를 외부로 전송",
        "b01.b1": "pod 보안 설정, 격리 런타임", "b01.b2": "NetworkPolicy, IMDSv2 hop limit 1",
        "b01.b3": "egress 차단 (NetworkPolicy)",
        "h06.a": "두 버전이 나눠 채점하는 group 하나 (rolling update 중)",
        "h06.b": "group마다 한 버전 고정 (교체는 배치 사이)",
        "h06.prompt": "prompt", "h06.prompt_sub": "1개",
        "h06.ans": "completion", "h06.ans_sub": "group 하나",
        "h06.v1": "v1 풀", "h06.v1s": "seed 3개, cap 없음",
        "h06.v2": "v2 풀", "h06.v2s": "seed 5개, cap 10배",
        "h06.adv": "advantage", "h06.adv_sub": "group 평균과 비교",
        "h06.bad": "학습 신호에 섞이는", "h06.bad_sub": "기준 차이",
        "h06.good": "completion 품질만", "h06.good_sub": "advantage에 반영",
        "h06.some": "일부", "h06.rest": "나머지", "h06.all": "전부", "h06.next": "다음 배치",
    },
    "en": {
        "b01.a": "Scoring without isolation",
        "b01.b": "Scoring in a sandbox: a different layer stops each risk",
        "b01.code": "Model-written code", "b01.code_sub": "run to score it",
        "b01.server": "My server (node)", "b01.pod": "Sandbox pod",
        "b01.r1": "Files", "b01.r1s": "server file system",
        "b01.r2": "Credentials", "b01.r2s": "node AWS role (IMDS)",
        "b01.r3": "Internet", "b01.r3s": "outside servers",
        "b01.a1": "open /etc/shadow", "b01.a2": "connect to 169.254.169.254", "b01.a3": "send results out",
        "b01.b1": "pod security settings, isolation runtime", "b01.b2": "NetworkPolicy, IMDSv2 hop limit 1",
        "b01.b3": "egress blocked (NetworkPolicy)",
        "h06.a": "One group scored by two versions (during a rolling update)",
        "h06.b": "One version per group (switch between batches)",
        "h06.prompt": "prompt", "h06.prompt_sub": "one",
        "h06.ans": "completions", "h06.ans_sub": "one group",
        "h06.v1": "v1 pool", "h06.v1s": "3 seeds, no cap",
        "h06.v2": "v2 pool", "h06.v2s": "5 seeds, cap 10x",
        "h06.adv": "advantage", "h06.adv_sub": "vs group mean",
        "h06.bad": "rule difference", "h06.bad_sub": "mixed into signal",
        "h06.good": "completion quality", "h06.good_sub": "only in advantage",
        "h06.some": "some", "h06.rest": "the rest", "h06.all": "all", "h06.next": "next batch",
    },
}


def beginner_01(lang: str) -> Figure:
    """docs/beginner/01_why_sandbox: the risk table (files, IMDS credentials, egress) and its blocking layers."""
    t = T[lang]
    fig = Figure(760, 566)
    rows = [(t["b01.r1"], t["b01.r1s"], t["b01.a1"], t["b01.b1"], "file"),
            (t["b01.r2"], t["b01.r2s"], t["b01.a2"], t["b01.b2"], "key"),
            (t["b01.r3"], t["b01.r3s"], t["b01.a3"], t["b01.b3"], "globe")]
    for p, (oy, letter, title) in enumerate(((0, "a", t["b01.a"]), (286, "b", t["b01.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 80
        if p == 1:
            fig.container(22, top - 30, 180, 228, t["b01.pod"], icon="shield-lock", stroke=ACCENT, color=ACCENT, bold=True)
        fig.box(36, top, 152, 186, t["b01.code"], t["b01.code_sub"], icon="code",
                fill=ACCENT_FILL if p == 1 else GREY_FILL, stroke=ACCENT if p == 1 else MUTED_STROKE,
                gid=f"n:code-{letter}")
        fig.container(520, top - 30, 222, 228, t["b01.server"], icon="server")
        for i, (res, res_sub, act, layer, ico) in enumerate(rows):
            cy = top + 25 + i * 68
            fig.box(540, cy - 25, 186, 50, res, res_sub, icon=ico, gid=f"n:res{i}-{letter}")
            if p == 0:
                fig.arrow([(188, cy), (538, cy)], color=RED, label=act, label_at=(363, cy - 8))
            else:
                fig.line([(188, cy), (468, cy)], color=INK)
                fig.block(470, cy)
                fig.text(328, cy - 8, layer, size=12)
    return fig


def handson_06(lang: str) -> Figure:
    """docs/handson/06_sandbox_update: v1 and v2 scoring one GRPO group vs a version pinned per group."""
    t = T[lang]
    fig = Figure(760, 556)
    # Columns: prompt | answers (x8) | edge labels | pools | advantage | outcome
    px, pw, ax, aw, ex0, ex1, vx, vw, dx, dw, ox, ow = 16, 100, 134, 90, 232, 296, 298, 164, 482, 116, 622, 126
    for p, (oy, letter, title) in enumerate(((0, "a", t["h06.a"]), (282, "b", t["h06.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 72
        mid, y1, y2 = top + 93, top + 28, top + 158
        lx = (ex0 + ex1) / 2
        fig.box(px, mid - 25, pw, 50, t["h06.prompt"], t["h06.prompt_sub"], icon="comment", gid=f"n:prompt-{letter}")
        fig.arrow([(px + pw, mid), (ax - 2, mid)])
        fig.stack(ax, top, aw, 186, t["h06.ans"], t["h06.ans_sub"], icon="stack", gid=f"n:answers-{letter}")
        fig.box(vx, y1 - 28, vw, 56, t["h06.v1"], t["h06.v1s"], icon="container", gid=f"n:v1-{letter}")
        fig.box(vx, y2 - 28, vw, 56, t["h06.v2"], t["h06.v2s"], icon="container", gid=f"n:v2-{letter}")
        fig.box(dx, top, dw, 186, t["h06.adv"], t["h06.adv_sub"], icon="graph", gid=f"n:adv-{letter}")
        fig.arrow([(vx + vw, y1), (dx - 2, y1)])
        if p == 0:
            fig.arrow([(ex0, y1), (ex1, y1)], label=t["h06.some"], label_at=(lx, y1 - 8))
            fig.arrow([(ex0, y2), (ex1, y2)], label=t["h06.rest"], label_at=(lx, y2 - 8))
            fig.arrow([(vx + vw, y2), (dx - 2, y2)])
            fig.arrow([(dx + dw, mid), (ox - 2, mid)], color=RED)
            fig.box(ox, mid - 52, ow, 104, t["h06.bad"], t["h06.bad_sub"], icon="alert", fill=RED_FILL, stroke=RED,
                    color=RED, gid="n:outcome-a")
        else:
            fig.arrow([(ex0, y1), (ex1, y1)], label=t["h06.all"], label_at=(lx, y1 - 8))
            fig.arrow([(ex0, y2), (ex1, y2)], color=MUTED_STROKE, dash="5 4", label=t["h06.next"],
                      label_at=(lx, y2 - 8))
            fig.arrow([(dx + dw, mid), (ox - 2, mid)], color=ACCENT)
            fig.box(ox, mid - 52, ow, 104, t["h06.good"], t["h06.good_sub"], icon="check-circle", fill=ACCENT_FILL,
                    stroke=ACCENT, gid="n:outcome-b")
    return fig


FIGURES = {"beginner-01_why_sandbox": beginner_01, "handson-06_sandbox_update": handson_06}
