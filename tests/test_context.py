"""Tests for kubeidea.core.context module."""

from kubeidea.core.context import AppContext


def test_app_context_defaults() -> None:
    """AppContext should have sensible defaults."""
    ctx = AppContext()
    assert ctx.current_context is None
    assert ctx.current_namespace == "default"
    assert ctx.settings == {}


def test_switch_context() -> None:
    """switch_context should update the active context."""
    ctx = AppContext()
    ctx.switch_context("minikube")
    assert ctx.current_context == "minikube"


def test_switch_namespace() -> None:
    """switch_namespace should update the active namespace."""
    ctx = AppContext()
    ctx.switch_namespace("kube-system")
    assert ctx.current_namespace == "kube-system"
