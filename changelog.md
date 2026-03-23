# Server Foundation Agent - Changelog

Project changes, architectural decisions, and the reasoning behind them. Each entry records what changed, why, and what it replaces.

**Format:** `## YYYY-MM-DD` heading, then entries with a brief title and explanation.

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
