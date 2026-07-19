---
name: jinhua
description: Gated Skill evolution for reusable workflow lessons in Agent Skills-compatible WorkBuddy setups. Use when work exposes a transferable method, repeated correction, missed expected procedure, or an explicit request to preserve/update a Skill or rule.
---

# jinhua for WorkBuddy

Use the canonical jinhua CLI and rules. This adapter is intentionally Skill-only because WorkBuddy hook packaging is not assumed here.

Set `JINHUA_ROOT` to the installed jinhua repository or plugin directory. Start with:

```bash
python "$JINHUA_ROOT/scripts/jinhua.py" --project-root "$PWD" cycle
```

Follow the existing jinhua loop and keep the user gate intact. Edit and verify accepted targets with host-native tools; apply commands are ledger-only.
