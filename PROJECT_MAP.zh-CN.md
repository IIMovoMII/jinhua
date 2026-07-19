# 项目地图

> 英文辅助版本见 [PROJECT_MAP.md](PROJECT_MAP.md)。

日常先读 `AGENTS.md`；涉及结构或文件归属时，再读 `PROJECT_RULES.md` 和 `PROJECT_INDEX.md`。

## 产品形态

Jinhua 是“精简 Skill + 标准库单文件 CLI + 薄宿主触发适配”。

- **触发层**：本地纠错分类、就绪提醒、按会话回合计数、同轮去重、固定每 8 轮回顾。
- **Skill**：语义写入/跳过判断、方法抽象、落点、提案内容和本地化用户对话。
- **CLI**：确定性存储、精确聚类、跨项目导入、迁移、完整提案记录、确认结果和验证。
- **Agent**：用户采纳后，用宿主原生工具修改并验证目标。
- **用户**：选择落点、拒绝或要求修订。

核心链路：

```text
signals -> clusters -> proposals -> user gate
```

## Active 目录

```text
jinhua/
├── SKILL.md
├── SKILL.zh-CN.md
├── README.md
├── README.en.md
├── AGENTS.md
├── PROJECT_RULES.md
├── PROJECT_INDEX.md
├── PROJECT_MAP.md
├── PROJECT_MAP.zh-CN.md
├── CHANGELOG.md
├── CHANGELOG.zh-CN.md
├── .codex-plugin/
│   └── plugin.json
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── .agents/plugins/
│   └── marketplace.json
├── hooks/
│   ├── hooks.json
│   ├── codex_user_prompt_submit.py
│   └── codex_post_tool_use.py
├── skills/jinhua/
│   └── SKILL.md
├── adapters/
│   ├── README.md
│   ├── openclaw/
│   ├── hermes/
│   ├── trae/
│   └── workbuddy/
├── scripts/
│   ├── jinhua.py
│   ├── test_core_loop.py
│   ├── test_trigger_layer.py
│   └── test_adapters.py
├── references/
│   ├── cli-usage.md
│   ├── data-policy.md
│   ├── runtime-schema.md
│   ├── hook-integration.md
│   ├── maintenance.md
│   └── zh-CN/
│       ├── cli-usage.md
│       ├── data-policy.md
│       ├── runtime-schema.md
│       ├── hook-integration.md
│       ├── maintenance.md
│       └── glossary.md
├── docs/
│   └── jinhua-logic.html
└── .github/
    ├── ISSUE_TEMPLATE/
    └── PULL_REQUEST_TEMPLATE.md
```

2.0 不再包含仓库 operator 种子目录。运行态只会出现在目标项目和被忽略的个人全局目录。

## 当前 CLI

`init`、`cycle`、`global-cycle`、`classify-input`、`codex-user-prompt-submit`、`codex-post-tool-use`、`guard`、`log-signal`、`list-clusters`、`propose`、`apply-proposal`、`reject-proposal`、`global-propose`、`global-apply`、`global-reject`、`status`、`global-status`、`validate`。

apply 命令只记账。提案命令必须提供具体目标、带标题的完整 Markdown 修改块和具体风险。

## 运行态边界

项目本地：

```text
<project-root>/.jinhua/data/
<project-root>/.jinhua/runtime/invocation-guard.json
```

个人全局：

```text
<jinhua-dir>/global-data/
```

两者都被 Git 忽略，不能打包或提交。

## 不要回退

- Hook 不自动写经验。
- 就绪聚类不能长期隐身，ready-attention 必须把它带回 Agent 注意力。
- 不因单条弱信号打扰用户。
- 不绕过带落点的用户确认门。
- 原生编辑和验证成功前，不记录采纳。
- 不把同项目重复算成跨项目重复。
- 不让用户自己寻找目标 Skill 或项目规则文件。
- 不重新加入模糊合并、压缩删除、operator 晋升、后台进程、数据库、向量库、仪表盘或第二套账本。
- 宿主专用包装放在 `adapters/`。
