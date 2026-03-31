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
| **release.yml**  | Tag push (`v*`)               | Build desktop binaries for Linux, macOS, Windows, Fedora, and Flatpak via `flet build` and attach them to the GitHub Release |
| **docs.yml**     | Push to `main` (docs changes) | Build and deploy MkDocs site to GitHub Pages                |

### Creating a release with binaries

You can trigger the release workflow in two ways:

=== "GitHub UI (no local steps needed)"

    1. Go to the repository's
       [Releases](https://github.com/Ops-Talks/kubeidea/releases) page.
    2. Click **Draft a new release**.
    3. In the **Choose a tag** dropdown, type a new tag name following
       semver (e.g. `v0.2.0`) and select **Create new tag on publish**.
    4. Fill in the release title and description (or leave them for
       auto-generation).
    5. Click **Publish release** — the tag is created and the workflow
       starts automatically.

=== "Local terminal"

    ```bash
    git tag v0.2.0
    git push origin v0.2.0
    ```

Once the tag is pushed, the **release** workflow triggers and runs the
following jobs:

**`build` (matrix)** — runs in parallel across three GitHub-hosted runners:

| Runner             | Package format          | Target   |
| ------------------ | ----------------------- | -------- |
| `ubuntu-latest`    | `kube-idea-linux.deb`   | `linux`  |
| `macos-latest`     | `kube-idea-macos.dmg`   | `macos`  |
| `windows-latest`   | `kube-idea-windows.zip` | `windows`|

Each runner sets up Python 3.12, installs Poetry and project
dependencies, then executes `poetry run flet build <target> --yes src/`
to produce a native binary. The `--yes` flag auto-confirms any interactive
prompts (e.g. Flutter SDK installation) so the build runs unattended in CI.
After the build, each runner packages the binary into the
platform-appropriate format:

- **Linux** — a `.deb` package built with `dpkg-deb`, which installs
  the application to `/opt/kube-idea` and symlinks the executable into
  `/usr/bin`.
- **macOS** — a `.dmg` disk image created with `hdiutil`.
- **Windows** — a `.zip` archive produced by PowerShell's
  `Compress-Archive`.

**`build-fedora`** — runs on `ubuntu-latest` inside a `fedora:latest`
container. It installs Fedora-specific system packages via `dnf`
(Python, clang, cmake, GTK3-devel, etc.), then builds the Linux
binary linked against Fedora's libraries and packages it as a
`.tar.gz` archive.

**`build-flatpak`** — runs on `ubuntu-latest`, builds the Linux binary
with Flet, installs `flatpak-builder` and the `org.freedesktop`
runtime/SDK, then packages the application as a `.flatpak` bundle
using the manifest at `flatpak/io.github.ops_talks.KubeIdea.yml`.
The Flatpak grants the application network access (for Kubernetes
API connectivity), display access (X11/Wayland), and read-only
access to `~/.kube` (for kubeconfig).

**`release`** — waits for `build`, `build-fedora`, and `build-flatpak`
to finish, downloads all five artifacts, and publishes a GitHub
Release with the following assets:

- `kube-idea-linux.deb` — Debian/Ubuntu package
- `kube-idea-macos.dmg` — macOS disk image
- `kube-idea-windows.zip` — Windows archive
- `kube-idea-fedora.tar.gz` — Fedora archive
- `kube-idea.flatpak` — Flatpak bundle (works on any Linux distro with Flatpak)

Users can then download the package for their platform from the
[Releases](https://github.com/Ops-Talks/kubeidea/releases) page.
