# Before you begin (beginner guide)

**TL;DR** Six chapters for people new to "how to safely run and grade code that AI wrote": chapters 1 to 4 build the concepts (about an hour in total), in chapter 5 you launch it yourself (free on your own PC, or a few dollars on AWS if you want), and chapter 6 explains sandboxes for multi-turn agents.

## Pain points

When one sentence has three or four words you have never seen (sandbox, gVisor, Kata, nvproxy, RuntimeClass, GRPO, reward hacking), it is easy to miss what matters. If you type the commands without knowing what the setup is meant to prevent, you cannot adapt when the situation changes even a little. Turning on a GPU in the cloud costs money and a setting left open by mistake becomes a security problem, so the newer you are, the more you hesitate to start.

![a: many new words arrive at once (gVisor, Kata, nvproxy, RuntimeClass, GRPO), and typing commands without knowing why leaves you stuck when things change even a little. b: chapters 1 to 4 explain each term in one line with pictures, and chapter 5 runs it on your PC (free) and AWS (optional), so you see what each command blocks](../images/figures/beginner-index.svg)

*Takeaway: Skipping the words and the reasons and copying commands first gets you through the screens but leaves nothing behind. With the reasons from chapters 1 to 4 first, you see what each command in chapter 5 protects against.*


## Why

- **Pictures and examples come first.** Each chapter answers one question, and each term is explained in one line the first time it appears.
- **"Why" comes first, "how" comes later.** After chapters 1 to 4, you see what each command in chapter 5 protects against.
- **We start with the path that costs nothing.** Chapter 5 runs on your PC first; the AWS stage is optional and shows screenshots from a real deployment.

**Before you start:** None. If you can paste commands into a terminal, that is enough; the guide explains as much Kubernetes and reinforcement learning as you need.

## Questions this guide answers

| Chapter | Question | One-line answer |
|---|---|---|
| [01](01_why_sandbox.md) | Why should code that AI wrote be locked up and run separately? | A model can write dangerous code regardless of intent, and if that code reaches your server's files, credentials, or network, it becomes an incident |
| [02](02_container_vs_sandbox.md) | Is a container not enough? | A regular container shares the host's kernel, so a single kernel vulnerability can bring the wall down. A sandbox puts up one more wall in between |
| [03](03_gpu_sandbox.md) | What is harder about code that uses a GPU? | The GPU driver lives inside the kernel, so the way you hand over the GPU decides the isolation level and which instances you can use |
| [04](04_rl_and_sandbox.md) | What does a sandbox do in reinforcement learning? | It is the grader that runs the code a model wrote and gives it a score. If the grader is fooled or the standard changes, the model learns the wrong thing |
| [05](05_hands_on.md) | Where do I start if I want to try it myself? | Launch a sandbox server on your PC and grade with it, and if you want, create a cluster on AWS with isolation runtimes installed, then delete it |
| [06](06_multi_turn_agent.md) | How should a multi-turn agent use sandboxes? | Every turn of one episode has to be graded in the same sandbox, so Agent Sandbox assigns one sandbox to each episode and deletes it when the episode ends |

```mermaid
flowchart LR
    A["01 Why isolate"] --> B["02 Containers and sandboxes"]
    B --> C["03 Isolating the GPU too"]
    C --> D["04 RL and grading"]
    D --> E["05 Try it yourself<br/>Your PC (free) → AWS (optional)"]
    E --> G["06 Multi-turn agents<br/>Agent Sandbox"]
    G -.-> F["Experienced path<br/>Choose a learning path"]
```

*Takeaway: Read the concepts in chapters 1 to 4, check them yourself in chapter 5, read about sandboxes for multi-turn agents in chapter 6, and then move on to the experienced path.*

## How to read

- **Terms box:** Expand the "Terms" box near the top of each chapter for that chapter's words, one line each. More words are in the [Glossary](../reference/glossary.md).
- **❓ Misconception box:** Corrects points that new learners often mix up.
- **In one line:** At the end of each chapter, one or two sentences to remember.
- **Analogies are a starting point.** We note separately where the analogy and reality differ.

## After you finish

After chapter 6, pick a course that runs real training on GPUs or one that reads through operations design in [Choose a learning path](../learning_paths.md).
