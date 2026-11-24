---
hide:
  - footer
---

# B1의 HyperPod 학습 노드 연결하기

EC2 채점 노드에서 CUDA 검사를 마쳤으면 EKS 터널을 열어 둔 채 학습 노드를 연결하세요.


HyperPod 클러스터를 만들고 EKS 클러스터에 연결합니다. 이 단계부터 HyperPod 인스턴스 요금이 발생합니다.

```bash
scripts/hyperpod/create.sh
```

<details class="note" markdown="1">
<summary>스크립트가 준비하는 IAM 역할, 버킷, 애드온</summary>

| 단계 | 하는 일 | 이유 |
|---|---|---|
| 1 dependency chart | `aws/sagemaker-hyperpod-cli`를 clone하고 `helm_chart/HyperPodHelmChart`를 `hyperpod-dependencies`라는 이름으로 `kube-system`에 설치 | API로 HyperPod를 만들 때 필요합니다 |
| 2 lifecycle bucket | `HYPERPOD_LCS_BUCKET`이 없으면 만들고, Block Public Access 네 가지(`BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets`)를 모두 켠 뒤 `infra/hyperpod/lifecycle/`을 올림 | lifecycle script는 노드가 만들어질 때 실행되어 노드 설정을 바꿀 수 있으므로 공개되면 안 됩니다 |
| 3 execution role | `${HYPERPOD_CLUSTER_NAME}-execution`: `sagemaker.amazonaws.com` 신뢰, `AmazonSageMakerClusterInstanceRolePolicy` + inline `hyperpod-eks`(EC2 ENI, ECR pull) + inline `lifecycle-bucket-read` | HyperPod 노드용 역할은 EKS 노드 역할과 따로 둡니다 |
| 4 CreateCluster | `Orchestrator.Eks.ClusterArn`, 인스턴스 그룹 `trainer`, EKS 클러스터 보안 그룹과 private subnet, `NodeRecovery: Automatic`으로 만듦. 생성 중에는 30초 간격으로 조회하고 실패 사유가 있으면 출력한 뒤 종료 | HyperPod 노드, EC2 노드, control plane이 같은 보안 그룹을 써서 서로 통신합니다 |
| 5 training operator | trainer 노드가 `Schedulable`이고 `Ready`가 될 때까지 기다린 뒤 `aws eks create-addon --addon-name amazon-sagemaker-hyperpod-training-operator` 뒤 `addon-active` 대기 | HyperPodPyTorchJob CRD와 controller를 설치합니다 |

- **1단계 dependency chart의 기본값**: main 브랜치 values 기준으로 health monitoring agent, deep health check, job auto-restart, MPI operator, NVIDIA, EFA, Neuron device plugin이 기본으로 켜집니다.
- **4단계의 인스턴스 그룹 `trainer`**: `ml.g5.2xlarge` 1대, `ThreadsPerCore` 2(vCPU 8개), `OnCreate` `on_create.sh`입니다. Worker는 CPU 5개, 메모리 24 GiB, GPU 1개를 요청합니다. 이 노드에서 operator, job별 pod manager, 그 밖의 시스템 pod가 요청한 CPU의 합은 2.75개였습니다.
- **4단계의 private subnet**: CDK 스택이 추가한 `kubernetes.io/role/internal-elb=1` 태그로 찾습니다.

</details>

**확인할 것:**

- 4단계에서 `waiting for InService (15-30 min)` 뒤에 클러스터 상태가 출력됩니다. `status`가 `InService`이고 `failure`가 비어 있어야 합니다.
- 마지막 `kubectl get nodes` 표에서 instance type이 `ml.g5.2xlarge`인 노드의 `node-health-status`가 `Schedulable`입니다. 출력은 대략 다음 형태입니다(예시).

```text
NAME              STATUS   ROLES    AGE   VERSION   NODE-HEALTH-STATUS   INSTANCE-TYPE
<ec2-node>        Ready    <none>   40m   v1.36.x                        g5.xlarge
<hyperpod-node>   Ready    <none>   5m    v1.36.x   Schedulable          ml.g5.2xlarge
```

??? note "버킷 이름의 `sagemaker-` 접두사"
    버킷 이름에 `sagemaker-` 접두사를 붙이는 것은 HyperPod 관리형 정책이 이 접두사를 전제로 한다는 `config.env.example` 주석을 따른 것입니다. 버킷 읽기 권한은 별도의 inline 정책이 부여합니다.

`cluster.json.tpl`은 deep health check(`OnStartDeepHealthChecks`: `InstanceStress`, `InstanceConnectivity` 등)를 설정하지 않으니, 필요하면 인스턴스 그룹에 직접 추가하세요.

??? note "Training operator 권한"
    B1의 CDK 스택은 `cert-manager`와 `eks-pod-identity-agent`를 설치하고 `aws-hyperpod/hp-training-operator-controller-manager` 서비스 계정에 IAM 역할을 연결합니다. `create.sh`는 HyperPod 클러스터에 `SageMaker=true` 태그를 붙입니다. 역할의 `AmazonSageMakerHyperPodTrainingOperatorAccess` 정책은 이 태그가 있어야 `DescribeClusterNode`를 허용합니다.

<details class="note" markdown="1">
<summary>training operator 설치만 실패했을 때</summary>

스크립트를 다시 실행하면 단계마다 다르게 동작합니다.

- **다시 적용하는 것**: 1단계의 Helm chart 설치와 2단계의 Block Public Access 설정, lifecycle 파일 업로드
- **없을 때만 실행하는 것**: 버킷 생성은 버킷이 없을 때만, 3단계의 역할 생성과 정책 연결은 역할이 없을 때만 실행합니다.
- **4단계의 `create-cluster`**: 같은 이름의 클러스터가 이미 있으면 실패할 것으로 봅니다(추론).

그래서 5단계만 실패했다면 스크립트를 다시 실행하지 말고, 전제조건을 준비한 뒤 다음 두 명령만 실행하세요.

```bash
source scripts/config.env
aws eks create-addon --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
  --addon-name amazon-sagemaker-hyperpod-training-operator
aws eks wait addon-active --region "$AWS_REGION" --cluster-name "$CLUSTER_NAME" \
  --addon-name amazon-sagemaker-hyperpod-training-operator
```

**확인할 것:** 둘째 명령이 오류 없이 끝납니다. add-on이 이미 있다는 오류가 나오면 첫 명령은 건너뛰고 둘째 명령만 실행하세요.

</details>

**문제가 생기면:** 상태가 `Failed`이거나 노드가 `Schedulable`이 되지 않으면 [문제 해결](../../../reference/troubleshooting.md)의 "HyperPod" 항목을 보세요.


trainer가 `Schedulable`이고 오퍼레이터가 `ACTIVE`이면 [03의 B1 탭](../03_pools/index.md#__tabbed_1_2)에서 EC2 채점 pool을 배포하세요.
