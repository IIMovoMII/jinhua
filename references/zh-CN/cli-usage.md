# CLI 使用说明

> 英文辅助版本见 [../cli-usage.md](../cli-usage.md)。

全局参数必须写在子命令之前。

## 自动检查点

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

`cycle` 会初始化或迁移本地运行态、按当前阈值重算历史活跃聚类、汇总本地状态、把压缩后的有效信号导入全局层，并显示待确认门或就绪提案骨架。

常用选项：

- `--json`：机器可读输出。
- `--fail-on-pending-gate`：存在本地或全局待确认门时退出码为 `2`。
- `--no-global`：测试或排错时跳过全局导入。
- `--project-id <stable-key>`：同一工作区包含无关项目或对话时提供稳定身份；只保存哈希。

## 触发层命令

```bash
python <jinhua-dir>/scripts/jinhua.py classify-input --text "你理解错了工作流" --json
python <jinhua-dir>/scripts/jinhua.py codex-user-prompt-submit
python <jinhua-dir>/scripts/jinhua.py codex-post-tool-use
```

- `classify-input` 返回 `none`、`possible_user_correction` 或 `strong_user_correction`。
- `codex-user-prompt-submit` 在本地分类、统计不同用户回合，按需注入极短纠错/就绪提醒，并在每 8 个新回合注入一次隐藏周期回顾。
- `codex-post-tool-use` 记录本轮已经进入 Jinhua，防止重复。

Hook 不迁移核心数据，不写 signals/proposals，也不修改文件。

## 记录信号

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> log-signal \
  --source-type user_correction \
  --summary "推荐项目前先读取 README 和相关源码" \
  --operator verification_path \
  --cluster-key verification_path:verify_projects_before_recommending \
  --context "评估是否采用外部项目" \
  --strength 2 \
  --trigger "准备推荐外部项目供用户采用" \
  --action "推荐前读取 README 和相关源码" \
  --transfer-conditions "Skill、库、工具或 agent 项目推荐" \
  --negative-cases "只需要快速列出名称" \
  --verification-path "引用读过的 README 和源码" \
  --auto-init
```

来源类型、摘要、operator、cluster key 和上下文是必填项。强度默认是 `1`；明确纠正、重复模式或高成本失败应显式传入对应强度。方法卡字段能改善迁移判断和全局指纹。

`--immediate` 只用于用户明确要求立即沉淀，或紧急且可复用的高成本失败。它是唯一允许跳过普通就绪阈值的入口。

同一项目出现两条同类信号后，不看强度，先进入“仅项目规则就绪”；此时 `propose` 只接受 `project_rule`。达到 3 条信号或总强度 5 后，恢复完整本地落点判断。项目规则采纳不会停用原信号，其他项目后续出现同类方法时仍可继续满足跨项目阈值。

## 创建本地提案

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> propose \
  --cluster-key verification_path:verify_projects_before_recommending \
  --placement skill_patch \
  --recommended-skill github-project-due-diligence \
  --recommended-skill-path "<skill-dir>/SKILL.md" \
  --target "<skill-dir>/SKILL.md / 来源验证" \
  --patch "## 来源验证

推荐供用户采用的项目之前，先读取 README 和相关源码。" \
  --risk "对只需要名称的快速查询可能增加工作量。"
```

具体 `target`、带标题的完整 Markdown `patch` 和 `risk` 都是必填项。`placement` 可以省略并使用骨架推荐。`skill_patch` 必须有具体 Skill 名称和路径；`project_rule` 必须有规则文件建议。两条信号触发的项目专用聚类会拒绝除 `project_rule` 以外的落点，提案必须指向推荐规则文件，实际修改目标也必须位于当前项目根目录内。

提案创建后进入 `pending_user_gate`，继续前必须展示本地化用户确认门。

## 采纳、修订或拒绝

用户采纳后，先用宿主原生工具修改并验证目标，再记录：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal \
  --proposal-id <proposal-id> \
  --placement skill_patch \
  --applied-target "<skill-dir>/SKILL.md" \
  --summary "已加入来源验证规则并核对差异。"
```

apply 命令不会写目标文件。

用户如果改选另一种落点，必须先修订提案，使所有者和目标信息与新落点一致，再记录采纳。

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal \
  --proposal-id <proposal-id> \
  --reason "范围太宽"

python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal \
  --proposal-id <proposal-id> \
  --reason "仅限采用型推荐" \
  --revision
```

修订会保留确认门。拒绝后需要 5 条新的同类信号才解除冷却。

## 全局晋升

普通 `cycle` 已经会导入本地信号。手动查看：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-cycle
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-status
```

创建全局提案时同样必须提供目标、完整 patch 和风险：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-propose \
  --method-fingerprint <fingerprint> \
  --placement personal_global_skill \
  --target "~/.codex/skills/<skill-name>/SKILL.md" \
  --patch "## 可复用规则

应用已经验证的跨项目方法。" \
  --risk "约束不同的项目可能不适用。"
```

原生编辑和验证完成后，用 `global-apply` 记录 `proposal-id`、placement、实际目标和摘要。拒绝或修订使用 `global-reject [--revision]`。

## 状态和验证

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> status
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> list-clusters
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> validate
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> guard --session-id s --turn-id t
```

`validate` 会先迁移旧运行态，再检查当前 schema 和废弃字段边界。

## 运行态文件

```text
<project-root>/.jinhua/
├── data/
│   ├── signals.jsonl
│   ├── cluster-state.json
│   ├── proposals.jsonl
│   ├── adopted-edits.jsonl
│   ├── rejected-proposals.jsonl
│   └── evolution-state.json
└── runtime/
    └── invocation-guard.json

<jinhua-dir>/global-data/
├── global-signals.jsonl
├── global-clusters.json
├── global-proposals.jsonl
├── adopted-global-edits.jsonl
├── rejected-global-proposals.jsonl
├── project-index.json
└── global-state.json
```

字段和迁移规则见 [runtime-schema.md](runtime-schema.md)。
