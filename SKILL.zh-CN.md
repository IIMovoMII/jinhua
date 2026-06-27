# jinhua 中文说明

> [SKILL.md](SKILL.md) 是真正被智能体（Agent）读取的英文控制文件；本文件面向中文用户，解释 jinhua 的运行逻辑和使用边界。

## 使命

`jinhua` 把真实项目里反复出现的工作经验，整理成小而明确、经过用户确认的 Skill 改进。

模型负责：

- 发现可复用的方法论信号。
- 把同类信号归到一起。
- 抽象成更通用的方法。
- 起草 Skill 修改提案。
- 调用 CLI 记录和验证数据。

用户只负责最后一道风险确认，确认项尽量用中文展示，括号里保留内部落点值：

- `项目规则 (project_rule)`：作为当前项目的轻量规则采纳。
- `增强已有 Skill (skill_patch)`：增强某个具体的已有本地 Skill。
- `个人全局 Skill (personal_global_skill)`：做成个人全局 Skill，或面向所有项目生效的规则。
- `拒绝 (No)`：拒绝提案，并让对应聚类进入冷却。
- `修订 (Revision)`：记录修改意见，重写后再确认。

## 唤醒边界

这个 Skill 被选中后，还要继续守住边界：

| 场景 | 动作 |
| --- | --- |
| 用户纠正了推理、验证、工作流程、工具选择，或漏掉了本该发生的流程 | 先跑 `cycle`；如果能写成可复用的 `trigger` + `action`，再考虑 `log-signal`。 |
| 同一项目反复出现同一种可复用方法 | 先跑 `cycle`；只记录真正的方法，不记录局部噪音。 |
| 明确失败已经修好，且原因可迁移 | 先完成用户任务，再考虑静默记录 `failure_trace`。 |
| 用户要求记住、沉淀、做成 Skill 或所有项目生效 | 先跑 `cycle`，再按落点阶梯判断。 |
| 一次性 bug、个人偏好、本地路径、临时命令、泛泛记忆 | 跳过 jinhua，不打扰用户。 |

## 交互语言

面向用户的解释要跟随用户当前语言。

- 用户用中文交流，就用中文解释提案、风险和确认问题。
- 用户用阿拉伯语交流，就用阿拉伯语解释提案、风险和确认问题。
- 用户切换语言后，跟随最近一次明确使用的语言。

可执行标识保持英文，避免命令和数据不兼容：

- CLI 命令、参数名、JSON 字段、id、文件路径和 operator id 不翻译。
- 项目经验记录、信号摘要（signal summary）和生成出来的 Skill 文件可以保持英文，除非用户要求中文。
- 用户确认尽量本地化展示。必要时在中文后保留 `project_rule`、`skill_patch`、`personal_global_skill`、`No`、`Revision` 这些内部值，避免 CLI 决策歧义。

## Codex 触发层

Skill 不能像后台服务一样常驻运行。jinhua 所说的“自动”，指的是：当这个 Skill 被选中时先跑 `cycle`；如果作为 Codex 插件安装，薄触发层可以在完整 Skill 加载前帮助宿主识别“用户可能正在纠错”的回合。

新的主触发路径是三道闸门：

1. `UserPromptSubmit`：只做本地输入分类，输出 `none`、`possible_user_correction` 或 `strong_user_correction`。它不记录信号、不运行 `cycle`、不创建提案、不改 Skill。
2. agent 直接调用：用户明确要求沉淀，或 agent 明确看到可复用的工作流、验证标准、工具选择经验时，可以在当前轮直接调用 jinhua。轻量 invocation guard 会防止同一轮重复调用。
3. `Stop`：可选的输出侧轻状态尾巴解析，只解析 `output_state`、`visibility`、`reason`，并检查 invocation guard。它不绕过 jinhua 原有规则，也不绕过用户确认门。

Codex 插件 hook 配置在 `hooks/codex-hooks.json`，会调用：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> codex-user-prompt-submit
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> codex-post-tool-use
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> codex-stop
```

旧的 `wake-check` 和 `hook-user-prompt-submit` 可以为了兼容继续存在，但不再是主触发路径。

当本 Skill 真正被选中时，运行确定性检查点：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> cycle
```

`cycle` 会做五件事：

1. 缺少 `.jinhua/data/` 时自动初始化。
2. 汇总当前项目里的信号、聚类和待确认提案。
3. 把活跃的本地信号导入已安装 Skill 的 `global-data/`。
4. 汇总跨项目方法聚类和全局待确认提案。
5. 为已经成熟的聚类打印提案骨架，包括建议落点（`placement_hint`）和具体本地 Skill 推荐。

在这些时机运行 `cycle`：

- Skill 刚被触发时。
- `log-signal`、`apply-proposal`、`reject-proposal` 等改变账本的命令之后。
- 一个包含明显方法论经验的大任务结束前。

如果 `cycle` 报告已有待确认的本地或全局提案，必须先把一个用户确认门展示出来，再创建新提案或继续 jinhua 这条分支。Hook 可以用 `cycle --json --fail-on-pending-gate`；退出码 `2` 表示必须先向用户展示待确认提案。

## 运行态数据

项目本地运行态：

- `.jinhua/data/signals.jsonl`
- `.jinhua/data/cluster-state.json`
- `.jinhua/data/proposals.jsonl`
- `.jinhua/data/adopted-edits.jsonl`
- `.jinhua/data/rejected-proposals.jsonl`
- `.jinhua/data/crystallized-operators.jsonl`
- `.jinhua/data/evolution-state.json`

跨项目运行态：

- `<jinhua-dir>/global-data/global-signals.jsonl`
- `<jinhua-dir>/global-data/global-clusters.json`
- `<jinhua-dir>/global-data/global-proposals.jsonl`
- `<jinhua-dir>/global-data/adopted-global-edits.jsonl`
- `<jinhua-dir>/global-data/rejected-global-proposals.jsonl`
- `<jinhua-dir>/global-data/project-index.json`
- `<jinhua-dir>/global-data/global-state.json`

原始证据留在项目本地。跨项目层只保存压缩过的方法论证据和哈希后的项目身份。

如果一个工作区里混有多个不相关项目或多段对话，用 `--project-id <stable-key>` 或 `JINHUA_PROJECT_ID` 手动区分；全局层只保存哈希，不保存明文 key。

## 记录信号

只记录清晰、可复用的方法论信号。弱信号通常直接忽略。

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> log-signal \
  --source-type user_correction \
  --summary "Read README and relevant source before recommending reusable GitHub projects" \
  --operator verification_path \
  --cluster-key verification_path:read_readme_and_source_before_recommending_projects \
  --context "researching reusable tools" \
  --strength 2 \
  --trigger "recommending external projects for adoption" \
  --action "verify README and relevant source before recommending" \
  --transfer-conditions "tool, library, Skill, or agent project recommendations" \
  --negative-cases "quick pointers where the user did not ask for adoption judgment" \
  --verification-path "cite README and source files used" \
  --confidence 0.8 \
  --auto-init
```

关键参数：

- `cluster_key`：本地聚类键，格式必须是 `operator:short_method_slug`。
- `strength`：信号强度；`1` 普通观察，`2` 明确纠正或重复模式，`3` 高成本失败、反复返工或用户明确要求沉淀。
- `trigger`：什么时候使用这个方法。
- `action`：可迁移的核心动作，也是全局合并最重要的线索。
- `transfer_conditions`：适合迁移到哪些场景。
- `negative_cases`：什么时候不要用。
- `verification_path`：如何检查这个方法是否真的执行到位。
- `confidence`：0 到 1 的辅助排序分，不是最终判断。

记录后再运行 `cycle`。

静默 `failure_trace` 只记录已经修好的失败，而且失败原因要明显可迁移。

## 写入或跳过的前置判断

不要把每个任务细节都硬塞进提案。多数普通任务信息应该跳过。

只有经验能写成可复用的 `trigger` + `action`，并且满足下面至少一条，才记录：

- 用户纠正了推理方向、验证标准或工作流程。
- 同一个方法在当前项目里反复出现。
- 明确失败已经修好，而且失败原因可迁移。
- 成功路径暴露出可复用的方法。
- 用户明确要求记住、沉淀、写进 Skill，或所有项目都这样做。

一次性偏好、普通代码 bug、本地路径、临时命令、本地 API 细节、只对当前对话有用的经验，都跳过。

## 本地提案确认

同一个项目里的重复，说明“当前项目现在需要”；不要等跨项目证据才给本地沉淀建议。

本地聚类满足任一条件时，可以创建提案：

- 至少 3 条活跃信号。
- 总强度至少 5。
- 用户明确要求“记住、沉淀、写进 Skill、现在就进化”。
- 出现可复用且紧急的高成本失败。

如果 `cycle` 打印出就绪聚类，不要只解释“可以生成提案”。必须立即创建提案，或者明确说明为什么跳过。

以 `cycle` 打印的骨架为起点，补齐落点、目标、改动和风险：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> propose \
  --cluster-key <cluster-key> \
  --decision proposed_edit \
  --placement <project_rule|skill_patch|personal_global_skill> \
  --target "<target Skill / file / insertion location>" \
  --patch "## <简短规则标题>

<完整 Markdown 规则块。>" \
  --risk "<main side effect>"
```

落点判断顺序：

1. `personal_global_skill`：只在用户明确要求所有项目生效、要求新建独立 Skill、这条方法是没有现有 Skill 归属的独立工作流，或全局证据已经足够时使用。
2. `skill_patch`：这条经验属于已有本地 Skill 时使用。agent 必须推荐最合适的具体 Skill 和路径，不能让用户自己去找。
3. `project_rule`：本地兜底。当前项目反复需要，但还不适合改已有 Skill，也不适合做成个人全局 Skill 时使用。

不要把当前项目约定、局部修复习惯、目录结构、框架细节、一次性工具偏好判成 `personal_global_skill`。正常分布应该是：大多数不写入，`project_rule` 较常见，`skill_patch` 较少，`personal_global_skill` 最少。

如果落点是 `project_rule`，使用 CLI 骨架里的 `recommended_project_rule_file` 和 `recommended_project_rule_reason`。它会优先推荐项目里已经存在的规则文件，并支持用 `--agent-profile` 或 `JINHUA_AGENT_PROFILE` 指定 `codex`、`claude`、`copilot`、`trae`、`hermes`、`openclaw`、`workbuddy`，也有 generic/custom 兜底。没有用户确认时，不要自动创建项目规则文件。

给用户展示时，用用户当前语言说明，但保留规范字段：

```markdown
## Skill Evolution Proposal

Trigger:
[为什么达到阈值]

Decision:
proposed_edit / crystallize_experience / merge_rule / experimental_operator / core_operator_promotion / reject

Recommended placement:
project_rule / skill_patch / personal_global_skill

Placement reason:
[为什么这是最小有用落点]

Evidence:
[最多 3 条代表性信号摘要]

Recommended local Skill:
[具体本地 Skill 名称；如果是 skill_patch，这项必填]

Recommended Skill path:
[本地 SKILL.md 路径；如果是 skill_patch，这项必填]

Recommended project rule file:
[项目规则文件；如果是 project_rule，这项必填]

Project rule reason:
[为什么推荐这个文件]

Target:
[目标 Skill / 文件 / 插入位置]

Patch:
[完整 Markdown 规则块，不要只写散句]

Risk:
[主要副作用]

User gate:
Choose: 项目规则(project_rule) / 增强已有 Skill(skill_patch) / 个人全局 Skill(personal_global_skill) / 拒绝(No) / 修订(Revision)
（选择某个落点，就等价于采纳这个落点。）
```

`decision` 值、proposal id、命令名、参数名、文件路径和代码片段保持英文。

## 全局晋升

“跨项目重复”不是简单看次数。只有同时满足这些条件，才算真正值得全局晋升：

- 规范化后的方法指纹（method fingerprint）匹配，优先来自 `operator + action`。
- `trigger` 和 `transfer_conditions` 能证明这个方法确实能迁移。
- 证据来自多个不同项目哈希，不是同一项目反复刷次数。
- 模型判断它通过抽象性、可迁移性、风险和重复性检查。
- 任何全局 Skill 修改前，都必须先给用户看全局提案。

默认全局成熟条件：

- 3 个不同项目、5 条证据、总强度 7。
- 或快速路径：2 个不同项目、总强度 6，并且有重复高强度证据或用户纠正证据。

`global-merge-suggestions` 只读查看相似全局聚类，不修改数据。

## 应用决策

本地提案：

- `项目规则(project_rule)`、`增强已有 Skill(skill_patch)` 或 `个人全局 Skill(personal_global_skill)`：运行 `apply-proposal --placement <chosen-placement>`，然后 `cycle`。
- `拒绝(No)`：运行 `reject-proposal`，然后 `cycle`。
- `修订(Revision)`：运行 `reject-proposal --revision`，按反馈重写后再问。

全局提案：

- `增强已有 Skill(skill_patch)` 或 `个人全局 Skill(personal_global_skill)`：运行 `global-apply --placement <chosen-placement>`，然后 `cycle`。
- `拒绝(No)`：运行 `global-reject`，然后 `cycle`。
- `修订(Revision)`：运行 `global-reject --revision`，按反馈重写后再问。

被拒绝的聚类会进入冷却。除非出现更强证据，不要反复打扰用户。

## 边界

CLI 只做确定性账本工作：初始化、追加信号、聚类、全局导入、记录提案、记录用户确认、合并建议、压缩和验证。

CLI 不判断某个方法是否可迁移、是否值得写入 Skill。这些判断由模型完成，风险由用户确认。
