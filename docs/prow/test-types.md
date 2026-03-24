# Prow Test Types

Common test types used across Server Foundation repositories in OpenShift CI.

## Test Definitions

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
| `fast-forward` | Postsubmit | Auto-merge main to latest release branch |
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
