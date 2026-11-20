# Misconceptions

!!! info "TL;DR"
    This page corrects 21 misconceptions that come up when you first work with GPU sandboxes and on-policy RL.

## Pain point

Since 2026-02, EC2 supports nested virtualization on some virtual instance types such as C8i, M8i and R8i, so "Kata needs `.metal`" now holds only when Kata assigns a GPU directly to the VM. gVisor, Kata and Firecracker are all called sandboxes, but each handles GPUs differently. It is also easy to assume that the default network policy of an open-source template, or a managed service, blocks all the traffic it should. And some errors go unnoticed because training keeps running: a rolling update, or scoring infrastructure errors as 0, makes the rewards wrong without stopping training.

![a: a mid-run sandbox version change done as a rolling update scores one group by two rules, and reward 0 on infrastructure errors such as a pod failure suppresses correct answers that were zeroed; in both cases training does not stop and rewards drift silently. b: version changes switch blue/green pools, and each reward batch is scored by one version only, and infrastructure errors become sandbox_error, which TRL returns as None to leave out of the baseline, so the group-relative advantage holds one version and scored samples only](../images/figures/reference-faq.svg)

*Takeaway: In both cases training keeps running, so nothing looks wrong while the rewards drift. Changing versions through blue/green pools while scoring each batch with one version only, and dropping unscored samples with None, as TRL does, keeps the group-relative advantage sound.*


## Why

- **Kata has different requirements for CPU and GPU sandboxes.** A CPU sandbox needs only `/dev/kvm`; assigning a GPU directly to the VM also needs the host to use the IOMMU directly.

**Before you start:** the scenarios A, B1 and B2 and the validation status on [Home](../index.md), how gVisor and Kata handle GPUs in [02 Isolation runtimes](../concepts/02_isolation_runtimes.md), and GRPO groups and advantages in [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md) make this page easier to read.

??? note "Terms"
    - **RuntimeClass**: the Kubernetes object that selects the container runtime (runc, gVisor, Kata) a pod runs with.
    - **nested virtualization**: running a virtual machine inside a virtual machine. On EC2, some families provide `/dev/kvm` for this.
    - **bare metal (`.metal`)**: an EC2 instance that uses the whole physical server without a hypervisor.
    - **GPU passthrough, VFIO, IOMMU**: handing a whole physical GPU to a VM (GPU passthrough), the Linux kernel feature that makes it possible (VFIO), and the hardware that confines a device's memory access to the VM (IOMMU).
    - **nvproxy, ioctl**: an ioctl is the system call a program uses to send commands to a driver; nvproxy is the gVisor layer that forwards only allowed ioctls to the GPU driver.
    - **NetworkPolicy**: the Kubernetes object that restricts traffic between pods and out of pods with allowlists.
    - **IMDS**: the metadata service (`169.254.169.254`) from which an EC2 instance gets its own information and IAM credentials.
    - **TokenReview**: the API that asks the Kubernetes API server whether a token is valid.
    - **blue/green**: a deployment method that starts the new version next to the old one, verifies it, and then moves traffic at once.
    - **golden submissions, parity**: golden submissions have known verdicts; parity is the check that two sandbox versions return the same verdicts for them.
    - **warm pool**: a set of sandboxes started in advance, before requests arrive.

    More terms are in the [Glossary](glossary.md).

## Runtimes and instances

!!! question "❓ Misconception: Kata needs a `.metal` instance"
    **Actually:** you need `.metal` only to hand a GPU to the Kata VM (GPU passthrough). CPU sandboxes run on regular VMs such as C8i, M8i and R8i with EC2 nested virtualization turned on (launched 2026-02-16).

    Kata can start a VM as long as `/dev/kvm` exists, but GPU passthrough needs a host that owns the physical GPU and the IOMMU. No G or P family supports nested virtualization, and the only x86 NVIDIA GPU bare metal type is `g4dn.metal`, so Kata + GPU still needs `.metal`.

    The following command lists the instance types that support nested virtualization in the current Region.

    ```bash
    # Instance types that support nested virtualization in the current Region
    aws ec2 describe-instance-types \
      --filters "Name=processor-info.supported-features,Values=nested-virtualization" \
      --query 'InstanceTypes[].InstanceType' --output text
    ```

    **What to look for:** if the list shows types such as `c8i.2xlarge`, you can create Kata CPU nodes in that Region. **If it fails:** see the Kata table in [Troubleshooting](troubleshooting.md). Details: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md), [03 Kata sandboxes](../handson/03_kata.md)

!!! question "❓ Misconception: gVisor's GPU isolation equals a VM boundary"
    **Actually:** gVisor shares the host's NVIDIA driver as it is, so it is weaker than a VM boundary.

    nvproxy reduces the exposed surface with an ioctl allowlist per driver version, but the gVisor documentation says it is "much less effective" at mitigating vulnerabilities inside the driver itself and that there is no validation of things like DMA buffers. The GKE Sandbox documentation also advises against GPU time-sharing in sandboxed pods. If the driver itself must be separated, choose Kata + VFIO, where the guest has its own driver. Details: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md), [02 Security](../production/02_security.md)

!!! question "❓ Misconception: Firecracker can pass a GPU through"
    **Actually:** Firecracker does not provide GPU passthrough.

    Firecracker uses a minimal device model built around virtio devices. PCI support was added in 1.13.0, but the changelog has no VFIO GPU passthrough. That is the background for Firecracker-based sandboxes such as E2B being mostly CPU only. This asset uses gVisor (nvproxy) or Kata + QEMU (VFIO) for GPU sandboxes. Details: [01 When the sandbox needs a GPU](../concepts/01_why_gpu_sandbox.md)

!!! question "❓ Misconception: Kata + Cloud Hypervisor can pass a GPU through just like QEMU"
    **Actually:** upstream does not support GPU passthrough with Cloud Hypervisor. The supported Kata GPU path is QEMU (`kata-qemu-nvidia-gpu`).

    Kata's `docs/hypervisors.md` marks GPU support for Cloud Hypervisor as not supported, and a maintainer answered in 2025-08 that you should use the QEMU GPU runtime class (issue #11687). This asset's `kata-clh-nvidia-gpu` is an experiment for evaluation, and Kata + Cloud Hypervisor is used as a CPU sandbox (`kata-clh-cpu`). Details: [03 Kata sandboxes](../handson/03_kata.md)

!!! question "❓ Misconception: Triton kernels obviously work on the Kata GPU pool (T4) too"
    **Actually:** whether Triton kernels work on T4 (`g4dn.metal`) has to be checked on your nodes with the golden kernels. This guide does not assert the range of GPUs that Triton officially supports.

    The T4 and Kata combination is also outside NVIDIA's Kata CI coverage (A100, H100). The following command sends the golden set to the Kata GPU pool and checks the verdicts.

    ```bash
    scripts/ops/verify.sh kata-qemu v1
    ```

    **What to look for:** in the output of step 3, `PASS` for `vector_add_triton` and `relu_bias_triton` means a Triton kernel compiled and ran on that pool and was classified as a custom kernel. **If it fails:** see the Kata table and the "Sandbox pools and readiness" table in [Troubleshooting](troubleshooting.md). Details: [04 Reward integrity](../production/04_reward_integrity.md)

## Platforms and managed services

!!! question "❓ Misconception: these sandboxes can run on default-AMI HyperPod nodes today"
    **Actually:** with the default AMI (Kubernetes 1.36), neither gVisor GPU sandboxes nor Kata GPU sandboxes can run on HyperPod nodes. The default scenario B1 runs only the training on HyperPod and keeps the sandboxes on EC2 nodes in the same EKS cluster. B2 is configured to run gVisor sandboxes on HyperPod nodes with a custom AMI that carries a supported driver, but it has not been run on AWS yet.

    The default AMI is blocked because the nvproxy of gVisor release-20261109.0 does not know the NVIDIA driver 595.91.07 in the HyperPod EKS AMIs (1.34 to 1.36) (unknown versions, which are not on the list, fail regardless of flags). B2 meets the condition by baking a custom AMI from the HyperPod public base AMI with the driver replaced by 580.178.04 and the pinned gVisor installed. When a node starts, the lifecycle script registers `runsc` with containerd ([B2 in 07 HyperPod scenario](../handson/07_hyperpod.md#b2)). Kata GPU sandboxes are not possible regardless of the Kubernetes version or the AMI. There are no `ml.*.metal` types, CreateCluster has no nested virtualization CPU option, and the G and P families do not support nested virtualization. Kata without a GPU is probably blocked by the same `/dev/kvm` requirement, but this is untested (inference), and the repository has no Kata setup for HyperPod. The following command starts a debug pod on each HyperPod node and prints the driver and whether gVisor supports it. At the end it deletes every pod in the `default` namespace whose name starts with `node-debugger-`, so if someone else is inspecting a node with `kubectl debug node`, wait until they finish.

    ```bash
    scripts/hyperpod/check_gvisor.sh
    ```

    **What to look for:** default-AMI nodes print `NOT supported by gVisor ...: keep sandboxes on EC2 (mode B1)`, and B2 custom-AMI nodes print `driver 580.178.04: SUPPORTED ...`. Run it again when a new AMI or gVisor release comes out. **If it fails:** see the HyperPod table in [Troubleshooting](troubleshooting.md). Details: [04 Platforms and instances](../concepts/04_platforms_and_instances.md), [07 HyperPod scenario](../handson/07_hyperpod.md)

!!! question "❓ Misconception: you can just install gVisor or Kata on EKS Auto Mode nodes"
    **Actually:** the EKS documentation states "You can't directly access or install software on instances managed by EKS Auto Mode". You cannot register runsc or kata-deploy on Auto Mode nodes.

    That is why this asset uses managed node groups in the hands-on and Karpenter NodePools in production. Part 1 of the AWS Korea tech blog series also explains that runsc cannot be registered on EKS Auto Mode. Details: [01 Capacity and nodes](../production/01_capacity_and_nodes.md)

!!! question "❓ Misconception: a managed code interpreter or sandbox service can give you a GPU sandbox"
    **Actually:** the AWS managed sandboxes this guide checked are CPU sandbox alternatives.

    The Amazon Bedrock AgentCore Code Interpreter documentation describes its execution environment as a containerized environment and does not mention GPUs. For AWS Nitro Sandboxes and EKS isolated pods (launched 2026-11-09, `runtimeClassName` `isolated-sandbox` or `confidential-sandbox`, Kubernetes 1.36 or later), the documentation says "GPU and other device passthrough are not supported at launch". If the reward must be measured on a GPU, run gVisor or Kata yourself, as this asset does. Details: [05 Decision guide](../concepts/05_decision_guide.md)

## Network and authentication

!!! question "❓ Misconception: a default-deny NetworkPolicy also blocks the node IP"
    **Actually:** the VPC CNI network policy agent allows traffic between a pod and its own node's IP regardless of policies, so that kubelet probes are never blocked (according to the aws-network-policy-agent source).

    That is why this asset puts an iptables node guard (`GPUSANDBOX-GUARD`) on sandbox nodes and lets a pod turn Ready only after it confirms that IMDS, the API server and `$(NODE_IP):10250` are unreachable. The following command checks that these targets are actually blocked in a pool.

    ```bash
    scripts/ops/verify.sh gvisor v1
    ```

    **What to look for:** in the output of step 2, `instance metadata`, `kubernetes api`, `node kubelet` and `internet (S3 endpoint)` are all `blocked (...)`. **If it fails:** see the "Sandbox pools and readiness" table in [Troubleshooting](troubleshooting.md). Details: [02 Security](../production/02_security.md), [04 Deploy and verify sandbox pools](../handson/04_sandbox_pools.md)

!!! question "❓ Misconception: the static policy (AST check) is the sandbox's security boundary"
    **Actually:** the static policy is a reward integrity device; the security boundary that protects the node is gVisor or Kata plus the network controls.

    This asset assumes that candidate code can run arbitrary Python inside the pod. The policy only closes the cheap ways of manipulating the measurement, such as replacing the timer or reaching harness internals. Details: [04 Reward integrity](../production/04_reward_integrity.md), [02 Security](../production/02_security.md)

!!! question "❓ Misconception: a token that passes TokenReview may be allowed to call"
    **Actually:** TokenReview proves only that a token is valid; it does not tell you whether that subject is authorized to call.

    Part 2 of the AWS Korea tech blog series makes this point while analyzing Agent Sandbox's sandbox-router, together with the fact that its default authorization is allow-all. This asset's gateway checks the `GATEWAY_ALLOWED_SUBJECTS` allowlist after TokenReview, and sandbox pods check the audience (`gpu-sandbox`) together with `SANDBOX_ALLOWED_SUBJECTS` and reject any mismatch. Details: [03 Gateway and pools](../production/03_gateway_and_pools.md), [02 Security](../production/02_security.md)

## Training and rewards

!!! question "❓ Misconception: a rolling update of the sandbox Deployment is safe during training"
    **Actually:** during a rolling update, old and new pods answer side by side, so completions of the same GRPO group can be scored by different rules. That corrupts the group-relative advantage.

    This asset starts a separate blue/green pool per (runtime, version). Once isolation checks and golden parity pass, the script updates the routing table, and because the trainer reads the routing table on every sandbox call, the new pool answers from the first request sent after the change is visible. A batch is always scored by one version. If the pool changes while a batch is being scored, results from the other pool are scored again on the new pool, and a batch whose results are all cached from one pool uses that pool's results without calling the sandbox. With TRL defaults a batch boundary is a step boundary. The following command runs that procedure (deploy, verify, parity, switch) in order. In the default scenario A, v1 already uses the GPUs of the two `sandbox-gvisor` nodes, so first scale that node group to 4 and check that the nodes are `Ready`. Otherwise the v2 pods get no GPU and step 1 waits up to 30 minutes and fails (the scaling command is in the preparation section of [06 Updating the sandbox during training](../handson/06_sandbox_update.md)).

    ```bash
    scripts/ops/rollout.sh gvisor v1 v2
    ```

    **What to look for:** a `PASS` line per golden entry and `{"event": "parity", ..., "passed": true}` are printed, and once the routing change reaches the pod (kubelet sync, about a minute) the trainer logs `sandbox_version_switch` when a batch is answered by a different pool than the previous one. If every result of a batch is cached from one pool, the sandbox is not called and that batch logs no such event. **If it fails:** see the "Version switches (routing)" table in [Troubleshooting](troubleshooting.md). Details: [05 Sandbox versioning](../production/05_sandbox_updates.md), [06 Updating the sandbox during training](../handson/06_sandbox_update.md)

!!! question "❓ Misconception: giving reward 0 on infrastructure errors is conservative and therefore safe"
    **Actually:** a 0 is a learning signal that says "this answer is bad", so giving 0 to samples that could not be scored distorts the reward.

    If a sample with a correct answer gets 0 because of a pod failure, that behavior is suppressed. If errors cluster on certain nodes, the noise is systematic as well. On the TRL path, all three reward functions return `None` for `sandbox_error`, which removes the sample from the group baseline. The veRL path has no skip signal and leaves the format score 0.1 with `sandbox_error: 1`, so watch that share. Details: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md), [04 Reward integrity](../production/04_reward_integrity.md)

!!! question "❓ Misconception: if parity passes, rewards stay the same"
    **Actually:** parity checks only the golden submissions. Both versions must return each golden's expected status (and the expected `custom_kernel` where one is set), and when both are `ok` and report a speedup, the new-to-old speedup ratio must also fall within 0.65 to 1.35 by default.

    With changes like v2's (seeds from 3 to 5, a 10x speedup cap), the goldens still pass, while policy samples near a boundary can get a different verdict or speedup. Record an intended reward change as a reward-function change, not as a version swap. Details: [05 Sandbox versioning](../production/05_sandbox_updates.md)

!!! question "❓ Misconception: speedups are about the same on any GPU"
    **Actually:** a speedup means something only on the GPU it was measured on. Treat speedups from the gVisor pool (A10G) and the Kata pool (T4) as different reward functions.

    `scripts/ops/bench.sh` also tells you to read the speedups of pools with different GPU types as per-GPU numbers. If the GPU you will deploy on is fixed, it is better to measure the reward on the same or a similar GPU. Details: [01 When the sandbox needs a GPU](../concepts/01_why_gpu_sandbox.md), [08 Runtime benchmark](../handson/08_benchmark.md)

## Agent Sandbox

!!! question "❓ Misconception: Agent Sandbox only supports gVisor"
    **Actually:** Agent Sandbox leaves isolation to the runtime selected by the RuntimeClass, so Kata works too.

    The upstream README says "Agent Sandbox is a sandbox orchestrator. It delegates low-level container isolation to secure Sandbox Runtimes (like gVisor or Kata Containers) by managing Pods configured to use these runtimes (via RuntimeClass)." The repository has Kata examples (kata-aks, kata-gke) and a GKE gVisor + L4 GPU example. This asset's extension also renders the same SandboxTemplate for each runtime profile, such as gvisor, kata-qemu and kata-clh-cpu. Kata GPU inside a SandboxTemplate (`kata-qemu-nvidia-gpu` with `nvidia.com/pgpu`), however, has not been verified. Details: [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

!!! question "❓ Misconception: Agent Sandbox's default SandboxTemplate policy blocks internet egress"
    **Actually:** according to part 2 of the AWS Korea tech blog series, the default policy leaves internet egress open.

    The default policy accepts ingress only from sandbox-router and allows egress to 0.0.0.0/0 minus RFC1918 and 169.254.0.0/16. The internal network and the IMDS range are excluded, but the internet stays open, so it does not prevent data exfiltration, C2 or mining. The same post also reports that before VPC CNI NetworkPolicy was enabled the sandbox reached IMDS and the Kubernetes API, and that the default DNS injection (`dnsPolicy: None` with 8.8.8.8 and 1.1.1.1) bypasses the Route 53 Resolver. This asset's extension sets `networkPolicy.egress: []` (deny all) and an explicit nameserver 127.0.0.1, so it does not use these defaults. Details: [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

!!! question "❓ Misconception: GPU sandboxes in a warm pool cost nothing while idle"
    **Actually:** a warm sandbox holds its GPU while it waits for a claim, so the cost of that GPU node keeps running.

    Keep the warm pool size (`replicas`) to what you need for the episodes running at the same time. Node costs and cleanup are covered in [08 Cost](../production/08_cost.md) and [99 Cleanup](../handson/99_cleanup.md). Details: [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

## Models, demo and validation status

!!! question "❓ Misconception: every Qwen2.5-Coder model is Apache-2.0"
    **Actually:** `Qwen/Qwen2.5-Coder-1.5B-Instruct` and `Qwen/Qwen2.5-Coder-7B-Instruct` are Apache-2.0 and ungated, but `Qwen2.5-Coder-3B-Instruct` has the qwen-research license (non-commercial).

    This asset does not use the 3B model. When you change models, check the license field of the Hugging Face model card yourself, and check the dataset licenses as well. Details: [Home](../index.md)

!!! question "❓ Misconception: the demo site is connected to a real GPU cluster"
    **Actually:** the demo is a static site (HTML, CSS, JS, no external scripts). It replays the scoring recording (`recording.json`) made by `python -m gpusandbox.tools record`, and when `extras.json` from `demo/build_extras.py` is present it also shows the benchmark and training records. Visitors never reach the cluster or a GPU.

    The site lives in a private S3 bucket with Block Public Access on, and CloudFront reads it only through Origin Access Control. The scoring recording published by default (`demo/site/data/recording.json`) was made on a laptop CPU pool and is meant to be replaced by a recording from a GPU cluster. A recording made on 2026-11-18 on the EKS gVisor A10G pool and Kata QEMU T4 pool is in `demo/recordings/2026-11-18-eks-gpu.json`. Details: [09 Demo site (CloudFront)](../handson/09_demo_site.md)

!!! question "❓ Misconception: the numbers in this guide were measured on AWS by this repository"
    **Actually:** only some of them. Prices and supported versions are cited from official documentation and public material, and the AWS steps have not all been run end to end. In the practice account, scenario A's gVisor path (`03` through `08`) ran on `g5`, and `ops/bench.sh` measured five pools (gVisor A10G, Kata QEMU T4 and the three CPU runtimes) twice, right after deployment and after a pool restart. The result table in [08 Runtime benchmark](../handson/08_benchmark.md) holds the second pass, with the measurement conditions. A recording of golden submissions scored on the A10G and T4 pools is in `demo/recordings/2026-11-18-eks-gpu.json`, and the dated run record is in [Verified facts and sources](sources.md#aws-run-record). Other numbers still come from official documentation and public material.

    What was verified locally are the pytest tests that run on CPU and a TRL GRPO dry run (2 steps). If you need latencies and speedups per runtime, measure them yourself with `scripts/ops/bench.sh`. Sources and evidence levels are collected in [Verified facts and sources](sources.md). Details: [Home](../index.md), [08 Runtime benchmark](../handson/08_benchmark.md)

??? note "References"
    | Topic | Link |
    |---|---|
    | EC2 nested virtualization (User Guide, What's New) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html , https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/ |
    | EC2 accelerated computing instances (`g4dn.metal`, `g5g.metal`) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
    | AWS Nitro Sandboxes, EKS sandboxing limitations | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html , https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
    | gVisor GPU support (nvproxy, security scope) | https://gvisor.dev/docs/user_guide/gpu/ , https://github.com/google/gvisor |
    | Kata 4.3.1 NVIDIA GPU passthrough, hypervisor support table, issue #11687 | https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md , https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md , https://github.com/kata-containers/kata-containers/issues/11687 |

    All sources: [this page in All references](references.md#ref-reference-faq)
