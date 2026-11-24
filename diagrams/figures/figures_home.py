"""AWS topology of the A, B1 and B2 GPU labs on the homepage and in the READMEs."""
from base64 import b64encode
from pathlib import Path

from figlib import ACCENT, INK, Figure

ICONS = Path(__file__).resolve().parents[2] / 'demo/site/icons'
SLATE = '#425369'
LINE = '#8495A8'
GREEN = '#267047'
TEXT = {
    'ko': dict(pc='운영자 PC', vpc='Amazon VPC', private='프라이빗 서브넷', relay='접속용 EC2',
               endpoint='A, B1은 프라이빗', endpoint_short='A/B1 프라이빗', lookup='DNS로 Ready pod 조회', tunnel='SSM 터널', direct='B2 직접 접속', deploy='워크로드 배포', pull='이미지 pull',
               workers='Amazon EKS 워커 노드', trainer='학습 노드', sandbox='GPU 채점 pool', system='B2 시스템 CPU (HyperPod)',
               submit='코드 채점 요청', result='채점 결과', metrics='판정과 속도', optional='선택'),
    'en': dict(pc='Operator', vpc='Amazon VPC', private='Private subnets', relay='Access EC2',
               endpoint='Private in A and B1', endpoint_short='Private in A/B1', lookup='Resolve Ready pod IPs', tunnel='SSM tunnel', direct='B2 direct access', deploy='Deploy workloads', pull='Pull images',
               workers='Amazon EKS workers', trainer='Training node', sandbox='GPU grading pool', system='B2 system CPU (HyperPod)',
               submit='Submit code', result='Grading result', metrics='Verdict and speedup', optional='Optional'),
}


def icon(f, name, x, y, size):
    data = b64encode((ICONS / f'{name}.svg').read_bytes()).decode('ascii')
    f.parts.append(f'<image x="{x}" y="{y}" width="{size}" height="{size}" '
                   f'href="data:image/svg+xml;base64,{data}"/>')


def label(f, x, y, text, size=15, *, bold=False, color=INK, anchor='start'):
    f.text(x, y, text, size=size, bold=bold, color=color, anchor=anchor)


def boundary(f, x, y, w, h, edge, fill, dash=None):
    f.rect(x, y, w, h, fill=fill, stroke=edge, width=1.4, dash=dash, rx=5)


def access_box(f, x, y, width, icon_name, title, subtitle, compact=False):
    height = 51 if compact else 50
    boundary(f, x, y, width, height, '#CFDACF', '#FFFFFF')
    size = 25 if compact else 32
    icon(f, icon_name, x + 7, y + (height - size) / 2, size)
    left = x + size + 13
    label(f, left, y + 21, title, 14 if compact else 16, bold=True)
    label(f, left, y + 39, subtitle, 12 if compact else 14, color=SLATE)


def workload(f, x, y, width, t, sandbox=False, compact=False):
    row_gap = 43 if compact else 51
    height = (125 if compact else 148) + (row_gap if sandbox else 0)
    boundary(f, x, y, width, height, ACCENT if sandbox else '#A4B2C2', '#EEF5FD' if sandbox else '#F4F6F9')
    label(f, x + 10, y + 23, t['sandbox' if sandbox else 'trainer'], 17, bold=True,
          color=ACCENT if sandbox else INK)
    label(f, x + width - 10, y + 22, 'ns: sandbox' if sandbox else 'ns: rl-trainer', 12,
          color=SLATE, anchor='end')
    f.line([(x+10, y+31), (x+width-10, y+31)], color='#C9D5E0', width=1)
    if sandbox:
        rows = [('ec2', 'EC2 gVisor (A, B1)', 'g5.xlarge × 2 (A10G)'),
                ('sagemaker', 'HyperPod gVisor (B2)', 'ml.g5.xlarge × 2 (A10G)'),
                ('ec2', 'Kata + QEMU (A, B1)', f'g4dn.metal, T4 ({t["optional"]})')]
    else:
        rows = [('ec2', 'Amazon EC2 (A)', 'g5.2xlarge, GRPO Job'),
                ('sagemaker', 'SageMaker HyperPod (B1, B2)', 'ml.g5.2xlarge, HyperPodPyTorchJob')]
    for i, (name, title, detail) in enumerate(rows):
        top = y + (40 if compact else 44) + i * row_gap
        size = 28 if compact else 32
        icon(f, name, x + 11, top + 1, size)
        label(f, x + size + 20, top + 13, title, 15, bold=True)
        label(f, x + size + 20, top + 32, detail, 13, color=SLATE)


def admin(f, points):
    f.arrow(points, color=INK, width=1.4, dash='5 3')


def desktop(lang):
    t = TEXT[lang]
    f = Figure(824, 521)
    boundary(f, 1, 51, 822, 468, '#44546A', '#FFFFFF')
    icon(f, 'aws-cloud', 13, 63, 34)
    label(f, 57, 86, 'AWS Cloud', 18, bold=True)
    icon(f, 'client', 10, 5, 33)
    label(f, 48, 20, t['pc'], 16, bold=True)
    label(f, 48, 38, 'kubectl / Helm', 13, color=SLATE)
    admin(f, [(151, 24), (243, 24), (243, 63)])
    icon(f, 'ssm', 224, 65, 37)
    label(f, 269, 80, 'AWS Systems Manager', 16, bold=True)
    label(f, 269, 100, 'Session Manager', 14, color=SLATE)
    icon(f, 'ecr', 630, 65, 37)
    label(f, 675, 89, 'Amazon ECR', 17, bold=True)
    boundary(f, 12, 122, 800, 384, GREEN, '#F6FAF6')
    label(f, 24, 145, t['vpc'], 16, bold=True, color=GREEN)
    label(f, 24, 165, t['private'], 14, color=GREEN)
    admin(f, [(243, 104), (243, 157)])
    label(f, 253, 145, t['tunnel'], 13, color=SLATE)
    admin(f, [(243, 24), (562, 24), (562, 157)])
    label(f, 406, 17, t['direct'], 14, color=SLATE, anchor='middle')
    access_box(f, 142, 159, 207, 'ec2', t['relay'], 't4g.nano (A, B1)')
    access_box(f, 462, 159, 200, 'eks', 'Amazon EKS API', t['endpoint'])
    admin(f, [(350, 185), (460, 185)])
    label(f, 405, 178, 'HTTPS 443', 13, color=SLATE, anchor='middle')
    boundary(f, 24, 236, 776, 258, '#7991A5', '#FFFFFF', '6 3')
    admin(f, [(549, 210), (549, 234)])
    label(f, 561, 228, t['deploy'], 13, color=SLATE)
    admin(f, [(752, 235), (752, 105)])
    label(f, 741, 149, t['pull'], 13, color=SLATE, anchor='end')
    icon(f, 'eks', 35, 244, 22)
    label(f, 65, 262, t['workers'], 17, bold=True)
    workload(f, 36, 277, 278, t)
    workload(f, 509, 277, 278, t, sandbox=True)
    access_box(f, 36, 432, 278, 'sagemaker', t['system'], 'ml.m5.xlarge × 1 (CoreDNS)')
    label(f, 411, 300, t['submit'], 17, bold=True, color=ACCENT, anchor='middle')
    f.arrow([(315, 313), (507, 313)], color=ACCENT, width=2)
    label(f, 411, 332, t['lookup'], 13, color=SLATE, anchor='middle')
    label(f, 411, 351, 'POST /v1/evaluate', 14, color=SLATE, anchor='middle')
    f.arrow([(508, 368), (316, 368)], color=ACCENT, width=2)
    label(f, 411, 392, t['result'], 17, bold=True, color=ACCENT, anchor='middle')
    label(f, 411, 413, t['metrics'], 14, color=SLATE, anchor='middle')
    return f


def mobile(lang):
    t = TEXT[lang]
    f = Figure(360, 716)
    icon(f, 'client', 9, 6, 26)
    label(f, 43, 24, t['pc']+' (kubectl)', 14, bold=True)
    boundary(f, 1, 44, 358, 670, '#44546A', '#FFFFFF')
    icon(f, 'aws-cloud', 9, 53, 27)
    label(f, 43, 73, 'AWS Cloud', 15, bold=True)
    admin(f, [(166, 20), (205, 20), (205, 52)])
    icon(f, 'ssm', 191, 54, 27)
    label(f, 224, 66, 'Systems Manager', 13, bold=True)
    label(f, 224, 82, 'Session Manager', 12, color=SLATE)
    boundary(f, 8, 100, 344, 564, GREEN, '#F6FAF6')
    label(f, 18, 121, t['vpc'], 14, bold=True, color=GREEN)
    admin(f, [(166, 20), (166, 127), (118, 127), (118, 134)])
    label(f, 158, 94, t['direct'], 12, color=SLATE, anchor='end')
    admin(f, [(242, 85), (242, 134)])
    label(f, 251, 119, t['tunnel'], 12, color=SLATE)
    access_box(f, 185, 136, 156, 'ec2', t['relay'], 't4g.nano (A, B1)', True)
    access_box(f, 17, 136, 130, 'eks', 'EKS API', t['endpoint_short'], True)
    admin(f, [(184, 169), (149, 169)])
    label(f, 166, 162, '443', 11, color=SLATE, anchor='middle')
    boundary(f, 17, 210, 326, 447, '#7991A5', '#FFFFFF', '5 3')
    admin(f, [(86, 188), (86, 208)])
    label(f, 99, 204, t['deploy'], 12, color=SLATE)
    icon(f, 'eks', 26, 216, 23)
    label(f, 55, 233, t['workers'], 16, bold=True)
    label(f, 335, 233, t['private'], 12, color=GREEN, anchor='end')
    workload(f, 25, 247, 310, t, compact=True)
    workload(f, 25, 418, 310, t, sandbox=True, compact=True)
    f.arrow([(42, 373), (42, 416)], color=ACCENT, width=1.8)
    label(f, 53, 391, t['submit'], 14, color=ACCENT, bold=True)
    label(f, 53, 407, '/v1/evaluate', 12, color=SLATE)
    f.arrow([(318, 417), (318, 374)], color=ACCENT, width=1.8)
    label(f, 307, 391, t['result'], 14, color=ACCENT, bold=True, anchor='end')
    label(f, 307, 407, t['metrics'], 12, color=SLATE, anchor='end')
    access_box(f, 25, 595, 310, 'sagemaker', t['system'], 'ml.m5.xlarge × 1 (CoreDNS)', True)
    icon(f, 'ecr', 21, 677, 27)
    label(f, 58, 696, 'Amazon ECR', 15, bold=True)
    admin(f, [(294, 658), (294, 691), (163, 691)])
    label(f, 223, 685, t['pull'], 12, color=SLATE, anchor='middle')
    return f


FIGURES = {'index--aws-architecture': desktop, 'index--aws-architecture-compact': mobile}
