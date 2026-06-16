# 运行态结构

> [../operator-json-schema.md](../operator-json-schema.md) 是英文主版本；本文件用中文解释各个 JSON/JSONL 文件的作用。

所有 JSONL 文件都是“一行一个 JSON 对象”。字段名保持英文，避免脚本和旧数据不兼容。

## signals.jsonl

本地方法论信号记录。每一行是一条脱敏后的经验。

必填字段：

- `id`：信号 id。
- `timestamp`：记录时间。
- `source_type`：信号来源。
- `summary`：脱敏摘要。
- `context`：任务上下文。
- `operator`：方法类型。
- `cluster_key`：本地聚类键。
- `strength`：信号强度。
- `status`：状态。

可选信号卡字段：

- `trigger`：触发条件。
- `action`：核心动作。
- `transfer_conditions`：迁移条件。
- `negative_cases`：反例或禁用场景。
- `verification_path`：验证路径。
- `confidence`：辅助信心分。
- `risk`：风险。
- `immediate`：是否来自用户明确要求立即沉淀。

`confidence` 范围是 0 到 1，只用于辅助排序。

## cluster-state.json

本地聚类状态。它把同类信号汇总到一个 `cluster_key` 下。

```json
{
  "schema_version": "2.0",
  "clusters": {
    "verification_path:read_readme_and_source_before_recommending_projects": {
      "cluster_key": "verification_path:read_readme_and_source_before_recommending_projects",
      "operator": "verification_path",
      "signal_count": 3,
      "strength_sum": 5,
      "sample_signal_ids": ["sig_..."],
      "last_seen": "2026-06-15T00:00:00Z",
      "status": "ready",
      "ready_reason": "signal_count >= 3",
      "cooldown_until": "",
      "cooldown_signal_remaining": 0
    }
  },
  "updated_at": "2026-06-15T00:00:00Z"
}
```

聚类状态包括：

- `active`：还在积累。
- `ready`：已达到提案条件。
- `proposed`：已经生成提案。
- `adopted`：已被采纳。
- `cooldown`：被拒绝后冷却中。

## proposals.jsonl

本地提案记录。提案必须等待用户确认。

必填字段：

- `id`
- `timestamp`
- `cluster_key`
- `decision`
- `trigger`
- `evidence_signal_ids`
- `target`
- `patch`
- `risk`
- `status`
- `user_gate`

新提案建议包含：

- `placement`：落点，取值为 `project_rule`、`skill_patch` 或 `personal_global_skill`。
- `placement_reason`：为什么推荐这个落点。
- `recommended_skill`：推荐增强的本地 Skill 名称。
- `recommended_skill_path`：推荐增强的本地 `SKILL.md` 路径。
- `recommended_skill_reason`：为什么推荐这个 Skill。
- `agent_profile`：只在 `project_rule` 时使用，表示当前按哪个 agent 档案推荐规则文件。
- `recommended_project_rule_file`：只在 `project_rule` 时使用，推荐的项目规则文件。
- `recommended_project_rule_path`：只在 `project_rule` 时使用，推荐文件的绝对路径。
- `recommended_project_rule_reason`：只在 `project_rule` 时使用，说明为什么推荐这个文件。
- `project_rule_candidates`：只在 `project_rule` 时使用，候选规则文件列表。

提案状态包括：

- `pending_user_gate`：等待用户确认。
- `applied`：已采纳。
- `rejected`：已拒绝。
- `needs_revision`：需要修改后再确认。

## adopted-edits.jsonl

记录被用户接受的本地提案：

- `id`
- `timestamp`
- `proposal_id`
- `cluster_key`
- `target_skill`
- `edit_summary`
- `decision`
- `placement`
- `placement_reason`
- `recommended_skill`
- `recommended_skill_path`
- `agent_profile`
- `recommended_project_rule_file`
- `recommended_project_rule_path`
- `recommended_project_rule_reason`
- `applied_path`

## rejected-proposals.jsonl

记录被用户拒绝或要求修改的本地提案：

- `id`
- `timestamp`
- `proposal_id`
- `cluster_key`
- `reason`
- `cooldown_until`
- `cooldown_signal_remaining`
- `evidence_signal_ids`

## global-signals.jsonl

全局信号记录。每条记录都来自本地信号，但只保存脱敏、压缩后的晋升证据。

必填字段：

- `id`
- `timestamp`
- `project_hash`
- `source_signal_id`
- `source_timestamp`
- `dedupe_key`
- `method_fingerprint`
- `method_key`
- `operator`
- `local_cluster_key`
- `summary`
- `context`
- `source_type`
- `strength`
- `status`

可选字段：

- `method_signature`
- `trigger`
- `action`
- `transfer_conditions`
- `negative_cases`
- `verification_path`
- `confidence`
- `risk`

`method_fingerprint` 来自规范化后的方法键。生成顺序是：优先用 `operator + action`，再回退到 `cluster_key`，最后才参考信号卡里的 `context` 或 `summary` 字段。`trigger` 和 `transfer_conditions` 只作为迁移判断和合并审查的证据。

## global-clusters.json

全局聚类状态。它判断同一方法是否在多个项目中重复出现。

```json
{
  "schema_version": "1.0",
  "clusters": {
    "abc123methodhash": {
      "method_fingerprint": "abc123methodhash",
      "method_key": "verification_path:verify_readme_source_recommending",
      "operator": "verification_path",
      "evidence_count": 5,
      "strength_sum": 7,
      "project_hashes": ["projecthash1", "projecthash2", "projecthash3"],
      "sample_global_signal_ids": ["gsig_..."],
      "summary_samples": ["Read README and source before recommending a project."],
      "method_signature_samples": ["action=verify README and source | trigger=recommending projects"],
      "source_type_counts": {"user_correction": 3},
      "user_correction_count": 3,
      "high_strength_count": 1,
      "last_seen": "2026-06-15T00:00:00Z",
      "status": "ready",
      "ready_reason": "unique_project_count >= 3 and strength_sum >= 7",
      "cooldown_until": "",
      "cooldown_signal_remaining": 0
    }
  },
  "updated_at": "2026-06-15T00:00:00Z"
}
```

## global-proposals.jsonl

全局提案记录。它用于跨项目方法是否写入 Skill 的用户确认。

必填字段：

- `id`
- `timestamp`
- `method_fingerprint`
- `method_key`
- `operator`
- `decision`
- `trigger`
- `evidence_global_signal_ids`
- `target`
- `patch`
- `risk`
- `project_count`
- `evidence_count`
- `strength_sum`
- `status`
- `user_gate`

新全局提案建议包含：

- `placement`：通常是 `skill_patch` 或 `personal_global_skill`。
- `placement_reason`：为什么推荐这个落点。
- `recommended_skill`：如果适合增强已有 Skill，这里记录推荐 Skill。
- `recommended_skill_path`：推荐 Skill 的本地路径。
- `recommended_skill_reason`：推荐理由。

## project-index.json

只保存项目身份哈希，不保存原始路径或明文项目 id：

```json
{
  "schema_version": "1.0",
  "projects": {
    "projecthash": {
      "project_hash": "projecthash",
      "identity_source": "git_remote",
      "first_seen": "2026-06-15T00:00:00Z",
      "last_seen": "2026-06-15T00:00:00Z",
      "imported_signal_count": 3,
      "last_scan_signal_count": 3
    }
  },
  "updated_at": "2026-06-15T00:00:00Z"
}
```

## crystallized-operators.jsonl

核心 operator 种子记录（seed records）仍保留，用于兼容和验证。但当前运行主闭环不依赖它来做最终判断。
