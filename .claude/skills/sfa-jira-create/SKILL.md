---
name: sfa-jira-create
description: "Create Jira issues in the ACM project on Red Hat Jira Cloud (redhat.atlassian.net) for the Server Foundation team. Use this skill when the user wants to create a new Jira issue, file a bug, create a task/story/epic/feature, or says things like 'create a jira', 'file a bug', 'new jira issue', 'open a ticket', 'track this in jira'. Also trigger when the user describes a problem or feature and asks to track it."
---

# Jira Create

Create Jira issues in the ACM project for the Server Foundation team.

## Reference Loading

Before executing, load relevant references:
- **For custom fields and activity type mapping**: Read `docs/jira/custom-fields.md`
- **For issue templates**: Read `docs/jira/templates.md`
- **For API details**: Read `docs/jira/api-reference.md`

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| type | Yes | - | `Epic`, `Bug`, `Task`, `Story`, `Feature`, `Initiative` |
| summary | Yes | - | Issue title |
| description | No | - | Issue body (use template from `docs/jira/templates.md`) |
| assignee | No | current user | Resolved via `team-members/team-members.md` |
| component | No | `Server Foundation` | |
| affects-version | **Yes** | - | Format: `MCE X.YY.Z` |
| fix-version | **Yes** | - | Format: `MCE X.YY.Z` |
| priority | No | `Major` | |
| severity | No | `Important` | `customfield_10840` |
| activity-type | **Yes** | auto-mapped | `customfield_10464` (see `docs/jira/custom-fields.md`) |
| link | No | - | Issue key to link to |
| link-type | No | `Relates` | `Relates`, `Blocks`, `Duplicates`, `is child of` |

## Workflow

### Step 1: Validate required fields

1. Check `affects-version` and `fix-version` — prompt if missing
2. Auto-map `activity-type` from issue type if not specified (see `docs/jira/custom-fields.md`)
3. Resolve `assignee` to email if specified

Do NOT proceed until required fields are provided.

### Step 2: Create via REST API

Use REST API directly (CLI cannot set option-type custom fields).

For **Epic**: also set `customfield_10011` (Epic Name) = summary.

Use the template from `docs/jira/templates.md` for the description if user didn't provide one.

```bash
cat > /tmp/jira_create.json << 'ENDOFJSON'
{
  "fields": {
    "project": {"key": "ACM"},
    "issuetype": {"name": "<Type>"},
    "summary": "<Summary>",
    "description": "<Description>\n\n----\n_Created by server-foundation-agent_",
    "priority": {"name": "<Priority>"},
    "labels": ["sfa-assisted"],
    "components": [{"name": "<Component>"}],
    "versions": [{"name": "<affects-version>"}],
    "fixVersions": [{"name": "<fix-version>"}],
    "customfield_10840": {"value": "<Severity>"},
    "customfield_10464": {"value": "<Activity Type>"}
  }
}
ENDOFJSON

curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/jira_create.json \
  "https://redhat.atlassian.net/rest/api/2/issue"
```

### Step 3: Assign (if specified)

```bash
curl -s -X PUT -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"assignee": {"name": "<email>"}}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>"
```

### Step 4: Link (if requested)

```bash
jira issue link <NEW-KEY> <LINK-TARGET> <link-type>
```

### Step 5: Show result

```bash
jira issue view <NEW-KEY>
```

Provide browse URL: `https://redhat.atlassian.net/browse/<KEY>`

## Examples

```
/sfa-jira-create --type bug --summary "Proxy agent crash on restart" --affects-version "MCE 2.14.0" --fix-version "MCE 2.14.0"
Create a jira bug for the cluster-proxy crash issue, affects MCE 2.14.0, assign to zhiwei
```
