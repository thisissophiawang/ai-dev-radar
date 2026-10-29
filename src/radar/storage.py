import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from zoneinfo import ZoneInfo


def stamp():
    return datetime.now(timezone.utc).isoformat()


def canonical(url):
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username:
        raise ValueError('无效的来源链接')
    query = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith('utm_') and k != 'fbclid']
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', urlencode(sorted(query)), ''))


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS mutation_requests(request_key TEXT PRIMARY KEY,payload TEXT NOT NULL,result TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,url TEXT UNIQUE,title TEXT,kind TEXT,
              excerpt TEXT,published_at TEXT,fetched_at TEXT,topic TEXT,metadata TEXT);
            CREATE TABLE IF NOT EXISTS item_sources(item_id TEXT,source TEXT,PRIMARY KEY(item_id,source));
            CREATE TABLE IF NOT EXISTS bookmarks(item_id TEXT PRIMARY KEY REFERENCES items(id),note TEXT,updated_at TEXT);
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,state TEXT,started_at TEXT,finished_at TEXT,results TEXT);
            CREATE TABLE IF NOT EXISTS verifications(seq INTEGER PRIMARY KEY AUTOINCREMENT,item_id TEXT REFERENCES items(id),stage TEXT,version TEXT,evidence TEXT,scope TEXT,checked_at TEXT,observed_push TEXT);
            CREATE TABLE IF NOT EXISTS snapshots(item_id TEXT,day TEXT,stars INTEGER,PRIMARY KEY(item_id,day));
            ''')

    @contextmanager
    def db(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        try:
            with c: yield c
        finally:
            c.close()

    def save(self, item, source):
        url = canonical(item['url'])
        key = hashlib.sha256(url.encode()).hexdigest()[:24]
        meta = item.get('metadata', {})
        with self.db() as c:
            c.execute('''INSERT INTO items VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,excerpt=excluded.excerpt,published_at=excluded.published_at,
            fetched_at=excluded.fetched_at,topic=excluded.topic,metadata=excluded.metadata''',
            (key,url,item['title'],item['kind'],item.get('excerpt',''),item.get('published_at'),stamp(),item.get('topic','AI'),json.dumps(meta)))
            c.execute('INSERT OR IGNORE INTO item_sources VALUES(?,?)',(key,source))
            if item['kind']=='repo':
                day = datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
                c.execute('INSERT INTO snapshots VALUES(?,?,?) ON CONFLICT(item_id,day) DO UPDATE SET stars=excluded.stars',(key,day,meta.get('stars',0)))
        return key

    def items(self, kind=None, q='', bookmarked=False, sort='recent', limit=100, offset=0, stage=None, item_id=None):
        sql = 'SELECT i.*,b.note,b.item_id IS NOT NULL AS bookmarked FROM items i LEFT JOIN bookmarks b ON b.item_id=i.id WHERE 1=1'
        args=[]
        if item_id is not None: sql+=' AND i.id=?'; args.append(item_id)
        if kind: sql+=' AND kind=?'; args.append(kind)
        if q: sql+=" AND (title LIKE ? OR excerpt LIKE ?)"; args.extend(['%'+q+'%']*2)
        if bookmarked: sql+=' AND b.item_id IS NOT NULL'
        if stage:
            sql+=" AND kind='repo' AND COALESCE((SELECT stage FROM verifications v WHERE v.item_id=i.id ORDER BY seq DESC LIMIT 1),'discovered')=?"; args.append(stage)
        if sort=='stars': sql+=" ORDER BY CAST(json_extract(metadata,'$.stars') AS INTEGER) DESC,i.id"
        else: sql+=' ORDER BY published_at IS NULL,published_at DESC,i.id'
        sql+=' LIMIT ? OFFSET ?'; args.extend([limit,offset])
        with self.db() as c:
            rows=[dict(r) for r in c.execute(sql,args)]
            for row in rows:
                row['metadata']=json.loads(row['metadata'])
                v=c.execute('SELECT * FROM verifications WHERE item_id=? ORDER BY seq DESC LIMIT 1',(row['id'],)).fetchone()
                row['verification']=dict(v) if v else {'stage':'discovered','checked_at':None}
                row['verification']['stale']=bool(v and v['observed_push']!=row['metadata'].get('pushed_at'))
                row['sources']=[r[0] for r in c.execute('SELECT source FROM item_sources WHERE item_id=?',(row['id'],))]
        return rows

    def bookmark(self, key, note):
        with self.db() as c:
            if not c.execute('SELECT 1 FROM items WHERE id=?',(key,)).fetchone(): raise KeyError(key)
            c.execute('INSERT INTO bookmarks VALUES(?,?,?) ON CONFLICT(item_id) DO UPDATE SET note=excluded.note,updated_at=excluded.updated_at',(key,note,stamp()))
            return dict(c.execute('SELECT * FROM bookmarks WHERE item_id=?',(key,)).fetchone())

    def unbookmark(self,key):
        with self.db() as c: c.execute('DELETE FROM bookmarks WHERE item_id=?',(key,))

    def new_run(self):
        key=uuid.uuid4().hex
        with self.db() as c: c.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(key,'running',stamp(),None,'[]'))
        return key

    def finish(self,key,state,results):
        with self.db() as c: c.execute('UPDATE runs SET state=?,finished_at=?,results=? WHERE id=?',(state,stamp(),json.dumps(results),key))

    def run(self,key=None):
        with self.db() as c:
            r=c.execute('SELECT * FROM runs WHERE id=?',(key,)).fetchone() if key else c.execute('SELECT * FROM runs ORDER BY started_at DESC LIMIT 1').fetchone()
        if not r: return None
        result=dict(r); result['results']=json.loads(result['results']); return result

    def recover(self):
        with self.db() as c: c.execute("UPDATE runs SET state='interrupted',finished_at=? WHERE state='running'",(stamp(),))

    def stats(self):
        with self.db() as c:
            counts={r[0]:r[1] for r in c.execute('SELECT kind,count(*) FROM items GROUP BY kind')}
            counts['bookmarks']=c.execute('SELECT count(*) FROM bookmarks').fetchone()[0]
        return counts

    def verify(self,key,stage,version,evidence,scope):
        stages=['discovered','docs_checked','local_passed','adopted']
        if stage not in stages[1:] or not all(v.strip() for v in (version,evidence,scope)):
            raise ValueError('必须填写版本、证据和验证范围')
        with self.db() as c:
            item=c.execute('SELECT * FROM items WHERE id=?',(key,)).fetchone()
            if not item: raise KeyError(key)
            if item['kind']!='repo': raise ValueError('只有项目支持验证状态')
            latest=c.execute('SELECT stage FROM verifications WHERE item_id=? ORDER BY seq DESC LIMIT 1',(key,)).fetchone()
            current=latest[0] if latest else 'discovered'
            if stages.index(stage)>stages.index(current)+1: raise ValueError('请先完成前一阶段验证')
            c.execute('INSERT INTO verifications(item_id,stage,version,evidence,scope,checked_at,observed_push) VALUES(?,?,?,?,?,?,?)',
                      (key,stage,version.strip(),evidence.strip(),scope.strip(),stamp(),json.loads(item['metadata']).get('pushed_at')))
            return dict(c.execute('SELECT * FROM verifications WHERE seq=last_insert_rowid()').fetchone())

    def verifications(self,key):
        with self.db() as c:
            if not c.execute('SELECT 1 FROM items WHERE id=?',(key,)).fetchone(): raise KeyError(key)
            return [dict(r) for r in c.execute('SELECT * FROM verifications WHERE item_id=? ORDER BY seq DESC',(key,))]

    def bookmark_write(self, operation, key, note, request_key):
        if operation not in ('save','remove') or not request_key.strip() or len(request_key)>200 or len(note)>5000:
            raise ValueError('INVALID_INPUT: invalid bookmark request')
        payload=json.dumps([operation,key,note],ensure_ascii=False)
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT payload,result FROM mutation_requests WHERE request_key=?',(request_key,)).fetchone()
            if old:
                if old['payload']!=payload: raise ValueError('CONFLICT: request key already used with different arguments')
                return json.loads(old['result'])
            if not c.execute('SELECT 1 FROM items WHERE id=?',(key,)).fetchone():
                raise ValueError('NOT_FOUND: item does not exist')
            if operation=='save':
                c.execute('INSERT INTO bookmarks VALUES(?,?,?) ON CONFLICT(item_id) DO UPDATE SET note=excluded.note,updated_at=excluded.updated_at',(key,note,stamp()))
            else:
                c.execute('DELETE FROM bookmarks WHERE item_id=?',(key,))
            row=c.execute('SELECT * FROM bookmarks WHERE item_id=?',(key,)).fetchone()
            result={'item_id':key,'bookmarked':row is not None,'bookmark':dict(row) if row else None,'request_key':request_key}
            c.execute('INSERT INTO mutation_requests VALUES(?,?,?)',(request_key,payload,json.dumps(result)))
            return result
