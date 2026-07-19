# Jinhua 运行规则（中文说明）

> 真正参与运行的控制文件是 [SKILL.md](SKILL.md)。本文件帮助中文用户理解其逻辑，不替代英文控制面。

Jinhua 把真实任务中可复用的方法经验，整理成经过用户确认的项目规则或 Skill 改进。

## 被调用后先做什么

Jinhua 被选中后先运行 `cycle`。它会初始化或迁移运行态、汇总本地和全局状态、导入新的跨项目证据，并显示就绪聚类或待确认门。

处理顺序固定为：

1. 先展示已经存在的待确认门。
2. 遇到就绪聚类时，创建一份完整提案，或者明确说明为什么暂不提案。
3. 新经验必须先通过“写入还是跳过”的判断。
4. 每次修改账本后再次运行 `cycle`。

Hook 只负责提醒、每个对话的回合计数和同轮去重，不负责写经验、生成提案、迁移核心数据或修改文件。

## 哪些经验值得记录

经验必须能够写成：

- `trigger`：未来什么情况下应该使用。
- `action`：遇到这种情况具体怎么做。

同时至少满足一项：

- 用户纠正了工作流、推理方向、验证标准、Skill/工具选择或遗漏流程。
- 同一个项目反复出现相同的可复用方法。
- 已修复失败暴露出可迁移原因。
- 成功路径证明了某种方法可以复用。
- 用户明确要求记住、沉淀、写入 Skill 或应用到其他项目。

一次性错误、表达偏好、私人事实、本地路径、临时命令、局部 API 细节和只对当前对话有用的信息应跳过。

Agent 可以记录自己的 `self_observation` 或已修复的 `failure_trace`，但一般应先完成用户任务。

## 信号强度和就绪

`strength` 只有三个等级：

- `1`：普通自我观察。
- `2`：明确用户纠正或重复模式。
- `3`：高成本失败、反复返工或用户明确要求沉淀。

同一项目的同一聚类达到 3 条信号，或总强度达到 5，就进入“就绪”。明确要求立即沉淀或紧急高成本失败可以使用 `log-signal --immediate`。

同一项目就绪已经说明当前项目有需求，不需要等待跨项目证据。

## 轻、中、重落点

按强特征优先判断：

1. `personal_global_skill`：明确要求所有项目生效、新建独立 Skill、方法本身是独立工作流，或已有成熟全局证据。
2. `skill_patch`：属于已有 Skill 的增强。Agent 必须推荐具体 Skill 和路径。
3. `project_rule`：只证明当前项目需要，且没有明确 Skill 归属或全局范围。

正常分布应是：大部分经验不写；项目规则较多；增强已有 Skill 较少；个人全局 Skill 最少。

项目规则支持 Codex、Claude Code、Copilot、TRAE、Hermes、OpenClaw、WorkBuddy 和通用兜底。不存在目标规则文件时，只给出建议，用户确认前不创建。

## 提案和用户确认门

提案必须来自就绪聚类，并包含：

- 具体目标；
- 带标题的完整 Markdown 修改块；
- 具体风险；
- 代表性证据；
- 推荐落点和理由；
- `skill_patch` 的具体 Skill/路径，或 `project_rule` 的具体规则文件。

中文确认门是：

```text
项目规则(project_rule)
增强已有 Skill(skill_patch)
个人全局 Skill(personal_global_skill)
拒绝(No)
修订(Revision)
```

“修订”会记录用户反馈、改写提案并再次询问。“拒绝”会让聚类进入冷却；收到 5 条新的同类信号后才重新允许提案。

如果用户改选另一种落点，先修订提案，使所有者、目标、修改块和风险与新落点一致，再执行修改。

用户采纳后，Agent 必须先用宿主原生编辑工具完成修改并验证，然后再调用 `apply-proposal` 或 `global-apply` 记录实际目标和修改摘要。CLI 本身不再写文件，也不能在修改失败时记录采纳。

## 跨项目晋升

`cycle` 会把项目本地信号压缩后导入全局层，只保存哈希化项目身份，不保存原始项目路径。

同类方法优先由规范化的 `operator + action` 生成 `method_fingerprint`。Agent 仍负责判断不同表述是否真的是同一方法。

普通全局就绪条件：

```text
3 个项目 + 5 条证据 + 总强度 7
```

快速路径：

```text
2 个项目 + 总强度 6
+ 至少 2 条高强度证据或用户纠正
```

全局提案只会落到“增强已有 Skill”或“个人全局 Skill”，并且仍需用户确认。

## 语言和隐私

Jinhua 跟随用户当前语言进行解释、展示风险和询问确认。命令、参数、JSON 字段、ID、路径、operator 和 placement id 保持英文。

原始证据留在项目本地；全局层只保存压缩方法和哈希身份。不要记录用户原文、凭证、私人路径或敏感项目标识。

## 按需参考

- 命令和状态变化：[references/zh-CN/cli-usage.md](references/zh-CN/cli-usage.md)
- 数据和隐私：[references/zh-CN/data-policy.md](references/zh-CN/data-policy.md)
- 运行态字段：[references/zh-CN/runtime-schema.md](references/zh-CN/runtime-schema.md)
- Hook 和宿主适配：[references/zh-CN/hook-integration.md](references/zh-CN/hook-integration.md)
- 维护规则：[references/zh-CN/maintenance.md](references/zh-CN/maintenance.md)
