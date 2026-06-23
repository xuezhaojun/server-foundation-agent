#!/usr/bin/env python3
"""Refresh PR state on fix-cve remediation.json rows via gh.

Usage:
    python3 workflows/fix-cve/enrich_remediation_prs.py <remediation.json>

Reads remediation.json, fetches live GitHub state for rows with pr_url, updates
pr_state / is_draft / merged_at, and reclassifies merged or closed PRs
(pr_opened / skipped_existing_pr → pr_merged / pr_closed).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from gh_pr_state import apply_pr_fields, fetch_pr_state, stored_pr_state_from_row  # noqa: E402

PR_ACTIONS = frozenset({"pr_opened", "skipped_existing_pr", "pr_merged", "pr_closed"})
ALLOWED_OUTPUT_DIR = Path(".output/cve-analysis")


def resolve_remediation_path(
    raw: str,
    *,
    allowed_base: Path | None = None,
) -> Path:
    """Resolve and validate remediation.json path stays under the output directory."""
    base = (allowed_base or (Path.cwd() / ALLOWED_OUTPUT_DIR)).resolve()
    path = Path(raw).resolve()
    if not path.is_relative_to(base):
        print(f"Path not allowed (must be under {base}): {raw}", file=sys.stderr)
        raise SystemExit(1)
    return path


def enrich(path: Path) -> tuple[list[dict], int]:
    with path.open(encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise SystemExit(f"{path}: expected JSON array")

    refreshed = 0
    out: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            out.append(row)
            continue
        url = row.get("pr_url")
        action = row.get("action", "")
        if not url or action not in PR_ACTIONS:
            out.append(row)
            continue
        state = fetch_pr_state(url)
        if state:
            refreshed += 1
        else:
            state = stored_pr_state_from_row(row)
        if not state:
            out.append(row)
            continue
        out.append(apply_pr_fields(row, state))

    with path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    return out, refreshed


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: enrich_remediation_prs.py <remediation.json>", file=sys.stderr)
        sys.exit(1)
    path = resolve_remediation_path(sys.argv[1])
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    _, refreshed = enrich(path)
    print(f"Enriched {path} ({refreshed} PR row(s) refreshed)")


if __name__ == "__main__":
    main()
