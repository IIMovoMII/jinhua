# Maintenance Rules

Jinhua is a compact Skill, a single-file standard-library CLI, and thin host trigger adapters. Keep that shape unless measured runtime evidence proves a split is necessary.

For navigation, read `AGENTS.md`, then `PROJECT_RULES.md` and `PROJECT_INDEX.md` when ownership or structure matters.

## File Ownership

- `SKILL.md`: active runtime control plane; keep it short.
- `SKILL.zh-CN.md`: Chinese explanation, not the active control plane.
- `scripts/jinhua.py`: only CLI and deterministic ledger implementation.
- `hooks/hooks.json` and `hooks/codex_*.py`: shared Codex and Claude Code trigger layer using the official default path; do not add a duplicate manifest override.
- `references/cli-usage.md`: command contract.
- `references/data-policy.md`: recordability and privacy.
- `references/runtime-schema.md`: current schemas and migration.
- `references/hook-integration.md`: trigger and host protocols.
- `adapters/`: host packaging only.

Do not add a reference when an existing topic file can hold the content.

## CLI Boundary

The CLI may:

- initialize and migrate runtime;
- record validated signals;
- update exact local and global clusters;
- recommend placement owners and project rule files;
- create complete user-gated proposals;
- record revision, rejection, and verified adoption;
- validate runtime data.

The CLI must not:

- make final semantic transferability judgments;
- fuzzy-merge methods automatically;
- write an approved Skill or rule file;
- store raw user text;
- run web searches;
- run as a daemon.

All accepted signals remain stored. Reject weak or unsafe content before writing.

## Trigger Boundary

Hooks may classify correction text, read ready/pending state, count turns, issue a fixed eight-turn review, and write invocation-guard runtime state.

Hooks must not migrate core schemas, log signals, create proposals, record gate outcomes, edit files, or call full `cycle` on every prompt.

## Plugin Validator Compatibility

Keep `.codex-plugin/plugin.json` free of a `hooks` override and use the official `hooks/hooks.json` default. Jinhua requires Codex 0.144.6 or newer for this path. Codex 0.139 does not discover the default plugin Hook file and is not supported by the 2.0 trigger package.

Validate the shared hook contract through `scripts/test_trigger_layer.py`, plugin validation, cachebuster/reinstall, and fresh Codex and Claude Code tasks.

## Localization

- Chinese public docs are the default user-facing source.
- English mirrors are maintained for public behavior.
- Do not translate CLI commands, option names, JSON keys, operator ids, or placement ids.
- Explain stable identifiers in `references/zh-CN/glossary.md`.
- User-facing gates and explanations follow the user's current language.

## Architecture

Do not add a daemon, external database, vector store, graph database, dashboard, multi-agent workflow, or second experience ledger without measured evidence and an explicit design decision.

## Packaging And Privacy

Never package or commit:

- `.jinhua/`;
- `global-data/`;
- `.claude/`;
- `.archive/`;
- `__pycache__/` or Python bytecode;
- local permission files or generated archives.

## Required Verification

```bash
python scripts/test_core_loop.py
python scripts/test_trigger_layer.py
python scripts/test_adapters.py
python -m py_compile scripts/jinhua.py hooks/codex_user_prompt_submit.py hooks/codex_post_tool_use.py
python scripts/jinhua.py --project-root <project-root> validate
git diff --check
```

Schema changes must update `references/runtime-schema.md` and its Chinese mirror. Trigger changes must update Hook tests and both Hook references.

Every published Skill/plugin change must complete: verification, plugin-creator cachebuster/reinstall, local enabled check, commit, and push.
