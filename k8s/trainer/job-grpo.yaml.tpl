# Scenario A: GRPO trainer as a Kubernetes Job on the EC2 trainer node (runc, 1x A10G).
# Rendered by scripts/07_run_grpo.sh.
apiVersion: batch/v1
kind: Job
metadata:
  name: grpo-${RUN_ID}
  namespace: rl-trainer
  labels:
    app: grpo-trainer
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 86400
  template:
    metadata:
      labels:
        app: grpo-trainer
        # Admitted by the sandbox namespace's NetworkPolicy.
        gpusandbox/client: "true"
    spec:
      serviceAccountName: grpo-trainer
      # No Kubernetes API token: the trainer only needs the sandbox-audience token below.
      automountServiceAccountToken: false
      restartPolicy: Never
      # Pod Security "restricted" (rl-trainer warns on it): run as the vLLM base image's own
      # non-root user (vllm, uid 2000, primary group 0, home /home/vllm; trainer/Dockerfile keeps it).
      securityContext:
        runAsNonRoot: true
        runAsUser: 2000
        seccompProfile: {type: RuntimeDefault}
      nodeSelector:
        gpusandbox/role: trainer
      tolerations:
        - {key: gpusandbox/role, operator: Equal, value: trainer, effect: NoSchedule}
        - {key: nvidia.com/gpu, operator: Exists, effect: NoSchedule}
      containers:
        - name: trainer
          image: ${TRAINER_IMAGE_URI}
          command: ["python", "/opt/gpusandbox/rl/trl/train_grpo.py"]
          args:
            - --output-dir=/outputs/grpo
            - --max-steps=${MAX_STEPS}
            - --model=${MODEL_ID}
            - --metrics-file=/outputs/grpo/sandbox_metrics.jsonl
          env:
            - {name: SANDBOX_ROUTING_FILE, value: /etc/gpusandbox/routing/routing.json}
            - {name: SANDBOX_TOKEN_FILE, value: /var/run/secrets/gpusandbox/token}
            - {name: HF_HOME, value: /cache/hf}
            - {name: PYTORCH_CUDA_ALLOC_CONF, value: "expandable_segments:True"}
            # Caches that default to ~ (vLLM, Triton, torch) go to the vllm user's writable home.
            - {name: HOME, value: /home/vllm}
          securityContext:
            allowPrivilegeEscalation: false
            capabilities: {drop: ["ALL"]}
          resources:
            requests: {cpu: "7", memory: 28Gi, nvidia.com/gpu: "1"}
            limits: {cpu: "7", memory: 28Gi, nvidia.com/gpu: "1"}
          volumeMounts:
            # Mounted as a directory (not subPath) so ConfigMap updates reach the pod.
            - {name: routing, mountPath: /etc/gpusandbox/routing, readOnly: true}
            - {name: sandbox-token, mountPath: /var/run/secrets/gpusandbox, readOnly: true}
            - {name: cache, mountPath: /cache}
            - {name: outputs, mountPath: /outputs}
            - {name: dshm, mountPath: /dev/shm}
      volumes:
        - name: routing
          configMap: {name: sandbox-routing}
        - name: sandbox-token
          projected:
            sources:
              - serviceAccountToken:
                  audience: ${SANDBOX_AUDIENCE}
                  expirationSeconds: 3600
                  path: token
        - name: cache
          emptyDir: {}
        - name: outputs
          emptyDir: {}
        - name: dshm
          emptyDir: {medium: Memory, sizeLimit: 8Gi}
