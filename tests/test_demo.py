"""Replay demo: static-site safety, recording schema and the CloudFront template's guarantees."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
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
    for page in ("index.html", "architecture.html"):
        html = (SITE / page).read_text()
        for tag in re.findall(r"<(?:script|link)[^>]*>", html):
            assert "http" not in tag, f"external resource in {page}: {tag}"
    for script in ("app.js", "arch.js"):
        js = (SITE / script).read_text()
        for banned in ("innerHTML", "outerHTML", "insertAdjacentHTML", "eval(", "new Function", "document.write"):
            assert banned not in js, (script, banned)
    js = (SITE / "app.js").read_text()
    assert "fetch(" not in (SITE / "arch.js").read_text(), "the patterns page uses only its own static data"
    # The architecture icons are plain images: no script, no event handlers, no external references.
    for icon in (SITE / "icons").glob("*.svg"):
        text = icon.read_text()
        assert not re.search(r"<script|\son\w+=|href=\"(?:https?:)?//", text), icon.name
    assert re.findall(r"fetch\(\"([^\"]+)\"", js) == ["data/recording.json", "data/extras.json"], "same-origin fetch only"
    assert "media-src 'self'" in _template()["Resources"]["SecurityHeaders"]["Properties"][
        "ResponseHeadersPolicyConfig"]["SecurityHeadersConfig"]["ContentSecurityPolicy"]["ContentSecurityPolicy"]


RECORDINGS = [SITE / "data/recording.json", *sorted((ROOT / "demo/recordings").glob("*.json"))]


@pytest.mark.parametrize("path", RECORDINGS, ids=lambda p: p.name)
def test_recording_schema_and_reward_consistency(path):
    from gpusandbox.golden import GOLDEN_SET
    from gpusandbox.rewards import score_verdict

    rec = json.loads(path.read_text())
    assert rec["schema"] == 1 and rec["pools"] and rec["goldens"]
    codes = {g.name: g.code for g in GOLDEN_SET}
    for pool in rec["pools"]:
        for name, verdict in pool["results"].items():
            assert verdict["status"] == verdict["expected_status"], (pool["runtime"], name)
            # The demo must show exactly what the trainer would compute.
            assert verdict["reward"] == score_verdict(verdict, codes[name])
    if path.parent == SITE / "data":
        assert any(e["event"] == "sandbox_version_switch" for e in rec["training"])


def _build_extras():
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_extras", ROOT / "demo/build_extras.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("path", [*RECORDINGS, SITE / "data/extras.json"], ids=lambda p: p.name)
def test_published_data_has_no_addresses_names_or_secrets(path):
    assert _build_extras().problems(json.loads(path.read_text())) == []


def test_redaction_masks_cluster_details_but_keeps_imds():
    redact = _build_extras().redact
    line = "\x1b[1;34m[13:37:44]\x1b[0m kubelet 10.0.50.127:10250 on ip-10-0-50-127.us-west-2.compute.internal"
    out = redact(line)
    assert "10.0.50.127" not in out and "compute.internal" not in out and "\x1b" not in out
    assert "<private-ip>:10250" in out and "<node>" in out
    assert redact("169.254.169.254:80 blocked") == "169.254.169.254:80 blocked"
    assert redact("52.92.152.216:443") == "<public-ip>:443"
    assert "123456789012" not in redact("123456789012.dkr.ecr.us-west-2.amazonaws.com/gpu-sandbox/sandbox")
    assert redact("arn:aws:iam::123456789012:role/x") == "<arn>"
    assert redact("Trying 10.0.12.34...") == "Trying <private-ip>..."
    assert redact("fe80::1ff:fe23:4567:890a dev eth0") == "<ipv6> dev eth0"
    assert redact("[13:37:42] 1) kernel") == "[13:37:42] 1) kernel"
    assert redact("10-0-12-34.sandbox.pod.cluster.local").startswith("<private-ip>.")
    assert redact("https://0123456789ABCDEF0123456789ABCDEF.gr7.us-west-2.eks.amazonaws.com") == "https://<aws-endpoint>"
    assert redact("rtb-0abc12345def67890 hf_abcdefghijklmnopqrstuvwxyz") == "<resource-id> <token>"
    problems = _build_extras().problems
    assert problems(["[alice@build-box ~]$ ls"]) and problems(["/root/.cache"]), "fail closed on what it cannot mask"


def test_waf_limits_video_downloads_per_ip():
    rules = {r["Name"]: r for r in _template()["Resources"]["WebAcl"]["Properties"]["Rules"]}
    media = rules["rate-limit-media-per-ip"]["Statement"]["RateBasedStatement"]
    assert media["AggregateKeyType"] == "IP" and media["Limit"] <= 100
    assert media["ScopeDownStatement"]["ByteMatchStatement"]["SearchString"] == "/media/"
    assert len({r["Priority"] for r in rules.values()}) == len(rules)
    deploy = (ROOT / "demo/deploy.sh").read_text()
    assert '--exclude "*"' in deploy and "build_extras.py\" --check" in deploy
    assert '--include "icons/*.svg"' in deploy and '--include "architecture.html"' in deploy


def test_extras_sections_parse_from_cluster_logs():
    extras = json.loads((SITE / "data/extras.json").read_text())
    assert extras["schema"] == "extras-1"
    # The public replay and the guide show the same B1 client placements and observations.
    b1 = json.loads((ROOT / "docs/handson/data/hyperpod-b1.json").read_text())
    assert extras["b1"] == b1
    assert [r["client"] for r in b1["bench"]["rows"]] == ["system", "hyperpod"]
    assert all(r["runtime"] == "gvisor" and r["ok"] == r["requests"] for r in b1["bench"]["rows"])
    assert len(b1["training"]["batches"]) == len(b1["training"]["steps"]) == 1
    passes = {p["label"]: p["rows"] for p in extras["bench"]["passes"]}
    assert all(r["ok"] == r["requests"] for rows in passes.values() for r in rows)
    assert all(r["cold_start_s"] for rows in passes.values() for r in rows)
    training = extras["training"]
    assert training["batches"] and len(training["steps"]) == len(training["batches"])
    assert any(e["event"] == "sandbox_version_switch" for e in extras["simulation"]["events"])
    ids = {t["id"] for t in extras["transcripts"]}
    assert {"verify-gvisor", "verify-kata-qemu"} <= ids
    for transcript in extras["transcripts"]:
        times = [line["t"] for line in transcript["lines"]]
        assert times == sorted(times), transcript["id"]


def test_runtime_results_match_the_guide_record(tmp_path):
    data = ROOT / "docs/handson/data"
    metadata = data / "runtime-benchmark-2026-11-22.meta.json"
    output = tmp_path / "extras.json"
    assert _build_extras().main(["--runtime-record", str(metadata), "--out", str(output)]) == 0
    run = json.loads(output.read_text())["runtime_run"]
    assert run == json.loads((SITE / "data/extras.json").read_text())["runtime_run"]
    config = json.loads(metadata.read_text())
    originals = [json.loads(line) for line in (data / config["jsonl"]).read_text().splitlines()]
    assert len(run["rows"]) == len(originals) == len(config["pools"])
    for row, raw in zip(run["rows"], originals, strict=True):
        raw.pop("address")
        assert row == {**raw, **config["pools"][raw["runtime"]]}
