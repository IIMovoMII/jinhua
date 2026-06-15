# jinhua

Languages: English | [Chinese](README.zh-CN.md)

`jinhua` is a small, deterministic Skill evolution loop for Codex and Claude Code.

It helps the model notice reusable methodology signals during real work, cluster them locally, promote compressed evidence across projects, and ask the user only when a concrete Skill Evolution Proposal is ready.

Chinese visual guide: [docs/jinhua-logic.html](docs/jinhua-logic.html)

The user gate is always:

```text
Yes / No / Revision
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
  --target "target-skill/SKILL.md / research workflow" \
  --patch "When recommending reusable external projects for adoption, verify the README and relevant source before claiming usefulness." \
  --risk "Can add work when the user only wants quick pointers."
```

If the user says yes:

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal \
  --proposal-id <prop_id> \
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
