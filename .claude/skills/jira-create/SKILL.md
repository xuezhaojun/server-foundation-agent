---
name: jira-create
description: "Create Jira issues in the ACM project on Red Hat Jira Cloud (redhat.atlassian.net) for the Server Foundation team. Use this skill when the user wants to create a new Jira issue, file a bug, create a task/story/epic/feature, or says things like 'create a jira', 'file a bug', 'new jira issue', 'open a ticket', 'track this in jira'. Also trigger when the user describes a problem or feature and asks to track it."
---

# Jira Create

Create Jira issues in the ACM project on https://redhat.atlassian.net for the Server Foundation team.

## Parameters

Parse these from the user's message or arguments:

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| type | Yes | - | `Epic`, `Bug`, `Task`, `Story`, `Feature`, `Initiative` |
| summary | Yes | - | Issue title |
| description | No | - | Issue body/description |
| assignee | No | current user | Team member name/email. Resolved via `team-members/team-members.md` |
| component | No | `Server Foundation` | Component field |
| affects-version | **Yes** | - | Format: `MCE X.YY.Z` (e.g., `MCE 2.14.0`) |
| fix-version | **Yes** | - | Format: `MCE X.YY.Z` (e.g., `MCE 2.14.0`) |
| priority | No | `Major` | Issue priority |
| severity | No | `Important` | Custom field `customfield_10840` |
| activity-type | **Yes** | auto-mapped | Custom field `customfield_10464`. See mapping below |
| link | No | - | Another Jira issue key to link to (e.g., `ACM-29991`) |
| link-type | No | `Relates` | `Relates`, `Blocks`, `Duplicates`, `is child of` |

### Version Shortcuts

Users often express versions in natural language:

- **"在 MCE 2.14.0 实现"** or **"for MCE 2.14.0"** → both versions = `MCE 2.14.0`
- **"MCE 2.13.0 发现的问题，2.14.0 fix"** → affects=`MCE 2.13.0`, fix=`MCE 2.14.0`
- **"found in 2.13, fix in 2.14"** → affects=`MCE 2.13.0`, fix=`MCE 2.14.0`

When only a single version is mentioned (not for a Bug), assume both are the same.

### Activity Type (required)

Auto-map based on issue type if not specified:

| Issue Type | Default Activity Type |
|------------|----------------------|
| Bug | Quality / Stability / Reliability |
| Vulnerability | Security & Compliance |
| Story / Feature / Epic / Initiative | Product / Portfolio Work |
| Task | Quality / Stability / Reliability |
| Spike | Future Sustainability |

Valid values:
- Associate Wellness & Development
- Incidents & Support
- Security & Compliance
- Quality / Stability / Reliability
- Future Sustainability
- Product / Portfolio Work

Always tell the user which Activity Type was selected.

## Workflow

### Step 1: Validate required fields

1. Check `affects-version` and `fix-version` — prompt if missing:
   > To create this Jira issue, I need:
   > - **Affects Version/s**: Which version is affected? (e.g., `MCE 2.14.0`)
   > - **Fix Version/s**: Which version should contain the fix? (e.g., `MCE 2.14.0`)
2. Auto-map `activity-type` if not specified. Tell the user which was selected.
3. If `assignee` is specified, resolve to email via `team-members/team-members.md`.

Do NOT proceed until required fields are provided.

### Step 2: Create the issue via REST API

**IMPORTANT**: Do NOT use `jira issue create` CLI for option-type custom fields. Use the REST API directly.

**For Epic type**: Include `customfield_10011` (Epic Name) set to summary value.

```bash
cat > /tmp/jira_create.json << 'ENDOFJSON'
{
  "fields": {
    "project": {"key": "ACM"},
    "issuetype": {"name": "<Type>"},
    "summary": "<Summary>",
    "description": "<Description or empty string>",
    "priority": {"name": "<Priority>"},
    "components": [{"name": "<Component>"}],
    "versions": [{"name": "<affects-version>"}],
    "fixVersions": [{"name": "<fix-version>"}],
    "customfield_10840": {"value": "<Severity>"},
    "customfield_10464": {"value": "<Activity Type>"},
    "customfield_10011": "<Epic Name, only for Epic type>"
  }
}
ENDOFJSON

curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/jira_create.json \
  "https://redhat.atlassian.net/rest/api/2/issue"
```

Notes:
- For **Epic**: include `customfield_10011`. Omit for non-Epic types.
- `versions` = Affects Version/s field
- `fixVersions` = Fix Version/s field
- Valid Severity: `Critical`, `Important`, `Moderate`, `Low`, `Informational`

Extract the issue key from the response (`key` field).

### Step 3: Assign the issue (if specified)

If assignee is specified and differs from current user:

```bash
curl -s -X PUT \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"assignee": {"name": "<email>"}}}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>"
```

### Step 4: Link the issue (if requested)

```bash
jira issue link <NEW-ISSUE-KEY> <LINK-TARGET> <link-type>
```

### Step 5: Show the result

```bash
jira issue view <NEW-ISSUE-KEY>
```

Provide the browse URL: `https://redhat.atlassian.net/browse/<NEW-ISSUE-KEY>`

## Examples

```
# Full example
/jira-create --type task --summary "Fix cluster-proxy cert rotation" --affects-version "MCE 2.14.0" --fix-version "MCE 2.14.0" --assignee zhiwei --link ACM-29991

# Minimal (will prompt for versions)
/jira-create --type bug --summary "Proxy agent crash on restart"

# Natural language
Create a jira bug for the cluster-proxy crash issue, affects MCE 2.14.0, assign to zhiwei
File a task to upgrade go dependencies for MCE 2.15.0
```

## Notes

- Project is always `ACM`
- Custom fields: Severity(`customfield_10840`), Activity Type(`customfield_10464`), Epic Name(`customfield_10011`)
- Authentication: Basic Auth with `$JIRA_EMAIL` + `$JIRA_API_TOKEN`
- Valid issue types: Epic, Bug, Task, Story, Feature, Initiative, Spike, Vulnerability
- Always capitalize issue type names
- Browse URL: `https://redhat.atlassian.net/browse/<ISSUE-KEY>`
