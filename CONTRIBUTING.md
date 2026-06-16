# 贡献指南

语言：简体中文 | [English](CONTRIBUTING.en.md)

感谢你帮助改进 jinhua。

## 开发规则

- `SKILL.md` 保持简洁，详细用法放到 `references/`。
- `scripts/jinhua.py` 默认只使用 Python 标准库，除非有非常充分的理由。
- 不要提交运行态目录：`.jinhua/` 或 `global-data/`。
- 不要记录用户原文、凭证、客户名称或敏感项目标识。
- 中文文档是默认公开版本。用户可见行为变化时，同步检查英文辅助文档。
- 中文文档要写给中文用户看，不要只做逐词翻译。

## 本地检查

提交 PR 前运行：

```bash
python -m py_compile scripts/jinhua.py
python scripts/jinhua.py --project-root <temporary-project-root> cycle
python scripts/jinhua.py --project-root <temporary-project-root> validate
```

建议用临时项目目录做冒烟测试（smoke test），避免在仓库里创建运行态文件。

## 拉取请求内容

请说明：

- 改了什么。
- 为什么有用。
- 如何验证。
- 是否影响兼容性或数据政策。
