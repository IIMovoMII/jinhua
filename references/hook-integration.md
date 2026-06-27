# Hook And Platform Integration

`jinhua` has two compatible entry paths:

1. Standard Skill selection through `SKILL.md` metadata.
2. Codex plugin command hooks through `hooks/codex-hooks.json`.

The CLI does not run as a daemon. Hooks only route attention and prevent duplicate same-turn work; they do not judge transferability, write signals, create proposals, or edit Skills.

## Primary Codex Trigger Layer

The primary hook path is three gates:

```text
UserPromptSubmit -> local correction classifier
PostToolUse      -> invocation guard record
Stop             -> output-state tail parser
```

`hooks/codex-hooks.json` calls these commands:

```bash
python <jinhua-dir>/hooks/codex_user_prompt_submit.py
python <jinhua-dir>/hooks/codex_post_tool_use.py
python <jinhua-dir>/hooks/codex_stop.py
```

The wrappers delegate to:

```bash
python <jinhua-dir>/scripts/jinhua.py codex-user-prompt-submit
python <jinhua-dir>/scripts/jinhua.py codex-post-tool-use
python <jinhua-dir>/scripts/jinhua.py codex-stop
```

## Gate 1: Input Classification

`codex-user-prompt-submit` reads hook JSON from stdin, extracts the latest prompt, and classifies it as:

- `none`
- `possible_user_correction`
- `strong_user_correction`

On a match, it emits only a short `hookSpecificOutput.additionalContext`. It never runs `cycle`, writes `signals.jsonl`, creates proposals, stores user text, or edits Skills.

Manual check:

```bash
python <jinhua-dir>/scripts/jinhua.py classify-input --text "you misunderstood, that's not the scope" --json
```

## Gate 2: Invocation Guard

`codex-post-tool-use` watches tool payloads for jinhua CLI entries such as `cycle`, `log-signal`, `propose`, `global-cycle`, or `global-propose`.

It records only lightweight runtime guard state under:

```text
.jinhua/runtime/invocation-guard.json
```

This is not an experience ledger. It is only a duplicate guard for the current session/turn/reason.

Guard decisions:

- `allow`
- `already_handled`
- `merge_context_only`
- `skip_duplicate`
- `block_loop`

## Gate 3: Output-State Tail

`codex-stop` parses a tiny final-state tail:

```text
output_state: ok
visibility: silent
```

Allowed `output_state` values:

- `ok`
- `user_correction_handled`
- `self_issue_detected`
- `uncertain`
- `jinhua_candidate`

Allowed `visibility` values:

- `silent`
- `notify`
- `ask_confirmation`

If `output_state = jinhua_candidate`, the Stop gate checks the invocation guard first. If jinhua already ran in the same turn, it skips duplicate triggering. If not, it may add a short reminder to consider the existing `cycle` / `log-signal` / `propose` flow. It must not bypass the user gate.

The Stop gate also counts per conversation. Every 8 user turns by default, it sends one silent fallback reminder to scan this turn and prior conversation for reusable lessons; no candidate means no jinhua work.

Codex hooks may not perfectly hide already-generated text in every host. This implementation parses and strips where the host supports it; absolute hiding requires an outer wrapper.

## Legacy Compatibility

These commands remain for older installations but are not the primary trigger path:

```bash
python <jinhua-dir>/scripts/jinhua.py wake-check --text "<latest user message>" --json
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> hook-user-prompt-submit
```

`hooks/claude-codex-hooks.json` is deprecated and points to `hooks/codex-hooks.json`.

## Safety Rules

- Do not auto-apply Skill edits.
- Do not bypass the placement-aware user gate: `project_rule`, `skill_patch`, `personal_global_skill`, `No`, or `Revision` displayed in the user's language.
- Do not save original user text.
- Do not copy raw project paths into global records.
- Do not make hooks responsible for methodology judgment.
- Do not run full `cycle` on every message.
- Do not treat hook output as final proof of transferability.
