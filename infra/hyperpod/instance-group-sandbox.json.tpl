{
  "InstanceGroupName": "sandbox",
  "InstanceType": "${HYPERPOD_SANDBOX_INSTANCE_TYPE}",
  "InstanceCount": ${HYPERPOD_SANDBOX_COUNT},
  "ImageId": "${HYPERPOD_B2_AMI_ID}",
  "LifeCycleConfig": {
    "SourceS3Uri": "s3://${HYPERPOD_LCS_BUCKET}/lifecycle/",
    "OnCreate": "on_create_sandbox.sh"
  },
  "ExecutionRole": "${HYPERPOD_EXECUTION_ROLE_ARN}",
  "ThreadsPerCore": 2,
  "KubernetesConfig": {
    "Labels": {"gpusandbox/role": "sandbox-hyperpod", "gpusandbox/device-plugin": "cdi"},
    "Taints": [{"Key": "gpusandbox/role", "Value": "sandbox-hyperpod", "Effect": "NoSchedule"}]
  }
}
