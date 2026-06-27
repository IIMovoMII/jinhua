# 项目地图

> 本文件是中文项目地图；英文辅助版本见 [PROJECT_MAP.md](PROJECT_MAP.md)。

## 产品形态

`jinhua` 是一个小型 Skill + 单文件 CLI。它负责把反复出现的方法论信号，转成经过用户确认的 Skill 改进。

职责分工：

- **Skill**：判断信号是否可复用、可迁移、有风险、重复，是否值得形成提案。
- **CLI**：记录信号、更新聚类、导入全局晋升证据、输出带落点的提案骨架、推荐项目规则文件、记录用户确认、给出合并建议、压缩并验证数据。
- **用户**：只做最后的风险确认，也就是 `Project Rule`、`Skill Patch`、`Personal Global Skill`、`No`、`Revision`。

## 主要文件

```text
jinhua/
├── SKILL.md
├── SKILL.zh-CN.md
├── README.md
├── README.en.md
├── CONTRIBUTING.md
├── CONTRIBUTING.en.md
├── SECURITY.md
├── SECURITY.en.md
├── CODE_OF_CONDUCT.md
├── CODE_OF_CONDUCT.en.md
├── PROJECT_MAP.md
├── PROJECT_MAP.zh-CN.md
├── CHANGELOG.md
├── CHANGELOG.zh-CN.md
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── config.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .codex-plugin/
│   └── plugin.json
├── hooks/
│   ├── codex-hooks.json
│   ├── codex_user_prompt_submit.py
│   ├── codex_post_tool_use.py
│   ├── codex_stop.py
│   └── claude-codex-hooks.json（legacy）
├── skills/
│   └── jinhua/
│       └── SKILL.md
├── scripts/
│   ├── jinhua.py
│   └── test_trigger_layer.py
├── references/
│   ├── cli-usage.md
│   ├── data-policy.md
│   ├── hook-integration.md
│   ├── maintenance.md
│   ├── operator-json-schema.md
│   └── zh-CN/
│       ├── cli-usage.md
│       ├── data-policy.md
│       ├── glossary.md
│       ├── hook-integration.md
│       ├── maintenance.md
│       └── operator-json-schema.md
├── docs/
│   └── jinhua-logic.html
└── data/
    ├── signals.jsonl
    ├── cluster-state.json
    ├── proposals.jsonl
    ├── adopted-edits.jsonl
    ├── rejected-proposals.jsonl
    ├── crystallized-operators.jsonl
    └── evolution-state.json
```

全局晋升运行态目录：

```text
jinhua/global-data/
├── global-signals.jsonl
├── global-clusters.json
├── global-proposals.jsonl
├── adopted-global-edits.jsonl
├── rejected-global-proposals.jsonl
├── project-index.json
└── global-state.json
```

`global-data/` 是运行态，不随开源包提交。

## CLI 入口

- `init`：初始化运行态。
- `cycle`：自动检查点。
- `classify-input`：新触发层的本地纠错分类。
- `codex-user-prompt-submit`：Codex 第一道输入侧 hook 入口。
- `codex-post-tool-use`：Codex 第二道 invocation guard 入口。
- `codex-stop`：Codex 第三道输出状态尾巴入口。
- `parse-output-state`：只读解析输出状态尾巴。
- `guard`：手动检查 invocation guard。
- `wake-check`：legacy 兼容粗筛，不再是主路径。
- `hook-user-prompt-submit`：legacy 兼容适配器，不再是主路径。
- `log-signal`：记录方法论信号。
- `list-clusters`：查看本地聚类。
- `propose`：创建本地提案。
- `apply-proposal`：记录本地采纳。
- `reject-proposal`：记录本地拒绝或修订。
- `global-cycle`：查看并导入全局晋升状态。
- `global-status`：查看全局统计。
- `global-propose`：创建全局提案。
- `global-merge-suggestions`：只读查看相似全局方法。
- `global-apply`：记录全局采纳。
- `global-reject`：记录全局拒绝或修订。
- `compact`：压缩低价值信号。
- `status`：查看本地状态。
- `validate`：验证数据结构。

公开 CLI 入口只围绕这条闭环展开，不额外扩张。

## 数据规则

- 项目原始证据留在 `.jinhua/data/`。
- 全局晋升层只保存压缩过的方法论证据。
- `project-index.json` 保存项目身份哈希，不保存原始路径。
- `global-data/` 和 `.jinhua/` 是运行态，不打包、不提交。
- 一个工作区混有多个不相关项目或对话时，用 `--project-id` 或 `JINHUA_PROJECT_ID` 区分。

## 不要回退

- 不要要求用户手动管理日常信号账本。
- 不要因为单条弱信号打扰用户。
- 不要绕过用户确认自动应用 Skill 修改。
- 不要把同一项目的重复信号算成跨项目重复。
- 推荐落点是 `skill_patch` 时，不要让用户自己找目标 Skill。
- 推荐落点是 `project_rule` 时，不要自动创建项目规则文件。
- 不要添加后台进程、外部数据库、向量库、仪表盘或机器学习核心闭环。
- 不要把宽泛的观察命令加入主流程。
- 不要让 hook 承担经验系统；hook 只做分类、防重复和状态尾巴解析。
- 仓库内插件元数据保持很薄：marketplace 文件负责被发现，`.codex-plugin/plugin.json` 暴露 Codex hooks 和 skills，真正的方法论逻辑仍然集中在根目录 `SKILL.md`。
