#!/usr/bin/env python3
"""Fetch Jira changelogs for sprint issues.

Fetches status transitions and sprint changes from Jira API for each issue
that is not in New/Backlog status. This replaces the manual curl-based
Phase 1.3 that the agent would otherwise need to interpret from the
workflow markdown.

Usage:
    python3 workflows/daily-scrum-prep/fetch_changelogs.py \
        <sprint_issues_raw.json> \
        <changelogs_output_dir>

Environment:
    JIRA_EMAIL       - Jira account email
    JIRA_API_TOKEN   - Jira API token
"""
import json
import os
import sys
import urllib.request
import urllib.error
import base64
import time

JIRA_BASE = "https://redhat.atlassian.net"
SKIP_STATUSES = {"New", "Backlog"}
# Limit concurrent fetches to stay within Jira rate limits
MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds


def get_auth_header():
    """Build Basic Auth header from environment variables."""
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    if not email or not token:
        print("WARNING: JIRA_EMAIL or JIRA_API_TOKEN not set, cannot fetch changelogs",
              file=sys.stderr)
        return None
    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {credentials}"


def fetch_issue_changelog(key, auth_header):
    """Fetch changelog for a single issue from Jira API."""
    url = f"{JIRA_BASE}/rest/api/2/issue/{key}?expand=changelog&fields=status"
    req = urllib.request.Request(url)
    req.add_header("Authorization", auth_header)
    req.add_header("Accept", "application/json")

    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES:
                print(f"  Rate limited on {key}, retrying in {RETRY_DELAY}s...",
                      file=sys.stderr)
                time.sleep(RETRY_DELAY)
                continue
            print(f"  HTTP {e.code} fetching {key}: {e.reason}", file=sys.stderr)
            return None
        except (urllib.error.URLError, OSError) as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            print(f"  Error fetching {key}: {e}", file=sys.stderr)
            return None
    return None


def extract_changelog(raw_data):
    """Extract status transitions and sprint changes from raw changelog."""
    if not raw_data or "changelog" not in raw_data:
        return {"status_transitions": [], "sprint_changes": []}

    status_transitions = []
    sprint_changes = []

    for history in raw_data.get("changelog", {}).get("histories", []):
        created = history.get("created", "")

        status_items = []
        sprint_items = []

        for item in history.get("items", []):
            if item.get("field") == "status":
                status_items.append({
                    "from": item.get("fromString", ""),
                    "to": item.get("toString", ""),
                })
            elif item.get("field") == "Sprint":
                sprint_items.append({
                    "from": item.get("fromString", ""),
                    "to": item.get("toString", ""),
                })

        if status_items:
            status_transitions.append({
                "created": created,
                "items": status_items,
            })
        if sprint_items:
            sprint_changes.append({
                "created": created,
                "items": sprint_items,
            })

    return {
        "status_transitions": status_transitions,
        "sprint_changes": sprint_changes,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: fetch_changelogs.py <sprint_issues.json> <changelogs_dir>",
              file=sys.stderr)
        sys.exit(1)

    issues_file = sys.argv[1]
    changelogs_dir = sys.argv[2]

    auth_header = get_auth_header()
    if not auth_header:
        print("Skipping changelog fetch — no Jira credentials", file=sys.stderr)
        os.makedirs(changelogs_dir, exist_ok=True)
        sys.exit(0)

    with open(issues_file) as f:
        raw_data = json.load(f)

    # Filter issues that need changelogs (not in New/Backlog)
    issues_to_fetch = []
    for item in raw_data.get("issues", []):
        status = item.get("fields", {}).get("status", {}).get("name", "")
        if status not in SKIP_STATUSES:
            issues_to_fetch.append(item["key"])

    print(f"Fetching changelogs for {len(issues_to_fetch)} issues "
          f"(skipping {len(raw_data.get('issues', [])) - len(issues_to_fetch)} in New/Backlog)",
          file=sys.stderr)

    os.makedirs(changelogs_dir, exist_ok=True)
    fetched = 0
    failed = 0

    for key in issues_to_fetch:
        raw = fetch_issue_changelog(key, auth_header)
        if raw:
            changelog = extract_changelog(raw)
            output_file = os.path.join(changelogs_dir, f"issue-{key}.json")
            with open(output_file, "w") as f:
                json.dump(changelog, f, indent=2)
            fetched += 1
        else:
            failed += 1

    print(f"Done: {fetched} fetched, {failed} failed", file=sys.stderr)


if __name__ == "__main__":
    main()
