# 术语与参数速查

Jinhua 的命令、参数、JSON 字段、operator id 和 placement id 必须保持英文，因为脚本和运行态会直接引用它们。中文文档解释含义，不改接口名称。

## 核心命令

| 名称 | 中文理解 | 作用 |
| --- | --- | --- |
| `init` | 初始化 | 创建项目本地运行态。 |
| `cycle` | 自动检查点 | 初始化或迁移、汇总本地/全局状态、导入跨项目证据、显示就绪聚类和待确认门。 |
| `classify-input` | 输入纠错分类 | 本地判断输入属于无纠错、可能纠错还是强纠错。 |
| `codex-user-prompt-submit` | 第一道闸门 | 本地分类、就绪提醒和每会话回合计数。 |
| `codex-post-tool-use` | 第二道闸门 | 记录本轮已经进入 Jinhua，防止重复。 |
| `codex-stop` | 第三道闸门 | 固定每 8 轮请求一次极短历史回顾，并防止 Stop 循环。 |
| `guard` | 调用保护门 | 手动查看或记录一次调用保护判断。 |
| `log-signal` | 记录信号 | 记录一条已经通过写入门的方法经验。 |
| `list-clusters` | 查看本地聚类 | 查看同类信号的数量、强度和状态。 |
| `propose` | 创建本地提案 | 为就绪本地聚类创建完整用户确认提案。 |
| `apply-proposal` | 记录本地采纳 | Agent 原生编辑并验证后，记录实际目标和修改摘要；不写目标文件。 |
| `reject-proposal` | 拒绝或修订 | 记录拒绝，或保存修订反馈并保持确认门。 |
| `global-cycle` | 全局检查点 | 手动导入和查看跨项目层；普通 `cycle` 已经会执行导入。 |
| `global-status` | 全局状态 | 查看全局项目、信号、聚类和提案统计。 |
| `global-propose` | 创建全局提案 | 为就绪跨项目方法创建完整用户确认提案。 |
| `global-apply` | 记录全局采纳 | 原生编辑并验证后记录全局采纳；不写目标文件。 |
| `global-reject` | 全局拒绝或修订 | 记录全局提案的拒绝或修订反馈。 |
| `status` | 本地状态 | 查看当前项目运行态统计。 |
| `validate` | 验证数据 | 迁移后检查 JSON/JSONL、引用关系和废弃字段。 |

## 常见参数

| 名称 | 中文理解 | 说明 |
| --- | --- | --- |
| `--project-root` | 项目根目录 | 本地运行态写入该项目的 `.jinhua/`。 |
| `--project-id` | 显式项目身份 | 一个工作区混有无关项目/对话时提供稳定身份；全局层只保存哈希。 |
| `--runtime-dir` | 本地运行态覆盖 | 主要用于测试。 |
| `--global-runtime-dir` | 全局运行态覆盖 | 主要用于测试或迁移验证。 |
| `--agent-profile` | Agent 类型 | 用于推荐项目规则文件，支持 Codex、Claude、Copilot、TRAE、Hermes、OpenClaw、WorkBuddy 和通用兜底。 |
| `--source-type` | 信号来源 | 例如 `user_correction`、`success_trace`、`failure_trace`、`self_observation`。 |
| `--summary` | 摘要或修改摘要 | 在 `log-signal` 中是脱敏经验摘要；在 apply 中是已验证修改摘要。 |
| `--operator` | 方法类型 | 认知操作分类。 |
| `--cluster-key` | 本地聚类键 | 格式是 `operator:lowercase_slug`。 |
| `--context` | 任务上下文 | 脱敏说明经验出现在哪类任务。 |
| `--strength` | 信号强度 | `1` 普通、`2` 明确、`3` 高成本或明确沉淀。 |
| `--trigger` | 触发条件 | 未来什么时候使用这个方法。 |
| `--action` | 方法动作 | 可迁移的核心动作；全局精确归并优先使用。 |
| `--transfer-conditions` | 迁移条件 | 方法适合迁移到哪些任务或项目。 |
| `--negative-cases` | 反例 | 什么时候不应使用。 |
| `--verification-path` | 验证路径 | 如何确认方法已经正确执行。 |
| `--risk` | 主要风险 | 提案中必须是具体内容，不能是占位符。 |
| `--immediate` | 即时通道 | 只用于明确沉淀要求或紧急、可复用的高成本失败。 |
| `--placement` | 落点 | `project_rule`、`skill_patch` 或 `personal_global_skill`。 |
| `--placement-reason` | 落点理由 | 说明为什么这是最小有用落点。 |
| `--recommended-skill` | 推荐 Skill | `skill_patch` 必须指定的具体所有者。 |
| `--recommended-skill-path` | 推荐 Skill 路径 | 推荐 Skill 的具体 `SKILL.md` 路径。 |
| `--target` | 提案目标 | 必须具体，不能使用方括号占位符。 |
| `--patch` | 完整修改块 | 必须是带 Markdown 标题的完整规则块。 |
| `--proposal-id` | 提案 ID | 采纳、拒绝或修订时定位提案。 |
| `--applied-target` | 实际修改目标 | Agent 已经完成并验证的真实目标。 |
| `--revision` | 修订模式 | 保存用户反馈，提案状态变为 `needs_revision`。 |

## 三种落点

| id | 中文理解 | 使用条件 |
| --- | --- | --- |
| `project_rule` | 项目规则 | 当前项目重复需要，但没有明确 Skill 所有者或全局范围。 |
| `skill_patch` | 增强已有 Skill | 方法明确属于一个已有 Skill；必须推荐具体 Skill 和路径。 |
| `personal_global_skill` | 个人全局 Skill | 明确所有项目生效、独立工作流，或已有成熟跨项目证据。 |

## 主要状态

| 状态 | 中文理解 |
| --- | --- |
| `active` | 正在积累证据。 |
| `ready` | 达到提案阈值，但还没有改变规则。 |
| `proposed` | 已创建提案。 |
| `pending_user_gate` | 正在等待用户选择落点、拒绝或修订。 |
| `needs_revision` | 用户要求修改提案后重新确认。 |
| `applied` | 用户采纳，Agent 已修改并验证，账本已记录。 |
| `rejected` | 用户拒绝。 |
| `adopted` | 聚类对应的提案已经采纳。 |
| `cooldown` | 拒绝后等待 5 条新的同类信号。 |

## 数据文件

| 文件 | 作用 |
| --- | --- |
| `signals.jsonl` | 项目本地方法信号。 |
| `cluster-state.json` | 本地聚类和就绪状态，schema `3.0`。 |
| `proposals.jsonl` | 本地提案和确认状态。 |
| `adopted-edits.jsonl` | 已完成、已验证的本地采纳记录。 |
| `rejected-proposals.jsonl` | 本地拒绝和固定信号冷却。 |
| `evolution-state.json` | 本地统计状态，schema `3.0`。 |
| `invocation-guard.json` | 触发层会话/回合计数和去重，不是经验账本。 |
| `global-signals.jsonl` | 跨项目压缩信号。 |
| `global-clusters.json` | 精确方法指纹聚类，schema `2.0`。 |
| `global-proposals.jsonl` | 全局提案。 |
| `project-index.json` | 哈希化项目身份和导入统计，schema `2.0`。 |

## 关键字段

| 字段 | 中文理解 |
| --- | --- |
| `method_fingerprint` | 基于规范化方法的稳定哈希，用于精确跨项目归并。 |
| `method_key` | 可读的规范化方法键。 |
| `dedupe_key` | 防止同一项目同一信号重复导入。 |
| `project_hash` | 项目身份哈希。 |
| `identity_source` | 项目身份来自 explicit、env、git remote 或 path。 |
| `user_gate` | 带落点的用户确认门。 |
| `cooldown_signal_remaining` | 还需要多少条新的同类信号才能解除冷却。 |
| `applied_target` | 实际完成修改的目标。 |
| `edit_summary` | 已验证修改的简短摘要。 |

## Operator IDs

Jinhua 保留 8 个核心分类和一个兜底：

| id | 中文理解 |
| --- | --- |
| `problem_representation` | 问题表征 |
| `domain_knowledge_access` | 领域知识接入 |
| `constraint_recognition` | 约束识别 |
| `candidate_competition` | 候选方案比较 |
| `counterfactual_check` | 反事实检查 |
| `verification_path` | 验证路径 |
| `compression` | 压缩表达与去重 |
| `skill_merge_suggestion` | Skill 归属或合并建议 |
| `other` | 无法归入以上分类时的兜底 |
