# Jira REST API Reference

API endpoints and authentication for Red Hat Jira Cloud.

## Authentication

All operations require two environment variables:

| Variable | Description |
|----------|-------------|
| `JIRA_EMAIL` | Red Hat email (e.g., `zxue@redhat.com`) |
| `JIRA_API_TOKEN` | API token from https://id.atlassian.com/manage-profile/security/api-tokens |

Format: HTTP Basic Auth with `$JIRA_EMAIL:$JIRA_API_TOKEN`.

### Pre-flight Check

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/myself" | jq '{name: .displayName, email: .emailAddress, accountId: .accountId}'
```

If this fails, stop and report the auth error.

## Base URL

`https://redhat.atlassian.net`

## API Version Strategy

| Operation | Endpoint | Version | Format |
|-----------|----------|---------|--------|
| Issue CRUD | `/rest/api/2/issue` | v2 | Wiki markup |
| Search/JQL | `/rest/api/3/search/jql` | v3 (POST) | ADF (response only) |
| Transitions | `/rest/api/2/issue/{key}/transitions` | v2 | — |
| Comments | `/rest/api/2/issue/{key}/comment` | v2 | Wiki markup |
| User info | `/rest/api/2/myself` | v2 | — |

**Why mixed versions**: Jira Cloud removed the v2 search endpoint. Use v3 POST for search, v2 for everything else (wiki markup is simpler than ADF).

## Common Operations

### Get Issue

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>?fields=summary,status,assignee,priority,issuetype"
```

### Create Issue

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/jira_create.json \
  "https://redhat.atlassian.net/rest/api/2/issue"
```

### Update Issue Fields

```bash
curl -s -X PUT \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"assignee": {"name": "<email>"}, "priority": {"name": "<Priority>"}}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>"
```

### Search Issues (JQL)

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jql": "<JQL>", "fields": ["issuetype","summary","status","priority","assignee","customfield_10020"], "maxResults": 100}' \
  "https://redhat.atlassian.net/rest/api/3/search/jql"
```

### Add Comment

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": "<wiki markup text>"}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>/comment"
```

### Get Transitions

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>/transitions" \
  | jq '.transitions[] | {id, name, to: .to.name}'
```

### Execute Transition

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transition": {"id": "<id>"}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>/transitions"
```

### Label Operations

```bash
# Add label
curl -s -X PUT -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"update": {"labels": [{"add": "<label>"}]}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>"

# Remove label
curl -s -X PUT -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"update": {"labels": [{"remove": "<label>"}]}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>"
```

## ACM Project Constants

- **Project key**: `ACM`
- **Default component**: `Server Foundation`
- **Browse URL**: `https://redhat.atlassian.net/browse/<KEY>`
- **Issue types**: Epic, Bug, Task, Story, Feature, Initiative, Spike, Vulnerability, Outcome, Risk, Closed Loop
