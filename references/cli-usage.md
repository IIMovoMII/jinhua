# CLI Usage

The CLI is a deterministic ledger. It does not decide whether a method is intelligent, transferable, or worth writing into a Skill.

## Automatic Checkpoint

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

`cycle` initializes missing runtime files, summarizes local state, imports active local signals into global promotion state, surfaces pending gates, and prints proposal skeleton hints for ready clusters.

Use `--json` for machine-readable output. Use `--no-global` only for tests or debugging.

## Project Identity

Global promotion groups evidence by hashed project identity. By default, jinhua uses the git remote when available, then falls back to the project root path.

If one workspace contains unrelated projects or conversations, pass a stable explicit identity:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> --project-id <stable-project-or-conversation-key> cycle
```

You can also set `JINHUA_PROJECT_ID`. The explicit value is hashed before storage; global records do not keep the raw id.

## Record A Signal

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

Only `source-type`, `summary`, `operator`, `cluster-key`, `context`, and `strength` are required. The signal-card fields improve cross-project fingerprinting.

## Local Proposals

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> propose \
  --cluster-key <cluster-key> \
  --decision proposed_edit \
  --target "<target Skill / file / insertion location>" \
  --patch "<1-3 sentence patch>" \
  --risk "<main side effect>"
```

After the user gate:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal --proposal-id <id>
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal --proposal-id <id> --reason "..."
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal --proposal-id <id> --reason "..." --revision
```

## Global Promotion

Ordinary `cycle` already imports local active signals into `global-data/`.

Manual inspection:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-status
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-cycle
```

Create a global proposal:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-propose \
  --method-fingerprint <fingerprint> \
  --decision proposed_edit \
  --target "<target Skill / file / insertion location>" \
  --patch "<1-3 sentence patch>" \
  --risk "<main side effect>"
```

Inspect possible duplicate global methods without mutating data:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> global-merge-suggestions
```

## Maintenance Commands

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> list-clusters
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> status
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> compact --dry-run
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> validate
```

## Runtime Files

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

Global:

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
