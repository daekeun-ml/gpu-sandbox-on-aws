{
  "ClusterName": "${HYPERPOD_CLUSTER_NAME}",
  "Orchestrator": {"Eks": {"ClusterArn": "${EKS_CLUSTER_ARN}"}},
  "InstanceGroups": [
    {
      "InstanceGroupName": "trainer",
      "InstanceType": "${HYPERPOD_TRAINER_INSTANCE_TYPE}",
      "InstanceCount": 1,
      "LifeCycleConfig": {
        "SourceS3Uri": "s3://${HYPERPOD_LCS_BUCKET}/lifecycle/",
        "OnCreate": "on_create.sh"
      },
      "ExecutionRole": "${HYPERPOD_EXECUTION_ROLE_ARN}",
      "ThreadsPerCore": 1
    }
  ],
  "VpcConfig": {
    "SecurityGroupIds": ["${HYPERPOD_SECURITY_GROUP_ID}"],
    "Subnets": ["${HYPERPOD_SUBNET_ID}"]
  },
  "NodeRecovery": "Automatic"
}
