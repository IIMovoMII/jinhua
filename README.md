# Jinhua

语言：简体中文 | [English](README.en.md)

Jinhua 是一个面向编程智能体（Agent）的本地方法经验沉淀工具。它把真实任务中反复纠正、验证或成功复用的方法，整理为经过用户确认的项目规则或 Skill 改进。

它不是聊天记录、个人记忆库或自动改写器。Jinhua 只保存脱敏后的方法论证据；Hook 不会自动写经验，任何规则修改都必须经过用户确认。

产品形态：

- Codex：插件（plugin）+ 三道本地触发闸门 + Skill + CLI。
- Claude Code：原生 Hook 适配 + 同一套 Skill/CLI。
- OpenClaw、Hermes、TRAE、WorkBuddy：轻量宿主包装，核心闭环不变。

中文逻辑图：[docs/jinhua-logic.html](docs/jinhua-logic.html)

## 完整闭环

```text
触发层发现可能值得检查的回合
        ↓
cycle：读取本地/全局状态，先显示待确认门
        ↓
写入门：能否压缩成可复用的 trigger + action？
        ├─ 否 → 跳过，不写账本
        └─ 是 → log-signal
                    ↓
              本地聚类与计数
                    ↓
        未就绪 → 继续积累，不打扰用户
        已就绪 → propose / global-propose
                    ↓
              用户确认落点
        ├─ 项目规则
        ├─ 增强已有 Skill
        ├─ 个人全局 Skill
        ├─ 修订 → 重写提案后再次确认
        └─ 拒绝 → 5 条新的同类信号后解除冷却
                    ↓
用户采纳：Agent 用宿主原生工具修改并验证目标
                    ↓
apply-proposal / global-apply 只记录已完成的采纳
                    ↓
cycle → validate
```

核心数据流始终是：

```text
signals -> clusters -> proposals -> user gate
```

触发层不能绕过这条链路，也不能绕过用户确认门。

## 三道触发闸门

### 第一道：输入侧本地判断

`UserPromptSubmit` 在主模型处理前用本地 Python 规则判断用户是否在纠正工作流、验证标准、工具/Skill 选择或遗漏流程：

```text
none
possible_user_correction
strong_user_correction
```

命中时只向当前正常模型调用加入一句短内部提示。它还会只读检查现有就绪聚类和待确认门，并按会话累计不同用户回合。它不运行 `cycle`，不迁移核心数据，不写 signals/proposals，也不保存用户原文。

### 第二道：Agent 直接调用 + 调用保护门

用户明确要求沉淀，或 Agent 明确发现可迁移方法时，可以在当前轮直接进入 Jinhua，不必等待周期检查。

`PostToolUse` 只记录本轮是否已经调用 Jinhua，防止输入提醒、Agent 主动调用和周期提醒重复触发。保护门只有四种结果：

```text
allow
already_handled
skip_duplicate
block_loop
```

### 第三道：每 8 轮周期回顾

`Stop` 按单个会话固定每 8 个不同用户回合触发一次极短回顾，要求 Agent 检查本轮及此前对话是否出现可复用方法。普通回合只运行本地脚本；周期到期时才请求一次额外模型继续。

Stop 不再要求模型输出状态尾巴，也不解析候选状态。检测到 `stop_hook_active` 或本轮已经进入 Jinhua 时直接放行，避免循环和重复调用。

三道闸门只负责分类、计数、提醒和去重。它们不会自动写信号、创建提案或修改规则。

详细协议见 [references/zh-CN/hook-integration.md](references/zh-CN/hook-integration.md)。

## 什么会被记录

一条经验必须同时具备：

- `trigger`：未来什么情况下使用。
- `action`：遇到这种情况具体怎么做。

并且至少满足一项：

- 用户纠正了工作流、推理方向、验证标准、Skill/工具选择或遗漏流程。
- 同一项目反复出现相同的可复用方法。
- 已修复失败暴露出可迁移原因。
- 成功路径证明某种方法可以复用。
- 用户明确要求记住、沉淀、写入 Skill 或应用到其他项目。

默认跳过：

- 一次性 bug 或事实修正。
- 语气、长短、排版等普通输出偏好。
- 私人事实、用户原文、凭证和敏感项目标识。
- 本地路径、临时命令、局部 API 细节。
- 只对当前对话有用、无法写成 `trigger + action` 的内容。

Agent 负责语义判断和抽象；CLI 只做确定性校验、存储、计数、聚类、迁移和确认结果记账。

## 强度与就绪

`strength` 固定为：

- `1`：普通自我观察。
- `2`：明确用户纠正或重复模式。
- `3`：高成本失败、反复返工或明确沉淀要求。

本地同类聚类满足任一条件即“就绪”：

```text
信号数 >= 3
或
总强度 >= 5
```

`log-signal --immediate` 是唯一即时通道，只用于明确沉淀要求或紧急、可复用的高成本失败。

“就绪”表示证据允许形成提案，不代表已经改规则。下一次输入侧 ready-attention 会把它带回 Agent 注意力，由 Agent 创建完整提案或给出具体跳过原因。

## 跨项目归并

`cycle` 会把本地有效信号压缩后导入个人全局层。全局层只保存哈希化项目身份和脱敏方法证据，不保存原始项目路径。

同类方法优先由规范化的 `operator + action` 生成精确 `method_fingerprint`。CLI 不做模糊相似度自动合并；Agent 负责把语义相同的方法压缩成一致动作。

普通全局就绪：

```text
3 个不同项目 + 5 条证据 + 总强度 7
```

快速路径：

```text
2 个不同项目 + 总强度 6
+ 至少 2 条高强度证据或用户纠正
```

## 三种落点与用户确认门

按强特征优先、轻层兜底：

1. `personal_global_skill`：明确要求所有项目生效、新建独立 Skill、方法本身是独立工作流，或已有成熟全局证据。
2. `skill_patch`：经验明显属于已有 Skill。提案必须给出最合适的具体 Skill 和路径。
3. `project_rule`：只证明当前项目需要，且没有明确 Skill 归属或全局范围。提案必须给出具体项目规则文件建议。

正常分布应是：大部分不写入，项目规则较多，增强已有 Skill 较少，个人全局 Skill 最少。

中文用户确认门：

```text
项目规则(project_rule)
增强已有 Skill(skill_patch)
个人全局 Skill(personal_global_skill)
拒绝(No)
修订(Revision)
```

提案必须包含具体目标、带标题的完整 Markdown 修改块、主要风险、证据、落点和落点理由。占位符不能进入用户确认门。

用户如果改选另一种落点，Agent 先修订提案，使目标、所有者、修改块和风险与新落点一致，再执行修改。

## 采纳是纯记账

用户选择落点后：

1. Agent 先用 Codex、Claude Code 等宿主的原生编辑工具修改目标。
2. Agent 运行对应验证并确认修改成功。
3. 成功后才调用 `apply-proposal` 或 `global-apply`，记录实际目标和修改摘要。

CLI 不再内置 Markdown 写入器。修改或验证失败时，不得把提案记为已采纳。

## 快速开始

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

记录一条已经通过筛选的信号：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> log-signal \
  --source-type user_correction \
  --summary "推荐可采用的外部项目之前先核对 README 和相关源码" \
  --operator verification_path \
  --cluster-key verification_path:verify_projects_before_recommending \
  --context "评估外部项目是否值得采用" \
  --strength 2 \
  --trigger "准备推荐外部项目供用户采用" \
  --action "推荐前读取 README 和相关源码" \
  --transfer-conditions "Skill、库、工具或 Agent 项目推荐" \
  --negative-cases "用户只需要快速列出名称" \
  --verification-path "说明已读取的 README 和源码位置" \
  --auto-init
```

创建提案时，`--target`、`--patch` 和 `--risk` 都是必填项；`--patch` 必须是带标题的完整 Markdown 块。

采纳后只记账：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal \
  --proposal-id <proposal-id> \
  --placement skill_patch \
  --applied-target "<skill-dir>/SKILL.md" \
  --summary "已加入并验证来源核对规则"
```

完整参数和状态变化见 [references/zh-CN/cli-usage.md](references/zh-CN/cli-usage.md)。

## 数据与迁移

项目本地：

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
```

个人全局层：

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

Jinhua 2.0 的本地 schema 是 `3.0`，全局 schema 是 `2.0`。第一次运行非 Hook 核心命令时自动迁移；迁移保留信号、证据、ID、提案状态和采纳结果，删除失效字段与 operator 晋升种子。所有信号永久保留，不再提供压缩删除命令。

迁移可重复执行且结果不变。JSON/JSONL 损坏时会在改写前中止。

一个工作区混有多个无关项目或对话时，使用 `--project-id <stable-key>` 或 `JINHUA_PROJECT_ID` 区分；明文只用于生成哈希，不进入全局记录。

字段说明见 [references/zh-CN/runtime-schema.md](references/zh-CN/runtime-schema.md)，隐私边界见 [references/zh-CN/data-policy.md](references/zh-CN/data-policy.md)。

## 宿主适配

| 宿主 | 入口 | 能力 |
| --- | --- | --- |
| Codex | `.codex-plugin/plugin.json` + `hooks/codex-hooks.json` | 三道触发闸门、Skill、CLI |
| Claude Code | `.claude-plugin/plugin.json` + `hooks/hooks.json` | 原生 Hook 适配、Skill、CLI |
| OpenClaw | `adapters/openclaw/` | 插件/Skill 包装 |
| Hermes | `adapters/hermes/` | Skill 包装 |
| TRAE | `adapters/trae/` | Skill 包装 |
| WorkBuddy | `adapters/workbuddy/` | Skill 包装 |

除 Codex 和 Claude Code 外，其他包装是否自动触发取决于宿主对 Skill/Hook 的支持；它们不会改变 Jinhua 内核。

## Token 与注意力成本

- 第一道分类、ready-attention、回合计数和调用保护都在本地运行，不单独调用模型。
- 普通回合不加载完整 Jinhua Skill，也不运行 `cycle`。
- 固定每 8 轮最多请求一次短回顾；这是唯一周期性额外模型继续。
- Skill 被真正选中后只加载精简后的 `SKILL.md`，详细文档按需读取。
- 没有强制状态尾巴、后台 daemon、外部数据库或向量检索。

## 开源与维护

- 项目入口：[AGENTS.md](AGENTS.md)
- 项目规范：[PROJECT_RULES.md](PROJECT_RULES.md)
- 逐文件索引：[PROJECT_INDEX.md](PROJECT_INDEX.md)
- 贡献指南：[CONTRIBUTING.md](CONTRIBUTING.md)
- 安全政策：[SECURITY.md](SECURITY.md)
- 行为准则：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

许可证：MIT。
