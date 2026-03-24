#!/usr/bin/env python3
"""Check Jira comments to find bugs already analyzed by server-foundation-agent.

Usage:
    python3 workflows/daily-bug-triage/check_prior_analysis.py <bugs_json> <new_bugs_out> <skipped_bugs_out>

Input:  JSON file with list of bug objects (from Phase 1)
Output: Two JSON files:
  - new_bugs_out: bugs that have NOT been previously analyzed (need full analysis)
  - skipped_bugs_out: bugs that HAVE been previously analyzed (skip to report)

Detection: looks for comments containing "server-foundation-agent" AND
"Bug Triage Analysis" — the signature left by post_jira_comments.py.

Requires JIRA_EMAIL and JIRA_API_TOKEN environment variables.
"""
import json
import os
import sys
import urllib.request
import base64


AGENT_MARKERS = ["server-foundation-agent", "Bug Triage Analysis"]


def fetch_comments(issue_key):
    """Fetch comments for a Jira issue. Returns list of comment body strings."""
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    if not email or not token:
        return []

    url = f"https://redhat.atlassian.net/rest/api/2/issue/{issue_key}/comment"
    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {credentials}",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [c.get("body", "") for c in data.get("comments", [])]
    except Exception as e:
        print(f"  WARN {issue_key}: failed to fetch comments: {e}", file=sys.stderr)
        return []


def has_prior_analysis(issue_key):
    """Check if server-foundation-agent has already posted a triage analysis."""
    comments = fetch_comments(issue_key)
    for body in comments:
        if all(marker in body for marker in AGENT_MARKERS):
            return True
    return False


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: check_prior_analysis.py <bugs_json> <new_bugs_out> <skipped_bugs_out>",
            file=sys.stderr,
        )
        sys.exit(1)

    bugs_json = sys.argv[1]
    new_bugs_out = sys.argv[2]
    skipped_bugs_out = sys.argv[3]

    with open(bugs_json, "r") as f:
        bugs = json.load(f)

    new_bugs = []
    skipped_bugs = []

    print(f"Checking {len(bugs)} bugs for prior analysis...", file=sys.stderr)

    for bug in bugs:
        key = bug["key"]
        if has_prior_analysis(key):
            print(f"  SKIP {key}: already analyzed by agent", file=sys.stderr)
            skipped_bugs.append(bug)
        else:
            print(f"  NEW  {key}: no prior analysis found", file=sys.stderr)
            new_bugs.append(bug)

    with open(new_bugs_out, "w") as f:
        json.dump(new_bugs, f, indent=2)

    with open(skipped_bugs_out, "w") as f:
        json.dump(skipped_bugs, f, indent=2)

    print(
        f"Result: {len(new_bugs)} need analysis, {len(skipped_bugs)} previously analyzed",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
