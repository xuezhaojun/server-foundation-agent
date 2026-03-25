# Solutions

Solutions are the agent's **"错题本" (error correction notebook)** — a collection of battle-tested SOPs for problems the agent has encountered before.

Just like a student flips through their error notebook when stuck on a similar problem, the agent searches `solutions/` when it hits a blocker. It extracts keywords from the error context, matches them against solution descriptions, and follows the proven fix if one exists.

**Key traits:**
- **Passive trigger** — not read proactively; only consulted when the agent gets stuck
- **Experience-driven** — each solution captures a real problem that was hard to solve, along with the verified fix
- **Keyword matching** — the agent extracts error signatures and searches this directory, just like looking up a similar problem in a notebook

> **How solutions differ from skills and workflows:**
>
> | Layer | Analogy | Who initiates |
> |-------|---------|---------------|
> | **Skills** | Basic toolkit | Called by upper layers |
> | **Workflows** | Exam procedures / SOP | Human says "start" |
> | **Solutions** | Error correction notebook | Agent self-consults when stuck |
>
> See also: [Workflows](../workflows/README.md) (user-triggered or scheduled processes), [Skills](../.claude/skills/README.md) (reusable atomic capabilities).

## Solution Catalog

| Solution | Description |
|----------|-------------|
| [older-branch-dep-upgrade](older-branch-dep-upgrade.md) | CVE-driven dependency upgrades on older release branches |
| [ocm-dependency-versions](ocm-dependency-versions.md) | OCM upstream dependency version survey and analysis |
| [import-klusterlet-validation-error](import-klusterlet-validation-error.md) | ManagedCluster import stuck due to kubectl/oc version incompatibility with Klusterlet CRD |
| [clock-sync-kind-cluster-limitation](clock-sync-kind-cluster-limitation.md) | Cannot test clock sync issues with kind clusters — must use OCP hub + macOS time change |
| [cluster-proxy-websocket-403](cluster-proxy-websocket-403.md) | Console WebSocket to cluster-proxy returns 403 due to stripped Host/Origin headers |
| [cluster-proxy-addon-restore-failure](cluster-proxy-addon-restore-failure.md) | cluster-proxy-addon fails after backup/restore due to customized CSR signer missing hub-config |

## Adding a New Solution

A good solution candidate is a problem that:
- Took significant effort to diagnose or fix
- Is likely to recur (e.g., on other repos, other branches, future upgrades)
- Has a non-obvious root cause or fix that the agent would struggle to rediscover

### Required Frontmatter

Every solution file **MUST** include YAML frontmatter for agent discoverability and lifecycle management:

```yaml
---
title: Short descriptive title of the problem
symptom: "Exact error message or observable behavior (grep-friendly)"
keywords: [keyword1, keyword2, keyword3]  # terms the agent matches against
affected_versions: "ACM 2.4-2.6"          # version range where this applies
last_verified: 2025-11-15                  # last date this solution was confirmed working
status: active                             # active | deprecated
---
```

| Field | Purpose | Who updates |
|-------|---------|-------------|
| `title` | Human-readable problem name | Author at creation |
| `symptom` | Exact error string — agent greps for this | Author at creation |
| `keywords` | Grep-friendly terms (error codes, component names, tool names) | Author; agent may append |
| `affected_versions` | Agent checks if current task version falls in range | Author; agent updates when verified on new versions |
| `last_verified` | Staleness indicator — solutions older than 6 months get lower trust | **Agent auto-updates** after successful use |
| `status` | `active` = usable, `deprecated` = kept for history but skipped | Human or staleness workflow |

### Required Body Structure

```markdown
## Symptom
What the error looks like — exact error messages, failing commands, observable behavior.
Include enough literal text for grep matching.

## Root Cause
Why it happens — the non-obvious explanation.

## Fix
Step-by-step resolution. Include commands, code snippets, or config changes.

## References
Links to Jira issues, PRs, Slack threads, or docs (optional but recommended).
```

### Solution Lifecycle

Solutions follow a natural lifecycle — no manual maintenance required:

1. **Creation** — author writes the solution with `last_verified: <today>` and `status: active`
2. **Auto-renewal** — when the agent successfully uses a solution to fix a problem, it updates `last_verified` to the current date
3. **Staleness detection** — a periodic workflow scans for solutions with `last_verified` older than 6 months and generates a report for human review
4. **Deprecation** — human sets `status: deprecated` for solutions that no longer apply (e.g., the bug was fixed upstream). Deprecated solutions remain in the directory for historical reference but the agent skips them.

### Steps

1. Create `solutions/<solution-name>.md` with the frontmatter and body structure above
2. Update the Solution Catalog table above
3. Open a PR
