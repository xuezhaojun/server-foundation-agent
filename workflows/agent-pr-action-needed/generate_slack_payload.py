#!/usr/bin/env python3
"""Generate Slack Block Kit payload for agent PRs needing human action.

Usage:
    python3 workflows/agent-pr-action-needed/generate_slack_payload.py \\
        <classified_prs.json> <output_payload.json>
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
    truncate,
)


def format_pr_line(pr: dict) -> str:
    title = truncate(escape_mrkdwn(pr.get("title", "")), 55)
    short_repo = pr.get("short_repo") or pr.get("repo", "").split("/")[-1]
    jira = pr.get("jira_key")
    jira_part = f" · {jira}" if jira else ""
    age = pr.get("age_days", "?")
    line = (
        f"• <{pr['url']}|#{pr['number']}> *{short_repo}*{jira_part} — {title} · _{age}d_"
    )
    if pr.get("needs_ok_to_test"):
        line += "\n     _Label:_ `needs-ok-to-test`"
    action = pr.get("action", "")
    if action:
        line += f"\n     _Action:_ {linkify_issue_keys(escape_mrkdwn(action))}"
    return line


def build_section(title: str, prs: list[dict], empty_text: str) -> list[dict]:
    blocks: list[dict] = [section_mrkdwn(f"*{title}* ({len(prs)})")]
    if not prs:
        blocks.append(section_mrkdwn(f"_{empty_text}_"))
    else:
        body = "\n".join(format_pr_line(p) for p in prs)
        blocks.append(section_mrkdwn(body))
    return blocks


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: generate_slack_payload.py <classified_prs.json> <output.json>",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)

    draft = data.get("draft_ready_for_review", [])
    awaiting = data.get("awaiting_approval", [])
    total = len(draft) + len(awaiting)
    today = today_iso()

    fallback = (
        f"Agent PR action needed — {today}: "
        f"{len(draft)} draft, {len(awaiting)} awaiting approval"
        if total
        else f"Agent PR action needed — {today}: no PRs need human action"
    )

    blocks: list[dict] = [
        header_block(f"Agent PRs need action — {today}"),
        section_mrkdwn(
            f"{SF_GROUP_MENTION}\n"
            f"*Summary:* {total} open PR(s) from `acm-agent[bot]` need human action "
            f"({len(draft)} draft · {len(awaiting)} awaiting approval)"
        ),
        {"type": "divider"},
    ]

    blocks.extend(
        build_section(
            "Draft — mark Ready for review",
            draft,
            "No draft agent PRs waiting.",
        )
    )
    blocks.append({"type": "divider"})
    blocks.extend(
        build_section(
            "Ready for review — approve",
            awaiting,
            "No agent PRs waiting on approval.",
        )
    )
    blocks.append({"type": "divider"})
    blocks.append(
        section_mrkdwn(
            "_After jira-pipeline creates a draft PR it stays in draft with "
            "`needs-ok-to-test` until an org member marks it ready and runs CI. "
            "Approve non-draft PRs once review looks good._"
        )
    )
    blocks.append(agent_footer_block(today))

    payload = {"text": fallback, "blocks": blocks}

    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {sys.argv[2]} ({total} PRs)")


if __name__ == "__main__":
    main()
