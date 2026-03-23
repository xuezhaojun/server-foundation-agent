---
name: sfa-project-report
description: "Generate progress reports from the GitHub Projects V2 board (stolostron/projects/9). Use this skill to produce sprint summaries, daily standups, weekly reports, or board analytics. Trigger phrases: 'board report', 'sprint report', 'project report', 'weekly summary', 'standup report', 'progress report', 'board analytics'."
---

# Project Report

Generate structured progress reports from board data. Optionally send to Slack via sfa-slack-notify.

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| type | No | status | status, standup, sprint, weekly |
| send-slack | No | false | Send report to Slack via sfa-slack-notify |

## Report Types

### status -- Board Status Overview

Quick snapshot of current board state.

- Per-status item counts and percentage
- Per-priority distribution
- Total items

### standup -- Daily Standup Summary

For daily standup meetings.

- Items currently "In progress" (what we are working on)
- Items moved to "Done" recently (what we completed)
- Items in "In review" (what needs review)
- P0 items in any status (blockers/urgent)

### sprint -- Sprint Summary Report

End-of-sprint report.

- Completion rate (Done items / total items)
- Items by status (what is left)
- Items by priority
- Items by size (effort distribution)

### weekly -- Weekly Progress Report

Week-over-week progress.

- Current board snapshot
- Items in each status
- Highlights: P0 items, overdue items (past target date)

## Workflow

### Step 1: Fetch board data

```bash
gh project item-list 9 --owner stolostron --format json
```

### Step 2: Analyze data with Python

```python
import json, sys
from collections import Counter
from datetime import date

data = json.load(sys.stdin)
items = data.get('items', [])

# Count by status
status_counts = Counter(i.get('status', 'No Status') for i in items)
priority_counts = Counter(i.get('priority', 'None') for i in items)
size_counts = Counter(i.get('size', 'None') for i in items)

total = len(items)
done = status_counts.get('Done', 0)
in_progress = status_counts.get('In progress', 0)
in_review = status_counts.get('In review', 0)

# Completion rate
completion_rate = (done / total * 100) if total > 0 else 0

# Overdue items (target date < today)
today = date.today().isoformat()
overdue = [i for i in items if i.get('target date', '') and i['target date'] < today and i.get('status') != 'Done']

# P0 items not done
p0_active = [i for i in items if i.get('priority') == 'P0' and i.get('status') != 'Done']
```

### Step 3: Format report

**Status report format:**

```
## Board Status Report

| Status | Count | % |
|--------|-------|---|
| In progress | X | X% |
| In review | X | X% |
| Ready | X | X% |
| Backlog | X | X% |
| Done | X | X% |
| **Total** | **X** | **100%** |

### Priority Distribution
- P0: X items
- P1: X items
- P2: X items
```

**Standup report format:**

```
## Daily Standup

### Working On (In Progress)
- Task title 1 [P0]
- Task title 2 [P1]

### Needs Review
- Task title 3

### Completed (Done)
- Task title 4
- Task title 5

### Blockers / Urgent (P0)
- Task title 6 -- Status: Ready
```

### Step 4: Send to Slack (if requested)

If `send-slack` is true, use the sfa-slack-notify skill to post the report to Slack. The report markdown should be converted to Slack-compatible format.

## Examples

```
# Quick status
/sfa-project-report

# Daily standup
/sfa-project-report --type standup

# Sprint summary
/sfa-project-report --type sprint

# Weekly report to Slack
/sfa-project-report --type weekly --send-slack

# Natural language
Show me the board report
Generate a standup summary
How's the sprint going?
Send weekly report to slack
```

## Notes

- All data comes from `gh project item-list` (no Jira queries needed)
- Reports are generated in markdown format
- Slack integration uses the existing sfa-slack-notify skill
- Dashboard: https://github.com/orgs/stolostron/projects/9
- See `docs/github-projects.md` for field reference
