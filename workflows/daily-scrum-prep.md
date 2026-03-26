# Daily Scrum Prep Workflow

Data-driven daily standup preparation for the Server Foundation team. Analyzes the current sprint using
professional Agile/Scrum metrics and delivers actionable coaching recommendations before each standup.

## Trigger Phrases

- `daily scrum prep`, `standup prep`, `scrum preparation`
- `sprint health check`, `sprint coaching`

## Key Metrics

| Metric | What It Measures | Why It Matters |
|--------|-----------------|----------------|
| **Commitment Completion Rate** | % of sprint-start issues now Done | Are we overcommitting? |
| **Scope Change Rate** | Issues added/removed after sprint start | Is scope being protected? |
| **Cycle Time** | Days from In Progress → Done | How fast do items flow? |
| **Review Bottleneck** | Issues stuck in Review | Where is the pipeline clogged? |
| **WIP Balance** | In Progress items per person | Are people overloaded? |
| **Sprint Burndown** | Done % vs elapsed % | Are we on track? |

## Workflow Phases

```
Phase 1: Collect       →  Phase 2: Compute Metrics  →  Phase 3: Agent Analysis  →  Phase 4: Distribute
query Jira sprint         cycle time, scope change,     AI insights + autonomous     Slack notification
issues + changelogs       commitment rate, WIP           Jira investigation
```

---

## Phase 1: Collect Sprint Data

### 1.1 Fetch Current Sprint Issues

```bash
mkdir -p .output/scrum-prep

curl -s -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = ACM AND component = \"Server Foundation\" AND sprint = \"<SPRINT_NAME>\" ORDER BY assignee ASC, status ASC",
    "fields": ["issuetype","summary","status","priority","assignee","customfield_10020","created"],
    "maxResults": 200
  }' \
  "https://redhat.atlassian.net/rest/api/3/search/jql" > .output/scrum-prep/sprint_issues_raw.json
```

**Sprint name discovery**: First query any SF issue with `sprint IN openSprints()` and extract the active sprint whose name starts with `SF-Sprint-` from `customfield_10020`. Use that name for the main query.

### 1.2 Extract Sprint Metadata

From the sprint field (`customfield_10020`), extract:
- Sprint name, start date, end date
- Calculate: elapsed days, remaining days, elapsed percentage

### 1.3 Fetch Changelogs for In-Progress and Done Issues

For cycle time and scope change detection, fetch changelogs for issues that have been worked on (status != New/Backlog):

```bash
# For each issue key that is not in New/Backlog status:
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/2/issue/<KEY>?expand=changelog&fields=status" \
  | jq '{
    key: .key,
    status: .fields.status.name,
    status_transitions: [.changelog.histories[] | {
      created: .created,
      items: [.items[] | select(.field == "status") | {from: .fromString, to: .toString}]
    } | select(.items | length > 0)],
    sprint_changes: [.changelog.histories[] | {
      created: .created,
      items: [.items[] | select(.field == "Sprint") | {from: .fromString, to: .toString}]
    } | select(.items | length > 0)]
  }'
```

**Performance note**: Changelogs require per-issue API calls. To stay within rate limits, batch up to 10 concurrent requests using `xargs -P10` or sequential calls with no delay (Jira Cloud allows ~10 req/s).

### 1.4 Early Exit

If the sprint query returns 0 issues (no active sprint), send a "no active sprint" Slack message and exit.

---

## Phase 2: Compute Metrics

Run the metrics computation script:

```bash
python3 workflows/daily-scrum-prep/compute_metrics.py \
  .output/scrum-prep/sprint_issues_raw.json \
  .output/scrum-prep/changelogs/ \
  .output/scrum-prep/metrics.json
```

### Metric Definitions

#### 2.1 Commitment Completion Rate

```
committed_issues = issues whose earliest sprint_change to this sprint <= sprint_start_date + 1 day
completed_issues = committed_issues with status in (Closed, Resolved)
commitment_rate = completed_issues / committed_issues * 100
```

**Benchmark**: Healthy teams target 80-90%. Below 70% signals overcommitment.

#### 2.2 Scope Change Rate

```
total_current = all issues in sprint now
added_after_start = issues whose first sprint_change to this sprint > sprint_start_date + 1 day
removed_from_sprint = issues with sprint_change removing this sprint (detected from changelogs)
scope_change_rate = (added_after_start + removed_from_sprint) / total_current * 100
```

**Benchmark**: Below 10% is excellent. Above 20% indicates planning problems.

#### 2.3 Cycle Time (days)

For each issue that transitioned to Done status during this sprint:

```
cycle_time = date(status → Done) - date(status → In Progress)
```

Report: median, average, p90 cycle time.

**Benchmark**: For a 3-week sprint, median cycle time should be 3-5 days.

#### 2.4 Review Bottleneck

```
in_review = count of issues with status "Review" or "Code Review"
review_age = days since each issue entered Review status (from changelog)
```

Flag issues in Review for > 2 days.

#### 2.5 WIP per Member

```
For each assignee:
  wip_count = issues with status "In Progress"
  review_count = issues with status "Review"
```

**Benchmark**: WIP limit should be 2-3 per person. Above 3 signals context switching.

#### 2.6 Sprint Burndown Position

```
elapsed_pct = (today - sprint_start) / (sprint_end - sprint_start) * 100
done_pct = issues_done / total_issues * 100
burndown_gap = elapsed_pct - done_pct
```

**Interpretation**:
- Gap < 5%: On track
- Gap 5-15%: Slightly behind, manageable
- Gap > 15%: At risk, needs intervention

---

## Phase 3: Agent-Driven Sprint Analysis

This phase combines **rule-based alerts** (deterministic, from Phase 2) with **AI-generated insights** (contextual, generated by the agent). Rule-based recommendations handle obvious threshold violations. The agent provides analysis that an experienced agile coach would give — understanding issue content, team dynamics, priority urgency, and workflow patterns.

### 3.1 Rule-Based Recommendations (automatic)

Computed by `compute_metrics.py` in Phase 2. These are deterministic alerts:
- Sprint burndown at risk (gap > 15%)
- Review bottleneck (> 5 items or items stuck > 2 days)
- WIP overload (> 3 items per person)
- Scope change (> 20%)
- Critical/Blocker items not started
- Commitment rate < 50% past sprint midpoint
- Cycle time exceeding target

These appear in the **"Action Required"** section of the Slack message.

### 3.2 AI Sprint Insights (agent-generated)

**Step 1 — Load initial data:**
- `.output/scrum-prep/metrics.json` — computed metrics and rule-based recommendations
- `.output/scrum-prep/agent_context.json` — per-member issue details, risk signals, days in status

**Step 2 — Autonomous investigation:**

The agent should NOT be limited to the pre-computed data. When the initial analysis raises questions, the agent should **proactively query Jira** for deeper context:

| Signal from initial data | Follow-up investigation |
|---|---|
| Issue stuck in same status > 5 days | Fetch issue comments to check for blockers or discussion |
| High-priority item not started | Check if it has linked/blocking issues, or if assignee has other urgent work |
| Member has unusual pattern (0 WIP, many backlog) | Check member's recent Jira activity — are they on PTO or working on non-sprint items? |
| Items bouncing between statuses | Fetch full changelog to understand the back-and-forth pattern |
| Related issues in Review from same component | Check if there's a parent epic connecting them |

**Jira queries the agent can make:**

```bash
# Fetch comments on a specific issue
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/3/issue/<KEY>/comment" | jq '.comments[-3:]'

# Check linked issues
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://redhat.atlassian.net/rest/api/3/issue/<KEY>?fields=issuelinks,parent" | jq '{links: .fields.issuelinks, parent: .fields.parent}'

# Check a member's recent activity (last 7 days)
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jql": "assignee = \"<NAME>\" AND updated >= -7d ORDER BY updated DESC", "fields": ["summary","status","updated"], "maxResults": 10}' \
  "https://redhat.atlassian.net/rest/api/3/search/jql"
```

The agent should limit follow-up queries to **at most 10 API calls** to stay within time/rate constraints.

**Step 3 — Generate insights:**

Analyze all collected data as a **senior agile coach**. Generate insights that simple threshold rules cannot produce.

**Analysis dimensions:**

1. **Issue content awareness** — Read summaries to understand the actual work. Group related issues (e.g., "3 of Le Yang's 5 review items are all cluster-proxy cert fixes — batch review would be efficient"). Use linked issues to identify dependency chains.

2. **Priority vs. progress alignment** — Are high-priority items progressing faster than low-priority ones? If a Blocker is in Backlog while Normal items are In Progress, flag the misalignment with specific issue keys and suggested action.

3. **Per-member coaching** — For each member with notable patterns, provide a specific, actionable suggestion. Use investigation findings to add context (e.g., "Jian Qiu's 2 review items have no reviewer comments yet — assign reviewers" rather than just "items stuck in review").

4. **Flow bottleneck analysis** — Look beyond counts. If most Review items share a component, suggest a themed review session. If items bounce between statuses (high transition count), check comments for unclear requirements.

5. **Sprint trajectory** — Based on burndown gap and remaining days, assess what's realistically achievable. Name specific items to prioritize vs. defer.

**Output:**

Write insights to `.output/scrum-prep/agent_insights.json`:

```json
{
  "team_insights": [
    "5 of 8 review items are cluster-proxy related — a focused 30-min session between Le Yang and Zhiwei could clear the bottleneck.",
    "ACM-31402 (Blocker) has been in New for 8 days. Comments show it's blocked by an upstream OCM API change (linked to ocm-io#423). Escalate to OCM maintainers.",
    "Sprint is 70% elapsed with 45% done. Realistically 4-5 more items can close — prioritize ACM-31100 and ACM-31205 (both in Review, close to done)."
  ],
  "member_insights": [
    {"member": "Le Yang", "insight": "5 items in Review, 3 are cluster-proxy cert fixes. Ask Zhiwei Yin to batch-review these today."},
    {"member": "Jian Qiu", "insight": "2 items in Review for 5+ days — no reviewer comments found. Assign specific reviewers to unblock."},
    {"member": "Qing Hao", "insight": "2 in progress, 1 not started (Critical). Finish current work before the Critical item ages further."}
  ]
}
```

**Constraints:**
- Maximum 5 team insights, 1 insight per member (only members with notable patterns)
- Each insight must reference specific issue keys when relevant
- Be concise — 1-2 sentences per insight
- Be actionable — suggest a specific action, not just describe a problem
- Don't repeat what the rule-based recommendations already say
- Limit follow-up Jira queries to 10 API calls max

---

## Phase 4: Generate Slack Payload & Distribute

### 4.1 Generate Slack Payload

```bash
python3 workflows/daily-scrum-prep/generate_slack_payload.py \
  .output/scrum-prep/metrics.json \
  .output/scrum-prep/slack_payload.json \
  .output/scrum-prep/agent_insights.json
```

### 4.2 Send to Slack

```bash
bash .claude/skills/sfa-slack-notify/send_to_slack.sh .output/scrum-prep/slack_payload.json
```

**Dependencies**:
- `workflows/daily-scrum-prep/compute_metrics.py`
- `workflows/daily-scrum-prep/generate_slack_payload.py`
- `.claude/skills/sfa-slack-notify/send_to_slack.sh`

---

## Slack Message Structure

### Header
```
📊 SF Daily Scrum Prep — YYYY-MM-DD
```

### Sprint Progress Bar
```
*SF-Sprint-38* · Day 12/21 · Ends Apr 2
Done ████████░░░░░░░░ 50% (34/68)  ·  Elapsed 57%
```

### Key Metrics Dashboard
```
Metric             Value    Trend   Benchmark
────────────────   ──────   ─────   ─────────
Commitment Rate     50%      —      Target: 80-90%
Scope Change        12%      —      Target: <10%
Median Cycle Time   3.2d     —      Target: 3-5d
Items in Review     12       —      Healthy: <5
Avg WIP/Person      1.4      —      Limit: 2-3
```

### Action Required (max 5 items, rule-based)
```
*🎯 Action Required*
• Sprint is at risk — 50% done but 57% elapsed. Consider descoping 2 lowest-priority unstarted items.
• 12 items stuck in Review. Suggest a focused review session — each member reviews 1 PR.
• ACM-31402 (Blocker) is still not started. This should be picked up today.
```

Note: Issue keys (e.g., ACM-31402) are rendered as clickable Jira links in Slack.

### Sprint Insights (AI-generated)
```
*🧠 Sprint Insights*
• 5 of 8 review items are cluster-proxy related — a focused 30-min session between Le Yang and Zhiwei could clear the bottleneck.
• ACM-31402 (Blocker) in New for 8 days — comments show it's blocked by upstream OCM API change. Escalate to OCM maintainers.
• Realistically 4-5 more items can close — prioritize ACM-31100 and ACM-31205 (both in Review, close to done).

*Per-member:*
• *Le Yang*: 5 items in Review, 3 are cluster-proxy cert fixes. Ask Zhiwei Yin to batch-review today.
• *Jian Qiu*: 2 items in Review for 5+ days — no reviewer comments found. Assign specific reviewers.
• *Qing Hao*: 2 in progress, 1 not started (Critical). Finish current work first.
```

### Per-Member Status (compact)
```
Member             New Back Prog  Rev Test Resv Clos
──────────────────  ─── ──── ──── ─── ──── ──── ────
Zhao Xue             0    0    0    1    0    2    6
Hui Chen             3    2    1    0    0    1   15
Song Lai             1    1    2    0    0    3    4
Jian Zhu             2    1    2    3    0    1    2
Le Yang              0    0    2    5    0    0    0
Qing Hao             1    0    2    0    0    0    0
Zhiwei Yin           0    0    1    1    0    0    0
Jian Qiu             0    0    0    2    0    0    0
```

### Review Queue (sprint-scoped)
```
*🔍 Review Queue — SF-Sprint-38* (12 items in sprint)
• ACM-30994 — Fix cluster-proxy cert renewal · Le Yang · 5d in review
• ACM-31100 — Update managed-serviceaccount API · Jian Qiu · 3d in review
```

Note: Only shows items that belong to the current active sprint. Items not in the sprint are excluded.

### Context Footer
```
Generated by server-foundation-agent · YYYY-MM-DD
```

---

## Edge Cases

- **No active sprint**: Send "No active SF sprint found" message
- **Sprint just started (< 2 days)**: Skip burndown and commitment analysis, focus on planning quality
- **Sprint ending soon (< 2 days)**: Emphasize close-out, flag items that won't make it
- **No changelogs available**: Skip cycle time, report "insufficient data"
- **API rate limit**: Limit changelog fetches to 30 most relevant issues (non-New, non-Closed)
