# When the sandbox needs a GPU

!!! info "TL;DR"
    The work that runs inside the sandbox determines whether it needs a GPU. This repository checks the correctness and execution time of generated GPU kernels to calculate a reward. A CPU sandbox is enough for tasks graded by CPU unit tests.

## Work that needs a GPU

Suppose you ask a model to write a faster Triton matrix multiplication kernel. The evaluator runs the submission and the reference implementation on the target GPU with the same inputs. A submission can earn a speed score once its output matches the reference. The sandbox runs the generated code in an environment separate from the training server and sends the evaluation results back.

KernelBench uses PyTorch reference implementations to evaluate the correctness and performance of generated GPU kernels. In CUDA Agent, researchers at ByteDance Seed and Tsinghua University trained a model using rewards based on GPU verification and performance against `torch.compile`. [KernelBench paper](https://arxiv.org/abs/2502.10517) [CUDA Agent](https://cuda-agent.github.io/)

| Other work | When the sandbox uses a GPU |
|---|---|
| Model inference | If inputs need to stay local, the sandbox can run a model on its GPU to generate or score answers. A call to an external model API can run on CPU. |
| Simulation | A GPU physics engine simulates repeated attempts by a robot to grasp an object, and the task measures the success rate. [NVIDIA Isaac Lab](https://developer.nvidia.com/isaac/lab) |
| Model training and tuning | An agent changes training code or settings, trains the model on a GPU, and compares accuracy. |

## CPU checks and GPU evaluation

A training server can use GPUs while grading with CPU unit tests. In this repository's kernel tasks, the trainer uses the CPU to extract code from each answer and check it against the policy. The GPU sandbox runs submissions that pass that check and compares their correctness and speed.

**Speedup** is the reference execution time divided by the submission's execution time. If the reference takes 4 ms and a correct submission takes 2 ms on the same GPU, the speedup is 2×.

![Submissions that pass CPU checks in the trainer go to the GPU pool. The CPU-only pool is a separate lab configuration.](../images/figures/concepts-01_why_gpu_sandbox--two-tier.en.svg)

## Operating GPU sandboxes

- **Device access** Firecracker v1.18.0 lacks GPU passthrough, which attaches a physical GPU directly to a VM. E2B sandboxes are also CPU-only. This repository uses gVisor and Kata + QEMU for its GPU labs. [Firecracker FAQ](https://github.com/firecracker-microvm/firecracker/blob/v1.18.0/FAQ.md) [E2B GPU support](https://docs.e2b.dev/faq/gpu-support) [Isolation runtimes](02_isolation_runtimes.md)
- **Consistent measurements** Other work running on the same GPU can change the execution time of a submission and affect its speed score. The lab assigns one GPU per pod and evaluates one submission at a time in each pod. [Deploy and verify sandbox pools](../handson/04_sandbox_pools.md)
- **Cost of concurrency** In this setup, ten pods running at the same time need ten GPUs. Pods waiting for requests keep their GPU allocations, so larger pools require more GPU capacity. [Capacity and nodes](../production/01_capacity_and_nodes.md)

??? note "CUDA errors and subsequent evaluations"
    Some CUDA errors, such as illegal memory accesses, can cause subsequent GPU work in the same process to fail. Pods that share a GPU through NVIDIA time-slicing draw from the same GPU memory capacity, and a device fault can affect several pods. [CUDA error codes](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TYPES.html) [NVIDIA GPU time-slicing](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)

    This repository runs each submission in a fresh process. When it detects a CUDA error while running the reference implementation, the sandbox returns `sandbox_error` and stops accepting requests. The TRL training run skips the failed evaluation. [On-policy RL and error handling](03_onpolicy_rl_with_sandboxes.md)

See [on-policy RL](03_onpolicy_rl_with_sandboxes.md) for how the trainer uses scores. The [CPU exercise](../handson/10_cpu_only.md) demonstrates the scoring flow without GPU instances.

## Separate kernel time from grading time

For a `relu_bias_triton` submission, `ref_ms_median` describes **one execution of the reference kernel**. `eval_p50_s` describes **one scoring request** and includes preparing the code, checking correctness, timing it and returning a verdict. The units are milliseconds and seconds respectively.

For example, on the gVisor pool with two A10Gs the reference median was 0.5833 ms, median kernel speedup was 1.743×, and median evaluation time was 9.984 s. Faster kernel code still needs preparation and correctness checks. Use speedup to compare implementations. Use evaluation latency and pool throughput to understand how long training may wait for scores. [Benchmark table and original JSONL](../handson/08_benchmark.md#runtime-results)

<a id="further-detail"></a>

## Tasks and grading criteria

A code model (default `Qwen/Qwen2.5-Coder-1.5B-Instruct`, Apache-2.0) rewrites a PyTorch module as `ModelNew` using Triton kernels, the sandbox measures correctness and speed and returns the result, and the trainer computes the format, correctness and speedup scores. The task contract is similar to KernelBench. Each task module has these.

- a trusted reference `Model`
- `get_init_inputs()`
- `get_inputs(seed, device, size)` that builds inputs per seed
- tolerances `ATOL` and `RTOL`

### Ten tasks (`src/gpusandbox/tasks/`)

| Level | task_id | What it computes |
|---|---|---|
| 0 | `vector_add` | elementwise sum of two 1-D float32 tensors |
| 0 | `relu_bias` | add a per-column bias to a 2-D activation, then ReLU |
| 0 | `scaled_residual` | `x + alpha * y` (alpha is a constructor argument) |
| 1 | `silu_mul` | `silu(a) * b` (the SwiGLU gate) |
| 1 | `gelu_tanh` | GELU with `approximate='tanh'` |
| 1 | `row_sum_sq` | sum of squares per row (output shape `[rows]`) |
| 2 | `row_softmax` | softmax over the last dimension (numerically stable) |
| 2 | `rms_norm` | RMSNorm over the last dimension |
| 2 | `layer_norm` | LayerNorm over the last dimension with weight and bias |
| 3 | `matmul_bias_relu` | float16 `relu(x @ w + b)`, accumulating in float32 inside the kernel |

By default `train_grpo.py` uses `--max-level 2` (nine tasks) and builds 64 rows per task (`--repeats`). The prompt contains a system prompt, the rules, a Triton example for an op outside the task set (`y = 2 * x`) and the reference source. The task set is part of the sandbox version, so changing a task means shipping a new sandbox version.

### Three-part reward

| Component | Value | Weight (`--reward-weights`) |
|---|---|---|
| format | 1.0 when the answer parses as a module that defines `ModelNew`, else 0.0 | 0.1 |
| correctness | `policy_violation`, `compile_error`, `timeout` 0.0 / `runtime_error` 0.05 / `wrong_answer` 0.2 / correct without a Triton kernel 0.3 / correct with a custom kernel 1.0 | 1.0 |
| speedup | log2 scale: 0.5x 0.0, 1x 0.5, 2x 1.0, capped at 1.5 from 4x. Only for correct custom kernels | 0.5 |

The weighted sum peaks at 0.1 + 1.0 + 0.5 x 1.5 = 1.85. Infrastructure errors (`sandbox_error`) are not the policy's fault, so with TRL all three components return `None` and the sample is excluded (reasoning in [03 On-policy RL with sandboxes](03_onpolicy_rl_with_sandboxes.md)).

### The RL loop

![A clockwise loop. vLLM generates 8 completions per task prompt from the dataset, the trainer extracts code and checks the AST policy on CPU, then sends it to a sandbox pod with one GPU. Inside the pod an untrusted child runs the candidate and a trusted parent judges its outputs with the reference and timing and returns the verdict. Then come the three-part reward (format, correctness, speedup), the group-relative GRPO advantage and the LoRA update (one optimizer step), and a dashed weight sync arrow returns to generation.](../images/figures/concepts-01_why_gpu_sandbox--rl-loop.en.svg)

*Takeaway: The sandbox sits between generation and update, so slow or wrong scoring slows down or skews the whole training run.*

## Scope and limits

- The CPU checks in the diagram run in the trainer. The separate CPU pool is for practicing the scoring flow without GPUs.
- [Production 04 Reward integrity](../production/04_reward_integrity.md) covers the evaluator's safeguards and their limits.

??? note "References"
    | Topic | Link |
    |---|---|
    | AWS Nitro Sandboxes | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html |
    | EKS sandboxing limitations | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
    | KernelBench GitHub, v0.1 blog | https://github.com/ScalingIntelligence/KernelBench , https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/ |
    | Tasks, prompts, reward code | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/tasks/__init__.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/prompts.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py |
    | Harness timing, policy | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/timing.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/harness/policy.py |

    [Selected references on this topic](../reference/references.md#ref-concepts-01-why-gpu-sandbox)
