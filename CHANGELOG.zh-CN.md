# CHANGELOG 中文说明

> 英文 [CHANGELOG.md](CHANGELOG.md) 是主版本；本文件是中文镜像。

## 2026-06-15 公开发布

- 发布 `jinhua`，一个用于用户确认式 Skill 进化的紧凑 Skill + CLI。
- 新增英文和中文文档：`README.md`、`SKILL.md`、`PROJECT_MAP.md`，以及对应的 `zh-CN` 镜像。
- 新增 `references/zh-CN/`，包含 CLI、schema、data policy、hook、maintenance 和术语表。
- 保留英文文档作为 canonical source，中文文档作为一等镜像。
- 保留 CLI 命令、参数名、JSON 字段和 operator id 的英文原名，并在中文术语表中解释含义。

## 产品功能

- 把 `cycle` 作为唯一自动检查点：本地初始化、本地状态、全局导入、全局状态、pending gates 和 ready proposal skeleton 都从这里进入。
- 给 `log-signal` 增加结构化 signal card 字段：`trigger`、`action`、`transfer_conditions`、`negative_cases`、`verification_path` 和 `confidence`。
- 改进全局 method fingerprint：优先使用 `operator + action`，再回退到 `cluster_key` 和 summary。
- 新增 `global-merge-suggestions`，用于只读地查看可能重复的全局方法。

## 产品边界

当前项目主线稳定可用：

- 确定性 CLI
- 项目本地 signals
- 全局晋升 memory
- proposal skeletons
- 用户确认后的 apply/reject
- validate

后续修改应主要限于 bug 修复、真实使用后的阈值微调、验证覆盖和文档压缩。
