# Verified facts and sources

!!! info "TL;DR"
    Find which AWS runs were performed and which figures come from official documents or third-party reports.

- [AWS run record](#aws-run-record) lists the runs performed for this repository.
- [Predeployment checks](#re-verify-checklist-before-deploying) cover prices, quotas, and driver compatibility.
- [Selected references](references.md) lists the original sources.

## Reading the evidence levels

| Label | Meaning | Examples in this guide |
|---|---|---|
| Locally verified by tests | This repository's pytest passes on CPU | Two-process harness, AST policy, audience-bound authentication, readiness tied to the egress check |
| Per official documentation | docs.aws.amazon.com, upstream docs and code | Families that support nested virtualization, the nvproxy driver policy, the VPC CNI allowing the node IP |
| Third-party report | Blogs, issues, public case studies | The `g4dn.metal` warm reboot problem, `reset_method=bus` on T4 |
| Blog measurement | A value someone else measured in a different environment | About 55 ms for a warm pool claim in part 2 of the AWS Korea tech blog series, about 3 s cold start in the AWS China blog |
| Inference | A judgment derived from the evidence, unverified | The effect of NodeConfig `imports` on keeping kata-deploy drop-ins |
| Executed on AWS by the author | Actually run in a practice account, with the output checked | The gVisor path of scenario A, Kata GPU (`g4dn.metal`), the three CPU runtimes of scenario C, the runtime benchmark, the demo site. The dated record is in [AWS run record](#aws-run-record) |
| Not executed on AWS by the author | Designed, with templates written, but not run | `ops/rollout.sh` in scenario A during training, HyperPod B2 on `ml.g5`. The full list is in [AWS run record](#aws-run-record) |

## What this repository verified

The first command below runs the whole local test suite without AWS or a GPU, and the second runs the CDK stack tests separately in a virtual environment with the CDK libraries. Set up the environment as described in [Getting started](../getting_started.md).

- **When you run the tests**: the tests run with the server's process reaper turned off, so they are safe on a Linux host.
- **When you start a server directly on a Linux host**: it can still terminate other processes of the same user, so read the warning on that page before you do.

```bash
# Full local test suite on CPU (no AWS, no GPU)
python -m pytest -q
# CDK stack tests: offline synth with cdk-nag (after uv pip install -r cdk/requirements.txt)
(cd cdk && python -m pytest -q tests)
```

**What to look for:**

- It ends with `passed` and no failures.
- While this page was written (2026-11-13), the whole suite passed on macOS (CPU only).
- The number of tests changes as the repository changes, so it is not fixed here. To count the tests in your checkout, run `python -m pytest --collect-only -q` from the repository root (the CDK stack tests are separate).

**If it fails:** [Troubleshooting](troubleshooting.md)

| Test file | Locally verified by these tests |
|---|---|
| `tests/test_policy.py` | What the AST policy allows (the Triton example, an autotuned kernel, an `input` parameter, type hints) and rejects (denied imports and builtins, a monkeypatch through an alias, dunder and private access, streams and graphs, Tensor subclasses) |
| `tests/test_harness_cpu.py` | The real two-process harness on CPU: correct, wrong, crash, syntax error, timeout, benchmark cheat, monkeypatch, consistency of the task references |
| `tests/test_routing_and_rewards.py` | Routing table reload and revision, `RoutingError` for a missing pool, code extraction, the speedup score, rewards per verdict with infrastructure errors excluded, results cached from another pool scored again on this batch's pool after a version switch, policy violations skipping the sandbox round trip |
| `tests/test_server_and_client.py` | Fail-closed authentication that checks audience and subject, the client across two loopback servers, 503 from a busy pod, Ready only after egress denial is verified, probe and parity on CPU pools, gateway group pins across a routing switch |
| `tests/test_manifests.py` | Sandbox manifests for each profile and version, static manifests, node user data (`infra/eks/userdata.py`), Karpenter templates, Agent Sandbox template rendering |
| `tests/test_agent_sandbox.py` | With a fake API: the SandboxClaim body, waiting for Ready and preferring `serviceFQDN`, claiming and releasing, releasing when the claim never becomes Ready |
| `tests/test_multiturn.py` | With a fake API and loopback CPU sandbox servers: one claim per episode, stopping when solved, deleting the claim on errors, the events and the episode reward, and the veRL tool logic without veRL installed |
| `tests/test_demo.py` | The demo CloudFormation template (private bucket, CloudFront access with an `AWS:SourceArn` condition, non-TLS requests denied, HTTPS redirect and security headers), a static site with no external resources or HTML injection, the recording schema and reward consistency |
| `cdk/tests/test_stack.py` | The synthesized CDK template: private endpoint (public only as a /32 opt-in), no `0.0.0.0/0` inbound rule, the node groups per scenario, cdk-nag passing for each scenario. The rest is in the list below the table |

`cdk/tests/test_stack.py` also checks the following.

- **IMDSv2**: IMDSv2 required in every launch template of scenario A synthesized with Kata CPU added (hop limit 1 and EBS encryption are checked only where the template sets them)
- **Node group settings**: nested virtualization on c8i, the IOMMU AMI and user data on the Kata GPU node group (IMDSv2 is not checked for that configuration)

A TRL 1.18.0 GRPO dry run (SmolLM2-135M, CPU, no vLLM) completed 2 steps, and the shell scripts pass shellcheck (author's record, 2026-11).

### AWS run record

All of these ran in the author's practice account.

| Date | Region | Target | What ran | Result |
|---|---|---|---|---|
| 2026-11-14 | us-west-2 | Scenario C (EKS 1.36) | `02_create_cluster.sh --cpu-only` (CDK deploy, about 20 minutes), `cdk/tunnel.sh`, `kata/cpu_nodes.sh` (about 14 minutes, mostly the kata-deploy install), stack deletion. Deployed and deleted twice. Part 2 of [05 Try it yourself](../beginner/05_hands_on.md) ran in this order too (including the runc comparison container on the same node) | Succeeded. Checked the cluster and node status, the private endpoint, nested virtualization and `/dev/kvm` on the c8i node, gVisor and the node guard, the tunnel listening only on `127.0.0.1`, the `gvisor-cpu` RuntimeClass, the smoke pods of the three runtimes, and the resources left after deletion |
| 2026-11-17 | us-west-2 | Scenario C (c8i) | `ops/rollout.sh kata-clh-cpu v1 v2`, with the model-free reward loop `ops/simulate.sh` running alongside (30 batches, about 16 minutes) | Succeeded. All four stages (deploy, verify, parity, switch) passed, and `sandbox_version_switch` was recorded at batch 8. `rollout.sh --finish` was not run. The output is in `demo/site/data/extras.json` |
| 2026-11-18 | us-west-2 | Scenario A (gVisor) | `02_create_cluster.sh`: the first creation with the GPU node groups rolled back on `InsufficientInstanceCapacity`, so the cluster was created system-only with `--hyperpod-b2`, then updated with `CHANGE_SCENARIO=1` to B1 (gVisor node group added) and then to A (trainer added). Then `03_build_push_images.sh` (all three images), `04_install_gpu_stack.sh` (`g5.xlarge`), `05_setup_namespaces_auth.sh`, `06_deploy_sandboxes.sh gvisor v1` (1 replica), `ops/verify.sh gvisor v1`, `07_run_grpo.sh 5` on `g5.2xlarge`, `08_cleanup.sh --images` | Succeeded. Smoke pod `cuda ok: NVIDIA A10G 2048.0`, driver 580.178.04 (proprietary, GSP off). The pool check passed with 6 golden verdicts PASS, 4 egress targets blocked and the `default` namespace blocked. The GRPO Job reached Complete (about 12 minutes, `train_runtime` about 401 s). The record does not show whether the AMI deletion step of `08_cleanup.sh` ran |
| 2026-11-18 | us-west-2 | Kata GPU and Kata CPU (another cluster, EKS 1.36) | Created system-only, then Kata CPU, Kata GPU and gVisor node groups added with `CHANGE_SCENARIO=1`. `kata/gpu_nodes.sh` (IOMMU AMI build, GPU Operator), `kata/cpu_nodes.sh`, `06_deploy_sandboxes.sh kata-qemu` (4 replicas), `ops/verify.sh` on `kata-qemu` and the three CPU pools | Succeeded. `pgpu=8`, 4 `kata-qemu` pods Ready (T4), pool checks passed. The run exposed the `vfio_iommu_type1` module problem and an AMI builder problem, and the scripts were fixed ([03 Kata sandboxes](../handson/03_kata.md)) |
| 2026-11-18 | us-west-2 | Experimental Kata CLH GPU (`kata-clh`) | Deployed the experimental pool with `ENABLE_EXPERIMENTAL_CLH_GPU=1` | Failed. The VM did not start even after the artifact paths were filled in (`create container timeout`). Left out of the benchmark |
| 2026-11-18 | us-west-2 | Runtime benchmark | `ops/bench.sh 32` on five pools (`gvisor`, `kata-qemu` and the three CPU pools) in the Kata cluster above, once right after deployment and once after a pool restart. The gVisor node in this cluster was one `g5.2xlarge` | Succeeded. All five pools returned 32 of 32 as `ok`. The result table is in [08 Runtime benchmark](../handson/08_benchmark.md) |
| 2026-11-18 | us-east-1 (cluster in us-west-2) | Demo site | `record` in the recorder pod (gVisor A10G pool, Kata QEMU T4 pool), `extras.json` built from the cluster logs, `demo/deploy.sh`, an external check after deployment | Succeeded. Checked the security headers, allowed methods, bucket settings and log delivery. With the default certificate the endpoint accepted TLS 1.0 and 1.1 handshakes (security design in [09 Demo site](../handson/09_demo_site.md)) |
| 2026-11-20 | us-west-2 | Scenario C (c8i) | `ops/rollout.sh kata-clh-cpu` (v1 to v2, v2 to v1) with `ops/simulate.sh` running, `extensions/agent_sandbox.sh install`, `pool kata-clh-cpu 1`, `claim kata-clh-cpu`, `episodes kata-clh-cpu 2 3` | Success. The switch happened once at a batch boundary and every batch had one version. One v2-to-v1 run failed parity on the speedup check from CPU timing noise (0.8979 to 0.5365, same verdicts). For Agent Sandbox, the claim got a sandbox address and released it, and the warm pool refilled with a new sandbox. `episodes` solved both episodes in 3 turns, with one claim and one sandbox per episode and no claims left afterwards |
| 2026-11-20 | us-west-2 | Scenario A (gVisor) | `01_check_prereqs.sh`, `02_create_cluster.sh` (first creation with the GPU node groups, CDK deploy about 15 min), `03_build_push_images.sh`, `04_install_gpu_stack.sh`, `05_setup_namespaces_auth.sh`, `06_deploy_sandboxes.sh gvisor v1`, `ops/verify.sh gvisor v1`, `07_run_grpo.sh` (default 60 steps) | Success. This time the first creation finished without a capacity error. The access instance lost its SSM connection right after registering (`ConnectionLost`), and the tunnel connected after a reboot. All six verification submissions passed. Training printed 60 `reward_batch` lines with no `sandbox_error` and no batch mixing versions, `train_runtime` 2697 s, and the Job was Complete in about 50 min. The `ok` share was 5.3% over the first 20 steps and 6.0% over the last 20 |
| 2026-11-22 | us-west-2 | HyperPod B1 on EKS 1.36 | `ml.g5.2xlarge` trainer, two EC2 `g5.xlarge` sandboxes, training operator `v1.3.0-eksbuild.1`, `hyperpod/run_grpo.sh 1` | `Completed=True`, 6/6 probe checks passed, 12 submissions evaluated, 1 correct. The HyperPod and EKS clusters, test GPU nodes, lifecycle bucket and test trainer repository were deleted. The EKS KMS key entered its seven-day deletion window. [Console and trainer screenshots](../handson/07_hyperpod.md#how-to-verify) |
| 2026-11-22 | us-west-2 | HyperPod B1 benchmark | `relu_bias_triton`, gVisor v1, two EC2 `g5.xlarge` sandbox nodes | EKS system and HyperPod trainer clients each passed 32/32. The HyperPod run reached 0.199 eval/s. [Measurements and screenshot](../handson/08_benchmark.md#hyperpod-b1) |

On 2026-11-14 the author also captured the Service Quotas screens and the HyperPod AMI search in the EC2 AMI Catalog from the ap-south-1 console. These were read-only views, and no script ran there.

**Not executed on AWS:**

- `ops/rollout.sh` in scenario A during training, and `ops/rollout.sh --finish` (not run in any scenario)
- HyperPod B2 with its custom sandbox AMI, automatic node replacement and checkpoint recovery.
- `demo/teardown.sh` (shellcheck only)
- The `gvisor-cpu` warm pool and the GPU section of [11 Multi-turn episodes](../handson/11_multi_turn.md) (it ran with the `kata-clh-cpu` warm pool)
- What the production guide adds to the hands-on: Karpenter NodePool, gateway, jwks-sync CronJob, pool hardening, warm capacity

Verify the rest yourself with the checks on each hands-on page.

## Re-verify checklist before deploying

The values below are as of 2026-11. Check them one by one before deploying or sharing.

- [ ] **Pinned versions:** check each project's release page for new versions and changes.
    - gVisor `GVISOR_RELEASE=20261109.0`, Kata `KATA_VERSION=4.3.1`
    - GPU Operator `v26.7.2`, NVIDIA device plugin `0.20.1`
    - Karpenter v1.15.2 (LTS v1.14.3)
    - AWS CDK CLI 2.1148.1 or later with `aws-cdk-lib` 2.276.0, cdk-nag 3.0.2
    - Agent Sandbox v1.0.11
    - TRL 1.18.0 (vLLM 0.33.0 in the trainer image), veRL 0.9.1 (vLLM 0.24.0 in the veRL image), KubeRay v1.7.2
- [ ] **Node drivers and the nvproxy list:** check that `B2_NVIDIA_DRIVER_VERSION` of the B2 custom AMI and the node drivers are on the supported list of the pinned gVisor release.
    - **EKS AL2023 NVIDIA AMI v20261107**: the default driver is 580.178.04 (the proprietary module with GSP off on g5, the open module on g6).
    - **HyperPod EKS AMIs**: 1.34 to 1.36 (2026-10-16) ship 595.91.07 and 1.33 ships 580.178.04.
- [ ] **Prices:** EC2 On-Demand and SageMaker AI (HyperPod `ml.*`) pricing. The values in this guide (such as 0.37484 USD/hour for `c8i.2xlarge`) are as of 2026-11.
- [ ] **Quotas:** Running On-Demand G and VT instances (vCPU based, can be 0 for new accounts), Running On-Demand Standard instances, and HyperPod's `ml.<type> for cluster usage`.
- [ ] **Kubernetes versions supported by HyperPod:** the prerequisites list 1.31 through 1.37 as of 2026-11-22. The lab uses 1.36.
- [ ] **EKS versions:** standard support 1.37, 1.36, 1.35, 1.34.
- [ ] **Nested virtualization families and Regions:** the family list in the User Guide and the support per Region.
- [ ] **GPU support in managed sandboxes:** "GPU and other device passthrough are not supported at launch" for Nitro Sandboxes and EKS isolated pods, and the execution environment described in the AgentCore Code Interpreter documentation.
- [ ] **Agent Sandbox CRD fields:** after upgrading the controller, re-check the field names of `SandboxClaim`, `SandboxTemplate` and `SandboxWarmPool`.
- [ ] **Model licenses:** the license field of each model card you use.
- [ ] **Demo site TLS:** with the default `*.cloudfront.net` certificate you cannot raise the viewer TLS policy, so if you need TLSv1.2_2021, use a custom domain and an ACM certificate in us-east-1.

The following commands check whether the node driver is on the supported list of the pinned gVisor release. Run them after `chroot /host` in a debug shell on the node (`kubectl debug node`, see "Checking on the node" in [Troubleshooting](troubleshooting.md)).

```bash
driver="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"; echo "$driver"   # loaded driver version
/usr/local/bin/runsc nvproxy list-supported-drivers | grep -wF "$driver"
```

**What to look for:**

- **If the second command prints one line with that driver version**: it is on the supported list.
- **If it prints nothing**: gVisor GPU sandboxes on that node will not become Ready.
- **HyperPod nodes**: `scripts/hyperpod/check_gvisor.sh` runs the same check.

The following command prints the quotas and nested virtualization support at once (read-only).

```bash
scripts/01_check_prereqs.sh
```

**What to look for:** the G and VT vCPU quota value, `nested-virtualization` support for `c8i.2xlarge` and the AZ list for the GPU instance types are printed, ending with `Done.`. **If it fails:** see the "Configuration and scripts" and "Cluster and nodes" tables in [Troubleshooting](troubleshooting.md).

## References

### AWS documentation and What's New

| Source | Facts it supports |
|---|---|
| [What's New: EC2 nested virtualization (2026-02)](https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual/) | Nested virtualization launched on 2026-02-16 on C8i, M8i and R8i virtual instances |
| [EC2 User Guide: nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html) | Supported families (M7i, M7i-flex, M8i, M8id, M8i-flex, C7i, C7i-flex, C8i, C8id, C8i-flex, R7i, R7iz, R8i, R8id, R8i-flex, X8i, I7i, I7ie), L1 hypervisors KVM and Hyper-V, no G or P families, `--cpu-options "NestedVirtualization=enabled"`, bare metal recommended for performance-sensitive virtualization |
| [EC2 accelerated computing instances](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html) | NVIDIA GPU bare metal: `g4dn.metal` (8 T4, 96 vCPU, 384 GiB) and `g5g.metal` (arm64, 2 T4G) |
| [EC2 instance type quotas](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html) | vCPU-based On-Demand quotas such as "Running On-Demand G and VT instances" |
| [EC2 On-Demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/) | USD per hour in us-east-1 and us-west-2: `g4dn.xlarge` 0.526, `g4dn.2xlarge` 0.752, `g6.xlarge` 0.8048, `g6.2xlarge` 0.9776, `g5.xlarge` 1.006, `g5.2xlarge` 1.212, `g6e.xlarge` 1.861, `g6e.12xlarge` 10.49264, `g6e.48xlarge` 30.13118, `p4d.24xlarge` 21.95764, `p5.48xlarge` 55.04, `g4dn.metal` 7.824 (Seoul 9.624), `g5g.metal` 2.744, `c5.metal` 4.08, `m6i.large` 0.096, `t3.large` 0.0832 |
| [AWS Nitro Sandboxes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html) | Launched 2026-11-09, `runtimeClassName` `isolated-sandbox`, `confidential-sandbox` |
| [EKS sandboxing limitations](https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html) | Kubernetes 1.36 or later, "GPU and other device passthrough are not supported at launch" |
| [EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) | Standard support 1.37, 1.36, 1.35, 1.34 (latest 1.37) |
| [Configure VPC CNI network policy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html) | `{"enableNetworkPolicy": "true"}`, VPC CNI 1.21 or later, standard mode allows new pods until policies apply, strict mode (`NETWORK_POLICY_ENFORCING_MODE`) default-denies everything including CoreDNS |
| [EKS Auto Mode managed instances](https://docs.aws.amazon.com/eks/latest/userguide/automode-learn-instances.html) | "You can't directly access or install software on instances managed by EKS Auto Mode" |
| [HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html) | Authentication mode API or API_AND_CONFIG_MAP, VPC CNI 1.18.3 or later, private subnets, Kubernetes 1.31 through 1.37, the dependency Helm chart when creating through the API, separate IAM roles for HyperPod nodes and EKS nodes |
| [HyperPod IAM prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html) | Execution role: `AmazonSageMakerClusterInstanceRolePolicy` plus an EC2 ENI and ECR inline policy |
| [HyperPod EKS AMI release notes](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-release-ami-eks.html) | Release of 2026-10-16: the AMIs for Kubernetes 1.34 to 1.36 ship NVIDIA 595.91.07, 1.33 (x86_64) ships 580.178.04. The 1.36 AMI has kernel 6.12.111, containerd 2.3.5, CUDA 13.2 |
| [HyperPod custom AMIs](https://docs.aws.amazon.com/sagemaker/latest/dg/hyperpod-custom-ami-support.html), [Build a custom AMI](https://docs.aws.amazon.com/sagemaker/latest/dg/hyperpod-custom-ami-how-to.html), [Cluster management with custom AMIs](https://docs.aws.amazon.com/sagemaker/latest/dg/hyperpod-custom-ami-cluster-management.html) | Only images built from a HyperPod public base AMI; "driver customizations" as a use case; the instance group's `ImageId` (EKS and Slurm); replace with `UpdateClusterSoftware` |
| [HyperPod automatic node recovery](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-node-recovery.html), [deep health checks](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html) | NodeRecovery Automatic, deep health checks (InstanceStress, InstanceConnectivity), the taint during checks and the `node-health-status` label |
| [HyperPod training operator](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html) | `HyperPodPyTorchJob`, `hyperpodrun`, `jobMaxRetryCount`, hang detection by log pattern |
| [Ray on HyperPod](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html) | Official documentation for running Ray on HyperPod |
| [SageMaker AI pricing](https://aws.amazon.com/sagemaker/ai/pricing/) | HyperPod USD per hour (us-east-1 and us-west-2): `ml.g4dn.xlarge` 0.7364, `ml.g6.xlarge` 1.127, `ml.g6.2xlarge` 1.222, `ml.g6.4xlarge` 1.654, `ml.g5.xlarge` 1.408, `ml.g5.2xlarge` 1.515, `ml.g5.8xlarge` 3.06, `ml.g6e.xlarge` 2.61 |
| [Amazon Bedrock AgentCore Code Interpreter](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html) | Describes the execution environment as a "containerized environment" and does not mention GPUs |

### AWS blogs

| Source | Facts it supports |
|---|---|
| [AWS Containers blog (2024): workload isolation with Kata Containers](https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/) | Kata + Firecracker on i3.metal |
| [AWS China blog (2026-07)](https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/) | c5.metal, Kata 3.31.0 + Cloud Hypervisor, OpenSandbox, Karpenter 1.12.1. Blog measurements: cold start about 3 s, pool claim about 230 ms. "CLH about 130 MB, QEMU about 160 MB" equals the Kata 3.31.0 `podFixed` defaults, so it is probably not a measurement |
| [AWS Korea tech blog "AWS에서 AI 에이전트 실행 환경 격리하기" (Isolating AI agent execution environments on AWS), part 1](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/) | Agent Sandbox v1.0.5 + gVisor release-20260928.0 on EKS 1.36, four isolation layers (Pod security settings, gVisor, NetworkPolicy, IMDS settings of a dedicated node group). The rest is in the list below the table |
| [Same series, part 2](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/) | Internet egress allowed by the default SandboxTemplate policy and DNS injection with public resolvers, IMDS and API reachable before NetworkPolicy was enabled, sandbox-router authorization (allow-all by default, TokenReview proves only validity, Tunnel mode bypasses NetworkPolicy). Measurements are in the list below the table |
| [Same series, part 3](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/) | Ably's operations case: one Sandbox per project, a dedicated on-demand Karpenter NodePool with `karpenter.sh/do-not-disrupt`, Kyverno and ExternalDNS, v1.0.8 `SandboxClaim.spec.env` starts fresh without a warm pool, runc today with a plan to evaluate Kata while keeping the API |

- **Rest of part 1**: runsc registered through NodeConfig, IMDSv2 required with hop limit 1, EKS Auto Mode cannot register runsc, RuntimeClass scheduling does not stop other pods that tolerate the same taint
- **Blog measurements in part 2 (EKS 1.36, m7i.xlarge)**: SandboxClaim to Ready about 2 s cold and about 55 ms from a warm pool, gVisor syscall cost from about 0.18 us to 2.2 us

### GitHub repositories and project documentation

| Source | Facts it supports |
|---|---|
| [gVisor installation](https://gvisor.dev/docs/user_guide/install/) | Latest release-20261109.0. Tarball-only since release-20260831 (`runsc`, `containerd-shim-runsc-v1`, and `gvisor-bin/`, which must stay next to `runsc`) |
| [gVisor release tarball (pinned URL)](https://storage.googleapis.com/gvisor/releases/release/20261109.0/x86_64/gvisor.tar.bz2) | A pinned release can be downloaded by URL (verify it with the `.sha512`) |
| [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/) | `nvproxy = "true"`, default capabilities `compute,utility`, driver policy (supported, unsupported, unknown), 580.178.04 supported since release-20260831.0. The rest is in the list below the table |
| [gVisor nvproxy driver table (release-20261109.0)](https://github.com/google/gvisor/blob/release-20261109.0/pkg/sentry/devices/nvproxy/version.go) | 580.159.04 and 580.178.04 are `addDriverABI` (supported), 595.71.05 is `addUnsupportedDriverABI`, 595.91.07 is absent (unknown). the development branch lacks 595.91.07 too (2026-11-14) |
| [NVIDIA 580.178.04 .run installer](https://download.nvidia.com/XFree86/Linux-x86_64/580.178.04/), [CUDA repo (Amazon Linux 2023)](https://developer.download.nvidia.com/compute/cuda/repos/amzn2023/x86_64/) | sha256 of the `.run` is `5975a86e...6d6f9` (NVIDIA's `.sha256sum`, same as the gVisor table). The repo has `kmod-nvidia-open-dkms-580.178.04`, `nvidia-driver-580.178.04` and more |
| [google/gvisor](https://github.com/google/gvisor) | gVisor source repository |
| [GKE Sandbox](https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods) | "Don't use GPU time-sharing in sandboxed Pods" |
| [Kata 4.3.1 NVIDIA GPU passthrough](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/use-cases/NVIDIA-GPU-passthrough-and-Kata-QEMU.md) | "Cold-plug is by design the only supported mode for NVIDIA GPU passthrough", the QEMU path |
| [Kata 4.3.1 hypervisors.md](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md) | GPU support for Cloud Hypervisor is not supported |
| [Kata issue #11687](https://github.com/kata-containers/kata-containers/issues/11687) | Maintainer answer (2025-08): "You should use the QEMU GPU runtime class." |
| [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers) | 4.3.1 (2026-10-21), runtime-rs as the default (since 4.0.0), the Go runtime deprecated but supported, the Helm chart `oci://ghcr.io/kata-containers/kata-deploy-charts/kata-deploy` with `deploymentMode` defaulting to `job`, RuntimeClass `overhead.podFixed` |
| [Firecracker FAQ](https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md), [CHANGELOG](https://github.com/firecracker-microvm/firecracker/blob/main/CHANGELOG.md) | Minimal device model, PCI support added in 1.13.0, no VFIO GPU passthrough in the changelog |
| [Modal Sandboxes](https://modal.com/docs/guide/sandbox) | "GPU Sandboxes are only supported with `runtime="gvisor"`" |
| [NVIDIA GPU Operator with Kata](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/deploy-kata-containers.html), [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator) | v26.7.2 sandbox mode values, `nvidia.com/pgpu`, "A node can only run one container runtime at a time", EKS validated with Ubuntu (AL2023 not listed) |
| [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin), [NVIDIA/nvidia-container-toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) | `deviceListStrategy: cdi-cri`, the container toolkit still required on the host |
| [awslabs/amazon-eks-ami v20261107](https://github.com/awslabs/amazon-eks-ami/releases/tag/v20261107) | AL2023 NVIDIA AMI: driver 580.178.04 by default (595.91.07 for g7 only), toolkit 1.20.1, containerd 2.3.7, no device plugin, CDI for kubelet 1.32 or later, user data runs between nodeadm-config and nodeadm-run |
| [aws/aws-network-policy-agent](https://github.com/aws/aws-network-policy-agent) | The node IP is allowed in both the ingress and the egress maps ("ensures kubelet liveness/readiness probes are never blocked") |
| [Karpenter docs](https://karpenter.sh/docs/), [aws/karpenter-provider-aws](https://github.com/aws/karpenter-provider-aws) | v1.15.2 (LTS v1.14.3), `karpenter.sh/v1`, `karpenter.k8s.aws/v1`, IMDS hop limit 1 by default, user MIME parts merged, EC2NodeClass `spec.cpuOptions.nestedVirtualization` |
| [eksctl docs: Cluster Access](https://docs.aws.amazon.com/eks/latest/eksctl/vpc-cluster-access.html) | "EKS does allow creating a configuration that allows only private access to be enabled, but eksctl doesn't support it during cluster creation": eksctl cannot create a cluster with only a private endpoint, so this asset creates the infrastructure with CDK |
| [aws/aws-cdk](https://github.com/aws/aws-cdk), [cdklabs/cdk-nag](https://github.com/cdklabs/cdk-nag) | `aws-cdk-lib` 2.276.0 and cdk-nag 3.0.2 are pinned. 2.276.0 works with CDK CLI 2.1148.1; moving to `aws-cdk-lib` 2.277.0 needs CLI 2.1148.2 or later (per the comment in the repository's `cdk/requirements.txt`) |
| [aws/sagemaker-hyperpod-cli](https://github.com/aws/sagemaker-hyperpod-cli) | The HyperPod dependency Helm chart (`helm_chart/HyperPodHelmChart`): health monitoring agent, deep health check RBAC, job-auto-restart, MPI operator, device plugin, Kueue |
| [awslabs/awsome-distributed-ai veRL example](https://github.com/awslabs/awsome-distributed-ai/tree/main/examples/training/verl/hyperpod-eks/rlvr) | veRL RLVR example on HyperPod EKS, pinned to veRL v0.6.1 (old keys), moved from the old aws-samples/awsome-distributed-training |
| [TRL docs](https://huggingface.co/docs/trl), [huggingface/trl](https://github.com/huggingface/trl), [PyPI trl 1.18.0](https://pypi.org/project/trl/1.18.0/) | TRL 1.18.0 (2026-11-13), supports vLLM 0.23 through 0.33.x, GRPOConfig defaults (`num_generations` 8, `beta` 0.0, `loss_type` "dapo", `scale_rewards` "group"), `None` handling in reward functions, async reward functions |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | vLLM 0.33.0 pins torch 2.14.0 and `transformers>=5.16.1,<5.21`, image `vllm/vllm-openai:v0.33.0` |
| [verl-project/verl](https://github.com/verl-project/verl) | veRL 0.9.1, the `reward.*` keys, the `compute_score` signature and return format, async recommended for sandboxed execution, Parquet columns |
| [kuberay-project/kuberay](https://github.com/kuberay-project/kuberay) | KubeRay v1.7.2, API `ray.io/v1` |
| [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct), [7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) | apache-2.0, ungated |
| [Qwen2.5-Coder-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct) | qwen-research (non-commercial) license, not used in this asset |
| [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) | v1.0.11 (2026-11-12), CRDs v1beta1 (Sandbox, SandboxTemplate, SandboxWarmPool, SandboxClaim), isolation delegated to the runtime through RuntimeClass, Kata examples and a GKE gVisor + L4 GPU example, SDKs (Python `k8s-agent-sandbox`, Go, TypeScript), sandbox-router |
| [agent-sandbox v1.0.11 install manifest](https://github.com/kubernetes-sigs/agent-sandbox/releases/download/v1.0.11/sandbox-with-extensions.yaml) | One manifest that installs the controller and the extensions |
| [AI on EKS: Agent Sandbox on EKS](https://awslabs.github.io/ai-on-eks/docs/infra/agents/agent-sandbox), [awslabs/ai-on-eks](https://github.com/awslabs/ai-on-eks) | gVisor kernel isolation, lifecycle management with the agent-sandbox CRDs (Sandbox, SandboxTemplate, SandboxWarmPool, SandboxClaim, v1beta1), no mention of GPUs (checked 2026-11). The rest is in the list below the table |
| [opensandbox-group/OpenSandbox](https://github.com/opensandbox-group/OpenSandbox) | release-1.2.1, Pool and BatchSandbox (v1alpha1) |
| [bytedance/SandboxFusion](https://github.com/bytedance/SandboxFusion) | `POST /run_code`, GPU execution serialized |

- **Rest of gVisor GPU support**: described against NVIDIA's open driver (the proprietary driver is not mentioned), documented GPUs (T4, A100/A10G, L4, H100), CDI compatibility, security scope ("much less effective ...", no validation of DMA buffers), the systrap platform on VMs
- **AI on EKS egress and node setup**: FQDN-based egress control (Cilium on Standard EKS, `ApplicationNetworkPolicy` on EKS Auto Mode), the KRO `AgentSandbox` resource, Karpenter with a gVisor NodePool (`runsc` installed through AL2023 user data)
- **AI on EKS runtime tiers**: `standard` (runc), `gvisor` (not on Auto Mode), `isolated-sandbox` (Nitro Sandboxes, on EKS Auto Mode with Kubernetes 1.36 or later or on Standard EKS with a custom AMI), Kata + Firecracker as a future tier (not included)

### Papers, blogs and reward hacking reports

| Source | Facts it supports |
|---|---|
| [KernelBench](https://github.com/ScalingIntelligence/KernelBench) | MIT, the `ModelNew` contract, allclose (fp32 1e-4, fp16/bf16 1e-2), 5 correctness trials and 100 performance trials, cuda_event timing with an L2 flush, `excessive_speedup_threshold` 10, the extra-stream gap and the host_time mode that measures all streams |
| [KernelBench v0.1 blog](https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/) | Reward hacking patterns: torch and cuBLAS calls, not calling the kernel, no-op kernels that reuse memory, stream timing mismatch |
| [Sakana AI CUDA Engineer](https://sakana.ai/ai-cuda-engineer/) | A memory exploit that skipped the correctness check |
| [Kevin-32B (Cognition)](https://cognition.com/blog/kevin-32b) | Copying the reference, try/except fallback, inheriting the reference class, reward 0 for PyTorch-only answers |
| [CUDA-L1 (arXiv 2507.14111)](https://arxiv.org/abs/2507.14111) | An extra stream fooled the timing in 82 of 250 cases (32.8%), lazy evaluation, caching |
| [INTELLECT-3 (arXiv 2512.16144)](https://arxiv.org/abs/2512.16144) | `kubectl exec` through the API at about 2.5 s per command, a gateway + headless Service + sidecar design, environments versioned independently of the trainer |

### Original source not confirmed

The primary source URLs of the items below were not confirmed. Find and check the original before citing them.

- **Northflank**: public material saying it uses Kata for GPUs and falls back to gVisor where nested virtualization is unavailable
- **TritonRL**: an approach that combines a rule-based linter with an LLM judge
- **KernelBench-Verified**: work mentioned alongside reward hacking countermeasures

Related pages: [Misconceptions](faq.md), [Troubleshooting](troubleshooting.md), [04 Reward integrity](../production/04_reward_integrity.md), [04 Platforms and instances](../concepts/04_platforms_and_instances.md)
