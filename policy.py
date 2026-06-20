"""Least-privilege policy + audit for an MCP agent's tools.

Each tool declares the capability it needs. The agent is granted a *set* of
capabilities; a call to a tool whose capability is not granted is denied
**before** the tool runs (default-deny). Every attempt — allowed or denied —
is written to an append-only audit log.

This is the enforcement layer behind the rule "no agent does more than it was
scoped to," kept deliberately small so it is easy to read and audit.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

AUDIT_LOG = Path(os.environ.get("AGENT_AUDIT_LOG", "audit.log"))

# Capabilities granted to THIS agent. Tighten per deployment / per agent.
# A production platform would load these from the agent's identity, not a const.
GRANTED: set[str] = {"kb.read", "status.read", "kb.write"}


class Denied(Exception):
    """Raised when a tool requires a capability the agent was not granted."""


def audit(event: str, **fields) -> None:
    """Append one structured record to the audit log. Never raises."""
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **fields,
    }
    try:
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError:
        # Auditing must not take down the tool; surface elsewhere in prod.
        pass


def require(capability: str) -> None:
    """Default-deny capability check. Raises ``Denied`` if not granted.

    Call this as the first line of every tool. The deny path is audited too,
    so an agent probing for capabilities it lacks leaves a trail.
    """
    if capability not in GRANTED:
        audit("denied", capability=capability)
        raise Denied(f"capability {capability!r} not granted to this agent")
    audit("granted", capability=capability)
