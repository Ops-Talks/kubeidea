"""Adapter for the Kubernetes metrics-server API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class NodeMetrics(BaseModel):
    """CPU and memory usage for a Kubernetes node."""

    name: str
    cpu_usage: str
    memory_usage: str


class PodMetrics(BaseModel):
    """CPU and memory usage for a Kubernetes pod."""

    name: str
    namespace: str
    containers: list[dict[str, str]]


class MetricsServerAdapter:
    """Fetches resource metrics from the Kubernetes metrics-server.

    The metrics-server must be installed in the cluster for these calls to
    succeed. Methods degrade gracefully and return empty lists when the
    metrics API is unavailable.
    """

    def __init__(self, api_client: Any) -> None:
        self._api_client = api_client

    def get_node_metrics(self) -> list[NodeMetrics]:
        """Fetch CPU/memory metrics for all nodes.

        Returns:
            A list of ``NodeMetrics`` objects.
        """
        from kubernetes.client import CustomObjectsApi

        api = CustomObjectsApi(api_client=self._api_client)
        try:
            result = api.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes",
            )
            return [
                NodeMetrics(
                    name=item["metadata"]["name"],
                    cpu_usage=item["usage"]["cpu"],
                    memory_usage=item["usage"]["memory"],
                )
                for item in result.get("items", [])
            ]
        except Exception:
            return []

    def get_pod_metrics(self, namespace: str = "default") -> list[PodMetrics]:
        """Fetch CPU/memory metrics for pods in a namespace.

        Args:
            namespace: Target namespace.

        Returns:
            A list of ``PodMetrics`` objects.
        """
        from kubernetes.client import CustomObjectsApi

        api = CustomObjectsApi(api_client=self._api_client)
        try:
            result = api.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=namespace,
                plural="pods",
            )
            return [
                PodMetrics(
                    name=item["metadata"]["name"],
                    namespace=namespace,
                    containers=[
                        {
                            "name": c["name"],
                            "cpu": c["usage"]["cpu"],
                            "memory": c["usage"]["memory"],
                        }
                        for c in item.get("containers", [])
                    ],
                )
                for item in result.get("items", [])
            ]
        except Exception:
            return []
