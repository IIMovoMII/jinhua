---
name: jinhua
description: Methodology Skill for reusable workflow signals and Skill evolution in Agent Skills-compatible coding agents. Use when user feedback semantically corrects the agent's workflow, verification standard, reasoning direction, tool/Skill choice, missed expected procedure, or Skill-evolution behavior; when work reveals a repeatable method, transferable failure, repeated pattern, Skill-rule gap, or explicit request to preserve a method as a Skill, project rule, AGENTS.md rule, or global practice. Skip one-off content fixes, private facts, ordinary preferences, task-local bugs, and non-transferable details.
---

# jinhua

## Mission

Turn repeated task experience into small, user-gated Skill improvements.

The model handles detection, clustering, abstraction, placement recommendation, proposal drafting, and CLI invocation. The user is only the risk gate. Show the gate in the user's language; for Chinese users, use:

- `项目规则 (project_rule)`: accept as a lightweight current-project rule.
- `增强已有 Skill (skill_patch)`: accept as an enhancement to a specific existing local Skill.
- `个人全局 Skill (personal_global_skill)`: accept as a personal global Skill or all-project rule.
- `拒绝 (No)`: reject it and cool down the cluster.
- `修订 (Revision)`: record revision feedback, rewrite, and ask the same gate again.

## Trigger Boundary

After this Skill is selected, keep the wake-up boundary tight:

| Case | Action |
| --- | --- |
| User correction or feedback changes workflow, verification, reasoning direction, Skill/tool choice, or a missed expected procedure | Run `cycle`; log only if the lesson can be written as reusable `trigger` plus `action`. |
| Same project repeats one reusable method | Run `cycle`; log only if the method is not local noise. |
| A fixed failure exposes a transferable cause | Finish the user task first, then consider a quiet `failure_trace`. |
| User asks to remember, crystallize, make a Skill, or apply everywhere | Run `cycle`; use the placement ladder. |
| One-off bug, preference, local path, temporary command, or generic memory | Skip jinhua work. |

## Interaction Language

### Localized Display Labels

When jinhua shows user-facing gates, status summaries, or proposal prompts, use the user's current language for display labels while keeping canonical CLI values, JSON keys, command names, file paths, and placement ids unchanged. For Chinese users, prefer labels such as 项目规则(project_rule), 增强已有 Skill(skill_patch), 个人全局 Skill(personal_global_skill), 拒绝(No), 修订(Revision), 信号, 聚类, 就绪, and 待确认门.

Use the user's current conversation language for all user-facing dialogue from this Skill.

Examples:

- If the user is speaking Arabic, explain the proposal, risk, and gate in Arabic.
- If the user is speaking Chinese, explain the proposal, risk, and Skill-generation prompt in Chinese.
- If the user switches language, follow the latest clear user language.

Keep durable data and executable identifiers stable:

- CLI commands, option names, JSON fields, ids, file paths, and operator ids stay in English.
- Project experience records, signal summaries, and generated Skill files may stay in English unless the user asks otherwise.
- Localize user gate labels for display. Include canonical placement ids such as `project_rule`, `skill_patch`, and `personal_global_skill` in parentheses when needed so the CLI decision is unambiguous.

## Codex Trigger Layer

A Skill cannot run as a true background daemon. Automatic means: when this Skill is selected, run `cycle`; when installed as a Codex plugin, the thin trigger layer may help the host notice likely correction turns before the full Skill is loaded.

The primary trigger path is three gates:

1. `UserPromptSubmit`: local input classification only. It returns `none`, `possible_user_correction`, or `strong_user_correction`; it never logs signals, runs `cycle`, creates proposals, or edits Skills.
2. Agent direct call: the agent may call jinhua in the current turn when the user explicitly asks to crystallize a method, or when the agent sees a reusable workflow/verification/tool-choice lesson. A lightweight invocation guard prevents duplicate same-turn jinhua calls.
3. `Stop`: optional lightweight output-state parsing. It can parse `output_state` / `visibility` / `reason`, check the invocation guard, and avoid duplicate follow-up. It does not bypass the core jinhua rules or user gate.

Codex plugin hook config lives in `hooks/codex-hooks.json` and calls:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> codex-user-prompt-submit
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> codex-post-tool-use
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> codex-stop
```

The legacy `wake-check` and `hook-user-prompt-submit` commands may remain for compatibility, but they are not the primary trigger path.

When this Skill is actually selected, run the deterministic checkpoint:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> cycle
```

`cycle` does five things:

1. Initializes `.jinhua/data/` if missing.
2. Summarizes local signals, clusters, and pending gates.
3. Imports active local signals into the installed Skill's `global-data/`.
4. Summarizes cross-project method clusters and pending global gates.
5. Prints proposal skeleton hints for ready clusters, including `placement_hint` and any concrete local Skill recommendation.

Run `cycle` at the start of a triggered invocation, after any ledger-changing command, and before finishing substantial work that contained a clear methodology signal.

If `cycle` reports pending local or global proposals, surface one user gate immediately before creating new proposals or continuing the jinhua branch. Hook runners may use `cycle --json --fail-on-pending-gate`; exit code `2` means a pending gate must be shown to the user.

## Runtime Data

Project-local runtime:

- `.jinhua/data/signals.jsonl`
- `.jinhua/data/cluster-state.json`
- `.jinhua/data/proposals.jsonl`
- `.jinhua/data/adopted-edits.jsonl`
- `.jinhua/data/rejected-proposals.jsonl`
- `.jinhua/data/crystallized-operators.jsonl`
- `.jinhua/data/evolution-state.json`

Cross-project runtime:

- `<jinhua-dir>/global-data/global-signals.jsonl`
- `<jinhua-dir>/global-data/global-clusters.json`
- `<jinhua-dir>/global-data/global-proposals.jsonl`
- `<jinhua-dir>/global-data/adopted-global-edits.jsonl`
- `<jinhua-dir>/global-data/rejected-global-proposals.jsonl`
- `<jinhua-dir>/global-data/project-index.json`
- `<jinhua-dir>/global-data/global-state.json`

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

Quiet `failure_trace` signals are for repaired failures whose cause is clearly transferable.

## Write-or-Skip Gate

Do not force every lesson into a proposal. Most task details should be skipped.

Log only if the lesson can become a reusable `trigger` plus `action` and at least one is true:

- The user corrected reasoning direction, verification standard, or workflow.
- The same method appears repeatedly in the current project.
- A clear failure was fixed and the cause is transferable.
- A success path reveals a reusable method.
- The user explicitly asks to remember, crystallize, write into a Skill, or apply everywhere.

Skip one-off preferences, ordinary code bugs, local paths, temporary commands, local API details, and lessons useful only in the current chat.

## Local Proposal Gate

Same-project repetition means current need; do not wait for cross-project evidence before proposing a local settling point.

Generate a proposal when one local cluster reaches any trigger:

- At least 3 active signals.
- Total strength at least 5.
- The user explicitly asks to remember, crystallize, write into a Skill, or evolve now.
- A high-cost failure is reusable and urgent.

If `cycle` prints ready clusters, do not merely explain readiness. Either create the proposal immediately, or state the concrete skip reason.

Use the `cycle` skeleton as a starting point, refine placement, target, patch, and risk, then run:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> propose \
  --cluster-key <cluster-key> \
  --decision proposed_edit \
  --placement <project_rule|skill_patch|personal_global_skill> \
  --target "<target Skill / file / insertion location>" \
  --patch "## <Short Rule Title>

<Complete Markdown rule block.>" \
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
[complete Markdown block, not a loose sentence]

Risk:
[main side effect]

User gate:
Choose: 项目规则(project_rule) / 增强已有 Skill(skill_patch) / 个人全局 Skill(personal_global_skill) / 拒绝(No) / 修订(Revision)
Choosing a placement means accepting that placement.
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

- `项目规则(project_rule)`, `增强已有 Skill(skill_patch)`, or `个人全局 Skill(personal_global_skill)`: run `apply-proposal --placement <chosen-placement>`, then `cycle`.
- `拒绝(No)`: run `reject-proposal`, then `cycle`.
- `修订(Revision)`: run `reject-proposal --revision`, rewrite, and ask again.

For global proposals:

- `增强已有 Skill(skill_patch)` or `个人全局 Skill(personal_global_skill)`: run `global-apply --placement <chosen-placement>`, then `cycle`.
- `拒绝(No)`: run `global-reject`, then `cycle`.
- `修订(Revision)`: run `global-reject --revision`, rewrite, and ask again.

Rejected clusters enter cooldown. Do not bother the user again unless stronger evidence appears.

## Boundaries

The CLI performs deterministic ledger work: init, signal append, clustering, global import, proposal records, gate outcomes, merge suggestions, compaction, and validation.

The CLI does not decide whether a method is transferable or worth writing. The model makes that judgment and the user gates risk.
