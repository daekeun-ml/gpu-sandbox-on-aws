# Before you begin

A model can give you code as an answer. To find out whether it works, you need to run it somewhere. This guide follows **where the code runs and how the result influences the model’s next training step**. You can read the first four chapters without installing anything or opening an AWS account.

| Chapter | Question to explore |
|---|---|
| [01 Why AI-generated code needs isolation](01_why_sandbox.md) | What happens to training if a sorting function never returns? |
| [02 Containers and sandboxes](02_container_vs_sandbox.md) | Who handles a file request under an ordinary container, gVisor or Kata? |
| [03 GPU access in a sandbox](03_gpu_sandbox.md) | How do you compare two correct implementations on a GPU? |
| [04 Reinforcement learning and sandboxes](04_rl_and_sandbox.md) | How can two correct answers earn different training rewards? |
| [05 Try it yourself](05_hands_on.md) | Why would a test pass when you submit a deliberately wrong answer? |
| [06 How an agent revises an answer](06_multi_turn_agent.md) | What carries over when the agent tries again in the same sandbox? |

## Pick a starting point { #choose-what-to-run-first }

- **Run a local example.** Chapter 05 grades prepared answers on your CPU. All you need to start is Git and `uv`. No AWS account or GPU is required. [Grade answers on your computer](05_hands_on.md)
- **Watch a run first.** Choose **Replay scoring** to see the same code evaluated under gVisor and Kata side by side. [Open the demo](https://dohbsn4kn34ya.cloudfront.net/?lang=en#try)
- **Deploy on AWS.** The hands-on guide offers CPU, EC2 GPU and HyperPod configurations. Creating the EKS cluster and workers incurs charges. [Start the AWS lab](../handson/index.md)

<span id="where-to-go-after-the-first-verdict"></span>

??? note "Explore one topic in more depth"
    For isolation on a shared node, see [runtime boundaries](../concepts/02_isolation_runtimes.md). For GPU placement, see [platforms and instances](../concepts/04_platforms_and_instances.md). [On-policy RL with sandboxes](../concepts/03_onpolicy_rl_with_sandboxes.md) explains the scoring rules. [Agent Sandbox](../concepts/06_agent_sandbox.md) follows the allocation across multiple submissions.
