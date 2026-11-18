# Keep the sandbox pods' copy of the ServiceAccount issuer keys current. Public keys only;
# the job needs read access to issuer discovery (granted to all ServiceAccounts by default)
# and patch access to one ConfigMap.
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jwks-sync
  namespace: sandbox-gateway
automountServiceAccountToken: true
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: jwks-sync
  namespace: sandbox
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["sandbox-auth-jwks"]
    verbs: ["get", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: jwks-sync
  namespace: sandbox
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: Role, name: jwks-sync}
subjects:
  - {kind: ServiceAccount, name: jwks-sync, namespace: sandbox-gateway}
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: jwks-sync
  namespace: sandbox-gateway
spec:
  schedule: "17 * * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          serviceAccountName: jwks-sync
          restartPolicy: Never
          nodeSelector: {gpusandbox/role: system}
          securityContext:
            runAsNonRoot: true
            runAsUser: 10001
            seccompProfile: {type: RuntimeDefault}
          containers:
            - name: sync
              image: ${CONTROL_IMAGE_URI}
              command: ["python", "-m", "gpusandbox.tools", "sync-jwks", "--namespace", "sandbox"]
              securityContext:
                allowPrivilegeEscalation: false
                readOnlyRootFilesystem: true
                capabilities: {drop: ["ALL"]}
