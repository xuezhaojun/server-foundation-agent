# MCE vs ACM Component Build Differences

Server Foundation components ship in two products: **MCE** (Multicluster Engine) and **ACM** (Advanced Cluster Management). MCE is a subset of ACM. The build and CI configurations differ across three key areas.

## 1. Tekton Pipelines (`.tekton/`)

Both MCE and ACM repos use the same shared pipeline from `stolostron/konflux-build-catalog` and build in the same tenant namespace (`crt-redhat-acm-tenant`). The key difference is the **application and component naming**:

| | MCE | ACM |
|---|---|---|
| Application label | `release-mce-217` | `release-acm-217` |
| Component name | `<name>-mce-217` | `<name>-acm-217` |
| Output image | `quay.io/redhat-user-workloads/crt-redhat-acm-tenant/<name>-mce-217:{{revision}}` | `quay.io/redhat-user-workloads/crt-redhat-acm-tenant/<name>-acm-217:{{revision}}` |

Both build for the same architectures: `linux/x86_64`, `linux/arm64`, `linux/ppc64le`, `linux/s390x`.

## 2. Dockerfile.rhtap

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

## 3. Publish Jobs (openshift/release CI configs)

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

## Summary

The MCE/ACM distinction is primarily a **naming and labeling** difference that routes components into the correct product build:

```
MCE path: main → backplane-2.17 → multicluster-engine/* images → MCE product
ACM path: main → release-2.17  → rhacm2/* images              → ACM product
```

The build infrastructure (Tekton pipelines, CI workflows, cluster pools, registries) is shared.
