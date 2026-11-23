"""Pain point schematics for the hands-on pages 00 to 05 (group fc).

Every box, label and value comes from the page's own Pain point and Why text or its body tables
(the source page is named in each docstring).
"""

from __future__ import annotations

from figlib import (ACCENT, ACCENT_FILL, GREY_FILL, INK, MUTED_STROKE, RED, RED_FILL, SIZE, SMALL, Figure,
                    text_width)

T = {
    "ko": {
        # 00 overview
        "h00.a": "놓치기 쉬운 네 가지", "h00.b": "이 핸즈온이 각각을 다루는 방법",
        "h00.t1": "실행 순서", "h00.t1s": "04는 03 뒤, 06은 05 뒤",
        "h00.t2": "G and VT 쿼터", "h00.t2s": "vCPU 기준, 0일 수 있는 기본값",
        "h00.t3": "과금 노드", "h00.t3s": "단계마다 다르게 켜는 노드",
        "h00.t4": "Kata + GPU", "h00.t4s": "최소 단위 g4dn.metal 한 대",
        "h00.m1": "03, 05 건너뛰기", "h00.m2": "쿼터를 올리지 않은 채", "h00.m3": "노드를 켜는 단계를 모른 채",
        "h00.m4": "GPU와 무관한 설정 실수",
        "h00.e1": "03: config.env 에러", "h00.e1s": "05: pool 배포 실패",
        "h00.e2": "노드 그룹 생성 실패", "h00.e2s": "02_create_cluster.sh",
        "h00.e3": "실습 뒤에도 노드 과금", "h00.e3s": "지우기 전까지 계속",
        "h00.e4": "g4dn.metal에서 디버깅", "h00.e4s": "시간당 7.824 USD",
        "h00.f1": "스크립트 중단", "h00.f1s": "필요한 값이 비거나 __SET_ME__면",
        "h00.f2": "01 사전 확인", "h00.f2s": "G and VT 쿼터 조회 (읽기 전용)",
        "h00.f3": "CDK 스택과 AMI 삭제", "h00.f3s": "클러스터 이름 입력, ECR은 --images",
        "h00.f4": "c8i.2xlarge에서 리허설", "h00.f4s": "g4dn.metal은 GPU passthrough만",
        "h00.s1": "번호 순서대로 실행", "h00.s2": "02 전에 01 실행", "h00.s3": "끝나면 08 실행",
        "h00.s4": "kata/cpu_nodes.sh 먼저",
        # 01 cluster and images
        "h01.a": "기본값으로 만든 EKS 클러스터", "h01.b": "CDK 스택: private endpoint만, IMDS hop limit 1",
        "h01.net": "인터넷", "h01.net_sub": "어디서나",
        "h01.cl_a": "EKS 클러스터 (기본값)", "h01.cl_b": "EKS 클러스터 (CDK 스택)",
        "h01.node_a": "노드 (IMDS hop limit 2 이상)", "h01.node_b": "노드 (IMDSv2 필수, hop limit 1)",
        "h01.api": "EKS API", "h01.api_sub": "IAM 인증은 그대로",
        "h01.pod": "pod 안의 코드",
        "h01.cred": "노드의 인스턴스 자격 증명", "h01.cred_sub": "IMDS 169.254.169.254",
        "h01.a1": "public endpoint로 접속 시도", "h01.a2": "IMDS 요청",
        "h01.b1": "private endpoint만, 작업 PC는 SSM 터널", "h01.b2": "응답 없음",
        # 02 gVisor
        "h02.a": "runc 방식 그대로, 확인하지 않는 드라이버 버전", "h02.b": "CDI 경로와 지원 목록에 있는 드라이버",
        "h02.runc": "runc 노드", "h02.runc_a": "nvidia-container-runtime hook", "h02.runc_b": "trainer",
        "h02.gv": "gVisor 노드", "h02.gv_sub": "Sentry가 syscall 처리",
        "h02.ami": "AMI 교체", "h02.ami_sub": "드라이버 버전 변경",
        "h02.g5": "g5 (A10G) 노드, GSP off", "h02.g5_sub": "proprietary 580.178.04",
        "h02.ctr": "GPU를 쓰는 컨테이너",
        "h02.sb_a": "sandbox 컨테이너", "h02.sb_as": "GPU 연결 경로 없음",
        "h02.sb_b": "GPU를 쓰는 sandbox 컨테이너", "h02.sb_bs": "runsc가 켜는 nvproxy",
        "h02.fail": "시작되지 않는 샌드박스",
        "h02.ok": "샌드박스 시작", "h02.ok_sub": "불일치면 Ready 불가 (fail closed)",
        "h02.a1": "hook의 GPU 주입", "h02.a2": "같은 hook 사용 불가", "h02.a3": "nvproxy가 지원하지 않는 버전",
        "h02.cdi": "CDI 장치 (device plugin cdi-cri)", "h02.same": "같은 device plugin (cdi-cri)", "h02.b3": "gVisor 지원 목록에 있는 버전",
        # 03 Kata
        "h03.a": "g4dn.metal에서 하는 모든 확인", "h03.b": "c8i.2xlarge에서 먼저 하는, GPU와 무관한 확인",
        "h03.grp": "GPU와 무관한 설정",
        "h03.c1": "kata-deploy, containerd drop-in", "h03.c2": "RuntimeClass, NetworkPolicy",
        "h03.c3": "node guard, 부팅 시간", "h03.c4": "GPU passthrough (VFIO, IOMMU)",
        "h03.metal": "g4dn.metal",
        "h03.metal_a": ["Kata VM에 GPU를 직접 할당할 수 있는", "유일한 x86 NVIDIA 인스턴스", "시간당 7.824 USD"],
        "h03.metal_b": "IOMMU AMI, 시간당 7.824 USD",
        "h03.c8i": "c8i.2xlarge", "h03.c8i_s": ["nested virtualization (/dev/kvm)", "시간당 0.37484 USD"],
        # 04 sandbox pools
        "h04.a": "일반 서비스의 기본 설정 그대로", "h04.b": "후보 코드의 접근 경로마다 다른 차단 계층",
        "h04.pod": "샌드박스 pod",
        "h04.code": "후보 코드", "h04.code_sub": "서버와 같은 pod",
        "h04.sec_a": "token, API key", "h04.sec_as": "pod에 둔 비밀",
        "h04.sec_b": "JWKS 공개 키", "h04.sec_bs": "비밀이 아닙니다",
        "h04.imds": "IMDS, API server", "h04.kubelet": "노드 kubelet", "h04.kubelet_sub": "포트 10250",
        "h04.a1": "읽기", "h04.a2": "정책 적용 전 default-allow", "h04.a3": "노드 IP는 항상 허용",
        "h04.b1": "훔칠 비밀 없음", "h04.b2": "NetworkPolicy가 차단, readiness가 확인",
        "h04.b3": "node guard가 차단, readiness가 확인",
        # 05 GRPO training
        "h05.a": "맞으면 1, 틀리면 0인 reward", "h05.b": "부분 점수와 sandbox_error 제외",
        "h05.ans": "completion", "h05.ans_sub": "group 하나",
        "h05.sb": "샌드박스", "h05.sb_sub": "채점",
        "h05.l1": "올바른 커널 없음", "h05.l2": "바쁘거나 장애가 난 pod",
        "h05.ra1": "reward 0", "h05.ra1s": "8개 모두 0점", "h05.ra2": "reward 0", "h05.ra2s": "채점 실패도 0점",
        "h05.rb1": "부분 점수", "h05.rb1s": "0.1, 0.15, 0.3, 0.4", "h05.rb2": "None", "h05.rb2s": "sandbox_error",
        "h05.oa1": "advantage 0", "h05.oa1s": "학습 신호 없음",
        "h05.oa2": "0점을 받는 policy", "h05.oa2s": "인프라 문제 때문에",
        "h05.ob1": "학습 신호가 되는 점수 차이", "h05.ob1s": "0.3과 0.1도 구분",
        "h05.ob2": "group baseline에서 제외", "h05.ob2s": "0점을 받지 않는 policy",
    },
    "en": {
        "h00.a": "Four things that are easy to miss", "h00.b": "How this hands-on handles each one",
        "h00.t1": "Run order", "h00.t1s": "04 after 03, 06 after 05",
        "h00.t2": "G and VT quota", "h00.t2s": "counts vCPUs, default can be 0",
        "h00.t3": "Billable nodes", "h00.t3s": "each step starts its own",
        "h00.t4": "Kata + GPU", "h00.t4s": "smallest unit one g4dn.metal",
        "h00.m1": "skip 03 or 05", "h00.m2": "not raised", "h00.m3": "not knowing which step",
        "h00.m4": "GPU-unrelated mistakes",
        "h00.e1": "03: config.env error", "h00.e1s": "05: pool deploy fails",
        "h00.e2": "node group creation fails", "h00.e2s": "02_create_cluster.sh",
        "h00.e3": "nodes bill after you finish", "h00.e3s": "until they are deleted",
        "h00.e4": "debugging on g4dn.metal", "h00.e4s": "7.824 USD per hour",
        "h00.f1": "scripts stop", "h00.f1s": "if a needed value is empty or __SET_ME__",
        "h00.f2": "01 prerequisite check", "h00.f2s": "reads the G and VT quota",
        "h00.f3": "CDK stack and AMIs deleted", "h00.f3s": "type the cluster name, ECR with --images",
        "h00.f4": "rehearse on c8i.2xlarge", "h00.f4s": "g4dn.metal only for passthrough",
        "h00.s1": "run in number order", "h00.s2": "run 01 before 02", "h00.s3": "run 08 when done",
        "h00.s4": "kata/cpu_nodes.sh first",
        "h01.a": "An EKS cluster created with defaults",
        "h01.b": "CDK stack: private endpoint only, IMDS hop limit 1",
        "h01.net": "Internet", "h01.net_sub": "anywhere",
        "h01.cl_a": "EKS cluster (defaults)", "h01.cl_b": "EKS cluster (CDK stack)",
        "h01.node_a": "Node (IMDS hop limit 2 or more)", "h01.node_b": "Node (IMDSv2 required, hop limit 1)",
        "h01.api": "EKS API", "h01.api_sub": "IAM auth still applies",
        "h01.pod": "Code in a pod",
        "h01.cred": "Node instance credentials", "h01.cred_sub": "IMDS 169.254.169.254",
        "h01.a1": "connection tried on the public endpoint", "h01.a2": "IMDS request",
        "h01.b1": "private endpoint only, work PC via SSM tunnel", "h01.b2": "no response back",
        "h02.a": "The runc way, driver version unchecked", "h02.b": "The CDI path and a driver on the support list",
        "h02.runc": "runc node", "h02.runc_a": "nvidia-container-runtime hook", "h02.runc_b": "trainer",
        "h02.gv": "gVisor node", "h02.gv_sub": "the Sentry receives syscalls",
        "h02.ami": "AMI change", "h02.ami_sub": "new driver version",
        "h02.g5": "g5 (A10G) node, GSP off", "h02.g5_sub": "proprietary 580.178.04",
        "h02.ctr": "container uses the GPU",
        "h02.sb_a": "sandbox container", "h02.sb_as": "no path for the devices",
        "h02.sb_b": "sandbox container uses the GPU", "h02.sb_bs": "runsc turns on nvproxy",
        "h02.fail": "sandbox does not start",
        "h02.ok": "sandbox starts", "h02.ok_sub": "not Ready on a mismatch (fail closed)",
        "h02.a1": "the hook injects the GPU", "h02.a2": "the same hook does not apply",
        "h02.a3": "version nvproxy does not know",
        "h02.cdi": "CDI devices (device plugin cdi-cri)", "h02.same": "the same device plugin (cdi-cri)", "h02.b3": "on the gVisor support list",
        "h03.a": "Every check lands on g4dn.metal", "h03.b": "GPU-unrelated checks run on c8i.2xlarge first",
        "h03.grp": "Settings unrelated to the GPU",
        "h03.c1": "kata-deploy, containerd drop-ins", "h03.c2": "RuntimeClasses, NetworkPolicy",
        "h03.c3": "node guard, boot time", "h03.c4": "GPU passthrough (VFIO, IOMMU)",
        "h03.metal": "g4dn.metal",
        "h03.metal_a": ["the only x86 NVIDIA instance", "that can hand a GPU to a Kata VM", "7.824 USD per hour"],
        "h03.metal_b": "IOMMU AMI, 7.824 USD per hour",
        "h03.c8i": "c8i.2xlarge", "h03.c8i_s": ["nested virtualization (/dev/kvm)", "0.37484 USD per hour"],
        "h04.a": "Defaults of a regular service", "h04.b": "A layer on every path candidate code can take",
        "h04.pod": "Sandbox pod",
        "h04.code": "Candidate code", "h04.code_sub": "same pod as the server",
        "h04.sec_a": "token, API key", "h04.sec_as": "secrets in the pod",
        "h04.sec_b": "JWKS public keys", "h04.sec_bs": "not a secret",
        "h04.imds": "IMDS, API server", "h04.kubelet": "Node kubelet", "h04.kubelet_sub": "port 10250",
        "h04.a1": "read", "h04.a2": "default-allow before policies apply", "h04.a3": "node IP always allowed",
        "h04.b1": "nothing to steal", "h04.b2": "NetworkPolicy blocks, readiness checks",
        "h04.b3": "node guard blocks, readiness checks",
        "h05.a": "A reward of 1 if correct and 0 otherwise", "h05.b": "Partial credit, sandbox_error excluded",
        "h05.ans": "completions", "h05.ans_sub": "one group",
        "h05.sb": "Sandbox", "h05.sb_sub": "scoring",
        "h05.l1": "no correct kernel", "h05.l2": "pod busy or dead",
        "h05.ra1": "reward 0", "h05.ra1s": "all 8 score 0", "h05.ra2": "reward 0", "h05.ra2s": "failed scoring too",
        "h05.rb1": "partial credit", "h05.rb1s": "0.1, 0.15, 0.3, 0.4", "h05.rb2": "None", "h05.rb2s": "sandbox_error",
        "h05.oa1": "advantage 0", "h05.oa1s": "no learning signal",
        "h05.oa2": "policy punished", "h05.oa2s": "for an infrastructure problem",
        "h05.ob1": "score gaps are a signal", "h05.ob1s": "0.3 and 0.1 differ",
        "h05.ob2": "left out of the baseline", "h05.ob2s": "not punished",
    },
}


def card(fig: Figure, x, y, w, h, label, subs, *, icon=None, fill=GREY_FILL, stroke=MUTED_STROKE, color=INK,
         gid=None) -> None:
    """A tall box like Figure.box, with an icon on top and several sub lines (box() takes one)."""
    fig.rect(x, y, w, h, fill=fill, stroke=stroke, gid=gid)
    block = (40 if icon else 0) + 17 + 17 * len(subs)
    top = y + (h - block) / 2
    if icon:
        fig.icon(icon, x + w / 2 - 14, top, 28, color)
        top += 40
    fig.text(x + w / 2, top + 13, label, color=color)
    for i, s in enumerate(subs):
        fig.text(x + w / 2, top + 13 + 17 * (i + 1), s, size=SMALL, color=color)
    need = max([text_width(label)] + [text_width(s, SMALL) for s in subs]) + 16
    assert need <= w, f"label too wide for card {gid or label!r}: {need:.0f} > {w}"


def _fits(label: str, gap: float, size: int = SMALL) -> None:
    """Edge labels sit above a line; keep them inside the gap they label."""
    assert text_width(label, size) + 12 <= gap, f"edge label too wide: {label!r} {text_width(label, size):.0f} > {gap}"


def handson_00(lang: str) -> Figure:
    """docs/handson/00_overview: order, G and VT quota, billable nodes and g4dn.metal debugging, and the guards."""
    t = T[lang]
    fig = Figure(760, 576)
    lx, lw, rx, rw = 16, 236, 470, 274
    for p, (oy, letter, title) in enumerate(((0, "a", t["h00.a"]), (288, "b", t["h00.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 52
        for i, ico in enumerate(("list-ordered", "meter", "credit-card", "cpu")):
            n = i + 1
            y = top + i * 58
            cy = y + 23
            fig.box(lx, y, lw, 46, t[f"h00.t{n}"], t[f"h00.t{n}s"], icon=ico, gid=f"n:topic{n}-{letter}")
            if p == 0:
                _fits(t[f"h00.m{n}"], rx - lx - lw)
                fig.arrow([(lx + lw, cy), (rx - 2, cy)], color=RED, label=t[f"h00.m{n}"],
                          label_at=((lx + lw + rx) / 2, cy - 8))
                fig.box(rx, y, rw, 46, t[f"h00.e{n}"], t[f"h00.e{n}s"], fill=RED_FILL, stroke=RED, color=RED,
                        gid=f"n:effect{n}-a")
            else:
                _fits(t[f"h00.s{n}"], rx - lx - lw)
                fig.arrow([(lx + lw, cy), (rx - 2, cy)], color=ACCENT, label=t[f"h00.s{n}"],
                          label_at=((lx + lw + rx) / 2, cy - 8))
                fig.box(rx, y, rw, 46, t[f"h00.f{n}"], t[f"h00.f{n}s"], fill=ACCENT_FILL, stroke=ACCENT,
                        gid=f"n:guard{n}-b")
    return fig


def handson_01(lang: str) -> Figure:
    """docs/handson/01_cluster_and_images: public endpoint and IMDS hop limit 2 vs the CDK stack defaults."""
    t = T[lang]
    fig = Figure(760, 552)
    nx, nw, cx, px, pw, ax, aw = 16, 140, 180, 212, 150, 506, 206
    bx = ax - 26
    for p, (oy, letter, title) in enumerate(((0, "a", t["h01.a"]), (276, "b", t["h01.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 50
        cy1, cy2 = top + 50, top + 149
        fig.container(cx, top, 744 - cx, 204, t["h01.cl_b" if p else "h01.cl_a"], icon="stack",
                      stroke=ACCENT if p else MUTED_STROKE, color=ACCENT if p else INK, bold=bool(p))
        fig.container(cx + 16, top + 90, 744 - cx - 32, 100, t["h01.node_b" if p else "h01.node_a"], icon="server")
        fig.box(nx, cy1 - 25, nw, 50, t["h01.net"], t["h01.net_sub"], icon="globe", gid=f"n:internet-{letter}")
        fig.box(ax, cy1 - 25, aw, 50, t["h01.api"], t["h01.api_sub"], gid=f"n:api-{letter}")
        fig.box(px, cy2 - 25, pw, 50, t["h01.pod"], icon="code", gid=f"n:pod-{letter}")
        fig.box(ax, cy2 - 25, aw, 50, t["h01.cred"], t["h01.cred_sub"], icon="key", gid=f"n:cred-{letter}")
        # Row 1 labels sit inside the cluster container, clear of its left edge.
        l1 = (cx + 16 + (bx if p else ax)) / 2
        if p == 0:
            _fits(t["h01.a1"], ax - cx - 16)
            _fits(t["h01.a2"], ax - px - pw)
            fig.arrow([(nx + nw, cy1), (ax - 2, cy1)], color=RED, label=t["h01.a1"], label_at=(l1, cy1 - 8))
            fig.arrow([(px + pw, cy2), (ax - 2, cy2)], color=RED, label=t["h01.a2"],
                      label_at=((px + pw + ax) / 2, cy2 - 8))
        else:
            _fits(t["h01.b1"], bx - cx - 16)
            _fits(t["h01.b2"], bx - px - pw)
            fig.line([(nx + nw, cy1), (bx, cy1)])
            fig.block(bx, cy1)
            fig.text(l1, cy1 - 8, t["h01.b1"], size=SMALL)
            fig.line([(px + pw, cy2), (bx, cy2)])
            fig.block(bx, cy2)
            fig.text((px + pw + bx) / 2, cy2 - 8, t["h01.b2"], size=SMALL)
    return fig


def handson_02(lang: str) -> Figure:
    """docs/handson/02_gvisor: the runc hook and an unknown driver vs CDI and the supported driver."""
    t = T[lang]
    fig = Figure(760, 556)
    lx, lw, rx, rw = 16, 220, 470, 274
    gap = rx - lx - lw
    for p, (oy, letter, title) in enumerate(((0, "a", t["h02.a"]), (278, "b", t["h02.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 52
        cys = [top + 25 + i * 74 for i in range(3)]
        mid = (lx + lw + rx) / 2
        # row 1: runc node
        fig.box(lx, cys[0] - 25, lw, 50, t["h02.runc"], t["h02.runc_b" if p else "h02.runc_a"], icon="server",
                gid=f"n:runc-{letter}")
        fig.box(rx, cys[0] - 25, rw, 50, t["h02.ctr"], icon="container", gid=f"n:ctr-{letter}")
        # row 2: gVisor node
        fig.box(lx, cys[1] - 25, lw, 50, t["h02.gv"], t["h02.gv_sub"], icon="server", gid=f"n:gvisor-{letter}")
        # row 3: driver
        if p == 0:
            fig.arrow([(lx + lw, cys[0]), (rx - 2, cys[0])], label=t["h02.a1"], label_at=(mid, cys[0] - 8))
            bx = rx - 26
            _fits(t["h02.a2"], bx - lx - lw)
            fig.line([(lx + lw, cys[1]), (bx, cys[1])], color=RED)
            fig.block(bx, cys[1])
            fig.text((lx + lw + bx) / 2, cys[1] - 8, t["h02.a2"], size=SMALL)
            fig.box(rx, cys[1] - 25, rw, 50, t["h02.sb_a"], t["h02.sb_as"], icon="container", gid="n:sandbox-a")
            fig.box(lx, cys[2] - 25, lw, 50, t["h02.ami"], t["h02.ami_sub"], icon="sync", gid="n:driver-a")
            _fits(t["h02.a3"], gap)
            fig.arrow([(lx + lw, cys[2]), (rx - 2, cys[2])], color=RED, label=t["h02.a3"], label_at=(mid, cys[2] - 8))
            fig.box(rx, cys[2] - 25, rw, 50, t["h02.fail"], icon="alert", fill=RED_FILL, stroke=RED, color=RED,
                    gid="n:outcome-a")
        else:
            _fits(t["h02.cdi"], gap)
            _fits(t["h02.same"], gap)
            fig.arrow([(lx + lw, cys[0]), (rx - 2, cys[0])], color=ACCENT, label=t["h02.same"],
                      label_at=(mid, cys[0] - 8))
            fig.arrow([(lx + lw, cys[1]), (rx - 2, cys[1])], color=ACCENT, label=t["h02.cdi"],
                      label_at=(mid, cys[1] - 8))
            fig.box(rx, cys[1] - 25, rw, 50, t["h02.sb_b"], t["h02.sb_bs"], icon="container", fill=ACCENT_FILL,
                    stroke=ACCENT, gid="n:sandbox-b")
            fig.box(lx, cys[2] - 25, lw, 50, t["h02.g5"], t["h02.g5_sub"], icon="cpu", gid="n:driver-b")
            _fits(t["h02.b3"], gap)
            fig.arrow([(lx + lw, cys[2]), (rx - 2, cys[2])], color=ACCENT, label=t["h02.b3"],
                      label_at=(mid, cys[2] - 8))
            fig.box(rx, cys[2] - 25, rw, 50, t["h02.ok"], t["h02.ok_sub"], icon="check-circle", fill=ACCENT_FILL,
                    stroke=ACCENT, gid="n:outcome-b")
    return fig


def handson_03(lang: str) -> Figure:
    """docs/handson/03_kata: every check on g4dn.metal vs GPU-unrelated checks on c8i.2xlarge first."""
    t = T[lang]
    fig = Figure(760, 584)
    gx, bx, bw, rx, rw = 16, 30, 248, 500, 244
    pitch, bh = 46, 36
    for p, (oy, letter, title) in enumerate(((0, "a", t["h03.a"]), (292, "b", t["h03.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 48
        ys = [top + 28 + i * pitch for i in range(3)]
        group_h = ys[2] + bh + 12 - top
        ys.append(top + group_h + 16)
        fig.container(gx, top, bw + 28, group_h, t["h03.grp"], icon="gear")
        for i, y in enumerate(ys):
            fig.box(bx, y, bw, bh, t[f"h03.c{i + 1}"], gid=f"n:check{i + 1}-{letter}")
        if p == 0:
            card(fig, rx, ys[0], rw, ys[3] + bh - ys[0], t["h03.metal"], t["h03.metal_a"], icon="server",
                 gid="n:metal-a")
        else:
            card(fig, rx, ys[0], rw, ys[2] + bh - ys[0], t["h03.c8i"], t["h03.c8i_s"], icon="cpu", fill=ACCENT_FILL,
                 stroke=ACCENT, gid="n:c8i-b")
            fig.box(rx, ys[3] + bh / 2 - 24, rw, 48, t["h03.metal"], t["h03.metal_b"], icon="server", gid="n:metal-b")
        for i, y in enumerate(ys):
            fig.arrow([(bx + bw, y + bh / 2), (rx - 2, y + bh / 2)], color=INK if i == 3 else (ACCENT if p else RED))
    return fig


def handson_04(lang: str) -> Figure:
    """docs/handson/04_sandbox_pools: secrets in the pod, default-allow and the node IP exception, and the layers."""
    t = T[lang]
    fig = Figure(760, 572)
    cx, cw, sx, sw, tx, tw, edge = 32, 156, 312, 170, 566, 178, 500
    for p, (oy, letter, title) in enumerate(((0, "a", t["h04.a"]), (286, "b", t["h04.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 80
        cys = [top + 25 + i * 68 for i in range(3)]
        fig.container(16, top - 30, edge - 16, 228, t["h04.pod"], icon="shield-lock", stroke=ACCENT if p else MUTED_STROKE,
                      color=ACCENT if p else INK, bold=bool(p))
        fig.box(cx, top, cw, 186, t["h04.code"], t["h04.code_sub"], icon="code",
                fill=ACCENT_FILL if p else GREY_FILL, stroke=ACCENT if p else MUTED_STROKE, gid=f"n:code-{letter}")
        if p == 0:
            fig.box(sx, cys[0] - 25, sw, 50, t["h04.sec_a"], t["h04.sec_as"], icon="key", gid="n:secret-a")
        else:
            fig.box(sx, cys[0] - 25, sw, 50, t["h04.sec_b"], t["h04.sec_bs"], icon="file", gid="n:secret-b")
        fig.box(tx, cys[1] - 25, tw, 50, t["h04.imds"], icon="server", gid=f"n:imds-{letter}")
        fig.box(tx, cys[2] - 25, tw, 50, t["h04.kubelet"], t["h04.kubelet_sub"], icon="server",
                gid=f"n:kubelet-{letter}")
        if p == 0:
            fig.arrow([(cx + cw, cys[0]), (sx - 2, cys[0])], color=RED, label=t["h04.a1"],
                      label_at=((cx + cw + sx) / 2, cys[0] - 8))
            for i in (1, 2):
                _fits(t[f"h04.a{i + 1}"], tx - cx - cw)
                fig.arrow([(cx + cw, cys[i]), (tx - 2, cys[i])], color=RED, label=t[f"h04.a{i + 1}"],
                          label_at=((cx + cw + edge) / 2, cys[i] - 8))
        else:
            _fits(t["h04.b1"], sx - cx - cw)
            fig.arrow([(cx + cw, cys[0]), (sx - 2, cys[0])], label=t["h04.b1"],
                      label_at=((cx + cw + sx) / 2, cys[0] - 8))
            bx = tx - 26
            for i in (1, 2):
                _fits(t[f"h04.b{i + 1}"], edge - cx - cw)
                fig.line([(cx + cw, cys[i]), (bx, cys[i])])
                fig.block(bx, cys[i])
                fig.text((cx + cw + edge) / 2, cys[i] - 8, t[f"h04.b{i + 1}"], size=SMALL)
    return fig


def handson_05(lang: str) -> Figure:
    """docs/handson/05_grpo_training: a 0-or-1 reward and failures scored 0 vs partial credit and None."""
    t = T[lang]
    fig = Figure(760, 500)
    ax, aw, sx, sw, rx, rw, ox, ow = 16, 96, 146, 104, 394, 148, 572, 172
    for p, (oy, letter, title) in enumerate(((0, "a", t["h05.a"]), (250, "b", t["h05.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 66
        h = 156
        mid, y1, y2 = top + h / 2, top + 28, top + h - 28
        fig.stack(ax, top, aw, h, t["h05.ans"], t["h05.ans_sub"], icon="stack", gid=f"n:answers-{letter}")
        fig.arrow([(ax + aw + 6, mid), (sx - 2, mid)])
        fig.box(sx, top, sw, h, t["h05.sb"], t["h05.sb_sub"], icon="container", gid=f"n:sandbox-{letter}")
        lx = (sx + sw + rx) / 2
        for i, (y, lab) in enumerate(((y1, "h05.l1"), (y2, "h05.l2"))):
            _fits(t[lab], rx - sx - sw)
            fig.arrow([(sx + sw, y), (rx - 2, y)], label=t[lab], label_at=(lx, y - 8))
        if p == 0:
            fig.box(rx, y1 - 28, rw, 56, t["h05.ra1"], t["h05.ra1s"], gid="n:reward1-a")
            fig.box(rx, y2 - 28, rw, 56, t["h05.ra2"], t["h05.ra2s"], gid="n:reward2-a")
            for y, n in ((y1, 1), (y2, 2)):
                fig.arrow([(rx + rw, y), (ox - 2, y)], color=RED)
                fig.box(ox, y - 28, ow, 56, t[f"h05.oa{n}"], t[f"h05.oa{n}s"], fill=RED_FILL, stroke=RED, color=RED,
                        gid=f"n:outcome{n}-a")
        else:
            fig.box(rx, y1 - 28, rw, 56, t["h05.rb1"], t["h05.rb1s"], gid="n:reward1-b")
            fig.box(rx, y2 - 28, rw, 56, t["h05.rb2"], t["h05.rb2s"], gid="n:reward2-b")
            for y, n in ((y1, 1), (y2, 2)):
                fig.arrow([(rx + rw, y), (ox - 2, y)], color=ACCENT)
                fig.box(ox, y - 28, ow, 56, t[f"h05.ob{n}"], t[f"h05.ob{n}s"], fill=ACCENT_FILL, stroke=ACCENT,
                        gid=f"n:outcome{n}-b")
    return fig


FIGURES = {
    "handson-00_overview": handson_00,
    "handson-01_cluster_and_images": handson_01,
    "handson-02_gvisor": handson_02,
    "handson-03_kata": handson_03,
    "handson-04_sandbox_pools": handson_04,
    "handson-05_grpo_training": handson_05,
}
