# Kube-IDEA

> **Kubernetes desktop IDE built with Python (Flet + Poetry).**

Kube-IDEA is a cross-platform desktop application for operating Kubernetes
clusters with a focus on **lightweight UX**, **security (DevSecOps)**, and
**extensibility**.

It is written in **Python**, uses **Poetry** for dependency management, and
renders a modern UI via **Flet** (Flutter).

---

## Implemented features

| Feature | Status | Description |
|---|---|---|
| **Cluster connection** | ✅ Done | Multi-context kubeconfig management with namespace selection |
| **Resource Explorer** | ✅ Done | Browse 17 resource types across 5 categories; detail panel with Info, Events, and YAML tabs |
| **CRUD operations** | ✅ Done | Delete, Scale (Deployments/StatefulSets), Restart (rolling restart via annotation patch) |
| **Search / filter** | ✅ Done | Instant name filter across all resource types in the active category |

## Planned features

| Feature | Description |
|---|---|
| **Logs** | Streaming logs with container filters; search; JSON/TXT export |
| **Exec** | Remote shell (TTY/resize) in containers |
| **Port-forward** | Service/Pod port-forwarding; active tunnel manager |
| **Metrics** | CPU/Memory from metrics-server; optional Prometheus connector |
| **RBAC Inspector** | Who-can-what analysis; SelfSubjectAccessReview simulation |
| **YAML Editor** | Schema validation (cluster OpenAPI); diffs vs. live |
| **Plugins** | Python entry-point based plugin system with host API |

See the [Roadmap](roadmap.md) for the full implementation plan.

---

## Quick links

- [Getting Started](getting-started.md) — install, run, and build
- [Architecture](architecture.md) — how the project is organized
- [Development](development.md) — workflow for contributors
- [Plugins](plugins.md) — extend Kube-IDEA with Python plugins
- [Security](security.md) — DevSecOps practices
- [Contributing](contributing.md) — how to contribute
- [Roadmap](roadmap.md) — what is coming next
