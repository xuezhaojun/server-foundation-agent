---
name: sfa-jira-search
description: "Search and list Jira issues for the Server Foundation team from the ACM project on Red Hat Jira Cloud (redhat.atlassian.net). Use this skill when the user wants to search, list, view, or check Jira issues for the team or a specific team member. Trigger phrases: 'list jiras', 'search jira', 'show jiras', 'team jiras', 'jira issues', 'what jiras does X have', 'show SF jira backlog', 'jira sprint status'. Supports filtering by assignee, status, type, sprint, component, and more."
---

# Jira Search

Search and list Jira issues for the Server Foundation team from the ACM project on https://redhat.atlassian.net.

## Team-Oriented Design

Unlike personal Jira queries, this skill supports querying issues for:
- **Any team member** by name, email, or GitHub username (resolved via `team-members/team-members.md`)
- **The entire SF team** (all members)
- **Current user** (default when no assignee is specified)

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| assignee | No | `currentUser()` | Team member name, email, or `team` for all SF members |
| status | No | not Closed | Single or comma-separated: `In Progress`, `New`, `Backlog`, `Review`, `Testing`, `Resolved` |
| type | No | all | `Epic`, `Bug`, `Task`, `Story`, `Feature`, `Initiative`, `Spike`, `Vulnerability` |
| priority | No | all | `Blocker`, `Critical`, `Major`, `Normal`, `Minor` |
| component | No | `Server Foundation` | Component filter (defaults to SF) |
| sprint | No | all | Sprint name or `current` for active sprint |
| label | No | all | Filter by label |
| limit | No | `100` | Maximum results |
| sort | No | type-status | `type-status`, `priority`, `updated`, `created` |

## Workflow

### Step 1: Resolve assignee

If the user specifies a team member:

1. Look up the member in `team-members/team-members.md` using fuzzy name matching (see CLAUDE.md name matching rules)
2. Use their **email** as the Jira assignee identifier
3. If `assignee=team`, build a JQL `assignee in (email1, email2, ...)` clause with all SF team member emails

If no assignee is specified, use `assignee = currentUser()`.

### Step 2: Build JQL and fetch issues

Use the Jira Cloud REST API v3 search endpoint (POST).

**IMPORTANT**: Jira Cloud has removed `/rest/api/2/search`. You MUST use `/rest/api/3/search/jql` with a POST request body.

Authentication uses Basic Auth with `$JIRA_EMAIL` and `$JIRA_API_TOKEN`.

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "<constructed JQL>",
    "fields": ["issuetype", "key", "summary", "status", "priority", "assignee", "customfield_10020", "updated", "components"],
    "maxResults": <limit>
  }' \
  "https://redhat.atlassian.net/rest/api/3/search/jql"
```

**JQL construction examples**:

```
# Default (current user, SF component, not closed)
project = ACM AND assignee = currentUser() AND component = "Server Foundation" AND status not in (Closed)

# Specific member
project = ACM AND assignee = "zxue@redhat.com" AND component = "Server Foundation" AND status not in (Closed)

# All SF team members
project = ACM AND assignee in ("leyan@redhat.com", "qhao@redhat.com", ...) AND component = "Server Foundation" AND status not in (Closed)

# With sprint filter
... AND sprint = "SF Sprint 2026-Q1-S3"

# With current sprint
... AND sprint in openSprints()
```

### Step 3: Parse and sort results

Parse the JSON response with Python. Extract sprint name from `customfield_10020` (JSON array of sprint objects, use last entry's `name` field).

**Sort orders**:

Type order: Epic(0) → Initiative(1) → Feature(2) → Story(3) → Task(4) → Bug(5) → Vulnerability(6)

Status order: In Progress(0) → New(1) → Backlog(2) → Review(3) → Testing(4) → Resolved(5)

```python
import json, sys

data = json.load(sys.stdin)
issues = data.get('issues', [])

results = []
for issue in issues:
    f = issue['fields']
    sprint_field = f.get('customfield_10020')
    sprint_name = ''
    if sprint_field and isinstance(sprint_field, list) and len(sprint_field) > 0:
        last_sprint = sprint_field[-1]
        sprint_name = last_sprint.get('name', '') if isinstance(last_sprint, dict) else ''

    assignee = f.get('assignee', {})
    assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'

    results.append({
        'type': f['issuetype']['name'],
        'key': issue['key'],
        'summary': f['summary'],
        'status': f['status']['name'],
        'priority': f['priority']['name'],
        'assignee': assignee_name,
        'sprint': sprint_name
    })

type_order = {'Epic': 0, 'Initiative': 1, 'Feature': 2, 'Story': 3, 'Task': 4, 'Bug': 5, 'Vulnerability': 6}
status_order = {'In Progress': 0, 'New': 1, 'Backlog': 2, 'Review': 3, 'Testing': 4, 'Resolved': 5}

results.sort(key=lambda x: (type_order.get(x['type'], 99), status_order.get(x['status'], 99)))

for r in results:
    print(f"{r['type']}\t{r['key']}\t{r['summary']}\t{r['status']}\t{r['priority']}\t{r['assignee']}\t{r['sprint']}")
```

### Step 4: Present results

Display as a **markdown table** with columns: Type, Key, Summary, Status, Priority, Assignee, Sprint.

- Bold the first row of each new Type group
- When querying a single person, the Assignee column can be omitted
- After the table, show:
  - Total number of issues
  - Status distribution (e.g., "3 In Progress, 5 New, 2 Review")
  - If team-wide: per-member count summary
- Include browse URL pattern: `https://redhat.atlassian.net/browse/<KEY>`

## Examples

```
# List my open jiras (default)
/sfa-jira-search

# Show all SF team issues in current sprint
/sfa-jira-search --assignee team --sprint current

# What bugs does zhiwei have?
/sfa-jira-search --assignee zhiwei --type Bug

# Show team's in-progress work
/sfa-jira-search --assignee team --status "In Progress"

# Natural language
Show me qiujian's open jiras
What jiras does the SF team have in progress?
List all SF bugs in the current sprint
```

## Notes

- Project is always `ACM`
- Sprint field is `customfield_10020` (JSON array of sprint objects)
- Authentication: Basic Auth with `$JIRA_EMAIL` + `$JIRA_API_TOKEN`
- Available statuses: New, Backlog, In Progress, Review, Testing, Resolved, Closed
- Browse URL: `https://redhat.atlassian.net/browse/<ISSUE-KEY>`
