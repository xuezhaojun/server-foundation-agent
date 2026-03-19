# Prow & CI Configuration for Server Foundation Repos

Server Foundation repos use OpenShift CI (Prow) for CI/CD. All configuration lives in the [openshift/release](https://github.com/openshift/release) repo, which is available locally at `repos/openshift/release/`.

## Two Key Directories

### 1. `ci-operator/config/stolostron/<repo>/` — CI Pipeline Definitions

Defines **what to build and how to test**. Each repo has one YAML file per branch:

```
stolostron-<repo>-main.yaml
stolostron-<repo>-backplane-2.11.yaml
stolostron-<repo>-release-2.16.yaml
```

Key sections in each config file:

| Section | Purpose |
|---------|---------|
| `base_images` | Container base images (e.g. `ubi-minimal:9`) |
| `build_root` | Go builder image and version (e.g. `go1.25-linux`) |
| `images` | Container images CI will build from the repo |
| `promotion` | Where successful builds are pushed (image registry namespace + version tag) |
| `releases` | Which OpenShift version to test against (e.g. OCP 4.22) |
| `tests` | Test definitions — unit, integration, e2e, sonar, image mirroring, fast-forward |

### 2. `core-services/prow/02_config/stolostron/<repo>/` — Prow Behavior & Merge Policy

Defines **PR automation rules** — when to trigger CI, how to merge, which plugins are active.

**Org-level configs** (apply to all stolostron repos):

| File | Purpose |
|------|---------|
| `_prowconfig.yaml` | Tide merge policy: squash merge, requires `approved` + `lgtm`, blocks on `hold`/`wip`/`needs-rebase` |
| `_pluginconfig.yaml` | Enabled plugins: approve, assign, hold, label, lgtm, trigger, verify-owners, wip, etc. LGTM acts as approval. |

**Repo-level configs** (overrides per repo):

| File | Purpose |
|------|---------|
| `_prowconfig.yaml` | Merge method override (most repos inherit squash from org) |
| `_pluginconfig.yaml` | Repo-specific plugins (e.g. `dco` for sign-off), trusted apps (Konflux, Dependabot) |

## How They Work Together

```
Developer opens PR
       │
       ▼
Prow plugins process PR (labels, DCO check, assign reviewers)
       │
       ▼
Prow triggers CI jobs defined in ci-operator configs
       │
       ▼
CI Operator builds images and runs tests (unit, e2e, sonar)
       │
       ▼
Tests pass + PR gets approved + lgtm → Tide merges (squash)
       │
       ▼
Postsubmit jobs run (image mirror, fast-forward, publish)
```

## CI Config Coverage per SF Repo

| Repository | CI Config Files | Prow Config | Branch Pattern |
|------------|:-:|:-:|----------------|
| ocm | 10 | Yes | `backplane-*` |
| managedcluster-import-controller | 9 | Yes | `backplane-*` |
| multicloud-operators-foundation | 9 | No (org defaults) | `backplane-*` |
| cluster-proxy | 13 | Yes | `backplane-*` |
| clusterlifecycle-state-metrics | 12 | Yes | `backplane-*` |
| managed-serviceaccount | 14 | Yes | `backplane-*` |
| cluster-proxy-addon | 10 | Yes | `backplane-*` |
| klusterlet-addon-controller | 9 | Yes | `release-*` |
| cluster-permission | 10 | Yes | `release-*` |
| multicluster-role-assignment | 4 | Yes | `release-*` |
| backplane-operator | 8 | Yes | `backplane-*` |

## Common Test Types

| Test | Type | Description |
|------|------|-------------|
| `verify` | Container | Code linting and formatting |
| `verify-deps` | Container | Dependency validation |
| `unit` | Container | Unit tests (`make test`) |
| `integration` | Container | Integration tests |
| `e2e` | Multi-stage | End-to-end tests using SF cluster pools |
| `sonar-pre-submit` | Multi-stage | SonarCloud analysis on PR |
| `sonar-post-submit` | Multi-stage | SonarCloud analysis after merge |
| `pr-image-mirror` | Multi-stage | Mirror PR images to quay.io |
| `pr-merge-image-mirror` | Postsubmit | Mirror merged images to quay.io |
| `fast-forward` | Postsubmit | Auto-merge main → latest release branch |
| `publish` | Postsubmit | Publish to OSCI pipeline |

## Cluster Pool Configuration

All SF e2e tests use the shared Server Foundation cluster pool:

```yaml
CLUSTERPOOL_GROUP_NAME: Server Foundation
CLUSTERPOOL_HOST_NAMESPACE: server-foundation
CLUSTERPOOL_HOST_PROW_KUBE_SECRET: ocm-sf-clusterpool
CLUSTERPOOL_LIFETIME: 2h
CLUSTERPOOL_LIST_INCLUSION_FILTER: prow
```

## Key Patterns

- **Fast-forward**: Most repos auto-merge `main` to their latest release branch (e.g. `backplane-2.17` or `release-2.17`) via postsubmit jobs
- **Skip conditions**: Tests skip on doc-only changes (`*.md`, `docs/`, `OWNERS`, `LICENSE`, `.tekton/`)
- **Multi-arch**: Some repos (e.g. multicloud-operators-foundation) build ARM64 images in addition to AMD64
- **Image promotion**: Main branch promotion is typically `disabled: true`; images are pushed via `pr-merge-image-mirror` workflow instead. Release branches actively promote to the `stolostron` namespace

## File Path Reference

```
repos/openshift/release/
├── ci-operator/config/stolostron/<repo>/
│   └── stolostron-<repo>-<branch>.yaml        # CI pipeline per branch
└── core-services/prow/02_config/stolostron/
    ├── _prowconfig.yaml                        # Org-level merge policy
    ├── _pluginconfig.yaml                      # Org-level plugins
    └── <repo>/
        ├── _prowconfig.yaml                    # Repo-level merge override
        └── _pluginconfig.yaml                  # Repo-level plugins
```
