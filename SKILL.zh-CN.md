# jinhua 中文说明

> 英文 [SKILL.md](SKILL.md) 是实际 Skill 控制面；本文件是面向中文用户的翻译说明，不作为 Codex/Claude 的主控文件。

## 使命

把真实任务中反复出现的经验，转化成小而明确、经过用户确认的 Skill 改进。

模型负责发现信号、聚类、抽象、起草提案和调用 CLI。用户只负责风险确认：

- `Yes`：应用或记录这个提案。
- `No`：拒绝提案，并让对应聚类进入冷却。
- `Revision`：记录修改意见，重写提案，再问同一个确认问题。

## 什么时候使用

当前任务出现可复用的方法论信号时使用本 Skill：

- 用户纠正了模型的推理方向、验证标准或工作流程。
- 某个任务成功，是因为一个可迁移的方法起作用。
- 某个任务失败或返工，是因为出现了重复的推理错误。
- 多个低层提示表达了同一个高层方法。
- 某个 Skill 规则缺失、重复、过宽、过窄或成本太高。
- 用户要求让 Skill 进化更自动、闭环或更聪明。

不要把它用于一次性事实、风格偏好、私人记忆、普通 bug 修复或通用 prompt 模板。

## 交互语言

本 Skill 面向用户输出的对话，应跟随用户当前使用的语言。

例子：

- 用户用阿拉伯语交流，就用阿拉伯语解释 proposal、risk 和用户确认。
- 用户用中文交流，就用中文解释 proposal、risk，以及生成 Skill 时给用户看的提示。
- 如果用户切换语言，跟随最近一次明确的用户语言。

持久化数据和可执行标识保持稳定：

- CLI 命令、参数名、JSON 字段、id、文件路径和 operator id 保持英文。
- 项目经验记录、signal summary 和生成出来的 Skill 文件可以保持英文，除非用户另有要求。
- 用户确认门可以本地化展示，但要同时包含规范 token：`Yes`、`No`、`Revision`，避免决策歧义。

## 自动检查点

Skill 本身不能作为真正的后台进程运行。这里的“自动”是指：只要触发本 Skill，就运行 `cycle`。

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> cycle
```

`cycle` 是确定性的检查点：

1. 如果缺少 `.jinhua/data/`，就初始化。
2. 汇总本地 signals、clusters 和 pending gates。
3. 把 active 本地信号导入已安装 Skill 的 `global-data/`。
4. 汇总跨项目 method clusters 和 pending global gates。
5. 为 ready clusters 打印 proposal skeleton 提示。

在触发 Skill 的开头、任何改变账本的命令之后，以及包含明确方法论信号的大任务结束前，都运行 `cycle`。

如果 `cycle` 报告有 pending 本地或全局 proposal，先处理用户确认，再创建新的 proposal。

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

原始证据留在项目本地。跨项目只晋升压缩过的方法论证据和哈希后的项目身份。

如果一个工作区里混有多个不相关项目或对话，使用 `--project-id <stable-key>` 或 `JINHUA_PROJECT_ID` 区分它们；全局层只保存哈希，不保存明文 key。

## 记录信号

只记录清晰、可复用的方法论信号。弱信号通常应该忽略。

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

`cluster_key` 的格式必须是：

```text
operator:short_method_slug
```

`strength` 含义：

- `1`：普通自我观察。
- `2`：明确用户纠正或重复模式。
- `3`：高成本失败、重复返工，或用户明确要求沉淀。

可选 signal card 字段能让跨项目合并更准确：

- `trigger`：这个方法什么时候适用。
- `action`：可复用的方法动作。
- `transfer_conditions`：它可以迁移到哪些场景。
- `negative_cases`：什么时候不要用。
- `verification_path`：如何检查这个方法是否被正确执行。
- `confidence`：0 到 1 的排序信号，不是最终裁判。

记录后运行 `cycle`。

## 本地提案确认

本地 cluster 满足任一条件时生成 proposal：

- 至少 3 条 active signals。
- 总 strength 至少 5。
- 用户明确要求 remember、crystallize、写入 Skill 或现在就 evolve。
- 高成本失败被判断为可复用且紧急。

以 `cycle` 输出的 skeleton 为起点，细化 target、patch 和 risk，然后运行：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <current-project-root> propose \
  --cluster-key <cluster-key> \
  --decision proposed_edit \
  --target "<target Skill / file / insertion location>" \
  --patch "<1-3 sentence patch>" \
  --risk "<main side effect>"
```

给用户展示下面这个结构，但外层说明要使用用户当前对话语言：

```markdown
## Skill Evolution Proposal

Trigger:
[why the threshold was reached]

Decision:
proposed_edit / crystallize_experience / merge_rule / experimental_operator / core_operator_promotion / reject

Evidence:
[up to 3 representative signal summaries]

Target:
[target Skill / file / insertion location]

Patch:
[1-3 sentence patch]

Risk:
[main side effect]

User gate:
Choose: Yes / No / Revision
```

即使外层说明本地化，`decision` 值、proposal id、命令名、参数名、文件路径和代码片段仍保持英文。

## 全局晋升

只有同时满足这些条件，才算真正跨项目重复：

- 规范化后的 method fingerprint 匹配，优先来自 `operator + action`。
- `trigger` 和 `transfer_conditions` 是迁移判断证据，不是硬拆分键。
- 证据来自多个不同项目哈希，而不是同一项目重复刷次数。
- 模型判断这个方法通过抽象性、可迁移性、风险和重复性检查。
- 任何全局 Skill 修改前都必须给用户看 global proposal。

默认全局 ready 条件：

- 3 个不同项目、5 条证据、strength 7。
- 或快速路径：2 个不同项目、strength 6，并且有重复高强度或用户纠正证据。

`global-merge-suggestions` 可以查看相似全局 clusters。它只给建议，不修改数据。

## 应用决策

本地 proposal：

- `Yes`：运行 `apply-proposal`，然后 `cycle`。
- `No`：运行 `reject-proposal`，然后 `cycle`。
- `Revision`：运行 `reject-proposal --revision`，重写后再问。

全局 proposal：

- `Yes`：运行 `global-apply`，然后 `cycle`。
- `No`：运行 `global-reject`，然后 `cycle`。
- `Revision`：运行 `global-reject --revision`，重写后再问。

被拒绝的 clusters 会进入冷却。除非出现更强证据，不要再次打扰用户。

## 边界

CLI 做确定性的账本工作：初始化、追加信号、聚类、全局导入、proposal 记录、用户确认结果、merge suggestion、压缩和验证。

CLI 不判断某个方法是否智能、可迁移或值得写入 Skill。这些判断由模型完成，风险由用户确认。

机器学习不是核心闭环的一部分。未来即使加入，也只能辅助排序或候选检索，不能绕过确定性规则、proposal review、validate 或用户确认。

## 成功标准

完整闭环成功时应满足：

1. 发现一条可复用的方法论信号。
2. `cycle` 确认状态和 pending gates。
3. 信号被静默记录并聚类。
4. ready clusters 产生 proposal skeleton。
5. 模型创建紧凑的 Skill Evolution Proposal。
6. 用户选择 Yes / No / Revision。
7. 采纳或拒绝结果被记录。
8. 采纳的变化以最小有用 patch 应用或记录。
9. 跨项目晋升使用不同项目证据，并走同一个用户确认门。
