import asyncio
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from radar.storage import Store


def test_stdio_catalog_and_followup(tmp_path):
    db=tmp_path/'radar.db'
    store=Store(db)
    key=store.save({'url':'https://github.com/example/crm','title':'CRM MCP','kind':'repo','metadata':{'pushed_at':'2026-10-01'}},'fixture')
    store.verify(key,'docs_checked','abc','README reviewed','Documentation only')
    run=store.new_run()
    store.finish(run,'partial',[{'id':'hf','state':'failed'}])
    async def scenario():
        params=StdioServerParameters(command=sys.executable,args=['-m','radar.mcp_server'],env={**os.environ,'PYTHONPATH':str(Path('src').resolve()),'RADAR_DB':str(db)})
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as client:
                await client.initialize()
                names={t.name for t in (await client.list_tools()).tools}
                assert {'radar_items_search','radar_item_get','radar_verification_history','radar_sources_list','radar_collection_status'} <= names
                result=await client.call_tool('radar_items_search',{'q':'CRM','stage':'docs_checked'})
                assert not result.isError
                assert result.structuredContent['items'][0]['id']==key
                detail=await client.call_tool('radar_item_get',{'item_id':key})
                assert detail.structuredContent['item']['url']=='https://github.com/example/crm'
                assert detail.structuredContent['item']['verification']['stage']=='docs_checked'
                history=await client.call_tool('radar_verification_history',{'item_id':key})
                assert history.structuredContent['history'][0]['version']=='abc'
                status=await client.call_tool('radar_collection_status',{'run_id':run})
                assert status.structuredContent['run']['state']=='partial'
                sources=await client.call_tool('radar_sources_list',{})
                assert sources.structuredContent['sources']
                missing=await client.call_tool('radar_item_get',{'item_id':'missing'})
                assert missing.isError
                invalid=await client.call_tool('radar_items_search',{'limit':100000})
                assert invalid.isError
    asyncio.run(scenario())
    assert store.stats()=={'repo':1,'bookmarks':0}
