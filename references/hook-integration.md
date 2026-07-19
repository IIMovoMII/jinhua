# Hook And Platform Integration

Jinhua has two compatible entry paths:

1. Skill selection through `SKILL.md`.
2. Host command hooks that route attention to the same Skill and CLI.

The CLI is not a daemon. Hooks classify, count, remind, and deduplicate only. They do not own methodology judgment or the experience ledger.

## Codex Trigger Layer

```text
UserPromptSubmit -> local correction classification + ready attention + turn count
PostToolUse      -> invocation guard record
Stop             -> fixed eight-turn periodic review + loop prevention
```

`hooks/codex-hooks.json` invokes:

```bash
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_user_prompt_submit.py"
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_post_tool_use.py"
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_stop.py"
```

Each wrapper forwards stdin to the matching command in `scripts/jinhua.py`.

## Project Root Resolution

The wrappers resolve the target project in this order:

1. documented top-level project path in the Hook payload;
2. explicitly supported host-wrapper paths such as `event.context.cwd`;
3. supported project-directory environment variables;
4. Hook process working directory.

UTF-8 BOM input is accepted. If the only fallback resolves to the installed Jinhua plugin directory, runtime writes are disabled instead of creating `.jinhua` inside the plugin.

## Authoritative Hook Evidence

Execution facts and Hook identity come only from documented, explicitly supported control fields. Codex and Claude Code expose fields such as `session_id`, `turn_id` or `prompt_id`, `cwd`, `stop_hook_active`, `tool_name`, and `tool_input.command` as control data.

Jinhua never infers execution, project identity, session identity, turn identity, or Stop recursion state from user prompts, documentation, tool responses, error logs, or arbitrary nested payload text. A command being mentioned is not evidence that it ran. Guard writes require both authoritative command evidence and authoritative session/turn identity. Unknown or incomplete payload shapes leave invocation-guard state unchanged until an explicit mapping and regression test are added.

## Host Trust Boundary

Hook discovery and execution are separate host states. After an update, Codex may mark a Hook as `modified` or `untrusted`. The host must trust the current Hook content before it executes.

This trust decision belongs to the host. It is not stored in Jinhua's signal, cluster, proposal, or invocation-guard data.

## Gate 1: UserPromptSubmit

`codex-user-prompt-submit` extracts the latest prompt and returns:

- `none`;
- `possible_user_correction`;
- `strong_user_correction`.

The classifier is fully local. On a correction match, it emits one short `hookSpecificOutput.additionalContext` asking the agent to align with the user's correction before considering Jinhua's existing write gate.

The same Hook:

- counts unique user turns per hashed session;
- marks a periodic check due every 8 turns;
- reads existing local/global ready clusters and pending user gates;
- may add one short ready-attention reminder.

It does not run `cycle`, migrate core data, save the prompt, append signals, create proposals, or edit files.

Manual classifier check:

```bash
python <jinhua-dir>/scripts/jinhua.py classify-input \
  --text "you misunderstood; change only the trigger layer" \
  --json
```

## Gate 2: PostToolUse Invocation Guard

`codex-post-tool-use` detects Jinhua CLI entries such as `cycle`, `log-signal`, `propose`, `global-cycle`, and `global-propose` only from supported shell-tool command input. It ignores command names found in prompts, files, search patterns, tool output, and non-shell tool arguments.

It records lightweight runtime state under:

```text
<project-root>/.jinhua/runtime/invocation-guard.json
```

The guard stores hashed session/turn ids, a reason digest, entry name, timestamp, recent events, turn counts, and periodic tickets. It is not an experience ledger.

Guard decisions:

- `allow`: first valid entry;
- `already_handled`: Stop sees that the turn already entered Jinhua;
- `skip_duplicate`: the same reason is repeated in the same turn;
- `block_loop`: repeated entries indicate a loop.

The first direct agent call remains allowed. Later Jinhua subcommands in the same turn belong to the same guarded workflow and do not create extra guard events; the guard only prevents duplicate trigger paths.

## Gate 3: Stop Periodic Review

`codex-stop` has two responsibilities:

1. if `stop_hook_active` is true, pass through immediately;
2. when the session's fixed eight-turn ticket is due, request one short continuation that scans the current turn and prior conversation for reusable workflow lessons.

Before requesting the continuation, Stop checks the invocation guard. If Jinhua already ran in the same turn, it consumes the periodic ticket and passes through.

The Stop Hook:

- does not parse an output-state tail;
- does not require the model to emit hidden status fields;
- does not create a candidate state;
- does not run `cycle` itself;
- issues at most one ticket per due turn.

The interval is fixed at 8 and cannot be overridden by environment variables.

## Ready Attention

Ready attention is the bridge from a mature cluster to model attention:

1. a non-Hook core command has already produced a `ready` cluster or pending gate;
2. the next `UserPromptSubmit` reads that state without migration;
3. one short context reminder asks the agent to run `cycle`;
4. the agent must create one complete proposal, surface one pending gate, or state a concrete skip reason.

The Hook itself never changes `ready` to `proposed`.

## Claude Code

`hooks/hooks.json` is the Claude Code plugin adapter. It uses the same three wrapper scripts and `${CLAUDE_PLUGIN_ROOT}`; no second trigger implementation or ledger exists.

Payload compatibility is checked through local protocol simulations in `scripts/test_adapters.py` and `scripts/test_trigger_layer.py`.

## Other Hosts

- OpenClaw: `adapters/openclaw/` packages a Skill/plugin wrapper.
- Hermes: `adapters/hermes/` provides a Skill wrapper.
- TRAE: `adapters/trae/` provides a Skill wrapper.
- WorkBuddy: `adapters/workbuddy/` provides a Skill wrapper.

These adapters expose the canonical Jinhua Skill/CLI. Automatic Hook support depends on the host; adapters must not modify the core plugin to emulate unsupported lifecycle events.

## Safety Rules

- Do not auto-log from Hooks.
- Do not run full `cycle` on every prompt.
- Do not store raw prompt text in runtime state.
- Do not bypass `signals -> clusters -> proposals -> user gate`.
- Do not auto-edit a Skill or project rule.
- Do not treat correction classification as proof that a transferable lesson exists.
