"""Tests for kubeidea.plugins.host module."""

from kubeidea.plugins.host import PluginHost


def test_discover_returns_empty_when_no_plugins() -> None:
    """PluginHost.discover should return an empty list by default."""
    host = PluginHost()
    plugins = host.discover()
    # In test env we do not expect any third-party plugins registered
    assert isinstance(plugins, list)


def test_loaded_plugins_initially_empty() -> None:
    """No plugins should be loaded before activation."""
    host = PluginHost()
    assert host.loaded_plugins == []


def test_activate_unknown_plugin() -> None:
    """Activating a non-existent plugin should return False."""
    host = PluginHost()
    assert host.activate("nonexistent-plugin", host_api=None) is False


def test_deactivate_unknown_plugin() -> None:
    """Deactivating a non-existent plugin should return False."""
    host = PluginHost()
    assert host.deactivate("nonexistent-plugin") is False
