# Contributing

Languages: English | [简体中文](CONTRIBUTING.md)

Thanks for helping improve jinhua.

## Development Rules

- Keep `SKILL.md` concise. Move detailed usage notes into `references/`.
- Keep `scripts/jinhua.py` standard-library only unless there is a strong reason.
- Do not commit runtime directories: `.jinhua/` or `global-data/`.
- Do not record private user text, credentials, customer names, or sensitive project identifiers.
- Keep Chinese as the default public documentation. Update English mirrors when user-facing behavior changes.

## Local Checks

Run these before opening a pull request:

```bash
python -m py_compile scripts/jinhua.py
python scripts/jinhua.py --project-root <temporary-project-root> cycle
python scripts/jinhua.py --project-root <temporary-project-root> validate
```

Use a temporary project root for smoke tests so repository runtime files are not created.

## Pull Requests

Include:

- What changed.
- Why it is useful.
- How it was verified.
- Any compatibility or data-policy impact.
