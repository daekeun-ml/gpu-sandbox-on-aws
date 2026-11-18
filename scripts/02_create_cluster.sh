#!/usr/bin/env bash
# Create the AWS infrastructure (VPC, EKS with a private API endpoint, node groups) with CDK.
#   scripts/02_create_cluster.sh                 scenario A: EC2 trainer + gVisor GPU nodes
#   scripts/02_create_cluster.sh --hyperpod      scenario B1: gVisor GPU nodes; the trainer runs on HyperPod
#   scripts/02_create_cluster.sh --hyperpod-b2   scenario B2: no EC2 GPU node groups (all on HyperPod)
#   scripts/02_create_cluster.sh --cpu-only      scenario C: the nested-virtualization CPU node only
# Add the Kata node groups with WITH_KATA_CPU=1 and WITH_KATA_GPU=1 in scripts/config.env and run
# this again: CDK changes only what differs (scripts/kata/cpu_nodes.sh and gpu_nodes.sh say when).
#
# The EKS API endpoint is not reachable from the internet. Open cdk/tunnel.sh in a second
# terminal before any kubectl or helm step.
# Billable: EKS control plane, NAT gateway, 2x m6i.large, the access instance, plus 2x g5.xlarge
# (A, B1) and g5.2xlarge (A).
source "$(dirname "$0")/lib.sh"

case "${1:-}" in
  "") scenario="${SCENARIO:-A}" ;;
  --hyperpod) scenario="B1" ;;
  --hyperpod-b2) scenario="B2" ;;
  --cpu-only) scenario="C" ;;
  *) die "unknown option ${1}; use --hyperpod, --hyperpod-b2 or --cpu-only" ;;
esac
export SCENARIO="${scenario}"
"${REPO_ROOT}/cdk/deploy.sh" "${scenario}"
