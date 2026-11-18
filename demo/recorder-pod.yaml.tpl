# Recorder pod for the replay demo (docs/handson/09_demo_site.md, section 2).
# It meets the conditions `gpusandbox.tools record` needs without a running training Job:
# rl-trainer namespace and client label (sandbox NetworkPolicy), an allowlisted ServiceAccount and
# a projected token with the sandbox audience (sandbox auth), and the trainer image (torch, for the
# task modules). It needs no GPU: the golden set runs in the sandbox pools.
#   python3 scripts/render.py demo/recorder-pod.yaml.tpl | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: demo-recorder
  namespace: rl-trainer
  labels:
    app: demo-recorder
    gpusandbox/client: "true"
spec:
  serviceAccountName: grpo-trainer
  automountServiceAccountToken: false
  restartPolicy: Never
  # Pod Security "restricted", like the trainer Job (the vLLM image's vllm user, uid 2000).
  securityContext:
    runAsNonRoot: true
    runAsUser: 2000
    seccompProfile: {type: RuntimeDefault}
  nodeSelector:
    gpusandbox/role: system
  containers:
    - name: recorder
      image: ${TRAINER_IMAGE_URI}
      # Stays up for three hours so that `kubectl exec` and `kubectl cp` work; delete it afterwards.
      command: ["sleep", "10800"]
      env:
        - {name: SANDBOX_TOKEN_FILE, value: /var/run/secrets/gpusandbox/token}
        - {name: HOME, value: /home/vllm}
      securityContext:
        allowPrivilegeEscalation: false
        capabilities: {drop: ["ALL"]}
      resources:
        requests: {cpu: 500m, memory: 2Gi}
        limits: {cpu: "1", memory: 4Gi}
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
