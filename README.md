# AI Dev Radar

A local-first dashboard that collects AI engineering news and GitHub projects for MCP, agent skills, and AI coding. Built with Python, FastAPI, SQLite, and a buildless browser UI.

## Current capabilities

- Browse collected AI news, discover open-source projects, and keep a personal reference library.
- Search titles and descriptions; sort repositories by recent activity or GitHub stars.
- Save bookmarks with notes, edit them, and remove them through the local dashboard.
- Collect automatically on first startup and daily while the service runs; trigger manual refreshes when needed.
- Inspect per-source results, partial failures, and collection timestamps without losing existing content.

The collection workflow developed on `codex/dashboard-collection` is now integrated into `main`.

On the development branch, an isolated **QwenPaw 2.2.2.post1** assistant can connect to the existing Radar database through seven MCP tools and load two research Skills. Run `sh scripts/start_assistant.sh` after the [local assistant setup](docs/assistant-setup.md), then open `http://127.0.0.1:8088/`. Runtime connectivity is verified; domestic-model conversation and embedded Dashboard chat are pending. Follow the [assistant implementation plan](docs/superpowers/plans/2026-10-29-qwenpaw-assistant.md) for the delivery sequence and acceptance criteria.

## How collection works

```text
Startup / daily schedule / manual refresh
                   |
                   v
        Single active collection run
                   |
                   v
     RSS feeds + GitHub REST endpoints
                   |
                   v
 Normalize URLs and source metadata
                   |
                   v
  SQLite upsert + daily star snapshots
                   |
                   v
  Dashboard -> source links -> bookmarks
```

1. **Trigger:** the scheduler checks once per minute for the daily 09:00 Asia/Shanghai cutoff. Concurrent refresh requests reuse the active run.
2. **Collect:** approved HTTPS sources are fetched with bounded response sizes and request timeouts. GitHub searches discover candidates alongside the configured seed repositories.
3. **Normalize:** tracking parameters are removed, business query parameters are retained, and canonical URLs identify records. Unknown publication dates remain unknown.
4. **Persist:** repeated items update existing rows; source attribution and daily repository star snapshots are saved separately. Bookmarks remain attached to stable item IDs.
5. **Report:** successful sources retain their results even when another source fails. A run ends as successful, partial, or failed; abandoned runs are marked interrupted on restart.
6. **Read and save:** the browser queries the local API, renders external content as text, and persists bookmarks and notes in SQLite.

## Architecture

| Component | Responsibility |
| --- | --- |
| `src/radar/app.py` | Local HTTP API, lifecycle, static page serving, and origin checks |
| `src/radar/collectors.py` | RSS parsing, GitHub discovery, and bounded source requests |
| `src/radar/refresh.py` | Collection orchestration, single-run coordination, and daily scheduling |
| `src/radar/storage.py` | SQLite records, canonical URLs, bookmarks, and snapshots |
| `src/radar/static/` | Responsive news, repository, and bookmark views |
| `src/radar/services/` | Shared catalog queries and idempotent bookmark operations |
| `src/radar/mcp_server.py` | Seven stdio MCP tools over the existing database |
| `skills/` | Evidence-aware project discovery and personal library workflows |
| `scripts/setup_qwenpaw.py` | Pinned, isolated assistant setup and actual runtime MCP checks |
| `scripts/start_assistant.sh` | Local QwenPaw Console startup on port 8088 |
| `scripts/start.sh` | Single-worker local startup |

## Run locally

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
./scripts/start.sh
```

Open [the local dashboard](http://127.0.0.1:8000). No Node build or cloud deployment is required. The startup script loads source directly; it avoids an editable-install encoding issue on Chinese directory paths.

The app collects on first startup, catches up after a missed daily run, and checks for the 09:00 Asia/Shanghai run every minute while running. Keep the terminal open and the computer awake for scheduled collection. Manual refresh is also available. Run only one dashboard collection worker. The separate MCP process may read and update bookmarks in the same SQLite database; it does not start a competing scheduler.

## Sources and limits

- Hugging Face Blog RSS: up to 80 articles.
- GitHub Blog AI/ML RSS: up to 80 articles (the current feed may contain fewer).
- Four seed repositories, plus three topic searches: up to 20 repositories per query.
- GitHub metadata is a discovery signal, not a quality certification. No repository code is executed.
- API rate limits may cause partial refreshes. Successful content is retained and failures appear in the source panel. There is no automatic high-frequency retry for 403/429 responses.
- Optionally export `GITHUB_TOKEN` in the shell before launch to use authenticated GitHub requests. Never put credentials in tracked files. `.env` is not loaded automatically.
- News text is the original source excerpt. AI chat, Chinese model summaries, and trend analytics are not implemented yet.

## Data and checks

SQLite lives in `data/radar.sqlite3` (ignored by Git); bookmarks and notes survive restarts. Daily repository star snapshots are collected for future trend work. Current scheduling uses local time conversion and stored attempt timestamps, not an OS background service.

```sh
PYTHONPATH=src .venv/bin/python -m pytest -q
node --check src/radar/static/app.js
# Optional browser smoke check with local server running and Chrome installed:
.venv/bin/python scripts/check_browser.py
```

The browser check temporarily creates and removes one bookmark; run it against a disposable/test database if personal bookmarks are present.

## Verified status

The current development increment passes **19 tests**, including actual MCP protocol calls, idempotent bookmark writes, and isolated QwenPaw setup and runtime reads. The suite emits one existing Starlette/httpx deprecation warning. Runtime-specific setup tests require the optional QwenPaw environment and skip when it is absent. Earlier dashboard browser checks covered bookmark persistence, search, mobile layout, tab sorting, and list-error reporting.

The observed live run on October 28, 2026 stored 90 articles and 57 distinct repositories. Both RSS feeds and three GitHub searches succeeded; four seed repository requests were rate-limited. This was a **partial live run**, not verification that every source succeeded. These counts are a historical validation snapshot, not a promise about future feed contents.

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for verification boundaries and outstanding work.

## Product direction

The longer-term goal is an AI-native personal research assistant backed by a domestic large language model. The current milestone supplies its reusable data collection and storage foundation.

Planned additions include sourced conversational answers, Chinese technical explanations, evidence-based project evaluation, and historical trend analysis. They are not available in the current dashboard. Codex and Superpowers support product development; a separately configured model provider will power the future in-product assistant.

## Development

- [Current project status](PROJECT_STATUS.md)
- [Project instructions](AGENTS.md)
- [MVP plan](docs/superpowers/plans/2026-10-28-ai-dev-radar-mvp.md)
- [Superpowers setup](docs/superpowers-setup.md)

Superpowers provides development skills; the runtime collector is ordinary application code and does not depend on an AI model.

## Freshness and project verification

Repository cards distinguish upstream push time, last collection time, and review time. Filter projects by **discovered**, **documentation checked**, **locally passed**, or **adopted**. The evidence dialog records a version/commit, evidence, scope, and timestamp; records are retained separately from automatic metadata refreshes. Later upstream changes mark the previous verification as needing review.

These are human-maintained evidence records, not automatic quality certificates. Stage progression requires the preceding stage. Three initial documentation reviews are recorded in [docs/verifications](docs/verifications); they do not imply successful local execution or production adoption. The manual `scripts/review_seed_projects.py` importer requires a separately authenticated `gh` CLI and should only be run after actually reviewing the named sources.

## MCP and Skills design

See the [MCP Tools and Skills Architecture](docs/architecture/mcp-skills-design.md) for the proposed shared-service architecture, nine MCP tools, four business Skills, evidence stages, write safeguards, and phased acceptance plan. Seven MCP tools are implemented: five catalog/status reads and two idempotent bookmark writes. Two business Skills are available in the isolated QwenPaw workspace. Collection-start and verification-write tools, additional Skills, real-model conversation acceptance, and embedded Dashboard chat remain pending.

### Read-only MCP integration

A local stdio MCP server now exposes five read tools over the same database as the dashboard: search, exact item details, verification history, configured sources, and collection status. See [local setup](docs/mcp-local-setup.md). Real SDK client tests cover protocol initialization and tool calls. QwenPaw runtime connectivity is also verified; domestic-model conversations remain pending.

### Bookmark MCP operations

The MCP server also exposes idempotent bookmark save/remove tools (seven tools total). HTTP and MCP share the bookmark service. Request replay returns the original operation result; query the item for current state. See the local setup guide for request-key semantics. The earlier bookmark milestone passed 14 tests; the current assistant increment passes 19 tests. Real-model assistant acceptance remains pending.

## Assistant setup and next delivery steps

Install and initialize the optional runtime after creating the Radar environment and database:

```sh
uv venv --python .venv/bin/python data/qwenpaw-venv
uv pip install --python data/qwenpaw-venv/bin/python 'qwenpaw==2.2.2.post1'
data/qwenpaw-venv/bin/python scripts/setup_qwenpaw.py --db data/radar.sqlite3
sh scripts/start_assistant.sh
```

On this machine the isolated runtime is already installed and initialized; use only the last command to restart it. Setup refuses to overwrite an existing assistant home. Open [the local assistant](http://127.0.0.1:8088/) and use Default Agent. Configure Kimi locally in Models before conversational acceptance; the pending model selection does not establish account access or a successful model call.

Delivery order: reusable data and MCP tools → isolated QwenPaw and workspace Skills → actual sourced question, follow-up and bookmark read-back → Dashboard chat adapter. The first two stages are verified. Model credentials, real conversational behavior, and the Dashboard adapter remain pending.

Runtime files, package snapshots, conversations and credentials stay under Git-ignored `data/`. The repository contains setup scripts and documentation, not the installed runtime or private data. See [assistant setup and acceptance](docs/assistant-setup.md) and the [step-by-step development plan](docs/superpowers/plans/2026-10-29-qwenpaw-assistant.md).
