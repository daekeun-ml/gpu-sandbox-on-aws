# 08 Runtime benchmark

**TL;DR** Measure cold start, evaluation latency, throughput and speedup of every deployed v1 pool with the same golden kernel, and compare only pools with the same GPU type.

## Pain point

gVisor runs on A10G (`g5.xlarge`) and Kata QEMU on T4 (`g4dn.metal`), so side-by-side numbers mix the runtime difference with the GPU difference. Boot times from blogs and CI use different measurement windows, machines and versions, so they do not carry over to your environment either.

![Two panels. a: the benchmark harness sends relu_bias_triton to the gVisor pool (g5.xlarge, A10G) and the Kata QEMU pool (g4dn.metal, T4), and the difference between the two pools mixes the runtime share and the GPU share, which cannot be separated. b: the same harness sends relu_bias_torch_only to the Kata CLH CPU pool and the Kata QEMU CPU pool on the same c8i.2xlarge node, so with the other conditions fixed the difference is the hypervisor only.](../images/figures/handson-08_benchmark.svg)

*Takeaway: The difference between two pools on different GPUs mixes the runtime's share with the GPU's share, so compare runtimes with a pair that fixes everything else, such as Kata CLH CPU and Kata QEMU CPU on the same c8i node.*


## Why

- **Same golden kernel, same harness, same API.** GPU pools get `relu_bias_triton`, CPU pools get `relu_bias_torch_only`.
- **Results land in JSONL.** `bench-<timestamp>.jsonl` at the repository root is easy to turn into a table.
- **Clean comparison axes are kept separate.** Comparisons within one GPU type, and Kata CLH CPU against Kata QEMU CPU on the same `c8i` node.

**Before you start:** the pools you want to compare must be deployed with [04 Deploy and verify sandbox pools](04_sandbox_pools.md) (the Kata pools come from [03 Kata sandboxes](03_kata.md)). How the three runtimes differ in structure is in [Isolation runtimes](../concepts/02_isolation_runtimes.md), and terms are in the [Glossary](../reference/glossary.md).

??? note "Terms (expand if a word is new to you)"
    - **Cold start**: on this page, the time from when a pod is created to when it becomes Ready.
    - **p50, p95**: when the measurements are sorted from smallest to largest, the values at the 50% and 95% positions. p50 shows typical latency, p95 shows the slow tail.
    - **Throughput**: completed evaluations per second.
    - **Golden submission**: a test answer with a fixed expected verdict. They live in `src/gpusandbox/golden.py`.
    - **Speedup, reference**: how many times faster the candidate kernel is than the trusted PyTorch reference implementation, and that baseline implementation itself.
    - **Hypervisor (QEMU, Cloud Hypervisor)**: the program Kata uses to start a VM per pod. This repository uses QEMU (`kata-qemu`) and Cloud Hypervisor (`kata-clh`).
    - **gVisor Sentry**: the user-space kernel in gVisor that handles the container's system calls.
    - **Nested virtualization, bare metal**: the ability to start a VM inside a VM, and an instance (`.metal`) that gives you the whole physical server without a hypervisor.
    - **`overhead.podFixed`**: a RuntimeClass value: the CPU and memory the scheduler reserves on top of each pod for the runtime.
    - **Pool claim**: taking one sandbox from a pool of sandboxes started in advance (a warm pool).
    - **JSONL**: a file format with one JSON object per line.

!!! warning "The numbers on this page are not measurements from this repository"
    The author did not run this benchmark on AWS, and the results table below is a blank template for you to fill in. The reference numbers are public sources from other machines, other versions and other measurement windows, so do not use them as predictions for this environment.

## Before you begin

List the pods in the `sandbox` namespace with their runtime and version labels.

```bash
kubectl -n sandbox get pods -L gpusandbox/runtime,gpusandbox/version
```

**What to look for:** every runtime you want to measure has pods with VERSION `v1`, and READY is `1/1` for all of them. The script silently skips runtimes without v1 pods.

Measure while training is stopped. A sandbox pod evaluates one request at a time, so if training and the benchmark share pods, waiting time mixes into the results.

**If it fails:** if READY is `0/1`, see the "Sandbox pools and readiness" section of [Troubleshooting](../reference/troubleshooting.md).

## Running it

Print the cold start of every deployed v1 pool and append the evaluation results to a JSONL file.

```bash
scripts/ops/bench.sh        # 32 evaluations per pool (default)
scripts/ops/bench.sh 64     # more requests per pool
```

| Order | What the script does |
|---|---|
| 1 | Goes through `gvisor`, `kata-qemu`, `kata-clh`, `kata-clh-cpu`, `kata-qemu-cpu` in that order and picks only pools that have `version=v1` pods |
| 2 | For every pod, prints the cold start in seconds: the Ready condition's `lastTransitionTime` minus `creationTimestamp` |
| 3 | Picks `relu_bias_triton` for GPU pools and `relu_bias_torch_only` for pools whose name ends in `-cpu` |
| 4 | Runs `gpusandbox.tools bench` as Job `bench-<runtime>-<epoch>` in `rl-trainer` and appends the one-line JSON result to `bench-<YYYYmmdd-HHMMSS>.jsonl` |

**What to look for:** each pool prints a block like this (example shape; values differ per environment):

```text
[hh:mm:ss] gvisor: cold start (creationTimestamp -> Ready)
  sandbox-gvisor-v1-<hash>: <N>s
  sandbox-gvisor-v1-<hash>: <N>s
[hh:mm:ss] gvisor: 32 evaluations of relu_bias_triton
{"address": "sandbox-gvisor-v1.sandbox.svc.cluster.local:8000", "golden": "relu_bias_triton", "runtime": "gvisor", "requests": 32, "ok": 32, ...}
```

The last line is `results: <repository path>/bench-<YYYYmmdd-HHMMSS>.jsonl`. In each JSON line, `ok` should equal `requests`.

The cold start values go only to the terminal, not to the JSONL, so write them down. The script measures only v1 pools; v2 uses a different number of seeds (5), so its evaluation time can differ; compare within one version.

**If it fails:** if every result of a pool fails (`ok` is 0), the bench Job fails and the script stops at that pool (later pools are not measured; behavior of the script code). If `ok` is smaller than `requests`, look up the error strings in the "Viewing /info with the probe tool" and "Sandbox pools and readiness" sections of [Troubleshooting](../reference/troubleshooting.md).

### bench JSON fields

| Field | Meaning |
|---|---|
| `address`, `golden`, `requests` | Target Service, golden used, number of requests sent |
| `runtime` | The runtime reported by the first `ok` result (the profile name, for example `gvisor`) |
| `ok` | Number of results with status `ok` |
| `throughput_eval_per_s` | Number of `ok` results divided by the total elapsed time (requests are sent to the whole pool at once) |
| `eval_p50_s`, `eval_p95_s` | p50/p95 of `duration_s` as measured by the sandbox server |
| `speedup_median` | Median of the measured speedups |
| `ref_ms_median` | Median time per iteration (ms) of the trusted PyTorch reference |

`eval_*`, `speedup_median` and `ref_ms_median` are computed from `ok` results only (failed requests stay out of the latency statistics).

## What goes into evaluation latency

`duration_s` is not the kernel run time but the total time to handle one request. The server creates a fresh process tree per request and goes through every stage below:

```mermaid
flowchart LR
    A["Policy check"] --> B["Untrusted child<br/>python -I, torch import,<br/>CUDA init, load candidate,<br/>Triton compile"]
    B --> C["Outputs per seed<br/>3 warmup, 20 timed"]
    C --> D["Trusted parent<br/>reference and comparison"]
    D --> E["Delete temp directory,<br/>reap leftover processes"]
```

*Takeaway: the part that actually runs the kernel is only a slice of C, so runtime differences in `duration_s` are expected to show up mostly in fixed costs such as process creation, imports, CUDA initialization and compilation (inference; confirm with your own measurements).*

The 3 warmup and 20 timed iterations are the server defaults (`HARNESS_WARMUP`, `HARNESS_ITERS`).

## How to interpret the results

| Comparison | Conditions | Metrics to look at |
|---|---|---|
| Kata CLH CPU vs Kata QEMU CPU | Same `c8i.2xlarge` node (nested virtualization), same image, same golden. Only the hypervisor differs | Cold start, `eval_p50_s`, `eval_p95_s` |
| Kata QEMU vs Kata CLH GPU (experimental) | Same `g4dn.metal`, same T4 | The metrics above and `ref_ms_median`. CLH GPU is not supported upstream, so a failure is not surprising |
| gVisor (A10G) | This repository has no runc baseline on the same A10G | The values themselves, and the same pool measured at another time |
| gVisor CPU vs Kata CPU | Same `c8i.2xlarge` node, same image, same golden. Only the isolation method differs (user-space kernel vs VM). Scenario C in [10 CPU-only path on c8i](10_cpu_only.md) brings up all three pools together | Cold start, `eval_p50_s`, `eval_p95_s` |
| Pools with different GPU types | A10G vs T4 | Do not use them to compare overhead. Treat speedups as per-GPU numbers only |

- **Throughput scales with the number of replicas.** The defaults are 2 for `gvisor`, 4 for `kata-qemu`, 2 for `kata-clh` and 2 for each CPU pool, so compare `throughput_eval_per_s` divided by the number of Ready pods.
- **Do not make the request count too large.** A pod evaluates one request at a time, so the client waits for a free pod, and a wait beyond 600 seconds (acquire timeout) turns the request into a `sandbox_error` and lowers `ok`.
- **Nested virtualization numbers do not carry over to bare metal.** AWS recommends bare metal for performance-sensitive virtualization workloads. Use the CLH vs QEMU result on `c8i` only as a relative comparison of the two hypervisors.
- **If `ref_ms_median` differs on the same GPU type,** that can be a sign that the runtime adds cost to the kernel launch and synchronization path (inference). This harness times with the host clock around `torch.cuda.synchronize()`, so launch cost is in the result.
- **Do not compare directly with KernelBench numbers.** KernelBench times with an L2 flush and CUDA events; this harness uses the host clock and a different input per iteration.

!!! question "❓ Misconception: putting the gVisor and Kata numbers side by side compares the runtimes"
    In this hands-on the gVisor pool (`g5.xlarge`, A10G) and the Kata GPU pool (`g4dn.metal`, T4) differ in GPU, instance and replica count, so you cannot isolate the runtime's share of the difference. To compare runtimes, use a pair with every other condition fixed, such as Kata CLH CPU and Kata QEMU CPU on the same node.

## Measuring cold start again

The script's cold start (pod creation to Ready) includes, by definition, all of the following, plus the wait for the node if the pod was created before its node existed:

- Scheduling and image pull (the CUDA PyTorch images are large)
- Runtime start: the gVisor Sentry, or the Kata VM boot. According to the deployment template comment, a GPU VM pins all guest memory before boot, so the first readiness can take several minutes
- Server start and the GPU probe (torch import and CUDA initialization in a new process)
- The egress denial check (runs in parallel with the GPU probe): when a blocked target drops packets, each target waits for a 2-second timeout, so with IMDS, the API server and the kubelet it takes at most about 6 seconds
- The 5-second readiness probe period and the 1-second resolution of timestamps

To measure again with the image already cached on the node, restart the Deployment while training is not running and rerun the script.

```bash
kubectl -n sandbox rollout restart deployment/sandbox-kata-qemu-v1
kubectl -n sandbox rollout status deployment/sandbox-kata-qemu-v1 --timeout=30m
scripts/ops/bench.sh
```

**What to look for:** the second command ends with `deployment "sandbox-kata-qemu-v1" successfully rolled out`, and the `kata-qemu` cold start lines of the third command show the new pod names.

With `maxSurge: 0`, pods are replaced one at a time, and in a pool with one pod per node, such as gVisor, the new pod starts only after the old one releases the GPU. To measure another pool, replace `kata-qemu` in the Deployment name with that runtime's name (for example `gvisor`).

**If it fails:** if the second command times out, see the "Sandbox pools and readiness" section of [Troubleshooting](../reference/troubleshooting.md), and for Kata also the "Kata" section.

## Results template

Fill in the values you measure, and record the measurement conditions so results can be compared later.

| runtime | Instance (GPU) | Ready pods | cold start (s, median over pods) | eval p50 (s) | eval p95 (s) | throughput (eval/s) | throughput per pod | median speedup | median ref_ms |
|---|---|---|---|---|---|---|---|---|---|
| `gvisor` | `g5.xlarge` (A10G) | | | | | | | | |
| `kata-qemu` | `g4dn.metal` (T4) | | | | | | | | |
| `kata-clh` (experimental) | `g4dn.metal` (T4) | | | | | | | | |
| `gvisor-cpu` | `c8i.2xlarge` (CPU, systrap) | | | | | | | n/a | |
| `kata-clh-cpu` | `c8i.2xlarge` (CPU, nested virt) | | | | | | | n/a | |
| `kata-qemu-cpu` | `c8i.2xlarge` (CPU, nested virt) | | | | | | | n/a | |

Measurement conditions: date, Region, `requests`, `IMAGE_TAG`, gVisor release, Kata version, EKS AMI version, the node's NVIDIA driver, and whether the image was cached.

This command summarizes the JSONL with one line per pool. Replace the file name with the `results:` path from the script's last line.

```bash
python3 - bench-<YYYYmmdd-HHMMSS>.jsonl <<'PY'
import json, sys
for line in open(sys.argv[1]):
    if not line.startswith("{"):
        continue  # skip non-JSON log lines
    r = json.loads(line)
    print(r.get("runtime"), r["ok"], r["requests"], r["eval_p50_s"], r["eval_p95_s"],
          r["throughput_eval_per_s"], r["speedup_median"], r["ref_ms_median"])
PY
```

**What to look for:** one line per measured pool, in the order runtime, ok, requests, p50, p95, throughput, median speedup, median ref_ms. Copy these values into the template above.

## Published reference numbers

| Source | Numbers | Conditions and limits |
|---|---|---|
| Kata metrics CI (3.28.0) | Boot to workload: CLH 0.39 s, QEMU 0.71 s | Different machines, wide tolerance. Measures only the window until the VM is up and the workload starts |
| AWS China blog (2026-07, `c5.metal`, Kata 3.31.0 + CLH, OpenSandbox, Karpenter 1.12.1) | Cold start about 3 s, pool claim about 230 ms | Measured by the blog authors on bare-metal CPU sandboxes. Pool claim appears to be the time to get a sandbox from a pre-warmed pool and differs from cold start |
| Memory numbers from the same blog | CLH about 130 MB, QEMU about 160 MB | They equal the `overhead.podFixed` defaults of Kata 3.31.0, so they are probably not measurements |
| Kata 4.3.1 RuntimeClass `overhead.podFixed` | clh 130Mi/250m, qemu 320Mi/250m, qemu-nvidia-gpu 10240Mi/1 CPU | What the scheduler reserves on top of each pod. Not a measurement of actual usage |

This hands-on starts pods in advance with Deployments, so the counterpart of the blog's pool claim is not the cold start but the time the client takes to get a free pod.

## Scope and limits

- **No runc baseline.** So gVisor's overhead cannot be computed directly.
- **Kata CLH GPU is not supported upstream,** so the experimental `kata-clh` pool may produce no results.
- **Nested virtualization results are for relative comparison.**
- **Cold start has a 1-second resolution.** Kubernetes timestamps are in seconds, so sub-second differences are invisible.
- **Only v1 pools are measured.** `v1` is fixed in the script's label selector and the Service address; measuring v2 means changing both.

## Time and cost

The benchmark is one Job per pool, so it should be short next to the time the nodes stay up (not measured). The cost is the node charges meanwhile, and `g4dn.metal` at 7.824 USD per hour is the largest (us-east-1 and us-west-2 On-Demand). `c8i.2xlarge` is 0.37484 USD per hour (same basis). When you are done, scale the GPU node groups to zero or delete them as described in [99 Cleanup](99_cleanup.md).

## How to verify

1. For every pool, `<runtime>: cold start (creationTimestamp -> Ready)` is followed by one `  <pod>: <N>s` line per pod.
2. A bench JSON line follows, and `ok` equals `requests`.
3. At the end, `results: <repo>/bench-<timestamp>.jsonl` is printed, and the file has one JSON line per measured pool.
4. Pools that are not deployed are skipped silently, so if a pool is missing, check for v1 pods with `kubectl -n sandbox get pods -L gpusandbox/runtime,gpusandbox/version` from "Before you begin".

??? note "References"
    | Topic | Link |
    |---|---|
    | EC2 nested virtualization (bare metal recommended) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html |
    | Amazon EC2 accelerated computing instances (A10G, T4) | https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html |
    | AWS China blog (Kata + CLH, OpenSandbox) | https://aws.amazon.com/cn/blogs/china/amazon-eks-build-security-ai-agent/ |
    | KernelBench (timing method) | https://github.com/ScalingIntelligence/KernelBench |

    All sources: [this page in All references](../reference/references.md#ref-handson-08-benchmark)
