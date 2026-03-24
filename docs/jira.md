# Jira Integration

Server Foundation team uses Red Hat Jira Cloud (https://redhat.atlassian.net) for issue tracking under the **ACM** (Advanced Cluster Management) project.

## Quick Reference

- **Project key**: `ACM`
- **Default component**: `Server Foundation`
- **Browse URL**: `https://redhat.atlassian.net/browse/<ISSUE-KEY>`
- **Auth**: Basic Auth with `$JIRA_EMAIL` + `$JIRA_API_TOKEN`

## Reference Materials

Load these on-demand based on the task at hand:

| Reference | Path | When to Load |
|-----------|------|-------------|
| [Custom Fields](jira/custom-fields.md) | `docs/jira/custom-fields.md` | Creating/updating issues with custom fields (severity, activity type, versions) |
| [Workflows](jira/workflows.md) | `docs/jira/workflows.md` | Status transitions, understanding workflow states |
| [Formatting](jira/formatting.md) | `docs/jira/formatting.md` | Writing comments/descriptions with Jira wiki markup |
| [JQL Reference](jira/jql-reference.md) | `docs/jira/jql-reference.md` | Building search queries, JQL syntax and functions |
| [API Reference](jira/api-reference.md) | `docs/jira/api-reference.md` | REST API endpoints, authentication, curl examples |
| [Templates](jira/templates.md) | `docs/jira/templates.md` | Issue creation templates (Bug, Epic, Story, Task, Vulnerability) |

## Bootstrap Sequence

At session start, verify Jira connectivity before executing any Jira operation:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/myself" \
  | jq '{name: .displayName, email: .emailAddress, accountId: .accountId}'
```

If auth fails (missing env vars or invalid token), stop and report clearly.

## Skills

Four CRUD skills and three scenario skills for Jira operations:

| Skill | Purpose | Trigger |
|-------|---------|---------|
| [sfa-jira-search](../.claude/skills/sfa-jira-search/SKILL.md) | Search/list issues (team-wide or per-member) | "show jiras", "what bugs does X have" |
| [sfa-jira-create](../.claude/skills/sfa-jira-create/SKILL.md) | Create issues with SF defaults | "create a jira bug" |
| [sfa-jira-update](../.claude/skills/sfa-jira-update/SKILL.md) | Status transitions and field updates | "move ACM-12345 to review" |
| [sfa-jira-comment](../.claude/skills/sfa-jira-comment/SKILL.md) | Add comments (PR links, progress notes) | "post PR to ACM-12345" |
| [sfa-jira-standup](../.claude/skills/sfa-jira-standup/SKILL.md) | Daily standup report | "standup", "daily update" |
| [sfa-jira-triage](../.claude/skills/sfa-jira-triage/SKILL.md) | Bug triage report | "triage bugs", "new bugs" |
| [sfa-jira-sprint-report](../.claude/skills/sfa-jira-sprint-report/SKILL.md) | Sprint health report | "sprint status", "sprint report" |

## Lifecycle Integration

```
1. Create issue         →  sfa-jira-create
2. Start development    →  sfa-jira-update --status "In Progress"
3. Create PR            →  sfa-jira-comment --pr-url <URL>
4. Submit for review    →  sfa-jira-update --status Review
5. PR merged            →  sfa-jira-comment "PR merged" + sfa-jira-update --status Resolved
```
