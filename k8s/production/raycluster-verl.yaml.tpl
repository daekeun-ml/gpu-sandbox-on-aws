# RayCluster for veRL (KubeRay ray.io/v1). Works on EC2 GPU nodes (scenario A) or HyperPod
# nodes (scenario B): pick the node selector with VERL_NODE_SELECTOR, for example
#   '{"gpusandbox/role": "trainer"}'                            EC2 node group or Karpenter
#   '{"sagemaker.amazonaws.com/node-health-status": "Schedulable", "node.kubernetes.io/instance-type": "ml.g6e.48xlarge"}'
# KubeRay's head Service is ClusterIP. The Ray dashboard and job API have no authentication,
# so the NetworkPolicy at the end admits only this RayCluster's own pods; operators reach the
# dashboard with kubectl port-forward (binds 127.0.0.1).
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: verl
  namespace: rl-trainer
spec:
  rayVersion: "${RAY_VERSION}"
  headGroupSpec:
    rayStartParams:
      dashboard-host: "0.0.0.0"   # inside the pod network only; see the NetworkPolicy below
      num-gpus: "0"
    template:
      metadata:
        labels: {app: verl-head}
      spec:
        nodeSelector: {gpusandbox/role: system}
        containers:
          - name: ray-head
            image: ${VERL_IMAGE_URI}
            resources:
              requests: {cpu: "4", memory: 16Gi}
              limits: {cpu: "4", memory: 16Gi}
            volumeMounts:
              - {name: shared, mountPath: /fsx}
        volumes:
          - name: shared
            persistentVolumeClaim: {claimName: ${SHARED_PVC}}
  workerGroupSpecs:
    - groupName: gpu
      replicas: ${VERL_NNODES}
      minReplicas: ${VERL_NNODES}
      maxReplicas: ${VERL_NNODES}
      rayStartParams:
        num-gpus: "${VERL_GPUS_PER_NODE}"
      template:
        metadata:
          labels:
            app: verl-worker
            # Reward workers run here and call the gateway.
            gpusandbox/client: "true"
        spec:
          serviceAccountName: grpo-trainer
          automountServiceAccountToken: false
          nodeSelector: ${VERL_NODE_SELECTOR}
          tolerations:
            - {key: nvidia.com/gpu, operator: Exists, effect: NoSchedule}
            - {key: gpusandbox/role, operator: Equal, value: trainer, effect: NoSchedule}
          containers:
            - name: ray-worker
              image: ${VERL_IMAGE_URI}
              env:
                - {name: SANDBOX_GATEWAY, value: "gateway.sandbox-gateway.svc.cluster.local:8080"}
                - {name: SANDBOX_TOKEN_FILE, value: /var/run/secrets/gpusandbox/token}
                - {name: HF_HOME, value: /fsx/hf}
              resources:
                requests: {nvidia.com/gpu: "${VERL_GPUS_PER_NODE}", cpu: "${VERL_CPU}", memory: ${VERL_MEMORY}}
                limits: {nvidia.com/gpu: "${VERL_GPUS_PER_NODE}", cpu: "${VERL_CPU}", memory: ${VERL_MEMORY}}
              volumeMounts:
                - {name: shared, mountPath: /fsx}
                - {name: gateway-token, mountPath: /var/run/secrets/gpusandbox, readOnly: true}
                - {name: dshm, mountPath: /dev/shm}
          volumes:
            - name: shared
              persistentVolumeClaim: {claimName: ${SHARED_PVC}}
            - name: gateway-token
              projected:
                sources:
                  - serviceAccountToken: {audience: gpu-sandbox-gateway, expirationSeconds: 3600, path: token}
            - name: dshm
              emptyDir: {medium: Memory, sizeLimit: 64Gi}
---
# Only members of this RayCluster may talk to its pods (GCS, dashboard, job API, workers).
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: verl-raycluster-members-only
  namespace: rl-trainer
spec:
  podSelector:
    matchLabels:
      ray.io/cluster: verl
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              ray.io/cluster: verl
