# Hook And Platform Integration

`cycle` is the automatic checkpoint.

The CLI does not run as a daemon. Platforms may call it, but they must not change the safety model.

For cheap pre-selection, platforms may call:

```bash
python <jinhua-dir>/scripts/jinhua.py wake-check --text "<latest user message>" --json
```

`wake-check` is read-only. It does not run `cycle`, log signals, store user text, or make methodology judgments. It only detects coarse meta-workflow cues such as missed Skill activation, workflow correction, verification-standard correction, or requests to preserve a method. If it returns `should_route: true`, route or prioritize `jinhua`, then let the Skill run `cycle` and apply the normal trigger/action tests.

## Codex

Codex should call:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

Use this at the start of a triggered Skill invocation, after `log-signal`, after proposal apply/reject, and before finishing substantial methodology work.

Hook runners that need a hard pending-gate signal may call:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle --json --fail-on-pending-gate
```

Exit code `2` means at least one local or global user gate is pending and must be surfaced before continuing the jinhua branch.

Codex does not need user setup after the Skill is installed. `cycle` initializes local and global runtime state.

## Claude Code

Optional hooks may call:

- `wake-check --json`
- `cycle`
- `cycle --json`
- `cycle --json --fail-on-pending-gate`
- `validate`

Hooks may call `log-signal` only when the platform can provide sanitized fields. Hooks must not store original user text.

## Safety Rules

- Do not auto-apply Skill edits.
- Do not bypass the placement-aware user gate: Project Rule / Skill Patch / Personal Global Skill / No / Revision.
- Do not save original user text.
- Do not copy raw project paths into global records.
- Do not make hooks responsible for methodology judgment.
- Do not run full `cycle` on every message; use `wake-check` for cheap routing and keep precise judgment inside the Skill.
- Do not treat CLI output as final proof of transferability.
