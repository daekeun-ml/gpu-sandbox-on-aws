"""Agent Sandbox extension: claim body, address resolution and the claim lifecycle."""

import pytest

from gpusandbox.agent_sandbox import EpisodeSandbox, claim_body, sandbox_address


def test_claim_body_targets_warm_pool_with_a_safety_shutdown():
    body = claim_body("episode-1", "kernel-eval-gvisor", max_lifetime_s=600, episode_labels={"run": "r1"})
    assert body["apiVersion"] == "extensions.agents.x-k8s.io/v1beta1"
    assert body["spec"]["warmPoolRef"] == {"name": "kernel-eval-gvisor"}
    assert body["spec"]["lifecycle"]["shutdownPolicy"] == "Delete"
    assert body["metadata"]["labels"] == {"gpusandbox/episode": "true", "run": "r1"}


def test_sandbox_address_waits_for_ready_and_prefers_service_fqdn():
    pending = {"status": {"conditions": [{"type": "Ready", "status": "False"}]}}
    assert sandbox_address(pending) is None
    ready = {"status": {"conditions": [{"type": "Ready", "status": "True"}],
                        "sandbox": {"name": "s1", "serviceFQDN": "s1.sandbox.svc.cluster.local", "podIPs": ["10.0.0.5"]}}}
    assert sandbox_address(ready) == "s1.sandbox.svc.cluster.local:8000"
    ready["status"]["sandbox"].pop("serviceFQDN")
    assert sandbox_address(ready) == "10.0.0.5:8000"


class FakeApi:
    def __init__(self, ready_after: int):
        self.ready_after = ready_after
        self.gets = 0
        self.created, self.deleted = [], []

    def create_namespaced_custom_object(self, group, version, ns, plural, body):
        self.created.append(body)

    def get_namespaced_custom_object(self, group, version, ns, plural, name):
        self.gets += 1
        status = "True" if self.gets >= self.ready_after else "False"
        return {"status": {"conditions": [{"type": "Ready", "status": status}],
                           "sandbox": {"name": "s1", "serviceFQDN": "s1.sandbox.svc.cluster.local"}}}

    def delete_namespaced_custom_object(self, group, version, ns, plural, name):
        self.deleted.append(name)


def test_episode_claims_then_releases(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    api = FakeApi(ready_after=3)
    with EpisodeSandbox("kernel-eval-gvisor", api=api) as episode:
        assert episode.address == "s1.sandbox.svc.cluster.local:8000"
        name = episode.name
    assert api.created[0]["metadata"]["name"] == name
    assert api.deleted == [name]


def test_episode_releases_the_claim_when_it_never_becomes_ready(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    api = FakeApi(ready_after=10**9)
    with pytest.raises(TimeoutError):
        with EpisodeSandbox("kernel-eval-gvisor", api=api, ready_timeout_s=0.01):
            pass
    assert len(api.deleted) == 1
