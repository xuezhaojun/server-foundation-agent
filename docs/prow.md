# Prow & CI Configuration for Server Foundation Repos

Server Foundation repos use OpenShift CI (Prow) for CI/CD. All configuration lives in the [openshift/release](https://github.com/openshift/release) repo, which is available locally at `repos/openshift/release/`.

## Reference Materials

Load these on-demand based on the task:

| Reference | Path | When to Load |
|-----------|------|-------------|
| [Test Types & Cluster Pools](prow/test-types.md) | `docs/prow/test-types.md` | Looking up test types, cluster pool config, CI patterns |
| [CI Coverage per Repo](prow/ci-coverage.md) | `docs/prow/ci-coverage.md` | Checking which repos have CI configs and branch patterns |

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
