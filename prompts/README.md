# Agent-swarm prompts

Model-agnostic workflow prompts for [agent-swarm](https://github.com/stolostron/agent-swarm)
(OpenCode/Crush). Sync this folder as a **Prompt Source** in a Swarmer workspace.

These are the runnable, self-contained specs for scheduled SFA automation.
Detailed phase docs and scripts live under `workflows/` — prompts embed what the
agent needs in a single injected file per run.

## Prompt map

| File | Workflow reference | Agent-swarm session | Schedule (example) |
|------|-------------------|---------------------|-------------------|
| `daily-bug-triage.md` | `workflows/daily-bug-triage.md` | `sfa-daily-bug-triage` | `0 9 * * 1-5` (weekdays 09:00 Asia/Shanghai) |
| `daily-bug-triage-analyze.md` | `workflows/daily-bug-triage/analyze_bug.md` | spawned by triage orchestrator | — |

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

## KubeOpenCode parity

CronTasks under `deploy/crontasks/` may reference `workflows/*.md` for the
always-on agent. Agent-swarm sessions should use these `prompts/` files instead.

Setup: [deploy/README.md](../deploy/README.md)

## Claude Code parity

| Agent-swarm prompt | Claude Code / KubeOpenCode |
|--------------------|---------------------------|
| `daily-bug-triage.md` | `workflows/daily-bug-triage.md`, CronTask `daily-bug-triage` |
| `daily-bug-triage-analyze.md` | `workflows/daily-bug-triage/analyze_bug.md` |
