---
name: jira-update
description: "Update Jira issue status, fields, or perform workflow transitions on Red Hat Jira Cloud (redhat.atlassian.net). Use this skill when the user wants to change a Jira issue's status (e.g., 'move to In Progress', 'mark as Review'), update fields (priority, assignee, summary), or says things like 'update jira', 'transition jira', 'move jira to review', 'change status', 'assign jira to X', 'start working on ACM-12345'."
---

# Jira Update

Update Jira issue status and fields on https://redhat.atlassian.net. Supports workflow transitions (status changes) and field updates.

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| issue-key | Yes | - | Jira issue key (e.g., `ACM-12345`) |
| status | No | - | Target status for workflow transition |
| assignee | No | - | Team member name/email |
| priority | No | - | `Blocker`, `Critical`, `Major`, `Normal`, `Minor` |
| summary | No | - | Update issue title |
| fix-version | No | - | Update fix version |
| add-label | No | - | Add a label |
| remove-label | No | - | Remove a label |

## Workflow Transitions

Jira uses workflow transitions (not direct status changes). To change status, you must find the correct transition ID first.

### Available Statuses and Common Transitions

```
New → In Progress → Review → Testing → Resolved → Closed
         ↑                                    ↓
         └────────────── Reopen ──────────────┘
```

Common transition names on Red Hat Jira:
- `Start Progress` → moves to "In Progress"
- `Request Review` / `Review` → moves to "Review"
- `Testing` → moves to "Testing"
- `Resolve` → moves to "Resolved"
- `Close` → moves to "Closed"
- `Reopen` → moves back to "In Progress"
- `Backlog` → moves to "Backlog"

## Workflow

### Step 1: Validate issue exists

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>?fields=status,summary,assignee,priority" | jq .
```

Confirm the issue exists and show current state to the user.

### Step 2: Perform status transition (if requested)

#### 2a: Get available transitions

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>/transitions" | jq '.transitions[] | {id, name, to: .to.name}'
```

Find the transition whose `to.name` matches the target status (case-insensitive). If no exact match, show available transitions and ask the user.

#### 2b: Execute the transition

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transition": {"id": "<transition-id>"}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>/transitions"
```

### Step 3: Update fields (if requested)

For field updates (assignee, priority, summary, etc.), use a single PUT request:

```bash
curl -s -X PUT \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "assignee": {"name": "<email>"},
      "priority": {"name": "<Priority>"},
      "summary": "<New summary>"
    }
  }' \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>"
```

Only include fields that need updating. If `assignee` is specified as a team member name, resolve to email via `team-members/team-members.md`.

For labels:
```bash
# Add label
curl -s -X PUT \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"update": {"labels": [{"add": "<label>"}]}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>"

# Remove label
curl -s -X PUT \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"update": {"labels": [{"remove": "<label>"}]}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>"
```

### Step 4: Verify and show result

```bash
jira issue view <ISSUE-KEY>
```

Show the updated state and browse URL: `https://redhat.atlassian.net/browse/<ISSUE-KEY>`

## Shortcut Patterns

Users often express transitions naturally:

| User says | Action |
|-----------|--------|
| "start ACM-12345" / "开始 ACM-12345" | Transition to In Progress |
| "ACM-12345 to review" / "提交 review" | Transition to Review |
| "resolve ACM-12345" | Transition to Resolved |
| "close ACM-12345" | Transition to Closed |
| "assign ACM-12345 to zhiwei" | Update assignee |
| "PR is merged, update ACM-12345" | Transition to Resolved + add comment |

When the user says "PR is merged, update jira", also trigger the `jira-comment` skill to add a PR link comment.

## Examples

```
# Transition status
/jira-update --issue-key ACM-12345 --status "In Progress"
/jira-update --issue-key ACM-12345 --status Review

# Update assignee
/jira-update --issue-key ACM-12345 --assignee zhiwei

# Multiple updates
/jira-update --issue-key ACM-12345 --status Review --priority Critical

# Natural language
Move ACM-12345 to review
Start working on ACM-12345
Assign ACM-12345 to qiujian
Mark ACM-12345 as resolved
```

## Notes

- Authentication: Basic Auth with `$JIRA_EMAIL` + `$JIRA_API_TOKEN`
- Transitions require the correct transition ID (not the status name)
- Always fetch available transitions first before attempting a status change
- Some transitions may require additional fields (e.g., resolution for "Resolve")
- Browse URL: `https://redhat.atlassian.net/browse/<ISSUE-KEY>`
