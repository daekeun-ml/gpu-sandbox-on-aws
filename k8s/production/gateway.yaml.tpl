# Production sandbox gateway. Trainers talk to the gateway; only the gateway talks to sandbox
# pods. Render and apply it with scripts/render.py (see docs/production/03_gateway_and_pools.md).
apiVersion: v1
kind: Namespace
metadata:
  name: sandbox-gateway
  labels:
    pod-security.kubernetes.io/enforce: restricted
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gateway
  namespace: sandbox-gateway
automountServiceAccountToken: false
---
# TokenReview: authenticate callers.
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: gpu-sandbox-gateway-tokenreview
rules:
  - apiGroups: ["authentication.k8s.io"]
    resources: ["tokenreviews"]
    verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gpu-sandbox-gateway-tokenreview
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: gpu-sandbox-gateway-tokenreview}
subjects:
  - {kind: ServiceAccount, name: gateway, namespace: sandbox-gateway}
---
# Pod recycling: delete draining sandbox pods so their Deployment replaces them.
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gpu-sandbox-gateway-recycler
  namespace: sandbox
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gpu-sandbox-gateway-recycler
  namespace: sandbox
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: Role, name: gpu-sandbox-gateway-recycler}
subjects:
  - {kind: ServiceAccount, name: gateway, namespace: sandbox-gateway}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: sandbox-gateway
  labels: {app.kubernetes.io/name: gpu-sandbox-gateway}
spec:
  # One replica on purpose: it is the single scheduler and holds the group pins. Run more
  # only with an external pin store (see docs/production/03_gateway_and_pools.md).
  replicas: 1
  selector:
    matchLabels: {app.kubernetes.io/name: gpu-sandbox-gateway}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: gpu-sandbox-gateway
        # The sandbox NetworkPolicy admits sandbox clients only.
        gpusandbox/client: "true"
    spec:
      serviceAccountName: gateway
      # The API token is mounted explicitly below (TokenReview + pod deletion only).
      automountServiceAccountToken: false
      priorityClassName: system-cluster-critical
      nodeSelector: {gpusandbox/role: system}
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: gateway
          image: ${CONTROL_IMAGE_URI}
          ports: [{name: http, containerPort: 8080}]
          env:
            - {name: GATEWAY_HOST, value: "0.0.0.0"}
            - {name: GATEWAY_AUTH_AUDIENCE, value: "gpu-sandbox-gateway"}
            - {name: GATEWAY_ALLOWED_SUBJECTS, value: "${GATEWAY_ALLOWED_SUBJECTS}"}
            - {name: GATEWAY_ROUTING_FILE, value: /etc/gpusandbox/routing/routing.json}
            - {name: GATEWAY_SANDBOX_TOKEN_FILE, value: /var/run/secrets/gpusandbox/token}
            - {name: GATEWAY_RECYCLE_PODS, value: "1"}
          resources:
            requests: {cpu: "1", memory: 1Gi}
            limits: {cpu: "2", memory: 2Gi}
          readinessProbe:
            httpGet: {path: /readyz, port: http}
          livenessProbe:
            httpGet: {path: /healthz, port: http}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: ["ALL"]}
          volumeMounts:
            - {name: routing, mountPath: /etc/gpusandbox/routing, readOnly: true}
            - {name: tokens, mountPath: /var/run/secrets, readOnly: true}
      volumes:
        - name: routing
          configMap: {name: sandbox-routing}
        - name: tokens
          projected:
            sources:
              # Kubernetes API token (TokenReview, pod recycling).
              - serviceAccountToken: {path: kubernetes.io/serviceaccount/token, expirationSeconds: 3600}
              - configMap:
                  name: kube-root-ca.crt
                  items: [{key: ca.crt, path: kubernetes.io/serviceaccount/ca.crt}]
              - downwardAPI:
                  items:
                    - path: kubernetes.io/serviceaccount/namespace
                      fieldRef: {fieldPath: metadata.namespace}
              # Token presented to sandbox pods.
              - serviceAccountToken: {path: gpusandbox/token, audience: "${SANDBOX_AUDIENCE}", expirationSeconds: 3600}
---
apiVersion: v1
kind: Service
metadata:
  name: gateway
  namespace: sandbox-gateway
spec:
  selector: {app.kubernetes.io/name: gpu-sandbox-gateway}
  ports: [{name: http, port: 8080, targetPort: http}]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-trainers-to-gateway
  namespace: sandbox-gateway
spec:
  podSelector: {matchLabels: {app.kubernetes.io/name: gpu-sandbox-gateway}}
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels: {kubernetes.io/metadata.name: rl-trainer}
      ports: [{protocol: TCP, port: 8080}]
---
# In production the sandbox pools admit the gateway only (replaces the hands-on policy that
# admits labelled trainer pods directly).
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-clients-to-sandbox-api
  namespace: sandbox
spec:
  podSelector:
    matchLabels: {app.kubernetes.io/name: gpu-sandbox}
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels: {kubernetes.io/metadata.name: sandbox-gateway}
          podSelector:
            matchLabels: {app.kubernetes.io/name: gpu-sandbox-gateway}
      ports: [{protocol: TCP, port: 8000}]
