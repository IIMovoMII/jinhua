# 项目规范

这是一个“Skill + 单文件 CLI + 薄触发层”的项目。规范的目标是保持主线清晰、运行态和发布文件分离、让后续智能体能快速定位正确文件。

## 文件边界

- `SKILL.md`：英文 active control plane，定义 Skill 被选中后的方法论流程。
- `README.md`：中文默认用户入口；`README.en.md`：英文辅助版本。
- `scripts/jinhua.py`：唯一 CLI。核心账本逻辑和触发层入口都在这里，但两者必须保持边界清楚。
- `hooks/codex-hooks.json`、`hooks/codex_user_prompt_submit.py`、`hooks/codex_post_tool_use.py`、`hooks/codex_stop.py`：Codex 触发层。
- `hooks/hooks.json`：Claude Code 的薄适配层，复用 Codex wrapper，不创建第二套逻辑。
- `data/`：随项目发布的 operator 种子数据。
- `references/`：按主题保存详细规则、数据政策、CLI 和宿主适配说明。
- `adapters/`：OpenClaw、Hermes、TRAE、WorkBuddy 等宿主的包装，不改变核心闭环。
- `PROJECT_INDEX.md`：逐文件导航；`PROJECT_MAP.md`：产品形态和目录概览。

## 运行态与归档

- `.jinhua/` 保存项目本地经验和触发层运行态，必须保留在本机但不得提交。
- `global-data/` 保存个人全局晋升运行态，必须保留在本机但不得提交。
- `.archive/` 只保存本地历史或可再生文件，不参与运行、不作为实现依据，也不得提交。
- `__pycache__/`、`.pyc` 等缓存可以清理或放入 `.archive/`，不能成为源码依赖。

## 修改约束

- 不绕过 `signals -> clusters -> proposals -> user gate`、placement ladder 或用户确认门。
- 触发层可以改输入分类、项目根解析、调用去重、周期检查和宿主协议适配；不得在 Hook 中写 `signals`、`proposals` 或新增经验账本。
- 保持 `scripts/jinhua.py` 为单文件，除非真实运行数据证明拆分有必要。
- 不新增后台 daemon、外部数据库、向量库、图数据库或第二套事件/经验状态。
- 用户可见行为变化时，同步中文默认文档和英文辅助文档；CLI 命令、参数、JSON 字段和 operator id 保持英文，并在中文术语表解释。

## 按需更新

- 小型实现修复：更新对应源码和测试即可。
- 入口、架构、文件归属或运行边界变化：同步 `AGENTS.md`、本文件、`PROJECT_INDEX.md`、`PROJECT_MAP` 和相关 references。
- 用户可见行为或数据政策变化：同步 README、SKILL、更新日志和中英文镜像。
- 不要求每次提交都修改这些导航文件，只有规则或结构真的变化时才更新。

## 验收

提交前至少运行：

```bash
python scripts/test_trigger_layer.py
python scripts/test_adapters.py
python -m py_compile scripts/jinhua.py hooks/codex_user_prompt_submit.py hooks/codex_post_tool_use.py hooks/codex_stop.py
git diff --check
```

运行测试产生的运行态和缓存必须留在忽略目录中。

## 发布闸门

每次修改 Skill 项目（源码、SKILL、Hook、插件清单或相关文档）都必须完成同一条链路：

1. 运行上面的验证命令，并检查 `git diff --check`。
2. 使用 `plugin-creator` 的 cachebuster/reinstall 流程更新本机插件；不要只改缓存目录或源文件。
3. 有意图地提交 Git，并推送当前分支到 GitHub。

只更新本地运行态、归档缓存或未进入发布包的临时文件时，不触发这条发布闸门。
