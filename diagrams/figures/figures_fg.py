"""Beginner guide part 06 (docs/beginner/06_multi_turn_agent): single-turn grading vs a multi-turn episode.

Every box and edge comes from the page named in the docstring. Shared geometry draws both languages.
"""

from __future__ import annotations

from figlib import ACCENT, ACCENT_FILL, INK, SMALL, Figure, text_width
from figures_fa import edge_label, vbox
from figures_fb import mbox

T = {
    "ko": {
        "a": "single-turn 채점: completion마다 유휴 pod 하나",
        "b": "multi-turn 에피소드: 모든 turn을 claim한 샌드박스 하나에서 채점",
        "trainer": "GRPO trainer", "trainer_sub": "completion마다 채점 1회",
        "submit": ["completion 1개 제출"], "verdict1": ["verdict 1개"],
        "pool": "reward 풀",
        "pod": "유휴 pod", "pod_sub": "요청마다 새로 선택",
        "cleared": "요청 후 작업 디렉터리, 남은 프로세스 정리",
        "agent": "에이전트 (모델)", "agent_sub": "에피소드 1개",
        "turns": [["turn 1 제출"], ["verdict 피드백"], ["turn 2 수정 제출"], ["verdict"]],
        "claimed": ["claim한 샌드박스 하나", "같은 샌드박스 버전", "GPU 프로필이면 같은 GPU", "에피소드 종료 후 삭제"],
        "warm": ["SandboxWarmPool", "미리 실행한 샌드박스"],
        "assign": "SandboxClaim으로 할당",
    },
    "en": {
        "a": "Single-turn grading: one free pod per completion",
        "b": "Multi-turn episode: every turn graded in one claimed sandbox",
        "trainer": "GRPO trainer", "trainer_sub": "one grading per completion",
        "submit": ["submit one completion"], "verdict1": ["one verdict"],
        "pool": "reward pool",
        "pod": "free pod", "pod_sub": "picked anew per request",
        "cleared": "work dir, processes cleared per request",
        "agent": "agent (model)", "agent_sub": "one episode",
        "turns": [["turn 1 submission"], ["verdict as feedback"], ["turn 2 revised submission"], ["verdict"]],
        "claimed": ["one claimed sandbox", "same sandbox version", "same GPU with a GPU profile", "deleted when the episode ends"],
        "warm": ["SandboxWarmPool", "sandboxes started ahead"],
        "assign": "assigned by a SandboxClaim",
    },
}


def _centred_label(fig: Figure, x0: float, x1: float, y: float, lines: list[str], step: int | None = None) -> None:
    """Edge label centred over the connector between x0 and x1 (room for the circled step number included)."""
    w = text_width(lines[0], SMALL) + (23 if step is not None else 0)
    assert w + 16 <= x1 - x0, f"edge label wider than its gap: {lines[0]!r}"
    edge_label(fig, (x0 + x1) / 2 - w / 2, y, lines, step=step)


def beginner_06(lang: str) -> Figure:
    """docs/beginner/06_multi_turn_agent Pain point: the reward pool grades each completion on any free pod and
    clears state; a multi-turn episode keeps one sandbox claimed from a SandboxWarmPool for all its turns."""
    t = T[lang]
    fig = Figure(760, 524)
    lx, lw, rx, rw = 16, 180, 440, 304
    gap0, gap1 = lx + lw, rx

    # a: single-turn, one completion -> reward pool -> any free pod -> one verdict
    fig.panel(16, 26, "a", t["a"])
    top, h = 48, 128
    vbox(fig, lx, top, lw, h, t["trainer"], t["trainer_sub"], icon="hubot", gid="n:trainer")
    fig.container(rx, top, rw, h, t["pool"], icon="stack")
    fig.stack(rx + 16, top + 34, rw - 54, 54, t["pod"], t["pod_sub"], mark="xN", icon="container", gid="n:pod")
    fig.text(rx + rw / 2, top + h - 14, t["cleared"], size=SMALL)
    y1, y2 = top + 44, top + 92
    fig.arrow([(gap0, y1), (gap1 - 2, y1)])
    _centred_label(fig, gap0, gap1, y1 - 8, t["submit"])
    fig.arrow([(gap1, y2), (gap0 + 2, y2)])
    _centred_label(fig, gap0, gap1, y2 - 8, t["verdict1"])

    # b: multi-turn, every turn of one episode goes to the same claimed sandbox
    oy = 196
    fig.panel(16, oy + 26, "b", t["b"])
    top, h = oy + 48, 170
    vbox(fig, lx, top, lw, h, t["agent"], t["agent_sub"], icon="hubot", gid="n:agent")
    mbox(fig, rx, top, rw, h, t["claimed"], icon="shield-lock", fill=ACCENT_FILL, stroke=ACCENT, gid="n:claimed")
    for i, lines in enumerate(t["turns"]):
        y = top + 34 + 38 * i
        to_sandbox = i % 2 == 0
        pts = [(gap0, y), (gap1 - 2, y)] if to_sandbox else [(gap1, y), (gap0 + 2, y)]
        fig.arrow(pts, color=ACCENT if to_sandbox else INK)
        _centred_label(fig, gap0, gap1, y - 8, lines, step=i + 1)
    wy = top + h + 40
    mbox(fig, rx, wy, rw, 54, t["warm"], icon="stack", gid="n:warm")
    cx = rx + rw / 2
    fig.arrow([(cx, wy), (cx, top + h + 2)])
    # Left of the connector: the right side has too little room for the English label.
    assert cx - 8 - text_width(t["assign"], SMALL) >= gap0 + 16, "assign label overlaps the agent column"
    fig.text(cx - 8, (wy + top + h) / 2 + 4, t["assign"], size=SMALL, anchor="end")
    return fig


FIGURES = {"beginner-06_multi_turn_agent": beginner_06}
