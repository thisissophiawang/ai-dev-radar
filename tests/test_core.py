import asyncio
import httpx
from fastapi.testclient import TestClient
from radar.storage import Store, canonical
from radar.collectors import parse_feed, fetch
from radar.app import create_app


def test_dedup_bookmark_restart(tmp_path):
    path = tmp_path/'test.db'
    store = Store(path)
    a = store.save({'url':'https://example.com/a?utm_source=x','title':'A','kind':'article'}, 'source')
    b = store.save({'url':'https://example.com/a','title':'B','kind':'article'}, 'source')
    assert a == b
    assert len(store.items()) == 1
    store.bookmark(a, '准备试用')
    assert Store(path).items(bookmarked=True)[0]['note'] == '准备试用'
    store.unbookmark(a)
    assert store.items(bookmarked=True) == []
    assert canonical('https://example.com/a?id=1') != canonical('https://example.com/a?id=2')


def test_feed_unknown_date_and_bad_links():
    items = parse_feed(b'<rss><channel><item><title>Hello</title><link>https://example.com/a</link></item><item><title>Bad</title><link>javascript:alert(1)</link></item></channel></rss>')
    assert len(items) == 1
    assert items[0]['published_at'] is None


def test_network_rate_limit_and_private_redirect():
    async def run():
        for code, headers in [(429, {'Retry-After':'60'}), (302, {'Location':'http://127.0.0.1/x'})]:
            async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(code,headers=headers))) as client:
                try:
                    await fetch(client,'https://huggingface.co/blog/feed.xml')
                except ValueError:
                    pass
                else:
                    assert False, 'Unsafe or rate-limited request accepted'
    asyncio.run(run())


def test_api_bookmark_and_html(tmp_path):
    app = create_app(tmp_path/'test.db', auto=False)
    item_id = app.state.store.save({'url':'https://example.com/a','title':'<script>alert(1)</script>','kind':'article'},'source')
    with TestClient(app) as client:
        assert client.get('/').status_code == 200
        assert client.put('/api/bookmarks/nope',json={'note':'a'}).status_code == 404
        assert client.put('/api/bookmarks/'+item_id,json={'note':'x'*5001}).status_code == 422
        assert client.put('/api/bookmarks/'+item_id,json={'note':'试用'}).status_code == 200
        assert client.get('/api/items?bookmarked=true').json()['items'][0]['note'] == '试用'
        assert client.delete('/api/bookmarks/'+item_id).status_code == 204


def test_refresh_partial_and_concurrent(tmp_path):
    from radar.refresh import Collector
    store = Store(tmp_path/'test.db')
    async def collect(source):
        await asyncio.sleep(.01)
        if source['id']=='bad': raise ValueError('offline')
        return [{'url':'https://example.com/a','title':'A','kind':'article'}]
    worker = Collector(store, sources=[{'id':'ok','name':'OK'},{'id':'bad','name':'Bad'}], collect=collect)
    async def run():
        a = worker.start()
        assert worker.start() == a
        await worker.task
        assert store.run(a)['state'] == 'partial'
        assert len(store.items()) == 1
        b = worker.start()
        await worker.task
        assert len(store.items()) == 1
    asyncio.run(run())


def test_recover_running_and_daily_due(tmp_path):
    from radar.refresh import due
    from datetime import datetime
    from zoneinfo import ZoneInfo
    s = Store(tmp_path/'test.db')
    rid=s.new_run()
    s.recover()
    assert s.run(rid)['state']=='interrupted'
    now=datetime(2026,10,28,10,tzinfo=ZoneInfo('Asia/Shanghai'))
    assert due(now,None)
    assert not due(now,'2026-10-28T01:00:00+00:00')


def test_nine_am_due_after_early_startup():
    from radar.refresh import due
    from datetime import datetime
    from zoneinfo import ZoneInfo
    now=datetime(2026,10,28,9,tzinfo=ZoneInfo('Asia/Shanghai'))
    assert due(now,'2026-10-28T00:00:00+00:00')
    assert not due(now,'2026-10-28T01:00:00+00:00')


def test_local_api_rejects_foreign_origin(tmp_path):
    with TestClient(create_app(tmp_path/'test.db',auto=False)) as client:
        assert client.post('/api/refresh',headers={'Origin':'https://evil.example'}).status_code==403
        assert client.get('/api/status',headers={'Host':'evil.example'}).status_code==403
