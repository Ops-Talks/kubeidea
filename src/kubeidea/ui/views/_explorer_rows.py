"""Row builders and visual constants for the Explorer resource list."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from kubeidea.kube.models import (
    ConfigMapInfo,
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

# ── Click-handler type alias ─────────────────────────────────────
ClickHandler = Callable[[str, Any], None]

# ── Status → color mapping ───────────────────────────────────────
STATUS_COLORS: dict[str, str] = {
    "Running": ft.Colors.GREEN_400,
    "Succeeded": ft.Colors.GREEN_200,
    "Pending": ft.Colors.ORANGE_400,
    "Failed": ft.Colors.RED_400,
    "Unknown": ft.Colors.GREY_500,
    "Ready": ft.Colors.GREEN_400,
    "NotReady": ft.Colors.RED_400,
    "Complete": ft.Colors.GREEN_200,
    "Bound": ft.Colors.GREEN_400,
    "Available": ft.Colors.GREEN_400,
    "Released": ft.Colors.ORANGE_400,
    "Normal": ft.Colors.BLUE_200,
    "Warning": ft.Colors.ORANGE_400,
}

# ── Kind → icon mapping ─────────────────────────────────────────
KIND_ICONS: dict[str, ft.IconData] = {
    "Pod": ft.Icons.WIDGETS,
    "Deployment": ft.Icons.LAYERS,
    "StatefulSet": ft.Icons.VIEW_COLUMN,
    "DaemonSet": ft.Icons.DEVICE_HUB,
    "Job": ft.Icons.WORK,
    "CronJob": ft.Icons.SCHEDULE,
    "Service": ft.Icons.DNS,
    "Ingress": ft.Icons.LANGUAGE,
    "NetworkPolicy": ft.Icons.SHIELD,
    "ConfigMap": ft.Icons.DESCRIPTION,
    "Secret": ft.Icons.LOCK,
    "ServiceAccount": ft.Icons.PERSON,
    "PersistentVolume": ft.Icons.STORAGE,
    "PersistentVolumeClaim": ft.Icons.FOLDER,
    "Node": ft.Icons.COMPUTER,
    "HorizontalPodAutoscaler": ft.Icons.AUTO_GRAPH,
    "Event": ft.Icons.EVENT,
}

# ── Kind → API kind string (for resources.py helpers) ────────────
API_KINDS: dict[str, str] = {
    "Pod": "pod",
    "Deployment": "deployment",
    "StatefulSet": "statefulset",
    "DaemonSet": "daemonset",
    "Job": "job",
    "CronJob": "cronjob",
    "Service": "service",
    "Ingress": "ingress",
    "NetworkPolicy": "networkpolicy",
    "ConfigMap": "configmap",
    "Secret": "secret",
    "ServiceAccount": "serviceaccount",
    "PersistentVolume": "persistentvolume",
    "PersistentVolumeClaim": "persistentvolumeclaim",
    "Node": "node",
    "HorizontalPodAutoscaler": "horizontalpodautoscaler",
}

# ── Plural display names ─────────────────────────────────────────
DISPLAY_PLURALS: dict[str, str] = {
    "Pod": "Pods",
    "Deployment": "Deployments",
    "StatefulSet": "StatefulSets",
    "DaemonSet": "DaemonSets",
    "Job": "Jobs",
    "CronJob": "CronJobs",
    "Service": "Services",
    "Ingress": "Ingresses",
    "NetworkPolicy": "Network Policies",
    "ConfigMap": "ConfigMaps",
    "Secret": "Secrets",
    "ServiceAccount": "Service Accounts",
    "PersistentVolume": "Persistent Volumes",
    "PersistentVolumeClaim": "PV Claims",
    "Node": "Nodes",
    "HorizontalPodAutoscaler": "HPAs",
    "Event": "Events",
}

# ── Category definitions (label, icon, resource kinds) ───────────
CATEGORIES: list[tuple[str, ft.IconData, list[str]]] = [
    (
        "Workloads",
        ft.Icons.WIDGETS,
        [
            "Pod",
            "Deployment",
            "StatefulSet",
            "DaemonSet",
            "Job",
            "CronJob",
        ],
    ),
    (
        "Networking",
        ft.Icons.LANGUAGE,
        [
            "Service",
            "Ingress",
            "NetworkPolicy",
        ],
    ),
    (
        "Config",
        ft.Icons.SETTINGS,
        [
            "ConfigMap",
            "Secret",
            "ServiceAccount",
        ],
    ),
    (
        "Storage",
        ft.Icons.STORAGE,
        [
            "PersistentVolume",
            "PersistentVolumeClaim",
        ],
    ),
    (
        "Cluster",
        ft.Icons.CLOUD,
        [
            "Node",
            "HorizontalPodAutoscaler",
            "Event",
        ],
    ),
]

# ── Tiny UI helpers ──────────────────────────────────────────────


def _pill(text: str, color: str) -> ft.Container:
    """Small coloured badge."""
    return ft.Container(
        content=ft.Text(text, size=11, color=color),
        bgcolor=ft.Colors.with_opacity(0.12, color),
        padding=ft.Padding.symmetric(horizontal=6, vertical=1),
        border_radius=4,
    )


def _dim(text: str) -> ft.Text:
    """Dimmed secondary text."""
    return ft.Text(text, size=11, color=ft.Colors.GREY_400)


def _row_box(controls: list[ft.Control], on_click: Any) -> ft.Container:
    """Wrap controls in a clickable row container."""
    return ft.Container(
        content=ft.Row(
            controls=controls,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=5),
        border_radius=4,
        on_click=on_click,
    )


# ── Section header ───────────────────────────────────────────────


def build_section_header(kind: str, count: int) -> ft.Container:
    """Section header showing resource type label and count badge."""
    icon = KIND_ICONS.get(kind, ft.Icons.CIRCLE)
    plural = DISPLAY_PLURALS.get(kind, kind + "s")
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(icon, size=16, color=ft.Colors.BLUE_200),
                ft.Text(
                    plural,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_300,
                ),
                _pill(str(count), ft.Colors.BLUE_200),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
        padding=ft.Padding.only(left=8, right=8, top=14, bottom=4),
    )


# ── Public builder ───────────────────────────────────────────────


def build_resource_row(
    kind: str,
    resource: Any,
    on_click: ClickHandler,
) -> ft.Container:
    """Build a clickable row for a single resource item."""

    def handler(_e: Any, k: str = kind, r: Any = resource) -> None:
        on_click(k, r)

    builder = _ROW_BUILDERS.get(kind, _generic_row)
    result: ft.Container = builder(resource, handler)
    return result


# ── Per-type row builders ────────────────────────────────────────


def _pod_row(pod: PodInfo, on_click: Any) -> ft.Container:
    color = STATUS_COLORS.get(pod.status, ft.Colors.GREY_500)
    return _row_box(
        [
            ft.Icon(ft.Icons.CIRCLE, size=10, color=color),
            ft.Text(pod.name, size=12, expand=True),
            _dim(pod.ready),
            _dim(f"↻{pod.restarts}"),
            _dim(pod.age),
        ],
        on_click,
    )


def _deployment_row(dep: DeploymentInfo, on_click: Any) -> ft.Container:
    ready = f"{dep.ready_replicas}/{dep.replicas}"
    return _row_box(
        [
            ft.Icon(ft.Icons.LAYERS, size=14, color=ft.Colors.BLUE_200),
            ft.Text(dep.name, size=12, expand=True),
            _dim(ready),
            _dim(dep.age),
        ],
        on_click,
    )


def _statefulset_row(ss: StatefulSetInfo, on_click: Any) -> ft.Container:
    ready = f"{ss.ready_replicas}/{ss.replicas}"
    return _row_box(
        [
            ft.Icon(ft.Icons.VIEW_COLUMN, size=14, color=ft.Colors.PURPLE_200),
            ft.Text(ss.name, size=12, expand=True),
            _dim(ready),
            _dim(ss.age),
        ],
        on_click,
    )


def _daemonset_row(ds: DaemonSetInfo, on_click: Any) -> ft.Container:
    ready = f"{ds.ready}/{ds.desired}"
    return _row_box(
        [
            ft.Icon(ft.Icons.DEVICE_HUB, size=14, color=ft.Colors.TEAL_200),
            ft.Text(ds.name, size=12, expand=True),
            _dim(ready),
            _dim(ds.age),
        ],
        on_click,
    )


def _job_row(job: JobInfo, on_click: Any) -> ft.Container:
    color = STATUS_COLORS.get(job.status, ft.Colors.GREY_500)
    return _row_box(
        [
            ft.Icon(ft.Icons.CIRCLE, size=10, color=color),
            ft.Text(job.name, size=12, expand=True),
            _dim(job.completions),
            _dim(job.age),
        ],
        on_click,
    )


def _cronjob_row(cj: CronJobInfo, on_click: Any) -> ft.Container:
    return _row_box(
        [
            ft.Icon(ft.Icons.SCHEDULE, size=14, color=ft.Colors.AMBER_200),
            ft.Text(cj.name, size=12, expand=True),
            _dim(cj.schedule),
            _dim(cj.age),
        ],
        on_click,
    )


def _service_row(svc: ServiceInfo, on_click: Any) -> ft.Container:
    ports_str = ", ".join(svc.ports[:3]) or "—"
    return _row_box(
        [
            ft.Icon(ft.Icons.DNS, size=14, color=ft.Colors.TEAL_200),
            ft.Text(svc.name, size=12, expand=True),
            _pill(svc.type, ft.Colors.TEAL_200),
            _dim(ports_str),
            _dim(svc.age),
        ],
        on_click,
    )


def _ingress_row(ing: IngressInfo, on_click: Any) -> ft.Container:
    hosts = ", ".join(ing.hosts[:2]) or "—"
    return _row_box(
        [
            ft.Icon(ft.Icons.LANGUAGE, size=14, color=ft.Colors.CYAN_200),
            ft.Text(ing.name, size=12, expand=True),
            _dim(hosts),
            _dim(ing.age),
        ],
        on_click,
    )


def _netpol_row(np_res: NetworkPolicyInfo, on_click: Any) -> ft.Container:
    types = ", ".join(np_res.policy_types) or "—"
    return _row_box(
        [
            ft.Icon(ft.Icons.SHIELD, size=14, color=ft.Colors.ORANGE_200),
            ft.Text(np_res.name, size=12, expand=True),
            _dim(types),
            _dim(np_res.age),
        ],
        on_click,
    )


def _configmap_row(cm: ConfigMapInfo, on_click: Any) -> ft.Container:
    return _row_box(
        [
            ft.Icon(ft.Icons.DESCRIPTION, size=14, color=ft.Colors.LIGHT_BLUE_200),
            ft.Text(cm.name, size=12, expand=True),
            _dim(f"{len(cm.data_keys)} keys"),
            _dim(cm.age),
        ],
        on_click,
    )


def _secret_row(sec: SecretInfo, on_click: Any) -> ft.Container:
    return _row_box(
        [
            ft.Icon(ft.Icons.LOCK, size=14, color=ft.Colors.RED_200),
            ft.Text(sec.name, size=12, expand=True),
            _pill(sec.type, ft.Colors.RED_200),
            _dim(f"{len(sec.data_keys)} keys"),
            _dim(sec.age),
        ],
        on_click,
    )


def _serviceaccount_row(sa: ServiceAccountInfo, on_click: Any) -> ft.Container:
    return _row_box(
        [
            ft.Icon(ft.Icons.PERSON, size=14, color=ft.Colors.INDIGO_200),
            ft.Text(sa.name, size=12, expand=True),
            _dim(f"{sa.secrets} secrets"),
            _dim(sa.age),
        ],
        on_click,
    )


def _pv_row(pv: PersistentVolumeInfo, on_click: Any) -> ft.Container:
    color = STATUS_COLORS.get(pv.status, ft.Colors.GREY_500)
    return _row_box(
        [
            ft.Icon(ft.Icons.CIRCLE, size=10, color=color),
            ft.Text(pv.name, size=12, expand=True),
            _dim(pv.capacity),
            _pill(pv.status, color),
            _dim(pv.age),
        ],
        on_click,
    )


def _pvc_row(pvc: PersistentVolumeClaimInfo, on_click: Any) -> ft.Container:
    color = STATUS_COLORS.get(pvc.status, ft.Colors.GREY_500)
    return _row_box(
        [
            ft.Icon(ft.Icons.CIRCLE, size=10, color=color),
            ft.Text(pvc.name, size=12, expand=True),
            _dim(pvc.capacity or "—"),
            _pill(pvc.status, color),
            _dim(pvc.age),
        ],
        on_click,
    )


def _node_row(node: NodeInfo, on_click: Any) -> ft.Container:
    color = STATUS_COLORS.get(node.status, ft.Colors.GREY_500)
    roles = ", ".join(node.roles) or "—"
    return _row_box(
        [
            ft.Icon(ft.Icons.CIRCLE, size=10, color=color),
            ft.Text(node.name, size=12, expand=True),
            _dim(roles),
            _dim(node.version),
            _dim(node.age),
        ],
        on_click,
    )


def _hpa_row(hpa: HPAInfo, on_click: Any) -> ft.Container:
    replicas = f"{hpa.current_replicas}/{hpa.min_replicas}-{hpa.max_replicas}"
    return _row_box(
        [
            ft.Icon(ft.Icons.AUTO_GRAPH, size=14, color=ft.Colors.GREEN_200),
            ft.Text(hpa.name, size=12, expand=True),
            _dim(hpa.target),
            _dim(replicas),
            _dim(hpa.age),
        ],
        on_click,
    )


def _event_row(ev: EventInfo, on_click: Any) -> ft.Container:
    """Events are shown inline but are *not* clickable."""
    color = STATUS_COLORS.get(ev.type, ft.Colors.GREY_500)
    msg = (ev.message[:55] + "…") if len(ev.message) > 55 else ev.message
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CIRCLE, size=10, color=color),
                ft.Text(ev.reason, size=12, width=100),
                ft.Text(
                    msg,
                    size=11,
                    color=ft.Colors.GREY_400,
                    expand=True,
                ),
                _dim(ev.last_seen),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=5),
        border_radius=4,
        # No on_click — events are informational
    )


def _generic_row(resource: Any, on_click: Any) -> ft.Container:
    name = getattr(resource, "name", str(resource))
    age = getattr(resource, "age", "")
    return _row_box(
        [
            ft.Icon(ft.Icons.CIRCLE, size=10, color=ft.Colors.GREY_500),
            ft.Text(name, size=12, expand=True),
            _dim(age),
        ],
        on_click,
    )


# ── Builder dispatch table ───────────────────────────────────────

_ROW_BUILDERS: dict[str, Callable[..., ft.Container]] = {
    "Pod": _pod_row,
    "Deployment": _deployment_row,
    "StatefulSet": _statefulset_row,
    "DaemonSet": _daemonset_row,
    "Job": _job_row,
    "CronJob": _cronjob_row,
    "Service": _service_row,
    "Ingress": _ingress_row,
    "NetworkPolicy": _netpol_row,
    "ConfigMap": _configmap_row,
    "Secret": _secret_row,
    "ServiceAccount": _serviceaccount_row,
    "PersistentVolume": _pv_row,
    "PersistentVolumeClaim": _pvc_row,
    "Node": _node_row,
    "HorizontalPodAutoscaler": _hpa_row,
    "Event": _event_row,
}
