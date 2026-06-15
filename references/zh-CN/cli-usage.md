# CLI 使用说明

> 英文 [../cli-usage.md](../cli-usage.md) 是主版本；本文件是中文镜像。

CLI 是确定性的账本工具。它不判断某个方法是否智能、可迁移或值得写入 Skill。

## 自动检查点

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

`cycle` 会初始化缺失的运行态文件，汇总本地状态，把 active 本地 signals 导入全局晋升层，提示 pending gates，并为 ready clusters 打印 proposal skeleton。

`--json` 可输出机器可读结果。`--no-global` 只用于测试或调试。

## 项目身份

全局晋升层会按哈希后的项目身份归并证据。默认规则是：优先使用 git remote；如果没有 git remote，就使用项目根目录路径。

如果一个工作区里混有多个不相关项目或对话，可以传入稳定的显式身份：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> --project-id <stable-project-or-conversation-key> cycle
```

也可以设置环境变量 `JINHUA_PROJECT_ID`。显式身份会先哈希再写入全局层；全局记录不会保存明文 id。

## 记录信号

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> log-signal \
  --source-type user_correction \
  --summary "Read README and relevant source before recommending reusable GitHub projects" \
  --operator verification_path \
  --cluster-key verification_path:read_readme_and_source_before_recommending_projects \
  --context "researching reusable tools" \
  --strength 2 \
  --trigger "recommending external projects for adoption" \
  --action "verify README and relevant source before recommending" \
  --transfer-conditions "tool, library, Skill, or agent project recommendations" \
  --negative-cases "quick pointers where the user did not ask for adoption judgment" \
  --verification-path "cite README and source files used" \
  --confidence 0.8 \
  --auto-init
```

必填项：

- `--source-type`
- `--summary`
- `--operator`
- `--cluster-key`
- `--context`
- `--strength`

signal card 字段可以提高跨项目 method fingerprint 的准确度：

- `--trigger`
- `--action`
- `--transfer-conditions`
- `--negative-cases`
- `--verification-path`
- `--confidence`

参数含义见 [glossary.md](glossary.md)。

## 本地提案

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> propose \
  --cluster-key <cluster-key> \
  --decision proposed_edit \
  --target "<target Skill / file / insertion location>" \
  --patch "<1-3 sentence patch>" \
  --risk "<main side effect>"
```

用户确认后：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal --proposal-id <id>
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal --proposal-id <id> --reason "..."
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal --proposal-id <id> --reason "..." --revision
```

## 全局晋升

普通 `cycle` 已经会把 active 本地 signals 导入 `global-data/`。

手动查看：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-status
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-cycle
```

创建全局提案：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-propose \
  --method-fingerprint <fingerprint> \
  --decision proposed_edit \
  --target "<target Skill / file / insertion location>" \
  --patch "<1-3 sentence patch>" \
  --risk "<main side effect>"
```

只读地查看可能重复的全局方法：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-merge-suggestions
```

## 维护命令

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> list-clusters
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> status
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> compact --dry-run
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> validate
```

## 运行态文件

项目本地：

```text
.jinhua/data/
├── signals.jsonl
├── cluster-state.json
├── proposals.jsonl
├── adopted-edits.jsonl
├── rejected-proposals.jsonl
├── crystallized-operators.jsonl
└── evolution-state.json
```

全局：

```text
<jinhua-dir>/global-data/
├── global-signals.jsonl
├── global-clusters.json
├── global-proposals.jsonl
├── adopted-global-edits.jsonl
├── rejected-global-proposals.jsonl
├── project-index.json
└── global-state.json
```
