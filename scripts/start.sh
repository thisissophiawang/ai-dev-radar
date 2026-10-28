#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  echo '请先按 README 安装独立环境。'; exit 1
fi
export PYTHONPATH="$PWD/src"
export PYTHONUTF8=1
exec .venv/bin/python -m uvicorn radar.app:app --host 127.0.0.1 --port "${RADAR_PORT:-8000}" --workers 1
