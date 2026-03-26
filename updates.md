# Server Foundation Agent - Updates

Daily development log. Each day's entry covers what changed, why, and any thoughts or discoveries along the way.

Use `/sfa-update` to append entries after each session.

**Format:** `## YYYY-MM-DD` heading, then bullet points. For significant architectural decisions, add a brief "Why / What it replaces" note (2-3 lines max) right after the bullet.

---

## 2026-03-26 (`cf83647...200c538`)

- **Migrated repos/ from git submodules to YAML-driven shallow clones.**
  *Design principle: "less structure, more intelligence."* Previously, repos were linked via git submodules — a hard structural coupling that caused maintenance friction (noisy git status, submodule pointer commits, complex add/remove workflows). Now repos are described in `repos/repos.yaml` and cloned by `repos/sync-repos.sh`. The agent reads the YAML to understand repo taxonomy (categories, orgs, descriptions) instead of relying on git's submodule machinery. Adding a new repo is just one YAML entry instead of `git submodule add` + commit. This also consolidates all repos-related files (`repos.yaml`, `sync-repos.sh`) into the `repos/` directory itself.

## 2026-03-26 (`cf83647...8391383`) (earlier session)

- Added `docs/dependencies.md` — full agent dependency inventory: CLI binaries, credentials, runtimes, per-skill KUBECONFIG targets.
- Added `sfa-cve-analysis` skill (#9), `sfa-bug-analyze` + `sfa-bug-reproduce` + `install-acm` + `uninstall-acm` skills (#7).
- Added `sfa-jira-inbox` skill (#8).
- Fixed daily-scrum: deterministic changelog fetch, sprint board column alignment, AI-driven sprint insights.
- Fixed jira-triage: exclude Konflux auto-created bugs.
- Added `clusteradm` submodule from open-cluster-management-io.
- Clarified per-skill KUBECONFIG targets: cluster-pools uses fixed collective cluster, install/uninstall/bug-reproduce use user-specified clusters.

## 2026-03-25 (`08fe928..d32af50`)

- Added **sfa-cluster-pools** and **sfa-prow-config** skills (#6).
- Added **server-mode agent** (`server-foundation-agent-live`) for cluster deployment.
- Added **daily scrum prep workflow**.
- Added **error-notebook framework** (`solutions/`) with 4 new solutions (cluster-proxy-websocket-403, cluster-proxy-addon-restore-failure, import-klusterlet-validation-error, clock-sync-kind-cluster-limitation).
- Added **sfa-solution-add** skill for recording new solutions.
- Renamed weekly-bot-pr-report → weekly-bot-pr-cleanup → weekly-bot-pr-hygiene.
- Clarified workflows vs solutions distinction in docs.
- Clarified repos/ (read-only) vs workspace/ (write) usage in CLAUDE.md.
- Refined triage skill: replaced verbose Cause/Fix with short summary in Slack output.
- Monitored flaky e2e on PR stolostron/multicloud-operators-foundation#1229 — cluster-proxy "No agent available" tunnel flake, auto-retested.

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
- Added `updates.md` and `sfa-update` skill, replacing `docs/limitations.md`.
