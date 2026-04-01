"""Typed Pydantic models for Kubernetes resources."""

from __future__ import annotations

from pydantic import BaseModel


class ContainerInfo(BaseModel):
    """Container information within a Pod."""

    name: str
    image: str
    ready: bool
    restart_count: int
    state: str  # Running, Waiting, Terminated


class PodInfo(BaseModel):
    """Pod resource information."""

    name: str
    namespace: str
    status: str  # phase: Running, Pending, Succeeded, Failed, Unknown
    ready: str  # e.g. "1/1", "0/1"
    restarts: int
    age: str  # human-readable age
    ip: str | None = None
    node: str | None = None
    labels: dict[str, str] = {}
    containers: list[ContainerInfo] = []


class DeploymentInfo(BaseModel):
    """Deployment resource information."""

    name: str
    namespace: str
    replicas: int
    ready_replicas: int
    available_replicas: int
    age: str
    labels: dict[str, str] = {}
    strategy: str = "RollingUpdate"


class ServiceInfo(BaseModel):
    """Service resource information."""

    name: str
    namespace: str
    type: str  # ClusterIP, NodePort, LoadBalancer, ExternalName
    cluster_ip: str | None = None
    ports: list[str] = []  # e.g. ["80/TCP", "443/TCP"]
    selector: dict[str, str] = {}
    age: str


class NodeInfo(BaseModel):
    """Node resource information."""

    name: str
    status: str  # Ready, NotReady
    roles: list[str] = []  # control-plane, worker, etc.
    version: str
    os_image: str
    kernel: str
    container_runtime: str
    cpu_capacity: str
    memory_capacity: str
    age: str


class ConfigMapInfo(BaseModel):
    """ConfigMap resource information."""

    name: str
    namespace: str
    data_keys: list[str] = []
    age: str


class SecretInfo(BaseModel):
    """Secret resource information (NEVER includes values)."""

    name: str
    namespace: str
    type: str  # Opaque, kubernetes.io/tls, etc.
    data_keys: list[str] = []  # ONLY key names, NEVER values
    age: str


class IngressInfo(BaseModel):
    """Ingress resource information."""

    name: str
    namespace: str
    hosts: list[str] = []
    paths: list[str] = []
    tls: bool = False
    age: str


class JobInfo(BaseModel):
    """Job resource information."""

    name: str
    namespace: str
    completions: str  # e.g. "1/1"
    status: str  # Complete, Failed, Running
    age: str


class CronJobInfo(BaseModel):
    """CronJob resource information."""

    name: str
    namespace: str
    schedule: str
    suspend: bool
    active: int
    last_schedule: str | None = None
    age: str


class StatefulSetInfo(BaseModel):
    """StatefulSet resource information."""

    name: str
    namespace: str
    replicas: int
    ready_replicas: int
    age: str


class DaemonSetInfo(BaseModel):
    """DaemonSet resource information."""

    name: str
    namespace: str
    desired: int
    current: int
    ready: int
    age: str


class PersistentVolumeInfo(BaseModel):
    """PersistentVolume resource information."""

    name: str
    capacity: str
    access_modes: list[str] = []
    reclaim_policy: str
    status: str  # Available, Bound, Released, Failed
    storage_class: str | None = None
    claim: str | None = None  # namespace/name
    age: str


class PersistentVolumeClaimInfo(BaseModel):
    """PersistentVolumeClaim resource information."""

    name: str
    namespace: str
    status: str  # Pending, Bound, Lost
    volume: str | None = None
    capacity: str | None = None
    access_modes: list[str] = []
    storage_class: str | None = None
    age: str


class HPAInfo(BaseModel):
    """HorizontalPodAutoscaler resource information."""

    name: str
    namespace: str
    target: str  # e.g. "Deployment/nginx"
    min_replicas: int
    max_replicas: int
    current_replicas: int
    age: str


class NetworkPolicyInfo(BaseModel):
    """NetworkPolicy resource information."""

    name: str
    namespace: str
    pod_selector: dict[str, str] = {}
    policy_types: list[str] = []  # Ingress, Egress
    age: str


class ServiceAccountInfo(BaseModel):
    """ServiceAccount resource information."""

    name: str
    namespace: str
    secrets: int
    age: str


class EventInfo(BaseModel):
    """Kubernetes Event information."""

    namespace: str | None = None
    type: str  # Normal, Warning
    reason: str
    message: str
    source: str
    involved_object: str  # e.g. "Pod/nginx-xxxx"
    count: int
    first_seen: str
    last_seen: str
