# Superpowers 中文版接入

- 来源：https://github.com/jnMetaCode/superpowers-zh
- 版本：1.8.0
- 固定提交：020339d1410e51a9eca16d26f4eac4cfee166d8a
- 安装日期：2026-10-28
- 范围：本项目 `.agents/skills/`，共 21 个技能及随附资源。
- 安装方式：Codex skill-installer，指定完整提交 SHA，Git 下载。
- 引导入口：项目根目录 `AGENTS.md`。
- 原始英文项目：https://github.com/obra/superpowers

这是 Codex 项目级技能安装，不是 Claude Code 完整插件安装；不配置 Claude SessionStart hooks，不安装推广的其他产品。第三方技能不做修改，定制规则单独保留。

在 Codex 中以本仓库目录打开聊天，下一轮可发现项目技能；若未出现，重新打开项目聊天。当前聊天位于父目录时，不能把子目录安装当作已自动加载。可显式要求读取 `.agents/skills/using-superpowers/SKILL.md`。

升级时先审核新版本差异，再替换技能并更新此记录和文件校验清单。安装完成仅说明文件可用，不代表所有技能或附带脚本均经过运行验证。

## 本机用户级安装（2026-10-28）

21个技能已另外安装到 `~/.agents/skills/`，82个文件与项目固定版本逐一核对一致；跨项目可用。官方技能发现文档：https://learn.chatgpt.com/docs/build-skills 。下一轮可使用，若未出现则重启Codex。同名项目级和用户级技能可能同时出现在选择器，项目内明确选择项目路径；二者当前内容一致。没有改动全局config.toml，没有运行各技能附带脚本的完整测试。
