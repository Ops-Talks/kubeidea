# Development

## Setup

```bash
# Clone the repository
git clone https://github.com/Ops-Talks/kubeidea.git
cd kubeidea

# Install all dependencies (including dev and docs groups)
poetry install --with docs
```

## Day-to-day workflow

```bash
# Run the desktop app (opens a native window)
poetry run flet run src/kubeidea/app.py

# Run the test suite
poetry run pytest

# Lint
poetry run ruff check src/ tests/

# Type-check
poetry run mypy src/kubeidea/

# Auto-fix lint issues
poetry run ruff check --fix src/ tests/
```

## Documentation

```bash
# Serve docs locally with live-reload
poetry run mkdocs serve

# Build static site
poetry run mkdocs build
```

The built site is placed in the `site/` directory (git-ignored).

## CI / CD

The project provides three GitHub Actions workflows under
`.github/workflows/`:

| Workflow         | Trigger                       | What it does                                                |
| ---------------- | ----------------------------- | ----------------------------------------------------------- |
| **ci.yml**       | Push / PR to `main`           | Lint (`ruff`, `mypy`), test (`pytest`), build docs          |
| **release.yml**  | Tag push (`v*`)               | Build desktop binaries for Linux, macOS, Windows via `flet build` and attach them to the GitHub Release |
| **docs.yml**     | Push to `main` (docs changes) | Build and deploy MkDocs site to GitHub Pages                |

### Creating a release with binaries

1. Tag a commit following semver: `git tag v0.1.0`
2. Push the tag: `git push origin v0.1.0`
3. The **release** workflow will:
    - Run on **three OS runners** (Ubuntu, macOS, Windows)
    - Execute `flet build` on each to produce a native binary
    - Create a GitHub Release and upload the binaries as assets
4. Users can then download the installer for their platform from the
   [Releases](https://github.com/Ops-Talks/kubeidea/releases) page.
