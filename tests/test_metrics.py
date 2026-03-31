"""Tests for kubeidea.metrics models."""

from kubeidea.metrics.server import NodeMetrics, PodMetrics


def test_node_metrics_model() -> None:
    """NodeMetrics should hold name, cpu, and memory fields."""
    nm = NodeMetrics(name="node-1", cpu_usage="250m", memory_usage="1Gi")
    assert nm.name == "node-1"
    assert nm.cpu_usage == "250m"


def test_pod_metrics_model() -> None:
    """PodMetrics should hold name, namespace, and container list."""
    pm = PodMetrics(
        name="my-pod",
        namespace="default",
        containers=[{"name": "app", "cpu": "100m", "memory": "128Mi"}],
    )
    assert pm.namespace == "default"
    assert len(pm.containers) == 1
