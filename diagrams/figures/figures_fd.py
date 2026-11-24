"""Pain point schematics for docs/handson 07, 08, 09, 10 and 99.

Each function draws one figure in one language from shared geometry. Every box and edge comes from the
page's own text (the source page is named in each docstring).
"""

from __future__ import annotations

from figlib import (ACCENT, ACCENT_FILL, GREY_FILL, INK, MUTED_STROKE, RED, RED_FILL, SIZE, SMALL, Figure,
                    text_width)

T = {
    "ko": {
        "h07.a": "며칠 걸리는 학습과 HyperPod 노드의 문제",
        "h07.b": "HyperPod의 복구 기능과 B2 채점 노드",
        "h07.e1": "GPU 노드 고장", "h07.e1s": "며칠짜리 on-policy 학습 중",
        "h07.e2": "생성이나 샌드박스 pool", "h07.e2s": "정지 (hang)",
        "h07.e3": "HyperPod 노드에 샌드박스", "h07.e3s": "gVisor GPU pool",
        "h07.a1e": "수동 노드 교체", "h07.a1o": "수동 job 재시작", "h07.a1os": "사람이 조치할 때까지 대기",
        "h07.a2e": "살아 있는 프로세스", "h07.a2o": "진행되지 않는 학습", "h07.a2os": "겉보기에는 정상",
        "h07.a3e": "기본 드라이버 595.112.07", "h07.a3o": "gVisor 실행 불가", "h07.a3os": "nvproxy 목록에 없는 드라이버",
        "h07.b1e": "NodeRecovery: Automatic", "h07.b1o": "노드 재부팅이나 교체",
        "h07.b1os": "training operator의 job 재시작",
        "h07.b2e": "로그 패턴으로 hang 감지", "h07.b2o": "hang이면 job 재시작",
        "h07.b2os": "elastic agent와 training operator",
        "h07.b3e": "580.178.04 설치 후 재부팅", "h07.b3o": "gVisor pool 기동",
        "h07.b3os": "샌드박스 전용 인스턴스 그룹 (B2)",
        "h08.a": "GPU가 다른 두 pool을 나란히 비교",
        "h08.b": "노드, 이미지, golden이 같은 쌍",
        "h08.h": "벤치마크 harness", "h08.ha": "relu_bias_triton", "h08.hb": "relu_bias_torch_only",
        "h08.p1a": "gVisor pool", "h08.p1as": "g5.xlarge, A10G",
        "h08.p2a": "Kata QEMU pool", "h08.p2as": "g4dn.metal, T4",
        "h08.p1b": "Kata CLH CPU pool", "h08.p1bs": "Cloud Hypervisor",
        "h08.p2b": "Kata QEMU CPU pool", "h08.p2bs": "QEMU",
        "h08.node": "같은 c8i.2xlarge 노드",
        "h08.d": "숫자 차이", "h08.ds": "두 pool 사이",
        "h08.bad": "런타임 + GPU 차이", "h08.bad_sub": "분리 불가",
        "h08.good": "RuntimeClass 차이", "h08.good_sub": "hypervisor, pod 예약량",
        "h09.a": "라이브 데모와 잘못 설정한 정적 호스팅",
        "h09.b": "기록 재생, 비공개 버킷, 텍스트로만 넣는 페이지",
        "h09.v": "방문자", "h09.vs": "인터넷",
        "h09.r": "기록 속 문자열", "h09.rs": "오류 메시지, 정책 위반",
        "h09.t1": "GPU 샌드박스", "h09.t1a": "켜 둔 동안 계속 과금", "h09.t1b": "기록을 만들 때만 필요",
        "h09.t2": "S3 버킷", "h09.t2s": "정적 파일과 기록",
        "h09.t3": "데모 페이지", "h09.t3s": "방문자 브라우저",
        "h09.a1": "라이브 데모: 인터넷에 열린 API", "h09.a2": "공개 버킷, website endpoint: CloudFront 우회",
        "h09.a3": "HTML로 넣으면 스크립트로 실행",
        "h09.b1": "기록 재생: 방문자는 CloudFront까지만", "h09.b2": "OAC, AWS:SourceArn: 직접 접근 403",
        "h09.b3": "텍스트로만 삽입, CSP는 자기 origin만",
        "h10.a": "시나리오 A: GPU 노드가 있어야 시작 가능",
        "h10.b": "시나리오 C: c8i.2xlarge 한 대에 세 런타임",
        "h10.qa": "G and VT 쿼터", "h10.qas": "0인 계정 다수",
        "h10.qb": "Standard 쿼터", "h10.qbs": "G and VT 쿼터 불필요",
        "h10.ok": "승인", "h10.zero": "0",
        "h10.w": "승인 대기", "h10.ws": "실습 시작 불가",
        "h10.sa": "시나리오 A", "h10.sa1": "컴퓨트 시간당 약 3.42 USD", "h10.sa2": "Kata GPU까지 11 USD 초과",
        "h10.sb": "시나리오 C", "h10.sb1": "컴퓨트 시간당 약 0.57 USD", "h10.sb2": "A의 약 6분의 1 (추정)",
        "h10.pa1": "gVisor pool", "h10.pa1s": "g5.xlarge, A10G",
        "h10.pa3": "Kata GPU pool", "h10.pa3s": "g4dn.metal, T4",
        "h10.pb1": "gVisor pool", "h10.pb1s": "runsc, systrap",
        "h10.pb2": "Kata CLH pool", "h10.pb2s": "Cloud Hypervisor",
        "h10.pb3": "Kata QEMU pool", "h10.pb3s": "QEMU VM",
        "h10.node": "c8i.2xlarge 한 대",
        "h10.oa": "런타임 차이만", "h10.oa1": "분리하기 어려운 비교", "h10.oa2": "노드와 GPU가 다르기 때문",
        "h10.ob": "차이를 런타임 차이로", "h10.ob1": "해석하기 쉬운 비교", "h10.ob2": "CPU, 메모리, 커널이 같기 때문",
        "h99.a": "CDK 스택만 지우면 남는 스택 밖의 리소스",
        "h99.b": "리소스마다 따로 있는 삭제 명령",
        "h99.cdk": "CDK 스택 삭제", "h99.cdks": "cdk destroy",
        "h99.r1": "클러스터, 노드 그룹, VPC, NAT gateway", "h99.r2": "AMI와 snapshot, ECR 이미지",
        "h99.r3": "HyperPod의 S3 버킷, IAM 역할", "h99.r4": "데모 사이트 stack",
        "h99.r5": "CDK bootstrap 스택 (CDKToolkit)",
        "h99.del": "함께 삭제", "h99.left": "남는 리소스",
        "h99.c1": "08_cleanup.sh", "h99.c1s": "--images면 ECR까지",
        "h99.c3": "hyperpod/delete.sh", "h99.c4": "demo/teardown.sh", "h99.c5": "직접 삭제",
        "h99.e1": "클러스터 이름 입력", "h99.e2": "ami, images 입력", "h99.e3": "HyperPod 이름, bucket 입력",
        "h99.e4": "stack 이름 입력", "h99.e5": "더 쓰지 않을 계정만",
    },
    "en": {
        "h07.a": "Where a days-long run and HyperPod nodes get stuck",
        "h07.b": "HyperPod recovery and B2 grading workers",
        "h07.e1": "GPU node fails", "h07.e1s": "in a days-long on-policy run",
        "h07.e2": "Generation or sandbox pool", "h07.e2s": "hangs",
        "h07.e3": "Sandbox on a HyperPod node", "h07.e3s": "gVisor GPU pool",
        "h07.a1e": "someone replaces the node", "h07.a1o": "someone restarts the job",
        "h07.a1os": "waits for a human",
        "h07.a2e": "process still alive", "h07.a2o": "training makes no progress",
        "h07.a2os": "looks healthy from outside",
        "h07.a3e": "default driver 595.112.07", "h07.a3o": "gVisor cannot run", "h07.a3os": "driver not in the nvproxy list",
        "h07.b1e": "NodeRecovery: Automatic", "h07.b1o": "node rebooted or replaced",
        "h07.b1os": "training operator restarts the job",
        "h07.b2e": "hang detection on log patterns", "h07.b2o": "job restarted on a hang",
        "h07.b2os": "elastic agent and training operator",
        "h07.b3e": "install 580.178.04 and reboot", "h07.b3o": "gVisor pool runs",
        "h07.b3os": "sandbox-only instance group (B2)",
        "h08.a": "Two pools on different GPUs side by side",
        "h08.b": "A pair on the same node, image and goldens",
        "h08.h": "Benchmark harness", "h08.ha": "relu_bias_triton", "h08.hb": "relu_bias_torch_only",
        "h08.p1a": "gVisor pool", "h08.p1as": "g5.xlarge, A10G",
        "h08.p2a": "Kata QEMU pool", "h08.p2as": "g4dn.metal, T4",
        "h08.p1b": "Kata CLH CPU pool", "h08.p1bs": "Cloud Hypervisor",
        "h08.p2b": "Kata QEMU CPU pool", "h08.p2bs": "QEMU",
        "h08.node": "same c8i.2xlarge node",
        "h08.d": "Difference", "h08.ds": "of the two pools",
        "h08.bad": "runtime + GPU share", "h08.bad_sub": "cannot be separated",
        "h08.good": "From RuntimeClass", "h08.good_sub": "hypervisor, podFixed",
        "h09.a": "A live demo, and static hosting set up wrong",
        "h09.b": "Replayed record, private bucket, text-only page",
        "h09.v": "Visitor", "h09.vs": "on the internet",
        "h09.r": "Strings in the record", "h09.rs": "errors, policy violations",
        "h09.t1": "GPU sandbox", "h09.t1a": "billed while it is up", "h09.t1b": "needed only to record",
        "h09.t2": "S3 bucket", "h09.t2s": "static files and record",
        "h09.t3": "Demo page", "h09.t3s": "visitor browser",
        "h09.a1": "live demo: API open to the internet",
        "h09.a2": "public bucket, website endpoint: bypasses CloudFront",
        "h09.a3": "inserted as HTML, it runs as script",
        "h09.b1": "replay a record: visitors reach only CloudFront",
        "h09.b2": "OAC, AWS:SourceArn: direct access 403",
        "h09.b3": "inserted as text only, CSP: own origin",
        "h10.a": "Scenario A: needs GPU nodes to start",
        "h10.b": "Scenario C: three runtimes on one c8i.2xlarge",
        "h10.qa": "G and VT quota", "h10.qas": "0 in many accounts",
        "h10.qb": "Standard quota", "h10.qbs": "no G and VT quota",
        "h10.ok": "approved", "h10.zero": "0",
        "h10.w": "Awaiting approval", "h10.ws": "cannot start",
        "h10.sa": "Scenario A", "h10.sa1": "about 3.42 USD per hour", "h10.sa2": "over 11 USD with Kata GPU",
        "h10.sb": "Scenario C", "h10.sb1": "about 0.57 USD per hour", "h10.sb2": "a sixth of A (estimate)",
        "h10.pa1": "gVisor pool", "h10.pa1s": "g5.xlarge, A10G",
        "h10.pa3": "Kata GPU pool", "h10.pa3s": "g4dn.metal, T4",
        "h10.pb1": "gVisor pool", "h10.pb1s": "runsc, systrap",
        "h10.pb2": "Kata CLH pool", "h10.pb2s": "Cloud Hypervisor",
        "h10.pb3": "Kata QEMU pool", "h10.pb3s": "QEMU VM",
        "h10.node": "one c8i.2xlarge",
        "h10.oa": "runtime effect", "h10.oa1": "hard to isolate", "h10.oa2": "nodes and GPUs differ",
        "h10.ob": "differences easier", "h10.ob1": "to pin on the runtime", "h10.ob2": "same CPU, memory, kernel",
        "h99.a": "Deleting only the CDK stack leaves what is outside it",
        "h99.b": "A delete command for each thing you created",
        "h99.cdk": "Delete the CDK stack", "h99.cdks": "cdk destroy",
        "h99.r1": "Cluster, node groups, VPC, NAT gateway", "h99.r2": "AMIs and snapshots, ECR images",
        "h99.r3": "HyperPod S3 bucket, IAM role", "h99.r4": "Demo site stack",
        "h99.r5": "CDK bootstrap stack (CDKToolkit)",
        "h99.del": "deleted with it", "h99.left": "remains",
        "h99.c1": "08_cleanup.sh", "h99.c1s": "--images: ECR too",
        "h99.c3": "hyperpod/delete.sh", "h99.c4": "demo/teardown.sh", "h99.c5": "Delete by hand",
        "h99.e1": "type the cluster name", "h99.e2": "type ami, images", "h99.e3": "type HyperPod name, bucket",
        "h99.e4": "type the stack name", "h99.e5": "only for an account you retire",
    },
}


def card(fig: Figure, x, y, w, h, label, subs, *, icon=None, fill=GREY_FILL, stroke=MUTED_STROKE, color=INK,
         gid=None):
    """A tall box with a name and two short lines; figlib's box holds one. Offsets match figlib's tall box."""
    fig.rect(x, y, w, h, fill=fill, stroke=stroke, gid=gid)
    shift = 8.5 * (len(subs) - 1)
    cy = y + h / 2
    if icon:
        fig.icon(icon, x + w / 2 - 14, cy - 50 - shift, 28, color)
        cy += 16
    lines = [(label, SIZE)] + [(s, SMALL) for s in subs]
    for i, (s, size) in enumerate(lines):
        fig.text(x + w / 2, cy - 3 - shift + 17 * i, s, size=size, color=color)
    need = max(text_width(s, size) for s, size in lines) + 16
    assert need <= w, f"label too wide for card {gid or label!r}: {need:.0f} > {w}"


def handson_07(lang: str) -> Figure:
    """docs/handson/scenarios/b/b1.md: node failure, a silent hang and the HyperPod AMI driver, and what HyperPod adds."""
    t = T[lang]
    fig = Figure(760, 540)
    ex, ew, ox, ow = 16, 230, 494, 250
    events = (("cpu", "e1"), ("hourglass", "e2"), ("container", "e3"))
    outcome_icons = {"a": ("person", "eye", "alert"), "b": ("sync", "sync", "check-circle")}
    for p, (oy, letter) in enumerate(((0, "a"), (272, "b"))):
        fig.panel(16, oy + 26, letter, t[f"h07.{letter}"])
        top = oy + 52
        for i, (ico, e) in enumerate(events):
            y = top + i * 72
            cy = y + 28
            k = f"h07.{letter}{i + 1}"
            fig.box(ex, y, ew, 56, t[f"h07.{e}"], t[f"h07.{e}s"], icon=ico, gid=f"n:{e}-{letter}")
            col = RED if p == 0 else ACCENT
            fig.arrow([(ex + ew, cy), (ox - 2, cy)], color=col, label=t[k + "e"],
                      label_at=((ex + ew + ox) / 2, cy - 8))
            fig.box(ox, y, ow, 56, t[k + "o"], t[k + "os"], icon=outcome_icons[letter][i],
                    fill=RED_FILL if p == 0 else ACCENT_FILL, stroke=col, color=RED if p == 0 else INK,
                    gid=f"n:outcome{i + 1}-{letter}")
    return fig


def handson_08(lang: str) -> Figure:
    """docs/handson/benchmarks/index.md: gVisor on A10G vs Kata QEMU on T4 mixes runtime and GPU; the fixed c8i pair does not."""
    t = T[lang]
    fig = Figure(760, 556)
    hx, hw, px, pw, dx, dw, ox, ow = 16, 140, 204, 180, 428, 140, 604, 140
    for p, (oy, letter) in enumerate(((0, "a"), (282, "b"))):
        fig.panel(16, oy + 26, letter, t[f"h08.{letter}"])
        top = oy + 72
        mid, y1, y2 = top + 93, top + 28, top + 158
        if p == 1:
            fig.container(px - 12, top - 30, pw + 24, 228, t["h08.node"], icon="server", stroke=ACCENT,
                          color=ACCENT, bold=True)
        fig.box(hx, top, hw, 186, t["h08.h"], t[f"h08.h{letter}"], icon="beaker", gid=f"n:harness-{letter}")
        for yy, k in ((y1, "p1"), (y2, "p2")):
            fig.arrow([(hx + hw, yy), (px - 2, yy)])
            fig.box(px, yy - 28, pw, 56, t[f"h08.{k}{letter}"], t[f"h08.{k}{letter}s"], icon="container",
                    gid=f"n:{k}-{letter}")
            fig.arrow([(px + pw, yy), (dx - 2, yy)])
        fig.box(dx, top, dw, 186, t["h08.d"], t["h08.ds"], icon="diff", gid=f"n:diff-{letter}")
        if p == 0:
            fig.arrow([(dx + dw, mid), (ox - 2, mid)], color=RED)
            fig.box(ox, mid - 52, ow, 104, t["h08.bad"], t["h08.bad_sub"], icon="alert", fill=RED_FILL,
                    stroke=RED, color=RED, gid="n:outcome-a")
        else:
            fig.arrow([(dx + dw, mid), (ox - 2, mid)], color=ACCENT)
            fig.box(ox, mid - 52, ow, 104, t["h08.good"], t["h08.good_sub"], icon="check-circle",
                    fill=ACCENT_FILL, stroke=ACCENT, gid="n:outcome-b")
    return fig


def handson_09(lang: str) -> Figure:
    """docs/reference/demo_site: live demo, bucket bypass and HTML injection, and replay, OAC and text-only insert."""
    t = T[lang]
    fig = Figure(760, 516)
    lx, lw, rx, rw = 16, 196, 544, 200
    targets = (("h09.t1", "cpu"), ("h09.t2", "database"), ("h09.t3", "browser"))
    for p, (oy, letter) in enumerate(((0, "a"), (262, "b"))):
        fig.panel(16, oy + 26, letter, t[f"h09.{letter}"])
        top = oy + 52
        fig.box(lx, top, lw, 118, t["h09.v"], t["h09.vs"], icon="person", gid=f"n:visitor-{letter}")
        fig.box(lx, top + 136, lw, 50, t["h09.r"], t["h09.rs"], icon="file-code", gid=f"n:record-{letter}")
        for i, (k, ico) in enumerate(targets):
            cy = top + 25 + i * 68
            sub = t[f"{k}{letter}"] if i == 0 else t[f"{k}s"]
            fig.box(rx, cy - 25, rw, 50, t[k], sub, icon=ico, gid=f"n:target{i + 1}-{letter}")
            label = t[f"h09.{letter}{i + 1}"]
            if p == 0:
                fig.arrow([(lx + lw, cy), (rx - 2, cy)], color=RED, label=label, label_at=((lx + lw + rx) / 2, cy - 8))
            elif i < 2:
                fig.line([(lx + lw, cy), (rx - 58, cy)], color=INK)
                fig.block(rx - 56, cy)
                fig.text((lx + lw + rx - 58) / 2, cy - 8, label, size=SMALL)
            else:
                fig.arrow([(lx + lw, cy), (rx - 2, cy)], color=ACCENT, label=label,
                          label_at=((lx + lw + rx) / 2, cy - 8))
    return fig


def handson_10(lang: str) -> Figure:
    """docs/handson/scenarios/c/index.md: GPU quota, cost and mismatched nodes in scenario A vs one c8i node in scenario C."""
    t = T[lang]
    fig = Figure(760, 572)
    qx, qw, sx, sw, px, pw, ox, ow = 16, 128, 210, 166, 418, 118, 576, 168
    for p, (oy, letter) in enumerate(((0, "a"), (288, "b"))):
        fig.panel(16, oy + 26, letter, t[f"h10.{letter}"])
        top = oy + 72
        slots = [top + 25 + i * 68 for i in range(3)]
        fig.box(qx, top, qw, 50, t[f"h10.q{letter}"], t[f"h10.q{letter}s"], gid=f"n:quota-{letter}")
        if p == 0:
            fig.arrow([(qx + qw, slots[0]), (sx - 2, slots[0])], label=t["h10.ok"],
                      label_at=((qx + qw + sx) / 2, slots[0] - 8))
            fig.arrow([(qx + qw / 2, top + 50), (qx + qw / 2, top + 134)], color=RED, label=t["h10.zero"],
                      label_at=(qx + qw / 2 + 12, top + 97))
            fig.box(qx, top + 136, qw, 50, t["h10.w"], t["h10.ws"], fill=RED_FILL, stroke=RED, color=RED,
                    gid="n:wait-a")
        else:
            fig.arrow([(qx + qw, slots[0]), (sx - 2, slots[0])])
            fig.container(px - 12, top - 30, pw + 24, 228, t["h10.node"], icon="server", stroke=ACCENT,
                          color=ACCENT, bold=True)
        card(fig, sx, top, sw, 186, t[f"h10.s{letter}"], [t[f"h10.s{letter}1"], t[f"h10.s{letter}2"]],
             icon="cloud", gid=f"n:scenario-{letter}")
        pools = (1, 3) if p == 0 else (1, 2, 3)
        for n in pools:
            yy = slots[n - 1]
            key = f"h10.p{letter}{n}"
            fig.arrow([(sx + sw, yy), (px - 2, yy)])
            fig.box(px, yy - 25, pw, 50, t[key], t[key + "s"], gid=f"n:pool{n}-{letter}")
            fig.arrow([(px + pw, yy), (ox - 2, yy)], color=RED if p == 0 else ACCENT)
        if p == 0:
            card(fig, ox, top, ow, 186, t["h10.oa"], [t["h10.oa1"], t["h10.oa2"]], icon="alert", fill=RED_FILL,
                 stroke=RED, color=RED, gid="n:outcome-a")
        else:
            card(fig, ox, top, ow, 186, t["h10.ob"], [t["h10.ob1"], t["h10.ob2"]], icon="check-circle",
                 fill=ACCENT_FILL, stroke=ACCENT, gid="n:outcome-b")
    return fig


def handson_99(lang: str) -> Figure:
    """docs/handson/cleanup.md: what deleting the CDK stack leaves behind, and the command that removes each part."""
    t = T[lang]
    fig = Figure(760, 572)
    lx, lw, rx, rw, rh, pitch = 16, 200, 448, 296, 36, 46
    rows = (("h99.r1", "server"), ("h99.r2", "package"), ("h99.r3", "database"), ("h99.r4", "browser"),
            ("h99.r5", "stack"))
    for p, (oy, letter) in enumerate(((0, "a"), (288, "b"))):
        fig.panel(16, oy + 26, letter, t[f"h99.{letter}"])
        top = oy + 50
        cys = [top + rh / 2 + i * pitch for i in range(5)]
        for i, (k, ico) in enumerate(rows):
            fig.box(rx, cys[i] - rh / 2, rw, rh, t[k], icon=ico, gid=f"n:res{i + 1}-{letter}")
        if p == 0:
            fig.box(lx, top, lw, 4 * pitch + rh, t["h99.cdk"], t["h99.cdks"], icon="trash", gid="n:cdk-a")
            fig.arrow([(lx + lw, cys[0]), (rx - 2, cys[0])], label=t["h99.del"],
                      label_at=((lx + lw + rx) / 2, cys[0] - 8))
            for cy in cys[1:]:
                fig.line([(lx + lw, cy), (rx - 58, cy)], color=RED, dash="5 4")
                fig.block(rx - 56, cy)
                fig.text((lx + lw + rx - 58) / 2, cy - 8, t["h99.left"], size=SMALL, color=RED)
        else:
            fig.box(lx, top, lw, pitch + rh, t["h99.c1"], t["h99.c1s"], icon="terminal", gid="n:cleanup-b")
            for i, k in ((2, "h99.c3"), (3, "h99.c4"), (4, "h99.c5")):
                fig.box(lx, cys[i] - rh / 2, lw, rh, t[k], icon="person" if i == 4 else "terminal",
                        gid=f"n:cmd{i + 1}-b")
            for i in range(5):
                manual = i == 4
                fig.arrow([(lx + lw, cys[i]), (rx - 2, cys[i])], color=MUTED_STROKE if manual else ACCENT,
                          dash="5 4" if manual else None, label=t[f"h99.e{i + 1}"],
                          label_at=((lx + lw + rx) / 2, cys[i] - 8))
    return fig


FIGURES = {
    "handson-07_hyperpod": handson_07,
    "handson-08_benchmark": handson_08,
    "handson-09_demo_site": handson_09,
    "handson-10_cpu_only": handson_10,
    "handson-99_cleanup": handson_99,
}
