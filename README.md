# mcp-agent-starter

A **minimal MCP server** that shows the security model an enterprise agent platform needs — in code you can read in one sitting.

Most "MCP server" examples expose tools with no guardrails. In production the hard part isn't the tool, it's **what an agent is allowed to do with it**. This starter bakes in three patterns:

| Pattern | Where | What it buys you |
|---|---|---|
| **Per-agent least privilege** | `policy.require()` | Tools declare a capability; calls are **default-deny**. An agent only does what it was scoped to. |
| **Audit** | `policy.audit()` | Every call — allowed *and* denied — is appended to `audit.log` as JSON. Probing leaves a trail. |
| **Human-confirm gate on writes** | `propose_write` → `confirm_write` | A mutating tool **stages** the change and returns a token; an explicit second call applies it. No one-step unreviewable mutation. |

## Tools

| Tool | Capability | Effect |
|---|---|---|
| `search_knowledge(query)` | `kb.read` | read-only lookup |
| `get_status()` | `status.read` | read-only status |
| `propose_write(key, value)` | `kb.write` | **stages** a change, returns a confirm token |
| `confirm_write(token)` | `kb.write` | applies the staged change |

## Run

```bash
pip install mcp
python server.py        # stdio MCP server
```

Connect from Claude Desktop — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agent-starter": { "command": "python", "args": ["/abs/path/to/server.py"] }
  }
}
```

## Try the guardrails

- Call `propose_write("notes", "hello")` → you get a token, **nothing changed yet**.
- Call `confirm_write("<token>")` → now it applies. Two steps, both audited.
- Remove `"kb.write"` from `GRANTED` in `policy.py` → write tools now **fail closed** with `Denied`, and the attempt is logged.
- `tail -f audit.log` while you work to watch the trail.

## Why default-deny

`require()` raises **before** the tool body runs. Add a tool, declare its capability, done — you can't accidentally ship an ungoverned tool, and the deny path is audited just like the allow path.

---

By **Gustavo Norymberg** — AI & Agentic Platform Architect. A teaching reference, not a framework. [LinkedIn](https://www.linkedin.com/in/gustavonorymberg)
