#!/usr/bin/env python3
"""Compute Agile sprint metrics from Jira data.

Usage:
    python3 workflows/daily-scrum-prep/compute_metrics.py \
        <sprint_issues_raw.json> \
        <changelogs_dir> \
        <output_metrics.json>

Input:
    - sprint_issues_raw.json: Raw Jira search result (v3 API)
    - changelogs_dir: Directory containing per-issue changelog JSON files (issue-<KEY>.json)

Output:
    - metrics.json: Computed sprint metrics, per-member stats, and coaching recommendations
"""
import json
import os
import sys
import datetime
from collections import defaultdict

# Status categories (match sprint board column order)
NEW_STATUSES = {"New"}
BACKLOG_STATUSES = {"Backlog", "Refinement"}
IN_PROGRESS_STATUSES = {"In Progress"}
REVIEW_STATUSES = {"Review", "Code Review"}
TESTING_STATUSES = {"Testing", "ON_QA"}
RESOLVED_STATUSES = {"Resolved", "Release Pending", "Verified"}
CLOSED_STATUSES = {"Closed"}
# Combined groups for existing logic
DONE_STATUSES = RESOLVED_STATUSES | CLOSED_STATUSES
NOT_STARTED_STATUSES = NEW_STATUSES | BACKLOG_STATUSES

# Benchmarks
COMMITMENT_RATE_TARGET = 85  # %
SCOPE_CHANGE_THRESHOLD = 10  # %
CYCLE_TIME_TARGET_DAYS = 5
REVIEW_AGE_WARN_DAYS = 2
WIP_LIMIT = 3
REVIEW_BOTTLENECK_THRESHOLD = 5


def parse_date(dt_str):
    """Parse ISO date string to date object."""
    if not dt_str:
        return None
    return datetime.date.fromisoformat(dt_str[:10])


def parse_datetime(dt_str):
    """Parse ISO datetime string to datetime object."""
    if not dt_str:
        return None
    # Handle timezone offset like +0000
    dt_str = dt_str.replace("+0000", "+00:00").replace("Z", "+00:00")
    try:
        return datetime.datetime.fromisoformat(dt_str)
    except ValueError:
        return datetime.datetime.fromisoformat(dt_str[:19])


def extract_sprint_info(issues):
    """Extract active SF sprint metadata from issue sprint fields."""
    for issue in issues:
        sprints = issue.get("fields", {}).get("customfield_10020") or []
        for s in sprints:
            if s.get("state") == "active" and s.get("name", "").startswith("SF-Sprint"):
                return {
                    "id": s["id"],
                    "name": s["name"],
                    "start_date": s.get("startDate", "")[:10],
                    "end_date": s.get("endDate", "")[:10],
                }
    # Fallback: use any active sprint
    for issue in issues:
        sprints = issue.get("fields", {}).get("customfield_10020") or []
        for s in sprints:
            if s.get("state") == "active":
                return {
                    "id": s["id"],
                    "name": s["name"],
                    "start_date": s.get("startDate", "")[:10],
                    "end_date": s.get("endDate", "")[:10],
                }
    return None


def parse_issues(raw_data):
    """Parse raw Jira search results into structured issue list."""
    issues = []
    for item in raw_data.get("issues", []):
        f = item["fields"]
        assignee_obj = f.get("assignee")
        sprints = f.get("customfield_10020") or []

        issues.append({
            "key": item["key"],
            "summary": f.get("summary", ""),
            "status": f["status"]["name"],
            "type": f["issuetype"]["name"],
            "priority": f["priority"]["name"] if f.get("priority") else "Normal",
            "assignee": assignee_obj["displayName"] if assignee_obj else "Unassigned",
            "created": f.get("created", "")[:10],
            "sprints": [s.get("name", "") for s in sprints if isinstance(s, dict)],
        })
    return issues


def load_changelogs(changelogs_dir):
    """Load per-issue changelog files."""
    changelogs = {}
    if not os.path.isdir(changelogs_dir):
        return changelogs
    for fname in os.listdir(changelogs_dir):
        if fname.startswith("issue-") and fname.endswith(".json"):
            key = fname.replace("issue-", "").replace(".json", "")
            with open(os.path.join(changelogs_dir, fname)) as f:
                changelogs[key] = json.load(f)
    return changelogs


def compute_scope_change(issues, changelogs, sprint_info):
    """Compute scope change rate: issues added after sprint start."""
    if not sprint_info:
        return {"added_after_start": 0, "total": len(issues), "rate": 0.0}

    sprint_start = parse_date(sprint_info["start_date"])
    sprint_name = sprint_info["name"]
    if not sprint_start:
        return {"added_after_start": 0, "total": len(issues), "rate": 0.0}

    # Grace period: 1 day after sprint start for planning adjustments
    grace_cutoff = sprint_start + datetime.timedelta(days=1)
    added_after = []

    for issue in issues:
        key = issue["key"]
        cl = changelogs.get(key, {})
        sprint_changes = cl.get("sprint_changes", [])

        # Find earliest addition to this sprint
        earliest_add = None
        for change in sprint_changes:
            for item in change.get("items", []):
                to_val = item.get("to", "")
                if sprint_name in to_val:
                    change_date = parse_date(change.get("created", ""))
                    if change_date and (earliest_add is None or change_date < earliest_add):
                        earliest_add = change_date

        if earliest_add and earliest_add > grace_cutoff:
            added_after.append(key)

    total = len(issues)
    rate = (len(added_after) / total * 100) if total > 0 else 0.0
    return {
        "added_after_start": len(added_after),
        "added_keys": added_after,
        "total": total,
        "rate": round(rate, 1),
    }


def compute_cycle_times(issues, changelogs):
    """Compute cycle time for completed issues (In Progress → Done)."""
    cycle_times = []

    for issue in issues:
        if issue["status"] not in DONE_STATUSES:
            continue
        key = issue["key"]
        cl = changelogs.get(key, {})
        transitions = cl.get("status_transitions", [])

        # Find first "In Progress" transition and last "Done" transition
        first_in_progress = None
        last_done = None

        for t in transitions:
            t_date = parse_datetime(t.get("created", ""))
            if not t_date:
                continue
            for item in t.get("items", []):
                if item.get("to") in IN_PROGRESS_STATUSES and first_in_progress is None:
                    first_in_progress = t_date
                if item.get("to") in DONE_STATUSES:
                    last_done = t_date

        if first_in_progress and last_done and last_done > first_in_progress:
            days = (last_done - first_in_progress).total_seconds() / 86400
            cycle_times.append({
                "key": key,
                "days": round(days, 1),
                "summary": issue["summary"],
            })

    if not cycle_times:
        return {"median": None, "average": None, "p90": None, "samples": 0, "items": []}

    sorted_times = sorted(ct["days"] for ct in cycle_times)
    n = len(sorted_times)
    median = sorted_times[n // 2]
    average = round(sum(sorted_times) / n, 1)
    p90_idx = min(int(n * 0.9), n - 1)
    p90 = sorted_times[p90_idx]

    return {
        "median": median,
        "average": average,
        "p90": p90,
        "samples": n,
        "items": sorted(cycle_times, key=lambda x: -x["days"])[:5],
    }


def compute_review_bottleneck(issues, changelogs):
    """Find issues stuck in Review and how long they've been there."""
    today = datetime.date.today()
    review_items = []

    for issue in issues:
        if issue["status"] not in REVIEW_STATUSES:
            continue
        key = issue["key"]
        cl = changelogs.get(key, {})
        transitions = cl.get("status_transitions", [])

        # Find when issue entered Review
        entered_review = None
        for t in transitions:
            for item in t.get("items", []):
                if item.get("to") in REVIEW_STATUSES:
                    entered_review = parse_date(t.get("created", ""))

        days_in_review = 0
        if entered_review:
            days_in_review = (today - entered_review).days

        review_items.append({
            "key": key,
            "summary": issue["summary"],
            "assignee": issue["assignee"],
            "days_in_review": days_in_review,
            "priority": issue["priority"],
        })

    return {
        "count": len(review_items),
        "items": sorted(review_items, key=lambda x: -x["days_in_review"]),
        "over_threshold": [r for r in review_items if r["days_in_review"] > REVIEW_AGE_WARN_DAYS],
    }


def compute_wip_per_member(issues):
    """Compute WIP (In Progress + Review) count per member."""
    member_wip = defaultdict(lambda: {"in_progress": 0, "review": 0, "total_wip": 0, "issues": []})

    for issue in issues:
        assignee = issue["assignee"]
        status = issue["status"]
        if status in IN_PROGRESS_STATUSES:
            member_wip[assignee]["in_progress"] += 1
            member_wip[assignee]["total_wip"] += 1
            member_wip[assignee]["issues"].append(issue["key"])
        elif status in REVIEW_STATUSES:
            member_wip[assignee]["review"] += 1
            member_wip[assignee]["total_wip"] += 1
            member_wip[assignee]["issues"].append(issue["key"])

    overloaded = {m: s for m, s in member_wip.items() if s["total_wip"] > WIP_LIMIT}
    active_members = [m for m in member_wip if member_wip[m]["total_wip"] > 0]
    avg_wip = round(sum(member_wip[m]["total_wip"] for m in active_members) / len(active_members), 1) if active_members else 0

    return {
        "per_member": dict(member_wip),
        "overloaded": overloaded,
        "avg_wip": avg_wip,
    }


def compute_burndown(issues, sprint_info):
    """Compute sprint burndown position."""
    if not sprint_info:
        return {"elapsed_pct": 0, "done_pct": 0, "gap": 0, "on_track": True}

    today = datetime.date.today()
    start = parse_date(sprint_info["start_date"])
    end = parse_date(sprint_info["end_date"])

    if not start or not end or end <= start:
        return {"elapsed_pct": 0, "done_pct": 0, "gap": 0, "on_track": True}

    total_days = (end - start).days
    elapsed_days = min((today - start).days, total_days)
    elapsed_pct = round(elapsed_days / total_days * 100)

    total_issues = len(issues)
    done_issues = sum(1 for i in issues if i["status"] in DONE_STATUSES)
    done_pct = round(done_issues / total_issues * 100) if total_issues > 0 else 0

    gap = elapsed_pct - done_pct

    return {
        "elapsed_days": elapsed_days,
        "total_days": total_days,
        "remaining_days": max(total_days - elapsed_days, 0),
        "elapsed_pct": elapsed_pct,
        "done_count": done_issues,
        "total_count": total_issues,
        "done_pct": done_pct,
        "gap": gap,
        "on_track": gap <= 5,
    }


def compute_per_member_breakdown(issues):
    """Compute per-member issue breakdown by status."""
    members = defaultdict(lambda: {
        "total": 0, "new": 0, "backlog": 0, "in_progress": 0,
        "review": 0, "testing": 0, "resolved": 0, "closed": 0,
        # Keep combined keys for backward compatibility
        "done": 0, "not_started": 0,
    })

    for issue in issues:
        assignee = issue["assignee"]
        members[assignee]["total"] += 1
        status = issue["status"]
        if status in NEW_STATUSES:
            members[assignee]["new"] += 1
            members[assignee]["not_started"] += 1
        elif status in BACKLOG_STATUSES:
            members[assignee]["backlog"] += 1
            members[assignee]["not_started"] += 1
        elif status in IN_PROGRESS_STATUSES:
            members[assignee]["in_progress"] += 1
        elif status in REVIEW_STATUSES:
            members[assignee]["review"] += 1
        elif status in TESTING_STATUSES:
            members[assignee]["testing"] += 1
            members[assignee]["done"] += 1
        elif status in RESOLVED_STATUSES:
            members[assignee]["resolved"] += 1
            members[assignee]["done"] += 1
        elif status in CLOSED_STATUSES:
            members[assignee]["closed"] += 1
            members[assignee]["done"] += 1

    # Sort by done count descending
    sorted_members = sorted(members.items(), key=lambda x: -x[1]["done"])
    return {m: s for m, s in sorted_members}


def compute_status_distribution(issues):
    """Count issues per status."""
    counts = defaultdict(int)
    for issue in issues:
        counts[issue["status"]] += 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def compute_type_distribution(issues):
    """Count issues per type."""
    counts = defaultdict(int)
    for issue in issues:
        counts[issue["type"]] += 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def compute_agent_context(issues, changelogs, sprint_info, burndown, review_bottleneck):
    """Build rich issue context for agent analysis.

    Organizes issue data per-member with details the agent needs to generate
    intelligent insights: summaries, priorities, days in current status, and
    status transitions.
    """
    today = datetime.date.today()

    # Compute days in current status for each issue
    issue_details = []
    for issue in issues:
        key = issue["key"]
        cl = changelogs.get(key, {})
        transitions = cl.get("status_transitions", [])

        # Find when issue entered current status
        entered_current = None
        for t in transitions:
            for item in t.get("items", []):
                if item.get("to") == issue["status"]:
                    entered_current = parse_date(t.get("created", ""))

        days_in_status = 0
        if entered_current:
            days_in_status = (today - entered_current).days
        elif issue["created"]:
            # Never transitioned — use creation date
            created = parse_date(issue["created"])
            if created:
                days_in_status = (today - created).days

        # Count how many status transitions this issue has had
        transition_count = sum(len(t.get("items", [])) for t in transitions)

        issue_details.append({
            "key": key,
            "summary": issue["summary"],
            "type": issue["type"],
            "status": issue["status"],
            "priority": issue["priority"],
            "assignee": issue["assignee"],
            "days_in_status": days_in_status,
            "transition_count": transition_count,
        })

    # Group by assignee for per-member analysis
    per_member_issues = defaultdict(list)
    for d in issue_details:
        per_member_issues[d["assignee"]].append(d)

    # Identify risk signals for the agent
    risks = []
    # High-priority items not started
    for d in issue_details:
        if d["priority"] in ("Critical", "Blocker") and d["status"] in NOT_STARTED_STATUSES:
            risks.append({
                "type": "high_priority_not_started",
                "issue": d["key"],
                "summary": d["summary"],
                "priority": d["priority"],
                "assignee": d["assignee"],
                "days_in_status": d["days_in_status"],
            })
    # Items stuck (long time in same status, not done)
    for d in issue_details:
        if d["status"] not in DONE_STATUSES and d["days_in_status"] > 5:
            risks.append({
                "type": "potentially_stuck",
                "issue": d["key"],
                "summary": d["summary"],
                "status": d["status"],
                "assignee": d["assignee"],
                "days_in_status": d["days_in_status"],
            })
    # Items bouncing (many transitions may indicate unclear requirements)
    for d in issue_details:
        if d["transition_count"] > 4:
            risks.append({
                "type": "excessive_transitions",
                "issue": d["key"],
                "summary": d["summary"],
                "assignee": d["assignee"],
                "transition_count": d["transition_count"],
            })

    return {
        "per_member_issues": {m: sorted(issues, key=lambda x: x["days_in_status"], reverse=True)
                              for m, issues in per_member_issues.items()},
        "risks": risks,
        "all_issues": issue_details,
    }


def generate_recommendations(burndown, scope_change, cycle_time, review_bottleneck, wip, issues):
    """Generate coaching recommendations based on metrics."""
    recs = []
    today = datetime.date.today()

    # Rule 1: Sprint burndown
    if burndown["gap"] > 15:
        # Count low-priority New items that could be descoped
        descopable = [i for i in issues if i["status"] in NOT_STARTED_STATUSES and i["priority"] in ("Normal", "Minor")]
        recs.append({
            "severity": "high",
            "category": "Burndown",
            "message": f"Sprint is at risk — {burndown['done_pct']}% done but {burndown['elapsed_pct']}% elapsed. "
                       f"Consider descoping {len(descopable)} lowest-priority unstarted items.",
        })
    elif burndown["gap"] > 5:
        recs.append({
            "severity": "medium",
            "category": "Burndown",
            "message": f"Slightly behind pace ({burndown['done_pct']}% done, {burndown['elapsed_pct']}% elapsed). "
                       f"Focus on closing items in Review before starting new work.",
        })

    # Rule 2: Review bottleneck
    if review_bottleneck["count"] > REVIEW_BOTTLENECK_THRESHOLD:
        recs.append({
            "severity": "high",
            "category": "Flow",
            "message": f"{review_bottleneck['count']} items stuck in Review. "
                       f"Suggest a focused review session today — each member reviews 1 PR.",
        })
    for item in review_bottleneck.get("over_threshold", []):
        recs.append({
            "severity": "medium",
            "category": "Flow",
            "message": f"{item['key']} has been in Review for {item['days_in_review']}d ({item['assignee']}). "
                       f"Consider assigning a specific reviewer.",
        })

    # Rule 3: WIP overload
    for member, stats in wip.get("overloaded", {}).items():
        recs.append({
            "severity": "medium",
            "category": "WIP",
            "message": f"{member} has {stats['total_wip']} items in progress/review (WIP limit: {WIP_LIMIT}). "
                       f"Consider finishing current work before starting new items.",
        })

    # Rule 4: Scope change
    if scope_change["rate"] > 20:
        recs.append({
            "severity": "high",
            "category": "Scope",
            "message": f"Scope change rate is {scope_change['rate']}% — "
                       f"{scope_change['added_after_start']} issues added after sprint start. "
                       f"Discuss with PO whether these should be deferred to next sprint.",
        })
    elif scope_change["rate"] > SCOPE_CHANGE_THRESHOLD:
        recs.append({
            "severity": "medium",
            "category": "Scope",
            "message": f"Scope change rate is {scope_change['rate']}% (target: <{SCOPE_CHANGE_THRESHOLD}%). "
                       f"{scope_change['added_after_start']} issues were added after sprint start.",
        })

    # Rule 5: Unstarted Critical/Blocker items
    critical_not_started = [
        i for i in issues
        if i["priority"] in ("Critical", "Blocker")
        and i["status"] in NOT_STARTED_STATUSES
    ]
    for item in critical_not_started:
        recs.append({
            "severity": "high",
            "category": "Priority",
            "message": f"{item['key']} ({item['priority']}) is still not started: {item['summary'][:60]}. "
                       f"This should be picked up today.",
        })

    # Rule 6: Commitment health (after midpoint)
    if burndown["elapsed_pct"] > 50:
        committed = burndown["total_count"]
        completed = burndown["done_count"]
        commit_rate = round(completed / committed * 100) if committed > 0 else 0
        if commit_rate < 50:
            recs.append({
                "severity": "medium",
                "category": "Commitment",
                "message": f"Commitment completion at {commit_rate}% past sprint midpoint. "
                           f"Team may be overcommitting — consider reducing sprint scope next planning.",
            })

    # Rule 7: Cycle time warning
    if cycle_time.get("median") and cycle_time["median"] > CYCLE_TIME_TARGET_DAYS * 1.5:
        recs.append({
            "severity": "medium",
            "category": "CycleTime",
            "message": f"Median cycle time is {cycle_time['median']}d (target: <{CYCLE_TIME_TARGET_DAYS}d). "
                       f"Consider breaking stories into smaller tasks.",
        })

    return recs


def main():
    if len(sys.argv) < 4:
        print("Usage: compute_metrics.py <sprint_issues.json> <changelogs_dir> <output.json>", file=sys.stderr)
        sys.exit(1)

    issues_file = sys.argv[1]
    changelogs_dir = sys.argv[2]
    output_file = sys.argv[3]

    with open(issues_file) as f:
        raw_data = json.load(f)

    issues = parse_issues(raw_data)
    sprint_info = extract_sprint_info(raw_data.get("issues", []))
    changelogs = load_changelogs(changelogs_dir)

    # Compute all metrics
    burndown = compute_burndown(issues, sprint_info)
    scope_change = compute_scope_change(issues, changelogs, sprint_info)
    cycle_time = compute_cycle_times(issues, changelogs)
    review_bottleneck = compute_review_bottleneck(issues, changelogs)
    wip = compute_wip_per_member(issues)
    per_member = compute_per_member_breakdown(issues)
    status_dist = compute_status_distribution(issues)
    type_dist = compute_type_distribution(issues)

    # Generate rule-based recommendations
    recommendations = generate_recommendations(
        burndown, scope_change, cycle_time, review_bottleneck, wip, issues
    )

    # Generate agent context for AI analysis
    agent_context = compute_agent_context(
        issues, changelogs, sprint_info, burndown, review_bottleneck
    )

    metrics = {
        "generated_at": datetime.datetime.now().isoformat(),
        "sprint": sprint_info,
        "burndown": burndown,
        "scope_change": {
            "added_after_start": scope_change["added_after_start"],
            "rate": scope_change["rate"],
            "total": scope_change["total"],
        },
        "cycle_time": {
            "median": cycle_time["median"],
            "average": cycle_time["average"],
            "p90": cycle_time["p90"],
            "samples": cycle_time["samples"],
            "slowest": cycle_time["items"][:3],
        },
        "review_bottleneck": {
            "count": review_bottleneck["count"],
            "over_2_days": len(review_bottleneck["over_threshold"]),
            "items": review_bottleneck["items"],
        },
        "wip": {
            "avg_wip_per_member": wip["avg_wip"],
            "overloaded_members": list(wip["overloaded"].keys()),
        },
        "status_distribution": status_dist,
        "type_distribution": type_dist,
        "per_member": per_member,
        "recommendations": recommendations,
        "agent_context": agent_context,
    }

    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)

    # Write agent context separately for easy reading
    context_file = output_file.replace("metrics.json", "agent_context.json")
    with open(context_file, "w") as f:
        json.dump(agent_context, f, indent=2, ensure_ascii=False, default=str)

    # Print summary to stderr
    print(f"Sprint: {sprint_info['name'] if sprint_info else 'unknown'}", file=sys.stderr)
    print(f"Issues: {len(issues)}", file=sys.stderr)
    print(f"Burndown: {burndown['done_pct']}% done, {burndown['elapsed_pct']}% elapsed (gap: {burndown['gap']}%)", file=sys.stderr)
    print(f"Review bottleneck: {review_bottleneck['count']} items", file=sys.stderr)
    print(f"Cycle time (median): {cycle_time['median']}d ({cycle_time['samples']} samples)", file=sys.stderr)
    print(f"Scope change: {scope_change['rate']}%", file=sys.stderr)
    print(f"Recommendations: {len(recommendations)}", file=sys.stderr)


if __name__ == "__main__":
    main()
