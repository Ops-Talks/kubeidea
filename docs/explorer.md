# Resource Explorer

The **Explorer** is the central panel of Kube-IDEA. It lets you browse,
inspect, and manage every Kubernetes resource in the connected cluster.

---

## Overview

Once connected to a cluster (via the **Clusters** page), select a namespace
from the dropdown at the top and the Explorer automatically loads resources
organized into five category tabs:

| Tab | Resources |
|---|---|
| **Workloads** | Pods, Deployments, StatefulSets, DaemonSets, Jobs, CronJobs |
| **Networking** | Services, Ingresses, NetworkPolicies |
| **Config** | ConfigMaps, Secrets, ServiceAccounts |
| **Storage** | PersistentVolumes, PersistentVolumeClaims |
| **Cluster** | Nodes, HPAs, Events |

Each resource type is displayed as a section with a header showing the count
and a list of resource rows with key information at a glance.

---

## Search / Filter

Use the **Filter by name…** search field in the header bar to instantly
filter resources in the current tab by name (case-insensitive substring
match). The filter applies across all resource types in the active category.

---

## Resource Detail Panel

Click any resource row to open the **Detail Panel** on the right side. The
detail panel includes three tabs:

### Info

Shows resource metadata and type-specific fields:

- **Common**: Name, Namespace, Age, Labels
- **Pod-specific**: Status, Ready count, Restarts, IP, Node, container
  details (image, state, restart count)
- **Deployment-specific**: Replicas (ready/total), Available, Strategy
- **Service-specific**: Type, Cluster IP, Ports
- **Node-specific**: Status, Roles, Version, OS, Kernel, Runtime, CPU/Memory
  capacity
- And more for every supported resource type.

### Events

Displays Kubernetes Events associated with the selected resource, filtered
by `involvedObject.name`. Each event shows:

- Type indicator (Normal / Warning)
- Reason
- Message
- Occurrence count

### YAML

The raw YAML manifest of the resource retrieved directly from the cluster
API server. Includes a **Copy YAML** button that places the full YAML into
the system clipboard.

---

## Actions

The detail panel exposes context-sensitive action buttons:

| Action | Available for | Description |
|---|---|---|
| **Scale** | Deployments, StatefulSets | Opens a dialog to set the desired replica count |
| **Restart** | Deployments, StatefulSets, DaemonSets | Rollout restart via pod template annotation patch |
| **Delete** | All resources (except Nodes and Events) | Deletes the resource after confirmation dialog |

All actions show a success or error notification via a snackbar.

!!! warning "RBAC"
    Operations respect your cluster RBAC permissions. If you lack the
    required verbs (e.g. `delete`, `patch`), the operation will fail with
    a clear error message.

---

## Architecture

```
ExplorerView (Flet Column)
 ├─ Header (title, connection chip)
 ├─ Toolbar (namespace dropdown, search, refresh)
 ├─ Split layout
 │   ├─ Left: Category Tabs → ListViews with resource rows
 │   └─ Right: Detail Panel (Info / Events / YAML tabs + action buttons)
 └─ CRUD dialogs (Scale, Restart, Delete confirmations)
```

### Backend

All Kubernetes operations are in `kubeidea.kube.resources`:

```python
# Listing (17 resource types)
list_pods(api_client, namespace) -> list[PodInfo]
list_deployments(api_client, namespace) -> list[DeploymentInfo]
list_services(api_client, namespace) -> list[ServiceInfo]
list_nodes(api_client) -> list[NodeInfo]
list_configmaps(api_client, namespace) -> list[ConfigMapInfo]
list_secrets(api_client, namespace) -> list[SecretInfo]
list_ingresses(api_client, namespace) -> list[IngressInfo]
list_jobs(api_client, namespace) -> list[JobInfo]
list_cronjobs(api_client, namespace) -> list[CronJobInfo]
list_statefulsets(api_client, namespace) -> list[StatefulSetInfo]
list_daemonsets(api_client, namespace) -> list[DaemonSetInfo]
list_persistentvolumes(api_client) -> list[PersistentVolumeInfo]
list_persistentvolumeclaims(api_client, namespace) -> list[PersistentVolumeClaimInfo]
list_hpa(api_client, namespace) -> list[HPAInfo]
list_networkpolicies(api_client, namespace) -> list[NetworkPolicyInfo]
list_serviceaccounts(api_client, namespace) -> list[ServiceAccountInfo]
list_events(api_client, namespace, involved_object_name?) -> list[EventInfo]

# Inspection
get_resource_yaml(api_client, kind, name, namespace) -> str

# Mutations
delete_resource(api_client, kind, name, namespace) -> bool
scale_resource(api_client, kind, name, namespace, replicas) -> bool
restart_resource(api_client, kind, name, namespace) -> bool
```

All models are typed Pydantic `BaseModel` classes defined in
`kubeidea.kube.models`.
