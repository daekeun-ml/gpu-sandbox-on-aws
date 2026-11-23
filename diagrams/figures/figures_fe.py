"""Production section schematics (00 to 04): five Pain point figures and three main figures.

Every box, label and edge comes from the page named in each docstring (Korean page and its .en.md).
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from figlib import (ACCENT, ACCENT_FILL, CONTAINER, GREY_FILL, INK, MUTED_STROKE, RED, RED_FILL, SIZE, SMALL,
                    Figure, text_width)

LINE = 17      # baseline pitch of the lines inside one box (matches figlib's label and sub line)
API_DASH = "5 4"

T = {
    "ko": {
        # 00 Pain point
        "p00.a": "핸즈온 구성을 그대로 확장할 때",
        "p00.b": "Production: gateway 한곳에서 선택, 노드와 키 자동화",
        "p00.callers": "trainer 프로세스", "p00.callers_sub": "TRL rank, veRL worker",
        "p00.verl": "veRL reward worker", "p00.verl_sub": "샘플 단위 채점",
        "p00.pod": "샌드박스 pod A", "p00.gw": "sandbox gateway",
        "p00.pick": "각자 빈 pod 판단", "p00.per_sample": "샘플마다 따로 routing",
        "p00.only_gw": "gateway만 호출", "p00.gkey": "group_key와 함께",
        "p00.ng": "노드 그룹 desired", "p00.ng_sub": "수동 조정",
        "p00.np": "Karpenter NodePool", "p00.np_sub": "0부터, limits 안에서",
        "p00.sync": "scripts/ops/sync_jwks.sh", "p00.sync_sub": "수동 실행",
        "p00.cron": "jwks-sync CronJob", "p00.cron_sub": "매시 17분",
        "p00.oa1": "503 재시도 증가", "p00.oa1s": "같은 pod로 몰리는 요청",
        "p00.oa2": "섞일 수 있는 v1과 v2", "p00.oa2s": "한 group 안에서",
        "p00.oa3": "부하와 무관한 GPU 노드", "p00.oa3s": "계속 실행되거나 늦게 증설",
        "p00.oa4": "서명 키가 바뀌면", "p00.oa4s": "새 키로 서명한 토큰 거부 (fail closed)",
        "p00.ob1": "pod마다 평가 1건", "p00.ob1s": "gateway가 고르는 빈 pod",
        "p00.ob2": "batch나 group마다 한 버전", "p00.ob2s": "TRL 스냅샷, veRL group_key pin",
        "p00.ob3": "Karpenter 노드는 자동 증감", "p00.ob3s": "CDK 노드 그룹은 직접 축소",
        "p00.ob4": "서명 키 회전 반영", "p00.ob4s": "ConfigMap을 자동 갱신",
        # 00 overview
        "o00.tr": "rl-trainer: trainer NodePool (g6e, p5) 또는 HyperPod 인스턴스 그룹",
        "o00.trl": "TRL ranks", "o00.trl_sub": "Job",
        "o00.verl": "veRL Ray workers", "o00.verl_sub": "RayCluster",
        "o00.gwns": "sandbox-gateway: system 노드",
        "o00.gw": ["sandbox gateway", "TokenReview, routing, group pin", "pod당 요청 1건, recycling"],
        "o00.jwks": "jwks-sync", "o00.jwks_sub": "CronJob",
        "o00.api": "Kubernetes API",
        "o00.sbns": "sandbox namespace",
        "o00.warm": "warm placeholder", "o00.warm_sub": "metal 한 대 확보",
        "o00.qemu": "sandbox-kata-qemu-v1", "o00.qemu_sub": "kata-qemu-nvidia-gpu",
        "o00.gvisor": "sandbox-gvisor-v1, v2", "o00.gvisor_sub": "gvisor (runsc, nvproxy)",
        "o00.clh": "sandbox-kata-clh-cpu-v1", "o00.clh_sub": "kata-clh (장치 없음)",
        "o00.npns": "Karpenter NodePool (클러스터 범위)",
        "o00.np_gpu": "sandbox-kata-gpu", "o00.np_gpu_sub": "g4dn.metal",
        "o00.np_gv": "sandbox-gvisor", "o00.np_gv_sub": "g5.xlarge, g5.2xlarge",
        "o00.np_cpu": "sandbox-kata-cpu", "o00.np_cpu_sub": "c8i, m8i, r8i",
        "o00.aud_gw": "aud gpu-sandbox-gateway", "o00.aud_sb": "aud gpu-sandbox",
        "o00.e_gw": ["TokenReview,", "draining pod 삭제"], "o00.e_jwks": ["JWKS 읽기,", "ConfigMap patch"],
        # 01 Pain point
        "p01.a": "수요가 생긴 뒤에 시작하는 노드, 자동으로 바뀌는 AMI",
        "p01.b": "metal 한 대 미리 확보, AMI와 gVisor 함께 고정",
        "p01.metal": "metal 노드 (sandbox-kata-gpu)", "p01.gv": "gVisor 노드 (sandbox-gvisor)",
        "p01.arrive": "reward batch 도착", "p01.arrive_sub": "샌드박스 pod를 배치할 노드 필요",
        "p01.boot": "g4dn.metal 부팅", "p01.boot_sub": "kata-deploy, vfio-pci 바인딩 수 분",
        "p01.wait": "그동안 대기하는 batch", "p01.wait_sub": "수요가 생긴 뒤 시작하는 느린 노드",
        "p01.preempt": "warm placeholder 선점", "p01.preempt_sub": "우선순위 -10, 즉시 선점되어 종료",
        "p01.ready": "이미 실행 중인 노드에 배치", "p01.ready_sub": "Karpenter가 추가하는 예비 노드",
        "p01.auto": "AMI 자동 갱신", "p01.auto_sub": "al2023@latest, drift 교체",
        "p01.unknown": "nvproxy가 지원하지 않는 드라이버", "p01.unknown_sub": "GPU 초기화 실패",
        "p01.zero": "샌드박스 Ready 불가", "p01.zero_sub": "pool 용량 0",
        "p01.pin": "AMI 버전 고정", "p01.pin_sub": "al2023@v20261107",
        "p01.ci": "CI에서 지원 확인", "p01.ci_sub": "nvproxy list-supported-drivers",
        "p01.raise": "통과할 때만 함께 승격", "p01.raise_sub": "AMI와 GVISOR_RELEASE",
        # 02 Pain point
        "p02.a": "하드닝하지 않은 runc pod",
        "p02.b": "계층마다 다른 경로를 막거나 줄임",
        "p02.code": "후보 코드", "p02.code_a": "runc pod", "p02.code_b": "gVisor 또는 Kata",
        "p02.pod": "샌드박스 pod",
        "p02.r1": "호스트 커널", "p02.r1s": "NVIDIA 드라이버",
        "p02.r2": "ServiceAccount token", "p02.r2s": "시크릿",
        "p02.r3": "자기 노드 IP", "p02.r3s": "노드의 로컬 서비스",
        "p02.r4": "다음 평가", "p02.r4s": "같은 pod에서 이어서 실행",
        "p02.a1": "그대로 공유", "p02.a2": "읽기", "p02.a3": "NetworkPolicy와 관계없이 허용",
        "p02.a4": "남은 프로세스, 캐시, GPU 상태",
        "p02.b1": ["gVisor Sentry 또는 Kata VM", "호스트 드라이버를 공유하는 gVisor"],
        "p02.b2": "토큰, 시크릿을 넣지 않는 설정", "p02.b3": "노드 가드, readiness 확인",
        "p02.b4": ["프로세스 정리, 요청별 캐시로 줄임", "v1은 pod 재활용 꺼짐"],
        # 02 threat model
        "o02.layers": [
            ("globe", "네트워크", "기본 거부, gateway만 ingress"),
            ("server", "노드", "전용 taint, 노드 가드, IMDS hop 1"),
            ("shield-lock", "런타임", "gVisor Sentry 또는 Kata VM"),
            ("container", "pod", "non-root, 읽기 전용 root FS, capability 없음, 토큰 없음"),
            ("terminal", "자식 프로세스", "env allowlist, 요청별 캐시, timeout"),
        ],
        "o02.code": "후보 코드", "o02.code_sub": "학습 중인 policy가 만든 코드",
        # 03 Pain point
        "p03.a": "호출자마다 pod 선택, 샘플마다 따로 채점",
        "p03.b": "in-flight와 버전을 관리하는 gateway 하나",
        "p03.trl": "TRL rank 0", "p03.verl": "veRL reward worker",
        "p03.s1": "group 17 샘플 1", "p03.s2": "group 17 샘플 2", "p03.s2_sub": "routing 전환 뒤",
        "p03.podA": "샌드박스 pod A", "p03.podA_bad": "503, 재시도", "p03.podB": "샌드박스 pod B",
        "p03.v1": "v1로 채점", "p03.v2": "v2로 채점", "p03.v2_sub": "같은 group, 다른 버전",
        "p03.v1pin": "v1로 채점", "p03.v1pin_sub": "group pin, TTL 900초",
        "p03.gw": ["sandbox gateway", "in-flight를 한곳에서 집계", "group_key pin"],
        "p03.free": "빈 pod로 판단", "p03.per_sample": "샘플마다 routing",
        "p03.one": "동시 1건", "p03.pinned": "첫 샘플의 버전",
        # 04 Pain point
        "p04.a": "같은 프로세스에서 채점: 더 빠른 커널 없이 높은 reward",
        "p04.b": "자식 프로세스 분리와 측정 절차 고정",
        "p04.proc": "채점 코드와 같은 Python 프로세스", "p04.child": "신뢰하지 않는 자식 프로세스",
        "p04.harness": "harness",
        "p04.code": "후보 코드", "p04.code_sub": "ModelNew",
        "p04.r1": "timer", "p04.r1s": "시간 측정",
        "p04.r2": "reference, 비교 함수", "p04.r2s": "정답과 판정",
        "p04.r3": "측정 구간", "p04.r3s": "timed iteration",
        "p04.a1": "바꿔치기", "p04.a2": "바꿔치기", "p04.a3": "추가 stream, 캐시, lazy 출력",
        "p04.b1": "정적 정책: 속성 대입 거부", "p04.b2": "정답 출력과 판정은 부모가",
        "p04.b3": "synchronize, 새 입력, checksum",
        # 04 two-process
        "o04.server": "샌드박스 서버 (uvicorn)", "o04.server_sub": "torch import 없음",
        "o04.spawn": "요청마다 새 프로세스",
        "o04.parent": "신뢰하는 부모: evaluate.py", "o04.child": "신뢰하지 않는 자식: runner.py",
        "o04.s1": "1. 정적 정책 (AST)", "o04.s1s": "check_source",
        "o04.s2": "2. 요청마다 새 seed", "o04.s2s": "정확성 seed, timing seed",
        "o04.s3": "3. 후보 ModelNew 실행", "o04.s3s": "seed별 출력 저장",
        "o04.s3b": "timing, checksum", "o04.s3bs": "runner.json 작성",
        "o04.s4": "4. reference 출력과 비교", "o04.s4s": "같은 seed, weights_only=True로 읽기",
        "o04.s5": "5. reference timing", "o04.s5s": "timed 출력 checksum 비교",
        "o04.s6": "6. verdict JSON 작성", "o04.s6s": "runner.py가 끝난 뒤 마지막에",
        "o04.none": "자식에게 없는 것", "o04.none_sub": "reference 출력, 토큰 같은 pod env",
        "o04.out_top": ["후보 코드, seed"], "o04.out_bot": ["env allowlist,", "새 session, timeout"],
        "o04.in_top": ["seed별 출력,", "runner.json"], "o04.in_bot": ["runner.json은", "1 MiB 제한, 타입 검사"],
    },
    "en": {
        "p00.a": "The hands-on setup scaled up as is",
        "p00.b": "Production: one gateway picks, nodes and keys follow automatically",
        "p00.callers": "trainer processes", "p00.callers_sub": "TRL ranks, veRL workers",
        "p00.verl": "veRL reward worker", "p00.verl_sub": "scores per sample",
        "p00.pod": "sandbox pod A", "p00.gw": "sandbox gateway",
        "p00.pick": "picks a pod alone", "p00.per_sample": "routing per sample",
        "p00.only_gw": "gateway only", "p00.gkey": "with group_key",
        "p00.ng": "node group desired", "p00.ng_sub": "set by hand",
        "p00.np": "Karpenter NodePool", "p00.np_sub": "from zero, within limits",
        "p00.sync": "scripts/ops/sync_jwks.sh", "p00.sync_sub": "run by hand",
        "p00.cron": "jwks-sync CronJob", "p00.cron_sub": "hourly at :17",
        "p00.oa1": "more 503 retries", "p00.oa1s": "requests pile onto one pod",
        "p00.oa2": "v1 and v2 can mix", "p00.oa2s": "inside one group",
        "p00.oa3": "GPU nodes ignore load", "p00.oa3s": "idle, or grow too late",
        "p00.oa4": "signing key changes", "p00.oa4s": "new-key tokens rejected",
        "p00.ob1": "one evaluation per pod", "p00.ob1s": "the gateway picks free pods",
        "p00.ob2": "one version per batch or group", "p00.ob2s": "TRL snapshot, veRL group_key pin",
        "p00.ob3": "Karpenter nodes follow load", "p00.ob3s": "CDK node groups: by hand",
        "p00.ob4": "follows key rotation", "p00.ob4s": "patches the ConfigMap",
        "o00.tr": "rl-trainer: trainer NodePool (g6e, p5) or HyperPod instance group",
        "o00.trl": "TRL ranks", "o00.trl_sub": "Job",
        "o00.verl": "veRL Ray workers", "o00.verl_sub": "RayCluster",
        "o00.gwns": "sandbox-gateway: system nodes",
        "o00.gw": ["sandbox gateway", "TokenReview, routing, group pins", "one request per pod, recycling"],
        "o00.jwks": "jwks-sync", "o00.jwks_sub": "CronJob",
        "o00.api": "Kubernetes API",
        "o00.sbns": "sandbox namespace",
        "o00.warm": "warm placeholder", "o00.warm_sub": "holds a metal node",
        "o00.qemu": "sandbox-kata-qemu-v1", "o00.qemu_sub": "kata-qemu-nvidia-gpu",
        "o00.gvisor": "sandbox-gvisor-v1, v2", "o00.gvisor_sub": "gvisor (runsc, nvproxy)",
        "o00.clh": "sandbox-kata-clh-cpu-v1", "o00.clh_sub": "kata-clh (no devices)",
        "o00.npns": "Karpenter NodePools (cluster scope)",
        "o00.np_gpu": "sandbox-kata-gpu", "o00.np_gpu_sub": "g4dn.metal",
        "o00.np_gv": "sandbox-gvisor", "o00.np_gv_sub": "g5.xlarge, g5.2xlarge",
        "o00.np_cpu": "sandbox-kata-cpu", "o00.np_cpu_sub": "c8i, m8i, r8i",
        "o00.aud_gw": "aud gpu-sandbox-gateway", "o00.aud_sb": "aud gpu-sandbox",
        "o00.e_gw": ["TokenReview,", "delete draining pods"], "o00.e_jwks": ["read JWKS,", "patch ConfigMap"],
        "p01.a": "Nodes started on demand, AMI updated automatically",
        "p01.b": "One metal node kept warm, AMI and gVisor pinned together",
        "p01.metal": "metal node (sandbox-kata-gpu)", "p01.gv": "gVisor node (sandbox-gvisor)",
        "p01.arrive": "reward batch arrives", "p01.arrive_sub": "sandbox pods need room",
        "p01.boot": "g4dn.metal boots", "p01.boot_sub": "kata-deploy, vfio-pci: minutes",
        "p01.wait": "batch waits meanwhile", "p01.wait_sub": "slow node started late",
        "p01.preempt": "warm placeholder preempted", "p01.preempt_sub": "priority -10, steps aside",
        "p01.ready": "runs on a ready node", "p01.ready_sub": "Karpenter adds a spare",
        "p01.auto": "automatic AMI update", "p01.auto_sub": "al2023@latest, drift",
        "p01.unknown": "driver unknown to nvproxy", "p01.unknown_sub": "GPU initialization fails",
        "p01.zero": "sandboxes never Ready", "p01.zero_sub": "pool capacity 0",
        "p01.pin": "AMI version pinned", "p01.pin_sub": "al2023@v20261107",
        "p01.ci": "CI checks support", "p01.ci_sub": "nvproxy list-supported-drivers",
        "p01.raise": "raised together on pass", "p01.raise_sub": "AMI and GVISOR_RELEASE",
        "p02.a": "An unhardened runc pod",
        "p02.b": "Each layer stops or narrows one path",
        "p02.code": "candidate code", "p02.code_a": "runc pod", "p02.code_b": "gVisor or Kata",
        "p02.pod": "sandbox pod",
        "p02.r1": "host kernel", "p02.r1s": "NVIDIA driver",
        "p02.r2": "ServiceAccount token", "p02.r2s": "secrets",
        "p02.r3": "own node IP", "p02.r3s": "node-local services",
        "p02.r4": "next evaluation", "p02.r4s": "in the same pod",
        "p02.a1": "shared directly", "p02.a2": "reads", "p02.a3": "allowed regardless of NetworkPolicy",
        "p02.a4": "leftover processes, caches, GPU state",
        "p02.b1": ["gVisor Sentry or Kata VM", "gVisor shares the host driver"],
        "p02.b2": "no token, no secrets mounted", "p02.b3": "node guard, readiness check",
        "p02.b4": ["narrowed by reaping, per-request caches", "pod recycling off in v1"],
        "o02.layers": [
            ("globe", "network", "default deny, gateway-only ingress"),
            ("server", "node", "dedicated taint, node guard, IMDS hop 1"),
            ("shield-lock", "runtime", "gVisor Sentry or Kata VM"),
            ("container", "pod", "non-root, read-only root FS, no capabilities, no token"),
            ("terminal", "child process", "env allowlist, per-request caches, timeout"),
        ],
        "o02.code": "candidate code", "o02.code_sub": "written by the policy in training",
        "p03.a": "Callers and samples decide alone",
        "p03.b": "One gateway tracks in-flight requests and versions",
        "p03.trl": "TRL rank 0", "p03.verl": "veRL reward worker",
        "p03.s1": "group 17 sample 1", "p03.s2": "group 17 sample 2", "p03.s2_sub": "after routing switch",
        "p03.podA": "sandbox pod A", "p03.podA_bad": "503, retry", "p03.podB": "sandbox pod B",
        "p03.v1": "scored by v1", "p03.v2": "scored by v2", "p03.v2_sub": "same group, other version",
        "p03.v1pin": "scored by v1", "p03.v1pin_sub": "group pin, TTL 900 s",
        "p03.gw": ["sandbox gateway", "counts in-flight", "group_key pins"],
        "p03.free": "sees pod as free", "p03.per_sample": "routing per sample",
        "p03.one": "one at a time", "p03.pinned": "pinned version",
        "p04.a": "Scored in one process: high reward without a faster kernel",
        "p04.b": "Candidate in a child process, measurement fixed",
        "p04.proc": "same Python process as the scoring code", "p04.child": "untrusted child process",
        "p04.harness": "harness",
        "p04.code": "candidate code", "p04.code_sub": "ModelNew",
        "p04.r1": "timer", "p04.r1s": "measures time",
        "p04.r2": "reference, compare", "p04.r2s": "answer and verdict",
        "p04.r3": "timed window", "p04.r3s": "timed iterations",
        "p04.a1": "replaces", "p04.a2": "replaces", "p04.a3": "extra stream, caching, lazy outputs",
        "p04.b1": "static policy: no attribute writes", "p04.b2": "answers, verdicts in the parent",
        "p04.b3": "synchronize, new inputs, checksums",
        "o04.server": "Sandbox server (uvicorn)", "o04.server_sub": "never imports torch",
        "o04.spawn": "new process per request",
        "o04.parent": "Trusted parent: evaluate.py", "o04.child": "Untrusted child: runner.py",
        "o04.s1": "1. Static policy (AST)", "o04.s1s": "check_source",
        "o04.s2": "2. Fresh seeds per request", "o04.s2s": "correctness and timing seeds",
        "o04.s3": "3. Run the candidate ModelNew", "o04.s3s": "save outputs per seed",
        "o04.s3b": "Timing, checksums", "o04.s3bs": "write runner.json",
        "o04.s4": "4. Compare with reference outputs", "o04.s4s": "same seeds, read with weights_only=True",
        "o04.s5": "5. Reference timing", "o04.s5s": "compare timed output checksums",
        "o04.s6": "6. Write the verdict JSON", "o04.s6s": "last, after runner.py exits",
        "o04.none": "What the child never gets", "o04.none_sub": "reference outputs, tokens in pod env",
        "o04.out_top": ["candidate code, seeds"], "o04.out_bot": ["env allowlist,", "new session, timeout"],
        "o04.in_top": ["outputs per seed,", "runner.json"], "o04.in_bot": ["runner.json:", "1 MiB cap, type checks"],
    },
}


# ---- helpers (plain SVG appended to fig.parts; figlib stays untouched) ----

def mbox(fig: Figure, x, y, w, h, lines, *, fill=GREY_FILL, stroke=MUTED_STROKE, color=INK, gid=None):
    """A box with a name (13 px) and further short lines (12 px), centred as one block."""
    fig.rect(x, y, w, h, fill=fill, stroke=stroke, gid=gid)
    first = y + h / 2 + 5 - (len(lines) - 1) * LINE / 2
    for i, s in enumerate(lines):
        fig.text(x + w / 2, first + i * LINE, s, size=SIZE if i == 0 else SMALL, color=color)
    need = max(text_width(s, SIZE if i == 0 else SMALL) for i, s in enumerate(lines)) + 16
    assert need <= w, f"label too wide for box {gid or lines[0]!r}: {need:.0f} > {w}"
    assert (len(lines) - 1) * LINE + 2 * 14 <= h, f"box {gid or lines[0]!r} too short for {len(lines)} lines"


def texts(fig: Figure, x, y, lines, *, anchor="middle", pitch=15, color=INK):
    """Edge label of one or more 12 px lines; y is the baseline of the last line."""
    for i, s in enumerate(lines):
        fig.text(x, y - (len(lines) - 1 - i) * pitch, s, size=SMALL, anchor=anchor, color=color)


def dot(fig: Figure, x, y, r=3.5, color=INK):
    """A branch point on a connector."""
    fig.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')


def ring(fig: Figure, x, y, w, h, icon, name, rest, *, stroke=CONTAINER, color=INK):
    """An outline layer whose title is a bold name followed by its controls in the regular weight."""
    fig.rect(x, y, w, h, fill="none", stroke=stroke, width=1.2, rx=8)
    fig.icon(icon, x + 10, y + 7, 15, color)
    tx = x + 32
    fig.parts.append(f'<text x="{tx}" y="{y + 20}" font-size="{SMALL}" fill="{color}" text-anchor="start">'
                     f'<tspan font-weight="600">{escape(name)}</tspan>'
                     f'<tspan dx="8">{escape(rest)}</tspan></text>')
    need = 32 + text_width(name, SMALL, bold=True) + 8 + text_width(rest, SMALL) + 12
    assert need <= w, f"ring title too wide: {name!r} {need:.0f} > {w}"


def api_arrow(fig: Figure, points):
    fig.arrow(points, color=MUTED_STROKE, width=1.4, dash=API_DASH)


# ---- Pain point figures ----

def production_00(lang: str) -> Figure:
    """docs/production/00_architecture Pain point: callers pick pods alone, per-sample routing, nodes and
    ops/sync_jwks.sh by hand (a); the gateway, Karpenter NodePools and the jwks-sync CronJob from Why (b)."""
    t = T[lang]
    fig = Figure(760, 556)
    c1x, c1w, c2x, c2w, c3x, c3w = 16, 170, 316, 150, 540, 204
    pitch, bh = 54, 44
    for p, (oy, letter, title) in enumerate(((0, "a", t["p00.a"]), (278, "b", t["p00.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 56
        cy = [top + i * pitch + bh / 2 for i in range(4)]
        sources = ((t["p00.callers"], t["p00.callers_sub"]), (t["p00.verl"], t["p00.verl_sub"]),
                   (t["p00.ng"], t["p00.ng_sub"]) if p == 0 else (t["p00.np"], t["p00.np_sub"]),
                   (t["p00.sync"], t["p00.sync_sub"]) if p == 0 else (t["p00.cron"], t["p00.cron_sub"]))
        for i, (lab, sub) in enumerate(sources):
            if i == 0:
                fig.stack(c1x, cy[i] - bh / 2, c1w, bh, lab, sub, mark="xN", gid=f"n:src{i}-{letter}")
            else:
                fig.box(c1x, cy[i] - bh / 2, c1w, bh, lab, sub, gid=f"n:src{i}-{letter}")
        outs = ([("p00.oa1", "p00.oa1s"), ("p00.oa2", "p00.oa2s"), ("p00.oa3", "p00.oa3s"), ("p00.oa4", "p00.oa4s")]
                if p == 0 else
                [("p00.ob1", "p00.ob1s"), ("p00.ob2", "p00.ob2s"), ("p00.ob3", "p00.ob3s"), ("p00.ob4", "p00.ob4s")])
        for i, (k, ks) in enumerate(outs):
            if p == 0:
                fig.box(c3x, cy[i] - bh / 2, c3w, bh, t[k], t[ks], fill=RED_FILL, stroke=RED, color=RED,
                        gid=f"n:out{i}-a")
            else:
                fig.box(c3x, cy[i] - bh / 2, c3w, bh, t[k], t[ks], fill=ACCENT_FILL, stroke=ACCENT,
                        gid=f"n:out{i}-b")
        out_color = RED if p == 0 else ACCENT
        lab_left = (c1x + c1w + 6 + c2x) / 2
        if p == 0:
            fig.box(c2x, cy[0] - bh / 2, c2w, bh, t["p00.pod"], icon="container", gid="n:podA")
            fig.arrow([(c1x + c1w + 6, cy[0]), (c2x - 2, cy[0])], label=t["p00.pick"], label_at=(lab_left, cy[0] - 8))
            fig.arrow([(c2x + c2w, cy[0]), (c3x - 2, cy[0])], color=out_color)
            fig.arrow([(c1x + c1w, cy[1]), (c3x - 2, cy[1])], color=out_color, label=t["p00.per_sample"],
                      label_at=(c2x + c2w / 2, cy[1] - 8))
        else:
            gtop, gbot = cy[0] - bh / 2, cy[1] + bh / 2
            fig.box(c2x, gtop, c2w, gbot - gtop, t["p00.gw"], fill=ACCENT_FILL, stroke=ACCENT, gid="n:gateway")
            fig.arrow([(c1x + c1w + 6, cy[0]), (c2x - 2, cy[0])], label=t["p00.only_gw"],
                      label_at=(lab_left, cy[0] - 8))
            fig.arrow([(c1x + c1w, cy[1]), (c2x - 2, cy[1])], label=t["p00.gkey"], label_at=(lab_left, cy[1] - 8))
            fig.arrow([(c2x + c2w, cy[0]), (c3x - 2, cy[0])], color=out_color)
            fig.arrow([(c2x + c2w, cy[1]), (c3x - 2, cy[1])], color=out_color)
        for i in (2, 3):
            fig.arrow([(c1x + c1w, cy[i]), (c3x - 2, cy[i])], color=out_color)
    return fig


def production_01(lang: str) -> Figure:
    """docs/production/01_capacity_and_nodes Pain point: slow metal started on demand and an AMI update that
    nvproxy does not know (a); the warm placeholder and the AMI and gVisor pin with a CI gate (b)."""
    t = T[lang]
    fig = Figure(760, 516)
    xs, ws = (36, 286, 536), (204, 204, 192)
    bh = 48
    lanes_a = ((t["p01.metal"], "server", [("p01.arrive", "p01.arrive_sub"), ("p01.boot", "p01.boot_sub"),
                                        ("p01.wait", "p01.wait_sub")]),
               (t["p01.gv"], "server", [("p01.auto", "p01.auto_sub"), ("p01.unknown", "p01.unknown_sub"),
                                     ("p01.zero", "p01.zero_sub")]))
    lanes_b = ((t["p01.metal"], "server", [("p01.arrive", "p01.arrive_sub"), ("p01.preempt", "p01.preempt_sub"),
                                        ("p01.ready", "p01.ready_sub")]),
               (t["p01.gv"], "server", [("p01.pin", "p01.pin_sub"), ("p01.ci", "p01.ci_sub"),
                                     ("p01.raise", "p01.raise_sub")]))
    for p, (oy, letter, title, lanes) in enumerate(((0, "a", t["p01.a"], lanes_a), (260, "b", t["p01.b"], lanes_b))):
        fig.panel(16, oy + 26, letter, title)
        for li, (lane_title, icon, steps) in enumerate(lanes):
            ly = oy + 44 + li * 104
            fig.container(16, ly, 728, 92, lane_title, icon=icon)
            by = ly + 30
            for si, (k, ks) in enumerate(steps):
                last = si == 2
                kw = {}
                if last:
                    kw = (dict(fill=RED_FILL, stroke=RED, color=RED) if p == 0 else
                          dict(fill=ACCENT_FILL, stroke=ACCENT))
                fig.box(xs[si], by, ws[si], bh, t[k], t[ks], gid=f"n:{letter}{li}{si}", **kw)
                if si:
                    color = (RED if p == 0 else ACCENT) if last else INK
                    fig.arrow([(xs[si - 1] + ws[si - 1], by + bh / 2), (xs[si] - 2, by + bh / 2)], color=color)
    return fig


def production_02(lang: str) -> Figure:
    """docs/production/02_security Pain point: what candidate code in an unhardened runc pod reaches (a) and
    the layer from Why that stops each path (b); the gVisor driver caveat is residual risk 1 on the page."""
    t = T[lang]
    fig = Figure(760, 584)
    rows = [("p02.r1", "p02.r1s", "p02.a1", "p02.b1", "cpu"), ("p02.r2", "p02.r2s", "p02.a2", "p02.b2", "key"),
            ("p02.r3", "p02.r3s", "p02.a3", "p02.b3", "server"), ("p02.r4", "p02.r4s", "p02.a4", "p02.b4", "sync")]
    pitch, bh = 52, 44
    for p, (oy, letter, title) in enumerate(((0, "a", t["p02.a"]), (286, "b", t["p02.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 70
        span = 3 * pitch + bh
        if p == 1:
            fig.container(22, top - 30, 180, span + 44, t["p02.pod"], icon="shield-lock", stroke=ACCENT,
                          color=ACCENT, bold=True)
        fig.box(36, top, 152, span, t["p02.code"], t["p02.code_a"] if p == 0 else t["p02.code_b"], icon="code",
                fill=ACCENT_FILL if p == 1 else GREY_FILL, stroke=ACCENT if p == 1 else MUTED_STROKE,
                gid=f"n:code-{letter}")
        for i, (res, res_sub, act, layer, ico) in enumerate(rows):
            cy = top + bh / 2 + i * pitch
            fig.box(540, cy - bh / 2, 204, bh, t[res], t[res_sub], icon=ico, gid=f"n:res{i}-{letter}")
            if p == 0:
                fig.arrow([(188, cy), (538, cy)], color=RED, label=t[act], label_at=(363, cy - 8))
            elif i == 3:
                # Narrowed, not closed: the path stays, drawn muted and dashed with no stop mark.
                fig.arrow([(188, cy), (538, cy)], color=MUTED_STROKE, dash="5 4")
                texts(fig, 363, cy - 8, t[layer])
            else:
                fig.line([(188, cy), (468, cy)], color=INK)
                fig.block(470, cy)
                lab = t[layer] if isinstance(t[layer], list) else [t[layer]]
                texts(fig, 328, cy - 8, lab)
    return fig


def production_03(lang: str) -> Figure:
    """docs/production/03_gateway_and_pools Pain point: slot collision on pod A and one group scored by v1 and
    v2 (a); one gateway that counts in-flight requests and pins the group (b, from Why and Group pin)."""
    t = T[lang]
    fig = Figure(760, 576)
    c1x, c1w, c2x, c2w, c3x, c3w = 16, 170, 286, 150, 536, 208
    bh = 44
    for p, (oy, letter, title) in enumerate(((0, "a", t["p03.a"]), (292, "b", t["p03.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 54
        ys = [top, top + 54, top + 124, top + 178]          # two lanes: slots (rows 0, 1) and versions (2, 3)
        cy = [y + bh / 2 for y in ys]
        fig.box(c1x, ys[0], c1w, bh, t["p03.trl"], gid=f"n:trl-{letter}")
        fig.box(c1x, ys[1], c1w, bh, t["p03.verl"], gid=f"n:verl-{letter}")
        fig.box(c1x, ys[2], c1w, bh, t["p03.s1"], gid=f"n:s1-{letter}")
        fig.box(c1x, ys[3], c1w, bh, t["p03.s2"], t["p03.s2_sub"], gid=f"n:s2-{letter}")
        mid = c2x + c2w / 2
        if p == 0:
            fig.box(c3x, ys[0], c3w, ys[1] + bh - ys[0], t["p03.podA"], t["p03.podA_bad"], fill=RED_FILL,
                    stroke=RED, color=RED, gid="n:podA-a")
            fig.box(c3x, ys[2], c3w, bh, t["p03.v1"], gid="n:v1-a")
            fig.box(c3x, ys[3], c3w, bh, t["p03.v2"], t["p03.v2_sub"], fill=RED_FILL, stroke=RED, color=RED,
                    gid="n:v2-a")
            for i in (0, 1):
                fig.arrow([(c1x + c1w, cy[i]), (c3x - 2, cy[i])], color=RED, label=t["p03.free"],
                          label_at=(mid, cy[i] - 8))
            fig.arrow([(c1x + c1w, cy[2]), (c3x - 2, cy[2])], label=t["p03.per_sample"], label_at=(mid, cy[2] - 8))
            fig.arrow([(c1x + c1w, cy[3]), (c3x - 2, cy[3])], color=RED, label=t["p03.per_sample"],
                      label_at=(mid, cy[3] - 8))
        else:
            mbox(fig, c2x, ys[0], c2w, ys[3] + bh - ys[0], t["p03.gw"], fill=ACCENT_FILL, stroke=ACCENT,
                 gid="n:gateway")
            fig.box(c3x, ys[0], c3w, bh, t["p03.podA"], gid="n:podA-b")
            fig.box(c3x, ys[1], c3w, bh, t["p03.podB"], gid="n:podB-b")
            fig.box(c3x, ys[2], c3w, ys[3] + bh - ys[2], t["p03.v1pin"], t["p03.v1pin_sub"], gid="n:v1-b")
            for i in range(4):
                fig.arrow([(c1x + c1w, cy[i]), (c2x - 2, cy[i])])
            lx = (c2x + c2w + c3x) / 2
            for i in (0, 1):
                fig.arrow([(c2x + c2w, cy[i]), (c3x - 2, cy[i])], color=ACCENT, label=t["p03.one"],
                          label_at=(lx, cy[i] - 8))
            vmid = (ys[2] + ys[3] + bh) / 2
            fig.arrow([(c2x + c2w, vmid), (c3x - 2, vmid)], color=ACCENT)
            texts(fig, lx, vmid - 8, [t["p03.pinned"]])
    return fig


def production_04(lang: str) -> Figure:
    """docs/production/04_reward_integrity Pain point: a candidate in the scoring process replaces the timer
    and the reference and games the timed window (a); the child process, static policy and measurement
    contract that stop each path (b)."""
    t = T[lang]
    fig = Figure(760, 570)
    rows = [("p04.r1", "p04.r1s", "p04.a1", "p04.b1", "stopwatch"), ("p04.r2", "p04.r2s", "p04.a2", "p04.b2", "law"),
            ("p04.r3", "p04.r3s", "p04.a3", "p04.b3", "clock")]
    pitch, bh = 62, 48
    for p, (oy, letter, title) in enumerate(((0, "a", t["p04.a"]), (286, "b", t["p04.b"]))):
        fig.panel(16, oy + 26, letter, title)
        top = oy + 84
        span = 2 * pitch + bh
        if p == 0:
            fig.container(16, top - 44, 728, span + 58, t["p04.proc"])
        else:
            fig.container(22, top - 30, 180, span + 44, t["p04.child"], icon="shield-lock", stroke=ACCENT,
                          color=ACCENT, bold=True)
        fig.box(36, top, 152, span, t["p04.code"], t["p04.code_sub"], icon="code",
                fill=ACCENT_FILL if p == 1 else GREY_FILL, stroke=ACCENT if p == 1 else MUTED_STROKE,
                gid=f"n:code-{letter}")
        fig.container(524, top - 30, 210, span + 40, t["p04.harness"])
        for i, (res, res_sub, act, layer, ico) in enumerate(rows):
            cy = top + bh / 2 + i * pitch
            fig.box(538, cy - bh / 2, 182, bh, t[res], t[res_sub], icon=ico, gid=f"n:res{i}-{letter}")
            if p == 0:
                fig.arrow([(188, cy), (536, cy)], color=RED, label=t[act], label_at=(356, cy - 8))
            else:
                fig.line([(188, cy), (456, cy)], color=INK)
                fig.block(458, cy)
                fig.text(322, cy - 8, t[layer], size=SMALL)
    return fig


# ---- Main figures ----

def production_00_overview(lang: str) -> Figure:
    """docs/production/00_architecture section 전체 구성: trainers call only the gateway, the gateway calls the
    pools of the sandbox namespace, and the gateway and jwks-sync call the Kubernetes API. Pools sit over their
    Karpenter NodePools (NodePool and RuntimeClass from the page's NodePool table)."""
    t = T[lang]
    fig = Figure(760, 578)
    # trainer tier
    tr_bot = 124
    fig.container(16, 14, 462, tr_bot - 14, t["o00.tr"])
    fig.stack(56, 60, 170, 50, t["o00.trl"], t["o00.trl_sub"], mark="xN", gid="n:trl")
    fig.stack(296, 60, 150, 50, t["o00.verl"], t["o00.verl_sub"], mark="xN", gid="n:verl")
    api_x, api_w, api_y, api_h = 500, 244, 43, 52
    fig.box(api_x, api_y, api_w, api_h, t["o00.api"], gid="n:api")
    api_bot = api_y + api_h + 2
    # gateway tier
    band_y = 168
    gx, gw, gy, gh = 124, 280, band_y + 30, 90
    gcx, gcy = gx + gw / 2, gy + gh / 2
    fig.container(16, band_y, 728, 132, t["o00.gwns"])
    mbox(fig, gx, gy, gw, gh, t["o00.gw"], gid="n:gateway")
    jx_c = api_x + api_w * 3 / 4
    fig.box(jx_c - 42, gcy - 23, 84, 46, t["o00.jwks"], t["o00.jwks_sub"], gid="n:jwks")
    fig.arrow([(gcx, tr_bot), (gcx, gy - 2)])
    fig.text(gcx + 8, (tr_bot + band_y) / 2 + 4, t["o00.aud_gw"], size=SMALL, anchor="start")
    # Kubernetes API calls (dashed): gateway goes right then up, jwks-sync goes straight up.
    gv_x = api_x + api_w / 4
    api_arrow(fig, [(gx + gw, gcy), (gv_x, gcy), (gv_x, api_bot)])
    texts(fig, (gx + gw + gv_x) / 2, gcy - 10, t["o00.e_gw"])
    api_arrow(fig, [(jx_c, gcy - 23), (jx_c, api_bot)])
    texts(fig, jx_c - 8, (tr_bot + band_y) / 2 + 11, t["o00.e_jwks"], anchor="end")
    # sandbox tier: warm placeholder | kata-qemu | gvisor | kata-clh-cpu, gaps of 21 px
    cols = [(36, 125), (182, 164), (367, 168), (556, 172)]
    sb_y = 360
    sy, sh = sb_y + 30, 52
    fig.container(16, sb_y, 728, 96, t["o00.sbns"], icon="shield-lock", stroke=ACCENT, color=ACCENT, bold=True)
    fig.box(cols[0][0], sy, cols[0][1], sh, t["o00.warm"], t["o00.warm_sub"], gid="n:warm")
    pools = [("o00.qemu", "o00.qemu_sub"), ("o00.gvisor", "o00.gvisor_sub"), ("o00.clh", "o00.clh_sub")]
    for (x, w), (k, ks) in zip(cols[1:], pools):
        fig.box(x, sy, w, sh, t[k], t[ks], fill=ACCENT_FILL, stroke=ACCENT, gid=f"n:{k}")
    drops = [x + w / 2 for x, w in cols[1:]]
    bus = 336
    assert abs(drops[0] - gcx) < 0.5, "trunk must run straight into the kata-qemu pool"
    fig.line([(gcx, gy + gh), (gcx, bus), (drops[-1], bus)])
    for dx in drops:
        fig.arrow([(dx, bus), (dx, sy - 2)])
    dot(fig, drops[0], bus)
    dot(fig, drops[1], bus)
    fig.text(gcx + 8, bus - 10, t["o00.aud_sb"], size=SMALL, anchor="start")
    # node tier
    np_y = 472
    fig.container(16, np_y, 728, 92, t["o00.npns"])
    nodes = [(36, 346 - 36, "o00.np_gpu", "o00.np_gpu_sub"), (cols[2][0], cols[2][1], "o00.np_gv", "o00.np_gv_sub"),
             (cols[3][0], cols[3][1], "o00.np_cpu", "o00.np_cpu_sub")]
    for x, w, k, ks in nodes:
        fig.box(x, np_y + 30, w, 48, t[k], t[ks], icon="server", gid=f"n:{k}")
    return fig


def production_02_threat(lang: str) -> Figure:
    """docs/production/02_security section 위협 모델: the five control layers around candidate code, from the
    child process out to the network (the Mermaid chain), drawn nested; the runtime is the isolation boundary."""
    t = T[lang]
    layers = t["o02.layers"]
    inset, strip = 14, 32
    fig = Figure(760, 326)
    for i, (icon, name, rest) in enumerate(layers):
        x0, y0 = 16 + inset * i, 12 + strip * i
        w, h = 728 - 2 * inset * i, fig.height - 24 - strip * i - inset * i
        is_rt = icon == "shield-lock"
        ring(fig, x0, y0, w, h, icon, name, rest, stroke=ACCENT if is_rt else CONTAINER,
             color=ACCENT if is_rt else INK)
    cw = 300
    cy0 = 12 + strip * len(layers) + 6
    fig.box(380 - cw / 2, cy0, cw, 56, t["o02.code"], t["o02.code_sub"], icon="code", gid="n:candidate")
    assert cy0 + 56 + inset <= fig.height - 12 - inset * (len(layers) - 1), "innermost ring too short"
    return fig


def production_04_two_process(lang: str) -> Figure:
    """docs/production/04_reward_integrity section 두 프로세스 구조: steps 1, 2, 4, 5, 6 in the trusted parent,
    step 3 in the untrusted child, what crosses the boundary each way, and what the child never receives."""
    t = T[lang]
    fig = Figure(760, 534)
    px, pw, bx, bw = 16, 292, 32, 260          # parent container and its boxes
    cx, cw, kx, kw = 468, 276, 484, 244        # child container and its boxes
    bh = 46
    fig.box(bx, 14, bw, 46, t["o04.server"], t["o04.server_sub"], icon="server", gid="n:server")
    fig.arrow([(bx + bw / 2, 60), (bx + bw / 2, 92)])
    fig.text(bx + bw / 2 + 8, 81, t["o04.spawn"], size=SMALL, anchor="start")
    fig.container(px, 92, pw, 428, t["o04.parent"], bold=True)
    ys = {1: 122, 2: 190, 4: 320, 5: 388, 6: 456}
    for s, y in ys.items():
        fig.box(bx, y, bw, bh, t[f"o04.s{s}"], t[f"o04.s{s}s"], gid=f"n:step{s}")
    fig.arrow([(bx + bw / 2, ys[1] + bh), (bx + bw / 2, ys[2] - 2)])
    fig.arrow([(bx + bw / 2, ys[4] + bh), (bx + bw / 2, ys[5] - 2)])
    fig.arrow([(bx + bw / 2, ys[5] + bh), (bx + bw / 2, ys[6] - 2)])
    fig.container(cx, 156, cw, 318, t["o04.child"], icon="shield-lock", stroke=ACCENT, color=ACCENT, bold=True)
    fig.box(kx, ys[2], kw, bh, t["o04.s3"], t["o04.s3s"], fill=ACCENT_FILL, stroke=ACCENT, gid="n:step3")
    fig.box(kx, ys[4], kw, bh, t["o04.s3b"], t["o04.s3bs"], fill=ACCENT_FILL, stroke=ACCENT, gid="n:step3b")
    fig.box(kx, 410, kw, bh, t["o04.none"], t["o04.none_sub"], fill="#FFFFFF", gid="n:never")
    fig.arrow([(kx + kw / 2, ys[2] + bh), (kx + kw / 2, ys[4] - 2)])
    # boundary crossings: out at step 2's height, back at step 4's height
    gap_mid = (px + pw + cx) / 2
    y_out, y_in = ys[2] + bh / 2, ys[4] + bh / 2
    fig.arrow([(bx + bw, y_out), (kx - 2, y_out)])
    texts(fig, gap_mid, y_out - 8, t["o04.out_top"])
    texts(fig, gap_mid, y_out + 18 + 15 * (len(t["o04.out_bot"]) - 1), t["o04.out_bot"])
    fig.arrow([(kx, y_in), (bx + bw + 2, y_in)])
    texts(fig, gap_mid, y_in - 8, t["o04.in_top"])
    texts(fig, gap_mid, y_in + 18 + 15 * (len(t["o04.in_bot"]) - 1), t["o04.in_bot"])
    return fig


FIGURES = {
    "production-00_architecture": production_00,
    "production-00_architecture--overview": production_00_overview,
    "production-01_capacity_and_nodes": production_01,
    "production-02_security": production_02,
    "production-02_security--threat-model": production_02_threat,
    "production-03_gateway_and_pools": production_03,
    "production-04_reward_integrity": production_04,
    "production-04_reward_integrity--two-process": production_04_two_process,
}
