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

`hooks/codex-hooks.json` calls these commands. Codex resolves `${CLAUDE_PLUGIN_ROOT}` before invoking the platform shell; the Windows override intentionally uses the same form so it does not depend on `cmd.exe` or PowerShell variable syntax:

```bash
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_user_prompt_submit.py"
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_post_tool_use.py"
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_stop.py"
```

The wrappers delegate to:

```bash
python <jinhua-dir>/scripts/jinhua.py codex-user-prompt-submit
python <jinhua-dir>/scripts/jinhua.py codex-post-tool-use
python <jinhua-dir>/scripts/jinhua.py codex-stop
```

The packaged wrappers receive the hook payload on stdin and resolve the project root in this order: an explicit project path in the payload, common nested payload fields, supported project-directory environment variables, and finally the hook process working directory. A process directory that resolves to the installed plugin itself is treated as unsafe, so the hook returns without creating runtime state rather than writing `.jinhua` into the plugin.

## Host Trust Boundary

Hook discovery and hook execution are separate host states. After a plugin update, Codex may list a Jinhua hook as `modified` or `untrusted`; that hook is discovered but will not run until the host trusts the current hook content. The trust decision belongs to Codex and is not part of the Jinhua experience ledger. A trusted hook then runs the same read-only trigger layer described below.

## Gate 1: Input Classification

`codex-user-prompt-submit` reads hook JSON from stdin, extracts the latest prompt, and classifies it as:

- `none`
- `possible_user_correction`
- `strong_user_correction`

On a match, it emits only a short `hookSpecificOutput.additionalContext`. Its stdout uses only fields accepted by the Codex hook schema. It never runs `cycle`, writes `signals.jsonl`, creates proposals, stores user text, or edits Skills.

It also performs a read-only ready-attention check against existing runtime JSON/JSONL. If ready clusters or pending user gates exist, it injects a short reminder to run `cycle` and either create one proposal, surface one gate, or state a concrete skip reason. This keeps `ready -> pending_user_gate` closed without a background daemon or extra model call.

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

If `output_state = jinhua_candidate`, the Stop gate checks the invocation guard first. If jinhua already ran in the same turn, it skips duplicate triggering. If not, it returns one short `decision: block` reason so Codex can continue the current turn and the agent can consider the existing `cycle` / `log-signal` / `propose` flow. When `stop_hook_active` is true, it always returns `continue: true`.

The Stop gate also counts per conversation. Every 8 user turns by default, it returns one short continuation reason asking the agent to scan this turn and prior conversation for reusable lessons. This is the only periodic extra model continuation; normal hook runs remain local and do not call jinhua core commands.

Codex Stop hooks cannot rewrite the already-generated assistant message through the hook output schema. Jinhua parses the tail for trigger decisions; it does not claim to strip host output. Absolute hiding requires an outer wrapper.

## Legacy Compatibility

These commands remain for older installations but are not the primary trigger path:

```bash
python <jinhua-dir>/scripts/jinhua.py wake-check --text "<latest user message>" --json
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> hook-user-prompt-submit
```

`hooks/claude-codex-hooks.json` is deprecated and points to `hooks/codex-hooks.json`.

## Host Adapters

Host-specific adapters live outside the core plugin:

- Claude Code: `hooks/hooks.json` uses the native plugin hook location and `${CLAUDE_PLUGIN_ROOT}` to call the same three wrappers.
- OpenClaw: `adapters/openclaw/openclaw.plugin.json` packages the Skill adapter under `adapters/openclaw/skills/jinhua/`.
- Hermes: `adapters/hermes/skills/jinhua/SKILL.md` is a Skill-only adapter.
- TRAE: `adapters/trae/skills/jinhua/SKILL.md` is a Skill-only adapter.
- WorkBuddy: `adapters/workbuddy/skills/jinhua/SKILL.md` is a Skill-only adapter.

Adapters must not create another ledger or bypass `signals -> clusters -> proposals -> user gate`.

## Safety Rules

- Do not auto-apply Skill edits.
- Do not bypass the placement-aware user gate: `project_rule`, `skill_patch`, `personal_global_skill`, `No`, or `Revision` displayed in the user's language.
- Do not save original user text.
- Do not copy raw project paths into global records.
- Do not make hooks responsible for methodology judgment.
- Do not run full `cycle` on every message.
- Do not treat hook output as final proof of transferability.
