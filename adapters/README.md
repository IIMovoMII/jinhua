# Agent Adapters

These adapters keep the core jinhua loop unchanged. They only expose the same Skill/CLI instructions through host-specific packaging.

## Support Levels

| Host | Adapter | Scope |
| --- | --- | --- |
| Claude Code | `hooks/hooks.json` | Native plugin hook adapter. Uses Claude Code's plugin hook location and `${CLAUDE_PLUGIN_ROOT}`. |
| OpenClaw | `adapters/openclaw/skills/jinhua/SKILL.md` | Skill adapter. Install as an OpenClaw skill or package inside an OpenClaw plugin. |
| Hermes | `adapters/hermes/skills/jinhua/SKILL.md` | Agent Skills-compatible skill adapter. |
| TRAE | `adapters/trae/skills/jinhua/SKILL.md` | Agent Skills-compatible skill adapter. |
| WorkBuddy | `adapters/workbuddy/skills/jinhua/SKILL.md` | Generic Agent Skills-compatible skill adapter. |

## Boundary

Adapters may route attention to jinhua. They must not create another experience ledger, bypass the user gate, or change `signals -> clusters -> proposals -> user gate`.
