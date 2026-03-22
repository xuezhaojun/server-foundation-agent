# Build & Release

Server Foundation components ship in two products: **MCE** (Multicluster Engine) and **ACM** (Advanced Cluster Management). MCE is a subset of ACM. This document covers active release branches and MCE/ACM build differences.

## Version Unification (2.17+)

Starting from **2.17**, MCE and ACM version numbers are unified — both use 2.17 instead of separate numbering. However, branch **prefixes** remain distinct: MCE repos still use `backplane-*` and ACM repos still use `release-*`.

## Active Release Branches

### MCE — `backplane-*` branches

MCE components use `backplane-X.Y` branches.

| Branch | Status |
|--------|--------|
| backplane-2.7 | Oldest active |
| backplane-2.8 | Active |
| backplane-2.9 | Active |
| backplane-2.10 | Active |
| backplane-2.11 | Active |
| backplane-2.17 | Latest (fast-forwarded from main) |

#### Per-repo notes

- **cluster-proxy-addon** — deprecated starting from backplane-2.11, active branches: backplane-2.7 ~ 2.10 only

### ACM — `release-*` branches

ACM components use `release-X.Y` branches.

| Branch | Status |
|--------|--------|
| release-2.12 | Oldest active |
| release-2.13 | Active |
| release-2.14 | Active |
| release-2.15 | Active |
| release-2.16 | Active |
| release-2.17 | Latest (fast-forwarded from main) |
| main | Development (fast-forwards to latest release branch) |

#### Per-repo notes

- **multicluster-role-assignment** — newer component, active branches: release-2.15 ~ 2.16 only

## Fast-Forward Mechanism

Changes are committed **only to `main`** for current development. The `main` branch is then **automatically fast-forwarded** to the latest branch of each type. This means you should **never commit directly** to the latest release/backplane branch — it receives updates from `main` automatically.

## Maintenance Branch Ranges

When doing maintenance work (e.g., dependency upgrades) "from branch X to main", you must submit changes to **every active branch in the range**, but **skip the latest branch** because it is fast-forwarded from `main`.

**Current fast-forward targets** (skip these — they sync from `main` automatically):
- MCE repos: `backplane-2.17`
- ACM repos: `release-2.17`

### MCE repos (backplane-* branches only)

"From backplane-2.7 to main" means: `backplane-2.7`, `2.8`, `2.9`, `2.10`, `2.11`, `main`
(skip `backplane-2.17`)

### ACM repos (release-* branches only)

"From release-2.12 to main" means: `release-2.12`, `2.13`, `2.14`, `2.15`, `2.16`, `main`
(skip `release-2.17`)

### Special repos (both backplane-* and release-* branches)

Some repos (e.g., **cluster-permission**, which moved from ACM to MCE) have both branch types. In that case, submit to all applicable branches in both ranges, still skipping the fast-forward target.

## MCE vs ACM Build Differences

The build and CI configurations differ across three key areas.

### 1. Tekton Pipelines (`.tekton/`)

Both MCE and ACM repos use the same shared pipeline from `stolostron/konflux-build-catalog` and build in the same tenant namespace (`crt-redhat-acm-tenant`). The key difference is the **application and component naming**:

| | MCE | ACM |
|---|---|---|
| Application label | `release-mce-217` | `release-acm-217` |
| Component name | `<name>-mce-217` | `<name>-acm-217` |
| Output image | `quay.io/redhat-user-workloads/crt-redhat-acm-tenant/<name>-mce-217:{{revision}}` | `quay.io/redhat-user-workloads/crt-redhat-acm-tenant/<name>-acm-217:{{revision}}` |

Both build for the same architectures: `linux/x86_64`, `linux/arm64`, `linux/ppc64le`, `linux/s390x`.

### 2. Dockerfile.rhtap

Both use the same builder (`brew.registry.redhat.io/rh-osbs/openshift-golang-builder:rhel_9_1.25`) and runtime base (`registry.access.redhat.com/ubi9/ubi-minimal:latest`). The difference is in **image metadata labels**:

| Label | MCE | ACM |
|-------|-----|-----|
| `name` | `multicluster-engine/<component>-rhel9` | `rhacm2/<component>-rhel9` |
| `cpe` | `cpe:/a:redhat:multicluster_engine:2.11::el9` | `cpe:/a:redhat:acm:2.16::el9` |
| Product prefix | `multicluster-engine/` | `rhacm2/` |

Examples:

```dockerfile
# MCE component (managed-serviceaccount)
LABEL name="multicluster-engine/managed-serviceaccount-rhel9"
LABEL cpe="cpe:/a:redhat:multicluster_engine:2.11::el9"

# ACM component (klusterlet-addon-controller)
LABEL name="rhacm2/klusterlet-addon-controller-rhel9"
LABEL cpe="cpe:/a:redhat:acm:2.16::el9"
```

### 3. Publish Jobs (openshift/release CI configs)

In the ci-operator configs, the main structural difference is the **fast-forward destination branch** and **promotion target**:

| | MCE | ACM |
|---|---|---|
| Fast-forward destination | `backplane-2.17` | `release-2.17` |
| Branch pattern | `backplane-*` | `release-*` |
| Promotion namespace | `stolostron` | `stolostron` |

Both use the same CI workflows:
- `ocm-ci-image-mirror` — mirror images to quay.io/stolostron
- `ocm-ci-fastforward` — auto-merge main to latest release branch

Promotion on `main` is typically `disabled: true` for both; images are pushed via `pr-merge-image-mirror` postsubmit jobs instead.

### Build Summary

The MCE/ACM distinction is primarily a **naming and labeling** difference that routes components into the correct product build:

```
MCE path: main → backplane-2.17 → multicluster-engine/* images → MCE product
ACM path: main → release-2.17  → rhacm2/* images              → ACM product
```

The build infrastructure (Tekton pipelines, CI workflows, cluster pools, registries) is shared.
