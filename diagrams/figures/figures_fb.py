"""Concept page schematics (docs/concepts/01 to 06): Pain point figures and main figures.

Every box and edge comes from the page named in each docstring. Shared geometry draws both languages.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from figlib import (ACCENT, ACCENT_FILL, GREY_FILL, INK, MUTED_STROKE, RED, RED_FILL, SIZE, SMALL, Figure,
                    text_width)

WHITE = "#FFFFFF"
PITCH = 17  # baseline distance between lines inside a box


def mbox(fig: Figure, x, y, w, h, lines, *, icon=None, fill=GREY_FILL, stroke=MUTED_STROKE, color=INK, dash=None,
         sw=1.2, gid=None):
    """A box with one 13 px name line and any number of 12 px lines, centred as one block."""
    fig.rect(x, y, w, h, fill=fill, stroke=stroke, width=sw, dash=dash, gid=gid)
    sizes = [SIZE] + [SMALL] * (len(lines) - 1)
    block = max(text_width(s, z) for s, z in zip(lines, sizes))
    tx, avail = x + w / 2, w
    if icon:
        start = x + (w - (20 + 10 + block)) / 2
        assert start - x >= 12, f"no room for icon padding in box {gid or lines[0]!r}: {start - x:.0f}px"
        fig.icon(icon, start, y + h / 2 - 10, 20, color)
        tx, avail = start + 30 + block / 2, w - 30
    first = y + h / 2 - (len(lines) - 1) * PITCH / 2 + SIZE * 0.36
    for i, (s, z) in enumerate(zip(lines, sizes)):
        fig.text(tx, first + i * PITCH, s, size=z, color=color)
    assert block + 16 <= avail, f"label too wide for box {gid or lines[0]!r}: {block + 16:.0f} > {avail:.0f}"
    need_h = (len(lines) - 1) * PITCH + 26
    assert need_h <= h, f"box {gid or lines[0]!r} too short: {need_h} > {h}"


def side_label(fig: Figure, x, y, s, color=INK):
    """Edge label to the right of a vertical connector."""
    fig.text(x + 6, y, s, size=SMALL, color=color, anchor="start")


T = {
    "ko": {
        # 01 two-tier
        "tt.trainer": "trainer 프로세스 (CPU)",
        "tt.comp": "completion",
        "tt.kr": ["KernelRewards", "코드 블록 추출, AST 정책", "(check_source)"],
        "tt.rej": ["no_code 또는", "policy_violation", "샌드박스 호출 없음"],
        "tt.cpu": ["CPU 계층 (선택)", "GPU 앞 단계로 자동 연결 안 됨", "Kata + CLH on c8i"],
        "tt.gpu": ["GPU 계층", "정확성 + timing", "gVisor 또는 Kata + QEMU"],
        "tt.verdict": "verdict",
        "tt.no": "코드 블록 없음 또는 정책 위반", "tt.yes": "통과",
        # 01 rl-loop
        "rl.data": ["데이터셋", "과제 prompt"],
        "rl.gen": ["vLLM 생성", "prompt마다 completion 8개"],
        "rl.ast": ["코드 추출, AST 정책 검사", "trainer, CPU"],
        "rl.pod": "샌드박스 pod (GPU 1개)",
        "rl.child": ["untrusted child", "후보 실행"],
        "rl.parent": ["trusted parent", "reference, timing, verdict"],
        "rl.out": "출력",
        "rl.reward": ["reward 3요소", "format, correctness, speedup"],
        "rl.grpo": ["GRPO", "group 기준 advantage"],
        "rl.lora": ["LoRA 업데이트", "optimizer step 1회"],
        "rl.sync": "가중치 동기화",
        # 02 gpu-paths
        "gp.title": "샌드박스에서 GPU에 접근하는 두 가지 방식",
        "gp.desc": "gVisor의 nvproxy는 노드의 NVIDIA 드라이버에 요청을 전달합니다. Kata VM 안의 NVIDIA 드라이버는 그 VM에 할당된 GPU를 제어합니다.",
        "gp.sandboxes": ("gVisor 샌드박스", "Kata 샌드박스 VM"),
        "gp.code": "제출 코드와 CUDA 라이브러리",
        "gp.proxy": "Sentry의 nvproxy", "gp.filter": "지원하는 장치 제어 요청만 전달",
        "gp.host_driver": "노드의 NVIDIA 드라이버", "gp.guest_driver": "VM의 NVIDIA 드라이버",
        "gp.guest_kernel": "게스트 Linux 커널에서 실행", "gp.assigned": "VFIO로 이 VM에 직접 할당",
        "pt.title": "물리 GPU 한 장을 Kata VM에 할당하는 과정",
        "pt.desc": "GPU는 서버의 PCIe 슬롯에 남습니다. QEMU가 VFIO로 GPU를 할당하면 VM의 NVIDIA 드라이버가 이 GPU를 제어합니다. GPU의 시스템 RAM 접근은 IOMMU가 허용한 범위로 제한됩니다.",
        "pt.host": "물리 서버", "pt.setup": "GPU를 VM에 할당할 때", "pt.run": "VM이 실행 중일 때",
        "pt.bind": "호스트 Linux", "pt.bind_sub": "GPU에 vfio-pci 드라이버 연결",
        "pt.assign": "QEMU", "pt.assign_sub": "VFIO로 GPU를 VM의 PCI 장치로 연결",
        "pt.vm": "Kata VM", "pt.app": "PyTorch와 CUDA", "pt.driver": "VM의 NVIDIA 드라이버",
        "pt.driver_sub": "할당된 GPU를 PCI 장치로 인식", "pt.command": "연산 명령",
        "pt.gpu": "물리 GPU", "pt.vram": "GPU 칩과 전용 메모리(VRAM)", "pt.slot": "서버의 PCIe 슬롯",
        "pt.dma": "시스템 RAM에 DMA 요청", "pt.iommu": "DMA 주소 변환과 권한 확인",
        "pt.allow": "접근 허용", "pt.deny": "접근 차단",
        "pt.mapped": "이 GPU에 매핑된 VM 메모리", "pt.other": "다른 VM이나 호스트 전용 메모리",
        "vmm.title": "게스트 명령 실행과 가상 디스크 구성",
        "vmm.desc": "QEMU는 하드웨어 가상화와 명령어 번역을 지원하고, Cloud Hypervisor는 하드웨어 가상화를 이용합니다. 같은 디스크 이미지를 QEMU는 IDE나 virtio-blk로, Cloud Hypervisor는 virtio-blk로 제공합니다.",
        "vmm.qemu": "다양한 컴퓨터와 장치를 재현", "vmm.clh": "최신 클라우드 게스트에 맞춘 VMM",
        "vmm.qemu_exec": "하드웨어 가상화 또는 명령어 번역", "vmm.clh_exec": "하드웨어 가상화로 게스트 명령 실행",
        "vmm.ide": "IDE 컨트롤러", "vmm.ide_request": "IDE 드라이버가 레지스터에 명령 기록",
        "vmm.virtio": "virtio-blk 디스크", "vmm.virtio_request": "virtio 드라이버가 공유 큐에 요청 등록",
        "vmm.disk": "호스트의 디스크 이미지", "vmm.read": "요청한 블록의 데이터를 읽음",
        # 03 version-swap
        "vs.ops": "운영자: scripts/ops/rollout.sh",
        "vs.steps": [["1. v2 배포", "트래픽 없음"], ["2. v2 검증", "격리 증거,", "golden verdict"],
                     ["3. parity", "v1과 v2의 golden", "결과 일치"], ["4. routing 전환", "다음 reward batch", "부터 v2"],
                     ["5. --finish", "v1을 0으로 축소", "롤백용으로 보존"]],
        "vs.fail": ["v1 유지", "v2에는 트래픽 없음"],
        "vs.fail_l": "실패", "vs.pass_l": "통과",
        "vs.trainer": "trainer: 샌드박스 호출마다 routing snapshot, batch마다 한 버전",
        "vs.sync": "약 1분 안에 반영",
        "vs.inflight": "첫 전환: v1에 보낸 batch는 v1에서 마무리",
        "vs.event": "sandbox_version_switch 기록",
        "vs.time": "시간 (학습은 계속 진행)",
        # 04 worker placement
        "p4.b1": "B1  학습 워커만 HyperPod에 배치", "p4.b2": "B2  모든 워커를 HyperPod에 배치",
        "p4.title": "B1과 B2의 워커 배치", "p4.desc": "B1은 시스템과 채점 워커를 EC2에 두고, B2는 세 역할을 모두 HyperPod에 둡니다.",
        "p4.roles": ("학습 GPU", "시스템 CPU", "gVisor 채점 GPU"),
        # 05 platform and runtime choices
        "p5.title": "GPU 실습의 플랫폼과 채점 런타임",
        "p5.desc": "A와 B1의 EC2 채점 노드는 gVisor 또는 Kata + QEMU를 사용합니다. B2의 HyperPod 채점 워커는 gVisor를 사용합니다.",
        "p5.platforms": (("A  EC2 자체 운영", "EC2에서 학습"), ("B1  혼합형", "HyperPod에서 학습"),
                         ("B2  HyperPod 관리형", "HyperPod에서 학습")),
        "p5.ec2": "EC2에서 GPU 채점", "p5.hp": "HyperPod에서 GPU 채점",
        "p5.gvisor": "기본 (A10G)", "p5.kata": "선택 (T4)",
        # 06 pain
        "p6.a": "reward pool: turn마다 다른 pod와 GPU",
        "p6.b": "Agent Sandbox: 에피소드 하나가 끝까지 쓰는 샌드박스 하나",
        "p6.ep": ["에피소드 하나"],
        "p6.t1": ["turn 1 제출"], "p6.t2": ["turn 2 수정 제출"],
        "p6.pa": ["pod A, GPU 1", "요청 후 작업 디렉터리, 프로세스 정리"],
        "p6.pb": ["pod B, GPU 2", "요청 후 작업 디렉터리, 프로세스 정리"],
        "p6.fresh": "에피소드마다 새로 생성하면",
        "p6.kata": ["Kata GPU VM", "첫 Ready까지 몇 분"],
        "p6.claimed": ["claim한 샌드박스 하나", "같은 pod와 GPU", "파일은 제출마다 삭제", "격리는 RuntimeClass (gVisor, Kata)"],
        "p6.claim": "SandboxClaim 생성",
        "p6.pool": ["SandboxWarmPool", "미리 기동, egress 차단 확인 뒤 Ready"],
        "p6.hand": "대기 중인 Sandbox 전달",
    },
    "en": {
        "tt.trainer": "trainer process (CPU)",
        "tt.comp": "completion",
        "tt.kr": ["KernelRewards", "code block extraction,", "AST policy (check_source)"],
        "tt.rej": ["no_code or", "policy_violation", "no sandbox call"],
        "tt.cpu": ["CPU tier (optional)", "not wired in front of the GPU", "Kata + CLH on c8i"],
        "tt.gpu": ["GPU tier", "correctness + timing", "gVisor or Kata + QEMU"],
        "tt.verdict": "verdict",
        "tt.no": "no code block, or a policy violation", "tt.yes": "passes",
        "rl.data": ["dataset", "task prompts"],
        "rl.gen": ["vLLM generation", "8 completions per prompt"],
        "rl.ast": ["code extraction, AST policy", "trainer, CPU"],
        "rl.pod": "sandbox pod (1 GPU)",
        "rl.child": ["untrusted child", "runs the candidate"],
        "rl.parent": ["trusted parent", "reference, timing, verdict"],
        "rl.out": "outputs",
        "rl.reward": ["three-part reward", "format, correctness, speedup"],
        "rl.grpo": ["GRPO", "group-relative advantage"],
        "rl.lora": ["LoRA update", "one optimizer step"],
        "rl.sync": "weight sync",
        "gp.title": "Two paths from a sandbox to a GPU",
        "gp.desc": "gVisor’s nvproxy forwards requests to the node’s NVIDIA driver. The driver inside a Kata VM controls the GPU assigned to that VM.",
        "gp.sandboxes": ("gVisor sandbox", "Kata sandbox VM"),
        "gp.code": "Code and CUDA libraries",
        "gp.proxy": "nvproxy in the Sentry", "gp.filter": "Forwards supported device requests",
        "gp.host_driver": "Node’s NVIDIA driver", "gp.guest_driver": "VM’s NVIDIA driver",
        "gp.guest_kernel": "Runs in the guest Linux kernel", "gp.assigned": "Assigned to this VM through VFIO",
        "pt.title": "Assigning one physical GPU to a Kata VM",
        "pt.desc": "The GPU stays in the server’s PCIe slot. QEMU assigns it through VFIO, and the guest NVIDIA driver controls it. The IOMMU restricts the GPU’s access to system RAM.",
        "pt.host": "Physical server", "pt.setup": "Assigning the GPU to the VM", "pt.run": "While the VM runs",
        "pt.bind": "Host Linux", "pt.bind_sub": "Binds the GPU to the vfio-pci driver",
        "pt.assign": "QEMU", "pt.assign_sub": "Assigns the GPU as a guest PCI device via VFIO",
        "pt.vm": "Kata VM", "pt.app": "PyTorch and CUDA", "pt.driver": "Guest NVIDIA driver",
        "pt.driver_sub": "Sees the GPU as a PCI device", "pt.command": "GPU commands",
        "pt.gpu": "Physical GPU", "pt.vram": "GPU chip and memory (VRAM)", "pt.slot": "Server PCIe slot",
        "pt.dma": "DMA request to system RAM", "pt.iommu": "DMA translation and access checks",
        "pt.allow": "Access allowed", "pt.deny": "Access denied",
        "pt.mapped": "VM memory mapped for this GPU", "pt.other": "Host-only memory or other VMs’ RAM",
        "vmm.title": "Guest execution and virtual disk interfaces",
        "vmm.desc": "QEMU supports hardware virtualization and instruction translation. Cloud Hypervisor uses hardware virtualization. QEMU offers IDE and virtio-blk disks, and Cloud Hypervisor offers virtio-blk.",
        "vmm.qemu": "Models many machines and devices", "vmm.clh": "VMM for modern cloud guests",
        "vmm.qemu_exec": "Hardware virtualization or translation", "vmm.clh_exec": "Guest runs with hardware virtualization",
        "vmm.ide": "IDE controller", "vmm.ide_request": "IDE driver writes a command to a register",
        "vmm.virtio": "virtio-blk disk", "vmm.virtio_request": "Virtio driver puts a request in a shared queue",
        "vmm.disk": "Disk image on the host", "vmm.read": "Read the data for the requested block",
        "vs.ops": "operator: scripts/ops/rollout.sh",
        "vs.steps": [["1. deploy v2", "no traffic"], ["2. verify v2", "isolation evidence,", "golden verdicts"],
                     ["3. parity", "golden results of", "v1 and v2 match"], ["4. switch routing", "v2 from the next", "reward batch"],
                     ["5. --finish", "scale v1 to 0", "kept for rollback"]],
        "vs.fail": ["keep v1", "v2 gets no traffic"],
        "vs.fail_l": "fail", "vs.pass_l": "pass",
        "vs.trainer": "trainer: a routing snapshot per sandbox call, one version per batch",
        "vs.sync": "reaches pods within about a minute",
        "vs.inflight": "first switch: a batch sent to v1 ends on v1",
        "vs.event": "logs sandbox_version_switch",
        "vs.time": "time (training does not stop)",
        "p4.b1": "B1  HyperPod for training", "p4.b2": "B2  HyperPod for all workers",
        "p4.title": "Worker placement in B1 and B2", "p4.desc": "B1 keeps system and grading workers on EC2. B2 runs all three roles on HyperPod.",
        "p4.roles": ("Training GPU", "System CPU", "gVisor grading GPUs"),
        "p5.title": "Choose a platform and a GPU grading runtime",
        "p5.desc": "A and B1 grade on EC2 with gVisor or Kata + QEMU. B2 grades on HyperPod with gVisor.",
        "p5.platforms": (("A  Self-managed EC2", "Train on EC2"), ("B1  Hybrid", "Train on HyperPod"),
                         ("B2  Managed HyperPod", "Train on HyperPod")),
        "p5.ec2": "Grade on EC2", "p5.hp": "Grade on HyperPod",
        "p5.gvisor": "Default (A10G)", "p5.kata": "Optional (T4)",
        "p6.a": "Reward pools: each turn on another pod and GPU",
        "p6.b": "Agent Sandbox: one episode keeps one sandbox to the end",
        "p6.ep": ["one episode"],
        "p6.t1": ["turn 1 submission"], "p6.t2": ["turn 2 revised submission"],
        "p6.pa": ["pod A, GPU 1", "work dir, processes cleared per request"],
        "p6.pb": ["pod B, GPU 2", "work dir, processes cleared per request"],
        "p6.fresh": "fresh start per episode",
        "p6.kata": ["Kata GPU VM", "minutes to first Ready"],
        "p6.claimed": ["one claimed sandbox", "same pod and GPU", "files removed per submission", "isolation from the RuntimeClass"],
        "p6.claim": "create a SandboxClaim",
        "p6.pool": ["SandboxWarmPool", "started ahead, Ready after egress check"],
        "p6.hand": "hands over a waiting Sandbox",
    },
}


def concepts_01_two_tier(lang: str) -> Figure:
    """docs/concepts/01_why_gpu_sandbox "두 계층 패턴": trainer pre-check, then the GPU tier and its verdict. The
    optional CPU tier stands apart: no pipeline forwards work from it to the GPU tier (적용 범위와 한계)."""
    t = T[lang]
    fig = Figure(760, 252)
    # Top row: completion | KernelRewards | reject. Bottom row: CPU tier (apart) | GPU tier | verdict
    ax, aw, bx, bw, dx, dw = 28, 104, 166, 196, 606, 128
    cx, cw, gx, gw = 28, 200, 250, 196
    fig.container(16, 16, 730, 112, t["tt.trainer"], icon="cpu")
    r1 = 82
    mbox(fig, ax, r1 - 20, aw, 40, [t["tt.comp"]], gid="n:completion")
    mbox(fig, bx, r1 - 30, bw, 60, t["tt.kr"], gid="n:kernelrewards")
    mbox(fig, dx, r1 - 30, dw, 60, t["tt.rej"], gid="n:reject")
    fig.arrow([(ax + aw, r1), (bx - 2, r1)])
    fig.arrow([(bx + bw, r1), (dx - 2, r1)], label=t["tt.no"], label_at=((bx + bw + dx) / 2, r1 - 8))
    r2 = 206
    mbox(fig, cx, r2 - 32, cw, 64, t["tt.cpu"], dash="5 4", gid="n:cpu-tier")
    mbox(fig, gx, r2 - 32, gw, 64, t["tt.gpu"], fill=ACCENT_FILL, stroke=ACCENT, gid="n:gpu-tier")
    mbox(fig, dx, r2 - 20, dw, 40, [t["tt.verdict"]], icon="check-circle", gid="n:verdict")
    px = 300
    fig.arrow([(px, r1 + 30), (px, r2 - 34)])
    side_label(fig, px, (r1 + 30 + r2 - 34) / 2 + 4, t["tt.yes"])
    fig.arrow([(gx + gw, r2), (dx - 2, r2)])
    fig.arrow([(dx + dw / 2, r1 + 30), (dx + dw / 2, r2 - 22)])
    return fig


def concepts_01_rl_loop(lang: str) -> Figure:
    """docs/concepts/01_why_gpu_sandbox "RL 루프": generation, CPU checks, sandbox scoring, reward, GRPO, LoRA, sync."""
    t = T[lang]
    fig = Figure(760, 314)
    # Columns: dataset | generation, LoRA | AST check, GRPO | sandbox pod, reward
    x0, w0, x1, w1, x2, w2, x3, w3 = 16, 104, 146, 176, 352, 176, 556, 188
    r1 = 98
    mbox(fig, x0, r1 - 24, w0, 48, t["rl.data"], gid="n:dataset")
    mbox(fig, x1, r1 - 24, w1, 48, t["rl.gen"], gid="n:generation")
    mbox(fig, x2, r1 - 24, w2, 48, t["rl.ast"], gid="n:ast-check")
    # Sandbox pod: the untrusted child runs the candidate, the trusted parent judges it
    fig.container(x3, 16, w3, 184, t["rl.pod"], icon="shield-lock", stroke=ACCENT, color=ACCENT, bold=True)
    ix, iw = x3 + 14, w3 - 28
    mbox(fig, ix, 46, iw, 46, t["rl.child"], gid="n:child")
    mbox(fig, ix, 136, iw, 46, t["rl.parent"], fill=ACCENT_FILL, stroke=ACCENT, gid="n:parent")
    fig.arrow([(ix + iw / 2, 92), (ix + iw / 2, 134)])
    side_label(fig, ix + iw / 2, 118, t["rl.out"])
    fig.arrow([(x0 + w0, r1), (x1 - 2, r1)])
    fig.arrow([(x1 + w1, r1), (x2 - 2, r1)])
    fig.arrow([(x2 + w2, r1), (x3 - 2, r1)])
    r2 = 274
    mbox(fig, x3, r2 - 24, w3, 48, t["rl.reward"], gid="n:reward")
    mbox(fig, x2, r2 - 24, w2, 48, t["rl.grpo"], gid="n:grpo")
    mbox(fig, x1, r2 - 24, w1, 48, t["rl.lora"], gid="n:lora")
    fig.arrow([(ix + iw / 2, 182), (ix + iw / 2, r2 - 26)])
    fig.arrow([(x3, r2), (x2 + w2 + 2, r2)])
    fig.arrow([(x2, r2), (x1 + w1 + 2, r2)])
    # Feedback: the updated weights go back to the generator
    fig.arrow([(x1 + w1 / 2, r2 - 24), (x1 + w1 / 2, r1 + 26)], dash="5 4")
    side_label(fig, x1 + w1 / 2, (r1 + r2) / 2 + 4, t["rl.sync"])
    return fig


def concepts_02_gpu_paths(lang: str) -> Figure:
    """Place each NVIDIA driver on the side of the sandbox boundary where it runs."""
    t = T[lang]
    fig = Figure(638, 352)
    fig.parts.append(f'<title>{escape(t["gp.title"])}</title><desc>{escape(t["gp.desc"])}</desc>')
    panels = zip((8, 326), ("gVisor", "Kata + QEMU"), ("g5.xlarge", "g4dn.metal"), t["gp.sandboxes"], strict=True)
    for x, runtime, instance, sandbox in panels:
        center = x + 152
        fig.text(x + 4, 24, runtime, size=20, bold=True, anchor="start")
        fig.container(x, 36, 304, 308, instance, icon="server", bold=True)
        fig.container(x + 12, 66, 280, 142, sandbox, icon="shield-lock", stroke=ACCENT, color=ACCENT, bold=True)
        fig.box(x + 24, 96, 256, 36, t["gp.code"], icon="code", fill=WHITE)
        fig.arrow([(center, 132), (center, 148)])
        if runtime == "gVisor":
            fig.box(x + 24, 150, 256, 46, t["gp.proxy"], t["gp.filter"], fill=ACCENT_FILL, stroke=ACCENT)
            fig.arrow([(center, 196), (center, 230)])
            fig.box(x + 24, 232, 256, 36, t["gp.host_driver"], icon="gear")
            fig.arrow([(center, 268), (center, 286)])
            fig.box(x + 24, 288, 256, 44, "NVIDIA A10G", icon="cpu")
        else:
            fig.box(x + 24, 150, 256, 46, t["gp.guest_driver"], t["gp.guest_kernel"], icon="gear",
                    fill=ACCENT_FILL, stroke=ACCENT)
            fig.arrow([(center, 196), (center, 286)])
            fig.box(x + 24, 288, 256, 44, "NVIDIA T4", t["gp.assigned"], icon="cpu")
    return fig


def concepts_02_gpu_passthrough(lang: str) -> Figure:
    """Separate PCI device assignment, guest commands and the GPU's DMA requests."""
    t = T[lang]
    fig = Figure(656, 495)
    fig.parts.append(f'<title>{escape(t["pt.title"])}</title><desc>{escape(t["pt.desc"])}</desc>')
    fig.container(6, 6, 644, 483, t["pt.host"], icon="server", bold=True)
    fig.text(20, 55, t["pt.setup"], size=17, bold=True, anchor="start")
    fig.box(20, 68, 247, 48, t["pt.bind"], t["pt.bind_sub"], icon="plug")
    fig.arrow([(267, 92), (307, 92)])
    fig.box(309, 68, 325, 48, t["pt.assign"], t["pt.assign_sub"], icon="gear")

    fig.line([(20, 132), (634, 132)], color=MUTED_STROKE, width=1)
    fig.text(20, 157, t["pt.run"], size=17, bold=True, anchor="start")
    fig.container(20, 169, 246, 143, t["pt.vm"], icon="shield-lock", stroke=ACCENT, color=ACCENT, bold=True)
    fig.box(31, 199, 224, 34, t["pt.app"], icon="code", fill=WHITE)
    fig.arrow([(143, 233), (143, 247)], color=ACCENT)
    fig.box(31, 249, 224, 51, t["pt.driver"], t["pt.driver_sub"], fill=ACCENT_FILL, stroke=ACCENT)

    # The card appears once, outside the VM but inside the physical server.
    fig.arrow([(255, 274), (383, 274)], color=ACCENT, width=2)
    fig.text(324, 263, t["pt.command"], size=13, color=ACCENT)
    fig.text(388, 218, t["pt.slot"], size=14, bold=True, anchor="start")
    fig.rect(385, 228, 249, 65, fill=ACCENT_FILL, stroke=ACCENT)
    fig.icon("cpu", 395, 245, 30, ACCENT)
    fig.text(435, 254, t["pt.gpu"], size=17, bold=True, anchor="start")
    fig.text(435, 275, t["pt.vram"], size=12, anchor="start")
    for x, width in ((401, 20), (426, 51)):
        fig.rect(x, 293, width, 5, fill=ACCENT, stroke=ACCENT, rx=0)

    fig.arrow([(519, 293), (519, 322), (328, 322), (328, 338)])
    fig.text(418, 315, t["pt.dma"], size=13)
    fig.box(195, 340, 266, 46, "IOMMU", t["pt.iommu"], icon="shield-lock")
    fig.line([(328, 386), (328, 399)])
    fig.arrow([(328, 399), (168, 399), (168, 431)], color=ACCENT)
    fig.text(175, 422, t["pt.allow"], size=13, color=ACCENT, anchor="start")
    fig.line([(328, 399), (488, 399), (488, 426)], color=RED, dash="4 3")
    fig.line([(481, 426), (495, 426)], color=RED, width=2)
    fig.text(497, 422, t["pt.deny"], size=13, color=RED, anchor="start")
    fig.box(27, 433, 282, 39, t["pt.mapped"], fill=ACCENT_FILL, stroke=ACCENT)
    fig.box(347, 433, 282, 39, t["pt.other"])
    return fig


def concepts_02_kata_hypervisors(lang: str) -> Figure:
    """Compare guest-visible disk interfaces backed by the same disk image."""
    t = T[lang]
    fig = Figure(600, 304)
    fig.parts.append(f'<title>{escape(t["vmm.title"])}</title><desc>{escape(t["vmm.desc"])}</desc>')
    fig.text(300, 23, t["vmm.title"], size=18, bold=True)
    for left, name, scope, execution in (
        (10, "QEMU", t["vmm.qemu"], t["vmm.qemu_exec"]),
        (310, "Cloud Hypervisor", t["vmm.clh"], t["vmm.clh_exec"]),
    ):
        fig.rect(left, 40, 280, 82, fill=WHITE, stroke=MUTED_STROKE)
        fig.text(left + 140, 64, name, size=17, bold=True)
        fig.text(left + 140, 85, scope, size=13)
        fig.text(left + 140, 109, execution, size=12, bold=True)

    # QEMU offers either interface. Both VMMs implement the virtio path.
    fig.arrow([(150, 122), (150, 167)])
    fig.arrow([(222, 122), (222, 145), (379, 145), (379, 167)], color=ACCENT)
    fig.arrow([(450, 122), (450, 167)], color=ACCENT)
    fig.box(10, 169, 280, 51, t["vmm.ide"], t["vmm.ide_request"])
    fig.box(310, 169, 280, 51, t["vmm.virtio"], t["vmm.virtio_request"], fill=ACCENT_FILL, stroke=ACCENT)
    fig.line([(150, 220), (150, 232), (450, 232), (450, 220)])
    fig.arrow([(300, 232), (300, 250)])
    fig.box(155, 252, 290, 44, t["vmm.disk"], t["vmm.read"], icon="database", fill=WHITE)
    return fig


def concepts_03_version_swap(lang: str) -> Figure:
    """docs/concepts/03_onpolicy_rl_with_sandboxes "학습 중 샌드박스 업데이트": rollout steps over the batch timeline."""
    t = T[lang]
    fig = Figure(760, 412)
    sg, sx0 = 33, 16
    sw = (728 - 4 * sg) / 5
    xs = [sx0 + i * (sw + sg) for i in range(5)]
    fy, sy, sh = 16, 124, 64
    # Parity failure branch above step 3, outside the operator lane
    mbox(fig, xs[2], fy, sw, 46, t["vs.fail"], gid="n:keep-v1")
    fig.arrow([(xs[2] + sw / 2, sy), (xs[2] + sw / 2, fy + 48)], color=RED)
    side_label(fig, xs[2] + sw / 2, fy + 64, t["vs.fail_l"], color=RED)
    fig.container(sx0 - 8, sy - 30, 744 - sx0 + 16, sh + 42, t["vs.ops"], icon="terminal")
    for i, (x, lines) in enumerate(zip(xs, t["vs.steps"])):
        style = {}
        if i == 2:
            style = dict(fill=WHITE, stroke=INK)
        elif i == 3:
            style = dict(fill=ACCENT_FILL, stroke=ACCENT)
        mbox(fig, x, sy, sw, sh, lines, gid=f"n:step{i + 1}", **style)
        if i < 4:
            lab = t["vs.pass_l"] if i == 2 else None
            fig.arrow([(x + sw, sy + sh / 2), (xs[i + 1] - 2, sy + sh / 2)], label=lab,
                      label_at=(x + sw + sg / 2, sy + sh / 2 - 8) if lab else None)
    # Batch timeline: the switch lands on a batch boundary under step 4
    switch_x = xs[3] + sw / 2
    ty, cy, ch = 238, 272, 36
    fig.container(sx0 - 8, ty, 744 - sx0 + 16, 106, t["vs.trainer"], icon="sync")
    cg, n_left = 8, 5
    half = 10  # half of the wider gap at the switch
    cw = (switch_x - half - sx0 - (n_left - 1) * cg) / n_left
    cells = [sx0 + i * (cw + cg) for i in range(n_left)]
    x = switch_x + half
    while x + cw <= 744 + 0.5:
        cells.append(x)
        x += cw + cg
    for i, x in enumerate(cells):
        v2 = x > switch_x
        mbox(fig, x, cy, cw, ch, ["v2 batch" if v2 else "v1 batch"], gid=f"n:batch{i}",
             **(dict(fill=ACCENT_FILL, stroke=ACCENT) if v2 else {}))
    fig.text(switch_x - 12, cy + ch + 22, t["vs.inflight"], size=SMALL, anchor="end")
    fig.text(switch_x + 12, cy + ch + 22, t["vs.event"], size=SMALL, anchor="start")
    fig.line([(switch_x, sy + sh + 2), (switch_x, cy + ch + 28)], color=ACCENT, width=1.6, dash="5 4")
    fig.text(switch_x + 8, (sy + sh + 12 + ty) / 2 + 4, t["vs.sync"], size=SMALL, anchor="start")
    # Time axis
    fig.arrow([(sx0, ty + 106 + 22), (744, ty + 106 + 22)], color=MUTED_STROKE)
    fig.text(744, ty + 106 + 42, t["vs.time"], size=SMALL, anchor="end")
    return fig


def concepts_04(lang: str) -> Figure:
    """Keep each role in the same column and show who manages its workers in B1 and B2."""
    t = T[lang]
    fig = Figure(544, 304)
    fig.parts.append(f'<title>{escape(t["p4.title"])}</title><desc>{escape(t["p4.desc"])}</desc>')
    for top, scenario, types in ((0, "b1", ("ml.g5.2xlarge × 1", "m6i.large × 2", "g5.xlarge × 2")),
                                 (152, "b2", ("ml.g5.2xlarge × 1", "ml.m5.xlarge × 1", "ml.g5.xlarge × 2"))):
        fig.text(10, top + 25, t[f"p4.{scenario}"], size=20, bold=True, anchor="start")
        hyperpod_width = 172 if scenario == "b1" else 528
        fig.rect(8, top + 35, hyperpod_width, 110, fill=ACCENT_FILL, stroke=ACCENT)
        fig.text(18, top + 55, "HyperPod", size=15, bold=True, color=ACCENT, anchor="start")
        if scenario == "b1":
            fig.rect(186, top + 35, 350, 110, fill=GREY_FILL, stroke=MUTED_STROKE)
            fig.text(196, top + 55, "EC2", size=15, bold=True, anchor="start")
        for x, icon, role, instance in zip((94, 272, 450), ("ai-model", "server", "shield-lock"),
                                           t["p4.roles"], types, strict=True):
            fig.icon(icon, x - 12, top + 65, 24)
            fig.text(x, top + 110, role, size=17, bold=True)
            fig.text(x, top + 133, instance, size=16)
    return fig


def concepts_05(lang: str) -> Figure:
    """Map the three GPU deployment scenarios to the grading runtimes available in the labs."""
    t = T[lang]
    fig = Figure(590, 276)
    fig.parts.append(f'<title>{escape(t["p5.title"])}</title><desc>{escape(t["p5.desc"])}</desc>')
    fig.text(10, 26, t["p5.title"], size=21, bold=True, anchor="start")
    platforms = zip((10, 205, 400), ("server", "git-merge", "cloud"), t["p5.platforms"], strict=True)
    for x, icon, (title, training) in platforms:
        center = x + 90
        fig.rect(x, 42, 180, 88, fill=GREY_FILL, stroke=MUTED_STROKE)
        fig.icon(icon, center - 12, 49, 24, ACCENT)
        fig.text(center, 96, title, size=15, bold=True)
        fig.text(center, 118, training, size=15)

    # A and B1 share the EC2 grading choices. B2 has its own HyperPod grading group.
    fig.line([(100, 130), (100, 139), (295, 139), (295, 130)], color=ACCENT, width=2)
    fig.arrow([(197.5, 139), (197.5, 152)], color=ACCENT, width=2)
    fig.arrow([(490, 130), (490, 152)], color=ACCENT, width=2)
    for x, width, title in ((10, 375, t["p5.ec2"]), (400, 180, t["p5.hp"])):
        fig.rect(x, 154, width, 114, fill=ACCENT_FILL, stroke=ACCENT)
        fig.text(x + width / 2, 178, title, size=15, bold=True, color=ACCENT)
    for x, width, name, info, icon in ((20, 169, "gVisor", t["p5.gvisor"], "shield-lock"),
                                       (200, 175, "Kata + QEMU", t["p5.kata"], "device-desktop"),
                                       (410, 160, "gVisor", t["p5.gvisor"], "shield-lock")):
        fig.rect(x, 189, width, 69, fill=WHITE, stroke=MUTED_STROKE)
        fig.icon(icon, x + 9, 206, 22, ACCENT)
        fig.text(x + width / 2 + 12, 217, name, size=16, bold=True)
        fig.text(x + width / 2 + 12, 242, info, size=15)
    return fig


def concepts_06(lang: str) -> Figure:
    """docs/concepts/06_agent_sandbox Pain point: turns scattered over a stateless pool vs one claimed sandbox."""
    t = T[lang]
    fig = Figure(760, 528)
    ex, ew, tx, tw, rx, rw = 16, 112, 186, 172, 444, 300
    for p, (oy, letter, title) in enumerate(((0, "a", t["p6.a"]), (264, "b", t["p6.b"]))):
        fix = p == 1
        fig.panel(16, oy + 24, letter, title)
        top = oy + 50
        r = [top + 24, top + 88, top + 172]
        mbox(fig, ex, top, ew, r[2] + 26 - top, t["p6.ep"], gid=f"n:episode-{letter}")
        mbox(fig, tx, r[0] - 22, tw, 44, t["p6.t1"], gid=f"n:turn1-{letter}")
        mbox(fig, tx, r[1] - 22, tw, 44, t["p6.t2"], gid=f"n:turn2-{letter}")
        fig.arrow([(ex + ew, r[0]), (tx - 2, r[0])])
        fig.arrow([(ex + ew, r[1]), (tx - 2, r[1])])
        if fix:
            mbox(fig, rx, r[0] - 22, rw, r[1] + 22 - (r[0] - 22), t["p6.claimed"], icon="shield-lock",
                 fill=ACCENT_FILL, stroke=ACCENT, gid="n:claimed")
            fig.arrow([(tx + tw, r[0]), (rx - 2, r[0])])
            fig.arrow([(tx + tw, r[1]), (rx - 2, r[1])])
            fig.arrow([(ex + ew, r[2]), (rx - 2, r[2])], label=t["p6.claim"], label_at=((ex + ew + rx) / 2, r[2] - 8))
            mbox(fig, rx, r[2] - 26, rw, 52, t["p6.pool"], icon="stack", gid="n:pool")
            fig.arrow([(rx + rw / 2, r[2] - 26), (rx + rw / 2, r[1] + 24)])
            fig.text(rx + rw / 2 - 8, (r[1] + 22 + r[2] - 26) / 2 + 4, t["p6.hand"], size=SMALL, anchor="end")
        else:
            mbox(fig, rx, r[0] - 22, rw, 44, t["p6.pa"], icon="container", gid="n:podA")
            mbox(fig, rx, r[1] - 22, rw, 44, t["p6.pb"], icon="container", gid="n:podB")
            fig.arrow([(tx + tw, r[0]), (rx - 2, r[0])])
            fig.arrow([(tx + tw, r[1]), (rx - 2, r[1])])
            fig.arrow([(ex + ew, r[2]), (rx - 2, r[2])], color=RED, dash="5 4", label=t["p6.fresh"],
                      label_at=((ex + ew + rx) / 2, r[2] - 8), label_color=RED)
            mbox(fig, rx, r[2] - 26, rw, 52, t["p6.kata"], icon="clock", fill=RED_FILL, stroke=RED, color=RED,
                 gid="n:kata")
    return fig


FIGURES = {
    "concepts-01_why_gpu_sandbox--two-tier": concepts_01_two_tier,
    "concepts-01_why_gpu_sandbox--rl-loop": concepts_01_rl_loop,
    "concepts-02_isolation_runtimes--gpu-paths": concepts_02_gpu_paths,
    "concepts-02_isolation_runtimes--gpu-passthrough": concepts_02_gpu_passthrough,
    "concepts-02_isolation_runtimes--kata-hypervisors": concepts_02_kata_hypervisors,
    "concepts-03_onpolicy_rl_with_sandboxes--version-swap": concepts_03_version_swap,
    "concepts-04_platforms_and_instances": concepts_04,
    "concepts-05_decision_guide--exercise-path": concepts_05,
    "concepts-06_agent_sandbox": concepts_06,
}
