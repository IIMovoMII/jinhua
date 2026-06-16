# CHANGELOG

## 2026-06-15 Placement-Aware Gate

- Added explicit proposal placements: `project_rule`, `skill_patch`, and `personal_global_skill`.
- Added local Skill recommendation for `skill_patch` proposals so users do not need to find the target Skill manually.
- Updated `cycle`, `propose`, `global-propose`, `apply-proposal`, and `global-apply` to carry placement fields through the closed loop.

## 2026-06-15 Public Release

- Published `jinhua` as a compact Skill + CLI for user-gated Skill evolution.
- Added English and Chinese documentation: default Chinese public docs plus English mirrors.
- Added `references/zh-CN/` with translated CLI, schema, data policy, hook, maintenance, and glossary docs.
- Made Chinese the default public documentation while keeping English mirrors for international users.
- Kept CLI commands, option names, JSON field names, and operator ids in English, with Chinese explanations in the glossary.

## Product Features

- Made `cycle` the single automatic checkpoint for local initialization, local status, global import, global status, pending gates, and ready proposal skeletons.
- Added structured signal-card fields to `log-signal`: `trigger`, `action`, `transfer_conditions`, `negative_cases`, `verification_path`, and `confidence`.
- Improved global method fingerprints to prefer `operator + action + trigger + transfer_conditions`, with fallback to `cluster_key` and summary.
- Added `global-merge-suggestions` for review-only duplicate method candidates.

## Product Boundary

The project is now considered a stable usable mainline:

- deterministic CLI
- project-local signals
- global promotion memory
- proposal skeletons
- user-gated apply/reject
- validation

Future changes should be limited to bug fixes, threshold tuning from real usage, validation coverage, and documentation compression.
