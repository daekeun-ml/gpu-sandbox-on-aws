# Script reference

!!! info "TL;DR"
    Choose a task below. Each entry explains how to run the script, how to recognize success, and what happens if you run it again.

Run from the repository root. Keep `cdk/tunnel.sh` open in another terminal for steps that use `kubectl` or Helm. See the [hands-on overview](../handson/00_overview.md) to choose a scenario.

| Task | Script |
|---|---|
| Check AWS setup, create EKS, and build images | [Steps 01–03 and the tunnel](#main-order) |
| Install runtimes and deploy pools | [Steps 04–06](#scripts04_install_gpu_stacksh), [Kata](#kata) |
| Run GRPO on EC2 (A) | [07_run_grpo.sh](#scripts07_run_grposh) |
| Run GRPO on HyperPod (B1 and B2) | [hyperpod/run_grpo.sh](#scriptshyperpodrun_grposh) |
| Verify, simulate, switch versions, or measure latency | [Verification and operations](#verification-and-operations) |
| Assign sandboxes per episode | [Extensions](#extensions) |
| Publish a recording | [Demo site](#demo-site) |
| Remove exercise resources | [Cleanup exercise](../handson/99_cleanup.md) |

## Main order

### `scripts/01_check_prereqs.sh`

- **What it does**: Checks the local tools, the AWS identity, the G and VT and Standard vCPU quotas, nested virtualization support of `KATA_CPU_INSTANCE_TYPE`, and which AZs offer the GPU instance types. It creates or changes nothing.
- **Usage**: `scripts/01_check_prereqs.sh` (no arguments)
- **When**: First, before `02_create_cluster.sh`. All scenarios (A, B1, B2, C).
- **Time and cost**: Short (lookups only). Nothing is billed.
- **Running it again**: Read-only, so running it again changes nothing. Run it again after a quota increase to see the new values.
- **Success signal**: The last log line is `Done. Request quota increases before 02_create_cluster.sh if any value above is too low.` The script does not judge whether a quota is enough, so compare the printed values with what you need.
- **If it fails**: [Troubleshooting: Configuration and scripts](troubleshooting.md#configuration-and-scripts), [01 Cluster and images](../handson/01_cluster_and_images.md)

### `scripts/02_create_cluster.sh`

- **What it does**: Runs `cdk/deploy.sh` to deploy the CDK stack `<CLUSTER_NAME>-cdk` (VPC, EKS with a private endpoint, add-ons, the node groups of the scenario, the access instance).
- **Usage**: `scripts/02_create_cluster.sh` (A, or `SCENARIO` from `config.env`), `--hyperpod` (B1), `--hyperpod-b2` (B2), `--cpu-only` (C). Add the Kata node groups with `WITH_KATA_CPU=1` and `WITH_KATA_GPU=1` (needs `KATA_IOMMU_AMI_ID`) in `scripts/config.env`.
- **When**: After `01_check_prereqs.sh`, and again with the same option when you add Kata node groups. All scenarios.
- **Time and cost**: 20-30 min (script estimate), about 20 min for scenario C (measured). Billing starts for the EKS control plane, the NAT gateway, 2x `m6i.large` and `t4g.nano`, plus 2x `g5.xlarge` (A, B1), `g5.2xlarge` (A), `c8i.2xlarge` (C or `WITH_KATA_CPU=1`) and `g4dn.metal` (`WITH_KATA_GPU=1`).
- **Running it again**: CDK changes only what differs, so the same settings change nothing, and a changed `WITH_KATA_*` changes only that node group. A scenario different from the deployed one stops with `the stack runs scenario <X>, not <Y>`; to switch on purpose, add `CHANGE_SCENARIO=1` (node groups are replaced). With `WITH_KATA_GPU=1` every run asks you to type `metal`, and a node count you changed outside CDK must be put back first ([06](../handson/06_sandbox_update.md)).
- **Success signal**: The CDK `Outputs` show `EndpointPublicAccess = false`, followed by the `Next:` hints. With the tunnel open, `kubectl get nodes` shows 2 system nodes and the scenario's nodes `Ready` (A: 1 trainer and 2 sandbox-gvisor, C: 1 sandbox-kata).
- **If it fails**: [Troubleshooting: CDK and the tunnel](troubleshooting.md#cdk-and-the-tunnel), [Troubleshooting: Cluster and nodes](troubleshooting.md#cluster-and-nodes)

### `cdk/tunnel.sh`

- **What it does**: Forwards `127.0.0.1:<port>` on your workstation to the private EKS API endpoint through an SSM Session Manager session, and points the kubectl context `<CLUSTER_NAME>-tunnel` at that port. It runs until you press Ctrl-C.
- **Usage**: `cdk/tunnel.sh [local_port]` (default 8443). Run it in a second terminal and leave it open.
- **When**: Open it between `02_create_cluster.sh` and `03_build_push_images.sh`, and keep it open for every step that uses kubectl or helm (04 onward, Kata, operations, HyperPod, extensions). All scenarios.
- **Time and cost**: Short. It creates no resources (the access instance comes from `02_create_cluster.sh`).
- **Running it again**: Every run rewrites the kubeconfig context and cluster entry and opens a new session. If the session drops, run it again; if an old tunnel still uses the same port, close that terminal first.
- **Success signal**: `kubectl context <CLUSTER_NAME>-tunnel -> 127.0.0.1:8443 -> <endpoint> (via i-...); Ctrl-C closes it`, then `Waiting for connections...`.
- **If it fails**: [Troubleshooting: CDK and the tunnel](troubleshooting.md#cdk-and-the-tunnel)

### `scripts/03_build_push_images.sh`

- **What it does**: Builds the sandbox, trainer and control images for `linux/amd64`, pushes them to ECR as `<ECR_REPO_PREFIX>/<name>:<IMAGE_TAG>`, and prints the `export` lines for `config.env`. It creates a missing ECR repository with IMMUTABLE tags and scan on push.
- **Usage**: `scripts/03_build_push_images.sh`, or `--no-trainer` to skip the trainer image. Scenario B uses `HYPERPOD=1 scripts/03_build_push_images.sh` to add `hyperpodrun` to the trainer.
- **When**: After `02_create_cluster.sh`, before `04_install_gpu_stack.sh`. A and B1, B2 (`HYPERPOD=1`), C (`--no-trainer`).
- **Time and cost**: Depends on the build host and the network. ECR storage is billed.
- **Running it again**: Tags are IMMUTABLE, so with the same `IMAGE_TAG` the push of the first image (sandbox) fails and the script stops. Change `IMAGE_TAG` in `scripts/config.env` (a value set in front of the command is overridden by `config.env`), run it again, and update `config.env` with the printed URIs.
- **Success signal**: After `Add to scripts/config.env:`, three export lines for `SANDBOX_IMAGE_URI`, `TRAINER_IMAGE_URI` and `CONTROL_IMAGE_URI` (two with `--no-trainer`, without `TRAINER_IMAGE_URI`).
- **If it fails**: [Troubleshooting: Configuration and scripts](troubleshooting.md#configuration-and-scripts), [01 Cluster and images](../handson/01_cluster_and_images.md)

### `scripts/04_install_gpu_stack.sh`

- **What it does**: Installs the NVIDIA device plugin (CDI mode) with Helm and sets its `CDI_DISABLE_HOOKS` env. Then it registers the `gvisor` RuntimeClass and checks the gVisor kernel and CUDA with one smoke pod.
- **Usage**: `scripts/04_install_gpu_stack.sh` (no arguments). When the stack runs scenario B2 or C, it skips the RuntimeClass and the smoke pod.
- **When**: After `03_build_push_images.sh`, before `05_setup_namespaces_auth.sh`. A and B1 use all of it, B2 only the device plugin. C runs `kata/cpu_nodes.sh` instead.
- **Time and cost**: Helm `--wait` for the device plugin, 15 min timeout for the smoke pod. Nothing new is billed.
- **Running it again**: `helm upgrade --install` and `kubectl apply` re-apply, and the smoke pod gets a new name and is deleted at the end. If every GPU on the sandbox-gvisor nodes is in use (the pool from `06_deploy_sandboxes.sh`), it stops before the smoke pod with `every GPU on the sandbox-gvisor nodes is in use`; free them with the printed `kubectl -n sandbox scale ... --replicas=0`, run it again, then bring the pool back with `06_deploy_sandboxes.sh gvisor v1`.
- **Success signal**: GPU 1 for each `gpusandbox/device-plugin=cdi` node (briefly `0` right after a restart), then `cuda ok: NVIDIA A10G 2048.0` from the smoke pod. If the smoke pod fails the script only warns, so look for this line yourself (B2 and C end with `skipping the gvisor RuntimeClass and the smoke pod`).
- **If it fails**: [Troubleshooting: gVisor](troubleshooting.md#gvisor), [02 gVisor GPU sandboxes](../handson/02_gvisor.md)

### `scripts/05_setup_namespaces_auth.sh`

- **What it does**: Applies the namespaces (Pod Security), the trainer RBAC and the NetworkPolicies, creates the JWKS ConfigMap with `ops/sync_jwks.sh`, and writes the routing ConfigMap `sandbox-routing` in `rl-trainer`.
- **Usage**: `scripts/05_setup_namespaces_auth.sh`. Choose the first pool with `ACTIVE_RUNTIME` and `ACTIVE_VERSION` (default `gvisor`, `v1`). For example, C uses `ACTIVE_RUNTIME=kata-clh-cpu` and B2 `ACTIVE_RUNTIME=gvisor-hyperpod`.
- **When**: After `04_install_gpu_stack.sh` (C: `kata/cpu_nodes.sh`), before `06_deploy_sandboxes.sh`. All scenarios.
- **Time and cost**: Short. Nothing is billed.
- **Running it again**: Everything is `kubectl apply`, but it rewrites the active pool of the routing table to `ACTIVE_RUNTIME` and `ACTIVE_VERSION` (`gvisor/v1` if unset) and puts the `sandbox` NetworkPolicies back to the hands-on rules. After a version switch or in scenario C, pass the values in use; to refresh only the signing keys, use `ops/sync_jwks.sh` (with the production gateway, re-apply the gateway manifests too).
- **Success signal**: The `"active"` entry at the top of the printed routing.json is the first pool. For A and B1 it is `{"runtime": "gvisor", "version": "v1"}`.
- **If it fails**: [Troubleshooting: 401 and 403 responses](troubleshooting.md#401-and-403-responses), [Troubleshooting: NetworkPolicy](troubleshooting.md#networkpolicy), [04 Deploy and verify sandbox pools](../handson/04_sandbox_pools.md)

### `scripts/06_deploy_sandboxes.sh`

- **What it does**: Deploys the sandbox pool `sandbox-<runtime>-<version>` (Deployment and headless Service) from the runtime profile (`k8s/sandbox/profiles/<runtime>.env`) and the version file (`k8s/sandbox/versions/<version>.env`), and waits for the rollout.
- **Usage**: `scripts/06_deploy_sandboxes.sh <runtime> [version] [replicas]`. runtime is `gvisor`, `gvisor-hyperpod`, `kata-qemu`, `kata-clh` (experimental), `gvisor-cpu`, `kata-clh-cpu` or `kata-qemu-cpu`; version is `v1` (default) or `v2`; without replicas the profile value is used.
- **When**: After `05_setup_namespaces_auth.sh`, once per pool. A and B1 use `gvisor`, B2 `gvisor-hyperpod`, C the three CPU pools.
- **Time and cost**: 30 min rollout timeout. It uses existing nodes, so nothing new is billed.
- **Running it again**: `kubectl apply` changes nothing if the manifest is the same; if the image or settings changed, the Deployment replaces its pods. The replica count goes back to the argument or the profile value, so this is also how you bring back a pool scaled to zero (`ops/rollout.sh --finish`, the hint of `04_install_gpu_stack.sh`).
- **Success signal**: The rollout finishes and the pods are `1/1 Running`.
- **If it fails**: [Troubleshooting: Sandbox pools and readiness](troubleshooting.md#sandbox-pools-and-readiness), [04 Deploy and verify sandbox pools](../handson/04_sandbox_pools.md)

### `scripts/07_run_grpo.sh`

- **What it does**: Creates the GRPO training Job `grpo-<RUN_ID>` in `rl-trainer` and, once the pod is Ready, shows its log as one-line summaries. Ctrl-C stops following the log, not the training.
- **Usage**: `scripts/07_run_grpo.sh [max_steps]` (default 60). Set `RUN_ID` and `MODEL_ID` (default `Qwen/Qwen2.5-Coder-1.5B-Instruct`) as environment variables; see the raw JSON with `GPUSANDBOX_LOG=json scripts/07_run_grpo.sh`.
- **When**: After `06_deploy_sandboxes.sh` and `ops/verify.sh`. Scenario A only (B uses `hyperpod/run_grpo.sh`, C uses `ops/simulate.sh`).
- **Time and cost**: About 50 min for the default 60 steps and about 12 min for 5 steps (measured, including image pull and model download, `g5.2xlarge`). Nothing new is billed.
- **Running it again**: `RUN_ID` defaults to the current time, so every run creates a new Job; finished Jobs stay for a day. The trainer node has one GPU, so while an earlier run is still training the new pod stays Pending and the script fails after its 30 min wait (the Job stays).
- **Success signal**: `routing  mode direct  runtime gvisor  version v1 ...`, then `batch` and `train` lines, and at the end `train done ...` and `done  output /outputs/grpo/final  reward_batches <int>`.
- **If it fails**: [Troubleshooting: Training](troubleshooting.md#training), [05 On-policy GRPO training](../handson/05_grpo_training.md)

### `scripts/08_cleanup.sh`

- **What it does**: Asks for the cluster name, deletes the pools, Jobs and the CDK stack with `cdk/destroy.sh --yes`, then deletes the AMIs whose IDs are in `config.env` (`KATA_IOMMU_AMI_ID`, `HYPERPOD_B2_AMI_ID`) and their snapshots, asking for each. At the end it lists the remaining instances.
- **Usage**: `scripts/08_cleanup.sh`, or `--images` to delete the ECR repositories too. In scenario B run `scripts/hyperpod/delete.sh` first.
- **When**: When you finish. All scenarios; with the tunnel open, the workloads in the cluster go first.
- **Time and cost**: Not recorded (it waits for the CloudFormation deletion). Billing for the stack's resources ends, and the secrets KMS key enters its 7-day deletion window.
- **Running it again**: Every run asks for the confirmation word and starts again with `cdk/destroy.sh`. If the ID of an AMI you already deleted is still in `config.env`, it can stop at the AMI step, so remove that ID before you run it again with `--images`.
- **Success signal**: The last table (instances tagged `project=gpu-sandbox-on-aws`) is empty.
- **If it fails**: [Troubleshooting: Cleanup and cost](troubleshooting.md#cleanup-and-cost), [99 Cleanup](../handson/99_cleanup.md)

## CDK

### `cdk/deploy.sh`

- **What it does**: Reads `scripts/config.env` and deploys the CDK stack `<CLUSTER_NAME>-cdk` with `cdk deploy --require-approval broadening`. `02_create_cluster.sh` runs this script.
- **Usage**: `cdk/deploy.sh [A|B1|B2|C] [--with-kata-cpu]` (without an argument, `SCENARIO`). With `ADMIN_PRINCIPAL_ARN` empty, your current IAM user or role becomes the cluster admin; add `CHANGE_SCENARIO=1` to change the scenario.
- **When**: Usually not run directly but through `02_create_cluster.sh`. All scenarios.
- **Time and cost**: Same as `02_create_cluster.sh`.
- **Running it again**: A scenario different from the stack output `Scenario` stops unless `CHANGE_SCENARIO=1` is set; the same scenario changes only what differs. A change that broadens IAM or security group permissions makes `cdk deploy` ask for approval.
- **Success signal**: The CDK `Outputs` (including `EndpointPublicAccess = false`) and the `Next:` hints.
- **If it fails**: [Troubleshooting: CDK and the tunnel](troubleshooting.md#cdk-and-the-tunnel)

### `cdk/destroy.sh`

- **What it does**: If the cluster API is reachable, deletes the Jobs in `rl-trainer` and the Deployments and Services in `sandbox` first; then deletes the stack with `cdk destroy --force` and the Lambda log groups left outside the stack. It keeps the ECR repositories and prints the command to delete them.
- **Usage**: `cdk/destroy.sh [--yes]` (`--yes` skips the prompt). Usually `08_cleanup.sh` runs it.
- **When**: At cleanup. All scenarios.
- **Time and cost**: Not recorded (it waits for the CloudFormation deletion). Billing for the stack's resources ends.
- **Running it again**: The in-cluster deletes use `--all`, so they are safe when nothing is left, and without the tunnel it only warns and goes on to delete the stack. How `cdk destroy` ends when the stack is already gone cannot be told from the code.
- **Success signal**: The instance table is empty, followed by `ECR repositories are kept. To delete them:`.
- **If it fails**: [Troubleshooting: Cleanup and cost](troubleshooting.md#cleanup-and-cost), [99 Cleanup](../handson/99_cleanup.md)

## Kata

### `scripts/kata/cpu_nodes.sh`

- **What it does**: Checks that the `sandbox-kata-cpu` node group exists and installs kata-deploy (Helm) and the `gvisor-cpu` RuntimeClass. Then the `gvisor-cpu`, `kata-clh` and `kata-qemu` smoke pods print the kernel seen inside each sandbox.
- **Usage**: `scripts/kata/cpu_nodes.sh` (no arguments). The node group comes from `02_create_cluster.sh --cpu-only` (C) or `WITH_KATA_CPU=1`.
- **When**: In C after `03_build_push_images.sh` (instead of 04); in the other scenarios after `04_install_gpu_stack.sh`, when you use the Kata CPU node.
- **Time and cost**: About 14 min (measured, mostly kata-deploy), 20 min kata-deploy timeout. Nothing new is billed (`c8i.2xlarge` comes from `02_create_cluster.sh`).
- **Running it again**: `helm upgrade --install` and `kubectl apply` re-apply, and the smoke pods get new names and are deleted. It shares the kata-deploy release with `kata/gpu_nodes.sh`, so running it again resets the release to the base values without the experimental CLH GPU values (`ENABLE_EXPERIMENTAL_CLH_GPU=1`).
- **Success signal**: The `kernel seen inside: ...` kernels of `gvisor-cpu`, `kata-clh` and `kata-qemu` all differ from the host kernel on the last line. A failed smoke pod only warns, so check the three lines yourself.
- **If it fails**: [Troubleshooting: Kata](troubleshooting.md#kata), [Troubleshooting: Configuration and scripts](troubleshooting.md#configuration-and-scripts), [03 Kata sandboxes](../handson/03_kata.md)

### `scripts/kata/gpu_nodes.sh`

- **What it does**: With `KATA_IOMMU_AMI_ID` empty, builds an AMI with the IOMMU enabled and stops. With the ID set, it checks the `sandbox-kata-gpu` node group, installs the GPU Operator and kata-deploy, and waits for `nvidia.com/pgpu` to appear.
- **Usage**: `scripts/kata/gpu_nodes.sh`. Put the `KATA_IOMMU_AMI_ID` printed by the first run and `WITH_KATA_GPU=1` in `config.env`, then run `02_create_cluster.sh` and this script again. Turn on the experimental `kata-clh-nvidia-gpu` with `ENABLE_EXPERIMENTAL_CLH_GPU=1`.
- **When**: After rehearsing with `kata/cpu_nodes.sh`, when you need Kata with a GPU (full path). It can be added to any scenario.
- **Time and cost**: About 10 min for the AMI (script estimate), up to 20 min waiting for pgpu. The AMI builder `m6i.large` (briefly) and the AMI snapshot are billed; `g4dn.metal` (7.824 USD/hour) starts when you run `02_create_cluster.sh` again.
- **Running it again**: Every run with `KATA_IOMMU_AMI_ID` empty builds another AMI, and `08_cleanup.sh` deletes only the one AMI in `config.env`, so put the first ID in right away. With the ID set, it re-applies both Helm releases with `helm upgrade --install`; running without `ENABLE_EXPERIMENTAL_CLH_GPU=1` drops the experimental kata-deploy values.
- **Success signal**: `pgpu=8  cc.ready.state=false`, then one line for the `kata-qemu-nvidia-gpu` RuntimeClass.
- **If it fails**: [Troubleshooting: Kata](troubleshooting.md#kata), [Troubleshooting: Configuration and scripts](troubleshooting.md#configuration-and-scripts), [03 Kata sandboxes](../handson/03_kata.md)

## Verification and operations

### `scripts/ops/verify.sh`

- **What it does**: Runs four checks on one pool: the kernel inside the sandbox vs the node's kernel, blocked connections from inside the sandbox (instance metadata, Kubernetes API, kubelet, internet), golden verdicts through the authenticated API (probe Job), and a blocked caller from another namespace.
- **Usage**: `scripts/ops/verify.sh <runtime> [version]` (version default `v1`)
- **When**: After every pool deployed with `06_deploy_sandboxes.sh`, and as step 2 of `ops/rollout.sh`. All scenarios.
- **Time and cost**: A few minutes (including the probe Job). Nothing is billed.
- **Running it again**: It only checks, so it is safe. Every run creates a new probe Job (`probe-<runtime>-<version>-<time>`, deleted 1 hour after it finishes) and a temporary pod in `default` (`--rm`).
- **Success signal**: The last line is `pool sandbox-<runtime>-<version> verified`. The script does not judge the kernel comparison of check 1, so check that the two printed values differ.
- **If it fails**: [Troubleshooting: Sandbox pools and readiness](troubleshooting.md#sandbox-pools-and-readiness), [Troubleshooting: 401 and 403 responses](troubleshooting.md#401-and-403-responses), [Troubleshooting: NetworkPolicy](troubleshooting.md#networkpolicy)

### `scripts/ops/rollout.sh`

- **What it does**: Switches the sandbox version blue/green while training runs: deploy the `<to>` pool, verify it, check parity with `<from>`, and switch the routing table (`rl-trainer`, and `sandbox-gateway` if it exists). `--finish` scales the `<from>` pool to zero.
- **Usage**: `scripts/ops/rollout.sh <runtime> <from> <to> [--finish]`. For example `scripts/ops/rollout.sh gvisor v1 v2`, then the same command with `--finish` once you see the switch. Roll back by swapping `<from>` and `<to>`.
- **When**: While `07_run_grpo.sh` (A), `hyperpod/run_grpo.sh` (B) or `ops/simulate.sh` (C) runs.
- **Time and cost**: See [06](../handson/06_sandbox_update.md). gVisor needs 2 more `g5.xlarge` for v2 (2.012 USD/hour while the node group has 4 nodes); Kata QEMU needs no extra node.
- **Running it again**: Without `--finish` it repeats steps 1 to 4: the deploy is `kubectl apply` and the switch writes the same table again. If parity fails it does not switch, and `<from>` keeps receiving requests. `--finish` skips the deploy and the switch and only scales `<from>` to zero, so run it after you see the switch in the trainer log.
- **Success signal**: `1) deploying` through `4) switching the routing table to <runtime>/<to>` in order, with every parity line `PASS`. Then the trainer (or simulate) log shows `SWITCH  <runtime>/<from> -> <runtime>/<to>`; `--finish` prints `deployment.apps/sandbox-<runtime>-<from> scaled`.
- **If it fails**: [Troubleshooting: Version switches (routing)](troubleshooting.md#version-switches-routing), [06 Updating the sandbox during training](../handson/06_sandbox_update.md)

### `scripts/ops/simulate.sh`

- **What it does**: Without a model, runs a Job that sends golden submissions batch by batch to the pool the routing ConfigMap points at, and shows the `reward_batch` and `sandbox_version_switch` events. This is not training.
- **Usage**: `scripts/ops/simulate.sh [steps] [interval_s]` (default 30 batches, 20 s)
- **When**: In scenario C after the pools and `ops/verify.sh`, together with `ops/rollout.sh` in a second terminal.
- **Time and cost**: By default 30 batches with 29 waits of 20 s. The 2026-11-17 run (`kata-clh-cpu`) took about 16 min. Nothing is billed.
- **Running it again**: Every run creates a new Job (`simulate-<time>`) and reads the active pool at that moment. Several runs at once send overlapping requests to the same pool.
- **Success signal**: A `batch <n>  <runtime>/<version>  ...` line per batch. After a version switch, one `SWITCH ...` line and `batch` lines without `MIXED VERSIONS`.
- **If it fails**: [Troubleshooting: Version switches (routing)](troubleshooting.md#version-switches-routing), [10 Hands-on lab with CPUs only](../handson/10_cpu_only.md)

### `scripts/ops/bench.sh`

- **What it does**: For every pool with v1 pods, prints the cold start (pod creation to Ready) and measures latency p50 and p95, throughput and speedup with the same golden kernel (`relu_bias_triton` on GPU, `relu_bias_torch_only` on CPU). Results go to `bench-<time>.jsonl`.
- **Usage**: `scripts/ops/bench.sh [requests]` (default 32)
- **When**: After the pools are deployed and verified, while no training runs. Optional in all scenarios.
- **Time and cost**: In the second pass on 2026-11-18 the evaluation phase took about 100-300 s per pool, about 13 min for five pools (Job creation and pool restarts not included). Nothing new is billed; the nodes bill while it runs.
- **Running it again**: Every run writes a new results file and creates a new bench Job per pool. Cold start is computed from the creation time of the current pods, so without restarting them you get the same values again (see the re-measuring steps in [08](../handson/08_benchmark.md)).
- **Success signal**: One `bench  <runtime>  ok <n>/<requests>  p50 ...` line per pool, and `results: <file>` at the end.
- **If it fails**: [Troubleshooting: Sandbox pools and readiness](troubleshooting.md#sandbox-pools-and-readiness), [08 Runtime benchmark](../handson/08_benchmark.md)

All five EKS pools completed 32 requests each (160/160). [Results and run conditions](../handson/08_benchmark.md#runtime-results)

### `scripts/ops/sync_jwks.sh`

- **What it does**: Copies the cluster's ServiceAccount issuer public keys (JWKS) and the issuer into the ConfigMap `sandbox-auth-jwks` in the `sandbox` namespace. These are not secrets.
- **Usage**: `scripts/ops/sync_jwks.sh` (no arguments)
- **When**: `05_setup_namespaces_auth.sh` runs it; run it on its own when the API server rotates its signing keys. All scenarios.
- **Time and cost**: Short. Nothing is billed.
- **Running it again**: It overwrites the ConfigMap with `kubectl apply`, so it is safe, and sandbox pods re-read the changed file. If the JWKS it fetched is empty, it stops before changing the ConfigMap.
- **Success signal**: The apply result for `configmap/sandbox-auth-jwks`, and the last line `issuer: <issuer URL>`.
- **If it fails**: [Troubleshooting: 401 and 403 responses](troubleshooting.md#401-and-403-responses)

## HyperPod

### Managed B2 with CPU and GPU workers on HyperPod

| Command | What it does |
|---|---|
| `scripts/hyperpod/create_managed.sh` | Submits the same AWS template as the HyperPod EKS wizard. Creates the control plane and the `system`, `trainer` and `sandbox` HyperPod groups. |
| `scripts/hyperpod/reboot_sandboxes.sh` | Stages the supported driver on the two grading workers, reboots workers that need it through HyperPod and verifies the running module. |
| `scripts/hyperpod/prepare_managed.sh` | Enables VPC CNI NetworkPolicy, places CoreDNS on `system` and checks the training operator and its certificate webhook. |
| `scripts/hyperpod/bench_b2.sh 32` | Runs the same Triton evaluation from the `system` and `trainer` groups in sequence. Writes one JSONL file per client. |

See the [B2 lab](../handson/07_hyperpod_b2.md) for regional settings, screenshots and cleanup. The `create.sh` and AMI build commands below belong to the separate CDK deployment.

### `scripts/hyperpod/create.sh`

- **What it does**: Prepares the HyperPod dependency Helm chart, the lifecycle script bucket (Block Public Access) and the execution role, attaches a HyperPod cluster to EKS with `create-cluster`, and installs the training operator add-on. `--b2` adds a `sandbox` instance group that boots from the custom AMI, and the `gvisor-hyperpod` RuntimeClass.
- **Usage**: `scripts/hyperpod/create.sh` (B1) or `--b2` (B2, needs `HYPERPOD_B2_AMI_ID`). Needs `git` and `jq`.
- **When**: B1 after `02_create_cluster.sh --hyperpod`, `HYPERPOD=1 03_build_push_images.sh` and `04_install_gpu_stack.sh`. B2 after `hyperpod/build_b2_ami.sh`.
- **Time and cost**: 15-30 min until InService (script estimate). Billing starts for HyperPod `ml.g5.2xlarge` (1.515 USD/hour); B2 adds 2x `ml.g5.xlarge`.
- **Running it again**: Steps 1 and 2 (Helm chart, Block Public Access, lifecycle upload) are applied again, and the bucket and role are created only if missing. Step 4 `create-cluster` is expected to fail when a cluster with that name exists (inferred), and step 5 fails too when the add-on exists; if only step 5 failed, run just the two commands in [07](../handson/07_hyperpod_b1.md).
- **Success signal**: `status` is `InService` and `failure` is empty, and the final node table shows the HyperPod nodes (B2: two `ml.g5.xlarge` nodes `Schedulable`).
- **If it fails**: [Troubleshooting: HyperPod](troubleshooting.md#hyperpod), [B1 · Train on HyperPod and grade on EC2](../handson/07_hyperpod_b1.md)

### `scripts/hyperpod/build_b2_ami.sh`

- **What it does**: Launches the HyperPod EKS base AMI on an `m6i.large` builder, replaces the NVIDIA driver with `B2_NVIDIA_DRIVER_VERSION` (580.178.04), adds gVisor, and images the result as a custom AMI. The builder's own security group (outbound HTTPS only) is deleted with the builder.
- **Usage**: `scripts/hyperpod/build_b2_ami.sh` (no arguments). Set the base AMI yourself with `HYPERPOD_BASE_AMI_ID`.
- **When**: In B2 after `02_create_cluster.sh --hyperpod-b2`, before `hyperpod/create.sh --b2`.
- **Time and cost**: 20-40 min (estimate). The `m6i.large` during the build and the AMI snapshot afterwards are billed.
- **Running it again**: It does not look at an existing `HYPERPOD_B2_AMI_ID` and builds a new AMI on every run, and `08_cleanup.sh` deletes only the one AMI in `config.env`, so delete older AMIs and snapshots yourself. A failed build leaves the stopped builder (EBS charges); clean it up with the printed commands before you run it again.
- **Success signal**: `GPUSANDBOX-B2-BUILD: OK ...`, then `export HYPERPOD_B2_AMI_ID="ami-..."`.
- **If it fails**: [Troubleshooting: HyperPod](troubleshooting.md#hyperpod), [Earlier CDK workflow with a custom AMI](hyperpod_custom_ami.md)

### `scripts/hyperpod/check_gvisor.sh`

- **What it does**. Checks the NVIDIA driver of each HyperPod worker outside the CPU system group against the pinned gVisor release. It creates a temporary namespace for its debug pods and removes that namespace after the checks.
- **Usage**: `scripts/hyperpod/check_gvisor.sh` (no arguments)
- **When**: In B2 after `hyperpod/create.sh --b2`, before deploying the pool.
- **Time and cost**: Not recorded in the docs (each node downloads gVisor). Nothing is billed.
- **Success signal**: `driver 580.178.04: SUPPORTED by gVisor ...` on the two sandbox nodes. `driver 595.91.07: NOT supported ...` on the trainer node is expected.
- **If it fails**: [Troubleshooting: HyperPod](troubleshooting.md#hyperpod), [Earlier CDK workflow with a custom AMI](hyperpod_custom_ami.md)

### `scripts/hyperpod/run_grpo.sh` { #scriptshyperpodrun_grposh }

Submit a GRPO Job to a HyperPod trainer in B1 or B2. The existing sandbox pool grades the model-generated code, and the trainer updates the model from those scores.

**Before you run it**　Prepare the training operator, trainer node, and sandbox pool in the [HyperPod exercise](../handson/07_hyperpod_b1.md). `HYPERPOD=1 scripts/03_build_push_images.sh` builds a trainer image with `hyperpodrun`. Set `TRAINER_IMAGE_URI`, `SANDBOX_AUDIENCE`, and `HYPERPOD_TRAINER_INSTANCE_TYPE` in `scripts/config.env`.

```bash
scripts/hyperpod/run_grpo.sh 5
```

The argument is the number of optimizer steps. It defaults to 60. The default model is `Qwen/Qwen2.5-Coder-1.5B-Instruct`. The script renders `k8s/trainer/hyperpod-job-grpo.yaml.tpl` and submits a `HyperPodPyTorchJob` named `grpo-<RUN_ID>` in `rl-trainer`. The operator schedules a pod that requests one GPU. The pod reads the routing ConfigMap and token to reach the pool.

| Check | Meaning |
|---|---|
| `HyperPodPyTorchJob grpo-<RUN_ID> submitted` | The API accepted the Job. Check the pod separately. |
| `routing` | The trainer read the pool route. The template expects this event within 20 minutes. |
| `reward_batch` and advancing steps | Check the sample verdicts and training progress. Investigate repeated `sandbox_error`. |

The B1 trainer completed one GRPO step and two EC2 gVisor sandboxes scored 12 submissions. [Job status and logs](../handson/07_hyperpod_b1.md#how-to-verify)

The script prints the Job name. Use it as the `HPJob` label value to find this run’s pod.

```bash
kubectl -n rl-trainer get pods -l 'HPJob=grpo-<RUN_ID>' -o wide
kubectl -n rl-trainer logs -f <trainer-pod> -c pytorch
```

`RUN_ID` defaults to the current timestamp. A new ID creates another Job, which may wait for the GPU if a previous Job is running. `/outputs` is an `emptyDir`, so replacing the pod removes checkpoints stored there.

See [HyperPod troubleshooting](troubleshooting.md#hyperpod) for operator and scheduling issues, or [training troubleshooting](troubleshooting.md#training) for missing scoring logs.

### `scripts/hyperpod/delete.sh`

- **What it does**: Asks for the HyperPod cluster name, deletes the HyperPodPyTorchJobs, the HyperPod cluster (waiting until it is gone) and the execution role, then asks again and empties and deletes the lifecycle bucket. The EKS cluster stays.
- **Usage**: `scripts/hyperpod/delete.sh` (no arguments)
- **When**: At cleanup in scenario B, before `08_cleanup.sh`.
- **Time and cost**: Not recorded in the docs (see [07](../handson/07_hyperpod_b1.md)). Billing for the HyperPod resources ends.
- **Running it again**: If the HyperPod cluster is already gone, `delete-cluster` fails and the script stops before the role and bucket steps. If the first run stopped at the bucket prompt, delete the remaining bucket yourself.
- **Success signal**: `waiting for the cluster to disappear`, `deleted role <name>-execution`, then the last line `HyperPod resources deleted`.
- **If it fails**: [Troubleshooting: Cleanup and cost](troubleshooting.md#cleanup-and-cost), [99 Cleanup](../handson/99_cleanup.md)

## Extensions

### `scripts/extensions/agent_sandbox.sh`

- **What it does**: Gives each episode its own sandbox from an Agent Sandbox warm pool. `install` sets up the controller and CRDs (default v1.0.11) and the claim RBAC, `pool` creates a SandboxTemplate and SandboxWarmPool, `claim` borrows one sandbox, prints its address and releases it, and `episodes` creates a Job that runs multi-turn episodes without a model.
- **Usage**: `scripts/extensions/agent_sandbox.sh install`, `pool <runtime> [n]` (default 1; version file from `VERSION_FILE`, default `v1`), `claim <runtime>`, `episodes <runtime> [episodes] [max_turns]` (default 2 and 3; `max_turns` 1 is single-turn). Change the release with `AGENT_SANDBOX_VERSION`.
- **When**: Optional, after the pools are verified. It works in any scenario; the recorded run used `kata-clh-cpu` in scenario C ([11](../handson/11_multi_turn.md)).
- **Time and cost**: About 25 s for 2 episodes of 3 turns (measured, `kata-clh-cpu` in scenario C). No new nodes, but every idle warm sandbox holds an accelerator.
- **Running it again**: `install` is `kubectl apply`, so it is safe. `pool` re-applies the template, but warm sandboxes that are already running keep the env they started with (`OnReplenish`), and without arguments it rewrites the pool to 1 replica and `v1`. `claim` and `episodes` create a new claim and a new Job (`episodes-<time>`) on every run, and a sandbox is deleted once it is released.
- **Success signal**: `install` shows 4 CRDs, `pool` logs `warm pool kernel-eval-<runtime>: <n> sandbox(es); ...`, `claim` prints `sandbox: ...  address: ...`, and `episodes` ends with a `summary  solved <n>/<n> ...` line and exit code 0.
- **If it fails**: [Troubleshooting: Agent Sandbox and multi-turn episodes](troubleshooting.md#agent-sandbox-and-multi-turn-episodes), [11 Multi-turn episodes](../handson/11_multi_turn.md)

## Demo site

### `demo/deploy.sh`

- **What it does**: Checks the recording (`recording.json`, and `extras.json` if present) for IP addresses, node names, account IDs, ARNs and tokens, then deploys a private S3, CloudFront and WAF stack in us-east-1 and uploads the static site. At the end it checks the WAF attachment, a 403 on direct S3 access, the CSP and HSTS headers, and the 301 redirect for `http://` requests.
- **Usage**: `demo/deploy.sh`. Set other data with `RECORDING=<file>` and `EXTRAS=<file>`, the stack name with `DEMO_STACK_NAME`, and a custom domain with `DEMO_DOMAIN` and `DEMO_CERT_ARN`.
- **When**: An optional step, independent of the cluster. You can deploy right away with the recording in the repository.
- **Time and cost**: Mostly waiting for the stack and CloudFront propagation; the wait for a 200 response is at most about 10 min (the real duration was not measured). S3, CloudFront requests and transfer, and AWS WAF (about 10 USD a month even with no visitors) are billed.
- **Running it again**: The stack goes through `aws cloudformation deploy` (no failure when nothing changed), the files are uploaded again by overwrite and `s3 sync --delete`, and a new invalidation is created. A run without the `EXTRAS` file leaves the `data/extras.json` uploaded earlier in S3.
- **Success signal**: The last line is `[demo] live: <URL>`. The header checks run even if no 200 response arrived, so open the URL in a browser yourself.
- **If it fails**: [CloudFront demo deployment](demo_site.md)

### `demo/teardown.sh`

- **What it does**: Asks for the stack name, empties the site bucket and deletes the demo stack. The access log bucket has `DeletionPolicy Retain` and stays.
- **Usage**: `demo/teardown.sh` (another stack name with `DEMO_STACK_NAME`)
- **When**: When you take the demo site down.
- **Time and cost**: Not recorded (it waits for the stack deletion). Billing for S3, CloudFront and WAF ends; the log bucket stays until you delete it (log objects expire after 90 days).
- **Running it again**: If the stack is already gone, reading its outputs fails and the script stops without deleting anything. Delete the remaining log bucket with the `aws s3 rb s3://<log bucket> --force` the first run printed.
- **Success signal**: `deleted gpu-sandbox-demo`, then `kept the access log bucket <log bucket>; ...`.
- **If it fails**: [99 Cleanup](../handson/99_cleanup.md), [CloudFront demo deployment](demo_site.md)

## Shared files

### `scripts/logview.py`

- **What it does**: Turns JSON events from standard input (`reward_batch`, `sandbox_version_switch`, parity, episodes, bench, trainer metrics) into short colored lines on a terminal. It does not change the pod logs or the metrics files.
- **Usage**: `... | python3 scripts/logview.py`. With `GPUSANDBOX_LOG=json` it shows the raw JSON; with `NO_COLOR` set it uses no colors. When its output goes to a pipe or a file, it passes lines through unchanged.
- **When**: Used automatically by `07_run_grpo.sh` and the scripts that use `lib_jobs.sh` (`ops/verify.sh`, `ops/rollout.sh`, `ops/simulate.sh`, `ops/bench.sh`, `agent_sandbox.sh episodes`).
- **Running it again**: A filter that keeps no state, so you can run it again at any time.
- **Success signal**: Summary lines such as `batch`, `SWITCH`, `PARITY PASS` and `bench`. Lines that are not JSON pass through, and only PASS, FAIL and errors get a color.
- **If it fails**: "How to verify" in [00 Hands-on overview](../handson/00_overview.md)

### `scripts/lib.sh`, `scripts/lib_jobs.sh`

- **What it does**: `lib.sh` is the shared start of every script (`set -euo pipefail`, reading `scripts/config.env`, `log`, `die`, `require_vars`, `require_tools`, `render`, `confirm`). `lib_jobs.sh` provides `run_tool_job` and `run_job_template`, which run `gpusandbox.tools` as a one-shot Job in the cluster and stream its log.
- **Usage**: Not run directly; other scripts read them with `source`.
- **When**: Every script except the two in `demo/` reads `lib.sh`; `ops/verify.sh`, `ops/rollout.sh`, `ops/simulate.sh`, `ops/bench.sh` and `agent_sandbox.sh` use `lib_jobs.sh`.
- **Running it again**: Every script run reads `config.env` again, and a value it `export`s overrides the same name set in front of the command (for example `IMAGE_TAG`, `WITH_KATA_CPU`). Job names end in the current time (seconds), so every run creates a new Job, and finished Jobs are deleted after 1 hour.
- **Success signal**: They return 0 only when the Job succeeded. If the pod does not start within 10 minutes, they fail with the warning `job <name> did not start`.
- **If it fails**: [Troubleshooting: Configuration and scripts](troubleshooting.md#configuration-and-scripts)
