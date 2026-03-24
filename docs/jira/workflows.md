# Jira Workflow Reference

Workflow states and transitions for the ACM project on Red Hat Jira Cloud.

## Status Flow

```
New → In Progress → Review → Testing → Resolved → Closed
         ↑                                    ↓
         └────────────── Reopen ──────────────┘
```

## Statuses

| Status | Description |
|--------|-------------|
| New | Newly created, not yet started |
| Backlog | Acknowledged but not planned for current sprint |
| In Progress | Actively being worked on |
| Review | Code submitted, PR under review |
| Testing | PR merged, awaiting QE verification |
| Resolved | Verified and done |
| Closed | Fully closed |

## Transition Names

Status changes require workflow transitions (not direct field updates). Use the transitions API to get the correct transition ID before executing.

| Transition Name | Target Status |
|----------------|---------------|
| Start Progress | In Progress |
| Request Review / Review | Review |
| Testing | Testing |
| Resolve | Resolved |
| Close | Closed |
| Reopen | In Progress |
| Backlog | Backlog |

## How to Execute a Transition

### 1. Get available transitions

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>/transitions" \
  | jq '.transitions[] | {id, name, to: .to.name}'
```

### 2. Execute the transition

Find the transition whose `to.name` matches the target status (case-insensitive), then:

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transition": {"id": "<transition-id>"}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>/transitions"
```

## Natural Language Shortcuts

| User says | Action |
|-----------|--------|
| "start ACM-12345" | Transition to In Progress |
| "ACM-12345 to review" | Transition to Review |
| "resolve ACM-12345" | Transition to Resolved |
| "close ACM-12345" | Transition to Closed |
| "PR is merged, update ACM-12345" | Transition to Resolved + add comment |

## Cross-Project Queries

When querying across multiple projects, use `statusCategory` instead of specific status names:
- `"To Do"` — New, Backlog
- `"In Progress"` — In Progress, Review, Testing
- `"Done"` — Resolved, Closed
