# 01 Why AI-generated code needs isolation

**TL;DR** Code that an AI model wrote has to run to be graded, so you lock it inside a "small computer you can throw away" (a sandbox) and need several layers of defense working together to really block it.

## Pain points

A model can write dangerous code even without bad intent. You only know whether code is correct and how fast it is by running it, so the moment you grade it, that code runs right next to your server's files, credentials, and network. One isolation runtime may seem enough, but experiments show that other settings do much of the blocking.

![a: without isolation, model-written code reaches the server files, the node credentials and the internet. b: in a sandbox, a different layer stops each risk (pod security settings and the isolation runtime, NetworkPolicy and IMDSv2 hop limit 1, egress blocking)](../images/figures/beginner-01_why_sandbox.svg)

*Takeaway: Run without isolation, scoring code reaches the server's files, credentials and the internet. In a sandbox each risk is stopped by a different layer, so the isolation runtime alone does not stop them all.*


## Why

- **Each risk is blocked by a different setting.** Pod security settings and the isolation runtime stop reads of server files, network rules and node settings stop credential theft, and network rules stop data from being sent out.
- **Defenses are stacked in layers.** For example, network rules and the EC2 metadata settings both guard the path to node credentials. Stacking more than one defense on a risk like this is called defense in depth. Some risks, such as sending data to the internet, are blocked by one layer only.

**Before you start:** None. The overall order is in [Before you begin](index.md).

??? note "Terms (expand if a word is new)"
    - **Sandbox:** An environment that runs untrusted code separately. Think of it as a disposable computer that you can just throw away if it breaks.
    - **pod:** The smallest unit for running containers in Kubernetes. In this guide, one sandbox is one pod.
    - **Node:** The server (EC2 instance) that a pod actually runs on.
    - **IMDS:** The address (`169.254.169.254`) where an EC2 instance gets information about itself and temporary credentials.
    - **Credentials:** Keys (tokens, keys) that prove "who I am" to AWS or Kubernetes.
    - **NetworkPolicy:** Firewall rules that decide who a pod can talk to.
    - **egress:** Traffic going from inside to outside. The opposite is ingress.

## What is dangerous

What a program run for grading can do falls into the six risks below, and each is blocked in a different place.

| Risk | Picture code like this | What blocks it |
|---|---|---|
| Reading server files | Opens `/etc/shadow` or another user's files | Not mounting the host file system into the pod, pod security settings (non-root user, dropped privileges), and the isolation runtime |
| Stealing credentials | Connects to `169.254.169.254` (IMDS) and takes the node's AWS permissions | NetworkPolicy, and the node settings of IMDSv2 required and hop limit 1 |
| Spreading elsewhere | Calls the Kubernetes API or connects to a neighboring sandbox | NetworkPolicy, and the setting that puts no token in the pod |
| Kernel attack | Triggers a kernel bug to escape from the container | Isolation runtime (gVisor, Kata) |
| Hogging resources | Keeps using CPU and memory with a computation that never ends | CPU and memory limits and an execution time limit |
| Exfiltrating data | Sends results or data to another server on the internet | Blocking outbound traffic (egress) |

A model in reinforcement learning tries every way to raise its score and really does open files or touch the code that measures time along the way, so these are blocked regardless of intent.

## Not one layer but many

![A table of the six layers and the risks each one blocks. The rows are 1 pod security settings (non-root user, dropped privileges), 2 isolation runtime (gVisor or Kata), 3 network rules (NetworkPolicy, outbound denied by default; new connections a pod opens to its own node are blocked by the node guard in 4), 4 node settings (IMDSv2 required, hop limit 1, node guard), 5 no credentials (no AWS keys and no service account token of its own in the sandbox pod; the server uses the token the caller sends to verify the caller), 6 resource and time limits (CPU, memory, execution time). A dot marks a risk the layer blocks: reading server files by 1 and 2, stealing credentials by 3 and 4, spreading elsewhere by 3 and 5, kernel attack by 2, hogging resources by 6, exfiltrating data by 3. Some risks are blocked by several layers](../images/figures/beginner-01_why_sandbox--layers.svg)

*Takeaway: Each of the six layers mainly handles a different risk. File access is limited by the pod's permissions and the isolation runtime, and outbound connections are blocked by the network rules. Several layers can work against the same risk.*


Part 1 of the AWS tech blog tried the same attacks on EKS against a regular container and against gVisor, and reports that of the four check items, three were blocked by the pod security settings, not by gVisor.

| Layer | What it does | In this repository |
|---|---|---|
| 1. pod security settings | Runs as a non-root user, drops privileges, uses a read-only file system, turns off automatic token mounting | Defaults of the sandbox pod (`uid 10001`, `capabilities: drop ALL`, `readOnlyRootFilesystem`) |
| 2. Isolation runtime | Intercepts system calls (gVisor) or runs in a separate VM altogether (Kata) | Chosen per pod with `RuntimeClass`. Details in [chapter 02](02_container_vs_sandbox.md) |
| 3. Network rules | Allows inbound connections only from whoever asked for grading, and blocks outbound connections by default. The EKS VPC CNI always allows traffic between a pod and its own node. The node guard in layer 4 drops new connections that a pod opens to its own node, and allows the node's health checks on the pod and their replies | Default deny in the `sandbox` namespace |
| 4. Node settings | Keeps pods from reaching the node's credentials (IMDS) and the node's own services | IMDSv2 required, hop limit 1, node guard |
| 5. No credentials | Mounts no AWS keys and no service account token of its own into the sandbox pod | `automountServiceAccountToken: false`, no secrets. The server uses the caller's token, sent with each grading request, to verify the caller |
| 6. Resource and time limits | Caps CPU, memory, and execution time | The pod's requests and limits, a time limit per evaluation |

!!! question "❓ Misconception: I created NetworkPolicy rules, so traffic is already blocked"
    On EKS, the rules only take effect after you turn on the network policy feature of the VPC CNI (`enableNetworkPolicy`). In the part 2 experiment of the blog, IMDS and the Kubernetes API were reachable until the feature was on. This repository creates its cluster with it turned on.

!!! question "❓ Misconception: With the default policy, outbound traffic is blocked too"
    The default policy of Agent Sandbox, which the blog series uses, blocks only the paths to private addresses and IMDS, and leaves traffic to the internet open, so data leaks need a separate block. This repository blocks all outbound traffic from the sandbox (`egress: []`), and before reporting ready, the sandbox checks for itself that the paths to IMDS, the Kubernetes API, and the node are blocked.

## What still remains

Even with many layers, the risk does not become zero. Part 1 of the blog states that it did not test attacks that break out of the container (container escape), so the choice of isolation runtime, the topic of the next chapter, matters.

## In one line

- Code that AI wrote can be dangerous regardless of intent, so lock it up before you run it.
- Locking it up is not the job of one isolation runtime; pod settings, the network, the node, credentials, and resource limits do it together.

## Next

In [02 Containers and sandboxes](02_container_vs_sandbox.md), we explain why a regular container is not enough, starting from the kernel.

??? note "References"
    | Topic | Link |
    |---|---|
    | AI agent sandbox, EKS isolation part 1 | https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/ |
    | Turning on network policy in EKS | https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html |
    | EC2 instance metadata (IMDSv2) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html |
    | This repository | https://github.com/daekeun-ml/gpu-sandbox-on-aws |

    All sources: [this page in All references](../reference/references.md#ref-beginner-01-why-sandbox)
