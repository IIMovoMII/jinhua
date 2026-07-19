# Jinhua Agent Instructions

- 先读 `PROJECT_RULES.md`；需要定位文件时读 `PROJECT_INDEX.md`，只读取与当前任务相关的 active 文件。
- `.jinhua/`、`global-data/`、`.archive/` 和缓存不是 active source；除非任务明确涉及运行态或历史恢复，否则不要读取、提交或打包。不得记录用户原文、凭证、私人路径或敏感项目标识。
- 不绕过 `signals -> clusters -> proposals -> user gate`、placement ladder 或用户确认门；触发层不得写信号/提案或新增第二套经验账本。
- 行为、入口或文件职责变化时，按需同步相关文档、`PROJECT_RULES.md` 和 `PROJECT_INDEX.md`。
- 修改源码、Skill、Hook、插件清单或相关文档后，必须完成验证、`plugin-creator` cachebuster/reinstall、本机 enabled 检查、提交并推送当前分支。
