"""Generate an opt-in MCP config after actual read-only protocol checks.
Does not install/configure QwenPaw or contact a model provider.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED={'radar_items_search','radar_item_get','radar_verification_history','radar_sources_list','radar_collection_status','radar_bookmark_save','radar_bookmark_remove'}


async def check(config):
    params=StdioServerParameters(**config)
    async with asyncio.timeout(20):
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as client:
                await client.initialize()
                tools={t.name for t in (await client.list_tools()).tools}
                if tools!=EXPECTED:
                    raise RuntimeError('Unexpected MCP tool catalog')
                for name,args in [('radar_sources_list',{}),('radar_items_search',{'limit':1})]:
                    result=await client.call_tool(name,args)
                    if result.isError or result.structuredContent is None:
                        raise RuntimeError('MCP read check failed: '+name)
                return len(tools)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if not args.db.is_file(): parser.error('Database must already exist')
    if args.output.exists(): parser.error('Output exists; choose a new path to preserve existing configuration')
    root=Path(__file__).resolve().parents[1]
    config={'command':sys.executable,'args':['-m','radar.mcp_server'],'env':{'PYTHONPATH':str(root/'src'),'RADAR_DB':str(args.db.resolve())}}
    count=asyncio.run(check(config))
    # Exclusive creation: never overwrite client settings, even in a race.
    with args.output.open('x') as f:
        json.dump({'mcpServers':{'ai-dev-radar':config}},f,ensure_ascii=False,indent=2)
        f.write('\n')
    print(json.dumps({'mcp_status':'passed','tool_count':count,'model_status':'not_tested','qwenpaw_status':'not_tested','config':str(args.output.resolve())}))


if __name__=='__main__':
    main()
