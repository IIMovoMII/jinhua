---
name: jinhua
description: Gated Skill evolution for reusable workflow lessons in Hermes. Use when work exposes a transferable method, repeated correction, missed expected procedure, or an explicit request to preserve/update a Skill or rule.
---

# jinhua for Hermes

Use the canonical jinhua CLI and rules. This adapter is Skill-only and does not add Hermes hooks.

Set `JINHUA_ROOT` to the installed jinhua repository or plugin directory. Start a triggered jinhua branch with:

```bash
python "$JINHUA_ROOT/scripts/jinhua.py" --project-root "$PWD" cycle
```

Then follow:

```text
cycle -> log-signal -> cycle -> propose/global-propose -> user gate -> apply/reject -> cycle -> validate
```

Do not create another memory ledger. Do not bypass the user gate.
