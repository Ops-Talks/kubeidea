# Security (DevSecOps)

Kube-IDEA follows security-first principles across its entire lifecycle.

## Dependency management

- All dependencies are **locked** via `poetry.lock` for reproducible builds
  and accurate Software Composition Analysis (SCA).
- The CI pipeline verifies the lock file is up to date.

## Static analysis

| Tool   | Purpose            |
| ------ | ------------------ |
| `ruff` | Linting & style    |
| `mypy` | Static type checks |

Both tools run automatically in the
[CI workflow](https://github.com/Ops-Talks/kubeidea/blob/main/.github/workflows/ci.yml).

## RBAC

All Kubernetes actions performed through the UI respect the cluster's
native RBAC model. Kube-IDEA uses `SelfSubjectAccessReview` to verify
permissions before executing operations, providing clear feedback when
access is denied.

## Secrets handling

Kube-IDEA **never** persists secrets to disk. Credentials and tokens are
managed through the OS keyring provider whenever possible.

## Telemetry

- Telemetry is **100 % opt-in** and **disabled by default**.
- No sensitive data is ever collected.
- Users can toggle telemetry from the Settings page.

## SBOM & supply chain

- **CycloneDX** SBOM generation is planned for CI.
- Code signing for release binaries is on the roadmap
  (Windows SignTool, macOS notarization, Linux `.deb`/`.rpm` signing).
