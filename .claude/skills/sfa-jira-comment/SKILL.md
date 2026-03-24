---
name: sfa-jira-comment
description: "Add comments to Jira issues on Red Hat Jira Cloud (redhat.atlassian.net). Use this skill when the user wants to add a comment, post a PR link, update progress, or log notes on a Jira issue. Trigger phrases: 'comment on jira', 'add jira comment', 'post PR to jira', 'update jira with PR', 'log progress on ACM-12345', 'link PR to jira'. Also trigger automatically when a PR is created and a Jira issue key is mentioned."
---

# Jira Comment

Add comments to Jira issues. Designed for workflow integration — linking PRs, logging progress, posting status updates.

## Reference Loading

Before executing, load relevant references as needed:
- **For wiki markup syntax**: Read `docs/jira/formatting.md`
- **For API details**: Read `docs/jira/api-reference.md`

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| issue-key | Yes | - | Jira issue key (e.g., `ACM-12345`) |
| comment | Yes | - | Comment text (supports Jira wiki markup) |
| pr-url | No | - | GitHub PR URL to format as structured comment |

## Comment Templates

### PR Link Comment

```
PR submitted: [<PR-title>|<PR-URL>]

Repository: <org/repo>
Branch: <branch-name>
Author: <author>

----
_— server-foundation-agent_
```

### Progress Update

```
*Progress Update* (<date>)

<user's message>

----
_— server-foundation-agent_
```

### General Comment

Post text as-is with wiki markup. **Always** append the agent signature footer.

## Workflow

### Step 1: Validate issue exists

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>?fields=summary,status" \
  | jq '{key: .key, summary: .fields.summary, status: .fields.status.name}'
```

### Step 2: Build comment body

If `pr-url` provided, fetch PR details:
```bash
gh pr view <PR-URL> --json title,headRefName,author,url
```

For wiki markup syntax, see `docs/jira/formatting.md`.

### Step 3: Post comment

```bash
curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": "<wiki markup text>"}' \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>/comment"
```

### Step 4: Show confirmation

Display issue key, summary, posted comment, and browse URL.

## PR Lookup

To check existing PR links on an issue:

```bash
# Check comments for PR URLs
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>/comment" | \
  jq '.comments[].body' | grep -i "github.com.*pull"
```

## Integration with Other Skills

- **After PR created**: Auto-comment PR URL, optionally transition to "Review" via `sfa-jira-update`
- **After PR merged**: Comment "PR merged", transition to "Resolved" via `sfa-jira-update`
- **During development**: Log progress notes as comments

## Examples

```
/sfa-jira-comment --issue-key ACM-12345 --pr-url https://github.com/stolostron/cluster-proxy/pull/99
Add a comment to ACM-12345: fixed the nil pointer in addon manager
```
