# AI Dev Radar

A local-first dashboard that collects AI engineering news and GitHub projects for MCP, agent skills, and AI coding. Built with Python, FastAPI, SQLite, and a buildless browser UI.

## Run locally

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
./scripts/start.sh
```

Open http://127.0.0.1:8000 . No Node build or cloud deployment is required. The startup script loads source directly; it avoids an editable-install encoding issue on Chinese directory paths.

The app collects on first startup, catches up after a missed daily run, and checks for the 09:00 Asia/Shanghai run every minute while running. Keep the terminal open and the computer awake for scheduled collection. Manual refresh is also available. Only one process/worker may use the database at a time.

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

## Development

- [Current project status](PROJECT_STATUS.md)
- [Project instructions](AGENTS.md)
- [MVP plan](docs/superpowers/plans/2026-10-28-ai-dev-radar-mvp.md)
- [Superpowers setup](docs/superpowers-setup.md)

Superpowers provides development skills; the runtime collector is ordinary application code and does not depend on an AI model.
