# One-shot multi-turn episode Job (scripts/extensions/agent_sandbox.sh episodes <runtime>):
# python -m gpusandbox.tools multiturn claims one warm sandbox per episode, submits golden
# kernels turn by turn, and deletes each claim when its episode ends.
#
# Unlike k8s/probe/job-probe.yaml.tpl this pod mounts a Kubernetes API token, because it creates,
# reads and deletes SandboxClaims. Its ServiceAccount, sandbox-episode, may do that and nothing
# else (Role sandbox-claims in trainer-claims-rbac.yaml). It also carries the sandbox-audience
# token and the client label that the warm pool's NetworkPolicy admits.
apiVersion: batch/v1
kind: Job
metadata:
  name: ${JOB_NAME}
  namespace: rl-trainer
  labels:
    app: sandbox-episode
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 3600
  template:
    metadata:
      labels:
        app: sandbox-episode
        gpusandbox/client: "true"
    spec:
      serviceAccountName: sandbox-episode
      # The account disables the token mount; this pod opts in for the claims API.
      automountServiceAccountToken: true
      restartPolicy: Never
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: episodes
          image: ${CONTROL_IMAGE_URI}
          command: ["python", "-m", "gpusandbox.tools"]
          args: ${TOOL_ARGS}
          env:
            - {name: SANDBOX_TOKEN_FILE, value: /var/run/secrets/gpusandbox/token}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: ["ALL"]}
          volumeMounts:
            - {name: sandbox-token, mountPath: /var/run/secrets/gpusandbox, readOnly: true}
      volumes:
        - name: sandbox-token
          projected:
            sources:
              - serviceAccountToken:
                  audience: ${SANDBOX_AUDIENCE}
                  expirationSeconds: 3600
                  path: token
