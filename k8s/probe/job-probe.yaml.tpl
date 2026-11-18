# One-shot operator job in the trainer namespace (so the sandbox NetworkPolicy admits it):
#   probe   isolation evidence + golden verdicts for one pool
#   parity  golden verdicts of a candidate version against the baseline
#   bench   latency and speedup for one golden kernel
#   simulate  reward batches without a model or GPU (scenario C)
# Rendered by scripts/ops/verify.sh, ops/simulate.sh, ops/rollout.sh and
# ops/bench.sh.
apiVersion: batch/v1
kind: Job
metadata:
  name: ${JOB_NAME}
  namespace: rl-trainer
  labels:
    app: sandbox-probe
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 3600
  template:
    metadata:
      labels:
        app: sandbox-probe
        gpusandbox/client: "true"
    spec:
      serviceAccountName: sandbox-probe
      automountServiceAccountToken: false
      restartPolicy: Never
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: probe
          image: ${CONTROL_IMAGE_URI}
          command: ["python", "-m", "gpusandbox.tools"]
          args: ${TOOL_ARGS}
          env:
            - {name: SANDBOX_TOKEN_FILE, value: /var/run/secrets/gpusandbox/token}
            - {name: SANDBOX_ROUTING_FILE, value: /etc/gpusandbox/routing/routing.json}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: ["ALL"]}
          volumeMounts:
            - {name: sandbox-token, mountPath: /var/run/secrets/gpusandbox, readOnly: true}
            # A directory mount (not subPath), so routing updates reach the running job.
            - {name: routing, mountPath: /etc/gpusandbox/routing, readOnly: true}
      volumes:
        - name: routing
          configMap: {name: sandbox-routing, optional: true}
        - name: sandbox-token
          projected:
            sources:
              - serviceAccountToken:
                  audience: ${SANDBOX_AUDIENCE}
                  expirationSeconds: 3600
                  path: token
