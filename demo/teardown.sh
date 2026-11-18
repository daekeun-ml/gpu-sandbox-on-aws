#!/usr/bin/env bash
# Remove the replay demo: empty the bucket, then delete the CloudFormation stack.
set -euo pipefail

AWS_REGION="us-east-1"   # where demo/deploy.sh creates the stack
STACK="${DEMO_STACK_NAME:-gpu-sandbox-demo}"

read -r -p "Delete demo stack ${STACK} and all files in its bucket? Type '${STACK}': " answer
[[ "${answer}" == "${STACK}" ]] || { echo "aborted"; exit 1; }

output() {
  aws cloudformation describe-stacks --region "${AWS_REGION}" --stack-name "${STACK}" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}
bucket="$(output BucketName)"
logs="$(output LogBucketName)"
aws s3 rm "s3://${bucket}" --recursive --region "${AWS_REGION}"
aws cloudformation delete-stack --region "${AWS_REGION}" --stack-name "${STACK}"
aws cloudformation wait stack-delete-complete --region "${AWS_REGION}" --stack-name "${STACK}"
echo "deleted ${STACK}"
# The access log bucket has DeletionPolicy Retain so the logs stay available for review.
echo "kept the access log bucket ${logs}; when you no longer need the logs: aws s3 rb s3://${logs} --force"
