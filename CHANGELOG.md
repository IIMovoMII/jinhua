# CHANGELOG

## 2026-06-27 Heavier Local Input Gate

- Grouped local correction matches by semantic category and returned structured match evidence from `classify-input`.
- Expanded the fully local first gate for missed Skill/tool/procedure activation cues while keeping ordinary clarification prompts out of strong triggering.

## 2026-06-27 Localized User Gate And Second Slimming

- Changed user-facing gate labels to Chinese-first display with stable canonical ids: `项目规则(project_rule)`, `增强已有 Skill(skill_patch)`, `个人全局 Skill(personal_global_skill)`, `拒绝(No)`, and `修订(Revision)`.
- Kept only the core operator seed file under root `data/`; removed empty ledger templates that looked like runtime state.
- Updated README, Skill docs, project maps, hook docs, glossary, and the static logic page.

## 2026-06-27 Codex Three-Gate Trigger Layer

- Replaced the old hook-first wake path with a Codex-focused three-gate trigger layer: local input correction classification, same-turn invocation guard, and lightweight output-state tail parsing.
- Added `hooks/codex-hooks.json` plus thin Codex hook wrappers for `UserPromptSubmit`, `PostToolUse`, and `Stop`.
- Added trigger-layer CLI commands: `classify-input`, `codex-user-prompt-submit`, `codex-post-tool-use`, `codex-stop`, `parse-output-state`, and `guard`.
- Kept `wake-check` and `hook-user-prompt-submit` as legacy compatibility commands, no longer the primary trigger path.
- Kept the core loop unchanged: `cycle`, `log-signal`, clustering, proposals, placement ladder, and the user gate still own Skill evolution.
- Added trigger-layer tests covering correction classification, internal hints, output-state parsing/stripping, invocation guard deduplication, direct agent calls, Stop-loop protection, and old hook manifest cleanup.

## 2026-06-25 Marketplace-Backed Plugin Packaging

- Added `.agents/plugins/marketplace.json` so Codex can discover `jinhua` as a real plugin source instead of only a copied Skill.
- Expanded `.codex-plugin/plugin.json` into a real plugin manifest with `skills` and `hooks`.
- Added `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for Claude Code style plugin packaging.
- Added `skills/jinhua/SKILL.md` as a thin plugin entry that delegates to the canonical root `SKILL.md`.

## 2026-06-25 Thin Plugin Hook Layer

- Added a minimal `.codex-plugin/plugin.json` and thin `hooks/` layer for Codex and Claude Code hook packaging.
- Kept the Skill itself focused on `SKILL.md` + `hook-user-prompt-submit`; the new hook layer just routes to the existing adapter.
- Updated the project map and hook docs to make the packaging boundary explicit.

## 2026-06-25 Codex / Claude Code Hook Adapter

- Added `hook-user-prompt-submit`, a read-only `UserPromptSubmit` adapter for Codex / Claude Code style hooks.
- The adapter reads hook JSON from stdin, extracts common prompt fields, and emits `hookSpecificOutput.additionalContext` only when `wake-check` matches.
- Clarified that Codex compatibility still primarily comes from `SKILL.md` metadata; hook execution is optional and host-config dependent.

## 2026-06-25 Hook-Aware Wake Check

- Added read-only `wake-check` for cheap hook pre-routing before loading the full Skill.
- Added `cycle --json --fail-on-pending-gate` so hook runners can treat pending user gates as exit code `2`.
- Documented the hook contract: use `wake-check` for coarse routing, then keep precise methodology judgment inside `jinhua`.

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
