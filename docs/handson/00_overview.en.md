# 00 Hands-on overview

Send code to a sandbox and follow its verdict into a training step. You can also practice grading and switching pools without a GPU.

## Choose an exercise

- **[A · Train on EC2 GPUs](scenario_a.md)** Generate code, grade it with gVisor and update the model with GRPO.
- **[B1 · Train on HyperPod](07_hyperpod_b1.md)** Run the trainer on HyperPod and grade its code on an EC2 gVisor pool.
- **[B2 · Run all workers on HyperPod](07_hyperpod_b2.md)** Create EKS through HyperPod, then send code from the training GPU to two grading GPUs.
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
    | B2 · All workers on HyperPod | 0 (worker quotas are under SageMaker) | 4.56 |
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

Creating a cluster starts charges for nodes and the NAT gateway. Choose a tab for its <span id="main-path">steps</span> and expand the <span id="aws-layout-per-scenario">architecture diagram</span> at the end. Keep `cdk/tunnel.sh` open in a separate terminal for A, B1 and C. For managed B2, connect directly to the EKS API.

=== "A · EC2 GPU"

    **[Start A · Train on EC2 GPUs](scenario_a.md)**

    1. Create EKS with `SCENARIO=A`, open the tunnel and prepare all three images. Check `kubectl get nodes` for one `Ready` trainer and two `Ready` gVisor nodes.
    2. Check CUDA in a gVisor pod and deploy the `gvisor` v1 pool. Check that `scripts/ops/verify.sh gvisor v1` ends with `verified`.
    3. For a first run, train for five steps with `scripts/07_run_grpo.sh 5`. To practice switching versions, increase the grading node group to four before starting the 60-step run. Switch with `scripts/ops/rollout.sh gvisor v1 v2` during training, then [clean up the EC2 lab](99_cleanup.md).

    **Check the result** Check `routing` for the pool, `batch` (`reward_batch` in raw JSON) for verdicts and `train` for model updates. If you switched versions, wait for a v2 verdict before scaling down v1 with `--finish`.

    ??? note "A architecture diagram"
        One `g5.2xlarge` trains the model. Two `g5.xlarge` nodes grade submissions in the base configuration.

        [![EC2 trainer sending submissions to two gVisor sandboxes in scenario A](../images/architecture/scenario-a.drawio.png)](../images/architecture/scenario-a.drawio.png)

=== "B1 · HyperPod + EC2"

    **[Start B1 · Train on HyperPod and grade on EC2](07_hyperpod_b1.md)**

    1. Create EKS and the EC2 grading nodes with `scripts/02_create_cluster.sh --hyperpod`. Build the images with `hyperpodrun` in the trainer image, check CUDA on EC2, then attach the training node with `scripts/hyperpod/create.sh`.
    2. Once the HyperPod training node is `Ready` and `Schedulable`, deploy the EC2 `gvisor` v1 pool. Look for `verified` at the end of `scripts/ops/verify.sh gvisor v1`.
    3. Run `scripts/hyperpod/run_grpo.sh 1` for one training step. During [cleanup](99_cleanup.md#1-hyperpod-first-scenario-b), delete HyperPod first, then the EKS stack.

    **Check the result** Look for verdicts from the EC2 pool in `reward_batch` and `Completed` on the HyperPod Job.

    ??? note "B1 architecture diagram"
        One HyperPod `ml.g5.2xlarge` trains the model. Two EC2 `g5.xlarge` nodes grade submissions.

        [![A HyperPod training node using an EC2 grading pool in the same EKS cluster](../images/architecture/scenario-b1.drawio.png)](../images/architecture/scenario-b1.drawio.png)

=== "B2 · HyperPod"

    **[Start B2 · Run all system, training and grading workers on HyperPod](07_hyperpod_b2.md)**

    1. Check the three group quotas in `us-east-1` and set `SCENARIO=B2` and `K8S_VERSION=1.36` in `scripts/config.env`. Create EKS and its workers with `scripts/hyperpod/create_managed.sh` and prepare the three HyperPod images. Once EKS is `ACTIVE`, connect directly with `aws eks update-kubeconfig`.
    2. When all four workers are `Ready`, apply driver `580.178.04` to the two grading workers. Prepare the training operator and `gvisor-hyperpod` runtime, then deploy and verify the v1 pool.
    3. Submit one step with `scripts/hyperpod/run_grpo.sh 1`. When the Job reaches `Completed`, run `scripts/hyperpod/bench_b2.sh 32`. The system worker and then the training worker each send 32 submissions. Save the results and [delete the wizard stack](07_hyperpod_b2.md#cleanup).

    **Check the result** Check `reward_batch` for v1 verdicts from `gvisor-hyperpod`. Compare success counts and grading times for both clients in the [benchmark results](08_benchmark.md#hyperpod-b2).

    ??? note "B2 architecture diagram"
        All four workers run on HyperPod. The `system` group has one `ml.m5.xlarge`, `trainer` has one `ml.g5.2xlarge`, and `sandbox` has two `ml.g5.xlarge` nodes.

        [![EKS control plane and the three HyperPod instance groups](../images/architecture/scenario-b2.drawio.png?layout=aws)](../images/architecture/scenario-b2.drawio.png?layout=aws)

=== "C · CPU"

    **[Start C · Switch grading pools without GPUs](10_cpu_only.md)**

    1. Set `KATA_CPU_REPLICAS=1`, create EKS with `scripts/02_create_cluster.sh --cpu-only` and open the tunnel. Prepare the sandbox and control images.
    2. Run `scripts/kata/cpu_nodes.sh` to compare the kernels of three runtimes on the `c8i.2xlarge` node. Set `kata-clh-cpu` as the active pool. Check `gvisor-cpu`, `kata-clh-cpu` and `kata-qemu-cpu` v1. Each should report `verified`.
    3. Start `scripts/ops/simulate.sh 30 20` to send prepared submissions. Run `scripts/ops/rollout.sh kata-clh-cpu v1 v2` in another terminal. Check the batch logs, then [clean up the CPU lab](99_cleanup.md).

    **Check the result** After `SWITCH`, check that the next graded `batch` has verdicts from `kata-clh-cpu` v2. Each batch should have one grading version.

    ??? note "C architecture diagram"
        A simulator on a system node sends the submissions. All three CPU runtimes run on the same `c8i.2xlarge`.

        [![Three CPU pools on a c8i node in scenario C](../images/architecture/scenario-c.drawio.png)](../images/architecture/scenario-c.drawio.png)

## Other exercises by goal { #optional-and-operations }

- **[03 · Check GPU access in Kata](03_kata.md).** To compare gVisor and VM isolation, identify the T4 inside a Kata QEMU guest. Build the IOMMU AMI first, then add `g4dn.metal` with `WITH_KATA_GPU=1`. For a CPU comparison, use `WITH_KATA_CPU=1` and `c8i.2xlarge`.
- **[08 · Benchmark the runtimes](08_benchmark.md#runtime-results).** Once training has stopped and the v1 pools have passed verification, grade the same submission repeatedly. Compare per-request latency with throughput across the pool.
- **[11 · Revise code over multiple turns](11_multi_turn.md).** On the C path, claim one sandbox per episode. Check that the turns in an episode use the same pod and the claim is released when the episode ends.

## Clean up the lab { #next-step }

For A, B1 and C, follow [99 Cleanup](99_cleanup.md). For managed B2, use [HyperPod wizard stack cleanup](07_hyperpod_b2.md#cleanup). Nodes still incur charges after you scale pods to zero. To pause an EC2 lab, see [Scaling node groups to zero](99_cleanup.md#pausing-scale-node-groups-to-zero).

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
    - HyperPod can report `InService` while the trainer instance is still provisioning. Check `Ready` and `Schedulable` on the node before submitting training. [HyperPod checks](07_hyperpod_b1.md#how-to-verify)

The [script reference](../reference/scripts.md) lists arguments, timeouts and what happens on a second run. [Runtime comparison](../concepts/02_isolation_runtimes.md) · [Glossary](../reference/glossary.md) · [Run records](../reference/sources.md#aws-run-record) · [Further reading](../reference/references.md#ref-handson-00-overview)
