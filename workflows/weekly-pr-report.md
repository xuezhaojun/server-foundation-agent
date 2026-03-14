# Weekly PR Report Workflow

Generate a categorized weekly report of all open human PRs on the Server Foundation project board.
The report helps the team identify merge-ready PRs, stale PRs, conflicts, and bottlenecks.

## Trigger Phrases

- `weekly PR report`, `PR health report`, `PR status report`
- `generate PR report`, `how are our PRs doing`

## Workflow Phases

```
Phase 1: Collect    →  Phase 2: Process    →  Phase 3: Report    →  Phase 4: Distribute (optional)
fetch-prs.sh all       filter & classify       generate Markdown       slack-notify
```

---

## Phase 1: Collect PR Data

Run the fetch-prs script with `all` detail level to get full PR lifecycle data:

```bash
cd /Users/zxue/workspaces/server-foundation-agent/.claude/skills/fetch-prs && bash fetch-prs.sh all
```

This returns a JSON array. Parse it with `jq`.

**Dependency**: `.claude/skills/fetch-prs/fetch-prs.sh`

---

## Phase 2: Process & Classify

### 2.1 Filter to Open Human PRs

From the JSON output, keep only PRs where:

- `content.state == "OPEN"`
- Author is NOT a bot

**Bot filter** — exclude PRs where `content.author.login` matches any of:

| Pattern | Match type |
|---------|------------|
| `red-hat-konflux` | exact |
| `dependabot` | exact |
| `renovate` | exact |
| any login ending with `[bot]` | suffix |
| any login ending with `-bot` | suffix |

### 2.2 Classify Each PR

Assign each open human PR to **exactly one** primary category. Evaluate rules **in order** — first match wins.

Extract these fields from each PR:

- **labels**: `[.content.labels.nodes[].name]` — array of label name strings
- **isDraft**: `.content.isDraft` — boolean
- **mergeable**: `.content.mergeable` — enum: `MERGEABLE`, `CONFLICTING`, or `UNKNOWN`
- **reviewDecision**: `.content.reviewDecision` — enum: `APPROVED`, `CHANGES_REQUESTED`, `REVIEW_REQUIRED`, or `null`
- **updatedAt**: `.content.updatedAt` — ISO 8601 timestamp

Helper definitions for rules:

- **has label X**: the labels array contains the string X
- **has `approved`**: `reviewDecision == "APPROVED"` OR labels contain `approved`
- **has `lgtm`**: labels contain `lgtm`
- **has `do-not-merge/*`**: any label starts with `do-not-merge/`

#### Classification Rules (first match wins)

| # | Category | Criteria |
|---|----------|----------|
| 1 | **Ready to Merge** | has `approved` AND has `lgtm` AND NO `do-not-merge/*` labels AND `isDraft == false` AND `mergeable == "MERGEABLE"` |
| 2 | **Work In Progress** | `isDraft == true` OR has label `do-not-merge/work-in-progress` |
| 3 | **On Hold** | has label `do-not-merge/hold` |
| 4 | **Needs Rebase** | has label `needs-rebase` OR `mergeable == "CONFLICTING"` |
| 5 | **Approved, Needs LGTM** | has `approved` AND NOT has `lgtm` AND NO `do-not-merge/*` labels |
| 6 | **Needs Review** | catch-all for everything else |

### 2.3 Compute Staleness

For every PR, compute days since `updatedAt` relative to today's date and assign a staleness bucket:

| Bucket | Days since last update |
|--------|------------------------|
| Fresh | 0–2 |
| Normal | 3–7 |
| Aging | 8–14 |
| Stale | 15–30 |
| Very Stale | 31–90 |
| Abandoned | 91+ |

---

## Phase 3: Generate Report

Produce the report in Markdown using the exact section order and format below.

### Report Template

```
# Server Foundation Weekly PR Report — {YYYY-MM-DD}

## Executive Summary

- **Total open human PRs:** {N}
- **By category:** Ready to Merge ({n}), Needs Review ({n}), Approved/Needs LGTM ({n}), WIP ({n}), On Hold ({n}), Needs Rebase ({n})
- **Staleness:** Fresh ({n}), Normal ({n}), Aging ({n}), Stale ({n}), Very Stale ({n}), Abandoned ({n})
- **Health score:** {percentage}% of PRs are Fresh or Normal

---

## Action Required: Ready to Merge

These PRs are approved, have LGTM, and are mergeable. They should be merged promptly.

| PR | Repository | Author | Title | Age (days) |
|----|------------|--------|-------|------------|
| [#123](url) | repo-name | @author | Title text | 5 |

> If empty: "No PRs are currently ready to merge."

---

## Action Required: Needs Review

These PRs have no approval or LGTM yet and need reviewer attention.

| PR | Repository | Author | Title | Days since update | Staleness |
|----|------------|--------|-------|--------------------|-----------|
| [#123](url) | repo-name | @author | Title text | 12 | Aging |

> Sort by days since update descending (stalest first).
> If empty: "All PRs have been reviewed."

---

## Approved, Needs LGTM

These PRs are approved but still need an LGTM label before they can merge.

| PR | Repository | Author | Title | Days since update |
|----|------------|--------|-------|--------------------|
| [#123](url) | repo-name | @author | Title text | 3 |

> If empty: "No PRs in this state."

---

## Work In Progress

Draft PRs or PRs with `do-not-merge/work-in-progress` label.

| PR | Repository | Author | Title | Days since update | Staleness |
|----|------------|--------|-------|--------------------|-----------|

> If empty: "No WIP PRs."

---

## On Hold

PRs with `do-not-merge/hold` label. These are intentionally paused.

| PR | Repository | Author | Title | Days since update |
|----|------------|--------|-------|--------------------|

> If empty: "No PRs on hold."

---

## Stale PR Alert

PRs that have not been updated in 15+ days, grouped by severity.

### Abandoned (91+ days)

| PR | Repository | Author | Title | Days since update |
|----|------------|--------|-------|--------------------|

### Very Stale (31–90 days)

| PR | Repository | Author | Title | Days since update |
|----|------------|--------|-------|--------------------|

### Stale (15–30 days)

| PR | Repository | Author | Title | Days since update |
|----|------------|--------|-------|--------------------|

> Only show sub-sections that have PRs. If no PRs are 15+ days stale: "No stale PRs — great job!"

---

## Conflict Alert

PRs with `mergeable == "CONFLICTING"` across ALL categories.

| PR | Repository | Author | Title | Category | Days since update |
|----|------------|--------|-------|----------|-------------------|

> If empty: "No PRs have merge conflicts."

---

## Per-Author Summary

| Author | Total | Ready | Needs Review | Approved/LGTM | WIP | On Hold | Rebase | Avg Days |
|--------|-------|-------|--------------|----------------|-----|---------|--------|----------|
| @author | 5 | 1 | 2 | 1 | 1 | 0 | 0 | 12 |

> Sort by Total descending.

---

## Per-Repository Summary

| Repository | Total | Ready | Needs Review | Approved/LGTM | WIP | On Hold | Rebase |
|------------|-------|-------|--------------|----------------|-----|---------|--------|
| org/repo | 8 | 2 | 3 | 1 | 1 | 0 | 1 |

> Sort by Total descending.
```

### Formatting Rules

1. **PR links**: Always format as `[#number](url)` — clickable Markdown links
2. **Author names**: Prefix with `@` (e.g., `@username`)
3. **Repository names**: Use short form `org/repo` from `repository.nameWithOwner`
4. **Dates**: Report date is today's date in `YYYY-MM-DD` format
5. **Days since update**: Integer, computed as `floor((today - updatedAt) / 86400)`
6. **Empty sections**: Always show the section header with the "If empty" message — never omit sections
7. **Sorting within tables**: Sort by days since update descending (stalest first) unless otherwise noted
8. **Health score**: `floor(100 * (fresh_count + normal_count) / total_count)`

---

## Phase 4: Distribute (optional)

If the user requests Slack notification, invoke the `slack-notify` skill with the generated Markdown report.

**Dependency**: `.claude/skills/slack-notify/SKILL.md`

Common trigger: user says "generate weekly PR report and send to Slack".

---

## Edge Cases

- **PR with null author**: Use `"unknown"` as author login. Treat as human (do not filter out).
- **PR with null `mergeable`**: Treat `UNKNOWN` or `null` as non-conflicting, non-mergeable. Such PRs cannot be "Ready to Merge" (rule 1 requires `MERGEABLE`) and will not trigger "Needs Rebase" (rule 4 requires `CONFLICTING`).
- **PR with null `reviewDecision`**: Treat as not approved — the PR has no review yet.
- **PR with null `updatedAt`**: Fall back to `createdAt` for staleness calculation.
- **Labels with 10+ labels**: The API returns at most 10 labels. Classification uses only what is returned.
- **PR matching multiple `do-not-merge/*` labels**: First-match-wins handles this — rule 2 (WIP) takes priority over rule 3 (Hold).

## Performance Notes

- The `fetch-prs.sh all` call may take a few seconds for the initial API call; subsequent calls use the 5-minute cache
- All filtering, classification, and aggregation should be done with `jq` in a single pass when possible
- Do NOT use `nocache` unless the user explicitly requests fresh data
