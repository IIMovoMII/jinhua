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

用户只负责最后一道风险确认，但不再只有简单的 `Yes / No`：

- `Project Rule`：作为当前项目的轻量规则采纳。
- `Skill Patch`：增强某个具体的已有本地 Skill。
- `Personal Global Skill`：做成个人全局 Skill，或面向所有项目生效的规则。
- `No`：拒绝提案，并让对应聚类进入冷却。
- `Revision`：记录修改意见，重写后再确认。

## 什么时候该触发

只有当前任务出现“以后还可能用到的方法”时，才应该用 jinhua。典型场景包括：

- 用户纠正了模型的推理方向、验证标准或工作流程。
- 一个任务成功，是因为某个可迁移的方法起了作用。
- 一个任务失败或返工，是因为出现了重复的推理错误。
- 几条看似零散的提示，其实表达的是同一个高层方法。
- 某个 Skill 规则缺失、重复、过宽、过窄或成本太高。
- 用户要求让 Skill 进化更自动、更闭环、更聪明。

不要用它记录一次性事实、个人偏好、私人记忆、普通 bug 修复，或泛泛的 prompt 模板。

## 交互语言

面向用户的解释要跟随用户当前语言。

- 用户用中文交流，就用中文解释提案、风险和确认问题。
- 用户用阿拉伯语交流，就用阿拉伯语解释提案、风险和确认问题。
- 用户切换语言后，跟随最近一次明确使用的语言。

可执行标识保持英文，避免命令和数据不兼容：

- CLI 命令、参数名、JSON 字段、id、文件路径和 operator id 不翻译。
- 项目经验记录、信号摘要（signal summary）和生成出来的 Skill 文件可以保持英文，除非用户要求中文。
- 用户确认可以本地化展示，但必须同时保留 `Yes`、`No`、`Revision`，避免误判。选择某个落点，就等价于对这个落点说 `Yes`。

## 自动检查点

Skill 不能像后台服务一样自己常驻运行。jinhua 所说的“自动”，指的是：只要这个 Skill 被触发，就先跑一次 `cycle`。

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> cycle
```

`cycle` 是确定性检查点，会做五件事：

1. 缺少 `.jinhua/data/` 时自动初始化。
2. 汇总当前项目里的信号、聚类和待确认提案。
3. 把活跃的本地信号导入已安装 Skill 的 `global-data/`。
4. 汇总跨项目方法聚类和全局待确认提案。
5. 为已经成熟的聚类打印提案骨架，包括建议落点（`placement_hint`）和具体本地 Skill 推荐。

在这些时机运行 `cycle`：

- Skill 刚被触发时。
- `log-signal`、`apply-proposal`、`reject-proposal` 等改变账本的命令之后。
- 一个包含明显方法论经验的大任务结束前。

如果 `cycle` 报告已有待确认的本地或全局提案，先处理用户确认，再创建新提案。

## 运行态数据

项目本地运行态：

- `.jinhua/data/signals.jsonl`
- `.jinhua/data/cluster-state.json`
- `.jinhua/data/proposals.jsonl`
- `.jinhua/data/adopted-edits.jsonl`
- `.jinhua/data/rejected-proposals.jsonl`
- `.jinhua/data/evolution-state.json`

跨项目运行态：

- `<jinhua-dir>/global-data/global-signals.jsonl`
- `<jinhua-dir>/global-data/global-clusters.json`
- `<jinhua-dir>/global-data/global-proposals.jsonl`
- `<jinhua-dir>/global-data/adopted-global-edits.jsonl`
- `<jinhua-dir>/global-data/rejected-global-proposals.jsonl`
- `<jinhua-dir>/global-data/project-index.json`

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

## 本地提案确认

同一个项目里的重复，说明“当前项目现在需要”。这时应该先给出本地沉淀建议，不要等跨项目证据。跨项目证据只用于全局晋升。

本地聚类满足任一条件时，可以创建提案：

- 至少 3 条活跃信号。
- 总强度至少 5。
- 用户明确要求“记住、沉淀、写进 Skill、现在就进化”。
- 出现可复用且紧急的高成本失败。

以 `cycle` 打印的骨架为起点，补齐落点、目标、改动和风险：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> propose \
  --cluster-key <cluster-key> \
  --decision proposed_edit \
  --placement <project_rule|skill_patch|personal_global_skill> \
  --target "<target Skill / file / insertion location>" \
  --patch "<1-3 sentence patch>" \
  --risk "<main side effect>"
```

三个落点：

- `project_rule`：轻量项目规则。适合“这个项目反复需要”，但还没有跨项目证据的经验。
- `skill_patch`：增强已有本地 Skill。agent 必须推荐最合适的具体 Skill 和路径，不能让用户自己去找。
- `personal_global_skill`：个人全局 Skill 或所有项目规则。适合用户明确要求全局生效，或全局晋升证据已经足够。

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

Target:
[目标 Skill / 文件 / 插入位置]

Patch:
[1 到 3 句话说明要怎么改]

Risk:
[主要副作用]

User gate:
Choose: Project Rule / Skill Patch / Personal Global Skill / No / Revision
（选择某个落点，就等价于 Yes 这个落点。）
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

- `Project Rule`、`Skill Patch` 或 `Personal Global Skill`：运行 `apply-proposal --placement <chosen-placement>`，然后 `cycle`。
- `No`：运行 `reject-proposal`，然后 `cycle`。
- `Revision`：运行 `reject-proposal --revision`，按反馈重写后再问。

全局提案：

- `Skill Patch` 或 `Personal Global Skill`：运行 `global-apply --placement <chosen-placement>`，然后 `cycle`。
- `No`：运行 `global-reject`，然后 `cycle`。
- `Revision`：运行 `global-reject --revision`，按反馈重写后再问。

被拒绝的聚类会进入冷却。除非出现更强证据，不要反复打扰用户。

## 边界

CLI 只做确定性账本工作：初始化、追加信号、聚类、全局导入、记录提案、记录用户确认、合并建议、压缩和验证。

CLI 不判断某个方法是否智能、是否可迁移、是否值得写入 Skill。这些判断由模型完成，风险由用户确认。

机器学习不是核心闭环。未来即使加入，也只能辅助排序或候选检索，不能绕过确定性规则、提案审查、数据验证和用户确认。

## 成功标准

完整闭环应当满足：

1. 发现一条可复用的方法论信号。
2. `cycle` 确认状态和待确认事项。
3. 信号被静默记录并进入聚类。
4. 成熟聚类产生提案骨架。
5. 模型创建紧凑的 Skill 进化提案，并推荐最小有用落点。
6. 如果落点是 `skill_patch`，模型必须推荐具体本地 Skill 和路径。
7. 用户选择 `Project Rule`、`Skill Patch`、`Personal Global Skill`、`No` 或 `Revision`。
8. 采纳或拒绝结果被记录。
9. 采纳的变化以最小有用改动应用或记录。
10. 跨项目晋升使用不同项目证据，并走同一个用户确认门。
