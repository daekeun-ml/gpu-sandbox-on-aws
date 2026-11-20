# On-policy RL with sandboxes

!!! info "TL;DR"
    GRPO compares completions of the same prompt to build advantages, so one group is scored by one sandbox version, infrastructure errors do not become wrong-answer scores, and versions switch at batch boundaries without stopping training.

## Pain point

- **If you fix the harness mid-training**: v1 and v2 scores mix inside one group, so the advantage learns the difference between versions instead of between behaviors.
- **If unscored samples get zero**: the policy is punished for infrastructure noise. A sample goes unscored when a pod was busy or dead.
- **If you stop the run to change the sandbox**: this wastes the GPU time and progress so far of a multi-day on-policy run.

![Two panels. a: in the group of one prompt, completion A scored by v1 gets 1.85, completion B with the same code scored by v2 gets 1.35, and the correct completion C gets zero from a pod failure, so the advantage against the group mean mixes in version gaps and infrastructure noise (red). b (TRL): A and B are both scored by v1 at 1.85, C becomes None from sandbox_error (dashed), and the advantage reflects only policy differences with C left out of the baseline.](../images/figures/concepts-03_onpolicy_rl_with_sandboxes.svg)

*Takeaway: When the same code scores differently by version and infrastructure failures enter as zeros, the advantage reflects versions and infrastructure, so one group is scored by one version and infrastructure errors are left out as None (TRL).*


## Why

- **Match the pinning unit to the trainer.** TRL scores each reward batch with one version; with veRL, the gateway pins a version per `group_key`.
- **Separate infrastructure errors from policy scores.** TRL excludes the sample with `None`; veRL gives only the format score and records a flag.
- **Switch without downtime using blue/green.** Start the new version next to the old one, check parity, then change only the routing table so the next batch uses it.

**Before you start:** read "Three-part reward" and "The RL loop" in [01 When the sandbox needs a GPU](01_why_gpu_sandbox.md) first. Unfamiliar terms are in the "Terms" box below and in the [Glossary](../reference/glossary.md).

??? note "Terms (expand if a word is new to you)"
    - **On-policy**: updating only with data the current policy just generated. A completion is discarded after one use.
    - **Group, completion**: a completion is one answer the model generated for a prompt; a group is the set of completions from the same prompt (eight here).
    - **Advantage**: how much a completion's reward exceeds the group average, divided by the standard deviation. A positive value reinforces that behavior.
    - **Optimizer step**: one update of the model weights with the computed gradients.
    - **Reward batch**: the set of completions TRL passes in one call to the reward functions.
    - **vLLM colocate**: the mode that runs the vLLM generation engine on the same GPU as the trainer.
    - **Routing table, snapshot**: the JSON (a ConfigMap) that says which sandbox pool (runtime, version) to use, and a copy of it fixed at one moment.
    - **Blue/green**: a deployment method that starts the new version (green) next to the current one (blue), verifies it, then moves traffic in one switch.
    - **Parity**: a check that the new version gives the same verdicts as the current one on the golden submissions.
    - **Draining**: a pod state in which it takes no new requests and waits to be replaced.
    - **veRL, `group_key`**: veRL is a Ray-based RL training framework; `group_key` is the key the gateway uses to recognize samples of the same group.

## One on-policy GRPO step

This asset keeps TRL's defaults and trains strictly on-policy. In `GRPOConfig`, `steps_per_generation` defaults to `gradient_accumulation_steps` and the generation batch size is `per_device_train_batch_size x num_processes x steps_per_generation`, so in the words of the TRL documentation "there is one generation batch processed per optimization step". `num_iterations` also defaults to 1, so each completion serves exactly one optimizer step and is then discarded.

| Setting (`train_grpo.py` default) | Value | Meaning |
|---|---|---|
| `--per-device-batch` | 4 | completions per micro-batch |
| `--grad-accum` | 4 | becomes the default of `steps_per_generation` |
| `--num-generations` | 8 | completions per prompt (group size) |
| Generation batch | 4 x 1 x 4 = 16 | with one process: 2 prompts x 8 completions |
| vLLM | `colocate`, `vllm_gpu_memory_utilization` 0.35, sleep mode | generation inside the trainer GPU |
| `beta`, `loss_type`, `scale_rewards` | TRL defaults (0.0, `dapo`, `group`) | no reference model, normalization per group |

After the optimizer step, TRL syncs the updated weights into vLLM for the next generation (as of TRL 1.18.0).

## Where the sandbox sits

The sandbox lives inside the reward function. `KernelRewards` hands three functions to TRL (`format_reward`, `correctness_reward`, `speedup_reward`), but caches results by a hash of (task, prompt, completion), so on one pool each completion is evaluated once and the three functions share the verdict.

```mermaid
sequenceDiagram
    autonumber
    participant T as GRPOTrainer
    participant V as vLLM (colocate)
    participant R as KernelRewards
    participant M as routing ConfigMap
    participant S as sandbox pods
    T->>V: generate 2 prompts x 8 completions (current weights)
    V-->>T: 16 completions
    T->>R: reward_funcs(prompts, completions, task_id)
    R->>R: code extraction, AST policy check (no_code and policy_violation end here)
    R->>M: snapshot() once per sandbox call (runtime, version, revision)
    loop each remaining completion, concurrently
        R->>S: POST /v1/evaluate (one at a time per pod)
        S-->>R: verdict or 503 busy (retry on another pod)
    end
    R-->>T: format, correctness, speedup (None for sandbox_error)
    T->>T: group-relative advantage, one LoRA optimizer step
    T->>V: weight sync
    Note over M: when the operator switches v1 to v2,<br/>it applies from the next sandbox call's snapshot<br/>(one batch is always scored by one version)
```

*Takeaway: the trainer takes one routing snapshot each time it sends requests to the sandbox, so a version switch usually applies from the next reward batch. If the switch lands while results cached from another pool are being scored again, the whole batch is scored again on the new pool, so one batch is always one version. A batch whose results are all cached from one pool calls no sandbox and is scored with that pool's results.*

The client allows one in-flight request per endpoint.

- **On a 503 (busy or draining) or a connection error**: it puts that pod on a 5-second cooldown and picks another free pod meanwhile. There are at most 4 attempts including the first, and a pod can be picked again once its cooldown ends.
- **4xx responses (authentication or request problems)**: they are not retried, since another pod would return the same.

For every batch that sends requests to the sandbox it prints one `reward_batch` JSON line (version, `served_versions`, `routing_revision`, counts per status, `pass_rate`, `mean_speedup`, p50/p95 evaluation time) and also appends it to `sandbox_metrics.jsonl`. `no_code` and `policy_violation` decided inside the trainer, and results served from the cache, are not counted, so the `pass_rate` denominator is the number of distinct scoring keys (task, prompt, completion text) this batch sent to the sandbox.

??? note "How the `pass_rate` denominator is counted"
    - A completion scored again because its cached result came from another pool is included.
    - A key sent more than once counts once, with its last result, and the same text under a different task or prompt counts separately.

??? info "Why HTTP to the pods instead of kubectl exec"
    The INTELLECT-3 report (arXiv 2512.16144) says kubectl exec through the API server grew to about 2.5 s per command, so they moved to a gateway, a headless Service and a sidecar. With a headless Service too (one that returns a DNS A record per Ready pod, without a virtual IP), the trainer here sends HTTP requests straight to pod IPs.

## Why one group must be scored by one version

The GRPO advantage normalizes the rewards of the G completions of one prompt by the group mean and standard deviation (`scale_rewards="group"`).

```text
A_i = (r_i - mean(r_1, ..., r_G)) / std(r_1, ..., r_G)
```

If the scoring rules differ inside a group, that difference becomes the advantage. This asset's v2 raises the seeds from 3 to 5 and caps the speedup at 10x (`k8s/sandbox/versions/v2.env`).

| The same completion (12x speedup from a measurement cheat) | v1 score | v2 score |
|---|---|---|
| format (weight 0.1) | 1.0 | 1.0 |
| correctness (weight 1.0) | 1.0 | 1.0 |
| speedup (weight 0.5) | 1.5 (log2 cap) | 0.5 (`implausible_speedup` sets the speedup to 1.0) |
| Weighted sum | 1.85 | 1.35 |

The same code can get a positive advantage under v1 and a negative one under v2. A borderline kernel can pass v1's three seeds and fail one of v2's five, becoming `wrong_answer` (0.2).

## How this asset pins versions

| Trainer | Pinning unit | Implementation |
|---|---|---|
| TRL (hands-on, direct) | reward batch | `SandboxClient.evaluate_batch` reads `RoutingTable.snapshot()` once per call and sends every request of that call to that snapshot's pool |
| TRL (production, gateway) | reward batch | the gateway's `POST /v1/evaluate_batch` uses one snapshot per request |
| veRL (gateway) | `group_key` = `{task_id}:{index}` | the gateway's `POST /v1/evaluate` pins the version that scored the group's first sample for `GATEWAY_GROUP_PIN_TTL_S` (default 900 s, 15 minutes) |

- **TRL (hands-on, direct)**: `KernelRewards` re-scores results cached from another pool so the batch matches one pool. `routing_revision` is recorded with the results.
- **veRL (gateway)**: the pin lives only in the gateway process memory and the TTL counts from the first request. The gateway does not read the epoch: after the TTL, or after a gateway restart, the next request picks the current version again, even for the same group.

The routing table is JSON from a ConfigMap, mounted as a directory because a subPath mount does not receive updates. The trainer re-reads it when it takes a snapshot, but reuses the previous contents if the last check was less than 2 seconds ago, and bumps `revision` on change. TRL scores the whole generation batch of a process at once (as of TRL 1.18.0), so with the hands-on's single process, one reward batch contains whole groups.

On the TRL path `KernelRewards` caches results under a key built from the task, prompt and completion, and stores with each result the pool (runtime, version) that produced it.

- **After a switch, when a batch holds both new completions and completions cached from the old pool**: the cached ones are scored again on the pool that scored the new ones.
- **When every result of the batch is already cached and all of them came from one pool**: the sandbox is not called and those results are used. In that case the batch is scored with the old pool's results even after the switch, and no `reward_batch` line is printed.
- **If the pool switches again during re-scoring**: the third attempt sends the whole batch in a single request.

One request is answered by one pool, so a batch is always scored by one version.

!!! note "Setups that split a group across processes"
    Each process takes its own snapshot, so right after a switch one group can span two versions. `routing_revision` is a per-process counter, so it cannot be compared across ranks. Compare `version` and `served_versions` from all ranks at the same `global_step`, or pin per `group_key` as the veRL path does.

## Do not turn infrastructure errors into wrong answers

| Verdict status | Responsible | TRL (`src/gpusandbox/rewards.py`) | veRL (`rl/verl/reward_fn.py`) |
|---|---|---|---|
| `ok`, `wrong_answer`, `compile_error`, `runtime_error`, `timeout`, `policy_violation`, `no_code` | policy | normal score | normal score (weighted sum) |
| `sandbox_error` | infrastructure | `None` from all three functions | there is no "skip" signal, so only the format score (0.1) is given and `sandbox_error: 1` is recorded |

- **How TRL handles `None`**: TRL excludes that reward function for the sample; when all return `None` the sample is unscorable, is left out of the group baseline and gets advantage 0.

A result becomes `sandbox_error` in these cases:

- no free pod within 600 seconds, or all 4 attempts failed
- a 4xx response, or a gateway error
- the harness's outer timeout, or a harness that ended without a result file
- a failure on the trusted reference path (with the `gpu_fault` flag for CUDA errors)

A candidate that dies with a segfault or a CUDA abort is the policy's responsibility: `runtime_error` (0.05). When `gpu_fault` occurs on the reference path, that pod stops taking work and the liveness probe (the check kubelet runs periodically to see whether the container is alive) restarts the container.

!!! warning "The veRL path is not fully neutral"
    With veRL a sample hit by an infrastructure error gets only the format score 0.1. That is below a correct sample but above `no_code` (0), so the group mean and the ranking of samples can differ from their real quality. If the `sandbox_error` ratio in `reward_extra_info` rises noticeably, fix the infrastructure cause before continuing training (on the TRL path, check `status` in `reward_batch`).

!!! question "❓ Misconception: giving infrastructure errors zero is the safe, conservative choice"
    Zero means "this answer is bad", so a correct sample zeroed by a pod failure gets suppressed, and when errors cluster (a failing node, for example) the noise becomes systematic. Leaving an unscored sample unscored distorts the signal less.

## Updating the sandbox during training

![A two-lane timeline. The top lane holds the steps of the operator's version switch script scripts/ops/rollout.sh: 1 deploy v2 (no traffic), 2 verify v2 (isolation evidence, golden verdicts), 3 parity (golden results of v1 and v2 match; on failure keep v1 and v2 gets no traffic), on pass 4 switch routing (v2 from the next reward batch), and 5 --finish (scale v1 to 0, kept for rollback). The bottom lane shows reward batches; the trainer takes a routing snapshot on each sandbox call, and one batch is scored by one version. A dashed line under step 4 (reaches pods within about a minute) marks the boundary between v1 batches on the left and v2 batches on the right; on a first switch a batch sent to v1 ends on v1, and sandbox_version_switch is logged where v2 takes over. An arrow at the bottom is time, with training not stopping.](../images/figures/concepts-03_onpolicy_rl_with_sandboxes--version-swap.svg)

*Takeaway: v2 receives traffic only after verification and parity, versions never mix within one reward batch during the switch, and v1 keeps scoring until then or if the deploy, verification or parity step fails.*


1. **Blue/green Deployments:** each (runtime, version) has its own Deployment and headless Service (`sandbox-<runtime>-<version>`). v2 starts next to v1 and receives no requests until the routing table points at it.
2. **Verification:** `scripts/ops/verify.sh` checks the isolation evidence per pod, that IMDS, the API server, the node's kubelet and the internet are blocked, the golden verdicts, and that access from another namespace is refused.
    - **If you installed the Production gateway**: first add the NetworkPolicy for verification Jobs from [Production 03](../production/03_gateway_and_pools.md), so the verification and parity Jobs can connect from `rl-trainer` straight to the sandbox.
3. **Parity:** for every golden submission the two versions must return the same verdict, and when both are `ok` the speedup ratio must be within tolerance (`--speedup-tolerance`, default 0.35); on failure the script stops.
4. **Switch:** the script updates the routing ConfigMap in the `rl-trainer` and `sandbox-gateway` namespaces one after the other, so if this step fails, check the active version in each namespace.
    - **When it takes effect**: after the routing ConfigMap changes, the kubelet sync reaches the mounted pods within about a minute. The trainer reads the new table when it scores the next reward batch, and with TRL's defaults one reward batch is one optimizer step, so the switch lands on a step boundary.
    - **Requests in flight during the switch**: requests already sent with the v1 snapshot finish on v1, and a batch that is being re-scored when the switch lands is scored again on the later version so it ends on one version.
5. **Cleanup and rollback:**
    - **`--finish`**: it scales v1 to zero but keeps its Deployment. On the gateway path (veRL), run it only after `GATEWAY_GROUP_PIN_TTL_S` (default 900 s) has passed since the switch, so requests pinned to v1 have finished.
    - **Rollback**: swap the arguments to go back to the v1 settings. The script redeploys v1 with the current `SANDBOX_IMAGE_URI`, so if the update also changes the image, pin each version's image URI in its version file ([Production 05](../production/05_sandbox_updates.md)).

In the default gVisor pool the two v1 pods already hold the GPUs of both `g5.xlarge` nodes. Run as is, the v2 pods stay Pending, step 1's `rollout status` fails after 30 minutes without progress (the Deployment `progressDeadlineSeconds` of 1800 seconds), and the switch never happens. Scale the `sandbox-gvisor` node group to 4 first; scenario A then needs 24 vCPU of G/VT quota (steps in [06 Updating the sandbox during training](../handson/06_sandbox_update.md)).

The first command covers steps 1 to 4, the second step 5, the third the rollback.

```bash
# Blue/green update of the gVisor pool while training runs
scripts/ops/rollout.sh gvisor v1 v2
# TRL: after sandbox_version_switch and reward_batch lines that serve only v2
#      with at least one status other than sandbox_error.
# veRL: after new groups report sandbox_version v2 and GATEWAY_GROUP_PIN_TTL_S has passed.
# Then retire v1 (kept for rollback)
scripts/ops/rollout.sh gvisor v1 v2 --finish
# Roll back at any point
scripts/ops/rollout.sh gvisor v2 v1
```

**What to look for:**

- **With TRL**: after the switch the trainer log shows the event below once, and afterwards `version` and `served_versions` in `reward_batch` change to `v2`.

    ```text
    {"event": "sandbox_version_switch", "from": "gvisor/v1", "to": "gvisor/v2", "routing_revision": ..., "global_step": ..., "ts": ...}
    ```

    The direct client records the requested version even on results whose connection failed, so also check that `status` holds a verdict other than `sandbox_error` before you run `--finish`.

- **With veRL**: there is no such event, so check `sandbox_version` of new groups and the per-version evaluation count on the gateway (`gateway_evaluations_total`).

The v2 example switches to draining after 200 evaluations.

- **With the production gateway**: replacing a draining pod is the job of the production gateway's recycler.
- **In the hands-on's direct mode**: a draining pod stays NotReady.

The hands-on procedure is in [06 Updating the sandbox during training](../handson/06_sandbox_update.md) and the operating design in [Production 05 Sandbox versioning](../production/05_sandbox_updates.md).

**If it fails:** if parity fails or a switch does not take effect, see the "version switch (routing)" section of [Troubleshooting](../reference/troubleshooting.md).

!!! question "❓ Misconception: changing the scoring rules during on-policy training means starting over"
    On-policy means the current policy generates the data; it does not stop the reward function from changing between steps. What you must keep is no version mixing inside a group and a logged switch point. The INTELLECT-3 report also runs environments "versioned independently of the trainer".

!!! question "❓ Misconception: passing parity means v1 and v2 give the same reward"
    Parity checks only that the golden submissions get the same verdicts and speedups within tolerance. v2 changes the seed count and the speedup cap on purpose, so some completions get a different reward. That is why the switch is aligned to a batch boundary and logged as `sandbox_version_switch`, to tell whether a change in the reward curve comes from the version switch.

## Scope and limits

- **Checked by local tests:** pytest checks the routing table reload and `revision` bump, the reward that turns `sandbox_error` into `None`, the golden probe and parity between two CPU pools, and the gateway's group pinning across a routing switch; the TRL path was checked for wiring only, with a one-process dry run.
- **Run on AWS:** in the practice account, a gVisor v1 pool was deployed and passed `scripts/ops/verify.sh gvisor v1`, and a `g5.2xlarge` trainer finished 5 GRPO steps ([run record](../reference/sources.md#aws-run-record)).
- **Not run on AWS:** a `scripts/ops/rollout.sh` version switch during training. Verify it with the checks in [06 Updating the sandbox during training](../handson/06_sandbox_update.md).

??? note "References"
    | Topic | Link |
    |---|---|
    | TRL GRPO trainer docs, GitHub | https://huggingface.co/docs/trl/main/en/grpo_trainer , https://github.com/huggingface/trl |
    | Ray on SageMaker HyperPod | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-ray.html |
    | Client, routing, pool | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/__init__.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/routing.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/client/pool.py |
    | Rewards, gateway, veRL reward | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/rewards.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/src/gpusandbox/gateway/app.py , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/rl/verl/reward_fn.py |
    | Blue/green script, version file | https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/scripts/ops/rollout.sh , https://github.com/daekeun-ml/gpu-sandbox-on-aws/blob/main/k8s/sandbox/versions/v2.env |

    All sources: [this page in All references](../reference/references.md#ref-concepts-03-onpolicy-rl-with-sandboxes)
