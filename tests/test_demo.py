"""Replay demo: static-site safety, recording schema and the CloudFront template's guarantees."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "demo/site"


class _CfnLoader(yaml.SafeLoader):
    pass


def _tag(loader, suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return {suffix: loader.construct_scalar(node)}
    if isinstance(node, yaml.SequenceNode):
        return {suffix: loader.construct_sequence(node, deep=True)}
    return {suffix: loader.construct_mapping(node, deep=True)}


_CfnLoader.add_multi_constructor("!", _tag)


def _template() -> dict:
    return yaml.load((ROOT / "demo/infra/site.yaml").read_text(), Loader=_CfnLoader)


def test_bucket_is_private_and_readable_only_by_this_distribution():
    res = _template()["Resources"]
    pab = res["SiteBucket"]["Properties"]["PublicAccessBlockConfiguration"]
    assert all(pab[k] is True for k in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"))
    statements = res["SiteBucketPolicy"]["Properties"]["PolicyDocument"]["Statement"]
    allow = [s for s in statements if s["Effect"] == "Allow"]
    assert len(allow) == 1 and allow[0]["Principal"] == {"Service": "cloudfront.amazonaws.com"}
    assert "AWS:SourceArn" in allow[0]["Condition"]["StringEquals"], "no unconditioned service grant"
    assert any(s["Effect"] == "Deny" and "aws:SecureTransport" in json.dumps(s) for s in statements)


def test_viewers_get_https_and_security_headers():
    res = _template()["Resources"]
    behavior = res["Distribution"]["Properties"]["DistributionConfig"]["DefaultCacheBehavior"]
    assert behavior["ViewerProtocolPolicy"] == "redirect-to-https"
    assert behavior["AllowedMethods"] == ["GET", "HEAD"]
    headers = res["SecurityHeaders"]["Properties"]["ResponseHeadersPolicyConfig"]["SecurityHeadersConfig"]
    csp = headers["ContentSecurityPolicy"]["ContentSecurityPolicy"]
    assert "default-src 'none'" in csp and "script-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert headers["StrictTransportSecurity"]["AccessControlMaxAgeSec"] >= 31536000


def test_site_loads_nothing_external_and_never_injects_html():
    html = (SITE / "index.html").read_text()
    for tag in re.findall(r"<(?:script|link)[^>]*>", html):
        assert "http" not in tag, f"external resource: {tag}"
    js = (SITE / "app.js").read_text()
    for banned in ("innerHTML", "outerHTML", "insertAdjacentHTML", "eval(", "new Function", "document.write"):
        assert banned not in js, banned
    assert re.findall(r"fetch\(\"([^\"]+)\"", js) == ["data/recording.json"], "same-origin fetch only"


def test_recording_schema_and_reward_consistency():
    from gpusandbox.golden import GOLDEN_SET
    from gpusandbox.rewards import score_verdict

    rec = json.loads((SITE / "data/recording.json").read_text())
    assert rec["schema"] == 1 and rec["pools"] and rec["goldens"]
    codes = {g.name: g.code for g in GOLDEN_SET}
    for pool in rec["pools"]:
        for name, verdict in pool["results"].items():
            assert verdict["status"] == verdict["expected_status"], (pool["runtime"], name)
            # The demo must show exactly what the trainer would compute.
            assert verdict["reward"] == score_verdict(verdict, codes[name])
    assert any(e["event"] == "sandbox_version_switch" for e in rec["training"])
