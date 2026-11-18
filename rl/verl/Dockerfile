# syntax=docker/dockerfile:1.7
#
# veRL trainer image (production track). veRL 0.9.1's [vllm] extra pins vllm 0.24.0,
# torch 2.11.0 and transformers 5.9.0, which differ from the TRL image, so it is a separate
# image. CUDA 13 builds need an NVIDIA driver of the 580 branch or newer on the node.
# Versions as of 2026-11; re-verify before building.
ARG BASE_IMAGE=vllm/vllm-openai:v0.24.0
FROM ${BASE_IMAGE}

ARG VERL_VERSION=0.9.1
WORKDIR /opt/gpusandbox
RUN pip freeze | grep -iE '^(torch|vllm|triton)==' > /tmp/constraints.txt \
 && pip install --no-cache-dir -c /tmp/constraints.txt "verl[vllm]==${VERL_VERSION}" "ray[default]" pandas pyarrow

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY rl ./rl
RUN pip install --no-cache-dir -c /tmp/constraints.txt ".[client]" \
 && python -c "import verl, gpusandbox.rewards; print('verl', verl.__version__)"

ENV PYTHONUNBUFFERED=1
ENTRYPOINT []
