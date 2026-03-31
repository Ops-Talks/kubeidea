"""Kubernetes API client wrapper and kubeconfig loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel


class KubeContext(BaseModel):
    """Represents a single kubeconfig context."""

    name: str
    cluster: str
    user: str
    namespace: str | None = None


class KubeConfigManager:
    """Manages kubeconfig parsing and context enumeration.

    Attributes:
        kubeconfig_path: Path to the kubeconfig file.
    """

    def __init__(self, kubeconfig_path: str | None = None) -> None:
        self.kubeconfig_path = kubeconfig_path or str(
            Path.home() / ".kube" / "config"
        )

    def list_contexts(self) -> list[KubeContext]:
        """List all available contexts from the kubeconfig file.

        Returns:
            A list of ``KubeContext`` instances parsed from the kubeconfig.
        """
        try:
            from kubernetes.config import list_kube_config_contexts

            contexts, _ = list_kube_config_contexts(
                config_file=self.kubeconfig_path
            )
            return [
                KubeContext(
                    name=ctx.get("name", ""),
                    cluster=ctx.get("context", {}).get("cluster", ""),
                    user=ctx.get("context", {}).get("user", ""),
                    namespace=ctx.get("context", {}).get("namespace"),
                )
                for ctx in contexts
            ]
        except Exception:
            return []

    def load_context(self, context_name: str) -> Any:
        """Load a specific kubeconfig context and return an API client.

        Args:
            context_name: The context name to activate.

        Returns:
            A configured ``kubernetes.client.ApiClient`` for the given context.
        """
        from kubernetes import client, config

        config.load_kube_config(
            config_file=self.kubeconfig_path, context=context_name
        )
        return client.ApiClient()
