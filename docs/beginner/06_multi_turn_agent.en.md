# 06 Multi-turn agents and Agent Sandbox

**TL;DR** Reward grading in this asset is single-turn: each completion gets one final verdict, with no step where the model reads the verdict and revises its answer, and each request is graded by one free pod of the reward pool. A multi-turn agent needs every turn of an episode graded in the same sandbox, so Agent Sandbox assigns one sandbox to each episode.

## Pain points

The reward pool picks one free pod for each request and reuses that pod for later grading. When a request ends, the server deletes that request's work directory and cleans up leftover processes. A multi-turn agent submits code, reads the verdict, revises the code and submits again, so every turn of one episode has to be graded in the same sandbox with the same sandbox version. For a GPU task, the speed before and after a fix also has to be compared on the same GPU. Creating a new sandbox for each episode means waiting for it to start every time, and a Kata GPU VM can take several minutes to become Ready for the first time.

![Two panels. a single-turn grading: the GRPO trainer submits one completion to the reward pool, the pool picks a free pod anew for each request, and one verdict comes back; after each request the server clears that request's work directory and leftover processes. b multi-turn episode: a sandbox started ahead in the SandboxWarmPool is assigned to the episode by a SandboxClaim. The agent (model) submits turn 1, reads the verdict as feedback, submits a revised turn 2 and gets another verdict. Every turn is graded in that one claimed sandbox with the same sandbox version (and on the same GPU with a GPU profile), and the sandbox is deleted when the episode ends.](../images/figures/beginner-06_multi_turn_agent.svg)

*Takeaway: In single-turn grading each completion gets one verdict, and a free pod grades the answers that need a new run. In a multi-turn episode one sandbox claimed from a warm pool grades every turn with the same version, and on the same GPU with a GPU profile.*


## Why

- **In the default grading pool, the next submission can go to a different pod.** When one sandbox is assigned to an episode, the fixed code is graded in the same environment.
- **Isolation comes from the RuntimeClass.** Agent Sandbox starts sandboxes ahead of time, assigns them and reclaims them.

**Before you start:** It is enough if you have read [chapter 04](04_rl_and_sandbox.md). You do not need to do the hands-on in [chapter 05](05_hands_on.md).

??? note "Terms (expand if a word is new)"
    - **Single-turn grading:** grading that uses one verdict per completion. The trainer sends only the answers that need a new run to the sandbox. GRPO training in this asset works this way.
    - **Multi-turn:** a way of working where the model calls a tool or submits code, reads the result and responds again, several times over.
    - **Turn:** one step of a multi-turn episode in which the model responds once. In this asset's task, it is one submission of code and the verdict that comes back.
    - **Episode:** one attempt in which the model works on one task over several turns.
    - **Verdict:** the result the harness returns after grading one submitted piece of code. It holds the status (correct, wrong answer, policy violation and so on) and the speedup.
    - **CRD (Custom Resource Definition):** a definition that adds a new resource type to Kubernetes.
    - **Warm pool:** a set of sandboxes started before any request arrives.
    - **Claim:** a request to be assigned one sandbox from a warm pool.

    More terms are in the [Glossary](../reference/glossary.md).

## Single-turn grading: this asset's reward pool

GRPO training uses one verdict per completion. Answers that need a new run go to one pod of the pool; answers with no code, or that fail the policy check up front, are judged by the trainer without being sent to the sandbox. This asset's reward pool is a set of sandbox pods run by one Deployment per runtime and version.

- **One free pod grades each request.** A pod handles one evaluation at a time, and a busy pod returns 503. The client then sends the request to another pod.
- **Each request uses its own work area.** For each request the server creates a work directory and a new process tree, and when the evaluation ends it deletes that work directory and cleans up leftover processes. The pod and its `/work` and `/tmp` volumes stay in use for later grading. A pod assigned to an episode goes through the same cleanup on every submission.
- **GPU idle time goes down.** A free pod is picked for every request, so fewer GPUs sit waiting for work.

## Multi-turn agents: grading per episode

A multi-turn agent repeats these steps within one episode.

1. It writes code and submits it (turn 1).
2. It reads the verdict as feedback. For example, the status, the end of the error message and the speedup are returned to the model.
3. It revises the code and submits it again (turn 2). Steps 2 and 3 repeat until the task is done.

A real agent reads the verdict and revises its code. The [chapter 11](../handson/11_multi_turn.md) exercise instead submits prepared test answers in a fixed order, in place of a model, to check that each one gets a verdict from the same sandbox. This asset's example sends every submission of one episode to the same sandbox. With a GPU profile, every turn is graded on the same GPU with the same sandbox version. The CPU exercise assigns sandboxes the same way. If the GPU or the grading version changes between turns, the verdicts of turn 1 and turn 2 cannot be compared on the same basis (inference). The reward pool picks a free pod anew for each request, so turns of the same episode can be graded on different pods and GPUs.

Creating a new sandbox for each episode instead means waiting for the sandbox to be ready every time an episode starts. A Kata GPU VM fixes all of its guest memory in place and initialises CUDA inside the guest, so it can take several minutes to become Ready for the first time (deployment template comment).

## Agent Sandbox

Agent Sandbox (kubernetes-sigs/agent-sandbox) is an open-source project developed under Kubernetes SIG Apps. It starts sandbox pods ahead of time, assigns one when a request arrives, and reclaims it when it is no longer used. It manages this work with resources defined as Kubernetes CRDs.

| Resource | What it does |
|---|---|
| `SandboxTemplate` | The settings used to create a sandbox pod. The image, the RuntimeClass and the NetworkPolicy are written here |
| `SandboxWarmPool` | Sets how many sandboxes made from a template are started ahead of time |
| `SandboxClaim` | A request to be assigned one sandbox from a warm pool. One is created for each episode |

One assigned sandbox is a `Sandbox` resource, which manages one pod. The warm pool creates `Sandbox` resources, so you do not create them yourself. All four resources use the API version `v1beta1`, and the latest release is v1.0.11.

### Lifecycle: claim, assignment, release

1. **Start ahead:** the SandboxWarmPool starts the set number (`replicas`) of sandboxes from the template. This asset's sandboxes become Ready only after the device check (GPU initialisation on a GPU profile) and the egress block check are done.
2. **Claim:** when an episode starts, one SandboxClaim is created.
3. **Assignment:** the controller assigns one waiting sandbox to the claim. The warm pool starts a new sandbox to keep `replicas`.
4. **Turns:** every evaluation request of the episode goes to the address recorded in the claim (`status.sandbox.serviceFQDN`).
5. **Release:** when the episode ends, the claim is deleted. The assigned sandbox and its pod are deleted with it and are not used again. With Kata, the VM and the GPU are returned as well.

The trainer may exit abnormally before it deletes the claim. This asset's `EpisodeSandbox` sets an expiry time (`shutdownTime`) on the claim, so once that time passes, the controller deletes the claim and the sandbox, and the GPU the sandbox held is released.

!!! question "❓ Misconception: Agent Sandbox isolates the sandbox"
    Isolation is done by the pod's RuntimeClass (gVisor or Kata). Agent Sandbox only prepares, assigns and reclaims sandboxes. So gVisor and Kata both use the same template. To change the runtime, pick its profile (`k8s/sandbox/profiles/`) and apply the RuntimeClass, the node selector and the GPU resource name (`nvidia.com/gpu` for gVisor, `nvidia.com/pgpu` for Kata) together.

## Choosing between the two

| Work | What to use | Why |
|---|---|---|
| Single-turn reward grading (GRPO uses one verdict per completion) | This asset's reward pool | A free pod is picked for every request, so GPU idle time goes down |
| Multi-turn agents (read the verdict, revise the code, submit again) | A per-episode sandbox (Agent Sandbox) | Every turn of an episode runs in the same sandbox with the same sandbox version, and on the same GPU with a GPU profile |

!!! warning "A waiting GPU sandbox holds its GPU too"
    A sandbox in the warm pool holds one GPU even while it handles no evaluation, so it costs money during that time. For example, the gVisor profile runs one sandbox per `g5.xlarge`, so one waiting sandbox holds a node that costs 1.006 USD per hour (On-Demand price in us-east-1 and us-west-2). Set `replicas` to the number of episodes you run at the same time, and scale the warm pool to 0 while training is stopped.

    ```bash
    # Hold no idle GPU: scale the warm pool to zero (claimed sandboxes are not touched).
    # Patch only replicas; "pool <runtime> 0" would also re-apply the template with VERSION_FILE (default v1).
    kubectl -n sandbox patch sandboxwarmpool kernel-eval-gvisor --type merge -p '{"spec":{"replicas":0}}'
    ```

## Comparison with the AI on EKS Agent Sandbox solution

The awslabs [AI on EKS](https://github.com/awslabs/ai-on-eks) project has an [Agent Sandbox on EKS](https://awslabs.github.io/ai-on-eks/docs/infra/agents/agent-sandbox) solution. Both that solution and this asset use kubernetes-sigs/agent-sandbox, but they cover different workloads.

| Item | AI on EKS Agent Sandbox solution | This asset |
|---|---|---|
| Target | AI agents that run model-generated code. The page does not mention GPUs | GPU kernel grading (reward) |
| Isolation runtime | Three tiers: `standard` (runc), `gvisor` (Standard EKS only), `isolated-sandbox` (Nitro Sandboxes) | gVisor + nvproxy (`g5.xlarge`, A10G) or Kata + VFIO (`g4dn.metal`, T4) |
| Use of Agent Sandbox | Manages the lifecycle with Sandbox, SandboxTemplate, SandboxWarmPool and SandboxClaim (`v1beta1`), and uses KRO to put several resources behind one `AgentSandbox` resource | An optional extension that claims one sandbox for each multi-turn episode. GPU tasks use a GPU profile, and the CPU exercise in chapter 11 runs without a GPU. Default grading uses the Deployment-based reward pool |
| Egress | Allows outbound traffic only to allowed domains (FQDN). Standard EKS uses Cilium and EKS Auto Mode uses `ApplicationNetworkPolicy` | Blocks all egress (`egress: []`). Only pods with the client label (`gpusandbox/client=true`) in the `rl-trainer` namespace can call the sandbox API, on TCP 8000 |
| Nodes | Karpenter and a dedicated gVisor NodePool (`runsc` installed through AL2023 user data) | EKS managed node groups and Karpenter NodePools from the CDK stack |

- **The `isolated-sandbox` tier:** each pod runs in its own Firecracker microVM on an EC2 Nitro Sandbox. It needs EKS Auto Mode (Kubernetes 1.36 or later) or Standard EKS with a custom AMI. According to this guide's [sources page](../reference/sources.md), Nitro Sandboxes do not support GPU passthrough at launch.
- **Kata + Firecracker:** the page lists it as a future tier, and it is not included in the solution.
- **How to choose:** for agent sandboxes that need no GPU and may connect only to allowed domains, refer to the AI on EKS solution. For grading kernels on a GPU inside the sandbox, refer to this asset.

## This asset's Agent Sandbox extension

This asset offers Agent Sandbox as an optional extension. The sandbox server, the image and the authentication method are the same as in the reward pool, and one pod is assigned to each episode. The list of accounts allowed to call it (the episode Job account is added and the gateway account is left out) and the restart setting after a failure (the extension template has no `livenessProbe`) differ from the default pool. The extension files are in `k8s/extensions/agent-sandbox/`, `scripts/extensions/agent_sandbox.sh` and `src/gpusandbox/agent_sandbox.py` (`EpisodeSandbox`).

## Scope and limits

- **Verification status:** this asset's Agent Sandbox extension passed local tests only. It was not run on a cluster or on AWS.
- The install, template settings, warm pool and claim commands and how to use `EpisodeSandbox` are in [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md).
- The AI on EKS solution is summarised from its public page as read in 2026-11; it was not run in this asset.

## In one line

- In single-turn grading, each completion gets one verdict. A free pod grades the answers that need a new run, and when the request ends the server deletes that request's work directory and cleans up leftover processes.
- A multi-turn agent claims one sandbox per episode, grades every turn with the same version (on the same GPU with a GPU profile), and deletes the claim when the episode ends. Isolation is done by the RuntimeClass.

## Next steps

- To run multi-turn episodes yourself, with one claimed sandbox per episode, go to [11 Multi-turn episodes](../handson/11_multi_turn.md).
- The install commands and code of the Agent Sandbox extension are in [06 Extending with Agent Sandbox](../concepts/06_agent_sandbox.md).
- Pick other courses in [Choose a learning path](../learning_paths.md).

??? note "References"
    | Topic | Link |
    |---|---|
    | Agent Sandbox (kubernetes-sigs/agent-sandbox) | https://github.com/kubernetes-sigs/agent-sandbox |
    | Agent Sandbox on EKS | https://awslabs.github.io/ai-on-eks/docs/infra/agents/agent-sandbox |
    | EKS sandboxing limitations | https://docs.aws.amazon.com/eks/latest/userguide/sandboxing-limitations.html |
    | Amazon EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
    | This repository's Agent Sandbox extension | https://github.com/daekeun-ml/gpu-sandbox-on-aws/tree/main/k8s/extensions/agent-sandbox |

    All sources: [this page in All references](../reference/references.md#ref-beginner-06-multi-turn-agent)
