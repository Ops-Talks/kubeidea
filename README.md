# Kube-IDEA

[![CI](https://github.com/Ops-Talks/kubeidea/actions/workflows/ci.yml/badge.svg)](https://github.com/Ops-Talks/kubeidea/actions/workflows/ci.yml)
[![Docs](https://github.com/Ops-Talks/kubeidea/actions/workflows/docs.yml/badge.svg)](https://ops-talks.github.io/kubeidea/)
[![Release](https://github.com/Ops-Talks/kubeidea/actions/workflows/release.yml/badge.svg)](https://github.com/Ops-Talks/kubeidea/actions/workflows/release.yml)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/flet-UI-purple?logo=flutter&logoColor=white)](https://flet.dev)
[![License](https://img.shields.io/github/license/Ops-Talks/kubeidea)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

> **Kubernetes desktop IDE built with Python (Flet + Poetry).**

Kube-IDEA is a cross-platform desktop application for operating Kubernetes
clusters with a focus on lightweight UX, security (DevSecOps), and
extensibility. It is written in **Python**, uses **Poetry** for dependency
management, and renders a modern UI via **Flet** (Flutter).

---

## Features (MVP scope)

| Feature | Description |
|---|---|
| **Cluster explorer** | List Namespaces, Pods, Deployments, Services, Nodes; view details, events, and YAML |
| **Logs** | Streaming logs with label/container filters; search; JSON/TXT export |
| **Exec** | Remote shell (TTY/resize) in containers |
| **Port-forward** | Service/Pod port-forwarding; active tunnel manager |
| **Metrics** | CPU/Memory from metrics-server; optional Prometheus connector |
| **RBAC Inspector** | Who-can-what analysis; SelfSubjectAccessReview simulation |
| **YAML Editor** | Schema validation (cluster OpenAPI); diffs vs. live |
| **Plugins** | Python entry-point based plugin system with host API |

---

## Architecture

```
+----------------------------- UI (Flet) ------------------------------+
|  Navigation     Panels     Logs/Term      YAML Editor     Metrics   |
+------------------------------|---------------------------------------+
                               v
                       +--------------+       +----------------+
                       |  Core App    |<----->|  Plugin Host   |
                       | (Python)     |       | (entry points) |
                       +------+-------+       +----------------+
                              |
    +-------------------------+-------------------------------+
    |                         |                               |
    v                         v                               v
[Kube Adapter]         [Observability]                 [Config & Sec]
- kubeconfig ctx       - metrics-server/Prom           - RBAC viewer
- CRUD resources       - events                        - Telemetry (opt-in)
- logs/exec/pf         - log aggregation               - Secrets handling

[CLI/Daemon optional]  [Store/Cache (SQLite)]  [Packaging/Updater]
```

---

## Project structure

```text
kube-idea/
├── pyproject.toml          # Poetry project definition & tool config
├── src/kubeidea/
│   ├── app.py              # Flet application entry point
│   ├── ui/                 # Flet views, routing, theming
│   │   ├── theme.py
│   │   ├── navigation.py
│   │   └── views/
│   │       └── home.py
│   ├── core/               # Application services, use cases
│   │   └── context.py
│   ├── kube/               # API clients, watchers, port-forward, exec
│   │   ├── client.py
│   │   └── resources.py
│   ├── metrics/            # metrics-server / Prometheus adapters
│   │   ├── server.py
│   │   └── prometheus.py
│   ├── plugins/            # Plugin host, SDK, lifecycle
│   │   └── host.py
│   ├── security/           # RBAC inspector, secrets handling
│   │   └── rbac.py
│   ├── config/             # Settings, kubeconfig manager
│   │   └── settings.py
│   └── utils/              # Logging, telemetry (opt-in), cache
│       └── logging.py
├── plugins/                # First-party sample plugins
├── tests/                  # pytest test suite
└── README.md
```

---

## Getting started

### Prerequisites

- **Python ≥ 3.11**
- **Poetry ≥ 1.9** (`pip install poetry`)

### Install dependencies

```bash
poetry install
```

### Run in development mode

```bash
poetry run flet run src/kubeidea/app.py
```

### Build desktop executables

```bash
poetry run flet build
```

### Run tests

```bash
poetry run pytest
```

### Lint & type-check

```bash
poetry run ruff check src/ tests/
poetry run mypy src/kubeidea/
```

---

## Development flow

```bash
# Bootstrap
poetry install

# Run app (opens native window)
poetry run flet run src/kubeidea/app.py

# Quality checks
poetry run pytest
poetry run ruff check src/ tests/
poetry run mypy src/kubeidea/
```

---

## Security (DevSecOps)

- **Locked dependencies** (`poetry.lock`) for reproducible builds and SCA.
- **Linters & types**: `ruff`, `mypy` in CI.
- **SBOM**: CycloneDX generation planned; license policy.
- **Secrets**: Never stored; use OS keyring provider.
- **RBAC**: All actions respect `SubjectAccessReview` of the cluster.
- **Telemetry**: 100 % opt-in, disabled by default, no sensitive data.

---

## License

See [LICENSE](LICENSE) for details.

---

## Documentation

Full documentation is available at
**<https://ops-talks.github.io/kubeidea/>**.

To serve the docs locally:

```bash
poetry install --with docs
poetry run mkdocs serve
```

---

## Releases & binaries

When a version tag (`v*`) is pushed, the
[release workflow](.github/workflows/release.yml) builds desktop binaries
for **Linux**, **macOS**, and **Windows** using `flet build` and attaches
them to the GitHub Release. Download installers from the
[Releases page](https://github.com/Ops-Talks/kubeidea/releases).
