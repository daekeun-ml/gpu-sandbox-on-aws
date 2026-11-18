#!/usr/bin/env bash
# Build the three images for linux/amd64 and push them to private ECR repositories.
#   sandbox  runs in every sandbox pod (gVisor and Kata alike)
#   trainer  TRL + vLLM trainer (HYPERPOD=1 adds hyperpodrun for scenario B)
#   control  gateway and operator tools (probe, parity, bench)
# The base images are large (PyTorch, vLLM); build on an x86_64 host with 100+ GB disk if your
# workstation is arm64. Prints the image URIs to add to scripts/config.env.
#   --no-trainer  skip the trainer image (scenario C has no trainer and no GPU)
source "$(dirname "$0")/lib.sh"
require_tools aws docker
require_vars AWS_REGION ECR_REPO_PREFIX IMAGE_TAG

with_trainer=1
case "${1:-}" in
  "") ;;
  --no-trainer) with_trainer=0 ;;
  *) die "unknown option ${1}; use --no-trainer" ;;
esac

registry="$(ecr_registry)"
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${registry}"

build() {
  local name="$1" dockerfile="$2"; shift 2
  local repo="${ECR_REPO_PREFIX}/${name}"
  aws ecr describe-repositories --region "${AWS_REGION}" --repository-names "${repo}" >/dev/null 2>&1 \
    || aws ecr create-repository --region "${AWS_REGION}" --repository-name "${repo}" \
         --image-scanning-configuration scanOnPush=true --image-tag-mutability IMMUTABLE >/dev/null
  local uri="${registry}/${repo}:${IMAGE_TAG}"
  log "building ${uri}"
  # build runs inside "$(...)", where set -e is not inherited: without "|| die" a failed build
  # would still print the URI and the script would exit 0.
  docker buildx build --platform linux/amd64 -f "${dockerfile}" -t "${uri}" "$@" --push "${REPO_ROOT}" \
    || die "building ${uri} failed"
  echo "${uri}"
}

sandbox_uri="$(build sandbox sandbox/Dockerfile | tail -1)"
if (( with_trainer )); then
  trainer_uri="$(build trainer trainer/Dockerfile --build-arg "INSTALL_HYPERPOD_AGENT=${HYPERPOD:-0}" | tail -1)"
fi
control_uri="$(build control gateway/Dockerfile | tail -1)"

echo
echo "Add to scripts/config.env:"
echo "export SANDBOX_IMAGE_URI=\"${sandbox_uri}\""
(( with_trainer )) && echo "export TRAINER_IMAGE_URI=\"${trainer_uri}\""
echo "export CONTROL_IMAGE_URI=\"${control_uri}\""
