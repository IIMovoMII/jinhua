# Hook 与平台集成

> [../hook-integration.md](../hook-integration.md) 是英文主版本；本文件说明中文用户该怎么理解平台集成。

`cycle` 是 jinhua 的自动检查点。平台可以帮忙调用它，但不能改变安全模型。

CLI 不作为后台进程运行，也不应该偷偷写入用户没有确认的 Skill 修改。

## Codex

Codex 触发 jinhua 时，应先调用：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle
```

建议调用时机：

- Skill 刚触发时。
- `log-signal` 后。
- 提案被采纳或拒绝后。
- 一个包含明显方法论经验的大任务结束前。

Skill 安装后，Codex 不需要用户额外配置。`cycle` 会在需要时初始化本地和全局运行态。

## Claude Code

可选 hooks 可以调用：

- `cycle`
- `cycle --json`
- `validate`

只有当平台能提供脱敏字段时，hooks 才能调用 `log-signal`。Hooks 不能保存用户原文，也不能替模型判断经验是否值得沉淀。

## 安全规则

- 不要自动应用 Skill 修改。
- 不要绕过 `Yes` / `No` / `Revision`。
- 不要保存用户原文。
- 不要把原始项目路径复制到全局记录。
- 不要让 hooks 负责方法论判断。
- 不要把 CLI 输出当成“可迁移性已经被证明”的最终结论。
