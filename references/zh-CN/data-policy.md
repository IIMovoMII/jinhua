# 数据政策

> 英文 [../data-policy.md](../data-policy.md) 是主版本；本文件是中文镜像。

只记录脱敏后的方法论信号。本 Skill 不是用户记忆、项目记忆或聊天记录。

## 可以记录

- 脱敏后的方法论摘要。
- 抽象方法动作。
- 触发条件。
- 迁移条件。
- 反例或禁用场景。
- 验证路径。
- operator id。
- strength 和可选 confidence。
- proposal gate 结果。
- 项目身份哈希。
- 压缩后的全局晋升证据。
- 哈希前的可选显式项目身份。

## 不能记录

- 用户身份信息。
- 联系方式、账户、密钥、token 或凭证。
- 完整用户原文。
- 完整对话。
- 客户名称、公司秘密或敏感项目标识。
- 私人偏好。
- 普通 bug 修复事实。
- 全局晋升记录里的原始项目路径。
- 全局晋升记录里的明文显式项目 id。

## 记录规则

如果无法安全脱敏，就不要记录。如果信号很弱，忽略它，而不是写入一个弱 reject。

高质量信号通常包含：

- 可复用方法。
- 清晰触发条件。
- 合理迁移条件。
- 已知反例或风险。
- 验证路径。

## 本地与全局

项目本地 `.jinhua/data/` 可以保存更完整的 signal card。

全局 `global-data/` 只能保存压缩晋升证据：

- method fingerprint
- method key
- 脱敏 summary
- signal-card fields
- operator
- source type
- strength
- 可选 confidence
- 项目身份哈希

不要把本地原始证据复制到全局状态。

使用 `--project-id` 或 `JINHUA_PROJECT_ID` 时，先哈希显式身份，只保存哈希和身份来源。

## 写入边界

自动积累不是后台任务。只有 Skill 被调用且模型调用 CLI 时，才会写入文件。

如果文件无法写入，说明持久化失败，并给出本来会写入的记录。
