# SF fix CVE (agent-swarm)

Monitor Server Foundation ProsSec vulnerability issues, create or update per-CVE
tracking tasks, run deep multi-branch impact analysis, post findings to Jira, open
**draft PRs** for fixable CVEs, and **close** vulnerability issues classified as
Not Applicable.

Designed for **non-interactive** scheduled or on-demand runs (cron or
`instruction_prompt: CVE-YYYY-NNNNN`). Skill reference:
`.claude/skills/sfa-cve-analysis/SKILL.md`. PR patterns: `prompts/jira-solve.md`.

## SFA conventions

**Working directory:** `/workspace/server-foundation-agent`

| Path | Repository |
|------|------------|
| `/workspace/server-foundation-agent` | `stolostron/server-foundation-agent` (this repo) |

**Jira:** MCP tools only (`search_issues`, `get_issue`, `create_issue`, `add_comment`,
`update_issue`, `transition_issue`). Host `https://redhat.atlassian.net`, project ACM.
Do **not** use Jira CLI. Do **not** use curl for vulnerability issue comments — MCP is
required (REST often returns 404 on ProsSec issues).

**Code access:**

| Location | Use |
|----------|-----|
| `repos/` | Read-only reference (`./repos/sync-repos.sh`) |
| `workspace/` | Writable worktrees for CVE fixes (`sfa-workspace-clone` skill) |

**GitHub:** `gh` for draft PRs. Commits: Conventional Commits + `Signed-off-by` +
`Co-authored-by: server-foundation-agent <sfa-bot@redhat.com>`. Label `sfa-assisted`
after PR create (see `prompts/_sfa-conventions.md`).

**Output dir:** `.output/cve-analysis/` (under working directory)

Extended conventions: `prompts/_sfa-conventions.md`

## Scope

**Default:** all active ProsSec vulnerability issues for Server Foundation.

**Active vulnerability JQL:**

```
project = ACM AND issuetype = Vulnerability AND component = "Server Foundation" AND labels = Security AND status NOT IN (Closed, Done)
```

**Optional `instruction_prompt` CVE filter:** if the text contains `CVE-YYYY-NNNNN`,
analyze that CVE only (include Closed/Done vulnerability issues for that CVE).

**Exclude:** bulk container-scan tickets without a single CVE in the summary (e.g.
`[Server Foundation] … - N HIGH CVEs`) unless `INCLUDE_BULK_SCANS` is set.

## Tracking task conventions

| Field | Value |
|-------|-------|
| Type | Task |
| Project | ACM |
| Component | Server Foundation |
| Summary | `CVE-{cve_id} ({issue_count} issues, {repo_count} repos)` |
| Work type | `10609` (Security & Compliance) — pass numeric ID to MCP `create_issue` |
| Assignee | Prefer Qing Hao; if assign fails, use `rjung@redhat.com` or leave unassigned |
| Description | From `format-cve-tracking-task.py` (never hand-format tables) |

**Existing tracking task JQL** (per CVE):

```
project = ACM AND issuetype = Task AND component = "Server Foundation" AND summary ~ "CVE-{cve_id}"
```

## Dedup between runs

Skip re-analysis for a CVE when **all** are true:

1. An open tracking task exists (`summary ~ "CVE-{cve_id}"`, not Closed/Done), **and**
2. Every active vulnerability issue for that CVE has a comment containing **both**
   `Deep CVE Impact Analysis` and `_— server-foundation-agent_`

If new vulnerability issues appeared since last run, re-run analysis for that CVE and
post comments only on issues missing the signature (do not duplicate on already-commented
issues).

Override: `FORCE_REANALYSIS` in `instruction_prompt` ignores dedup.

## Branch mapping (Jira → git)

Derive target branch from vulnerability issue summary bracket or `target_version`:

| Jira bracket / version | Git branch |
|------------------------|------------|
| `[mce-2.8]` / MCE 2.8.x | `backplane-2.8` |
| `[mce-2.9]` | `backplane-2.9` |
| `[mce-2.10]` | `backplane-2.10` |
| `[mce-2.11]` | `backplane-2.11` |
| `[mce-2.17]` | `backplane-2.17` |
| `[acm-2.13]` / ACM 2.13.x | `release-2.13` |
| `[acm-2.14]` | `release-2.14` |
| (no bracket, mainline) | `main` |

Repos using `release-*` instead of `backplane-*`: `klusterlet-addon-controller`,
`cluster-permission`.

## Workflow

```
Collect → Group by CVE → Tracking tasks → Deep analysis → Jira comments → Remediation → [Slack] → Summary
```

## Phase 1: Collect vulnerability issues

1. `mkdir -p .output/cve-analysis`

2. MCP `search_issues` with active vulnerability JQL (`max_results`: `100`). If
   `instruction_prompt` names a CVE, use:

   ```
   project = ACM AND issuetype = Vulnerability AND component = "Server Foundation" AND labels = Security AND summary ~ "CVE-YYYY-NNNNN"
   ```

3. Write `.output/cve-analysis/vulnerabilities.json` — array of `{key, summary, labels,
   status, priority, created, target_version, url}`.

4. **Early exit:** if zero issues, post minimal Slack ("no active SF CVE issues") when
   `SLACK_WEBHOOK_URL` is set, then stop successfully.

## Phase 2: Group by CVE

1. Extract CVE IDs from each issue summary (`CVE-\d{4}-\d+`) or `CVE-*` labels.

2. Build `.output/cve-analysis/cve_groups.json`:

   ```json
   {
     "CVE-2026-39821": ["ACM-35352", "ACM-35353"],
     "CVE-2026-46595": ["ACM-35339"]
   }
   ```

3. Apply dedup (skip CVEs fully analyzed unless `FORCE_REANALYSIS`). Write
   `.output/cve-analysis/cve_to_process.json` — CVE IDs needing work this run.

## Phase 3: Tracking tasks

For each CVE in `cve_to_process.json`:

### 3.1 Check existing tracker

MCP search:

```
project = ACM AND issuetype = Task AND component = "Server Foundation" AND summary ~ "CVE-{cve_id}" AND status NOT IN (Closed, Done)
```

If found → record `tracking_key` in `.output/cve-analysis/tracking/{cve_id}.json`.
Skip creation.

### 3.2 Generate description (required script)

Fetch vulnerability issues for the CVE via MCP, save REST-shaped JSON for the script:

```bash
# Build issues payload from MCP results into .output/cve-analysis/issues-{cve_id}.json
# Must be {"issues": [{"key", "fields": {summary, labels, versions, status, priority, created}}]}

python3 .claude/skills/sfa-cve-analysis/format-cve-tracking-task.py \
  .output/cve-analysis/issues-{cve_id}.json \
  {cve_id} \
  > .output/cve-analysis/description-{cve_id}.txt
```

Parse counts from description header (`Total Related Issues`, repo count from
`**Repository:` lines).

### 3.3 Create tracking task (if missing)

MCP `create_issue`:

- `project_key`: ACM
- `issue_type`: Task
- `components`: ["Server Foundation"]
- `summary`: `CVE-{cve_id} ({issue_count} issues, {repo_count} repos)`
- `description`: contents of `description-{cve_id}.txt`
- `work_type`: `10609`
- `assignee`: try Qing Hao account; on failure use `rjung@redhat.com`

Record new `tracking_key`.

## Phase 4: Deep impact analysis

Run for **every** CVE in `cve_to_process.json` (non-interactive — do not ask the user).

### 4.1 CVE metadata

WebSearch / pkg.go.dev vuln DB for each CVE:

- Affected package and version range
- Fixed version
- Brief description

Save to `.output/cve-analysis/cve-meta-{cve_id}.json`.

### 4.2 Clone and analyze branches

Use temp dir `/tmp/cve-analysis/repos` (or `.output/cve-analysis/repos`).

**Repositories** — derive from vulnerability issues for this CVE (via script output
or pscomponent labels). Common SF repos:

| Repository | Branches |
|------------|----------|
| stolostron/ocm | main, backplane-2.17, backplane-2.11, backplane-2.10, backplane-2.9, backplane-2.8 |
| stolostron/clusterlifecycle-state-metrics | main, backplane-2.17, backplane-2.11, backplane-2.10, backplane-2.9, backplane-2.8 |
| stolostron/multicloud-operators-foundation | main, backplane-2.17, backplane-2.11, backplane-2.10, backplane-2.9, backplane-2.8 |
| stolostron/managed-serviceaccount | main, backplane-2.17, backplane-2.11, backplane-2.10, backplane-2.9, backplane-2.8 |
| stolostron/cluster-proxy-addon | main, backplane-2.17, backplane-2.11, backplane-2.10, backplane-2.9, backplane-2.8 |
| stolostron/cluster-proxy | main, backplane-2.17, backplane-2.11, backplane-2.10, backplane-2.9, backplane-2.8 |
| stolostron/managedcluster-import-controller | main, backplane-2.17, backplane-2.11, backplane-2.10, backplane-2.9, backplane-2.8 |
| stolostron/klusterlet-addon-controller | main, release-2.17, release-2.16, release-2.15, release-2.14, release-2.13 |
| stolostron/cluster-permission | main, release-2.17, release-2.16, release-2.15, release-2.14, release-2.13 |

Per repo/branch:

1. `git fetch origin {branch} --depth 1` and checkout
2. Read `go.mod` for `golang.org/x/net`, `golang.org/x/crypto`, Go version
3. `go mod why` for affected package (e.g. `golang.org/x/net/idna`, `golang.org/x/crypto/ssh`)
4. Grep for direct usage (`idna`, `ssh.NewServerConn`, `ssh.ServerConfig`)
5. Classify impact:
   - ❌ Vulnerable / ⚠️ Potentially Vulnerable / ✅ Not Vulnerable / ➖ Not Applicable

**Older-branch upgrades:** follow `solutions/older-branch-dep-upgrade.md` for fix
recommendations (minimal `go get`, avoid OCM dep tier jumps).

Write report: `.output/cve-analysis/deep-analysis-{cve_id}.md`

## Phase 5: Post Jira comments

Use **Jira wiki markup** (see `docs/jira/formatting.md`). Footer on every comment:

```
----
_— server-foundation-agent_
```

Convert markdown reports with `h2.` / `h3.` headings, `*bold*`, `{{monospace}}`,
`||table||` rows.

### 5.1 Tracking task

MCP `add_comment` on `tracking_key` with **full** deep analysis report from
`deep-analysis-{cve_id}.md`.

### 5.2 Individual vulnerability issues

For each issue key in the CVE group, MCP `add_comment` with a **component-specific**
summary:

- Issue key, repository, branch (from JIRA target version / summary bracket)
- Installed dependency version vs fix version
- Impact assessment (one line)
- Remediation command (`go get …`)
- Link to tracking task: `[ACM-XXXXX|https://redhat.atlassian.net/browse/ACM-XXXXX]`

Skip issues that already have the dedup signature (unless `FORCE_REANALYSIS`).

## Phase 6: Remediation actions

Run after Phase 5 unless `SKIP_REMEDIATION` is set. Non-interactive — do not ask the
user.

Write `.output/cve-analysis/remediation.json` — array of action records:

```json
{
  "cve_id": "CVE-2026-46595",
  "issue_key": "ACM-35339",
  "repo": "stolostron/ocm",
  "branch": "backplane-2.8",
  "impact": "Not Applicable",
  "action": "closed",
  "pr_url": null,
  "notes": "go mod why shows ssh package not needed"
}
```

`action` values: `pr_opened`, `closed`, `skipped_already_fixed`, `skipped_existing_pr`,
`failed`.

### 6.1 Build remediation plan

From `deep-analysis-{cve_id}.md`, map each **active** vulnerability issue to:

- Repository (pscomponent label or summary image path → repo name)
- Target branch (branch mapping table above)
- Per-issue impact from deep analysis for that repo/branch

**Group fixes:** one draft PR per `(repo, branch, CVE)` — not one PR per container-image
ticket. Link all related vulnerability issue keys in the PR body and Jira comments.

### 6.2 Not Applicable → close Jira

When deep analysis classifies the issue's repo/branch as **➖ Not Applicable**:

1. MCP `add_comment` on the vulnerability issue (skip if comment already contains
   `CVE Remediation: Not Applicable` and `_— server-foundation-agent_` unless
   `FORCE_REANALYSIS`):
   - Evidence: `go mod why` output, grep results, why the vulnerable API is unused
   - Statement: issue closed as not applicable to this component/branch
2. MCP `transition_issue`:
   - If status is New/To Do → try `In Progress` first when available
   - Then transition to **Closed** (or **Resolve** then **Close** if the workflow
     requires two steps)
   - If transition fails, record `action: failed` with error; do **not** retry blindly
3. Record each closed issue in `remediation.json`
4. MCP `add_comment` on the tracking task summarizing closed keys for this CVE

**Guardrail:** close **only** when classification is Not Applicable with documented
evidence in the comment. Never close ❌ Vulnerable or ⚠️ Potentially Vulnerable issues.

### 6.3 Already fixed → skip PR

When classification is **✅ Not Vulnerable** (installed version ≥ fix version):

- Ensure Phase 5 comment documents the evidence
- Record `action: skipped_already_fixed` in `remediation.json`
- Do **not** close automatically (human/QE may still want scan ticket cleanup)

### 6.4 Vulnerable / Potentially Vulnerable → draft PR

When classification is **❌ Vulnerable** or **⚠️ Potentially Vulnerable**:

1. **Dedup PR:** search for an open PR on the repo with branch/title containing
   `{cve_id}` or `{cve_id lower}`; if found → record `skipped_existing_pr`, link PR in
   tracking-task comment, for each linked issue transition New → **In Progress** →
   **Review** when still before Review (see step 8), then skip new PR
2. **Start work in Jira** — for each linked vulnerability issue (MCP `transition_issue`):
   - If status is **In Progress**, **Review**, or later → skip
   - Otherwise transition to **In Progress** (transition name may be `Start Progress`)
   - If transition fails: MCP `add_comment` with the error, record `action: failed`,
     skip PR for this `(repo, branch, CVE)` group
3. **Clone worktree:**
   ```bash
   bash .claude/skills/sfa-workspace-clone/clone-worktree.sh \
     --new <org/repo> cve-<CVE-ID>-<branch-suffix> --base <branch>
   ```
   Example: `--base backplane-2.8` → branch `cve-CVE-2026-39821-backplane-2-8`
4. **Apply minimal fix** per `solutions/older-branch-dep-upgrade.md`:
   - Prefer `go get <module>@<fix-version>` (and `go mod tidy`)
   - Run `go mod vendor` when the repo vendors dependencies
   - Avoid OCM dependency tier jumps; use `replace` only when the SOP requires it
5. **Verify** in the worktree (sequential, allow ≥ 5 min):
   ```bash
   make check
   make test
   ```
   Fix failures from your changes; record failure if tests cannot pass after reasonable
   effort
6. **Commit and push:**
   ```bash
   git commit -s -m "$(cat <<'EOF'
   fix(security): bump <module> for <CVE-ID>

   Co-authored-by: server-foundation-agent <sfa-bot@redhat.com>
   EOF
   )"
   git push origin HEAD
   ```
7. **Draft PR:**
   ```bash
   gh pr create --draft --repo <org/repo> \
     --title "<CVE-ID>: bump <module> on <branch>" \
     --body "$(cat <<'EOF'
   ## CVE
   <CVE-ID> — <one-line description>

   ## Jira
   - https://redhat.atlassian.net/browse/ACM-XXXXX
   (list all linked vulnerability keys)

   ## Summary
   <go get command and version change>

   ## Test plan
   - [x] make check
   - [x] make test

   ---
   *Created with [server-foundation-agent](https://github.com/stolostron/server-foundation-agent)*
   EOF
   )"
   gh pr edit <PR-NUMBER> --repo <org/repo> --add-label "sfa-assisted"
   ```
8. **Jira updates** for each linked vulnerability issue:
   - MCP `add_comment` with PR URL, fix summary, and signature footer
   - MCP `update_issue` — set `git_pull_requests` to the PR URL when the field is
     supported (best effort)
   - MCP `transition_issue` to **Review** when available (transition name may be
     `Request Review` or `Review`); skip if already Review or later; record transition
     failure in `remediation.json` notes but do not revert the PR
9. MCP `add_comment` on tracking task — PR table for this CVE
10. Record `action: pr_opened` with `pr_url` in `remediation.json`

**Limit:** at most **one new PR per repo/branch/CVE** per run. Defer extra branches to
the run summary as human follow-ups.

### 6.5 Remediation report

Write `.output/cve-analysis/remediation-report.md` with:

- PRs opened (URL, repo, branch, linked JIRA keys)
- Issues closed as Not Applicable (keys + one-line rationale)
- Skipped (already fixed, existing PR)
- Failures (PR create, transition, tests)

Post the remediation summary (or link to full report) as MCP `add_comment` on each
tracking task processed this run.

## Phase 7: Slack (optional)

If `SLACK_WEBHOOK_URL` is set and not `SKIP_SLACK`, post a digest:

- CVEs processed this run
- New tracking tasks created (keys + links)
- Count of vulnerability issues commented
- Draft PRs opened (count + links from `remediation.json`)
- Vulnerability issues closed as Not Applicable (count + keys)
- Remediation failures (if any)

Use `bash .claude/skills/sfa-slack-notify/send_to_slack.sh` with a JSON payload under
`.output/cve-analysis/slack_payload.json`, or post a simple text block via the webhook.

## Final summary

Report in session output:

- Vulnerability issues found / CVEs grouped / CVEs skipped (dedup)
- Tracking tasks created vs reused
- Deep analyses completed
- Jira comments posted (tracking + per-issue counts)
- **Remediation:** draft PRs opened (table: PR URL, repo, branch, linked keys)
- **Remediation:** vulnerability issues closed as Not Applicable (table: key, rationale)
- Remediation skipped / failed counts from `remediation.json`
- Failures (assignee, MCP, clone, missing branches, PR push, Jira transition)
- Recommended human follow-ups (remaining branches, mark PRs ready, `/ok-to-test`)

## instruction_prompt overrides

| Text | Effect |
|------|--------|
| `CVE-YYYY-NNNNN` | Analyze only that CVE (all statuses) |
| `FORCE_REANALYSIS` | Ignore dedup; repost all comments |
| `SKIP_DEEP_ANALYSIS` | Tracking tasks only (Phases 1–3) |
| `SKIP_REMEDIATION` | Analysis + Jira comments only (skip Phase 6) |
| `SKIP_SLACK` | Skip Phase 7 |
| `INCLUDE_BULK_SCANS` | Include multi-CVE scanner tickets |

## Do not

- Ask the user for confirmation (automated mode)
- Hand-format tracking task repository tables (always use the script)
- Use curl REST for comments on vulnerability issues
- Create duplicate tracking tasks for the same CVE
- Mark draft PRs ready for review or merge them
- Close vulnerability issues unless classification is **Not Applicable** with evidence
- Open more than one PR per `(repo, branch, CVE)` per run
- Cascade major dependency upgrades on older branches (follow the older-branch SOP)
