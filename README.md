# jinhua

Languages: English | [Chinese](README.zh-CN.md)

`jinhua` is a small, deterministic Skill evolution loop for Codex and Claude Code.

It helps the model notice reusable methodology signals during real work, cluster them locally, promote compressed evidence across projects, and ask the user only when a concrete Skill Evolution Proposal is ready.

Chinese visual guide: [docs/jinhua-logic.html](docs/jinhua-logic.html)

The user gate is placement-aware:

```text
Project Rule / Skill Patch / Personal Global Skill / No / Revision
```

User-facing dialogue follows the user's current conversation language. Durable data, CLI identifiers, JSON fields, and generated Skill files may remain English unless the user asks otherwise.

## Core Loop

```text
cycle
-> log-signal
-> cycle
-> propose or global-propose when ready
-> user gate
-> apply/reject
-> cycle
-> validate
```

`cycle` is the automatic checkpoint. It initializes missing runtime state, scans local clusters, imports local signals into the global promotion layer, surfaces pending gates, and prints proposal skeleton hints for ready clusters.

## Rules

jinhua records only reusable methodology signals. A signal should have a future `trigger` plus `action`.

Record when at least one is true:

- User correction changes the model's reasoning, verification standard, or workflow.
- The same method repeats in the current project.
- A fixed failure exposes a transferable cause.
- A success path exposes a reusable method.
- The user explicitly asks to remember, crystallize, write into a Skill, or apply everywhere.

Skip one-off preferences, ordinary bugs, local paths, temporary commands, local API details, and lessons useful only in the current chat.

Strength is simple:

- `1`: ordinary observation.
- `2`: clear user correction or repeated pattern.
- `3`: high-cost failure, repeated rework, or explicit crystallization request.

Local readiness:

- `signal_count >= 3`, or
- `strength_sum >= 5`, or
- explicit immediate user request, or
- reusable urgent high-cost failure.

Global readiness:

- Same normalized `method_fingerprint`.
- Default: 3 projects, 5 evidence records, strength 7.
- Fast path: 2 projects, strength 6, with strong correction or high-strength evidence.

Placement is decided in this order:

1. `personal_global_skill`: all-project request, new standalone Skill, independent workflow, or global evidence.
2. `skill_patch`: belongs in an existing local Skill; jinhua recommends the concrete Skill and path.
3. `project_rule`: current-project need that is not clearly global or an existing Skill patch.
4. Otherwise: do not write.

For `project_rule`, jinhua recommends a target file with `recommended_project_rule_file`. It prefers existing project files and supports `--agent-profile` / `JINHUA_AGENT_PROFILE` for `codex`, `claude`, `copilot`, `trae`, `hermes`, `openclaw`, `workbuddy`, and generic/custom fallback. It does not auto-create project rule files.

## Quick Start

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

Log a structured reusable methodology signal:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> log-signal \
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

Re-run:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

When a local cluster is ready:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> propose \
  --cluster-key verification_path:read_readme_and_source_before_recommending_projects \
  --decision proposed_edit \
  --placement skill_patch \
  --target "target-skill/SKILL.md / research workflow" \
  --patch "When recommending reusable external projects for adoption, verify the README and relevant source before claiming usefulness." \
  --risk "Can add work when the user only wants quick pointers."
```

Placement choices:

- `project_rule`: lightweight current-project rule.
- `skill_patch`: enhance a concrete existing local Skill. jinhua recommends the best matching local Skill and path; the user should not have to search manually.
- `personal_global_skill`: personal global Skill or all-project rule.

If the user chooses a placement:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal \
  --proposal-id <prop_id> \
  --placement skill_patch \
  --target-skill target-skill \
  --summary "Added source-backed recommendation rule"
```

If the user says no:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal \
  --proposal-id <prop_id> \
  --reason "Too broad"
```

Validate:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> validate
```

## Commands

Primary workflow:

- `cycle`
- `log-signal`
- `list-clusters`
- `propose`
- `apply-proposal`
- `reject-proposal`
- `global-cycle`
- `global-status`
- `global-propose`
- `global-merge-suggestions`
- `global-apply`
- `global-reject`
- `compact`
- `status`
- `validate`

The CLI exposes only the commands above.

## Runtime Data

Project-local:

```text
.jinhua/data/
|-- signals.jsonl
|-- cluster-state.json
|-- proposals.jsonl
|-- adopted-edits.jsonl
|-- rejected-proposals.jsonl
|-- crystallized-operators.jsonl
`-- evolution-state.json
```

Global promotion:

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

No setup is required after installation. `cycle` creates the runtime state when needed.

If one workspace contains unrelated projects or conversations, pass `--project-id <stable-key>` or set `JINHUA_PROJECT_ID` to separate their global promotion evidence. The raw key is hashed before storage.

## Design Boundaries

- No daemon.
- No external database.
- No vector store.
- No dashboard.
- No machine-learning core loop.
- No user gate bypass.
- User-facing Skill dialogue follows the user's current language; executable identifiers stay English.

The system stays small on purpose. Machine learning, if ever added, should only assist ranking or retrieval and must remain optional.

## License

MIT.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
