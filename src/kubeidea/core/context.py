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
    """

    current_context: str | None = None
    current_namespace: str = "default"
    settings: dict[str, Any] = field(default_factory=dict)

    def switch_context(self, context_name: str) -> None:
        """Switch the active Kubernetes context.

        Args:
            context_name: Name of the kubeconfig context to activate.
        """
        self.current_context = context_name

    def switch_namespace(self, namespace: str) -> None:
        """Switch the active namespace.

        Args:
            namespace: Namespace to select.
        """
        self.current_namespace = namespace
