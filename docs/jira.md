# Jira Integration

Server Foundation team uses Red Hat Jira Cloud (https://redhat.atlassian.net) for issue tracking under the **ACM** (Advanced Cluster Management) project.

## Authentication

All Jira operations require two environment variables:

| Variable | Description |
|----------|-------------|
| `JIRA_EMAIL` | Your Red Hat email (e.g., `zxue@redhat.com`) |
| `JIRA_API_TOKEN` | API token from https://id.atlassian.com/manage-profile/security/api-tokens |

Authentication uses HTTP Basic Auth: `$JIRA_EMAIL:$JIRA_API_TOKEN`.

## ACM Project Structure

- **Project key**: `ACM`
- **Default component**: `Server Foundation`
- **Jira instance**: `https://redhat.atlassian.net`
- **Browse URL pattern**: `https://redhat.atlassian.net/browse/<ISSUE-KEY>`

### Issue Types

Epic, Bug, Task, Story, Feature, Initiative, Spike, Vulnerability, Outcome, Risk, Closed Loop

### Custom Fields

| Field | Field ID | Type | Notes |
|-------|----------|------|-------|
| Severity | `customfield_10840` | Option | `Critical`, `Important`, `Moderate`, `Low`, `Informational` |
| Activity Type | `customfield_10464` | Option | Required field. See mapping below |
| Epic Name | `customfield_10011` | String | Required when creating Epics |
| Sprint | `customfield_10020` | JSON Array | Array of sprint objects with `name`, `state`, etc. |
| Git Pull Request | `customfield_10875` | String | GitHub PR URL in smart-link format |

### Activity Type Mapping

Activity Type (`customfield_10464`) is **required** for all issues. Default mapping by issue type:

| Issue Type | Default Activity Type |
|------------|----------------------|
| Bug | Quality / Stability / Reliability |
| Vulnerability | Security & Compliance |
| Story / Feature / Epic / Initiative | Product / Portfolio Work |
| Task | Quality / Stability / Reliability |
| Spike | Future Sustainability |

All valid values:
- Associate Wellness & Development
- Incidents & Support
- Security & Compliance
- Quality / Stability / Reliability
- Future Sustainability
- Product / Portfolio Work

### Version Format

Versions follow the format `MCE X.YY.Z` (e.g., `MCE 2.14.0`). Both `affects-version` and `fix-version` are required fields.

## Workflow & Statuses

```
New → In Progress → Review → Testing → Resolved → Closed
         ↑                                    ↓
         └────────────── Reopen ──────────────┘
```

| Status | Description |
|--------|-------------|
| New | Newly created, not yet started |
| Backlog | Acknowledged but not planned for current sprint |
| In Progress | Actively being worked on |
| Review | Code submitted, PR under review |
| Testing | PR merged, awaiting QE verification |
| Resolved | Verified and done |
| Closed | Fully closed |

### Common Transitions

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

## REST API Notes

### API Versions

- **Issue CRUD**: Use `/rest/api/2/issue` (v2) — supports wiki markup for comments and descriptions
- **Search/JQL**: Use `/rest/api/3/search/jql` with POST — Jira Cloud has removed the v2 search endpoint
- **Transitions**: Use `/rest/api/2/issue/{key}/transitions`
- **Comments**: Use `/rest/api/2/issue/{key}/comment`

### Jira Wiki Markup (for v2 endpoints)

- Bold: `*text*`
- Links: `[title|url]`
- Inline code: `{{code}}`
- Headings: `h3. Title`
- Lists: `* item` (unordered), `# item` (ordered)

### CLI vs REST API

The `jira` CLI tool works for simple operations (`jira issue view`, `jira issue link`), but does **not** support option-type custom fields (Severity, Activity Type) via `--custom`. Always use the REST API directly for creating and updating issues with custom fields.

## Skills

Four Jira skills are available for the agent:

| Skill | Purpose | Example Trigger |
|-------|---------|-----------------|
| [jira-search](../.claude/skills/jira-search/SKILL.md) | Search/list issues (team-wide or per-member) | "show team jiras", "what bugs does zhiwei have" |
| [jira-create](../.claude/skills/jira-create/SKILL.md) | Create issues with SF defaults | "create a jira bug for cluster-proxy crash" |
| [jira-update](../.claude/skills/jira-update/SKILL.md) | Status transitions and field updates | "move ACM-12345 to review" |
| [jira-comment](../.claude/skills/jira-comment/SKILL.md) | Add comments (PR links, progress notes) | "post PR to ACM-12345" |

### Workflow Integration

These skills chain together to support the full development lifecycle:

```
1. Create issue         →  jira-create
2. Start development    →  jira-update --status "In Progress"
3. Create PR            →  jira-comment --pr-url <URL>
4. Submit for review    →  jira-update --status Review
5. PR merged            →  jira-comment "PR merged" + jira-update --status Resolved
```
