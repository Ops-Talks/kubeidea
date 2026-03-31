# Getting Started

## Prerequisites

- **Python ≥ 3.11**
- **Poetry ≥ 1.9** — install with `pip install poetry`

## Install dependencies

```bash
poetry install
```

## Run in development mode

This opens a native desktop window powered by Flet/Flutter:

```bash
poetry run flet run src/kubeidea/app.py
```

## Build desktop executables

Flet includes built-in packaging to produce native executables for
**Linux**, **macOS**, and **Windows** from a single Python codebase:

```bash
poetry run flet build
```

!!! tip "Cross-platform builds"
    The `flet build` command produces a binary for the OS you are running on.
    To generate binaries for all three platforms, the project uses a
    [GitHub Actions release workflow](https://github.com/Ops-Talks/kubeidea/blob/main/.github/workflows/release.yml)
    that runs on `ubuntu-latest`, `macos-latest`, and `windows-latest`
    runners and attaches the resulting artifacts to each GitHub Release.

## Run tests

```bash
poetry run pytest
```

## Lint & type-check

```bash
poetry run ruff check src/ tests/
poetry run mypy src/kubeidea/
```

## Serve the documentation locally

```bash
poetry install --with docs
poetry run mkdocs serve
```

Then open <http://127.0.0.1:8000> in your browser.
