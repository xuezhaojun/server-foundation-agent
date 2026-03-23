# Skills

Skills are task-specific workflows the agent can execute. Each skill has a step-by-step checklist in its `SKILL.md`. All skills use the `sfa-` prefix (Server Foundation Agent) for discoverability.

| Skill | Description | Trigger |
|-------|-------------|---------|
| [sfa-github-fetch-prs](sfa-github-fetch-prs/SKILL.md) | Fetch all active PRs for the Server Foundation team | On demand |
| [sfa-workspace-clone](sfa-workspace-clone/SKILL.md) | Clone a repo and create a worktree for a PR or new branch (MUST use for all workspace checkouts) | On demand |
| [sfa-workspace-cleanup](sfa-workspace-cleanup/SKILL.md) | Remove workspace worktrees/clones whose PRs are merged/closed | On demand |
| [sfa-repo-sync](sfa-repo-sync/SKILL.md) | Initialize or update all submodules under repos/ to latest | On demand |
| [sfa-slack-notify](sfa-slack-notify/SKILL.md) | Send formatted notifications to Slack | On demand |
| [sfa-jira-search](sfa-jira-search/SKILL.md) | Search/list Jira issues for the SF team (supports team-wide and per-member queries) | On demand |
| [sfa-jira-create](sfa-jira-create/SKILL.md) | Create Jira issues in the ACM project with SF defaults | On demand |
| [sfa-jira-update](sfa-jira-update/SKILL.md) | Update Jira issue status (workflow transitions) and fields | On demand |
| [sfa-jira-comment](sfa-jira-comment/SKILL.md) | Add comments to Jira issues (PR links, progress updates) | On demand |
| [sfa-project-create](sfa-project-create/SKILL.md) | Create tasks (draft issues) or add Issues/PRs to the GitHub Projects board | On demand |
| [sfa-project-update](sfa-project-update/SKILL.md) | Update task status, priority, size, dates on the Projects board | On demand |
| [sfa-project-search](sfa-project-search/SKILL.md) | List/filter/query items on the Projects board | On demand |
| [sfa-project-sync](sfa-project-sync/SKILL.md) | Sync Jira issues to the GitHub Projects board | On demand |
| [sfa-project-report](sfa-project-report/SKILL.md) | Generate progress reports from board data, optionally send to Slack | On demand |
| [sfa-session-log](sfa-session-log/SKILL.md) | Log session summary to updates.md (what was done, issues, limitations) | On demand |

## Adding a New Skill

1. Create `.claude/skills/sfa-<category>-<name>/SKILL.md` with frontmatter (`name`, `description`) and a step-by-step checklist
2. Update this table
3. (Optional) Add a CronJob in `deploy/cronjobs/` if the skill should run on a schedule
4. Open a PR — the skill is available to the agent once merged
