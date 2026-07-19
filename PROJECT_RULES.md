# 项目规范

Jinhua 是“精简 Skill + 单文件标准库 CLI + 薄宿主触发适配”。目标是让主闭环可审计、运行态与发布文件分离、后续 Agent 能快速找到权威文件。

## 权威边界

- `SKILL.md`：英文 active control plane，定义 Skill 被选中后的流程。
- `SKILL.zh-CN.md`：中文解释，不替代控制面。
- `scripts/jinhua.py`：唯一 CLI，包含确定性核心账本和触发层命令；两者必须保持边界。
- `hooks/codex-hooks.json`、`hooks/codex_*.py`：Codex 三道触发闸门。
- `hooks/hooks.json`：Claude Code 薄适配，复用同一 wrapper。
- `references/`：CLI、数据政策、运行态 schema、Hook 和维护规则。
- `adapters/`：其他宿主包装，不改变核心闭环。
- `PROJECT_INDEX.md`：逐文件导航；`PROJECT_MAP*.md`：产品形态和目录概览。

## 运行态与归档

- `.jinhua/` 保存项目本地经验和触发层运行态，必须保留在本机但不得提交。
- `global-data/` 保存个人全局晋升运行态，必须保留在本机但不得提交。
- `.archive/` 只保存本地历史或可再生文件，不参与运行、不作为实现依据，也不得提交。
- `__pycache__/`、`*.pyc` 等缓存不能成为源码依赖。

## 不可破坏的闭环

- 保持 `signals -> clusters -> proposals -> user gate`。
- 保持本地阈值：3 条信号或总强度 5。
- 保持全局普通阈值和快速路径。
- 保持 `project_rule -> skill_patch -> personal_global_skill` 的落点语义。
- Hook 只能分类、计数、提醒、读取 ready/pending 状态和同轮去重；不得迁移核心数据、写 signals/proposals 或修改文件。
- Hook 判断执行事实时只信任宿主权威控制字段；不得从用户文本、文档、工具输出、错误日志或任意嵌套文本推断，未知 payload 不得改变调用保护状态。
- CLI apply 只记录已经由宿主原生工具完成并验证的修改，不写目标文件。
- 不新增第二套经验账本、后台 daemon、外部数据库、向量库、图数据库或多智能体流程。

## 数据和语言

- 不记录用户原文、凭证、私人路径或敏感项目标识。
- 全局层只保存压缩方法证据和哈希化项目身份。
- 中文公开文档为默认入口；英文辅助文档同步用户可见行为。
- 命令、参数、JSON 字段、operator id 和 placement id 保持英文。

## 按需同步

- 实现修复：更新对应源码和测试。
- 用户可见行为变化：同步 README、SKILL、reference 和中英文镜像。
- 入口、结构或文件职责变化：按需同步 `AGENTS.md`、本文件、`PROJECT_INDEX.md` 和 `PROJECT_MAP*.md`。
- schema 变化：同步中英文 `runtime-schema.md` 和迁移测试。

## 验收

```bash
python scripts/test_core_loop.py
python scripts/test_trigger_layer.py
python scripts/test_adapters.py
python -m py_compile scripts/jinhua.py hooks/codex_user_prompt_submit.py hooks/codex_post_tool_use.py hooks/codex_stop.py
python scripts/jinhua.py --project-root <project-root> validate
git diff --check
```

测试产生的运行态和缓存必须留在忽略目录。

## 发布闸门

每次修改 Skill、CLI、Hook、插件清单或相关文档，都必须完成：

1. 全量验证和隐私扫描。
2. 使用 `plugin-creator` 的 cachebuster/reinstall 流程更新本机。
3. 检查插件 installed/enabled 和 Hook 配置。
4. 提交并推送当前分支。

不得只修改源文件或缓存目录后声称发布完成。
