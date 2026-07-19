# 项目文件索引

日常先读 [AGENTS.md](AGENTS.md) 和 [PROJECT_RULES.md](PROJECT_RULES.md)。本索引用于定位权威文件，不要求每次任务全量读取。

## 快速定位

| 任务 | 先读 | 再读 |
| --- | --- | --- |
| Skill 方法论流程 | `SKILL.md` | `references/data-policy.md` |
| 中文用户说明 | `README.md` | `SKILL.zh-CN.md`、`references/zh-CN/` |
| 核心账本与闭环 | `scripts/jinhua.py` | `scripts/test_core_loop.py`、`references/cli-usage.md` |
| Codex 触发层 | `hooks/codex-hooks.json` | `hooks/codex_*.py`、`scripts/test_trigger_layer.py`、`references/hook-integration.md` |
| Claude Code 适配 | `hooks/hooks.json` | `scripts/test_adapters.py`、`adapters/README.md` |
| 数据结构与迁移 | `references/runtime-schema.md` | `scripts/test_core_loop.py`、`references/data-policy.md` |
| 插件发布 | `.codex-plugin/plugin.json` | `.agents/plugins/marketplace.json`、`PROJECT_RULES.md` |
| 文件归属调整 | `PROJECT_RULES.md` | 本文件、`PROJECT_MAP*.md` |

## 控制面和用户文档

| 文件 | 职责 |
| --- | --- |
| `SKILL.md` | 英文 active control plane；只保留运行硬约束和 reference 路由。 |
| `SKILL.zh-CN.md` | 中文运行逻辑说明，不替代控制面。 |
| `README.md` | 中文默认用户入口，说明完整闭环、触发、阈值、落点、迁移和成本。 |
| `README.en.md` | 英文辅助版本。 |
| `docs/jinhua-logic.html` | 中文静态逻辑图，不参与运行。 |
| `CHANGELOG.md` | 英文历史变更。 |
| `CHANGELOG.zh-CN.md` | 中文默认更新日志。 |
| `PROJECT_MAP.md` | 英文产品形态和目录概览。 |
| `PROJECT_MAP.zh-CN.md` | 中文产品形态和目录概览。 |

## CLI、核心闭环和测试

| 文件 | 职责 |
| --- | --- |
| `scripts/jinhua.py` | 唯一 CLI：初始化、迁移、信号、聚类、全局导入、完整提案、确认结果纯记账、状态和验证。 |
| `scripts/test_core_loop.py` | 标准库端到端测试：阈值、提案、确认门、冷却、全局路径、迁移和废弃接口。 |
| `scripts/test_trigger_layer.py` | 纠错分类、项目根解析、ready-attention、调用保护、每会话 8 轮和 Stop 防循环。 |
| `scripts/test_adapters.py` | Claude Code、OpenClaw、Hermes、TRAE、WorkBuddy 包装冒烟测试。 |

## Codex 和宿主适配

| 文件 | 职责 |
| --- | --- |
| `hooks/codex-hooks.json` | Codex 三个 command Hook 定义。 |
| `hooks/codex_user_prompt_submit.py` | 第一道闸门薄 wrapper。 |
| `hooks/codex_post_tool_use.py` | 第二道调用保护薄 wrapper。 |
| `hooks/codex_stop.py` | 第三道固定周期回顾薄 wrapper。 |
| `hooks/hooks.json` | Claude Code 原生 Hook 适配，复用同一 wrapper。 |
| `skills/jinhua/SKILL.md` | Codex 插件内薄 Skill 入口，委托给根目录 `SKILL.md`。 |
| `adapters/README.md` | 各宿主支持范围和边界。 |
| `adapters/openclaw/openclaw.plugin.json` | OpenClaw 插件包装清单。 |
| `adapters/openclaw/skills/jinhua/SKILL.md` | OpenClaw Skill 入口。 |
| `adapters/hermes/skills/jinhua/SKILL.md` | Hermes Skill 入口。 |
| `adapters/trae/skills/jinhua/SKILL.md` | TRAE Skill 入口。 |
| `adapters/workbuddy/skills/jinhua/SKILL.md` | WorkBuddy Skill 入口。 |

## 详细参考

| 文件 | 职责 |
| --- | --- |
| `references/cli-usage.md` | 当前 CLI 命令、参数和状态变化。 |
| `references/data-policy.md` | 写入门、本地/全局边界、隐私与保留策略。 |
| `references/runtime-schema.md` | 本地 3.0、全局 2.0 schema 和迁移规则。 |
| `references/hook-integration.md` | 三道触发闸门、宿主协议和信任边界。 |
| `references/maintenance.md` | 长期维护、打包和发布规则。 |
| `references/zh-CN/cli-usage.md` | CLI 中文解释。 |
| `references/zh-CN/data-policy.md` | 数据政策中文解释。 |
| `references/zh-CN/runtime-schema.md` | 运行态结构和迁移中文解释。 |
| `references/zh-CN/hook-integration.md` | 触发层中文解释。 |
| `references/zh-CN/maintenance.md` | 维护规则中文解释。 |
| `references/zh-CN/glossary.md` | 命令、参数、状态和字段术语表。 |

## 插件、开源和工程文件

| 文件/目录 | 职责 |
| --- | --- |
| `.codex-plugin/plugin.json` | Codex 插件清单，声明 Skill 和 Hook。 |
| `.agents/plugins/marketplace.json` | Codex personal marketplace 发现入口。 |
| `.claude-plugin/plugin.json` | Claude Code 插件清单。 |
| `.claude-plugin/marketplace.json` | Claude Code marketplace 清单。 |
| `.github/ISSUE_TEMPLATE/` | GitHub Issue 模板。 |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR 验证和隐私检查模板。 |
| `.gitignore` | 排除运行态、缓存和本地归档。 |
| `LICENSE` | MIT 许可证。 |
| `CONTRIBUTING*.md` | 中英文贡献指南。 |
| `CODE_OF_CONDUCT*.md` | 中英文行为准则。 |
| `SECURITY*.md` | 中英文安全政策。 |

## 不要当作源码读取

| 目录 | 说明 |
| --- | --- |
| `.jinhua/` | 当前项目本地经验和触发运行态；保留使用，不提交，不作为实现依据。 |
| `global-data/` | 个人全局晋升运行态；保留使用，不打包、不提交。 |
| `.archive/` | 本地历史和可再生文件；不运行、不提交。 |
| `__pycache__/`、`*.pyc` | 可再生 Python 缓存。 |

## 变更后同步

- 改核心字段或状态：同步 runtime schema、数据政策和核心测试。
- 改触发层：同步 Hook 文档、触发测试和宿主适配测试。
- 改入口、目录或职责：按需同步 `AGENTS.md`、`PROJECT_RULES.md`、本索引和项目地图。
- 不机械修改无关文档。
