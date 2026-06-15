# Runtime Schemas

All JSONL files contain one JSON object per line.

## signals.jsonl

Required:

- `id`
- `timestamp`
- `source_type`
- `summary`
- `context`
- `operator`
- `cluster_key`
- `strength`
- `status`

Optional signal card:

- `trigger`
- `action`
- `transfer_conditions`
- `negative_cases`
- `verification_path`
- `confidence`
- `risk`
- `immediate`

`confidence` is 0..1 and is only a ranking hint.

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

Cluster statuses: `active`, `ready`, `proposed`, `adopted`, `cooldown`.

## proposals.jsonl

Required:

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

Proposal statuses: `pending_user_gate`, `applied`, `rejected`, `needs_revision`.

## adopted-edits.jsonl

Records accepted local proposals:

- `id`
- `timestamp`
- `proposal_id`
- `cluster_key`
- `target_skill`
- `edit_summary`
- `decision`
- `applied_path`

## rejected-proposals.jsonl

Records rejected local proposals:

- `id`
- `timestamp`
- `proposal_id`
- `cluster_key`
- `reason`
- `cooldown_until`
- `cooldown_signal_remaining`
- `evidence_signal_ids`

## global-signals.jsonl

One sanitized promotion record per imported local signal.

Required:

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

Optional:

- `method_signature`
- `trigger`
- `action`
- `transfer_conditions`
- `negative_cases`
- `verification_path`
- `confidence`
- `risk`

`method_fingerprint` is derived from the normalized method key. The key prefers `operator + action`, then falls back to `cluster_key`, then signal-card context or summary. `trigger` and `transfer_conditions` remain evidence for transfer judgment and merge review.

## global-clusters.json

```json
{
  "schema_version": "1.0",
  "clusters": {
    "abc123methodhash": {
      "method_fingerprint": "abc123methodhash",
      "method_key": "verification_path:verify_readme_source_recommending_external_projects",
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

Required:

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

Stores hashed project identities only:

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

Seed operator records remain supported for compatibility and validation. They are not the main runtime loop.
