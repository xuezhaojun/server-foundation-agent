# Server Foundation Agent - Updates

Daily development log. Each day's entry covers what changed, why, and any thoughts or discoveries along the way.

Use `/sfa-session-log` to append entries after each session.

**Format:** `## YYYY-MM-DD` heading, then bullet points. For significant architectural decisions, add a brief "Why / What it replaces" note (2-3 lines max) right after the bullet.

---

## 2026-03-24

- Adopted **progressive disclosure** as a core agent design principle. Inspired by [HCM Jira Administrator Agent](https://github.com/openshift-online/rosa-claude-plugins/tree/main/hcm-jira-administrator-agent). Context window is a scarce resource — skills contain workflow steps ("how"), reference knowledge ("what") lives in separate docs loaded on demand.
- Refactored all Jira skills: split `docs/jira.md` into 6 reference files under `docs/jira/`, slimmed 4 SKILL.md files by ~45%.
- Added 3 new scenario-based Jira skills: `sfa-jira-standup`, `sfa-jira-triage`, `sfa-jira-sprint-report`.
- Applied progressive disclosure to `docs/repo-dependencies.md` (393→~150 lines index + sub-files), `docs/prow.md`, `docs/build-release.md`.
- Added progressive disclosure section to root CLAUDE.md as permanent design guideline (SKILL.md < ~100 lines, docs > 150 lines should split, shared content extracted to reference files).
- Added **daily-bug-triage workflow** — automated triage of SF Jira bugs in "New" status every weekday at 09:00 CST. Sub-agents search `repos/` for root cause analysis, results posted to Slack.
  - Why: manual bug triage was slow and inconsistent. Automation ensures every new bug gets at least a first-pass analysis.

## 2026-03-23

- Fixed 2 cluster-permission bugs. Root cause tied to recent ACM→MCE migration.
- Test cluster access is a game changer — once agent got admin kubeconfig, it found root cause fast. Confirms: agent needs cluster access for debug tasks.
- Agent lacks long-term memory of engineering activities. Had to manually tell it about the cluster-permission migration. It should know "what happened recently" as context — recent changes are highly correlated with recent bugs. Need a mechanism to feed engineering history into agent context.
- Agent cannot access QE Jenkins (`*.dno.corp.redhat.com`) — behind VPN. Workaround: paste logs manually.
- Agent cannot access downstream test environments — can't reproduce or verify. Need dedicated test cluster.
- Removed GitHub Projects board and 5 related skills (`sfa-project-{create,update,search,sync,report}`). Jira is the sole project tracking tool — the board was redundant overhead.
  - What replaces it: Jira (project tracking), `updates.md` (session logs), `sfa-jira-comment` (progress updates).
- Added `updates.md` and `sfa-session-log` skill, replacing `docs/limitations.md`.
