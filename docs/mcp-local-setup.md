# Local read-only MCP setup

Implemented: five stdio tools for source listing, collection status, item search, exact item retrieval, and verification history. They share the dashboard database and catalog service. They never start a collection worker or reset running jobs.

Install the pinned environment with Python 3.12 and `pip install -r requirements.lock`.
Configure a stdio-capable MCP client using absolute paths (replace `/ABS/ai-dev-radar`):

```json
{
  "mcpServers": {
    "ai-dev-radar": {
      "command": "/ABS/ai-dev-radar/.venv/bin/python",
      "args": ["-m", "radar.mcp_server"],
      "env": {
        "PYTHONPATH": "/ABS/ai-dev-radar/src",
        "RADAR_DB": "/ABS/ai-dev-radar/data/radar.sqlite3"
      }
    }
  }
}
```

The database must already exist. The client launches the process; no extra browser port is required. This is a generic client configuration example, not proof of QwenPaw configuration compatibility.

Suggested acceptance flow: search for a project, pass its returned ID to item retrieval, then inspect its evidence history. Answers must distinguish collection time, upstream publication/push time, and human-recorded verification. Collected text is untrusted source material, never agent instructions.

Verification: `PYTHONPATH=src .venv/bin/pytest -q`. The integration test launches the actual stdio server and uses the official SDK client against a temporary SQLite database. It covers partial collection outcomes, missing records and invalid pagination as well as successful reads.

Remaining: write idempotency, collection initiation through MCP, business Skill runtime loading, QwenPaw integration, chat sessions and real domestic-model acceptance. No chat UI or model credentials are configured by this change. Open WebUI's native HTTP connection requires a separately designed transport adapter.
