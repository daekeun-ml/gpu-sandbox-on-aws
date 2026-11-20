# 01 Why AI-generated code needs isolation

A model returns code as text. Once you run it to check the answer, it becomes a program that can act with the permissions of its execution environment. It might open a file, make a network connection, or get stuck in a loop.

## Separating scoring from training

If a trainer executes a submission in its own process, the submission can access files that the trainer can read, including configuration and checkpoints. A submission that hangs can also interrupt training. Separating the execution environment limits how far each failure can spread when the trainer grades many submissions.

A **sandbox** runs the submission with limited access to files, the network, and machine resources. The trainer sends the answer and receives the evaluation result.

| What the submission does | How the sandbox handles it |
|---|---|
| Produces an output | Compares it with the reference answer. |
| Runs indefinitely | Stops it at the time limit. |
| Tries to reach files or external services it does not need | Applies file permissions and network rules. |

![The trainer sends code and a task ID to a separate sandbox, which executes the submission and returns the verdict.](../images/figures/beginner-01_why_sandbox--execution-boundary.en.svg)

## Defense in depth

Each control has a different job. Low privileges limit file access, network rules limit connections, and time and memory limits contain runaway computation. The [security design](../production/02_security.md) describes the controls used together in this repository.

[Chapter 02](02_container_vs_sandbox.md) follows a file request through runc, gVisor, and Kata.
