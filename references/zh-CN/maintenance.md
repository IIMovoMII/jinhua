# 维护规则

> 英文 [../maintenance.md](../maintenance.md) 是主版本；本文件是中文镜像。

这个项目是一个小型 Skill + 单文件 CLI。除非真实使用证明有必要，否则保持这个形态。

## 文件规则

- `SKILL.md` 是控制面，不是知识库。
- `SKILL.zh-CN.md` 是中文说明，不替代英文控制面。
- `README.md` 是英文用户指南。
- `README.zh-CN.md` 是中文用户指南。
- `PROJECT_MAP.md` 是导航地图。
- `references/` 主目录保持精简。
- `references/zh-CN/` 保存中文镜像和术语表。
- 如果内容能放进现有文件，不要新增 reference 文件。

## CLI 规则

只要工作流仍然清晰，就保持 `scripts/jinhua.py` 为单文件。

CLI 可以：

- 初始化运行态。
- 记录结构化 signals。
- 更新本地 clusters。
- 导入全局晋升 records。
- 输出 proposal skeletons。
- 记录用户确认结果。
- 只读建议全局 merge candidates。
- 压缩和验证数据。

CLI 不能：

- 做最终可迁移性判断。
- 绕过用户确认自动应用 Skill 修改。
- 存储用户原文。
- 执行网页搜索。
- 作为 daemon 运行。
- 把机器学习作为必需核心依赖。

## 中文镜像规则

- 英文文档是 canonical source。
- 修改英文语义时，检查对应中文镜像是否需要同步。
- CLI 命令、参数名、JSON 字段、operator id 不翻译。
- 中文文档负责解释这些英文名的含义。
- `references/zh-CN/glossary.md` 是中文用户理解参数的入口。
- 面向用户的 Skill 对话应跟随用户当前语言。
- 持久化数据、schema 字段、命令名和生成出来的 Skill 文件可以保持英文，除非用户另有要求。

## 架构规则

不要添加：

- daemon
- 外部数据库
- 向量库
- 图数据库
- dashboard
- 机器学习核心闭环
- multi-agent workflow

只有真实运行数据出现可测量瓶颈时，才重新考虑架构。

## 打包规则

不要打包：

- `.jinhua/`
- `global-data/`
- `.claude/`
- `skill.zip`
- `__pycache__/`
- 本地权限文件

Schema 变更必须更新英文和中文 schema 文档，并通过 `validate`。
