# Contributing

Thank you for your interest in contributing to Kube-IDEA! 🎉

## Getting started

1. **Fork** the repository and clone your fork.
2. Install dependencies:

    ```bash
    poetry install --with docs
    ```

3. Create a feature branch:

    ```bash
    git checkout -b feature/my-change
    ```

4. Make your changes and ensure all checks pass:

    ```bash
    poetry run pytest
    poetry run ruff check src/ tests/
    poetry run mypy src/kubeidea/
    ```

5. Commit with a clear message and open a **Pull Request**.

## Code style

- Follow the rules enforced by **ruff** (config in `pyproject.toml`).
- All public functions and classes must have **type annotations** and
  **docstrings**.
- Maximum line length: **120 characters**.

## Tests

- Place tests under `tests/`.
- Use `pytest`; async tests use `pytest-asyncio`.
- Aim for ≥ 80 % code coverage.

## Documentation

- Docs source lives in `docs/` and uses **MkDocs** with the **Material**
  theme.
- Preview locally:

    ```bash
    poetry run mkdocs serve
    ```

## Commit conventions

Use clear, descriptive commit messages. Prefix with a type when possible:

| Prefix     | Usage                          |
| ---------- | ------------------------------ |
| `feat:`    | New feature                    |
| `fix:`     | Bug fix                        |
| `docs:`    | Documentation only             |
| `test:`    | Adding or updating tests       |
| `chore:`   | Maintenance / tooling          |
| `refactor:`| Code changes without behavior change |
