"""Tests for kubeidea.core.context module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from kubeidea.core.context import AppContext


def test_app_context_defaults() -> None:
    """AppContext should have sensible defaults."""
    ctx = AppContext()
    assert ctx.current_context is None
    assert ctx.current_namespace == "default"
    assert ctx.settings == {}
    assert ctx.rbac_inspector is None


def test_switch_context() -> None:
    """switch_context should update the active context."""
    ctx = AppContext()
    mock_client = object()
    ctx.switch_context("minikube", mock_client, ["default", "kube-system"])
    assert ctx.current_context == "minikube"
    assert ctx.api_client is mock_client
    assert ctx.namespaces == ["default", "kube-system"]
    assert ctx.current_namespace == "default"


def test_switch_namespace() -> None:
    """switch_namespace should update the active namespace."""
    ctx = AppContext()
    ctx.switch_namespace("kube-system")
    assert ctx.current_namespace == "kube-system"


def test_switch_context_creates_rbac_inspector() -> None:
    """switch_context should create an RBACInspector bound to the new api_client."""
    ctx = AppContext()
    mock_client = object()
    with patch("kubeidea.core.context.RBACInspector") as mock_cls:
        sentinel = MagicMock()
        mock_cls.return_value = sentinel
        ctx.switch_context("minikube", mock_client, ["default"])
        mock_cls.assert_called_once_with(mock_client)
        assert ctx.rbac_inspector is sentinel


def test_disconnect_clears_rbac_inspector() -> None:
    """disconnect should set rbac_inspector back to None."""
    ctx = AppContext()
    mock_client = object()
    with patch("kubeidea.core.context.RBACInspector"):
        ctx.switch_context("minikube", mock_client, ["default"])
    assert ctx.rbac_inspector is not None
    ctx.disconnect()
    assert ctx.rbac_inspector is None
