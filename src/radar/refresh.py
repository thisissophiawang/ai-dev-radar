import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .collectors import SOURCES, collect_source

ZONE=ZoneInfo('Asia/Shanghai')


def due(now,last):
    if last is None: return True
    previous=datetime.fromisoformat(last).astimezone(ZONE)
    local=now.astimezone(ZONE)
    cutoff=local.replace(hour=9,minute=0,second=0,microsecond=0)
    return local>=cutoff and previous<cutoff


def next_due(now):
    local=now.astimezone(ZONE)
    target=local.replace(hour=9,minute=0,second=0,microsecond=0)
    return (target if target>local else target+timedelta(days=1)).isoformat()


class Collector:
    def __init__(self,store,sources=None,collect=None):
        self.store=store; self.sources=SOURCES if sources is None else sources
        self.collect=collect or collect_source
        self.task=None; self.current=None

    def start(self):
        if self.task and not self.task.done(): return self.current
        self.current=self.store.new_run()
        self.task=asyncio.create_task(self.run(self.current))
        return self.current

    async def run(self,key):
        results=[]
        try:
            for source in self.sources:
                try:
                    items=await self.collect(source)
                    for item in items: self.store.save(item,source['name'])
                    results.append({'source':source['name'],'state':'succeeded','count':len(items)})
                except Exception as exc:
                    # Only known sanitized operational messages are surfaced, never request headers.
                    message=str(exc) if isinstance(exc,ValueError) else '来源处理失败：'+type(exc).__name__
                    results.append({'source':source['name'],'state':'failed','count':0,'error':message[:300]})
            ok=sum(r['state']=='succeeded' for r in results)
            self.store.finish(key,'succeeded' if ok==len(results) else 'partial' if ok else 'failed',results)
        except asyncio.CancelledError:
            self.store.finish(key,'interrupted',results)
            raise

    async def schedule(self):
        while True:
            last=self.store.run()
            if due(datetime.now(ZONE),last['started_at'] if last else None): self.start()
            await asyncio.sleep(60)
