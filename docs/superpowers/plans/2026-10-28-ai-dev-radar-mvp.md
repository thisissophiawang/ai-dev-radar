# AI Dev Radar 最小闭环实现计划

> **面向 AI 代理的工作者：** 使用 executing-plans 逐任务执行；每项先写失败测试，再做最小实现，最后回读验收。默认单执行者，不启动并行实现。

**目标：** 每天打开本地页面，获得真实 AI 资讯和 MCP / AI coding 项目，理解值得关注的原因，并收藏留待实践。

**架构：** Python FastAPI 提供采集、查询和收藏接口，SQLite 持久化；首版使用服务端 HTML 模板与少量原生 JavaScript，降低前后端工具链成本。先完成采集与收藏闭环，再接一个模型完成中文开发分析。

**技术栈：** Python 3.12、FastAPI、Jinja2、sqlite3、httpx、feedparser、pytest；浏览器验收用 Playwright。实施时核实兼容版本并锁定依赖。

**规格：** `../specs/2026-10-28-ai-dev-radar-design.md` 为长期背景；本计划的范围与契约调整优先。原10项计划保留为后续路线，不与本计划同时执行。

## 本次明确的范围调整
用户明确要求以最小闭环为目标。以下是据此提出的实施选择，不冒充用户指定技术栈：
- 第一版只做一页，三个标签：资讯、项目、收藏；详情用侧栏或展开区域。
- 用FastAPI模板直接提供页面，暂不引入React/Node构建。数据服务保持独立，将来需要时再换前端。
- 第一版按Star热度、最近维护时间、兴趣词匹配筛选项目，标“候选”；不实现缺乏证据的综合质量评分。
- 每天首次打开页面触发更新，另有手动刷新；不做常驻定时器或macOS后台服务。用户不开页面时不保证采集。
- 先不做趋势图、自动执行外部项目、多代理编排、MCP server、复杂方法知识库。
- 中文摘要和开发方法拆解列为第二个小闭环；完成第一个闭环不能宣称用户全部目标已完成。

## 两个里程碑
M1：真实资讯/项目 → 去重保存 → 本地页面 → 查看原文 → 收藏/笔记 → 重启回读。完成Task 1—4。
M2：有来源的资料 → 中文解释与开发方法 → 个人应用建议 → 收藏。完成Task 5及真实模型验收。
趋势需求保留：从Task 2开始记每日仓库快照，但先不展示历史不足的曲线。真实历史充足后再启用7/30天观察；首版不声称已经识别行业风向。

## 全局约束与接口
只绑定127.0.0.1；SQLite存data/radar.sqlite3，数据库与.env不提交；日志不输出密钥。
一个Uvicorn worker；后台刷新使用进程锁，重复点击返回同一run_id；多进程部署不在本期。
时间存UTC，按Asia/Shanghai展示。发布时间未知保持null，不用采集时间充当发布时间。
HTTP请求20秒超时、5MB上限，最多3次尝试；429延后并显示下次可重试时间，不等待长时间阻塞请求。
固定公开HTTPS来源，重定向重新核验目标；不允许自定义任意URL或访问私网地址。
外部内容仅作为资料；HTML模板自动转义，模型没有执行工具或读取密钥的权限。

SQLite表：items、item_sources、bookmarks、runs、source_status、repo_snapshots、analyses。
Item字段：id、kind(article/repo)、canonical_url(唯一)、title、excerpt、published_at(可空)、fetched_at、topic、metadata_json、content_hash。
项目metadata含full_name/stars/pushed_at/archived/license(可空)，不将README声明等同于实测结果。
Bookmark字段：item_id(唯一)、note、updated_at；支持添加、编辑、取消。
Run状态：running/succeeded/partial/failed/interrupted；source_status记录各源最后成功时间及错误。
RepoSnapshot唯一键(repo_id,上海日期)，存stars；同日覆盖，不制造多个历史点。
Analysis字段：item_id/content_hash/provider/model/prompt_version为缓存键，另存summary/problem/approach/application/limitations/evidence_urls/status。

接口：
- GET / → HTML；GET /api/items?kind=article|repo&bookmarked=false&q=&limit=20&offset=0。
- GET /api/items/{id} → 详情含来源和收藏状态；GET /api/status → 最近刷新与来源状态。
- POST /api/refresh → 202 {run_id}；GET /api/runs/{id} → 状态及各源结果。
- PUT /api/bookmarks/{id} {note} → 回读后的收藏；DELETE /api/bookmarks/{id} → 204。
- POST /api/analyses/{id} → 202，详情接口读取生成状态；未配置模型返回503 MODEL_NOT_CONFIGURED。
- 错误统一{code,message}；不存在的item返回404；limit为1..100，note最多5000字。

## 文件职责
```
pyproject.toml / requirements.lock     包、测试、依赖
src/radar/app.py                       页面和HTTP入口，生命周期
src/radar/models.py                    数据契约
src/radar/storage.py                   建表、去重、查询、收藏回读
src/radar/collectors.py                GitHub/RSS，网络约束
src/radar/refresh.py                   刷新锁、来源状态、启动恢复
src/radar/analysis.py                  单一模型适配、结果校验与缓存
src/radar/templates/index.html         一页三个标签
src/radar/static/app.js / style.css    页面交互和样式
config/sources.json                    已核实来源与项目查询
scripts/start.sh                       启动本地服务
.env.example                          凭据与模型占位值
 tests/                               离线行为测试、HTTP fixtures、浏览器测试
 docs/acceptance-mvp.md                真实验收结果
```

## 审查重点
- 两次刷新及同源重复内容：不能多次入库（Task 1/2）。
- 一个源429或超时：其他源结果保留、旧内容仍可读（Task 2）。
- 重启时旧任务仍running：标interrupted，允许后续刷新（Task 2）。
- 恶意HTML、私网重定向：文本转义、请求拒绝（Task 2/3）。
- 无模型/模型编造引用：核心浏览可用、错误显式、伪造引用拒收（Task 5）。

## Task 1：本地数据与收藏可用
文件：pyproject.toml、models.py、storage.py、app.py；tests/test_storage.py、test_api.py。
接口：`init_db(path: Path) -> None`；`upsert_item(conn, item: Item) -> str`返回稳定id；`save_bookmark(conn, item_id: str, note: str) -> Bookmark`。
- [ ] 建立Python 3.12隔离环境，不改系统Python；定义包radar和dev依赖。
- [ ] 写失败测试：同一canonical_url两次保存返回同id，items行数=1；关闭并重开DB后笔记="准备试用"；未知id收藏返回404。
- [ ] 运行 `.venv/bin/python -m pytest tests/test_storage.py tests/test_api.py -q`，确认目标行为缺失导致失败。
- [ ] 实现建表、事务、UPSERT、列表和收藏接口；迁移初期使用PRAGMA user_version=1，发现更高版本拒绝静默降级。
- [ ] 再跑同一命令，全部通过；包含取消收藏后列表不再显示、笔记超长422的断言。
验收：真实临时数据库重开回读正确；此时仅证明数据闭环，不算真实资讯采集成功。

## Task 2：真实采集并可重复刷新
文件：collectors.py、refresh.py、sources.json；tests/test_collectors.py、test_refresh.py。
接口：`collect_github(client, query: str) -> list[Item]`；`collect_feed(client, url: str) -> list[Item]`；`start_refresh() -> str`返回run_id。
- [ ] 核实两个独立资讯来源的实际RSS/Atom地址（候选Hugging Face与GitHub Blog；不稳定时使用另一官方源并记录理由）。先做真实连接探测再写入配置，不猜订阅URL。
- [ ] GitHub保留4个种子项目，另用三组查询发现候选：MCP server、agent skills、AI coding；每查询最多20项、仅未归档项目；保存查询和截断范围，不声称全网榜单。
- [ ] 写HTTP fixture失败测试：200入库、重复采集增量=0、304不清空、429最多3次、缺失发布日期仍null、私网重定向被拒。
- [ ] 运行 `.venv/bin/python -m pytest tests/test_collectors.py tests/test_refresh.py -q`，观察有效失败。
- [ ] 实现受限HTTP与去重：删除utm_*和fbclid但保留业务查询参数；同URL更新内容；来源映射保留。
- [ ] 一个源失败标partial；两个同时刷新返回同run_id；进程启动将上次running改interrupted。每天首次GET /页面仅在当天未尝试刷新时启动；失败后需手动重试，避免刷新页面导致请求风暴。
- [ ] 重跑测试全部通过；执行真实刷新，记录GitHub及两个资讯源各自的条数、时间、失败状态。
验收：三个来源类别均有真实结果，至少1篇真实文章与4个种子项目；无今日文章显示“今日暂无更新”，不能填假新闻。源暂时失败则验收标阻塞。

## Task 3：一个页面完成阅读和收藏
文件：templates/index.html、static/app.js、style.css、app.py；tests/test_ui.py。
- [ ] 先写浏览器流程测试：打开资讯→查看来源→收藏并写笔记→刷新页面→收藏标签仍可见→取消收藏后消失。
- [ ] 运行 `.venv/bin/python -m pytest tests/test_ui.py -q`，确认因页面行为尚不存在失败。
- [ ] 实现三个标签与搜索；资讯按发布时间降序（未知时间单列）；项目支持Star、最近维护排序，并展示具体事实和“候选，未实测”。兴趣词匹配只显示匹配词，不声称质量评分。
- [ ] 展示原始发布时间/采集时间/来源链接/最近成功刷新时间；今日没有内容仍可查看近7天，默认近7天。
- [ ] 原始excerpt直接显示；无中文分析时标“原文摘要”。工程文章加“开发实践”标签，正文仍链接原文，不提前构建方法库。
- [ ] 覆盖加载、无结果、部分源失败状态；HTML脚本字符串作为文字展示。
- [ ] 重跑浏览器测试，通过后人工用真实数据库走一遍收藏闭环，检查窄屏和控制台。
验收：页面用真实HTTP与SQLite，不用localStorage代替持久化；刷新按钮不是装饰按钮。

## Task 4：可启动、可恢复、最小闭环验收
文件：scripts/start.sh、README.md、docs/acceptance-mvp.md；tests/test_acceptance.py。
- [ ] 先写停止/重启流程测试：收藏→终止服务→再次启动→原笔记仍在；中断刷新重启后状态为interrupted且可手动重试。
- [ ] 运行 `.venv/bin/python -m pytest tests/test_acceptance.py -q`，验证失败后再完善启动与恢复。
- [ ] start.sh检查独立环境，启动 `.venv/bin/python -m uvicorn radar.app:app --host 127.0.0.1 --port 8000 --workers 1`；可缺少GitHub token，但被限流时明确提示，不能复用聊天工具授权当作应用凭据。
- [ ] 执行 `.venv/bin/python -m pytest -q`，所有已实现测试通过；git diff --check无错误。
- [ ] 真实采集连续刷新两次，断言canonical_url无重复；保存源成功/失败与重启回读记录，不导出密钥或私人笔记。
验收M1：用户可以启动→更新→浏览→打开原文→收藏→重启后继续阅读。只宣称采集与收藏闭环完成，中文分析和趋势尚未完成。

## Task 5：中文理解与开发方法的最小闭环
依赖：用户选择模型提供方、模型和可用凭据。M1不依赖此选择。本计划不假定当前聊天模型可被本地应用免费调用。
文件：analysis.py、app.py、详情区域；tests/test_analysis.py。
接口：`analyze(item: Item, provider: Provider) -> Analysis`；`Provider.generate(payload: dict) -> dict`。只实现一个真实提供方，不做通用多模型平台。
- [ ] 写失败测试：无Key调用次数=0、伪造引用被拒、重复内容同模型只调用1次、配置模型不同不误用旧缓存、达到日配额不再调用。
- [ ] 运行 `.venv/bin/python -m pytest tests/test_analysis.py -q`，确认目标行为失败。
- [ ] 固定输出：中文一句话摘要、解决的问题、实现方法、对MCP/AI开发的应用、限制、证据URL。输入只有标题/订阅excerpt时标“仅基于摘要”，不能推断完整代码架构。
- [ ] 先按需点击“生成中文解读”，不默认分析全库；每上海自然日最多20次实际调用（失败也计数）、输入12000字符、输出1200 tokens上限。
- [ ] 校验所有证据URL属于输入来源集合，内容不得触发命令执行；结构错误标failed。成功后页面回读、收藏同一item，形成理解→记录闭环。
- [ ] 离线测试通过后，对5篇真实资讯与5个项目做真实生成和人工抽查；逐项核对引用是否支持陈述。若出现无依据结论，修正提示/校验并重验。
验收M2：10条解读均能回溯资料、正确标注资料覆盖范围；模型配置缺失则明确未完成，不用假摘要替代。

## 完成定义与后续增量
- M1完成：Task 1—4及真实验收通过。
- M2完成：Task 5真实模型验收通过。
- 完整长期目标还包括：真实7/30天趋势、带证据的质量评估、个人试用沉淀。这些不属于本次最小闭环的完成声明。
- 第一项后续增量优先真实历史趋势，复用已经记录的快照；再考虑评分表单和独立方法库。

## 每项执行纪律
一个任务完成后记录改动、命令、结果、真实证据、剩余条件；再进入下一个。出错用systematic-debugging；宣布完成前用verification-before-completion。无已授权提交/推送时保留本地改动即可，不因技能默认要求擅自发布。

## 可直接执行的指令
“使用executing-plans，执行本计划Task 1—4，先做真实采集和收藏最小闭环。默认单执行者，在本地运行，每项测试和回读通过后继续。模型解读按Task 5单独接入，缺Key不阻塞前四项；不要发布网站。”

## 当前状态
- [x] 最小闭环任务拆解完成。
- [ ] Task 1 本地数据与收藏。
- [ ] Task 2 真实采集。
- [ ] Task 3 页面闭环。
- [ ] Task 4 M1验收。
- [ ] Task 5 M2中文解读。
