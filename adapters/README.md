# Agent Adapters

Adapters expose the canonical Jinhua Skill and CLI without changing the core loop.

| Host | Adapter | Scope |
| --- | --- | --- |
| Codex and Claude Code | `hooks/hooks.json` | Shared UserPromptSubmit, PostToolUse, and Stop hooks using one wrapper set. |
| OpenClaw | `adapters/openclaw/openclaw.plugin.json` + Skill | Plugin/Skill packaging. |
| Hermes | `adapters/hermes/skills/jinhua/SKILL.md` | Agent Skills-compatible wrapper. |
| TRAE | `adapters/trae/skills/jinhua/SKILL.md` | Agent Skills-compatible wrapper. |
| WorkBuddy | `adapters/workbuddy/skills/jinhua/SKILL.md` | Generic Agent Skills-compatible wrapper. |

## Shared Contract

- Start a selected Jinhua branch with `cycle`.
- Apply the same `trigger + action` write gate and thresholds.
- Create complete proposals only from ready clusters.
- Preserve the localized placement-aware user gate.
- Edit and verify accepted targets with host-native tools before recording adoption.
- Do not create another ledger or auto-log from adapter hooks.

Only Codex and Claude Code adapters include lifecycle Hook definitions here. Automatic triggering for other hosts depends on their own plugin and Skill support.
