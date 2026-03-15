# Weekly Bot PR Report Workflow

Analyze all open bot-submitted PRs on the Server Foundation project board, check their CI status,
and generate an actionable report that tells the team which PRs are safe to merge and which need investigation.

## Trigger Phrases

- `weekly bot PR report`, `bot PR report`, `konflux PR report`
- `analyze bot PRs`, `check bot PR CI status`

## Workflow Phases

```
Phase 1: Collect    →  Phase 2: CI Check    →  Phase 3: Diagnose    →  Phase 4: Report    →  Phase 5: Distribute (optional)
fetch-prs skill        gh pr checks            apply triage rules       generate Markdown       slack-notify
```

---

## Phase 1: Collect PR Data

Use the `fetch-prs` skill with `all` detail level to get full PR lifecycle data.

### 1.1 Filter to Open Bot PRs

From the JSON output, keep only PRs where:

- `content.state == "OPEN"`
- Author **IS** a bot

**Bot filter** — include PRs where `content.author.login` matches any of:

| Pattern | Match type |
|---------|------------|
| `red-hat-konflux` | exact |
| `dependabot` | exact |
| `renovate` | exact |
| any login ending with `[bot]` | suffix |
| any login ending with `-bot` | suffix |

**Dependency**: `.claude/skills/fetch-prs/SKILL.md`

---

## Phase 2: Retrieve CI Check Status

For each open bot PR, retrieve CI check results:

```bash
gh pr checks <PR_NUMBER> -R <REPO_OWNER/REPO_NAME>
```

Parse the output into structured data. Each check has:

- **name**: Check name (e.g., `ci/prow/images`, `Red Hat Konflux / ...`)
- **status**: `pass`, `fail`, or `pending`
- **duration**: Run time
- **url**: Link to check details

### 2.1 Classify Check Results Per PR

For each PR, compute:

- **all_passed**: Every check has status `pass` (ignore `tide` which is always `pending` until merge labels are added)
- **has_failures**: At least one check has status `fail`
- **all_pending**: All checks are still `pending`

---

## Phase 3: Diagnose Failures

For PRs where `has_failures == true`, apply the following triage rules **in order** to determine the diagnosis.

### Rule 1: Check `go.mod` Changes (Dependency-Only Upgrade)

Determine if the PR is a pure dependency upgrade by examining what files changed:

```bash
gh pr diff <PR_NUMBER> -R <REPO_OWNER/REPO_NAME> --name-only
```

A PR is a **dependency-only upgrade** if the changed files consist exclusively of:

- `go.mod`
- `go.sum`
- `vendor/` directory files
- RPM lockfiles (e.g., `rpms.lock.yaml`, `rpm_lockfile.yaml`)
- Konflux pipeline/config files (e.g., `.tekton/`, `.konflux/`)

If a PR modifies source code files (`.go` files outside `vendor/`, Makefiles, Dockerfiles, etc.),
it is NOT a pure dependency upgrade and requires closer review.

**Why this matters**: Pure dependency upgrades have predictable failure patterns. Build or test
failures on a dependency-only PR usually indicate an incompatible API change in the upstream
dependency, not a bug in our code.

### Rule 2: Check Image Build Status

For each PR, check if the **image build** CI check passed:

- Look for checks matching: `ci/prow/images` or `*-on-pull-request` (Konflux pipeline build)
- If `ci/prow/images` has status `fail` → the basic build is broken, this is a **core failure**
- If Konflux `*-on-pull-request` checks all fail → Konflux build pipeline is broken

**Why this matters**: If the image build itself fails, the dependency upgrade introduced a
compile-time incompatibility. This is a fundamental problem that blocks everything else
(tests, e2e, integration all depend on a successful build).

### 3.1 Assign Diagnosis

Combine the rules into a diagnosis for each failing PR:

| Diagnosis | Condition |
|-----------|-----------|
| **Build Broken** | Rule 2 fails: `ci/prow/images` is `fail`. This is the most critical — the code does not compile. |
| **Dependency Incompatible** | Rule 1 confirms dependency-only + Rule 2 (images) passes, but tests fail. The dependency upgrade compiles but breaks tests. |
| **Konflux Pipeline Issue** | Prow checks pass but Konflux `*-on-pull-request` checks fail. Likely a Konflux infra issue, not a code issue. |
| **Test Failures Only** | Images build passes, non-dependency files changed, tests fail. Needs manual investigation. |
| **Pending** | Checks are still running — revisit later. |

---

## Phase 4: Generate Report

Produce the report in Markdown using the exact section order and format below.

### Report Template

```
# Server Foundation Weekly Bot PR Report — {YYYY-MM-DD}

## Executive Summary

- **Total open bot PRs:** {N}
- **All checks passed (ready to merge):** {n}
- **Has failures:** {n}
- **Still pending:** {n}
- **Bot author breakdown:** red-hat-konflux ({n}), dependabot ({n}), ...

---

## Ready to Merge

These bot PRs have all CI checks passing. Recommend adding `approved` + `lgtm` labels to merge.

| PR | Repository | Branch | Title | Age (days) | Checks |
|----|------------|--------|-------|------------|--------|
| [#123](url) | repo-name | backplane-2.9 | Update golang.org/x/crypto | 5 | All pass |

> If empty: "No bot PRs are currently ready to merge."

---

## Needs Investigation

Bot PRs with CI failures, grouped by diagnosis.

### Build Broken (Critical)

The image build failed — the dependency upgrade introduced a compile-time incompatibility.

| PR | Repository | Branch | Title | Diagnosis Details | Failed Checks |
|----|------------|--------|-------|-------------------|---------------|
| [#123](url) | repo-name | backplane-2.6 | Update helm.sh/helm/v3 | go.mod only, images fail | ci/prow/images, ci/prow/e2e, ... |

### Dependency Incompatible

The build passes but tests fail. The dependency compiles but has API/behavior changes.

| PR | Repository | Branch | Title | Failed Checks |
|----|------------|--------|-------|---------------|

### Konflux Pipeline Issue

Prow CI passes but Konflux pipeline checks fail. Likely infrastructure, not code.

| PR | Repository | Branch | Title | Prow Status | Konflux Failed |
|----|------------|--------|-------|-------------|----------------|
| [#123](url) | repo-name | backplane-2.6 | Update x/crypto | All pass | on-pull-request, enterprise-contract |

### Test Failures Only

Image build passes but tests fail. Requires manual investigation.

| PR | Repository | Branch | Title | Failed Checks |
|----|------------|--------|-------|---------------|

### Still Pending

Checks are still running. Revisit later.

| PR | Repository | Branch | Title | Pending Checks |
|----|------------|--------|-------|----------------|

> Only show sub-sections that have PRs.

---

## Per-Repository Summary

| Repository | Total | Ready | Build Broken | Dep Incompatible | Konflux Issue | Test Fail | Pending |
|------------|-------|-------|--------------|-------------------|---------------|-----------|---------|
| org/repo | 7 | 0 | 4 | 0 | 2 | 0 | 1 |

> Sort by Total descending.

---

## Per-Branch Summary

| Branch | Total | Ready | Build Broken | Dep Incompatible | Konflux Issue | Test Fail | Pending |
|--------|-------|-------|--------------|-------------------|---------------|-----------|---------|
| backplane-2.6 | 5 | 1 | 2 | 0 | 2 | 0 | 0 |
| backplane-2.9 | 3 | 2 | 1 | 0 | 0 | 0 | 0 |

> Extract branch from PR title (text in parentheses at end, e.g., "(backplane-2.9)") or from the head branch name.
> Sort by branch version descending (newest first).
```

### Formatting Rules

1. **PR links**: Always format as `[#number](url)` — clickable Markdown links
2. **Repository names**: Use short form `org/repo` from `repository.nameWithOwner`
3. **Branch**: Extract from PR title parentheses or head branch name
4. **Dates**: Report date is today's date in `YYYY-MM-DD` format
5. **Age**: Integer days since `createdAt`, computed as `floor((today - createdAt) / 86400)`
6. **Failed Checks**: Comma-separated list of failed check names (short form, e.g., `images`, `e2e`, `unit`)
7. **Empty sections**: Show section header with "If empty" message — never omit sections
8. **Sorting within tables**: Sort by repository, then branch version descending

---

## Phase 5: Distribute (optional)

If the user requests Slack notification, invoke the `slack-notify` skill with the generated Markdown report.

**Dependency**: `.claude/skills/slack-notify/SKILL.md`

---

## Edge Cases

- **PR with no checks reported**: `gh pr checks` returns empty — treat as "Pending" and note it.
- **PR with only `tide` pending**: If the only non-pass check is `tide` (which requires labels), treat as "All pass".
- **Checks still running**: If any check is `pending`, classify PR as "Still Pending" regardless of other pass/fail results.
- **Multiple bot authors**: Group by bot author in the executive summary but analyze all together.
- **Monorepo PRs (e.g., stolostron/ocm)**: A single PR may trigger checks for multiple components (addon-manager, placement, registration, etc.). All component checks must pass for the PR to be "ready".
- **`renovate/artifacts` check**: This is a Renovate-specific artifact update check. If it fails, note it but do not treat it as a build failure — it indicates Renovate could not auto-update lock files.
- **`SonarCloud Code Analysis`**: This is a code quality check. Ignore it for pass/fail classification — it almost always passes for bot PRs.

## Performance Notes

- Phase 2 makes one `gh pr checks` call per PR — for 14 PRs this takes ~10 seconds
- Use `gh pr diff --name-only` (not full diff) to minimize API data transfer
- Cache from `fetch-prs` skill is reused if within TTL — do NOT use `nocache` unless user requests it
- Run `gh pr checks` calls sequentially to avoid GitHub API rate limiting
