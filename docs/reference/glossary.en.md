# Glossary

!!! info "TL;DR"
    Terms are in alphabetical order. Each entry points to a page that uses the term.

In RL, a rollout generates answers. In Kubernetes, a rollout updates a deployment. See [W](#w) for how warm pools and warm placeholders use GPU capacity.

## A

**Advantage**
:   In GRPO, a value that says how much better one completion is than the other completions of the same group. The policy is updated to produce answers with a positive advantage more often and answers with a negative advantage less often. For how it is computed, see Group-relative advantage below. Used in: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

**Agent Sandbox (kubernetes-sigs/agent-sandbox)**
:   An open source sandbox orchestrator that pre-starts, lends and takes back sandbox pods through Kubernetes CRDs. It leaves the isolation itself to the pod's RuntimeClass (gVisor, Kata and others). The latest release is v1.0.11 with v1beta1 CRDs. Used in: [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

**Audience (`aud`)**
:   The claim that names who a token was issued for. This repository separates `gpu-sandbox` for sandboxes from `gpu-sandbox-gateway` for the gateway, so a token for one does not work at the other. Used in: [02 Security](../production/02_security.md)

**AWS CDK, cdk-nag**
:   AWS CDK is a tool that defines AWS infrastructure in code (Python here) and deploys it as a CloudFormation stack; cdk-nag is an open source tool that checks that code against AWS best-practice rules. This repository creates the VPC, the EKS cluster and the node groups as one CDK stack (`scripts/02_create_cluster.sh` calls `cdk/deploy.sh`), and cdk-nag runs on every synth and stops the deploy on any finding acknowledged without a reason. Used in: [09 Provisioning with CDK](../production/09_cdk.md)

## B

**Bare metal (`.metal`)**
:   An EC2 instance that gives you a whole physical server instead of a virtual machine. The host owns `/dev/kvm`, the IOMMU and the physical GPUs, which Kata GPU passthrough needs. The only EC2 bare metal types with NVIDIA GPUs are `g4dn.metal` and `g5g.metal` (arm64). Used in: [04 Platforms and instances](../concepts/04_platforms_and_instances.md)

**Blue/green**
:   A deployment style that leaves the current version (blue) running, starts the new version (green) next to it, and moves traffic in one step after verification. This repository keeps a separate Deployment per (runtime, version) and switches with the routing ConfigMap. Used in: [05 Sandbox versioning](../production/05_sandbox_updates.md)

## C

**CDI (Container Device Interface)**
:   A standard format that describes which device files and libraries go into a container. This repository installs the NVIDIA device plugin with `deviceListStrategy: cdi-cri`, and gVisor (runsc) uses the GPU devices it receives through CDI as they are. Used in: [02 gVisor GPU sandboxes](../handson/02_gvisor.md)

**Checksum**
:   A short fingerprint computed from the contents of data. On every timed iteration the harness compares the checksum of the candidate's output with the reference, which catches output that is wrong only during measurement ("correct until the benchmark starts"). Used in: [04 Reward integrity](../production/04_reward_integrity.md)

**Cloud Hypervisor (CLH)**
:   A lightweight hypervisor that Kata can use. This repository uses it for the device-free Kata CPU pool. Kata upstream does not support GPU passthrough with CLH.

    - **When you create the CPU pool**: the profile you pass to the deploy script is `kata-clh-cpu`. The v1 Deployment is named `sandbox-kata-clh-cpu-v1`, and the profile selects the RuntimeClass `kata-clh`.
    - **When you pass `kata-clh` to the deploy script**: it selects the experimental GPU profile instead.

    Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

**Completion**
:   In RL, the answer the model generates for one prompt. This repository's GRPO generates 8 completions per prompt (one group) and scores the code block inside a completion in the sandbox. Used in: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

**Consolidation**
:   Karpenter removing empty or underused nodes. The GPU NodePools in this repository use `WhenEmpty`, which removes only empty nodes, so evaluating sandboxes are never moved. Used in: [01 Capacity and nodes](../production/01_capacity_and_nodes.md)

**containerd shim**
:   A small intermediary process that containerd starts per pod (sandbox) to pass commands to a specific runtime. gVisor uses `containerd-shim-runsc-v1`; Kata uses the Go shim or the runtime-rs shim. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

**CSP (Content-Security-Policy)**
:   An HTTP response header that limits where a browser may load scripts and resources from for a page. The demo site adds a strict CSP plus other security headers such as HSTS through a CloudFront response headers policy. Used in: [09 Demo site (CloudFront)](../handson/09_demo_site.md)

## D

**Deep health check**
:   The checks SageMaker HyperPod runs to find faults in GPU instances (InstanceStress, InstanceConnectivity). While a check runs the node carries a taint, and nodes in instance groups with these checks turned on cannot have custom taints. Used in: [07 HyperPod scenario](../handson/07_hyperpod.md)

**Device plugin**
:   A Kubernetes component that advertises a node's devices (such as GPUs) to kubelet under a resource name such as `nvidia.com/gpu`. When a pod requests that resource, the scheduler places it on a node with a free device. GPUs for Kata passthrough are advertised by the GPU Operator as `nvidia.com/pgpu`. Used in: [02 gVisor GPU sandboxes](../handson/02_gvisor.md)

**Draining, recycling**
:   Draining is the state a sandbox enters, leaving Ready, after a set number of evaluations (`SANDBOX_MAX_EVALS`) or a GPU error. Recycling is the gateway deleting that pod so that the Deployment creates a new one; under Kata a new pod is a new VM. Used in: [03 Gateway and pools](../production/03_gateway_and_pools.md)

**Drift**
:   Karpenter finding nodes that no longer match their NodePool or EC2NodeClass settings (for example the AMI) and replacing them. Used in: [01 Capacity and nodes](../production/01_capacity_and_nodes.md)

## E

**EC2NodeClass**
:   See the Karpenter NodePool, EC2NodeClass entry under K.

**Episode**
:   One attempt in agentic RL where the model works on one task over several turns. This repository's Agent Sandbox extension assigns one sandbox to each episode through one SandboxClaim and gives the sandbox back by deleting the claim when the episode ends. Used in: [06 Multi-turn agents and Agent Sandbox](../beginner/06_multi_turn_agent.md), [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

## F

**Fail closed**
:   Rejecting instead of allowing when a setting is missing or cannot be checked. The sandbox server rejects every protected route with 401 when any of the audience, issuer, allowlist or JWKS is missing. Used in: [02 Security](../production/02_security.md)

## G

**Golden submission**
:   Candidate code whose verdict is known in advance. This repository's golden set has six entries (two correct Triton kernels, a correct torch-only answer, a wrong answer, a benchmark cheat, a host file read) and is the reference point for checking that a sandbox works and that a new version matches the old one. Used in: [05 Sandbox versioning](../production/05_sandbox_updates.md)

**GPU passthrough**
:   Handing a whole physical GPU to a VM through VFIO, so that the driver inside the VM drives the GPU directly. The host must own the IOMMU and the physical GPU, so on AWS this repository's x86 setup takes a `g4dn.metal`. In Kata, only QEMU cold-plug is officially supported. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

**Group (GRPO group)**
:   In GRPO, the set of completions generated from one prompt (8 in this repository). Advantages are computed relative to the group, so one group must be scored by one sandbox version. It is not the same as a node group or a HyperPod instance group. Used in: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

**Group pin (`group_key`)**
:   The gateway keeps scoring the samples of one `group_key` (one GRPO group) with the routing snapshot taken for the first sample. The default TTL is 900 seconds, and the pins live only in gateway memory, so they disappear when the gateway restarts. Used in: [03 Gateway and pools](../production/03_gateway_and_pools.md)

**Group-relative advantage**
:   How GRPO computes advantages. The rewards of the completions from the same prompt are normalized by the group mean and standard deviation (TRL default `scale_rewards="group"`), so the ranking inside the group becomes the learning signal. That is why one group must be scored by one sandbox version. Used in: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

**GRPO (Group Relative Policy Optimization)**
:   An RL algorithm that generates several completions per prompt (a group, 8 in this repository), scores them, and reinforces the answers that are better relative to their group. This repository uses the GRPO implementations of TRL (hands-on) and veRL (production). Used in: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

**gVisor**
:   An isolation runtime that reduces how much of the host kernel a container can reach directly. A user-space kernel (the Sentry) receives and handles the system calls instead. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

**gVisor Sentry**
:   gVisor's user-space kernel. It receives the container's system calls in place of the host kernel, and on virtual machines it runs on the systrap platform. This is why `uname -r` inside the sandbox shows a different value from the node. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

## H

**Harness**
:   The evaluation code that runs candidate code, checks correctness and speed, and produces a verdict. This repository's harness is split into a trusted parent process (policy check, reference, timing, verdict) and an untrusted child process (runs the candidate). Used in: [04 Reward integrity](../production/04_reward_integrity.md)

**Headless Service**
:   A Kubernetes Service without a virtual IP (`clusterIP: None`) whose DNS returns the IPs of the Ready pods directly. A client or the gateway can pick a pod itself and send one evaluation per pod. Used in: [04 Deploy and verify sandbox pools](../handson/04_sandbox_pools.md)

**HyperPod instance group**
:   A set of nodes in a SageMaker HyperPod cluster that share one instance type and configuration. Scenario B in this repository puts the trainer on an `ml.g5.2xlarge` instance group and attaches those nodes to the same EKS cluster as the sandboxes. Used in: [07 HyperPod scenario](../handson/07_hyperpod.md)

**HyperPodPyTorchJob**
:   The training job resource provided by the HyperPod training operator add-on. It starts with the `hyperpodrun` launcher and supports restarts per `jobMaxRetryCount` and stall detection from log patterns (`logMonitoringConfiguration`). Used in: [07 HyperPod scenario](../handson/07_hyperpod.md)

## I

**IMDS (Instance Metadata Service)**
:   The metadata service inside an EC2 instance at `169.254.169.254`. It also hands out the temporary credentials of the node IAM role, so this repository keeps sandbox pods away from it with hop limit 1 and blocked egress. Used in: [02 Security](../production/02_security.md)

**ioctl**
:   The system call a program uses to send device-specific commands to a driver. GPU work also reaches the driver as ioctls on the NVIDIA device files, and gVisor nvproxy filters those ioctls through an allowlist. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

**IOMMU**
:   Hardware that limits which memory a device can reach through DMA. In VFIO passthrough it confines the GPU's memory access to the VM. On AL2023 kernels it needs the `intel_iommu=on` kernel argument. Used in: [03 Kata sandboxes (CLH, QEMU)](../handson/03_kata.md)

## J

**JWKS (JSON Web Key Set)**
:   The set of public keys that verifies token signatures. The cluster's ServiceAccount issuer publishes it at `/openid/v1/jwks`, and this repository copies it into the `sandbox-auth-jwks` ConfigMap so that sandboxes can verify tokens without API access. They are public keys, not secrets. Used in: [02 Security](../production/02_security.md)

## K

**Karpenter NodePool, EC2NodeClass**
:   Karpenter is a Kubernetes node autoscaler that starts and returns EC2 nodes to match pod demand. A NodePool states which nodes to start (instance types, taints, labels, caps, disruption policy); an EC2NodeClass holds the AWS launch settings (AMI, subnets, security groups, disks, user data, nested virtualization). Used in: [01 Capacity and nodes](../production/01_capacity_and_nodes.md)

**Kata Containers**
:   A runtime that starts a lightweight VM per pod and runs the containers inside it. It uses QEMU or Cloud Hypervisor as the hypervisor, and every pod has its own guest kernel. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

**KernelBench**
:   A public benchmark (MIT license) that measures the ability to write GPU kernels. This repository follows its task format (`Model`, `ModelNew`), correctness tolerances, timing approach and `excessive_speedup_threshold` of 10. Used in: [01 When the sandbox needs a GPU](../concepts/01_why_gpu_sandbox.md)

**KL penalty (`beta`)**
:   A KL divergence term added to the loss, with its coefficient, that keeps the policy under training from drifting too far from a reference model. The TRL 1.18.0 GRPO default is `beta` 0.0, so there is no KL term and no reference model is loaded. This repository keeps that default. Used in: [05 On-policy GRPO training](../handson/05_grpo_training.md)

**KVM**
:   The hardware virtualization feature built into the Linux kernel, used through the `/dev/kvm` device. Kata's QEMU and Cloud Hypervisor start VMs on KVM, so Kata nodes need `/dev/kvm`. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

## L

**Lifecycle script**
:   A setup script that HyperPod downloads from S3 and runs when it creates a node. This repository's `infra/hyperpod/lifecycle/on_create.sh` for the trainer group installs nothing, and `on_create_sandbox.sh` for the B2 sandbox group checks the driver, then registers `runsc` and installs the node guard. Keep the `sagemaker-` prefix in the bucket name. Used in: [07 HyperPod scenario](../handson/07_hyperpod.md)

**LoRA**
:   A fine-tuning method that trains small low-rank matrices instead of all model weights. It reduces the trainable parameters and optimizer state, and the hands-on is configured to train a 1.5B model on one A10G this way. The defaults are `r` 32, `lora_alpha` 64, all linear layers. Used in: [05 On-policy GRPO training](../handson/05_grpo_training.md)

## M

**Multi-turn**
:   A way of working where the model calls a tool or submits code, reads the result and responds again, several times over. It is distinct from single-turn grading, which grades each completion on its own with no second response to the result. GRPO training in this repository uses single-turn grading, and multi-turn agents use the per-episode sandboxes of the Agent Sandbox extension. Used in: [06 Multi-turn agents and Agent Sandbox](../beginner/06_multi_turn_agent.md), [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

## N

**Nested virtualization**
:   Running a hypervisor (KVM) again inside a virtual EC2 instance. It launched in 2026-02 starting with C8i, M8i and R8i, and the G and P families with GPUs do not support it. This repository uses it for the GPU-free Kata CPU tier. Used in: [04 Platforms and instances](../concepts/04_platforms_and_instances.md)

**NetworkPolicy**
:   A Kubernetes rule that defines, by namespace and label, which traffic a pod may send and receive. On EKS the VPC CNI enforces it (`enableNetworkPolicy`), and in standard mode a new pod starts default-allow until its policies apply. Used in: [02 Security](../production/02_security.md)

**NodeConfig, nodeadm**
:   nodeadm is the bootstrap tool that joins EKS AL2023 nodes to the cluster, and NodeConfig is its configuration passed in user data. This repository uses NodeConfig to add the `runsc` runtime to containerd. nodeadm rewrites `/etc/containerd/config.toml` on every boot. Used in: [02 gVisor GPU sandboxes](../handson/02_gvisor.md)

**nvproxy**
:   The gVisor component that lets containers use NVIDIA GPUs. It filters the ioctls to the GPU driver through an allowlist per driver version and forwards them to the host driver; it works only when the driver version is exactly on the support list. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

## O

**OAC (Origin Access Control)**
:   A CloudFront feature that makes CloudFront send signed requests to an S3 origin. The bucket policy allows only the CloudFront service principal for one distribution (an `AWS:SourceArn` condition), so the bucket stays private and its content is served only through CloudFront. The CloudFront documentation recommends OAC instead of the older origin access identity (OAI). Used in: [09 Demo site (CloudFront)](../handson/09_demo_site.md)

**On-policy**
:   Training on data (completions) generated by the very policy being updated. The TRL hands-on trains strictly on-policy: each generated batch is used for exactly one optimizer step (the TRL `steps_per_generation` default). The veRL setup splits a training batch (64 prompts) into PPO mini-batches (32 prompts) and updates several times. Used in: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

## P

**Parity check**
:   A check that a new sandbox version gives the same verdicts as the old one on the golden submissions. Both versions must meet each golden's expected status (and the expected `custom_kernel` where one is set), and the two statuses must match. When both are `ok` and report a speedup, the new speedup divided by the old one must also be within the tolerance (default 0.35) of 1. Only then does traffic move. Used in: [05 Sandbox versioning](../production/05_sandbox_updates.md)

**PDB (PodDisruptionBudget)**
:   A cap on how many pods may go down at once during voluntary disruptions such as drains. It applies to the eviction API only, so it does not stop the gateway's recycling, which deletes pods directly. Used in: [01 Capacity and nodes](../production/01_capacity_and_nodes.md)

**Plausibility cap**
:   An upper bound on implausibly large speedups (`HARNESS_MAX_SPEEDUP`). The v2 version file uses 10, the same value as KernelBench's `excessive_speedup_threshold`; above the cap the verdict gets the `implausible_speedup` flag and the speedup is recorded as 1.0. Used in: [04 Reward integrity](../production/04_reward_integrity.md)

**Policy**
:   In RL, the model being trained. It generates completions for prompts and is updated with the rewards those completions receive. It is not the same as the harness's static policy (`harness/policy.py`), IAM policies or NetworkPolicies. Used in: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

**PriorityClass, preemption**
:   A PriorityClass is a pod's priority value, and preemption is the scheduler evicting a lower-priority pod to make room for a higher-priority one. This repository's warm placeholder (-10) is the first to be evicted when a sandbox pod needs room. Used in: [01 Capacity and nodes](../production/01_capacity_and_nodes.md)

**Private endpoint (EKS API)**
:   An EKS API server address reachable only from inside the VPC. This repository's cluster turns the public endpoint off and only the private endpoint on, so kubectl and helm on your workstation reach the API through the SSM port forwarding of `cdk/tunnel.sh`. Used in: [09 Provisioning with CDK](../production/09_cdk.md)

**Projected ServiceAccount token**
:   A ServiceAccount token that kubelet writes as a file into a pod volume. It has a chosen audience and lifetime (`expirationSeconds`), and kubelet replaces it periodically at the same path. This repository uses 3600-second tokens and re-reads the file on every request. Used in: [02 Security](../production/02_security.md)

## Q

**QEMU**
:   One of the hypervisors Kata uses. QEMU is the only hypervisor with which Kata officially supports NVIDIA GPU passthrough, so this repository's Kata GPU pool uses the `kata-qemu-nvidia-gpu` RuntimeClass. Used in: [03 Kata sandboxes (CLH, QEMU)](../handson/03_kata.md)

## R

**ResourceQuota**
:   A cap on the total resources one namespace may request. With the production `k8s/production/pool-hardening.yaml` applied, requests in the `sandbox` namespace are capped at 16 `nvidia.com/gpu`, 8 `nvidia.com/pgpu` and 64 pods. The default hands-on install creates no quota. Used in: [01 Capacity and nodes](../production/01_capacity_and_nodes.md)

**Reward hacking**
:   A policy raising its score by exploiting gaps in the reward measurement instead of solving the task. Reported cases in the KernelBench line of work include fooling the timing with extra CUDA streams, caching results, being wrong only during the benchmark, and lazy tensors. Used in: [04 Reward integrity](../production/04_reward_integrity.md)

**Rollout**
:   In RL, the step where the current policy generates completions for the prompts. In GRPO it generates one group per prompt. This is a different meaning from a Kubernetes Deployment rollout (`kubectl rollout`). Used in: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

**Routing table (`sandbox-routing`)**
:   `routing.json`, which names the active (runtime, version) pool and lists the address of each pool. It is deployed as the `sandbox-routing` ConfigMap and read by the trainer and the gateway. Used in: [05 Sandbox versioning](../production/05_sandbox_updates.md)

**runc**
:   Kubernetes' default container runtime. Containers share the host kernel and drivers directly. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

**RuntimeClass**
:   A Kubernetes object that selects the container runtime for a pod. The pod's `runtimeClassName` points to a RuntimeClass, and the RuntimeClass `handler` must equal the `runtimes.<name>` key in the containerd configuration. It can also carry scheduling rules and pod overhead. Used in: [02 Isolation runtimes](../concepts/02_isolation_runtimes.md)

## S

**SandboxClaim**
:   The Agent Sandbox request resource that borrows one sandbox from a warm pool. `spec.warmPoolRef` points to the pool, and once the claim is Ready its address appears in `status.sandbox.serviceFQDN`. Deleting the claim returns the sandbox. Used in: [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

**sandbox_error**
:   The verdict for an infrastructure failure that is not the candidate's fault (authentication failure, transport failure, reference failure and so on). On the TRL path the reward is `None` and the sample is left out of training; on the veRL path the sample gets the format score only and a flag. Used in: [03 On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md)

**sandbox-router**
:   An optional Agent Sandbox component: an HTTP reverse proxy that forwards client requests to a claimed sandbox. The AWS Korea blog pointed out that its default authorization setting allows every request. This repository's extension does not use the router and sends requests directly to the claim's `serviceFQDN`. Used in: [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

**SandboxTemplate**
:   The Agent Sandbox resource that defines what a sandbox pod looks like (pod template, NetworkPolicy, Service, environment variable injection policy). This repository creates one `kernel-eval-<runtime>` template per runtime profile. Used in: [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

**SandboxWarmPool**
:   The Agent Sandbox resource that keeps a set number of sandboxes from a SandboxTemplate started ahead of time. A claim gets a sandbox that is already prepared, which shortens the wait. Warm GPU sandboxes hold their GPU even while idle. Used in: [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md)

**Speedup**
:   The reference implementation's run time divided by the candidate kernel's run time. By default only correct custom kernels get a speedup score; with `--allow-torch-only`, correct PyTorch-only answers are scored on the same scale. The score is log2-scaled: 0 at 0.5x, 0.5 at 1x, 1.0 at 2x, capped at 1.5 (4x). Used in: [05 On-policy GRPO training](../handson/05_grpo_training.md)

**SSM Session Manager port forwarding**
:   An AWS Systems Manager feature that connects a local port on your machine to an address inside the VPC through an instance with the SSM agent. The instance needs no inbound port and no public IP, and your machine needs the Session Manager plugin for the AWS CLI. This repository's `cdk/tunnel.sh` connects `127.0.0.1:8443` to the private API endpoint. Used in: [09 Provisioning with CDK](../production/09_cdk.md)

## T

**T4**
:   An NVIDIA GPU model. On EC2 it comes in `g4dn` instances, and `g4dn.metal` has eight of them. It is the only x86 NVIDIA GPU on EC2 that can be assigned directly to a VM, so the Kata GPU sandboxes of this asset measure the reward on a T4. Used in: [Decision guide](../concepts/05_decision_guide.md), [03 Kata sandboxes (CLH, QEMU)](../handson/03_kata.md)

**Taint, toleration**
:   A taint is a mark on a node that keeps pods without a matching toleration from being scheduled there, and a toleration is a pod setting that lets the pod be scheduled on a node with that taint. This repository makes sandbox nodes dedicated with `gpusandbox/role=<role>:NoSchedule` taints. Used in: [01 Capacity and nodes](../production/01_capacity_and_nodes.md)

**TokenReview**
:   A Kubernetes API that asks the API server whether a token is valid and whose it is. The gateway uses it to authenticate callers and caches successful results for 60 seconds. It reports validity only, not permission, so the gateway also checks an allowlist. Used in: [02 Security](../production/02_security.md)

**Triton**
:   A language and compiler for writing GPU kernels in Python. The tasks in this repository ask the policy to write Triton kernels, and the harness records how many times the Triton launch function was called up to the end of the correctness check. That is a call count, not a count of successful kernel runs. Used in: [01 When the sandbox needs a GPU](../concepts/01_why_gpu_sandbox.md)

**Turn**
:   One step of a multi-turn episode in which the model responds once. In this repository's kernel task it is one submission of code and the verdict that comes back, and every turn of one episode is graded in the same sandbox. Used in: [06 Multi-turn agents and Agent Sandbox](../beginner/06_multi_turn_agent.md)

## V

**Verdict**
:   The JSON result the harness returns after scoring one candidate. It contains `status` (`ok`, `wrong_answer`, `policy_violation` and so on), `speedup` and `flags`, and the trainer turns it into a reward. Used in: [04 Reward integrity](../production/04_reward_integrity.md)

**VFIO**
:   The Linux kernel feature that hands a whole PCI device such as a GPU to user space or a VM (the `vfio-pci` driver). Kata GPU passthrough uses this path. VFIO pins all VM memory, so memory cannot be overcommitted. Used in: [03 Kata sandboxes (CLH, QEMU)](../handson/03_kata.md)

**vLLM colocate mode**
:   In TRL GRPO, running the vLLM generation engine inside the training process so that both share one GPU (`vllm_mode="colocate"`). This repository gives vLLM 35% of the GPU memory (`--vllm-gpu-memory-utilization 0.35`) and uses sleep mode to free that memory during the optimizer step. Used in: [05 On-policy GRPO training](../handson/05_grpo_training.md)

## W

**Warm pool, warm placeholder**
:   Starting resources ahead of time to hide slow startup. The production warm placeholder is an empty pod that holds one metal node; the Agent Sandbox SandboxWarmPool pre-starts the sandbox pods themselves. Used in: [01 Capacity and nodes](../production/01_capacity_and_nodes.md)

## ❓ Misconceptions

!!! question "❓ Misconception: rollout is a Kubernetes deployment term"
    This guidebook uses it in two senses. Tell them apart by whether the surrounding text is about training or about deployment.

    - **RL context (GRPO, veRL)**: a rollout is the step where the policy generates completions.
    - **Deployment context**: each command does something different.
        - `kubectl rollout status` waits until the given Deployment has finished rolling out.
        - `scripts/ops/rollout.sh` deploys the new version as a separate Deployment, verifies it, and then moves traffic by changing the routing table.

!!! question "❓ Misconception: the warm placeholder also reserves a GPU"
    - **Production warm placeholder**: it requests CPU and memory only, never a GPU. It just holds the node and steps aside when a sandbox pod arrives.
    - **Agent Sandbox SandboxWarmPool**: it pre-starts sandbox pods with the resources set in the profile. With a GPU profile it holds GPUs even while idle; with a CPU profile (for example `kata-clh-cpu`) it requests no GPU.

!!! question "❓ Misconception: Kata only runs on `.metal` instances"
    That is true only for GPU passthrough. Kata without devices runs without `.metal` on the `/dev/kvm` that EC2 nested virtualization provides. Handing a GPU to a VM requires the host to own the physical GPU and the IOMMU, which is why this repository's x86 setup takes a `g4dn.metal`.

??? note "References"
    | Topic | Link |
    |---|---|
    | Amazon EC2 nested virtualization | [Amazon EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) |
    | Configure network policy (Amazon EKS) | [Configure network policy (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) |
    | gVisor GPU support | [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/), [google/gvisor](https://github.com/google/gvisor) |
    | Kata Containers 4.3.1 NVIDIA GPU passthrough | [Kata Containers 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md), [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers) |
    | Karpenter documentation | [Karpenter documentation](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws) |

    [Selected references on this topic](references.md#ref-reference-glossary)

The full list of sources is in [Verified facts and sources](sources.md).
