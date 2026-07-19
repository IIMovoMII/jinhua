# 项目文件索引

这是 Jinhua 的逐文件导航。日常修改先读 [AGENTS.md](AGENTS.md) 和 [PROJECT_RULES.md](PROJECT_RULES.md)；本索引用于确认文件职责，不要求每次任务全量阅读。

## 快速定位

| 任务 | 先读 | 再读 |
| --- | --- | --- |
| Skill 方法论流程 | `SKILL.md` | `references/data-policy.md`、`references/maintenance.md` |
| 中文用户说明 | `README.md` | `references/zh-CN/` |
| Codex 触发层 | `hooks/codex-hooks.json` | `hooks/codex_*.py`、`references/hook-integration.md`、`scripts/jinhua.py` 的触发层函数 |
| Claude Code 适配 | `hooks/hooks.json` | `adapters/README.md`、`references/hook-integration.md` |
| 核心账本/闭环 | `scripts/jinhua.py` | `SKILL.md`、`references/cli-usage.md` |
| 数据结构 | `references/operator-json-schema.md` | `references/data-policy.md`、`scripts/jinhua.py` 的 validate 函数 |
| 插件发布 | `.codex-plugin/plugin.json` | `.agents/plugins/marketplace.json`、`CONTRIBUTING.md` |
| 文件归属/结构调整 | `PROJECT_RULES.md` | 本文件、`PROJECT_MAP.md` |

## Active 文件

### 控制面和用户文档

| 文件 | 职责 |
| --- | --- |
| `SKILL.md` | 英文 active control plane；定义触发边界、信号记录、聚类、提案、用户确认和全局晋升规则。 |
| `SKILL.zh-CN.md` | 面向中文用户的 Skill 运行逻辑说明，不替代 `SKILL.md`。 |
| `README.md` | 中文默认入口，解释产品形态、三道触发闸门、命令、数据和边界。 |
| `README.en.md` | README 的英文辅助版本。 |
| `docs/jinhua-logic.html` | 静态可视化说明页；用于人类阅读，不是运行入口，也不覆盖 Hook 协议细节。 |
| `CHANGELOG.md` | 英文历史变更记录。 |
| `CHANGELOG.zh-CN.md` | 中文历史变更记录。 |
| `PROJECT_MAP.md` | 英文产品形态和目录概览。 |
| `PROJECT_MAP.zh-CN.md` | 中文产品形态和目录概览。 |

### CLI、核心闭环和测试

| 文件 | 职责 |
| --- | --- |
| `scripts/jinhua.py` | 唯一 CLI：运行态初始化、信号、聚类、全局导入、提案、用户确认结果、压缩、验证，以及只读触发层入口。 |
| `scripts/test_trigger_layer.py` | 输入分类、项目根解析、周期 Stop、调用保护、输出协议和旧兼容命令测试。 |
| `scripts/test_adapters.py` | Claude Code、OpenClaw、Hermes、TRAE、WorkBuddy 适配层冒烟测试。 |
| `data/crystallized-operators.jsonl` | 随项目发布的 operator 种子数据；不是当前项目的运行态账本。 |

### Codex 和其他宿主触发层

| 文件 | 职责 |
| --- | --- |
| `hooks/codex-hooks.json` | Codex 插件 manifest 引用的三个 Hook 定义。 |
| `hooks/codex_user_prompt_submit.py` | UserPromptSubmit 薄 wrapper，转发输入 payload。 |
| `hooks/codex_post_tool_use.py` | PostToolUse 薄 wrapper，转发工具调用 payload。 |
| `hooks/codex_stop.py` | Stop 薄 wrapper，转发输出状态和周期检查 payload。 |
| `hooks/hooks.json` | Claude Code 原生 Hook 适配，复用上面三个 wrapper。 |
| `adapters/README.md` | 宿主适配范围和边界。 |
| `adapters/openclaw/openclaw.plugin.json` | OpenClaw 插件包装清单。 |
| `adapters/openclaw/skills/jinhua/SKILL.md` | OpenClaw Skill 入口。 |
| `adapters/hermes/skills/jinhua/SKILL.md` | Hermes Skill 入口。 |
| `adapters/trae/skills/jinhua/SKILL.md` | TRAE Skill 入口。 |
| `adapters/workbuddy/skills/jinhua/SKILL.md` | WorkBuddy Skill 入口。 |
| `skills/jinhua/SKILL.md` | Codex 插件内的薄 Skill 入口，指向根目录权威流程。 |

### 详细参考

| 文件 | 职责 |
| --- | --- |
| `references/cli-usage.md` | CLI 命令、参数和闭环调用顺序。 |
| `references/data-policy.md` | 可记录/不可记录的数据和本地/全局边界。 |
| `references/hook-integration.md` | Codex 三道触发闸门、Hook 协议、信任边界和宿主适配。 |
| `references/maintenance.md` | 长期维护、文档同步、架构和打包规则。 |
| `references/operator-json-schema.md` | operator 种子和信号结构约定。 |
| `references/zh-CN/cli-usage.md` | CLI 中文解释。 |
| `references/zh-CN/data-policy.md` | 数据政策中文解释。 |
| `references/zh-CN/glossary.md` | `cycle`、`cluster_key`、`verification_path` 等术语入口。 |
| `references/zh-CN/hook-integration.md` | 触发层中文解释。 |
| `references/zh-CN/maintenance.md` | 维护规则中文解释。 |
| `references/zh-CN/operator-json-schema.md` | 数据结构中文解释。 |

### 插件、开源和工程文件

| 文件/目录 | 职责 |
| --- | --- |
| `.codex-plugin/plugin.json` | Codex 插件清单，声明 Skill 和 Codex Hook。 |
| `.agents/plugins/marketplace.json` | Codex 个人 marketplace 的公开发现入口。 |
| `.claude-plugin/plugin.json` | Claude Code 插件清单。 |
| `.claude-plugin/marketplace.json` | Claude Code marketplace 清单。 |
| `.github/ISSUE_TEMPLATE/` | GitHub Issue 模板。 |
| `.github/PULL_REQUEST_TEMPLATE.md` | GitHub PR 检查项和说明模板。 |
| `.editorconfig` | 编辑器基础格式。 |
| `.gitattributes` | Git 属性。 |
| `.gitignore` | 运行态、缓存、归档和本地文件排除规则。 |
| `LICENSE` | MIT 许可证。 |
| `CONTRIBUTING.md` / `CONTRIBUTING.en.md` | 中英文贡献指南。 |
| `CODE_OF_CONDUCT.md` / `CODE_OF_CONDUCT.en.md` | 中英文行为准则。 |
| `SECURITY.md` / `SECURITY.en.md` | 中英文安全政策。 |

## 不要当作源码读取

| 目录 | 说明 |
| --- | --- |
| `.jinhua/` | 当前项目的本地信号、聚类、提案、应用记录和触发层运行态；保留使用，但不作为项目实现依据，也不提交。 |
| `global-data/` | 个人全局晋升运行态；保留使用，但不打包、不提交。 |
| `.archive/` | 历史兼容文件和可再生缓存的本地归档；不运行、不提交，除非任务明确要求恢复历史。 |
| `__pycache__/`、`*.pyc` | Python 可再生缓存；不作为源码依据。 |

## 变更后同步规则

- 只改实现细节：同步对应测试；如果用户可见行为变化，再同步 README、SKILL 和中英文镜像。
- 改入口、目录、文件职责或架构边界：按需同步 `AGENTS.md`、`PROJECT_RULES.md`、本索引、`PROJECT_MAP` 和相关 reference。
- 改数据字段或验证规则：同步 schema、数据政策和 `validate` 测试。
- 不要因为每次小修改而机械更新全部导航文件。
