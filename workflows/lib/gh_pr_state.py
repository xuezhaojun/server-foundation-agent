"""Fetch and classify GitHub pull request state via the gh CLI."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

_GITHUB_NAME = r"[A-Za-z0-9][A-Za-z0-9._-]*"
PR_PATH_RE = re.compile(
    rf"^/({_GITHUB_NAME})/({_GITHUB_NAME})/pull/(?P<number>\d+)$"
)
PR_REF_RE = re.compile(r"\b([\w][\w.-]*)#(\d+)\b")


@dataclass(frozen=True)
class PrState:
    url: str
    repo: str
    number: int
    state: str
    is_draft: bool
    merged_at: Optional[str]
    title: str = ""

    @property
    def bucket(self) -> str:
        """Classify PR for human follow-up: draft, awaiting_approval, merged, closed."""
        if self.state == "MERGED":
            return "merged"
        if self.state == "CLOSED":
            return "closed"
        if self.is_draft:
            return "draft"
        return "awaiting_approval"


def parse_pr_url(url: str) -> tuple[str, int] | None:
    """Return (owner/repo, number) from a GitHub PR URL, or None."""
    if not url:
        return None
    parsed = urlparse(url.strip().rstrip("/"))
    if parsed.netloc not in ("github.com", "www.github.com"):
        return None
    match = PR_PATH_RE.match(parsed.path)
    if not match:
        return None
    owner, name, number = match.group(1), match.group(2), int(match.group("number"))
    return f"{owner}/{name}", number


def _truthy_draft(value: Any) -> bool:
    """True only for bool True or case-insensitive string \"true\"."""
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


def fetch_pr_state(url: str, *, timeout: int = 30) -> PrState | None:
    """Query gh for current PR state. Returns None if URL is invalid or gh fails."""
    parsed = parse_pr_url(url)
    if not parsed:
        return None
    repo, number = parsed
    try:
        proc = subprocess.run(
            [
                "gh",
                "pr",
                "view",
                str(number),
                "--repo",
                repo,
                "--json",
                "state,isDraft,mergedAt,title,url",
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return PrState(
        url=data.get("url") or url,
        repo=repo,
        number=number,
        state=str(data.get("state") or "UNKNOWN").upper(),
        is_draft=bool(data.get("isDraft")),
        merged_at=data.get("mergedAt"),
        title=str(data.get("title") or ""),
    )


def stored_pr_state_from_row(row: dict[str, Any]) -> PrState | None:
    """Build PrState from fields on a remediation row (no gh call)."""
    url = row.get("pr_url")
    if not url:
        return None
    parsed = parse_pr_url(url)
    if not parsed:
        return None
    repo, number = parsed
    return PrState(
        url=url,
        repo=repo,
        number=number,
        state=str(row.get("pr_state") or "UNKNOWN").upper(),
        is_draft=_truthy_draft(row.get("is_draft")),
        merged_at=row.get("merged_at"),
        title=str(row.get("pr_title") or ""),
    )


def pr_state_from_row(row: dict[str, Any]) -> PrState | None:
    """Use live gh data when available; fall back to fields stored on a remediation row."""
    url = row.get("pr_url")
    if not url:
        return None
    live = fetch_pr_state(url)
    if live:
        return live
    return stored_pr_state_from_row(row)


def apply_pr_fields(row: dict[str, Any], state: PrState) -> dict[str, Any]:
    """Return a copy of row with normalized PR state fields."""
    updated = dict(row)
    updated["pr_state"] = state.state
    updated["is_draft"] = state.is_draft
    updated["merged_at"] = state.merged_at
    updated["pr_title"] = state.title
    action = row.get("action", "")
    if action in ("pr_opened", "skipped_existing_pr"):
        if state.state == "MERGED":
            updated["action"] = "pr_merged"
        elif state.state == "CLOSED":
            updated["action"] = "pr_closed"
    return updated


def pr_short_label(repo: str, number: int | None) -> str:
    """Human label like klusterlet-addon-controller#659."""
    short = repo.split("/")[-1] if repo else "repo"
    return f"{short}#{number}" if number else short


def pr_lookup_from_entries(prs: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Map repo-short#number (lower case) to PR URL for linkify helpers."""
    lookup: dict[str, str] = {}
    for entry in prs.values():
        repo = entry.get("repo", "")
        number = entry.get("pr_number")
        url = entry.get("pr_url")
        if not url or not number:
            continue
        short = repo.split("/")[-1] if repo else ""
        if short:
            lookup[f"{short}#{number}".lower()] = url
    return lookup


def linkify_pr_refs(text: str, pr_lookup: dict[str, str]) -> str:
    """Replace repo#number tokens with Slack mrkdwn links when URL is known."""

    def repl(match: re.Match[str]) -> str:
        key = f"{match.group(1)}#{match.group(2)}"
        url = pr_lookup.get(key.lower())
        if url:
            return f"<{url}|{key}>"
        return match.group(0)

    return PR_REF_RE.sub(repl, text)
