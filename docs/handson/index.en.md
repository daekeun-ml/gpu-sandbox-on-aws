---
hide:
  - footer
---

# Hands-on overview

<span id="00-hands-on-overview"></span>

## Start from your terminal { #quickstart }

```bash
git clone https://github.com/daekeun-ml/gpu-sandbox-on-aws.git
cd gpu-sandbox-on-aws
./scripts/quickstart.sh
```

If the project is already on your machine, run only the last command from its directory. With your lab AWS credentials active, choose `A`, `B1`, `B2` or `C`. The `init` step creates the configuration file. Charges start when `infra` provisions the cluster.

To preview the steps, add `plan` after the scenario name, for example `./scripts/quickstart.sh B2 plan`. [Clean up after the lab](cleanup.md#quickstart)

## Choose an exercise

To run the commands yourself, choose a configuration below and follow **shared steps 01–03**. Start the scenario workload once the grading pool reports `verified`.

- **[Train on EC2 GPUs (A)](common/01_provision/index.md#__tabbed_1_1)** Generate code, grade it with gVisor and update the model with GRPO.
- **[Train on HyperPod (B1)](common/01_provision/index.md#__tabbed_1_2)** Run the trainer on HyperPod and grade its code on an EC2 gVisor pool.
- **[Run all workers on HyperPod (B2)](common/01_provision/index.md#__tabbed_1_3)** Create EKS through HyperPod, then send code from the training GPU to two grading GPUs.
- **[Switch pools without GPUs (C)](common/01_provision/index.md#__tabbed_1_4)** Compare three CPU runtimes and switch from v1 to v2 as the simulator sends submissions.

After choosing a path, **check the nodes and then the grading pool**. A `Ready` node can accept pods. Later, `verified` on the grading pool means the sample submissions received their expected verdicts. Look for each result at its own step.

## Check before deploying { #prerequisites }

For A, B1 and C, finish [local setup](start.md) and run `scripts/01_check_prereqs.sh`. Check the account, Region and EC2 vCPU quotas in its output. For B1, also check the HyperPod trainer quota. For B2, start with the [three regional SageMaker quotas](common/01_provision/hyperpod.md#check-regional-quotas).

<div id="time-and-cost" markdown>

??? note "Quotas, hourly cost and expected duration by scenario"
    Allow 20–30 minutes to create the cluster. On a `g5.2xlarge`, five GRPO steps took about 12 minutes and 60 steps about 50 minutes, including image and model downloads. A 30-batch CPU simulation took about 16 minutes.

    | Base configuration | EC2 quota required (vCPUs) | Nodes (USD/hour) |
    |---|---|---:|
    | A (EC2 GPU) | G/VT 16, Standard 6 | 3.42 |
    | B1 (HyperPod trainer) | G/VT 8, Standard 6 | 3.72 |
    | B2 (All workers on HyperPod) | 0 (worker quotas are under SageMaker) | 4.56 |
    | C (CPU only) | Standard 14 | 0.57 |

    B1 also needs one `ml.g5.2xlarge for cluster usage` instance under SageMaker. Quotas apply per Region.

    These estimates use On-Demand rates in `us-west-2` and `us-east-1`. Add the EKS control plane (0.10 USD/hour under standard support), access instance, NAT gateway, storage, logs and data transfer.

    - **Switching gVisor versions.** In A, two additional `g5.xlarge` nodes run v2 alongside v1. Allow 24 G/VT vCPUs and about 2.01 USD/hour in temporary node costs.
    - <span id="minimal-path-and-full-path">**Adding Kata.**</span> With both a `c8i.2xlarge` and a `g4dn.metal`, A's nodes cost about 11.61 USD/hour. Allow 112 G/VT vCPUs, or 120 during the gVisor switch. Standard usage reaches 16 vCPUs while the CPU node and the temporary AMI builder are both running. [Instance costs and quotas](../concepts/04_platforms_and_instances.md)

</div>

??? note "Tools, configuration and where to check quotas"
    - Install the AWS CLI, CDK CLI 2.1148.1 or later, Node.js 22 or 24, `kubectl`, Helm, Docker, Python, `jq` and the Session Manager plugin. Check `docker buildx version` as well. HyperPod also uses `git`. [Cluster and images](common/01_provision/cdk.md) covers the CDK libraries and bootstrapping each account and Region.
    - If the configuration file is missing, copy `scripts/config.env.example` to `scripts/config.env`. Check `AWS_REGION`, `CLUSTER_NAME` and `SCENARIO`. Leave `WITH_KATA_CPU` and `WITH_KATA_GPU` at `0` for the base paths. Allow at least 100 GB of free disk on the x86_64 image build host.
    - In Service Quotas, select your lab Region. Under EC2, check the applied values for `Running On-Demand G and VT instances` and `Running On-Demand Standard`. For C, also check that the `c8i.2xlarge` supported features include `nested-virtualization`.

## Follow your scenario { #step-order }

Creating a cluster starts charges for nodes and the NAT gateway. Choose a tab for its <span id="main-path">steps</span> and expand the <span id="aws-layout-per-scenario">architecture diagram</span> at the end. Keep `cdk/tunnel.sh` open in a separate terminal for A, B1 and C. For managed B2, connect directly to the EKS API.

=== "A (EC2 GPU)"

    [01 Provision the cluster](common/01_provision/index.md#__tabbed_1_1) → [02 Prepare the runtime](common/02_runtimes/index.md#__tabbed_1_1) → [03 Deploy and verify the pool](common/03_pools/index.md#__tabbed_1_1)

    After verifying the pool, start the **[A walkthrough](scenarios/a/index.md)**.

    **Check the result** Check `routing` for the pool, `batch` (`reward_batch` in raw JSON) for verdicts and `train` for model updates. If you switched versions, wait for a v2 verdict before scaling down v1 with `--finish`.

    ??? note "A architecture diagram"
        One `g5.2xlarge` trains the model. Two `g5.xlarge` nodes grade submissions in the base configuration.

        [![EC2 trainer sending submissions to two gVisor sandboxes in scenario A](../images/architecture/scenario-a.drawio.png)](../images/architecture/scenario-a.drawio.png)

=== "B1 (HyperPod + EC2)"

    [01 Provision the cluster](common/01_provision/index.md#__tabbed_1_2) → [02 Prepare the runtime](common/02_runtimes/index.md#__tabbed_1_2) → [03 Deploy and verify the pool](common/03_pools/index.md#__tabbed_1_2)

    After verifying the pool, start the **[B1 walkthrough](scenarios/b/b1.md)**.

    **Check the result** Look for verdicts from the EC2 pool in `reward_batch` and `Completed` on the HyperPod Job.

    ??? note "B1 architecture diagram"
        One HyperPod `ml.g5.2xlarge` trains the model. Two EC2 `g5.xlarge` nodes grade submissions.

        [![A HyperPod training node using an EC2 grading pool in the same EKS cluster](../images/architecture/scenario-b1.drawio.png)](../images/architecture/scenario-b1.drawio.png)

=== "B2 (HyperPod)"

    [01 Provision the cluster](common/01_provision/index.md#__tabbed_1_3) → [02 Prepare the runtime](common/02_runtimes/index.md#__tabbed_1_3) → [03 Deploy and verify the pool](common/03_pools/index.md#__tabbed_1_3)

    After verifying the pool, start the **[B2 walkthrough](scenarios/b/b2.md)**.

    **Check the result** Check `reward_batch` for v1 verdicts from `gvisor-hyperpod`. Compare success counts and grading times for both clients in the [benchmark results](benchmarks/index.md#hyperpod-b2).

    ??? note "B2 architecture diagram"
        All four workers run on HyperPod. The `system` group has one `ml.m5.xlarge`, `trainer` has one `ml.g5.2xlarge`, and `sandbox` has two `ml.g5.xlarge` nodes.

        [![EKS control plane and the three HyperPod instance groups](../images/architecture/scenario-b2.drawio.png?layout=aws)](../images/architecture/scenario-b2.drawio.png?layout=aws)

=== "C (CPU)"

    [01 Provision the cluster](common/01_provision/index.md#__tabbed_1_4) → [02 Prepare the runtime](common/02_runtimes/index.md#__tabbed_1_4) → [03 Deploy and verify the pool](common/03_pools/index.md#__tabbed_1_4)

    After verifying the pool, start the **[C walkthrough](scenarios/c/index.md)**.

    **Check the result** After `SWITCH`, check that the next graded `batch` has verdicts from `kata-clh-cpu` v2. Each batch should have one grading version.

    ??? note "C architecture diagram"
        A simulator on a system node sends the submissions. All three CPU runtimes run on the same `c8i.2xlarge`.

        [![Three CPU pools on a c8i node in scenario C](../images/architecture/scenario-c.drawio.png)](../images/architecture/scenario-c.drawio.png)

## After the scenario workload { #optional-and-operations }

- [Benchmark the runtimes](benchmarks/index.md) after training or the CPU simulation ends. In B2, compare requests from the system worker with requests from the trainer.
- To revise a submission over several turns in one sandbox, follow [multi-turn grading](extensions/multi_turn.md). C uses its existing CPU node. A needs one free GPU.


## Clean up the lab { #next-step }

For A, B1 and C, follow [Cleanup](cleanup.md). For managed B2, use [HyperPod wizard stack cleanup](scenarios/b/b2.md#cleanup). Nodes still incur charges after you scale pods to zero. To pause an EC2 lab, see [Scaling node groups to zero](cleanup.md#pausing-scale-node-groups-to-zero).

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

    <span id="request-path"></span>**Grading.** The trainer reads the pool version for a batch from the `sandbox-routing` ConfigMap. The headless Service returns ready pod addresses through DNS. The trainer calls `/v1/evaluate`. The pod verifies the token signature with JWKS and returns a verdict. If a busy pod returns `503 busy`, the client retries another pod. [Pool deployment and authentication](common/03_pools/details.md)

??? note "<span id='how-to-verify'>Reading Ready, verified and reward_batch in the logs</span>"
    - A `Ready` node is available to Kubernetes for scheduling. The `verified` line from `ops/verify.sh` means the pool passed the automated checks. Compare the two kernel strings in the first check yourself.
    - `reward_batch` records submission counts and verdicts. If you see repeated `sandbox_error` results, check [pool health and authentication](../reference/troubleshooting.md) alongside the training steps.
    - Prefix a command with `GPUSANDBOX_LOG=json` for raw events. For an ordinary Kubernetes Job already running, use `kubectl -n rl-trainer logs -f job/<job-name>`.

??? note "When a script is still waiting"
    - The gVisor smoke pod has a 15-minute deadline. The pool rollout allows up to 30 minutes. These are wait limits. To see why a pod is pending, inspect its events with `kubectl -n sandbox describe pod <pod-name>` for a grading pod.
    - Kata CPU setup took about 14 minutes in the practice account, mostly installing kata-deploy. Kata GPU setup has two runs. The first builds the AMI when `KATA_IOMMU_AMI_ID` is empty. After saving the ID, enable `WITH_KATA_GPU=1` and rerun cluster creation with the original scenario option. The second `scripts/kata/gpu_nodes.sh` run checks for `nvidia.com/pgpu` on the metal node.
    - HyperPod can report `InService` while the trainer instance is still provisioning. Check `Ready` and `Schedulable` on the node before submitting training. [HyperPod checks](scenarios/b/b1.md#how-to-verify)

The [script reference](../reference/scripts.md) lists arguments, timeouts and what happens on a second run. [Runtime comparison](../concepts/02_isolation_runtimes.md), [Glossary](../reference/glossary.md), [Run records](../reference/sources.md#aws-run-record), [Further reading](../reference/references.md#ref-handson-00-overview)
