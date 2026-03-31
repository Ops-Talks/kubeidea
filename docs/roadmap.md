# Roadmap

## Timeline overview

| Phase          | EPICs                                             | Timeline   |
| -------------- | ------------------------------------------------- | ---------- |
| Foundation     | App Desktop (Flet + Packaging) · Context Manager  | Month 1–2  |
| Troubleshooting| Logs, Exec, Port-forward · Metrics                | Month 3–4  |
| Governance     | YAML Editor · RBAC Inspector                      | Month 5    |
| Ecosystem      | Plugins · Distribution · Security/Compliance      | Month 6    |

## Phase details

### Foundation (Month 1–2)

- Boot Flet application, routing, and layout
- Theme (light/dark) and settings persistence
- i18n support (pt-BR / en-US)
- Packaging pipeline for Linux, macOS, Windows
- Kubeconfig parsing, context/namespace switching
- Resource listing with watch and reconnection

### Troubleshooting (Month 3–4)

- Streaming logs with filters, search, and export
- Remote shell (exec) with TTY/resize
- Port-forward manager with auto-reconnect
- Metrics-server adapter and charts
- Optional Prometheus connector

### Governance (Month 5)

- YAML editor with cluster OpenAPI validation
- Diff view (manifest vs. live)
- RBAC inspector with role/binding mapping
- Access simulation (impersonation)

### Ecosystem (Month 6)

- Plugin SDK and entry-point discovery
- Telemetry (opt-in) with privacy page
- In-app updater with signature verification
- SBOM generation and dependency scanning
- CI pipeline: pytest, ruff, mypy (coverage ≥ 80 %)
