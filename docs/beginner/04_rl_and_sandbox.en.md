# 04 Reinforcement learning and sandboxes

**TL;DR** In reinforcement learning (RL), the sandbox is the exam room and the grader that actually runs the model's code and scores it, so if the grader is fooled or the grading standard changes midway, the model learns the wrong thing.

## Pain points

The model learns only from the score, not from a person's explanation, so a wrong score teaches the wrong thing. If the easiest way to raise the score is "fooling the grader" rather than "solving it properly," the model will find that way. Training runs for days, so at some point you will need to fix the sandbox, and if grading standards get mixed at the moment you switch, training becomes unstable.

![a: an answer that raises the score through a gap in grading, and v1 and v2 standards mixed in one group, both give a wrong score, so the model learns the wrong thing. b: the harness blocks cheating with separate processes and new inputs, and one version grades each batch (switching between batches), so the score is right under one standard and the model improves from it](../images/figures/beginner-04_rl_and_sandbox.svg)

*Takeaway: Whether from a fooled grader or mixed standards, a wrong score becomes wrong learning. With the harness blocking cheating and one version per batch, the model learns from the right score.*


## Why

- **When you see the training loop as a picture, you can see where the sandbox sits.**
- **We look at "cheating the grader" cases that were actually reported, and how to block them.**
- **We cover the moment you change the grading standard.** This explains why this repository changes the sandbox the way it does, without stopping training.

**Before you start:** It is enough if you have read [chapter 01](01_why_sandbox.md) through [chapter 03](03_gpu_sandbox.md). There are no equations.

??? note "Terms (expand if a word is new)"
    - **Reinforcement learning (RL):** A way of teaching where, instead of telling the correct answer directly, you give a score (reward) for the result of an action.
    - **reward:** The score given to an answer the model wrote. Here, it is decided by "whether the code is correct" and "how fast it is."
    - **GRPO:** A reinforcement learning method that has the model write several answers to the same problem, then teaches it to do more of what the answers that did relatively well within that group did.
    - **on-policy:** A way of learning only from answers written by the model's "current self." Once it writes answers, it learns from them right away and then writes the next answers.
    - **reward hacking:** Raising only the score by using gaps in the grading method, without properly solving the problem.
    - **harness:** The grading program that runs submitted code, compares it to the correct answer, and measures time.
    - **batch:** A bundle of answers collected and graded at once.

## Where the sandbox sits in the training loop

![A problem (rewrite a PyTorch op as a faster GPU kernel) goes into the model, which is trained on GPU. 1 The model reads the problem and writes code for the sandbox (exam room and grader, with a GPU to measure speed), 2 the sandbox runs it to check whether it is correct and how fast and gives a score (reward: correctness, speedup), 3 the model is adjusted to write more high-scoring answers. The mark in the middle shows that the loop repeats thousands of times](../images/figures/beginner-04_rl_and_sandbox--rl-loop.svg)

*Takeaway: The model writes code, the sandbox runs it and gives a score, and the model gets better from the score. This loop repeats thousands of times.*


The problem in this repository is "rewrite a PyTorch operation as a faster GPU kernel." The sandbox runs the submitted code, measures whether the result is the same as the original operation (correctness) and how much faster it got (speedup), and makes a score from these two. Speed has to be measured on a GPU, so the sandbox needs one.

## GRPO: learning by comparing answers with each other

GRPO has the model write several answers (for example, 8) to one problem and compares them within that group: an answer above the group average becomes "do more of this," and one below it "do less of this."

| Answers to the same problem | Score | Compared with the group average | What the model learns |
|---|---|---|---|
| Answer A: correct and 1.5 times faster | High | Above average | Writes more like A |
| Answer B: correct but slow | Medium | Near average | Stays about the same |
| Answer C: wrong | Low | Below average | Writes less like C |

This method rests on the assumption that **the answers in the same group were graded by the same standard**.

## Cheating the grader (reward hacking)

Here are cases actually reported on GPU kernel tasks.

| Case | What happened | How to block it (this repository) |
|---|---|---|
| Fooling the clock | Creates a separate execution stream (CUDA stream) to hide work that has not finished yet while time is being measured | Waits for the whole GPU to finish before measuring time, and forbids separate execution streams |
| Copying the answer | Instead of writing its own kernel, calls the original operation or an existing library as is | Checks whether a self-written GPU kernel (Triton) actually ran, and lowers the score if there is none |
| Saving results | Notices that the same input repeats and returns the previous result | Changes the input every time it measures, and checks a checksum of the result |
| Tampering with the grader | Swaps out the timing function inside the same process | Splits the grader and the submitted code into different processes, and checks dangerous code before running it (AST policy) |

They come from public benchmarks such as KernelBench and related research, and the detailed list and sources are in [04 Reward integrity](../production/04_reward_integrity.md), written for experienced readers.

!!! question "❓ Misconception: A sandbox only needs to keep things secure"
    A sandbox is a wall that protects the server and also has to be a fair grader. However strong the wall, if the grading is fooled, the model learns how to cheat. That is why this repository designed its grading program (harness) separately.

## When you change the grading standard during training

When you fix the sandbox (security patches, improvements to grading rules), the thing to be most careful about is **keeping the old standard (v1) and the new standard (v2) from mixing within one group**.

Suppose that of 8 answers to the same problem, 4 were graded with v1 and 4 with v2. The model mistakes the score difference between the two standards for "a difference that came from better code" and learns it. On-policy training reflects that result in the very next step, so what it learned wrong gets mixed right into the next answers (inference).

So this repository uses three rules.

1. **One batch is graded with one version.** The version to use is set when the batch starts, and it does not change until the batch ends.
2. **First check that the new version makes the same judgments as the old one.** Test answers whose results are known in advance (golden), such as correct, wrong, and cheating answers, are fed to both versions and the results are compared (parity check).
3. **Switching happens between batches.** If you change only the routing table, grading uses the new version from the next batch on.

In the output below, switching from v1 to v2 under these rules gives v1 up to batch 2 and v2 from batch 3, with only one version per batch (`served_versions`).

![Reward loop output: v1 up to batch 2, v2 from batch 3](../images/learning/local-reward-loop.png)

*A run with two sandbox servers on the author's laptop; the cluster prints output in the same form.*

## In one line

- In reinforcement learning, the sandbox is both the exam room and the grader, and the score is the model's textbook.
- The grader must not be fooled (preventing reward hacking), and the same group must be graded by the same standard (pinning the version).

## Next

In [05 Try it yourself](05_hands_on.md), you launch a sandbox yourself and grade with it, then put the three runtimes on AWS.

??? note "References"
    | Topic | Link |
    |---|---|
    | KernelBench | https://arxiv.org/abs/2502.10517 |
    | TRL GRPO Trainer | https://huggingface.co/docs/trl/main/en/grpo_trainer |
    | KernelBench | https://github.com/ScalingIntelligence/KernelBench |
    | This repository's grading program (harness) | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/src/gpusandbox/harness |

    All sources: [this page in All references](../reference/references.md#ref-beginner-04-rl-and-sandbox)
