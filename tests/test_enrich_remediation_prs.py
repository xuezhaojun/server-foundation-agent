"""Tests for workflows/fix-cve/enrich_remediation_prs.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflows" / "fix-cve"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflows" / "lib"))

from enrich_remediation_prs import enrich, resolve_remediation_path  # noqa: E402


def test_enrich_uses_stored_pr_state_when_gh_unavailable(tmp_path, monkeypatch):
    path = tmp_path / "remediation.json"
    rows = [
        {
            "action": "skipped_existing_pr",
            "pr_url": "https://github.com/stolostron/ocm/pull/767",
            "pr_state": "MERGED",
            "is_draft": False,
            "merged_at": "2026-06-22T20:19:32Z",
            "issue_key": "ACM-1",
        }
    ]
    path.write_text(json.dumps(rows), encoding="utf-8")

    monkeypatch.setattr("enrich_remediation_prs.fetch_pr_state", lambda _url: None)

    out, refreshed = enrich(path)
    assert refreshed == 0
    assert out[0]["action"] == "pr_merged"
    assert out[0]["pr_state"] == "MERGED"
    assert json.loads(path.read_text(encoding="utf-8"))[0]["action"] == "pr_merged"


def test_enrich_prefers_live_gh_state(tmp_path, monkeypatch):
    from gh_pr_state import PrState  # noqa: E402

    path = tmp_path / "remediation.json"
    url = "https://github.com/stolostron/ocm/pull/800"
    rows = [
        {
            "action": "pr_opened",
            "pr_url": url,
            "pr_state": "OPEN",
            "is_draft": True,
            "issue_key": "ACM-2",
        }
    ]
    path.write_text(json.dumps(rows), encoding="utf-8")

    live = PrState(
        url=url,
        repo="stolostron/ocm",
        number=800,
        state="OPEN",
        is_draft=False,
        merged_at=None,
        title="Ready PR",
    )
    monkeypatch.setattr("enrich_remediation_prs.fetch_pr_state", lambda _url: live)

    out, refreshed = enrich(path)
    assert refreshed == 1
    assert out[0]["is_draft"] is False
    assert out[0]["pr_title"] == "Ready PR"


def test_resolve_remediation_path_accepts_path_under_output_dir(tmp_path):
    base = tmp_path / "cve-analysis"
    base.mkdir()
    remediation = base / "remediation.json"
    remediation.write_text("[]", encoding="utf-8")
    resolved = resolve_remediation_path(str(remediation), allowed_base=base)
    assert resolved == remediation.resolve()


def test_resolve_remediation_path_rejects_traversal(tmp_path):
    base = tmp_path / "cve-analysis"
    base.mkdir()
    outside = tmp_path / "secret.json"
    outside.write_text("[]", encoding="utf-8")
    try:
        resolve_remediation_path(str(outside), allowed_base=base)
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 1
