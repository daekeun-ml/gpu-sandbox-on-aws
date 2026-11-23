# 00 Hands-on overview

Send code to a sandbox and follow its verdict into a training step. You can also practice grading and switching pools without a GPU.

## Choose an exercise

- **[A · Train on EC2 GPUs](01_cluster_and_images.md)** Generate code, grade it with gVisor and update the model with GRPO.
- **[B1 · Train on HyperPod](07_hyperpod.md)** Run the trainer on HyperPod and grade its code on an EC2 gVisor pool.
- **[C · Switch pools without GPUs](10_cpu_only.md)** Compare three CPU runtimes and switch from v1 to v2 as the simulator sends submissions.

After choosing a path, **check the nodes and then the grading pool**. A `Ready` node can accept pods. Later, `verified` on the grading pool means the sample submissions received their expected verdicts. Look for each result at its own step.

## Check before deploying { #prerequisites }

Complete the local test and `scripts/config.env` setup in [Getting started](../getting_started.md). From the repository root, run the read-only check for your tools and AWS account configuration.

```bash
scripts/01_check_prereqs.sh
```

Check the **AWS account, Region and EC2 quota values** in the output against your planned deployment. For HyperPod, also check the SageMaker quota in Service Quotas.

<div id="time-and-cost" markdown>

??? note "Quotas, hourly cost and expected duration by scenario"
    Allow 20–30 minutes to create the cluster. On a `g5.2xlarge`, five GRPO steps took about 12 minutes and 60 steps about 50 minutes, including image and model downloads. A 30-batch CPU simulation took about 16 minutes.

    | Base configuration | EC2 quota required (vCPUs) | Nodes (USD/hour) |
    |---|---|---:|
    | A · EC2 GPU | G/VT 16, Standard 6 | 3.42 |
    | B1 · HyperPod trainer | G/VT 8, Standard 6 | 3.72 |
    | C · CPU only | Standard 14 | 0.57 |

    B1 also needs one `ml.g5.2xlarge for cluster usage` instance under SageMaker. Quotas apply per Region.

    These estimates use On-Demand rates in `us-west-2` and `us-east-1`. Add the EKS control plane (0.10 USD/hour under standard support), access instance, NAT gateway, storage, logs and data transfer.

    - **Switching gVisor versions.** In A, two additional `g5.xlarge` nodes run v2 alongside v1. Allow 24 G/VT vCPUs and about 2.01 USD/hour in temporary node costs.
    - <span id="minimal-path-and-full-path">**Adding Kata.**</span> With both a `c8i.2xlarge` and a `g4dn.metal`, A's nodes cost about 11.61 USD/hour. Allow 112 G/VT vCPUs, or 120 during the gVisor switch. Standard usage reaches 16 vCPUs while the CPU node and the temporary AMI builder are both running. [Instance costs and quotas](../concepts/04_platforms_and_instances.md)

</div>

??? note "Tools, configuration and where to check quotas"
    - Install the AWS CLI, CDK CLI 2.1148.1 or later, Node.js 22 or 24, `kubectl`, Helm, Docker, Python, `jq` and the Session Manager plugin. Check `docker buildx version` as well. HyperPod also uses `git`. [01 Cluster and images](01_cluster_and_images.md) covers the CDK libraries and bootstrapping each account and Region.
    - If the configuration file is missing, copy `scripts/config.env.example` to `scripts/config.env`. Check `AWS_REGION`, `CLUSTER_NAME` and `SCENARIO`. Leave `WITH_KATA_CPU` and `WITH_KATA_GPU` at `0` for the base paths. Allow at least 100 GB of free disk on the x86_64 image build host.
    - In Service Quotas, select your lab Region. Under EC2, check the applied values for `Running On-Demand G and VT instances` and `Running On-Demand Standard`. For C, also check that the `c8i.2xlarge` supported features include `nested-virtualization`.

## Follow your scenario { #step-order }

Creating the cluster starts charges for resources including nodes and the NAT gateway. <span id="main-path">Follow one tab</span> for the run order and <span id="aws-layout-per-scenario">its architecture diagram</span>. After provisioning EKS, keep `cdk/tunnel.sh` running in a separate terminal while you work with the cluster.

=== "A · EC2 GPU"

    1. **[Create the cluster and images](01_cluster_and_images.md).** With `SCENARIO=A`, run `scripts/02_create_cluster.sh`. Open the tunnel and use `kubectl get nodes` to check that one trainer and two gVisor nodes are `Ready`. Save the three image URIs printed by `scripts/03_build_push_images.sh` in the configuration file.
    2. **[Check GPU access](02_gvisor.md).** Run `scripts/04_install_gpu_stack.sh`. The gVisor smoke pod should print `cuda ok:` and the GPU name.
    3. **[Deploy and verify the grading pool](04_sandbox_pools.md).** Set up namespaces and authentication with `scripts/05_setup_namespaces_auth.sh`, then run `scripts/06_deploy_sandboxes.sh gvisor v1`. Look for `pool sandbox-gvisor-v1 verified` at the end of `scripts/ops/verify.sh gvisor v1`.
    4. **[Start GRPO training](05_grpo_training.md).** Run `scripts/07_run_grpo.sh`. The `routing` event identifies the selected pool. Look for verdicts in a `batch` line (`reward_batch` in raw JSON) and for the training step to advance.
    5. **[Switch to v2 during training](06_sandbox_update.md).** Increase the sandbox node group to four nodes so v1 and v2 can hold GPUs at the same time. While training is running, run `scripts/ops/rollout.sh gvisor v1 v2` from another working terminal. Once a new batch has been graded on v2, use `--finish` to scale down v1.

    ??? note "A diagram · Training and grading on EC2"
        The `g5.2xlarge` trainer updates the model. The two `g5.xlarge` sandbox nodes each hold an A10G for grading. Select the diagram to enlarge it.

        [![EC2 trainer sending submissions to two gVisor sandboxes in scenario A](../images/architecture/scenario-a.drawio.png)](../images/architecture/scenario-a.drawio.png)

=== "B · HyperPod"

    1. **[Prepare the B1 cluster and images](07_hyperpod.md).** Run `scripts/02_create_cluster.sh --hyperpod` to create EKS and the EC2 grading nodes. Open the tunnel, then build the trainer with `HYPERPOD=1 scripts/03_build_push_images.sh` to include `hyperpodrun`. Save the printed image URIs in the configuration file.
    2. **Connect the training node.** Check the EC2 GPU with `scripts/04_install_gpu_stack.sh`, then run `scripts/hyperpod/create.sh`. Verify that the HyperPod trainer node is `Ready` and its `node-health-status` is `Schedulable`.
    3. **Verify the grading pool.** Run `scripts/05_setup_namespaces_auth.sh` and deploy the EC2 pool with `scripts/06_deploy_sandboxes.sh gvisor v1`. Look for `verified` in `scripts/ops/verify.sh gvisor v1`.
    4. **[Follow one training step](07_hyperpod.md#how-to-verify).** Submit the Job with `scripts/hyperpod/run_grpo.sh 1`. Check that the trainer pod ran on the HyperPod node, `reward_batch` recorded verdicts from the EC2 pool and the Job reached `Completed`.

    ??? note "B1 diagram · HyperPod trainer and EC2 grading pool"
        The trainer uses an `ml.g5.2xlarge`. The gVisor sandboxes run on two EC2 `g5.xlarge` nodes.

        [![A HyperPod training node using an EC2 grading pool in the same EKS cluster](../images/architecture/scenario-b1.drawio.png)](../images/architecture/scenario-b1.drawio.png)

    **[B2 · Run all workers on HyperPod](07_hyperpod_b2.md)** uses the EKS creation workflow in HyperPod. `system` hosts the CPU pods, `trainer` trains the model and `sandbox` runs two GPU graders. Check the three instance groups before running the same GRPO exercise.

=== "C · CPU"

    1. **[Prepare the CPU cluster](10_cpu_only.md).** Run `scripts/02_create_cluster.sh --cpu-only` to create EKS and its `c8i.2xlarge` sandbox node. Open the tunnel. Save the sandbox and control image URIs printed by `scripts/03_build_push_images.sh --no-trainer` in the configuration file.
    2. **Check the runtimes.** `scripts/kata/cpu_nodes.sh` starts gVisor, Kata with Cloud Hypervisor, and Kata with QEMU smoke pods on the same node. Compare the kernel reported inside each pod with the host kernel printed at the end.
    3. **Deploy and verify three pools.** Set `KATA_CPU_REPLICAS=1` in the configuration file and run `ACTIVE_RUNTIME=kata-clh-cpu scripts/05_setup_namespaces_auth.sh`. Deploy v1 of each CPU pool and verify each with `scripts/ops/verify.sh`. [Pool deployment commands](10_cpu_only.md)
    4. **Switch grading versions.** Run `scripts/ops/simulate.sh 30 20` in one working terminal to send prepared submissions. Run `scripts/ops/rollout.sh kata-clh-cpu v1 v2` in another. Batches should use v1 before the switch and v2 afterward, with one version per batch.

    ??? note "C diagram · Three runtimes on a CPU node"
        A simulator on a system node sends submissions to the grading pools. All three runtimes share one `c8i.2xlarge`.

        [![Three CPU pools on a c8i node in scenario C](../images/architecture/scenario-c.drawio.png)](../images/architecture/scenario-c.drawio.png)

## Other exercises by goal { #optional-and-operations }

- **[03 · Check GPU access in Kata](03_kata.md).** To compare gVisor and VM isolation, identify the T4 inside a Kata QEMU guest. Build the IOMMU AMI first, then add `g4dn.metal` with `WITH_KATA_GPU=1`. For a CPU comparison, use `WITH_KATA_CPU=1` and `c8i.2xlarge`.
- **[08 · Benchmark the runtimes](08_benchmark.md#runtime-results).** Once training has stopped and the v1 pools have passed verification, grade the same submission repeatedly. Compare per-request latency with throughput across the pool.
- **[11 · Revise code over multiple turns](11_multi_turn.md).** On the C path, claim one sandbox per episode. Check that the turns in an episode use the same pod and the claim is released when the episode ends.
- **[09 · Replay a scoring run](09_demo_site.md).** Open the [public demo](https://dohbsn4kn34ya.cloudfront.net/?lang=en) to see results before creating a cluster. Chapter 09 shows how to publish your own recording with S3 and CloudFront.

## Clean up the lab { #next-step }

Keep the tunnel open for [99 Cleanup](99_cleanup.md). If you used Agent Sandbox, finish the episodes and clean up its claims and warm pools first. **For B, delete HyperPod with `scripts/hyperpod/delete.sh` before removing EKS.** On all three paths, `scripts/08_cleanup.sh` removes the EKS stack. Check the final instance list for remaining lab nodes. A demo site you deployed has its own cleanup step.

To delete the ECR images too, use the `--images` option during cleanup. Scaling sandbox pods to zero leaves EC2 nodes billable. To pause and resume later, see [Scaling node groups to zero](99_cleanup.md#pausing-scale-node-groups-to-zero).

## Architecture and log details { #architecture }

The [deployment diagrams in the demo](https://dohbsn4kn34ya.cloudfront.net/architecture.html?lang=en) show the path of a request for each scenario.

??? note "<span id='node-groups-and-namespaces'>Node groups and namespaces</span>"
    Training Jobs in `rl-trainer` and grading pods in `sandbox` run on different nodes. The `gpusandbox/role` taint on sandbox nodes requires a matching toleration. Node management DaemonSets such as the GPU device plugin also run there.

    | Default node group | Role and runtime |
    |---|---|
    | `system` | Two `m6i.large` nodes run CoreDNS and add-ons |
    | `trainer` | A's `g5.2xlarge` trains the model |
    | `sandbox-gvisor` | Two `g5.xlarge` nodes run the `gvisor` GPU pool in A and B1 |
    | `sandbox-kata-cpu` | A `c8i.2xlarge` runs `gvisor-cpu`, `kata-clh-cpu` and `kata-qemu-cpu` |
    | `sandbox-kata-gpu` | A `g4dn.metal` runs the `kata-qemu` pool with the `kata-qemu-nvidia-gpu` RuntimeClass |

??? note "From the workstation to EKS and from the trainer to a sandbox"
    <span id="infrastructure-and-access-cdk-tunnel"></span>**Cluster access.** `cdk/tunnel.sh` connects `127.0.0.1:8443` on the workstation to the private EKS API through the SSM access instance. `kubectl config current-context` should report `<CLUSTER_NAME>-tunnel`.

    <span id="request-path"></span>**Grading.** The trainer reads the pool version for a batch from the `sandbox-routing` ConfigMap. The headless Service returns ready pod addresses through DNS. The trainer calls `/v1/evaluate`. The pod verifies the token signature with JWKS and returns a verdict. If a busy pod returns `503 busy`, the client retries another pod. [Pool deployment and authentication](04_sandbox_pools.md)

??? note "<span id='how-to-verify'>Reading Ready, verified and reward_batch in the logs</span>"
    - A `Ready` node is available to Kubernetes for scheduling. The `verified` line from `ops/verify.sh` means the pool passed the automated checks. Compare the two kernel strings in the first check yourself.
    - `reward_batch` records submission counts and verdicts. If you see repeated `sandbox_error` results, check [pool health and authentication](../reference/troubleshooting.md) alongside the training steps.
    - Prefix a command with `GPUSANDBOX_LOG=json` for raw events. For an ordinary Kubernetes Job already running, use `kubectl -n rl-trainer logs -f job/<job-name>`.

??? note "When a script is still waiting"
    - The gVisor smoke pod has a 15-minute deadline. The pool rollout allows up to 30 minutes. These are wait limits. To see why a pod is pending, inspect its events with `kubectl -n sandbox describe pod <pod-name>` for a grading pod.
    - Kata CPU setup took about 14 minutes in the practice account, mostly installing kata-deploy. Kata GPU setup has two runs. The first builds the AMI when `KATA_IOMMU_AMI_ID` is empty. After saving the ID, enable `WITH_KATA_GPU=1` and rerun cluster creation with the original scenario option. The second `scripts/kata/gpu_nodes.sh` run checks for `nvidia.com/pgpu` on the metal node.
    - HyperPod can report `InService` while the trainer instance is still provisioning. Check `Ready` and `Schedulable` on the node before submitting training. [HyperPod checks](07_hyperpod.md#how-to-verify)

The [script reference](../reference/scripts.md) lists arguments, timeouts and what happens on a second run. [Runtime comparison](../concepts/02_isolation_runtimes.md) · [Glossary](../reference/glossary.md) · [Run records](../reference/sources.md#aws-run-record) · [Further reading](../reference/references.md#ref-handson-00-overview)
