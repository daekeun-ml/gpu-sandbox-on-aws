#!/usr/bin/env bash
# Run the workshop from a checkout. Each named step can also be invoked on its own.
set -euo pipefail
cd "$(dirname "$0")/.."
root="$PWD"
usage() {
  cat <<'EOF'
Usage: scripts/quickstart.sh local
       scripts/quickstart.sh A|B1|B2|C [plan|STEP]

local   Grade sample submissions on CPU. Requires uv; no AWS account needed.
A       Train and grade on EC2 GPUs (5 GRPO steps).
B1      Train on HyperPod and grade on EC2 GPUs (1 GRPO step).
B2      Run all workers on HyperPod, then benchmark both clients.
C       Compare CPU runtimes and switch grading versions during a simulation.

With only a scenario name, press Enter to execute each step, or q to stop.
Use 'plan' to see the order without creating resources. To resume, run a named
step. Invoke 'cleanup' separately when finished. Configuration and trainer logs
are kept in .quickstart/<scenario>/. Set AWS_PROFILE before starting if needed.
EOF
}
fail() { echo "quickstart: $*" >&2; exit 1; }
if (($# == 0)); then
  usage
  [[ -t 0 ]] || exit 0
  read -r -p 'Choose local, A, B1, B2 or C: ' selection
  set -- "$selection"
fi
case "$1" in -h|--help) usage; exit 0 ;; esac
(($# <= 2)) || { usage >&2; exit 2; }
scenario="$1"
action="${2:-guide}"
case "$scenario" in
  local)
    (($# == 1)) || fail 'local takes no further arguments'
    py="$root/.venv/bin/python"
    if [[ ! -x "$py" ]]; then uv venv --python 3.14 .venv; fi
    if ! "$py" -c 'import torch, numpy' 2>/dev/null; then
      if [[ "$(uname -s)" == Linux ]]; then
        uv pip install --python "$py" --index-url https://download.pytorch.org/whl/cpu torch numpy
      else
        uv pip install --python "$py" torch numpy
      fi
    fi
    if ! "$py" -c 'import pytest, gpusandbox, httpx, fastapi, uvicorn, jwt, prometheus_client' 2>/dev/null; then
      uv pip install --python "$py" -e '.[dev]'
    fi
    exec "$py" -m pytest -v tests/test_server_and_client.py::test_golden_probe_and_parity_on_cpu_pools ;;
  A|B1|B2|C) ;;
  *) usage >&2; exit 2 ;;
esac
steps=(init check infra connect images runtime)
[[ "$scenario" != B1 ]] || steps+=(trainer)
steps+=(pool run)
[[ "$scenario" != B2 ]] || steps+=(bench)
extras=(cleanup)
[[ "$scenario" == B2 ]] || extras+=(tunnel bench)
[[ "$scenario" != C ]] || extras+=(switch)
plan() {
  printf 'Scenario %s\n' "$scenario"
  local i step description
  for ((i=0; i<${#steps[@]}; i++)); do
    step="${steps[i]}"
    case "$step" in
      init) description='Create or open the scenario configuration' ;;
      check) description='Check tools, account and regional quotas' ;;
      infra) description='Provision the cluster and its initial workers (billable)' ;;
      connect) description='Connect kubectl and list the nodes' ;;
      images) description='Build and push images to ECR' ;;
      runtime) description='Prepare the grading runtimes' ;;
      trainer) description='Attach the HyperPod training node to EKS' ;;
      pool) description='Deploy and verify the v1 grading pools' ;;
      run) description='Submit the workload and read its results' ;;
      bench) description='Benchmark the system and training clients in sequence' ;;
    esac
    printf '%2d. %-8s %s\n' "$((i+1))" "$step" "$description"
  done
  printf 'Separate commands: %s\n' "${extras[*]}"
}
[[ "$action" != plan ]] || { plan; exit 0; }
[[ "$action" =~ ^[a-z]+$ ]] || fail "unknown step: $action"
case " ${steps[*]} ${extras[*]} guide " in *" $action "*) ;; *) fail "unknown step '$action'; run $0 $scenario plan" ;; esac
folder="$root/.quickstart/$scenario"
export GPUSANDBOX_CONFIG="$folder/config.env" AWS_PAGER=''
# Keep kubectl/Helm and the foreground SSM tunnel on the same isolated context.
export KUBECONFIG="$folder/kubeconfig"
export PATH="$root/.venv/bin:$PATH"
init_config() {
  if [[ -f "$GPUSANDBOX_CONFIG" ]]; then printf 'Using %s\n' "$GPUSANDBOX_CONFIG"; return; fi
  local region="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-west-2}}" account suffix prefix
  if [[ "$scenario" == B2 ]]; then region="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"; fi
  account=$(aws sts get-caller-identity --region "$region" --query Account --output text)
  [[ "$account" =~ ^[0-9]{12}$ ]] || fail 'could not determine the AWS account'
  suffix=$(printf '%s' "$scenario" | tr '[:upper:]' '[:lower:]'); prefix="gpu-sandbox-qs-$suffix"
  mkdir -p "$folder"
  (
    umask 077
    tmp=$(mktemp "$folder/config.XXXXXX"); trap 'rm -f "$tmp"' EXIT
    # Set each value once so edits to the generated profile take effect.
    python3 - "$scenario" "$account" "$region" "$prefix" > "$tmp" <<'PYCONFIG'
from pathlib import Path
import re
import shlex
import sys

scenario, account, region, prefix = sys.argv[1:]
values = {
    'SCENARIO': scenario, 'AWS_REGION': region, 'CLUSTER_NAME': prefix + '-eks',
    'ECR_REPO_PREFIX': prefix, 'HYPERPOD_CLUSTER_NAME': prefix + '-hp',
    'HYPERPOD_LCS_BUCKET': f'sagemaker-qs-{scenario.lower()}-{account}-{region}',
}
if scenario == 'B2' and region == 'us-east-1':
    values['HYPERPOD_AZ_IDS'] = 'use1-az1,use1-az2'
for line in Path('scripts/config.env.example').read_text().splitlines()[2:]:
    key = re.match(r'export (\w+)=', line)
    if key and key[1] in values:
        line = f'export {key[1]}={shlex.quote(values[key[1]])}'
    print(line)
print('\n# Quickstart account and images for this scenario.')
print(f'export QUICKSTART_ACCOUNT={account}')
if scenario == 'C':
    print('export KATA_CPU_REPLICAS=1')
images = ['sandbox', 'control'] if scenario == 'C' else ['sandbox', 'control', 'trainer']
for image in images:
    print(f'export {image.upper()}_IMAGE_URI="$QUICKSTART_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_PREFIX/{image}:$IMAGE_TAG"')
PYCONFIG
    # Do not replace an existing configuration, including one created by another run.
    ln "$tmp" "$GPUSANDBOX_CONFIG" || [[ -f "$GPUSANDBOX_CONFIG" ]]
  )
  printf 'Review %s before deployment (region, names, role ARN, quotas).\n' "$GPUSANDBOX_CONFIG"
}
load_config() {
  [[ -f "$GPUSANDBOX_CONFIG" ]] || fail "run scripts/quickstart.sh $scenario init first"
  # shellcheck source=scripts/lib.sh
  source scripts/lib.sh
  [[ "$SCENARIO" == "$scenario" ]] || fail "SCENARIO in $GPUSANDBOX_CONFIG must be $scenario"
  [[ "$(account_id)" == "$QUICKSTART_ACCOUNT" ]] || fail 'AWS account differs from the configuration; check AWS_PROFILE'
}
check_tools() {
  require_tools aws kubectl helm docker jq python3
  docker buildx version
  if [[ "$scenario" != B2 ]]; then
    require_tools uv
    scripts/01_check_prereqs.sh
    case "$scenario" in
      A) echo 'Required free EC2 vCPUs: 6 Standard, 16 G/VT.' ;;
      B1) echo 'Required free EC2 vCPUs: 6 Standard, 8 G/VT.' ;;
      C) echo 'Required: 14 free Standard vCPUs and nested virtualization on the c8i node.' ;;
    esac
  fi
  if [[ "$scenario" == B1 || "$scenario" == B2 ]]; then
    echo "Check SageMaker cluster usage quotas in $AWS_REGION for $HYPERPOD_TRAINER_INSTANCE_TYPE (1 trainer)."
    if [[ "$scenario" == B2 ]]; then
      ((BASH_VERSINFO[0] >= 4)) || fail "B2 needs Bash 4 or later"
      require_vars HYPERPOD_AZ_IDS
      echo "Also check $HYPERPOD_SYSTEM_INSTANCE_TYPE (1 system) and $HYPERPOD_SANDBOX_INSTANCE_TYPE ($HYPERPOD_SANDBOX_COUNT graders)."
    else require_tools git; fi
    local types=("$HYPERPOD_TRAINER_INSTANCE_TYPE") type code
    [[ "$scenario" != B2 ]] || types+=("$HYPERPOD_SYSTEM_INSTANCE_TYPE" "$HYPERPOD_SANDBOX_INSTANCE_TYPE")
    for type in "${types[@]}"; do
      case "$type" in
        ml.g5.2xlarge) code=L-596C3331 ;;
        ml.g5.xlarge) code=L-4645950E ;;
        ml.m5.xlarge) code=L-E9225B85 ;;
        *) aws service-quotas list-service-quotas --service-code sagemaker --region "$AWS_REGION" \
             --query "Quotas[?QuotaName=='$type for cluster usage'].[QuotaName,Value]" --output table
           continue ;;
      esac
      aws service-quotas get-service-quota --service-code sagemaker --region "$AWS_REGION" \
        --quota-code "$code" --query 'Quota.[QuotaName,Value]' --output text
    done
  fi
}
infra() {
  if [[ "$scenario" == B2 ]]; then
    scripts/hyperpod/create_managed.sh
    aws cloudformation wait stack-create-complete --region "$AWS_REGION" --stack-name "${HYPERPOD_MANAGED_STACK:-$CLUSTER_NAME-hyperpod}"
  else
    require_tools uv
    [[ -x "$root/.venv/bin/python" ]] || uv venv --python 3.14 .venv
    uv pip install --python "$root/.venv/bin/python" -r cdk/requirements.txt
    cdk bootstrap "aws://$QUICKSTART_ACCOUNT/$AWS_REGION"
    case "$scenario" in
      A) scripts/02_create_cluster.sh ;;
      B1) scripts/02_create_cluster.sh --hyperpod ;;
      C) scripts/02_create_cluster.sh --cpu-only ;;
    esac
  fi
}
connect_cluster() {
  if [[ "$scenario" == B2 ]]; then
    aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME" --alias "$CLUSTER_NAME"
  else
    echo "In a second terminal, run: scripts/quickstart.sh $scenario tunnel"
    echo 'Keep that terminal open. Continue here when port 8443 is open.'
    if [[ -t 0 ]]; then read -r -p 'Press Enter when connected: ' _; fi
  fi
  kubectl get nodes -L gpusandbox/role
}
runtime() {
  case "$scenario" in
    C) scripts/kata/cpu_nodes.sh ;;
    B2) scripts/hyperpod/reboot_sandboxes.sh; scripts/hyperpod/prepare_managed.sh; scripts/04_install_gpu_stack.sh ;;
    *) scripts/04_install_gpu_stack.sh ;;
  esac
}
pools() {
  local runtimes=(gvisor) runtime_name
  case "$scenario" in
    C) runtimes=(kata-clh-cpu gvisor-cpu kata-qemu-cpu) ;;
    B2) runtimes=(gvisor-hyperpod) ;;
  esac
  ACTIVE_RUNTIME="${runtimes[0]}" scripts/05_setup_namespaces_auth.sh
  if [[ "$scenario" == B2 ]]; then kubectl apply -f k8s/runtimes/runtimeclass-gvisor-hyperpod.yaml; fi
  for runtime_name in "${runtimes[@]}"; do
    if [[ "$scenario" == B2 ]]; then
      scripts/06_deploy_sandboxes.sh "$runtime_name" v1 "$HYPERPOD_SANDBOX_COUNT"
    else
      scripts/06_deploy_sandboxes.sh "$runtime_name" v1
    fi
    scripts/ops/verify.sh "$runtime_name" v1
  done
  echo 'Compare the sandbox and node kernel versions in the verification output.'
}
workload() {
  local job
  case "$scenario" in
    A)
      scripts/07_run_grpo.sh 5 | tee "$folder/grpo-$RUN_ID.log"
      kubectl -n rl-trainer wait --for=condition=Complete "job/grpo-$RUN_ID" --timeout=30m ;;
    B1|B2)
      job="grpo-$RUN_ID"
      scripts/hyperpod/run_grpo.sh 1
      kubectl -n rl-trainer wait --for=create pods -l "HPJob=$job" --timeout=10m
      kubectl -n rl-trainer wait --for=condition=Ready pods -l "HPJob=$job" --timeout=30m
      kubectl -n rl-trainer get pods -l "HPJob=$job" -o wide | tee "$folder/$job-placement.txt"
      kubectl -n rl-trainer logs -f -l "HPJob=$job" -c pytorch --tail=-1 | tee "$folder/$job.log"
      kubectl -n rl-trainer wait --for=condition=Completed "hyperpodpytorchjob/$job" --timeout=30m ;;
    C)
      echo 'After the first v1 batch, run scripts/quickstart.sh C switch in a second work terminal.'
      scripts/ops/simulate.sh 30 20 ;;
  esac
}
cleanup() {
  case "$scenario" in
    B2)
      local stack="${HYPERPOD_MANAGED_STACK:-$CLUSTER_NAME-hyperpod}"
      aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$stack" --output json | jq -e \
        --arg hp "$HYPERPOD_CLUSTER_NAME" '.Stacks[0] | any(.Tags[]?; .Key=="project" and .Value=="gpu-sandbox-on-aws") and any(.Parameters[]?; .ParameterKey=="HyperPodClusterName" and .ParameterValue==$hp)' >/dev/null
      confirm "$stack" "Delete the B2 stack and its EKS and HyperPod clusters in $AWS_REGION?"
      aws cloudformation delete-stack --region "$AWS_REGION" --stack-name "$stack"
      aws cloudformation wait stack-delete-complete --region "$AWS_REGION" --stack-name "$stack"
      echo "Stack deleted. Retained: lifecycle bucket $HYPERPOD_LCS_BUCKET, ECR repositories under $ECR_REPO_PREFIX, and CloudWatch logs." ;;
    B1) scripts/hyperpod/delete.sh; scripts/08_cleanup.sh ;;
    *) scripts/08_cleanup.sh ;;
  esac
}
run_step() {
  local step="$1"
  if [[ "$step" == init ]]; then init_config; return; fi
  load_config
  case "$step" in
    runtime|trainer|pool|run|bench|switch|cleanup)
      local expected="$CLUSTER_NAME-tunnel"
      [[ "$scenario" != B2 ]] || expected="$CLUSTER_NAME"
      if [[ "$step" != cleanup || ( "$scenario" != B2 && -s "$KUBECONFIG" ) ]]; then
        [[ "$(kubectl config current-context)" == "$expected" ]] || fail "expected kubectl context $expected; repeat the connect step"
      fi ;;
  esac
  printf '\n[%s / %s] %s  %s  %s\n' "$scenario" "$step" "$QUICKSTART_ACCOUNT" "$AWS_REGION" "$CLUSTER_NAME"
  case "$step" in
    check) check_tools ;;
    infra) infra ;;
    tunnel) cdk/tunnel.sh ;;
    connect) connect_cluster ;;
    images)
      export REUSE_EXISTING_IMAGES=1
      case "$scenario" in
        C) scripts/03_build_push_images.sh --no-trainer ;;
        B1|B2) HYPERPOD=1 scripts/03_build_push_images.sh ;;
        A) scripts/03_build_push_images.sh ;;
      esac
      echo "Image URIs are already configured in $GPUSANDBOX_CONFIG." ;;
    runtime) runtime ;;
    trainer) scripts/hyperpod/create.sh ;;
    pool) pools ;;
    run) export RUN_ID="${RUN_ID:-qs-$(date +%Y%m%d-%H%M%S)-$$}"; workload ;;
    bench)
      if [[ "$scenario" == B2 ]]; then BENCH_OUT_DIR="$folder" scripts/hyperpod/bench_b2.sh 32; else scripts/ops/bench.sh 32; fi ;;
    switch) scripts/ops/rollout.sh kata-clh-cpu v1 v2 ;;
    cleanup) cleanup ;;
  esac
}
if [[ "$action" != guide ]]; then run_step "$action"; exit; fi
plan
for step in "${steps[@]}"; do
  printf '\nNext: scripts/quickstart.sh %s %s\n' "$scenario" "$step"
  read -r -p 'Enter to run, q to leave: ' answer || exit 0
  [[ -z "$answer" ]] || exit 0
  run_step "$step"
done
printf '\nFinished. To remove provisioned compute: scripts/quickstart.sh %s cleanup\n' "$scenario"
