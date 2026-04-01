# Kube-IDEA — Copilot Instructions

## Stack

- **Language**: Python ≥ 3.11 with full type annotations (`mypy --strict`).
- **UI**: [Flet](https://flet.dev) (Flutter renderer). Use `ft.run()` — `ft.app()` is deprecated since 0.80.
- **Dependencies**: managed with Poetry (`pyproject.toml` + `poetry.lock`). Do not edit `poetry.lock` manually.
- **Linter / formatter**: `ruff` (rules E, F, I, N, W, UP). Never disable rules without a comment explaining why.
- **Testing**: `pytest` under `tests/`. Async tests use `pytest-asyncio`. Target coverage ≥ 80 %.

## Project layout

```
src/kubeidea/
  app.py          # Flet bootstrap — ft.run(main)
  ui/             # All Flet views and navigation
  core/           # AppContext, business logic, use-cases
  kube/           # kubernetes-python API wrappers
  metrics/        # metrics-server / Prometheus adapters
  plugins/        # Plugin host and entry-point discovery
  security/       # RBAC inspector, SubjectAccessReview
  config/         # Settings persistence
  utils/          # Logging, telemetry helpers
tests/            # Mirrors src/kubeidea/ structure
```

See [docs/architecture.md](docs/architecture.md) for component boundaries.

## Coding conventions

- Views extend `ft.Column` or `ft.Container`; receive `page: ft.Page` in `__init__`.
- Navigation index → view mapping lives in `app.py`; do not embed routing logic inside views.
- `ft.Icon` takes the icon **as the first positional argument**, not `name=`.
- All Kubernetes calls go through `kube/client.py` — never import `kubernetes` directly in UI code.
- Secrets are never stored to disk; use the OS keyring (`keyring` lib) where persistence is required.
- Telemetry is opt-in only; never collect data unless the user has explicitly enabled it in settings.

## CI / build

- `poetry run pytest` — must pass before any PR merge.
- `poetry run ruff check src/ tests/` — zero warnings.
- `poetry run mypy src/kubeidea/` — zero errors.
- Desktop binaries are built with `flet build <target>` via the release workflow on `v*` tags.
- Docs are deployed to `gh-pages` branch with `mkdocs gh-deploy --force`.

## Security (DevSecOps)

- All cluster actions must respect the user's RBAC via `SubjectAccessReview` — see `security/rbac.py`.
- Never log kubeconfig tokens, credentials, or secret values.
- Dependencies must stay pinned in `poetry.lock`; raise a PR to update them explicitly.
