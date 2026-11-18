#!/usr/bin/env bash
# Remove the replay demo: empty the bucket, then delete the CloudFormation stack.
set -euo pipefail

AWS_REGION="${AWS_REGION:?set AWS_REGION}"
STACK="${DEMO_STACK_NAME:-gpu-sandbox-demo}"

read -r -p "Delete demo stack ${STACK} and all files in its bucket? Type '${STACK}': " answer
[[ "${answer}" == "${STACK}" ]] || { echo "aborted"; exit 1; }

bucket="$(aws cloudformation describe-stacks --region "${AWS_REGION}" --stack-name "${STACK}" \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)"
aws s3 rm "s3://${bucket}" --recursive --region "${AWS_REGION}"
aws cloudformation delete-stack --region "${AWS_REGION}" --stack-name "${STACK}"
aws cloudformation wait stack-delete-complete --region "${AWS_REGION}" --stack-name "${STACK}"
echo "deleted ${STACK}"
