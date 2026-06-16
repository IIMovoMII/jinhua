# Maintenance Rules

This project is a small Skill + single-file CLI. Keep it that way unless real usage proves otherwise.

## File Rules

- `SKILL.md` is the control plane, not a knowledge base.
- `SKILL.zh-CN.md` is a Chinese explanation, not the active control plane.
- `README.md` is the user-facing usage guide.
- `README.md` is the default Chinese user-facing usage guide.
- `README.en.md` is the English mirror.
- `PROJECT_MAP.md` is the navigation map.
- `references/` must stay under 8 files.
- Do not add a new reference file if an existing one can hold the content.

## Localization Rules

- Chinese public docs are the default source for user-facing pages.
- When user-facing behavior changes, check both Chinese defaults and English mirrors.
- Do not translate CLI commands, option names, JSON field names, or operator ids.
- Explain those English identifiers in `references/zh-CN/glossary.md`.
- User-facing Skill dialogue should follow the user's current language.
- Durable data, schema fields, command names, and generated Skill files may remain English unless the user asks otherwise.

## CLI Rules

Keep `scripts/jinhua.py` single-file while the workflow remains understandable.

The CLI may:

- initialize runtime state
- record structured signals
- update local clusters
- import global promotion records
- emit proposal skeletons
- record user-gated outcomes
- suggest global merge candidates without mutation
- compact and validate data

The CLI must not:

- judge final transferability
- auto-apply Skill edits without the user gate
- store raw user text
- run web searches
- run as a daemon
- make machine learning a required core dependency

## Architecture Rules

Do not add:

- daemon
- external database
- vector store
- graph database
- dashboard
- ML core loop
- multi-agent workflow

Only reconsider architecture when a measured bottleneck appears in real runtime data.

## Packaging Rules

Do not package:

- `.jinhua/`
- `global-data/`
- `.claude/`
- `skill.zip`
- `__pycache__/`
- local permission files

Schema changes must update `references/operator-json-schema.md` and pass `validate`.
