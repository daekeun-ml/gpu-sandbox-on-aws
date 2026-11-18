#!/usr/bin/env python3
"""cdk deploy entry point. Run through cdk/deploy.sh, which exports scripts/config.env."""

import os

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from gpusandbox_cdk.config import Settings
from gpusandbox_cdk.stack import GpuSandboxStack

settings = Settings.from_env()
app = cdk.App()
GpuSandboxStack(
    app, f"{settings.cluster_name}-cdk",
    settings=settings,
    env=cdk.Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
                        region=os.environ.get("AWS_REGION") or os.environ.get("CDK_DEFAULT_REGION")),
    description="GPU sandbox on AWS: EKS infrastructure (private API endpoint)",
)
# Security checks run on every synth; unsuppressed findings fail the deploy.
cdk.Validations.of(app).add_plugins(AwsSolutionsChecks(app, verbose=True))
app.synth()
