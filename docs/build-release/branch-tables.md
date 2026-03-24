# Active Release Branches

## MCE — `backplane-*` branches

MCE components use `backplane-X.Y` branches.

| Branch | Status |
|--------|--------|
| backplane-2.7 | Oldest active |
| backplane-2.8 | Active |
| backplane-2.9 | Active |
| backplane-2.10 | Active |
| backplane-2.11 | Active |
| backplane-2.17 | Latest (fast-forwarded from main) |

### Per-repo notes

- **cluster-proxy-addon** — deprecated starting from backplane-2.11, active branches: backplane-2.7 ~ 2.10 only

## ACM — `release-*` branches

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

### Per-repo notes

- **multicluster-role-assignment** — newer component, active branches: release-2.15 ~ 2.16 only

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
