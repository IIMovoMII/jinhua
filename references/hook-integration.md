# Hook And Platform Integration

`cycle` is the automatic checkpoint.

The CLI does not run as a daemon. Platforms may call it, but they must not change the safety model.

## Codex

Codex should call:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

Use this at the start of a triggered Skill invocation, after `log-signal`, after proposal apply/reject, and before finishing substantial methodology work.

Codex does not need user setup after the Skill is installed. `cycle` initializes local and global runtime state.

## Claude Code

Optional hooks may call:

- `cycle`
- `cycle --json`
- `validate`

Hooks may call `log-signal` only when the platform can provide sanitized fields. Hooks must not store original user text.

## Safety Rules

- Do not auto-apply Skill edits.
- Do not bypass the placement-aware user gate: Project Rule / Skill Patch / Personal Global Skill / No / Revision.
- Do not save original user text.
- Do not copy raw project paths into global records.
- Do not make hooks responsible for methodology judgment.
- Do not treat CLI output as final proof of transferability.
