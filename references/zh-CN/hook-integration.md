# Hook 与平台集成

> 英文参考见 [../hook-integration.md](../hook-integration.md)；本文件用中文解释 Codex / Claude Code 怎么接入。

`jinhua` 有两条兼容的唤醒路径：

1. 标准 Skill 选择：宿主通过 `SKILL.md` 的 `name` 和 `description` 发现并加载 Skill。
2. 可选 hook 前置路由：宿主支持 `UserPromptSubmit` hook 时，先跑一个很便宜的粗筛。

CLI 不作为后台进程运行。Hook 可以帮助路由注意力，但不能改变安全模型。

只靠一个 Skill 仓库本身，不能强行让别人的 Codex 自动弹出“信任 hook”的提醒。对其他用户来说，hook 定义必须放在 Codex 会扫描的配置层里，比如 `~/.codex/hooks.json`、`~/.codex/config.toml`、`<repo>/.codex/hooks.json`、`<repo>/.codex/config.toml`，或者某个插件自己的 `hooks/hooks.json`。

当前仓库已经带了走这条路径所需的薄插件层：

- `.agents/plugins/marketplace.json`
- `.codex-plugin/plugin.json`
- `.claude-plugin/plugin.json`

## 只读文本粗筛

手动粗筛可以用：

```bash
python <jinhua-dir>/scripts/jinhua.py wake-check --text "<latest user message>" --json
```

`wake-check` 是只读的。它不会运行 `cycle`，不会记录信号，不会保存用户原文，也不会替模型判断经验是否值得沉淀。它只识别几类明显的元工作流线索：Skill 没触发、流程纠正、验证标准纠正、工具选择纠正，或用户要求把方法沉淀下来。

## UserPromptSubmit 适配器

Codex / Claude Code 这类 hook 可以调用：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> hook-user-prompt-submit
```

适配器从 stdin 读取 hook JSON，并尝试提取常见 prompt 字段：

- `prompt`
- `userPrompt`
- `message`
- `input.prompt`

如果没有传 `--project-root`，但 hook payload 里有 `cwd`，适配器会用 `cwd` 生成后续 `cycle` 提示。

如果命中同一套粗筛规则，适配器返回：

```json
{
  "continue": true,
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "..."
  }
}
```

如果没命中，只返回：

```json
{"continue": true}
```

这样 token 成本很低：每轮最多跑一次小正则检查；只有命中时，宿主 agent 才会收到一条很短的上下文提醒，然后再加载 `jinhua`。

## Codex

Codex Skill 的主要标准是 `SKILL.md`：必须有 YAML frontmatter，包括 `name` 和 `description`。这是 `jinhua` 对 Codex 的主兼容路径。

如果当前 Codex 环境支持并实际运行 hook，可以把 `UserPromptSubmit` 配到 `hook-user-prompt-submit`。有些 Codex 环境可能不会执行本地 hook，或者需要项目被信任、单独配置；这种情况下，`jinhua` 仍然通过普通 Skill 选择机制工作。

最小 `hooks.json` 形态：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"<jinhua-dir>/scripts/jinhua.py\" hook-user-prompt-submit",
            "timeout": 5,
            "statusMessage": "Checking jinhua wake-up"
          }
        ]
      }
    ]
  }
}
```

不要依赖 `UserPromptSubmit` 的 matcher；Codex 目前会忽略这个事件的 matcher。让适配器自己做便宜粗筛即可。

当 `jinhua` 真正被选中时，应先运行：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

如果 hook 需要把待确认提案当成硬信号，可以调用：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle --json --fail-on-pending-gate
```

退出码 `2` 表示存在本地或全局待确认提案，agent 必须先向用户展示确认门，再继续 jinhua 这条分支。

## Claude Code

Claude Code 可以用同一个 `UserPromptSubmit` 适配器。hook 命令从 stdin 接收平台传来的 hook JSON，再把适配器 JSON 输出到 stdout。

最小 `settings.json` 形态：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"<jinhua-dir>/scripts/jinhua.py\" hook-user-prompt-submit",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

需要时可以每轮都跑 `hook-user-prompt-submit`，但不要每轮都跑完整 `cycle`。适配器只在出现明显方法论线索时注入上下文，然后由被选中的 Skill 再运行 `cycle`。

## 安全规则

- 不要自动应用 Skill 修改。
- 不要绕过带落点的用户确认门：`Project Rule` / `Skill Patch` / `Personal Global Skill` / `No` / `Revision`。
- 不要保存用户原文。
- 不要把原始项目路径复制到全局记录。
- 不要让 hook 负责方法论判断。
- 不要每条消息都跑完整 `cycle`。
- 不要把 hook 输出当成“可迁移性已经被证明”的最终结论。
