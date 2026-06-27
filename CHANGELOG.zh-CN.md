# 更新日志

> 本文件是中文更新说明；英文辅助版本见 [CHANGELOG.md](CHANGELOG.md)。

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
