# Skills

Skills are task-specific workflows the agent can execute. Each skill has a step-by-step checklist in its `SKILL.md`.

| Skill | Description | Trigger |
|-------|-------------|---------|
| [fetch-prs](fetch-prs/SKILL.md) | Fetch all active PRs for the Server Foundation team | On demand |
| [slack-notify](slack-notify/SKILL.md) | Send formatted notifications to Slack | On demand |
| [clone-worktree](clone-worktree/SKILL.md) | Clone a repo and create a worktree for a PR or new branch (MUST use for all workspace checkouts) | On demand |
| [cleanup-workspace](cleanup-workspace/SKILL.md) | Remove workspace worktrees/clones whose PRs are merged/closed | On demand |
| [sync-repos](sync-repos/SKILL.md) | Initialize or update all submodules under repos/ to latest | On demand |
| [jira-search](jira-search/SKILL.md) | Search/list Jira issues for the SF team (supports team-wide and per-member queries) | On demand |
| [jira-create](jira-create/SKILL.md) | Create Jira issues in the ACM project with SF defaults | On demand |
| [jira-update](jira-update/SKILL.md) | Update Jira issue status (workflow transitions) and fields | On demand |
| [jira-comment](jira-comment/SKILL.md) | Add comments to Jira issues (PR links, progress updates) | On demand |

## Adding a New Skill

1. Create `.claude/skills/<skill-name>/SKILL.md` with frontmatter (`name`, `description`) and a step-by-step checklist
2. Update this table
3. (Optional) Add a CronJob in `deploy/cronjobs/` if the skill should run on a schedule
4. Open a PR — the skill is available to the agent once merged
