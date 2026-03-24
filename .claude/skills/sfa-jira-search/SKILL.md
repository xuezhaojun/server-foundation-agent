---
name: sfa-jira-search
description: "Search and list Jira issues for the Server Foundation team from the ACM project on Red Hat Jira Cloud (redhat.atlassian.net). Use this skill when the user wants to search, list, view, or check Jira issues for the team or a specific team member. Trigger phrases: 'list jiras', 'search jira', 'show jiras', 'team jiras', 'jira issues', 'what jiras does X have', 'show SF jira backlog', 'jira sprint status'. Supports filtering by assignee, status, type, sprint, component, and more."
---

# Jira Search

Search and list Jira issues for the SF team from the ACM project.

## Reference Loading

Before executing, load relevant references as needed:
- **For JQL syntax**: Read `docs/jira/jql-reference.md`
- **For API details**: Read `docs/jira/api-reference.md`
- **For custom fields**: Read `docs/jira/custom-fields.md`

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| assignee | No | `currentUser()` | Team member name, email, or `team` for all SF members |
| status | No | not Closed | Comma-separated: `In Progress`, `New`, `Backlog`, `Review`, `Testing`, `Resolved` |
| type | No | all | `Epic`, `Bug`, `Task`, `Story`, `Feature`, etc. |
| priority | No | all | `Blocker`, `Critical`, `Major`, `Normal`, `Minor` |
| component | No | `Server Foundation` | Component filter |
| sprint | No | all | Sprint name or `current` for active sprint |
| label | No | all | Filter by label |
| limit | No | `100` | Maximum results |
| sort | No | type-status | `type-status`, `priority`, `updated`, `created` |

## Workflow

### Step 1: Resolve assignee

1. If specified, look up in `team-members/team-members.md` using fuzzy name matching
2. Use their **email** as Jira identifier
3. If `assignee=team`, build `assignee in (email1, email2, ...)` with all SF emails
4. If unspecified, use `assignee = currentUser()`

### Step 2: Build JQL and fetch

Use `/rest/api/3/search/jql` POST endpoint. See `docs/jira/api-reference.md` for curl template.

Request fields: `["issuetype", "key", "summary", "status", "priority", "assignee", "customfield_10020", "updated", "components"]`

### Step 3: Parse and sort

Parse with Python. Extract sprint from `customfield_10020` (see `docs/jira/custom-fields.md`).

Sort orders:
- Type: Epic(0) → Initiative(1) → Feature(2) → Story(3) → Task(4) → Bug(5) → Vulnerability(6)
- Status: In Progress(0) → New(1) → Backlog(2) → Review(3) → Testing(4) → Resolved(5)

### Step 4: Present results

Display as markdown table: Type | Key | Summary | Status | Priority | Assignee | Sprint

- Bold first row of each Type group
- Omit Assignee column for single-person queries
- Show total count and status distribution after the table
- For team-wide: include per-member count

## Examples

```
/sfa-jira-search --assignee team --sprint current
Show me qiujian's open jiras
List all SF bugs in the current sprint
```
