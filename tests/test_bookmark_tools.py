from concurrent.futures import ThreadPoolExecutor
import pytest
from radar.storage import Store


def test_bookmark_replay_conflict_and_restart(tmp_path):
    s=Store(tmp_path/'db')
    key=s.save({'url':'https://example.com/tool','title':'Tool','kind':'repo'},'fixture')
    first=s.bookmark_write('save',key,'Try this','request-1')
    assert first['bookmark']['note']=='Try this'
    assert Store(s.path).bookmark_write('save',key,'Try this','request-1')==first
    with pytest.raises(ValueError,match='CONFLICT'):
        s.bookmark_write('save',key,'Different','request-1')
    removed=s.bookmark_write('remove',key,'','request-2')
    assert removed['bookmarked'] is False
    s.bookmark_write('save',key,'New note','request-3')
    assert s.bookmark_write('remove',key,'','request-2')==removed
    assert s.items()[0]['note']=='New note'  # replay must not repeat an old deletion
    with pytest.raises(ValueError,match='NOT_FOUND'):
        s.bookmark_write('save','missing','','request-4')


def test_concurrent_identical_requests(tmp_path):
    s=Store(tmp_path/'db')
    key=s.save({'url':'https://example.com/tool','title':'Tool','kind':'repo'},'fixture')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:s.bookmark_write('save',key,'note','same-key'),range(8)))
    assert all(r==results[0] for r in results)
    with s.db() as c:
        assert c.execute('SELECT count(*) FROM mutation_requests').fetchone()[0]==1
    assert s.stats()['bookmarks']==1
