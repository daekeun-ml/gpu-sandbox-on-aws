"""How a single submission and a multi-turn episode use sandboxes in chapter 06."""

from __future__ import annotations

from figlib import ACCENT, ACCENT_FILL, CONTAINER, GREY_FILL, INK, Figure
from figures_fa import beginner_label

T = {
    "ko": {
        "single": "서로 다른 답을 한 번씩 채점할 때", "request": "답안 하나", "free": "빈 샌드박스",
        "episode": "한 문제에 다시 도전할 때", "agent": "에이전트", "sandbox": "같은 샌드박스",
        "first": "코드 제출", "revision": "고친 코드 제출",
        "note": "에피소드가 끝나면 샌드박스를 반납합니다.",
    },
    "en": {
        "single": "Evaluate independent answers", "request": "One submission", "free": "Any free sandbox",
        "episode": "Revise an answer to one problem", "agent": "Agent", "sandbox": "Same sandbox",
        "first": "Submit code", "revision": "Submit revised code",
        "note": "Release the sandbox when the episode ends.",
    },
}


def beginner_06(lang: str) -> Figure:
    t = T[lang]
    fig = Figure(512, 370)
    fig.text(14, 30, t["single"], size=22, bold=True, anchor="start")
    beginner_label(fig, 14, 46, 182, t["request"], icon="file-code")
    fig.arrow([(196, 69), (301, 69)], color=ACCENT, width=2)
    beginner_label(fig, 304, 46, 194, t["free"], highlight=True, icon="shield-lock")

    fig.line([(14, 112), (498, 112)], color=CONTAINER, width=1)
    fig.text(14, 150, t["episode"], size=22, bold=True, anchor="start")
    fig.rect(14, 169, 128, 150, fill=GREY_FILL, stroke=CONTAINER)
    fig.rect(368, 169, 130, 150, fill=ACCENT_FILL, stroke=CONTAINER)
    fig.icon("hubot", 60, 207, 36, ACCENT)
    fig.icon("shield-lock", 415, 207, 36, ACCENT)
    fig.text(78, 270, t["agent"], size=18, bold=True)
    fig.text(433, 270, t["sandbox"], size=17, bold=True)
    for y, label, outbound in ((192, t["first"], True), (229, "wrong_answer", False),
                               (267, t["revision"], True), (305, "ok", False)):
        points = [(142, y), (366, y)] if outbound else [(368, y), (144, y)]
        fig.arrow(points, color=ACCENT if outbound else INK, width=2)
        fig.text(255, y - 6, label, size=16)
    fig.text(14, 352, t["note"], size=17, anchor="start")
    return fig


FIGURES = {"beginner-06_multi_turn_agent": beginner_06}
