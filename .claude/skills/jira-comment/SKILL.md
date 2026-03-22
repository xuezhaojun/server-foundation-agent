---
name: jira-comment
description: "Add comments to Jira issues on Red Hat Jira Cloud (redhat.atlassian.net). Use this skill when the user wants to add a comment, post a PR link, update progress, or log notes on a Jira issue. Trigger phrases: 'comment on jira', 'add jira comment', 'post PR to jira', 'update jira with PR', 'log progress on ACM-12345', 'link PR to jira'. Also trigger automatically when a PR is created and a Jira issue key is mentioned."
---

# Jira Comment

Add comments to Jira issues on https://redhat.atlassian.net. Designed for workflow integration — linking PRs, logging progress, and posting status updates.

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| issue-key | Yes | - | Jira issue key (e.g., `ACM-12345`) |
| comment | Yes | - | Comment text (supports Jira wiki markup) |
| pr-url | No | - | GitHub PR URL to format as a structured comment |

## Comment Templates

### PR Link Comment

When a PR URL is provided (or detected from context), format a structured comment:

```
PR submitted: [<PR-title>|<PR-URL>]

Repository: <org/repo>
Branch: <branch-name>
Author: <author>
```

### Progress Update Comment

When the user wants to log progress:

```
*Progress Update* (<date>)

<user's message>
```

### General Comment

For free-form comments, post the text as-is with Jira wiki markup.

## Workflow

### Step 1: Validate issue exists

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>?fields=summary,status" | jq '{key: .key, summary: .fields.summary, status: .fields.status.name}'
```

### Step 2: Build comment body

If a `pr-url` is provided, fetch PR details from GitHub:

```bash
# Extract org/repo and PR number from URL
gh pr view <PR-URL> --json title,headRefName,author,url
```

Then format the PR link comment using the template above.

For Jira Cloud REST API v2, the comment body uses **plain text with Jira wiki markup** (not ADF):

- Bold: `*text*`
- Links: `[title|url]`
- Code: `{{code}}`
- Headings: `h3. Title`

### Step 3: Post the comment

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "body": "<comment text with Jira wiki markup>"
  }' \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>/comment"
```

### Step 4: Show confirmation

Display:
- The issue key and summary
- The comment that was posted
- Browse URL: `https://redhat.atlassian.net/browse/<ISSUE-KEY>`

## PR Lookup from Issue

To check existing PR links on an issue (e.g., when user asks "what PRs are linked to ACM-12345"):

### Check comments for PR URLs

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>/comment" | \
  jq '.comments[].body' | grep -i "github.com.*pull"
```

### Check custom fields for PR references

The Git Pull Request field is stored in `customfield_10875`:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<ISSUE-KEY>" | \
  jq '.fields | to_entries[] | select(.value != null and (.value | tostring | (contains("github") or contains("pull"))))'
```

## Examples

```
# Add a PR link comment
/jira-comment --issue-key ACM-12345 --pr-url https://github.com/stolostron/cluster-proxy/pull/99

# Free-form comment
/jira-comment --issue-key ACM-12345 --comment "Identified root cause: cert rotation timer not reset after reconnect"

# Natural language
Post the PR link to ACM-12345
Add a comment to ACM-12345: fixed the nil pointer in addon manager
Update ACM-12345 with the PR
What PRs are linked to ACM-12345?
```

## Integration with Other Skills

This skill works well in combination with other skills:

1. **After creating a PR** (via clone-worktree + git workflow):
   - Auto-comment the PR URL on the related Jira issue
   - Optionally transition the issue to "Review" using `jira-update`

2. **After PR is merged**:
   - Comment "PR merged" on the Jira issue
   - Transition to "Resolved" using `jira-update`

3. **During development**:
   - Log progress notes as comments
   - Transition to "In Progress" using `jira-update`

## Notes

- Authentication: Basic Auth with `$JIRA_EMAIL` + `$JIRA_API_TOKEN`
- Jira Cloud REST API v2 comment endpoint uses wiki markup format (not Atlassian Document Format)
- For v3 endpoints, ADF format is required — use v2 for simplicity
- Browse URL: `https://redhat.atlassian.net/browse/<ISSUE-KEY>`
