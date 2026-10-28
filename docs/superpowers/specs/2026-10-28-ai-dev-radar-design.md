# AI Dev Radar 本地个人版设计

> 最小闭环调整：首版范围与技术简化以 [MVP计划](../plans/2026-10-28-ai-dev-radar-mvp.md) 为准；本文保留长期需求。

状态：基于现有对话的可执行设计稿；当前授权范围为计划与 Superpowers 安装，尚未授权执行整套产品开发。

## 目标与使用过程
每天打开本机页面，看到最新 AI 消息、值得研究的 MCP / AI 编程 GitHub 项目、可复用开发方法；收藏并记录试用结果。消息与项目均有原始来源、发布时间或更新时间、采集时间。应用只有本人使用，不发布网站。

日常路径：启动 → 补采 → 今日精选 → 阅读来源与中文解释 → 收藏 → 标记待读/试用/已采用。手动刷新和定时刷新走同一个流程。

## 已明确的需求与设计选择
用户明确：本地自用、海外 AI 消息与开发逻辑、趋势观察、优质 GitHub 项目、参考 CRM 开发逻辑与 Superpowers。
以下为本方案的默认选择，可在实施前修改：React + TypeScript + Vite、Python 3.12 + FastAPI、SQLite；09:00 Asia/Shanghai 每日采集；首版单执行者；首版不实现自动安装候选项目、自动修改代码、复杂多代理调度或公网部署。
本机当前 python3 为 3.8.18，Node 为 23.9.0；实施前使用独立 Python 3.12 环境和满足所选 Vite engines 的受支持 Node LTS，不替换系统解释器。依赖在实施时锁定，不在计划中虚构已经安装的版本。

## 系统边界
Superpowers 指导开发过程；运行中的采集、评分、定时任务由业务代码负责。MCP 是后续给外部 Agent 调用现有业务函数的入口，不作为前端与后端通信协议。
浏览器 → FastAPI → SQLite；后台采集器 → API/RSS → 标准化与去重 → 规则评分/可选模型摘要 → SQLite → 页面。
默认只绑定 127.0.0.1。密钥仅后端环境变量；日志不得输出 Authorization、token 或完整环境变量。

## 数据与接口契约
SQLite 表：sources、items、repo_snapshots、summaries、bookmarks、runs、run_sources、settings、repo_evaluations。迁移采用版本编号 SQL 文件。
- Source：id、kind(github/rss)、url、enabled、etag、last_modified、last_success_at。
- Item：id、kind(article/repo)、source_id、external_id、canonical_url、title、body_excerpt、published_at(可空)、fetched_at、topic、content_hash。unique(source_id,external_id)；canonical_url 用于跨来源文章归并，来源映射另存 item_sources。时间落库 UTC，页面按上海时区展示。
- RepoSnapshot：repo_id、snapshot_date(上海日期)、stars、forks、pushed_at、archived、license；unique(repo_id,snapshot_date)。更新同日快照，不新增同日历史点。
- Summary：item_id、content_hash、prompt_version、provider、model、summary_zh、problem、approach、limitations、application、evidence_urls、status(pending/ready/failed)。同内容与模型配置复用缓存。
- Bookmark：item_id、state(to_read/trying/adopted/rejected)、note、updated_at。
- Run：id、trigger(manual/scheduled/startup)、state(queued/running/succeeded/partial/failed/interrupted)、started_at、finished_at；每个来源另记状态与错误。
- Score：dimensions 字典（各 0..100 或 null）、evidence 字典、coverage、total(可空)、version；不把未观察到的测试或维护质量默认为零。

HTTP：GET /api/health；GET /api/items?kind=&topic=&q=&limit=20&cursor=；GET /api/items/{id}；PUT /api/bookmarks/{id}；GET /api/bookmarks；POST /api/refresh 返回 202 与 run_id（运行中返回同一 run_id）；GET /api/runs/{id}；GET /api/status；GET /api/trends?days=7|30。响应错误统一 {code,message,details}，无密钥。

人工评分闭环：项目详情页提供“评估”表单，可录入五个维度的0..100分值及每维证据链接、备注；缺项允许保存但总分为空。repo_evaluations按repo_id存当前评估、version及updated_at。GET /api/repo-evaluations/{id}读取；PUT /api/repo-evaluations/{id}校验后保存并返回回读结果；不存在的项目404，越界分数422。

## 采集、筛选和信息质量
初始 GitHub 种子：obra/superpowers、jnMetaCode/superpowers-zh、github/spec-kit、modelcontextprotocol/python-sdk。发现查询：MCP server、agent skills、AI coding，限制每次每查询最多 100 个候选并记录覆盖范围，不宣称抓全网。
初始资讯候选：Anthropic Engineering、Hugging Face Blog、GitHub Blog AI。实施时逐一核实实际 RSS/Atom 地址与返回内容；无法取得稳定订阅源的来源标为未接通，不用示例文章冒充今日资讯。至少两个独立资讯来源真实采集成功才通过完整采集验收。
HTTP 超时 20 秒；单源最多 3 次请求尝试；429 按 Retry-After 或 rate reset 延后，禁止高频重试；单源失败不回滚其他来源成功数据。接收上限 5MB；仅抓配置中的 HTTPS 公开源，重定向后再次校验，禁止回环/私网目标。
去重先按来源 ID，再按去追踪参数（utm_*、fbclid）的 URL，保留业务查询参数；同 URL 内容更新更新原条目。相似标题只形成关联提示，首版不自动合并。
今日按 published_at 的上海自然日筛选；published_at 缺失单列“今日发现，发布时间未知”。获取时间不得替代发布时间。

## 评分与趋势
个人相关性30%、工程质量25%、复用成本20%、维护15%、社区10%。每维要求事实依据；只有五维齐全才显示总分，缺失则显示分项及 coverage，列入待评估。自动规则生成可核实指标，人工评估补充工程与复用维度；模型建议不得伪装成实测结论。
README 中的声明标“作者声明”，执行测试才标“本地验证”。排序顺序：已完整评分的项目按 total 降序，未评估项另组。
趋势只使用观察到的独立事件、仓库快照及来源数量。7天/30天 Star 增量需存在准确基准日快照，否则 null；新装显示“历史数据不足”。趋势文字明确区分事实和推断，不自动生成投资/职业建议。

## AI 能力与费用
先跑无模型采集闭环，再接可替换模型 adapter。无 Key 时显示原始内容和“未生成中文摘要”，仍可收藏/检索；不能把规则提取声称为 AI 分析。
提供方、模型与费用限额尚未由用户选择：有 Key 后才做真实模型验收。默认每日最多20条、每条输入最多12000字符、输出最多1200 tokens，失败不无限重试。内容一律作为不可信资料输入，无工具执行权限。摘要每条至少一个属于输入来源的证据链接，否则拒收。

## 页面
今日精选、项目库、方法库、趋势、我的收藏；方法库来自有结构化摘要的文章，未生成时明确空态。全部页面有加载/空/失败/过期状态。收藏采用服务器持久化。趋势不足时不画伪造曲线。首版浅色中文界面，桌面优先，窄屏可读。

## 调度与恢复
一个后台 worker；数据库唯一运行锁防止多个进程并发采集。锁有心跳与过期恢复；程序重启将失效 running 标 interrupted。09:00 到点采集；关机错过时，下次启动只补采一次当前缺失窗口，不循环补跑每一天。记录最近成功时间和下次计划时间。所有功能只在进程存活、电脑联网且未休眠时运行；开机自启作为后续选择。

## 验收边界
A：离线测试及页面构建通过。B：GitHub + 两个独立资讯来源真实采集、重复刷新无重复、重启数据保留。C：真实模型摘要抽查10条全部有可回溯引用，不支持的结论能被识别；未配模型则 C 未完成。D：手动、定时、重启补采三路径验证；连续3个自然日实际运行有记录后才称“持续运行验证通过”。
本期交付包含 A/B、C 的可配置实现与条件验收、D 的恢复验证；三日观察与历史趋势必须如实标待观察。
