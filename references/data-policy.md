# Data Policy

Jinhua records sanitized methodology evidence, not user memory, project memory, or chat history.

## Recordability Gate

Record only when the lesson can be expressed as both:

- a reusable `trigger`;
- a reusable `action`.

At least one must also be true:

- the user corrected workflow, reasoning direction, verification, Skill/tool choice, or a missed procedure;
- the method repeated in the current project;
- a repaired failure exposed a transferable cause;
- a successful path exposed a reusable method;
- the user explicitly requested crystallization.

If either `trigger` or `action` cannot be written without private task details, skip the signal.

## May Record

- sanitized summary and context;
- operator id and local `cluster_key`;
- source type and strength;
- trigger, action, transfer conditions, negative cases, verification path, and risk;
- proposal target, complete Markdown patch, risk, placement, and evidence ids;
- user gate outcome;
- actual applied target and verified edit summary;
- hashed project identity;
- compressed cross-project evidence.

## Must Not Record

- complete user prompts or conversations;
- names, contact details, accounts, credentials, keys, or tokens;
- client names, company secrets, or sensitive project identifiers;
- personal preferences;
- ordinary one-off bug facts;
- raw project paths in global promotion data;
- raw explicit project ids in global promotion data.

If safe sanitization is not possible, do not record.

## Local And Global Boundaries

Project-local `.jinhua/data/` may keep richer signal cards and evidence ids.

Global `global-data/` may keep only:

- hashed project identity;
- exact method fingerprint and readable method key;
- sanitized summary/context;
- operator, source type, and strength;
- reusable signal-card fields;
- evidence ids and aggregate counts.

Do not copy raw local evidence into global records. When `--project-id` or `JINHUA_PROJECT_ID` is used, hash the explicit value and store only the hash and identity source.

## Hook Boundary

Hooks may write only `.jinhua/runtime/invocation-guard.json` for local classification support, unique-turn counting, fixed periodic checks, and same-turn deduplication.

Hooks must not:

- migrate core data;
- append `signals.jsonl`;
- create or update proposals;
- record adoption or rejection;
- edit a Skill or project rule.

## Retention

Jinhua 2.0 keeps all accepted signals. There is no compaction or ignored-signal status. A weak or unsafe lesson should be skipped before writing rather than written and deleted later.

## Adoption Boundary

The agent edits and verifies an approved target with host-native tools. `apply-proposal` and `global-apply` only record a completed adoption. If editing or verification fails, no adoption record may be written.

If persistence itself fails, tell the user that the ledger was not updated. Do not claim a signal, proposal, or adoption was saved.
