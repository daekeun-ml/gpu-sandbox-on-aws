# 04 Reinforcement learning and sandboxes

!!! info "TL;DR"
    In reinforcement learning (RL), the sandbox is the exam room and the grader that actually runs the model's code and scores it, so if the grader is fooled or answers to the same problem are graded by different standards, the model learns the wrong thing.

## Pain points

The model learns only from the score, not from a person's explanation, so a wrong score teaches the wrong thing. If the easiest way to raise the score is "fooling the grader" rather than "solving it properly," the model will find that way. Training runs for days, so at some point you will need to fix the sandbox, and if grading standards get mixed at the moment you switch, training becomes unstable.

![a: an answer that raises the score through a gap in grading, and v1 and v2 standards mixed in one group, both give a wrong score, so the model learns the wrong thing. b: the harness blocks known cheats with separate processes and new inputs, and one version grades each batch (a switch during grading never mixes versions within a batch), so the score is consistent under one standard and the model improves from it](../images/figures/beginner-04_rl_and_sandbox.svg)

*Takeaway: If a cheating answer gets a high score, or two grading standards are mixed in one group, the model learns that score gap as it is. The harness compares the submitted code's output with the reference operation on changing inputs and blocks known cheats. The trainer uses verdicts from one version for all answers in a batch, so differences between grading standards do not leak into the score.*


## Why

- **If slow code that fakes its timing gets a high score, the model writes such code more often.** So the harness is built to block cheating actually reported on GPU kernel tasks.
- **The sandbox can be replaced during training.** Even during a switch, the trainer makes the verdicts of one batch come from one version, so answers to the same problem can still be compared with each other.

**Before you start:** It is enough if you have read [chapter 01](01_why_sandbox.md) through [chapter 03](03_gpu_sandbox.md). There are no equations.

??? note "Terms (expand if a word is new)"
    - **Reinforcement learning (RL):** A way of teaching where, instead of telling the correct answer directly, you give a score (reward) for the result of an action.
    - **reward:** The score given to an answer the model wrote. Here, it combines the answer format, "whether the code is correct" and "how fast it is."
    - **GRPO:** A reinforcement learning method that has the model write several answers to the same problem, then teaches it to do more of what the answers that did relatively well within that group did.
    - **on-policy:** A way of learning only from answers written by the model's "current self." Once it writes answers, it learns from them right away and then writes the next answers.
    - **reward hacking:** Raising only the score by using gaps in the grading method, without properly solving the problem.
    - **harness:** The grading program that runs submitted code, compares it to the correct answer, and measures time.
    - **batch:** A bundle of answers collected and graded at once.

## Where the sandbox sits in the training loop

![A problem (rewrite a PyTorch op as a faster GPU kernel) goes into the model, which is trained on GPU. 1 The model reads the problem and writes code for the sandbox (exam room and grader, with a GPU to measure speed), 2 the sandbox runs it and measures correctness and speedup, and the trainer computes the score (reward) from them, 3 the model is adjusted to write more high-scoring answers. The mark in the middle shows that the loop repeats every training step (60 steps by default)](../images/figures/beginner-04_rl_and_sandbox--rl-loop.svg)

*Takeaway: The model writes code, the sandbox runs and grades it, and the trainer adjusts the model from the result. This repeats at every training step. The default training in this repository is 60 steps, and a run argument changes it.*


The problem in this repository is "rewrite a PyTorch operation as a faster GPU kernel." The sandbox runs the submitted code and measures whether the result is the same as the original operation (correctness) and how much faster it got (speedup). The trainer turns this result and the answer format into the score (reward) used for training. Speed has to be measured on a GPU, so the sandbox needs one.

## GRPO: learning by comparing answers with each other

GRPO has the model write several answers (for example, 8) to one problem and compares them within that group: an answer above the group average becomes "do more of this," and one below it "do less of this."

| Answers to the same problem | Score | Compared with the group average | What the model learns |
|---|---|---|---|
| Answer A: correct and 1.5 times faster | High | Above average | Writes more like A |
| Answer B: correct but slower than the reference | Medium | A little above average | Also writes more like B (less so than A) |
| Answer C: wrong | Low | Below average | Writes less like C |

B gets a lower speed score than A, but the wrong answer C pulls the average down, so B can still be above it. If all three answers follow the format and A and B use their own kernels, this repository's scoring (`src/gpusandbox/rewards.py`) gives A about 1.50, B at 0.9 times the reference speed about 1.31, and C (wrong) 0.3, for an average of about 1.04.

This method rests on the assumption that **the answers in the same group were graded by the same standard**.

## Cheating the grader (reward hacking)

Here are cases actually reported on GPU kernel tasks.

| Case | What happened | How to block it (this repository) |
|---|---|---|
| Fooling the clock | Creates a separate execution stream (CUDA stream) to hide work that has not finished yet while time is being measured | Runs the submitted code, waits until every GPU execution stream has finished, then records the elapsed time; the APIs that create separate execution streams are forbidden |
| Copying the answer | Instead of writing its own kernel, calls the original operation or an existing library as is | Checks whether the code uses a self-written GPU kernel (Triton) and, when launches can be counted, whether it actually ran. A correct answer without its own kernel gets only partial credit |
| Saving results | Notices that the same input repeats and returns the previous result | Changes the input every time it measures, and checks a checksum of the result |
| Tampering with the grader | Swaps out the timing function inside the same process | Checks the code before running it (AST policy) and blocks code that changes module attributes such as the timing function. The candidate's run time is measured in the same child process as the candidate, while the reference op, the result comparison and the final verdict stay in a separate parent process |

They come from public benchmarks such as KernelBench and related research, and the detailed list and sources are in [04 Reward integrity](../production/04_reward_integrity.md), written for experienced readers.

!!! question "❓ Misconception: A sandbox only needs to keep things secure"
    A sandbox is a wall that protects the server and also has to be a fair grader. However strong the wall, if the grading is fooled, the model learns how to cheat. That is why this repository designed its grading program (harness) separately.

## When you change the grading standard during training

When you fix the sandbox (security patches, improvements to grading rules), the thing to be most careful about is **keeping the old standard (v1) and the new standard (v2) from mixing within one group**.

Suppose that of 8 answers to the same problem, 4 were graded with v1 and 4 with v2. The model mistakes the score difference between the two standards for "a difference that came from better code" and learns it. On-policy training reflects that result in the very next step, so what it learned wrong gets mixed right into the next answers (inference).

So this repository uses three rules.

1. **One batch is graded with one version.** The trainer makes the final verdicts of a batch come from one pool (the group of sandboxes for one runtime and version). If the pool changes while the batch is graded, answers that came from another pool are graded again on the current pool. If it changes again during that, the third request sends the whole batch at once, and one request is answered by one pool.
2. **First check that the new version makes the same judgments as the old one.** Test answers whose results are known in advance (golden), such as correct, wrong, and cheating answers, are fed to both versions and the results are compared (parity check).
3. **A version switch takes effect per batch.** The trainer reads the routing table each time it calls a sandbox, so grading requests made after it reads the changed table go to the new version. A batch that is being graded during the switch still ends up with verdicts from one version, by rule 1. If every answer in a batch was already graded by one pool and sits in the trainer's cache, though, the trainer uses those verdicts without calling a sandbox, so such a batch can still be scored with the old version's results after the switch. On a cluster the changed table can take about a minute to reach the trainer pod.

In the output below, switching from v1 to v2 under these rules gives v1 up to batch 2 and v2 from batch 3, with only one version per batch (`served_versions`).

![Reward loop output: v1 up to batch 2, v2 from batch 3](../images/learning/local-reward-loop.png)

*A run with two sandbox servers on the author's laptop; the cluster prints output in the same form.*

## In one line

- In reinforcement learning, the sandbox runs and grades the code the model wrote, and the model learns from the score computed from that result.
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
