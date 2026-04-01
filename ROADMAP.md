# Kube-IDEA — ROADMAP

> Última atualização: 2026-04-01
>
> Formato: **EPIC › STORY › TASK › SUBTASK** (estilo Jira)
>
> Legenda de status:
> ✅ Done  ·  🔧 In Progress  ·  ⬚ To Do

---

## Estado Atual do Projeto

O que **funciona hoje**:

- Navegação lateral (9 destinos)
- Conexão com cluster via kubeconfig (listar contextos, conectar, desconectar)
- **Explorer completo**: listagem de 17 tipos de recurso (Pods, Deployments, Services, StatefulSets, DaemonSets, Jobs, CronJobs, Nodes, ConfigMaps, Secrets, Ingresses, PVs, PVCs, HPAs, NetworkPolicies, ServiceAccounts, Events) organizados em 5 abas de categoria
- **Painel de detalhes**: clique em recurso abre Info + Events + YAML
- **Operações CRUD**: delete, scale (Deployment/StatefulSet), restart (rollout restart)
- **Busca por nome**: filtro instantâneo no explorer
- Backend de métricas (Prometheus + metrics-server) — **sem UI**
- Backend de RBAC Inspector — **sem UI**
- Backend de Plugin Host (discovery + lifecycle) — **sem UI**
- Backend de Settings (persistência JSON) — **sem UI**
- Tela Home (estática)
- Tema (dark/light)
- 148 testes unitários (122 para recursos + 16 para core + 10 para SettingsView)

O que **NÃO funciona / NÃO existe**:

- 6 das 9 views são `PlaceholderView` (Logs, Metrics, YAML, RBAC, Plugins, ~~Settings~~)
- **SettingsView implementada**: aparência, idioma, kubeconfig, telemetria, sobre
- Zero streaming de logs
- Zero exec/shell em containers
- Zero port-forward
- Zero recursos além de Pod/Deployment/Service (faltam Node, ConfigMap, Secret, Ingress, Job, CronJob, StatefulSet, DaemonSet, PV/PVC, HPA, NetworkPolicy, etc.)
- `apply_resource()` (create/update from YAML) ainda não implementado
- CLI (Typer) declarado como dependência mas nunca utilizado
- 1 dependência declarada e não usada (`typer`)

---

## EPIC-01: Resource Explorer Completo

> **Objetivo**: Transformar o explorer de uma lista simplificada em um painel completo de visualização, inspeção e gestão de recursos Kubernetes.

### STORY-01.01: Suporte a Todos os Tipos de Recurso Core

> O explorer hoje só lista Pod, Deployment e Service. Precisa cobrir todos os tipos essenciais.

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-01.01.01 | Task | Implementar `list_nodes()` em `kube/resources.py` | ✅ |
| TASK-01.01.02 | Task | Implementar `list_configmaps(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.03 | Task | Implementar `list_secrets(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.04 | Task | Implementar `list_ingresses(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.05 | Task | Implementar `list_jobs(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.06 | Task | Implementar `list_cronjobs(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.07 | Task | Implementar `list_statefulsets(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.08 | Task | Implementar `list_daemonsets(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.09 | Task | Implementar `list_persistentvolumes()` e `list_persistentvolumeclaims(namespace)` | ✅ |
| TASK-01.01.10 | Task | Implementar `list_hpa(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.11 | Task | Implementar `list_networkpolicies(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.12 | Task | Implementar `list_serviceaccounts(namespace)` em `kube/resources.py` | ✅ |
| TASK-01.01.13 | Task | Adicionar abas/seções no ExplorerView para cada tipo de recurso | ✅ |
| TASK-01.01.14 | Task | Testes unitários para cada nova função de listagem | ✅ |

### STORY-01.02: Painel de Detalhes de Recurso

> Ao clicar em um recurso, deve abrir um painel lateral/modal com todas as informações daquele recurso.

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-01.02.01 | Task | Implementar `get_resource(api_client, kind, name, namespace)` genérico em `kube/resources.py` | ✅ |
| TASK-01.02.02 | Task | Criar componente `ResourceDetailPanel` em `ui/views/` | ✅ |
| SUB-01.02.02.01 | Subtask | Seção de metadata (name, namespace, labels, annotations, creation timestamp) | ✅ |
| SUB-01.02.02.02 | Subtask | Seção de spec (renderização dinâmica baseada no kind) | ✅ |
| SUB-01.02.02.03 | Subtask | Seção de status (conditions, phase, ready) | ✅ |
| SUB-01.02.02.04 | Subtask | Seção de containers (para Pods: image, ports, env, resources, estado) | ✅ |
| TASK-01.02.03 | Task | Integrar detail panel no ExplorerView com click em recurso | ✅ |
| TASK-01.02.04 | Task | Testes para `get_resource` | ✅ |

### STORY-01.03: Visualização de Events

> Exibir Events do Kubernetes associados a recursos e do namespace.

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-01.03.01 | Task | Implementar `list_events(namespace, involved_object?)` em `kube/resources.py` | ✅ |
| TASK-01.03.02 | Task | Criar componente `EventsPanel` (tabela com type, reason, message, age, count) | ✅ |
| TASK-01.03.03 | Task | Integrar EventsPanel no ResourceDetailPanel (events do recurso selecionado) | ✅ |
| TASK-01.03.04 | Task | Adicionar aba de Events no ExplorerView (events do namespace) | ✅ |
| TASK-01.03.05 | Task | Testes unitários para `list_events` | ✅ |

### STORY-01.04: Visualização YAML de Recursos

> Ver o YAML completo de qualquer recurso diretamente do explorer.

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-01.04.01 | Task | Implementar `get_resource_yaml(api_client, kind, name, namespace) -> str` | ✅ |
| TASK-01.04.02 | Task | Criar componente `YamlViewer` (read-only, syntax highlight, copy to clipboard) | ✅ |
| TASK-01.04.03 | Task | Integrar YamlViewer no ResourceDetailPanel (aba YAML) | ✅ |
| TASK-01.04.04 | Task | Testes para serialização YAML | ✅ |

### STORY-01.05: Operações CRUD em Recursos

> Criar, editar e deletar recursos Kubernetes.

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-01.05.01 | Task | Implementar `delete_resource(api_client, kind, name, namespace)` em `kube/resources.py` | ✅ |
| TASK-01.05.02 | Task | Implementar `apply_resource(api_client, manifest_yaml)` (create or update) | ⬚ |
| TASK-01.05.03 | Task | Implementar `scale_resource(api_client, kind, name, namespace, replicas)` | ✅ |
| TASK-01.05.04 | Task | Implementar `restart_resource(api_client, kind, name, namespace)` (rollout restart) | ✅ |
| TASK-01.05.05 | Task | Verificar permissão via `RBACInspector.can_i()` antes de cada operação | ⬚ |
| TASK-01.05.06 | Task | Diálogo de confirmação para operações destrutivas (delete, scale to 0) | ✅ |
| TASK-01.05.07 | Task | Botões de ação no ResourceDetailPanel (Delete, Scale, Restart) | ✅ |
| TASK-01.05.08 | Task | Feedback visual de sucesso/erro via Snackbar | ✅ |
| TASK-01.05.09 | Task | Testes para operações CRUD (com mocks do API client) | ✅ |

### STORY-01.06: Busca e Filtros no Explorer

> Encontrar recursos rapidamente por nome, label ou status.

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-01.06.01 | Task | Adicionar campo de busca por nome (text filter) no ExplorerView | ✅ |
| TASK-01.06.02 | Task | Adicionar filtro por label selector | ⬚ |
| TASK-01.06.03 | Task | Adicionar filtro por status (Running, Pending, Failed, etc.) | ⬚ |
| TASK-01.06.04 | Task | Sorting por colunas (name, age, status) | ⬚ |

---

## EPIC-02: Logs — Streaming e Visualização

> **Objetivo**: Implementar visualização de logs de containers com streaming em tempo real, filtros, busca e exportação.

### STORY-02.01: Backend de Logs

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-02.01.01 | Task | Implementar `read_pod_logs(api_client, pod, namespace, container?, tail_lines?, since?)` em `kube/logs.py` | ⬚ |
| SUB-02.01.01.01 | Subtask | Suporte a `tail_lines` (últimas N linhas) | ⬚ |
| SUB-02.01.01.02 | Subtask | Suporte a `since_seconds` (logs desde X segundos atrás) | ⬚ |
| SUB-02.01.01.03 | Subtask | Suporte a container específico (multi-container pods) | ⬚ |
| SUB-02.01.01.04 | Subtask | Suporte a `previous=True` (logs de container anterior/crashloop) | ⬚ |
| TASK-02.01.02 | Task | Implementar `stream_pod_logs()` (follow=True, generator/async iterator) | ⬚ |
| TASK-02.01.03 | Task | Testes unitários para funções de log | ⬚ |

### STORY-02.02: LogsView — Interface de Visualização

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-02.02.01 | Task | Criar `LogsView` substituindo `PlaceholderView` | ⬚ |
| SUB-02.02.01.01 | Subtask | Seletor de Pod (dropdown com pods do namespace atual) | ⬚ |
| SUB-02.02.01.02 | Subtask | Seletor de Container (para pods multi-container) | ⬚ |
| SUB-02.02.01.03 | Subtask | Opção de tail lines (50, 100, 500, 1000, All) | ⬚ |
| SUB-02.02.01.04 | Subtask | Toggle "Previous container" para crashloop debugging | ⬚ |
| TASK-02.02.02 | Task | Painel de texto com scroll para exibir logs | ⬚ |
| SUB-02.02.02.01 | Subtask | Auto-scroll para o final (seguir novos logs) | ⬚ |
| SUB-02.02.02.02 | Subtask | Colorização por nível (ERROR=vermelho, WARN=amarelo, INFO=branco) | ⬚ |
| SUB-02.02.02.03 | Subtask | Timestamps formatados | ⬚ |
| TASK-02.02.03 | Task | Campo de busca/filtro de texto nos logs | ⬚ |
| TASK-02.02.04 | Task | Streaming em tempo real com toggle start/stop | ⬚ |

### STORY-02.03: Exportação de Logs

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-02.03.01 | Task | Botão "Export" — salvar logs como `.txt` | ⬚ |
| TASK-02.03.02 | Task | Botão "Export JSON" — salvar logs como `.json` (se formato JSON detectado) | ⬚ |
| TASK-02.03.03 | Task | Botão "Copy to clipboard" — copiar logs visíveis | ⬚ |

---

## EPIC-03: Exec — Terminal Remoto em Containers

> **Objetivo**: Permitir abrir um shell interativo dentro de containers Kubernetes.

### STORY-03.01: Backend de Exec

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-03.01.01 | Task | Implementar `exec_in_pod(api_client, pod, namespace, container, command)` em `kube/exec.py` | ⬚ |
| SUB-03.01.01.01 | Subtask | Conexão WebSocket via `stream()` do kubernetes-client | ⬚ |
| SUB-03.01.01.02 | Subtask | Suporte a stdin/stdout/stderr | ⬚ |
| SUB-03.01.01.03 | Subtask | Suporte a TTY (terminal interativo) | ⬚ |
| SUB-03.01.01.04 | Subtask | Detecção de shell disponível (`/bin/bash`, `/bin/sh`, `/bin/ash`) | ⬚ |
| TASK-03.01.02 | Task | Verificação RBAC antes de exec (`can_i("create", "pods/exec")`) | ⬚ |
| TASK-03.01.03 | Task | Testes para exec (mocked WebSocket) | ⬚ |

### STORY-03.02: Terminal UI

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-03.02.01 | Task | Integrar componente de terminal na UI (xterm.js via Flet ou widget custom) | ⬚ |
| SUB-03.02.01.01 | Subtask | Input de teclado → stdin do container | ⬚ |
| SUB-03.02.01.02 | Subtask | stdout/stderr do container → renderizar no terminal | ⬚ |
| SUB-03.02.01.03 | Subtask | Resize do terminal (SIGWINCH) | ⬚ |
| TASK-03.02.02 | Task | Seletor de Pod + Container para iniciar sessão | ⬚ |
| TASK-03.02.03 | Task | Suporte a múltiplas sessões de terminal simultâneas (tabs) | ⬚ |
| TASK-03.02.04 | Task | Botão de disconnect/encerrar sessão | ⬚ |

---

## EPIC-04: Port-Forward — Gestão de Túneis

> **Objetivo**: Permitir port-forward de Services e Pods com gerenciamento visual de túneis ativos.

### STORY-04.01: Backend de Port-Forward

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-04.01.01 | Task | Implementar `PortForwarder` em `kube/portforward.py` | ⬚ |
| SUB-04.01.01.01 | Subtask | Port-forward para Pod (local_port → pod_port) | ⬚ |
| SUB-04.01.01.02 | Subtask | Port-forward para Service (resolve para pod, forward) | ⬚ |
| SUB-04.01.01.03 | Subtask | Detecção de porta local disponível (auto-assign) | ⬚ |
| SUB-04.01.01.04 | Subtask | Lifecycle management (start/stop/health-check) | ⬚ |
| TASK-04.01.02 | Task | `PortForwardManager` — gerenciar múltiplos túneis ativos | ⬚ |
| TASK-04.01.03 | Task | Testes unitários | ⬚ |

### STORY-04.02: Port-Forward UI

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-04.02.01 | Task | Criar diálogo de "New Port Forward" (selecionar pod/service, portas) | ⬚ |
| TASK-04.02.02 | Task | Painel de túneis ativos (lista com status, local_port, remote, botão stop) | ⬚ |
| TASK-04.02.03 | Task | Indicador no navigation rail ou status bar de túneis ativos | ⬚ |
| TASK-04.02.04 | Task | Botão "Open in browser" para túneis HTTP | ⬚ |

---

## EPIC-05: Metrics Dashboard

> **Objetivo**: Conectar os adapters de métricas já implementados (Prometheus + metrics-server) a uma UI visual com gráficos e tabelas.

### STORY-05.01: Metrics View — Node & Pod Metrics

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-05.01.01 | Task | Criar `MetricsView` substituindo `PlaceholderView` | ⬚ |
| SUB-05.01.01.01 | Subtask | Tabela de Node metrics (CPU, Memory por nó — via `MetricsServerAdapter`) | ⬚ |
| SUB-05.01.01.02 | Subtask | Tabela de Pod metrics (CPU, Memory por pod/container) | ⬚ |
| SUB-05.01.01.03 | Subtask | Seletor de namespace para pod metrics | ⬚ |
| TASK-05.01.02 | Task | Detecção automática de metrics-server (graceful fallback se não instalado) | ⬚ |
| TASK-05.01.03 | Task | Testes para MetricsView | ⬚ |

### STORY-05.02: Gráficos de Métricas

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-05.02.01 | Task | Implementar gráficos de barras horizontais para CPU/Memory usage | ⬚ |
| TASK-05.02.02 | Task | Progress bars com percentual de utilização (requests vs limits vs actual) | ⬚ |
| TASK-05.02.03 | Task | Color coding: verde (<70%), amarelo (70-90%), vermelho (>90%) | ⬚ |

### STORY-05.03: Integração Prometheus

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-05.03.01 | Task | Campo de configuração da URL do Prometheus (Settings ou inline) | ⬚ |
| TASK-05.03.02 | Task | Queries pré-definidas (cluster CPU total, memory total, pod top-10) | ⬚ |
| TASK-05.03.03 | Task | Campo de query PromQL customizada (query bar) | ⬚ |
| TASK-05.03.04 | Task | Exibir resultados de PromQL em tabela | ⬚ |

---

## EPIC-06: RBAC Inspector UI

> **Objetivo**: Conectar o `RBACInspector` (backend já implementado) a uma interface visual de análise de permissões.

### STORY-06.01: RBAC View

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-06.01.01 | Task | Criar `RBACView` substituindo `PlaceholderView` | ⬚ |
| SUB-06.01.01.01 | Subtask | Aba "Cluster Roles" — tabela com ClusterRoles e suas rules | ⬚ |
| SUB-06.01.01.02 | Subtask | Aba "Roles" — tabela com Roles do namespace selecionado | ⬚ |
| SUB-06.01.01.03 | Subtask | Expandir role para ver rules (api_groups, resources, verbs) | ⬚ |
| TASK-06.01.02 | Task | Testes para RBACView | ⬚ |

### STORY-06.02: Who-Can-What Analysis

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-06.02.01 | Task | Implementar `list_cluster_role_bindings()` e `list_role_bindings(namespace)` em `security/rbac.py` | ⬚ |
| TASK-06.02.02 | Task | Aba "Bindings" — mostrar quem está bound a cada role | ⬚ |
| TASK-06.02.03 | Task | Funcionalidade "Can I?" — formulário: verb + resource + namespace → resultado | ⬚ |
| TASK-06.02.04 | Task | Funcionalidade "Who Can?" — dado um resource + verb, listar subjects com acesso | ⬚ |
| TASK-06.02.05 | Task | Testes para análise who-can-what | ⬚ |

---

## EPIC-07: YAML Editor

> **Objetivo**: Editor de manifests YAML com validação, syntax highlighting e diff contra estado live no cluster.

### STORY-07.01: Editor Básico

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-07.01.01 | Task | Criar `YamlEditorView` substituindo `PlaceholderView` | ⬚ |
| TASK-07.01.02 | Task | Área de texto editável com monospace font para YAML | ⬚ |
| TASK-07.01.03 | Task | Validação de sintaxe YAML em tempo real (usar `pyyaml`) | ⬚ |
| TASK-07.01.04 | Task | Botão "Apply" — enviar manifest ao cluster via `apply_resource()` | ⬚ |
| TASK-07.01.05 | Task | Verificação RBAC antes de apply | ⬚ |
| TASK-07.01.06 | Task | Feedback de sucesso/erro | ⬚ |

### STORY-07.02: Templates e Importação

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-07.02.01 | Task | Botão "Load from cluster" — abrir recurso existente para edição | ⬚ |
| TASK-07.02.02 | Task | Botão "Load from file" — abrir YAML do filesystem | ⬚ |
| TASK-07.02.03 | Task | Templates de recursos comuns (Pod, Deployment, Service, ConfigMap, etc.) | ⬚ |

### STORY-07.03: Diff contra Cluster

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-07.03.01 | Task | Implementar `diff_resource(api_client, manifest_yaml) -> DiffResult` em `kube/resources.py` | ⬚ |
| TASK-07.03.02 | Task | Visualização side-by-side (local vs live) com highlight de diferenças | ⬚ |
| TASK-07.03.03 | Task | Botão "Dry Run" — server-side dry-run para validar antes de aplicar | ⬚ |

### STORY-07.04: Validação com OpenAPI Schema

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-07.04.01 | Task | Obter OpenAPI schema do cluster (`/openapi/v2` ou `/openapi/v3`) | ⬚ |
| TASK-07.04.02 | Task | Validar manifest contra schema do cluster (field types, required fields) | ⬚ |
| TASK-07.04.03 | Task | Exibir erros de validação inline no editor | ⬚ |

---

## EPIC-08: Plugin Management UI

> **Objetivo**: Conectar o `PluginHost` (backend já implementado) a uma interface de gerenciamento de plugins.

### STORY-08.01: Plugins View

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-08.01.01 | Task | Criar `PluginsView` substituindo `PlaceholderView` | ⬚ |
| TASK-08.01.02 | Task | Lista de plugins descobertos (nome, módulo, status loaded/unloaded) | ⬚ |
| TASK-08.01.03 | Task | Botão Activate/Deactivate por plugin | ⬚ |
| TASK-08.01.04 | Task | Indicador visual de status (ícone verde=ativo, cinza=inativo, vermelho=erro) | ⬚ |
| TASK-08.01.05 | Task | Informações do plugin (versão, autor, descrição — se disponíveis no entry point metadata) | ⬚ |
| TASK-08.01.06 | Task | Testes para PluginsView | ⬚ |

### STORY-08.02: Plugin Host API para UI

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-08.02.01 | Task | Definir `HostAPI` que plugins recebem no `activate()` (acesso a AppContext, page, etc.) | ⬚ |
| TASK-08.02.02 | Task | Permitir plugins registrar: views custom, menu items, ações em recursos | ⬚ |
| TASK-08.02.03 | Task | Criar plugin de exemplo funcional no diretório `plugins/` | ⬚ |

---

## EPIC-09: Settings UI

> **Objetivo**: Conectar `AppSettings` (backend já implementado) a uma interface de configuração.

### STORY-09.01: Settings View

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-09.01.01 | Task | Criar `SettingsView` substituindo `PlaceholderView` | ✅ |
| SUB-09.01.01.01 | Subtask | Seção "Aparência": toggle dark/light theme (com apply em tempo real) | ✅ |
| SUB-09.01.01.02 | Subtask | Seção "Idioma": dropdown de idioma (en-US, pt-BR, etc.) | ✅ |
| SUB-09.01.01.03 | Subtask | Seção "Kubeconfig": campo para path do kubeconfig (com file picker) | ✅ |
| SUB-09.01.01.04 | Subtask | Seção "Telemetria": toggle opt-in com explicação clara | ✅ |
| SUB-09.01.01.05 | Subtask | Seção "Sobre": versão do app, links para docs e GitHub | ✅ |
| TASK-09.01.02 | Task | Botão "Save" que chama `AppSettings.save()` | ✅ |
| TASK-09.01.03 | Task | Carregar valores atuais de `AppSettings.load()` ao abrir a view | ✅ |
| TASK-09.01.04 | Task | Aplicar tema imediatamente ao trocar dark/light (sem precisar reiniciar) | ✅ |
| TASK-09.01.05 | Task | Testes para SettingsView | ✅ |

### STORY-09.02: Configurações Avançadas

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-09.02.01 | Task | Configuração de URL do Prometheus (para EPIC-05) | ⬚ |
| TASK-09.02.02 | Task | Configuração de log level da aplicação | ⬚ |
| TASK-09.02.03 | Task | Configuração de auto-refresh interval para Explorer | ⬚ |
| TASK-09.02.04 | Task | Reset to defaults | ✅ |

---

## EPIC-10: Watchers & Real-Time Updates

> **Objetivo**: Substituir polling manual por watches do Kubernetes API para atualizações em tempo real.

### STORY-10.01: Kubernetes Watch Backend

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-10.01.01 | Task | Implementar `ResourceWatcher` em `kube/watcher.py` usando `kubernetes.watch.Watch` | ⬚ |
| SUB-10.01.01.01 | Subtask | Watch para Pods (ADDED, MODIFIED, DELETED events) | ⬚ |
| SUB-10.01.01.02 | Subtask | Watch para Deployments | ⬚ |
| SUB-10.01.01.03 | Subtask | Watch para Services | ⬚ |
| SUB-10.01.01.04 | Subtask | Watch para Events | ⬚ |
| TASK-10.01.02 | Task | Reconexão automática com backoff exponencial | ⬚ |
| TASK-10.01.03 | Task | Testes para watcher | ⬚ |

### STORY-10.02: Integração UI com Watchers

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-10.02.01 | Task | ExplorerView atualiza automaticamente quando watch recebe evento | ⬚ |
| TASK-10.02.02 | Task | Indicador visual de "live" / "watching" no ExplorerView | ⬚ |
| TASK-10.02.03 | Task | Notificações visuais para eventos críticos (Pod crash, Deployment failed) | ⬚ |
| TASK-10.02.04 | Task | Auto-refresh configurável (toggle on/off, intervalo) | ⬚ |

---

## EPIC-11: CLI Interface

> **Objetivo**: Implementar interface CLI headless usando Typer (dependência já declarada mas não utilizada).

### STORY-11.01: Comandos CLI Básicos

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-11.01.01 | Task | Criar `kubeidea/cli.py` com Typer app | ⬚ |
| TASK-11.01.02 | Task | Comando `kubeidea contexts` — listar contextos do kubeconfig | ⬚ |
| TASK-11.01.03 | Task | Comando `kubeidea resources <kind> [--namespace]` — listar recursos | ⬚ |
| TASK-11.01.04 | Task | Comando `kubeidea logs <pod> [--namespace] [--follow]` — ver logs | ⬚ |
| TASK-11.01.05 | Task | Comando `kubeidea metrics [nodes|pods] [--namespace]` — ver métricas | ⬚ |
| TASK-11.01.06 | Task | Registrar CLI como entry point no `pyproject.toml` (`[project.scripts]`) | ⬚ |
| TASK-11.01.07 | Task | Testes para comandos CLI | ⬚ |

---

## EPIC-12: DevSecOps & Quality

> **Objetivo**: Hardening de segurança, qualidade de código e pipeline de CI/CD.

### STORY-12.01: Cobertura de Testes

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-12.01.01 | Task | Atingir ≥80% de cobertura em `kube/` (mocks do kubernetes client) | ⬚ |
| TASK-12.01.02 | Task | Atingir ≥80% de cobertura em `metrics/` | ⬚ |
| TASK-12.01.03 | Task | Atingir ≥80% de cobertura em `security/` | ⬚ |
| TASK-12.01.04 | Task | Atingir ≥80% de cobertura em `plugins/` | ⬚ |
| TASK-12.01.05 | Task | Atingir ≥80% de cobertura em `config/` | ⬚ |
| TASK-12.01.06 | Task | Adicionar `pytest-cov` ao CI com threshold de 80% | ⬚ |

### STORY-12.02: SBOM & Supply Chain

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-12.02.01 | Task | Integrar CycloneDX SBOM generation no CI | ⬚ |
| TASK-12.02.02 | Task | Publicar SBOM como artefato de release | ⬚ |
| TASK-12.02.03 | Task | License policy check (nenhuma dependência GPL em projeto MIT) | ⬚ |

### STORY-12.03: Code Signing & Notarization

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-12.03.01 | Task | macOS: Notarização com Apple Developer ID | ⬚ |
| TASK-12.03.02 | Task | Windows: Assinatura com SignTool | ⬚ |
| TASK-12.03.03 | Task | Linux: Assinatura de `.deb` e `.rpm` | ⬚ |

### STORY-12.04: Segurança de Secrets

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-12.04.01 | Task | Integrar `keyring` lib para persistência segura de credenciais | ⬚ |
| TASK-12.04.02 | Task | Sanitização de logs — nunca logar tokens, passwords ou secret values | ⬚ |
| TASK-12.04.03 | Task | Audit: varrer codebase por possíveis leaks de dados sensíveis | ⬚ |
| TASK-12.04.04 | Task | Usar `flet.security.encrypt/decrypt` (Fernet/AES-128) para dados sensíveis em trânsito e cache (ref: [Flet Cookbook — Encrypting Sensitive Data](https://docs.flet.dev/cookbook/encrypting-sensitive-data/)) | ⬚ |

---

## EPIC-13: UX & Polish

> **Objetivo**: Melhorias gerais de usabilidade, acessibilidade e experiência do usuário.

### STORY-13.01: Status Bar Global

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-13.01.01 | Task | Criar status bar no rodapé da janela | ⬚ |
| SUB-13.01.01.01 | Subtask | Exibir contexto ativo + namespace ativo | ⬚ |
| SUB-13.01.01.02 | Subtask | Exibir versão do cluster (server version) | ⬚ |
| SUB-13.01.01.03 | Subtask | Indicador de conexão (conectado/desconectado) | ⬚ |
| SUB-13.01.01.04 | Subtask | Contador de port-forwards ativos | ⬚ |

### STORY-13.02: Notificações e Feedback

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-13.02.01 | Task | Sistema de notificações (snackbar/toast) para ações do usuário | ⬚ |
| TASK-13.02.02 | Task | Loading indicators (spinners) para operações async | ⬚ |
| TASK-13.02.03 | Task | Error boundaries — tratar exceções sem crashar o app | ⬚ |

### STORY-13.03: Atalhos de Teclado

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-13.03.01 | Task | `Ctrl+K` — Command palette / busca rápida | ⬚ |
| TASK-13.03.02 | Task | `Ctrl+1..9` — Navegar para seção por número | ⬚ |
| TASK-13.03.03 | Task | `Ctrl+R` — Refresh view atual | ⬚ |
| TASK-13.03.04 | Task | `Ctrl+L` — Foco no campo de busca/filtro | ⬚ |
| TASK-13.03.05 | Task | `Escape` — Fechar painel de detalhes / cancelar operação | ⬚ |
| TASK-13.03.06 | Task | Implementar handler global `page.on_keyboard_event` (ref: [Flet Cookbook — Keyboard Shortcuts](https://docs.flet.dev/cookbook/keyboard-shortcuts/)) | ⬚ |

### STORY-13.04: Multi-contexto Simultâneo

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-13.04.01 | Task | Suporte a múltiplos clusters conectados simultaneamente | ⬚ |
| TASK-13.04.02 | Task | Tabs ou split-view para comparar recursos entre clusters | ⬚ |
| TASK-13.04.03 | Task | Context switcher rápido no status bar | ⬚ |

### STORY-13.05: Internacionalização (i18n)

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-13.05.01 | Task | Implementar sistema de i18n (dicionários de strings) | ⬚ |
| TASK-13.05.02 | Task | Tradução pt-BR completa | ⬚ |
| TASK-13.05.03 | Task | Tradução en-US completa (base) | ⬚ |
| TASK-13.05.04 | Task | Carregar idioma de `AppSettings.language` | ⬚ |

### STORY-13.06: Animações e Transições

> Usar animações implícitas do Flet para transições suaves entre views e estados da UI.
> Ref: [Flet Cookbook — Animations](https://docs.flet.dev/cookbook/animations/)

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-13.06.01 | Task | `AnimatedSwitcher` para transição ao trocar views no `content_area` (navegação) | ⬚ |
| TASK-13.06.02 | Task | `animate_opacity` para fade-in/out do detail panel no Explorer | ⬚ |
| TASK-13.06.03 | Task | `animate` em containers de cards de recurso (hover, seleção) | ⬚ |
| TASK-13.06.04 | Task | `animate_offset` para slide-in do painel lateral de detalhes | ⬚ |

### STORY-13.07: Acessibilidade (a11y)

> Garantir que o app seja utilizável com screen readers e teclado.
> Ref: [Flet Cookbook — Accessibility](https://docs.flet.dev/cookbook/accessibility/)

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-13.07.01 | Task | Adicionar `tooltip` em todos os `IconButton` sem label visível | ⬚ |
| TASK-13.07.02 | Task | Adicionar `semantics_label` em textos de status (ícones de cor, badges) | ⬚ |
| TASK-13.07.03 | Task | `Shift+S` — Toggle `page.show_semantics_debugger` em modo dev | ⬚ |
| TASK-13.07.04 | Task | Garantir que `Dropdown.label` e `TextField.label` estão presentes para screen readers | ⬚ |

### STORY-13.08: Otimização de Listas Grandes

> Otimizar performance de scroll para clusters com centenas/milhares de recursos.
> Ref: [Flet Cookbook — Large Lists](https://docs.flet.dev/cookbook/large-lists/)

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-13.08.01 | Task | Definir `first_item_prototype=True` nos `ListView` do Explorer para scroll otimizado | ⬚ |
| TASK-13.08.02 | Task | Implementar batch updates (`page.update()` a cada N itens) para carregamento inicial | ⬚ |
| TASK-13.08.03 | Task | Avaliar `GridView` com `max_extent` para visualização alternativa de recursos | ⬚ |
| TASK-13.08.04 | Task | Paginação virtual — carregar recursos sob demanda ao scrollar | ⬚ |

### STORY-13.09: Theming Avançado

> Aproveitar nested themes e `color_scheme_seed` do Flet para UI mais expressiva.
> Ref: [Flet Cookbook — Theming](https://docs.flet.dev/cookbook/theming/)

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-13.09.01 | Task | Usar `Container.theme_mode` para painéis de erro (forçar tema com destaque vermelho) | ⬚ |
| TASK-13.09.02 | Task | Nested theme para RBAC Inspector (color_scheme_seed distinto) | ⬚ |
| TASK-13.09.03 | Task | Usar `page.dark_theme` com seed diferente de `page.theme` para melhor contraste | ⬚ |
| TASK-13.09.04 | Task | Permitir seleção de cor de destaque (accent color) nas Settings | ⬚ |

---

## EPIC-14: Limpeza Técnica & Debt

> **Objetivo**: Resolver débito técnico acumulado.

### STORY-14.01: Dependências Não Utilizadas

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-14.01.01 | Task | Usar `pyyaml` no projeto (YAML Editor) ou remover do `pyproject.toml` | ✅ |
| TASK-14.01.02 | Task | ~~Usar `typer`~~ Removido do `pyproject.toml` — não utilizado | ✅ |

### STORY-14.02: Modelos de Dados Tipados

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-14.02.01 | Task | Substituir `list[dict]` retornados por `list_pods()` etc. por Pydantic models tipados | ⬚ |
| TASK-14.02.02 | Task | Criar models: `PodInfo`, `DeploymentInfo`, `ServiceInfo`, `NodeInfo`, etc. | ⬚ |
| TASK-14.02.03 | Task | Atualizar ExplorerView para consumir models tipados | ⬚ |

### STORY-14.03: Async/Threading

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-14.03.01 | Task | Mover chamadas Kubernetes API para threads (`asyncio.to_thread`) | ✅ |
| TASK-14.03.02 | Task | Loading states enquanto API calls estão em andamento | ⬚ |
| TASK-14.03.03 | Task | Tratamento de timeout para chamadas ao cluster | ⬚ |
| TASK-14.03.04 | Task | Converter `main()` para `async def main()` e usar `async` event handlers | ✅ |
| TASK-14.03.05 | Task | Usar `page.run_task()` para background tasks (auto-refresh, watchers) | ✅ |
| TASK-14.03.06 | Task | Usar `did_mount()`/`will_unmount()` para lifecycle de views com tarefas contínuas (ex: streaming de logs) | ⬚ |

### STORY-14.04: Documentação do Código

| ID | Tipo | Descrição | Status |
|---|---|---|---|
| TASK-14.04.01 | Task | Docstrings completas em todos os módulos públicos | ⬚ |
| TASK-14.04.02 | Task | Atualizar `docs/architecture.md` refletindo estado real | ⬚ |
| TASK-14.04.03 | Task | Atualizar `README.md` — separar "Features implementadas" de "Planejadas" | ⬚ |

---

## Resumo por EPIC

| EPIC | Título | Stories | Tasks | Prioridade Sugerida |
|---|---|---|---|---|
| EPIC-01 | Resource Explorer Completo | 6 | 36 | 🔴 Crítica |
| EPIC-02 | Logs — Streaming e Visualização | 3 | 16 | 🔴 Crítica |
| EPIC-03 | Exec — Terminal Remoto | 2 | 10 | 🟠 Alta |
| EPIC-04 | Port-Forward | 2 | 8 | 🟠 Alta |
| EPIC-05 | Metrics Dashboard | 3 | 10 | 🟡 Média |
| EPIC-06 | RBAC Inspector UI | 2 | 8 | 🟡 Média |
| EPIC-07 | YAML Editor | 4 | 12 | 🟡 Média |
| EPIC-08 | Plugin Management UI | 2 | 9 | 🟢 Baixa |
| EPIC-09 | Settings UI | 2 | 13 | 🟡 Média |
| EPIC-10 | Watchers & Real-Time | 2 | 8 | 🟡 Média |
| EPIC-11 | CLI Interface | 1 | 7 | 🟢 Baixa |
| EPIC-12 | DevSecOps & Quality | 4 | 16 | 🟠 Alta |
| EPIC-13 | UX & Polish | 9 | 33 | 🟢 Baixa |
| EPIC-14 | Limpeza Técnica & Debt | 4 | 14 | 🟡 Média |
| **TOTAL** | | **46** | **191** | |

---

## Ordem de Execução Sugerida

```
Fase 1 — Fundação (EPIC-14 + EPIC-09)
  └─ Limpar debt, tipar modelos, async/threading (Flet Cookbook), Settings UI
      │
Fase 2 — Core Features (EPIC-01 + EPIC-02)
  └─ Explorer completo + Logs (com did_mount/will_unmount para streaming)
      │
Fase 3 — Operações (EPIC-03 + EPIC-04 + EPIC-05)
  └─ Exec, Port-Forward, Metrics
      │
Fase 4 — Segurança & Edição (EPIC-06 + EPIC-07 + EPIC-12)
  └─ RBAC UI, YAML Editor, DevSecOps (flet.security.encrypt/decrypt)
      │
Fase 5 — Extensibilidade & UX (EPIC-08 + EPIC-10 + EPIC-11 + EPIC-13)
  └─ Plugins UI, Watchers, CLI, Polish (animações, a11y, large lists, theming, atalhos)
```
