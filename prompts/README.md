# Agent-swarm prompts

Model-agnostic workflow prompts for [agent-swarm](https://github.com/stolostron/agent-swarm)
(OpenCode/Crush). Sync this folder as a **Prompt Source** in a Swarmer workspace.

These are the runnable, self-contained specs for scheduled SFA automation.
Detailed phase docs and scripts live under `workflows/` — prompts embed what the
agent needs in a single injected file per run.

## Jira automation model

Two-stage SF Jira automation:

![SF Jira automation model](../docs/assets/jira-automation-model.png)

- **[daily-bug-triage.md](daily-bug-triage.md)**: triage only; auto-fix stays **off** unless `ENABLE_AUTO_FIX` is set (unchanged).
- **[jira-pipeline.md](jira-pipeline.md)**: the **only** scheduled auto-fix path; runs only when a human has added `issue-for-agent` after triage.

### Details

| Stage | Schedule | Auto-fix |
|-------|----------|----------|
| Triage | Weekdays 09:00 | **Off** unless `ENABLE_AUTO_FIX` |
| Fix | Weekdays 09:00 and 17:00 | **On** for `issue-for-agent` issues only |

**Labels:** `agent-triaged` (triage done) · `issue-for-agent` (human opt-in) · `agent-processed` (pipeline completed)

**Grooming:** triage → human adds `issue-for-agent` → pipeline fixes one issue → `agent-processed`. To retry: remove `agent-processed`, keep `issue-for-agent`.

Agent queue JQL and extended docs: [`_sfa-conventions.md`](_sfa-conventions.md)

## Prompt map

| File | Agent-swarm session | Schedule (example) |
|------|---------------------|-------------------|
| `daily-bug-triage.md` | `sfa-daily-bug-triage` | `0 9 * * 1-5` (weekdays 09:00 Asia/Shanghai) |
| `daily-bug-triage-analyze.md` | spawned by triage orchestrator | — |
| `jira-pipeline.md` | `sfa-jira-pipeline` | `0 9,17 * * 1-5` (weekdays 09:00 and 17:00 Asia/Shanghai) |
| `jira-solve.md` | `sfa-jira-solve` | On-demand + `instruction_prompt: ACM-12345` |

Triage also references helper scripts under `workflows/daily-bug-triage/` and optional
long-form docs in `workflows/daily-bug-triage.md`.

## Conventions

Each orchestrator prompt embeds an **SFA conventions** section (self-contained for
agent-swarm). Extended reference: `prompts/_sfa-conventions.md`.

## Workspace layout

| Clone path | Repository |
|------------|------------|
| `/workspace/server-foundation-agent` | `stolostron/server-foundation-agent` |

**Working directory:** `/workspace/server-foundation-agent`

Optional: pre-sync `repos/` in the workspace PVC or run `./repos/sync-repos.sh` at
the start of triage.

## MCP

Enable workspace **Jira MCP** (`jira-mcp-server` / Atlassian catalog). Prefer MCP
for search and comments; Python scripts under `workflows/daily-bug-triage/` are
fallbacks when MCP cannot post or read comments.

Setup: sync this folder as a **Prompt Source** in a Swarmer workspace — see
[agent-swarm](https://github.com/stolostron/agent-swarm).
