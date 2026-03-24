# Per-Repo Dependency Details

Detailed dependency information for each Server Foundation repository.

## open-cluster-management-io (upstream)

### api
- **Go deps on SF repos**: None (foundation layer)
- **Provides**: All OCM CRD types — ManagedCluster, ManifestWork, Placement, ManagedClusterAddOn, ClusterManagementAddOn, ClusterManager, Klusterlet
- **Used by**: Every other SF repo

### sdk-go
- **Go deps**: api
- **Provides**: Base controller factory, CloudEvents (MQTT/gRPC/PubSub), cert rotation, patcher, CEL library, serving cert
- **Used by**: addon-framework, ocm, cluster-proxy, managedcluster-import-controller, multicloud-operators-foundation, cluster-proxy-addon, backplane-operator

### addon-framework
- **Go deps**: api, sdk-go
- **Provides**: Addon manager, agent interface, addon factory, lease controller, test utilities
- **Used by**: ocm, cluster-proxy, managed-serviceaccount, multicloud-operators-foundation, cluster-proxy-addon

### ocm
- **Go deps**: api, sdk-go, addon-framework
- **Provides**: OCM hub implementation — registration, work, placement, addon-manager controllers; Helm chart helpers
- **Used by**: managedcluster-import-controller (chart helpers)

### cluster-proxy
- **Go deps**: api, sdk-go, addon-framework
- **External deps**: apiserver-network-proxy (konnectivity)
- **Provides**: Konnectivity-based proxy for accessing managed clusters

### managed-serviceaccount
- **Go deps**: api, addon-framework (sdk-go indirect)
- **Provides**: ManagedServiceAccount CRD and addon for token-based SA projection
- **Used by**: cluster-permission, multicloud-operators-foundation

### cluster-permission
- **Go deps**: api, managed-serviceaccount
- **Provides**: ClusterPermission CRD for RBAC distribution via ManifestWork
- **Used by**: multicluster-role-assignment, multicloud-operators-foundation

## stolostron (downstream)

### managedcluster-import-controller
- **Go deps**: api, sdk-go, ocm (chart helpers), cluster-lifecycle-api
- **Function**: Manages cluster import workflow, creates ManifestWork for cluster bootstrap

### multicloud-operators-foundation
- **Go deps**: api, sdk-go, addon-framework, managed-serviceaccount, cluster-permission, cluster-lifecycle-api
- **Function**: Foundation controllers — heaviest dependency footprint among SF repos
- **Note**: Uses both managed-serviceaccount and cluster-permission client APIs

### clusterlifecycle-state-metrics
- **Go deps**: api (v1.1.0), cluster-lifecycle-api, stolostron/applier, stolostron/library-go
- **Function**: Prometheus metrics exporter for cluster lifecycle
- **Note**: Uses outdated api v1.1.0

### cluster-proxy-addon
- **Go deps**: api (v0.15.0), sdk-go (v0.15.0), addon-framework (v0.11.0)
- **Function**: Addon manager for cluster-proxy deployment
- **Note**: Uses very outdated dependencies — deprecated from backplane-2.11

### klusterlet-addon-controller
- **Go deps**: api (v0.14.1), cluster-lifecycle-api
- **Function**: Creates ManagedClusterAddon resources for klusterlet add-ons

### multicluster-role-assignment
- **Go deps**: api, cluster-permission
- **Function**: Higher-level abstraction — uses Placement to create ClusterPermission per cluster

### backplane-operator
- **Go deps**: api (v0.13.0), sdk-go
- **Function**: MCE operator — deploys all SF components via Helm charts
- **Manages**: ClusterManager CR, server-foundation, cluster-permission, managed-serviceaccount, cluster-proxy-addon
