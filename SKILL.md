---
name: jinhua
description: Methodology Skill evolution assistant for Agent Skills-compatible coding agents, including Claude Code and Codex. Use when task work reveals reusable prompting habits, user corrections, repeated reasoning failures, successful reasoning traces, Skill self-improvement opportunities, compact Skill update proposals, or when a user asks to make Skill evolution automatic/closed-loop. The Skill proactively runs its cycle command, silently accumulates reusable methodology signals, clusters them locally and globally, recommends the right placement layer, and asks the user for a placement-aware gate when evidence is strong enough. Do not use for ordinary prompt writing, generic memory, personal preferences, or normal task execution without a methodology signal.
---

# jinhua

## Mission

Turn repeated task experience into small, user-gated Skill improvements.

The model handles detection, clustering, abstraction, placement recommendation, proposal drafting, and CLI invocation. The user is only the risk gate:

- `Project Rule`: accept as a lightweight current-project rule.
- `Skill Patch`: accept as an enhancement to a specific existing local Skill.
- `Personal Global Skill`: accept as a personal global Skill or all-project rule.
- `No`: reject it and cool down the cluster.
- `Revision`: record revision feedback, rewrite, and ask the same gate again.

## Use This When

Use this Skill when the current work reveals a reusable methodology signal:

- The user corrects the model's reasoning direction, verification standard, or workflow.
- A task succeeds because a transferable method worked.
- A task fails or needs rework because a recurring reasoning mistake appeared.
- Several prompts express the same higher-level method.
- A Skill rule is missing, duplicated, too broad, too narrow, or too costly.
- The user asks to make Skill evolution automatic, closed-loop, or more intelligent.

Do not use it for one-off facts, style preferences, private memory, ordinary bug fixes, or generic prompt templates.

## Interaction Language

Use the user's current conversation language for all user-facing dialogue from this Skill.

Examples:

- If the user is speaking Arabic, explain the proposal, risk, and gate in Arabic.
- If the user is speaking Chinese, explain the proposal, risk, and Skill-generation prompt in Chinese.
- If the user switches language, follow the latest clear user language.

Keep durable data and executable identifiers stable:

- CLI commands, option names, JSON fields, ids, file paths, and operator ids stay in English.
- Project experience records, signal summaries, and generated Skill files may stay in English unless the user asks otherwise.
- The user gate may be localized for display, but include the canonical tokens `Yes`, `No`, and `Revision` so the decision is unambiguous. A placement choice counts as `Yes` for that placement.

## Automatic Checkpoint

A Skill cannot run as a true background daemon. Automatic means: whenever this Skill triggers, run `cycle`.

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> cycle
```

`cycle` is the deterministic checkpoint:

1. Initializes `.jinhua/data/` if missing.
2. Summarizes local signals, clusters, and pending gates.
3. Imports active local signals into the installed Skill's `global-data/`.
4. Summarizes cross-project method clusters and pending global gates.
5. Prints proposal skeleton hints for ready clusters, including `placement_hint` and any concrete local Skill recommendation.

Run `cycle` at the start of a triggered invocation, after any ledger-changing command, and before finishing substantial work that contained a clear methodology signal.

If `cycle` reports pending local or global proposals, process that user gate before creating new proposals.

## Runtime Data

Project-local runtime:

- `.jinhua/data/signals.jsonl`
- `.jinhua/data/cluster-state.json`
- `.jinhua/data/proposals.jsonl`
- `.jinhua/data/adopted-edits.jsonl`
- `.jinhua/data/rejected-proposals.jsonl`
- `.jinhua/data/evolution-state.json`

Cross-project runtime:

- `<jinhua-dir>/global-data/global-signals.jsonl`
- `<jinhua-dir>/global-data/global-clusters.json`
- `<jinhua-dir>/global-data/global-proposals.jsonl`
- `<jinhua-dir>/global-data/adopted-global-edits.jsonl`
- `<jinhua-dir>/global-data/rejected-global-proposals.jsonl`
- `<jinhua-dir>/global-data/project-index.json`

Keep raw evidence project-local. Promote only compressed methodology evidence and hashed project identity.

If one workspace contains unrelated projects or conversations, use `--project-id <stable-key>` or `JINHUA_PROJECT_ID` so global promotion can distinguish them without storing the raw key.

## Signal Recording

Log only clear reusable methodology signals. Weak signals should usually be ignored.

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> log-signal \
  --source-type user_correction \
  --summary "Read README and relevant source before recommending reusable GitHub projects" \
  --operator verification_path \
  --cluster-key verification_path:read_readme_and_source_before_recommending_projects \
  --context "researching reusable tools" \
  --strength 2 \
  --trigger "recommending external projects for adoption" \
  --action "verify README and relevant source before recommending" \
  --transfer-conditions "tool, library, Skill, or agent project recommendations" \
  --negative-cases "quick pointers where the user did not ask for adoption judgment" \
  --verification-path "cite README and source files used" \
  --confidence 0.8 \
  --auto-init
```

Required key:

```text
operator:short_method_slug
```

Strength:

- `1`: ordinary self-observation.
- `2`: clear user correction or repeated pattern.
- `3`: high-cost failure, repeated rework, or explicit crystallization request.

Optional signal-card fields make cross-project merging more accurate:

- `trigger`: when the method applies.
- `action`: the reusable method action.
- `transfer_conditions`: where it transfers.
- `negative_cases`: when not to use it.
- `verification_path`: how to check it.
- `confidence`: optional 0..1 ranking signal, never a final authority.

After `log-signal`, run `cycle`.

## Write-or-Skip Gate

Do not force every lesson into a proposal. Most task details should be skipped.

Log only if the lesson can become a reusable `trigger` plus `action` and at least one is true:

- The user corrected reasoning direction, verification standard, or workflow.
- The same method appears repeatedly in the current project.
- A clear failure was fixed and the cause is transferable.
- A success path reveals a reusable method.
- The user explicitly asks to remember, crystallize, write into a Skill, or apply everywhere.

Skip one-off preferences, ordinary code bugs, local paths, temporary commands, local API details, and lessons useful only in the current chat.

## Failure Trace Candidate

After clear failure evidence, consider a quiet `failure_trace` signal only if all are true:

1. The task was fixed or the failure cause is known.
2. The lesson can be phrased as a future `trigger` plus `action`.
3. The lesson is not a one-off typo, missing import, or local API detail.

If yes, log a quiet signal and run `cycle`. If not, do nothing. Fix the user's task first; never interrupt the task just to analyze a failure.

## Local Proposal Gate

Local repetition means current need. If the same project repeatedly produces the same reusable method, propose a local settling point; do not wait for cross-project evidence. Cross-project evidence is required only for global promotion.

Generate a proposal when one local cluster reaches any trigger:

- At least 3 active signals.
- Total strength at least 5.
- The user explicitly asks to remember, crystallize, write into a Skill, or evolve now.
- A high-cost failure is reusable and urgent.

Use the `cycle` skeleton as a starting point, refine placement, target, patch, and risk, then run:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> propose \
  --cluster-key <cluster-key> \
  --decision proposed_edit \
  --placement <project_rule|skill_patch|personal_global_skill> \
  --target "<target Skill / file / insertion location>" \
  --patch "<1-3 sentence patch>" \
  --risk "<main side effect>"
```

Placement ladder:

1. `personal_global_skill`: use only when the user asks for all-project behavior, asks for a new standalone Skill, the method is an independent workflow with no existing Skill owner, or global evidence supports it.
2. `skill_patch`: use when the method belongs in an existing local Skill. The agent must recommend the most suitable concrete local Skill and path; do not ask the user to find it.
3. `project_rule`: use as the local fallback when current-project repetition shows need but the method is not clearly an existing Skill patch or personal global Skill.

Do not choose `personal_global_skill` for current-project conventions, local repair habits, directory structure, framework details, or one-off tool preferences. Normal distribution should be: skip most, `project_rule` often, `skill_patch` less often, `personal_global_skill` least often.

For `project_rule`, use the CLI skeleton's `recommended_project_rule_file` and `recommended_project_rule_reason`. It prefers existing project files and supports `--agent-profile` / `JINHUA_AGENT_PROFILE` for `codex`, `claude`, `copilot`, `trae`, `hermes`, `openclaw`, `workbuddy`, and generic/custom fallback. Never auto-create a project rule file without user confirmation.

Show the user this structure, rendered in the user's current conversation language:

```markdown
## Skill Evolution Proposal

Trigger:
[why the threshold was reached]

Decision:
proposed_edit / crystallize_experience / merge_rule / experimental_operator / core_operator_promotion / reject

Recommended placement:
project_rule / skill_patch / personal_global_skill

Placement reason:
[why this layer is the smallest useful landing point]

Evidence:
[up to 3 representative signal summaries]

Recommended local Skill:
[specific local Skill name, required when placement is skill_patch]

Recommended Skill path:
[local SKILL.md path, required when placement is skill_patch]

Recommended project rule file:
[project rule file, required when placement is project_rule]

Project rule reason:
[why this file was recommended]

Target:
[target Skill / file / insertion location]

Patch:
[1-3 sentence patch]

Risk:
[main side effect]

User gate:
Choose: Project Rule / Skill Patch / Personal Global Skill / No / Revision
(Choosing a placement counts as Yes for that placement.)
```

Keep `decision` values, proposal ids, command names, option names, file paths, and code snippets in English even when the surrounding explanation is localized.

## Global Promotion

Cross-project repetition is real only when:

- The normalized method fingerprint matches, preferably from `operator + action`.
- `trigger` and `transfer_conditions` are evidence for transfer judgment, not hard split keys.
- Evidence comes from multiple unique project hashes.
- The method passes model judgment for abstraction, transferability, risk, and duplication.
- A global proposal is shown to the user before any global Skill edit is adopted.

Default global readiness:

- 3 unique projects, 5 evidence records, and strength 7.
- Or fast path: 2 unique projects, strength 6, and repeated high-strength or user-correction evidence.

Use `global-merge-suggestions` to inspect similar global clusters. It never mutates data.

## Applying Decisions

For local proposals:

- `Project Rule`, `Skill Patch`, or `Personal Global Skill`: run `apply-proposal --placement <chosen-placement>`, then `cycle`.
- `No`: run `reject-proposal`, then `cycle`.
- `Revision`: run `reject-proposal --revision`, rewrite, and ask again.

For global proposals:

- `Skill Patch` or `Personal Global Skill`: run `global-apply --placement <chosen-placement>`, then `cycle`.
- `No`: run `global-reject`, then `cycle`.
- `Revision`: run `global-reject --revision`, rewrite, and ask again.

Rejected clusters enter cooldown. Do not bother the user again unless stronger evidence appears.

## Boundaries

The CLI performs deterministic ledger work: init, signal append, clustering, global import, proposal records, gate outcomes, merge suggestions, compaction, and validation.

The CLI does not decide whether a method is intelligent, transferable, or worth writing. The model makes that judgment and the user gates risk.

Machine learning is not part of the core loop. If ever added, it may only assist ranking or candidate retrieval; it must not bypass deterministic rules, proposal review, validation, or the user gate.

## Success Criteria

A complete loop is successful when:

1. A reusable methodology signal is detected.
2. `cycle` confirms state and pending gates.
3. The signal is logged and clustered without interrupting the user.
4. Ready clusters produce proposal skeletons.
5. The model creates a compact Skill Evolution Proposal with the smallest useful placement layer.
6. If the proposal is a `skill_patch`, the model recommends the concrete local Skill and path.
7. The user chooses Project Rule / Skill Patch / Personal Global Skill / No / Revision.
8. The accepted or rejected outcome is recorded.
9. Accepted changes are applied or recorded with the smallest useful patch.
10. Cross-project promotion uses unique-project evidence and the same user gate.
