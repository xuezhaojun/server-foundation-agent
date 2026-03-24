---
name: sfa-jira-sprint-report
description: "Generate a sprint health report for the Server Foundation team. Use this skill when the user wants to check sprint progress, see sprint status, or says 'sprint report', 'sprint status', 'sprint health', 'sprint progress', 'how is the sprint going'. Queries Jira for current sprint issues and generates a health report with completion rates and per-member breakdown."
---

# Jira Sprint Report

Generate a sprint health report for the SF team.

## Reference Loading

- **For JQL syntax**: Read `docs/jira/jql-reference.md`
- **For API details**: Read `docs/jira/api-reference.md`

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| sprint | No | current | Sprint name or `current` for active sprint |

## Workflow

### Step 1: Query sprint issues

```
project = ACM AND component = "Server Foundation" AND sprint IN openSprints() ORDER BY assignee ASC, status ASC
```

If a specific sprint name is given, use `sprint = "<name>"` instead.

Request fields: `["issuetype", "summary", "status", "priority", "assignee", "customfield_10020", "story_points"]`.

### Step 2: Compute statistics

Using Python, calculate:

1. **Completion rate**: % of issues in Resolved/Closed vs total
2. **Status distribution**: count per status
3. **Per-member breakdown**: issues per assignee with their status distribution
4. **Type distribution**: Bugs vs Stories vs Tasks etc.

### Step 3: Format sprint report

```markdown
## Sprint Report — <Sprint Name>

### Overview
- **Total issues**: <count>
- **Completed**: <count> (<percent>%)
- **In Progress**: <count>
- **Not Started**: <count>

### Status Distribution
| Status | Count | Bar |
|--------|-------|-----|
| Resolved | 8 | ████████ |
| In Progress | 5 | █████ |
| Review | 3 | ███ |
| New | 2 | ██ |

### Per-Member Breakdown
| Member | Total | Done | In Progress | Not Started |
|--------|-------|------|-------------|-------------|
| Zhao Xue | 4 | 2 | 1 | 1 |
| Yin ZhiWei | 3 | 1 | 2 | 0 |
| ... | ... | ... | ... | ... |

### Type Distribution
| Type | Count |
|------|-------|
| Bug | 6 |
| Story | 4 |
| Task | 3 |

### Attention Items
- <count> issues still in *New* status
- <count> bugs with *Critical* severity
- <count> issues unassigned
```

### Step 4: Highlight risks

Flag any issues that need attention:
- Critical/Blocker items not in progress
- Issues stuck in same status for >5 days
- Unassigned issues

## Examples

```
/sfa-jira-sprint-report
Sprint status
How is the sprint going?
Sprint report for "SF Sprint 2026-Q1-S3"
```
