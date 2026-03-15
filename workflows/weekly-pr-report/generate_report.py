#!/usr/bin/env python3
"""Phase 3: Generate the full Markdown PR report.

Usage:
    python3 workflows/weekly-pr-report/generate_report.py <processed_prs.json> <output.md>

Input:  Processed PR JSON (output of process_prs.jq)
Output: Markdown report file
"""
import json
import sys
import datetime
from collections import defaultdict


def main():
    if len(sys.argv) < 3:
        print("Usage: generate_report.py <processed_prs.json> <output.md>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r') as f:
        prs = json.load(f)

    today = datetime.date.today().isoformat()
    total = len(prs)

    categories = {
        "Ready to Merge": [],
        "Needs Review": [],
        "Approved, Needs LGTM": [],
        "Work In Progress": [],
        "On Hold": [],
        "Needs Rebase": []
    }

    staleness = {
        "Fresh": [],
        "Normal": [],
        "Aging": [],
        "Stale": [],
        "Very Stale": [],
        "Abandoned": []
    }

    conflicts = []

    authors = defaultdict(lambda: {"Total": 0, "Ready": 0, "Needs Review": 0, "Approved, Needs LGTM": 0, "WIP": 0, "On Hold": 0, "Rebase": 0, "Days": 0})
    repos = defaultdict(lambda: {"Total": 0, "Ready": 0, "Needs Review": 0, "Approved, Needs LGTM": 0, "WIP": 0, "On Hold": 0, "Rebase": 0})

    for pr in prs:
        cat = pr["category"]
        categories[cat].append(pr)

        stale = pr["staleness"]
        staleness[stale].append(pr)

        if pr["mergeable"] == "CONFLICTING":
            conflicts.append(pr)

        author = pr["author"]
        authors[author]["Total"] += 1
        cat_key_map = {
            "Ready to Merge": "Ready",
            "Needs Review": "Needs Review",
            "Approved, Needs LGTM": "Approved, Needs LGTM",
            "Work In Progress": "WIP",
            "On Hold": "On Hold",
            "Needs Rebase": "Rebase"
        }
        authors[author][cat_key_map[cat]] += 1
        authors[author]["Days"] += pr["days"]

        repo = pr["content"]["repository"]["nameWithOwner"]
        repos[repo]["Total"] += 1
        repos[repo][cat_key_map[cat]] += 1

    health_score = int((len(staleness["Fresh"]) + len(staleness["Normal"])) / total * 100) if total > 0 else 100

    # Sort categories
    for cat_list in categories.values():
        cat_list.sort(key=lambda x: x['days'], reverse=True)
    conflicts.sort(key=lambda x: x['days'], reverse=True)

    def format_pr(pr):
        return f"| [#{pr['number']}]({pr['url']}) | {pr['repo']} | @{pr['author']} | {pr['title']} | {pr['days']} |"

    def format_pr_staleness(pr):
        return f"| [#{pr['number']}]({pr['url']}) | {pr['repo']} | @{pr['author']} | {pr['title']} | {pr['days']} | {pr['staleness']} |"

    def format_pr_conflict(pr):
        return f"| [#{pr['number']}]({pr['url']}) | {pr['repo']} | @{pr['author']} | {pr['title']} | {pr['category']} | {pr['days']} |"

    md = [
        f"# Server Foundation Weekly PR Report — {today}",
        "",
        "## Executive Summary",
        "",
        f"- **Total open human PRs:** {total}",
        f"- **By category:** Ready to Merge ({len(categories['Ready to Merge'])}), Needs Review ({len(categories['Needs Review'])}), Approved/Needs LGTM ({len(categories['Approved, Needs LGTM'])}), WIP ({len(categories['Work In Progress'])}), On Hold ({len(categories['On Hold'])}), Needs Rebase ({len(categories['Needs Rebase'])})",
        f"- **Staleness:** Fresh ({len(staleness['Fresh'])}), Normal ({len(staleness['Normal'])}), Aging ({len(staleness['Aging'])}), Stale ({len(staleness['Stale'])}), Very Stale ({len(staleness['Very Stale'])}), Abandoned ({len(staleness['Abandoned'])})",
        f"- **Health score:** {health_score}% of PRs are Fresh or Normal",
        "",
        "---",
        "",
        "## Action Required: Ready to Merge",
        "",
        "These PRs are approved, have LGTM, and are mergeable. They should be merged promptly.",
        ""
    ]

    if categories['Ready to Merge']:
        md.append("| PR | Repository | Author | Title | Age (days) |")
        md.append("|----|------------|--------|-------|------------|")
        for pr in categories['Ready to Merge']:
            md.append(format_pr(pr))
    else:
        md.append("> No PRs are currently ready to merge.")

    md.extend(["", "---", "", "## Action Required: Needs Review", "",
               "These PRs have no approval or LGTM yet and need reviewer attention.", ""])

    if categories['Needs Review']:
        md.append("| PR | Repository | Author | Title | Days since update | Staleness |")
        md.append("|----|------------|--------|-------|--------------------|-----------|")
        for pr in categories['Needs Review']:
            md.append(format_pr_staleness(pr))
    else:
        md.append("> All PRs have been reviewed.")

    md.extend(["", "---", "", "## Approved, Needs LGTM", "",
               "These PRs are approved but still need an LGTM label before they can merge.", ""])

    if categories['Approved, Needs LGTM']:
        md.append("| PR | Repository | Author | Title | Days since update |")
        md.append("|----|------------|--------|-------|--------------------|")
        for pr in categories['Approved, Needs LGTM']:
            md.append(format_pr(pr))
    else:
        md.append("> No PRs in this state.")

    md.extend(["", "---", "", "## Work In Progress", "",
               "Draft PRs or PRs with `do-not-merge/work-in-progress` label.", ""])

    if categories['Work In Progress']:
        md.append("| PR | Repository | Author | Title | Days since update | Staleness |")
        md.append("|----|------------|--------|-------|--------------------|-----------|")
        for pr in categories['Work In Progress']:
            md.append(format_pr_staleness(pr))
    else:
        md.append("> No WIP PRs.")

    md.extend(["", "---", "", "## On Hold", "",
               "PRs with `do-not-merge/hold` label. These are intentionally paused.", ""])

    if categories['On Hold']:
        md.append("| PR | Repository | Author | Title | Days since update |")
        md.append("|----|------------|--------|-------|--------------------|")
        for pr in categories['On Hold']:
            md.append(format_pr(pr))
    else:
        md.append("> No PRs on hold.")

    md.extend(["", "---", "", "## Stale PR Alert", "",
               "PRs that have not been updated in 15+ days, grouped by severity.", ""])

    stale_total = len(staleness['Abandoned']) + len(staleness['Very Stale']) + len(staleness['Stale'])
    if stale_total > 0:
        for bucket, label in [('Abandoned', 'Abandoned (91+ days)'),
                               ('Very Stale', 'Very Stale (31\u201390 days)'),
                               ('Stale', 'Stale (15\u201330 days)')]:
            if staleness[bucket]:
                md.extend([
                    f"### {label}", "",
                    "| PR | Repository | Author | Title | Days since update |",
                    "|----|------------|--------|-------|--------------------|"
                ])
                for pr in sorted(staleness[bucket], key=lambda x: x['days'], reverse=True):
                    md.append(format_pr(pr))
                md.append("")
    else:
        md.extend(["> No stale PRs \u2014 great job!", ""])

    md.extend(["---", "", "## Conflict Alert", "",
               'PRs with `mergeable == "CONFLICTING"` across ALL categories.', ""])

    if conflicts:
        md.append("| PR | Repository | Author | Title | Category | Days since update |")
        md.append("|----|------------|--------|-------|----------|-------------------|")
        for pr in conflicts:
            md.append(format_pr_conflict(pr))
    else:
        md.append("> No PRs have merge conflicts.")

    md.extend(["", "---", "", "## Per-Author Summary", "",
               "| Author | Total | Ready | Needs Review | Approved/LGTM | WIP | On Hold | Rebase | Avg Days |",
               "|--------|-------|-------|--------------|----------------|-----|---------|--------|----------|"])

    for author, stats in sorted(authors.items(), key=lambda x: x[1]['Total'], reverse=True):
        avg = int(stats['Days'] / stats['Total']) if stats['Total'] > 0 else 0
        md.append(f"| @{author} | {stats['Total']} | {stats['Ready']} | {stats['Needs Review']} | {stats['Approved, Needs LGTM']} | {stats['WIP']} | {stats['On Hold']} | {stats['Rebase']} | {avg} |")

    md.extend(["", "---", "", "## Per-Repository Summary", "",
               "| Repository | Total | Ready | Needs Review | Approved/LGTM | WIP | On Hold | Rebase |",
               "|------------|-------|-------|--------------|----------------|-----|---------|--------|"])

    for repo, stats in sorted(repos.items(), key=lambda x: x[1]['Total'], reverse=True):
        md.append(f"| {repo} | {stats['Total']} | {stats['Ready']} | {stats['Needs Review']} | {stats['Approved, Needs LGTM']} | {stats['WIP']} | {stats['On Hold']} | {stats['Rebase']} |")

    with open(output_file, 'w') as f:
        f.write('\n'.join(md) + '\n')

    print(f"Report written to {output_file}")


if __name__ == '__main__':
    main()
