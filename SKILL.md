---
name: jinhua
description: Gated Skill evolution for reusable workflow lessons. Use when the user asks to preserve or update a Skill/rule, or when work exposes a transferable method, repeated correction, or missed agent procedure. Skip one-off fixes, preferences, and private facts.
---

# jinhua

Turn reusable workflow lessons into small improvements that the user explicitly approves.

## Required Flow

When this Skill is selected, run:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> cycle
```

Then follow this order:

1. Surface an existing pending user gate before starting new jinhua work.
2. If `cycle` reports a ready cluster, create one complete proposal or state a concrete skip reason.
3. Log a new signal only after the write-or-skip gate below passes.
4. Run `cycle` after every ledger-changing command.

Hooks only route attention, count turns, and prevent duplicate same-turn calls. They never log signals, create proposals, migrate core data, or edit files. Read [references/hook-integration.md](references/hook-integration.md) only for Hook or host-adapter work.

## Write-Or-Skip Gate

Write only when the lesson can be expressed as both:

- `trigger`: the future condition where the method applies.
- `action`: the reusable action to take.

At least one must also be true:

- The user corrected workflow, reasoning direction, verification, Skill/tool choice, or a missed procedure.
- The same reusable method repeated in the current project.
- A repaired failure exposed a transferable cause.
- A successful path exposed a reusable method.
- The user explicitly asked to preserve, crystallize, write, or apply the method elsewhere.

Finish the user task before logging a repaired failure unless the user explicitly asks to crystallize it now.

Skip one-off bugs, output preferences, private facts, local paths, temporary commands, local API details, and lessons useful only in the current conversation.

## Signal And Readiness

Strength is fixed:

- `1`: ordinary self-observation.
- `2`: clear user correction or repeated pattern.
- `3`: high-cost failure, repeated rework, or explicit crystallization request.

Use `log-signal --immediate` only for an explicit crystallization request or an urgent reusable high-cost failure.

At 2 same-project signals, ignore strength and allow only a `project_rule`; its proposal and applied target must stay inside the current project. At 3 signals or total strength 5, use the normal placement ladder.

Local adoption leaves signals active for global import. Non-Hook core commands recheck historical active clusters against current thresholds without rewriting signals.

The model chooses the reusable abstraction, operator, `cluster_key`, strength, and placement. The CLI only validates, stores, counts, clusters, migrates, and records gate outcomes. Read [references/data-policy.md](references/data-policy.md) before changing recordability or privacy rules.

## Placement

Choose the smallest useful landing point by strong evidence first:

1. `personal_global_skill`: explicit all-project behavior, a new standalone Skill, an independent workflow with no existing owner, or mature global evidence.
2. `skill_patch`: the method clearly belongs to an existing Skill. Recommend the concrete Skill and path; never make the user search for it.
3. `project_rule`: current-project need without a clear Skill owner or global scope.

Normal distribution should be: skip most, `project_rule` often, `skill_patch` less often, `personal_global_skill` least often.

For `project_rule`, use the CLI recommendation for the current agent profile. Do not create a missing project rule file before user confirmation.

## Proposal And User Gate

Create proposals only from ready clusters. Every proposal must contain:

- concrete `target`;
- complete Markdown `patch` with a heading;
- concrete `risk`;
- representative evidence;
- placement and placement reason;
- concrete Skill/path for `skill_patch` or rule-file recommendation for `project_rule`.

Show the gate in the user's current language. For Chinese users:

```text
项目规则(project_rule)
增强已有 Skill(skill_patch)
个人全局 Skill(personal_global_skill)
拒绝(No)
修订(Revision)
```

For two-signal project-only readiness, show only `项目规则(project_rule)`, `拒绝(No)`, and `修订(Revision)`.

Choosing a placement accepts that placement. `Revision` records feedback, rewrites the proposal, and asks the same gate again. `No` puts the cluster into cooldown until 5 new same-cluster signals arrive.

If the user selects a different placement, revise the proposal first so its owner, target, patch, and risk match that placement.

After acceptance:

1. Edit the approved target with the host's native file tools.
2. Verify the actual change.
3. Only then run `apply-proposal` or `global-apply` with the chosen placement, actual applied target, and edit summary.

The apply commands only record adoption. They do not edit files. Never record adoption after an edit or verification failure.

## Global Promotion

`cycle` imports compressed active local signals into global runtime with hashed project identity. Raw evidence stays project-local.

Global grouping uses a stable method fingerprint, preferably normalized `operator + action`. The model still judges abstraction, transferability, risk, and duplication.

Global readiness is:

- 3 unique projects, 5 evidence records, and total strength 7; or
- cross-project repeat path: 2 unique projects and 3 evidence records, regardless of strength; or
- fast path: 2 unique projects, total strength 6, plus at least 2 high-strength or user-correction records.

Global proposals use only `skill_patch` or `personal_global_skill` and always pass through the user gate.

## Language And References

Use the user's latest clear language for dialogue, proposal explanations, risks, status summaries, and gate labels. Keep commands, option names, JSON fields, ids, paths, operator ids, and placement ids in English.

Read references only when needed:

- CLI syntax and state transitions: [references/cli-usage.md](references/cli-usage.md)
- Recordability, privacy, and project identity: [references/data-policy.md](references/data-policy.md)
- Runtime file schemas and migration: [references/runtime-schema.md](references/runtime-schema.md)
- Hook and host behavior: [references/hook-integration.md](references/hook-integration.md)
- Maintenance and packaging: [references/maintenance.md](references/maintenance.md)

## Hard Boundaries

- Do not create a second experience ledger.
- Do not auto-log from Hooks.
- Do not bypass readiness except through `log-signal --immediate`.
- Do not bypass the placement-aware user gate.
- Do not auto-edit a Skill or rule from the CLI.
- Do not store raw user messages, credentials, private paths, or sensitive project identifiers in global data.
