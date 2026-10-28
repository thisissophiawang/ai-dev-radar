# Project Status — AI Dev Radar

Updated: 2026-10-28 (Asia/Shanghai)
Integrated branch: `main` (collection implementation originated on `codex/dashboard-collection`)

## Current milestone

Local automatic data collection dashboard implemented. This is the data foundation for a future AI-native assistant; domestic-model chat and analysis are not implemented yet.

## Implemented

- FastAPI service and responsive, buildless dashboard with news, repository, and bookmark tabs.
- Hugging Face and GitHub AI/ML RSS collectors.
- GitHub seed repository metadata and topic-based project discovery (MCP, agent skills, AI coding).
- SQLite canonical-URL deduplication, source attribution, bookmarks, notes, and daily star snapshots.
- Manual refresh, startup catch-up, and daily 09:00 Asia/Shanghai collection while the service remains running.
- Single-process refresh exclusion, interrupted-run recovery, partial-success reporting, and preservation of old content.
- Bounded source requests, allowlisted HTTPS destinations, cross-origin write protection, safe text rendering, and credential exclusion from Git.
- Project/user Superpowers setup and MVP implementation documents.

## Validation performed

- Backend suite: **8 passed**, with one upstream Starlette/httpx TestClient deprecation warning.
- JavaScript syntax: `node --check src/radar/static/app.js` passed.
- Real browser: bookmark save/reload/remove, repository search, mobile overflow check, and page-error check passed.
- Browser regression: repository-only sorting and persistent list-error display passed after fixes.
- Real collection: **90 articles and 57 distinct repositories** persisted; **0 duplicate URLs** found after reopening the database.
- Both RSS feeds and all three GitHub topic searches succeeded in the observed live run.
- Four seed repository requests failed because unauthenticated GitHub REST requests were rate-limited. The observed run is therefore **partial**, not fully successful.
- Repository data and user notes are local-only and excluded from this commit.

## Remaining limitations / work

- Authenticate GitHub through the application's optional `GITHUB_TOKEN` environment variable and revalidate all four seed repositories after rate limits permit. CLI/connector login is not silently reused by the app.
- Daily timing is behavior-tested; a real unattended 09:00 run and multi-day observation are still pending.
- Full stop/start persistence is covered at storage level; the browser check reloads the page, not the entire server process.
- Only one worker/process may use this collector database; no OS launch-at-login service is installed.
- Collection uses bounded feed/search windows, not exhaustive internet coverage; HTTP conditional caching is not implemented yet.
- Some feeds provide titles and links without excerpts. These are displayed honestly as missing descriptions.
- Chinese summaries, conversational assistant, domestic model adapter, evidence-based quality scoring, and historical trend UI remain future milestones.

## Run

```sh
./scripts/start.sh
```

Open http://127.0.0.1:8000 . Keep the process running and the computer awake for automatic updates.

## Next action

Finish authenticated source validation, then connect one domestic model to turn collected evidence into sourced Chinese answers. Preserve collection functions as reusable tools for that future assistant.

## Project verification update — 2026-10-28

Implemented on `codex/project-verification`:
- Repository cards now distinguish collection time, upstream push time, and human review time.
- Four evidence stages: discovered, documentation checked, locally passed, adopted.
- Repository-only filtering and evidence history dialog with version, scope, and timestamp.
- Explicit manual records, not automated certifications. Missing evidence and skipped progression are rejected; records survive collector refresh and application restart.
- Upstream push-time changes flag old evidence for re-review without erasing history.
- Three prioritized projects have pinned-commit documentation reviews: superpowers-zh, spec-kit, python-sdk. None is newly claimed as locally passed or adopted by these review records.
- Review reports: `docs/verifications/`. The manual review import uses authenticated GitHub CLI separately from scheduled collection.
- Validation: 11 backend tests passed; browser filtering, evidence history, timestamps, and mobile layout passed. Existing Starlette/httpx warning remains.

## Read-only MCP increment — October 28, 2026

- Added shared validated catalog queries for HTTP and MCP.
- Added five stdio read tools using the official MCP Python SDK 1.30.0 (v1 compatibility line).
- Verified real subprocess/client initialization, tool discovery, search, exact item follow-up, evidence history, source listing, partial-run status, missing items and invalid limits.
- Full local suite: 12 passed; one existing Starlette/httpx deprecation warning.
- This is local protocol validation with fixture data, not real model/QwenPaw acceptance.
- Remaining: controlled writes and idempotency, business Skills, assistant integration and domestic model configuration.
