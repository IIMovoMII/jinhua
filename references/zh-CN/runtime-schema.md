# 运行态数据结构

> 英文辅助版本见 [../runtime-schema.md](../runtime-schema.md)。

Jinhua 2.0 把原始证据留在项目本地，全局层只保存压缩后的方法证据和哈希化项目身份。

## 本地运行态

本地文件位于 `<project-root>/.jinhua/data/`。

### signals.jsonl

必填字段：

- `id`、`timestamp`
- `source_type`
- `summary`、`context`
- `operator`、`cluster_key`
- `strength`：只能是 `1`、`2`、`3`
- `status`：2.0 中固定为 `active`

可选方法卡字段：

- `trigger`：什么时候使用
- `action`：具体怎么做
- `transfer_conditions`：能迁移到哪里
- `negative_cases`：什么情况下不要使用
- `verification_path`：如何验证
- `risk`
- `immediate`

`cluster_key` 必须使用 `operator:lowercase_slug`。operator 只用于方法分类，不再存在 operator 自身晋升系统。

### cluster-state.json

schema 版本是 `3.0`。

```json
{
  "schema_version": "3.0",
  "clusters": {
    "verification_path:verify_before_claiming": {
      "cluster_key": "verification_path:verify_before_claiming",
      "operator": "verification_path",
      "signal_count": 3,
      "strength_sum": 5,
      "sample_signal_ids": ["sig_..."],
      "last_seen": "2026-07-19T00:00:00Z",
      "status": "ready",
      "ready_reason": "signal_count >= 3",
      "cooldown_signal_remaining": 0
    }
  },
  "updated_at": "2026-07-19T00:00:00Z"
}
```

聚类状态包括 `active`、`ready`、`proposed`、`adopted`、`cooldown`。

### proposals.jsonl

必填字段：

- `id`、`timestamp`
- `cluster_key`、`trigger`
- `evidence_signal_ids`
- `placement`、`placement_reason`
- `target`、`patch`、`risk`
- `status`、`user_gate`

不同落点还需要：

- `skill_patch`：`recommended_skill`、`recommended_skill_path`、`recommended_skill_reason`
- `project_rule`：`agent_profile`、`recommended_project_rule_file`、对应路径和理由

提案状态包括 `pending_user_gate`、`needs_revision`、`applied`、`rejected`。

### adopted-edits.jsonl

必填字段：

- `id`、`timestamp`、`proposal_id`
- `cluster_key`
- `applied_target`
- `edit_summary`
- `placement`、`placement_reason`

采纳命令只记录已经由 agent 完成并验证的修改，不负责写文件。

### rejected-proposals.jsonl

记录提案 ID、聚类、拒绝原因、证据 ID 和 `cooldown_signal_remaining`。默认需要 5 条新的同类信号才解除冷却，不再使用时间冷却。

### evolution-state.json

schema 版本是 `3.0`。保存最后提案 ID、信号总数、采纳数、拒绝数和更新时间。

## 全局运行态

全局文件默认位于 `<jinhua-dir>/global-data/`。

### global-signals.jsonl

每条本地信号最多导入一次，保存：

- 哈希化 `project_hash`
- 本地信号 ID 和去重键
- `method_fingerprint`、`method_key`、`method_signature`
- operator、压缩摘要、来源类型、强度和风险
- 已提供的方法卡字段
- 固定状态 `active`

不会导入用户原文或原始项目路径。

### global-clusters.json

schema 版本是 `2.0`。每个方法指纹保存证据数、总强度、不同项目哈希、样本 ID、来源统计、纠正/高强度计数、就绪状态和剩余冷却信号数。

### global-proposals.jsonl

保存方法指纹、证据、落点、目标、完整 patch、风险、项目/证据/强度统计和用户门。全局落点只能是 `skill_patch` 或 `personal_global_skill`。

### adopted-global-edits.jsonl

保存实际修改目标、修改摘要、placement、方法指纹和推荐 Skill 信息。

### rejected-global-proposals.jsonl

保存提案和方法 ID、拒绝原因、证据 ID 和剩余冷却信号数。

### project-index.json

schema 版本是 `2.0`。只保存项目哈希、身份来源、首次/最后出现时间、导入信号数和最后扫描数，不保存原始显式项目 ID。

### global-state.json

schema 版本是 `2.0`。保存最后扫描时间、项目/信号/就绪统计和最后提案 ID。

## 触发层运行态

`.jinhua/runtime/invocation-guard.json` 不是经验账本。它只保存哈希化会话/回合、近期 Jinhua 调用、周期 Stop 票据和每个会话的回合数。Hook 可以写这个文件，但不会触发核心账本迁移。

## 2.0 自动迁移

第一次运行非 Hook 核心命令时，本地 schema 从 `2.0` 升到 `3.0`，全局 schema 从 `1.0` 升到 `2.0`。

迁移保留 ID、证据、状态、计数、placement、target、patch 和 risk；删除失效的 confidence、proposal decision、时间冷却、内置写入器字段和 operator 种子。旧 operator 晋升提案会变成普通提案。

迁移可重复运行且结果不变，写入时使用原子替换；任何 JSON 损坏都会在改写前中止。
