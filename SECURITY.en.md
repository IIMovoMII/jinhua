# Security Policy

Languages: English | [简体中文](SECURITY.md)

## Supported Versions

The `main` branch is the supported development line.

## Reporting A Vulnerability

Please open a private security advisory on GitHub when available. If private advisories are not available, open a minimal public issue without sensitive exploit details and ask for a private contact path.

Do not include secrets, user data, private prompts, or proprietary project content in public reports.

## Scope

jinhua is a local ledger Skill. Security-relevant reports include:

- Sensitive data written to global state.
- Raw user text or project paths leaking into files intended for sharing.
- Command execution behavior that is broader than documented.
- Data corruption that can cause unintended Skill changes.

## Out Of Scope

- Requests to bypass the user gate.
- Reports that require storing credentials in the repository.
- Vulnerabilities in unrelated host agents or IDEs.
