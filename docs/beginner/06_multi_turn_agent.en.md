# 06 Multi-turn agents and Agent Sandbox

An agent can read a verdict, revise its answer, and submit again. For example, if a sorting function drops duplicate values, the agent can preserve duplicates in its next submission. Each submission is a **turn**, and the attempt to solve one problem is an **episode**.

## One sandbox for the episode

Assigning the episode to one sandbox keeps the runtime and grader version consistent across turns. On a GPU profile, those turns also use the same GPU. The grading server clears its working files and processes after each submission. The agent sends the full revised code on every turn and uses the prior verdict as feedback.

![A shared pool can route turns to different pods, while one claim assigns a sandbox to all turns in an episode](../images/figures/beginner-06_multi_turn_agent.en.svg)

## Prepare, assign, and clean up

1. Agent Sandbox starts a **warm pool** of ready sandboxes.
2. At the start of an episode, the runner creates a `SandboxClaim` and sends all submissions to the assigned address.
3. At the end, the runner deletes the claim and the sandbox is removed.

A warm pool reduces startup wait and uses CPU or GPU capacity while idle. See [Agent Sandbox concepts](../concepts/06_agent_sandbox.md) for how assignment relates to the isolation runtime.

In the [multi-turn hands-on exercise](../handson/11_multi_turn.md), the CPU runner submits prepared answers in sequence. Look for the same `claim` across turns and `released: true` at the end.
