# jinhua

语言：[English](README.md) | 简体中文

`jinhua` 是一个给 Codex 和 Claude Code 使用的小型、确定性的 Skill 进化闭环工具。

它帮助模型在真实任务中发现可复用的方法论信号，把这些信号在当前项目内聚类，再把压缩后的证据晋升到跨项目层。只有当证据足够强、能形成具体 Skill 修改提案时，才打扰用户做一次风险确认。

中文运行逻辑图：[docs/jinhua-logic.html](docs/jinhua-logic.html)

用户确认入口始终只有：

```text
Yes / No / Revision
```

面向用户的对话会跟随用户当前语言。持久化数据、CLI 标识、JSON 字段和生成出来的 Skill 文件可以保持英文，除非用户另有要求。

## 核心闭环

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

`cycle` 是自动检查点。它会初始化缺失的运行态目录，扫描本地聚类，把本地 active 信号导入全局晋升层，提示待处理确认，并为 ready 聚类输出 proposal skeleton。

## 快速开始

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

记录一条结构化、可复用的方法论信号：

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

这些英文命令和字段不要翻译，它们是 CLI/API 名称。含义可以这样理解：

- `cycle`：跑一次自动检查点，初始化、扫描、导入全局层、提示下一步。
- `log-signal`：记录一条可复用的方法论信号。
- `cluster_key` / `--cluster-key`：本地聚类键，格式是 `operator:short_method_slug`。
- `verification_path` / `--verification-path`：验证路径，说明这个方法应该怎么检查。
- `operator`：方法所属的认知操作类型，例如 `verification_path` 表示“先设计验证路径”。
- `strength`：信号强度，`1` 弱，`2` 明确，`3` 高成本失败或强烈要求沉淀。
- `confidence`：0 到 1 的模型信心，只用于排序，不是最终判断。

完整术语表见 [references/zh-CN/glossary.md](references/zh-CN/glossary.md)。

重新运行：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

当本地聚类 ready 后创建提案：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> propose \
  --cluster-key verification_path:read_readme_and_source_before_recommending_projects \
  --decision proposed_edit \
  --target "target-skill/SKILL.md / research workflow" \
  --patch "When recommending reusable external projects for adoption, verify the README and relevant source before claiming usefulness." \
  --risk "Can add work when the user only wants quick pointers."
```

用户说 Yes 后：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> apply-proposal \
  --proposal-id <prop_id> \
  --target-skill target-skill \
  --summary "Added source-backed recommendation rule"
```

用户说 No 后：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> reject-proposal \
  --proposal-id <prop_id> \
  --reason "Too broad"
```

验证运行态：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> validate
```

## 命令列表

主流程：

- `cycle`
- `log-signal`
- `list-clusters`
- `propose`
- `apply-proposal`
- `reject-proposal`
- `global-cycle`
- `global-status`
- `global-propose`
- `global-merge-suggestions`
- `global-apply`
- `global-reject`
- `compact`
- `status`
- `validate`

CLI 只暴露上面的命令。

## 运行态数据

项目本地：

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

全局晋升层：

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

安装后不需要额外设置。`cycle` 会在需要时创建运行态。

如果一个工作区里混有多个不相关项目或对话，传入 `--project-id <stable-key>` 或设置 `JINHUA_PROJECT_ID`，就能把它们的全局晋升证据分开。明文 key 会先哈希再存储。

## 设计边界

- 没有后台 daemon。
- 没有外部数据库。
- 没有向量库。
- 没有 dashboard。
- 没有机器学习核心闭环。
- 不绕过用户确认。
- 面向用户的 Skill 对话跟随用户当前语言；可执行标识保持英文。

这个系统故意保持小。未来即使加入机器学习，也只能作为排序或检索辅助，并且必须是可选层。

## 许可证

MIT.

## 贡献

见 [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)、[SECURITY.zh-CN.md](SECURITY.zh-CN.md) 和 [CODE_OF_CONDUCT.zh-CN.md](CODE_OF_CONDUCT.zh-CN.md)。
