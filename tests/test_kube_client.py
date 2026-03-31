"""Tests for kubeidea.kube.client module."""

from kubeidea.kube.client import KubeConfigManager, KubeContext


def test_kube_context_model() -> None:
    """KubeContext should accept required and optional fields."""
    ctx = KubeContext(name="minikube", cluster="minikube", user="minikube-user")
    assert ctx.name == "minikube"
    assert ctx.namespace is None


def test_kube_context_with_namespace() -> None:
    """KubeContext should accept an explicit namespace."""
    ctx = KubeContext(name="prod", cluster="prod-cluster", user="admin", namespace="kube-system")
    assert ctx.namespace == "kube-system"


def test_kube_config_manager_default_path() -> None:
    """KubeConfigManager should default to ~/.kube/config."""
    mgr = KubeConfigManager()
    assert mgr.kubeconfig_path.endswith(".kube/config")


def test_list_contexts_graceful_on_missing_file() -> None:
    """list_contexts should return empty list when kubeconfig is missing."""
    mgr = KubeConfigManager(kubeconfig_path="/tmp/nonexistent-kubeconfig")
    contexts = mgr.list_contexts()
    assert contexts == []
