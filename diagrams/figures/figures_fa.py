"""Pain point and main schematics for the home page, the path pages and the beginner guide (group fa).

Each function draws one figure in one language from shared geometry. Every box and edge comes from
the page named in its docstring.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from figlib import (ACCENT, ACCENT_FILL, CONTAINER, GREY_FILL, INK, MUTED_STROKE, RED, RED_FILL, SIZE, SMALL,
                    Figure, text_width)

T = {
    "ko": {
        # docs/index.md, Pain point
        "ix.a": "서로 다른 두 문제: host를 공유하는 runc, 학습 중 섞이는 버전",
        "ix.b": "각각의 대응: 격리 런타임, 배치(또는 group)마다 한 버전",
        "ix.code": "policy가 쓴 커널 코드", "ix.code_sub": "reward를 GPU에서 측정",
        "ix.runc": "runc 컨테이너", "ix.runc_sub": "일반 컨테이너",
        "ix.iso": "gVisor 또는 Kata", "ix.iso_sub": "RuntimeClass로 선택",
        "ix.kern_a": "공유하는 host 커널", "ix.kern_a_sub": "GPU 드라이버 포함",
        "ix.kern_b": "host 커널",
        "ix.group": "GRPO group 하나",
        "ix.mix": "섞이는 v1, v2 reward", "ix.mix_sub": "학습 중 이미지, harness 교체",
        "ix.pin": "한 버전으로 채점", "ix.pin_sub": "배치(또는 group) 단위 고정",
        "ix.bad": "잘못 계산되는 advantage", "ix.good": "reward 일관성 유지",
        # docs/index.md, 만드는 것
        "wb.train": "학습 (EC2 GPU 노드 또는 HyperPod 노드)",
        "wb.model": "policy 모델 + vLLM", "wb.model_sub": "GRPO, on-policy",
        "wb.model_sub2": "g5.2xlarge 또는 ml.g5.2xlarge",
        "wb.pool": "샌드박스 pool (EC2 GPU, CPU 노드)",
        "wb.g": "gVisor + nvproxy", "wb.g_sub": "g5.xlarge (A10G)",
        "wb.q": "Kata + QEMU", "wb.q_sub": "g4dn.metal (T4)",
        "wb.c": "Kata + Cloud Hypervisor", "wb.c_sub": "CPU 계층 (c8i, nested virt)", "wb.c_sub2": "GPU는 실험적",
        "wb.same": "같은 이미지, 프로필이 RuntimeClass와 노드를 정함",
        "wb.fwd": "커널 코드", "wb.pin": "group 단위 버전 고정", "wb.back": "정확성, speedup",
        # docs/learning_paths.md
        "lp.a": "어디서 시작할지 모른 채 GPU 코스부터 고를 때",
        "lp.b": "무료 코스부터, 비용 먼저 확인",
        "lp.reader": "처음 온 독자",
        "lp.pages": "46개 페이지", "lp.pages_sub": "시나리오 A, B1, B2, C",
        "lp.gpu": "GPU 코스부터 시작", "lp.gpu_sub": "아직 GPU가 필요 없는데도",
        "lp.cost": "시간당 몇 달러", "lp.cost_sub": "노드를 켜 둔 동안",
        "lp.c1": "코스 1: 읽기", "lp.c2": "코스 2: 로컬 실행", "lp.free": "0원",
        "lp.paid": "코스 3~6: AWS", "lp.paid_sub": "무료 코스 다음에", "lp.paid_sub2": "쿼터, 비용 먼저 확인",
        # docs/handson/start.md
        "gs.a": "GPU 노드부터 띄울 때",
        "gs.b": "로컬 CPU에서 파이프라인부터 확인할 때",
        "gs.start": "GPU 노드 기동", "gs.start_sub": "과금 시작",
        "gs.err": "오류 발견", "gs.err_sub": "import 오류,", "gs.err_sub2": "설정 누락",
        "gs.fix": "고치기", "gs.rerun": "다시 실행",
        "gs.bill_a": "GPU 노드 과금: 고치고 다시 실행하는 동안에도 계속",
        "gs.local": "로컬 CPU에서 확인", "gs.local_sub": "pytest 110개,", "gs.local_sub2": "GRPO dry run 2 step",
        "gs.env": "scripts/config.env", "gs.env_sub": "필요한 값이 비거나", "gs.env_sub2": "__SET_ME__면 멈춤",
        "gs.path": "경로 고르기", "gs.path_sub": "A, B1, B2, C,", "gs.path_sub2": "Production",
        "gs.free": "AWS 비용 없음", "gs.bill_b": "GPU 노드 과금",
        # docs/beginner/index.md
        "bi.a": "이유를 건너뛰고 명령부터 따라 할 때",
        "bi.b": "개념을 먼저 읽고 실습할 때",
        "bi.words": "한꺼번에 나오는 낯선 용어", "bi.words_sub": "gVisor, Kata, nvproxy,",
        "bi.words_sub2": "RuntimeClass, GRPO",
        "bi.copy": "명령만 따라 치기", "bi.copy_sub": "이유를 모른 채",
        "bi.stuck": "응용 불가", "bi.stuck_sub": "상황이 조금만 바뀌어도",
        "bi.why": "1~4편: 그림과 예시", "bi.why_sub": "용어는 처음 나올 때", "bi.why_sub2": "한 줄로 pool이",
        "bi.how": "5편: 직접 해 보기", "bi.how_sub": "내 PC (무료),", "bi.how_sub2": "AWS (선택)",
        "bi.see": "채점 결과를 직접 확인",
        # docs/beginner/01_why_sandbox.md, 실행 시간과 파일 접근
        "ly.title": "정렬 함수에 적용하는 세 가지 제한",
        "ly.desc": "반복문은 정해진 시간이 지나면 멈춥니다. 모델 파일은 학습 서버에 두고, 샌드박스에서 외부로 여는 연결은 기본으로 차단합니다.",
        "ly.time": "실행 시간", "ly.start": "함수 시작", "ly.loop": "끝나지 않는 반복문", "ly.stop": "시간이 다 되면 중단",
        "ly.files": "파일 접근", "ly.sandbox": "샌드박스", "ly.input": "정렬 코드와 숫자 목록",
        "ly.trainer": "학습 서버", "ly.checkpoint": "저장해 둔 모델 파일",
        "ly.file_note": "학습 서버의 모델 파일은 샌드박스와 공유하지 않습니다.",
        "ly.network": "외부 연결", "ly.external": "외부 서버", "ly.blocked": "기본 차단",
        # docs/beginner/02_container_vs_sandbox.md, Pain point
        "b02.a": "일반 컨테이너: 함께 쓰는 서버 커널 하나",
        "b02.b": "샌드박스 런타임: 컨테이너와 커널 사이에 하나 더 두는 격리 계층",
        "b02.c": "컨테이너", "b02.cpod": "pod {}의 컨테이너", "b02.wall": "Sentry 또는 VM 커널", "b02.wall_sub": "pod마다 하나",
        "b02.kern_a": "서버 커널 하나", "b02.kern_b": "서버 커널",
        "b02.weak": "커널 취약점 하나",
        "b02.bad": "위험해질 수 있음", "b02.bad_sub": "A, B, C 모두", "b02.good": "추가 격리 계층", "b02.good_sub": "A, B, C 앞에",
        # docs/beginner/02_container_vs_sandbox.md, 세 가지 격리 방식
        "tw.title": "코드가 input.txt를 열 때", "tw.source": "코드가 실행되는 곳", "tw.dest": "요청을 받는 곳",
        "tw.rows": (("일반 컨테이너", "runc", "노드의 Linux 커널"),
                    ("샌드박스", "gVisor", "Sentry"), ("가상 머신", "Kata", "VM 안의 Linux 커널")),
        # docs/beginner/03_gpu_sandbox.md, Pain point
        "b03.a": "GPU 없는 microVM과 일반 컨테이너",
        "b03.b": "GPU를 격리 경계 안에서 쓰는 두 방식",
        "b03.task": "GPU 커널 채점", "b03.task_sub": "실제 GPU 필요",
        "b03.fc": "Firecracker 기반 microVM", "b03.nodev": "GPU를 연결할 장치 없음", "b03.cant": "채점 불가",
        "b03.runc": "일반 컨테이너", "b03.runc_sub": "runc", "b03.bug": "드라이버 버그",
        "b03.host": "서버 커널에 영향을 주는 버그",
        "b03.gv": "gVisor + nvproxy", "b03.gv_sub": "g5.xlarge (일반 GPU VM)", "b03.check": "ioctl을 검사해 전달",
        "b03.gv_out": "허용 목록의 명령만", "b03.gv_out_sub": "서버의 드라이버로",
        "b03.kt": "Kata + VFIO", "b03.kt_sub": "g4dn.metal (bare metal)", "b03.pass": "GPU를 VM에 직접 할당",
        "b03.kt_out": "드라이버는 VM 안에서 실행", "b03.kt_out_sub": "하이퍼바이저, 장치 위험은 남음",
        # docs/beginner/03_gpu_sandbox.md, GPU 접근 경로
        "gp.title": "샌드박스에서 GPU까지",
        "gp.rows": (("gVisor", "nvproxy가 허용한 요청을 노드 드라이버로 전달합니다.", ("코드", "요청 검사", "노드 드라이버", "A10G")),
                    ("Kata + QEMU", "VM 안의 드라이버가 배정받은 물리 GPU를 사용합니다.", ("VM 안의 코드", "VM 안의 드라이버", "T4"))),
        # docs/beginner/04_rl_and_sandbox.md, Pain point
        "b04.a": "채점을 속인 답과 섞인 채점 기준",
        "b04.b": "속임수 차단, 한 배치에 한 버전",
        "b04.hack": "채점을 속인 답", "b04.hack_sub": "채점 코드의 허점으로 올린 점수",
        "b04.mix": "한 group 안에 v1, v2", "b04.mix_sub": "섞이는 채점 기준",
        "b04.wrong": "잘못된 점수", "b04.learn_bad": "잘못 학습하는 모델",
        "b04.guard": "속임수를 막는 harness", "b04.guard_sub": "프로세스 분리, 입력 교체",
        "b04.pin": "한 배치는 한 버전", "b04.pin_sub": "배치 안에서는 안 섞임",
        "b04.right": "일관된 점수", "b04.right_sub": "같은 기준으로 채점",
        "b04.learn_good": "이 점수로 학습하는 모델",
        # docs/beginner/04_rl_and_sandbox.md, 학습 루프에서 샌드박스의 자리
        "rl.title": "현재 모델이 만든 답으로 학습하는 과정",
        "rl.model": "현재 모델", "rl.model_sub": "같은 문제에 답 두 개 작성",
        "rl.sandbox": "샌드박스", "rl.sandbox_sub": "두 답을 각각 실행",
        "rl.trainer": "학습 프로그램", "rl.trainer_sub": "답마다 보상 계산",
        "rl.submit": "코드 제출", "rl.result": "정답 여부와 실행 시간", "rl.update": "보상으로 모델 조정",
        # docs/beginner/05_hands_on.md, Pain point
        "b05.a": "바로 AWS에서 시작하고, 끝난 뒤 삭제를 잊을 때",
        "b05.b": "내 PC에서 먼저 실습하고, 끝나면 한 번에 삭제",
        "b05.aws": "바로 AWS에서 시작", "b05.aws_sub": "개념 확인 없이",
        "b05.both": "비용과 설정 오류", "b05.both_sub": "한꺼번에 발생",
        "b05.lost": "찾기 어려운", "b05.lost_sub": "문제의 원인",
        "b05.end": "실습 끝", "b05.forgot": "삭제를 잊으면",
        "b05.left": "남은 리소스", "b05.left_sub": "계속 과금",
        "b05.pc": "1부: 내 PC에서 채점", "b05.pc_sub": "무료, 30분 안팎",
        "b05.seen": "채점 역할 확인", "b05.seen_sub": "여기서 멈춰도 됩니다",
        "b05.opt": "선택",
        "b05.cloud": "2부: AWS에서 비교", "b05.cloud_sub": "세 런타임, 몇 달러",
        "b05.destroy": "cdk/destroy.sh",
        "b05.gone": "한 번에 삭제되는 스택", "b05.gone_sub": "하나씩 찾지 않아도 됩니다",
    },
    "en": {
        "ix.a": "Two separate problems: runc shares the host, versions mix during training",
        "ix.b": "One fix each: an isolation runtime, one version per batch (or group)",
        "ix.code": "Kernel code from the policy", "ix.code_sub": "reward measured on a GPU",
        "ix.runc": "runc container", "ix.runc_sub": "plain container",
        "ix.iso": "gVisor or Kata", "ix.iso_sub": "chosen by RuntimeClass",
        "ix.kern_a": "Shared host kernel", "ix.kern_a_sub": "and the GPU driver",
        "ix.kern_b": "Host kernel",
        "ix.group": "One GRPO group",
        "ix.mix": "v1 and v2 rewards mixed", "ix.mix_sub": "image or harness changed",
        "ix.pin": "Scored by one version", "ix.pin_sub": "pinned per batch (or group)",
        "ix.bad": "Advantage goes wrong", "ix.good": "Rewards stay consistent",
        "wb.train": "Training (EC2 GPU node or HyperPod node)",
        "wb.model": "Policy model + vLLM", "wb.model_sub": "GRPO, on-policy",
        "wb.model_sub2": "g5.2xlarge or ml.g5.2xlarge",
        "wb.pool": "Sandbox pools (EC2 GPU, CPU nodes)",
        "wb.g": "gVisor + nvproxy", "wb.g_sub": "g5.xlarge (A10G)",
        "wb.q": "Kata + QEMU", "wb.q_sub": "g4dn.metal (T4)",
        "wb.c": "Kata + Cloud Hypervisor", "wb.c_sub": "CPU tier (c8i, nested virt)", "wb.c_sub2": "GPU is experimental",
        "wb.same": "One image; profiles set RuntimeClass, nodes",
        "wb.fwd": "kernel code", "wb.pin": "version pinned per group", "wb.back": "correctness, speedup",
        "lp.a": "Picking a GPU path without a starting point",
        "lp.b": "Free paths first, costs shown up front",
        "lp.reader": "New reader",
        "lp.pages": "46 pages", "lp.pages_sub": "scenarios A, B1, B2, C",
        "lp.gpu": "Starts a GPU path", "lp.gpu_sub": "without needing it",
        "lp.cost": "A few dollars", "lp.cost_sub": "per hour while it runs",
        "lp.c1": "Path 1: Reading", "lp.c2": "Path 2: Local run", "lp.free": "free",
        "lp.paid": "Paths 3 to 6: AWS", "lp.paid_sub": "after the free paths", "lp.paid_sub2": "quota, cost up front",
        "gs.a": "Starting the GPU nodes first",
        "gs.b": "Checking the plumbing on a local CPU first",
        "gs.start": "GPU nodes start", "gs.start_sub": "billing begins",
        "gs.err": "Error found", "gs.err_sub": "import error or", "gs.err_sub2": "missing setting",
        "gs.fix": "Fix it", "gs.rerun": "Run again",
        "gs.bill_a": "GPU node billing: continues while you fix and rerun",
        "gs.local": "Local CPU check", "gs.local_sub": "110 pytest tests,", "gs.local_sub2": "2-step GRPO dry run",
        "gs.env": "scripts/config.env", "gs.env_sub": "stops if a value it needs", "gs.env_sub2": "is empty or __SET_ME__",
        "gs.path": "Pick a path", "gs.path_sub": "A, B1, B2, C,", "gs.path_sub2": "production",
        "gs.free": "No AWS cost", "gs.bill_b": "GPU node billing",
        "bi.a": "Copying commands before the reasons",
        "bi.b": "\"Why\" first, \"how\" later",
        "bi.words": "Many new words at once", "bi.words_sub": "gVisor, Kata, nvproxy,",
        "bi.words_sub2": "RuntimeClass, GRPO",
        "bi.copy": "Typing commands", "bi.copy_sub": "without knowing why",
        "bi.stuck": "Stuck when things change", "bi.stuck_sub": "even a little",
        "bi.why": "Chapters 1 to 4: pictures", "bi.why_sub": "each term explained", "bi.why_sub2": "in one line",
        "bi.how": "Chapter 5: hands-on", "bi.how_sub": "your PC (free),", "bi.how_sub2": "AWS (optional)",
        "bi.see": "Check the grading yourself",
        "ly.title": "Three limits on the sorting function",
        "ly.desc": "A time limit stops the loop. Model files stay on the training server. New outbound connections are blocked by default.",
        "ly.time": "Running time", "ly.start": "Function starts", "ly.loop": "Loop still running", "ly.stop": "Stopped at the time limit",
        "ly.files": "File access", "ly.sandbox": "Sandbox", "ly.input": "Code and input list",
        "ly.trainer": "Training server", "ly.checkpoint": "Saved model files",
        "ly.file_note": "Model files stay on the training server, outside the sandbox.",
        "ly.network": "Outbound connections", "ly.external": "External server", "ly.blocked": "Blocked by default",
        "b02.a": "Plain containers: one server kernel shared",
        "b02.b": "Sandbox runtimes: one more wall between container and kernel",
        "b02.c": "Container", "b02.cpod": "pod {} container", "b02.wall": "Sentry or VM kernel", "b02.wall_sub": "one per pod",
        "b02.kern_a": "One server kernel", "b02.kern_b": "Server kernel",
        "b02.weak": "one kernel weakness",
        "b02.bad": "May be at risk", "b02.bad_sub": "A, B and C", "b02.good": "One more wall", "b02.good_sub": "in front of A, B and C",
        "tw.title": "When code opens input.txt", "tw.source": "Where the code runs", "tw.dest": "Who handles the request",
        "tw.rows": (("Regular container", "runc", "Node’s Linux kernel"),
                    ("Sandbox", "gVisor", "Sentry"), ("Virtual machine", "Kata", "Linux kernel in the VM")),
        "b03.a": "A microVM without a GPU, and a plain container",
        "b03.b": "Two ways to bring the GPU inside the wall",
        "b03.task": "Grading a GPU kernel", "b03.task_sub": "needs a real GPU",
        "b03.fc": "Firecracker-based microVM", "b03.nodev": "no device for a GPU", "b03.cant": "Cannot grade",
        "b03.runc": "Regular container", "b03.runc_sub": "runc", "b03.bug": "driver bug",
        "b03.host": "Reaches the server kernel",
        "b03.gv": "gVisor + nvproxy", "b03.gv_sub": "g5.xlarge (regular GPU VM)", "b03.check": "checks, forwards ioctls",
        "b03.gv_out": "Only allowlisted calls", "b03.gv_out_sub": "reach the server driver",
        "b03.kt": "Kata + VFIO", "b03.kt_sub": "g4dn.metal (bare metal)", "b03.pass": "whole GPU to the VM",
        "b03.kt_out": "Driver runs inside the VM", "b03.kt_out_sub": "hypervisor, device risks stay",
        "gp.title": "From the sandbox to the GPU",
        "gp.rows": (("gVisor", "nvproxy forwards supported requests to the node driver.", ("Code", "nvproxy", "Node driver", "A10G")),
                    ("Kata + QEMU", "The VM’s driver controls the physical GPU assigned to it.", ("Code in VM", "Driver in VM", "T4"))),
        "b04.a": "A fooled grader and mixed standards",
        "b04.b": "Cheating blocked, one version per batch",
        "b04.hack": "Answer that fooled the grader", "b04.hack_sub": "raises the score through a gap",
        "b04.mix": "v1 and v2 in one group", "b04.mix_sub": "grading standards mixed",
        "b04.wrong": "Wrong score", "b04.learn_bad": "Model learns the wrong thing",
        "b04.guard": "Harness blocks cheating", "b04.guard_sub": "separate processes, new inputs",
        "b04.pin": "One version per batch", "b04.pin_sub": "never mixed in a batch",
        "b04.right": "Consistent score", "b04.right_sub": "one grading standard",
        "b04.learn_good": "Model improves from the score",
        "rl.title": "Learning from the current model’s answers",
        "rl.model": "Current model", "rl.model_sub": "Two answers, one task",
        "rl.sandbox": "Sandbox", "rl.sandbox_sub": "Runs both submissions",
        "rl.trainer": "Trainer", "rl.trainer_sub": "Scores each answer",
        "rl.submit": "Submit code", "rl.result": "Correctness and timing", "rl.update": "Update from rewards",
        "b05.a": "Straight to AWS, then forgetting to delete",
        "b05.b": "Your PC first, then delete everything at once",
        "b05.aws": "Straight to AWS", "b05.aws_sub": "without the concepts",
        "b05.both": "Costs and config errors", "b05.both_sub": "at once",
        "b05.lost": "Hard to tell", "b05.lost_sub": "what the problem is",
        "b05.end": "Lab ends", "b05.forgot": "forget to delete",
        "b05.left": "Leftover resources", "b05.left_sub": "keep billing",
        "b05.pc": "Part 1: grade on your PC", "b05.pc_sub": "free, about 30 minutes",
        "b05.seen": "Grader's role checked", "b05.seen_sub": "you can stop here",
        "b05.opt": "optional",
        "b05.cloud": "Part 2: compare on AWS", "b05.cloud_sub": "3 runtimes, a few dollars",
        "b05.destroy": "cdk/destroy.sh",
        "b05.gone": "One stack deleted at once", "b05.gone_sub": "no hunting one by one",
    },
}


# Helpers for shapes figlib lacks. They only append plain SVG to fig.parts.

def _fits(text: str, size: int, room: float, what: str) -> None:
    need = text_width(text, size) + 16
    assert need <= room, f"label too wide for {what}: {text!r} needs {need:.0f} > {room:.0f}"


def vbox(fig, x, y, w, h, label, subs=(), *, icon=None, fill=GREY_FILL, stroke=MUTED_STROKE, color=INK, gid=None):
    """Tall box: optional icon above the name and up to three sub lines, centred as one group."""
    subs = [subs] if isinstance(subs, str) else [s for s in subs if s]
    fig.rect(x, y, w, h, fill=fill, stroke=stroke, gid=gid)
    block = (34 if icon else 0) + 13 + 17 * len(subs)
    top = y + (h - block) / 2
    assert top - y >= 10, f"box {gid or label!r} too short: {top - y:.0f}px padding"
    if icon:
        fig.icon(icon, x + w / 2 - 12, top, 24, color)
        top += 34
    cx = x + w / 2
    fig.text(cx, top + 10, label, color=color)
    for i, s in enumerate(subs):
        fig.text(cx, top + 10 + 17 * (i + 1), s, size=SMALL, color=color)
    _fits(label, SIZE, w, gid or label)
    for s in subs:
        _fits(s, SMALL, w, gid or label)


def stepnum(fig, cx, cy, n):
    """A circled step number drawn as shapes."""
    fig.parts.append(f'<circle cx="{cx}" cy="{cy}" r="8.5" fill="#FFFFFF" stroke="{INK}" stroke-width="1.2"/>')
    fig.text(cx, cy + 4.2, str(n), size=SMALL)


def edge_label(fig, x, y, lines, *, anchor="start", step=None, color=INK):
    """Multi-line 12 px edge label; an optional step number sits before the first line."""
    mark = 23 if step is not None else 0  # room for the circled number and its gap
    tx = x + mark if anchor == "start" else x
    if step is not None:
        first = text_width(lines[0], SMALL)
        stepnum(fig, x + 8.5 if anchor == "start" else x - first - 14.5, y - 4, step)
    for i, s in enumerate(lines):
        fig.text(tx, y + 16 * i, s, size=SMALL, color=color, anchor=anchor)
        w, extra = text_width(s, SMALL), mark if i == 0 else 0
        lo, hi = (tx - extra, tx + w) if anchor == "start" else (tx - w - extra, tx)
        assert lo >= 8 and hi <= fig.width - 8, f"edge label off canvas: {s!r} spans {lo:.0f}..{hi:.0f}"


def band(fig, x, y, w, h, label, *, fill, stroke, color):
    fig.rect(x, y, w, h, fill=fill, stroke=stroke, rx=4)
    fig.text(x + w / 2, y + h / 2 + 4.2, label, size=SMALL, color=color)
    _fits(label, SMALL, w, label)


# Pain point figures

def index_pain(lang: str) -> Figure:
    """docs/index.md: runc shares the host kernel and driver; v1 and v2 mixed in one GRPO group. Fix from Why."""
    t = T[lang]
    fig = Figure(760, 404)
    xs, ws = (16, 286, 538), (220, 204, 206)
    for p, (oy, letter, title) in enumerate(((0, "a", t["ix.a"]), (210, "b", t["ix.b"]))):
        fig.panel(16, oy + 26, letter, title)
        r1, r2 = oy + 58, oy + 132
        for top in (r1, r2):
            mid = top + 25
            fig.arrow([(xs[0] + ws[0], mid), (xs[1] - 2, mid)])
            fig.arrow([(xs[1] + ws[1], mid), (xs[2] - 2, mid)], color=RED if p == 0 else ACCENT if top == r2 else INK)
        fig.box(xs[0], r1, ws[0], 50, t["ix.code"], t["ix.code_sub"], icon="file-code", gid=f"n:code-{letter}")
        fig.box(xs[0], r2, ws[0], 50, t["ix.group"], icon="stack", gid=f"n:group-{letter}")
        if p == 0:
            fig.box(xs[1], r1, ws[1], 50, t["ix.runc"], t["ix.runc_sub"], icon="container", gid="n:runc")
            fig.box(xs[2], r1, ws[2], 50, t["ix.kern_a"], t["ix.kern_a_sub"], icon="server", fill=RED_FILL,
                    stroke=RED, color=RED, gid="n:kernel-a")
            fig.box(xs[1], r2, ws[1], 50, t["ix.mix"], t["ix.mix_sub"], icon="versions", gid="n:mix")
            fig.box(xs[2], r2, ws[2], 50, t["ix.bad"], icon="alert", fill=RED_FILL, stroke=RED, color=RED,
                    gid="n:bad")
        else:
            fig.box(xs[1], r1, ws[1], 50, t["ix.iso"], t["ix.iso_sub"], icon="shield-lock", fill=ACCENT_FILL,
                    stroke=ACCENT, gid="n:iso")
            fig.box(xs[2], r1, ws[2], 50, t["ix.kern_b"], icon="server", gid="n:kernel-b")
            fig.box(xs[1], r2, ws[1], 50, t["ix.pin"], t["ix.pin_sub"], icon="pin", gid="n:pin")
            fig.box(xs[2], r2, ws[2], 50, t["ix.good"], icon="check-circle", fill=ACCENT_FILL, stroke=ACCENT,
                    gid="n:good")
    return fig


def learning_paths_pain(lang: str) -> Figure:
    """docs/learning_paths.md: starting a GPU path blind costs per hour; free paths 1 and 2 first (TL;DR, Why)."""
    t = T[lang]
    fig = Figure(760, 362)
    w, gap, h = 158, 32, 104
    xs = [16 + i * (w + gap) for i in range(4)]
    for p, (oy, letter, title) in enumerate(((0, "a", t["lp.a"]), (184, "b", t["lp.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 52
        mid = top + h / 2
        for i in range(3):
            last = i == 2
            if p == 0:
                color, dash = (RED if last else INK), None
            else:
                color, dash = (MUTED_STROKE, "5 4") if last else (INK, None)
            fig.arrow([(xs[i] + w, mid), (xs[i + 1] - 2, mid)], color=color, dash=dash)
        vbox(fig, xs[0], top, w, h, t["lp.reader"], icon="person", gid=f"n:reader-{letter}")
        if p == 0:
            vbox(fig, xs[1], top, w, h, t["lp.pages"], t["lp.pages_sub"], icon="book", gid="n:pages")
            vbox(fig, xs[2], top, w, h, t["lp.gpu"], t["lp.gpu_sub"], icon="cpu", gid="n:gpu")
            vbox(fig, xs[3], top, w, h, t["lp.cost"], t["lp.cost_sub"], icon="alert", fill=RED_FILL, stroke=RED,
                 color=RED, gid="n:cost")
        else:
            vbox(fig, xs[1], top, w, h, t["lp.c1"], t["lp.free"], icon="book", fill=ACCENT_FILL, stroke=ACCENT,
                 gid="n:course1")
            vbox(fig, xs[2], top, w, h, t["lp.c2"], t["lp.free"], icon="terminal", fill=ACCENT_FILL, stroke=ACCENT,
                 gid="n:course2")
            vbox(fig, xs[3], top, w, h, t["lp.paid"], (t["lp.paid_sub"], t["lp.paid_sub2"]), icon="cloud",
                 gid="n:paid")
    return fig


def getting_started_pain(lang: str) -> Figure:
    """docs/handson/start.md: errors found after GPU nodes start keep billing; local CPU check first (Why)."""
    t = T[lang]
    fig = Figure(760, 422)
    w, gap, h = 158, 32, 104
    xs = [16 + i * (w + gap) for i in range(4)]
    span = xs[3] + w - xs[0]
    for p, (oy, letter, title) in enumerate(((0, "a", t["gs.a"]), (214, "b", t["gs.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 52
        mid = top + h / 2
        for i in range(3):
            fig.arrow([(xs[i] + w, mid), (xs[i + 1] - 2, mid)])
        by = top + h + 14
        if p == 0:
            vbox(fig, xs[0], top, w, h, t["gs.start"], t["gs.start_sub"], icon="cpu", gid="n:start-a")
            vbox(fig, xs[1], top, w, h, t["gs.err"], (t["gs.err_sub"], t["gs.err_sub2"]), icon="bug", gid="n:err")
            vbox(fig, xs[2], top, w, h, t["gs.fix"], icon="tools", gid="n:fix")
            vbox(fig, xs[3], top, w, h, t["gs.rerun"], icon="sync", gid="n:rerun")
            band(fig, xs[0], by, span, 26, t["gs.bill_a"], fill=RED_FILL, stroke=RED, color=RED)
        else:
            vbox(fig, xs[0], top, w, h, t["gs.local"], (t["gs.local_sub"], t["gs.local_sub2"]), icon="beaker",
                 fill=ACCENT_FILL, stroke=ACCENT, gid="n:local")
            vbox(fig, xs[1], top, w, h, t["gs.env"], (t["gs.env_sub"], t["gs.env_sub2"]), icon="file-code",
                 gid="n:env")
            vbox(fig, xs[2], top, w, h, t["gs.path"], (t["gs.path_sub"], t["gs.path_sub2"]), icon="git-branch",
                 gid="n:path")
            vbox(fig, xs[3], top, w, h, t["gs.start"], t["gs.start_sub"], icon="cpu", gid="n:start-b")
            band(fig, xs[0], by, w, 26, t["gs.free"], fill=ACCENT_FILL, stroke=ACCENT, color=INK)
            band(fig, xs[3], by, w, 26, t["gs.bill_b"], fill=GREY_FILL, stroke=MUTED_STROKE, color=INK)
    return fig


def beginner_index_pain(lang: str) -> Figure:
    """docs/beginner/index.md: new words and commands without reasons; why first, then how (Why)."""
    t = T[lang]
    fig = Figure(760, 362)
    w, gap, h = 216, 40, 104
    xs = [16 + i * (w + gap) for i in range(3)]
    for p, (oy, letter, title) in enumerate(((0, "a", t["bi.a"]), (184, "b", t["bi.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 52
        mid = top + h / 2
        for i in range(2):
            color = INK if i == 0 else (RED if p == 0 else ACCENT)
            fig.arrow([(xs[i] + w, mid), (xs[i + 1] - 2, mid)], color=color)
        if p == 0:
            vbox(fig, xs[0], top, w, h, t["bi.words"], (t["bi.words_sub"], t["bi.words_sub2"]), icon="typography",
                 gid="n:words")
            vbox(fig, xs[1], top, w, h, t["bi.copy"], t["bi.copy_sub"], icon="terminal", gid="n:copy")
            vbox(fig, xs[2], top, w, h, t["bi.stuck"], t["bi.stuck_sub"], icon="alert", fill=RED_FILL, stroke=RED,
                 color=RED, gid="n:stuck")
        else:
            vbox(fig, xs[0], top, w, h, t["bi.why"], (t["bi.why_sub"], t["bi.why_sub2"]), icon="book", gid="n:why")
            vbox(fig, xs[1], top, w, h, t["bi.how"], (t["bi.how_sub"], t["bi.how_sub2"]), icon="terminal",
                 gid="n:how")
            vbox(fig, xs[2], top, w, h, t["bi.see"], icon="check-circle", fill=ACCENT_FILL, stroke=ACCENT,
                 gid="n:see")
    return fig


def beginner_02_pain(lang: str) -> Figure:
    """docs/beginner/02_container_vs_sandbox.md: one shared kernel; sandbox runtimes add one wall per pod (TL;DR),
    between the container in that pod and the server kernel."""
    t = T[lang]
    fig = Figure(760, 470)
    cx, cw, wx, ww, kx, kw, ox, ow = 16, 116, 166, 142, 340, 126, 608, 136
    for p, (oy, letter, title) in enumerate(((0, "a", t["b02.a"]), (236, "b", t["b02.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 56
        rows = [top + i * 58 for i in range(3)]
        kh = rows[2] + 42 - top
        fig.box(kx, top, kw, kh, t["b02.kern_a"] if p == 0 else t["b02.kern_b"], icon="server",
                gid=f"n:kernel-{letter}")
        for name, ry in zip("ABC", rows):
            mid = ry + 21
            clabel = f"{t['b02.c']} {name}" if p == 0 else t["b02.cpod"].format(name)
            fig.box(cx, ry, cw, 42, clabel, gid=f"n:c{name}-{letter}")
            if p == 0:
                fig.arrow([(cx + cw, mid), (kx - 2, mid)])
            else:
                fig.arrow([(cx + cw, mid), (wx - 2, mid)])
                fig.box(wx, ry, ww, 42, t["b02.wall"], t["b02.wall_sub"], fill=ACCENT_FILL, stroke=ACCENT,
                        gid=f"n:wall{name}")
                fig.arrow([(wx + ww, mid), (kx - 2, mid)])
        kmid = top + kh / 2
        fig.arrow([(kx + kw, kmid), (ox - 2, kmid)], color=RED if p == 0 else ACCENT,
                  label=t["b02.weak"], label_at=((kx + kw + ox) / 2, kmid - 8))
        _fits(t["b02.weak"], SMALL, ox - kx - kw + 14, "b02 edge")
        if p == 0:
            vbox(fig, ox, kmid - 52, ow, 104, t["b02.bad"], t["b02.bad_sub"], icon="alert", fill=RED_FILL, stroke=RED, color=RED,
                 gid="n:bad")
        else:
            vbox(fig, ox, kmid - 52, ow, 104, t["b02.good"], t["b02.good_sub"], icon="shield-lock", fill=ACCENT_FILL,
                 stroke=ACCENT, gid="n:good")
    return fig


def beginner_03_pain(lang: str) -> Figure:
    """docs/beginner/03_gpu_sandbox.md: microVM has no GPU device, runc lets driver bugs reach the kernel;
    gVisor + nvproxy and Kata + VFIO from the body."""
    t = T[lang]
    fig = Figure(760, 458)
    sx, sw, rx, rw, ox, ow = 16, 142, 194, 186, 532, 212
    for p, (oy, letter, title) in enumerate(((0, "a", t["b03.a"]), (232, "b", t["b03.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 56
        y1, y2 = top + 27, top + 135
        vbox(fig, sx, top, sw, 162, t["b03.task"], t["b03.task_sub"], icon="cpu", gid=f"n:task-{letter}")
        lx = (rx + rw + ox) / 2
        for y in (y1, y2):
            fig.arrow([(sx + sw, y), (rx - 2, y)])
        if p == 0:
            rows = ((y1, t["b03.fc"], None, t["b03.nodev"], t["b03.cant"], None, "n:fc"),
                    (y2, t["b03.runc"], t["b03.runc_sub"], t["b03.bug"], t["b03.host"], None, "n:runc"))
        else:
            rows = ((y1, t["b03.gv"], t["b03.gv_sub"], t["b03.check"], t["b03.gv_out"], t["b03.gv_out_sub"], "n:gv"),
                    (y2, t["b03.kt"], t["b03.kt_sub"], t["b03.pass"], t["b03.kt_out"], t["b03.kt_out_sub"], "n:kt"))
        for y, name, sub, edge, out, out_sub, gid in rows:
            fig.box(rx, y - 27, rw, 54, name, sub, fill=ACCENT_FILL if p else GREY_FILL,
                    stroke=ACCENT if p else MUTED_STROKE, gid=gid)
            fig.arrow([(rx + rw, y), (ox - 2, y)], color=RED if p == 0 else ACCENT, label=edge, label_at=(lx, y - 8))
            _fits(edge, SMALL, ox - rx - rw + 14, "b03 edge")
            if p == 0:
                fig.box(ox, y - 27, ow, 54, out, out_sub, icon="alert", fill=RED_FILL, stroke=RED, color=RED,
                        gid=f"{gid}-out")
            else:
                fig.box(ox, y - 27, ow, 54, out, out_sub, icon="check-circle", fill=ACCENT_FILL, stroke=ACCENT,
                        gid=f"{gid}-out")
    return fig


def beginner_04_pain(lang: str) -> Figure:
    """docs/beginner/04_rl_and_sandbox.md: a fooled grader or mixed v1/v2 gives wrong scores; harness and
    one version per batch from the body."""
    t = T[lang]
    fig = Figure(760, 444)
    ix, iw, sx, sw, lx, lw = 16, 252, 332, 160, 548, 196
    for p, (oy, letter, title) in enumerate(((0, "a", t["b04.a"]), (224, "b", t["b04.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 56
        y1, y2 = top + 27, top + 127
        mid = (y1 + y2) / 2
        bad = p == 0
        for y in (y1, y2):
            fig.arrow([(ix + iw, y), (sx - 2, y)])
        fig.arrow([(sx + sw, mid), (lx - 2, mid)], color=RED if bad else ACCENT)
        if bad:
            fig.box(ix, y1 - 27, iw, 54, t["b04.hack"], t["b04.hack_sub"], icon="bug", gid="n:hack")
            fig.box(ix, y2 - 27, iw, 54, t["b04.mix"], t["b04.mix_sub"], icon="versions", gid="n:mix")
            vbox(fig, sx, top, sw, 154, t["b04.wrong"], icon="alert", fill=RED_FILL, stroke=RED, color=RED,
                 gid="n:wrong")
            vbox(fig, lx, mid - 52, lw, 104, t["b04.learn_bad"], icon="hubot", fill=RED_FILL, stroke=RED, color=RED,
                 gid="n:learn-a")
        else:
            fig.box(ix, y1 - 27, iw, 54, t["b04.guard"], t["b04.guard_sub"], icon="shield-check", gid="n:guard")
            fig.box(ix, y2 - 27, iw, 54, t["b04.pin"], t["b04.pin_sub"], icon="pin", gid="n:pin")
            vbox(fig, sx, top, sw, 154, t["b04.right"], t["b04.right_sub"], icon="check-circle", fill=ACCENT_FILL,
                 stroke=ACCENT, gid="n:right")
            vbox(fig, lx, mid - 52, lw, 104, t["b04.learn_good"], icon="hubot", gid="n:learn-b")
    return fig


def beginner_05_pain(lang: str) -> Figure:
    """docs/beginner/05_hands_on.md: AWS before the concepts, and a forgotten delete; part 1 on the PC first and
    cdk/destroy.sh from the body."""
    t = T[lang]
    fig = Figure(760, 404)
    xs, ws = (16, 260, 530), (196, 190, 214)
    for p, (oy, letter, title) in enumerate(((0, "a", t["b05.a"]), (210, "b", t["b05.b"]))):
        fig.panel(16, oy + 26, letter, title)
        r1, r2 = oy + 58, oy + 132
        m1, m2 = r1 + 25, r2 + 25
        lx = (xs[0] + ws[0] + xs[2]) / 2
        if p == 0:
            fig.arrow([(xs[0] + ws[0], m1), (xs[1] - 2, m1)])
            fig.arrow([(xs[1] + ws[1], m1), (xs[2] - 2, m1)], color=RED)
            fig.box(xs[0], r1, ws[0], 50, t["b05.aws"], t["b05.aws_sub"], icon="cloud", gid="n:aws")
            fig.box(xs[1], r1, ws[1], 50, t["b05.both"], t["b05.both_sub"], icon="bug", gid="n:both")
            fig.box(xs[2], r1, ws[2], 50, t["b05.lost"], t["b05.lost_sub"], icon="alert", fill=RED_FILL, stroke=RED,
                    color=RED, gid="n:lost")
            fig.arrow([(xs[0] + ws[0], m2), (xs[2] - 2, m2)], color=RED, label=t["b05.forgot"], label_at=(lx, m2 - 8),
                      label_color=RED)
            fig.box(xs[2], r2, ws[2], 50, t["b05.left"], t["b05.left_sub"], icon="credit-card", fill=RED_FILL,
                    stroke=RED, color=RED, gid="n:left")
        else:
            fig.arrow([(xs[0] + ws[0], m1), (xs[1] - 2, m1)])
            fig.arrow([(xs[1] + ws[1], m1), (xs[2] - 2, m1)], color=MUTED_STROKE, dash="5 4", label=t["b05.opt"],
                      label_at=((xs[1] + ws[1] + xs[2]) / 2, m1 - 8))
            _fits(t["b05.opt"], SMALL, xs[2] - xs[1] - ws[1] + 14, "b05 edge")
            fig.box(xs[0], r1, ws[0], 50, t["b05.pc"], t["b05.pc_sub"], icon="device-desktop", gid="n:pc")
            fig.box(xs[1], r1, ws[1], 50, t["b05.seen"], t["b05.seen_sub"], icon="check-circle", fill=ACCENT_FILL,
                    stroke=ACCENT, gid="n:seen")
            fig.box(xs[2], r1, ws[2], 50, t["b05.cloud"], t["b05.cloud_sub"], icon="cloud", gid="n:cloud")
            fig.arrow([(xs[0] + ws[0], m2), (xs[2] - 2, m2)], color=ACCENT, label=t["b05.destroy"],
                      label_at=(lx, m2 - 8))
            fig.box(xs[2], r2, ws[2], 50, t["b05.gone"], t["b05.gone_sub"], icon="trash", fill=ACCENT_FILL,
                    stroke=ACCENT, gid="n:gone")
        fig.box(xs[0], r2, ws[0], 50, t["b05.end"], icon="check", gid=f"n:end-{letter}")
    return fig


# Main figures

def index_what_we_build(lang: str) -> Figure:
    """docs/index.md "만드는 것": trainer, three sandbox runtimes in EC2 pools, version pinning per group."""
    t = T[lang]
    fig = Figure(760, 340)
    tx, tw_, px, pw = 16, 266, 478, 266
    top, rows_top, row_h, row_gap = 16, 52, 68, 12
    bottom = rows_top + 3 * row_h + 2 * row_gap
    centre = (rows_top + bottom) / 2
    mh = 140
    my = centre - mh / 2
    fig.container(tx, my - 32, tw_, mh + 48, t["wb.train"])
    _fits(t["wb.train"], SMALL, tw_ - 4, "trainer title")
    vbox(fig, tx + 16, my, tw_ - 32, mh, t["wb.model"], (t["wb.model_sub"], t["wb.model_sub2"]), icon="hubot",
         gid="n:policy")
    fig.container(px, top, pw, bottom + 44 - top, t["wb.pool"], icon="shield-lock", stroke=ACCENT, color=ACCENT,
                  bold=True)
    rows = ((t["wb.g"], (t["wb.g_sub"],), "n:gvisor"), (t["wb.q"], (t["wb.q_sub"],), "n:kata-qemu"),
            (t["wb.c"], (t["wb.c_sub"], t["wb.c_sub2"]), "n:kata-clh"))
    for i, (name, subs, gid) in enumerate(rows):
        vbox(fig, px + 16, rows_top + i * (row_h + row_gap), pw - 32, row_h, name, subs, fill=ACCENT_FILL,
             stroke=ACCENT, gid=gid)
    fig.text(px + pw / 2, bottom + 27, t["wb.same"], size=SMALL)
    _fits(t["wb.same"], SMALL, pw, "pool footer")
    model_r = tx + tw_ - 16
    lx = (tx + tw_ + px) / 2
    fy, by = centre - 30, centre + 30
    fig.arrow([(model_r, fy), (px - 2, fy)], width=2.0)
    fig.text(lx, fy - 24, t["wb.fwd"], size=SMALL)
    fig.text(lx, fy - 8, t["wb.pin"], size=SMALL)
    fig.arrow([(px, by), (model_r + 2, by)], width=2.0)
    fig.text(lx, by - 8, t["wb.back"], size=SMALL)
    for s in (t["wb.fwd"], t["wb.pin"], t["wb.back"]):
        _fits(s, SMALL, px - tx - tw_, "wb edge")
    return fig


def beginner_01_layers(lang: str) -> Figure:
    """Show the time limit, file boundary and outbound network rule for one sorting function."""
    t = T[lang]
    fig = Figure(512, 434)
    fig.parts.append(f'<title>{escape(t["ly.title"])}</title><desc>{escape(t["ly.desc"])}</desc>')
    fig.text(16, 31, t["ly.title"], size=24, bold=True, anchor="start")
    for top, height, icon, heading in ((48, 102, "clock", "ly.time"),
                                        (160, 138, "file-directory", "ly.files"),
                                        (308, 114, "globe", "ly.network")):
        fig.rect(12, top, 488, height, fill="#FFFFFF", stroke=CONTAINER, rx=10)
        fig.icon(icon, 28, top + 12, 24, ACCENT)
        fig.text(63, top + 32, t[heading], size=21, bold=True, anchor="start")

    # A timeout takes effect at the end of the run.
    fig.line([(36, 112), (476, 112)], color=ACCENT, width=3)
    fig.parts.append(f'<circle cx="36" cy="112" r="4" fill="{ACCENT}"/>')
    fig.line([(476, 103), (476, 121)], color=ACCENT, width=3)
    fig.text(256, 105, t["ly.loop"], size=18)
    fig.text(31, 139, t["ly.start"], size=17, anchor="start")
    fig.text(481, 139, t["ly.stop"], size=17, bold=True, anchor="end")

    # Separate compartments show where the files live before the code even starts.
    for left, title, files, fill in ((28, "ly.sandbox", "ly.input", ACCENT_FILL),
                                      (280, "ly.trainer", "ly.checkpoint", GREY_FILL)):
        fig.rect(left, 207, 204, 53, fill=fill, stroke=CONTAINER)
        fig.text(left + 102, 229, t[title], size=18, bold=True)
        fig.text(left + 102, 250, t[files], size=17)
        _fits(t[files], 17, 204, files)
    fig.icon("lock", 246, 222, 20)
    fig.text(28, 284, t["ly.file_note"], size=16, anchor="start")
    _fits(t["ly.file_note"], 16, 464, "file boundary caption")

    # The line stops before it reaches the external server.
    fig.rect(28, 364, 130, 40, fill=ACCENT_FILL, stroke=CONTAINER)
    fig.text(93, 390, t["ly.sandbox"], size=18)
    fig.rect(354, 364, 130, 40, fill=GREY_FILL, stroke=CONTAINER)
    fig.text(419, 390, t["ly.external"], size=18)
    fig.arrow([(158, 385), (296, 385)], color=ACCENT, width=2)
    fig.line([(304, 376), (304, 394)], color=RED, width=3)
    fig.text(250, 373, t["ly.blocked"], size=17, bold=True)
    return fig


def beginner_label(fig, x, y, width, label, detail=None, *, highlight=False):
    """Label a node in a request path, with an optional second line."""
    height = 62 if detail else 46
    fig.rect(x, y, width, height, fill=ACCENT_FILL if highlight else GREY_FILL, stroke=CONTAINER)
    fig.text(x + width / 2, y + 28, label, size=17, bold=True)
    _fits(label, 17, width, label)
    if detail:
        fig.text(x + width / 2, y + 49, detail, size=16)
        _fits(detail, 16, width, detail)


def beginner_02_three_walls(lang: str) -> Figure:
    """Follow the same file-open request to its first handler in each runtime."""
    t = T[lang]
    fig = Figure(510, 306)
    fig.text(16, 31, t["tw.title"], size=24, bold=True, anchor="start")
    fig.text(16, 68, t["tw.source"], size=17, anchor="start")
    fig.text(268, 68, t["tw.dest"], size=17, anchor="start")
    for i, (source, runtime, handler) in enumerate(t["tw.rows"]):
        top = 82 + 74 * i
        beginner_label(fig, 16, top, 180, source, runtime)
        fig.arrow([(196, top + 31), (264, top + 31)], color=ACCENT, width=2)
        beginner_label(fig, 268, top + 8, 226, handler, highlight=True)
    return fig


def beginner_03_gpu_path(lang: str) -> Figure:
    """Compare the node driver with the guest driver of the VM that owns a GPU."""
    t = T[lang]
    fig = Figure(530, 298)
    fig.text(16, 31, t["gp.title"], size=24, bold=True, anchor="start")
    for i, (name, summary, nodes) in enumerate(t["gp.rows"]):
        top = 50 + 126 * i
        fig.text(16, top + 15, name, size=21, bold=True, color=ACCENT, anchor="start")
        fig.text(16, top + 43, summary, size=17, anchor="start")
        _fits(summary, 17, fig.width - 16, name)
        widths = (84, 106, 146, 78) if len(nodes) == 4 else (138, 188, 100)
        gap = (fig.width - 32 - sum(widths)) / (len(nodes) - 1)
        x = 16
        for j, (label, width) in enumerate(zip(nodes, widths, strict=True)):
            beginner_label(fig, x, top + 56, width, label, highlight=j == len(nodes) - 2)
            if j + 1 < len(nodes):
                fig.arrow([(x + width, top + 79), (x + width + gap - 2, top + 79)], width=1.6)
            x += width + gap
    return fig


def beginner_04_rl_loop(lang: str) -> Figure:
    """The sandbox returns results; the trainer turns those results into rewards."""
    t = T[lang]
    fig = Figure(524, 280)
    fig.text(16, 31, t["rl.title"], size=23, bold=True, anchor="start")
    beginner_label(fig, 16, 58, 189, t["rl.model"], t["rl.model_sub"])
    beginner_label(fig, 316, 58, 191, t["rl.sandbox"], t["rl.sandbox_sub"], highlight=True)
    beginner_label(fig, 16, 202, 189, t["rl.trainer"], t["rl.trainer_sub"])
    fig.arrow([(205, 92), (313, 92)], color=ACCENT, width=2)
    fig.text(260, 81, t["rl.submit"], size=16)
    fig.arrow([(412, 120), (412, 233), (208, 233)], color=ACCENT, width=2)
    fig.text(311, 218, t["rl.result"], size=16)
    fig.arrow([(110, 202), (110, 123)], color=ACCENT, width=2)
    fig.text(124, 166, t["rl.update"], size=16, anchor="start")
    return fig


FIGURES = {
    "index": index_pain,
    "index--what-we-build": index_what_we_build,
    "learning_paths": learning_paths_pain,
    "getting_started": getting_started_pain,
    "beginner-index": beginner_index_pain,
    "beginner-01_why_sandbox--layers": beginner_01_layers,
    "beginner-02_container_vs_sandbox": beginner_02_pain,
    "beginner-02_container_vs_sandbox--three-walls": beginner_02_three_walls,
    "beginner-03_gpu_sandbox": beginner_03_pain,
    "beginner-03_gpu_sandbox--gpu-path": beginner_03_gpu_path,
    "beginner-04_rl_and_sandbox": beginner_04_pain,
    "beginner-04_rl_and_sandbox--rl-loop": beginner_04_rl_loop,
    "beginner-05_hands_on": beginner_05_pain,
}
