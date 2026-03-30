# Server Foundation Related Repositories

All Server Foundation related repositories are cloned as **read-only** shallow copies under `repos/`, organized by category. The repo registry is defined in [repos.yaml](../repos/repos.yaml).

For active branch and version mapping information, see [releases.md](releases.md).

For inter-repository dependency analysis and diagrams, see [repo-dependencies.md](repo-dependencies.md).

## Build Context

Server Foundation components ship in two products:

- **MCE** (Multicluster Engine) — repos use `backplane-*` branches
- **ACM** (Advanced Cluster Management) — repos use `release-*` branches. MCE is a subset of ACM.

## Repo Sync

Use the helper script to manage local clones:

```bash
# Clone all repos (shallow, depth 1)
./repos/sync-repos.sh

# Update all repos to latest remote commits
./repos/sync-repos.sh --update

# Show status of all repos
./repos/sync-repos.sh --status
```

The script reads [repos.yaml](../repos/repos.yaml) and clones repos into the matching directory structure under `repos/`. Adding a new repo is as simple as adding an entry to `repos.yaml` and re-running the sync.

## stolostron (`repos/server-foundation/stolostron/`)

### MCE Components (`backplane-*` branches)

| Repository | Description |
|------------|-------------|
| [ocm](https://github.com/stolostron/ocm) | OCM downstream |
| [managedcluster-import-controller](https://github.com/stolostron/managedcluster-import-controller) | Manages cluster imports |
| [multicloud-operators-foundation](https://github.com/stolostron/multicloud-operators-foundation) | Foundation operators |
| [cluster-proxy](https://github.com/stolostron/cluster-proxy) | Konnectivity-based cluster proxy |
| [clusterlifecycle-state-metrics](https://github.com/stolostron/clusterlifecycle-state-metrics) | Cluster lifecycle metrics |
| [managed-serviceaccount](https://github.com/stolostron/managed-serviceaccount) | Managed ServiceAccount |
| [cluster-proxy-addon](https://github.com/stolostron/cluster-proxy-addon) | Cluster proxy addon (deprecated from backplane-2.11) |

### ACM Components (`release-*` branches)

| Repository | Description |
|------------|-------------|
| [klusterlet-addon-controller](https://github.com/stolostron/klusterlet-addon-controller) | Klusterlet addon controller |
| [cluster-permission](https://github.com/stolostron/cluster-permission) | Cluster permission management (migrated to MCE in 2.17) |
| [multicluster-role-assignment](https://github.com/stolostron/multicluster-role-assignment) | Multicluster RBAC |

### Dependency Libraries (`repos/deps/`, forked with SF-specific changes)

| Repository | Description |
|------------|-------------|
| [apiserver-network-proxy](https://github.com/stolostron/apiserver-network-proxy) | ANP fork, key dependency of cluster-proxy |
| [grpc-go](https://github.com/stolostron/grpc-go) | gRPC-Go fork, key dependency of cluster-proxy |

### Dependency Components (`repos/installer/`, not owned by SF, but tightly coupled)

| Repository | Description |
|------------|-------------|
| [backplane-operator](https://github.com/stolostron/backplane-operator) | Installs all MCE/Foundation components into ACM |
| [multiclusterhub-operator](https://github.com/stolostron/multiclusterhub-operator) | Installs ACM components on top of MCE |

## open-cluster-management-io (`repos/server-foundation/ocm-io/`, upstream)

| Repository | Description |
|------------|-------------|
| [ocm](https://github.com/open-cluster-management-io/ocm) | OCM core (upstream) |
| [api](https://github.com/open-cluster-management-io/api) | OCM API definitions |
| [sdk-go](https://github.com/open-cluster-management-io/sdk-go) | OCM Go SDK |
| [addon-framework](https://github.com/open-cluster-management-io/addon-framework) | Addon development framework |
| [cluster-proxy](https://github.com/open-cluster-management-io/cluster-proxy) | Cluster proxy (upstream) |
| [managed-serviceaccount](https://github.com/open-cluster-management-io/managed-serviceaccount) | Managed ServiceAccount (upstream) |
| [cluster-permission](https://github.com/open-cluster-management-io/cluster-permission) | Cluster permission (upstream) |
| [clusteradm](https://github.com/open-cluster-management-io/clusteradm) | OCM CLI tool for cluster management |

## Build / CI (`repos/build/`)

| Repository | Description |
|------------|-------------|
| [openshift/release](https://github.com/openshift/release) | OpenShift CI release configuration (prow jobs, configs) |
| [stolostron/konflux-build-catalog](https://github.com/stolostron/konflux-build-catalog) | Konflux build catalog for stolostron |
| [stolostron/acm-infra](https://github.com/stolostron/acm-infra) | ACM infrastructure and build tooling |

## QE Tests (`repos/qe/`)

| Repository | Description |
|------------|-------------|
| [acmqe-foundation-test](https://github.com/stolostron/acmqe-foundation-test) | QE automated regression tests for all SF components. When Jira issues or Slack mention "automated tests", "auto regression", or QE-reported test failures, check this repo for relevant test code. |

## Documentation (`repos/docs/`)

| Repository | Description |
|------------|-------------|
| [open-cluster-management-io.github.io](https://github.com/open-cluster-management-io/open-cluster-management-io.github.io) | OCM community documentation site |
| [rhacm-docs](https://github.com/stolostron/rhacm-docs) | Red Hat Advanced Cluster Management product documentation |
