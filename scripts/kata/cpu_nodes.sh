#!/usr/bin/env bash
# CPU sandbox node on a virtual instance with EC2 nested virtualization (no .metal): Kata
# (kata-clh, kata-qemu) and gVisor (gvisor-cpu) side by side, for a fraction of the
# g4dn.metal price. Scenario C uses only this node; the other scenarios use it as the CPU tier.
# Billable: 1x c8i.2xlarge (0.37484 USD/hour in us-east-1 and us-west-2, as of 2026-11).
source "$(dirname "$0")/../lib.sh"
require_tools aws helm kubectl
require_vars CLUSTER_NAME AWS_REGION KATA_VERSION

# The node group and its nested-virtualization launch template come from the CDK stack
# (scenario C, or any scenario with WITH_KATA_CPU=1). This step installs Kata on it.
aws eks describe-nodegroup --region "${AWS_REGION}" --cluster-name "${CLUSTER_NAME}" \
  --nodegroup-name sandbox-kata-cpu >/dev/null 2>&1 \
  || die "no sandbox-kata-cpu node group: set WITH_KATA_CPU=1 in scripts/config.env and run scripts/02_create_cluster.sh again"

log "installing kata-deploy ${KATA_VERSION} (DaemonSet mode, Kata nodes only)"
helm upgrade --install kata-deploy oci://ghcr.io/kata-containers/kata-deploy-charts/kata-deploy \
  --version "${KATA_VERSION}" --namespace kube-system \
  -f "${REPO_ROOT}/infra/kata/kata-deploy-values.yaml" --wait --timeout 20m

kubectl apply -f "${REPO_ROOT}/k8s/runtimes/runtimeclass-gvisor-cpu.yaml"

log "checking /dev/kvm and the runtime classes"
node="$(kubectl get nodes -l gpusandbox/kata-gpu=false -o jsonpath='{.items[0].metadata.name}')"
kubectl get node "${node}" -o jsonpath='{.metadata.labels.katacontainers\.io/kata-runtime}{"\n"}'
kubectl get runtimeclass | grep -E '^kata-(clh|qemu) ' || die "kata runtime classes missing"
kubectl get runtimeclass gvisor-cpu

# gVisor reports its own synthetic kernel version; Kata reports the guest VM kernel.
for rc in gvisor-cpu kata-clh kata-qemu; do
  pod="${rc}-smoke-$RANDOM"
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata: {name: ${pod}, namespace: default}
spec:
  runtimeClassName: ${rc}
  restartPolicy: Never
  automountServiceAccountToken: false
  nodeSelector: {gpusandbox/kata-gpu: "false"}
  tolerations: [{key: gpusandbox/role, operator: Equal, value: sandbox-kata, effect: NoSchedule}]
  containers:
    - name: smoke
      image: public.ecr.aws/amazonlinux/amazonlinux:2023
      command: ["/bin/sh", "-c", "echo kernel seen inside: \$(uname -r) \$(uname -v)"]
      resources: {limits: {cpu: "1", memory: 512Mi}}
EOF
  kubectl wait --for=jsonpath='{.status.phase}'=Succeeded "pod/${pod}" --timeout=10m \
    || warn "${pod} did not succeed: kubectl describe pod ${pod}"
  echo "${rc}: $(kubectl logs "${pod}" | tr '\n' ' ')"
  kubectl delete pod "${pod}" --wait=false
done
log "host kernel for comparison: $(kubectl get node "${node}" -o jsonpath='{.status.nodeInfo.kernelVersion}')"
