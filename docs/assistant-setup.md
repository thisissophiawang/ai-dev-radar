# Local assistant setup and acceptance

Updated: 2026-10-29. QwenPaw **2.2.2.post1** is installed in an isolated environment under `data/qwenpaw-venv`. Radar keeps its existing `.venv`; neither environment replaces the system Python.

## What is verified

- Official release metadata: `v2.2.2.post1`, target commit `b6715daabaa4f966626317452980fb84b8be9ab9`.
- Official runtime configuration models load the default workspace with seven Radar tools and the real dashboard database path.
- QwenPaw's actual `StdIOStatefulClient` initializes Radar MCP, discovers seven tools, and calls source listing and item search against the existing database.
- QwenPaw's Skill service parses, scans, enables, and lists `discover-dev-projects` and `manage-dev-library` as available for the Console workspace. This proves runtime availability, not correct model behavior.
- The Console is reachable on `http://127.0.0.1:8088/`; its Models page includes Kimi configuration.
- The default research agent explicitly selects `kimi-cn / kimi-k2.5` as a pending candidate, preventing inheritance of the runtime's default free router. This is not a statement about the user's account entitlement or model compatibility.

## Start on this machine

From the repository root:

```sh
sh scripts/start_assistant.sh
```

Open **http://127.0.0.1:8088/**. Use the **Default Agent** for Radar research. The assistant uses `data/qwenpaw-home`, distinct from any global QwenPaw installation. The runtime also creates its standard QA helper; that helper is not the Radar acceptance target.

The launcher sets `QWENPAW_WORKING_DIR` and disables optional telemetry. An upstream bridge path still defaults to `~/.qwenpaw` in this release; `scripts/run_assistant.py` sets its process-local path to the isolated home before app startup. No upstream package files are patched. Built-in shell/browser/file-writing tools are disabled for the research agent; file reading remains available for Skill instructions.

## Fresh setup on another machine

Requires Python 3.12, a configured Radar `.venv`, and an existing Radar database:

```sh
uv venv --python .venv/bin/python data/qwenpaw-venv
uv pip install --python data/qwenpaw-venv/bin/python 'qwenpaw==2.2.2.post1'
data/qwenpaw-venv/bin/python scripts/setup_qwenpaw.py --db data/radar.sqlite3
sh scripts/start_assistant.sh
```

Setup refuses an existing home; it never resets conversations or credentials. If initialization fails, inspect the new directory and its error log before choosing a fresh `--home`. A custom `--home` is useful for tests; the standard launcher deliberately targets `data/qwenpaw-home` only. The local package snapshot is `data/qwenpaw-requirements.lock`; runtime configuration/report, database, keys and packages stay Git-ignored. Installation may use different compatible dependency versions on another platform.

The generic configuration generator remains available for other clients:

```sh
.venv/bin/python scripts/prepare_assistant.py --db data/radar.sqlite3 --output data/another-client.json
```

It checks the actual MCP protocol before exclusively creating output. It does not install or modify a client.

## Configure the model locally

1. Open **Models → Global models → Kimi → Configure**.
2. Enter the API credential locally and check that the China endpoint and model are available to your account. Never put a key in Git or send it in chat.
3. Under **Current agent**, choose your actually available tool-calling model. The configured `kimi-k2.5` is a candidate, not a requirement; choose a different account-supported model if necessary.
4. Return to Chat using **Default Agent**. The configured model receives questions and the retrieved data needed to answer them. Local collection and model inference are separate boundaries.

No model key was supplied and no real conversational model acceptance was performed in this increment. Automatic source refresh and the assistant are independent processes; MCP reads do not start another scheduler.

## Three-turn acceptance (pending)

| Turn | Copyable question | Required observable evidence |
| --- | --- | --- |
| 1 | 推荐几个值得关注的 AI 开发工具，说明来源、采集时间和验证状态。 | Actual source/search/detail tool calls; numbered items retain stable IDs; no invention of freshness or quality |
| 2 | 第二个怎么用，是否已经在本地跑通？ | Same displayed item ID; actual verification-history read; honest version/scope/stale limits |
| 3 | 把它收藏，备注“准备研究其开发方法”。 | Explicit save tool, same request key on retries, separate item_get read-back, matching Dashboard bookmark |
| New session | 查看我刚刚收藏的项目及备注。 | Search with bookmarked=true; state survives session boundaries |
| Failure | Repeat while model/network is unavailable. | Visible failure; no fabricated answer, write receipt or collection claim |

Record date, runtime version, selected model, tool calls, item IDs and result status in a local acceptance report. Do not include credentials. Only after this real-model loop passes should Dashboard's chat adapter be implemented against the inspected runtime REST/session contracts.

## Development sequence

See [executable plan](superpowers/plans/2026-10-29-qwenpaw-assistant.md): existing services → isolated runtime → MCP reads and Skill availability → real model conversation → Dashboard adapter. The first stages are implemented; the last two remain pending model configuration and behavioral acceptance.

Primary references inspected:
- [Official fixed release](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.2.post1)
- [MCP configuration at the inspected commit](https://github.com/agentscope-ai/QwenPaw/blob/b6715daabaa4f966626317452980fb84b8be9ab9/website/public/docs/mcp.en.md)
- [Workspace Skill lifecycle at the inspected commit](https://github.com/agentscope-ai/QwenPaw/blob/b6715daabaa4f966626317452980fb84b8be9ab9/website/public/docs/skills.en.md)
- [Kimi provider source](https://github.com/agentscope-ai/QwenPaw/blob/b6715daabaa4f966626317452980fb84b8be9ab9/src/qwenpaw/providers/provider_catalog.py)
