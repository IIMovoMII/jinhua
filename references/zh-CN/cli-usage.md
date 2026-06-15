# CLI 使用说明

> [../cli-usage.md](../cli-usage.md) 是英文主版本；本文件用中文解释怎么运行这些命令。

CLI 是确定性的账本工具。它只负责写入、聚类、导入、压缩和验证数据；“某条经验是否值得沉淀”由模型判断，最后由用户确认。

## 自动检查点

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

`cycle` 是最常用的入口。它会：

- 创建缺失的运行态文件。
- 汇总当前项目里的信号和聚类。
- 把活跃本地信号导入全局晋升层。
- 提示是否有待确认提案。
- 为已经成熟的聚类打印提案骨架，包括建议落点（`placement_hint`）。如果建议落点是 `skill_patch`，还会尽量给出具体本地 Skill 和路径。

`--json` 会输出机器可读结果。`--no-global` 只建议在测试或调试时使用。

## 项目身份

全局晋升层需要判断“这条经验是不是跨项目重复出现”。默认身份规则是：

1. 优先使用 git remote。
2. 没有 git remote 时，使用项目根目录路径。

如果一个工作区里混有多个不相关项目或多段对话，请显式传入身份：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> --project-id <stable-project-or-conversation-key> cycle
```

也可以设置环境变量 `JINHUA_PROJECT_ID`。显式身份会先哈希再写入全局层，明文不会保存。

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

必填参数：

- `--source-type`：信号来源。
- `--summary`：脱敏后的方法论摘要。
- `--operator`：方法类型。
- `--cluster-key`：本地聚类键。
- `--context`：任务上下文。
- `--strength`：信号强度。

建议补齐的信号卡字段：

- `--trigger`：什么时候用。
- `--action`：核心动作。
- `--transfer-conditions`：适合迁移到哪里。
- `--negative-cases`：什么时候不要用。
- `--verification-path`：怎么验证。
- `--confidence`：辅助排序分。

这些字段越清楚，跨项目合并越不容易把不同经验混在一起。参数含义见 [glossary.md](glossary.md)。

## 本地提案

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> propose \
  --cluster-key <cluster-key> \
  --decision proposed_edit \
  --placement <project_rule|skill_patch|personal_global_skill> \
  --target "<target Skill / file / insertion location>" \
  --patch "<1-3 sentence patch>" \
  --risk "<main side effect>"
```

`--placement` 可以不传；不传时使用 `cycle` 骨架里的建议落点。

- `project_rule`：当前项目规则。适合本项目反复需要、但还没有跨项目证据的经验。
- `skill_patch`：增强已有本地 Skill。jinhua 会推荐最合适的具体 Skill 和路径；只有要覆盖推荐时，才需要手动传 `--recommended-skill` 或 `--recommended-skill-path`。
- `personal_global_skill`：个人全局 Skill 或所有项目规则。

用户确认后记录结果：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal --proposal-id <id> --placement <chosen-placement>
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal --proposal-id <id> --reason "..."
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal --proposal-id <id> --reason "..." --revision
```

`--revision` 表示用户不是彻底拒绝，而是要求修改后再看。

## 全局晋升

普通 `cycle` 已经会把活跃本地信号导入 `global-data/`。

手动查看全局状态：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-status
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-cycle
```

创建全局提案：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-propose \
  --method-fingerprint <fingerprint> \
  --decision proposed_edit \
  --placement <skill_patch|personal_global_skill> \
  --target "<target Skill / file / insertion location>" \
  --patch "<1-3 sentence patch>" \
  --risk "<main side effect>"
```

全局提案通常只在两个落点里选：有合适的已有本地 Skill，就用 `skill_patch`；没有清晰归属，才考虑 `personal_global_skill`。同项目内反复出现的经验，先走本地提案，不用等跨项目证据。

只读查看可能重复的全局方法：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-merge-suggestions
```

这个命令只给合并建议，不会改数据。

## 维护命令

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> list-clusters
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> status
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> compact --dry-run
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> validate
```

- `list-clusters`：看本地有哪些聚类。
- `status`：看本地统计。
- `compact --dry-run`：预览压缩会删掉哪些低价值信号。
- `validate`：检查 JSON/JSONL 数据结构和引用关系。

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
