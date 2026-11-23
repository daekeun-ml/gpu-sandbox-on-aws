# Choose a learning path

New to sandboxes? Follow one answer from code to score in the [beginner guide](beginner/index.md), or grade it yourself in path 2.

<div id="choosing-a-starting-point" class="grid cards" markdown>

-   **<span id="pick-a-path-with-a-few-questions">Working without AWS?</span>**

    - [1 · See how grading works](#course-1)
    - [2 · Grade answers locally](#course-2)
    - [7 · Design a production service](#course-7)

-   **Running a lab on AWS?**

    - [3 · Switch grading pools on CPU](#course-3)
    - [4 · Train a model on EC2 GPUs](#course-4)
    - [5 · Train a model on HyperPod](#course-5)
    - [6 · Add a Kata GPU](#course-6)

</div>

## In a browser or on your computer { #steps-per-path }

### 1. Follow a submission through grading { #course-1 }

Read chapters 1–4 of the [beginner guide](beginner/index.md). In the [public demo](https://dohbsn4kn34ya.cloudfront.net/?lang=en#try), select **Missing ReLU** and replay the grading run. You'll see what happened when gVisor and Kata each ran the same code in isolation. Allow 1–2 hours for the reading and demo.

Why do both runs show **wrong answer** (`wrong_answer`)? The code adds two numbers but leaves negative sums unchanged. The task requires replacing those with zero. The sandbox runs the code, the grader compares its output with the expected answer, and the trainer uses the result to update the model.

??? note "Read more about isolation and training"
    - Which tasks need grading on a GPU? [When the sandbox needs a GPU](concepts/01_why_gpu_sandbox.md)
    - Which kernel handles a submission's requests under gVisor and Kata? [Isolation runtimes](concepts/02_isolation_runtimes.md)
    - What has to stay consistent when the grader changes during training? [On-policy RL with sandboxes](concepts/03_onpolicy_rl_with_sandboxes.md) · [Decision guide](concepts/05_decision_guide.md)

### 2. Grade correct and incorrect answers locally { #course-2 }

Follow sections 1–2 of the [first grading exercise](beginner/05_hands_on.md). Use Git and `uv` to prepare a Python 3.14 environment, then run the test that sends the same submissions to two local CPU servers. Allow 30–60 minutes including installation.

Look for **`1 passed`**. Both servers identified correct answers, wrong answers and policy violations as expected. This exercise runs without an AWS account or GPU.

??? example "Test output and an optional macOS exercise"
    ![Terminal showing 1 passed after checking submissions on two local CPU servers](images/learning/local-cpu-grading.png)

    On Linux, use the pytest exercise above. On macOS you can also launch both servers to inspect individual verdicts, or run two GRPO training steps with a small model. [Local run instructions](getting_started.md#4-loopback-smoke-run-macos)

### 7. Design a production service { #course-7 }

Follow a request from a training node in the [production architecture diagram](production/00_architecture.md). Mark where the gateway checks the caller and where to pin the grader version so every answer in a batch uses the same one. Allow 2–3 hours for a design review. All you need is a browser.

??? note "Reading for each design decision"
    - **Who can submit code, and what can it do?** [Security](production/02_security.md) · [Reward integrity](production/04_reward_integrity.md)
    - **Where does a request go, and when can it switch to a new version?** [Gateway and pools](production/03_gateway_and_pools.md) · [Sandbox versioning](production/05_sandbox_updates.md)
    - **How many nodes will the service need, and what will they cost?** [Capacity and nodes](production/01_capacity_and_nodes.md) · [Cost](production/08_cost.md) · [CDK stacks](production/09_cdk.md)
    - **How will operators track latency and errors across training nodes?** [Scaling with veRL](production/06_scaling_with_verl.md) · [Observability and operations](production/07_observability_and_operations.md)

## On AWS { #what-each-path-requires }

For your first AWS lab, [check your tools and regional quotas](handson/00_overview.md#prerequisites) before deploying. Charges begin when you create the cluster.

??? note "<span id='prerequisites-and-cost-per-path'>Time, node costs and quotas for paths 3–6</span>"
    | Path | Time to allow | Node cost (USD/hour) |
    |---|---|---:|
    | 3 · CPU only (C) | Half a day | About 0.57 |
    | 4 · EC2 GPU (A) | One day | About 3.42 |
    | 5 · HyperPod (B1 / B2) | A day or more | About 3.72 / 4.56 |
    | 6 · Add a Kata GPU | Half a day after path 3 or 4 | Add 7.824 for the metal node |

    <span id="scope-and-limits"></span>Node estimates use On-Demand rates in `us-west-2` and `us-east-1`. The EKS control plane (0.10 USD/hour under standard support), access instance, NAT gateway, storage and data transfer incur separate charges.

    - **CPU and EC2 GPU.** C needs 14 Standard vCPUs. A needs 6 Standard and 16 G/VT vCPUs. While gVisor v1 and v2 both run in A, allow 24 G/VT vCPUs and about 2.01 USD/hour in additional node costs.
    - **HyperPod.** B1 needs 6 Standard and 8 G/VT vCPUs, plus one SageMaker `ml.g5.2xlarge for cluster usage` instance. B2 needs quota for one HyperPod `ml.m5.xlarge`, one `ml.g5.2xlarge` and two `ml.g5.xlarge` instances.
    - **Kata GPU.** The metal node uses another 96 G/VT vCPUs. Adding it to C brings node costs to about 8.39 USD/hour. Adding both the CPU rehearsal node and the metal node to A brings the total to about 11.61 USD/hour. Allow 16 Standard vCPUs when the CPU rehearsal node and temporary AMI builder run together. [Instance quotas and costs](concepts/04_platforms_and_instances.md)

### 3. Switch grading pools on CPU · scenario C { #course-3 }

In the [CPU-only lab](handson/10_cpu_only.md), run gVisor and Kata on one `c8i.2xlarge`. A simulator keeps sending prepared submissions as you switch the pool of grading servers from v1 to v2. This path runs without a GPU or a training job.

Read the `batch` line after `SWITCH`. When `kata-clh-cpu/v2` returns `ok` and `wrong_answer`, the new pool has graded the submissions.

??? example "Compare the batches on each side of the switch"
    Batch 6 used v1 and batch 7 used v2. Both returned one correct answer and two wrong answers.

    ![Simulator log switching to v2 between batches 6 and 7 while grading the same submissions](images/terminal/simulate-switch.png)

### 4. Train with GRPO on EC2 GPUs · scenario A { #course-4 }

Begin with [the scenario A walkthrough](handson/scenario_a.md), then check [GPU access in gVisor](handson/02_gvisor.md) and [deploy the grading pool](handson/04_sandbox_pools.md). In the [GRPO lab](handson/05_grpo_training.md), the model generates several answers and uses their scores to update its weights.

[Switch pools during training](handson/06_sandbox_update.md) to see one batch finish on a single grader version and the next start on v2. [Batch logs before and after the switch](handson/06_sandbox_update.md#switch-batches)

### 5. Train with GRPO on HyperPod · scenario B1 { #course-5 }

Start with B1 in the [HyperPod lab](handson/07_hyperpod_b1.md). SageMaker HyperPod runs the trainer, and a gVisor pool on EC2 grades the code. Check that the trainer ran on a HyperPod node, that `reward_batch` recorded grading outcomes, and that the training job reached `Completed`.

The guide includes the verdicts for 12 submissions from one training step and a separate benchmark that sent a fixed kernel 32 times after training. [B1 run and training logs](handson/07_hyperpod_b1.md#how-to-verify) · [B1 benchmark results](handson/08_benchmark.md#hyperpod-b1)

??? note "Run the grading nodes on HyperPod too"
    [Managed B2](handson/07_hyperpod_b2.md) puts the CPU worker, the GPU trainer and both GPU graders in the HyperPod EKS workflow. B1 and B2 use separate clusters.

### 6. Use a GPU inside a Kata VM · add to path 3 or 4 { #course-6 }

Before cleaning up path 3 or 4, follow the CPU rehearsal and GPU passthrough stages of the [Kata lab](handson/03_kata.md). [Deploy the pool](handson/04_sandbox_pools.md) and run `scripts/ops/verify.sh kata-qemu v1`. Look for `Tesla T4` and `PASS` on all six test submissions to confirm GPU grading inside the VM. [GPU verification from the Kata guest](handson/03_kata.md#gpu-run)

??? note "Compare gVisor and Kata GPU performance"
    On path 4, wait for training to stop, then run the benchmark while both `gvisor v1` and `kata-qemu v1` are Ready. If you already scaled gVisor v1 down with `--finish` in chapter 06, bring it back first. [Runtime benchmark steps and results](handson/08_benchmark.md#runtime-results)

### When you pause or finish { #three-habits-that-prevent-cost-accidents }

After paths 3–6, follow [99 Cleanup](handson/99_cleanup.md) and check the last table for remaining lab instances. **For HyperPod, run `scripts/hyperpod/delete.sh` before deleting EKS.**

??? note "Costs while keeping a cluster between sessions"
    Scale unused EC2 practice node groups to zero. Scaling pods down still leaves their nodes running. The two system nodes, EKS and the NAT gateway also continue to incur charges while the cluster exists. [Resource cleanup](handson/99_cleanup.md)

<span id="next-steps"></span><span id="if-you-get-stuck"></span>Look up unfamiliar terms in the [glossary](reference/glossary.md) and error messages in [troubleshooting](reference/troubleshooting.md). [Frequently asked questions](reference/faq.md) · [Configuration](reference/configuration.md)
