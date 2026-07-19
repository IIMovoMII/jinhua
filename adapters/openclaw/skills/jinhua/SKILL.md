---
name: jinhua
description: Gated Skill evolution for reusable workflow lessons in OpenClaw. Use when work reveals a transferable method, repeated correction, missed expected procedure, or an explicit request to preserve/update a Skill or rule.
metadata:
  openclaw:
    category: productivity
    requires:
      bins:
        - python
---

# jinhua for OpenClaw

Use the canonical jinhua CLI and Skill rules. This adapter does not create another memory system.

Set `JINHUA_ROOT` to the installed jinhua repository or plugin directory. If unset, use the current workspace copy when it contains `scripts/jinhua.py`.

Start a triggered jinhua branch with:

```bash
python "$JINHUA_ROOT/scripts/jinhua.py" --project-root "$PWD" cycle
```

Then follow the canonical loop:

```text
cycle -> log-signal -> cycle -> propose/global-propose -> user gate -> apply/reject -> cycle -> validate
```

Do not write signals unless the lesson can become a reusable `trigger` plus `action`. Do not apply edits without the user gate.
