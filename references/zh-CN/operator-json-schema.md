# 运行态 Schema

> 英文 [../operator-json-schema.md](../operator-json-schema.md) 是主版本；本文件是中文镜像。

所有 JSONL 文件都是“一行一个 JSON 对象”。

## signals.jsonl

必填字段：

- `id`
- `timestamp`
- `source_type`
- `summary`
- `context`
- `operator`
- `cluster_key`
- `strength`
- `status`

可选 signal card 字段：

- `trigger`
- `action`
- `transfer_conditions`
- `negative_cases`
- `verification_path`
- `confidence`
- `risk`
- `immediate`

`confidence` 范围是 0 到 1，只是排序提示。

## cluster-state.json

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

cluster 状态包括：`active`、`ready`、`proposed`、`adopted`、`cooldown`。

## proposals.jsonl

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

proposal 状态包括：`pending_user_gate`、`applied`、`rejected`、`needs_revision`。

## adopted-edits.jsonl

记录被用户接受的本地提案：

- `id`
- `timestamp`
- `proposal_id`
- `cluster_key`
- `target_skill`
- `edit_summary`
- `decision`
- `applied_path`

## rejected-proposals.jsonl

记录被用户拒绝的本地提案：

- `id`
- `timestamp`
- `proposal_id`
- `cluster_key`
- `reason`
- `cooldown_until`
- `cooldown_signal_remaining`
- `evidence_signal_ids`

## global-signals.jsonl

每条记录都是从本地 signal 导入的、脱敏压缩后的晋升证据。

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

`method_fingerprint` 来自规范化后的 method key。优先使用 `operator + action`，然后回退到 `cluster_key`，最后回退到 signal-card context 或 summary。`trigger` 和 `transfer_conditions` 作为迁移判断和 merge review 的证据。

## global-clusters.json

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

## project-index.json

只保存项目身份哈希：

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

核心 operator seed records 仍保留兼容和验证用途，但不是当前运行主闭环。
