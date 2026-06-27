# Hook 与平台集成

> 英文参考见 [../hook-integration.md](../hook-integration.md)。

`jinhua` 有两条兼容入口：

1. 标准 Skill 选择：宿主通过 `SKILL.md` 的 metadata 发现并加载 Skill。
2. Codex 插件 command hook：通过 `hooks/codex-hooks.json` 接入。

CLI 不是后台进程。Hook 只负责唤醒辅助和防重复，不负责判断经验是否可迁移，不写信号，不创建提案，也不改 Skill。

## Codex 主触发层

主 hook 路径是三道闸门：

```text
UserPromptSubmit -> 本地纠错分类
PostToolUse      -> invocation guard 记录
Stop             -> 输出状态尾巴解析
```

`hooks/codex-hooks.json` 调用：

```bash
python <jinhua-dir>/hooks/codex_user_prompt_submit.py
python <jinhua-dir>/hooks/codex_post_tool_use.py
python <jinhua-dir>/hooks/codex_stop.py
```

这些 wrapper 会转给：

```bash
python <jinhua-dir>/scripts/jinhua.py codex-user-prompt-submit
python <jinhua-dir>/scripts/jinhua.py codex-post-tool-use
python <jinhua-dir>/scripts/jinhua.py codex-stop
```

## 第一道：输入分类

`codex-user-prompt-submit` 从 stdin 读取 hook JSON，提取用户最新输入，并分类为：

- `none`
- `possible_user_correction`
- `strong_user_correction`

命中时只输出一条很短的 `hookSpecificOutput.additionalContext`。它不会运行 `cycle`，不会写 `signals.jsonl`，不会创建提案，不保存用户原文，也不改 Skill。

手动检查：

```bash
python <jinhua-dir>/scripts/jinhua.py classify-input --text "你没懂，这不是我要的范围" --json
```

## 第二道：调用保护门

`codex-post-tool-use` 会观察工具 payload，识别 jinhua CLI 入口，例如 `cycle`、`log-signal`、`propose`、`global-cycle`、`global-propose`。

它只写轻量运行时 guard：

```text
.jinhua/runtime/invocation-guard.json
```

这不是经验账本，只是当前 session / turn / reason 的防重复记录。

guard 决策：

- `allow`
- `already_handled`
- `merge_context_only`
- `skip_duplicate`
- `block_loop`

## 第三道：输出状态尾巴

`codex-stop` 解析极短状态尾巴：

```text
output_state: ok
visibility: silent
```

允许的 `output_state`：

- `ok`
- `user_correction_handled`
- `self_issue_detected`
- `uncertain`
- `jinhua_candidate`

允许的 `visibility`：

- `silent`
- `notify`
- `ask_confirmation`

如果 `output_state = jinhua_candidate`，Stop 闸门会先查 invocation guard。本轮已经跑过 jinhua，就跳过重复触发；本轮没跑过，才可能给 agent 一个极短提醒，让它按原有 `cycle` / `log-signal` / `propose` 流程判断。它不能绕过用户确认门。

Codex hook 不一定能在每个宿主里完美隐藏已经生成的文本。本实现会在宿主支持时尽量解析和剥离；如果需要绝对隐藏，需要更外层 wrapper。

## 旧兼容入口

下面两个命令保留给旧安装，但不再是主路径：

```bash
python <jinhua-dir>/scripts/jinhua.py wake-check --text "<latest user message>" --json
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> hook-user-prompt-submit
```

`hooks/claude-codex-hooks.json` 已标记 deprecated，并指向 `hooks/codex-hooks.json`。

## 安全规则

- 不自动应用 Skill 修改。
- 不绕过带落点的用户确认门：`Project Rule` / `Skill Patch` / `Personal Global Skill` / `No` / `Revision`。
- 不保存用户原文。
- 不把原始项目路径复制到全局记录。
- 不让 hook 负责方法论判断。
- 不每条消息都跑完整 `cycle`。
- 不把 hook 输出当成“可迁移性已经被证明”的最终结论。
