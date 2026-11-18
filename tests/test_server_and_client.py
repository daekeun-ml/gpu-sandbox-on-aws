"""Server, auth and client end to end on loopback (CPU)."""

import json
import time

import httpx
import pytest

from gpusandbox.auth import AuthConfig
from gpusandbox.client import RoutingTable, SandboxClient
from gpusandbox.rewards import KernelRewards
from tests.conftest import CORRECT_RELU_BIAS, WRONG_RELU_BIAS, ServerThread, free_port

pytestmark = pytest.mark.slow

ISSUER = "https://oidc.example.test/id/TEST"
AUDIENCE = "gpu-sandbox"
TRAINER = "system:serviceaccount:rl-trainer:grpo-trainer"


@pytest.fixture
def signing_material(tmp_path):
    """A throwaway RSA key and its JWKS, standing in for the cluster's ServiceAccount issuer."""
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    jwk.update(kid="test-key", alg="RS256", use="sig")
    jwks_file = tmp_path / "jwks.json"
    jwks_file.write_text(json.dumps({"keys": [jwk]}))

    def mint(sub=TRAINER, aud=AUDIENCE, ttl=600):
        now = int(time.time())
        claims = {"iss": ISSUER, "sub": sub, "aud": [aud], "iat": now, "nbf": now, "exp": now + ttl}
        return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "test-key"})

    return jwks_file, mint


def test_auth_is_fail_closed_and_checks_audience_and_subject(cpu_settings, signing_material):
    from gpusandbox.server.app import create_app

    jwks_file, mint = signing_material
    unconfigured = AuthConfig(audience="", issuer="", allowed_subjects=frozenset(), jwks_file=None)
    configured = AuthConfig(
        audience=AUDIENCE, issuer=ISSUER, allowed_subjects=frozenset({TRAINER}), jwks_file=jwks_file
    )
    port_a, port_b = free_port(), free_port()
    with ServerThread(create_app(cpu_settings, unconfigured), port_a), ServerThread(
        create_app(cpu_settings, configured), port_b
    ):
        # Unconfigured auth rejects even a well-formed token.
        r = httpx.get(f"http://127.0.0.1:{port_a}/info", headers={"Authorization": f"Bearer {mint()}"})
        assert r.status_code == 401

        base = f"http://127.0.0.1:{port_b}"
        assert httpx.get(f"{base}/info").status_code == 401
        assert httpx.get(f"{base}/info").headers.get("www-authenticate") == "Bearer"
        assert httpx.get(f"{base}/info", headers={"Authorization": f"Bearer {mint(aud='kubernetes')}"}).status_code == 401
        assert httpx.get(f"{base}/info", headers={"Authorization": f"Bearer {mint(ttl=-120)}"}).status_code == 401
        other = "system:serviceaccount:default:default"
        assert httpx.get(f"{base}/info", headers={"Authorization": f"Bearer {mint(sub=other)}"}).status_code == 403
        ok = httpx.get(f"{base}/info", headers={"Authorization": f"Bearer {mint()}"})
        assert ok.status_code == 200 and ok.json()["runtime"] == "local"
        # Probes stay open for kubelet and reveal nothing.
        assert httpx.get(f"{base}/healthz").json() == {"status": "alive"}


def test_client_rewards_end_to_end_over_two_pods(sandbox_servers, tmp_path):
    routing = RoutingTable(
        document={
            "active": {"runtime": "local", "version": "v1"},
            "pools": {"local": {"v1": ",".join(sandbox_servers)}},
        }
    )
    client = SandboxClient(routing)
    rewards = KernelRewards(client, require_triton=False, metrics_file=tmp_path / "m.jsonl")
    codes = [CORRECT_RELU_BIAS, WRONG_RELU_BIAS, CORRECT_RELU_BIAS + "\n# variant\n"]
    completions = [[{"role": "assistant", "content": f"```python\n{c}\n```"}] for c in codes]
    prompts = [[{"role": "user", "content": "p"}]] * len(codes)
    scores = rewards.correctness_reward(prompts, completions, task_id=["relu_bias"] * len(codes))
    assert scores == [1.0, 0.2, 1.0]

    record = json.loads((tmp_path / "m.jsonl").read_text().splitlines()[0])
    assert record["status"] == {"ok": 2, "wrong_answer": 1}
    assert record["served_versions"] == {"test": 3}


def test_busy_pod_returns_503(sandbox_servers):
    # The lock is per pod: while one evaluation runs, a second request must be refused.
    import concurrent.futures

    url = f"http://{sandbox_servers[0]}/v1/evaluate"
    body = {"task_id": "relu_bias", "code": CORRECT_RELU_BIAS}
    with concurrent.futures.ThreadPoolExecutor(4) as ex:
        codes = list(ex.map(lambda _: httpx.post(url, json=body, timeout=120).status_code, range(4)))
    assert 200 in codes and 503 in codes


def test_readiness_requires_verified_egress_denial(cpu_settings, bypass_auth):
    """A reachable probe target keeps the pod out of service; an unroutable one lets it in."""
    import socket
    from dataclasses import replace

    from gpusandbox.server.app import create_app

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    open_target = f"127.0.0.1:{listener.getsockname()[1]}"
    try:
        leaky = replace(cpu_settings, egress_probe_targets=(open_target,))
        sealed = replace(cpu_settings, egress_probe_targets=("10.255.255.1:9",))
        port_a, port_b = free_port(), free_port()
        with ServerThread(create_app(leaky, bypass_auth), port_a), ServerThread(
            create_app(sealed, bypass_auth), port_b
        ):
            deadline = time.time() + 20
            while time.time() < deadline:
                if httpx.get(f"http://127.0.0.1:{port_b}/readyz").status_code == 200:
                    break
                time.sleep(0.5)
            assert httpx.get(f"http://127.0.0.1:{port_b}/readyz").status_code == 200
            assert httpx.get(f"http://127.0.0.1:{port_a}/readyz").status_code == 503
            info = httpx.get(f"http://127.0.0.1:{port_a}/info").json()
            assert info["egress_blocked"] is False and open_target in info["egress_open_targets"][0]
    finally:
        listener.close()


def test_golden_probe_and_parity_on_cpu_pools(sandbox_servers, capsys):
    """The operator tools pass on two healthy pools and catch a behaviour change."""
    import asyncio

    from gpusandbox import tools

    address = ",".join(sandbox_servers)
    # Egress self-test is off in the CPU fixture, so /info reports egress_blocked=True.
    assert asyncio.run(tools.probe(address, "cpu")) == 0
    assert asyncio.run(tools.parity(sandbox_servers[0], sandbox_servers[1], "cpu", 10.0)) == 0
    out = capsys.readouterr().out
    assert "FAIL" not in out and '"passed": true' in out


def test_simulate_reports_a_version_switch_between_batches(sandbox_servers, tmp_path, monkeypatch, capsys):
    """Scenario C: the reward loop without a model sees a routing change at a batch boundary."""
    from gpusandbox import tools
    from gpusandbox.golden import golden_for

    routing_file = tmp_path / "routing.json"

    def write(version: str) -> None:
        routing_file.write_text(json.dumps({
            "active": {"runtime": "local", "version": version},
            "pools": {"local": {"v1": sandbox_servers[0], "v2": sandbox_servers[1]}},
        }))

    write("v1")
    # The pause between batches is where an operator would run scripts/ops/rollout.sh.
    monkeypatch.setattr(tools.time, "sleep", lambda _s: write("v2"))
    table = RoutingTable(routing_file, min_reload_interval_s=0)
    assert tools.simulate(steps=2, interval_s=0, device="cpu", routing=table) == 0

    events = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    assert events[0]["event"] == "simulate" and "not training" in events[0]["note"]
    batches = [e for e in events if e["event"] == "reward_batch"]
    switches = [e for e in events if e["event"] == "sandbox_version_switch"]
    assert [b["version"] for b in batches] == ["v1", "v2"]
    assert [b["global_step"] for b in batches] == [1, 2]
    assert switches == [{**switches[0], "from": "local/v1", "to": "local/v2", "global_step": 2}]
    # Policy violations are judged locally; every other golden reaches the sandbox.
    sent = [g for g in golden_for("cpu") if g.expect_status != "policy_violation"]
    assert batches[0]["n"] == len(sent)
    assert batches[0]["status"].get("ok", 0) == sum(g.expect_status == "ok" for g in sent)


def test_gateway_pins_groups_across_a_routing_switch(sandbox_servers, tmp_path, monkeypatch):
    """Samples of one group stay on the version that scored the group's first sample."""
    import os as _os

    from gpusandbox.gateway import app as gw

    routing_file = tmp_path / "routing.json"

    def write(version):
        routing_file.write_text(json.dumps({
            "active": {"runtime": "local", "version": version},
            "pools": {"local": {"v1": sandbox_servers[0], "v2": sandbox_servers[1]}},
        }))
        _os.utime(routing_file, (time.time() + 5, time.time() + 5))

    write("v1")
    monkeypatch.setenv("GATEWAY_ROUTING_FILE", str(routing_file))
    monkeypatch.setenv("GATEWAY_RECYCLE_PODS", "0")
    monkeypatch.setattr(gw.TokenReviewVerifier, "verify", lambda self, h: "system:serviceaccount:t:t")
    port = free_port()
    with ServerThread(gw.create_app(), port):
        base = f"http://127.0.0.1:{port}"
        item = {"task_id": "relu_bias", "code": CORRECT_RELU_BIAS}
        first = httpx.post(f"{base}/v1/evaluate", json={**item, "group_key": "g1"}, timeout=120).json()
        write("v2")
        time.sleep(2.5)  # RoutingTable re-reads at most every 2 s
        same_group = httpx.post(f"{base}/v1/evaluate", json={**item, "group_key": "g1"}, timeout=120).json()
        new_group = httpx.post(f"{base}/v1/evaluate", json={**item, "group_key": "g2"}, timeout=120).json()
        batch = httpx.post(f"{base}/v1/evaluate_batch", json={"items": [item, item]}, timeout=120).json()
    assert first["endpoint"] == sandbox_servers[0] and first["routing_revision"] == 1
    assert same_group["endpoint"] == sandbox_servers[0], "group g1 must stay on v1"
    assert new_group["endpoint"] == sandbox_servers[1]
    assert batch["version"] == "v2" and {r["endpoint"] for r in batch["results"]} == {sandbox_servers[1]}
