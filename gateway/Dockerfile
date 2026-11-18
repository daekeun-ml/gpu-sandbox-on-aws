# syntax=docker/dockerfile:1.7
#
# Control-plane image: the production sandbox gateway and the operator tools
# (python -m gpusandbox.tools probe|parity|bench). No GPU, no torch.
ARG BASE_IMAGE=public.ecr.aws/docker/library/python:3.14-slim
FROM ${BASE_IMAGE}

WORKDIR /opt/gpusandbox
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[gateway]" \
 && python -c "import gpusandbox.gateway.app, gpusandbox.tools"

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin gateway
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["gpusandbox-gateway"]
