# Agent Sandbox extension (kubernetes-sigs/agent-sandbox v1.0.11, CRDs v1beta1, as of 2026-11).
#
# The same sandbox server as the pools in k8s/sandbox/, but managed per episode: a
# SandboxWarmPool keeps pre-started sandboxes (GPU initialised, egress verified), and the
# trainer claims one per multi-turn episode (SandboxClaim), then releases it. Agent Sandbox
# delegates isolation to the pod's RuntimeClass, so the profiles in k8s/sandbox/profiles/
# (gvisor, kata-qemu, kata-clh-cpu, ...) apply unchanged.
# Rendered by scripts/extensions/agent_sandbox.sh pool <runtime>.
apiVersion: extensions.agents.x-k8s.io/v1beta1
kind: SandboxTemplate
metadata:
  name: kernel-eval-${RUNTIME}
  namespace: sandbox
  labels:
    gpusandbox/runtime: ${RUNTIME}
spec:
  # Claims must not change the environment the harness measures in.
  envVarsInjectionPolicy: Disallowed
  # Per-sandbox headless Service: <sandbox>.<namespace>.svc (status.sandbox.serviceFQDN).
  service: true
  # Replaces the controller's default policy, which allows egress to public addresses.
  networkPolicy:
    ingress:
      - from:
          - namespaceSelector:
              matchLabels: {kubernetes.io/metadata.name: rl-trainer}
            podSelector:
              matchLabels: {gpusandbox/client: "true"}
        ports:
          - {protocol: TCP, port: 8000}
    # No egress rules: nothing leaves the sandbox (no DNS either). Confirm the generated
    # NetworkPolicy with kubectl -n sandbox get networkpolicy -o yaml after applying.
    egress: []
  podTemplate:
    metadata:
      labels:
        app.kubernetes.io/name: gpu-sandbox
        gpusandbox/runtime: ${RUNTIME}
        gpusandbox/managed-by: agent-sandbox
    spec:
      runtimeClassName: ${RUNTIME_CLASS}
      serviceAccountName: gpu-sandbox
      automountServiceAccountToken: false
      enableServiceLinks: false
      restartPolicy: OnFailure
      # Explicit DNS settings stop the controller from injecting public resolvers; the
      # sandbox needs no name resolution at all.
      dnsPolicy: None
      dnsConfig:
        nameservers: ["127.0.0.1"]
      nodeSelector: ${NODE_SELECTOR}
      tolerations:
        - {key: gpusandbox/role, operator: Equal, value: "${NODE_ROLE}", effect: NoSchedule}
        - {key: nvidia.com/gpu, operator: Exists, effect: NoSchedule}
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: sandbox
          image: ${SANDBOX_IMAGE_URI}
          ports:
            - {name: http, containerPort: 8000, protocol: TCP}
          env:
            - {name: SANDBOX_HOST, value: "0.0.0.0"}
            - {name: SANDBOX_VERSION, value: "${VERSION}"}
            - {name: SANDBOX_RUNTIME, value: "${RUNTIME}"}
            - {name: SANDBOX_DEVICE, value: "${SANDBOX_DEVICE}"}
            - {name: SANDBOX_SIZE, value: "${SANDBOX_SIZE}"}
            - {name: HARNESS_SEEDS, value: "${HARNESS_SEEDS}"}
            - {name: HARNESS_MAX_SPEEDUP, value: "${HARNESS_MAX_SPEEDUP}"}
            - name: POD_NAME
              valueFrom: {fieldRef: {fieldPath: metadata.name}}
            - name: NODE_IP
              valueFrom: {fieldRef: {fieldPath: status.hostIP}}
            - name: SANDBOX_EGRESS_PROBE_TARGETS
              value: "169.254.169.254:80,apiserver,$$(NODE_IP):10250"
            - {name: SANDBOX_AUTH_AUDIENCE, value: "${SANDBOX_AUDIENCE}"}
            - {name: SANDBOX_AUTH_ISSUER, value: "${OIDC_ISSUER}"}
            - {name: SANDBOX_AUTH_ALLOWED_SUBJECTS, value: "${SANDBOX_ALLOWED_SUBJECTS}"}
            - {name: SANDBOX_AUTH_JWKS_FILE, value: /etc/gpusandbox/auth/jwks.json}
          resources:
            requests:
              cpu: "${CPU}"
              memory: ${MEMORY}
              ${ACCELERATOR_LIMIT}
            limits:
              cpu: "${CPU}"
              memory: ${MEMORY}
              ${ACCELERATOR_LIMIT}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: ["ALL"]}
          startupProbe:
            httpGet: {path: /readyz, port: http}
            periodSeconds: 5
            failureThreshold: 120
          readinessProbe:
            httpGet: {path: /readyz, port: http}
            periodSeconds: 5
          volumeMounts:
            - {name: work, mountPath: /work}
            - {name: tmp, mountPath: /tmp}
            - {name: auth, mountPath: /etc/gpusandbox/auth, readOnly: true}
      volumes:
        - name: work
          emptyDir: {sizeLimit: 8Gi}
        - name: tmp
          emptyDir: {sizeLimit: 2Gi}
        - name: auth
          configMap: {name: sandbox-auth-jwks}
---
# Every warm sandbox holds a GPU while it waits, so size this to the number of episodes that
# run at the same time, not to the rollout batch.
apiVersion: extensions.agents.x-k8s.io/v1beta1
kind: SandboxWarmPool
metadata:
  name: kernel-eval-${RUNTIME}
  namespace: sandbox
spec:
  replicas: ${WARM_REPLICAS}
  sandboxTemplateRef:
    name: kernel-eval-${RUNTIME}
  updateStrategy:
    # Replace stale sandboxes only when they are claimed or deleted, so a template change
    # does not reboot every Kata GPU VM at once.
    type: OnReplenish
