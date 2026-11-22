# Scenario B: the same GRPO trainer as a HyperPodPyTorchJob on a HyperPod node.
# Needs the HyperPod training operator add-on and a trainer image built with
# INSTALL_HYPERPOD_AGENT=1 (hyperpodrun). Rendered by scripts/hyperpod/run_grpo.sh.
#
# What HyperPod adds for a long on-policy run: deep health checks and automatic replacement
# of a faulty GPU node, job restarts (jobMaxRetryCount), and log-based hang detection. The
# trainer resumes from its latest checkpoint after a restart (train_grpo.py looks for one).
apiVersion: sagemaker.amazonaws.com/v1
kind: HyperPodPyTorchJob
metadata:
  name: grpo-${RUN_ID}
  namespace: rl-trainer
spec:
  nprocPerNode: "1"
  runPolicy:
    jobMaxRetryCount: 3
    restartPolicy:
      numRestartBeforeFullJobRestart: 1
      evalPeriodSeconds: 3600
      maxFullJobRestarts: 2
    cleanPodPolicy: All
    logMonitoringConfiguration:
      # The trainer prints one JSON line when routing is resolved, then one per reward batch.
      - name: JobStart
        logPattern: '.*"event": "routing".*'
        expectedStartCutOffInSeconds: 1200
      # No reward batch for 30 minutes means generation or the sandbox pool is stuck.
      - name: RewardStalled
        logPattern: '.*"event": "reward_batch".*'
        expectedRecurringFrequencyInSeconds: 1800
  replicaSpecs:
    - name: pods
      replicas: 1
      template:
        metadata:
          labels:
            app: grpo-trainer
            gpusandbox/client: "true"
        spec:
          serviceAccountName: grpo-trainer
          automountServiceAccountToken: false
          affinity:
            nodeAffinity:
              requiredDuringSchedulingIgnoredDuringExecution:
                nodeSelectorTerms:
                  - matchExpressions:
                      - key: node.kubernetes.io/instance-type
                        operator: In
                        values: ["${HYPERPOD_TRAINER_INSTANCE_TYPE}"]
                      - key: sagemaker.amazonaws.com/node-health-status
                        operator: In
                        values: ["Schedulable"]
          containers:
            - name: pytorch
              image: ${TRAINER_IMAGE_URI}
              command:
                - hyperpodrun
                - --nproc_per_node=1
                - --nnodes=1
                - /opt/gpusandbox/rl/trl/train_grpo.py
                - --output-dir=/outputs/grpo
                - --max-steps=${MAX_STEPS}
                - --model=${MODEL_ID}
                - --metrics-file=/outputs/grpo/sandbox_metrics.jsonl
              env:
                - {name: SANDBOX_ROUTING_FILE, value: /etc/gpusandbox/routing/routing.json}
                - {name: SANDBOX_TOKEN_FILE, value: /var/run/secrets/gpusandbox/token}
                - {name: HF_HOME, value: /cache/hf}
                - {name: PYTORCH_CUDA_ALLOC_CONF, value: "expandable_segments:True"}
              resources:
                # The operator, per-job pod manager and monitoring pods share the trainer node.
                requests: {nvidia.com/gpu: "1", cpu: "5", memory: 24Gi}
                limits: {nvidia.com/gpu: "1", cpu: "5", memory: 24Gi}
              volumeMounts:
                - {name: routing, mountPath: /etc/gpusandbox/routing, readOnly: true}
                - {name: sandbox-token, mountPath: /var/run/secrets/gpusandbox, readOnly: true}
                - {name: cache, mountPath: /cache}
                # emptyDir keeps the hands-on simple (Pod Security "baseline" forbids
                # hostPath). To resume after a node replacement, mount shared storage here
                # (FSx for Lustre PVC); see docs/production/06_scaling_with_verl.md.
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
