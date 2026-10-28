import asyncio
import calendar
import html
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, urljoin, urlencode
import feedparser
import httpx
from .storage import canonical

ALLOWED = {'api.github.com', 'huggingface.co', 'github.blog'}
SEEDS=['obra/superpowers','jnMetaCode/superpowers-zh','github/spec-kit','modelcontextprotocol/python-sdk']
SOURCES=[{'id':'hf','name':'Hugging Face Blog','url':'https://huggingface.co/blog/feed.xml','kind':'rss'},
 {'id':'gh-blog','name':'GitHub Blog · AI','url':'https://github.blog/ai-and-ml/feed/','kind':'rss'}]
SOURCES += [{'id':'repo:'+r,'name':r,'url':'https://api.github.com/repos/'+r,'kind':'repo'} for r in SEEDS]
SOURCES += [{'id':'search:'+topic,'name':'GitHub · '+topic,'url':'https://api.github.com/search/repositories?'+urlencode({'q':query+' archived:false','sort':'updated','per_page':20}),'kind':'search'} for topic,query in [('MCP','topic:mcp-server'),('Skills','topic:agent-skills'),('AI coding','topic:ai-coding')]]


def plain(value):
    return html.unescape(re.sub('<[^>]+>',' ',value or '')).strip()[:2000]


async def fetch(client, url):
    for attempt in range(3):
        try:
            current=url
            for redirect in range(4):
                parsed=urlsplit(current)
                if parsed.scheme!='https' or parsed.hostname not in ALLOWED or parsed.port not in (None,443) or parsed.username:
                    raise ValueError('来源地址不在允许列表')
                headers={'User-Agent':'AI-Dev-Radar/0.1','Accept':'application/json' if parsed.hostname=='api.github.com' else 'application/rss+xml, application/atom+xml, application/xml'}
                token=os.getenv('GITHUB_TOKEN')
                if token and parsed.hostname=='api.github.com': headers['Authorization']='Bearer '+token
                async with client.stream('GET',current,headers=headers,follow_redirects=False,timeout=20) as r:
                    if r.status_code in (301,302,303,307,308):
                        current=urljoin(current,r.headers.get('location','')); continue
                    if r.status_code in (403,429):
                        raise ValueError('来源限制访问或额度不足；稍后重试（Retry-After='+r.headers.get('retry-after','未知')+'；reset='+r.headers.get('x-ratelimit-reset','未知')+'）')
                    if r.status_code==304: return None
                    r.raise_for_status()
                    body=bytearray()
                    async for chunk in r.aiter_bytes():
                        body.extend(chunk)
                        if len(body)>5*1024*1024: raise ValueError('来源内容超过5MB')
                    return bytes(body)
            raise ValueError('来源重定向过多')
        except (httpx.TimeoutException,httpx.NetworkError,httpx.HTTPStatusError):
            if attempt==2: raise ValueError('来源网络请求失败（已尝试3次）') from None
            await asyncio.sleep(attempt+1)


def parse_feed(body):
    feed=feedparser.parse(body)
    if not feed.entries and not feed.get('feed'): raise ValueError('无效订阅内容')
    items=[]
    for entry in feed.entries[:80]:
        try: url=canonical(entry.get('link',''))
        except ValueError: continue
        date=entry.get('published_parsed')
        published=datetime.fromtimestamp(calendar.timegm(date),timezone.utc).isoformat() if date else None
        items.append({'url':url,'title':plain(entry.get('title','Untitled')),'kind':'article','excerpt':plain(entry.get('summary','')),'published_at':published,'topic':'开发实践'})
    return items


def repo_item(repo):
    return {'url':repo['html_url'],'title':repo['full_name'],'kind':'repo','excerpt':repo.get('description') or '',
      'published_at':repo.get('pushed_at'),'topic':'MCP / AI 开发','metadata':{'stars':repo.get('stargazers_count',0),'language':repo.get('language'),'license':(repo.get('license') or {}).get('spdx_id'),'archived':repo.get('archived',False),'pushed_at':repo.get('pushed_at'),'topics':repo.get('topics',[])}}


async def collect_source(source):
    import json
    async with httpx.AsyncClient() as client:
        body=await fetch(client,source['url'])
    if body is None: return []
    if source['kind']=='rss': return parse_feed(body)
    data=json.loads(body)
    return [repo_item(r) for r in data['items']] if source['kind']=='search' else [repo_item(data)]
