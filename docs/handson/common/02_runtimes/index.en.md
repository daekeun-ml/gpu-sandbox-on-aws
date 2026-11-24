---
hide:
  - footer
---

# 02 Prepare the sandbox runtime

After [shared step 01](../01_provision/index.md), make sure the image URIs are saved in `scripts/config.env`. Run the commands from the project directory. For A, B1 and C, leave the SSM tunnel open and use the original terminal. For B2, use the EKS context from step 01.

=== "A (EC2 GPU)"

    For installation steps and sample CUDA check output, see the [EC2 gVisor guide](gvisor.md).

    Run this before deploying the `gvisor` v1 pool, with one free GPU on an EC2 grader.

    ```bash
    scripts/04_install_gpu_stack.sh
    ```

    On the default A10G nodes, look for `Starting gVisor...` at runtime startup and `cuda ok: NVIDIA A10G 2048.0` for the CUDA calculation. [Sample GPU check output](gvisor.md#gpu-smoke)

    [03 Deploy and verify grading pools (A)](../03_pools/index.md#__tabbed_1_1)

=== "B1 (HyperPod + EC2)"

    For a walkthrough of both steps, start with [checking gVisor and the GPU on EC2](gvisor.md), then see [connecting the HyperPod trainer to EKS](b1_trainer.md).

    1. **Check the GPU on an EC2 grader**

        ```bash
        scripts/04_install_gpu_stack.sh
        ```

        On the default A10G nodes, look for `Starting gVisor...` at runtime startup and `cuda ok: NVIDIA A10G 2048.0` for the CUDA calculation. [Sample GPU check output](gvisor.md#gpu-smoke)

    2. **Attach the HyperPod trainer to EKS**

        This command provisions a billable HyperPod training instance.

        ```bash
        scripts/hyperpod/create.sh
        ```

        In the final node list, check that the trainer is `Ready` and its health label reads `Schedulable`. Deploy the grading pool once the command below returns `ACTIVE`.

        ```bash
        source scripts/config.env
        aws eks describe-addon --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
          --addon-name amazon-sagemaker-hyperpod-training-operator --query 'addon.status' --output text
        ```

    [03 Deploy and verify grading pools (B1)](../03_pools/index.md#__tabbed_1_2)

=== "B2 (HyperPod)"

    The [HyperPod worker guide](b2_workers.md) explains why the grading workers need a different driver and how to recover if the training operator fails to install.

    1. **Prepare the drivers on the two grading workers**

        Run this with Bash 4 or later once both graders are `Ready`. The script reboots the grading workers that need the driver change and checks the loaded driver.

        ```bash
        scripts/hyperpod/reboot_sandboxes.sh
        ```

    2. **Prepare the training operator and GPU plugin**

        ```bash
        scripts/hyperpod/prepare_managed.sh
        ```

        When the operator reports `ACTIVE`, install the GPU plugin.

        ```bash
        scripts/04_install_gpu_stack.sh
        ```

    3. **Register the RuntimeClass for HyperPod grading**

        ```bash
        kubectl apply -f k8s/runtimes/runtimeclass-gvisor-hyperpod.yaml
        kubectl get runtimeclass gvisor-hyperpod
        ```

        Check that the `gvisor-hyperpod` row lists `runsc` as its `HANDLER`. Verify GPU grading after deploying the two pods in step 03.

    [03 Deploy and verify grading pools (B2)](../03_pools/index.md#__tabbed_1_3)

=== "C (CPU)"

    For installation steps and a comparison of the three kernel versions, see the [Kata CPU guide](kata.md#kata-cpu).

    Install the CPU runtimes and run the test pods on the `c8i.2xlarge` node from step 01.

    ```bash
    scripts/kata/cpu_nodes.sh
    ```

    Compare the kernel versions printed for `gvisor-cpu`, `kata-clh` and `kata-qemu` with the host kernel on the last line. gVisor reports its own kernel and Kata reports the guest kernel inside its VM. [Output from the three runtimes](kata.md#cpu-run)

    [03 Deploy and verify grading pools (C)](../03_pools/index.md#__tabbed_1_4)

For an additional EC2 configuration that passes a physical GPU to a VM, see [Kata GPU passthrough](kata.md#kata-gpu).
