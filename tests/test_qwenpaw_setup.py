"""Catch setup overwriting a live workspace or pointing MCP at another DB."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
from radar.storage import Store

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'data/qwenpaw-venv/bin/python'


def setup(python, db, home):
    return subprocess.run([str(python), 'scripts/setup_qwenpaw.py', '--db', str(db),
                           '--home', str(home)], cwd=ROOT, capture_output=True,
                          text=True, timeout=120)


def test_missing_database_does_not_initialize_runtime(tmp_path):
    home = tmp_path / 'assistant'
    result = setup(sys.executable, tmp_path / 'missing.db', home)
    assert result.returncode != 0
    assert 'Database must already exist' in result.stderr
    assert not home.exists()


def test_existing_workspace_is_never_overwritten(tmp_path):
    db = tmp_path / 'radar.db'
    Store(db)
    home = tmp_path / 'assistant'
    home.mkdir()
    state = home / 'config.json'
    state.write_text('{"preserve":"session and model settings"}')
    before = state.read_bytes()
    result = setup(sys.executable, db, home)
    assert result.returncode != 0
    assert 'already exists' in result.stderr
    assert state.read_bytes() == before


@pytest.mark.skipif(not RUNTIME.exists(), reason='Optional isolated QwenPaw runtime not installed')
def test_real_runtime_loads_workspace_skills_and_radar_config(tmp_path):
    db = tmp_path / 'radar data.db'
    Store(db)
    home = tmp_path / 'assistant home'
    result = setup(RUNTIME, db, home)
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads((home / 'radar-setup-report.json').read_text())
    assert report['version'] == '2.2.2.post1'
    assert report['model_acceptance'] == 'not_tested'
    assert report['runtime_tool_connection'] == 'passed'
    assert set(report['skills_available']) == {'discover-dev-projects', 'manage-dev-library'}
    profile = json.loads((home / 'workspaces/default/agent.json').read_text())
    assert profile['active_model']['provider_id'] == 'kimi-cn'
    client = profile['mcp']['clients']['ai-dev-radar']
    assert client['env']['RADAR_DB'] == str(db.resolve())
    assert Path(client['command']).is_file()
    assert len(client['tools']) == 7
    assert client['cwd'] == str(ROOT)
    for name in ('discover-dev-projects', 'manage-dev-library'):
        assert (home / 'workspaces/default/skills' / name / 'SKILL.md').is_file()
    assert not profile['tools']['builtin_tools']['execute_shell_command']['enabled']
