# Server Foundation Agent - Changelog

Project changes, architectural decisions, and the reasoning behind them. Each entry records what changed, why, and what it replaces.

**Format:** `## YYYY-MM-DD` heading, then entries with a brief title and explanation.

---

## 2026-03-24

### Added daily-bug-triage workflow

New automated workflow that triages all Server Foundation Jira bugs in "New" status every weekday at 09:00 CST. For each bug, a sub-agent analyzes the codebase to find the root cause, then a summary is sent to Slack with `@acm-server-foundation` mention.

**Files added:**
- `workflows/daily-bug-triage.md` — workflow definition (4 phases: collect, analyze, report, distribute)
- `workflows/daily-bug-triage/analyze_bug.md` — sub-agent instructions for codebase analysis
- `workflows/daily-bug-triage/generate_slack_payload.py` — Slack Block Kit payload generator
- `deploy/cronjobs/every-weekday-morning.yaml` — CronJob (Mon-Fri 09:00 CST / 01:00 UTC)

**Design decisions:**
- Sub-agents search `repos/` (read-only submodules) for analysis — no git clone needed
- Analysis supports 4 statuses: root-cause-found, partial-analysis, insufficient-info, error
- Graceful degradation: if analysis fails or info is insufficient, the reason is reported instead of silently skipping

---

## 2026-03-23

### Removed GitHub Projects board and related skills

Removed 5 skills (`sfa-project-{create,update,search,sync,report}`) and `docs/github-projects.md`.

**Why:** Jira is already the team's source of truth for project tracking. The GitHub Projects board (stolostron/projects/9) was a redundant layer — agent tasks almost always map to Jira issues, and maintaining two boards added overhead without clear value. The agent couldn't automatically update board status after completing work, making it a manual burden.

**What replaces it:**
- Team project management → Jira (unchanged)
- Agent session logs → `updates.md`
- Agent progress on Jira issues → `sfa-jira-comment`

### Added updates.md and sfa-session-log skill

Replaced `docs/limitations.md` with `updates.md` — a concise daily development log (tweet-style). Added `sfa-session-log` skill for quick post-session logging.

### Added changelog.md

This file. Records project structural changes and decisions.
