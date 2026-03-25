---
name: sfa-jira-standup
description: "Generate a daily standup report from Jira for a Server Foundation team member. Use this skill when the user wants a standup summary, daily update, or asks 'what did I do yesterday', 'standup', 'daily update', 'my status'. Queries Jira to find recently updated and in-progress issues, then formats a standup report."
---

# Jira Standup Report

Generate a daily standup report from Jira issues.

## Reference Loading

- **For JQL syntax**: Read `docs/jira/jql-reference.md`
- **For API details**: Read `docs/jira/api-reference.md`

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| assignee | No | current user | Team member name/email |
| days | No | 1 | How many days back to look for "Done" items |

## Workflow

### Step 1: Resolve assignee

If specified, look up in `team-members/team-members.md`. Otherwise use `currentUser()`.

### Step 2: Run two JQL queries

**Query 1 — What I did (updated yesterday/recently):**

```
project = ACM AND component = "Server Foundation" AND assignee = <user> AND updated >= -<days>d AND status IN (Resolved, Closed, Review, Testing)
```

**Query 2 — What I'm doing (in progress):**

```
project = ACM AND component = "Server Foundation" AND assignee = <user> AND status IN ("In Progress", "New")
```

Use `/rest/api/3/search/jql` POST for both. Request fields: `["issuetype", "summary", "status", "priority", "updated"]`.

### Step 3: Format standup report

```markdown
## Standup Report — <Name> (<date>)

### Done (updated in last <N> day(s))
- [ACM-12345](https://redhat.atlassian.net/browse/ACM-12345) Fix proxy cert rotation — *Resolved*
- [ACM-12346](https://redhat.atlassian.net/browse/ACM-12346) Update go dependencies — *Review*

### In Progress
- [ACM-12347](https://redhat.atlassian.net/browse/ACM-12347) Implement addon health check — *In Progress*
- [ACM-12348](https://redhat.atlassian.net/browse/ACM-12348) Investigate flaky test — *New*

### Blockers
<None identified — ask the user if they have any>
```

### Step 4: Ask about blockers

After presenting the report, ask: "Any blockers to add?"

## Examples

```
/sfa-jira-standup
What did I do yesterday?
Standup for zhiwei
```
