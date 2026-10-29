"""Import explicitly reviewed project documentation using an authenticated gh CLI.
Run manually, never as part of the scheduled collector. Does not execute repository code.
"""
import json
import subprocess
from pathlib import Path
from radar.storage import Store, stamp
from radar.collectors import repo_item

REVIEWS={
 'jnMetaCode/superpowers-zh':'适用于本项目的需求、计划、测试与审查流程。已核对README的项目级/用户级安装和21个技能说明；本记录仅证明文档核查，不证明所有附带脚本可用。',
 'github/spec-kit':'适用于需求规格到任务拆解。README要求Python 3.11+与uv，提供specify/init及规格流程；与现有Superpowers存在功能重叠，暂不额外安装，未实测CLI。',
 'modelcontextprotocol/python-sdk':'适用于后续把采集查询暴露给AI助手。README说明Python 3.11+，MCPServer/Client及stdio/HTTP示例；当前dashboard尚未接入MCP，未验证SDK运行或业务适配。'
}
def get(path):
    return json.loads(subprocess.check_output(['gh','api',path],text=True))
if __name__=='__main__':
    store=Store('data/radar.sqlite3')
    for repo,scope in REVIEWS.items():
        metadata=get('repos/'+repo)
        commit=get('repos/'+repo+'/commits/HEAD')['sha']
        # Fetch pinned README again to make evidence reproducible at the recorded commit.
        readme=get('repos/'+repo+'/contents/README.md?ref='+commit)
        import base64,hashlib
        content=base64.b64decode(readme['content'])
        evidence='https://github.com/'+repo+'/blob/'+commit+'/README.md'
        key=store.save(repo_item(metadata),'GitHub · authenticated documentation review')
        store.verify(key,'docs_checked',commit,evidence,scope)
        report={'repo':repo,'stage':'docs_checked','checked_at':stamp(),'commit':commit,'readme_sha256':hashlib.sha256(content).hexdigest(),'evidence':evidence,'scope':scope,'executed':False}
        Path('docs/verifications/'+repo.replace('/','--')+'.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(repo, 'docs_checked',commit[:12])
