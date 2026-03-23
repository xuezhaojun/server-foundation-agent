---
name: sfa-project-sync
description: "Sync Jira issues to the GitHub Projects V2 board (stolostron/projects/9). Use this skill to import Jira issues as board items, keeping the board in sync with Jira sprint work. Trigger phrases: 'sync jira to board', 'import jira tasks', 'sync sprint to board', 'pull jira issues to project'."
---

# Project Sync

Import Jira issues from the ACM project into the GitHub Projects V2 board. One-directional: Jira -> Board.

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| assignee | No | `currentUser()` | Team member name, email, or `team` for all SF members |
| sprint | No | `current` | Sprint name or `current` for active sprint |
| status | No | not Closed | Jira status filter |
| type | No | all | Jira issue type filter |
| dry-run | No | `false` | Show what would be synced without creating items |

## Workflow

### Step 1: Resolve assignee

If the user specifies a team member:

1. Look up the member in `team-members/team-members.md` using fuzzy name matching (see CLAUDE.md name matching rules)
2. Use their **email** as the Jira assignee identifier
3. If `assignee=team`, build a JQL `assignee in (email1, email2, ...)` clause with all SF team member emails

If no assignee is specified, use `assignee = currentUser()`.

### Step 2: Fetch Jira issues

Use the Jira Cloud REST API v3 search endpoint (POST).

**IMPORTANT**: Jira Cloud has removed `/rest/api/2/search`. You MUST use `/rest/api/3/search/jql` with a POST request body.

Authentication uses Basic Auth with `$JIRA_EMAIL` and `$JIRA_API_TOKEN`.

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "<constructed JQL>",
    "fields": ["issuetype", "key", "summary", "status", "priority", "assignee"],
    "maxResults": 100
  }' \
  "https://redhat.atlassian.net/rest/api/3/search/jql"
```

**JQL construction examples**:

```
# Default (current user, SF component, current sprint, not closed)
project = ACM AND assignee = currentUser() AND component = "Server Foundation" AND sprint in openSprints() AND status not in (Closed)

# Specific member
project = ACM AND assignee = "zxue@redhat.com" AND component = "Server Foundation" AND sprint in openSprints() AND status not in (Closed)

# All SF team members
project = ACM AND assignee in ("leyan@redhat.com", "qhao@redhat.com", ...) AND component = "Server Foundation" AND sprint in openSprints() AND status not in (Closed)

# With named sprint
... AND sprint = "SF Sprint 2026-Q1-S3"
```

Adjust JQL based on parameters (assignee, sprint, status, type).

### Step 3: Fetch existing board items

```bash
gh project item-list 9 --owner stolostron --format json
```

Build a set of existing item titles to check for duplicates. Use Jira key prefix (e.g., `[ACM-12345]`) for dedup matching.

### Step 4: Identify new items to sync

For each Jira issue:
1. Check if an item with the Jira key already exists on the board (title contains the key)
2. If not, mark it as a new item to create

If dry-run is enabled, skip to Step 6 and report what would be added without creating items.

### Step 5: Create board items for new Jira issues

For each new issue:

```bash
gh project item-create 9 --owner stolostron \
  --title "[<JIRA-KEY>] <summary>" \
  --body "Jira: https://redhat.atlassian.net/browse/<JIRA-KEY>\nType: <type>\nAssignee: <assignee>" \
  --format json
```

Then set fields based on Jira data using `gh project item-edit`.

**Map Jira status to board Status:**

| Jira Status | Board Status |
|-------------|-------------|
| New, Backlog | Backlog |
| In Progress | In progress |
| Review | In review |
| Testing, Resolved | In review |
| Done, Closed | Done |

**Map Jira priority to board Priority:**

| Jira Priority | Board Priority |
|---------------|---------------|
| Blocker, Critical | P0 |
| Major | P1 |
| Normal, Minor | P2 |

**Field IDs for `gh project item-edit`:**

- Project ID: `PVT_kwDOA5awWc4BSgim`
- Status field: `PVTSSF_lADOA5awWc4BSgimzhABWLU`
  - Backlog: `f75ad846`
  - Ready: `61e4505c`
  - In progress: `47fc9ee4`
  - In review: `df73e18b`
  - Done: `98236657`
- Priority field: `PVTSSF_lADOA5awWc4BSgimzhABWTk`
  - P0: `79628723`
  - P1: `0a877460`
  - P2: `da944a9c`

```bash
# Set status
gh project item-edit --project-id PVT_kwDOA5awWc4BSgim \
  --id <ITEM_ID> \
  --field-id PVTSSF_lADOA5awWc4BSgimzhABWLU \
  --single-select-option-id <STATUS_OPTION_ID>

# Set priority
gh project item-edit --project-id PVT_kwDOA5awWc4BSgim \
  --id <ITEM_ID> \
  --field-id PVTSSF_lADOA5awWc4BSgimzhABWTk \
  --single-select-option-id <PRIORITY_OPTION_ID>
```

### Step 6: Report results

Show a summary:
- Total Jira issues found
- Already on board (skipped)
- Newly added (or would be added, if dry-run)
- Table of newly added items with columns: Jira Key, Summary, Status, Priority

If dry-run, prefix the summary with "DRY RUN" and note that no items were created.

## Examples

```
# Sync current sprint issues for current user
/sfa-project-sync

# Sync specific member's issues
/sfa-project-sync --assignee zhiwei --sprint current

# Sync all SF team issues
/sfa-project-sync --assignee team

# Dry run to preview what would be synced
/sfa-project-sync --dry-run

# Sync only bugs
/sfa-project-sync --assignee team --type Bug

# Natural language
Sync my jira sprint tasks to the board
Import team's current sprint issues to the project board
Pull zhiwei's jiras to the kanban
```

## Notes

- Sync is one-directional: Jira -> Board (board does not update Jira)
- Dedup by Jira key in title (prefix format: `[ACM-12345]`)
- Authentication: Jira uses `$JIRA_EMAIL` + `$JIRA_API_TOKEN`; GitHub uses `gh` CLI auth
- Requires both Jira and GitHub credentials to be configured
- Project is always `ACM`, component is always `Server Foundation`
- See `docs/github-projects.md` for board field IDs and full reference
- See `docs/jira.md` for Jira API reference
- Dashboard: https://github.com/orgs/stolostron/projects/9
