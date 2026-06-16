# 更新日志

> 本文件是中文更新说明；英文辅助版本见 [CHANGELOG.md](CHANGELOG.md)。

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
