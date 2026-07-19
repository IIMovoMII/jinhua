# PROJECT_MAP

Daily entry: read `AGENTS.md`; read `PROJECT_RULES.md` and `PROJECT_INDEX.md` when structure or ownership matters.

## Product Shape

Jinhua is a compact Skill + standard-library CLI + thin host trigger adapters.

- **Trigger layer**: local correction classification, ready attention, per-session turn counting, same-turn deduplication, and a fixed eight-turn review.
- **Skill**: semantic write/skip judgment, abstraction, placement, proposal content, and localized user dialogue.
- **CLI**: deterministic storage, exact clustering, cross-project import, migration, complete proposal records, gate outcomes, and validation.
- **Agent**: edits and verifies an accepted target with host-native tools.
- **User**: approves placement, rejects, or requests revision.

The core remains:

```text
signals -> clusters -> proposals -> user gate
```

## Active Tree

```text
jinhua/
|-- SKILL.md
|-- SKILL.zh-CN.md
|-- README.md
|-- README.en.md
|-- AGENTS.md
|-- PROJECT_RULES.md
|-- PROJECT_INDEX.md
|-- PROJECT_MAP.md
|-- PROJECT_MAP.zh-CN.md
|-- CHANGELOG.md
|-- CHANGELOG.zh-CN.md
|-- .codex-plugin/
|   `-- plugin.json
|-- .claude-plugin/
|   |-- plugin.json
|   `-- marketplace.json
|-- .agents/plugins/
|   `-- marketplace.json
|-- hooks/
|   |-- hooks.json
|   |-- codex_user_prompt_submit.py
|   |-- codex_post_tool_use.py
|   `-- codex_stop.py
|-- skills/jinhua/
|   `-- SKILL.md
|-- adapters/
|   |-- README.md
|   |-- openclaw/
|   |-- hermes/
|   |-- trae/
|   `-- workbuddy/
|-- scripts/
|   |-- jinhua.py
|   |-- test_core_loop.py
|   |-- test_trigger_layer.py
|   `-- test_adapters.py
|-- references/
|   |-- cli-usage.md
|   |-- data-policy.md
|   |-- runtime-schema.md
|   |-- hook-integration.md
|   |-- maintenance.md
|   `-- zh-CN/
|       |-- cli-usage.md
|       |-- data-policy.md
|       |-- runtime-schema.md
|       |-- hook-integration.md
|       |-- maintenance.md
|       `-- glossary.md
|-- docs/
|   `-- jinhua-logic.html
`-- .github/
    |-- ISSUE_TEMPLATE/
    `-- PULL_REQUEST_TEMPLATE.md
```

There is no repository seed-data directory in 2.0. Runtime data is created only under the target project or ignored personal global runtime.

## Current CLI Surface

`init`, `cycle`, `global-cycle`, `classify-input`, `codex-user-prompt-submit`, `codex-post-tool-use`, `codex-stop`, `guard`, `log-signal`, `list-clusters`, `propose`, `apply-proposal`, `reject-proposal`, `global-propose`, `global-apply`, `global-reject`, `status`, `global-status`, and `validate`.

Apply commands are ledger-only. Proposal commands require a concrete target, complete Markdown patch, and concrete risk.

## Runtime Boundaries

Project-local:

```text
<project-root>/.jinhua/data/
<project-root>/.jinhua/runtime/invocation-guard.json
```

Personal global:

```text
<jinhua-dir>/global-data/
```

Both directories are ignored and must never be packaged or committed.

## Do Not Regress

- Do not auto-log from Hooks.
- Do not hide a ready cluster indefinitely; ready attention must bring it back to the agent.
- Do not interrupt for weak single signals.
- Do not bypass the placement-aware user gate.
- Do not record adoption before native editing and verification succeed.
- Do not count same-project repetition as cross-project repetition.
- Do not ask the user to find a target Skill or project rule file.
- Do not add fuzzy merge, compaction, operator promotion, daemon, database, vector store, dashboard, or a second ledger.
- Keep host-specific packaging under `adapters/`.
