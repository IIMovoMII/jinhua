# 维护规则

> 英文辅助版本见 [../maintenance.md](../maintenance.md)。

Jinhua 的稳定形态是：精简 Skill、单文件标准库 CLI、薄宿主触发适配。除非真实运行数据证明必须拆分，否则保持这个形态。

日常先读 `AGENTS.md`；涉及文件归属或结构时，再读 `PROJECT_RULES.md` 和 `PROJECT_INDEX.md`。

## 文件职责

- `SKILL.md`：实际运行控制面，保持简短。
- `SKILL.zh-CN.md`：中文说明，不替代控制面。
- `scripts/jinhua.py`：唯一 CLI 和确定性账本实现。
- `hooks/codex-hooks.json`、`hooks/codex_*.py`：Codex 触发层。
- `hooks/hooks.json`：复用同一 wrapper 的 Claude Code 适配。
- `references/cli-usage.md`：命令契约。
- `references/data-policy.md`：记录和隐私边界。
- `references/runtime-schema.md`：当前结构与迁移。
- `references/hook-integration.md`：触发层和宿主协议。
- `adapters/`：只放宿主包装。

现有主题文件能承载的内容，不要再新建 reference。

## CLI 边界

CLI 可以：

- 初始化和迁移运行态；
- 记录已经通过筛选的信号；
- 更新精确本地/全局聚类；
- 推荐落点所有者和项目规则文件；
- 创建完整的用户确认提案；
- 记录修订、拒绝和已验证采纳；
- 验证运行态。

CLI 不能：

- 最终判断语义可迁移性；
- 自动模糊合并方法；
- 写入用户批准的 Skill 或规则文件；
- 保存用户原文；
- 执行网页搜索；
- 作为后台进程运行。

已经写入的信号永久保留。弱信号和不安全内容必须在写入前拒绝。

## 触发层边界

Hook 可以做本地纠错分类、读取就绪/待确认状态、统计回合、固定每 8 轮提醒，以及写调用保护运行态。

Hook 不能迁移核心 schema、写信号、创建提案、记录确认结果、修改文件，也不能每条消息都跑完整 `cycle`。

## 中文与英文

- 中文公开文档是默认入口。
- 英文镜像要同步用户可见行为。
- CLI 命令、参数、JSON 字段、operator id 和 placement id 不翻译。
- 稳定英文标识在 `references/zh-CN/glossary.md` 中解释。
- 用户确认门和说明跟随用户当前语言。

## 架构约束

没有真实数据和明确设计决定时，不添加后台进程、外部数据库、向量库、图数据库、仪表盘、多智能体流程或第二套经验账本。

## 打包与隐私

不得打包或提交：

- `.jinhua/`；
- `global-data/`；
- `.claude/`；
- `.archive/`；
- `__pycache__/` 和 Python 字节码；
- 本地权限文件或生成压缩包。

## 必须验证

```bash
python scripts/test_core_loop.py
python scripts/test_trigger_layer.py
python scripts/test_adapters.py
python -m py_compile scripts/jinhua.py hooks/codex_user_prompt_submit.py hooks/codex_post_tool_use.py hooks/codex_stop.py
python scripts/jinhua.py --project-root <project-root> validate
git diff --check
```

schema 变化必须同步 `references/runtime-schema.md` 和中文镜像；触发层变化必须同步 Hook 测试和中英文 Hook 文档。

每次发布 Skill/插件改动都要完成：验证、plugin-creator cachebuster/reinstall、本机 enabled 检查、提交和推送。
