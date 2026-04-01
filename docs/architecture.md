# Architecture

## High-level overview

```text
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

## Project structure

```text
kube-idea/
├── pyproject.toml          # Poetry project definition & tool config
├── mkdocs.yml              # MkDocs configuration
├── docs/                   # Documentation source (MkDocs)
├── src/kubeidea/
│   ├── app.py              # Flet application entry point
│   ├── ui/                 # Flet views, routing, theming
│   │   ├── theme.py
│   │   ├── navigation.py
│   │   └── views/
│   │       ├── home.py
│   │       ├── explorer.py   # Resource browser (17 types, CRUD, detail panel)
│   │       ├── clusters.py   # Cluster connection management
│   │       └── placeholder.py
│   ├── core/               # Application services, use cases
│   │   └── context.py
│   ├── kube/               # API clients, watchers, port-forward, exec
│   │   ├── client.py
│   │   ├── resources.py    # 22 functions: list_*, get, delete, scale, restart
│   │   └── models.py       # 18 Pydantic models (PodInfo, DeploymentInfo, …)
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
├── tests/                  # pytest test suite (138 tests)
│   ├── test_context.py
│   ├── test_resources.py   # 122 tests for models + resources
│   └── test_settings.py
└── README.md
```

## Key technology choices

| Layer            | Technology                                      |
| ---------------- | ----------------------------------------------- |
| **UI**           | [Flet](https://flet.dev) (Flutter rendering)    |
| **Kubernetes**   | `kubernetes` Python client                      |
| **Data models**  | [Pydantic](https://docs.pydantic.dev) v2        |
| **HTTP**         | [httpx](https://www.python-httpx.org)            |
| **CLI**          | [Typer](https://typer.tiangolo.com)              |
| **Packaging**    | Poetry + Flet built-in packaging                |
| **Docs**         | MkDocs with Material theme                      |
