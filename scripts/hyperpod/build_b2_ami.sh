#!/usr/bin/env bash
# Scenario B2, step 1: build the custom HyperPod AMI (NVIDIA driver that gVisor nvproxy supports,
# plus the pinned gVisor binaries). Run before scripts/hyperpod/create.sh --b2.
# Billable: one m6i.large for the build (20-40 min) and the AMI's EBS snapshot until you delete
# it (scripts/08_cleanup.sh asks).
source "$(dirname "$0")/../lib.sh"
"${REPO_ROOT}/infra/hyperpod/ami/build-b2-ami.sh"
