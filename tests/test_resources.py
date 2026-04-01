"""Comprehensive tests for kubeidea.kube.models and kubeidea.kube.resources."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

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
from kubeidea.kube.resources import (
    _resource_age,
    apply_resource,
    delete_resource,
    get_resource_yaml,
    list_configmaps,
    list_cronjobs,
    list_daemonsets,
    list_deployments,
    list_events,
    list_hpa,
    list_ingresses,
    list_jobs,
    list_namespaces,
    list_networkpolicies,
    list_nodes,
    list_persistentvolumeclaims,
    list_persistentvolumes,
    list_pods,
    list_secrets,
    list_serviceaccounts,
    list_services,
    list_statefulsets,
    restart_resource,
    scale_resource,
)

# ---------------------------------------------------------------------------
# Helper: _resource_age
# ---------------------------------------------------------------------------


class TestResourceAge:
    """Tests for the _resource_age helper function."""

    def test_none_returns_unknown(self) -> None:
        assert _resource_age(None) == "Unknown"

    def test_falsy_returns_unknown(self) -> None:
        assert _resource_age("") == "Unknown"

    def test_no_timestamp_attr_returns_unknown(self) -> None:
        assert _resource_age("not-a-datetime") == "Unknown"

    def test_days_ago(self) -> None:
        ts = datetime.now(UTC) - timedelta(days=5, hours=3)
        result = _resource_age(ts)
        assert result == "5d"

    def test_hours_ago(self) -> None:
        ts = datetime.now(UTC) - timedelta(hours=3, minutes=15)
        result = _resource_age(ts)
        assert result == "3h"

    def test_minutes_ago(self) -> None:
        ts = datetime.now(UTC) - timedelta(minutes=42)
        result = _resource_age(ts)
        assert result == "42m"

    def test_zero_minutes(self) -> None:
        ts = datetime.now(UTC) - timedelta(seconds=10)
        result = _resource_age(ts)
        assert result == "0m"

    def test_naive_datetime_gets_utc(self) -> None:
        """Naive timestamps should be treated as UTC."""
        ts = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=2)
        result = _resource_age(ts)
        assert result == "2d"


# ---------------------------------------------------------------------------
# Model creation tests
# ---------------------------------------------------------------------------


class TestModelCreation:
    """Verify all Pydantic models can be instantiated with required fields."""

    def test_container_info(self) -> None:
        c = ContainerInfo(name="nginx", image="nginx:latest", ready=True, restart_count=0, state="Running")
        assert c.name == "nginx"
        assert c.ready is True

    def test_pod_info_minimal(self) -> None:
        p = PodInfo(name="pod-1", namespace="default", status="Running", ready="1/1", restarts=0, age="5d")
        assert p.ip is None
        assert p.containers == []
        assert p.labels == {}

    def test_pod_info_full(self) -> None:
        c = ContainerInfo(name="app", image="app:v1", ready=True, restart_count=2, state="Running")
        p = PodInfo(
            name="pod-2",
            namespace="kube-system",
            status="Running",
            ready="1/1",
            restarts=2,
            age="1h",
            ip="10.0.0.1",
            node="node-1",
            labels={"app": "web"},
            containers=[c],
        )
        assert p.ip == "10.0.0.1"
        assert len(p.containers) == 1

    def test_deployment_info(self) -> None:
        d = DeploymentInfo(
            name="deploy-1", namespace="default", replicas=3, ready_replicas=3, available_replicas=3, age="2d"
        )
        assert d.strategy == "RollingUpdate"

    def test_service_info(self) -> None:
        s = ServiceInfo(name="svc-1", namespace="default", type="ClusterIP", age="1d")
        assert s.ports == []
        assert s.cluster_ip is None

    def test_node_info(self) -> None:
        n = NodeInfo(
            name="node-1",
            status="Ready",
            version="v1.28.0",
            os_image="Ubuntu 22.04",
            kernel="5.15.0",
            container_runtime="containerd://1.7.0",
            cpu_capacity="4",
            memory_capacity="8Gi",
            age="30d",
        )
        assert n.roles == []

    def test_configmap_info(self) -> None:
        cm = ConfigMapInfo(name="cm-1", namespace="default", age="1d")
        assert cm.data_keys == []

    def test_secret_info(self) -> None:
        s = SecretInfo(name="sec-1", namespace="default", type="Opaque", age="1d")
        assert s.data_keys == []

    def test_ingress_info(self) -> None:
        i = IngressInfo(name="ing-1", namespace="default", age="1d")
        assert i.tls is False

    def test_job_info(self) -> None:
        j = JobInfo(name="job-1", namespace="default", completions="1/1", status="Complete", age="1h")
        assert j.status == "Complete"

    def test_cronjob_info(self) -> None:
        cj = CronJobInfo(name="cj-1", namespace="default", schedule="*/5 * * * *", suspend=False, active=0, age="1d")
        assert cj.last_schedule is None

    def test_statefulset_info(self) -> None:
        ss = StatefulSetInfo(name="ss-1", namespace="default", replicas=3, ready_replicas=3, age="2d")
        assert ss.replicas == 3

    def test_daemonset_info(self) -> None:
        ds = DaemonSetInfo(name="ds-1", namespace="default", desired=3, current=3, ready=3, age="5d")
        assert ds.desired == 3

    def test_persistent_volume_info(self) -> None:
        pv = PersistentVolumeInfo(name="pv-1", capacity="10Gi", reclaim_policy="Retain", status="Bound", age="10d")
        assert pv.claim is None

    def test_persistent_volume_claim_info(self) -> None:
        pvc = PersistentVolumeClaimInfo(name="pvc-1", namespace="default", status="Bound", age="5d")
        assert pvc.volume is None

    def test_hpa_info(self) -> None:
        h = HPAInfo(
            name="hpa-1",
            namespace="default",
            target="Deployment/nginx",
            min_replicas=1,
            max_replicas=10,
            current_replicas=3,
            age="1d",
        )
        assert h.target == "Deployment/nginx"

    def test_network_policy_info(self) -> None:
        np_info = NetworkPolicyInfo(name="np-1", namespace="default", age="1d")
        assert np_info.pod_selector == {}
        assert np_info.policy_types == []

    def test_service_account_info(self) -> None:
        sa = ServiceAccountInfo(name="sa-1", namespace="default", secrets=1, age="1d")
        assert sa.secrets == 1

    def test_event_info(self) -> None:
        ev = EventInfo(
            type="Normal",
            reason="Scheduled",
            message="Pod scheduled",
            source="scheduler",
            involved_object="Pod/nginx",
            count=1,
            first_seen="2024-01-01",
            last_seen="2024-01-01",
        )
        assert ev.namespace is None


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

_TS = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


def _mock_metadata(
    name: str = "test",
    namespace: str = "default",
    labels: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock Kubernetes metadata object."""
    meta = MagicMock()
    meta.name = name
    meta.namespace = namespace
    meta.creation_timestamp = _TS
    meta.labels = labels or {}
    return meta


# ---------------------------------------------------------------------------
# list_namespaces
# ---------------------------------------------------------------------------


class TestListNamespaces:
    def test_returns_sorted_names(self) -> None:
        mock_client = MagicMock()
        ns1 = MagicMock()
        ns1.metadata = _mock_metadata(name="kube-system")
        ns2 = MagicMock()
        ns2.metadata = _mock_metadata(name="default")

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespace.return_value.items = [ns1, ns2]
            mock_core.return_value = mock_api

            result = list_namespaces(mock_client)
            assert result == ["default", "kube-system"]

    def test_skips_none_metadata(self) -> None:
        mock_client = MagicMock()
        ns1 = MagicMock()
        ns1.metadata = None
        ns2 = MagicMock()
        ns2.metadata = _mock_metadata(name="default")

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespace.return_value.items = [ns1, ns2]
            mock_core.return_value = mock_api

            result = list_namespaces(mock_client)
            assert result == ["default"]


# ---------------------------------------------------------------------------
# list_pods
# ---------------------------------------------------------------------------


class TestListPods:
    def _make_pod(
        self,
        name: str = "pod-1",
        phase: str = "Running",
        *,
        with_containers: bool = True,
    ) -> MagicMock:
        pod = MagicMock()
        pod.metadata = _mock_metadata(name=name, labels={"app": "web"})
        pod.status.phase = phase
        pod.status.pod_ip = "10.0.0.1"
        pod.spec.node_name = "node-1"

        if with_containers:
            cs = MagicMock()
            cs.name = "nginx"
            cs.image = "nginx:latest"
            cs.ready = True
            cs.restart_count = 2
            cs.state.running = True
            cs.state.terminated = None
            pod.status.container_statuses = [cs]
            pod.spec.containers = [MagicMock()]
        else:
            pod.status.container_statuses = None
            pod.spec.containers = [MagicMock(), MagicMock()]
        return pod

    def test_basic_pod_listing(self) -> None:
        mock_client = MagicMock()
        pod = self._make_pod()

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_pod.return_value.items = [pod]
            mock_core.return_value = mock_api

            result = list_pods(mock_client, namespace="default")
            assert len(result) == 1
            assert isinstance(result[0], PodInfo)
            assert result[0].name == "pod-1"
            assert result[0].status == "Running"
            assert result[0].restarts == 2
            assert result[0].ip == "10.0.0.1"
            assert result[0].node == "node-1"
            assert result[0].labels == {"app": "web"}
            assert len(result[0].containers) == 1
            assert result[0].containers[0].state == "Running"

    def test_pod_without_container_statuses(self) -> None:
        mock_client = MagicMock()
        pod = self._make_pod(with_containers=False)

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_pod.return_value.items = [pod]
            mock_core.return_value = mock_api

            result = list_pods(mock_client)
            assert len(result) == 1
            assert result[0].ready == "0/2"
            assert result[0].containers == []

    def test_pod_no_metadata_skipped(self) -> None:
        mock_client = MagicMock()
        pod = MagicMock()
        pod.metadata = None

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_pod.return_value.items = [pod]
            mock_core.return_value = mock_api

            result = list_pods(mock_client)
            assert result == []

    def test_terminated_container_state(self) -> None:
        mock_client = MagicMock()
        pod = MagicMock()
        pod.metadata = _mock_metadata(name="terminated-pod")
        pod.status.phase = "Succeeded"
        pod.status.pod_ip = None
        pod.spec.node_name = None
        cs = MagicMock()
        cs.name = "worker"
        cs.image = "worker:v1"
        cs.ready = False
        cs.restart_count = 0
        cs.state.running = None
        cs.state.terminated = True
        pod.status.container_statuses = [cs]
        pod.spec.containers = [MagicMock()]

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_pod.return_value.items = [pod]
            mock_core.return_value = mock_api

            result = list_pods(mock_client)
            assert result[0].containers[0].state == "Terminated"

    def test_waiting_container_state(self) -> None:
        mock_client = MagicMock()
        pod = MagicMock()
        pod.metadata = _mock_metadata(name="waiting-pod")
        pod.status.phase = "Pending"
        pod.status.pod_ip = None
        pod.spec.node_name = None
        cs = MagicMock()
        cs.name = "init"
        cs.image = "init:v1"
        cs.ready = False
        cs.restart_count = 0
        cs.state.running = None
        cs.state.terminated = None
        pod.status.container_statuses = [cs]
        pod.spec.containers = [MagicMock()]

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_pod.return_value.items = [pod]
            mock_core.return_value = mock_api

            result = list_pods(mock_client)
            assert result[0].containers[0].state == "Waiting"


# ---------------------------------------------------------------------------
# list_deployments
# ---------------------------------------------------------------------------


class TestListDeployments:
    def test_basic_deployment_listing(self) -> None:
        mock_client = MagicMock()
        dep = MagicMock()
        dep.metadata = _mock_metadata(name="nginx-deploy", labels={"app": "nginx"})
        dep.spec.replicas = 3
        dep.spec.strategy.type = "RollingUpdate"
        dep.status.ready_replicas = 3
        dep.status.available_replicas = 3

        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.list_namespaced_deployment.return_value.items = [dep]
            mock_apps.return_value = mock_api

            result = list_deployments(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], DeploymentInfo)
            assert result[0].name == "nginx-deploy"
            assert result[0].replicas == 3
            assert result[0].ready_replicas == 3
            assert result[0].strategy == "RollingUpdate"

    def test_deployment_no_metadata(self) -> None:
        mock_client = MagicMock()
        dep = MagicMock()
        dep.metadata = None

        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.list_namespaced_deployment.return_value.items = [dep]
            mock_apps.return_value = mock_api

            result = list_deployments(mock_client)
            assert result == []

    def test_empty_deployment_list(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.list_namespaced_deployment.return_value.items = []
            mock_apps.return_value = mock_api

            result = list_deployments(mock_client)
            assert result == []


# ---------------------------------------------------------------------------
# list_services
# ---------------------------------------------------------------------------


class TestListServices:
    def test_basic_service_listing(self) -> None:
        mock_client = MagicMock()
        svc = MagicMock()
        svc.metadata = _mock_metadata(name="my-svc")
        svc.spec.type = "ClusterIP"
        svc.spec.cluster_ip = "10.96.0.1"
        svc.spec.selector = {"app": "web"}
        port = MagicMock()
        port.port = 80
        port.protocol = "TCP"
        svc.spec.ports = [port]

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_service.return_value.items = [svc]
            mock_core.return_value = mock_api

            result = list_services(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], ServiceInfo)
            assert result[0].type == "ClusterIP"
            assert result[0].ports == ["80/TCP"]
            assert result[0].cluster_ip == "10.96.0.1"

    def test_service_no_ports(self) -> None:
        mock_client = MagicMock()
        svc = MagicMock()
        svc.metadata = _mock_metadata(name="headless")
        svc.spec.type = "ClusterIP"
        svc.spec.cluster_ip = "None"
        svc.spec.selector = {}
        svc.spec.ports = None

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_service.return_value.items = [svc]
            mock_core.return_value = mock_api

            result = list_services(mock_client)
            assert result[0].ports == []


# ---------------------------------------------------------------------------
# list_nodes
# ---------------------------------------------------------------------------


class TestListNodes:
    def test_basic_node_listing(self) -> None:
        mock_client = MagicMock()
        node = MagicMock()
        node.metadata = _mock_metadata(
            name="node-1",
            labels={"node-role.kubernetes.io/control-plane": ""},
        )
        cond = MagicMock()
        cond.type = "Ready"
        cond.status = "True"
        node.status.conditions = [cond]
        node.status.node_info.kubelet_version = "v1.28.0"
        node.status.node_info.os_image = "Ubuntu 22.04"
        node.status.node_info.kernel_version = "5.15.0"
        node.status.node_info.container_runtime_version = "containerd://1.7.0"
        node.status.capacity = {"cpu": "4", "memory": "8Gi"}

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_node.return_value.items = [node]
            mock_core.return_value = mock_api

            result = list_nodes(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], NodeInfo)
            assert result[0].name == "node-1"
            assert result[0].status == "Ready"
            assert result[0].roles == ["control-plane"]
            assert result[0].version == "v1.28.0"
            assert result[0].cpu_capacity == "4"

    def test_node_not_ready(self) -> None:
        mock_client = MagicMock()
        node = MagicMock()
        node.metadata = _mock_metadata(name="node-bad")
        cond = MagicMock()
        cond.type = "Ready"
        cond.status = "False"
        node.status.conditions = [cond]
        node.status.node_info.kubelet_version = "v1.28.0"
        node.status.node_info.os_image = "Ubuntu 22.04"
        node.status.node_info.kernel_version = "5.15.0"
        node.status.node_info.container_runtime_version = "containerd://1.7.0"
        node.status.capacity = {"cpu": "2", "memory": "4Gi"}

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_node.return_value.items = [node]
            mock_core.return_value = mock_api

            result = list_nodes(mock_client)
            assert result[0].status == "NotReady"

    def test_node_no_metadata_skipped(self) -> None:
        mock_client = MagicMock()
        node = MagicMock()
        node.metadata = None

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_node.return_value.items = [node]
            mock_core.return_value = mock_api

            result = list_nodes(mock_client)
            assert result == []

    def test_node_exception_returns_empty(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_node.side_effect = Exception("connection refused")
            mock_core.return_value = mock_api

            result = list_nodes(mock_client)
            assert result == []


# ---------------------------------------------------------------------------
# list_configmaps
# ---------------------------------------------------------------------------


class TestListConfigMaps:
    def test_basic_listing(self) -> None:
        mock_client = MagicMock()
        cm = MagicMock()
        cm.metadata = _mock_metadata(name="my-config")
        cm.data = {"key1": "val1", "key2": "val2"}

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_config_map.return_value.items = [cm]
            mock_core.return_value = mock_api

            result = list_configmaps(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], ConfigMapInfo)
            assert sorted(result[0].data_keys) == ["key1", "key2"]

    def test_configmap_no_data(self) -> None:
        mock_client = MagicMock()
        cm = MagicMock()
        cm.metadata = _mock_metadata(name="empty-cm")
        cm.data = None

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_config_map.return_value.items = [cm]
            mock_core.return_value = mock_api

            result = list_configmaps(mock_client)
            assert result[0].data_keys == []


# ---------------------------------------------------------------------------
# list_secrets
# ---------------------------------------------------------------------------


class TestListSecrets:
    def test_returns_only_key_names(self) -> None:
        mock_client = MagicMock()
        secret = MagicMock()
        secret.metadata = _mock_metadata(name="my-secret")
        secret.type = "Opaque"
        secret.data = {"username": "dXNlcg==", "password": "cGFzcw=="}

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_secret.return_value.items = [secret]
            mock_core.return_value = mock_api

            result = list_secrets(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], SecretInfo)
            assert sorted(result[0].data_keys) == ["password", "username"]
            # Ensure no values leaked
            model_dump = result[0].model_dump()
            for val in model_dump.values():
                if isinstance(val, list):
                    for item in val:
                        assert item not in ("dXNlcg==", "cGFzcw==")

    def test_secret_no_data(self) -> None:
        mock_client = MagicMock()
        secret = MagicMock()
        secret.metadata = _mock_metadata(name="empty-sec")
        secret.type = "kubernetes.io/tls"
        secret.data = None

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_secret.return_value.items = [secret]
            mock_core.return_value = mock_api

            result = list_secrets(mock_client)
            assert result[0].data_keys == []
            assert result[0].type == "kubernetes.io/tls"


# ---------------------------------------------------------------------------
# list_ingresses
# ---------------------------------------------------------------------------


class TestListIngresses:
    def test_basic_ingress(self) -> None:
        mock_client = MagicMock()
        ing = MagicMock()
        ing.metadata = _mock_metadata(name="my-ingress")
        rule = MagicMock()
        rule.host = "example.com"
        path_obj = MagicMock()
        path_obj.path = "/api"
        rule.http.paths = [path_obj]
        ing.spec.rules = [rule]
        ing.spec.tls = [MagicMock()]

        with patch("kubernetes.client.NetworkingV1Api") as mock_net:
            mock_api = MagicMock()
            mock_api.list_namespaced_ingress.return_value.items = [ing]
            mock_net.return_value = mock_api

            result = list_ingresses(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], IngressInfo)
            assert result[0].hosts == ["example.com"]
            assert result[0].paths == ["/api"]
            assert result[0].tls is True

    def test_ingress_no_tls(self) -> None:
        mock_client = MagicMock()
        ing = MagicMock()
        ing.metadata = _mock_metadata(name="no-tls")
        ing.spec.rules = []
        ing.spec.tls = None

        with patch("kubernetes.client.NetworkingV1Api") as mock_net:
            mock_api = MagicMock()
            mock_api.list_namespaced_ingress.return_value.items = [ing]
            mock_net.return_value = mock_api

            result = list_ingresses(mock_client)
            assert result[0].tls is False

    def test_ingress_exception_returns_empty(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.NetworkingV1Api") as mock_net:
            mock_api = MagicMock()
            mock_api.list_namespaced_ingress.side_effect = Exception("fail")
            mock_net.return_value = mock_api

            result = list_ingresses(mock_client)
            assert result == []


# ---------------------------------------------------------------------------
# list_jobs
# ---------------------------------------------------------------------------


class TestListJobs:
    def test_completed_job(self) -> None:
        mock_client = MagicMock()
        job = MagicMock()
        job.metadata = _mock_metadata(name="my-job")
        job.spec.completions = 1
        job.status.succeeded = 1
        cond = MagicMock()
        cond.type = "Complete"
        cond.status = "True"
        job.status.conditions = [cond]

        with patch("kubernetes.client.BatchV1Api") as mock_batch:
            mock_api = MagicMock()
            mock_api.list_namespaced_job.return_value.items = [job]
            mock_batch.return_value = mock_api

            result = list_jobs(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], JobInfo)
            assert result[0].status == "Complete"
            assert result[0].completions == "1/1"

    def test_failed_job(self) -> None:
        mock_client = MagicMock()
        job = MagicMock()
        job.metadata = _mock_metadata(name="failed-job")
        job.spec.completions = 1
        job.status.succeeded = 0
        cond = MagicMock()
        cond.type = "Failed"
        cond.status = "True"
        job.status.conditions = [cond]

        with patch("kubernetes.client.BatchV1Api") as mock_batch:
            mock_api = MagicMock()
            mock_api.list_namespaced_job.return_value.items = [job]
            mock_batch.return_value = mock_api

            result = list_jobs(mock_client)
            assert result[0].status == "Failed"

    def test_running_job_no_conditions(self) -> None:
        mock_client = MagicMock()
        job = MagicMock()
        job.metadata = _mock_metadata(name="running-job")
        job.spec.completions = 3
        job.status.succeeded = 1
        job.status.conditions = None

        with patch("kubernetes.client.BatchV1Api") as mock_batch:
            mock_api = MagicMock()
            mock_api.list_namespaced_job.return_value.items = [job]
            mock_batch.return_value = mock_api

            result = list_jobs(mock_client)
            assert result[0].status == "Running"
            assert result[0].completions == "1/3"


# ---------------------------------------------------------------------------
# list_cronjobs
# ---------------------------------------------------------------------------


class TestListCronJobs:
    def test_basic_cronjob(self) -> None:
        mock_client = MagicMock()
        cj = MagicMock()
        cj.metadata = _mock_metadata(name="my-cron")
        cj.spec.schedule = "*/5 * * * *"
        cj.spec.suspend = False
        cj.status.active = [MagicMock()]
        cj.status.last_schedule_time = _TS

        with patch("kubernetes.client.BatchV1Api") as mock_batch:
            mock_api = MagicMock()
            mock_api.list_namespaced_cron_job.return_value.items = [cj]
            mock_batch.return_value = mock_api

            result = list_cronjobs(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], CronJobInfo)
            assert result[0].schedule == "*/5 * * * *"
            assert result[0].active == 1
            assert result[0].last_schedule is not None

    def test_cronjob_no_active(self) -> None:
        mock_client = MagicMock()
        cj = MagicMock()
        cj.metadata = _mock_metadata(name="idle-cron")
        cj.spec.schedule = "0 0 * * *"
        cj.spec.suspend = True
        cj.status.active = None
        cj.status.last_schedule_time = None

        with patch("kubernetes.client.BatchV1Api") as mock_batch:
            mock_api = MagicMock()
            mock_api.list_namespaced_cron_job.return_value.items = [cj]
            mock_batch.return_value = mock_api

            result = list_cronjobs(mock_client)
            assert result[0].active == 0
            assert result[0].suspend is True
            assert result[0].last_schedule is None


# ---------------------------------------------------------------------------
# list_statefulsets
# ---------------------------------------------------------------------------


class TestListStatefulSets:
    def test_basic_statefulset(self) -> None:
        mock_client = MagicMock()
        ss = MagicMock()
        ss.metadata = _mock_metadata(name="my-ss")
        ss.spec.replicas = 3
        ss.status.ready_replicas = 3

        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.list_namespaced_stateful_set.return_value.items = [ss]
            mock_apps.return_value = mock_api

            result = list_statefulsets(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], StatefulSetInfo)
            assert result[0].replicas == 3
            assert result[0].ready_replicas == 3

    def test_statefulset_no_ready(self) -> None:
        mock_client = MagicMock()
        ss = MagicMock()
        ss.metadata = _mock_metadata(name="unready-ss")
        ss.spec.replicas = 2
        ss.status.ready_replicas = None

        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.list_namespaced_stateful_set.return_value.items = [ss]
            mock_apps.return_value = mock_api

            result = list_statefulsets(mock_client)
            assert result[0].ready_replicas == 0


# ---------------------------------------------------------------------------
# list_daemonsets
# ---------------------------------------------------------------------------


class TestListDaemonSets:
    def test_basic_daemonset(self) -> None:
        mock_client = MagicMock()
        ds = MagicMock()
        ds.metadata = _mock_metadata(name="my-ds")
        ds.status.desired_number_scheduled = 3
        ds.status.current_number_scheduled = 3
        ds.status.number_ready = 3

        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.list_namespaced_daemon_set.return_value.items = [ds]
            mock_apps.return_value = mock_api

            result = list_daemonsets(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], DaemonSetInfo)
            assert result[0].desired == 3
            assert result[0].current == 3
            assert result[0].ready == 3

    def test_daemonset_exception(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.list_namespaced_daemon_set.side_effect = Exception("err")
            mock_apps.return_value = mock_api

            result = list_daemonsets(mock_client)
            assert result == []


# ---------------------------------------------------------------------------
# list_persistentvolumes
# ---------------------------------------------------------------------------


class TestListPersistentVolumes:
    def test_basic_pv(self) -> None:
        mock_client = MagicMock()
        pv = MagicMock()
        pv.metadata = _mock_metadata(name="pv-1")
        pv.spec.capacity = {"storage": "10Gi"}
        pv.spec.access_modes = ["ReadWriteOnce"]
        pv.spec.persistent_volume_reclaim_policy = "Retain"
        pv.spec.storage_class_name = "standard"
        pv.spec.claim_ref.namespace = "default"
        pv.spec.claim_ref.name = "pvc-1"
        pv.status.phase = "Bound"

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_persistent_volume.return_value.items = [pv]
            mock_core.return_value = mock_api

            result = list_persistentvolumes(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], PersistentVolumeInfo)
            assert result[0].capacity == "10Gi"
            assert result[0].claim == "default/pvc-1"
            assert result[0].status == "Bound"

    def test_pv_no_claim_ref(self) -> None:
        mock_client = MagicMock()
        pv = MagicMock()
        pv.metadata = _mock_metadata(name="pv-avail")
        pv.spec.capacity = {"storage": "5Gi"}
        pv.spec.access_modes = ["ReadWriteMany"]
        pv.spec.persistent_volume_reclaim_policy = "Delete"
        pv.spec.storage_class_name = None
        pv.spec.claim_ref = None
        pv.status.phase = "Available"

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_persistent_volume.return_value.items = [pv]
            mock_core.return_value = mock_api

            result = list_persistentvolumes(mock_client)
            assert result[0].claim is None
            assert result[0].status == "Available"


# ---------------------------------------------------------------------------
# list_persistentvolumeclaims
# ---------------------------------------------------------------------------


class TestListPersistentVolumeClaims:
    def test_basic_pvc(self) -> None:
        mock_client = MagicMock()
        pvc = MagicMock()
        pvc.metadata = _mock_metadata(name="pvc-1")
        pvc.spec.volume_name = "pv-1"
        pvc.spec.access_modes = ["ReadWriteOnce"]
        pvc.spec.storage_class_name = "standard"
        pvc.status.phase = "Bound"
        pvc.status.capacity = {"storage": "10Gi"}
        pvc.status.access_modes = ["ReadWriteOnce"]

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_persistent_volume_claim.return_value.items = [pvc]
            mock_core.return_value = mock_api

            result = list_persistentvolumeclaims(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], PersistentVolumeClaimInfo)
            assert result[0].volume == "pv-1"
            assert result[0].status == "Bound"

    def test_pvc_pending(self) -> None:
        mock_client = MagicMock()
        pvc = MagicMock()
        pvc.metadata = _mock_metadata(name="pvc-pending")
        pvc.spec.volume_name = None
        pvc.spec.access_modes = None
        pvc.spec.storage_class_name = None
        pvc.status.phase = "Pending"
        pvc.status.capacity = None
        pvc.status.access_modes = None

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_persistent_volume_claim.return_value.items = [pvc]
            mock_core.return_value = mock_api

            result = list_persistentvolumeclaims(mock_client)
            assert result[0].status == "Pending"
            assert result[0].capacity is None


# ---------------------------------------------------------------------------
# list_hpa
# ---------------------------------------------------------------------------


class TestListHPA:
    def test_basic_hpa(self) -> None:
        mock_client = MagicMock()
        hpa = MagicMock()
        hpa.metadata = _mock_metadata(name="my-hpa")
        hpa.spec.scale_target_ref.kind = "Deployment"
        hpa.spec.scale_target_ref.name = "nginx"
        hpa.spec.min_replicas = 1
        hpa.spec.max_replicas = 10
        hpa.status.current_replicas = 3

        with patch("kubernetes.client.AutoscalingV2Api") as mock_auto:
            mock_api = MagicMock()
            mock_api.list_namespaced_horizontal_pod_autoscaler.return_value.items = [hpa]
            mock_auto.return_value = mock_api

            result = list_hpa(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], HPAInfo)
            assert result[0].target == "Deployment/nginx"
            assert result[0].min_replicas == 1
            assert result[0].max_replicas == 10

    def test_hpa_exception(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AutoscalingV2Api") as mock_auto:
            mock_api = MagicMock()
            mock_api.list_namespaced_horizontal_pod_autoscaler.side_effect = Exception("err")
            mock_auto.return_value = mock_api

            result = list_hpa(mock_client)
            assert result == []


# ---------------------------------------------------------------------------
# list_networkpolicies
# ---------------------------------------------------------------------------


class TestListNetworkPolicies:
    def test_basic_netpol(self) -> None:
        mock_client = MagicMock()
        np_item = MagicMock()
        np_item.metadata = _mock_metadata(name="deny-all")
        np_item.spec.pod_selector.match_labels = {"app": "web"}
        np_item.spec.policy_types = ["Ingress", "Egress"]

        with patch("kubernetes.client.NetworkingV1Api") as mock_net:
            mock_api = MagicMock()
            mock_api.list_namespaced_network_policy.return_value.items = [np_item]
            mock_net.return_value = mock_api

            result = list_networkpolicies(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], NetworkPolicyInfo)
            assert result[0].pod_selector == {"app": "web"}
            assert result[0].policy_types == ["Ingress", "Egress"]

    def test_netpol_no_selector(self) -> None:
        mock_client = MagicMock()
        np_item = MagicMock()
        np_item.metadata = _mock_metadata(name="allow-all")
        np_item.spec.pod_selector.match_labels = None
        np_item.spec.policy_types = []

        with patch("kubernetes.client.NetworkingV1Api") as mock_net:
            mock_api = MagicMock()
            mock_api.list_namespaced_network_policy.return_value.items = [np_item]
            mock_net.return_value = mock_api

            result = list_networkpolicies(mock_client)
            assert result[0].pod_selector == {}


# ---------------------------------------------------------------------------
# list_serviceaccounts
# ---------------------------------------------------------------------------


class TestListServiceAccounts:
    def test_basic_sa(self) -> None:
        mock_client = MagicMock()
        sa = MagicMock()
        sa.metadata = _mock_metadata(name="default")
        sa.secrets = [MagicMock(), MagicMock()]

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_service_account.return_value.items = [sa]
            mock_core.return_value = mock_api

            result = list_serviceaccounts(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], ServiceAccountInfo)
            assert result[0].secrets == 2

    def test_sa_no_secrets(self) -> None:
        mock_client = MagicMock()
        sa = MagicMock()
        sa.metadata = _mock_metadata(name="no-secret")
        sa.secrets = None

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_service_account.return_value.items = [sa]
            mock_core.return_value = mock_api

            result = list_serviceaccounts(mock_client)
            assert result[0].secrets == 0


# ---------------------------------------------------------------------------
# list_events
# ---------------------------------------------------------------------------


class TestListEvents:
    def _make_event(
        self,
        name: str = "ev-1",
        ev_type: str = "Normal",
        reason: str = "Scheduled",
        obj_kind: str = "Pod",
        obj_name: str = "nginx",
    ) -> MagicMock:
        ev = MagicMock()
        ev.metadata = _mock_metadata(name=name)
        ev.type = ev_type
        ev.reason = reason
        ev.message = "Pod was scheduled"
        ev.source.component = "scheduler"
        ev.involved_object.kind = obj_kind
        ev.involved_object.name = obj_name
        ev.count = 1
        ev.first_timestamp = _TS
        ev.last_timestamp = _TS
        return ev

    def test_basic_event_listing(self) -> None:
        mock_client = MagicMock()
        ev = self._make_event()

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_event.return_value.items = [ev]
            mock_core.return_value = mock_api

            result = list_events(mock_client)
            assert len(result) == 1
            assert isinstance(result[0], EventInfo)
            assert result[0].reason == "Scheduled"
            assert result[0].involved_object == "Pod/nginx"

    def test_event_filtering_by_object_name(self) -> None:
        mock_client = MagicMock()
        ev = self._make_event(obj_name="nginx-pod")

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_event.return_value.items = [ev]
            mock_core.return_value = mock_api

            # The function uses field_selector on the API call
            result = list_events(mock_client, involved_object_name="nginx-pod")
            assert len(result) == 1

    def test_event_exception(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_event.side_effect = Exception("err")
            mock_core.return_value = mock_api

            result = list_events(mock_client)
            assert result == []


# ---------------------------------------------------------------------------
# get_resource_yaml
# ---------------------------------------------------------------------------


class TestGetResourceYAML:
    def test_get_pod_yaml(self) -> None:
        mock_client = MagicMock()
        mock_resource = MagicMock()
        mock_client.sanitize_for_serialization.return_value = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "nginx"},
        }

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.read_namespaced_pod.return_value = mock_resource
            mock_core.return_value = mock_api

            result = get_resource_yaml(mock_client, "Pod", "nginx", "default")
            assert "kind: Pod" in result
            assert "name: nginx" in result

    def test_get_deployment_yaml(self) -> None:
        mock_client = MagicMock()
        mock_client.sanitize_for_serialization.return_value = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "nginx-deploy"},
        }

        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.read_namespaced_deployment.return_value = MagicMock()
            mock_apps.return_value = mock_api

            result = get_resource_yaml(mock_client, "Deployment", "nginx-deploy")
            assert "Deployment" in result

    def test_unsupported_kind(self) -> None:
        mock_client = MagicMock()
        result = get_resource_yaml(mock_client, "UnknownKind", "foo")
        assert "Unsupported kind" in result

    def test_cluster_scoped_node(self) -> None:
        mock_client = MagicMock()
        mock_client.sanitize_for_serialization.return_value = {
            "apiVersion": "v1",
            "kind": "Node",
            "metadata": {"name": "node-1"},
        }

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.read_node.return_value = MagicMock()
            mock_core.return_value = mock_api

            result = get_resource_yaml(mock_client, "node", "node-1")
            assert "Node" in result

    def test_exception_returns_error_comment(self) -> None:
        mock_client = MagicMock()

        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.read_namespaced_pod.side_effect = Exception("not found")
            mock_core.return_value = mock_api

            result = get_resource_yaml(mock_client, "Pod", "missing")
            assert "Error retrieving" in result


# ---------------------------------------------------------------------------
# delete_resource
# ---------------------------------------------------------------------------


class TestDeleteResource:
    def test_delete_pod_success(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_core.return_value = mock_api

            result = delete_resource(mock_client, "Pod", "nginx", "default")
            assert result is True
            mock_api.delete_namespaced_pod.assert_called_once_with(name="nginx", namespace="default")

    def test_delete_deployment_success(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_apps.return_value = mock_api

            result = delete_resource(mock_client, "Deployment", "nginx", "default")
            assert result is True
            mock_api.delete_namespaced_deployment.assert_called_once()

    def test_delete_cluster_scoped_pv(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_core.return_value = mock_api

            result = delete_resource(mock_client, "persistentvolume", "pv-1", "default")
            assert result is True
            mock_api.delete_persistent_volume.assert_called_once_with(name="pv-1")

    def test_delete_unsupported_kind(self) -> None:
        mock_client = MagicMock()
        result = delete_resource(mock_client, "UnknownKind", "foo", "default")
        assert result is False

    def test_delete_exception_returns_false(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.delete_namespaced_pod.side_effect = Exception("forbidden")
            mock_core.return_value = mock_api

            result = delete_resource(mock_client, "Pod", "nginx", "default")
            assert result is False

    @pytest.mark.parametrize(
        "kind",
        [
            "service",
            "configmap",
            "secret",
            "ingress",
            "job",
            "cronjob",
            "statefulset",
            "daemonset",
            "persistentvolumeclaim",
            "serviceaccount",
            "networkpolicy",
            "namespace",
            "node",
        ],
    )
    def test_delete_various_kinds(self, kind: str) -> None:
        mock_client = MagicMock()
        # Patch all possible API classes
        with (
            patch("kubernetes.client.CoreV1Api") as mock_core,
            patch("kubernetes.client.AppsV1Api") as mock_apps,
            patch("kubernetes.client.BatchV1Api") as mock_batch,
            patch("kubernetes.client.NetworkingV1Api") as mock_net,
            patch("kubernetes.client.AutoscalingV2Api") as mock_auto,
        ):
            for mock_cls in (mock_core, mock_apps, mock_batch, mock_net, mock_auto):
                mock_cls.return_value = MagicMock()

            result = delete_resource(mock_client, kind, "test-resource", "default")
            assert result is True


# ---------------------------------------------------------------------------
# scale_resource
# ---------------------------------------------------------------------------


class TestScaleResource:
    def test_scale_deployment(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_apps.return_value = mock_api

            result = scale_resource(mock_client, "Deployment", "nginx", "default", replicas=5)
            assert result is True
            mock_api.patch_namespaced_deployment_scale.assert_called_once_with(
                name="nginx", namespace="default", body={"spec": {"replicas": 5}}
            )

    def test_scale_statefulset(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_apps.return_value = mock_api

            result = scale_resource(mock_client, "StatefulSet", "redis", "default", replicas=3)
            assert result is True
            mock_api.patch_namespaced_stateful_set_scale.assert_called_once()

    def test_scale_replicaset(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_apps.return_value = mock_api

            result = scale_resource(mock_client, "ReplicaSet", "rs-1", "default", replicas=2)
            assert result is True
            mock_api.patch_namespaced_replica_set_scale.assert_called_once()

    def test_scale_unsupported_kind(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api"):
            result = scale_resource(mock_client, "DaemonSet", "ds-1", "default", replicas=3)
            assert result is False

    def test_scale_exception(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.patch_namespaced_deployment_scale.side_effect = Exception("err")
            mock_apps.return_value = mock_api

            result = scale_resource(mock_client, "Deployment", "nginx", "default", replicas=5)
            assert result is False


# ---------------------------------------------------------------------------
# restart_resource
# ---------------------------------------------------------------------------


class TestRestartResource:
    def test_restart_deployment(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_apps.return_value = mock_api

            result = restart_resource(mock_client, "Deployment", "nginx", "default")
            assert result is True
            mock_api.patch_namespaced_deployment.assert_called_once()
            call_body = mock_api.patch_namespaced_deployment.call_args
            body = call_body.kwargs.get("body", call_body[1].get("body", {}))
            assert "kubectl.kubernetes.io/restartedAt" in body["spec"]["template"]["metadata"]["annotations"]

    def test_restart_statefulset(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_apps.return_value = mock_api

            result = restart_resource(mock_client, "StatefulSet", "redis", "default")
            assert result is True
            mock_api.patch_namespaced_stateful_set.assert_called_once()

    def test_restart_daemonset(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_apps.return_value = mock_api

            result = restart_resource(mock_client, "DaemonSet", "fluentd", "default")
            assert result is True
            mock_api.patch_namespaced_daemon_set.assert_called_once()

    def test_restart_unsupported_kind(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api"):
            result = restart_resource(mock_client, "Pod", "nginx", "default")
            assert result is False

    def test_restart_exception(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.patch_namespaced_deployment.side_effect = Exception("err")
            mock_apps.return_value = mock_api

            result = restart_resource(mock_client, "Deployment", "nginx", "default")
            assert result is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases across various listing functions."""

    def test_empty_pod_list(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_pod.return_value.items = []
            mock_core.return_value = mock_api

            result = list_pods(mock_client)
            assert result == []

    def test_empty_node_list(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_node.return_value.items = []
            mock_core.return_value = mock_api

            result = list_nodes(mock_client)
            assert result == []

    def test_api_exception_pods(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_pod.side_effect = Exception("timeout")
            mock_core.return_value = mock_api

            result = list_pods(mock_client)
            assert result == []

    def test_api_exception_deployments(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.list_namespaced_deployment.side_effect = Exception("timeout")
            mock_apps.return_value = mock_api

            result = list_deployments(mock_client)
            assert result == []

    def test_api_exception_services(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_service.side_effect = Exception("timeout")
            mock_core.return_value = mock_api

            result = list_services(mock_client)
            assert result == []

    def test_api_exception_configmaps(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_config_map.side_effect = Exception("err")
            mock_core.return_value = mock_api

            result = list_configmaps(mock_client)
            assert result == []

    def test_api_exception_secrets(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_secret.side_effect = Exception("err")
            mock_core.return_value = mock_api

            result = list_secrets(mock_client)
            assert result == []

    def test_api_exception_jobs(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.BatchV1Api") as mock_batch:
            mock_api = MagicMock()
            mock_api.list_namespaced_job.side_effect = Exception("err")
            mock_batch.return_value = mock_api

            result = list_jobs(mock_client)
            assert result == []

    def test_api_exception_cronjobs(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.BatchV1Api") as mock_batch:
            mock_api = MagicMock()
            mock_api.list_namespaced_cron_job.side_effect = Exception("err")
            mock_batch.return_value = mock_api

            result = list_cronjobs(mock_client)
            assert result == []

    def test_api_exception_statefulsets(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.AppsV1Api") as mock_apps:
            mock_api = MagicMock()
            mock_api.list_namespaced_stateful_set.side_effect = Exception("err")
            mock_apps.return_value = mock_api

            result = list_statefulsets(mock_client)
            assert result == []

    def test_api_exception_pvs(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_persistent_volume.side_effect = Exception("err")
            mock_core.return_value = mock_api

            result = list_persistentvolumes(mock_client)
            assert result == []

    def test_api_exception_pvcs(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_persistent_volume_claim.side_effect = Exception("err")
            mock_core.return_value = mock_api

            result = list_persistentvolumeclaims(mock_client)
            assert result == []

    def test_api_exception_netpol(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.NetworkingV1Api") as mock_net:
            mock_api = MagicMock()
            mock_api.list_namespaced_network_policy.side_effect = Exception("err")
            mock_net.return_value = mock_api

            result = list_networkpolicies(mock_client)
            assert result == []

    def test_api_exception_serviceaccounts(self) -> None:
        mock_client = MagicMock()
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_api.list_namespaced_service_account.side_effect = Exception("err")
            mock_core.return_value = mock_api

            result = list_serviceaccounts(mock_client)
            assert result == []


# ---------------------------------------------------------------------------
# apply_resource
# ---------------------------------------------------------------------------


class TestApplyResource:
    """Tests for the apply_resource function."""

    def test_create_namespaced_success(self) -> None:
        """apply_resource should create a new namespaced resource."""
        mock_client = MagicMock()
        manifest = (
            "apiVersion: v1\n"
            "kind: ConfigMap\n"
            "metadata:\n"
            "  name: my-config\n"
            "  namespace: default\n"
            "data:\n"
            "  key: value\n"
        )
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_core.return_value = mock_api

            result = apply_resource(mock_client, manifest)
            assert result is True
            mock_api.create_namespaced_config_map.assert_called_once()

    def test_create_cluster_scoped_success(self) -> None:
        """apply_resource should create a cluster-scoped resource."""
        mock_client = MagicMock()
        manifest = "apiVersion: v1\n" "kind: Namespace\n" "metadata:\n" "  name: test-ns\n"
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_core.return_value = mock_api

            result = apply_resource(mock_client, manifest)
            assert result is True
            mock_api.create_namespace.assert_called_once()

    def test_replace_on_409_conflict(self) -> None:
        """apply_resource should replace when create returns 409."""
        from kubernetes.client.rest import ApiException

        mock_client = MagicMock()
        manifest = "apiVersion: apps/v1\n" "kind: Deployment\n" "metadata:\n" "  name: nginx\n" "  namespace: default\n"
        with (
            patch("kubernetes.client.AppsV1Api") as mock_apps,
        ):
            mock_api = MagicMock()
            mock_apps.return_value = mock_api
            # First call (create) raises 409, second call (replace) succeeds
            mock_api.create_namespaced_deployment.side_effect = ApiException(
                status=409,
            )

            result = apply_resource(mock_client, manifest)
            assert result is True
            mock_api.create_namespaced_deployment.assert_called_once()
            mock_api.replace_namespaced_deployment.assert_called_once()

    def test_create_fails_non_409(self) -> None:
        """apply_resource should return False on non-409 API errors."""
        from kubernetes.client.rest import ApiException

        mock_client = MagicMock()
        manifest = "apiVersion: v1\n" "kind: Pod\n" "metadata:\n" "  name: test-pod\n" "  namespace: default\n"
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_core.return_value = mock_api
            mock_api.create_namespaced_pod.side_effect = ApiException(
                status=403,
            )

            result = apply_resource(mock_client, manifest)
            assert result is False

    def test_invalid_yaml(self) -> None:
        """apply_resource should return False for invalid YAML."""
        mock_client = MagicMock()
        result = apply_resource(mock_client, ": invalid: yaml: [")
        assert result is False

    def test_missing_kind(self) -> None:
        """apply_resource should return False when kind is missing."""
        mock_client = MagicMock()
        manifest = "metadata:\n  name: test\n"
        result = apply_resource(mock_client, manifest)
        assert result is False

    def test_missing_name(self) -> None:
        """apply_resource should return False when name is missing."""
        mock_client = MagicMock()
        manifest = "kind: Pod\nmetadata:\n  namespace: default\n"
        result = apply_resource(mock_client, manifest)
        assert result is False

    def test_unsupported_kind(self) -> None:
        """apply_resource should return False for unsupported kinds."""
        mock_client = MagicMock()
        manifest = "kind: CustomResource\nmetadata:\n  name: test\n"
        result = apply_resource(mock_client, manifest)
        assert result is False

    def test_replace_failure_returns_false(self) -> None:
        """apply_resource should return False when both create and replace fail."""
        from kubernetes.client.rest import ApiException

        mock_client = MagicMock()
        manifest = "apiVersion: v1\n" "kind: Service\n" "metadata:\n" "  name: my-svc\n" "  namespace: default\n"
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_core.return_value = mock_api
            mock_api.create_namespaced_service.side_effect = ApiException(
                status=409,
            )
            mock_api.replace_namespaced_service.side_effect = Exception(
                "replace failed",
            )

            result = apply_resource(mock_client, manifest)
            assert result is False

    def test_default_namespace(self) -> None:
        """apply_resource should default to 'default' namespace when not specified."""
        mock_client = MagicMock()
        manifest = "apiVersion: v1\n" "kind: Secret\n" "metadata:\n" "  name: my-secret\n"
        with patch("kubernetes.client.CoreV1Api") as mock_core:
            mock_api = MagicMock()
            mock_core.return_value = mock_api

            result = apply_resource(mock_client, manifest)
            assert result is True
            call_kwargs = mock_api.create_namespaced_secret.call_args
            assert call_kwargs[1]["namespace"] == "default"
