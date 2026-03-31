"""Plugin discovery and lifecycle management via entry points."""

from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass, field
from typing import Any, Protocol

PLUGIN_GROUP = "kubeidea.plugins"


class PluginInterface(Protocol):
    """Protocol that every Kube-IDEA plugin must implement."""

    name: str

    def activate(self, host_api: Any) -> None:
        """Called when the plugin is loaded.

        Args:
            host_api: Reference to the host application API surface.
        """
        ...

    def deactivate(self) -> None:
        """Called when the plugin is unloaded."""
        ...


@dataclass
class PluginInfo:
    """Metadata about a discovered plugin.

    Attributes:
        name: Plugin identifier (entry-point name).
        module: Fully qualified module path.
        loaded: Whether the plugin has been successfully activated.
        instance: The instantiated plugin object, if loaded.
    """

    name: str
    module: str
    loaded: bool = False
    instance: Any = None


@dataclass
class PluginHost:
    """Discovers and manages Kube-IDEA plugins.

    Plugins are registered via Python entry points under the
    ``kubeidea.plugins`` group.
    """

    _plugins: dict[str, PluginInfo] = field(default_factory=dict)

    def discover(self) -> list[PluginInfo]:
        """Discover all installed plugins.

        Returns:
            A list of ``PluginInfo`` for each discovered plugin.
        """
        eps = importlib.metadata.entry_points()
        group_eps = eps.select(group=PLUGIN_GROUP)

        for ep in group_eps:
            if ep.name not in self._plugins:
                self._plugins[ep.name] = PluginInfo(
                    name=ep.name,
                    module=ep.value,
                )
        return list(self._plugins.values())

    def activate(self, plugin_name: str, host_api: Any) -> bool:
        """Activate a plugin by name.

        Args:
            plugin_name: The entry-point name of the plugin.
            host_api: Host API object passed to the plugin.

        Returns:
            ``True`` if activation succeeded, ``False`` otherwise.
        """
        info = self._plugins.get(plugin_name)
        if info is None or info.loaded:
            return False

        eps = importlib.metadata.entry_points()
        group_eps = eps.select(group=PLUGIN_GROUP)

        for ep in group_eps:
            if ep.name == plugin_name:
                try:
                    plugin_cls = ep.load()
                    instance = plugin_cls()
                    instance.activate(host_api)
                    info.instance = instance
                    info.loaded = True
                    return True
                except Exception:
                    return False
        return False

    def deactivate(self, plugin_name: str) -> bool:
        """Deactivate a loaded plugin.

        Args:
            plugin_name: The entry-point name of the plugin.

        Returns:
            ``True`` if deactivation succeeded, ``False`` otherwise.
        """
        info = self._plugins.get(plugin_name)
        if info is None or not info.loaded or info.instance is None:
            return False
        try:
            info.instance.deactivate()
        except Exception:
            pass
        info.loaded = False
        info.instance = None
        return True

    @property
    def loaded_plugins(self) -> list[PluginInfo]:
        """Return all currently loaded plugins."""
        return [p for p in self._plugins.values() if p.loaded]
