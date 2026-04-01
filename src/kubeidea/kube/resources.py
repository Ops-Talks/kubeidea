"""Kubernetes resource listing, inspection, and mutation helpers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import yaml

from kubeidea.kube.models import (
    ConfigMapInfo,
    ContainerInfo,
    CronJobInfo,
    DaemonSetInfo,
    DeploymentInfo,
    EventInfo,
    HPAInfo,
    IngressInfo,
    JobInfo,
    NetworkPolicyInfo,
    NodeInfo,
    PersistentVolumeClaimInfo,
    PersistentVolumeInfo,
    PodInfo,
    SecretInfo,
    ServiceAccountInfo,
    ServiceInfo,
    StatefulSetInfo,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resource_age(creation_timestamp: Any) -> str:
    """Compute human-readable age from a Kubernetes creation timestamp."""
    if not creation_timestamp:
        return "Unknown"
    now = datetime.now(UTC)
    if hasattr(creation_timestamp, "timestamp"):
        created = (
            creation_timestamp.replace(tzinfo=UTC)
            if creation_timestamp.tzinfo is None
            else creation_timestamp
        )
    else:
        return "Unknown"
    delta = now - created
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    if days > 0:
        return f"{days}d"
    if hours > 0:
        return f"{hours}h"
    return f"{minutes}m"


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------


def list_namespaces(api_client: Any) -> list[str]:
    """List all namespaces the current user can access."""
    from kubernetes.client import CoreV1Api

    v1 = CoreV1Api(api_client=api_client)
    ns_list = v1.list_namespace()
    return sorted(ns.metadata.name for ns in ns_list.items if ns.metadata)


# ---------------------------------------------------------------------------
# Pods
# ---------------------------------------------------------------------------


def list_pods(api_client: Any, namespace: str = "default") -> list[PodInfo]:
    """List pods in a given namespace."""
    from kubernetes.client import CoreV1Api

    try:
        v1 = CoreV1Api(api_client=api_client)
        pod_list = v1.list_namespaced_pod(namespace=namespace)
    except Exception:
        logger.exception("Failed to list pods in namespace %s", namespace)
        return []

    results: list[PodInfo] = []
    for pod in pod_list.items:
        if not pod.metadata:
            continue
        containers: list[ContainerInfo] = []
        total_restarts = 0
        ready_count = 0
        total_count = 0
        if pod.status and pod.status.container_statuses:
            for cs in pod.status.container_statuses:
                total_count += 1
                total_restarts += cs.restart_count or 0
                if cs.ready:
                    ready_count += 1
                state = "Waiting"
                if cs.state:
                    if cs.state.running:
                        state = "Running"
                    elif cs.state.terminated:
                        state = "Terminated"
                containers.append(
                    ContainerInfo(
                        name=cs.name,
                        image=cs.image or "",
                        ready=bool(cs.ready),
                        restart_count=cs.restart_count or 0,
                        state=state,
                    )
                )
        elif pod.spec and pod.spec.containers:
            total_count = len(pod.spec.containers)
        results.append(
            PodInfo(
                name=pod.metadata.name,
                namespace=pod.metadata.namespace or namespace,
                status=pod.status.phase if pod.status else "Unknown",
                ready=f"{ready_count}/{total_count}",
                restarts=total_restarts,
                age=_resource_age(pod.metadata.creation_timestamp),
                ip=pod.status.pod_ip if pod.status else None,
                node=pod.spec.node_name if pod.spec else None,
                labels=dict(pod.metadata.labels or {}),
                containers=containers,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Deployments
# ---------------------------------------------------------------------------


def list_deployments(api_client: Any, namespace: str = "default") -> list[DeploymentInfo]:
    """List deployments in a given namespace."""
    from kubernetes.client import AppsV1Api

    try:
        apps = AppsV1Api(api_client=api_client)
        dep_list = apps.list_namespaced_deployment(namespace=namespace)
    except Exception:
        logger.exception("Failed to list deployments in namespace %s", namespace)
        return []

    return [
        DeploymentInfo(
            name=dep.metadata.name,
            namespace=dep.metadata.namespace or namespace,
            replicas=dep.spec.replicas if dep.spec else 0,
            ready_replicas=dep.status.ready_replicas or 0 if dep.status else 0,
            available_replicas=dep.status.available_replicas or 0 if dep.status else 0,
            age=_resource_age(dep.metadata.creation_timestamp),
            labels=dict(dep.metadata.labels or {}),
            strategy=dep.spec.strategy.type if dep.spec and dep.spec.strategy else "RollingUpdate",
        )
        for dep in dep_list.items
        if dep.metadata
    ]


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


def list_services(api_client: Any, namespace: str = "default") -> list[ServiceInfo]:
    """List services in a given namespace."""
    from kubernetes.client import CoreV1Api

    try:
        v1 = CoreV1Api(api_client=api_client)
        svc_list = v1.list_namespaced_service(namespace=namespace)
    except Exception:
        logger.exception("Failed to list services in namespace %s", namespace)
        return []

    results: list[ServiceInfo] = []
    for svc in svc_list.items:
        if not svc.metadata:
            continue
        ports: list[str] = []
        if svc.spec and svc.spec.ports:
            for p in svc.spec.ports:
                ports.append(f"{p.port}/{p.protocol or 'TCP'}")
        results.append(
            ServiceInfo(
                name=svc.metadata.name,
                namespace=svc.metadata.namespace or namespace,
                type=svc.spec.type if svc.spec else "Unknown",
                cluster_ip=svc.spec.cluster_ip if svc.spec else None,
                ports=ports,
                selector=dict(svc.spec.selector or {}) if svc.spec else {},
                age=_resource_age(svc.metadata.creation_timestamp),
            )
        )
    return results


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def list_nodes(api_client: Any) -> list[NodeInfo]:
    """List all cluster nodes."""
    from kubernetes.client import CoreV1Api

    try:
        v1 = CoreV1Api(api_client=api_client)
        node_list = v1.list_node()
    except Exception:
        logger.exception("Failed to list nodes")
        return []

    results: list[NodeInfo] = []
    for node in node_list.items:
        if not node.metadata:
            continue
        status = "NotReady"
        if node.status and node.status.conditions:
            for cond in node.status.conditions:
                if cond.type == "Ready" and cond.status == "True":
                    status = "Ready"
        roles: list[str] = []
        for lbl in (node.metadata.labels or {}):
            if lbl.startswith("node-role.kubernetes.io/"):
                roles.append(lbl.split("/", 1)[1])
        ni = node.status.node_info if node.status and node.status.node_info else None
        cap = node.status.capacity if node.status else None
        results.append(
            NodeInfo(
                name=node.metadata.name,
                status=status,
                roles=roles,
                version=ni.kubelet_version if ni else "",
                os_image=ni.os_image if ni else "",
                kernel=ni.kernel_version if ni else "",
                container_runtime=ni.container_runtime_version if ni else "",
                cpu_capacity=str(cap.get("cpu", "")) if cap else "",
                memory_capacity=str(cap.get("memory", "")) if cap else "",
                age=_resource_age(node.metadata.creation_timestamp),
            )
        )
    return results


# ---------------------------------------------------------------------------
# ConfigMaps
# ---------------------------------------------------------------------------


def list_configmaps(api_client: Any, namespace: str = "default") -> list[ConfigMapInfo]:
    """List ConfigMaps in a given namespace."""
    from kubernetes.client import CoreV1Api

    try:
        v1 = CoreV1Api(api_client=api_client)
        cm_list = v1.list_namespaced_config_map(namespace=namespace)
    except Exception:
        logger.exception("Failed to list configmaps in namespace %s", namespace)
        return []

    return [
        ConfigMapInfo(
            name=cm.metadata.name,
            namespace=cm.metadata.namespace or namespace,
            data_keys=list((cm.data or {}).keys()),
            age=_resource_age(cm.metadata.creation_timestamp),
        )
        for cm in cm_list.items
        if cm.metadata
    ]


# ---------------------------------------------------------------------------
# Secrets (NEVER expose values)
# ---------------------------------------------------------------------------


def list_secrets(api_client: Any, namespace: str = "default") -> list[SecretInfo]:
    """List Secrets in a given namespace. Only key names are returned — never values."""
    from kubernetes.client import CoreV1Api

    try:
        v1 = CoreV1Api(api_client=api_client)
        sec_list = v1.list_namespaced_secret(namespace=namespace)
    except Exception:
        logger.exception("Failed to list secrets in namespace %s", namespace)
        return []

    return [
        SecretInfo(
            name=sec.metadata.name,
            namespace=sec.metadata.namespace or namespace,
            type=sec.type or "Opaque",
            data_keys=list((sec.data or {}).keys()),
            age=_resource_age(sec.metadata.creation_timestamp),
        )
        for sec in sec_list.items
        if sec.metadata
    ]


# ---------------------------------------------------------------------------
# Ingresses
# ---------------------------------------------------------------------------


def list_ingresses(api_client: Any, namespace: str = "default") -> list[IngressInfo]:
    """List Ingresses in a given namespace."""
    from kubernetes.client import NetworkingV1Api

    try:
        net = NetworkingV1Api(api_client=api_client)
        ing_list = net.list_namespaced_ingress(namespace=namespace)
    except Exception:
        logger.exception("Failed to list ingresses in namespace %s", namespace)
        return []

    results: list[IngressInfo] = []
    for ing in ing_list.items:
        if not ing.metadata:
            continue
        hosts: list[str] = []
        paths: list[str] = []
        has_tls = bool(ing.spec and ing.spec.tls)
        if ing.spec and ing.spec.rules:
            for rule in ing.spec.rules:
                if rule.host:
                    hosts.append(rule.host)
                if rule.http and rule.http.paths:
                    for p in rule.http.paths:
                        paths.append(p.path or "/")
        results.append(
            IngressInfo(
                name=ing.metadata.name,
                namespace=ing.metadata.namespace or namespace,
                hosts=hosts,
                paths=paths,
                tls=has_tls,
                age=_resource_age(ing.metadata.creation_timestamp),
            )
        )
    return results


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


def list_jobs(api_client: Any, namespace: str = "default") -> list[JobInfo]:
    """List Jobs in a given namespace."""
    from kubernetes.client import BatchV1Api

    try:
        batch = BatchV1Api(api_client=api_client)
        job_list = batch.list_namespaced_job(namespace=namespace)
    except Exception:
        logger.exception("Failed to list jobs in namespace %s", namespace)
        return []

    results: list[JobInfo] = []
    for job in job_list.items:
        if not job.metadata:
            continue
        desired = job.spec.completions if job.spec and job.spec.completions else 1
        succeeded = job.status.succeeded or 0 if job.status else 0
        if job.status and job.status.conditions:
            for cond in job.status.conditions:
                if cond.type == "Failed" and cond.status == "True":
                    status = "Failed"
                    break
                if cond.type == "Complete" and cond.status == "True":
                    status = "Complete"
                    break
            else:
                status = "Running"
        elif succeeded >= desired:
            status = "Complete"
        else:
            status = "Running"
        results.append(
            JobInfo(
                name=job.metadata.name,
                namespace=job.metadata.namespace or namespace,
                completions=f"{succeeded}/{desired}",
                status=status,
                age=_resource_age(job.metadata.creation_timestamp),
            )
        )
    return results


# ---------------------------------------------------------------------------
# CronJobs
# ---------------------------------------------------------------------------


def list_cronjobs(api_client: Any, namespace: str = "default") -> list[CronJobInfo]:
    """List CronJobs in a given namespace."""
    from kubernetes.client import BatchV1Api

    try:
        batch = BatchV1Api(api_client=api_client)
        cj_list = batch.list_namespaced_cron_job(namespace=namespace)
    except Exception:
        logger.exception("Failed to list cronjobs in namespace %s", namespace)
        return []

    return [
        CronJobInfo(
            name=cj.metadata.name,
            namespace=cj.metadata.namespace or namespace,
            schedule=cj.spec.schedule if cj.spec else "",
            suspend=bool(cj.spec.suspend) if cj.spec else False,
            active=len(cj.status.active or []) if cj.status else 0,
            last_schedule=str(cj.status.last_schedule_time) if cj.status and cj.status.last_schedule_time else None,
            age=_resource_age(cj.metadata.creation_timestamp),
        )
        for cj in cj_list.items
        if cj.metadata
    ]


# ---------------------------------------------------------------------------
# StatefulSets
# ---------------------------------------------------------------------------


def list_statefulsets(api_client: Any, namespace: str = "default") -> list[StatefulSetInfo]:
    """List StatefulSets in a given namespace."""
    from kubernetes.client import AppsV1Api

    try:
        apps = AppsV1Api(api_client=api_client)
        ss_list = apps.list_namespaced_stateful_set(namespace=namespace)
    except Exception:
        logger.exception("Failed to list statefulsets in namespace %s", namespace)
        return []

    return [
        StatefulSetInfo(
            name=ss.metadata.name,
            namespace=ss.metadata.namespace or namespace,
            replicas=ss.spec.replicas if ss.spec else 0,
            ready_replicas=ss.status.ready_replicas or 0 if ss.status else 0,
            age=_resource_age(ss.metadata.creation_timestamp),
        )
        for ss in ss_list.items
        if ss.metadata
    ]


# ---------------------------------------------------------------------------
# DaemonSets
# ---------------------------------------------------------------------------


def list_daemonsets(api_client: Any, namespace: str = "default") -> list[DaemonSetInfo]:
    """List DaemonSets in a given namespace."""
    from kubernetes.client import AppsV1Api

    try:
        apps = AppsV1Api(api_client=api_client)
        ds_list = apps.list_namespaced_daemon_set(namespace=namespace)
    except Exception:
        logger.exception("Failed to list daemonsets in namespace %s", namespace)
        return []

    return [
        DaemonSetInfo(
            name=ds.metadata.name,
            namespace=ds.metadata.namespace or namespace,
            desired=ds.status.desired_number_scheduled or 0 if ds.status else 0,
            current=ds.status.current_number_scheduled or 0 if ds.status else 0,
            ready=ds.status.number_ready or 0 if ds.status else 0,
            age=_resource_age(ds.metadata.creation_timestamp),
        )
        for ds in ds_list.items
        if ds.metadata
    ]


# ---------------------------------------------------------------------------
# PersistentVolumes
# ---------------------------------------------------------------------------


def list_persistentvolumes(api_client: Any) -> list[PersistentVolumeInfo]:
    """List all PersistentVolumes."""
    from kubernetes.client import CoreV1Api

    try:
        v1 = CoreV1Api(api_client=api_client)
        pv_list = v1.list_persistent_volume()
    except Exception:
        logger.exception("Failed to list persistent volumes")
        return []

    results: list[PersistentVolumeInfo] = []
    for pv in pv_list.items:
        if not pv.metadata:
            continue
        cap = pv.spec.capacity if pv.spec else None
        claim_ref = pv.spec.claim_ref if pv.spec else None
        claim = f"{claim_ref.namespace}/{claim_ref.name}" if claim_ref else None
        results.append(
            PersistentVolumeInfo(
                name=pv.metadata.name,
                capacity=str(cap.get("storage", "")) if cap else "",
                access_modes=list(pv.spec.access_modes or []) if pv.spec else [],
                reclaim_policy=pv.spec.persistent_volume_reclaim_policy or "" if pv.spec else "",
                status=pv.status.phase if pv.status else "Unknown",
                storage_class=pv.spec.storage_class_name if pv.spec else None,
                claim=claim,
                age=_resource_age(pv.metadata.creation_timestamp),
            )
        )
    return results


# ---------------------------------------------------------------------------
# PersistentVolumeClaims
# ---------------------------------------------------------------------------


def list_persistentvolumeclaims(api_client: Any, namespace: str = "default") -> list[PersistentVolumeClaimInfo]:
    """List PersistentVolumeClaims in a given namespace."""
    from kubernetes.client import CoreV1Api

    try:
        v1 = CoreV1Api(api_client=api_client)
        pvc_list = v1.list_namespaced_persistent_volume_claim(namespace=namespace)
    except Exception:
        logger.exception("Failed to list PVCs in namespace %s", namespace)
        return []

    results: list[PersistentVolumeClaimInfo] = []
    for pvc in pvc_list.items:
        if not pvc.metadata:
            continue
        cap = pvc.status.capacity if pvc.status and pvc.status.capacity else None
        results.append(
            PersistentVolumeClaimInfo(
                name=pvc.metadata.name,
                namespace=pvc.metadata.namespace or namespace,
                status=pvc.status.phase if pvc.status else "Pending",
                volume=pvc.spec.volume_name if pvc.spec else None,
                capacity=str(cap.get("storage", "")) if cap else None,
                access_modes=list(pvc.status.access_modes or []) if pvc.status else [],
                storage_class=pvc.spec.storage_class_name if pvc.spec else None,
                age=_resource_age(pvc.metadata.creation_timestamp),
            )
        )
    return results


# ---------------------------------------------------------------------------
# HorizontalPodAutoscalers
# ---------------------------------------------------------------------------


def list_hpa(api_client: Any, namespace: str = "default") -> list[HPAInfo]:
    """List HorizontalPodAutoscalers in a given namespace."""
    from kubernetes.client import AutoscalingV2Api

    try:
        auto = AutoscalingV2Api(api_client=api_client)
        hpa_list = auto.list_namespaced_horizontal_pod_autoscaler(namespace=namespace)
    except Exception:
        logger.exception("Failed to list HPAs in namespace %s", namespace)
        return []

    return [
        HPAInfo(
            name=h.metadata.name,
            namespace=h.metadata.namespace or namespace,
            target=(
                f"{h.spec.scale_target_ref.kind}/{h.spec.scale_target_ref.name}"
                if h.spec and h.spec.scale_target_ref
                else ""
            ),
            min_replicas=h.spec.min_replicas or 1 if h.spec else 1,
            max_replicas=h.spec.max_replicas if h.spec else 0,
            current_replicas=h.status.current_replicas or 0 if h.status else 0,
            age=_resource_age(h.metadata.creation_timestamp),
        )
        for h in hpa_list.items
        if h.metadata
    ]


# ---------------------------------------------------------------------------
# NetworkPolicies
# ---------------------------------------------------------------------------


def list_networkpolicies(api_client: Any, namespace: str = "default") -> list[NetworkPolicyInfo]:
    """List NetworkPolicies in a given namespace."""
    from kubernetes.client import NetworkingV1Api

    try:
        net = NetworkingV1Api(api_client=api_client)
        np_list = net.list_namespaced_network_policy(namespace=namespace)
    except Exception:
        logger.exception("Failed to list network policies in namespace %s", namespace)
        return []

    return [
        NetworkPolicyInfo(
            name=np.metadata.name,
            namespace=np.metadata.namespace or namespace,
            pod_selector=dict((np.spec.pod_selector.match_labels or {}) if np.spec and np.spec.pod_selector else {}),
            policy_types=list(np.spec.policy_types or []) if np.spec else [],
            age=_resource_age(np.metadata.creation_timestamp),
        )
        for np in np_list.items
        if np.metadata
    ]


# ---------------------------------------------------------------------------
# ServiceAccounts
# ---------------------------------------------------------------------------


def list_serviceaccounts(api_client: Any, namespace: str = "default") -> list[ServiceAccountInfo]:
    """List ServiceAccounts in a given namespace."""
    from kubernetes.client import CoreV1Api

    try:
        v1 = CoreV1Api(api_client=api_client)
        sa_list = v1.list_namespaced_service_account(namespace=namespace)
    except Exception:
        logger.exception("Failed to list service accounts in namespace %s", namespace)
        return []

    return [
        ServiceAccountInfo(
            name=sa.metadata.name,
            namespace=sa.metadata.namespace or namespace,
            secrets=len(sa.secrets or []) if sa.secrets else 0,
            age=_resource_age(sa.metadata.creation_timestamp),
        )
        for sa in sa_list.items
        if sa.metadata
    ]


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


def list_events(
    api_client: Any,
    namespace: str = "default",
    involved_object_name: str | None = None,
) -> list[EventInfo]:
    """List Events in a given namespace, optionally filtered by involved object."""
    from kubernetes.client import CoreV1Api

    try:
        v1 = CoreV1Api(api_client=api_client)
        if involved_object_name:
            ev_list = v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={involved_object_name}",
            )
        else:
            ev_list = v1.list_namespaced_event(namespace=namespace)
    except Exception:
        logger.exception("Failed to list events in namespace %s", namespace)
        return []

    results: list[EventInfo] = []
    for ev in ev_list.items:
        if not ev.metadata:
            continue
        involved = ""
        if ev.involved_object:
            involved = f"{ev.involved_object.kind or ''}/{ev.involved_object.name or ''}"
        source_component = ""
        if ev.source:
            source_component = ev.source.component or ""
        results.append(
            EventInfo(
                namespace=ev.metadata.namespace,
                type=ev.type or "Normal",
                reason=ev.reason or "",
                message=ev.message or "",
                source=source_component,
                involved_object=involved,
                count=ev.count or 1,
                first_seen=str(ev.first_timestamp or ""),
                last_seen=str(ev.last_timestamp or ""),
            )
        )
    return results


# ---------------------------------------------------------------------------
# Resource YAML
# ---------------------------------------------------------------------------

_KIND_API_MAP: dict[str, tuple[str, str]] = {
    "pod": ("CoreV1Api", "read_namespaced_pod"),
    "deployment": ("AppsV1Api", "read_namespaced_deployment"),
    "service": ("CoreV1Api", "read_namespaced_service"),
    "configmap": ("CoreV1Api", "read_namespaced_config_map"),
    "secret": ("CoreV1Api", "read_namespaced_secret"),
    "ingress": ("NetworkingV1Api", "read_namespaced_ingress"),
    "job": ("BatchV1Api", "read_namespaced_job"),
    "cronjob": ("BatchV1Api", "read_namespaced_cron_job"),
    "statefulset": ("AppsV1Api", "read_namespaced_stateful_set"),
    "daemonset": ("AppsV1Api", "read_namespaced_daemon_set"),
    "persistentvolumeclaim": ("CoreV1Api", "read_namespaced_persistent_volume_claim"),
    "horizontalpodautoscaler": ("AutoscalingV2Api", "read_namespaced_horizontal_pod_autoscaler"),
    "networkpolicy": ("NetworkingV1Api", "read_namespaced_network_policy"),
    "serviceaccount": ("CoreV1Api", "read_namespaced_service_account"),
}

_KIND_CLUSTER_API_MAP: dict[str, tuple[str, str]] = {
    "node": ("CoreV1Api", "read_node"),
    "persistentvolume": ("CoreV1Api", "read_persistent_volume"),
}


def get_resource_yaml(api_client: Any, kind: str, name: str, namespace: str = "default") -> str:
    """Get the YAML representation of a Kubernetes resource.

    Args:
        api_client: A configured ``kubernetes.client.ApiClient``.
        kind: Resource kind (e.g. ``"pod"``, ``"deployment"``).
        name: Resource name.
        namespace: Target namespace (ignored for cluster-scoped resources).

    Returns:
        YAML string of the resource.
    """
    import kubernetes.client as k8s_client

    kind_lower = kind.lower()

    try:
        if kind_lower in _KIND_API_MAP:
            api_class_name, method_name = _KIND_API_MAP[kind_lower]
            api = getattr(k8s_client, api_class_name)(api_client=api_client)
            resource = getattr(api, method_name)(name=name, namespace=namespace)
        elif kind_lower in _KIND_CLUSTER_API_MAP:
            api_class_name, method_name = _KIND_CLUSTER_API_MAP[kind_lower]
            api = getattr(k8s_client, api_class_name)(api_client=api_client)
            resource = getattr(api, method_name)(name=name)
        else:
            return f"# Unsupported kind: {kind}"

        raw = api_client.sanitize_for_serialization(resource)
        return yaml.safe_dump(raw, default_flow_style=False, sort_keys=False)  # type: ignore[no-any-return]
    except Exception:
        logger.exception("Failed to get YAML for %s/%s in %s", kind, name, namespace)
        return f"# Error retrieving {kind}/{name}"


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

_KIND_DELETE_MAP: dict[str, tuple[str, str]] = {
    "pod": ("CoreV1Api", "delete_namespaced_pod"),
    "deployment": ("AppsV1Api", "delete_namespaced_deployment"),
    "service": ("CoreV1Api", "delete_namespaced_service"),
    "configmap": ("CoreV1Api", "delete_namespaced_config_map"),
    "secret": ("CoreV1Api", "delete_namespaced_secret"),
    "ingress": ("NetworkingV1Api", "delete_namespaced_ingress"),
    "job": ("BatchV1Api", "delete_namespaced_job"),
    "cronjob": ("BatchV1Api", "delete_namespaced_cron_job"),
    "statefulset": ("AppsV1Api", "delete_namespaced_stateful_set"),
    "daemonset": ("AppsV1Api", "delete_namespaced_daemon_set"),
    "persistentvolumeclaim": ("CoreV1Api", "delete_namespaced_persistent_volume_claim"),
    "horizontalpodautoscaler": ("AutoscalingV2Api", "delete_namespaced_horizontal_pod_autoscaler"),
    "networkpolicy": ("NetworkingV1Api", "delete_namespaced_network_policy"),
    "serviceaccount": ("CoreV1Api", "delete_namespaced_service_account"),
}

_KIND_DELETE_CLUSTER_MAP: dict[str, tuple[str, str]] = {
    "namespace": ("CoreV1Api", "delete_namespace"),
    "node": ("CoreV1Api", "delete_node"),
    "persistentvolume": ("CoreV1Api", "delete_persistent_volume"),
}


def delete_resource(api_client: Any, kind: str, name: str, namespace: str = "default") -> bool:
    """Delete a Kubernetes resource.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    import kubernetes.client as k8s_client

    kind_lower = kind.lower()
    try:
        if kind_lower in _KIND_DELETE_MAP:
            api_class_name, method_name = _KIND_DELETE_MAP[kind_lower]
            api = getattr(k8s_client, api_class_name)(api_client=api_client)
            getattr(api, method_name)(name=name, namespace=namespace)
        elif kind_lower in _KIND_DELETE_CLUSTER_MAP:
            api_class_name, method_name = _KIND_DELETE_CLUSTER_MAP[kind_lower]
            api = getattr(k8s_client, api_class_name)(api_client=api_client)
            getattr(api, method_name)(name=name)
        else:
            logger.warning("delete_resource: unsupported kind %s", kind)
            return False
        return True
    except Exception:
        logger.exception("Failed to delete %s/%s in %s", kind, name, namespace)
        return False


def scale_resource(
    api_client: Any,
    kind: str,
    name: str,
    namespace: str,
    replicas: int,
) -> bool:
    """Scale a Deployment, StatefulSet, or ReplicaSet.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    from kubernetes.client import AppsV1Api

    apps = AppsV1Api(api_client=api_client)
    body = {"spec": {"replicas": replicas}}
    kind_lower = kind.lower()
    try:
        if kind_lower == "deployment":
            apps.patch_namespaced_deployment_scale(name=name, namespace=namespace, body=body)
        elif kind_lower == "statefulset":
            apps.patch_namespaced_stateful_set_scale(name=name, namespace=namespace, body=body)
        elif kind_lower == "replicaset":
            apps.patch_namespaced_replica_set_scale(name=name, namespace=namespace, body=body)
        else:
            logger.warning("scale_resource: unsupported kind %s", kind)
            return False
        return True
    except Exception:
        logger.exception("Failed to scale %s/%s in %s", kind, name, namespace)
        return False


def restart_resource(api_client: Any, kind: str, name: str, namespace: str) -> bool:
    """Rollout restart a Deployment, StatefulSet, or DaemonSet.

    Patches the pod template annotation with the current timestamp to trigger
    a rolling restart.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    from kubernetes.client import AppsV1Api

    apps = AppsV1Api(api_client=api_client)
    now = datetime.now(UTC).isoformat()
    body = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {"kubectl.kubernetes.io/restartedAt": now},
                },
            },
        },
    }
    kind_lower = kind.lower()
    try:
        if kind_lower == "deployment":
            apps.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
        elif kind_lower == "statefulset":
            apps.patch_namespaced_stateful_set(name=name, namespace=namespace, body=body)
        elif kind_lower == "daemonset":
            apps.patch_namespaced_daemon_set(name=name, namespace=namespace, body=body)
        else:
            logger.warning("restart_resource: unsupported kind %s", kind)
            return False
        return True
    except Exception:
        logger.exception("Failed to restart %s/%s in %s", kind, name, namespace)
        return False


# ---------------------------------------------------------------------------
# Apply (create-or-replace) helpers
# ---------------------------------------------------------------------------

_KIND_CREATE_MAP: dict[str, tuple[str, str]] = {
    "pod": ("CoreV1Api", "create_namespaced_pod"),
    "deployment": ("AppsV1Api", "create_namespaced_deployment"),
    "service": ("CoreV1Api", "create_namespaced_service"),
    "configmap": ("CoreV1Api", "create_namespaced_config_map"),
    "secret": ("CoreV1Api", "create_namespaced_secret"),
    "ingress": ("NetworkingV1Api", "create_namespaced_ingress"),
    "job": ("BatchV1Api", "create_namespaced_job"),
    "cronjob": ("BatchV1Api", "create_namespaced_cron_job"),
    "statefulset": ("AppsV1Api", "create_namespaced_stateful_set"),
    "daemonset": ("AppsV1Api", "create_namespaced_daemon_set"),
    "persistentvolumeclaim": ("CoreV1Api", "create_namespaced_persistent_volume_claim"),
    "horizontalpodautoscaler": ("AutoscalingV2Api", "create_namespaced_horizontal_pod_autoscaler"),
    "networkpolicy": ("NetworkingV1Api", "create_namespaced_network_policy"),
    "serviceaccount": ("CoreV1Api", "create_namespaced_service_account"),
}

_KIND_CREATE_CLUSTER_MAP: dict[str, tuple[str, str]] = {
    "namespace": ("CoreV1Api", "create_namespace"),
    "node": ("CoreV1Api", "create_node"),
    "persistentvolume": ("CoreV1Api", "create_persistent_volume"),
}

_KIND_REPLACE_MAP: dict[str, tuple[str, str]] = {
    "pod": ("CoreV1Api", "replace_namespaced_pod"),
    "deployment": ("AppsV1Api", "replace_namespaced_deployment"),
    "service": ("CoreV1Api", "replace_namespaced_service"),
    "configmap": ("CoreV1Api", "replace_namespaced_config_map"),
    "secret": ("CoreV1Api", "replace_namespaced_secret"),
    "ingress": ("NetworkingV1Api", "replace_namespaced_ingress"),
    "job": ("BatchV1Api", "replace_namespaced_job"),
    "cronjob": ("BatchV1Api", "replace_namespaced_cron_job"),
    "statefulset": ("AppsV1Api", "replace_namespaced_stateful_set"),
    "daemonset": ("AppsV1Api", "replace_namespaced_daemon_set"),
    "persistentvolumeclaim": ("CoreV1Api", "replace_namespaced_persistent_volume_claim"),
    "horizontalpodautoscaler": ("AutoscalingV2Api", "replace_namespaced_horizontal_pod_autoscaler"),
    "networkpolicy": ("NetworkingV1Api", "replace_namespaced_network_policy"),
    "serviceaccount": ("CoreV1Api", "replace_namespaced_service_account"),
}

_KIND_REPLACE_CLUSTER_MAP: dict[str, tuple[str, str]] = {
    "namespace": ("CoreV1Api", "replace_namespace"),
    "node": ("CoreV1Api", "replace_node"),
    "persistentvolume": ("CoreV1Api", "replace_persistent_volume"),
}


def apply_resource(api_client: Any, manifest_yaml: str) -> bool:
    """Apply a Kubernetes resource from a YAML manifest string.

    Attempts to **create** the resource first.  If creation fails with HTTP
    409 (Conflict — the resource already exists), falls back to **replace**.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    import kubernetes.client as k8s_client
    from kubernetes.client.rest import ApiException

    try:
        doc: dict[str, Any] = yaml.safe_load(manifest_yaml)
    except yaml.YAMLError:
        logger.exception("apply_resource: failed to parse YAML manifest")
        return False

    if not isinstance(doc, dict):
        logger.warning("apply_resource: manifest is not a YAML mapping")
        return False

    kind: str | None = doc.get("kind")
    metadata: dict[str, Any] = doc.get("metadata", {})
    name: str | None = metadata.get("name")

    if not kind or not name:
        logger.warning("apply_resource: manifest missing 'kind' or 'metadata.name'")
        return False

    kind_lower = kind.lower()
    namespace: str = metadata.get("namespace", "default")

    # Resolve API class + method names
    if kind_lower in _KIND_CREATE_MAP:
        create_api_cls, create_method = _KIND_CREATE_MAP[kind_lower]
        replace_api_cls, replace_method = _KIND_REPLACE_MAP[kind_lower]
        is_namespaced = True
    elif kind_lower in _KIND_CREATE_CLUSTER_MAP:
        create_api_cls, create_method = _KIND_CREATE_CLUSTER_MAP[kind_lower]
        replace_api_cls, replace_method = _KIND_REPLACE_CLUSTER_MAP[kind_lower]
        is_namespaced = False
    else:
        logger.warning("apply_resource: unsupported kind %s", kind)
        return False

    # Try create first
    try:
        api = getattr(k8s_client, create_api_cls)(api_client=api_client)
        if is_namespaced:
            getattr(api, create_method)(namespace=namespace, body=doc)
        else:
            getattr(api, create_method)(body=doc)
        return True
    except ApiException as exc:
        if exc.status != 409:
            logger.exception(
                "Failed to create %s/%s in %s", kind, name, namespace,
            )
            return False

    # Conflict → replace
    try:
        api = getattr(k8s_client, replace_api_cls)(api_client=api_client)
        if is_namespaced:
            getattr(api, replace_method)(name=name, namespace=namespace, body=doc)
        else:
            getattr(api, replace_method)(name=name, body=doc)
        return True
    except Exception:
        logger.exception("Failed to replace %s/%s in %s", kind, name, namespace)
        return False
