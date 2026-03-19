# Active Releases & Branch Mapping

## MCE (Multicluster Engine) — `backplane-*` branches

MCE components use `backplane-X.Y` branches. `main` fast-forwards to the next unreleased version.

| Branch | Status |
|--------|--------|
| backplane-2.7 | Oldest active |
| backplane-2.8 | Active |
| backplane-2.9 | Active |
| backplane-2.10 | Active |
| backplane-2.11 | Active |
| backplane-2.12 | Active |
| main | Development (fast-forwards to backplane-2.17) |

### Per-repo notes

- **cluster-proxy-addon** — deprecated starting from backplane-2.11, active branches: backplane-2.7 ~ 2.10 only

## ACM (Advanced Cluster Management) — `release-*` branches

ACM components use `release-X.Y` branches. MCE is a subset of ACM.

| Branch | Status |
|--------|--------|
| release-2.12 | Oldest active |
| release-2.13 | Active |
| release-2.14 | Active |
| release-2.15 | Active |
| release-2.16 | Active |
| main | Development (fast-forwards to release-2.17) |

### Per-repo notes

- **multicluster-role-assignment** — newer component, active branches: release-2.15 ~ 2.16 only
