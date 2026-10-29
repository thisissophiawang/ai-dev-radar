"""Pinned-runtime launcher; keep the upstream browser bridge config local too."""
from pathlib import Path
import os


def main():
    root = Path(__file__).resolve().parents[1]
    home = root / 'data/qwenpaw-home'
    os.environ['QWENPAW_WORKING_DIR'] = str(home)
    os.environ['QWENPAW_TELEMETRY_DISABLED'] = '1'
    # QwenPaw 2.2.2.post1 hardcodes this optional bridge's default to ~/.qwenpaw.
    # Override its process-local state before app import, preserving isolation.
    from qwenpaw.browser.control_link.chrome.state import get_nm_bridge_route_state
    get_nm_bridge_route_state().config_path = home / 'nm-bridge.json'
    from qwenpaw.cli.main import cli
    cli(args=['app', '--host', '127.0.0.1', '--port', '8088'])


if __name__ == '__main__':
    main()
