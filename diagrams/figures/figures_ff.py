"""Pain point schematics for production 05 to 09 (group ff).

Each function draws one figure in one language from shared geometry. Every box, label and value comes
from the page named in the docstring (its Pain point prose, Why bullets and body).
"""

from __future__ import annotations

from figlib import (ACCENT, ACCENT_FILL, GREY_FILL, INK, MUTED_STROKE, RED, RED_FILL, SIZE, SMALL, Figure,
                    text_width)

T = {
    "ko": {
        # production/05_sandbox_updates
        "p05.a": "rolling update: 함께 응답하는 구버전과 신버전 pod",
        "p05.b": "blue/green: 검증과 parity 뒤 batch나 group 단위로 전환",
        "p05.ans": "completion", "p05.ans_sub": "GRPO group 하나",
        "p05.dep": "rolling update 중인 Deployment",
        "p05.old": "구버전 pod", "p05.old_s": "기존 채점 규칙",
        "p05.new": "신버전 pod", "p05.new_s": "새 채점 규칙",
        "p05.pools": "(runtime, version)마다 pool 하나",
        "p05.v1": "sandbox-gvisor-v1", "p05.v1s": "active, 롤백용으로 유지",
        "p05.v2": "sandbox-gvisor-v2", "p05.v2s": "검증, parity 전 트래픽 없음",
        "p05.some": "일부", "p05.rest": "나머지", "p05.all": "전부", "p05.switch": "다음 batch나 group부터",
        "p05.adv": "group 기준 advantage",
        "p05.bad": "섞이는 두 규칙의 점수", "p05.good": "한 버전의 점수만",
        # production/06_scaling_with_verl
        "p06.a": "trainer GPU 한 장과 샌드박스가 차례로 실행하는 세 단계",
        "p06.b": "여러 GPU로: group_key마다 버전을 고정하는 gateway",
        "p06.gpu": "trainer: A10G 한 장 (24 GB)",
        "p06.gen": "vLLM 생성", "p06.upd": "업데이트", "p06.next": "다음 step",
        "p06.mem": "24 GB", "p06.w": "7B bf16 가중치만 약 15 GB",
        "p06.rw": "reward 채점", "p06.rw_s": "샌드박스",
        "p06.batch": "샌드박스 호출마다 snapshot 하나", "p06.per_batch": "한 batch는 한 버전", "p06.reward": "reward",
        "p06.rc": "RayCluster verl (rl-trainer)",
        "p06.wk": "GPU worker", "p06.wk_s": "actor, vLLM rollout, reward worker",
        "p06.req": "POST /v1/evaluate + group_key", "p06.per_sample": "샘플마다",
        "p06.gw": "sandbox gateway", "p06.gw_s": "group_key마다 버전 고정",
        "p06.pool": "샌드박스 pool", "p06.pool_s": "runtime별, version별",
        "p06.same": "같은 group은 같은 버전",
        # production/07_observability_and_operations
        "p07.a": "샌드박스 쪽 고장에도 멈추지 않는 학습",
        "p07.b": "reward 품질 신호에 경보",
        "p07.src": "샌드박스 쪽 고장",
        "p07.r1": "인증 실패", "p07.r1s": "대량의 401 응답",
        "p07.r2": "줄어드는 pool", "p07.r2s": "Ready가 아닌 pod",
        "p07.r3": "reward hacking", "p07.r3s": "flag는 verdict에만 기록",
        "p07.e1": "sandbox_error 샘플을 None으로 제외",
        "p07.e2": "DNS에서 빠지고 남은 pod로 몰리는 요청",
        "p07.e3": "지표 집계 없음",
        "p07.out": "trainer에서 보이는 결과",
        "p07.o1": "advantage 0", "p07.o1s": "모두 제외되면 신호 없는 step",
        "p07.o2": "느려지기만 하는 step", "p07.o3": "오르는 것처럼 보이는 reward",
        "p07.alarm": "경보",
        "p07.s1": "status.sandbox_error / n", "p07.s2": "Deployment별 available, desired",
        "p07.s3": "flag 개수 (확장 필요)",
        "p07.l1": "sandbox_error 비율", "p07.l1s": "TRL 5% 초과, 3 batch 연속",
        "p07.l2": "Ready pod 부족", "p07.l2s": "available이 desired 미만 10분",
        "p07.l3": "reward hacking 신호", "p07.l3s": "flag 비율 상승 추세",
        # production/08_cost
        "p08.a": "노드 단위 과금: 유휴 상태에도, run이 끝난 뒤에도 과금",
        "p08.b": "reward 구간에 맞춘 pool, 빨리 반납하는 빈 노드",
        "p08.lane1": "trainer", "p08.lane2": "샌드박스 GPU",
        "p08.gen": "생성", "p08.rw": "reward 채점", "p08.upd": "업데이트",
        "p08.idle": "유휴", "p08.busy": "사용 중",
        "p08.end_a": "run 종료, pool은 그대로", "p08.end_b": "run 종료, replicas 0",
        "p08.left": "g4dn.metal 방치", "p08.left_s": "7.824 USD/시간",
        "p08.wait": "30분 비면 반납 시작", "p08.wait_s": "consolidateAfter 30분",
        "p08.br_a": "사용 여부와 관계없이 노드 단위로 과금", "p08.br_a2": "주말 48시간이면 375.552 USD",
        "p08.br_b": "reward 구간의 몰림에 맞춘 pool 크기", "p08.br_b2": "빈 기간마다 약 3.912 USD", "p08.br_b3": "노드가 종료될 때까지 과금",
        "p08.node": "g4dn.metal (T4 8개)",
        "p08.used_a": "T4 4개만 사용", "p08.price_a": "사용한 T4당 1.956 USD/시간",
        "p08.used_b": "T4 8개 모두 사용", "p08.price_b": "T4당 0.978 USD/시간",
        # production/09_cdk
        "p09.a": "단계별 생성, 단계별 삭제",
        "p09.b": "스택 하나로 생성, 스택 단위로 삭제",
        "p09.mk_a": "여러 스크립트", "p09.mk_a_s": "순서대로 실행",
        "p09.mk_b": "cdk/deploy.sh", "p09.mk_b_s": "스택 하나 배포",
        "p09.step": "단계 {}",
        "p09.res_a": "단계별 리소스", "p09.res_b": "CDK 스택 하나 (CloudFormation)",
        "p09.r1": "클러스터", "p09.r2": "노드 그룹", "p09.r3": "launch template, 로그 그룹",
        "p09.del_a": "단계마다 삭제", "p09.del_a_s": "리소스별로 따로",
        "p09.del_b": "cdk/destroy.sh", "p09.del_b_s": "스택 전체 삭제",
        "p09.out_a": "하나라도 남으면", "p09.out_a_s": "비용, 다음 생성 실패",
        "p09.out_b": "스택과 함께 삭제", "p09.out_b_s": "AMI, ECR은 따로 삭제",
    },
    "en": {
        "p05.a": "Rolling update: old and new pods answer side by side",
        "p05.b": "Blue/green: switch per batch or group after verification and parity",
        "p05.ans": "completions", "p05.ans_sub": "one GRPO group",
        "p05.dep": "Deployment in a rolling update",
        "p05.old": "old pod", "p05.old_s": "old scoring rules",
        "p05.new": "new pod", "p05.new_s": "new scoring rules",
        "p05.pools": "one pool per (runtime, version)",
        "p05.v1": "sandbox-gvisor-v1", "p05.v1s": "active, kept for rollback",
        "p05.v2": "sandbox-gvisor-v2", "p05.v2s": "no traffic before checks",
        "p05.some": "some", "p05.rest": "the rest", "p05.all": "all", "p05.switch": "next batch or group",
        "p05.adv": "group-relative advantage",
        "p05.bad": "scores of two rules mixed", "p05.good": "scores of one version",
        "p06.a": "One trainer GPU and the sandbox run the three phases in turn",
        "p06.b": "Many GPUs: the gateway pins a version per group_key",
        "p06.gpu": "trainer: one A10G (24 GB)",
        "p06.gen": "vLLM generation", "p06.upd": "update", "p06.next": "next step",
        "p06.mem": "24 GB", "p06.w": "7B bf16 weights alone about 15 GB",
        "p06.rw": "reward scoring", "p06.rw_s": "sandbox",
        "p06.batch": "one snapshot per sandbox call", "p06.per_batch": "one version per batch", "p06.reward": "rewards",
        "p06.rc": "RayCluster verl (rl-trainer)",
        "p06.wk": "GPU worker", "p06.wk_s": "actor, vLLM rollout, reward worker",
        "p06.req": "POST /v1/evaluate + group_key", "p06.per_sample": "per sample",
        "p06.gw": "sandbox gateway", "p06.gw_s": "pins a version per group_key",
        "p06.pool": "sandbox pools", "p06.pool_s": "per runtime, per version",
        "p06.same": "same group, same version",
        "p07.a": "Sandbox-side failures do not stop training",
        "p07.b": "Alarms on reward quality signals",
        "p07.src": "sandbox-side failures",
        "p07.r1": "Authentication fails", "p07.r1s": "a flood of 401s",
        "p07.r2": "Pool shrinks", "p07.r2s": "pods not Ready",
        "p07.r3": "Reward hacking", "p07.r3s": "flags in verdicts only",
        "p07.e1": "sandbox_error samples dropped with None",
        "p07.e2": "out of DNS, load on the remaining pods",
        "p07.e3": "not aggregated into metrics",
        "p07.out": "what the trainer shows",
        "p07.o1": "advantage 0", "p07.o1s": "all dropped: nothing learned",
        "p07.o2": "steps just get slower", "p07.o3": "rewards seem to improve",
        "p07.alarm": "alarms",
        "p07.s1": "status.sandbox_error / n", "p07.s2": "available vs desired per Deployment",
        "p07.s3": "flag counts (extension needed)",
        "p07.l1": "sandbox_error rate", "p07.l1s": "TRL over 5%, 3 batches in a row",
        "p07.l2": "Ready pods short", "p07.l2s": "available below desired, 10 min",
        "p07.l3": "reward hacking signal", "p07.l3s": "flag rate trending up",
        "p08.a": "Per-node billing: it bills when idle and after the run",
        "p08.b": "Pool sized to the reward phase, empty nodes returned quickly",
        "p08.lane1": "trainer", "p08.lane2": "sandbox GPU",
        "p08.gen": "generation", "p08.rw": "reward", "p08.upd": "update",
        "p08.idle": "idle", "p08.busy": "busy",
        "p08.end_a": "run ends, pool kept", "p08.end_b": "run ends, replicas 0",
        "p08.left": "g4dn.metal left on", "p08.left_s": "7.824 USD per hour",
        "p08.wait": "released from 30 min", "p08.wait_s": "consolidateAfter 30 min",
        "p08.br_a": "billed per node, busy or idle", "p08.br_a2": "48-hour weekend: 375.552 USD",
        "p08.br_b": "pool sized to the reward phase", "p08.br_b2": "about 3.912 USD per empty period", "p08.br_b3": "billed until the node ends",
        "p08.node": "g4dn.metal (8 T4s)",
        "p08.used_a": "only 4 T4s in use", "p08.price_a": "1.956 USD/hour per T4 used",
        "p08.used_b": "all 8 T4s in use", "p08.price_b": "0.978 USD/hour per T4",
        "p09.a": "Created step by step, deleted step by step",
        "p09.b": "Created as one stack, deleted as a stack",
        "p09.mk_a": "several scripts", "p09.mk_a_s": "run in order",
        "p09.mk_b": "cdk/deploy.sh", "p09.mk_b_s": "one stack",
        "p09.step": "step {}",
        "p09.res_a": "resources per step", "p09.res_b": "one CDK stack (CloudFormation)",
        "p09.r1": "cluster", "p09.r2": "node groups", "p09.r3": "launch templates, log groups",
        "p09.del_a": "delete per step", "p09.del_a_s": "one by one",
        "p09.del_b": "cdk/destroy.sh", "p09.del_b_s": "whole stack",
        "p09.out_a": "one leftover", "p09.out_a_s": "cost, next create fails",
        "p09.out_b": "stack deleted whole", "p09.out_b_s": "AMI, ECR: separately",
    },
}


# Helpers for primitives figlib lacks (timeline segments, brackets, GPU slots). Plain SVG via fig.parts.

def _seg(fig: Figure, x, y, w, h, label, sub=None, *, fill=GREY_FILL, stroke=MUTED_STROKE, color=INK, gid=None):
    """A timeline segment: square-cornered so neighbours butt together."""
    fig.rect(x, y, w, h, fill=fill, stroke=stroke, rx=0, gid=gid)
    cx, cy = x + w / 2, y + h / 2
    if sub:
        fig.text(cx, cy - 3, label, color=color)
        fig.text(cx, cy + 14, sub, size=SMALL, color=color)
    else:
        fig.text(cx, cy + SIZE * 0.36, label, color=color)
    need = max(text_width(label), text_width(sub, SMALL) if sub else 0) + 12
    assert need <= w, f"label too wide for segment {gid or label!r}: {need:.0f} > {w:.0f}"


def _bracket(fig: Figure, x0, x1, y, label, *, color=INK):
    """A span marker under a timeline: a line with end ticks and a centred label below."""
    fig.line([(x0, y - 5), (x0, y), (x1, y), (x1, y - 5)], color=MUTED_STROKE, width=1.2)
    fig.text((x0 + x1) / 2, y + 16, label, size=SMALL, color=color)
    assert text_width(label, SMALL) + 8 <= x1 - x0 + 40, f"bracket label too wide: {label!r}"


def _slots(fig: Figure, x, y, n_used, *, fill, stroke):
    """Eight GPU slots of one node, 4 per row; the first n_used are filled and labelled."""
    size, gap = 26, 8
    for i in range(8):
        sx, sy = x + (i % 4) * (size + gap), y + (i // 4) * (size + gap)
        used = i < n_used
        fig.rect(sx, sy, size, size, fill=fill if used else "#FFFFFF", stroke=stroke if used else MUTED_STROKE,
                 rx=3)
        if used:  # empty slots stay blank so used and unused read apart in greyscale too
            fig.text(sx + size / 2, sy + size / 2 + SMALL * 0.36, "T4", size=SMALL)


def production_05(lang: str) -> Figure:
    """docs/production/05_sandbox_updates: rolling update mixes two scoring rules in one group (a) vs
    blue/green pools that switch per reward batch (TRL) or per group (veRL) after verify and parity (b)."""
    t = T[lang]
    fig = Figure(760, 566)
    sx, sw, cx, cw, bx, bw, ox, ow = 16, 120, 314, 228, 330, 196, 578, 166
    e0, e1 = sx + sw + 10, bx - 2
    lx = (e0 + e1) / 2
    for p, (oy, letter, title) in enumerate(((0, "a", t["p05.a"]), (286, "b", t["p05.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 80
        y1, y2 = top + 40, top + 146
        fig.stack(sx, top, sw, 186, t["p05.ans"], t["p05.ans_sub"], icon="stack", gid=f"n:answers-{letter}")
        if p == 0:
            fig.container(cx, top - 30, cw, 228, t["p05.dep"])
            fig.box(bx, y1 - 30, bw, 60, t["p05.old"], t["p05.old_s"], icon="container", gid="n:old-a")
            fig.box(bx, y2 - 30, bw, 60, t["p05.new"], t["p05.new_s"], icon="container", gid="n:new-a")
            fig.arrow([(e0, y1), (e1, y1)], label=t["p05.some"], label_at=(lx, y1 - 8))
            fig.arrow([(e0, y2), (e1, y2)], label=t["p05.rest"], label_at=(lx, y2 - 8))
            fig.arrow([(bx + bw, y1), (ox - 2, y1)], color=RED)
            fig.arrow([(bx + bw, y2), (ox - 2, y2)], color=RED)
            fig.box(ox, top, ow, 186, t["p05.adv"], t["p05.bad"], icon="alert", fill=RED_FILL, stroke=RED,
                    color=RED, gid="n:outcome-a")
        else:
            fig.container(cx, top - 30, cw, 228, t["p05.pools"], stroke=ACCENT, color=ACCENT, bold=True)
            fig.box(bx, y1 - 30, bw, 60, t["p05.v1"], t["p05.v1s"], icon="container", gid="n:v1-b")
            fig.box(bx, y2 - 30, bw, 60, t["p05.v2"], t["p05.v2s"], icon="container", gid="n:v2-b")
            fig.arrow([(e0, y1), (e1, y1)], label=t["p05.all"], label_at=(lx, y1 - 8))
            fig.arrow([(e0, y2), (e1, y2)], color=MUTED_STROKE, dash="5 4", label=t["p05.switch"],
                      label_at=(lx, y2 - 8))
            assert text_width(t["p05.switch"], SMALL) + 8 <= 2 * (cx - lx), "switch label crosses the pool frame"
            fig.arrow([(bx + bw, y1), (ox - 2, y1)], color=ACCENT)
            fig.box(ox, top, ow, 186, t["p05.adv"], t["p05.good"], icon="check-circle", fill=ACCENT_FILL,
                    stroke=ACCENT, gid="n:outcome-b")
    return fig


def production_06(lang: str) -> Figure:
    """docs/production/06_scaling_with_verl: one A10G runs generation, scoring and update in turn with 7B weights
    taking about 15 of 24 GB (a) vs GPU workers xN calling the gateway per sample with a group_key (b)."""
    t = T[lang]
    fig = Figure(760, 566)
    cx, cw, ix, iw, rx, rw = 16, 300, 36, 200, 560, 184
    lx = (cx + cw + rx) / 2             # edge labels sit between the container edge and the right column
    for p, (oy, letter, title) in enumerate(((0, "a", t["p06.a"]), (286, "b", t["p06.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 80
        y1, y2 = top + 24, top + 108
        if p == 0:
            fig.container(cx, top - 30, cw, 228, t["p06.gpu"], icon="cpu")
            fig.box(ix, top, iw, 48, t["p06.gen"], gid="n:gen")
            fig.box(ix, top + 84, iw, 48, t["p06.upd"], gid="n:update")
            fig.arrow([(ix + iw / 2, top + 84), (ix + iw / 2, top + 50)])
            fig.text(ix + iw / 2 + 8, top + 71, t["p06.next"], size=SMALL, anchor="start")
            # Memory bar: the whole bar is the GPU, the filled part the 7B bf16 weights (15 of 24 GB).
            bar_w = cw - 40
            fig.text(ix, top + 155, t["p06.w"], size=SMALL, color=RED, anchor="start")
            fig.text(ix + bar_w, top + 155, t["p06.mem"], size=SMALL, anchor="end")
            fig.rect(ix, top + 162, bar_w, 24, fill="#FFFFFF", stroke=MUTED_STROKE, rx=3, gid="n:memory")
            fig.rect(ix, top + 162, bar_w * 15 / 24, 24, fill=RED_FILL, stroke=RED, rx=3)
            assert text_width(t["p06.w"], SMALL) + text_width(t["p06.mem"], SMALL) + 16 <= bar_w
            fig.box(rx, top, rw, 132, t["p06.rw"], t["p06.rw_s"], icon="shield-lock", gid="n:reward")
            fig.arrow([(ix + iw, y1), (rx - 2, y1)], label=t["p06.batch"], label_at=(lx, y1 - 8))
            fig.text(lx, y1 + 18, t["p06.per_batch"], size=SMALL)
            fig.arrow([(rx, y2), (ix + iw + 2, y2)], label=t["p06.reward"], label_at=(lx, y2 - 8))
        else:
            fig.container(cx, top - 30, cw, 228, t["p06.rc"], icon="cpu")
            sw = 220
            fig.stack(ix, top, sw, 186, t["p06.wk"], t["p06.wk_s"], mark="xN", icon="stack", gid="n:workers")
            fig.arrow([(ix + sw + 10, y1), (rx - 2, y1)], color=ACCENT, label=t["p06.req"], label_at=(lx, y1 - 8))
            fig.text(lx, y1 + 18, t["p06.per_sample"], size=SMALL)
            fig.box(rx, top, rw, 48, t["p06.gw"], t["p06.gw_s"], fill=ACCENT_FILL, stroke=ACCENT, gid="n:gateway")
            fig.box(rx, top + 138, rw, 48, t["p06.pool"], t["p06.pool_s"], icon="container", gid="n:pools")
            mx = rx + rw / 2
            fig.arrow([(mx, top + 48), (mx, top + 136)], color=ACCENT)
            fig.text(mx - 8, top + 97, t["p06.same"], size=SMALL, anchor="end")
    return fig


def production_07(lang: str) -> Figure:
    """docs/production/07_observability_and_operations: three sandbox-side failures that keep training running
    (a) vs the alarm each one should trip, from the recommended alarm table (b)."""
    t = T[lang]
    fig = Figure(760, 566)
    lx, lw, rx, rw = 36, 196, 532, 196
    for p, (oy, letter, title) in enumerate(((0, "a", t["p07.a"]), (286, "b", t["p07.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 80
        fig.container(22, top - 30, 224, 228, t["p07.src"])
        if p == 0:
            fig.container(rx - 14, top - 30, rw + 28, 228, t["p07.out"])
        else:
            fig.container(rx - 14, top - 30, rw + 28, 228, t["p07.alarm"], icon="bell", stroke=ACCENT, color=ACCENT,
                          bold=True)
        rows = [(t["p07.r1"], t["p07.r1s"], "key", t["p07.e1"], (t["p07.o1"], t["p07.o1s"]),
                 t["p07.s1"], (t["p07.l1"], t["p07.l1s"])),
                (t["p07.r2"], t["p07.r2s"], "container", t["p07.e2"], (t["p07.o2"], None),
                 t["p07.s2"], (t["p07.l2"], t["p07.l2s"])),
                (t["p07.r3"], t["p07.r3s"], "bug", t["p07.e3"], (t["p07.o3"], None),
                 t["p07.s3"], (t["p07.l3"], t["p07.l3s"]))]
        mid = (lx + lw + rx) / 2
        for i, (name, name_sub, ico, effect, outcome, signal, alarm) in enumerate(rows):
            cy = top + 25 + i * 68
            fig.box(lx, cy - 25, lw, 50, name, name_sub, icon=ico, gid=f"n:fail{i}-{letter}")
            if p == 0:
                fig.arrow([(lx + lw, cy), (rx - 2, cy)], color=RED, label=effect, label_at=(mid, cy - 8))
                fig.box(rx, cy - 25, rw, 50, *outcome, fill=RED_FILL, stroke=RED, color=RED, gid=f"n:out{i}")
            else:
                # Dashed: the flag count is a suggested extension, not in the repository.
                fig.arrow([(lx + lw, cy), (rx - 2, cy)], dash="5 4" if i == 2 else None, label=signal,
                          label_at=(mid, cy - 8))
                fig.box(rx, cy - 25, rw, 50, *alarm, gid=f"n:alarm{i}")
    return fig


def production_08(lang: str) -> Figure:
    """docs/production/08_cost: sandbox GPUs bill per node through idle phases and after the run, half-used
    metal doubles the price per T4 (a) vs a pool sized to the reward phase, replicas 0 after the run and the
    30-minute consolidation, with all 8 T4s filled (b)."""
    t = T[lang]
    fig = Figure(760, 436)
    x0 = 108
    widths = (84, 96, 84)
    xs = [x0, x0 + widths[0], x0 + widths[0] + widths[1]]
    x_run = xs[2] + widths[2]          # end of the run
    ax, aw = x_run + 12, 150           # after-run segment
    nx, nw = 568, 176                  # node container
    for p, (oy, letter, title) in enumerate(((0, "a", t["p08.a"]), (224, "b", t["p08.b"]))):
        fig.panel(16, oy + 26, letter, title)
        l1, l2 = oy + 62, oy + 112      # lane tops
        fig.text(16, l1 + 23, t["p08.lane1"], anchor="start")
        fig.text(16, l2 + 25, t["p08.lane2"], anchor="start")
        for i, key in enumerate(("p08.gen", "p08.rw", "p08.upd")):
            _seg(fig, xs[i], l1, widths[i], 36, t[key], gid=f"n:phase{i}-{letter}")
            busy = i == 1
            _seg(fig, xs[i], l2, widths[i], 40, t["p08.busy" if busy else "p08.idle"],
                 fill=GREY_FILL if busy else "#FFFFFF", gid=f"n:gpu{i}-{letter}")
        fig.line([(x_run + 6, l1 - 6), (x_run + 6, l2 + 46)], color=INK, width=1.2)
        fig.text(ax, l1 + 23, t["p08.end_a" if p == 0 else "p08.end_b"], size=SMALL, anchor="start")
        _bracket(fig, x0, x_run, l2 + 54, t["p08.br_a" if p == 0 else "p08.br_b"])
        if p == 0:
            _seg(fig, ax, l2, aw, 40, t["p08.left"], t["p08.left_s"], fill=RED_FILL, stroke=RED, color=RED,
                 gid="n:left-on")
            fig.text(ax + aw / 2, l2 + 70, t["p08.br_a2"], size=SMALL, color=RED)
        else:
            _seg(fig, ax, l2, aw, 40, t["p08.wait"], t["p08.wait_s"], gid="n:wait")
            fig.line([(ax + aw, l2 - 6), (ax + aw, l2 + 46)], color=ACCENT, width=2.4)
            fig.text(ax + aw / 2, l2 + 70, t["p08.br_b2"], size=SMALL)
            fig.text(ax + aw / 2, l2 + 86, t["p08.br_b3"], size=SMALL)
            for s in (t["p08.br_b2"], t["p08.br_b3"]):
                assert text_width(s, SMALL) + 8 <= 2 * (nx - ax - aw / 2), f"cost note too wide: {s!r}"
        stroke, color = (MUTED_STROKE, INK) if p == 0 else (ACCENT, ACCENT)
        fig.container(nx, oy + 50, nw, 150, t["p08.node"], icon="server", stroke=stroke, color=color, bold=p == 1)
        _slots(fig, nx + (nw - 128) / 2, oy + 80, 4 if p == 0 else 8, fill=GREY_FILL if p == 0 else ACCENT_FILL,
               stroke=MUTED_STROKE if p == 0 else ACCENT)
        used, price = t["p08.used_a" if p == 0 else "p08.used_b"], t["p08.price_a" if p == 0 else "p08.price_b"]
        fig.text(nx + nw / 2, oy + 164, used, size=SMALL)
        fig.text(nx + nw / 2, oy + 184, price, size=SMALL, color=RED if p == 0 else INK)
        assert text_width(price, SMALL) + 20 <= nw, f"price line too wide for node box: {price!r}"
    return fig


def production_09(lang: str) -> Figure:
    """docs/production/09_cdk: resources created and deleted per script step (a) vs one CDK stack created by
    cdk/deploy.sh and deleted by cdk/destroy.sh (b)."""
    t = T[lang]
    fig = Figure(760, 566)
    mx, mw, cx, cw, bx, bw, dx, dw, ox, ow = 16, 108, 184, 222, 198, 194, 456, 124, 606, 138
    for p, (oy, letter, title) in enumerate(((0, "a", t["p09.a"]), (286, "b", t["p09.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 80
        mid = top + 93
        if p == 0:
            fig.box(mx, top, mw, 186, t["p09.mk_a"], t["p09.mk_a_s"], icon="terminal", gid="n:make-a")
            fig.container(cx, top - 30, cw, 228, t["p09.res_a"])
            fig.box(dx, top, dw, 186, t["p09.del_a"], t["p09.del_a_s"], icon="trash", gid="n:delete-a")
        else:
            fig.box(mx, top, mw, 186, t["p09.mk_b"], t["p09.mk_b_s"], icon="terminal", gid="n:make-b")
            fig.container(cx, top - 30, cw, 228, t["p09.res_b"], icon="stack", stroke=ACCENT, color=ACCENT, bold=True)
            fig.box(dx, top, dw, 186, t["p09.del_b"], t["p09.del_b_s"], icon="trash", gid="n:delete-b")
            fig.arrow([(mx + mw, mid), (cx - 2, mid)], color=ACCENT)
            fig.arrow([(cx + cw, mid), (dx - 2, mid)], color=ACCENT)
        for i, key in enumerate(("p09.r1", "p09.r2", "p09.r3")):
            cy = top + 25 + i * 68
            fig.box(bx, cy - 25, bw, 50, t[key], gid=f"n:res{i}-{letter}")
            if p == 0:
                fig.arrow([(mx + mw, cy), (bx - 2, cy)], label=t["p09.step"].format(i + 1),
                          label_at=((mx + mw + cx) / 2, cy - 8))
                fig.arrow([(bx + bw, cy), (dx - 2, cy)])
        if p == 0:
            fig.arrow([(dx + dw, mid), (ox - 2, mid)], color=RED)
            fig.box(ox, mid - 52, ow, 104, t["p09.out_a"], t["p09.out_a_s"], icon="alert", fill=RED_FILL,
                    stroke=RED, color=RED, gid="n:outcome-a")
        else:
            fig.arrow([(dx + dw, mid), (ox - 2, mid)], color=ACCENT)
            fig.box(ox, mid - 52, ow, 104, t["p09.out_b"], t["p09.out_b_s"], icon="check-circle",
                    fill=ACCENT_FILL, stroke=ACCENT, gid="n:outcome-b")
    return fig


FIGURES = {
    "production-05_sandbox_updates": production_05,
    "production-06_scaling_with_verl": production_06,
    "production-07_observability_and_operations": production_07,
    "production-08_cost": production_08,
    "production-09_cdk": production_09,
}
