# PROJECT_MAP 中文说明

> 英文 [PROJECT_MAP.md](PROJECT_MAP.md) 是主版本；本文件是中文镜像。

## 产品形态

`jinhua` 是一个紧凑的 Skill + CLI，用来把重复出现的方法论信号转成经过用户确认的 Skill 改进。

职责分工：

- **Skill**：判断一个信号是否可复用、可迁移、有风险、重复或值得提案。
- **CLI**：记录 signals、更新 clusters、导入全局晋升证据、输出 skeleton、记录用户确认结果、建议 merge candidates、压缩和验证数据。
- **用户**：只做 Yes / No / Revision 风险确认。

## 主要文件

```text
jinhua/
├── SKILL.md
├── SKILL.zh-CN.md
├── README.md
├── README.zh-CN.md
├── CONTRIBUTING.md
├── CONTRIBUTING.zh-CN.md
├── SECURITY.md
├── SECURITY.zh-CN.md
├── CODE_OF_CONDUCT.md
├── CODE_OF_CONDUCT.zh-CN.md
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
├── scripts/
│   └── jinhua.py
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

运行态全局晋升目录：

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

## 当前 CLI 入口

- `init`
- `cycle`
- `log-signal`
- `list-clusters`
- `propose`
- `apply-proposal`
- `reject-proposal`
- `global-cycle`
- `global-status`
- `global-propose`
- `global-merge-suggestions`
- `global-apply`
- `global-reject`
- `compact`
- `status`
- `validate`

公开 CLI 入口只围绕上面的闭环展开。

## 数据规则

- 项目原始证据留在 `.jinhua/data/`。
- 全局晋升层只保存压缩过的方法论证据。
- `project-index.json` 保存项目身份哈希，不保存原始路径。
- `global-data/` 和 `.jinhua/` 是运行态，不打包、不提交。
- 一个工作区混有多个不相关项目或对话时，使用 `--project-id` 或 `JINHUA_PROJECT_ID` 区分。

## 不要回退

- 不要要求用户管理日常信号账本。
- 不要因为单条弱信号打扰用户。
- 不要绕过用户确认自动应用 Skill 修改。
- 不要把同一项目的重复信号算成跨项目重复。
- 不要添加 daemon、数据库、向量库、dashboard 或机器学习核心闭环。
- 不要把宽泛 observation 命令加入主流程。
