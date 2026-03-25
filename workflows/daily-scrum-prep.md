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
Phase 1: Collect        →  Phase 2: Compute Metrics   →  Phase 3: Coach         →  Phase 4: Distribute
query Jira sprint          cycle time, scope change,      expert recommendations     Slack notification
issues + changelogs        commitment rate, WIP            based on metrics
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

## Phase 3: Generate Coaching Recommendations

Based on computed metrics, generate targeted recommendations. This uses rule-based logic (not AI inference) for consistency.

**Output constraints**: All recommendations (high + medium) are merged, sorted by severity (high first), and **capped at 5 items total**. No separate "Suggestions" section. Issue keys are rendered as clickable Jira links.

### Recommendation Rules

```python
recommendations = []

# Rule 1: Sprint burndown
if burndown_gap > 15:
    recommendations.append({
        "severity": "high",
        "category": "Burndown",
        "message": "Sprint is at risk — {done_pct}% done but {elapsed_pct}% elapsed. Consider descoping {n} lowest-priority items."
    })
elif burndown_gap > 5:
    recommendations.append({
        "severity": "medium",
        "category": "Burndown",
        "message": "Slightly behind pace. Focus on closing items in Review before starting new work."
    })

# Rule 2: Review bottleneck
if in_review_count > 5:
    recommendations.append({
        "severity": "high",
        "category": "Flow",
        "message": "{n} items stuck in Review. Suggest a focused review session today — each member reviews 1 PR."
    })
for issue in review_items_over_2_days:
    recommendations.append({
        "severity": "medium",
        "category": "Flow",
        "message": "{key} has been in Review for {days}d. Consider assigning a specific reviewer."
    })

# Rule 3: WIP overload
for member in members_with_wip_over_3:
    recommendations.append({
        "severity": "medium",
        "category": "WIP",
        "message": "{member} has {n} items in progress. Consider finishing current work before starting new items."
    })

# Rule 4: Scope change
if scope_change_rate > 20:
    recommendations.append({
        "severity": "high",
        "category": "Scope",
        "message": "Scope change rate is {rate}% — {n} issues added after sprint start. Discuss with PO whether these should be deferred."
    })

# Rule 5: Unstarted high-priority items
for issue in critical_blocker_not_started:
    recommendations.append({
        "severity": "high",
        "category": "Priority",
        "message": "{key} ({priority}) is still not started. This should be picked up today."
    })

# Rule 6: Commitment health (only meaningful after sprint midpoint)
if elapsed_pct > 50 and commitment_rate < 50:
    recommendations.append({
        "severity": "medium",
        "category": "Commitment",
        "message": "Commitment completion at {rate}% past sprint midpoint. Team may be overcommitting — consider reducing sprint scope next planning."
    })
```

---

## Phase 4: Generate Slack Payload & Distribute

### 4.1 Generate Slack Payload

```bash
python3 workflows/daily-scrum-prep/generate_slack_payload.py \
  .output/scrum-prep/metrics.json \
  .output/scrum-prep/slack_payload.json
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

### Action Required (max 5 items)
```
*🎯 Action Required*
📉 Sprint is at risk — 50% done but 57% elapsed. Consider descoping 2 lowest-priority unstarted items.
🔀 12 items stuck in Review. Suggest a focused review session — each member reviews 1 PR.
⚡ ACM-31402 (Blocker) is still not started. This should be picked up today.
```

Note: Issue keys (e.g., ACM-31402) are rendered as clickable Jira links in Slack.
No separate "Suggestions" section — all recommendations are merged and capped at 3.

### Per-Member Status (compact)
```
Member          Done  InProg  Review  New
──────────────  ────  ──────  ──────  ───
Zhao Xue          8       0       1    0
Hui Chen         16       1       0    5
Song Lai          7       2       0    2
Jian Zhu          3       2       3    3
Le Yang           0       2       5    0
Qing Hao          0       2       0    1
Zhiwei Yin        0       1       1    0
Jian Qiu          0       0       2    0
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
