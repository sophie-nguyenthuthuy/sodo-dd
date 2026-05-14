## Summary

<!-- 1-3 bullets explaining what and why -->

## Scope

- [ ] backend
- [ ] frontend
- [ ] infra / CI
- [ ] docs

## Compliance checklist (gate)

- [ ] No PII added to logs or error messages
- [ ] New external-system calls have a `mock` mode for local dev
- [ ] Field-level encryption applied to any new PII column
- [ ] Audit-log entries added for any new state-changing action

## Test plan

- [ ] Unit tests added / updated
- [ ] Manual repro covered
- [ ] `make test` green
