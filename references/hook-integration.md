# Hook And Platform Integration

`jinhua` has two compatible wake-up paths:

1. Standard Skill selection through `SKILL.md` metadata.
2. Optional `UserPromptSubmit` hook pre-routing when the host agent supports hooks.

The CLI does not run as a daemon. Hooks may route attention, but they must not change the safety model.

A Skill repo by itself cannot force hook trust prompts. For other users, the hook definition must live in a Codex-scanned hook layer such as `~/.codex/hooks.json`, `~/.codex/config.toml`, `<repo>/.codex/hooks.json`, `<repo>/.codex/config.toml`, or a plugin's `hooks/hooks.json`.

This repo now includes the thin plugin packaging for that route:

- `.agents/plugins/marketplace.json`
- `.codex-plugin/plugin.json`
- `.claude-plugin/plugin.json`

## Cheap Text Check

For manual pre-selection:

```bash
python <jinhua-dir>/scripts/jinhua.py wake-check --text "<latest user message>" --json
```

`wake-check` is read-only. It does not run `cycle`, log signals, store user text, or make methodology judgments. It only detects coarse meta-workflow cues such as missed Skill activation, workflow correction, verification-standard correction, tool-choice correction, or requests to preserve a method.

## UserPromptSubmit Adapter

For Codex / Claude Code style hooks:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> hook-user-prompt-submit
```

The adapter reads the hook JSON payload from stdin and extracts common prompt fields:

- `prompt`
- `userPrompt`
- `message`
- `input.prompt`

If `--project-root` is not supplied and the hook payload contains `cwd`, the adapter uses `cwd` in the follow-up `cycle` hint.

If the prompt matches the same coarse wake check, the adapter returns:

```json
{
  "continue": true,
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "..."
  }
}
```

If it does not match, it returns only:

```json
{"continue": true}
```

This keeps hook cost low: every prompt can run a small regex check, but the full Skill only loads when the host agent sees the additional context and routes to `jinhua`.

## Codex

Codex Skills are discovered through `SKILL.md` with YAML frontmatter `name` and `description`. This is the primary compatibility path.

If the Codex environment supports and runs hooks, configure `UserPromptSubmit` to call `hook-user-prompt-submit`. Some Codex environments may not execute local hooks, or may require separate trusted-project configuration; in that case, the Skill still works through normal Skill selection.

Minimal `hooks.json` shape:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"<jinhua-dir>/scripts/jinhua.py\" hook-user-prompt-submit",
            "timeout": 5,
            "statusMessage": "Checking jinhua wake-up"
          }
        ]
      }
    ]
  }
}
```

Do not rely on a matcher for `UserPromptSubmit`; Codex currently ignores matchers for that event. Let the adapter do the cheap filtering.

When `jinhua` is actually selected, it should run:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

Hook runners that need a hard pending-gate signal may call:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle --json --fail-on-pending-gate
```

Exit code `2` means at least one local or global user gate is pending and must be surfaced before continuing the jinhua branch.

## Claude Code

Claude Code can use the same `UserPromptSubmit` adapter. The hook command should receive the platform hook JSON on stdin and return the adapter JSON on stdout.

Minimal `settings.json` shape:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"<jinhua-dir>/scripts/jinhua.py\" hook-user-prompt-submit",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Use `hook-user-prompt-submit` for every prompt if needed; do not run full `cycle` on every prompt. Let the adapter add context only when a coarse methodology cue is present, then let the selected Skill run `cycle`.

## Safety Rules

- Do not auto-apply Skill edits.
- Do not bypass the placement-aware user gate: Project Rule / Skill Patch / Personal Global Skill / No / Revision.
- Do not save original user text.
- Do not copy raw project paths into global records.
- Do not make hooks responsible for methodology judgment.
- Do not run full `cycle` on every message.
- Do not treat hook output as final proof of transferability.
