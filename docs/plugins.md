# Plugins

Kube-IDEA supports a plugin system based on
[Python entry points](https://packaging.python.org/en/latest/specifications/entry-points/).

## How it works

1. A plugin is a regular Python package that declares an entry point under
   the `kubeidea.plugins` group.
2. At startup, the **Plugin Host** discovers all installed entry points in
   that group and exposes them for activation.
3. Each plugin implements the `PluginInterface` protocol (defined in
   `kubeidea.plugins.host`).

## Writing a plugin

### 1. Create a new Python package

```text
kubeidea-myplugin/
├── pyproject.toml
└── src/kubeidea_myplugin/
    └── __init__.py
```

### 2. Implement the interface

```python
# src/kubeidea_myplugin/__init__.py
from __future__ import annotations
from typing import Any


class Plugin:
    """Example Kube-IDEA plugin."""

    name = "my-plugin"

    def activate(self, host_api: Any) -> None:
        """Called when the plugin is loaded."""
        print(f"{self.name} activated")

    def deactivate(self) -> None:
        """Called when the plugin is unloaded."""
        print(f"{self.name} deactivated")
```

### 3. Register the entry point

In the plugin's `pyproject.toml`:

```toml
[project.entry-points."kubeidea.plugins"]
my-plugin = "kubeidea_myplugin:Plugin"
```

### 4. Install and test

```bash
# Install the plugin in the same environment
pip install -e ./kubeidea-myplugin

# Start Kube-IDEA — the plugin will be discovered automatically
poetry run flet run src/kubeidea/app.py
```

## Plugin Host API

The `PluginHost` class (in `kubeidea.plugins.host`) provides:

| Method               | Description                                      |
| -------------------- | ------------------------------------------------ |
| `discover()`         | Scan entry points and return a list of `PluginInfo` |
| `activate(name, …)`  | Load and activate a plugin by name               |
| `deactivate(name)`   | Deactivate a loaded plugin                       |
| `loaded_plugins`     | Property listing all currently active plugins    |
