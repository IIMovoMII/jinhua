# PROJECT_MAP

## Product Shape

`jinhua` is a compact Skill + CLI that turns repeated methodology signals into user-gated Skill improvements.

Responsibility split:

- **Skill**: decides whether a signal is reusable, transferable, risky, duplicated, or worth proposing.
- **CLI**: records signals, clusters evidence, imports global promotion evidence, emits placement-aware skeletons, recommends project-rule files, records gate outcomes, suggests merge candidates, compacts, and validates.
- **User**: gates proposals with Project Rule / Skill Patch / Personal Global Skill / No / Revision.

## Main Files

```text
jinhua/
|-- SKILL.md
|-- README.md
|-- README.en.md
|-- CONTRIBUTING.md
|-- CONTRIBUTING.en.md
|-- SECURITY.md
|-- SECURITY.en.md
|-- CODE_OF_CONDUCT.md
|-- CODE_OF_CONDUCT.en.md
|-- PROJECT_MAP.md
|-- CHANGELOG.md
|-- .github/
|   |-- ISSUE_TEMPLATE/
|   |   |-- bug_report.yml
|   |   |-- feature_request.yml
|   |   `-- config.yml
|   `-- PULL_REQUEST_TEMPLATE.md
|-- scripts/
|   `-- jinhua.py
|-- references/
|   |-- cli-usage.md
|   |-- operator-json-schema.md
|   |-- data-policy.md
|   |-- hook-integration.md
|   `-- maintenance.md
|-- docs/
|   `-- jinhua-logic.html
`-- data/
    |-- signals.jsonl
    |-- cluster-state.json
    |-- proposals.jsonl
    |-- adopted-edits.jsonl
    |-- rejected-proposals.jsonl
    |-- crystallized-operators.jsonl
    `-- evolution-state.json
```

Runtime-only global promotion directory:

```text
jinhua/global-data/
|-- global-signals.jsonl
|-- global-clusters.json
|-- global-proposals.jsonl
|-- adopted-global-edits.jsonl
|-- rejected-global-proposals.jsonl
|-- project-index.json
`-- global-state.json
```

## Current CLI Surface

- `init`
- `cycle`
- `log-signal`
- `list-clusters`
- `propose`
- `apply-proposal`
- `reject-proposal`
- `global-cycle`
- `global-status`
- `global-propose`
- `global-merge-suggestions`
- `global-apply`
- `global-reject`
- `compact`
- `status`
- `validate`

The public CLI surface is intentionally focused on the closed loop above.

## Data Rules

- Project-local raw evidence stays under `.jinhua/data/`.
- Global promotion stores compressed methodology evidence only.
- `project-index.json` stores hashed project identities, not raw paths.
- `global-data/` and `.jinhua/` are runtime state and must not be packaged.
- Use `--project-id` or `JINHUA_PROJECT_ID` when one workspace contains unrelated projects or conversations.

## Do Not Regress

- Do not ask the user to manage daily signal bookkeeping.
- Do not interrupt the user for weak single signals.
- Do not auto-apply Skill edits without a user gate.
- Do not count duplicate same-project signals as cross-project repetition.
- Do not ask the user to find the target Skill when `skill_patch` is the recommended placement.
- Do not auto-create project rule files when `project_rule` is the recommended placement.
- Do not add daemon, database, vector store, dashboard, or ML core loop.
- Do not add broad observation commands as first-class workflow.
