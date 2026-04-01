"""Core application context and lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppContext:
    """Central application context holding shared state.

    Attributes:
        current_context: Active Kubernetes context name.
        current_namespace: Active namespace (default: ``"default"``).
        settings: User preferences dictionary.
        api_client: Active Kubernetes API client, set after connection.
        namespaces: Namespaces accessible with the current credentials.
        rbac_inspector: Lazily-created :class:`~kubeidea.security.rbac.RBACInspector`
            bound to the active ``api_client``.  ``None`` when disconnected.
    """

    current_context: str | None = None
    current_namespace: str = "default"
    settings: dict[str, Any] = field(default_factory=dict)
    api_client: Any | None = None
    namespaces: list[str] = field(default_factory=list)
    rbac_inspector: Any | None = None

    @property
    def connected(self) -> bool:
        """Return True if a cluster connection is active."""
        return self.api_client is not None

    def switch_context(self, context_name: str, api_client: Any, namespaces: list[str]) -> None:
        """Switch the active Kubernetes context.

        Args:
            context_name: Name of the kubeconfig context to activate.
            api_client: Configured ``kubernetes.client.ApiClient``.
            namespaces: List of accessible namespace names.
        """
        from kubeidea.security.rbac import RBACInspector

        self.current_context = context_name
        self.api_client = api_client
        self.rbac_inspector = RBACInspector(api_client)
        self.namespaces = namespaces
        if namespaces:
            self.current_namespace = namespaces[0] if "default" not in namespaces else "default"

    def switch_namespace(self, namespace: str) -> None:
        """Switch the active namespace.

        Args:
            namespace: Namespace to select.
        """
        self.current_namespace = namespace

    def disconnect(self) -> None:
        """Clear the active connection."""
        self.current_context = None
        self.api_client = None
        self.rbac_inspector = None
        self.namespaces = []
        self.current_namespace = "default"
