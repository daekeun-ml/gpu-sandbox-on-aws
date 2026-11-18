# One sandbox pool = one (runtime, version) Deployment + one headless Service.
# Rendered by scripts/06_deploy_sandboxes.sh with a profile from k8s/sandbox/profiles/.
# A new sandbox version is a new Deployment next to the old one (blue/green), never an
# in-place rolling update, so that every GRPO group is scored by exactly one version.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sandbox-${RUNTIME}-${VERSION}
  namespace: sandbox
  labels:
    app.kubernetes.io/name: gpu-sandbox
    gpusandbox/runtime: ${RUNTIME}
    gpusandbox/version: ${VERSION}
spec:
  replicas: ${REPLICAS}
  revisionHistoryLimit: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 0          # GPUs are the constraint; never ask for an extra one
      maxUnavailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: gpu-sandbox
      gpusandbox/runtime: ${RUNTIME}
      gpusandbox/version: ${VERSION}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: gpu-sandbox
        gpusandbox/runtime: ${RUNTIME}
        gpusandbox/version: ${VERSION}
    spec:
      runtimeClassName: ${RUNTIME_CLASS}
      serviceAccountName: gpu-sandbox
      # Candidate code shares this pod: give it nothing worth stealing.
      automountServiceAccountToken: false
      enableServiceLinks: false
      terminationGracePeriodSeconds: 15
      nodeSelector: ${NODE_SELECTOR}
      tolerations:
        - key: gpusandbox/role
          operator: Equal
          value: ${NODE_ROLE}
          effect: NoSchedule
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              gpusandbox/runtime: ${RUNTIME}
              gpusandbox/version: ${VERSION}
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: sandbox
          image: ${SANDBOX_IMAGE_URI}
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          env:
            # Inside the pod network only: headless ClusterIP Service, no NodePort or
            # LoadBalancer, and a NetworkPolicy that admits labelled trainer pods only.
            - {name: SANDBOX_HOST, value: "0.0.0.0"}
            - {name: SANDBOX_VERSION, value: "${VERSION}"}
            - {name: SANDBOX_RUNTIME, value: "${RUNTIME}"}
            - {name: SANDBOX_DEVICE, value: "${SANDBOX_DEVICE}"}
            - {name: SANDBOX_SIZE, value: "${SANDBOX_SIZE}"}
            - {name: SANDBOX_MAX_EVALS, value: "${SANDBOX_MAX_EVALS}"}
            - {name: HARNESS_SEEDS, value: "${HARNESS_SEEDS}"}
            - {name: HARNESS_MAX_SPEEDUP, value: "${HARNESS_MAX_SPEEDUP}"}
            - name: POD_NAME
              valueFrom: {fieldRef: {fieldPath: metadata.name}}
            - name: NODE_NAME
              valueFrom: {fieldRef: {fieldPath: spec.nodeName}}
            - name: NODE_IP
              valueFrom: {fieldRef: {fieldPath: status.hostIP}}
            # Readiness requires all of these to be unreachable: instance metadata, the
            # Kubernetes API and the node's kubelet port.
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
              ephemeral-storage: 12Gi
              ${ACCELERATOR_LIMIT}
            limits:
              cpu: "${CPU}"
              memory: ${MEMORY}
              ephemeral-storage: 12Gi
              ${ACCELERATOR_LIMIT}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          # A Kata GPU VM pins all guest memory before boot and CUDA initialises inside the
          # guest, so the first readiness can take several minutes.
          startupProbe:
            httpGet: {path: /readyz, port: http}
            periodSeconds: 5
            failureThreshold: 120
          readinessProbe:
            httpGet: {path: /readyz, port: http}
            periodSeconds: 5
            failureThreshold: 2
          livenessProbe:
            httpGet: {path: /healthz, port: http}
            periodSeconds: 10
            failureThreshold: 3
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
          configMap:
            name: sandbox-auth-jwks
---
# Headless: one DNS A record per *ready* pod, so readiness gating happens before any client
# learns a pod's address. ClusterIP-only by construction (no type, no external exposure).
apiVersion: v1
kind: Service
metadata:
  name: sandbox-${RUNTIME}-${VERSION}
  namespace: sandbox
  labels:
    app.kubernetes.io/name: gpu-sandbox
    gpusandbox/runtime: ${RUNTIME}
    gpusandbox/version: ${VERSION}
spec:
  clusterIP: None
  publishNotReadyAddresses: false
  selector:
    app.kubernetes.io/name: gpu-sandbox
    gpusandbox/runtime: ${RUNTIME}
    gpusandbox/version: ${VERSION}
  ports:
    - name: http
      port: 8000
      targetPort: http
      protocol: TCP
