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

`hooks/codex-hooks.json` 调用这些命令。Codex 会在交给平台 shell 前替换 `${CLAUDE_PLUGIN_ROOT}`；Windows 覆盖命令也故意使用同一写法，不依赖 `cmd.exe` 或 PowerShell 的变量语法：

```bash
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_user_prompt_submit.py"
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_post_tool_use.py"
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_stop.py"
```

这些 wrapper 会转给：

```bash
python <jinhua-dir>/scripts/jinhua.py codex-user-prompt-submit
python <jinhua-dir>/scripts/jinhua.py codex-post-tool-use
python <jinhua-dir>/scripts/jinhua.py codex-stop
```

打包后的 wrapper 从 stdin 接收 Hook payload，并按以下顺序定位项目根目录：payload 中明确的项目路径、payload 常见嵌套字段、支持的项目目录环境变量，最后才是 Hook 进程当前目录。如果当前目录解析出来正好是已安装插件自身，Hook 会认为路径不安全并直接返回，不会把运行态 `.jinhua` 写进插件目录。

## 宿主信任边界

Hook 被发现和 Hook 真正执行是两个不同状态。插件更新后，Codex 可能把 Jinhua Hook 列为 `modified` 或 `untrusted`；这表示已经发现它，但还不会执行，必须先由宿主信任当前 Hook 内容。信任决定属于 Codex 宿主，不属于 Jinhua 的经验账本。信任完成后，Hook 才会运行下面描述的只读触发层。

## 第一道：输入分类

`codex-user-prompt-submit` 从 stdin 读取 hook JSON，提取用户最新输入，并分类为：

- `none`
- `possible_user_correction`
- `strong_user_correction`

命中时只输出一条很短的 `hookSpecificOutput.additionalContext`，并且 stdout 只使用 Codex hook 协议允许的字段。它不会运行 `cycle`，不会写 `signals.jsonl`，不会创建提案，不保存用户原文，也不改 Skill。

它还会只读检查现有运行态 JSON/JSONL。如果已经有就绪聚类或待确认门，它会注入一条很短的提醒：先跑 `cycle`，再创建一个提案、展示一个确认门，或明确说明为什么跳过。这样不用后台服务，也不用额外模型调用，就能把 `就绪 -> 待确认门` 的注意力闭环补上。

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

如果 `output_state = jinhua_candidate`，Stop 闸门会先查 invocation guard。本轮已经跑过 jinhua，就跳过重复触发；本轮没跑过，就返回一次很短的 `decision: block` 原因，让 Codex 继续当前轮，由 agent 按原有 `cycle` / `log-signal` / `propose` 流程判断。`stop_hook_active = true` 时始终返回 `continue: true`，防止循环。它不能绕过用户确认门。

Stop 闸门还会按单个对话计数。默认每 8 个用户回合返回一次很短的继续原因，让 agent 检查本轮和过往对话是否有可复用经验；这是唯一的周期性额外模型继续，普通 Hook 仍只在本地运行，不调用 jinhua 核心命令。

Codex Stop hook 的输出协议不能改写已经生成的 assistant 正文。Jinhua 只解析状态尾巴用于触发判断，不再宣称能剥离宿主正文；如果需要绝对隐藏，需要更外层 wrapper。

## 旧兼容入口

下面两个命令保留给旧安装，但不再是主路径：

```bash
python <jinhua-dir>/scripts/jinhua.py wake-check --text "<latest user message>" --json
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> hook-user-prompt-submit
```

`hooks/claude-codex-hooks.json` 已标记 deprecated，并指向 `hooks/codex-hooks.json`。

## 宿主适配

宿主专用适配放在核心插件之外：

- Claude Code：`hooks/hooks.json` 使用原生 plugin hook 位置和 `${CLAUDE_PLUGIN_ROOT}`，调用同一组三道闸门 wrapper。
- OpenClaw：`adapters/openclaw/openclaw.plugin.json` 打包 `adapters/openclaw/skills/jinhua/` 下的 Skill 适配。
- Hermes：`adapters/hermes/skills/jinhua/SKILL.md` 是纯 Skill 适配。
- TRAE：`adapters/trae/skills/jinhua/SKILL.md` 是纯 Skill 适配。
- WorkBuddy：`adapters/workbuddy/skills/jinhua/SKILL.md` 是纯 Skill 适配。

适配层不能新增另一套账本，也不能绕过 `signals -> clusters -> proposals -> user gate` 主闭环。

## 安全规则

- 不自动应用 Skill 修改。
- 不绕过带落点的用户确认门：`项目规则(project_rule)` / `增强已有 Skill(skill_patch)` / `个人全局 Skill(personal_global_skill)` / `拒绝(No)` / `修订(Revision)`。
- 不保存用户原文。
- 不把原始项目路径复制到全局记录。
- 不让 hook 负责方法论判断。
- 不每条消息都跑完整 `cycle`。
- 不把 hook 输出当成“可迁移性已经被证明”的最终结论。
