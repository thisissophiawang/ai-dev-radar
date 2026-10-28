import asyncio
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Literal
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .storage import Store
from .refresh import Collector, next_due, ZONE


class Note(BaseModel):
    note: str=Field(default='',max_length=5000)


def create_app(db_path=None,auto=True):
    store=Store(db_path or os.getenv('RADAR_DB','data/radar.sqlite3'))
    worker=Collector(store)
    @asynccontextmanager
    async def lifespan(app):
        store.recover()
        task=asyncio.create_task(worker.schedule()) if auto else None
        yield
        for t in (task,worker.task):
            if t:
                t.cancel()
                with suppress(asyncio.CancelledError): await t
    app=FastAPI(lifespan=lifespan)
    app.state.store=store; app.state.worker=worker
    static=Path(__file__).parent/'static'
    app.mount('/static',StaticFiles(directory=static),name='static')

    @app.middleware('http')
    async def local_only(request: Request,call_next):
        # Guard against cross-origin websites triggering local writes and DNS rebinding.
        host=request.headers.get('host','').split(':')[0]
        if host not in ('127.0.0.1','localhost','testserver'): return JSONResponse({'detail':'Local access only'},status_code=403)
        origin=request.headers.get('origin')
        if origin and origin not in ('http://'+request.headers.get('host',''),'https://'+request.headers.get('host','')):
            return JSONResponse({'detail':'Cross-origin request rejected'},status_code=403)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        return response

    @app.get('/')
    def index(): return FileResponse(static/'index.html')
    @app.get('/api/health')
    def health(): return {'status':'ok'}
    @app.get('/api/items')
    def items(kind: Literal['article','repo']|None=None,q: str=Query('',max_length=200),bookmarked: bool=False,sort: Literal['recent','stars']='recent',limit: int=Query(40,ge=1,le=100),offset: int=Query(0,ge=0)):
        return {'items':store.items(kind,q,bookmarked,sort,limit,offset)}
    @app.get('/api/status')
    def status(): return {'counts':store.stats(),'run':store.run(),'next_run':next_due(datetime.now(ZONE)),'auto':auto}
    @app.post('/api/refresh',status_code=202)
    async def refresh(): return {'run_id':worker.start()}
    @app.get('/api/runs/{key}')
    def run(key: str):
        data=store.run(key)
        if not data: raise HTTPException(404,'任务不存在')
        return data
    @app.put('/api/bookmarks/{key}')
    def bookmark(key: str,note: Note):
        try: return store.bookmark(key,note.note)
        except KeyError: raise HTTPException(404,'内容不存在')
    @app.delete('/api/bookmarks/{key}',status_code=204)
    def remove(key: str):
        store.unbookmark(key)
        return Response(status_code=204)
    return app

app=create_app()
