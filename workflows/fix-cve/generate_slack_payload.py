#!/usr/bin/env python3
"""Generate Slack Block Kit payload for fix-cve agent-swarm runs.

Usage:
    python3 workflows/fix-cve/generate_slack_payload.py \\
        <output_dir_or_remediation.json> <slack_payload.json>

Reads optional files from the output directory (when first arg is a directory):
  - remediation.json — array of remediation action records
  - run_meta.json — optional counts and failure strings
  - vulnerabilities.json — optional; used for early-exit / issue counts
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from slack_blocks import (
    SF_GROUP_MENTION,
    agent_footer_block,
    escape_mrkdwn,
    header_block,
    linkify_issue_keys,
    section_mrkdwn,
    today_iso,
)


def _load_json(path: Path) -> object | None:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _resolve_input_dir(arg: str) -> tuple[Path, Path]:
    p = Path(arg)
    if p.is_dir():
        return p, p / "remediation.json"
    return p.parent, p


def _format_pr_line(pr_url: str, repo: str, branch: str, keys: list[str]) -> str:
    repo_short = repo.split("/")[-1] if repo else "repo"
    key_part = ", ".join(keys[:6])
    if len(keys) > 6:
        key_part += f" (+{len(keys) - 6} more)"
    return (
        f"• <{pr_url}|{repo_short} `{branch}`> — "
        f"{linkify_issue_keys(escape_mrkdwn(key_part))}"
    )


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: generate_slack_payload.py <output_dir|remediation.json> "
            "<slack_payload.json>",
            file=sys.stderr,
        )
        sys.exit(1)

    input_dir, remediation_path = _resolve_input_dir(sys.argv[1])
    out_path = Path(sys.argv[2])

    remediation_raw = _load_json(remediation_path)
    remediation: list[dict] = remediation_raw if isinstance(remediation_raw, list) else []

    meta = _load_json(input_dir / "run_meta.json")
    if not isinstance(meta, dict):
        meta = {}

    vulns = _load_json(input_dir / "vulnerabilities.json")
    issue_count = len(vulns) if isinstance(vulns, list) else meta.get("issues_found")

    prs: dict[str, dict] = {}
    closed: list[dict] = []
    for row in remediation:
        action = row.get("action", "")
        if action in ("pr_opened", "skipped_existing_pr") and row.get("pr_url"):
            url = row["pr_url"]
            entry = prs.setdefault(
                url,
                {
                    "pr_url": url,
                    "repo": row.get("repo", ""),
                    "branch": row.get("branch", ""),
                    "keys": [],
                },
            )
            key = row.get("issue_key")
            if key and key not in entry["keys"]:
                entry["keys"].append(key)
        elif action == "closed":
            closed.append(row)

    failures: list[str] = list(meta.get("failures") or [])
    for row in remediation:
        if row.get("action") == "failed" and row.get("notes"):
            failures.append(str(row["notes"]))

    cves_processed = meta.get("cves_processed")
    if cves_processed is None:
        cves = {r.get("cve_id") for r in remediation if r.get("cve_id")}
        cves_processed = len(cves)

    today = today_iso()
    pr_count = len(prs)
    closed_count = len(closed)

    if issue_count == 0 and not remediation:
        fallback = f"SF CVE fix — {today}: no active vulnerability issues"
        blocks = [
            header_block(f"SF CVE fix — {today}"),
            section_mrkdwn(f"{SF_GROUP_MENTION}\n_No active Server Foundation CVE issues._"),
            agent_footer_block(today),
        ]
    else:
        fallback = (
            f"SF CVE fix — {today}: {pr_count} draft PR(s), "
            f"{closed_count} closed N/A, {cves_processed or 0} CVE(s) processed"
        )
        summary_lines = [
            f"{SF_GROUP_MENTION}",
            f"*CVEs processed:* {cves_processed or 0}",
        ]
        if issue_count is not None:
            summary_lines.append(f"*Active issues scanned:* {issue_count}")
        if meta.get("comments_posted") is not None:
            summary_lines.append(f"*Jira comments posted:* {meta['comments_posted']}")
        summary_lines.append(
            f"*Draft PRs:* {pr_count} · *Closed (N/A):* {closed_count}"
        )

        blocks: list[dict] = [
            header_block(f"SF CVE fix — {today}"),
            section_mrkdwn("\n".join(summary_lines)),
            {"type": "divider"},
        ]

        if prs:
            pr_lines = [
                _format_pr_line(p["pr_url"], p["repo"], p["branch"], p["keys"])
                for p in prs.values()
            ]
            blocks.append(section_mrkdwn(f"*Draft PRs opened*\n" + "\n".join(pr_lines)))
            blocks.append({"type": "divider"})

        if closed:
            closed_lines = []
            for row in closed[:20]:
                key = row.get("issue_key", "?")
                note = truncate_note(row.get("notes") or row.get("impact") or "")
                closed_lines.append(
                    f"• {linkify_issue_keys(key)} — {escape_mrkdwn(note)}"
                )
            blocks.append(
                section_mrkdwn(
                    f"*Closed as Not Applicable* ({closed_count})\n"
                    + "\n".join(closed_lines)
                )
            )
            blocks.append({"type": "divider"})

        follow_up = meta.get("follow_up") or (
            "Comment `/ok-to-test` on draft PRs · approve when CI passes · "
            "move vulnerability issues to Review after marking PRs ready"
        )
        blocks.append(section_mrkdwn(f"*Follow-up*\n{linkify_issue_keys(follow_up)}"))

        if failures:
            fail_text = "\n".join(f"• {escape_mrkdwn(f)}" for f in failures[:10])
            blocks.append({"type": "divider"})
            blocks.append(section_mrkdwn(f"*Warnings / failures*\n{fail_text}"))

        blocks.append(agent_footer_block(today))

    payload = {"text": fallback, "blocks": blocks}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {out_path} ({pr_count} PRs, {closed_count} closed)")


def truncate_note(text: str, max_len: int = 80) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


if __name__ == "__main__":
    main()
