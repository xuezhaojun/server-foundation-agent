---
title: OCM upstream dependency version survey and compatibility tiers
symptom: "Need to determine which OCM dependency versions are compatible with a given branch"
keywords: [OCM, addon-framework, api, sdk-go, k8s.io, controller-runtime, version, tier, compatibility, backplane, release, dependency]
affected_versions: "All ACM/MCE versions"
last_verified: 2026-03-19
status: active
---

# OCM Dependency Versions Survey

Updated: 2026-03-19

## Upstream Dependency Analysis (addon-framework / api / sdk-go)

This section shows the Go version and k8s.io package versions required by each tagged release of the three OCM upstream dependencies. This is critical for understanding upgrade compatibility — jumping to a newer version of these libraries may force a Go and k8s version bump.

### addon-framework

| Version | Go | k8s.io/* | controller-runtime |
|---------|-----|---------|-------------------|
| v0.9.0 | 1.21 | v0.29.x | v0.16.2 |
| v0.11.0 | 1.22 | v0.30.x | v0.18.4 |
| v0.12.0 | 1.22 | v0.30.x | v0.18.4 |
| v1.1.0 | 1.24 | v0.33.x | v0.20.2 |
| v1.1.1 | 1.24 | v0.33.x | v0.20.2 |
| v1.2.0 | 1.25 | v0.34.x | v0.22.4 |

### api

| Version | Go | k8s.io/* | controller-runtime |
|---------|-----|---------|-------------------|
| v0.8.0 | 1.18 | v0.23.x | v0.11.1 |
| v0.13.0 | 1.21 | v0.29.x | v0.16.2 |
| v0.15.0 | 1.22 | v0.30.x | v0.18.4 |
| v0.16.0 | 1.22 | v0.30.x | v0.18.4 |
| v0.16.1 | 1.22 | v0.30.x | v0.18.4 |
| v1.1.0 | 1.24 | v0.33.x | v0.20.2 |
| v1.2.0 | 1.25 | v0.34.x | v0.22.3 |

### sdk-go

| Version | Go | k8s.io/* | controller-runtime |
|---------|-----|---------|-------------------|
| v0.13.0 | 1.21 | v0.29.x | v0.16.2 |
| v0.15.0 | 1.22 | v0.30.x | v0.18.4 |
| v0.16.0 | 1.22 | v0.30.x | v0.18.4 |
| v1.1.0 | 1.24 | v0.33.x | v0.20.2 |
| v1.2.0 | 1.25 | v0.34.x | v0.22.3 |

### Version Tier Summary

| Tier | addon-framework | api | sdk-go | Go | k8s.io | controller-runtime |
|------|----------------|-----|--------|-----|--------|-------------------|
| Tier A (oldest) | v0.9.0 | v0.8.0, v0.13.0 | v0.13.0 | 1.18~1.21 | v0.23~v0.29 | v0.11~v0.16 |
| Tier B | v0.11.0, v0.12.0 | v0.15.0, v0.16.x | v0.15.0, v0.16.0 | 1.22 | v0.30 | v0.18 |
| Tier C | v1.1.x | v1.1.0 | v1.1.0 | 1.24 | v0.33 | v0.20 |
| Tier D (newest) | v1.2.0 | v1.2.0 | v1.2.0 | 1.25 | v0.34 | v0.22 |

**Key insight**: There are 4 distinct compatibility tiers. Upgrading across tiers requires bumping Go version and all k8s.io packages simultaneously. Within the same tier, versions are interchangeable.

---

## Per-Release Dependency Usage

### backplane-2.7 / release-2.12

| Branch | Repo | addon-framework | api | sdk-go |
|--------|------|-----------------|-----|--------|
| backplane-2.7 | cluster-proxy | v0.11.0 | v0.15.0 | v0.15.0 |
| backplane-2.7 | cluster-proxy-addon | v0.11.0 | v0.15.0 | v0.15.0 |
| backplane-2.7 | clusterlifecycle-state-metrics | - | v0.8.0 | - |
| backplane-2.7 | managed-serviceaccount | v0.9.0 | v0.13.0 | v0.13.0 |
| backplane-2.7 | managedcluster-import-controller | - | v0.14.1-0.20240627145512-bd6f2229b53c | - |
| backplane-2.7 | multicloud-operators-foundation | v0.9.1-0.20240416063208-ecb7f349df05 | v0.14.1-0.20240627145512-bd6f2229b53c | v0.13.1-0.20240416030555-aa744f426379 |
| backplane-2.7 | ocm | v0.10.1-0.20241009100235-11aa520f541f | v0.14.1-0.20241008081048-f6c658202790 | v0.14.1-0.20240918072645-225dcf1b6866 |
| release-2.12 | cluster-permission | - | v0.13.0 | - |
| release-2.12 | klusterlet-addon-controller | - | v0.14.1-0.20240627145512-bd6f2229b53c | - |

> **Tier**: Mixed A/B — managed-serviceaccount on Tier A (Go 1.21, k8s v0.29), others on Tier B (Go 1.22, k8s v0.30). Pseudo-versions are between A and B.

---

### backplane-2.8 / release-2.13

| Branch | Repo | addon-framework | api | sdk-go |
|--------|------|-----------------|-----|--------|
| backplane-2.8 | cluster-proxy | v0.12.0 | v0.16.0 | v0.16.0 |
| backplane-2.8 | cluster-proxy-addon | v0.11.0 | v0.15.0 | v0.15.0 |
| backplane-2.8 | clusterlifecycle-state-metrics | - | v0.8.0 | - |
| backplane-2.8 | managed-serviceaccount | v0.11.0 | v0.15.0 | v0.15.0 |
| backplane-2.8 | managedcluster-import-controller | - | v0.14.1-0.20250708065710-54efb2e2ae7b | - |
| backplane-2.8 | multicloud-operators-foundation | v0.12.0 | v0.16.0 | v0.16.0 |
| backplane-2.8 | ocm | v0.11.1-0.20250218075422-4329ebea390c | v0.15.1-0.20250116010516-3a595d6a4e40 | v0.15.1-0.20250226084813-5e5833f198e9 |
| release-2.13 | cluster-permission | - | v0.15.0 | - |
| release-2.13 | klusterlet-addon-controller | - | v0.14.1-0.20240627145512-bd6f2229b53c | - |

> **Tier**: Mostly B (Go 1.22, k8s v0.30). Exception: clusterlifecycle-state-metrics uses api v0.8.0 (Tier A), klusterlet-addon-controller uses pseudo-version ~v0.14 (Tier A).

---

### backplane-2.9 / release-2.14

| Branch | Repo | addon-framework | api | sdk-go |
|--------|------|-----------------|-----|--------|
| backplane-2.9 | cluster-proxy | v0.12.0 | v0.16.0 | v0.16.0 |
| backplane-2.9 | cluster-proxy-addon | v0.11.0 | v0.15.0 | v0.15.0 |
| backplane-2.9 | clusterlifecycle-state-metrics | - | v0.8.0 | - |
| backplane-2.9 | managed-serviceaccount | v0.12.0 | v0.16.1 | v0.16.0 |
| backplane-2.9 | managedcluster-import-controller | - | v1.0.1-0.20250722080758-779879f46835 | - |
| backplane-2.9 | multicloud-operators-foundation | v0.12.0 | v0.16.0 | v0.16.0 |
| backplane-2.9 | ocm | v0.12.1-0.20250407131028-9d436ffc2da7 | v0.16.2-0.20250529024642-922ceaca4e66 | v0.16.1-0.20250428032116-875454003818 |
| release-2.14 | cluster-permission | - | v0.15.0 | - |
| release-2.14 | klusterlet-addon-controller | - | v0.14.1-0.20240627145512-bd6f2229b53c | - |

> **Tier**: Mostly B (Go 1.22, k8s v0.30). managedcluster-import-controller uses api pseudo-version v1.0.1 which sits between Tier B and C.

---

### backplane-2.10 / release-2.15

| Branch | Repo | addon-framework | api | sdk-go |
|--------|------|-----------------|-----|--------|
| backplane-2.10 | cluster-proxy | v0.12.0 | v0.16.0 | v0.16.0 |
| backplane-2.10 | cluster-proxy-addon | v0.11.0 | v0.15.0 | v0.15.0 |
| backplane-2.10 | clusterlifecycle-state-metrics | - | v0.8.0 | - |
| backplane-2.10 | managed-serviceaccount | v1.1.0 | v1.1.0 | v1.1.0 |
| backplane-2.10 | managedcluster-import-controller | - | v1.0.1-0.20250911094832-3b7c6bea0358 | v1.0.1-0.20250911065113-bff262df709b |
| backplane-2.10 | multicloud-operators-foundation | v0.12.0 | v1.0.1-0.20250911094832-3b7c6bea0358 | v0.16.0 |
| backplane-2.10 | ocm | v1.1.0 | v1.1.0 | v1.1.0 |
| release-2.15 | cluster-permission | - | v0.15.0 | - |
| release-2.15 | klusterlet-addon-controller | - | v0.14.1-0.20240627145512-bd6f2229b53c | - |

> **Tier**: Mixed B/C — ocm and managed-serviceaccount already on Tier C (Go 1.24, k8s v0.33), while cluster-proxy, cluster-proxy-addon, multicloud-operators-foundation still on Tier B. klusterlet-addon-controller still on Tier A pseudo-version.

---

### backplane-2.11 / release-2.16

| Branch | Repo | addon-framework | api | sdk-go |
|--------|------|-----------------|-----|--------|
| backplane-2.11 | cluster-proxy | v1.2.0 | v1.2.0 | v1.2.0 |
| backplane-2.11 | clusterlifecycle-state-metrics | - | v1.1.0 | - |
| backplane-2.11 | managed-serviceaccount | v1.2.0 | v1.2.0 | v1.2.0 |
| backplane-2.11 | managedcluster-import-controller | - | v1.2.0 | v1.1.1-0.20260127092137-c07e0fafa331 |
| backplane-2.11 | multicloud-operators-foundation | v1.2.0 | v1.2.0 | v1.2.0 |
| backplane-2.11 | ocm | v1.2.0 | v1.2.0 | v1.2.0 |
| release-2.16 | cluster-permission | - | v0.15.0 | - |
| release-2.16 | klusterlet-addon-controller | - | v0.14.1-0.20240627145512-bd6f2229b53c | - |

> **Tier**: Mostly D (Go 1.25, k8s v0.34). Exceptions: clusterlifecycle-state-metrics uses api v1.1.0 (Tier C), cluster-permission uses api v0.15.0 (Tier B), klusterlet-addon-controller still on Tier A pseudo-version.

---

### main

| Branch | Repo | addon-framework | api | sdk-go |
|--------|------|-----------------|-----|--------|
| main | cluster-permission | - | v0.15.0 | - |
| main | cluster-proxy | v1.1.1 | v1.1.0 | v1.1.0 |
| main | clusterlifecycle-state-metrics | - | v0.8.0 | - |
| main | klusterlet-addon-controller | - | v0.14.1-0.20240627145512-bd6f2229b53c | - |
| main | managed-serviceaccount | v1.1.0 | v1.1.0 | v1.1.0 |
| main | managedcluster-import-controller | - | v1.0.1-0.20250911094832-3b7c6bea0358 | v1.0.1-0.20250911065113-bff262df709b |
| main | multicloud-operators-foundation | v0.12.0 | v1.0.1-0.20250911094832-3b7c6bea0358 | v0.16.0 |
| main | ocm | v1.1.0 | v1.1.0 | v1.1.0 |

> **Tier**: Mixed B/C — most repos on Tier C (Go 1.24, k8s v0.33). cluster-permission (Tier B), clusterlifecycle-state-metrics (Tier A), klusterlet-addon-controller (Tier A pseudo-version) are lagging behind.
