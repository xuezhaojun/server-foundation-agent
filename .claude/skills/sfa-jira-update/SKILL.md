---
name: sfa-jira-update
description: "Update Jira issue status, fields, or perform workflow transitions on Red Hat Jira Cloud (redhat.atlassian.net). Use this skill when the user wants to change a Jira issue's status (e.g., 'move to In Progress', 'mark as Review'), update fields (priority, assignee, summary), or says things like 'update jira', 'transition jira', 'move jira to review', 'change status', 'assign jira to X', 'start working on ACM-12345'."
---

# Jira Update

Update Jira issue status and fields. Supports workflow transitions and field updates.

## Reference Loading

Before executing, load relevant references as needed:
- **For workflow transitions**: Read `docs/jira/workflows.md`
- **For API details**: Read `docs/jira/api-reference.md`

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

## Workflow

### Step 1: Validate issue exists

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>?fields=status,summary,assignee,priority" | jq .
```

### Step 2: Status transition (if requested)

See `docs/jira/workflows.md` for transition details. Get available transitions, find matching `to.name`, then execute.

### Step 3: Update fields (if requested)

Single PUT request. Only include fields that need updating. Resolve assignee via `team-members/team-members.md`.

For label operations, use `{"update": {"labels": [{"add": "<label>"}]}}` syntax. See `docs/jira/api-reference.md`.

### Step 4: Verify and show result

```bash
jira issue view <KEY>
```

Show browse URL: `https://redhat.atlassian.net/browse/<KEY>`

## Shortcut Patterns

| User says | Action |
|-----------|--------|
| "start ACM-12345" | Transition to In Progress |
| "ACM-12345 to review" | Transition to Review |
| "resolve ACM-12345" | Transition to Resolved |
| "close ACM-12345" | Transition to Closed |
| "assign ACM-12345 to zhiwei" | Update assignee |
| "PR is merged, update ACM-12345" | Transition to Resolved + trigger `sfa-jira-comment` |

## Examples

```
/sfa-jira-update --issue-key ACM-12345 --status "In Progress"
Move ACM-12345 to review
Assign ACM-12345 to qiujian
```
