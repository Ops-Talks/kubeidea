# Kube-IDEA

> **Kubernetes desktop IDE built with Python (Flet + Poetry).**

Kube-IDEA is a cross-platform desktop application for operating Kubernetes
clusters with a focus on **lightweight UX**, **security (DevSecOps)**, and
**extensibility**.

It is written in **Python**, uses **Poetry** for dependency management, and
renders a modern UI via **Flet** (Flutter).

---

## Features (MVP scope)

| Feature              | Description                                                                    |
| -------------------- | ------------------------------------------------------------------------------ |
| **Cluster explorer** | List Namespaces, Pods, Deployments, Services, Nodes; view details, events, YAML |
| **Logs**             | Streaming logs with label/container filters; search; JSON/TXT export           |
| **Exec**             | Remote shell (TTY/resize) in containers                                        |
| **Port-forward**     | Service/Pod port-forwarding; active tunnel manager                             |
| **Metrics**          | CPU/Memory from metrics-server; optional Prometheus connector                  |
| **RBAC Inspector**   | Who-can-what analysis; SelfSubjectAccessReview simulation                      |
| **YAML Editor**      | Schema validation (cluster OpenAPI); diffs vs. live                            |
| **Plugins**          | Python entry-point based plugin system with host API                           |

---

## Quick links

- [Getting Started](getting-started.md) — install, run, and build
- [Architecture](architecture.md) — how the project is organized
- [Development](development.md) — workflow for contributors
- [Plugins](plugins.md) — extend Kube-IDEA with Python plugins
- [Security](security.md) — DevSecOps practices
- [Contributing](contributing.md) — how to contribute
- [Roadmap](roadmap.md) — what is coming next
