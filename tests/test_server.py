"""The tools: deny runs before the body, writes take two calls."""

import pytest

import policy
import server


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "AUDIT_LOG", tmp_path / "audit.log")
    monkeypatch.setattr(policy, "GRANTED", {"kb.read", "status.read", "kb.write"})
    monkeypatch.setattr(server, "_KB", dict(server._KB))
    monkeypatch.setattr(server, "_PENDING", {})


def token_from(reply: str) -> str:
    return reply.split("token='")[1].split("'")[0]


def test_read_tools_work():
    assert "runbooks" in server.search_knowledge("runbooks")
    assert server.get_status().startswith("ok")


def test_propose_does_not_change_anything():
    server.propose_write("notes", "hello")
    assert "notes" not in server._KB


def test_confirm_applies_the_staged_change():
    token = token_from(server.propose_write("notes", "hello"))
    server.confirm_write(token)
    assert server._KB["notes"] == "hello"


def test_token_works_once():
    token = token_from(server.propose_write("notes", "hello"))
    server.confirm_write(token)
    assert server.confirm_write(token).startswith("unknown token")


def test_write_tools_fail_closed_without_grant(monkeypatch):
    monkeypatch.setattr(policy, "GRANTED", {"kb.read"})
    with pytest.raises(policy.Denied):
        server.propose_write("notes", "hello")
    with pytest.raises(policy.Denied):
        server.confirm_write("any")
    assert "notes" not in server._KB


def test_same_grant_can_propose_and_confirm():
    # Documented limit: nothing proves the second call came from a human.
    token = token_from(server.propose_write("notes", "x"))
    assert server.confirm_write(token).startswith("applied")
