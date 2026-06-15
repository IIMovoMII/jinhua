# 术语与参数速查

jinhua 会保留 CLI 命令、参数名、JSON 字段名和 operator id 的英文形式。原因很简单：这些名字会被脚本、数据文件和示例命令直接引用，翻译后命令就不能运行，旧数据也可能不兼容。

中文文档负责解释它们的含义，但不改这些名字。

## 核心命令

| 名称 | 中文理解 | 作用 |
|---|---|---|
| `cycle` | 自动检查点 | 初始化运行态，扫描本地聚类，导入全局层，提示待确认事项和成熟聚类。 |
| `log-signal` | 记录信号 | 记录一条可复用的方法论信号。 |
| `list-clusters` | 查看本地聚类 | 查看本地信号聚类的状态、数量和强度。 |
| `propose` | 创建本地提案 | 为成熟的本地聚类创建用户确认提案。 |
| `apply-proposal` | 采纳本地提案 | 用户说 `Yes` 后记录采纳，必要时写入目标文件。 |
| `reject-proposal` | 拒绝本地提案 | 用户说 `No` 或 `Revision` 后记录拒绝/修订，并进入冷却。 |
| `global-cycle` | 全局检查点 | 手动导入本地信号并查看全局晋升层；普通流程里 `cycle` 已经会做这件事。 |
| `global-status` | 全局状态 | 查看全局信号、聚类、提案和项目数量。 |
| `global-propose` | 创建全局提案 | 为成熟的跨项目方法聚类创建用户确认提案。 |
| `global-merge-suggestions` | 全局合并建议 | 只读列出相似的跨项目方法，不修改数据。 |
| `global-apply` | 采纳全局提案 | 用户说 `Yes` 后记录全局采纳。 |
| `global-reject` | 拒绝全局提案 | 用户说 `No` 或 `Revision` 后记录全局拒绝/修订。 |
| `compact` | 压缩信号 | 删除低价值原始信号，保留聚类摘要和强证据。 |
| `status` | 本地状态 | 查看当前项目本地运行态统计。 |
| `validate` | 验证数据 | 检查 JSON/JSONL 数据结构和引用关系。 |

## 常见参数

| 名称 | 中文理解 | 说明 |
|---|---|---|
| `--project-root` | 项目根目录 | 指定当前项目；运行态会写到这个项目的 `.jinhua/`。 |
| `--project-id` | 显式项目身份 | 一个工作区混有多个不相关项目或多段对话时，用稳定 id 区分；写入全局层前会先哈希。 |
| `--runtime-dir` | 本地运行态目录 | 覆盖默认 `.jinhua/`，主要用于测试。 |
| `--global-runtime-dir` | 全局运行态目录 | 覆盖默认 `global-data/`，主要用于测试或迁移。 |
| `--source-type` | 信号来源类型 | 例如 `user_correction`、`success_trace`、`failure_trace`。 |
| `--summary` | 信号摘要 | 模型写的脱敏方法论摘要，不是用户原文。 |
| `--operator` | 方法类型 | 认知操作分类，例如 `verification_path`。 |
| `--cluster-key` | 本地聚类键 | 把同类信号归到一起，格式必须是 `operator:short_method_slug`。 |
| `--context` | 任务上下文 | 简短说明信号出现在哪类任务中。 |
| `--strength` | 信号强度 | `1` 普通，`2` 明确，`3` 高成本/紧急。 |
| `--trigger` | 触发条件 | 什么时候应该使用这个方法。 |
| `--action` | 方法动作 | 可迁移的核心动作；全局合并优先看它。 |
| `--transfer-conditions` | 迁移条件 | 这个方法适合迁移到哪些场景。 |
| `--negative-cases` | 反例/禁用场景 | 什么时候不应该使用这个方法。 |
| `--verification-path` | 验证路径 | 如何检查这个方法是否被正确执行。 |
| `--confidence` | 信心分 | 0 到 1 的辅助排序信号，不是最终判断。 |
| `--auto-init` | 自动初始化 | 如果运行态不存在，先创建。 |
| `--immediate` | 立即触发 | 用户明确要求现在就沉淀或写入时使用。 |

## JSON 字段

| 字段 | 中文理解 | 说明 |
|---|---|---|
| `signals.jsonl` | 信号记录文件 | 每行一条本地方法论信号。 |
| `cluster-state.json` | 本地聚类状态 | 汇总同类信号。 |
| `proposals.jsonl` | 本地提案记录 | 记录用户确认前后的本地提案。 |
| `global-signals.jsonl` | 全局信号记录 | 从项目本地晋升来的压缩证据。 |
| `global-clusters.json` | 全局方法聚类 | 跨项目方法指纹聚类。 |
| `project-index.json` | 项目索引 | 只保存项目哈希和计数，不保存原始路径。 |
| `identity_source` | 身份来源 | 说明项目哈希来自 `explicit`、`env`、`git_remote` 还是 `path`。 |
| `method_fingerprint` | 方法指纹 | 跨项目归并用的稳定哈希。 |
| `method_key` | 方法键 | 可读形式的规范化方法名称。 |
| `dedupe_key` | 去重键 | 避免同一项目的同一信号重复导入。 |
| `status` | 状态 | 例如 `active`、`ready`、`proposed`、`cooldown`。 |
| `user_gate` | 用户确认门 | 始终是 `Yes` / `No` / `Revision`。 |

## Operator IDs

| id | 中文理解 |
|---|---|
| `problem_representation` | 问题表征 |
| `domain_knowledge_access` | 领域知识接入 |
| `constraint_recognition` | 约束识别 |
| `candidate_competition` | 候选方案比较 |
| `counterfactual_check` | 反事实检查 |
| `verification_path` | 验证路径 |
| `compression` | 压缩与去重 |
| `skill_merge_suggestion` | Skill 合并/写入建议 |
| `other` | 其他 |
