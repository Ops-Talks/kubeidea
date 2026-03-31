"""RBAC inspection — map roles, bindings, and simulate access."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RoleInfo(BaseModel):
    """Summary of a Role or ClusterRole."""

    name: str
    namespace: str | None = None
    rules: list[dict[str, Any]]
    is_cluster_role: bool = False


class BindingInfo(BaseModel):
    """Summary of a RoleBinding or ClusterRoleBinding."""

    name: str
    namespace: str | None = None
    role_name: str
    subjects: list[dict[str, str]]
    is_cluster_binding: bool = False


class RBACInspector:
    """Inspect RBAC roles and bindings in a Kubernetes cluster.

    Args:
        api_client: A configured ``kubernetes.client.ApiClient``.
    """

    def __init__(self, api_client: Any) -> None:
        self._api_client = api_client

    def list_cluster_roles(self) -> list[RoleInfo]:
        """List all ClusterRoles.

        Returns:
            A list of ``RoleInfo`` objects for cluster-level roles.
        """
        from kubernetes.client import RbacAuthorizationV1Api

        api = RbacAuthorizationV1Api(api_client=self._api_client)
        roles = api.list_cluster_role()
        return [
            RoleInfo(
                name=r.metadata.name,
                rules=[
                    {
                        "api_groups": rule.api_groups or [],
                        "resources": rule.resources or [],
                        "verbs": rule.verbs or [],
                    }
                    for rule in (r.rules or [])
                ],
                is_cluster_role=True,
            )
            for r in roles.items
            if r.metadata
        ]

    def list_roles(self, namespace: str = "default") -> list[RoleInfo]:
        """List Roles in a namespace.

        Args:
            namespace: Target namespace.

        Returns:
            A list of ``RoleInfo`` objects for namespace-level roles.
        """
        from kubernetes.client import RbacAuthorizationV1Api

        api = RbacAuthorizationV1Api(api_client=self._api_client)
        roles = api.list_namespaced_role(namespace=namespace)
        return [
            RoleInfo(
                name=r.metadata.name,
                namespace=namespace,
                rules=[
                    {
                        "api_groups": rule.api_groups or [],
                        "resources": rule.resources or [],
                        "verbs": rule.verbs or [],
                    }
                    for rule in (r.rules or [])
                ],
            )
            for r in roles.items
            if r.metadata
        ]

    def can_i(self, verb: str, resource: str, namespace: str = "default") -> bool:
        """Check whether the current user can perform an action (SelfSubjectAccessReview).

        Args:
            verb: The API verb (e.g. ``"get"``, ``"list"``, ``"create"``).
            resource: The resource type (e.g. ``"pods"``, ``"deployments"``).
            namespace: Namespace for the check.

        Returns:
            ``True`` if the action is allowed.
        """
        from kubernetes.client import (
            AuthorizationV1Api,
            V1ResourceAttributes,
            V1SelfSubjectAccessReview,
            V1SelfSubjectAccessReviewSpec,
        )

        api = AuthorizationV1Api(api_client=self._api_client)
        review = V1SelfSubjectAccessReview(
            spec=V1SelfSubjectAccessReviewSpec(
                resource_attributes=V1ResourceAttributes(
                    namespace=namespace,
                    verb=verb,
                    resource=resource,
                )
            )
        )
        result = api.create_self_subject_access_review(body=review)
        return bool(result.status and result.status.allowed)
