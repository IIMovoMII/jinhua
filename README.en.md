# Jinhua

Languages: English | [简体中文](README.md)

Jinhua is a local methodology-learning tool for coding agents. It turns reusable workflow corrections, verified failures, and successful methods into project rules or Skill improvements that the user explicitly approves.

It is not chat history, personal memory, or an automatic editor. Jinhua stores sanitized methodology evidence only. Hooks never auto-log experience, and every rule change remains behind the user gate.

Product shape:

- Codex: plugin + three local trigger gates + Skill + CLI.
- Claude Code: native hook adapter using the same Skill and CLI.
- OpenClaw, Hermes, TRAE, and WorkBuddy: thin host adapters with no change to the core loop.

The Codex plugin trigger layer requires Codex CLI/Desktop runtime `0.144.6` or newer; older versions may not discover the default `hooks/hooks.json`.

Chinese visual guide: [docs/jinhua-logic.html](docs/jinhua-logic.html)

## Complete Loop

```text
Trigger layer notices a turn worth checking
        ↓
cycle: read local/global state and surface pending gates first
        ↓
Write gate: can the lesson become reusable trigger + action?
        ├─ No  → skip without writing
        └─ Yes → log-signal
                    ↓
              local clustering
                    ↓
        not ready → keep accumulating quietly
        ready     → propose / global-propose
                    ↓
              placement-aware user gate
        ├─ project_rule
        ├─ skill_patch
        ├─ personal_global_skill
        ├─ Revision → rewrite and ask again
        └─ No → cooldown until 5 new same-cluster signals
                    ↓
On acceptance, the agent edits and verifies with host-native tools
                    ↓
apply-proposal / global-apply records the completed adoption only
                    ↓
cycle → validate
```

The core data flow remains:

```text
signals -> clusters -> proposals -> user gate
```

The trigger layer cannot bypass this flow or the user gate.

## Three Trigger Gates

### Gate 1: Local Input Classification

`UserPromptSubmit` uses local Python rules before the main model handles the prompt. It classifies likely workflow, verification, tool/Skill, or missed-procedure corrections as:

```text
none
possible_user_correction
strong_user_correction
```

On a match it adds one short internal hint to the normal model call. It also reads existing ready clusters and pending gates and counts unique user turns per session. It never runs `cycle`, migrates core data, writes signals/proposals, or stores the user's original prompt.

### Gate 2: Direct Agent Call And Invocation Guard

The agent may enter Jinhua immediately when the user explicitly asks to crystallize a method or when a transferable workflow lesson is clear.

`PostToolUse` records whether Jinhua already ran in the current turn so input attention, direct calls, and periodic checks cannot duplicate work. Guard results are:

```text
allow
already_handled
skip_duplicate
block_loop
```

### Gate 3: Fixed Eight-Turn Review

`Stop` requests one short review every 8 unique user turns in each session. The review covers the current turn and prior conversation. Ordinary turns run local code only; one extra model continuation occurs only when the interval is due.

Stop no longer requires or parses an output-state tail. It passes through when `stop_hook_active` is set or when Jinhua already ran in that turn, preventing loops and duplicate calls.

All three gates only classify, count, remind, and deduplicate. They never write signals, create proposals, or edit rules.

See [references/hook-integration.md](references/hook-integration.md) for host protocol details.

## Recordability

A lesson must contain both:

- `trigger`: the future condition where it applies.
- `action`: the reusable action to take.

At least one must also be true:

- The user corrected workflow, reasoning direction, verification, Skill/tool choice, or a missed procedure.
- The same reusable method repeated in the current project.
- A repaired failure exposed a transferable cause.
- A successful path exposed a reusable method.
- The user explicitly asked to preserve, crystallize, write, or apply the method elsewhere.

Skip one-off bugs, ordinary output preferences, private facts, raw user text, credentials, local paths, temporary commands, local API details, and conversation-only lessons.

The agent owns semantic judgment and abstraction. The CLI only validates, stores, counts, clusters, migrates, and records gate outcomes.

## Strength And Readiness

`strength` is fixed:

- `1`: ordinary self-observation.
- `2`: clear user correction or repeated pattern.
- `3`: high-cost failure, repeated rework, or explicit crystallization request.

A local cluster becomes ready at:

```text
signal_count >= 3
or
strength_sum >= 5
```

`log-signal --immediate` is the only immediate channel and is reserved for an explicit crystallization request or urgent reusable high-cost failure.

Ready means evidence is sufficient for a proposal, not that a rule has changed. The next ready-attention check brings it back to the agent, which must create a complete proposal or state a concrete skip reason.

## Cross-Project Promotion

`cycle` imports compressed active local signals into the personal global runtime. Global data stores hashed project identity and sanitized method evidence, never raw project paths.

Exact grouping prefers a normalized `operator + action` `method_fingerprint`. The CLI does not perform fuzzy similarity merging; the agent is responsible for compressing semantically identical methods into the same action.

Ordinary global readiness:

```text
3 projects + 5 evidence records + strength 7
```

Fast path:

```text
2 projects + strength 6
+ at least 2 high-strength or user-correction records
```

## Placement And User Gate

Choose by strong evidence first and use the lightest fallback:

1. `personal_global_skill`: explicit all-project behavior, a new standalone Skill, an independent workflow, or mature global evidence.
2. `skill_patch`: the lesson clearly belongs to an existing Skill. The proposal must name the concrete Skill and path.
3. `project_rule`: current-project need without a clear Skill owner or global scope. The proposal must recommend a concrete project rule file.

The normal distribution should be: skip most, project rules often, Skill patches less often, personal global Skills least often.

In Chinese conversations the user gate is:

```text
项目规则(project_rule)
增强已有 Skill(skill_patch)
个人全局 Skill(personal_global_skill)
拒绝(No)
修订(Revision)
```

Every proposal requires a concrete target, a complete Markdown patch with a heading, a concrete risk, representative evidence, placement, and placement reason. Placeholders cannot enter the user gate.

If the user chooses a different placement, the agent revises the proposal first so the owner, target, patch, and risk match the new placement.

## Adoption Is Ledger-Only

After the user accepts:

1. The agent edits the target with Codex, Claude Code, or another host's native tools.
2. The agent verifies the actual change.
3. Only then does it call `apply-proposal` or `global-apply` with the applied target and edit summary.

The CLI has no built-in Markdown writer. A failed edit or verification must never be recorded as adopted.

## Quick Start

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

Record a signal that already passed the write gate:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> log-signal \
  --source-type user_correction \
  --summary "Read the README and relevant source before recommending a project" \
  --operator verification_path \
  --cluster-key verification_path:verify_projects_before_recommending \
  --context "evaluating reusable external projects" \
  --strength 2 \
  --trigger "recommending an external project for adoption" \
  --action "read the README and relevant source before recommending" \
  --transfer-conditions "Skill, library, tool, or agent-project recommendations" \
  --negative-cases "quick name-only pointers" \
  --verification-path "identify the README and source inspected" \
  --auto-init
```

`propose` requires `--target`, `--patch`, and `--risk`; the patch must be a complete Markdown block with a heading.

After native editing and verification, record adoption:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal \
  --proposal-id <proposal-id> \
  --placement skill_patch \
  --applied-target "<skill-dir>/SKILL.md" \
  --summary "Added and verified the approved source-check rule"
```

See [references/cli-usage.md](references/cli-usage.md) for the complete command contract.

## Runtime And Migration

Project-local:

```text
<project-root>/.jinhua/
|-- data/
|   |-- signals.jsonl
|   |-- cluster-state.json
|   |-- proposals.jsonl
|   |-- adopted-edits.jsonl
|   |-- rejected-proposals.jsonl
|   `-- evolution-state.json
`-- runtime/
    `-- invocation-guard.json
```

Personal global runtime:

```text
<jinhua-dir>/global-data/
|-- global-signals.jsonl
|-- global-clusters.json
|-- global-proposals.jsonl
|-- adopted-global-edits.jsonl
|-- rejected-global-proposals.jsonl
|-- project-index.json
`-- global-state.json
```

Jinhua 2.0 uses local schema `3.0` and global schema `2.0`. The first non-Hook core command migrates older runtime automatically. Migration preserves signals, evidence, ids, proposal states, and adoption outcomes while removing obsolete fields and operator-promotion seed data. Signals are retained permanently; there is no compaction command.

Migration is idempotent. Malformed JSON/JSONL aborts before any rewrite.

Use `--project-id <stable-key>` or `JINHUA_PROJECT_ID` when unrelated projects or conversations share one workspace. The raw key is used only to derive a hash.

See [references/runtime-schema.md](references/runtime-schema.md) and [references/data-policy.md](references/data-policy.md).

## Host Adapters

| Host | Entry | Scope |
| --- | --- | --- |
| Codex | `.codex-plugin/plugin.json` + `hooks/hooks.json` | three trigger gates, Skill, CLI |
| Claude Code | `.claude-plugin/plugin.json` + the same `hooks/hooks.json` | native hooks, Skill, CLI |
| OpenClaw | `adapters/openclaw/` | plugin/Skill wrapper |
| Hermes | `adapters/hermes/` | Skill wrapper |
| TRAE | `adapters/trae/` | Skill wrapper |
| WorkBuddy | `adapters/workbuddy/` | Skill wrapper |

Outside Codex and Claude Code, automatic triggering depends on host support. Adapters never change the Jinhua core.

## Token And Attention Cost

- Input classification, ready attention, turn counting, and invocation guarding are local and add no separate model call.
- Ordinary turns do not load the full Jinhua Skill or run `cycle`.
- The fixed eight-turn fallback requests at most one short periodic continuation.
- Once selected, the trimmed `SKILL.md` is the only automatic control surface; references are read on demand.
- There is no forced output tail, daemon, external database, or vector retrieval.

## Project Navigation

- [AGENTS.md](AGENTS.md)
- [PROJECT_RULES.md](PROJECT_RULES.md)
- [PROJECT_INDEX.md](PROJECT_INDEX.md)
- [CONTRIBUTING.en.md](CONTRIBUTING.en.md)
- [SECURITY.en.md](SECURITY.en.md)
- [CODE_OF_CONDUCT.en.md](CODE_OF_CONDUCT.en.md)

License: MIT.
