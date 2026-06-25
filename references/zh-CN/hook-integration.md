# Hook 与平台集成

> 英文参考见 [../hook-integration.md](../hook-integration.md)；本文件说明中文用户该怎么理解平台集成。

`cycle` 是 jinhua 的自动检查点。平台可以帮忙调用它，但不能改变安全模型。

CLI 不作为后台进程运行，也不应该偷偷写入用户没有确认的 Skill 修改。

如果平台需要很轻的前置路由，可以调用：

```bash
python <jinhua-dir>/scripts/jinhua.py wake-check --text "<latest user message>" --json
```

`wake-check` 是只读粗筛。它不会运行 `cycle`，不会记录信号，不会保存用户原文，也不会替模型判断某条经验是否值得沉淀。它只识别几类明显的元工作流线索：Skill 没触发、流程纠正、验证标准纠正、工具选择纠正，或用户要求把方法沉淀下来。返回 `should_route: true` 时，平台应优先路由到 jinhua，然后由 jinhua 运行 `cycle` 并继续做严格判断。

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

如果 hook 需要把待确认提案当成硬信号，可以调用：

```bash
python <jinhua-dir>/scripts/jinhua.py --project-root <project-root> cycle --json --fail-on-pending-gate
```

退出码 `2` 表示存在本地或全局待确认提案，agent 必须先把用户确认门展示出来，再继续 jinhua 这条分支。

## Claude Code

可选 hooks 可以调用：

- `wake-check --json`
- `cycle`
- `cycle --json`
- `cycle --json --fail-on-pending-gate`
- `validate`

只有当平台能提供脱敏字段时，hooks 才能调用 `log-signal`。Hooks 不能保存用户原文，也不能替模型判断经验是否值得沉淀。

## 安全规则

- 不要自动应用 Skill 修改。
- 不要绕过带落点的用户确认门：`Project Rule` / `Skill Patch` / `Personal Global Skill` / `No` / `Revision`。
- 不要保存用户原文。
- 不要把原始项目路径复制到全局记录。
- 不要让 hooks 负责方法论判断。
- 不要每条消息都跑完整 `cycle`；先用 `wake-check` 做便宜路由，精确判断仍然留在 Skill 内部。
- 不要把 CLI 输出当成“可迁移性已经被证明”的最终结论。
