# Hook 与平台集成

> 英文 [../hook-integration.md](../hook-integration.md) 是主版本；本文件是中文镜像。

`cycle` 是自动检查点。

CLI 不作为 daemon 运行。平台可以调用它，但不能改变安全模型。

## Codex

Codex 应调用：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

在触发 Skill 的开头、`log-signal` 后、proposal apply/reject 后，以及包含大量方法论工作的任务结束前使用。

Skill 安装后，Codex 不需要用户额外设置。`cycle` 会初始化本地和全局运行态。

## Claude Code

可选 hooks 可以调用：

- `cycle`
- `cycle --json`
- `validate`

只有当平台能提供脱敏字段时，hooks 才能调用 `log-signal`。Hooks 不能保存用户原文。

## 安全规则

- 不要自动应用 Skill 修改。
- 不要绕过 Yes / No / Revision。
- 不要保存用户原文。
- 不要把原始项目路径复制到全局记录。
- 不要让 hooks 负责方法论判断。
- 不要把 CLI 输出当成可迁移性的最终证明。
