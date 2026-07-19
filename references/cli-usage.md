# CLI Usage

All commands use Python's standard library. Put global options before the subcommand.

## Checkpoint

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

`cycle` initializes or migrates local runtime, summarizes local state, imports compressed active signals into global runtime, and surfaces pending gates or ready proposal skeletons.

Useful options:

- `--json`: machine-readable output
- `--fail-on-pending-gate`: exit `2` when a local/global gate is waiting
- `--no-global`: skip global import for tests or diagnostics
- `--project-id <stable-key>`: distinguish unrelated projects/conversations sharing one workspace; only its hash is stored

## Trigger Layer

```bash
python <jinhua-dir>/scripts/jinhua.py classify-input --text "you misunderstood the workflow" --json
python <jinhua-dir>/scripts/jinhua.py codex-user-prompt-submit
python <jinhua-dir>/scripts/jinhua.py codex-post-tool-use
```

- `classify-input` returns `none`, `possible_user_correction`, or `strong_user_correction`.
- `codex-user-prompt-submit` classifies locally, counts unique turns, may inject short correction/ready attention, and adds one hidden periodic review every 8 new turns.
- `codex-post-tool-use` records same-turn Jinhua entry for duplicate protection.

Hooks never migrate core data, write signals/proposals, or edit files.

## Record A Signal

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> log-signal \
  --source-type user_correction \
  --summary "Read README and relevant source before recommending a project" \
  --operator verification_path \
  --cluster-key verification_path:verify_projects_before_recommending \
  --context "evaluating reusable external projects" \
  --strength 2 \
  --trigger "recommending an external project for adoption" \
  --action "read the README and relevant source before recommending" \
  --transfer-conditions "Skill, library, tool, or agent-project recommendations" \
  --negative-cases "quick name-only pointers" \
  --verification-path "cite the README and inspected source" \
  --auto-init
```

Source type, summary, operator, cluster key, and context are required. Strength defaults to `1`; pass it explicitly when the evidence is a correction, repetition, or high-cost failure. Signal-card fields improve transfer judgment and global fingerprints.

Use `--immediate` only for an explicit crystallization request or urgent reusable high-cost failure. It is the only readiness bypass.

## Local Proposal

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> propose \
  --cluster-key verification_path:verify_projects_before_recommending \
  --placement skill_patch \
  --recommended-skill github-project-due-diligence \
  --recommended-skill-path "<skill-dir>/SKILL.md" \
  --target "<skill-dir>/SKILL.md / Source Verification" \
  --patch "## Source Verification

Read the README and relevant source before recommending a project for adoption." \
  --risk "May add unnecessary work to quick name-only pointers."
```

`target`, a Markdown `patch` with a heading, and `risk` are mandatory. `placement` may be omitted to use the skeleton recommendation. A `skill_patch` requires a concrete Skill name/path; a `project_rule` requires the resolver's project-rule file.

The proposal enters `pending_user_gate`. Show the localized user gate before continuing.

## Apply, Revise, Or Reject

After the user accepts, edit and verify the target with the host's native tools. Then record adoption:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal \
  --proposal-id <proposal-id> \
  --placement skill_patch \
  --applied-target "<skill-dir>/SKILL.md" \
  --summary "Added the approved Source Verification rule and verified the diff."
```

The apply command never writes the target file.

If the user chooses a different placement, revise the proposal before applying so its owner and target metadata match the accepted placement.

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal \
  --proposal-id <proposal-id> \
  --reason "Too broad"

python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal \
  --proposal-id <proposal-id> \
  --reason "Limit it to adoption recommendations" \
  --revision
```

Revision keeps the gate open. Rejection starts a fixed 5-new-signal cooldown.

## Global Promotion

Ordinary `cycle` already imports local signals. Manual inspection:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-cycle
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-status
```

Create a ready global proposal with mandatory target/patch/risk:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-propose \
  --method-fingerprint <fingerprint> \
  --placement personal_global_skill \
  --target "~/.codex/skills/<skill-name>/SKILL.md" \
  --patch "## Reusable Rule

Apply the verified cross-project method." \
  --risk "May be too broad for projects with different constraints."
```

After native editing and verification, use `global-apply` with `--proposal-id`, `--placement`, `--applied-target`, and `--summary`. Use `global-reject [--revision]` for rejection or revision.

## Diagnostics

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> status
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> list-clusters
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> validate
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> guard --session-id s --turn-id t
```

`validate` migrates old runtime first, then enforces the current schema and removed-field boundary.

## Runtime Files

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

<jinhua-dir>/global-data/
|-- global-signals.jsonl
|-- global-clusters.json
|-- global-proposals.jsonl
|-- adopted-global-edits.jsonl
|-- rejected-global-proposals.jsonl
|-- project-index.json
`-- global-state.json
```

See [runtime-schema.md](runtime-schema.md) for fields and migration behavior.
