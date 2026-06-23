"""Tests for workflows/lib/gh_pr_state.py (no gh/network required)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflows" / "lib"))

from gh_pr_state import (  # noqa: E402
    PrState,
    apply_pr_fields,
    fetch_pr_state,
    linkify_pr_refs,
    parse_pr_url,
    pr_lookup_from_entries,
    pr_state_from_row,
    stored_pr_state_from_row,
)


def test_parse_pr_url():
    assert parse_pr_url(
        "https://github.com/stolostron/ocm/pull/767"
    ) == ("stolostron/ocm", 767)
    assert parse_pr_url(
        "https://github.com/stolostron/klusterlet-addon-controller/pull/659/"
    ) == ("stolostron/klusterlet-addon-controller", 659)
    assert parse_pr_url("https://example.com/foo") is None
    assert parse_pr_url("") is None
    assert parse_pr_url("https://github.com/foo|bar/repo/pull/1") is None
    assert parse_pr_url("https://github.com/foo/bar<script>/pull/1") is None
    assert parse_pr_url("https://github.com/foo/bar/pull/1|@channel") is None


def test_pr_state_bucket():
    assert PrState("u", "stolostron/ocm", 1, "MERGED", False, "2026-01-01").bucket == "merged"
    assert PrState("u", "stolostron/ocm", 1, "CLOSED", False, None).bucket == "closed"
    assert PrState("u", "stolostron/ocm", 1, "OPEN", True, None).bucket == "draft"
    assert (
        PrState("u", "stolostron/ocm", 1, "OPEN", False, None).bucket
        == "awaiting_approval"
    )


def test_apply_pr_fields_merged_reclassifies_action():
    row = {
        "action": "skipped_existing_pr",
        "pr_url": "https://github.com/stolostron/ocm/pull/767",
        "issue_key": "ACM-1",
    }
    state = PrState(
        url=row["pr_url"],
        repo="stolostron/ocm",
        number=767,
        state="MERGED",
        is_draft=False,
        merged_at="2026-06-22T20:19:32Z",
        title="CVE fix",
    )
    out = apply_pr_fields(row, state)
    assert out["action"] == "pr_merged"
    assert out["pr_state"] == "MERGED"
    assert out["is_draft"] is False
    assert out["merged_at"] == "2026-06-22T20:19:32Z"


def test_apply_pr_fields_open_draft_keeps_action():
    row = {"action": "pr_opened", "pr_url": "https://github.com/stolostron/ocm/pull/800"}
    state = PrState(
        url=row["pr_url"],
        repo="stolostron/ocm",
        number=800,
        state="OPEN",
        is_draft=True,
        merged_at=None,
    )
    out = apply_pr_fields(row, state)
    assert out["action"] == "pr_opened"
    assert out["is_draft"] is True


def test_linkify_pr_refs():
    lookup = {"multicloud-operators-foundation#1319": "https://github.com/stolostron/multicloud-operators-foundation/pull/1319"}
    text = "multicloud-operators-foundation#1319 needs /approve"
    out = linkify_pr_refs(text, lookup)
    assert out.startswith("<https://github.com/stolostron/multicloud-operators-foundation/pull/1319|")
    assert "needs /approve" in out


def test_pr_lookup_from_entries():
    prs = {
        "u": {
            "pr_url": "https://github.com/stolostron/ocm/pull/767",
            "repo": "stolostron/ocm",
            "pr_number": 767,
        }
    }
    lookup = pr_lookup_from_entries(prs)
    assert lookup["ocm#767"] == "https://github.com/stolostron/ocm/pull/767"


def test_stored_pr_state_from_row():
    row = {
        "pr_url": "https://github.com/stolostron/ocm/pull/767",
        "pr_state": "MERGED",
        "is_draft": False,
        "merged_at": "2026-06-22T20:19:32Z",
        "pr_title": "CVE fix",
    }
    state = stored_pr_state_from_row(row)
    assert state is not None
    assert state.state == "MERGED"
    assert state.is_draft is False
    assert state.merged_at == "2026-06-22T20:19:32Z"
    assert state.title == "CVE fix"


def test_stored_pr_state_from_row_is_draft_string_false():
    row = {
        "pr_url": "https://github.com/stolostron/ocm/pull/800",
        "pr_state": "OPEN",
        "is_draft": "false",
    }
    state = stored_pr_state_from_row(row)
    assert state is not None
    assert state.is_draft is False
    assert state.bucket == "awaiting_approval"


def test_stored_pr_state_from_row_is_draft_string_true():
    row = {
        "pr_url": "https://github.com/stolostron/ocm/pull/801",
        "pr_state": "OPEN",
        "is_draft": "True",
    }
    state = stored_pr_state_from_row(row)
    assert state is not None
    assert state.is_draft is True
    assert state.bucket == "draft"


def test_pr_state_from_row_falls_back_when_gh_unavailable(monkeypatch):
    row = {
        "pr_url": "https://github.com/stolostron/ocm/pull/767",
        "pr_state": "OPEN",
        "is_draft": False,
    }
    monkeypatch.setattr("gh_pr_state.fetch_pr_state", lambda _url: None)
    state = pr_state_from_row(row)
    assert state is not None
    assert state.state == "OPEN"
    assert state.is_draft is False


def test_fetch_pr_state_returns_none_on_os_error(monkeypatch):
    def _raise_permission(*_args, **_kwargs):
        raise PermissionError("gh not executable")

    monkeypatch.setattr("gh_pr_state.subprocess.run", _raise_permission)
    assert (
        fetch_pr_state("https://github.com/stolostron/ocm/pull/767") is None
    )
