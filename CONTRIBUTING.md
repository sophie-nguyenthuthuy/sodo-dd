# Contributing

## Local setup

```bash
cp .env.example .env
make up
make migrate
make seed
make test
```

## Code style

- Python: ruff (line 100), strict mypy. `make fmt` rewrites in place.
- TypeScript: `next lint` + `tsc --noEmit`.
- Conventional commits encouraged: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`.

## Pull requests

Use the template. PRs touching adapters or compliance must check the gate on the
template before review.

## Branching

- `main` is protected; merge via PR after CI green.
- Feature branches: `feat/<short-topic>`; fixes: `fix/<short-topic>`.

## Testing

Adapters must ship with mock mode coverage. New PII columns require an encryption test
in `tests/test_security.py`.
