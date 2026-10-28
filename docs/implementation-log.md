# Dashboard collection execution ledger
Plan: docs/superpowers/plans/2026-10-28-ai-dev-radar-mvp.md
Scope: data collection dashboard only; no model calls, no publication.
Ruling: Reuse the dedicated ai-dev-radar checkout on codex/dashboard-collection, preserving pending plan documents; no second checkout needed for a single implementation owner.
Ruling: Add daily 09:00 Asia/Shanghai in-process scheduling and startup catch-up to fulfill automatic collection. Computer must be awake and process running.
Preflight: list/detail/save use the same stable canonical URL id; no model dependency.
Sources: Hugging Face blog/feed.xml and GitHub Blog ai-and-ml/feed returned HTTP 200 RSS on 2026-10-28.
Initial test attempt blocked by incomplete dependency installation; not counted as RED.

Implementation outcome (2026-10-28):
- Dependencies installed directly; editable install failed because setuptools encoded the Chinese checkout path as ASCII. Startup uses PYTHONPATH=src.
- Tests first failed due to missing production modules; initial implementation reached 5 pass / 1 missing-page failure, then 6 pass.
- Added a failing 09:00 cutoff regression, fixed early-startup suppression; final backend suite 8 passed (one dependency deprecation warning).
- Real run: 90 articles, 57 repositories; two feeds + three searches succeeded, four seeds rate-limited. Stopped retrying limited endpoints.
- Browser bookmark/search/mobile checks passed. Independent review found tab-sort leakage and status-poll error masking; regression reproduced, fixes passed.
- No models, cloud deployment, or external repository execution added.

## Read-only MCP increment

Ruling: reuse the existing codex/project-verification checkout and preserve its unfinished verification changes; extracting catalog reads first minimizes disruption to the running collection dashboard.
Ruling: use official SDK 1.30.0 with <2 constraint for the initial adapter; v2 migration is a separate compatibility decision.
RED: real stdio integration failed because radar.mcp_server did not exist.
Implementation: shared Catalog/CatalogQuery, exact ID filtering, five read tools, no collector/recovery lifecycle in the MCP process.
Integration finding: bare dict annotations did not generate structuredContent; inspecting installed SDK output-schema handling identified the cause. Typed dict[str, Any] fixed the contract.
GREEN: full suite 12 passed, one existing Starlette/httpx deprecation warning.
Delivery: docs/mcp-local-setup.md. Model and QwenPaw integration are not yet implemented or accepted.

## Bookmark operations increment

RED: two storage tests failed on missing bookmark_write; after the transaction implementation they passed. Extended real stdio test failed on unknown radar_bookmark_save, then passed after tool registration.
GREEN: full suite 14 passed, one existing deprecation warning. Transaction tests cover concurrent same-key calls, conflicting reuse, restart replay, and old deletion replay after a fresh save.
Ruling: replay is a historical operation receipt; clients must use item_get for current state. Legacy HTTP deletion of missing IDs remains a 204 no-op. No QwenPaw/model execution is claimed.
