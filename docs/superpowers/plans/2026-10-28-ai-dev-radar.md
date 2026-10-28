# AI Dev Radar 实现计划

> 范围更新：当前优先执行 [最小闭环计划](2026-10-28-ai-dev-radar-mvp.md)。本文保留为后续功能路线，不与最小闭环计划同时执行。

> **面向 AI 代理的工作者：** 使用 executing-plans 逐任务实现；默认单执行者。每项先写失败测试，再最小实现，验证通过才勾选。当前仅交付计划，不执行产品开发。

**目标：** 本地可用、有来源证据的个人 AI 开发情报 dashboard。

**架构：** 采集工具、业务编排、个人配置分层。前端使用 HTTP 调用 FastAPI，所有事实、收藏与任务状态持久化到 SQLite；模型只做有引用的内容转换。

**技术栈：** Python 3.12、FastAPI、sqlite3、httpx、feedparser、pytest；React、TypeScript、Vite、Vitest、Playwright。实现时核实依赖兼容性并提交锁文件。

**规格：** `docs/superpowers/specs/2026-10-28-ai-dev-radar-design.md`。以下路径均相对 ai-dev-radar 仓库根目录。

## 全局约束
- 本地自用，只绑定127.0.0.1，不发布网站；不自动安装或执行外部仓库代码。
- UTC存储，Asia/Shanghai展示与每日09:00调度。
- 缺失发布时间保持null；缺失评分或历史数据不得编造。
- 网络请求20秒超时，单源最多3次尝试，5MB上限。
- 默认每日模型处理最多20条，单条输入12000字符，输出1200 tokens。
- 所有测试均使用独立临时数据库，离线测试默认禁止外网。
- 写入收藏、采集结果都要查询回读；连续3日运行与单次测试分开报告。
- 每完成一个任务保存证据；提交和推送按用户授权范围处理，技能本身不授予发布权限。

## 审查重点
1. 429/单源断网：任务3、4证明局部失败不清空已有数据、不无限重试。
2. 两个刷新并发/进程崩溃：任务4、8证明不重复入库且失效任务可恢复。
3. 上海午夜与未知发布时间：任务2、6证明今日筛选准确且不伪造发布时间。
4. 提示注入与伪造引用：任务7证明外部内容不能触发工具，非输入URL拒收。
5. 恶意订阅URL/HTML：任务3、6证明私网重定向被拒绝、页面不执行外部脚本。

## 文件职责与接口
```
backend/pyproject.toml              包与测试配置；src布局，包名radar
backend/src/radar/app.py           FastAPI入口及生命周期
backend/src/radar/config.py        环境变量与数据目录
backend/src/radar/db.py            连接与SQL迁移
backend/src/radar/migrations/      版本化SQL
backend/src/radar/models.py        Item, Source, Run, Summary, Score的Pydantic模型
backend/src/radar/items.py         保存、去重、查询与收藏
backend/src/radar/collectors/      http.py、github.py、rss.py
backend/src/radar/refresh.py       单次采集与运行记录
backend/src/radar/scoring.py       有证据的评分
backend/src/radar/summaries.py     模型adapter、缓存与结果验证
backend/src/radar/scheduler.py     上海时区调度、锁、恢复
backend/src/radar/trends.py        快照差值和来源统计
backend/src/radar/cli.py           init-db / refresh / verify-live
config/sources.json               来源、启用状态及查询；不含密钥
config/interests.json             兴趣词和权重
frontend/src/api.ts               类型化HTTP接口
frontend/src/pages/               Today, Repos, Methods, Trends, Bookmarks
frontend/src/components/          来源、状态、评分证据等公共组件
backend/tests/                   与模块对应的离线行为测试及fixtures
frontend/e2e/                    使用隔离数据库的真实后端浏览器测试
scripts/dev.sh                   开发启动（两个进程退出时一并关闭）
scripts/start.sh                 构建产物由FastAPI提供的单进程本地启动
.env.example                    只有占位值
```

核心签名（在对应任务定义的模块中实现）：
- `init_db(path: Path) -> None`
- `upsert_items(conn, items: list[Item]) -> SaveStats`；SaveStats含inserted/updated/unchanged。
- `list_items(conn, filters: ItemFilters) -> Page[Item]`；Page含items/next_cursor。
- `collect(source: Source, client: httpx.AsyncClient) -> list[Item]`，GitHub/RSS分别实现。
- `refresh(trigger: Literal['manual','scheduled','startup']) -> Run`，锁已占用时返回当前Run。
- `score_repo(dimensions: dict[str, float | None], evidence: dict[str, list[str]]) -> Score`
- `summarize(item: Item, provider: SummaryProvider) -> Summary`；adapter接口 `generate(payload: dict) -> dict`。
- `due(now: datetime, last_attempt: datetime | None) -> bool`。
- `star_delta(snapshots: list[RepoSnapshot], end_date: date, days: int) -> int | None`。

接口细节以规格为准；所有模型字段必须在任务2统一定义，后续不得自行改名。

## 执行顺序
任务1→2→3→4→5→6，先完成无模型可用闭环；然后7→8→9→10。任务7的真实调用依赖用户选择模型和提供后端凭据，其他任务可继续完成。

### Task 01：本地服务可启动

**文件：** backend/pyproject.toml、src/radar/app.py、config.py；.env.example、scripts/dev.sh；测试 backend/tests/test_health.py。

**交付与实现约束：** 先确认 Python 3.12、受支持 Node LTS；创建隔离环境和最小 FastAPI 包。GET /api/health 返回 {status:"ok"}，不读取网络、密钥或数据库；端口默认8000。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```python
assert client.get("/api/health").json() == {"status": "ok"}
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：创建环境用 python3.12 -m venv backend/.venv；安装用 backend/.venv/bin/python -m pip install -e "./backend[dev]"。锁定最终依赖。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd backend && .venv/bin/python -m pytest tests/test_health.py -q
```

- [ ] 回读并记录验收：健康检查PASS；后端仅回环监听；记录环境版本。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

### Task 02：数据持久化、去重与收藏

**文件：** backend/src/radar/{models,db,items}.py、migrations/001_initial.sql；backend/tests/test_items.py。

**交付与实现约束：** 实现规格全部表和统一模型；upsert用事务；URL仅删除utm_*和fbclid；每次收藏按item_id UPSERT。Page游标为排序键(fetched_at,id)，limit范围1..100，非法值422。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```python
assert second_save.inserted == 0
assert reopened.get_bookmark(item.id).note == "准备试用"
assert unknown_date_item.published_at is None
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：覆盖同URL更新、不同业务查询参数不合并、空内容、中文检索、数据库重开；保存原始来源映射。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd backend && .venv/bin/python -m pytest tests/test_items.py -q
```

- [ ] 回读并记录验收：回读一致，重复导入不增行；所有迁移重复启动安全。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

### Task 03：GitHub和资讯采集器

**文件：** backend/src/radar/collectors/{http,github,rss}.py；config/sources.json；backend/tests/test_collectors.py、fixtures/。

**交付与实现约束：** 使用httpx与feedparser；GitHub API读取仓库事实，RSS解析发布时间；实现网络域校验、响应大小限制和来源etag缓存。分页有上限；401/403明确失败，304保持原内容。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```python
assert limited_run.request_count <= 3
assert parse_feed(no_date_fixture)[0].published_at is None
assert redirect_to_private_network.rejected is True
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：先用模拟HTTP验证200/304/429/超时/无效XML/私网重定向；随后核实两个资讯源的真实订阅入口，并记入sources.json。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd backend && .venv/bin/python -m pytest tests/test_collectors.py -q
```

- [ ] 回读并记录验收：离线测试PASS；真实源状态分别报告。某来源不可用不得填假数据。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

### Task 04：刷新编排和可观察任务

**文件：** backend/src/radar/{refresh,cli,app}.py；backend/tests/test_refresh.py。

**交付与实现约束：** 实现POST /api/refresh与GET /api/runs/{id}；202立即返回，后台执行。SQLite事务获取唯一运行锁；每源独立事务，成功即保存，最终按来源成功数得succeeded/partial/failed。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```python
assert concurrent_a.run_id == concurrent_b.run_id
assert partial_run.state == "partial"
assert successful_source_items_survive_failure is True
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：定义数据库锁lease：每30秒心跳、90秒失效；run_sources只对本次来源记录。锁获取和run创建同事务。此处实现锁基础，任务8补重启恢复。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd backend && .venv/bin/python -m pytest tests/test_refresh.py -q
```

- [ ] 回读并记录验收：手动刷新可查询终态；重复刷新无重复记录；失败原因可见且无密钥。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

### Task 05：项目评分可解释

**文件：** backend/src/radar/scoring.py；config/interests.json；backend/tests/test_scoring.py。

**交付与实现约束：** 按30/25/20/15/10权重；Score coverage为已观测维度权重之和/100；任一维缺失则total=null。维度有值却无依据时视作缺失；评分保留版本和证据。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```python
assert score_repo(all_100, valid_evidence).total == 100
assert score_repo(missing_quality, evidence).total is None
assert score_repo(missing_quality, evidence).coverage == 0.75
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：首版提供人工评估入口；自动采集仅补可核实指标，不能从“存在tests目录”推断测试通过。越界分数拒收。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd backend && .venv/bin/python -m pytest tests/test_scoring.py -q
```

- [ ] 回读并记录验收：每个分项可展开依据；待评估与已验证区分。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

### Task 06：Dashboard与收藏完整闭环

**文件：** frontend/package.json、src/api.ts、src/pages/*、src/components/*；backend/src/radar/app.py；frontend/e2e/dashboard.spec.ts。

**交付与实现约束：** 建立React+TS+Vite应用，提供五个入口；后端补齐规格GET/PUT接口与GET/PUT /api/repo-evaluations/{id}（写评分维度和证据）。先用真实入库数据完成列表、过滤、详情、收藏，再美化。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```typescript
await expect(page.getByText("发布时间未知")).toBeVisible();
// 收藏后刷新页面，断言同条目和笔记仍存在。
// 输入含<script>的标题，断言仅作为文本展示。
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：配置Playwright启动隔离后端；测试使用fixture入库但验收另跑真实源。UI不使用dangerouslySetInnerHTML；错误、空列表、未生成摘要均有明确状态。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd frontend && npm run typecheck && npm run build && npx playwright test e2e/dashboard.spec.ts
```

- [ ] 回读并记录验收：真实后端+浏览器收藏回读通过；无控制台错误；断网时显示缓存与过期标记。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

### Task 07：中文摘要与方法拆解

**文件：** backend/src/radar/summaries.py、providers.py；backend/tests/test_summaries.py；frontend/src/pages/Methods.tsx。

**交付与实现约束：** 实现SummaryProvider协议、结构化结果校验、内容hash缓存；外部文本放资料字段，无执行工具。首次仅实现用户选定提供方的真实adapter，另有测试fake。没Key不发请求。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```python
assert invalid_citation.status == "failed"
assert calls_after_same_content == 1
assert no_key_request_count == 0
assert over_daily_limit_request_count == 0
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：输出summary_zh/problem/approach/limitations/application/evidence_urls；至少一条输入URL。输入里要求泄露密钥或执行命令时只作被分析文本。到20条停止并显示配额状态。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd backend && .venv/bin/python -m pytest tests/test_summaries.py -q
```

- [ ] 回读并记录验收：离线行为PASS；有Key后抽查10条真实摘要。无Key标“adapter真实验证未完成”，不得称AI功能全验收。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

### Task 08：定时更新、重启恢复与启动脚本

**文件：** backend/src/radar/scheduler.py、app.py；scripts/start.sh；backend/tests/test_scheduler.py。

**交付与实现约束：** 单进程生命周期运行worker，09:00上海触发；启动后判断当天窗口是否漏跑。last_attempt避免同日失败引发每次启动风暴，手动重试仍允许。恢复过期锁并标interrupted；复用任务4刷新函数。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```python
assert due(shanghai_0859, yesterday) is False
assert due(shanghai_0900, yesterday) is True
assert startup_twice.created_runs == 1
assert stale_running.state == "interrupted"
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：测试跨午夜、机器错过多日、手动与调度重叠、崩溃后恢复。start.sh提供预构建前端，由FastAPI同源托管；浏览器仅连接回环接口。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd backend && .venv/bin/python -m pytest tests/test_scheduler.py -q
```

- [ ] 回读并记录验收：手动/定时/补采均有运行证据；README明确电脑休眠不能准时采集；自动开机启动不在本期。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

### Task 09：真实历史趋势

**文件：** backend/src/radar/trends.py；backend/tests/test_trends.py；frontend/src/pages/Trends.tsx。

**交付与实现约束：** 以上海日期保存每日最后一条仓库快照；仅end_date与end_date-days都存在时返回差值。资讯按canonical_url去重计数，按来源单列，样本量和覆盖窗口可见。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```python
assert star_delta(one_day, today, 7) is None
assert star_delta(two_exact_points_100_130, today, 7) == 30
assert same_day_snapshot_count == 1
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：首版趋势由统计与固定解释生成；无基准日不插值；负增长如实显示；不把讨论次数作为真实采用量。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd backend && .venv/bin/python -m pytest tests/test_trends.py -q
```

- [ ] 回读并记录验收：历史不足空态明确；7/30天选择正确；不得用fixture图表冒充个人历史。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

### Task 10：集成验收与交接

**文件：** backend/src/radar/cli.py；README.md；docs/acceptance.md；frontend/e2e/acceptance.spec.ts。

**交付与实现约束：** 实现python -m radar.cli verify-live --output docs/evidence/live.json；输出来源状态、条数、时间、重复运行差值与重启回读结果。将模型/持续3日状态分别列出。

- [ ] 写行为测试，包含以下断言（fixture命名由实现者确定，断言取值不可改变）：

```python
assert duplicate_refresh.new_duplicate_rows == 0
assert persisted_bookmark_after_restart == expected_bookmark
assert acceptance.fake_items_in_live_database == 0
```

- [ ] 运行下列命令，先确认因目标行为缺失而失败；环境未配置导致的失败不算有效红灯。
- [ ] 最小实现：在仓库根执行backend/.venv/bin/python -m radar.cli verify-live --output docs/evidence/live.json；人工核对GitHub、两个资讯来源、10条模型摘要（有Key时）。核验导出不含Key或私人笔记。
- [ ] 再运行同一命令，预期全部PASS/退出码0：

```bash
cd backend && .venv/bin/python -m pytest -q
cd ../frontend && npm run typecheck && npm run build && npx playwright test
```

- [ ] 回读并记录验收：A/B/C/D逐项写通过/失败/未测/待观察；所有已实现关键测试通过才能交付；三日观察不能提前勾选。
- [ ] 检查差异和凭据泄露，记录更改文件与验证结果；在已获提交授权时做独立提交。

## 任务结束后的统一报告

每次报告：当前Task、实际改动、测试命令及结果、真实调用证据、剩余阻塞、下一任务。失败先使用systematic-debugging找根因，不通过删测试或改预期“修绿”。没有执行的测试标未测。

## 后续增量（不混入首版完成声明）
- 本地只读MCP接口：search_items、get_daily_digest、get_repo_evaluation；复用现有查询函数，验证initialize→tools/list→tools/call三步。
- 有真实历史后增加趋势解释与个性化推荐；以收藏反馈评估推荐效果。
- 若需要长期开机运行，再配置macOS登录启动；单独验证卸载和停机行为。

## 可直接交给Codex的执行指令

> 使用 using-superpowers 和 executing-plans，阅读本计划与对应设计，按Task 01到10顺序实施。默认单执行者，先完成真实采集和收藏闭环，再做AI摘要。每项先写行为测试、确认失败、实现并验证；保留测试和真实调用证据。模型尚未选择时继续完成不依赖模型的任务，不能伪造摘要。只在本地运行，不发布网站。

## 当前完成状态
- [x] 用户级及项目级Superpowers文件安装。
- [x] 设计与执行计划编写。
- [ ] Task 01—10产品实现。
- [ ] 本地真实数据验收。
- [ ] 模型真实调用验收。
- [ ] 连续3个自然日运行观察。

## 设计检查结果

独立只读检查发现人工评分录入缺口，已在设计补齐repo_evaluations、详情表单和GET/PUT接口，并由Task 05/06覆盖。用户级安装82个文件已与固定版本哈希逐一核对。产品测试命令为未来执行步骤，本轮未运行产品测试。
