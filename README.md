# jinhua

语言：简体中文 | [English](README.en.md)

`jinhua` 是给 Codex、Claude Code 等支持 Skill 的编程智能体（Agent）使用的本地工具。它做一件事：把你在真实项目里反复纠正、反复验证出来的“工作方法”，整理成可以复用、可以进化的 Skill 规则。

它不会把每次聊天都记下来，也不会偷偷改 Skill。它只记录脱敏后的方法论信号；只有证据足够强、能写成明确提案时，才请用户做一次确认。

确认入口现在是“带落点的确认”：

```text
Project Rule / Skill Patch / Personal Global Skill / No / Revision
```

- `Project Rule`：作为当前项目的轻量规则采纳。
- `Skill Patch`：增强某个具体的已有本地 Skill。
- `Personal Global Skill`：做成个人全局 Skill，或面向所有项目生效的规则。
- `No`：拒绝，并让这类提案暂时冷却。
- `Revision`：先按你的意见修改，再重新确认。

中文运行逻辑图见：[docs/jinhua-logic.html](docs/jinhua-logic.html)。

## 它解决什么

很多智能体（Agent）用久了会遇到同一个问题：你反复教它某种做法，但这些经验很难稳定沉淀到 Skill 里。`jinhua` 的目标就是把这个过程做成闭环：

```text
cycle
-> log-signal
-> cycle
-> propose 或 global-propose
-> 用户确认
-> apply/reject
-> cycle
-> validate
```

这里的几个英文词是命令名，不能翻译：

- `cycle`：跑一次自动检查。它会初始化运行态、统计本地信号、导入全局层，并提示下一步。
- `log-signal`：记录一条可复用的方法论信号。
- `propose`：为当前项目里的成熟信号创建提案。
- `global-propose`：为跨项目重复出现的方法创建提案。
- `apply/reject`：记录用户采纳或拒绝。
- `validate`：检查运行态数据有没有坏。

## 唤醒机制

`jinhua` 不是后台服务，不会一直监听所有对话。它的自动调用分两步：

1. 宿主 agent 平时只看到 `SKILL.md` 里的 `name` 和 `description`，token 成本很低。
2. 当用户纠正工作流、反复出现同类方法、修复了可迁移失败，或说“记住这个 / 沉淀一下 / 写进 Skill / 所有项目都这样”时，agent 才加载完整 Skill，并先运行 `cycle`。

这意味着：没提到 `jinhua` 也可以被调用，但前提是当前任务真的出现了方法论信号。普通 bug、一次性偏好、本地路径、临时命令不会触发，这是为了少打扰、少耗 token。

如果宿主 agent 支持前置路由，可以先跑只读粗筛：

```bash
python <jinhua-dir>/scripts/jinhua.py wake-check --text "<latest user message>" --json
```

`wake-check` 只判断是否应该优先路由到 jinhua，不记录用户原文，也不替你生成经验。真正的记录、聚类和提案仍然从 `cycle` 开始。

## 判断规则

`jinhua` 只记录可复用的方法论信号。能记录的经验，至少要能写成未来的 `trigger`（什么时候用）和 `action`（怎么做）。

满足下面任一情况，才考虑记录：

- 用户纠正了推理方向、验证标准或工作流程。
- 同一个方法在当前项目里重复出现。
- 某次失败已经修好，而且失败原因能迁移到以后。
- 某次成功暴露出可复用的做法。
- 用户明确要求记住、沉淀、写进 Skill，或所有项目都这样做。

下面这些不记录：

- 一次性偏好。
- 普通代码 bug。
- 本地路径、临时命令、本地 API 细节。
- 只对当前对话有用的经验。

强度（`strength`）这样打分：

- `1`：普通观察。
- `2`：明确用户纠正，或同类模式重复出现。
- `3`：高成本失败、反复返工，或用户明确要求沉淀。

本地触发提案：

- 同一聚类至少 3 条信号，或
- 总强度至少 5，或
- 用户明确要求现在沉淀，或
- 出现可复用且紧急的高成本失败。

全局触发提案：

- 先归到同一个规范化方法指纹（`method_fingerprint`）。
- 默认路径：3 个项目、5 条证据、总强度 7。
- 快速路径：2 个项目、总强度 6，并且有强纠正或高强度证据。

落点按这个顺序判断：

1. `personal_global_skill`：用户要求所有项目生效、要求新建独立 Skill、方法本身是独立工作流，或全局证据已经足够。
2. `skill_patch`：经验明显属于已有本地 Skill；jinhua 会推荐具体 Skill 和路径。
3. `project_rule`：当前项目需要，但还不适合做成全局 Skill，也不适合改已有 Skill。
4. 其他情况：不写入。

如果落点是 `project_rule`，jinhua 会给出 `recommended_project_rule_file`。它优先推荐项目里已经存在的规则文件，也支持用 `--agent-profile` 或 `JINHUA_AGENT_PROFILE` 指定 `codex`、`claude`、`copilot`、`trae`、`hermes`、`openclaw`、`workbuddy`，未知 agent 会走 generic/custom 兜底。它只推荐，不会自动创建项目规则文件。

## 快速开始

先跑一次自动检查点（cycle）：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

如果任务里出现了明确、可复用的方法论经验，再记录信号：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> log-signal \
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

这段命令里的英文参数是 CLI 接口名。常用参数可以这样理解：

- `--source-type`：信号来源，比如用户纠正（user_correction）或成功经验（success_trace）。
- `--summary`：脱敏后的经验摘要，不要写用户原文。
- `--operator`：经验类型，例如验证路径（verification_path）。
- `--cluster-key`：本地聚类键，格式必须是 `operator:short_method_slug`。
- `--context`：这条经验出现在哪类任务里。
- `--strength`：信号强度，`1` 普通，`2` 明确，`3` 高成本失败或强烈要求沉淀。
- `--trigger`：什么时候应该使用这个方法。
- `--action`：可迁移的核心动作；跨项目合并时优先看它。
- `--transfer-conditions`：适合迁移到哪些场景。
- `--negative-cases`：什么时候不要用。
- `--verification-path`：怎么确认这个方法真的被执行了。
- `--confidence`：0 到 1 的辅助排序分，不是最终裁判。

完整术语表见 [references/zh-CN/glossary.md](references/zh-CN/glossary.md)。

记录后再跑一次：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

## 创建和处理提案

当某个本地聚类成熟后，可以创建提案：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> propose \
  --cluster-key verification_path:read_readme_and_source_before_recommending_projects \
  --decision proposed_edit \
  --placement skill_patch \
  --target "target-skill/SKILL.md / research workflow" \
  --patch "## Source-Backed Recommendations

When recommending reusable external projects for adoption, verify the README and relevant source before claiming usefulness." \
  --risk "Can add work when the user only wants quick pointers."
```

落点分三层：

- `project_rule`：轻量项目规则，适合只在当前项目反复出现的经验。
- `skill_patch`：增强已有本地 Skill。jinhua 会推荐最合适的具体 Skill 和路径，不需要用户自己找。
- `personal_global_skill`：个人全局 Skill 或所有项目规则，适合明确要跨项目生效的经验。

用户选择某个落点后记录采纳：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal \
  --proposal-id <prop_id> \
  --placement skill_patch \
  --target-skill target-skill \
  --target-skill-path "<target-skill-dir>/SKILL.md" \
  --insert-after "## Use This When" \
  --patch "## Source-Backed Recommendations

When recommending reusable external projects for adoption, verify the README and relevant source before claiming usefulness." \
  --summary "Added source-backed recommendation rule"
```

用户选择 `No` 后记录拒绝：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal \
  --proposal-id <prop_id> \
  --reason "Too broad"
```

最后验证数据：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> validate
```

## 常用命令

- `cycle`：自动检查点。
- `wake-check`：只读前置粗筛，判断是否应优先路由到 jinhua。
- `log-signal`：记录方法论信号。
- `list-clusters`：查看本地聚类。
- `propose`：创建本地提案。
- `apply-proposal`：记录本地采纳。
- `reject-proposal`：记录本地拒绝或修订。
- `global-cycle`：手动查看全局晋升层。
- `global-status`：查看全局状态。
- `global-propose`：创建全局提案。
- `global-merge-suggestions`：只读查看可能重复的全局方法。
- `global-apply`：记录全局采纳。
- `global-reject`：记录全局拒绝或修订。
- `compact`：压缩低价值信号。
- `status`：查看本地状态。
- `validate`：验证 JSON/JSONL 数据。

## 数据放在哪里

项目本地运行态：

```text
.jinhua/data/
├── signals.jsonl
├── cluster-state.json
├── proposals.jsonl
├── adopted-edits.jsonl
├── rejected-proposals.jsonl
├── crystallized-operators.jsonl
└── evolution-state.json
```

跨项目晋升层：

```text
<jinhua-dir>/global-data/
├── global-signals.jsonl
├── global-clusters.json
├── global-proposals.jsonl
├── adopted-global-edits.jsonl
├── rejected-global-proposals.jsonl
├── project-index.json
└── global-state.json
```

安装后不需要用户额外配置。`cycle` 会在需要时创建这些文件。

如果一个工作区里混有多个不相关项目或多段对话，请传入 `--project-id <stable-key>`，或设置 `JINHUA_PROJECT_ID`。这个值会先哈希再写入全局层，明文不会保存。

## 设计边界

`jinhua` 故意保持小：

- 不做后台进程（daemon）。
- 不依赖外部数据库。
- 不依赖向量库。
- 不做仪表盘（dashboard）。
- 不把机器学习放进核心闭环。
- 不绕过用户确认。

未来即使加入机器学习，也只能作为可选的排序或检索辅助，不能替代确定性规则、数据验证和用户确认。

## 许可证

MIT。

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)、[SECURITY.md](SECURITY.md) 和 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。英文辅助文档见 [CONTRIBUTING.en.md](CONTRIBUTING.en.md)、[SECURITY.en.md](SECURITY.en.md) 和 [CODE_OF_CONDUCT.en.md](CODE_OF_CONDUCT.en.md)。
