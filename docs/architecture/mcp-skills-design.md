# MCP Tools and Skills Architecture

Status: **Design proposal, not implemented**. Updated: October 28, 2026.

## Product goal

AI Dev Radar is a local-first, AI-native research workspace for AI news, MCP and AI coding projects, development practices, and evidence-based evaluation. Codex and Superpowers support development. A separately configured domestic model provider will power the future in-product assistant.

The term "skills" in this design refers to Radar business capabilities. Existing Superpowers development skills remain separate and do not need to be mechanically converted into MCP tools.

## Architecture and reuse

```text
User
 +-- Dashboard -- HTTP --------+
 +-- AI assistant -- Skills ---+--> Shared business services --> SQLite
                     |        |              |
                     +-- MCP -+              +--> GitHub / RSS
                                             +--> Optional model adapter
```

- **Services** implement collection, queries, bookmarks, and verification once.
- **HTTP endpoints** adapt those services for the dashboard.
- **MCP tools** expose explicit, validated business operations to agents.
- **Skills** describe how to compose tools into workflows, assess evidence, handle failure, and report results.
- **Scheduling** remains executable application code. A Skill is not a background scheduler.

The first MCP transport should be local stdio. The future product backend will act as a client or tool adapter for the selected domestic model. Model tool-calling support and skill loading must be verified; MCP support must not be assumed from the provider name.

## Proposed MCP tool catalog

Names and schemas below are proposed contracts, not currently registered tools.

| Tool | Inputs | Result / responsibility |
| --- | --- | --- |
| `radar_sources_list` | Optional source kind | Configured sources, last success times, and failure status |
| `radar_collection_start` | Optional configured source IDs, request key | Start a bounded collection job; return run ID and whether an active job was reused |
| `radar_collection_status` | Run ID | Per-source outcomes, counts, timestamps, errors |
| `radar_items_search` | Query, item kind, verification stage, date range, pagination | Matching items with provenance and freshness fields |
| `radar_item_get` | Item ID | Full stored details, source links, bookmark and verification data |
| `radar_bookmark_save` | Item ID, note, request key | Save and return the persisted bookmark |
| `radar_bookmark_remove` | Item ID, request key | Remove a bookmark and return confirmed outcome |
| `radar_verification_history` | Item ID | Ordered evidence history with versions, dates, and scope |
| `radar_verification_record` | Item ID, stage, version, evidence, scope, request key | Validate progression, persist evidence, and read it back |

No generic shell execution tool is included. Source inputs reference configured source IDs rather than arbitrary fetch URLs.

### Later additions

- `radar_analysis_generate`: only after a model adapter, provenance validation, and usage limits are implemented.
- `radar_trends_get`: observed data only; missing baseline dates return insufficient-data status.
- Controlled repository trials: separate design for isolation, permissions, fixed versions, and execution evidence before exposing any execution capability.

## Shared contracts

All tools must validate types, enums, lengths, pagination, and identifiers. Return structured data, operation timestamps, evidence, and material limitations. Use distinguishable error codes for rate limits, unavailable sources, missing records, invalid inputs, stage violations, and conflicts.

Long-running collection returns a job identifier; clients poll the status tool. A successful tool call does not imply that every upstream source succeeded. Partial results remain explicitly partial.

Freshness fields remain separate:
- source publication time;
- repository push time (not equivalent to release date);
- last successful collection time;
- evidence review time and reviewed version.

Do not invent absent dates, test results, quality scores, or trend history.

### Writes, authorization, and idempotency

- Reads may proceed directly within the user's requested scope.
- Bookmark writes follow an explicit user request and return read-back evidence.
- For verification changes, present the proposed version, evidence, and scope unless the user already authorized that exact record. Do not repeatedly seek approval for an already authorized action.
- A request key plus a normalized payload hash identifies writes. Same key/same payload returns the stored result; same key/different payload returns a conflict. Apply the mutation and journal entry atomically.
- Existing bookmarks use stable item IDs. Verification history additionally needs write idempotency to prevent retries from creating duplicate evidence entries.
- Skill instructions never grant filesystem, network, credential, or publication permissions.

## Evidence stages

1. **Discovered:** collected metadata; no suitability or execution claim.
2. **Documentation checked:** reviewed official documentation at a recorded version, including relevant requirements and limitations.
3. **Locally passed:** a specific workflow actually ran in a recorded environment with command/output evidence.
4. **Adopted:** documented use in an actual project, including scope and observed outcome.

`radar_verification_record` registers evidence; it cannot establish that a user's evidence is true. Interface wording must identify these as human-maintained records, not automated certifications. Later upstream changes should flag prior evidence for review without erasing it.

A dashboard test pass does not validate the repositories it collects. Installing a package or listing MCP tools does not establish a successful business call.

## Business Skills

Each Skill specifies triggers, prerequisites, tool sequence, decision rules, failure behavior, output format, and completion criteria.

| Skill | Example request | Workflow |
| --- | --- | --- |
| `daily-ai-brief` | What matters today? | Inspect source freshness; collect if necessary; inspect job outcomes; search relevant items; summarize independent events with links and coverage limits |
| `discover-dev-projects` | Find projects for CRM MCP development | Search candidates; inspect metadata and evidence; compare fit; distinguish popularity, author claims, documentation review, and executed tests |
| `review-project-evidence` | Is this project usable? | Read version and history; inspect official material using available authorized retrieval tools; identify knowns and unknowns; register evidence only when justified and authorized |
| `manage-dev-library` | Save this project and its potential use | Resolve the exact item; save bookmark/note; read back and report the persisted result |

Later Skills:
- `explain-development-method`: problem, implementation approach, reusable parts, applicability, and limitations.
- `observe-ai-trends`: observed windows, independent source counts, facts versus inference, counterevidence, and missing baselines.

The evidence-review Skill may require an authorized document reader beyond the initial nine Radar tools. If the material is unavailable, it must report the gap rather than claim the review occurred. The first release must not silently fetch or execute arbitrary repository code.

## Proposed code layout

```text
src/radar/
  services/
    collection.py
    catalog.py
    bookmarks.py
    verification.py
  app.py                 # HTTP adapter
  mcp_server.py          # MCP tool registration and adapters
  storage.py             # SQLite
  collectors.py          # External data retrieval
skills/
  daily-ai-brief/SKILL.md
  discover-dev-projects/SKILL.md
  review-project-evidence/SKILL.md
  manage-dev-library/SKILL.md
```

Extract existing behavior incrementally. Preserve HTTP compatibility and the existing dashboard while adding missing service contracts. Do not introduce a separate database or duplicate collection pipeline for MCP.

## Delivery phases and acceptance

| Phase | Deliverable | Required evidence |
| --- | --- | --- |
| 1 | Shared services | Existing dashboard behavior and regression suite remain passing |
| 2 | Read-only MCP tools | Client initialization, tool discovery, and actual read calls with validated results |
| 3 | Controlled mutation tools | Concurrency, duplicate requests, conflicting keys, invalid transitions, and read-back tests |
| 4 | Four business Skills | Real user scenarios demonstrate correct tool selection, source attribution, partial-failure reporting, and honest completion boundaries |
| 5 | Domestic-model assistant | Real model-backed question → tool call → sourced answer → follow-up → saved note workflow |

First delivery target: phases 1–4. Phase 5 depends on the selected model/provider, credentials, tool-calling compatibility, and budget. Offline fixtures, simulated model calls, and real provider validation must be reported separately.

## Current implementation boundary

The repository already contains a local collection dashboard and HTTP/SQLite business code. Project verification UI work is being developed separately. This document does **not** claim that an MCP server, the proposed business Skills, idempotency journal, or domestic-model assistant exists yet.
