# SFA conventions (shared reference)

Embedded in workflow prompts under `prompts/`. **Agents should use inline
conventions in the active prompt** — not a separate read step.

If reading from disk (optional):

- `/workspace/server-foundation-agent/prompts/_sfa-conventions.md` (this file)

## Repository

| Path | GitHub |
|------|--------|
| `/workspace/server-foundation-agent` | `stolostron/server-foundation-agent` |

**Working directory:** repo root before `./repos/sync-repos.sh`, workflow scripts, or
`.output/` writes.

## Jira (MCP preferred)

Use **Jira MCP tools** when available (`search_issues`, `get_issue`, `add_comment`,
`update_issue`). Do **not** use Jira CLI.

Script fallbacks (when MCP lacks comment access or posting fails) may use REST via
`JIRA_EMAIL` + `JIRA_API_TOKEN` — see `workflows/daily-bug-triage/*.py`.

**Host:** `https://redhat.atlassian.net`
**Project:** ACM
**Team component:** `Server Foundation`

### Daily bug triage label

After posting triage analysis, add label **`agent-triaged`** via MCP `update_issue` (or
REST fallback in `post_jira_comments.py`). Used for dedup in Phase 1.5 alongside
the triage comment signature.

## Code access

| Location | Use |
|----------|-----|
| `repos/` | Read-only reference clones (`./repos/sync-repos.sh`) |
| `workspace/` | Writable worktrees for fixes (`sfa-workspace-clone` skill) |

Never commit inside `repos/`.

## GitHub

- Use `gh` for PRs
- Draft PRs until a human marks ready
- Commits: conventional + `Signed-off-by`

## Slack

- `SLACK_WEBHOOK_URL` for notifications
- Helper: `.claude/skills/sfa-slack-notify/send_to_slack.sh`

## Automation footer

Daily bug triage Jira comments must end with:

```
_— server-foundation-agent (daily bug triage)_
```

and include `h3. Bug Triage Analysis` so dedup scripts recognize prior runs.
