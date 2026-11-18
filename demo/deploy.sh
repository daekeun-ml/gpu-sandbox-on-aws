#!/usr/bin/env bash
# Deploy the replay demo: private S3 bucket + CloudFront (OAC), then upload the static site.
#   demo/deploy.sh                       uses demo/site/data/recording.json as is
#   RECORDING=path/to/rec.json demo/deploy.sh   publish another recording
# Optional: DEMO_DOMAIN and DEMO_CERT_ARN (ACM, us-east-1) for a custom domain with TLS 1.2+.
#
# The demo is public by design (anyone with the URL can view it) and contains only the
# recording and static files. Review the recording before publishing: it is shown verbatim.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# us-east-1 only: the WAF web ACL for CloudFront and the CloudFront log delivery live there
# (see Rules in demo/infra/site.yaml). CloudFront itself is global.
AWS_REGION="us-east-1"
STACK="${DEMO_STACK_NAME:-gpu-sandbox-demo}"
SITE="${REPO_ROOT}/demo/site"
RECORDING="${RECORDING:-${SITE}/data/recording.json}"

python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['schema'] == 1 and d['pools']" "${RECORDING}"

echo "[demo] deploying stack ${STACK} in ${AWS_REGION}"
aws cloudformation deploy --region "${AWS_REGION}" --stack-name "${STACK}" \
  --template-file "${REPO_ROOT}/demo/infra/site.yaml" \
  --parameter-overrides "AliasDomain=${DEMO_DOMAIN:-}" "AcmCertificateArn=${DEMO_CERT_ARN:-}" \
  --no-fail-on-empty-changeset

output() {
  aws cloudformation describe-stacks --region "${AWS_REGION}" --stack-name "${STACK}" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}
bucket="$(output BucketName)"
distribution="$(output DistributionId)"
domain="$(output DistributionDomainName)"

echo "[demo] uploading site to s3://${bucket}"
aws s3 sync "${SITE}" "s3://${bucket}" --delete --exclude "data/*" --region "${AWS_REGION}"
aws s3 cp "${RECORDING}" "s3://${bucket}/data/recording.json" --region "${AWS_REGION}" \
  --content-type application/json --cache-control "no-cache"
aws cloudfront create-invalidation --distribution-id "${distribution}" --paths "/*" >/dev/null

echo "[demo] checking that the distribution has the WAF web ACL"
waf="$(aws cloudfront get-distribution-config --id "${distribution}" --query 'DistributionConfig.WebACLId' --output text)"
if [[ "${waf}" != arn:* ]]; then
  echo "[demo] ERROR: no WAF web ACL on ${distribution}. Fix before sharing." >&2
  exit 1
fi
echo "[demo] checking that the bucket itself is not readable anonymously"
direct="$(curl -s -o /dev/null -w '%{http_code}' "https://${bucket}.s3.${AWS_REGION}.amazonaws.com/index.html")"
if [[ "${direct}" != "403" ]]; then
  echo "[demo] ERROR: direct S3 access returned ${direct}, expected 403. Fix before sharing." >&2
  exit 1
fi

echo "[demo] checking the public URL and its security headers (the distribution may take minutes)"
url="https://${DEMO_DOMAIN:-${domain}}/"
for _ in $(seq 1 30); do
  code="$(curl -s -o /dev/null -w '%{http_code}' "${url}")"
  [[ "${code}" == "200" ]] && break
  sleep 20
done
headers="$(curl -sI "${url}")"
grep -qi '^content-security-policy:' <<<"${headers}" || { echo "[demo] ERROR: CSP header missing" >&2; exit 1; }
grep -qi '^strict-transport-security:' <<<"${headers}" || { echo "[demo] ERROR: HSTS header missing" >&2; exit 1; }
plain="$(curl -s -o /dev/null -w '%{http_code}' "http://${DEMO_DOMAIN:-${domain}}/")"
[[ "${plain}" == "301" ]] || { echo "[demo] ERROR: http:// returned ${plain}, expected a 301 redirect to https" >&2; exit 1; }
echo "[demo] live: ${url}"
