# Project Status — AI Dev Radar

Updated: 2026-10-29 (Asia/Shanghai)
Current development branch: `codex/project-verification`
Latest committed implementation: `11c0458` (previously pushed; local origin tracking ref matches HEAD; not merged into `main`).
Current delivery increment: assistant preparation, isolated QwenPaw setup/launcher, two business Skills, integration notes, executable plan and tests. Commit and remote confirmation are reported in the delivery message.
`main` contains the earlier collection dashboard baseline.

## Current milestone

Local collection dashboard, project evidence tracking, and seven MCP tools (five reads, two bookmark writes) are implemented. The collection foundation is usable; the end-to-end AI assistant and feedback loop are not complete. Domestic-model chat and analysis are not implemented yet.

QwenPaw 2.2.2.post1 is now installed locally in an isolated environment. Its real MCP client has queried the existing Radar database and its workspace Skill service lists both research Skills as available. Console startup is verified; actual model-backed conversation and embedded Dashboard chat remain pending.

## Implemented

- FastAPI service and responsive, buildless dashboard with news, repository, and bookmark tabs.
- Hugging Face and GitHub AI/ML RSS collectors.
- GitHub seed repository metadata and topic-based project discovery (MCP, agent skills, AI coding).
- SQLite canonical-URL deduplication, source attribution, bookmarks, notes, and daily star snapshots.
- Manual refresh, startup catch-up, and daily 09:00 Asia/Shanghai collection while the service remains running.
- Single-process refresh exclusion, interrupted-run recovery, partial-success reporting, and preservation of old content.
- Bounded source requests, allowlisted HTTPS destinations, cross-origin write protection, safe text rendering, and credential exclusion from Git.
- Project/user Superpowers setup and MVP implementation documents.

## Initial collection milestone — historical validation

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

## Next action — minimal end-to-end loop

1. DONE locally: bookmark save/remove through shared services and MCP, with request-key replay, conflicting-payload rejection, and persisted read-back. Current full suite: 16 passed, one existing deprecation warning.
2. Two business workflow drafts now exist. Validate their format and behavior, then explicitly load them in the chosen assistant runtime; file creation alone does not prove execution.
3. Connect one QwenPaw instance and one configured domestic model. Validate search → exact-item follow-up → explicit save → read-back with a real provider. Model selection, credentials and tool compatibility are prerequisites, not completed setup.
4. In parallel with assistant acceptance, configure the application's GitHub credential and verify all sources; observe an unattended scheduled run and then multiple days. Do not equate timer tests with uninterrupted operation.

Acceptance scenario: ask for noteworthy AI development tools and recent AI news, ask whether the second candidate actually passed local testing, save it with a note, and retrieve the saved note in a new conversation. Responses must cite actual records and dates and disclose missing evidence or partial collection.

## Goal and self-loop assessment

| Loop | Current evidence | Missing for acceptance |
| --- | --- | --- |
| Collect → deduplicate → store → display → next scheduled collection | Implemented; historical live collection was partial; scheduler tests passed | Authenticated full-source validation, unattended and multi-day observation; service must remain running and machine awake |
| Question → tools → sourced answer → follow-up → saved result | Seven MCP tools, including bookmark writes, passed SDK protocol tests; real local database read connectivity also checked | Skill validation/loading, model/runtime integration, persistent conversation and real-model acceptance |
| Usage feedback → improved selection → next recommendation | Bookmarks, notes and evidence records exist as inputs | Explicit preference/ranking rules, feedback consumption, evaluation and demonstrated improvement |

Overall: the data foundation is delivered. The user's full AI-native research assistant goal and autonomous feedback loop are not yet achieved. No automatic testing/adoption of collected repositories is implemented. Current scheduling does not install an OS background service, recover an exited process, or resolve rate limits autonomously.

## Status maintenance policy

Every development update must update this file before its commit: date, change summary, phase, verification evidence, remaining gaps and next action. Label historical measurements; never present fixtures or old runs as current production evidence. Record the resulting commit/push reference in the handoff or subsequent status update to avoid self-referential commit hashes. Keep main versus feature-branch delivery explicit.


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

## Status reconciliation — October 28, 2026

- Reconciled the current milestone and branch with pushed implementation commit `61365bb`.
- Marked initial 8-test results and live collection counts as historical; latest implementation suite was 12 passed, one upstream deprecation warning.
- Clarified the three separate loops and the next minimal acceptance scenario.
- Added mandatory per-update status recording to AGENTS.md. This update changes documentation only; no new runtime functionality or model acceptance is claimed.

## Product scope correction — October 28, 2026

- Product: a local personal AI development intelligence and research assistant covering international AI news, MCP/Skills/AI coding projects, reusable development methods and evidence-based trends.
- Previous CRM delivery experience is a process reference only, not this product's domain or candidate-selection filter.
- Corrected the acceptance scenario, architecture example and protocol test fixture; reconciled stale implementation statements in README and architecture documentation.
- Ordered delivery and acceptance criteria: [corrected roadmap](docs/superpowers/plans/2026-10-28-personal-ai-research-loop.md).
- Validation: `PYTHONPATH=src .venv/bin/pytest -q` → 12 passed, one existing Starlette/httpx deprecation warning; `git diff --check` passed. No new assistant functionality implemented by this correction.

## Bookmark MCP delivery — October 28, 2026

- Implemented `radar_bookmark_save` and `radar_bookmark_remove`; seven MCP tools now exist (five reads, two writes).
- Dashboard HTTP and MCP bookmark operations now share the Bookmarks service; existing HTTP response shapes and missing-bookmark deletion behavior remain compatible.
- SQLite transaction atomically stores the mutation and request result. Same key and arguments replay the original outcome; different arguments conflict. An old removal replay cannot remove a later re-save. Current state is retrieved separately via item_get.
- Real SDK subprocess test covers search → item → save → replay → read-back → conflict → remove. SQLite tests cover restart persistence and eight concurrent identical requests.
- Validation: `PYTHONPATH=src .venv/bin/pytest -q` → 14 passed, one existing Starlette/httpx deprecation warning; `git diff --check` passed.
- Next: implement/load project-discovery and library-management Skills in a verified QwenPaw runtime, then configure one domestic model and validate actual conversation. No real-model or QwenPaw acceptance yet. Running dashboard process must restart to load updated Python code.

## Commit delivery notes — October 28, 2026

- Delivery branch: `codex/project-verification`; this delivery does not merge into `main`.
- Includes the product-scope correction, ordered personal AI research roadmap, mandatory per-update status policy, shared bookmark service, transactional request journal, two MCP write tools, and regression tests.
- Fresh pre-commit validation: 14 tests passed, one existing Starlette/httpx deprecation warning; whitespace/diff check passed.
- Detailed English notes: `docs/commit-notes/2026-10-28-bookmark-mcp.md` and the commit message body.
- Next milestone: load business Skills in a verified QwenPaw runtime and configure a domestic model for sourced multi-turn answers. No model, QwenPaw, or unattended multi-day acceptance is claimed.

## Assistant preparation — October 29, 2026

- User clarified there is no existing QwenPaw installation. Evaluate QwenPaw + Kimi versus WorkBuddy; do not assume credentials or a running assistant already exist.
- Added `scripts/prepare_assistant.py`: real stdio initialization, seven-tool catalog verification, source/search read calls, and non-overwriting generic client configuration generation.
- Added two draft business Skills for evidence-aware project discovery and library management. Neither is installed or behaviorally validated in an assistant runtime. The optional skill validator is blocked by missing PyYAML in the project environment.
- Validation: full suite 16 passed, one existing deprecation warning. Also ran the preparation script against the actual local Radar database; seven tools and read calls passed. No model invocation, runtime install, or chat acceptance is claimed.
- Integration notes: `docs/assistant-setup.md`. Next: pin and inspect the selected runtime, configure the chosen model locally, load Skills and perform real conversational acceptance.
- This increment remains local and uncommitted.

## Progress audit — October 29, 2026

- Re-read status, integration notes and Git working tree; corrected stale top-level date, commit reference and loop table.
- Fresh validation: `PYTHONPATH=src .venv/bin/pytest -q` → 16 passed, one existing Starlette/httpx warning. No live source refresh or model call performed in this audit.
- Current phase: assistant integration preparation (roadmap step 2), not completed conversational assistant.
- Immediate sequence: validate Skill drafts; inspect/pin and isolate QwenPaw installation; configure Kimi API locally when available; load Radar tools and Skills; verify three-turn sourced conversation and bookmark read-back; then integrate the verified chain into Dashboard.
- API credentials are needed for real Kimi calls, not for local setup, tool testing or continued implementation. No purchase or configured key is assumed.

## Isolated assistant runtime delivery — October 29, 2026

- Installed official QwenPaw `2.2.2.post1` in `data/qwenpaw-venv`; dependency snapshot is local `data/qwenpaw-requirements.lock`. The existing Radar environment and database remain the business implementation.
- Added `scripts/setup_qwenpaw.py`: validates inputs and pinned runtime, refuses an existing workspace, initializes version-compatible configuration, loads seven Radar tools, copies/scans/enables two research Skills through QwenPaw's Skill service, and checks actual read calls with QwenPaw's own MCP client. Configuration/test paths containing spaces pass.
- Real setup against `data/radar.sqlite3`: seven tools discovered; source listing and item search passed; both Skills are listed as available for the default Console workspace. This is runtime integration evidence, not proof of successful model reasoning or correct Skill use during conversation.
- Added a loopback launcher at `http://127.0.0.1:8088/`. The Console and Models page were inspected in the browser; server startup logs confirm the Radar MCP connection. The service remains running for local configuration/testing.
- Fixed an observed upstream isolation issue: Chrome bridge bootstrap defaults to `~/.qwenpaw` despite the custom working directory. The launcher sets process-local bridge state to the project home before loading the app; upstream package files remain unmodified.
- Explicitly selected pending `kimi-cn / kimi-k2.5` for the research agent to prevent inheritance of QwenPaw's default free router. No API key is configured, no model-backed conversation has been accepted, and account/model entitlement is unknown. Configure an actually available model in the local Models page.
- Full verification: `PYTHONPATH=src .venv/bin/pytest -q` → **19 passed**, one existing Starlette/httpx deprecation warning. New setup tests were observed failing before implementation and passing afterward. `git diff --check` passed. Runtime logs also show upstream duplicate-plugin warnings and unsuccessful discovery of unconfigured Ollama/LM Studio; these do not establish local-model availability.
- Development sequence and checkboxes: `docs/superpowers/plans/2026-10-29-qwenpaw-assistant.md`. Setup and runtime connection are complete; real-model three-turn acceptance and the subsequent Dashboard chat adapter remain pending.
- Ruling: keep the existing QwenPaw-first sequence instead of building a second model orchestration stack before real behavior is verified. Keep model credentials and runtime data local. Complete all credential-independent setup now; record model acceptance as pending.
- Delivery branch: `codex/project-verification`. This increment remains local and uncommitted; no new push or merge is claimed.


## Assistant commit preparation — October 29, 2026

- User requested committing and pushing the assistant increment with an updated English README.
- README now documents the runtime setup/start commands, seven-tool architecture, workspace Skills, single collection-worker boundary, current 19-test evidence, and the remaining real-model/Dashboard-chat acceptance.
- Includes both the earlier assistant preparation work and the isolated QwenPaw setup/launch implementation, tests, business Skills and executable plan.
- Fresh pre-commit validation: `PYTHONPATH=src .venv/bin/pytest -q` → 19 passed, one existing Starlette/httpx deprecation warning. `git diff --check` passed.
- Runtime installations, private configuration, conversations, model keys, logs and SQLite files remain excluded by Git ignore rules.
- Delivery target: existing `codex/project-verification` branch. The current commit hash and push result are reported after execution; this delivery does not claim real-model acceptance or a merge into main.
