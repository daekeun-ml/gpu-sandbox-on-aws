# Before you begin

This guide follows AI-generated code from execution to grading and training. Each chapter uses an example suited to its topic, from opening a file to comparing GPU runtimes. The local exercise requires neither an AWS account nor a GPU.

| Chapter | What you will learn |
|---|---|
| [01 Code isolation](01_why_sandbox.md) | Which permissions generated code gets when it runs |
| [02 Containers and sandboxes](02_container_vs_sandbox.md) | Where runc, gVisor, and Kata handle system calls |
| [03 GPU access](03_gpu_sandbox.md) | When to grade on a GPU and how to connect it |
| [04 Reinforcement learning](04_rl_and_sandbox.md) | How execution results become rewards |
| [05 Local exercise](05_hands_on.md) | How to check verdicts on your computer |
| [06 Multi-turn agents](06_multi_turn_agent.md) | How one episode gets its own sandbox |

Start with the [local exercise](05_hands_on.md) if you prefer to run something first. For an AWS deployment, see the [hands-on overview](../handson/00_overview.md).
