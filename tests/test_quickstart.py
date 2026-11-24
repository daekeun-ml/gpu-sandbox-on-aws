"""Exercise the README entry point without provisioning AWS resources."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def executable(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('#!/usr/bin/env bash\nset -eu\n' + body + '\n')
    path.chmod(0o755)


@pytest.fixture
def lab(tmp_path):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    for name in ('quickstart.sh', 'lib.sh', 'config.env.example'):
        shutil.copy2(ROOT / 'scripts' / name, scripts / name)
    bin_dir = tmp_path / 'bin'
    calls = tmp_path / 'calls'
    calls.touch()
    # Spy on the existing implementation scripts, keeping the real profile and dispatch logic.
    for path in [*(ROOT / 'scripts').rglob('*.sh'), ROOT / 'cdk/tunnel.sh']:
        if path.name in ('quickstart.sh', 'lib.sh'):
            continue
        rel = path.relative_to(ROOT)
        executable(tmp_path / rel, f'''echo "{rel} $* | runtime=${{ACTIVE_RUNTIME:-}} hp=${{HYPERPOD:-0}}" >> "$CALLS"
[[ "${{FAIL_SCRIPT:-}}" != {rel} ]]''')
    executable(bin_dir / 'aws', '''echo "aws $*" >> "$CALLS"
case "$1 $2" in
  'sts get-caller-identity') echo "${MOCK_ACCOUNT:-123456789012}" ;;
  'cloudformation describe-stacks') echo "${MOCK_STACK:-null}" ;;
esac''')
    executable(bin_dir / 'kubectl', '''echo "kubectl $*" >> "$CALLS"
if [[ "$*" == 'config current-context' ]]; then
  if [[ "$SCENARIO" == B2 ]]; then echo "${MOCK_CONTEXT:-$CLUSTER_NAME}"; else echo "${MOCK_CONTEXT:-$CLUSTER_NAME-tunnel}"; fi
fi''')
    for tool in ('uv', 'cdk', 'docker', 'helm', 'git'):
        executable(bin_dir / tool, 'echo "${0##*/} $*" >> "$CALLS"')
    if not shutil.which('jq'):
        executable(bin_dir / 'jq', 'exit 1')
    py = tmp_path / '.venv/bin/python'
    py.parent.mkdir(parents=True)
    py.symlink_to(sys.executable)
    env = {'PATH': f'{bin_dir}:{os.environ["PATH"]}', 'CALLS': str(calls), 'HOME': str(tmp_path)}

    def run(*args, stdin='', **overrides):
        return subprocess.run([scripts / 'quickstart.sh', *args], input=stdin, capture_output=True,
                              text=True, cwd=tmp_path, env={**env, **overrides}, timeout=15)

    return tmp_path, calls, run


@pytest.mark.parametrize('scenario,required', [
    ('A', ['scripts/02_create_cluster.sh  |', 'scripts/03_build_push_images.sh  | runtime= hp=0',
           'scripts/06_deploy_sandboxes.sh gvisor v1', 'scripts/07_run_grpo.sh 5']),
    ('B1', ['scripts/02_create_cluster.sh --hyperpod', 'scripts/03_build_push_images.sh  | runtime= hp=1',
            'scripts/hyperpod/create.sh', 'scripts/06_deploy_sandboxes.sh gvisor v1', 'scripts/hyperpod/run_grpo.sh 1']),
    ('B2', ['scripts/hyperpod/create_managed.sh', 'aws eks update-kubeconfig', 'scripts/03_build_push_images.sh  | runtime= hp=1',
            'scripts/hyperpod/reboot_sandboxes.sh', 'scripts/hyperpod/prepare_managed.sh', 'runtime=gvisor-hyperpod',
            'scripts/06_deploy_sandboxes.sh gvisor-hyperpod v1 2', 'scripts/hyperpod/run_grpo.sh 1',
            'scripts/hyperpod/bench_b2.sh 32']),
    ('C', ['scripts/02_create_cluster.sh --cpu-only', 'scripts/03_build_push_images.sh --no-trainer',
           'scripts/kata/cpu_nodes.sh', 'runtime=kata-clh-cpu', 'scripts/ops/verify.sh gvisor-cpu v1',
           'scripts/ops/verify.sh kata-qemu-cpu v1', 'scripts/ops/simulate.sh 30 20']),
])
def test_guided_routes(lab, scenario, required):
    root, calls, run = lab
    plan = run(scenario, 'plan')
    assert plan.returncode == 0 and 'infra' in plan.stdout
    assert calls.read_text() == '' and not (root / '.quickstart').exists()
    result = run(scenario, stdin='\n' * 12)
    assert result.returncode == 0, result.stderr
    logs = calls.read_text()
    offsets = [logs.index(command) for command in required]
    assert offsets == sorted(offsets)
    assert 'delete-stack' not in logs and 'scripts/08_cleanup' not in logs
    assert not (root / 'scripts/config.env').exists()
    if scenario == 'B2':
        assert 'cdk bootstrap' not in logs and '02_create_cluster' not in logs and 'cdk/tunnel.sh' not in logs
    if scenario == 'C':
        assert '07_run_grpo' not in logs and '04_install_gpu_stack' not in logs
        assert run('C', 'switch').returncode == 0
        assert 'scripts/ops/rollout.sh kata-clh-cpu v1 v2' in calls.read_text()


def test_profiles_and_failure_boundaries(lab):
    root, calls, run = lab
    for scenario, region in [('C', 'us-west-2'), ('B2', 'us-east-1')]:
        assert run(scenario, 'init').returncode == 0
        profile = root / '.quickstart' / scenario / 'config.env'
        text = profile.read_text()
        assert re.findall(r'^export AWS_REGION=(.*)$', text, re.M) == [region]
        profile.write_text(text + '\n# Keep manual changes\n')
        assert run(scenario, 'init').returncode == 0 and profile.read_text().endswith('# Keep manual changes\n')
    assert run('B2', 'tunnel').returncode != 0
    assert run('A', 'pool run').returncode != 0
    assert run('B2', 'pool', MOCK_ACCOUNT='000000000001').returncode != 0
    assert run('B2', 'pool', MOCK_CONTEXT='unrelated-cluster').returncode != 0
    assert '06_deploy_sandboxes' not in calls.read_text()
    result = run('B2', stdin='\n' * 12, FAIL_SCRIPT='scripts/hyperpod/reboot_sandboxes.sh')
    assert result.returncode != 0 and 'prepare_managed' not in calls.read_text()
    assert run('A', stdin='q\n').returncode == 0 and not (root / '.quickstart/A').exists()


def test_managed_cleanup_checks_stack_and_confirmation(lab):
    if not shutil.which('jq'):
        pytest.skip('managed stack validation uses jq')
    _, calls, run = lab
    assert run('B2', 'init').returncode == 0
    name = 'gpu-sandbox-qs-b2-eks-hyperpod'
    stack = {'Tags': [{'Key': 'project', 'Value': 'gpu-sandbox-on-aws'}],
             'Parameters': [{'ParameterKey': 'HyperPodClusterName', 'ParameterValue': 'gpu-sandbox-qs-b2-hp'}]}
    unrelated = json.dumps({'Stacks': [{**stack, 'Tags': []}]})
    assert run('B2', 'cleanup', stdin=name + '\n', MOCK_STACK=unrelated).returncode != 0
    valid = json.dumps({'Stacks': [stack]})
    assert run('B2', 'cleanup', stdin='q\n', MOCK_STACK=valid).returncode != 0
    assert 'cloudformation delete-stack' not in calls.read_text()
    assert run('B2', 'cleanup', stdin=name + '\n', MOCK_STACK=valid).returncode == 0
    assert f'cloudformation delete-stack --region us-east-1 --stack-name {name}' in calls.read_text()


def test_b1_cleanup_after_an_interrupted_deployment(lab):
    root, calls, run = lab
    assert run('B1', 'init').returncode == 0
    shutil.copy2(ROOT / 'scripts/hyperpod/delete.sh', root / 'scripts/hyperpod/delete.sh')
    executable(root / 'bin/aws', '''echo "aws $*" >> "$CALLS"
case "$1 $2" in
  'sts get-caller-identity') echo 123456789012 ;;
  'sagemaker describe-cluster') echo "${MOCK_STATUS_ERROR:-ResourceNotFound}" >&2; exit 1 ;;
  'iam get-role') echo NoSuchEntity >&2; exit 1 ;;
  's3api head-bucket') echo '(404)' >&2; exit 1 ;;
  *) exit 9 ;;
esac''')
    name = 'gpu-sandbox-qs-b1-hp\n'
    assert run('B1', 'cleanup', stdin=name, MOCK_STATUS_ERROR='AccessDenied').returncode != 0
    assert 'scripts/08_cleanup.sh' not in calls.read_text()
    assert run('B1', 'cleanup', stdin=name).returncode == 0
    assert 'scripts/08_cleanup.sh' in calls.read_text() and 'sagemaker delete-cluster' not in calls.read_text()


def test_resume_partial_image_build(lab):
    root, calls, run = lab
    assert run('C', 'init').returncode == 0
    shutil.copy2(ROOT / 'scripts/03_build_push_images.sh', root / 'scripts/03_build_push_images.sh')
    executable(root / 'bin/aws', '''echo "aws $*" >> "$CALLS"
case "$1 $2" in
  'sts get-caller-identity') echo 123456789012 ;;
  'ecr describe-images')
    if [[ "$*" == *'/control'* ]]; then echo "${MOCK_LOOKUP_ERROR:-ImageNotFoundException}" >&2; exit 1; fi ;;
esac''')
    assert run('C', 'images', MOCK_LOOKUP_ERROR='AccessDenied').returncode != 0
    assert 'docker buildx build' not in calls.read_text()
    assert run('C', 'images').returncode == 0
    builds = [line for line in calls.read_text().splitlines() if 'docker buildx build' in line]
    assert len(builds) == 1 and 'gpu-sandbox-qs-c/control:v1' in builds[0]
