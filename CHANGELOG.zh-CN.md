# 更新日志

> 本文件是中文更新说明；英文辅助版本见 [CHANGELOG.md](CHANGELOG.md)。

## 未发布

- Codex 与 Claude Code 统一使用官方默认 `hooks/hooks.json`，删除重复的 `hooks/codex-hooks.json` 和 manifest 覆盖字段；该触发包要求 Codex 0.144.6 或更高版本。
- 修复 PostToolUse 把 README、用户输入、搜索表达式或工具输出中的 Jinhua 命令文字误判为真实调用的问题。
- 项目、会话、回合和 Stop 递归状态只从宿主权威字段读取；未知 payload 不再改变调用保护状态。
- Codex 使用 `turn_id`、Claude Code 兼容 `prompt_id`；同一回合的多个 Jinhua 子命令只记录一个保护事件。
- 新增“提到命令”和“执行命令”的反例测试，并覆盖伪造 `cwd`、session、turn 和 `stop_hook_active`。

## 2.0.0 - 2026-07-19

- 把实际加载的 Skill 控制面从 302 行、15,415 字节精简为只保留硬规则和按需路由的控制文件，同时保留触发、阈值、落点和用户确认语义。
- 触发层收敛为：本地纠错/就绪提醒、Agent 当前轮直接调用与同轮保护、每个会话固定 8 轮 Stop 回顾。
- 删除输出状态尾巴，以及 `wake-check`、`hook-user-prompt-submit`、`parse-output-state` 命令。
- 删除提案 decision/confidence、operator 晋升脚手架和种子、压缩删除、全局模糊合并建议、时间冷却和 force 旁路。
- 提案必须包含具体目标、完整 Markdown 修改块和具体风险；`skill_patch` 与 `project_rule` 必须有具体所有者。
- apply 命令改为纯记账：Agent 先用宿主原生工具修改并验证，再记录 `applied_target` 和 `edit_summary`。
- 新增本地 schema 3.0、全局 schema 2.0 的幂等自动迁移；数据损坏时改写前中止，已有信号不丢失。
- 新增标准库核心闭环测试，并同步 Codex、Claude Code、OpenClaw、Hermes、TRAE、WorkBuddy 包装。

### 删除的公开命令

- `wake-check`
- `hook-user-prompt-submit`
- `parse-output-state`
- `compact`
- `global-merge-suggestions`

### 删除的公开参数

- `--decision`
- `--confidence`
- `--force`
- `--target-skill-path`
- apply 阶段的 `--patch`
- `--insert-after`
- `--cooldown-days`
- `--cooldown-signals`

## 2026-07-19 项目导航与归档边界

- 新增简短的智能体说明、项目规范和逐文件索引，让后续任务只读取相关 active 文件，不扫描运行态和历史文件。
- 已把被新触发层替代的 `claude-codex-hooks.json` 和 Python 生成缓存移到本地、被忽略的 `.archive/`。
- 保留 `.jinhua/` 和 `global-data/`，因为它们是正在使用的运行态，不是过时文件。

## 2026-07-19 Codex Hook 信任与运行验证

- 已确认 Codex 能通过插件清单发现 Jinhua 的三个触发 Hook，并把命令解析到 `${CLAUDE_PLUGIN_ROOT}` 下。
- 明确宿主侧信任边界：Hook 即使已经被发现，只要状态是 `modified` 或 `untrusted`，就不会真正执行；插件更新后必须由宿主信任当前 Hook 内容。
- 已用一次不修改文件的真实 Codex 运行验证：只新增按会话计数的触发层运行态，`signals`、聚类和提案数据保持不变。

## 2026-07-19 Codex Hook 协议兼容

- 三个 Codex Hook 的 stdout 现在严格符合宿主协议，不再输出内部 `jinhua` 状态字段。
- Stop 提醒改用 Codex 支持的 `decision: block + reason`，并显式处理 `stop_hook_active`，用运行态 ticket 防止循环。
- Windows Hook 命令统一使用 Codex 会替换的 `${CLAUDE_PLUGIN_ROOT}`，不再依赖 shell 专用变量语法。

## 2026-07-19 Codex Hook 项目根目录解析

- 修复三个 Codex Hook 命令，把插件根目录变量用于运行时解析，不再把 `<jinhua-dir>` 当成真实路径执行。
- 项目根目录解析支持常见的嵌套 payload 字段和项目目录环境变量。
- 兼容 Windows Hook stdin 可能带有的 UTF-8 BOM，避免因此丢失项目路径。
- 如果无法得到可信的项目根目录，Hook 不会把运行态写进已安装插件目录。

## 2026-06-27 Agent 适配层

- 新增 `hooks/hooks.json`，作为 Claude Code plugin hook 适配，不改核心插件 manifest。
- 在 `adapters/` 下新增 OpenClaw、Hermes、TRAE、WorkBuddy 适配。
- 新增 adapter 冒烟测试，确保宿主包装和 jinhua 核心账本分离。

## 2026-06-27 就绪提醒桥

- 给 `codex-user-prompt-submit` 增加只读就绪提醒检查。
- 如果本地/全局已经有就绪聚类或待确认门，下一轮提示词会收到一句很短的提醒：运行 `cycle`，然后创建一个提案、展示一个确认门，或明确说明为什么跳过。
- 这个桥不运行 `cycle`，不写信号，不创建提案，不改 Skill，也不绕过用户确认门。

## 2026-06-27 加重本地输入闸门

- `classify-input` 的本地纠错命中改为按语义分类，并返回结构化命中证据。
- 扩充第一道本地闸门对 Skill、工具、流程漏触发的识别，同时继续避免把普通澄清误判为强触发。
- 新增按单个对话计数的 Stop 周期兜底：默认每 8 个用户回合，用极短静默提示提醒 agent 检查本轮和过往对话是否有可复用经验。

## 2026-06-27 用户确认门本地化与二次瘦身

- 用户可见确认门改为中文优先展示：`项目规则(project_rule)`、`增强已有 Skill(skill_patch)`、`个人全局 Skill(personal_global_skill)`、`拒绝(No)`、`修订(Revision)`。
- 根目录 `data/` 只保留核心 operator 种子文件，删除容易误导为运行态的空账本模板。
- 同步更新 README、Skill 说明、项目地图、hook 文档、术语表和静态逻辑图。

## 2026-06-27 Codex 三道闸门触发层

- 用 Codex 优先的三道闸门触发层替换旧的 hook-first 唤醒路径：输入侧本地纠错分类、同轮 invocation guard 防重复、输出侧轻状态尾巴解析。
- 新增 `hooks/codex-hooks.json`，以及 `UserPromptSubmit`、`PostToolUse`、`Stop` 三个很薄的 Codex hook wrapper。
- 新增触发层 CLI 命令：`classify-input`、`codex-user-prompt-submit`、`codex-post-tool-use`、`codex-stop`、`parse-output-state`、`guard`。
- `wake-check` 和 `hook-user-prompt-submit` 保留为 legacy 兼容命令，但不再是主触发路径。
- 核心闭环不变：`cycle`、`log-signal`、聚类、提案、落点阶梯和用户确认门仍然负责 Skill 进化。
- 新增触发层测试，覆盖纠错分类、内部提示、状态尾巴解析/剥离、调用去重、agent 直接调用、Stop 防循环和旧 hook manifest 清理。

## 2026-06-25 插件市场包装补齐

- 新增 `.agents/plugins/marketplace.json`，让 Codex 能把 `jinhua` 当成真正插件源发现，而不只是复制进来的 Skill。
- 把 `.codex-plugin/plugin.json` 补成真实插件清单，显式声明 `skills` 和 `hooks`。
- 新增 `.claude-plugin/plugin.json` 和 `.claude-plugin/marketplace.json`，对齐 Claude Code 的插件包装入口。
- 新增 `skills/jinhua/SKILL.md`，作为很薄的插件技能入口，再转到根目录权威版 `SKILL.md`。

## 2026-06-25 轻量插件钩子层

- 新增最小 `.codex-plugin/plugin.json` 和 `hooks/` 薄包装层，用于 Codex 和 Claude Code 的 hook 打包。
- Skill 本体继续只负责 `SKILL.md` + `hook-user-prompt-submit`；新的 hook 层只转发到现有适配器。
- 更新了项目地图和 hook 文档，把“Skill 本体”和“hook 打包层”的边界写清楚。

## 2026-06-25 Codex / Claude Code hook 适配器

- 新增只读命令 `hook-user-prompt-submit`，用于 Codex / Claude Code 这类 `UserPromptSubmit` hook。
- 适配器从 stdin 读取 hook JSON，提取常见 prompt 字段，只在 `wake-check` 命中时输出 `hookSpecificOutput.additionalContext`。
- 明确 Codex 兼容主路径仍然是 `SKILL.md` 元信息；hook 是否真正运行取决于宿主配置。

## 2026-06-25 支持 hook 的轻量唤醒检查

- 新增只读命令 `wake-check`，用于 hook 在加载完整 Skill 前做便宜的前置路由。
- 新增 `cycle --json --fail-on-pending-gate`，让 hook 可以用退出码 `2` 识别待确认提案。
- 明确 hook 契约：`wake-check` 只做粗筛，精确的方法论判断仍然留在 jinhua 内部。

## 2026-06-15 带落点的用户确认

- 新增明确提案落点：`project_rule`、`skill_patch`、`personal_global_skill`。
- `skill_patch` 提案会推荐具体本地 Skill，用户不需要自己找目标 Skill。
- `cycle`、`propose`、`global-propose`、`apply-proposal`、`global-apply` 都会携带落点字段，形成完整闭环。

## 2026-06-15 公开发布

- 发布 `jinhua`：一个用于 Skill 进化的本地闭环工具，适用于 Codex、Claude Code 等支持 Skill 的编程智能体（Agent）。
- 新增英文和中文文档：`README`、`SKILL`、`PROJECT_MAP`、贡献指南、安全政策和行为准则。
- 新增 `references/zh-CN/`，说明 CLI 用法、数据政策、平台集成、维护规则、运行态结构和术语。
- 中文文档作为默认公开版本，同时保留英文辅助文档。
- CLI 命令、参数名、JSON 字段和 operator id 保持英文，并在中文术语表里解释。

## 核心能力

- `cycle` 成为唯一自动检查点：初始化、本地状态、全局导入、全局状态、待确认事项和成熟聚类提示都从这里进入。
- `log-signal` 支持结构化信号卡字段：`trigger`、`action`、`transfer_conditions`、`negative_cases`、`verification_path` 和 `confidence`。
- 全局方法指纹（method fingerprint）优先使用 `operator + action`，再回退到 `cluster_key` 和摘要。
- `global-merge-suggestions` 可以只读查看可能重复的跨项目方法。

## 产品边界

当前主线保持稳定、克制：

- 确定性 CLI。
- 项目本地信号。
- 全局晋升层。
- 提案骨架。
- 用户确认后的采纳/拒绝记录。
- 数据验证。

后续修改主要应围绕 bug 修复、真实使用后的阈值微调、验证覆盖和文档压缩展开。
