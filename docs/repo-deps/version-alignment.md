# Dependency Version Alignment

Current dependency versions across all Server Foundation repositories.

## Version Table

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
