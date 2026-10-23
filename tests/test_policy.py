"""The policy gate: default-deny, and both paths audited."""

import json

import pytest

import policy


@pytest.fixture(autouse=True)
def audit_log(tmp_path, monkeypatch):
    log = tmp_path / "audit.log"
    monkeypatch.setattr(policy, "AUDIT_LOG", log)
    monkeypatch.setattr(policy, "GRANTED", {"kb.read"})
    return log


def records(log):
    return [json.loads(line) for line in log.read_text().splitlines()]


def test_granted_capability_passes_and_is_audited(audit_log):
    policy.require("kb.read")
    last = records(audit_log)[-1]
    assert last["event"] == "granted"
    assert last["capability"] == "kb.read"


def test_ungranted_capability_is_denied_and_audited(audit_log):
    with pytest.raises(policy.Denied):
        policy.require("kb.write")
    assert records(audit_log)[-1]["event"] == "denied"
    assert records(audit_log)[-1]["capability"] == "kb.write"


def test_unknown_capability_is_denied(audit_log):
    with pytest.raises(policy.Denied):
        policy.require("anything.else")


def test_audit_write_failure_does_not_raise(monkeypatch, tmp_path):
    # Documented limit: if the log cannot be written, the call still runs.
    monkeypatch.setattr(policy, "AUDIT_LOG", tmp_path / "missing-dir" / "audit.log")
    policy.require("kb.read")
