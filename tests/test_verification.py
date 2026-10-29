import pytest
from fastapi.testclient import TestClient
from radar.app import create_app
from radar.storage import Store


def test_stages_evidence_and_refresh_survival(tmp_path):
    s=Store(tmp_path/'db')
    item={'url':'https://github.com/a/b','title':'a/b','kind':'repo','metadata':{'pushed_at':'2026-10-01T00:00:00Z'}}
    key=s.save(item,'GitHub')
    assert s.items()[0]['verification']['stage']=='discovered'
    with pytest.raises(ValueError): s.verify(key,'local_passed','abc','run log','scope')
    with pytest.raises(ValueError): s.verify(key,'docs_checked','abc','','scope')
    s.verify(key,'docs_checked','abc','https://github.com/a/b/blob/abc/README.md','README reviewed; not executed')
    s.save(item,'GitHub')
    row=s.items()[0]
    assert row['verification']['stage']=='docs_checked'
    assert not row['verification']['stale']
    item['metadata']['pushed_at']='2026-10-02T00:00:00Z'
    s.save(item,'GitHub')
    assert s.items()[0]['verification']['stale']
    assert len(s.verifications(key))==1


def test_verification_api_validation_and_filter(tmp_path):
    app=create_app(tmp_path/'db',auto=False)
    key=app.state.store.save({'url':'https://github.com/a/b','title':'a/b','kind':'repo'},'source')
    with TestClient(app) as c:
        payload={'stage':'docs_checked','version':'abc','evidence':'README checked','scope':'Documentation only'}
        assert c.put('/api/verifications/'+key,json=payload).status_code==200
        assert len(c.get('/api/items?stage=docs_checked').json()['items'])==1
        assert c.get('/api/items?stage=discovered').json()['items']==[]
        assert c.put('/api/verifications/'+key,json={**payload,'stage':'adopted'}).status_code==422
        assert c.get('/api/verifications/'+key).json()[0]['version']=='abc'


def test_progression_history_survives_restart(tmp_path):
    path=tmp_path/'db'
    s=Store(path)
    key=s.save({'url':'https://github.com/a/b','title':'a/b','kind':'repo'},'source')
    for stage in ('docs_checked','local_passed','adopted'):
        s.verify(key,stage,'fixed-sha','Recorded test evidence','Only the described workflow')
    assert Store(path).items()[0]['verification']['stage']=='adopted'
    assert [r['stage'] for r in Store(path).verifications(key)]==['adopted','local_passed','docs_checked']
