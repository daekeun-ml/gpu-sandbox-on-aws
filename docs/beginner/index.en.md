# Before you begin

When a model writes code, you can run it, check the result, and turn the result into a score for training. Chapters 1–4 explain where sandboxes and GPUs fit. Chapter 5 grades submissions on your computer without an AWS account, and chapter 6 follows an agent that revises an answer after seeing its score.

| Chapter | What you will learn |
|---|---|
| [01 Code isolation](01_why_sandbox.md) | Which permissions generated code gets when it runs |
| [02 Containers and sandboxes](02_container_vs_sandbox.md) | Where runc, gVisor, and Kata handle system calls |
| [03 GPU access](03_gpu_sandbox.md) | When to grade on a GPU and how to connect it |
| [04 Reinforcement learning](04_rl_and_sandbox.md) | How execution results become rewards |
| [05 Try it yourself](05_hands_on.md) | How to read a local verdict and compare kernels on EKS |
| [06 Multi-turn agents](06_multi_turn_agent.md) | How one episode gets its own sandbox |

Start with the [local exercise](05_hands_on.md) if you prefer to run something first. For an AWS deployment, see the [hands-on overview](../handson/index.md).

## Choose what to run first

Take a function that adds `[1, 1]` to `[-3, 2]` and clamps negative values to zero. The expected answer is `[0, 3]`. **On your computer**, send a deliberately wrong answer and check that the grader returns `wrong_answer`. **On AWS**, start gVisor and Kata pods on the same CPU node and compare the Linux kernels they see. The local exercise requires no account or GPU. The optional AWS exercise incurs EKS and EC2 charges. [Local scoring and the optional AWS exercise](05_hands_on.md)

To see GPU grading before provisioning anything, choose **Replay scoring** in the public demo. It shows the gVisor and Kata verdicts for the same submission side by side. Chapter 4 explains how the trainer uses a verdict when it updates the model. [Scoring replay](https://dohbsn4kn34ya.cloudfront.net/?lang=en#try)

## Where to go after the first verdict

Pick a question raised by the local exercise.

| Question | Chapter |
|---|---|
| Can the ranking of two kernels change on another GPU? | [GPU workloads and grading criteria](../concepts/01_why_gpu_sandbox.md) |
| How can I tell whether two pods share a kernel? | [Runtime boundaries](../concepts/02_isolation_runtimes.md) |
| Does the model learn that an answer is wrong if its sandbox stops responding? | [GRPO and infrastructure errors](../concepts/03_onpolicy_rl_with_sandboxes.md) |
| Where does a score request go with training on HyperPod and grading on EC2? | [Platforms and instances](../concepts/04_platforms_and_instances.md) |
| What stays allocated when the episode ends? | [Agent Sandbox allocation and release](../concepts/06_agent_sandbox.md) |
