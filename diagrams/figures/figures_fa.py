"""Schematics for the README, the getting-started page and the beginner guide.

Each function draws one figure in one language from shared geometry. Every box and edge comes from
the page named in its docstring.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from figlib import (ACCENT, ACCENT_FILL, CONTAINER, GREY_FILL, INK, MUTED_STROKE, RED, RED_FILL, SIZE, SMALL,
                    Figure, text_width)

T = {
    "ko": {
        # README.md, 채점 요청 한 건 따라가기
        "wb.train": "학습 (EC2 GPU 노드 또는 HyperPod 노드)",
        "wb.model": "policy 모델 + vLLM", "wb.model_sub": "GRPO, on-policy",
        "wb.model_sub2": "g5.2xlarge 또는 ml.g5.2xlarge",
        "wb.pool": "샌드박스 pool (EC2 GPU, CPU 노드)",
        "wb.g": "gVisor + nvproxy", "wb.g_sub": "g5.xlarge (A10G)",
        "wb.q": "Kata + QEMU", "wb.q_sub": "g4dn.metal (T4)",
        "wb.c": "Kata + Cloud Hypervisor", "wb.c_sub": "CPU 계층 (c8i, nested virt)", "wb.c_sub2": "GPU는 실험적",
        "wb.same": "같은 이미지, 프로필이 RuntimeClass와 노드를 정함",
        "wb.fwd": "커널 코드", "wb.pin": "group 단위 버전 고정", "wb.back": "정확성, speedup",
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
        # docs/beginner/01_why_sandbox.md, 실행 시간과 파일 접근
        "ly.title": "정렬 함수에 적용하는 세 가지 제한",
        "ly.desc": "반복문은 정해진 시간이 지나면 멈춥니다. 모델 파일은 학습 서버에 두고, 샌드박스에서 외부로 여는 연결은 기본으로 차단합니다.",
        "ly.time": "실행 시간", "ly.start": "함수 시작", "ly.loop": "끝나지 않는 반복문", "ly.stop": "시간이 다 되면 중단",
        "ly.files": "파일 접근", "ly.sandbox": "샌드박스", "ly.input": "정렬 코드와 숫자 목록",
        "ly.trainer": "학습 서버", "ly.checkpoint": "저장해 둔 모델 파일",
        "ly.file_note": "학습 서버의 모델 파일은 샌드박스와 공유하지 않습니다.",
        "ly.network": "외부 연결", "ly.external": "외부 서버", "ly.blocked": "기본 차단",
        # docs/beginner/02_container_vs_sandbox.md, 세 가지 격리 방식
        "tw.title": "코드가 input.txt를 열 때", "tw.source": "코드가 실행되는 곳", "tw.dest": "요청을 받는 곳",
        "tw.rows": (("일반 컨테이너", "runc", "노드의 Linux 커널"),
                    ("샌드박스", "gVisor", "Sentry"), ("가상 머신", "Kata", "VM 안의 Linux 커널")),
        # docs/beginner/03_gpu_sandbox.md, GPU 접근 경로
        "gp.gvisor": "gVisor 샌드박스", "gp.kata": "Kata + QEMU 가상 머신",
        "gp.gvisor_desc": "Sentry가 코드의 요청을 받습니다. GPU 요청은 nvproxy를 거쳐 샌드박스 밖에 있는 노드의 NVIDIA 드라이버로 전달됩니다.",
        "gp.kata_desc": "가상 머신의 Linux 커널이 코드의 요청을 받습니다. VM 안의 NVIDIA 드라이버가 이 VM에 배정된 GPU를 제어합니다.",
        "gp.code": "제출한 코드", "gp.guest": "VM의 Linux 커널",
        "gp.file": "파일", "gp.network": "네트워크", "gp.request": "GPU 요청",
        "gp.node": "샌드박스 밖의 노드", "gp.driver": "NVIDIA 드라이버",
        "gp.node_gpu": "노드의 GPU", "gp.vm_gpu": "VM에 할당된 GPU",
        # docs/beginner/04_rl_and_sandbox.md, 학습 루프에서 샌드박스의 자리
        "rl.title": "현재 모델이 만든 답으로 학습하는 과정",
        "rl.model": "현재 모델", "rl.model_sub": "같은 문제에 답 두 개 작성",
        "rl.sandbox": "샌드박스", "rl.sandbox_sub": "두 답을 각각 실행",
        "rl.trainer": "학습 프로그램", "rl.trainer_sub": "답마다 보상 계산",
        "rl.submit": "코드 제출", "rl.result": "정답 여부와 실행 시간", "rl.update": "보상으로 모델 조정",
    },
    "en": {
        "wb.train": "Training (EC2 GPU node or HyperPod node)",
        "wb.model": "Policy model + vLLM", "wb.model_sub": "GRPO, on-policy",
        "wb.model_sub2": "g5.2xlarge or ml.g5.2xlarge",
        "wb.pool": "Sandbox pools (EC2 GPU, CPU nodes)",
        "wb.g": "gVisor + nvproxy", "wb.g_sub": "g5.xlarge (A10G)",
        "wb.q": "Kata + QEMU", "wb.q_sub": "g4dn.metal (T4)",
        "wb.c": "Kata + Cloud Hypervisor", "wb.c_sub": "CPU tier (c8i, nested virt)", "wb.c_sub2": "GPU is experimental",
        "wb.same": "One image; profiles set RuntimeClass, nodes",
        "wb.fwd": "kernel code", "wb.pin": "version pinned per group", "wb.back": "correctness, speedup",
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
        "ly.title": "Three limits on the sorting function",
        "ly.desc": "A time limit stops the loop. Model files stay on the training server. New outbound connections are blocked by default.",
        "ly.time": "Running time", "ly.start": "Function starts", "ly.loop": "Loop still running", "ly.stop": "Stopped at the time limit",
        "ly.files": "File access", "ly.sandbox": "Sandbox", "ly.input": "Code and input list",
        "ly.trainer": "Training server", "ly.checkpoint": "Saved model files",
        "ly.file_note": "Model files stay on the training server, outside the sandbox.",
        "ly.network": "Outbound connections", "ly.external": "External server", "ly.blocked": "Blocked by default",
        "tw.title": "When code opens input.txt", "tw.source": "Where the code runs", "tw.dest": "Who handles the request",
        "tw.rows": (("Regular container", "runc", "Node’s Linux kernel"),
                    ("Sandbox", "gVisor", "Sentry"), ("Virtual machine", "Kata", "Linux kernel in the VM")),
        "gp.gvisor": "gVisor sandbox", "gp.kata": "Kata + QEMU virtual machine",
        "gp.gvisor_desc": "Sentry receives the code’s requests. GPU requests go through nvproxy to the node’s NVIDIA driver outside the sandbox.",
        "gp.kata_desc": "The VM’s Linux kernel receives the code’s requests. The NVIDIA driver inside the VM controls the GPU assigned to it.",
        "gp.code": "Submitted code", "gp.guest": "VM’s Linux kernel",
        "gp.file": "File", "gp.network": "Network", "gp.request": "GPU request",
        "gp.node": "Outside the sandbox", "gp.driver": "NVIDIA driver",
        "gp.node_gpu": "Node GPU", "gp.vm_gpu": "Assigned GPU",
        "rl.title": "Learning from the current model’s answers",
        "rl.model": "Current model", "rl.model_sub": "Two answers, one task",
        "rl.sandbox": "Sandbox", "rl.sandbox_sub": "Runs both submissions",
        "rl.trainer": "Trainer", "rl.trainer_sub": "Scores each answer",
        "rl.submit": "Submit code", "rl.result": "Correctness and timing", "rl.update": "Update from rewards",
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


def band(fig, x, y, w, h, label, *, fill, stroke, color):
    fig.rect(x, y, w, h, fill=fill, stroke=stroke, rx=4)
    fig.text(x + w / 2, y + h / 2 + 4.2, label, size=SMALL, color=color)
    _fits(label, SMALL, w, label)


# Pain point figures

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


# Main figures

def index_what_we_build(lang: str) -> Figure:
    """The README follows a batch from the trainer to its versioned grading pool."""
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
    for left, title, files, fill, icon in ((28, "ly.sandbox", "ly.input", ACCENT_FILL, "shield-lock"),
                                           (280, "ly.trainer", "ly.checkpoint", GREY_FILL, "server")):
        fig.rect(left, 207, 204, 53, fill=fill, stroke=CONTAINER)
        beginner_icon_heading(fig, left, 230, 204, t[title], icon, size=18)
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


def beginner_icon_heading(fig, x, baseline, width, label, icon, *, size=17):
    """Center an Octicon and its label, leaving the line below free for a caption."""
    icon_size, gap = 24, 8
    group_width = icon_size + gap + text_width(label, size, bold=True)
    assert group_width + 12 <= width, f"icon and label too wide for {label!r}"
    left = x + (width - group_width) / 2
    fig.icon(icon, left, baseline - 18, icon_size, ACCENT)
    fig.text(left + icon_size + gap, baseline, label, size=size, bold=True, anchor="start")


def beginner_label(fig, x, y, width, label, detail=None, *, highlight=False, icon=None):
    """Label a node in a request path, with an optional second line."""
    height = 62 if detail else 46
    fig.rect(x, y, width, height, fill=ACCENT_FILL if highlight else GREY_FILL, stroke=CONTAINER)
    if icon:
        beginner_icon_heading(fig, x, y + 28, width, label, icon)
    else:
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
    icons = ("container", "shield-lock", "device-desktop")
    for i, ((source, runtime, handler), icon) in enumerate(zip(t["tw.rows"], icons, strict=True)):
        top = 82 + 74 * i
        beginner_label(fig, 16, top, 196, source, runtime, icon=icon)
        fig.arrow([(212, top + 31), (264, top + 31)], color=ACCENT, width=2)
        beginner_label(fig, 268, top + 8, 226, handler, highlight=True)
    return fig


def beginner_03_runtime_path(lang: str, *, kata: bool) -> Figure:
    """Use the same landmarks in both drawings and move the boundary around the guest driver."""
    t = T[lang]
    fig = Figure(544, 302)
    heading = t["gp.kata"] if kata else t["gp.gvisor"]
    description = t["gp.kata_desc"] if kata else t["gp.gvisor_desc"]
    fig.parts.append(f"<title>{escape(heading)}</title><desc>{escape(description)}</desc>")

    fig.rect(6, 5, 532 if kata else 330, 237, fill="#FFFFFF", stroke=ACCENT, width=2, rx=12)
    fig.icon("shield-lock", 19, 14, 22, ACCENT)
    fig.text(48, 32, heading, size=20, bold=True, color=ACCENT, anchor="start")
    beginner_label(fig, 74, 44, 180, t["gp.code"], icon="file-code")
    fig.arrow([(164, 90), (164, 106)])
    beginner_label(fig, 64, 109, 200, t["gp.guest"] if kata else "Sentry")

    # Keep file and network requests visible, but only follow the GPU branch to a device.
    for left, width, label, start_x in ((16, 70, t["gp.file"], 116), (97, 102, t["gp.network"], 148)):
        center = left + width / 2
        fig.arrow([(start_x, 155), (center, 176)], color=MUTED_STROKE)
        beginner_label(fig, left, 179, width, label)
    fig.arrow([(215, 155), (268, 176 if kata else 170)], color=ACCENT, width=2)
    if kata:
        beginner_label(fig, 210, 179, 116, t["gp.request"], highlight=True)
    else:
        beginner_label(fig, 210, 173, 116, t["gp.request"], "nvproxy", highlight=True)
        fig.text(439, 165, t["gp.node"], size=17, anchor="middle")

    fig.arrow([(326, 202), (351, 202)], color=ACCENT, width=2)
    beginner_label(fig, 354, 179, 170, t["gp.driver"], highlight=True, icon="gear")
    fig.arrow([(439, 225), (439, 254)], color=ACCENT, width=2)
    fig.rect(344, 257, 190, 39, fill=GREY_FILL, stroke=CONTAINER)
    fig.icon("cpu", 352, 266, 21)
    gpu = t["gp.vm_gpu"] if kata else t["gp.node_gpu"]
    fig.text(451, 283, gpu, size=17, bold=True)
    _fits(gpu, 17, 158, "GPU label")
    return fig


def beginner_04_rl_loop(lang: str) -> Figure:
    """The sandbox returns results; the trainer turns those results into rewards."""
    t = T[lang]
    fig = Figure(524, 280)
    fig.text(16, 31, t["rl.title"], size=23, bold=True, anchor="start")
    beginner_label(fig, 16, 58, 189, t["rl.model"], t["rl.model_sub"], icon="ai-model")
    beginner_label(fig, 316, 58, 191, t["rl.sandbox"], t["rl.sandbox_sub"], highlight=True, icon="shield-lock")
    beginner_label(fig, 16, 202, 189, t["rl.trainer"], t["rl.trainer_sub"], icon="sliders")
    fig.arrow([(205, 92), (313, 92)], color=ACCENT, width=2)
    fig.text(260, 81, t["rl.submit"], size=16)
    fig.arrow([(412, 120), (412, 233), (208, 233)], color=ACCENT, width=2)
    fig.text(311, 218, t["rl.result"], size=16)
    fig.arrow([(110, 202), (110, 123)], color=ACCENT, width=2)
    fig.text(124, 166, t["rl.update"], size=16, anchor="start")
    return fig


FIGURES = {
    "index--what-we-build": index_what_we_build,
    "getting_started": getting_started_pain,
    "beginner-01_why_sandbox--layers": beginner_01_layers,
    "beginner-02_container_vs_sandbox--three-walls": beginner_02_three_walls,
    "beginner-03_gpu_sandbox--gvisor": lambda lang: beginner_03_runtime_path(lang, kata=False),
    "beginner-03_gpu_sandbox--kata-qemu": lambda lang: beginner_03_runtime_path(lang, kata=True),
    "beginner-04_rl_and_sandbox--rl-loop": beginner_04_rl_loop,
}
