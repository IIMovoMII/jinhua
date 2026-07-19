# Hook 与平台集成

> 英文辅助版本见 [../hook-integration.md](../hook-integration.md)。

Jinhua 有两条入口：

1. 宿主通过 `SKILL.md` 选择 Skill。
2. 宿主 command hook 把注意力引到同一套 Skill 和 CLI。

CLI 不是后台进程。Hook 只做分类、计数、提醒和去重，不负责方法论判断，也不拥有经验账本。

## Codex 三道触发闸门

```text
UserPromptSubmit -> 本地纠错分类 + 就绪提醒 + 回合计数
PostToolUse      -> 调用保护门记录
Stop             -> 固定每 8 轮回顾 + 防循环
```

`hooks/codex-hooks.json` 调用：

```bash
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_user_prompt_submit.py"
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_post_tool_use.py"
python "${CLAUDE_PLUGIN_ROOT}/hooks/codex_stop.py"
```

三个 wrapper 都把 stdin 原样转发给 `scripts/jinhua.py` 中对应命令。

## 项目根目录解析

wrapper 按以下顺序定位目标项目：

1. Hook payload 中明确的项目路径；
2. 常见嵌套 payload 字段；
3. 支持的项目目录环境变量；
4. Hook 进程当前目录。

输入可以带 UTF-8 BOM。如果最后只能解析到已安装的 Jinhua 插件目录，Hook 会禁用运行态写入，不会把 `.jinhua` 错写进插件。

## 宿主信任边界

Hook 被发现和真正执行是两个状态。插件更新后，Codex 可能把 Hook 标为 `modified` 或 `untrusted`；宿主信任当前 Hook 内容后才会执行。

这个信任决定属于宿主，不进入 Jinhua 的信号、聚类、提案或调用保护运行态。

## 第一道：UserPromptSubmit

`codex-user-prompt-submit` 提取最新用户输入并返回：

- `none`；
- `possible_user_correction`；
- `strong_user_correction`。

分类完全在本地完成。命中纠错时，只输出一句很短的 `hookSpecificOutput.additionalContext`，要求 Agent 先对齐用户纠正，再按 Jinhua 原有写入门判断是否有可迁移经验。

同一个 Hook 还会：

- 按哈希化 session 统计不同用户回合；
- 每 8 轮把周期检查标为待执行；
- 只读检查已有本地/全局就绪聚类和待确认门；
- 按需增加一句就绪提醒。

它不会运行 `cycle`，不会迁移核心数据，不保存用户输入，不追加信号，不创建提案，也不修改文件。

手动检查分类器：

```bash
python <jinhua-dir>/scripts/jinhua.py classify-input \
  --text "你理解错了，只改触发层" \
  --json
```

## 第二道：PostToolUse 调用保护门

`codex-post-tool-use` 识别 `cycle`、`log-signal`、`propose`、`global-cycle`、`global-propose` 等 Jinhua CLI 入口。

轻量运行态写在：

```text
<project-root>/.jinhua/runtime/invocation-guard.json
```

它保存哈希化 session/turn、原因摘要哈希、入口、时间、近期事件、回合计数和周期票据。这不是经验账本。

保护门结果：

- `allow`：第一次有效进入；
- `already_handled`：Stop 发现本轮已经进入 Jinhua；
- `skip_duplicate`：同轮同原因重复；
- `block_loop`：同轮多次进入，疑似循环。

Agent 当前轮第一次直接调用始终允许，保护门只拦后续重复路径。

## 第三道：Stop 周期回顾

`codex-stop` 只负责：

1. `stop_hook_active` 为真时立即放行；
2. 当前 session 满 8 个不同用户回合时，请求一次极短继续，让 Agent 检查本轮及此前对话是否出现可复用方法。

请求继续前先查调用保护门。本轮已经运行 Jinhua 时，会消费周期票据并直接放行。

Stop Hook：

- 不解析输出状态尾巴；
- 不要求模型输出隐藏状态字段；
- 不创建候选状态；
- 不自行运行 `cycle`；
- 同一个到期回合最多请求一次。

周期固定为 8，环境变量不能覆盖。

## 就绪提醒

就绪提醒负责把成熟证据重新带回模型注意力：

1. 某个非 Hook 核心命令已经产生 `ready` 聚类或待确认门；
2. 下一次 `UserPromptSubmit` 只读旧状态，不触发迁移；
3. 一句短提示要求 Agent 运行 `cycle`；
4. Agent 必须创建一个完整提案、展示一个待确认门，或给出具体跳过原因。

Hook 自身不会把 `ready` 改成 `proposed`。

## Claude Code

`hooks/hooks.json` 是 Claude Code 插件适配。它使用同一组三个 wrapper 和 `${CLAUDE_PLUGIN_ROOT}`，没有第二套触发逻辑或账本。

`scripts/test_adapters.py` 和 `scripts/test_trigger_layer.py` 负责本地协议模拟。

## 其他宿主

- OpenClaw：`adapters/openclaw/` 提供插件/Skill 包装。
- Hermes：`adapters/hermes/` 提供 Skill 包装。
- TRAE：`adapters/trae/` 提供 Skill 包装。
- WorkBuddy：`adapters/workbuddy/` 提供 Skill 包装。

这些适配层只暴露权威 Skill/CLI。是否能自动 Hook 取决于宿主能力；不能为了模拟不存在的生命周期事件而修改 Jinhua 内核。

## 安全规则

- Hook 不自动写经验。
- 不在每条消息上运行完整 `cycle`。
- 不把用户原文写进运行态。
- 不绕过 `signals -> clusters -> proposals -> user gate`。
- 不自动修改 Skill 或项目规则。
- 本地纠错命中不等于已经证明存在可迁移经验。
