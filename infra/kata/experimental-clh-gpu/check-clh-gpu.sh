#!/usr/bin/env bash
# Probe whether the experimental kata-clh-nvidia-gpu runtime class can initialise CUDA on the
# Kata GPU node. Prints the outcome; it does not change cluster state beyond one short-lived
# pod in the sandbox namespace, which it deletes.
source "$(dirname "$0")/../../../scripts/lib.sh"
require_tools kubectl
require_vars SANDBOX_IMAGE_URI

pod="clh-gpu-probe-$RANDOM"
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: ${pod}
  namespace: sandbox
  labels: {app.kubernetes.io/name: gpu-sandbox-probe}
spec:
  runtimeClassName: kata-clh-nvidia-gpu
  restartPolicy: Never
  automountServiceAccountToken: false
  nodeSelector: {gpusandbox/kata-gpu: "true"}
  tolerations:
    - {key: gpusandbox/role, operator: Equal, value: sandbox-kata, effect: NoSchedule}
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    seccompProfile: {type: RuntimeDefault}
  containers:
    - name: probe
      image: ${SANDBOX_IMAGE_URI}
      command: ["python", "-c", "import torch, platform; print(platform.release()); print(torch.cuda.is_available() and torch.cuda.get_device_name(0))"]
      resources:
        limits: {cpu: "4", memory: 16Gi, nvidia.com/pgpu: "1"}
      securityContext:
        allowPrivilegeEscalation: false
        capabilities: {drop: ["ALL"]}
EOF
kubectl -n sandbox wait --for=jsonpath='{.status.phase}'=Succeeded "pod/${pod}" --timeout=20m \
  || warn "pod did not succeed; inspect: kubectl -n sandbox describe pod ${pod}"
if ! kubectl -n sandbox logs "${pod}"; then
  warn "no logs: the VM probably never started"
fi
kubectl -n sandbox delete pod "${pod}" --wait=false
