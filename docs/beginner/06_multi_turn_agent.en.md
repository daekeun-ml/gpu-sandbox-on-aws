# 06 How an agent revises an answer { #06-multi-turn-agents-and-agent-sandbox }

In chapter 05 you checked that an incorrect submission received `wrong_answer`. Now imagine an **agent** that can read the feedback and submit a revision. If it skipped the step that replaces negative numbers with zero, for example, it can add that step and try again. One submission and its result are a **turn**. All the turns spent attempting one problem make up an **episode**.

## Why keep one sandbox while revising an answer? { #one-sandbox-for-the-episode }

Sending the first answer and the revision to the same sandbox keeps the runtime and grading rules the same. For GPU tasks, both runs also measure time on the same GPU. Independent answers that only need one evaluation each can go to whichever sandbox is free.

![Independent answers can go to any free sandbox. Revisions within one episode go to the same sandbox.](../images/figures/beginner-06_multi_turn_agent.en.svg?v=2)

<span id="what-carries-over-to-the-next-turn"></span>

**Does the same sandbox keep files written by the previous submission?** In this lab the grading server cleans up the working directory and remaining processes after each submission. The agent keeps the previous answer and its feedback, then sends the **entire revised program** on the next turn.

## Read the three attempts in a lab run { #reading-one-episode-in-the-logs }

The CPU exercise sends prepared answers in a fixed order so you can reproduce the sequence (`scripted`). Follow the three `episode 1` turn lines from top to bottom.

![In the Kata CPU lab the first submission is rejected, the second gives a wrong answer and the third succeeds](../images/terminal/agent-sandbox-episodes.png)

| Turn | Verdict on screen | What happened? |
|---|---|---|
| First | `policy_violation` | The submission used a prohibited operation and was rejected before execution. |
| Second | `wrong_answer` | It ran, but its output differed from the expected result. |
| Third | `ok` | The answer passed, and the episode ended as `solved`. |

At the bottom, `solved 2/2` means both episodes reached a correct answer. `mean turns 3.0` means it took three submissions per episode on average. [Run the episode exercise](../handson/extensions/multi_turn.md)

<span id="choose-a-pool-or-an-episode-claim"></span>

## What happens to the sandbox when the episode ends? { #prepare-assign-and-clean-up }

In this lab **Agent Sandbox** assigns a sandbox to an episode. A **warm pool** is a group of sandboxes already running and ready for the next allocation.

1. At the start, the episode runner creates a `SandboxClaim` to request a ready sandbox.
2. The runner sends the initial answer and every revision to the assigned address.
3. After a correct answer or the final allowed attempt, the runner deletes the claim. The sandbox used by the episode is deleted too.

<span id="why-a-warm-sandbox-may-remain-after-release"></span>

??? note "Why is there a ready sandbox after release?"
    If the warm pool is set to one, Agent Sandbox replenishes it for the next episode. The new sandbox starts with a clean environment. An idle GPU sandbox still holds a GPU. Scaling the warm pool to zero frees the device for other work. EC2 node charges continue until the node is terminated. [Release and cleanup](../handson/extensions/multi_turn.md)

??? note "How do I verify the allocation in the logs?"
    Compare `claim`, `pod` and `address` across turns in one episode. `released: true` in the end event means the runner released the claim. A `true` value for `one_sandbox_per_episode` in the summary means every turn of each episode used the same sandbox. [Agent Sandbox configuration and code](../concepts/06_agent_sandbox.md)

Pick a configuration in the [AWS hands-on guide](../handson/index.md) or choose a topic from the [learning paths](../learning_paths.md).
