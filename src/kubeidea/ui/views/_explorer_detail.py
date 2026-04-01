"""Detail panel for the Explorer view — info, events, YAML, and actions."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import flet as ft

from kubeidea.core.context import AppContext
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
from kubeidea.kube.resources import (
    delete_resource,
    get_resource_yaml,
    list_events,
    restart_resource,
    scale_resource,
)
from kubeidea.ui.views._explorer_rows import API_KINDS, KIND_ICONS, STATUS_COLORS

logger = logging.getLogger(__name__)

_SCALABLE = {"Deployment", "StatefulSet"}
_RESTARTABLE = {"Deployment", "StatefulSet", "DaemonSet"}

# Kind -> Kubernetes API resource plural (used for RBAC checks)
_KIND_RESOURCE_PLURAL: dict[str, str] = {
    "Pod": "pods",
    "Deployment": "deployments",
    "StatefulSet": "statefulsets",
    "DaemonSet": "daemonsets",
    "Job": "jobs",
    "CronJob": "cronjobs",
    "Service": "services",
    "Ingress": "ingresses",
    "NetworkPolicy": "networkpolicies",
    "ConfigMap": "configmaps",
    "Secret": "secrets",
    "ServiceAccount": "serviceaccounts",
    "PersistentVolume": "persistentvolumes",
    "PersistentVolumeClaim": "persistentvolumeclaims",
    "Node": "nodes",
    "HorizontalPodAutoscaler": "horizontalpodautoscalers",
}

_CLUSTER_SCOPED_KINDS = {"Node", "PersistentVolume"}


class DetailPanel(ft.Column):
    """Right-side detail panel showing resource info, events, and YAML."""

    def __init__(
        self,
        page: ft.Page,
        ctx: AppContext,
        on_close: Callable[[], None],
        on_resource_deleted: Callable[[], None],
    ) -> None:
        super().__init__(expand=True)
        self._page = page
        self._ctx = ctx
        self._on_close = on_close
        self._on_resource_deleted = on_resource_deleted

        self._kind: str = ""
        self._resource: Any = None
        self._yaml_loaded: bool = False
        self._events_loaded: bool = False
        self._yaml_text: str = ""
        self._detail_tabs: ft.Tabs | None = None

        # Persistent child views (re-populated each time a resource is shown)
        self._info_view = ft.ListView(expand=True, spacing=4, padding=12)
        self._events_view = ft.ListView(expand=True, spacing=4, padding=12)
        self._yaml_view = ft.Column(
            expand=True, scroll=ft.ScrollMode.AUTO, spacing=8,
        )

        self._build_empty()

    # ── Public API ────────────────────────────────────────────────

    def show(self, kind: str, resource: Any) -> None:
        """Populate the panel with details for *resource*."""
        self._kind = kind
        self._resource = resource
        self._yaml_loaded = False
        self._events_loaded = False
        self._yaml_text = ""
        self._build_detail()

    def hide(self) -> None:
        """Return the panel to its empty state."""
        self._kind = ""
        self._resource = None
        self._build_empty()

    # ── Empty placeholder ─────────────────────────────────────────

    def _build_empty(self) -> None:
        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.TOUCH_APP, size=48,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text(
                            "Select a resource",
                            size=14, color=ft.Colors.GREY_500,
                        ),
                        ft.Text(
                            "Click any item on the left to view details.",
                            size=12, color=ft.Colors.GREY_600,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
                expand=True,
                alignment=ft.Alignment(0, 0),
            ),
        ]

    # ── Detail view builder ───────────────────────────────────────

    def _build_detail(self) -> None:
        res = self._resource
        icon = KIND_ICONS.get(self._kind, ft.Icons.CIRCLE)
        res_name = getattr(res, "name", getattr(res, "reason", "—"))

        # ── header ────────────────────────────────────────────────
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=20, color=ft.Colors.BLUE_200),
                    ft.Column(
                        controls=[
                            ft.Text(
                                res_name, size=16,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                self._kind, size=11,
                                color=ft.Colors.GREY_400,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        tooltip="Close",
                        on_click=lambda _: self._on_close(),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(left=16, right=8, top=8, bottom=4),
        )

        # ── action buttons ────────────────────────────────────────
        actions = self._build_actions()

        # ── info content ──────────────────────────────────────────
        self._info_view.controls.clear()
        self._populate_info()

        # ── events / yaml placeholders (lazy-loaded) ──────────────
        self._events_view.controls.clear()
        self._events_view.controls.append(
            ft.Text(
                "Switch to this tab to load events.",
                size=12, color=ft.Colors.GREY_500,
            ),
        )
        self._yaml_view.controls.clear()
        self._yaml_view.controls.append(
            ft.Text(
                "Switch to this tab to load YAML.",
                size=12, color=ft.Colors.GREY_500,
            ),
        )

        # ── inner tabs ────────────────────────────────────────────
        self._detail_tabs = ft.Tabs(
            length=3,
            selected_index=0,
            expand=True,
            on_change=self._on_tab_change,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(
                                label="Info",
                                icon=ft.Icons.INFO_OUTLINE,
                            ),
                            ft.Tab(
                                label="Events",
                                icon=ft.Icons.EVENT,
                            ),
                            ft.Tab(
                                label="YAML",
                                icon=ft.Icons.CODE,
                            ),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self._info_view,
                            self._events_view,
                            self._yaml_view,
                        ],
                    ),
                ],
            ),
        )

        self.controls = [header, actions, ft.Divider(height=1), self._detail_tabs]

    # ── Action buttons ────────────────────────────────────────────

    def _can_i(self, verb: str) -> bool:
        """Check RBAC permission for the current resource. Fail-open on error."""
        inspector = self._ctx.rbac_inspector
        if inspector is None:
            return True
        resource_plural = _KIND_RESOURCE_PLURAL.get(self._kind)
        if not resource_plural:
            return True
        try:
            ns = getattr(self._resource, "namespace", self._ctx.current_namespace)
            return inspector.can_i(verb, resource_plural, ns)
        except Exception:
            logger.debug("RBAC check failed for %s %s, allowing", verb, self._kind)
            return True

    def _build_actions(self) -> ft.Container:
        buttons: list[ft.Control] = []
        if self._kind in _SCALABLE:
            allowed = self._can_i("patch")
            buttons.append(
                ft.Button(
                    content=ft.Text("Scale"), icon=ft.Icons.TUNE,
                    on_click=self._on_scale_click,
                    disabled=not allowed,
                    tooltip=None if allowed else "Insufficient permissions",
                ),
            )
        if self._kind in _RESTARTABLE:
            allowed = self._can_i("patch")
            buttons.append(
                ft.Button(
                    content=ft.Text("Restart"), icon=ft.Icons.RESTART_ALT,
                    on_click=self._on_restart_click,
                    disabled=not allowed,
                    tooltip=None if allowed else "Insufficient permissions",
                ),
            )
        if self._kind in API_KINDS:
            allowed = self._can_i("delete")
            buttons.append(
                ft.Button(
                    content=ft.Text("Delete"), icon=ft.Icons.DELETE,
                    on_click=self._on_delete_click,
                    disabled=not allowed,
                    tooltip=None if allowed else "Insufficient permissions",
                ),
            )
        if not buttons:
            return ft.Container()
        return ft.Container(
            content=ft.Row(controls=buttons, spacing=8),
            padding=ft.Padding.symmetric(horizontal=16, vertical=4),
        )

    # ── Lazy tab loading ──────────────────────────────────────────

    def _on_tab_change(self, _e: Any) -> None:
        if self._detail_tabs is None:
            return
        idx = self._detail_tabs.selected_index
        if idx == 1 and not self._events_loaded:
            self._load_events()
        elif idx == 2 and not self._yaml_loaded:
            self._load_yaml()

    # ── Info tab ──────────────────────────────────────────────────

    def _populate_info(self) -> None:
        res = self._resource
        rows = self._info_view.controls

        # common metadata
        if hasattr(res, "name"):
            rows.append(_kv("Name", res.name))
        if hasattr(res, "namespace"):
            rows.append(_kv("Namespace", res.namespace))
        if hasattr(res, "age"):
            rows.append(_kv("Age", res.age))
        if hasattr(res, "labels") and res.labels:
            rows.append(_labels_row("Labels", res.labels))
        rows.append(ft.Divider(height=1))

        builder = _INFO_BUILDERS.get(self._kind)
        if builder:
            builder(res, rows)

    # ── Events tab ────────────────────────────────────────────────

    def _load_events(self) -> None:
        self._events_loaded = True
        self._events_view.controls.clear()
        client = self._ctx.api_client
        if not client:
            self._events_view.controls.append(
                ft.Text("Not connected.", size=12, color=ft.Colors.GREY_500),
            )
            self._page.update()
            return
        res_name = getattr(self._resource, "name", None)
        if not res_name:
            self._events_view.controls.append(
                ft.Text(
                    "Events view not available for this resource.",
                    size=12, color=ft.Colors.GREY_500,
                ),
            )
            self._page.update()
            return
        try:
            ns = getattr(self._resource, "namespace", "default")
            events = list_events(
                client, ns, involved_object_name=res_name,
            )
            if not events:
                self._events_view.controls.append(
                    ft.Text(
                        "No events found.", size=12,
                        color=ft.Colors.GREY_500,
                    ),
                )
            else:
                for ev in events:
                    self._events_view.controls.append(
                        self._event_card(ev),
                    )
        except Exception as exc:
            self._events_view.controls.append(_error_row(str(exc)))
        self._page.update()

    @staticmethod
    def _event_card(ev: EventInfo) -> ft.Container:
        color = STATUS_COLORS.get(ev.type, ft.Colors.GREY_500)
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CIRCLE, size=8, color=color),
                            ft.Text(
                                ev.reason, size=12,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Text(
                                f"×{ev.count}", size=11,
                                color=ft.Colors.GREY_400,
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                ev.last_seen, size=11,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    ft.Text(
                        ev.message, size=11,
                        color=ft.Colors.GREY_400, selectable=True,
                    ),
                ],
                spacing=2,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            border_radius=4,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        )

    # ── YAML tab ──────────────────────────────────────────────────

    def _load_yaml(self) -> None:
        self._yaml_loaded = True
        self._yaml_view.controls.clear()
        client = self._ctx.api_client
        res_name = getattr(self._resource, "name", None)
        api_kind = API_KINDS.get(self._kind)

        if not client or not res_name or not api_kind:
            self._yaml_view.controls.append(
                ft.Text(
                    "YAML view not available for this resource.",
                    size=12, color=ft.Colors.GREY_500,
                ),
            )
            self._page.update()
            return
        try:
            ns = getattr(self._resource, "namespace", "default")
            self._yaml_text = get_resource_yaml(
                client, api_kind, res_name, ns,
            )
            self._yaml_view.controls.append(
                ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.COPY,
                            tooltip="Copy YAML to clipboard",
                            on_click=self._on_copy_yaml,
                        ),
                    ],
                ),
            )
            self._yaml_view.controls.append(
                ft.Container(
                    content=ft.Text(
                        self._yaml_text, size=11,
                        font_family="monospace", selectable=True,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    padding=12,
                    border_radius=8,
                ),
            )
        except Exception as exc:
            self._yaml_view.controls.append(_error_row(str(exc)))
        self._page.update()

    def _on_copy_yaml(self, _e: Any) -> None:
        if self._yaml_text:
            self._page.set_clipboard(self._yaml_text)
            self._page.open(
                ft.SnackBar(ft.Text("YAML copied to clipboard")),
            )

    # ── Delete action ─────────────────────────────────────────────

    def _on_delete_click(self, _e: Any) -> None:
        res = self._resource
        api_kind = API_KINDS.get(self._kind, self._kind.lower())
        res_name = getattr(res, "name", "?")

        def confirm(_e: Any) -> None:
            self._page.close(dlg)
            client = self._ctx.api_client
            if not client:
                return
            ns = getattr(res, "namespace", "default")
            ok = delete_resource(client, api_kind, res_name, ns)
            if ok:
                self._page.open(
                    ft.SnackBar(
                        ft.Text(f"Deleted {self._kind}/{res_name}"),
                    ),
                )
                self.hide()
                self._on_resource_deleted()
            else:
                self._page.open(
                    ft.SnackBar(
                        ft.Text(
                            f"Failed to delete {self._kind}/{res_name}",
                        ),
                    ),
                )

        def cancel(_e: Any) -> None:
            self._page.close(dlg)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(
                f"Delete {self._kind} '{res_name}'?\n"
                "This action cannot be undone.",
            ),
            actions=[
                ft.Button(content=ft.Text("Cancel"), on_click=cancel),
                ft.Button(content=ft.Text("Delete"), on_click=confirm),
            ],
        )
        self._page.open(dlg)

    # ── Scale action ──────────────────────────────────────────────

    def _on_scale_click(self, _e: Any) -> None:
        res = self._resource
        api_kind = API_KINDS.get(self._kind, self._kind.lower())
        current = getattr(res, "replicas", 1)
        replicas_field = ft.TextField(
            label="Replicas",
            value=str(current),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120,
        )

        def confirm(_e: Any) -> None:
            self._page.close(dlg)
            client = self._ctx.api_client
            if not client:
                return
            try:
                count = int(replicas_field.value or "0")
            except ValueError:
                self._page.open(
                    ft.SnackBar(ft.Text("Invalid replica count")),
                )
                return
            ns = getattr(res, "namespace", "default")
            ok = scale_resource(client, api_kind, res.name, ns, count)
            if ok:
                self._page.open(
                    ft.SnackBar(
                        ft.Text(
                            f"Scaled {self._kind}/{res.name} → {count}",
                        ),
                    ),
                )
                self._on_resource_deleted()  # triggers list refresh
            else:
                self._page.open(
                    ft.SnackBar(
                        ft.Text(
                            f"Failed to scale {self._kind}/{res.name}",
                        ),
                    ),
                )

        def cancel(_e: Any) -> None:
            self._page.close(dlg)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Scale {self._kind}"),
            content=ft.Column(
                controls=[
                    ft.Text(f"Set replica count for '{res.name}':"),
                    replicas_field,
                ],
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.Button(content=ft.Text("Cancel"), on_click=cancel),
                ft.Button(content=ft.Text("Scale"), on_click=confirm),
            ],
        )
        self._page.open(dlg)

    # ── Restart action ────────────────────────────────────────────

    def _on_restart_click(self, _e: Any) -> None:
        res = self._resource
        api_kind = API_KINDS.get(self._kind, self._kind.lower())

        def confirm(_e: Any) -> None:
            self._page.close(dlg)
            client = self._ctx.api_client
            if not client:
                return
            ns = getattr(res, "namespace", "default")
            ok = restart_resource(client, api_kind, res.name, ns)
            if ok:
                self._page.open(
                    ft.SnackBar(
                        ft.Text(
                            f"Restarting {self._kind}/{res.name}",
                        ),
                    ),
                )
            else:
                self._page.open(
                    ft.SnackBar(
                        ft.Text(
                            f"Failed to restart {self._kind}/{res.name}",
                        ),
                    ),
                )

        def cancel(_e: Any) -> None:
            self._page.close(dlg)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirm Restart"),
            content=ft.Text(
                f"Rollout-restart {self._kind} '{res.name}'?",
            ),
            actions=[
                ft.Button(content=ft.Text("Cancel"), on_click=cancel),
                ft.Button(content=ft.Text("Restart"), on_click=confirm),
            ],
        )
        self._page.open(dlg)


# =====================================================================
# Module-level helpers (used by DetailPanel and info builders)
# =====================================================================


def _kv(label: str, value: str) -> ft.Container:
    """Key-value row for the Info tab."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(label, size=12, color=ft.Colors.GREY_400, width=130),
                ft.Text(
                    str(value), size=12,
                    selectable=True, expand=True,
                ),
            ],
            spacing=8,
        ),
        padding=ft.Padding.symmetric(horizontal=4, vertical=2),
    )


def _labels_row(title: str, labels: dict[str, str]) -> ft.Container:
    """Display a dict as a row of small label chips."""
    chips: list[ft.Control] = [
        ft.Container(
            content=ft.Text(f"{k}={v}", size=10),
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.BLUE),
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            border_radius=4,
        )
        for k, v in labels.items()
    ]
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    title, size=12,
                    color=ft.Colors.GREY_400, width=130,
                ),
                ft.Row(
                    controls=chips, wrap=True,
                    spacing=4, run_spacing=4, expand=True,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=ft.Padding.symmetric(horizontal=4, vertical=2),
    )


def _error_row(msg: str) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ERROR, size=16, color=ft.Colors.RED_400),
                ft.Text(
                    msg, size=12,
                    color=ft.Colors.RED_300, selectable=True,
                ),
            ],
            spacing=6,
        ),
        padding=12,
    )


# =====================================================================
# Per-kind info builders
# =====================================================================


def _pod_info(pod: PodInfo, rows: list[ft.Control]) -> None:
    rows.append(_kv("Status", pod.status))
    rows.append(_kv("Ready", pod.ready))
    rows.append(_kv("Restarts", str(pod.restarts)))
    rows.append(_kv("IP", pod.ip or "—"))
    rows.append(_kv("Node", pod.node or "—"))
    if pod.containers:
        rows.append(ft.Divider(height=1))
        rows.append(
            ft.Container(
                content=ft.Text(
                    "Containers", size=13,
                    weight=ft.FontWeight.BOLD,
                ),
                padding=ft.Padding.only(left=4, top=8, bottom=4),
            ),
        )
        for c in pod.containers:
            c_color = STATUS_COLORS.get(c.state, ft.Colors.GREY_500)
            rows.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.CIRCLE,
                                        size=8, color=c_color,
                                    ),
                                    ft.Text(
                                        c.name, size=12,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                spacing=6,
                            ),
                            ft.Text(
                                c.image, size=11,
                                color=ft.Colors.GREY_400,
                                selectable=True,
                            ),
                            ft.Text(
                                f"State: {c.state}  ·  "
                                f"Restarts: {c.restart_count}",
                                size=11,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        spacing=2,
                    ),
                    padding=ft.Padding.only(left=16, top=4, bottom=4),
                    bgcolor=ft.Colors.with_opacity(
                        0.03, ft.Colors.WHITE,
                    ),
                    border_radius=4,
                ),
            )


def _deployment_info(
    dep: DeploymentInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Replicas", str(dep.replicas)))
    rows.append(_kv("Ready", str(dep.ready_replicas)))
    rows.append(_kv("Available", str(dep.available_replicas)))
    rows.append(_kv("Strategy", dep.strategy))


def _statefulset_info(
    ss: StatefulSetInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Replicas", str(ss.replicas)))
    rows.append(_kv("Ready", str(ss.ready_replicas)))


def _daemonset_info(
    ds: DaemonSetInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Desired", str(ds.desired)))
    rows.append(_kv("Current", str(ds.current)))
    rows.append(_kv("Ready", str(ds.ready)))


def _job_info(job: JobInfo, rows: list[ft.Control]) -> None:
    rows.append(_kv("Completions", job.completions))
    rows.append(_kv("Status", job.status))


def _cronjob_info(
    cj: CronJobInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Schedule", cj.schedule))
    rows.append(_kv("Suspend", str(cj.suspend)))
    rows.append(_kv("Active", str(cj.active)))
    rows.append(_kv("Last Schedule", cj.last_schedule or "—"))


def _service_info(
    svc: ServiceInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Type", svc.type))
    rows.append(_kv("Cluster IP", svc.cluster_ip or "—"))
    rows.append(_kv("Ports", ", ".join(svc.ports) or "—"))
    if svc.selector:
        rows.append(_labels_row("Selector", svc.selector))


def _ingress_info(
    ing: IngressInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Hosts", ", ".join(ing.hosts) or "—"))
    rows.append(_kv("Paths", ", ".join(ing.paths) or "—"))
    rows.append(_kv("TLS", "Yes" if ing.tls else "No"))


def _netpol_info(
    np_res: NetworkPolicyInfo, rows: list[ft.Control],
) -> None:
    types = ", ".join(np_res.policy_types) or "—"
    rows.append(_kv("Policy Types", types))
    if np_res.pod_selector:
        rows.append(_labels_row("Pod Selector", np_res.pod_selector))


def _configmap_info(
    cm: ConfigMapInfo, rows: list[ft.Control],
) -> None:
    keys = ", ".join(cm.data_keys) or "—"
    rows.append(_kv("Data Keys", keys))


def _secret_info(
    sec: SecretInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Type", sec.type))
    rows.append(_kv("Data Keys", ", ".join(sec.data_keys) or "—"))


def _sa_info(
    sa: ServiceAccountInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Secrets", str(sa.secrets)))


def _pv_info(
    pv: PersistentVolumeInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Capacity", pv.capacity))
    rows.append(_kv("Access Modes", ", ".join(pv.access_modes) or "—"))
    rows.append(_kv("Reclaim Policy", pv.reclaim_policy))
    rows.append(_kv("Status", pv.status))
    rows.append(_kv("Storage Class", pv.storage_class or "—"))
    rows.append(_kv("Claim", pv.claim or "—"))


def _pvc_info(
    pvc: PersistentVolumeClaimInfo, rows: list[ft.Control],
) -> None:
    rows.append(_kv("Status", pvc.status))
    rows.append(_kv("Volume", pvc.volume or "—"))
    rows.append(_kv("Capacity", pvc.capacity or "—"))
    access = ", ".join(pvc.access_modes) or "—"
    rows.append(_kv("Access Modes", access))
    rows.append(_kv("Storage Class", pvc.storage_class or "—"))


def _node_info(node: NodeInfo, rows: list[ft.Control]) -> None:
    rows.append(_kv("Status", node.status))
    rows.append(_kv("Roles", ", ".join(node.roles) or "—"))
    rows.append(_kv("Version", node.version))
    rows.append(_kv("OS Image", node.os_image))
    rows.append(_kv("Kernel", node.kernel))
    rows.append(_kv("Container Runtime", node.container_runtime))
    rows.append(_kv("CPU Capacity", node.cpu_capacity))
    rows.append(_kv("Memory", node.memory_capacity))


def _hpa_info(hpa: HPAInfo, rows: list[ft.Control]) -> None:
    rows.append(_kv("Target", hpa.target))
    rows.append(_kv("Min Replicas", str(hpa.min_replicas)))
    rows.append(_kv("Max Replicas", str(hpa.max_replicas)))
    rows.append(_kv("Current Replicas", str(hpa.current_replicas)))


def _event_info(ev: EventInfo, rows: list[ft.Control]) -> None:
    rows.append(_kv("Type", ev.type))
    rows.append(_kv("Reason", ev.reason))
    rows.append(_kv("Source", ev.source))
    rows.append(_kv("Involved Object", ev.involved_object))
    rows.append(_kv("Count", str(ev.count)))
    rows.append(_kv("First Seen", ev.first_seen))
    rows.append(_kv("Last Seen", ev.last_seen))
    rows.append(ft.Divider(height=1))
    rows.append(
        ft.Container(
            content=ft.Text(ev.message, size=12, selectable=True),
            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
        ),
    )


_INFO_BUILDERS: dict[str, Callable[..., None]] = {
    "Pod": _pod_info,
    "Deployment": _deployment_info,
    "StatefulSet": _statefulset_info,
    "DaemonSet": _daemonset_info,
    "Job": _job_info,
    "CronJob": _cronjob_info,
    "Service": _service_info,
    "Ingress": _ingress_info,
    "NetworkPolicy": _netpol_info,
    "ConfigMap": _configmap_info,
    "Secret": _secret_info,
    "ServiceAccount": _sa_info,
    "PersistentVolume": _pv_info,
    "PersistentVolumeClaim": _pvc_info,
    "Node": _node_info,
    "HorizontalPodAutoscaler": _hpa_info,
    "Event": _event_info,
}
