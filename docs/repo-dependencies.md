# Server Foundation Repository Dependencies

This document describes the inter-dependencies between all Server Foundation owned repositories, covering Go module imports, API/CRD type usage, runtime/functional coupling, test dependencies, and deployment relationships.

For the repo list and branch conventions, see [repos.md](repos.md).

## Dependency Overview Diagram

```mermaid
graph TD
    subgraph "Layer 0 — API Definitions"
        API["ocm-io/api"]
    end

    subgraph "Layer 1 — SDK"
        SDK["ocm-io/sdk-go"]
    end

    subgraph "Layer 2 — Framework"
        AF["ocm-io/addon-framework"]
    end

    subgraph "Layer 3 — Core & Addons"
        OCM["ocm-io/ocm"]
        CP["ocm-io/cluster-proxy"]
        MSA["ocm-io/managed-serviceaccount"]
    end

    subgraph "Layer 4 — Higher-level"
        CPERM["ocm-io/cluster-permission"]
    end

    SDK --> API
    AF --> API
    AF --> SDK
    OCM --> API
    OCM --> SDK
    OCM --> AF
    CP --> API
    CP --> SDK
    CP --> AF
    MSA --> API
    MSA --> AF
    CPERM --> API
    CPERM --> MSA
```

## Upstream (ocm-io) Dependency Layers

The upstream OCM repos follow a clean, acyclic layered architecture:

| Layer | Repo | Depends On | Provides |
|-------|------|------------|----------|
| 0 | `api` | (none) | All OCM CRD types: ManagedCluster, ManifestWork, Placement, AddOn, ClusterManager |
| 1 | `sdk-go` | api | Base controller factory, CloudEvents (MQTT/gRPC), cert rotation, patcher, CEL library |
| 2 | `addon-framework` | api, sdk-go | Addon manager, agent interface, addon factory, lease controller |
| 3 | `ocm` | api, sdk-go, addon-framework | OCM hub: registration, work, placement, addon-manager controllers |
| 3 | `cluster-proxy` | api, sdk-go, addon-framework | Konnectivity-based cluster proxy addon |
| 3 | `managed-serviceaccount` | api, addon-framework | Token-based ServiceAccount projection addon |
| 4 | `cluster-permission` | api, managed-serviceaccount | RBAC permission distribution across clusters |

No circular dependencies exist in the upstream layer.

## Downstream (stolostron) Dependencies

### Upstream Fork Relationships

```mermaid
graph LR
    subgraph "Upstream (ocm-io)"
        U_OCM["ocm-io/ocm"]
        U_CP["ocm-io/cluster-proxy"]
        U_MSA["ocm-io/managed-serviceaccount"]
    end

    subgraph "Downstream (stolostron)"
        D_OCM["stolostron/ocm"]
        D_CP["stolostron/cluster-proxy"]
        D_MSA["stolostron/managed-serviceaccount"]
    end

    U_OCM -.->|fork| D_OCM
    U_CP -.->|fork| D_CP
    U_MSA -.->|fork| D_MSA
```

Three stolostron repos are direct downstream forks of upstream ocm-io repos. They carry the same Go module path and share the same dependency structure.

### stolostron-only Repos

These repos exist only in stolostron (no upstream equivalent):

| Repo | Key SF Dependencies |
|------|---------------------|
| `managedcluster-import-controller` | api, sdk-go, stolostron/ocm (chart helpers), cluster-lifecycle-api |
| `multicloud-operators-foundation` | api, sdk-go, addon-framework, managed-serviceaccount, cluster-permission, cluster-lifecycle-api |
| `clusterlifecycle-state-metrics` | api, cluster-lifecycle-api, stolostron/applier |
| `cluster-proxy-addon` | api, sdk-go, addon-framework |
| `klusterlet-addon-controller` | api, cluster-lifecycle-api |
| `multicluster-role-assignment` | api, cluster-permission |
| `backplane-operator` | api, sdk-go (deploys all SF components) |

## Full Dependency Graph

```mermaid
graph TD
    %% Upstream foundation
    API["api<br/><i>CRD definitions</i>"]
    SDK["sdk-go<br/><i>controller SDK</i>"]
    AF["addon-framework<br/><i>addon SDK</i>"]

    %% Upstream addons & core
    OCM["ocm<br/><i>hub operator</i>"]
    CP["cluster-proxy<br/><i>proxy addon</i>"]
    MSA["managed-serviceaccount<br/><i>SA addon</i>"]
    CPERM["cluster-permission<br/><i>RBAC addon</i>"]

    %% stolostron-only
    MIC["managedcluster-import-controller<br/><i>cluster import</i>"]
    MOF["multicloud-operators-foundation<br/><i>foundation controllers</i>"]
    CSM["clusterlifecycle-state-metrics<br/><i>metrics exporter</i>"]
    CPA["cluster-proxy-addon<br/><i>proxy addon mgr</i>"]
    KAC["klusterlet-addon-controller<br/><i>klusterlet addons</i>"]
    MRA["multicluster-role-assignment<br/><i>multicluster RBAC</i>"]
    BPO["backplane-operator<br/><i>MCE installer</i>"]

    %% External
    CLAPI["cluster-lifecycle-api<br/><i>ACM helpers</i>"]

    %% Layer 0→1
    SDK --> API
    %% Layer 1→2
    AF --> API
    AF --> SDK
    %% Layer 2→3
    OCM --> AF
    OCM --> SDK
    OCM --> API
    CP --> AF
    CP --> API
    MSA --> AF
    MSA --> API
    %% Layer 3→4
    CPERM --> MSA
    CPERM --> API

    %% stolostron-only deps
    MIC --> API
    MIC --> SDK
    MIC --> OCM
    MIC --> CLAPI

    MOF --> API
    MOF --> SDK
    MOF --> AF
    MOF --> MSA
    MOF --> CPERM
    MOF --> CLAPI

    CSM --> API
    CSM --> CLAPI

    CPA --> API
    CPA --> SDK
    CPA --> AF

    KAC --> API
    KAC --> CLAPI

    MRA --> API
    MRA --> CPERM

    BPO --> API
    BPO --> SDK

    %% Styling
    classDef upstream fill:#e1f5fe,stroke:#0288d1
    classDef downstream fill:#fff3e0,stroke:#f57c00
    classDef external fill:#f3e5f5,stroke:#7b1fa2
    classDef foundation fill:#e8f5e9,stroke:#388e3c

    class API,SDK,AF foundation
    class OCM,CP,MSA,CPERM upstream
    class MIC,MOF,CSM,CPA,KAC,MRA,BPO downstream
    class CLAPI external
```

## Deployment Dependency Graph

This diagram shows how `backplane-operator` deploys all SF components at runtime:

```mermaid
graph TD
    BPO["backplane-operator<br/><i>MCE Operator</i>"]

    subgraph "OCM Core (via ClusterManager CR)"
        REG["registration"]
        WORK["work"]
        PLACE["placement"]
        ADDONMGR["addon-manager"]
    end

    subgraph "Server Foundation Chart"
        MIC["managedcluster-import-controller"]
        OCMCTRL["ocm-controller<br/><i>(foundation)</i>"]
        OCMPROXY["ocm-proxyserver"]
    end

    subgraph "Toggle Components (optional)"
        CPERM["cluster-permission"]
        MSA["managed-serviceaccount"]
        CPA["cluster-proxy-addon"]
    end

    BPO -->|"ClusterManager CR"| REG
    BPO -->|"ClusterManager CR"| WORK
    BPO -->|"ClusterManager CR"| PLACE
    BPO -->|"ClusterManager CR"| ADDONMGR
    BPO -->|"server-foundation chart"| MIC
    BPO -->|"server-foundation chart"| OCMCTRL
    BPO -->|"server-foundation chart"| OCMPROXY
    BPO -->|"toggle chart"| CPERM
    BPO -->|"toggle chart"| MSA
    BPO -->|"toggle chart"| CPA

    classDef operator fill:#ffecb3,stroke:#ff8f00
    classDef core fill:#e1f5fe,stroke:#0288d1
    classDef sf fill:#e8f5e9,stroke:#388e3c
    classDef toggle fill:#fff3e0,stroke:#f57c00

    class BPO operator
    class REG,WORK,PLACE,ADDONMGR core
    class MIC,OCMCTRL,OCMPROXY sf
    class CPERM,MSA,CPA toggle
```

## Runtime Integration Flow

This diagram shows how components interact at runtime:

```mermaid
graph LR
    subgraph "Hub Cluster"
        MRA["multicluster-role-assignment"]
        CPERM["cluster-permission"]
        MSA["managed-serviceaccount"]
        MIC["managedcluster-import-controller"]
        MOF["foundation controllers"]
        CPA["cluster-proxy-addon"]
        KAC["klusterlet-addon-controller"]
    end

    subgraph "Managed Cluster"
        AGENT["proxy-agent"]
        MSAAGENT["msa-agent"]
        RBAC["RBAC resources"]
    end

    subgraph "OCM CRDs"
        MW["ManifestWork"]
        MC["ManagedCluster"]
        PL["Placement"]
        MCA["ManagedClusterAddon"]
        CP_CR["ClusterPermission"]
        MSA_CR["ManagedServiceAccount"]
        MCRA["MultiClusterRoleAssignment"]
    end

    MRA -->|"watches"| MCRA
    MRA -->|"resolves"| PL
    MRA -->|"creates"| CP_CR
    CPERM -->|"watches"| CP_CR
    CPERM -->|"checks"| MSA_CR
    CPERM -->|"creates"| MW
    MW -->|"distributes"| RBAC
    MSA -->|"manages"| MSA_CR
    MSA -->|"deploys agent"| MSAAGENT
    MIC -->|"watches"| MC
    MIC -->|"creates"| MW
    MOF -->|"uses"| MSA_CR
    MOF -->|"uses"| CP_CR
    CPA -->|"manages"| MCA
    CPA -->|"deploys"| AGENT
    KAC -->|"watches"| MC
    KAC -->|"creates"| MCA
```

## Detailed Per-Repo Dependencies

### open-cluster-management-io (upstream)

#### api
- **Go deps on SF repos**: None (foundation layer)
- **Provides**: All OCM CRD types — ManagedCluster, ManifestWork, Placement, ManagedClusterAddOn, ClusterManagementAddOn, ClusterManager, Klusterlet
- **Used by**: Every other SF repo

#### sdk-go
- **Go deps**: api
- **Provides**: Base controller factory, CloudEvents (MQTT/gRPC/PubSub), cert rotation, patcher, CEL library, serving cert
- **Used by**: addon-framework, ocm, cluster-proxy, managedcluster-import-controller, multicloud-operators-foundation, cluster-proxy-addon, backplane-operator

#### addon-framework
- **Go deps**: api, sdk-go
- **Provides**: Addon manager, agent interface, addon factory, lease controller, test utilities
- **Used by**: ocm, cluster-proxy, managed-serviceaccount, multicloud-operators-foundation, cluster-proxy-addon

#### ocm
- **Go deps**: api, sdk-go, addon-framework
- **Provides**: OCM hub implementation — registration, work, placement, addon-manager controllers; Helm chart helpers
- **Used by**: managedcluster-import-controller (chart helpers)

#### cluster-proxy
- **Go deps**: api, sdk-go, addon-framework
- **External deps**: apiserver-network-proxy (konnectivity)
- **Provides**: Konnectivity-based proxy for accessing managed clusters

#### managed-serviceaccount
- **Go deps**: api, addon-framework (sdk-go indirect)
- **Provides**: ManagedServiceAccount CRD and addon for token-based SA projection
- **Used by**: cluster-permission, multicloud-operators-foundation

#### cluster-permission
- **Go deps**: api, managed-serviceaccount
- **Provides**: ClusterPermission CRD for RBAC distribution via ManifestWork
- **Used by**: multicluster-role-assignment, multicloud-operators-foundation

### stolostron (downstream)

#### managedcluster-import-controller
- **Go deps**: api, sdk-go, ocm (chart helpers), cluster-lifecycle-api
- **Function**: Manages cluster import workflow, creates ManifestWork for cluster bootstrap

#### multicloud-operators-foundation
- **Go deps**: api, sdk-go, addon-framework, managed-serviceaccount, cluster-permission, cluster-lifecycle-api
- **Function**: Foundation controllers — heaviest dependency footprint among SF repos
- **Note**: Uses both managed-serviceaccount and cluster-permission client APIs

#### clusterlifecycle-state-metrics
- **Go deps**: api (v1.1.0), cluster-lifecycle-api, stolostron/applier, stolostron/library-go
- **Function**: Prometheus metrics exporter for cluster lifecycle
- **Note**: Uses outdated api v1.1.0

#### cluster-proxy-addon
- **Go deps**: api (v0.15.0), sdk-go (v0.15.0), addon-framework (v0.11.0)
- **Function**: Addon manager for cluster-proxy deployment
- **Note**: Uses very outdated dependencies — deprecated from backplane-2.11

#### klusterlet-addon-controller
- **Go deps**: api (v0.14.1), cluster-lifecycle-api
- **Function**: Creates ManagedClusterAddon resources for klusterlet add-ons

#### multicluster-role-assignment
- **Go deps**: api, cluster-permission
- **Function**: Higher-level abstraction — uses Placement to create ClusterPermission per cluster

#### backplane-operator
- **Go deps**: api (v0.13.0), sdk-go
- **Function**: MCE operator — deploys all SF components via Helm charts
- **Manages**: ClusterManager CR, server-foundation, cluster-permission, managed-serviceaccount, cluster-proxy-addon

## Version Alignment

| Repo | api version | sdk-go version | addon-framework version | Status |
|------|-------------|----------------|------------------------|--------|
| sdk-go | v1.2.1 | — | — | Current |
| addon-framework | v1.2.1 | v1.2.1 | — | Current |
| ocm | v1.2.1 | v1.2.1 | v1.2.1 | Current |
| cluster-proxy | v1.2.0 | v1.2.0 | v1.2.0 | Current |
| managed-serviceaccount | v1.2.0 | — | v1.2.0 | Current |
| multicloud-operators-foundation | v1.2.1 | v1.2.1 | v1.2.1 | Current |
| managedcluster-import-controller | v1.2.0 | v1.2.1 | — | Current |
| multicluster-role-assignment | v1.2.0 | — | — | Current |
| cluster-permission | **v0.15.0** | — | — | Outdated |
| clusterlifecycle-state-metrics | **v1.1.0** | — | — | Outdated |
| cluster-proxy-addon | **v0.15.0** | **v0.15.0** | **v0.11.0** | Very outdated |
| klusterlet-addon-controller | **v0.14.1** | — | — | Outdated |
| backplane-operator | **v0.13.0** | **v0.13.1** | — | Outdated |

## Key Observations

1. **Clean layered architecture** — No circular dependencies in the upstream layer. Each layer only depends on layers below it.

2. **`api` is the universal foundation** — Every SF repo depends on it. Changes here have the widest blast radius.

3. **`multicloud-operators-foundation` is the heaviest consumer** — It depends on api, sdk-go, addon-framework, managed-serviceaccount, cluster-permission, and cluster-lifecycle-api.

4. **`backplane-operator` is the deployment root** — It deploys all MCE/SF components via Helm charts and ClusterManager CR.

5. **Version drift** — Several downstream repos use significantly outdated dependency versions. `cluster-proxy-addon` (deprecated from backplane-2.11) is the most outdated.

6. **`cluster-lifecycle-api` is a shared stolostron dependency** — Used by managedcluster-import-controller, multicloud-operators-foundation, clusterlifecycle-state-metrics, and klusterlet-addon-controller.

7. **Runtime chain**: `multicluster-role-assignment → cluster-permission → ManifestWork → managed cluster RBAC` forms the RBAC distribution pipeline.
