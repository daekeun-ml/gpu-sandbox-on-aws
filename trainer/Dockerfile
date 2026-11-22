# syntax=docker/dockerfile:1.7
#
# On-policy GRPO trainer image (TRL + vLLM colocate mode) for the hands-on track.
#
# TRL 1.18.0 declares vllm>=0.23.0,<0.34.0, and vllm 0.33.0 pins torch 2.14.0 and
# transformers>=5.16.1,<5.21.0. Starting from the vLLM image keeps that triangle consistent;
# the constraints file stops pip from upgrading torch/transformers/vllm underneath it.
# HyperPod elastic agent 1.1.3 requires torch < 2.12. Its vLLM 0.26 base uses torch 2.11.
ARG BASE_IMAGE=vllm/vllm-openai:v0.33.0
ARG HYPERPOD_BASE_IMAGE=vllm/vllm-openai:v0.26.0
ARG INSTALL_HYPERPOD_AGENT=0
FROM ${BASE_IMAGE} AS trainer-0
FROM ${HYPERPOD_BASE_IMAGE} AS trainer-1
FROM trainer-${INSTALL_HYPERPOD_AGENT}

# The vLLM image has python3 (3.12) but no "python" command, and the import check below, CMD
# and the Job spec (k8s/trainer/job-grpo.yaml.tpl) all call "python".
RUN command -v python >/dev/null 2>&1 || ln -s "$(command -v python3)" /usr/local/bin/python

ARG TRL_VERSION=1.18.0
ARG PEFT_VERSION=0.21.3
# Set INSTALL_HYPERPOD_AGENT=1 for the HyperPod track (HyperPodPyTorchJob uses hyperpodrun).
ARG INSTALL_HYPERPOD_AGENT=0

WORKDIR /opt/gpusandbox
RUN pip freeze | grep -iE '^(torch|transformers|vllm|triton)==' > /tmp/constraints.txt \
 && pip install --no-cache-dir -c /tmp/constraints.txt \
      "trl==${TRL_VERSION}" "peft==${PEFT_VERSION}" "datasets>=4.7" \
 && if [ "${INSTALL_HYPERPOD_AGENT}" = "1" ]; then \
      pip install --no-cache-dir -c /tmp/constraints.txt hyperpod-elastic-agent==1.1.3 \
      && hyperpodrun --help >/dev/null; \
    fi

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY rl ./rl
RUN pip install --no-cache-dir -c /tmp/constraints.txt ".[client]" \
 && python -c "import trl, peft, vllm, gpusandbox.rewards; print('trl', trl.__version__, 'vllm', vllm.__version__)"

# k8s/trainer/job-grpo.yaml.tpl runs as uid 2000 (Pod Security "restricted"). The vLLM image ships
# that user as "vllm"; create it if another BASE_IMAGE lacks it, so the home and passwd entry exist.
RUN id -u vllm >/dev/null 2>&1 || useradd --uid 2000 --gid 0 --create-home --shell /usr/sbin/nologin vllm

ENV PYTHONUNBUFFERED=1
# The vLLM image's entrypoint starts an OpenAI server; the Job spec sets the command.
ENTRYPOINT []
CMD ["python", "/opt/gpusandbox/rl/trl/train_grpo.py", "--help"]
