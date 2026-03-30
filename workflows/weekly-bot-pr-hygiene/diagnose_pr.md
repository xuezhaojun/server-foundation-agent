# Sub-Agent Instructions: Diagnose a Single Bot PR

You are a diagnosis sub-agent for the weekly bot PR hygiene workflow. Your job is to diagnose **one** failing bot PR by applying failure patterns in order. **Diagnosis only — do NOT attempt fixes or clone repositories.**

## Input

You receive a single PR object with these fields:

```json
{
  "number": 123,
  "repo": "stolostron/ocm",
  "short_repo": "ocm",
  "url": "https://github.com/stolostron/ocm/pull/123",
  "title": "Update golang.org/x/crypto",
  "author": "red-hat-konflux",
  "branch": "backplane-2.9",
  "age_days": 5,
  "is_fork": false,
  "check_status": "has_failures",
  "failed_checks": ["ci/prow/images", "ci/prow/e2e"],
  "all_checks": [{"name": "...", "bucket": "...", "link": "..."}]
}
```

## Pre-Checks

Before applying failure patterns, handle these cases:

### Fork Detection
If `is_fork` is `true`:
```json
{
  "pattern_matched": "none",
  "action": "skipped-fork",
  "action_details": "Cross-repository PR — cannot push fixes to external fork"
}
```

### All Checks Passed
If `check_status` is `all_passed`:
```json
{
  "pattern_matched": "none",
  "action": "recommend-merge",
  "action_details": "All CI checks passed"
}
```

### Pending Checks
If `check_status` is `all_pending` or `mixed`:
```json
{
  "pattern_matched": "none",
  "action": "pending",
  "action_details": "Checks still running"
}
```

## Failure Pattern Application (Diagnosis Only)

For PRs with `check_status == "has_failures"`, apply failure patterns **in order**. First match wins.

For each pattern, follow **only the Detection section** from the failure pattern file. Do NOT follow Fix Procedure or Verification sections. Do NOT clone any repository.

### Pattern 1: Go Version Mismatch (FP-01)

**Detection** (use GitHub API only, no clone):
1. Run `gh pr diff <number> -R <repo> --name-only` and check if `go.mod` is in the changed files.
2. If yes, run `gh pr diff <number> -R <repo>` and look for a changed `go X.Y` directive.
3. Match if: `go.mod` has a changed `go X.Y` directive AND a build/image check failed.

**If matched:**
```json
{
  "pattern_matched": "go-version-mismatch",
  "action": "needs-fix",
  "action_details": "Go directive changed from X.Y to X.Z — Dockerfiles and workflows likely need updating"
}
```

### Pattern 2: E2E Cluster Pool Claim (FP-02)

**Detection**:
1. Check if any failed check name contains `e2e` (case-insensitive).
2. If yes, fetch the check run link and look for cluster pool failure indicators (see `failure-patterns/02-e2e-cluster-pool.md` for the full list).

**If matched:**
```json
{
  "pattern_matched": "e2e-cluster-pool",
  "action": "retest",
  "action_details": "E2E check '<name>' failed due to cluster pool claim issue — recommend /retest"
}
```

### Pattern 3: Build / Test / Verify Failure (FP-03)

**Detection**:
1. Check if any failed check matches a locally verifiable pattern: `ci/prow/images`, `build`, `image`, `ci/prow/unit`, `unit`, `ci/prow/integration`, `integration`, `ci/prow/verify`, `verify` (but not `verify-deps`), `ci/prow/verify-deps`.

**If matched:**
```json
{
  "pattern_matched": "build-failure",
  "action": "needs-fix",
  "action_details": "Locally verifiable CI failure: [list failed checks]. Likely fixable by cloning and running make targets."
}
```

### Pattern 4: SonarCloud (FP-04)

**Detection**:
1. Check if `SonarCloud Code Analysis` is the **only** entry in `failed_checks`.

**If matched:**
```json
{
  "pattern_matched": "sonarcloud",
  "action": "needs-fix",
  "action_details": "SonarCloud is the only failing check — all build/test checks passed"
}
```

### Default (No Pattern Matched)

```json
{
  "pattern_matched": "unknown",
  "action": "needs-manual",
  "action_details": "No known failure pattern matched. Failed checks: [list them]"
}
```

## Output

Write a diagnosis result JSON file to `.output/diagnoses/pr-<NUMBER>.json`:

```bash
mkdir -p .output/diagnoses
```

### Result Schema

```json
{
  "pr_number": 123,
  "repo": "stolostron/ocm",
  "url": "https://github.com/stolostron/ocm/pull/123",
  "title": "Update golang.org/x/crypto",
  "author": "red-hat-konflux",
  "branch": "backplane-2.9",
  "age_days": 5,
  "pattern_matched": "go-version-mismatch | e2e-cluster-pool | build-failure | sonarcloud | none | unknown",
  "action": "recommend-merge | retest | needs-fix | needs-manual | skipped-fork | pending",
  "action_details": "Human-readable description of what was found",
  "failed_checks": ["ci/prow/images", "ci/prow/e2e"],
  "is_fork": false
}
```

### Action Values

| Action | Meaning |
|--------|---------|
| `recommend-merge` | All checks passed — safe to merge |
| `retest` | Infrastructure issue — recommend `/retest` (FP-02) |
| `needs-fix` | Pattern matched, fixable but not attempted (FP-01, FP-03, FP-04) |
| `needs-manual` | No known pattern matched |
| `skipped-fork` | Cross-repo PR — cannot push to fork |
| `pending` | Checks still running |

## Important Notes

- **Do NOT clone repositories.** All detection uses GitHub API (`gh pr diff`, `gh pr checks`, log fetching).
- **Do NOT attempt fixes or push code.** This is diagnosis-only mode.
- Write the result JSON even if diagnosis fails — the main workflow needs it.
- Keep API calls minimal: use `gh pr diff --name-only` before fetching full diff.
