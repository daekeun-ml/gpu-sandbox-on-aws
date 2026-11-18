# syntax=docker/dockerfile:1.7
#
# GPU sandbox image. The same image runs under gVisor, Kata + Cloud Hypervisor and
# Kata + QEMU.
#
# The NVIDIA kernel driver is never part of a container image:
#   * gVisor: the container talks to the host driver through nvproxy.
#   * Kata:   the container talks to the driver inside the guest VM.
# Only CUDA user-space libraries (bundled with the PyTorch wheels) live in this image.
#
# The CUDA 12.6 build keeps sm_75 (T4, the only bare-metal GPU family used for Kata in this
# asset) and needs an older minimum driver than CUDA 13 builds. Re-verify the tag before use.
ARG BASE_IMAGE=pytorch/pytorch:2.14.1-cuda12.6-cudnn9-runtime
FROM ${BASE_IMAGE}

# Triton compiles a small C launcher on first use, so a C toolchain is required at runtime.
# tini runs as PID 1 to reap zombies; the server reaps everything else after each request.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libc6-dev tini \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/gpusandbox
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
# The base image's Ubuntu Python is marked EXTERNALLY-MANAGED (PEP 668), and PyTorch itself is
# pip-installed into it, so install next to it the same way. Older pips ignore the variable.
RUN PIP_BREAK_SYSTEM_PACKAGES=1 pip install --no-cache-dir ".[server]" \
 && python -c "import gpusandbox.server.app, triton; print('triton', triton.__version__)"

# Unprivileged user. The pod spec enforces runAsNonRoot and a read-only root filesystem;
# /work and /tmp are emptyDir volumes. No credentials are ever mounted into this pod.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin sandbox
USER 10001:10001
ENV SANDBOX_WORK_ROOT=/work \
    HOME=/tmp \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["gpusandbox-server"]
