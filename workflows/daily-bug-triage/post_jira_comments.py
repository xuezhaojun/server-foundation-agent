#!/usr/bin/env python3
"""Post full bug triage analysis as Jira comments.

Usage:
    python3 workflows/daily-bug-triage/post_jira_comments.py <analyses_dir>

For each bug-*.json in the analyses directory, posts a formatted Jira comment
with the complete root cause analysis, relevant files, and suggested fix.
Requires JIRA_EMAIL and JIRA_API_TOKEN environment variables.
"""
import json
import glob
import os
import sys
import urllib.request
import base64
import datetime


def build_comment_body(analysis):
    """Build Jira wiki markup comment from analysis result."""
    status = analysis.get("analysis_status", "unknown")
    lines = [
        f"h3. Bug Triage Analysis",
        f"",
        f"*Analysis Status:* {status}",
        f"*Confidence:* {analysis.get('confidence', 'N/A')}",
        f"*Relevant Repo:* {analysis.get('relevant_repo', 'N/A')}",
    ]

    # Relevant files
    files = analysis.get("relevant_files", [])
    if files:
        lines.append(f"*Relevant Files:*")
        for f in files:
            lines.append(f"- {{{{{{code}}}}}} {f}")
        lines.append("")

    # Root cause (full, no truncation)
    root_cause = analysis.get("root_cause", "")
    if root_cause:
        lines.append(f"h4. Root Cause")
        lines.append(root_cause)
        lines.append("")

    # Suggested fix (full, no truncation)
    fix = analysis.get("suggested_fix", "")
    if fix:
        lines.append(f"h4. Suggested Fix")
        lines.append(fix)
        lines.append("")

    # Draft PR
    draft_pr_url = analysis.get("draft_pr_url", "")
    if draft_pr_url:
        lines.append(f"h4. Draft PR")
        lines.append(f"[View Draft PR|{draft_pr_url}]")
        lines.append("")

    # Notes
    notes = analysis.get("notes", "")
    if notes:
        lines.append(f"h4. Notes")
        lines.append(notes)
        lines.append("")

    lines.append("----")
    lines.append("_— server-foundation-agent (daily bug triage)_")

    return "\n".join(lines)


def post_comment(issue_key, body):
    """Post a comment to a Jira issue using REST API v2."""
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    if not email or not token:
        print(f"  SKIP {issue_key}: JIRA_EMAIL or JIRA_API_TOKEN not set", file=sys.stderr)
        return False

    url = f"https://redhat.atlassian.net/rest/api/2/issue/{issue_key}/comment"
    payload = json.dumps({"body": body}).encode("utf-8")

    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {credentials}",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201):
                print(f"  OK {issue_key}: comment posted", file=sys.stderr)
                return True
            else:
                print(f"  FAIL {issue_key}: HTTP {resp.status}", file=sys.stderr)
                return False
    except Exception as e:
        print(f"  FAIL {issue_key}: {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: post_jira_comments.py <analyses_dir>", file=sys.stderr)
        sys.exit(1)

    analyses_dir = sys.argv[1]
    pattern = os.path.join(analyses_dir, "bug-*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print("No analysis files found", file=sys.stderr)
        return

    print(f"Posting Jira comments for {len(files)} bugs...", file=sys.stderr)

    success = 0
    for path in files:
        with open(path, "r") as f:
            analysis = json.load(f)

        key = analysis.get("key", "")
        status = analysis.get("analysis_status", "")
        if not key:
            print(f"  SKIP: no issue key in {path}", file=sys.stderr)
            continue

        # Only post comments for bugs with meaningful analysis
        if status in ("error",):
            print(f"  SKIP {key}: analysis status is '{status}'", file=sys.stderr)
            continue

        body = build_comment_body(analysis)
        if post_comment(key, body):
            success += 1

    print(f"Done: {success}/{len(files)} comments posted", file=sys.stderr)


if __name__ == "__main__":
    main()
