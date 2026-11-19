"""Hands-on page 11 (docs/handson/11_multi_turn): turns spread over a reward pool vs one claimed sandbox per
episode on the scenario C node.

Every box and edge comes from the page named in the docstring. Shared geometry draws both languages.
"""

from __future__ import annotations

from figlib import ACCENT, ACCENT_FILL, INK, RED, RED_FILL, SMALL, Figure, text_width
from figures_fa import edge_label, vbox
from figures_fb import mbox

T = {
    "ko": {
        "a": "에피소드 단위 샌드박스가 없으면: turn마다 다른 pod",
        "b": "시나리오 C의 Agent Sandbox: 에피소드마다 샌드박스 하나를 claim",
        "episode": "에피소드 하나",
        "pool": "reward 풀 (Deployment): 요청마다 유휴 pod 선택",
        "pa": ["pod A", "요청 후 작업 디렉터리, 프로세스 정리"],
        "pb": ["pod B", "요청 후 작업 디렉터리, 프로세스 정리"],
        "t1": ["turn 1 제출"], "t2": ["turn 2 수정 제출"],
        "fresh": ["에피소드마다 새로 만들면"],
        "slow": ["새 샌드박스 시작", "Ready까지 대기, Kata GPU VM은 몇 분"],
        "job": "Job episodes", "job_subs": ["ns rl-trainer", "SA sandbox-episode", "에피소드 2개를 차례로"],
        "node": "c8i.2xlarge 노드 (nested virtualization)",
        "warm": ["SandboxWarmPool", "kernel-eval-gvisor-cpu, 대기 샌드박스 2개"],
        "assign": ["대기 샌드박스 하나 할당"],
        "claimed": ["claim한 샌드박스 하나 (gvisor-cpu)", "turn 1, 2, 3을 같은 pod에서 채점", "작업 디렉터리는 제출마다 삭제",
                    "claim을 삭제하면 샌드박스도 삭제"],
        "e_claim": ["에피소드마다 SandboxClaim 생성"],
        "e_turns": ["turn 1, 2, 3 제출"],
        "e_verdict": ["verdict 피드백"],
        "e_delete": ["에피소드 끝: claim 삭제"],
    },
    "en": {
        "a": "Without per-episode sandboxes: another pod per turn",
        "b": "Agent Sandbox in scenario C: one claimed sandbox per episode",
        "episode": "one episode",
        "pool": "reward pool (Deployment): a free pod per request",
        "pa": ["pod A", "work dir, processes cleared per request"],
        "pb": ["pod B", "work dir, processes cleared per request"],
        "t1": ["turn 1 submission"], "t2": ["turn 2 revised submission"],
        "fresh": ["new sandbox per episode"],
        "slow": ["start a new sandbox", "wait for Ready; minutes for a Kata GPU VM"],
        "job": "Job episodes", "job_subs": ["ns rl-trainer", "SA sandbox-episode", "2 episodes in turn"],
        "node": "c8i.2xlarge node (nested virtualization)",
        "warm": ["SandboxWarmPool", "kernel-eval-gvisor-cpu, 2 waiting sandboxes"],
        "assign": ["assigns one waiting sandbox"],
        "claimed": ["one claimed sandbox (gvisor-cpu)", "turns 1, 2, 3 graded on the same pod", "work dir removed per submission",
                    "deleting the claim deletes the sandbox"],
        "e_claim": ["one SandboxClaim per episode"],
        "e_turns": ["submit turns 1, 2, 3"],
        "e_verdict": ["verdict comes back as feedback"],
        "e_delete": ["episode over: delete the claim"],
    },
}


def _label(fig: Figure, x0: float, x1: float, y: float, lines: list[str], *, step: int | None = None,
           color: str = INK) -> None:
    """Edge label centred over a horizontal connector between x0 and x1 (circled step number included)."""
    w = text_width(lines[0], SMALL) + (23 if step is not None else 0)
    assert w + 16 <= x1 - x0, f"edge label wider than its gap: {lines[0]!r}"
    edge_label(fig, (x0 + x1) / 2 - w / 2, y, lines, step=step, color=color)


def handson_11(lang: str) -> Figure:
    """docs/handson/11_multi_turn Pain point: a reward pool may answer each turn from another pod and removes
    state after every request, and a fresh sandbox per episode means waiting for Ready; on the scenario C node
    the episodes Job claims one gvisor-cpu sandbox per episode from a SandboxWarmPool, sends turns 1 to 3 to it,
    and deletes the claim when the episode ends."""
    t = T[lang]
    fig = Figure(760, 590)
    lx, lw, rx, rw = 16, 150, 404, 340
    ix, iw = rx + 16, rw - 32

    # a: turns of one episode land on whichever pod is free; a fresh sandbox per episode waits for Ready
    fig.panel(16, 26, "a", t["a"])
    top = 48
    fig.container(rx, top, rw, 140, t["pool"], icon="stack")
    rows = [top + 54, top + 106]
    for i, (key, edge) in enumerate((("pa", "t1"), ("pb", "t2"))):
        mbox(fig, ix, rows[i] - 22, iw, 44, t[key], icon="container", gid=f"n:pod{i + 1}")
        fig.arrow([(lx + lw, rows[i]), (ix - 2, rows[i])])
        _label(fig, lx + lw, rx, rows[i] - 8, t[edge])
    red_y = top + 176
    mbox(fig, rx, red_y - 26, rw, 52, t["slow"], icon="clock", fill=RED_FILL, stroke=RED, color=RED, gid="n:slow")
    fig.arrow([(lx + lw, red_y), (rx - 2, red_y)], color=RED, dash="5 4")
    _label(fig, lx + lw, rx, red_y - 8, t["fresh"], color=RED)
    mbox(fig, lx, top, lw, red_y + 26 - top, [t["episode"]], gid="n:episode")

    # b: scenario C, one claimed gvisor-cpu sandbox per episode on the c8i node
    oy = 270
    fig.panel(16, oy + 26, "b", t["b"])
    top = oy + 50
    fig.container(rx, top, rw, 252, t["node"], icon="server", stroke=ACCENT, color=ACCENT, bold=True)
    warm_y, claimed_y, claimed_h = top + 30, top + 126, 110
    mbox(fig, ix, warm_y, iw, 52, t["warm"], icon="stack", gid="n:warm")
    mbox(fig, ix, claimed_y, iw, claimed_h, t["claimed"], icon="shield-lock", fill=ACCENT_FILL, stroke=ACCENT,
         gid="n:claimed")
    ax = ix + 40
    fig.arrow([(ax, warm_y + 52), (ax, claimed_y - 2)])
    edge_label(fig, ax + 8, (warm_y + 52 + claimed_y) / 2 + 4, t["assign"], step=2)
    assert ax + 8 + 23 + text_width(t["assign"][0], SMALL) + 8 <= ix + iw, "assign label overflows the node"

    vbox(fig, lx, warm_y, lw, claimed_y + claimed_h - warm_y, t["job"], t["job_subs"], icon="workflow",
         gid="n:job")
    jx = lx + lw
    wy = warm_y + 26
    fig.arrow([(jx, wy), (ix - 2, wy)])
    _label(fig, jx, rx, wy - 8, t["e_claim"], step=1)
    ys = [claimed_y + 26, claimed_y + 58, claimed_y + 90]
    fig.arrow([(jx, ys[0]), (ix - 2, ys[0])], color=ACCENT)
    _label(fig, jx, rx, ys[0] - 8, t["e_turns"], step=3)
    fig.arrow([(ix, ys[1]), (jx + 2, ys[1])])
    _label(fig, jx, rx, ys[1] - 8, t["e_verdict"], step=4)
    fig.arrow([(jx, ys[2]), (ix - 2, ys[2])], dash="5 4")
    _label(fig, jx, rx, ys[2] - 8, t["e_delete"], step=5)
    return fig


FIGURES = {"handson-11_multi_turn": handson_11}
