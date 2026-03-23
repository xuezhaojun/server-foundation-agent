---
name: sfa-project-update
description: "Update task status, priority, size, dates, or other fields on the GitHub Projects V2 board (stolostron/projects/9). Use this skill when the user wants to update a task, move a task to a different status, change priority, mark something as done, or says things like 'update task', 'move to in progress', 'mark done', 'change priority', 'set target date'."
---

# Project Update

Update fields on items in the project board at https://github.com/orgs/stolostron/projects/9.

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| item | Yes | - | Item title (fuzzy match) or item ID |
| status | No | - | Backlog, Ready, In progress, In review, Done |
| priority | No | - | P0, P1, P2 |
| size | No | - | XS, S, M, L, XL |
| start-date | No | - | YYYY-MM-DD |
| target-date | No | - | YYYY-MM-DD |
| title | No | - | New title for draft issue |
| body | No | - | New body for draft issue |
| archive | No | false | Archive the item |

## Workflow

### Step 1: Find the item

List all items and find by title match or ID:

```bash
gh project item-list 9 --owner stolostron --format json
```

Parse JSON to find matching item. Use case-insensitive substring match on title. If multiple matches, show them and ask the user to clarify. If using item ID directly, skip the search.

### Step 2: Update fields

Project ID: `PVT_kwDOA5awWc4BSgim`

For each requested field change, run a separate command:

**Status:**
```bash
gh project item-edit --id <item-id> --field-id PVTSSF_lADOA5awWc4BSgimzhABWLU --project-id PVT_kwDOA5awWc4BSgim --single-select-option-id <option-id>
```
Options: Backlog=f75ad846, Ready=61e4505c, In progress=47fc9ee4, In review=df73e18b, Done=98236657

**Priority:**
```bash
gh project item-edit --id <item-id> --field-id PVTSSF_lADOA5awWc4BSgimzhABWTk --project-id PVT_kwDOA5awWc4BSgim --single-select-option-id <option-id>
```
Options: P0=79628723, P1=0a877460, P2=da944a9c

**Size:**
```bash
gh project item-edit --id <item-id> --field-id PVTSSF_lADOA5awWc4BSgimzhABWTo --project-id PVT_kwDOA5awWc4BSgim --single-select-option-id <option-id>
```
Options: XS=6c6483d2, S=f784b110, M=7515a9f1, L=817d0097, XL=db339eb2

**Start date:**
```bash
gh project item-edit --id <item-id> --field-id PVTF_lADOA5awWc4BSgimzhABWTw --project-id PVT_kwDOA5awWc4BSgim --date "YYYY-MM-DD"
```

**Target date:**
```bash
gh project item-edit --id <item-id> --field-id PVTF_lADOA5awWc4BSgimzhABWT0 --project-id PVT_kwDOA5awWc4BSgim --date "YYYY-MM-DD"
```

**Title/Body (draft issues only):**
```bash
gh project item-edit --id <item-id> --title "New title" --body "New body"
```

**Archive:**
```bash
gh project item-archive 9 --owner stolostron --id <item-id>
```

### Step 3: Verify and show result

List the item again to confirm updates. Show updated fields.

## Shortcut Patterns

Users often express updates naturally:

| User says | Action |
|-----------|--------|
| "start task X" | Status -> In progress, Start date -> today |
| "task X done" / "mark X done" | Status -> Done |
| "task X to review" | Status -> In review |
| "bump priority of X to P0" | Priority -> P0 |
| "archive done tasks" | Archive all items with Status=Done |

## Examples

```
# Update status
/sfa-project-update --item "Review PR #456" --status "In progress"

# Multiple field update
/sfa-project-update --item "cluster-proxy upgrade" --status Done --priority P0

# Set dates
/sfa-project-update --item "Go dep upgrade" --start-date 2026-03-23 --target-date 2026-04-01

# Archive
/sfa-project-update --item "Review PR #456" --archive

# Natural language
Move "cluster-proxy cert rotation" to done
Start working on the Go upgrade task
Archive all completed tasks
```

## Notes

- Project number: 9, Owner: stolostron
- Project ID: PVT_kwDOA5awWc4BSgim
- Each field update is a separate API call
- Title/body edits only work on draft issues, not linked Issues/PRs
- See `docs/github-projects.md` for complete field ID reference
- Dashboard: https://github.com/orgs/stolostron/projects/9
