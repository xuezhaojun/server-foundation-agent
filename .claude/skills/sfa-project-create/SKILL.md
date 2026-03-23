---
name: sfa-project-create
description: "Create tasks on the GitHub Projects V2 board (stolostron/projects/9). Use this skill when the user wants to create a project task, add a work item to the board, track something on the kanban, or says things like 'create a task', 'add to board', 'track this on the project', 'new board item'. Also trigger when the agent needs to track its own work."
---

# Project Create

Create tasks (draft issues) or add existing GitHub Issues/PRs to the project board at https://github.com/orgs/stolostron/projects/9.

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| title | Yes (for draft) | - | Task title |
| body | No | - | Task description/context |
| url | Yes (for existing) | - | GitHub Issue or PR URL to add |
| status | No | Backlog | Backlog, Ready, In progress, In review, Done |
| priority | No | - | P0, P1, P2 |
| size | No | - | XS, S, M, L, XL |
| start-date | No | - | YYYY-MM-DD format |
| target-date | No | - | YYYY-MM-DD format |
| supervisor | No | - | GitHub username of the human supervisor (sets Assignees field) |

Either `title` (for draft issue) or `url` (for existing issue/PR) is required.

**Convention:** The Assignees field represents the **human supervisor** who oversees and approves the agent's work. When creating a task, resolve the supervisor name to a GitHub username via `team-members/team-members.md`.

## Workflow

### Step 1: Create or add the item

**For draft issues (new tasks):**
```bash
gh project item-create 9 --owner stolostron --title "<title>" --body "<body>" --format json
```

**For existing Issues/PRs:**
```bash
gh project item-add 9 --owner stolostron --url "<issue-or-pr-url>" --format json
```

Extract the item `id` from the JSON response.

### Step 2: Set field values

Reference: `docs/github-projects.md` for all field IDs and option IDs.

Project ID: `PVT_kwDOA5awWc4BSgim`

For each field that needs setting, run a separate `gh project item-edit` command:

**Status** (single-select):
```bash
gh project item-edit --id <item-id> --field-id PVTSSF_lADOA5awWc4BSgimzhABWLU --project-id PVT_kwDOA5awWc4BSgim --single-select-option-id <status-option-id>
```

Status option IDs: Backlog=f75ad846, Ready=61e4505c, In progress=47fc9ee4, In review=df73e18b, Done=98236657

**Priority** (single-select):
```bash
gh project item-edit --id <item-id> --field-id PVTSSF_lADOA5awWc4BSgimzhABWTk --project-id PVT_kwDOA5awWc4BSgim --single-select-option-id <priority-option-id>
```

Priority option IDs: P0=79628723, P1=0a877460, P2=da944a9c

**Size** (single-select):
```bash
gh project item-edit --id <item-id> --field-id PVTSSF_lADOA5awWc4BSgimzhABWTo --project-id PVT_kwDOA5awWc4BSgim --single-select-option-id <size-option-id>
```

Size option IDs: XS=6c6483d2, S=f784b110, M=7515a9f1, L=817d0097, XL=db339eb2

**Start date** (date):
```bash
gh project item-edit --id <item-id> --field-id PVTF_lADOA5awWc4BSgimzhABWTw --project-id PVT_kwDOA5awWc4BSgim --date "YYYY-MM-DD"
```

**Target date** (date):
```bash
gh project item-edit --id <item-id> --field-id PVTF_lADOA5awWc4BSgimzhABWT0 --project-id PVT_kwDOA5awWc4BSgim --date "YYYY-MM-DD"
```

### Step 3: Show the result

Display created item with all set fields. Provide the board URL: https://github.com/orgs/stolostron/projects/9

## Examples

```
# Create a draft task
/sfa-project-create --title "Review PR #456 cluster-proxy" --status Ready --priority P1 --size S

# Add existing PR to board
/sfa-project-create --url https://github.com/stolostron/cluster-proxy/pull/456 --status "In progress"

# Natural language
Track the cluster-proxy cert rotation work on the board as P0
Add PR #123 to the project board
Create a task to upgrade Go dependencies, size M, target 2026-04-01
```

## Notes

- Project number: 9, Owner: stolostron
- Project ID: PVT_kwDOA5awWc4BSgim
- Each field update requires a separate `gh project item-edit` call
- Draft issues are lightweight -- no repo association needed
- See `docs/github-projects.md` for complete field ID reference
- Dashboard: https://github.com/orgs/stolostron/projects/9
