#!/bin/bash
# Minimal HyperPod (EKS) lifecycle script for the trainer instance group.
# HyperPod's AMI already configures containerd, the NVIDIA driver and NVMe storage
# (/opt/sagemaker). Nothing sandbox-related runs on the trainer nodes: the GPU sandboxes run on
# EC2 node groups (scenario B1) or on the separate sandbox instance group (scenario B2,
# on_create_sandbox.sh).
set -euo pipefail

echo "[gpu-sandbox] on_create start: $(date -Is)"
echo "[gpu-sandbox] on_create done: $(date -Is)"
