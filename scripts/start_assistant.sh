#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export QWENPAW_WORKING_DIR="$ROOT/data/qwenpaw-home"
export QWENPAW_TELEMETRY_DISABLED=1
if [ ! -f "$QWENPAW_WORKING_DIR/radar-setup-report.json" ]; then
  echo 'Run scripts/setup_qwenpaw.py with the isolated QwenPaw Python first.' >&2
  exit 1
fi
cd "$ROOT"
exec "$ROOT/data/qwenpaw-venv/bin/python" "$ROOT/scripts/run_assistant.py"
