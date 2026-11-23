"""Concept page schematics (docs/concepts/01 to 06): Pain point figures and main figures.

Every box and edge comes from the page named in each docstring. Shared geometry draws both languages.
"""

from __future__ import annotations

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


def dot(fig: Figure, x, y, color=INK):
    fig.parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{color}"/>')


def side_label(fig: Figure, x, y, s, color=INK):
    """Edge label to the right of a vertical connector."""
    fig.text(x + 6, y, s, size=SMALL, color=color, anchor="start")


T = {
    "ko": {
        # 01 pain
        "p1.a": "CPU 샌드박스로는 채점 불가, GPU를 연결하면 생기는 위험",
        "p1.b": "이 에셋: CPU에서 먼저 하는 검사와 위험별 대응",
        "p1.code": "후보 커널 코드", "p1.code_sub": "모델이 쓴 Triton 커널",
        "p1.cpu_a": "CPU 전용 샌드박스", "p1.cpu_a_sub": "GPU 없음",
        "p1.gpu_a": "GPU 샌드박스", "p1.gpu_a_sub": "GPU 연결",
        "p1.cpu_b": "CPU에서 먼저 검사", "p1.cpu_b_sub": "형식, AST 정책",
        "p1.gpu_b": "GPU 샌드박스 pod", "p1.gpu_b_sub": "pod당 GPU 1개, 평가 1개",
        "p1.oa": ["GPU에서 측정하는 과제는 채점 불가", "GPU 드라이버에 접근하는 신뢰할 수 없는 코드", "다음 평가에 남는 이전 상태",
                  "샌드박스마다 GPU 1개, 비용 증가", "측정을 속여 reward 획득"],
        "p1.ob": ["위반은 GPU 실행 전에 판정", "노드를 보호하는 gVisor 또는 Kata", "실행마다 새 프로세스 트리와 캐시",
                  "GPU로는 정확성과 timing만 측정", "host clock timing, 출력 checksum 비교"],
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
        # 02 pain
        "p2.cols": [
            ("gVisor + GPU", [["host 드라이버", "허용된 ioctl만 전달"], ["/dev/kvm 불필요", "systrap 플랫폼"],
                              ["일반 GPU VM", "g5.xlarge 등"], ["해당 없음", "경계는 사용자 공간 커널"]]),
            ("Kata + GPU", [["guest 드라이버", "GPU를 VM에 직접 할당 (VFIO)"], ["/dev/kvm, IOMMU", "GPU를 소유한 host"],
                            ["g4dn.metal만", "x86 NVIDIA GPU의 유일한 .metal"],
                            ["upstream 지원은 QEMU만", "Cloud Hypervisor는 미지원"]]),
            ("Kata CPU 전용", [["GPU 없음", "CPU 샌드박스"], ["/dev/kvm", "nested virtualization으로 제공"],
                               ["nested virtualization VM", "c8i.2xlarge 등, 2026-02부터"],
                               ["Cloud Hypervisor, QEMU", "둘 다 지원"]]),
        ],
        "p2.rows": ["GPU 경로", "필요한 것", "인스턴스", "hypervisor"],
        # 02 gpu-paths
        "gp.a": "gVisor + nvproxy (g5.xlarge, 일반 VM)",
        "gp.b": "Kata + QEMU (g4dn.metal)",
        "gp.sbx_a": "pod (gVisor)", "gp.host_a": "host (g5.xlarge)",
        "gp.sbx_b": "guest VM (pod)", "gp.host_b": "host (g4dn.metal)",
        "gp.code": ["후보 코드", "CUDA 사용자 공간 라이브러리"],
        "gp.a_rows": [["Sentry (사용자 공간 커널)", "systrap 플랫폼"], ["nvproxy", "드라이버 버전별 ioctl allowlist"],
                      ["host NVIDIA 드라이버", "580.178.04 proprietary, GSP off"], ["A10G"]],
        "gp.b_rows": [["guest kernel + guest NVIDIA 드라이버", "kata-deploy 제공, open 615.71.09"],
                      ["VFIO passthrough", "DMA를 VM 안으로 제한하는 IOMMU"], None, ["T4", "host는 vfio-pci만 bind"]],
        "gp.no_host_driver": "host에 NVIDIA 드라이버 없음",
        # 03 pain
        "p3.a": "학습 중 섞이는 버전, 0점으로 처리되는 pod 장애",
        "p3.b": "한 group은 한 버전, 인프라 오류는 None으로 제외 (TRL)",
        "p3.prompt": "prompt", "p3.prompt_sub": "1개",
        "p3.group": "group (같은 prompt)",
        "p3.ca": ["completion A", "v1로 채점"],
        "p3.cb_a": ["completion B (A와 같은 코드)", "v2로 채점"],
        "p3.cb_b": ["completion B (A와 같은 코드)", "v1로 채점"],
        "p3.cc_a": ["completion C (정답)", "pod 장애"],
        "p3.cc_b": ["completion C (정답)", "sandbox_error"],
        "p3.s_a": ["1.85", "1.35", "0점"], "p3.s_b": ["1.85", "1.85", "None"],
        "p3.adv": ["advantage", "group 평균과 비교"],
        "p3.bad": ["advantage에 섞이는", "버전 차이와", "인프라 잡음"],
        "p3.good": ["policy 차이만 반영", "C는 baseline에서 제외"],
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
        # 04 pain
        "p4.a": "샌드박스도 기본 AMI의 HyperPod 노드에 두면: gVisor와 Kata 모두 실행 불가",
        "p4.b": "B1: trainer만 HyperPod에, 샌드박스는 같은 클러스터의 EC2 노드에",
        "p4.eks": "EKS 클러스터", "p4.hp": "HyperPod 인스턴스 그룹", "p4.ec2": "EC2 노드 그룹",
        "p4.trainer": ["trainer", "ml.g5.2xlarge"],
        "p4.gv_a": ["gVisor 샌드박스", "드라이버 595.91.07은 unknown"],
        "p4.kt_a": ["Kata 샌드박스", "ml.*.metal, nested virtualization 없음"],
        "p4.gv_b": ["gVisor 샌드박스", "g5.xlarge"],
        "p4.kt_b": ["Kata 샌드박스", "g4dn.metal (GPU), c8i.2xlarge (CPU)"],
        # 05 pain
        "p5.cols": [["T4"], ["최신 GPU", "L4, L40S, H100"]],
        "p5.rows": ["VM 경계", "사용자 공간 커널 경계", "AWS 관리형 격리"],
        "p5.vm_t4": ["Kata + QEMU", "g4dn.metal, VFIO"],
        "p5.vm_new": ["EC2에 없음"],
        "p5.us_t4": ["gVisor on g4dn", "이 에셋에서 미검증"],
        "p5.us_new": ["gVisor + nvproxy", "G/P 계열 VM (g5, g6, g6e, p5)"],
        "p5.managed": ["Nitro Sandboxes, EKS isolated pods", "출시 시점 CPU 전용 (GPU passthrough 미지원)"],
        # 05 decision tree
        "dt.A": ["샌드박스 안에서 GPU 필요"],
        "dt.B": ["관리형 서비스 선호"],
        "dt.C": ["관리형 GPU 샌드박스 선호"],
        "dt.D": ["VM 경계 필요", "(서로 다른 고객의 적대적 코드)"],
        "dt.E": ["T4에서 측정한 timing으로 충분"],
        "dt.B1": ["AgentCore Code Interpreter 또는", "Nitro Sandboxes, EKS isolated pods", "(CPU 전용)"],
        "dt.B2": ["Kata + CLH on c8i", "(nested virtualization)"],
        "dt.C1": ["서드파티 서비스", "(예: Modal, gVisor 기반)", "이 에셋 범위 밖"],
        "dt.F": ["gVisor + nvproxy on G/P 계열 VM", "g5 (A10G), g6 (L4), g6e (L40S), p5 (H100)"],
        "dt.E1": ["Kata + QEMU on g4dn.metal", "VM 경계 + VFIO"],
        "dt.E2": ["EC2에 없는 VM 경계 + 최신 GPU 조합", "gVisor + 보완 통제로 위험을 수용하거나", "요구 사항을 다시 검토"],
        "dt.yes": "예", "dt.no": "아니오",
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
        "p1.a": "A CPU sandbox cannot score the task; attaching a GPU brings risks",
        "p1.b": "This asset: filter on CPU first, one countermeasure per risk",
        "p1.code": "Candidate kernel", "p1.code_sub": "Triton, by the model",
        "p1.cpu_a": "CPU-only sandbox", "p1.cpu_a_sub": "no GPU",
        "p1.gpu_a": "GPU sandbox", "p1.gpu_a_sub": "GPU attached",
        "p1.cpu_b": "Checks on CPU first", "p1.cpu_b_sub": "format, AST policy",
        "p1.gpu_b": "GPU sandbox pod", "p1.gpu_b_sub": "1 GPU, 1 evaluation per pod",
        "p1.oa": ["cannot score tasks measured on a GPU", "untrusted code reaches the GPU driver",
                  "state leaks into the next evaluation", "one GPU per sandbox, higher cost",
                  "fools the measurement for reward"],
        "p1.ob": ["violations get a verdict before the GPU", "gVisor or Kata protects the node",
                  "new process tree and caches per run", "the GPU measures only correctness and timing",
                  "host clock timing, output checksums"],
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
        "p2.cols": [
            ("gVisor + GPU", [["host driver", "forwards only allowed ioctls"], ["no /dev/kvm needed", "systrap platform"],
                              ["regular GPU VM", "g5.xlarge and others"], ["not applicable", "boundary: user-space kernel"]]),
            ("Kata + GPU", [["guest driver", "whole GPU into the VM (VFIO)"], ["/dev/kvm, IOMMU", "a host that owns the GPU"],
                            ["g4dn.metal only", "the only x86 NVIDIA .metal"],
                            ["upstream: QEMU only", "Cloud Hypervisor not supported"]]),
            ("Kata CPU only", [["no GPU", "CPU sandbox"], ["/dev/kvm", "from nested virtualization"],
                               ["nested virtualization VM", "c8i.2xlarge etc., since 2026-02"],
                               ["Cloud Hypervisor, QEMU", "both supported"]]),
        ],
        "p2.rows": ["GPU path", "requires", "instance", "hypervisor"],
        "gp.a": "gVisor + nvproxy (g5.xlarge, regular VM)",
        "gp.b": "Kata + QEMU (g4dn.metal)",
        "gp.sbx_a": "pod (gVisor)", "gp.host_a": "host (g5.xlarge)",
        "gp.sbx_b": "guest VM (pod)", "gp.host_b": "host (g4dn.metal)",
        "gp.code": ["candidate code", "CUDA user-space libraries"],
        "gp.a_rows": [["Sentry (user-space kernel)", "systrap platform"], ["nvproxy", "ioctl allowlist per driver version"],
                      ["host NVIDIA driver", "580.178.04 proprietary, GSP off"], ["A10G"]],
        "gp.b_rows": [["guest kernel + guest NVIDIA driver", "shipped by kata-deploy, open 615.71.09"],
                      ["VFIO passthrough", "IOMMU confines DMA to the VM"], None,
                      ["T4", "the host binds only vfio-pci"]],
        "gp.no_host_driver": "no NVIDIA driver on the host",
        "p3.a": "Versions mix during training, and a pod failure enters as zero",
        "p3.b": "One version per group, infrastructure errors excluded as None (TRL)",
        "p3.prompt": "prompt", "p3.prompt_sub": "one",
        "p3.group": "group (same prompt)",
        "p3.ca": ["completion A", "scored by v1"],
        "p3.cb_a": ["completion B (same code as A)", "scored by v2"],
        "p3.cb_b": ["completion B (same code as A)", "scored by v1"],
        "p3.cc_a": ["completion C (correct)", "pod failure"],
        "p3.cc_b": ["completion C (correct)", "sandbox_error"],
        "p3.s_a": ["1.85", "1.35", "zero"], "p3.s_b": ["1.85", "1.85", "None"],
        "p3.adv": ["advantage", "vs group mean"],
        "p3.bad": ["version gaps and", "infrastructure noise", "mixed into advantage"],
        "p3.good": ["policy differences only", "C left out of the baseline"],
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
        "p4.a": "Sandboxes on default-AMI HyperPod nodes too: gVisor and Kata are both blocked",
        "p4.b": "B1: only the trainer on HyperPod, sandboxes on EC2 nodes of the same cluster",
        "p4.eks": "EKS cluster", "p4.hp": "HyperPod instance group", "p4.ec2": "EC2 node groups",
        "p4.trainer": ["trainer", "ml.g5.2xlarge"],
        "p4.gv_a": ["gVisor sandbox", "driver 595.91.07 is unknown"],
        "p4.kt_a": ["Kata sandbox", "no ml.*.metal, no nested virtualization"],
        "p4.gv_b": ["gVisor sandbox", "g5.xlarge"],
        "p4.kt_b": ["Kata sandbox", "g4dn.metal (GPU), c8i.2xlarge (CPU)"],
        "p5.cols": [["T4"], ["current GPU", "L4, L40S, H100"]],
        "p5.rows": ["VM boundary", "user-space kernel boundary", "AWS managed isolation"],
        "p5.vm_t4": ["Kata + QEMU", "g4dn.metal, VFIO"],
        "p5.vm_new": ["not on EC2"],
        "p5.us_t4": ["gVisor on g4dn", "unverified in this asset"],
        "p5.us_new": ["gVisor + nvproxy", "G/P family VMs (g5, g6, g6e, p5)"],
        "p5.managed": ["Nitro Sandboxes, EKS isolated pods", "CPU only at launch (no GPU passthrough)"],
        "dt.A": ["GPU needed", "inside the sandbox"],
        "dt.B": ["prefer a", "managed service"],
        "dt.C": ["prefer a managed", "GPU sandbox"],
        "dt.D": ["VM boundary needed", "(adversarial code from", "different customers)"],
        "dt.E": ["T4 is acceptable", "for measurement"],
        "dt.B1": ["AgentCore Code Interpreter or", "Nitro Sandboxes, EKS isolated pods", "(CPU only)"],
        "dt.B2": ["Kata + CLH on c8i", "(nested virtualization)"],
        "dt.C1": ["third-party service", "(for example Modal, gVisor-based)", "out of scope for this asset"],
        "dt.F": ["gVisor + nvproxy on G/P family VMs", "g5 (A10G), g6 (L4), g6e (L40S), p5 (H100)"],
        "dt.E1": ["Kata + QEMU on g4dn.metal", "VM boundary + VFIO"],
        "dt.E2": ["EC2 has no VM boundary +", "current GPU combination", "accept the risk with gVisor +",
                  "compensating controls, or", "revisit the requirements"],
        "dt.yes": "yes", "dt.no": "no",
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


def concepts_01(lang: str) -> Figure:
    """docs/concepts/01_why_gpu_sandbox Pain point: CPU-only cannot score; a GPU brings four risks; the page's answers."""
    t = T[lang]
    fig = Figure(760, 552)
    cx, cw, mx, mw, ox, ow = 16, 136, 192, 178, 410, 334
    for p, (oy, letter, title) in enumerate(((0, "a", t["p1.a"]), (276, "b", t["p1.b"]))):
        fig.panel(16, oy + 24, letter, title)
        top = oy + 46
        fix = p == 1
        fig.box(cx, top, cw, 212, t["p1.code"], t["p1.code_sub"], icon="code", gid=f"n:code-{letter}")
        # CPU row and GPU block in the middle column
        r0 = top + 20
        rows = [top + 72 + i * 40 for i in range(4)]
        if fix:
            fig.box(mx, top, mw, 40, t["p1.cpu_b"], t["p1.cpu_b_sub"], icon="cpu", gid="n:cpu-b")
            fig.box(mx, top + 52, mw, 160, t["p1.gpu_b"], t["p1.gpu_b_sub"], icon="shield-lock", fill=ACCENT_FILL,
                    stroke=ACCENT, gid="n:gpu-b")
        else:
            fig.box(mx, top, mw, 40, t["p1.cpu_a"], t["p1.cpu_a_sub"], icon="cpu", gid="n:cpu-a")
            fig.box(mx, top + 52, mw, 160, t["p1.gpu_a"], t["p1.gpu_a_sub"], icon="container", gid="n:gpu-a")
        # One branch point from the code box to both sandboxes
        bus, gmid = cx + cw + 20, top + 132
        fig.line([(cx + cw, top + 106), (bus, top + 106)])
        dot(fig, bus, top + 106)
        fig.line([(bus, top + 106), (bus, r0)])
        fig.arrow([(bus, r0), (mx - 2, r0)])
        fig.line([(bus, top + 106), (bus, gmid)])
        fig.arrow([(bus, gmid), (mx - 2, gmid)])
        outs = t["p1.ob"] if fix else t["p1.oa"]
        col = ACCENT if fix else RED
        style = dict(fill=ACCENT_FILL, stroke=ACCENT, color=INK) if fix else dict(fill=RED_FILL, stroke=RED, color=RED)
        for i, (cy, s) in enumerate(zip([r0] + rows, outs)):
            fig.arrow([(mx + mw, cy), (ox - 2, cy)], color=col)
            mbox(fig, ox, cy - 15, ow, 30, [s], gid=f"n:out{i}-{letter}", **style)
    return fig


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


def concepts_02(lang: str) -> Figure:
    """docs/concepts/02_isolation_runtimes Pain point: three runtimes; only Kata + GPU needs .metal and QEMU."""
    t = T[lang]
    fig = Figure(760, 300)
    lx, cw, gap, bh = 86, 214, 8, 46
    rows_y = [50 + i * (bh + 12) for i in range(4)]
    for y, label in zip(rows_y, t["p2.rows"]):
        fig.text(16, y + bh / 2 + 4, label, size=SMALL, bold=True, anchor="start")
    for c, (runtime, cells) in enumerate(t["p2.cols"]):
        x = lx + c * (cw + gap)
        fig.container(x, 16, cw, rows_y[-1] + bh + 12 - 16, runtime, bold=True)
        for r, (y, lines) in enumerate(zip(rows_y, cells)):
            # The two constraints that only Kata + GPU carries are the bottleneck of the page
            style = dict(fill=RED_FILL, stroke=RED, color=RED) if c == 1 and r >= 2 else {}
            mbox(fig, x + 12, y, cw - 24, bh, lines, gid=f"n:c{c}r{r}", **style)
    return fig


def concepts_02_gpu_paths(lang: str) -> Figure:
    """docs/concepts/02_isolation_runtimes "GPU 경로 두 가지": gVisor nvproxy vs Kata VFIO on the same five rows."""
    t = T[lang]
    fig = Figure(760, 546)
    pw, gap, bh, pitch = 356, 16, 46, 100
    rows = [74 + i * pitch for i in range(5)]  # box tops
    for p, (letter, title, sbx, host, body, split) in enumerate((
            ("a", t["gp.a"], t["gp.sbx_a"], t["gp.host_a"], t["gp.a_rows"], 3),
            ("b", t["gp.b"], t["gp.sbx_b"], t["gp.host_b"], t["gp.b_rows"], 2))):
        x = 16 + p * (pw + gap)
        fig.panel(x, 26, letter, title)
        # The isolation boundary (accent) holds the rows above the split; the host holds the rest
        fig.container(x, rows[0] - 30, pw, rows[split - 1] + bh + 10 - (rows[0] - 30), sbx, icon="shield-lock",
                      stroke=ACCENT, color=ACCENT, bold=True)
        fig.container(x, rows[split] - 30, pw, rows[4] + bh + 10 - (rows[split] - 30), host, icon="server", bold=True)
        bx, bw = x + 20, pw - 40
        cx = bx + bw / 2
        labels = [t["gp.code"]] + body
        prev_bottom = None
        for i, (y, lines) in enumerate(zip(rows, labels)):
            if lines is None:
                # Kata: nothing on the host sits between VFIO and the GPU
                side_label(fig, cx, y + bh / 2 + 4, t["gp.no_host_driver"])
                continue
            inside = i < split
            mbox(fig, bx, y, bw, bh, lines, gid=f"n:{letter}{i}",
                 **(dict(fill=ACCENT_FILL, stroke=ACCENT) if inside else {}))
            if prev_bottom is not None:
                fig.arrow([(cx, prev_bottom), (cx, y - 2)])
            prev_bottom = y + bh
    return fig


def concepts_03(lang: str) -> Figure:
    """docs/concepts/03_onpolicy_rl_with_sandboxes Pain point: mixed versions and zeroed failures vs pinned + None."""
    t = T[lang]
    fig = Figure(760, 542)
    px, pw, gx, gw, ax, aw, ox, ow = 16, 104, 152, 226, 446, 104, 590, 154
    for p, (oy, letter, title) in enumerate(((0, "a", t["p3.a"]), (268, "b", t["p3.b"]))):
        fix = p == 1
        fig.panel(16, oy + 24, letter, title)
        top = oy + 44
        ys = [top + 52 + i * 64 for i in range(3)]
        mid = ys[1]
        fig.box(px, mid - 25, pw, 50, t["p3.prompt"], t["p3.prompt_sub"], icon="comment", gid=f"n:prompt-{letter}")
        fig.container(gx - 12, top, gw + 24, 216, t["p3.group"], icon="stack")
        rows = [t["p3.ca"], t["p3.cb_b"] if fix else t["p3.cb_a"], t["p3.cc_b"] if fix else t["p3.cc_a"]]
        scores = t["p3.s_b"] if fix else t["p3.s_a"]
        fig.arrow([(px + pw, mid), (gx - 14, mid)])
        mbox(fig, ax, top + 28, aw, 176, t["p3.adv"], gid=f"n:adv-{letter}")
        for i, (y, lines, s) in enumerate(zip(ys, rows, scores)):
            mbox(fig, gx, y - 24, gw, 48, lines, gid=f"n:c{i}-{letter}")
            if fix and i == 2:
                col, dash = MUTED_STROKE, "5 4"
            elif not fix and i > 0:
                col, dash = RED, None
            else:
                col, dash = INK, None
            fig.arrow([(gx + gw, y), (ax - 2, y)], color=col, dash=dash, label=s,
                      label_at=((gx + gw + ax) / 2, y - 8), label_color=RED if col == RED else INK)
        if fix:
            fig.arrow([(ax + aw, mid), (ox - 2, mid)], color=ACCENT)
            mbox(fig, ox, mid - 44, ow, 88, t["p3.good"], fill=ACCENT_FILL, stroke=ACCENT, gid="n:outcome-b")
        else:
            fig.arrow([(ax + aw, mid), (ox - 2, mid)], color=RED)
            mbox(fig, ox, mid - 44, ow, 88, t["p3.bad"], fill=RED_FILL, stroke=RED, color=RED, gid="n:outcome-a")
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
    """docs/concepts/04_platforms_and_instances Pain point: sandboxes on HyperPod blocked vs B1 placement."""
    t = T[lang]
    fig = Figure(760, 482)
    tx, tw, sx, swid = 46, 170, 404, 310
    for p, (oy, letter, title) in enumerate(((0, "a", t["p4.a"]), (240, "b", t["p4.b"]))):
        fix = p == 1
        fig.panel(16, oy + 24, letter, title)
        top = oy + 46
        fig.container(16, top, 728, 182, t["p4.eks"], icon="cloud")
        if fix:
            fig.container(30, top + 30, 202, 138, t["p4.hp"], icon="server")
            fig.container(388, top + 30, 342, 138, t["p4.ec2"], icon="server", stroke=ACCENT, color=ACCENT, bold=True)
        else:
            fig.container(30, top + 30, 700, 138, t["p4.hp"], icon="server")
        mbox(fig, tx, top + 62, tw, 96, t["p4.trainer"], icon="hubot", gid=f"n:trainer-{letter}")
        boxes = (t["p4.gv_b"], t["p4.kt_b"]) if fix else (t["p4.gv_a"], t["p4.kt_a"])
        for i, (y, lines) in enumerate(zip((top + 62, top + 114), boxes)):
            if fix:
                mbox(fig, sx, y, swid, 44, lines, icon="shield-lock", fill=ACCENT_FILL, stroke=ACCENT, gid=f"n:sbx{i}-b")
            else:
                mbox(fig, sx, y, swid, 44, lines, icon="alert", fill=RED_FILL, stroke=RED, color=RED, gid=f"n:sbx{i}-a")
    return fig


def concepts_05(lang: str) -> Figure:
    """docs/concepts/05_decision_guide Pain point: isolation boundary x measurement GPU, plus managed isolation."""
    t = T[lang]
    fig = Figure(760, 278)
    hx, hw, c1, c2, cw = 16, 176, 204, 478, 266
    hy, rh, rg = 16, 56, 14
    for x, lines in zip((c1, c2), t["p5.cols"]):
        fig.text(x + cw / 2, hy + 18, lines[0], size=SMALL, bold=True)
        if len(lines) > 1:
            fig.text(x + cw / 2, hy + 35, lines[1], size=SMALL)
    ys = [hy + 50 + i * (rh + rg) for i in range(3)]
    for y, label in zip(ys, t["p5.rows"]):
        fig.text(hx, y + rh / 2 + 4, label, size=SMALL, bold=True, anchor="start")
    ok = dict(fill=ACCENT_FILL, stroke=ACCENT)
    bad = dict(fill=RED_FILL, stroke=RED, color=RED)
    mbox(fig, c1, ys[0], cw, rh, t["p5.vm_t4"], icon="check-circle", gid="n:vm-t4", **ok)
    mbox(fig, c2, ys[0], cw, rh, t["p5.vm_new"], icon="x-circle", gid="n:vm-new", **bad)
    mbox(fig, c1, ys[1], cw, rh, t["p5.us_t4"], icon="question", gid="n:us-t4")
    mbox(fig, c2, ys[1], cw, rh, t["p5.us_new"], icon="check-circle", gid="n:us-new", **ok)
    mbox(fig, c1, ys[2], c2 + cw - c1, rh, t["p5.managed"], icon="x-circle", gid="n:managed", **bad)
    return fig


def concepts_05_decision_tree(lang: str) -> Figure:
    """docs/concepts/05_decision_guide "결정 트리": every branch and leaf of the Mermaid tree, as an orthogonal ladder."""
    t = T[lang]
    yes, no = t["dt.yes"], t["dt.no"]
    dx, dw, bx, bw, lx, lw = 16, 196, 272, 140, 452, 292

    def height(key):
        return max(40, (len(t[key]) - 1) * PITCH + 30)

    leaf_rows = ["dt.B1", "dt.B2", "dt.C1", "dt.F", "dt.E1", "dt.E2"]
    spine = {0: "dt.A", 2: "dt.C", 3: "dt.D", 4: "dt.E"}
    hs = [max(height(k), height(spine[i]) if i in spine else 0) for i, k in enumerate(leaf_rows)]
    # Rows joined by a vertical spine edge (C to D, D to E) need room for the edge and its label
    gaps = [14, 14, 34, 34, 14]
    ys, y = [], 16
    for i, h in enumerate(hs):
        ys.append(y + h / 2)
        y += h + (gaps[i] if i < len(gaps) else 0)
    fig = Figure(760, int(y + 16))
    decision = dict(fill=WHITE, stroke=INK)
    accent = dict(fill=ACCENT_FILL, stroke=ACCENT)

    def dbox(x, w, key, cy, gid):
        h = height(key)
        mbox(fig, x, cy - h / 2, w, h, t[key], gid=gid, **decision)
        return cy - h / 2, cy + h / 2

    def leaf(i, gid, **style):
        h = height(leaf_rows[i])
        mbox(fig, lx, ys[i] - h / 2, lw, h, t[leaf_rows[i]], gid=gid, **style)

    a_top, a_bot = dbox(dx, dw, "dt.A", ys[0], "n:A")
    b_top, b_bot = dbox(bx, bw, "dt.B", ys[0], "n:B")
    c_top, c_bot = dbox(dx, dw, "dt.C", ys[2], "n:C")
    d_top, d_bot = dbox(dx, dw, "dt.D", ys[3], "n:D")
    e_top, e_bot = dbox(dx, dw, "dt.E", ys[4], "n:E")
    leaf(0, "n:B1")
    leaf(1, "n:B2", **accent)
    leaf(2, "n:C1")
    leaf(3, "n:F", **accent)
    leaf(4, "n:E1", **accent)
    leaf(5, "n:E2", fill=RED_FILL, stroke=RED, color=RED)

    def h_edge(x0, x1, cy, label):
        fig.arrow([(x0, cy), (x1 - 2, cy)], label=label, label_at=((x0 + x1) / 2, cy - 8))

    def v_edge(x, y0, y1, label):
        fig.arrow([(x, y0), (x, y1 - 2)])
        side_label(fig, x, (y0 + y1) / 2 + 4, label)

    dcx, bcx = dx + dw / 2, bx + bw / 2
    h_edge(dx + dw, bx, ys[0], no)
    h_edge(bx + bw, lx, ys[0], yes)
    fig.arrow([(bcx, b_bot), (bcx, ys[1]), (lx - 2, ys[1])])
    side_label(fig, bcx, (b_bot + ys[1]) / 2 + 4, no)
    v_edge(dcx, a_bot, c_top, yes)
    h_edge(dx + dw, lx, ys[2], yes)
    v_edge(dcx, c_bot, d_top, no)
    h_edge(dx + dw, lx, ys[3], no)
    v_edge(dcx, d_bot, e_top, yes)
    h_edge(dx + dw, lx, ys[4], yes)
    fig.arrow([(dcx, e_bot), (dcx, ys[5]), (lx - 2, ys[5])])
    side_label(fig, dcx, (e_bot + ys[5]) / 2 + 4, no)
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
    "concepts-01_why_gpu_sandbox": concepts_01,
    "concepts-01_why_gpu_sandbox--two-tier": concepts_01_two_tier,
    "concepts-01_why_gpu_sandbox--rl-loop": concepts_01_rl_loop,
    "concepts-02_isolation_runtimes": concepts_02,
    "concepts-02_isolation_runtimes--gpu-paths": concepts_02_gpu_paths,
    "concepts-03_onpolicy_rl_with_sandboxes": concepts_03,
    "concepts-03_onpolicy_rl_with_sandboxes--version-swap": concepts_03_version_swap,
    "concepts-04_platforms_and_instances": concepts_04,
    "concepts-05_decision_guide": concepts_05,
    "concepts-05_decision_guide--decision-tree": concepts_05_decision_tree,
    "concepts-06_agent_sandbox": concepts_06,
}
