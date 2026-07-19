# Runtime Schema

Jinhua 2.0 keeps raw evidence project-local and stores only compressed evidence in the global promotion runtime.

## Local Runtime

Local files live under `<project-root>/.jinhua/data/`.

### signals.jsonl

Required fields:

- `id`, `timestamp`
- `source_type`
- `summary`, `context`
- `operator`, `cluster_key`
- `strength`: `1`, `2`, or `3`
- `status`: always `active` in 2.0

Optional reusable signal-card fields:

- `trigger`
- `action`
- `transfer_conditions`
- `negative_cases`
- `verification_path`
- `risk`
- `immediate`

`cluster_key` must use `operator:lowercase_slug`. Operator ids are fixed in the CLI and remain a classification taxonomy, not an operator-evolution system.

### cluster-state.json

Schema version: `3.0`.

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

Cluster statuses: `active`, `ready`, `proposed`, `adopted`, `cooldown`.

### proposals.jsonl

Required fields:

- `id`, `timestamp`
- `cluster_key`, `trigger`
- `evidence_signal_ids`
- `placement`, `placement_reason`
- `target`, `patch`, `risk`
- `status`, `user_gate`

Placement-specific fields:

- `skill_patch`: `recommended_skill`, `recommended_skill_path`, `recommended_skill_reason`
- `project_rule`: `agent_profile`, `recommended_project_rule_file`, `recommended_project_rule_path`, `recommended_project_rule_reason`

Proposal statuses: `pending_user_gate`, `needs_revision`, `applied`, `rejected`.

### adopted-edits.jsonl

Required fields:

- `id`, `timestamp`, `proposal_id`
- `cluster_key`
- `applied_target`
- `edit_summary`
- `placement`, `placement_reason`

Recommendation fields may be copied from the proposal for auditability. Apply commands record an already completed and verified edit; they do not edit files.

### rejected-proposals.jsonl

Required fields:

- `id`, `timestamp`, `proposal_id`, `cluster_key`
- `reason`
- `cooldown_signal_remaining`
- `evidence_signal_ids`

The default cooldown is 5 new same-cluster signals. There is no time-based cooldown.

### evolution-state.json

Schema version: `3.0`.

Tracks `last_proposal_id`, total signal count, adopted edit count, rejected proposal count, and `updated_at`.

## Global Runtime

Global files live under `<jinhua-dir>/global-data/` unless `--global-runtime-dir` overrides the location.

### global-signals.jsonl

Stores one compressed record per imported local signal:

- hashed `project_hash`
- `source_signal_id` and `dedupe_key`
- `method_fingerprint`, `method_key`, `method_signature`
- operator, compressed summary/context, source type, strength, risk
- reusable signal-card fields when present
- status `active`

Raw project paths and original user messages are not promoted.

### global-clusters.json

Schema version: `2.0`.

Each fingerprint stores evidence count, strength sum, unique project hashes, sample ids, summary/signature samples, source-type counts, correction/high-strength counts, readiness state, and `cooldown_signal_remaining`.

### global-proposals.jsonl

Required fields:

- `id`, `timestamp`
- `method_fingerprint`, `method_key`, `operator`
- `trigger`, `evidence_global_signal_ids`
- `placement`, `placement_reason`
- `target`, `patch`, `risk`
- project/evidence/strength counts
- `status`, `user_gate`

Global placement is only `skill_patch` or `personal_global_skill`.

### adopted-global-edits.jsonl

Uses the same adoption evidence as local records: `proposal_id`, `applied_target`, `edit_summary`, placement, method fingerprint/key, and recommendation metadata.

### rejected-global-proposals.jsonl

Stores proposal/method ids, rejection reason, evidence ids, and `cooldown_signal_remaining`.

### project-index.json

Schema version: `2.0`. Stores hashed project identities, identity source, first/last seen timestamps, imported signal count, and last scan count. It never stores the raw explicit project id.

### global-state.json

Schema version: `2.0`. Stores last scan time/counts, last ready count, last proposal id, and update time.

## Trigger Runtime

`.jinhua/runtime/invocation-guard.json` is not an experience ledger. Schema version `2` stores only hashed sessions/turns, recent Jinhua invocation events, and per-session turn counts. The eighth-turn condition is computed from each new `turn_id` instead of a persisted Stop ticket. Reading old runtime removes `stop_tickets` and `periodic_stop_due`; Hooks may write this file, but core migrations do not run from Hooks.

## 2.0 Migration

The first non-Hook core CLI command migrates local schema `2.0 -> 3.0` and global schema `1.0 -> 2.0`.

Migration preserves ids, evidence, statuses, counts, placement, target, patch, and risk. It removes obsolete confidence, proposal decision, time cooldown, built-in writer fields, and operator seed data. Old operator-promotion proposals become ordinary proposals. Migration is idempotent and uses atomic file replacement; malformed JSON aborts before any rewrite.
