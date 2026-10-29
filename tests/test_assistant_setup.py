import json
import os
from pathlib import Path
import subprocess
import sys
from radar.storage import Store


def test_setup_checks_actual_mcp_and_generates_portable_config(tmp_path):
    db=tmp_path/'local data.db'
    Store(db)
    out=tmp_path/'client.json'
    result=subprocess.run([sys.executable,'scripts/prepare_assistant.py','--db',str(db),'--output',str(out)],capture_output=True,text=True,timeout=30,env={**os.environ,'PYTHONPATH':str(Path('src').resolve())})
    assert result.returncode==0, result.stderr
    report=json.loads(result.stdout)
    assert report['mcp_status']=='passed'
    assert report['tool_count']==7
    assert report['model_status']=='not_tested'
    cfg=json.loads(out.read_text())['mcpServers']['ai-dev-radar']
    assert cfg['env']['RADAR_DB']==str(db.resolve())
    assert cfg['command']==sys.executable
    before=out.read_bytes()
    repeat=subprocess.run([sys.executable,'scripts/prepare_assistant.py','--db',str(db),'--output',str(out)],capture_output=True,text=True,timeout=30)
    assert repeat.returncode!=0
    assert out.read_bytes()==before


def test_setup_does_not_create_missing_database(tmp_path):
    db=tmp_path/'missing.db'
    result=subprocess.run([sys.executable,'scripts/prepare_assistant.py','--db',str(db),'--output',str(tmp_path/'client.json')],capture_output=True,text=True,timeout=30)
    assert result.returncode!=0
    assert not db.exists()
