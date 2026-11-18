# Karpenter v1 EC2NodeClasses for the production track (Karpenter 1.15.x, as of 2026-11).
# Install Karpenter itself with the official guide (IAM, interruption queue, Helm), then:
#   python3 scripts/render.py infra/karpenter/nodeclasses.yaml.tpl | kubectl apply -f -
#   kubectl apply -f infra/karpenter/nodepools.yaml
# Karpenter merges these user data parts with its own NodeConfig (cluster settings, labels,
# taints) and keeps IMDSv2 with hop limit 1 by default.
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: sandbox-gvisor
spec:
  role: ${KARPENTER_NODE_ROLE}
  amiSelectorTerms:
    - alias: al2023@latest   # GPU instance types get the NVIDIA variant
  subnetSelectorTerms:
    - tags: {karpenter.sh/discovery: "${CLUSTER_NAME}"}
  securityGroupSelectorTerms:
    - tags: {karpenter.sh/discovery: "${CLUSTER_NAME}"}
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs: {volumeSize: 100Gi, volumeType: gp3, encrypted: true, deleteOnTermination: true}
  userData: |
    MIME-Version: 1.0
    Content-Type: multipart/mixed; boundary="GPUSANDBOX"

    --GPUSANDBOX
    Content-Type: application/node.eks.aws

    apiVersion: node.eks.aws/v1alpha1
    kind: NodeConfig
    spec:
      containerd:
        config: |
          [plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runsc]
            runtime_type = 'io.containerd.runsc.v1'
          [plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runsc.options]
            TypeUrl = 'io.containerd.runsc.v1.options'
            ConfigPath = '/etc/containerd/runsc.toml'

    --GPUSANDBOX
    Content-Type: text/x-shellscript; charset="us-ascii"

    #!/bin/bash
    export GVISOR_RELEASE="${GVISOR_RELEASE}"
    @@include infra/gvisor/install-gvisor.sh@@

    --GPUSANDBOX
    Content-Type: text/x-shellscript; charset="us-ascii"

    @@include infra/eks/node-guard.sh@@
    --GPUSANDBOX--
---
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: sandbox-kata-gpu
spec:
  role: ${KARPENTER_NODE_ROLE}
  # Standard AL2023 EKS AMI with intel_iommu=on (infra/kata/build-iommu-ami.sh). Selecting an
  # AMI by ID instead of an alias means Karpenter needs amiFamily to generate the bootstrap.
  amiFamily: AL2023
  amiSelectorTerms:
    - id: ${KATA_IOMMU_AMI_ID}
  subnetSelectorTerms:
    - tags: {karpenter.sh/discovery: "${CLUSTER_NAME}"}
  securityGroupSelectorTerms:
    - tags: {karpenter.sh/discovery: "${CLUSTER_NAME}"}
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs: {volumeSize: 200Gi, volumeType: gp3, encrypted: true, deleteOnTermination: true}
  userData: |
    MIME-Version: 1.0
    Content-Type: multipart/mixed; boundary="GPUSANDBOX"

    --GPUSANDBOX
    Content-Type: application/node.eks.aws

    apiVersion: node.eks.aws/v1alpha1
    kind: NodeConfig
    spec:
      containerd:
        config: |
          imports = ["/etc/containerd/conf.d/*.toml"]
      kubelet:
        config:
          runtimeRequestTimeout: 20m

    --GPUSANDBOX
    Content-Type: text/x-shellscript; charset="us-ascii"

    #!/bin/bash
    install -d -m 0755 /etc/containerd/conf.d

    --GPUSANDBOX
    Content-Type: text/x-shellscript; charset="us-ascii"

    @@include infra/eks/node-guard.sh@@
    --GPUSANDBOX--
---
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: sandbox-kata-cpu
spec:
  role: ${KARPENTER_NODE_ROLE}
  amiSelectorTerms:
    - alias: al2023@latest
  # /dev/kvm on a virtual instance: EC2 nested virtualization (C/M/R 7i and 8i style families).
  cpuOptions:
    nestedVirtualization: enabled
  subnetSelectorTerms:
    - tags: {karpenter.sh/discovery: "${CLUSTER_NAME}"}
  securityGroupSelectorTerms:
    - tags: {karpenter.sh/discovery: "${CLUSTER_NAME}"}
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs: {volumeSize: 100Gi, volumeType: gp3, encrypted: true, deleteOnTermination: true}
  userData: |
    MIME-Version: 1.0
    Content-Type: multipart/mixed; boundary="GPUSANDBOX"

    --GPUSANDBOX
    Content-Type: application/node.eks.aws

    apiVersion: node.eks.aws/v1alpha1
    kind: NodeConfig
    spec:
      containerd:
        config: |
          imports = ["/etc/containerd/conf.d/*.toml"]

    --GPUSANDBOX
    Content-Type: text/x-shellscript; charset="us-ascii"

    #!/bin/bash
    install -d -m 0755 /etc/containerd/conf.d

    --GPUSANDBOX
    Content-Type: text/x-shellscript; charset="us-ascii"

    @@include infra/eks/node-guard.sh@@
    --GPUSANDBOX--
---
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: trainer
spec:
  role: ${KARPENTER_NODE_ROLE}
  amiSelectorTerms:
    - alias: al2023@latest
  subnetSelectorTerms:
    - tags: {karpenter.sh/discovery: "${CLUSTER_NAME}"}
  securityGroupSelectorTerms:
    - tags: {karpenter.sh/discovery: "${CLUSTER_NAME}"}
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs: {volumeSize: 500Gi, volumeType: gp3, encrypted: true, deleteOnTermination: true}
