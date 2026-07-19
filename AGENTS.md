# Jinhua Agent Instructions

- 先读 `PROJECT_RULES.md`；需要定位文件时读 `PROJECT_INDEX.md`，只读取与当前任务相关的 active 文件。
- `SKILL.md` 是控制面，`scripts/jinhua.py` 是唯一 CLI，`hooks/codex-hooks.json` 和三个 `hooks/codex_*.py` 是 Codex 触发层；不要把归档内容当作实现依据。
- `.jinhua/`、`global-data/` 是运行态，`.archive/` 和 `__pycache__/` 不是 active source；除非任务明确涉及历史恢复，否则不要读取或提交它们。
- 保持 `signals -> clusters -> proposals -> user gate`、placement ladder 和用户确认门不被绕过；触发层可以独立优化，但不能新增第二套经验账本。
- 不记录用户原文、凭证、私人路径或敏感项目标识；不要把运行态打进插件包。
- 行为、入口或文件归属发生变化时，按需同步对应文档、`AGENTS.md`、`PROJECT_RULES.md` 和 `PROJECT_INDEX.md`，不要求每次小修改都更新。
- 每次修改 Skill 项目（源码、SKILL、Hook、插件清单或相关文档）都必须运行验证、用 `plugin-creator` 的 cachebuster/reinstall 流程更新本机、提交 Git，并推送当前分支；未完成这条链路不要声称修改完成。
