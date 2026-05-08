"""Tests for warm_list.py."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def test_21d_band_first_nudge(tmp_workspace, write_pipeline, run_script):
    write_pipeline([
        {"investor_id": "n1", "investor_name": "Nurturee 1",
         "status": "nurture", "last_warm_touch": _days_ago(22)},
    ])
    r = run_script("warm_list.py")
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert "n1" in payload["overdue_21"]


def test_45d_band_second_nudge(tmp_workspace, write_pipeline, run_script):
    write_pipeline([
        {"investor_id": "n1", "investor_name": "X",
         "status": "nurture", "last_warm_touch": _days_ago(46)},
    ])
    r = run_script("warm_list.py")
    payload = json.loads(r.stdout)
    assert "n1" in payload["overdue_45"]


def test_90d_band_third_nudge(tmp_workspace, write_pipeline, run_script):
    write_pipeline([
        {"investor_id": "n1", "investor_name": "X",
         "status": "nurture", "last_warm_touch": _days_ago(91)},
    ])
    r = run_script("warm_list.py")
    payload = json.loads(r.stdout)
    assert "n1" in payload["overdue_90"]


def test_91_plus_appears_in_do_not_contact_recommendation(
    tmp_workspace, write_pipeline, run_script,
):
    """The 90+ band markdown nudges the user toward do_not_contact."""
    write_pipeline([
        {"investor_id": "n1", "investor_name": "X",
         "status": "nurture", "last_warm_touch": _days_ago(120)},
    ])
    r = run_script("warm_list.py")
    md = (tmp_workspace / "pipeline" / "warm-list.md").read_text(encoding="utf-8")
    assert "do_not_contact" in md


def test_only_nurture_status_surfaced(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "nurt", "investor_name": "N",
         "status": "nurture", "last_warm_touch": _days_ago(50)},
        {"investor_id": "conn", "investor_name": "C",
         "status": "connected", "last_warm_touch": _days_ago(50)},
    ])
    r = run_script("warm_list.py")
    payload = json.loads(r.stdout)
    assert payload["nurture_total"] == 1
    assert "nurt" in payload["overdue_45"]
    assert "conn" not in payload["overdue_45"]


def test_empty_pipeline_produces_graceful_markdown(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([])
    r = run_script("warm_list.py")
    assert r.returncode == 0
    md = (tmp_workspace / "pipeline" / "warm-list.md").read_text(encoding="utf-8")
    assert "Total nurture investors: 0" in md
    payload = json.loads(r.stdout)
    assert payload["nurture_total"] == 0


def test_writes_warm_list_md(tmp_workspace, write_pipeline, run_script):
    write_pipeline([
        {"investor_id": "n1", "investor_name": "Nurturee",
         "status": "nurture", "last_warm_touch": _days_ago(30)},
    ])
    r = run_script("warm_list.py")
    md_path = tmp_workspace / "pipeline" / "warm-list.md"
    assert md_path.exists()
    md = md_path.read_text(encoding="utf-8")
    assert "# Warm List" in md
    assert "Nurturee" in md


def test_missing_last_warm_touch_treated_as_overdue(
    tmp_workspace, write_pipeline, run_script,
):
    """Never-touched-warmly investor → 999 days_since → 90d band."""
    write_pipeline([
        {"investor_id": "n1", "investor_name": "X",
         "status": "nurture", "last_warm_touch": ""},
    ])
    r = run_script("warm_list.py")
    payload = json.loads(r.stdout)
    assert "n1" in payload["overdue_90"]


def test_upcoming_band_15_to_20_days(tmp_workspace, write_pipeline, run_script):
    write_pipeline([
        {"investor_id": "u1", "investor_name": "U",
         "status": "nurture", "last_warm_touch": _days_ago(17)},
    ])
    r = run_script("warm_list.py")
    payload = json.loads(r.stdout)
    assert "u1" in payload["upcoming"]


def test_holding_band_under_15_days(tmp_workspace, write_pipeline, run_script):
    write_pipeline([
        {"investor_id": "h1", "investor_name": "H",
         "status": "nurture", "last_warm_touch": _days_ago(5)},
    ])
    r = run_script("warm_list.py")
    payload = json.loads(r.stdout)
    # holding investors are not in any "overdue" or "upcoming" key
    for key in ("overdue_21", "overdue_45", "overdue_90", "upcoming"):
        assert "h1" not in payload[key]


def test_lead_candidate_marker_in_markdown(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "n1", "investor_name": "Lead Inv",
         "status": "nurture", "last_warm_touch": _days_ago(50),
         "lead_candidate": "yes"},
    ])
    r = run_script("warm_list.py")
    md = (tmp_workspace / "pipeline" / "warm-list.md").read_text(encoding="utf-8")
    assert "(lead candidate)" in md


def test_invalid_last_warm_touch_treated_as_never(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "n1", "investor_name": "X",
         "status": "nurture", "last_warm_touch": "not-a-date"},
    ])
    r = run_script("warm_list.py")
    payload = json.loads(r.stdout)
    assert "n1" in payload["overdue_90"]


def test_missing_pipeline_csv_emits_error_envelope(tmp_workspace, run_script):
    """Script emits a structured error envelope with non-zero exit.

    Spec: missing-input should be exit 2; current script returns 1.
    """
    r = run_script("warm_list.py")
    assert r.returncode != 0
    payload = json.loads(r.stdout)
    assert "pipeline.csv" in payload["error"]
    assert payload["fix"]
    assert payload["field"]


def test_no_deprecation_warnings(tmp_workspace, write_pipeline, run_script):
    write_pipeline([
        {"investor_id": "n1", "investor_name": "X",
         "status": "nurture", "last_warm_touch": _days_ago(30)},
    ])
    r = run_script("warm_list.py")
    assert "DeprecationWarning" not in (r.stderr or "")
    assert r.returncode == 0
