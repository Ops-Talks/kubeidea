"""Kubernetes resource listing and watch helpers."""

from __future__ import annotations

from typing import Any


def list_namespaces(api_client: Any) -> list[str]:
    """List all namespaces the current user can access.

    Args:
        api_client: A configured ``kubernetes.client.ApiClient``.

    Returns:
        A sorted list of namespace names.
    """
    from kubernetes.client import CoreV1Api

    v1 = CoreV1Api(api_client=api_client)
    ns_list = v1.list_namespace()
    return sorted(ns.metadata.name for ns in ns_list.items if ns.metadata)


def list_pods(api_client: Any, namespace: str = "default") -> list[dict[str, Any]]:
    """List pods in a given namespace.

    Args:
        api_client: A configured ``kubernetes.client.ApiClient``.
        namespace: Target namespace.

    Returns:
        A list of dicts with pod ``name`` and ``status``.
    """
    from kubernetes.client import CoreV1Api

    v1 = CoreV1Api(api_client=api_client)
    pod_list = v1.list_namespaced_pod(namespace=namespace)
    return [
        {
            "name": pod.metadata.name,
            "status": pod.status.phase if pod.status else "Unknown",
        }
        for pod in pod_list.items
        if pod.metadata
    ]


def list_deployments(api_client: Any, namespace: str = "default") -> list[dict[str, Any]]:
    """List deployments in a given namespace.

    Args:
        api_client: A configured ``kubernetes.client.ApiClient``.
        namespace: Target namespace.

    Returns:
        A list of dicts with deployment ``name`` and ``replicas``.
    """
    from kubernetes.client import AppsV1Api

    apps = AppsV1Api(api_client=api_client)
    dep_list = apps.list_namespaced_deployment(namespace=namespace)
    return [
        {
            "name": dep.metadata.name,
            "replicas": dep.spec.replicas if dep.spec else 0,
        }
        for dep in dep_list.items
        if dep.metadata
    ]


def list_services(api_client: Any, namespace: str = "default") -> list[dict[str, Any]]:
    """List services in a given namespace.

    Args:
        api_client: A configured ``kubernetes.client.ApiClient``.
        namespace: Target namespace.

    Returns:
        A list of dicts with service ``name`` and ``type``.
    """
    from kubernetes.client import CoreV1Api

    v1 = CoreV1Api(api_client=api_client)
    svc_list = v1.list_namespaced_service(namespace=namespace)
    return [
        {
            "name": svc.metadata.name,
            "type": svc.spec.type if svc.spec else "Unknown",
        }
        for svc in svc_list.items
        if svc.metadata
    ]
