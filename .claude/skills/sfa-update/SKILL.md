---
name: sfa-update
description: "Log a session summary to updates.md. Use this skill after completing a session to record what was done, issues encountered, limitations discovered, and any notes. Trigger phrases: 'log session', 'session summary', 'update log', 'record session', 'write update', 'add update', 'session log', 'log update'."
---

# Update Log

Append a concise session summary to `updates.md` in the project root.

## CRITICAL: Brevity Rule

Each entry MUST be extremely concise — like a tweet. Strip all details, keep only the core. No sub-sections, no bold labels, no verbose descriptions. Just bullet points stating what happened.

**Bad:** "**QE Jenkins platform inaccessible** — URL: `https://...`. When QE reports bugs, they often include links to detailed error logs on this internal Jenkins instance. The agent cannot access these logs because the platform sits behind Red Hat's corporate VPN..."

**Good:** "Agent cannot access QE Jenkins (`*.dno.corp.redhat.com`) — behind VPN. Workaround: users paste logs manually."

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| content | No | - | User-provided description. If omitted, agent auto-summarizes the session. |

## Workflow

### Step 1: Read updates.md

Check today's date. If today's heading (`## YYYY-MM-DD`) exists, append bullets under it. Otherwise, add a new date heading.

### Step 2: Distill to core points

Whether from user input or auto-summary, compress to the minimum:
- What was done (1 line per item)
- Issues hit (1 line per issue)
- Limitations found (1 line per limitation)

Skip categories with nothing to say. No headers like "What was done:" — just write the bullets.

### Step 3: Append to updates.md

**If today's date heading exists** — add bullets under it:

```markdown
- Fixed X in PR #42. Hit flaky CI test, retried.
- Discovered agent can't access Brew builds behind VPN.
```

**If today's date heading does NOT exist** — add new section with commit range:

```markdown

## YYYY-MM-DD (`<first-commit>...<latest-commit>`)

- Fixed X in PR #42. Hit flaky CI test, retried.
- Discovered agent can't access Brew builds behind VPN.
```

To get the commit range, run:
```bash
git log --oneline --since="YYYY-MM-DDT00:00:00" --until="YYYY-MM-DDT23:59:59"
```
Use the oldest and newest commit short hashes from today. If no commits exist, omit the parenthetical.

### Step 4: Confirm

Show the added bullets to the user.

## Examples

```
/sfa-update
/sfa-update Fixed cluster-permission RBAC issue in PR #42. Hit flaky CI test.
/sfa-update Discovered agent cannot access Brew builds behind VPN.
Log this session
Write an update
```
