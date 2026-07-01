## Summary

Describe what changed and why.

## Type

- [ ] Bug fix
- [ ] Feature
- [ ] Provider support
- [ ] Documentation
- [ ] Tests or tooling

## Verification

- [ ] `py -3 -m pytest Codebase\v2\tests -q`
- [ ] `py -3 -m ruff check .`
- [ ] Manual UI check, if UI changed

## Safety

- [ ] No local session data, logs, exports, trash data, secrets, or machine-specific paths are committed
- [ ] Provider delete or resume behavior is conservative and tested
- [ ] README or SECURITY notes were updated if user-facing behavior changed

