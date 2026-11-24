# 01 Why AI-generated code needs isolation

Suppose you ask a model to write a function that sorts numbers from smallest to largest. You need to run the code to check that `[3, 1, 2]` comes back as `[1, 2, 3]`. What happens if you call that function inside the program training the model?

## Where should the generated code run? { #separating-scoring-from-training }

If a bug in the loop keeps the function from finishing, the training program waits for it and cannot move on to the next submission. If the function opens a file, it can read files the training program has permission to read. Sorting numbers requires no such access.

In this lab, the training program sends the code to a **sandbox**. This is a separate environment that limits which files the code can access, where it can connect and how long it can run.

![The training program on the left sends code to the sandbox on the right and receives the result.](../images/figures/beginner-01_why_sandbox--execution-boundary.en.svg?v=2)

Follow the arrow to the right. The training program sends the code along with a **task ID** that identifies the problem it should solve. The sandbox runs the function on test inputs for that problem and compares its output with the expected answers. If `[3, 1, 2]` comes back as `[1, 3, 2]`, for example, the function finished but the result is `wrong_answer`. The training program uses the result to calculate a reward.

<span id="which-setting-protects-what"></span>

## Why set separate limits on time and file access? { #defense-in-depth }

Suppose the same function gets an empty list `[]` and never leaves its loop. Once the time limit expires, the sandbox stops the function and returns `timeout`. The training program can move on.

**Would a time limit also protect the training files?** If the function has permission to read a file, it can open it as soon as it starts. The training server keeps its **checkpoint**, a file that saves the model's state so training can resume later, outside the sandbox. The sorting function only needs the numbers in its test input.

<span id="sandbox-limits"></span>

![A time limit stops a function that keeps running. Model files stay on the training server, and new connections from the sandbox to external servers are blocked by default.](../images/figures/beginner-01_why_sandbox--layers.en.svg?v=2)

Follow the arrow towards the external server. Sorting numbers needs no internet connection. The sandbox can reply to the training program's request, and the default rules block any new connection the sorting function tries to open to a server on the internet.

??? note "How does the AWS lab enforce these limits?"
    Kubernetes runs the sandbox in a unit called a **pod**. The sandbox runs as an unprivileged user with a read-only root filesystem. Each submission gets its own working directory.

    gVisor or Kata handles requests the code makes to the operating system. Network rules restrict outbound connections. The sandbox receives neither AWS keys nor a Kubernetes service account token of its own. The lab also limits CPU and memory use. [Security settings in the AWS lab](../production/02_security.md)

<span id="reading-ready-and-ok"></span>

??? note "What do Ready and ok mean in the lab?"
    `Ready` means the sandbox can accept a request. `ok` means the submitted code passed the correctness checks. If you send a deliberately incorrect answer and get `wrong_answer`, the grader did its job on that submission. [Chapter 05 hands-on lab](05_hands_on.md)

The next chapter follows a request to open a file in a regular container, in gVisor and in Kata. [02 Containers and sandboxes](02_container_vs_sandbox.md)
