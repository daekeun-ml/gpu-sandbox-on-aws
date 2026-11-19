"""Pain point and main schematics for the home page, the path pages and the beginner guide (group fa).

Each function draws one figure in one language from shared geometry. Every box and edge comes from
the page named in its docstring.
"""

from __future__ import annotations

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
        "wb.pool": "샌드박스 풀 (EC2 GPU, CPU 노드)",
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
        # docs/getting_started.md
        "gs.a": "GPU 노드부터 띄울 때",
        "gs.b": "로컬 CPU에서 파이프라인부터 확인할 때",
        "gs.start": "GPU 노드 기동", "gs.start_sub": "과금 시작",
        "gs.err": "오류 발견", "gs.err_sub": "import 오류,", "gs.err_sub2": "설정 누락",
        "gs.fix": "고치기", "gs.rerun": "다시 실행",
        "gs.bill_a": "GPU 노드 과금: 고치고 다시 실행하는 동안에도 계속",
        "gs.local": "로컬 CPU에서 확인", "gs.local_sub": "pytest 105개,", "gs.local_sub2": "GRPO dry run 2 step",
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
        "bi.why": "1~4편: 그림과 예시", "bi.why_sub": "용어는 처음 나올 때", "bi.why_sub2": "한 줄로 풀이",
        "bi.how": "5편: 직접 해 보기", "bi.how_sub": "내 PC (무료),", "bi.how_sub2": "AWS (선택)",
        "bi.see": "채점 결과를 직접 확인",
        # docs/beginner/01_why_sandbox.md, 한 겹이 아니라 여러 겹
        "ly.title": "샌드박스의 여섯 층", "ly.head": "막는 위험",
        "ly.l1": "pod 보안 설정", "ly.l1s": "root가 아닌 사용자, 권한 제거",
        "ly.l2": "격리 런타임", "ly.l2s": "gVisor 또는 Kata",
        "ly.l3": "네트워크 규칙", "ly.l3s": "NetworkPolicy, 나가는 연결 기본 차단",
        "ly.l4": "노드 설정", "ly.l4s": "IMDSv2 필수, hop limit 1, node guard",
        "ly.l5": "자격 증명 없음", "ly.l5s": "AWS 키, 자체 서비스 계정 토큰 없음",
        "ly.l6": "자원과 시간 한도", "ly.l6s": "CPU, 메모리, 실행 시간",
        "ly.risks": [("서버 파일", "읽기"), ("자격 증명", "빼내기"), ("다른 곳으로", "퍼지기"), ("커널", "공격"),
                     ("자원", "독차지"), ("데이터", "빼돌리기")],
        "ly.note": "점은 그 층이 막는 위험입니다. 한 위험을 여러 층이 함께 막기도 합니다.",
        # docs/beginner/02_container_vs_sandbox.md, Pain point
        "b02.a": "일반 컨테이너: 함께 쓰는 서버 커널 하나",
        "b02.b": "샌드박스 런타임: 컨테이너와 커널 사이에 하나 더 두는 격리 계층",
        "b02.c": "컨테이너", "b02.cpod": "pod {}의 컨테이너", "b02.wall": "Sentry 또는 VM 커널", "b02.wall_sub": "pod마다 하나",
        "b02.kern_a": "서버 커널 하나", "b02.kern_b": "서버 커널",
        "b02.weak": "커널 취약점 하나",
        "b02.bad": "위험해질 수 있음", "b02.bad_sub": "A, B, C 모두", "b02.good": "추가 격리 계층", "b02.good_sub": "A, B, C 앞에",
        # docs/beginner/02_container_vs_sandbox.md, 세 가지 격리 방식
        "tw.runc": "runc (일반 컨테이너)", "tw.gvisor": "gVisor", "tw.kata": "Kata",
        "tw.pod": "pod", "tw.vm": "VM",
        "tw.code": "코드", "tw.sentry": "Sentry", "tw.vmk": "VM 안의 커널", "tw.per": "pod마다 하나",
        "tw.sys": "시스템 호출", "tw.few": "꼭 필요한 일부만", "tw.kvm": "KVM 경계",
        "tw.kern": "서버 커널",
        "tw.w1": "경계: namespace, cgroup", "tw.w2": "경계: 시스템 호출을 대신 처리하는 Sentry",
        "tw.w3": "경계: 하드웨어 가상화(KVM)",
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
        "gp.torch": "PyTorch 코드", "gp.cuda": "CUDA 라이브러리", "gp.drv": "NVIDIA 드라이버", "gp.drv_sub": "커널 안",
        "gp.gpu": "GPU", "gp.ioctl": "ioctl (장치 명령)",
        "gp.gv": "gVisor + nvproxy", "gp.gv_sub": "명령을 검사해 허용 목록만 전달하는 지점",
        "gp.kt": "Kata + VFIO passthrough", "gp.kt_sub": "코드부터 드라이버와 GPU까지 모두 pod의 VM 안에",
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
        "rl.task": "문제", "rl.task_sub": "PyTorch 연산을 더 빠른 GPU 커널로 다시 쓰기",
        "rl.model": "모델", "rl.model_sub": "GPU에서 학습",
        "rl.sb": "샌드박스", "rl.sb_sub": "코드 실행과 채점", "rl.sb_sub2": "속도 측정에 GPU 사용",
        "rl.score": "점수 (reward)", "rl.score_sub": "trainer가 계산",
        "rl.e1": ["문제를 보고 코드 작성"],
        "rl.e2": ["실행해 정확성과", "speedup 측정"],
        "rl.e3": ["점수가 높은 답을", "더 쓰도록 조정"],
        "rl.rep": "step마다 반복 (기본 60 step)",
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
        "gs.local": "Local CPU check", "gs.local_sub": "105 pytest tests,", "gs.local_sub2": "2-step GRPO dry run",
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
        "ly.title": "The six layers of a sandbox", "ly.head": "Risks blocked",
        "ly.l1": "pod security settings", "ly.l1s": "non-root user, dropped privileges",
        "ly.l2": "Isolation runtime", "ly.l2s": "gVisor or Kata",
        "ly.l3": "Network rules", "ly.l3s": "NetworkPolicy, default-deny outbound",
        "ly.l4": "Node settings", "ly.l4s": "IMDSv2 required, hop limit 1, node guard",
        "ly.l5": "No credentials", "ly.l5s": "no AWS keys or service account token",
        "ly.l6": "Resource and time limits", "ly.l6s": "CPU, memory, execution time",
        "ly.risks": [("Reading", "server files"), ("Stealing", "credentials"), ("Spreading", "elsewhere"),
                     ("Kernel", "attack"), ("Hogging", "resources"), ("Exfiltrating", "data")],
        "ly.note": "A dot marks a risk the layer blocks; some risks are blocked by several layers.",
        "b02.a": "Plain containers: one server kernel shared",
        "b02.b": "Sandbox runtimes: one more wall between container and kernel",
        "b02.c": "Container", "b02.cpod": "pod {} container", "b02.wall": "Sentry or VM kernel", "b02.wall_sub": "one per pod",
        "b02.kern_a": "One server kernel", "b02.kern_b": "Server kernel",
        "b02.weak": "one kernel weakness",
        "b02.bad": "May be at risk", "b02.bad_sub": "A, B and C", "b02.good": "One more wall", "b02.good_sub": "in front of A, B and C",
        "tw.runc": "runc (regular container)", "tw.gvisor": "gVisor", "tw.kata": "Kata",
        "tw.pod": "pod", "tw.vm": "VM",
        "tw.code": "Code", "tw.sentry": "Sentry", "tw.vmk": "Kernel inside the VM", "tw.per": "one per pod",
        "tw.sys": "system call", "tw.few": "only a necessary few", "tw.kvm": "KVM boundary",
        "tw.kern": "Server kernel",
        "tw.w1": "Wall: namespace, cgroup", "tw.w2": "Wall: Sentry handles system calls",
        "tw.w3": "Wall: hardware virtualization (KVM)",
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
        "gp.torch": "PyTorch code", "gp.cuda": "CUDA library", "gp.drv": "NVIDIA driver", "gp.drv_sub": "inside the kernel",
        "gp.gpu": "GPU", "gp.ioctl": "ioctl (order form)",
        "gp.gv": "gVisor + nvproxy", "gp.gv_sub": "checks commands here, passes only the allowlist",
        "gp.kt": "Kata + VFIO passthrough", "gp.kt_sub": "code, driver and GPU all go whole into the pod's VM",
        "b04.a": "A fooled grader and mixed standards",
        "b04.b": "Cheating blocked, one version per batch",
        "b04.hack": "Answer that fooled the grader", "b04.hack_sub": "raises the score through a gap",
        "b04.mix": "v1 and v2 in one group", "b04.mix_sub": "grading standards mixed",
        "b04.wrong": "Wrong score", "b04.learn_bad": "Model learns the wrong thing",
        "b04.guard": "Harness blocks cheating", "b04.guard_sub": "separate processes, new inputs",
        "b04.pin": "One version per batch", "b04.pin_sub": "never mixed in a batch",
        "b04.right": "Consistent score", "b04.right_sub": "one grading standard",
        "b04.learn_good": "Model improves from the score",
        "rl.task": "Problem", "rl.task_sub": "rewrite a PyTorch op as a faster GPU kernel",
        "rl.model": "Model", "rl.model_sub": "trained on GPU",
        "rl.sb": "Sandbox", "rl.sb_sub": "exam room and grader", "rl.sb_sub2": "a GPU to measure speed",
        "rl.score": "Score (reward)", "rl.score_sub": "computed by the trainer",
        "rl.e1": ["Reads the problem and writes code"],
        "rl.e2": ["Runs it and", "measures", "correctness,", "speedup"],
        "rl.e3": ["Adjusts to write", "more high-scoring", "answers"],
        "rl.rep": "repeats every step (60 by default)",
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
    """docs/getting_started.md: errors found after GPU nodes start keep billing; local CPU check first (Why)."""
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
    """docs/beginner/01_why_sandbox.md "여러 층의 방어": the six layers of the layer table as rows and the six
    risks of the risk table as columns; a dot where the risk table names the layer as a blocking setting."""
    t = T[lang]
    fig = Figure(760, 428)
    bx, bw = 16, 728
    cx0, cwid = 312, 72
    fig.text(bx, 24, t["ly.title"], size=14, bold=True, anchor="start")
    fig.text(cx0 + 3 * cwid, 24, t["ly.head"], size=SMALL, bold=True)
    for j, (h1, h2) in enumerate(t["ly.risks"]):
        hx = cx0 + cwid * (j + 0.5)
        fig.text(hx, 48, h1, size=SMALL)
        fig.text(hx, 63, h2, size=SMALL)
        for h in (h1, h2):
            _fits(h, SMALL, cwid + 4, f"risk header {j}")
    # Rows of the layer table; columns in the order of the risk table.
    blocks = ({0}, {0, 3}, {1, 2, 5}, {1}, {2}, {4})
    y0, bh, step = 76, 46, 52
    for i in range(6):
        y = y0 + i * step
        n = i + 1
        fig.rect(bx, y, bw, bh, fill="#FFFFFF", stroke=ACCENT, gid=f"n:layer{n}")
        cxn = bx + 22
        fig.parts.append(f'<circle cx="{cxn}" cy="{y + bh / 2}" r="10" fill="{ACCENT_FILL}" stroke="{ACCENT}" '
                         f'stroke-width="1.2"/>')
        fig.text(cxn, y + bh / 2 + 4.2, str(n), size=SMALL)
        fig.text(cxn + 22, y + 19, t[f"ly.l{n}"], anchor="start")
        fig.text(cxn + 22, y + 36, t[f"ly.l{n}s"], size=SMALL, anchor="start")
        _fits(t[f"ly.l{n}"], SIZE, cx0 - cxn - 22, f"layer {n}")
        _fits(t[f"ly.l{n}s"], SMALL, cx0 - cxn - 22, f"layer {n}")
        for j in range(6):
            dx = cx0 + cwid * (j + 0.5)
            if j in blocks[i]:
                fig.parts.append(f'<circle cx="{dx}" cy="{y + bh / 2}" r="7" fill="{ACCENT}"/>')
            else:
                fig.parts.append(f'<circle cx="{dx}" cy="{y + bh / 2}" r="2" fill="{CONTAINER}"/>')
    fig.text(bx, y0 + 6 * step + 16, t["ly.note"], size=SMALL, anchor="start")
    _fits(t["ly.note"], SMALL, bw, "layers note")
    return fig


def beginner_02_three_walls(lang: str) -> Figure:
    """docs/beginner/02_container_vs_sandbox.md "세 가지 격리 방식": runc, gVisor and Kata as identical panels."""
    t = T[lang]
    fig = Figure(760, 384)
    pw = 232
    panels = (("a", t["tw.runc"], t["tw.pod"], None, None, t["tw.w1"]),
              ("b", t["tw.gvisor"], t["tw.pod"], t["tw.sentry"], t["tw.few"], t["tw.w2"]),
              ("c", t["tw.kata"], t["tw.vm"], t["tw.vmk"], t["tw.kvm"], t["tw.w3"]))
    for i, (letter, title, holder, wall, edge, note) in enumerate(panels):
        x0 = 16 + i * (pw + 16)
        fig.panel(x0, 26, letter, title)
        bx, bw = x0 + 16, pw - 32
        ax = bx + bw * 0.3
        lx = ax + 10
        kata = letter == "c"
        hold_h = 92 if wall is None else 192
        fig.container(x0, 46, pw, hold_h, holder, stroke=ACCENT if kata else CONTAINER,
                      color=ACCENT if kata else INK, bold=kata)
        fig.box(bx, 76, bw, 44, t["tw.code"], icon="code", gid=f"n:code-{letter}")
        if wall is None:
            fig.arrow([(ax, 120), (ax, 288)])
            fig.text(lx, 214, t["tw.sys"], size=SMALL, anchor="start")
        else:
            fig.arrow([(ax, 120), (ax, 166)])
            fig.text(lx, 148, t["tw.sys"], size=SMALL, anchor="start")
            fig.box(bx, 168, bw, 54, wall, t["tw.per"], fill=ACCENT_FILL, stroke=ACCENT, gid=f"n:wall-{letter}")
            fig.arrow([(ax, 222), (ax, 288)])
            fig.text(lx, 268, edge, size=SMALL, anchor="start")
            _fits(edge, SMALL, x0 + pw - lx + 16, f"edge {letter}")
        fig.box(bx, 290, bw, 44, t["tw.kern"], icon="server", gid=f"n:kernel-{letter}")
        fig.text(x0 + pw / 2, 362, note, size=SMALL)
        _fits(note, SMALL, pw + 12, f"note {letter}")
    return fig


def beginner_03_gpu_path(lang: str) -> Figure:
    """docs/beginner/03_gpu_sandbox.md "GPU 접근 경로": the path to the GPU and where each runtime puts its isolation boundary
    (the two approaches from the next section)."""
    t = T[lang]
    fig = Figure(760, 268)
    top, h = 74, 96
    boxes = ((16, 128, t["gp.torch"], (), "code", "n:torch"),
             (184, 140, t["gp.cuda"], (), "package", "n:cuda"),
             (494, 160, t["gp.drv"], (t["gp.drv_sub"],), "gear", "n:driver"),
             (690, 54, t["gp.gpu"], (), "cpu", "n:gpu"))
    for x, w, label, subs, icon, gid in boxes:
        vbox(fig, x, top, w, h, label, subs, icon=icon, gid=gid)
    mid = top + h / 2
    for (x, w, *_), (nx, *_) in zip(boxes, boxes[1:]):
        fig.arrow([(x + w, mid), (nx - 2, mid)], width=2.0)
    fig.text((184 + 140 + 456) / 2, mid - 8, t["gp.ioctl"], size=SMALL)
    # gVisor: a wall across the ioctl edge.
    wx = 456
    fig.line([(wx, top - 14), (wx, top + h + 14)], color=ACCENT, width=3.2)
    fig.text(wx, 28, t["gp.gv"], color=ACCENT, bold=True)
    fig.text(wx, 46, t["gp.gv_sub"], size=SMALL)
    # Kata: the whole path inside the pod's VM.
    yb = top + h + 30
    fig.line([(16, yb - 8), (16, yb), (744, yb), (744, yb - 8)], color=ACCENT, width=2.0)
    fig.text(380, yb + 24, t["gp.kt"], color=ACCENT, bold=True)
    fig.text(380, yb + 42, t["gp.kt_sub"], size=SMALL)
    return fig


def beginner_04_rl_loop(lang: str) -> Figure:
    """docs/beginner/04_rl_and_sandbox.md "학습 루프에서 샌드박스의 자리": model, sandbox, score as a loop."""
    t = T[lang]
    fig = Figure(760, 404)
    mx, sx, w = 24, 516, 220
    top, h = 104, 104
    fig.box(mx, 16, 300, 50, t["rl.task"], t["rl.task_sub"], gid="n:task")
    fig.arrow([(mx + w / 2, 66), (mx + w / 2, top - 2)])
    vbox(fig, mx, top, w, h, t["rl.model"], t["rl.model_sub"], icon="hubot", gid="n:model")
    vbox(fig, sx, top, w, h, t["rl.sb"], (t["rl.sb_sub"], t["rl.sb_sub2"]), icon="shield-lock", fill=ACCENT_FILL,
         stroke=ACCENT, gid="n:sandbox")
    rx, ry, rw, rh = 270, 300, 220, 84
    vbox(fig, rx, ry, rw, rh, t["rl.score"], t["rl.score_sub"], icon="graph", gid="n:score")
    my = top + h / 2
    ry_mid = ry + rh / 2
    # 1: model -> sandbox, 2: sandbox -> score, 3: score -> model.
    fig.arrow([(mx + w, my), (sx - 2, my)], width=2.0)
    e1 = t["rl.e1"]
    e1w = text_width(e1[0], SMALL) + 23
    edge_label(fig, (mx + w + sx) / 2 - e1w / 2, my - 10, e1, step=1)
    scx = sx + w / 2
    fig.arrow([(scx, top + h), (scx, ry_mid), (rx + rw + 2, ry_mid)], width=2.0)
    edge_label(fig, scx + 12, top + h + 34, t["rl.e2"], step=2)
    mcx = mx + w / 2
    fig.arrow([(rx, ry_mid), (mcx, ry_mid), (mcx, top + h + 2)], width=2.0)
    edge_label(fig, mcx - 12, top + h + 34, t["rl.e3"], anchor="end", step=3)
    cx = (mx + w + sx) / 2
    fig.icon("sync", cx - 13, my + 44, 26)
    fig.text(cx, my + 92, t["rl.rep"], size=SMALL)
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
