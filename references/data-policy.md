# Data Policy

Record only sanitized methodology signals. This Skill is not user memory, project memory, or chat history.

## May Record

- Sanitized methodology summaries.
- Abstract method actions.
- Trigger conditions.
- Transfer conditions.
- Negative cases.
- Verification paths.
- Operator id.
- Strength and optional confidence.
- Proposal gate outcomes.
- Hashed project identity.
- Compressed global promotion evidence.
- Optional explicit project identity before hashing.

## Must Not Record

- User identity details.
- Contact details, accounts, keys, tokens, or credentials.
- Complete user original text.
- Complete conversations.
- Client names, company secrets, or sensitive project identifiers.
- Personal preferences.
- Ordinary bug-fix facts.
- Raw project paths in global promotion records.
- Raw explicit project ids in global promotion records.

## Recording Rule

If safe sanitization is not possible, do not record. If the signal is weak, ignore it instead of writing a weak reject.

High-quality signals usually contain:

- A reusable method.
- A clear trigger.
- A plausible transfer condition.
- A known negative case or risk.
- A verification path.

## Local vs Global

Project-local `.jinhua/data/` may keep richer signal cards.

Global `global-data/` may keep only compressed promotion evidence:

- method fingerprint
- method key
- sanitized summary
- signal-card fields
- operator
- source type
- strength
- optional confidence
- hashed project identity

Do not copy raw local evidence into global state.

When `--project-id` or `JINHUA_PROJECT_ID` is used, hash the explicit value and store only the hash plus identity source.

## Write Boundary

Automatic accumulation is not a background task. Writing occurs only when the Skill is invoked and the model calls the CLI.

If files cannot be written, say that persistence failed and provide the record that would have been written.
