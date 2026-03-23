---
name: sfa-project-search
description: "Search, list, and filter tasks on the GitHub Projects V2 board (stolostron/projects/9). Use this skill when the user wants to see board status, list tasks, check what's in progress, view the kanban, or says things like 'show tasks', 'board status', 'what's in progress', 'list board items', 'show my tasks', 'project status'."
---

# Project Search

List and filter items on the project board at https://github.com/orgs/stolostron/projects/9.

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| status | No | all | Backlog, In progress, In review, Done |
| priority | No | all | P0, P1, P2 |
| size | No | all | XS, S, M, L, XL |
| keyword | No | - | Search in title/body text |
| format | No | table | table, summary, json |

## Workflow

### Step 1: Fetch all items

```bash
gh project item-list 9 --owner stolostron --format json
```

Note: `gh project item-list` does NOT support server-side filtering. All filtering must be done client-side after fetching.

The JSON output contains items with their field values. Each item has:
- `id`: Item ID
- `title`: Item title
- `body`: Item body (for draft issues)
- `type`: DRAFT_ISSUE, ISSUE, or PULL_REQUEST
- `status`: Status field value
- `priority`: Priority field value (from custom field)
- `size`: Size field value (from custom field)
- Other field values

### Step 2: Filter results

Use Python to parse and filter:

```python
import json, sys

data = json.load(sys.stdin)
items = data.get('items', [])

# Apply filters (example for status filter)
filtered = items
if status_filter:
    filtered = [i for i in filtered if i.get('status', '').lower() == status_filter.lower()]
if priority_filter:
    filtered = [i for i in filtered if i.get('priority', '').lower() == priority_filter.lower()]
if keyword_filter:
    kw = keyword_filter.lower()
    filtered = [i for i in filtered if kw in i.get('title', '').lower() or kw in (i.get('body') or '').lower()]

# Sort: by priority (P0 first), then status order
priority_order = {'P0': 0, 'P1': 1, 'P2': 2, '': 3}
status_order = {'In progress': 0, 'In review': 1, 'Backlog': 2, 'Done': 3}

filtered.sort(key=lambda x: (priority_order.get(x.get('priority', ''), 3), status_order.get(x.get('status', ''), 5)))

for item in filtered:
    print(f"{item.get('status','')}\t{item.get('priority','')}\t{item.get('size','')}\t{item['title']}")
```

### Step 3: Present results

Display as a markdown table with columns: Status, Priority, Size, Title, Type.

After the table, show:
- Total count and per-status distribution
- Per-priority distribution if multiple priorities exist
- Board URL: https://github.com/orgs/stolostron/projects/9

**Summary format** (when format=summary):
Show only counts and distributions, no item details.

## Examples

```
# Show all items
/sfa-project-search

# Filter by status
/sfa-project-search --status "In progress"

# Filter by priority
/sfa-project-search --priority P0

# Search by keyword
/sfa-project-search --keyword "cluster-proxy"

# Natural language
Show me what's on the board
What tasks are in progress?
Any P0 items on the board?
Board status summary
```

## Notes

- Project number: 9, Owner: stolostron
- All filtering is client-side (API limitation)
- Items can be draft issues, linked issues, or linked PRs
- Empty board returns "No items on the board."
- See `docs/github-projects.md` for field reference
- Dashboard: https://github.com/orgs/stolostron/projects/9
