---
name: jinhua
description: Gated Skill evolution for reusable workflow lessons in TRAE. Use when work exposes a transferable method, repeated correction, missed expected procedure, or an explicit request to preserve/update a Skill or rule.
---

# jinhua for TRAE

Use jinhua as an Agent Skill. This adapter only teaches TRAE how to call the existing jinhua CLI.

Set `JINHUA_ROOT` to the installed jinhua repository or plugin directory. Start with:

```bash
python "$JINHUA_ROOT/scripts/jinhua.py" --project-root "$PWD" cycle
```

Only log a signal when the lesson has a reusable `trigger` plus `action`. If a cluster is ready, create one complete proposal or state a concrete skip reason. Keep the user gate intact. After acceptance, edit and verify with host-native tools before using the ledger-only apply command.
