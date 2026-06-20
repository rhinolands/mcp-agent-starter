"""mcp-agent-starter — a minimal MCP server with an enterprise security model.

Demonstrates three patterns every production agent platform needs, in code you
can read in one sitting:

  1. Per-agent least privilege   — tools declare a capability; default-deny.
  2. Audit                        — every tool call is logged append-only.
  3. Human-confirm gate on writes — a mutating tool stages the change and
                                    returns a token; a second, explicit call
                                    applies it. The agent can never mutate in
                                    one unreviewable step.

Run as a stdio MCP server:

    pip install mcp
    python server.py

Then point any MCP client (e.g. Claude Desktop) at it — see README.md.
"""

from __future__ import annotations

import secrets

from mcp.server.fastmcp import FastMCP

from policy import audit, require

mcp = FastMCP("agent-starter")

# Demo "knowledge" the read tools serve. Canned — no real data.
_KB: dict[str, str] = {
    "runbooks": "How-to guides for routine operations.",
    "architecture": "System design notes and decisions.",
    "policies": "Security and access policies.",
}

# Writes staged by propose_write, awaiting confirm_write: token -> (key, value).
_PENDING: dict[str, tuple[str, str]] = {}


@mcp.tool()
def search_knowledge(query: str) -> str:
    """Search the knowledge base (read-only). Requires capability `kb.read`."""
    require("kb.read")
    q = query.lower()
    hits = {k: v for k, v in _KB.items() if q in k or q in v.lower()}
    audit("tool", name="search_knowledge", query=query, hits=len(hits))
    return "\n".join(f"- {k}: {v}" for k, v in hits.items()) or "no matches"


@mcp.tool()
def get_status() -> str:
    """Report platform status (read-only). Requires capability `status.read`."""
    require("status.read")
    audit("tool", name="get_status")
    return f"ok — {len(_KB)} knowledge sections loaded"


@mcp.tool()
def propose_write(key: str, value: str) -> str:
    """Stage a change to the knowledge base. Does NOT apply it.

    Returns a confirmation token; an operator must call ``confirm_write(token)``
    to apply. Requires capability `kb.write`.
    """
    require("kb.write")
    token = secrets.token_hex(8)
    _PENDING[token] = (key, value)
    audit("propose_write", key=key, token=token)
    return (
        "PENDING — review, then confirm.\n"
        f"  change: set {key!r} = {value!r}\n"
        f"  apply with: confirm_write(token='{token}')"
    )


@mcp.tool()
def confirm_write(token: str) -> str:
    """Apply a previously proposed change. Requires capability `kb.write`.

    The two-step gate keeps a mutating action human-in-the-loop and fully
    audited: nothing changes until this explicit second call.
    """
    require("kb.write")
    if token not in _PENDING:
        audit("confirm_write", token=token, result="unknown-token")
        return "unknown or expired token — nothing applied"
    key, value = _PENDING.pop(token)
    _KB[key] = value
    audit("confirm_write", token=token, key=key, result="applied")
    return f"applied — {key!r} updated"


if __name__ == "__main__":
    mcp.run()
