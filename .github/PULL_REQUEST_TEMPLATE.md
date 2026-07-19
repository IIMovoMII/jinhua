## Summary

- TODO

## Verification

- [ ] `python scripts/test_core_loop.py`
- [ ] `python scripts/test_trigger_layer.py`
- [ ] `python scripts/test_adapters.py`
- [ ] Python compile checks passed
- [ ] Runtime `validate` passed
- [ ] JSON and `git diff --check` passed
- [ ] Plugin cachebuster/reinstall and enabled check passed

## Data Policy

- [ ] No runtime state, secrets, private prompts, or sensitive project identifiers are included.
- [ ] `.jinhua/`, `global-data/`, `.archive/`, and generated caches are not tracked.

## Compatibility

- [ ] Core loop and user gate remain intact.
- [ ] Hook changes do not write signals or proposals.
- [ ] Chinese default docs and English mirrors are synchronized where needed.

## Notes

- TODO
