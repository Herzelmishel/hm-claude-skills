"""Tests for campaign_summary.py."""
from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path

import pytest


def _today() -> str:
    return date.today().isoformat()


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def test_writes_weekly_summary_md_on_populated_workspace(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    write_pipeline([
        {"investor_id": "inv_1", "investor_name": "A", "status": "soft_commit"},
        {"investor_id": "inv_2", "investor_name": "B", "status": "pass"},
    ])
    write_touches([
        {"investor_id": "inv_1", "touch_date": _today(),
         "status_after": "connection_sent", "estimated_minutes": "15"},
        {"investor_id": "inv_1", "touch_date": _today(),
         "status_after": "connected", "estimated_minutes": "5"},
    ])
    write_commitments([
        {"investor_id": "inv_1", "soft_commit_amount": "25000"},
    ])
    r = run_script("campaign_summary.py")
    assert r.returncode == 0, r.stdout + r.stderr
    summary_path = tmp_workspace / "pipeline" / "weekly-summary.md"
    assert summary_path.exists()
    text = summary_path.read_text(encoding="utf-8")
    assert "# Weekly Summary" in text
    assert "Conversion Math" in text


def test_conversion_math_event_based_denominators(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    """Denominators come from touches.csv unique counts, not pipeline.csv."""
    write_pipeline([
        {"investor_id": f"inv_{i}", "status": "connected"} for i in range(1, 6)
    ])
    # 5 connection_sent, 4 connected → 80% accept rate
    touches = []
    for i in range(1, 6):
        touches.append({"investor_id": f"inv_{i}", "touch_date": _today(),
                        "status_after": "connection_sent",
                        "estimated_minutes": "15"})
    for i in range(1, 5):
        touches.append({"investor_id": f"inv_{i}", "touch_date": _today(),
                        "status_after": "connected",
                        "estimated_minutes": "5"})
    write_touches(touches)
    write_commitments([])

    r = run_script("campaign_summary.py")
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert payload["rates"]["accept_rate"] == pytest.approx(0.8)


def test_unique_counts_dedupe_repeated_status_events(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    """If the same investor logs connection_sent twice, count once."""
    write_pipeline([{"investor_id": "inv_1", "status": "connected"}])
    write_touches([
        {"investor_id": "inv_1", "touch_date": _today(),
         "status_after": "connection_sent", "estimated_minutes": "15"},
        {"investor_id": "inv_1", "touch_date": _today(),
         "status_after": "connection_sent", "estimated_minutes": "15"},
        {"investor_id": "inv_1", "touch_date": _today(),
         "status_after": "connected", "estimated_minutes": "5"},
    ])
    write_commitments([])
    r = run_script("campaign_summary.py")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    # 1 / 1 unique investors → 100%
    assert payload["rates"]["accept_rate"] == 1.0


def test_estimated_hours_per_investor_and_total(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    write_pipeline([
        {"investor_id": "inv_1", "status": "soft_commit"},
        {"investor_id": "inv_2", "status": "pass"},
    ])
    write_touches([
        {"investor_id": "inv_1", "touch_date": _today(),
         "status_after": "intro_call_done", "estimated_minutes": "60"},
        {"investor_id": "inv_2", "touch_date": _today(),
         "status_after": "pass", "estimated_minutes": "120"},
    ])
    write_commitments([])
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    # 60 + 120 = 180 minutes = 3 hours
    assert payload["total_hours"] == pytest.approx(3.0)


def test_hours_per_pass_and_per_commit(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    write_pipeline([
        {"investor_id": "inv_pass", "status": "pass"},
        {"investor_id": "inv_commit", "status": "soft_commit"},
    ])
    write_touches([
        {"investor_id": "inv_pass", "touch_date": _today(),
         "status_after": "pass", "estimated_minutes": "120"},
        {"investor_id": "inv_commit", "touch_date": _today(),
         "status_after": "soft_commit", "estimated_minutes": "60"},
    ])
    write_commitments([])
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    assert payload["hours_per_pass"] == 2.0
    assert payload["hours_per_commit"] == 1.0


def test_bottleneck_low_accept_rate_flag(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    write_pipeline([{"investor_id": f"inv_{i}", "status": "connected"} for i in range(1, 11)])
    touches = []
    for i in range(1, 11):
        touches.append({"investor_id": f"inv_{i}", "touch_date": _today(),
                        "status_after": "connection_sent",
                        "estimated_minutes": "15"})
    # Only 1/10 connected → 10% (below 30% threshold)
    touches.append({"investor_id": "inv_1", "touch_date": _today(),
                    "status_after": "connected", "estimated_minutes": "5"})
    write_touches(touches)
    write_commitments([])

    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    flags = payload["bottleneck_flags"]
    assert any("Low accept rate" in f for f in flags)


def test_top5_actions_sorted_by_overdue_then_score(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    write_pipeline([
        {"investor_id": "a", "investor_name": "A", "status": "connected",
         "next_action": "follow up", "next_action_date": _days_ago(10),
         "score_10": "5"},
        {"investor_id": "b", "investor_name": "B", "status": "connected",
         "next_action": "follow up", "next_action_date": _days_ago(20),
         "score_10": "3"},
        {"investor_id": "c", "investor_name": "C", "status": "connected",
         "next_action": "follow up", "next_action_date": _days_ago(20),
         "score_10": "9"},
    ])
    write_touches([])
    write_commitments([])
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    top = payload["top_actions"]
    assert top[0]["investor_id"] == "c"  # 20 overdue, score 9
    assert top[1]["investor_id"] == "b"  # 20 overdue, score 3
    assert top[2]["investor_id"] == "a"  # 10 overdue


def test_empty_workspace_graceful_zeros(
    tmp_workspace, write_pipeline, run_script,
):
    """No touches, no commitments → no division by zero."""
    write_pipeline([{"investor_id": "inv_1", "status": "connected"}])
    r = run_script("campaign_summary.py")
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert payload["total_hours"] == 0.0
    assert payload["rates"]["accept_rate"] == 0.0
    assert payload["bottleneck_flags"] == []


def test_missing_pipeline_csv_emits_error_envelope(
    tmp_workspace, run_script,
):
    """Script emits a structured error envelope with code=2 (missing input)."""
    r = run_script("campaign_summary.py")
    assert r.returncode == 2, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert "pipeline.csv" in payload["error"]
    assert payload["fix"]
    assert payload["field"]
    if "code" in payload:
        assert payload["code"] == 2


def test_momentum_score_rewards_recent_activity(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    write_pipeline([{"investor_id": "x", "status": "soft_commit"}])
    write_touches([
        {"investor_id": "x", "touch_date": _today(),
         "status_after": "soft_commit", "estimated_minutes": "60"},
        {"investor_id": "x", "touch_date": _today(),
         "status_after": "replied_positive", "estimated_minutes": "5"},
    ])
    write_commitments([])
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    assert payload["momentum_score"] >= 70
    assert payload["momentum_score"] <= 100


def test_commitments_amounts_summed(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    write_pipeline([{"investor_id": "x", "status": "signed_safe"}])
    write_touches([])
    write_commitments([
        {"investor_id": "x", "soft_commit_amount": "10000",
         "signed_safe_amount": "25000", "cash_received_amount": "0"},
        {"investor_id": "y", "soft_commit_amount": "5000"},
    ])
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    assert payload["soft_commit_amount"] == 15000.0
    assert payload["signed_amount"] == 25000.0


def test_invalid_estimated_minutes_falls_back_to_zero(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([{"investor_id": "x", "status": "connected"}])
    write_touches([
        {"investor_id": "x", "touch_date": _today(),
         "status_after": "connection_sent", "estimated_minutes": "not-a-number"},
    ])
    r = run_script("campaign_summary.py")
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert payload["total_hours"] == 0.0


def test_invalid_score_10_falls_back_to_zero(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "x", "status": "connected",
         "next_action": "follow", "next_action_date": _days_ago(2),
         "score_10": "bogus"},
    ])
    write_touches([])
    r = run_script("campaign_summary.py")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["top_actions"][0]["score_10"] == 0.0


def test_no_deprecation_warnings(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "x", "status": "connected"}])
    r = run_script("campaign_summary.py")
    assert "DeprecationWarning" not in (r.stderr or "")
    assert r.returncode == 0


def test_top5_truncates_to_5(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": f"i{n}", "status": "connected",
         "next_action": "x", "next_action_date": _days_ago(n + 1),
         "score_10": "5"}
        for n in range(7)
    ])
    write_touches([])
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    assert len(payload["top_actions"]) == 5


def test_pipeline_rows_without_next_action_are_excluded_from_top(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "x", "status": "connected"},
    ])
    write_touches([])
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    assert payload["top_actions"] == []


def test_invalid_next_action_date_treated_as_no_overdue(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """parse_iso ValueError branch: bogus date string."""
    write_pipeline([
        {"investor_id": "x", "status": "connected",
         "next_action": "ping", "next_action_date": "not-a-date",
         "score_10": "5"},
    ])
    write_touches([])
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    assert payload["top_actions"][0]["days_overdue"] == -999


def test_empty_next_action_date_treated_as_no_overdue(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """parse_iso empty-string branch."""
    write_pipeline([
        {"investor_id": "x", "status": "connected",
         "next_action": "ping", "next_action_date": "",
         "score_10": "5"},
    ])
    write_touches([])
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    assert payload["top_actions"][0]["days_overdue"] == -999


def test_invalid_commitment_amount_falls_back_to_zero(
    tmp_workspace, write_pipeline, write_touches, write_commitments, run_script,
):
    """safe_float ValueError branch."""
    write_pipeline([{"investor_id": "x", "status": "soft_commit"}])
    write_touches([])
    write_commitments([
        {"investor_id": "x", "soft_commit_amount": "not-a-number"},
    ])
    r = run_script("campaign_summary.py")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["soft_commit_amount"] == 0.0


def test_low_reply_rate_flag(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """Low reply rate threshold."""
    write_pipeline([{"investor_id": f"i{n}", "status": "connected"}
                    for n in range(20)])
    touches = []
    for n in range(20):
        touches.append({"investor_id": f"i{n}", "touch_date": _today(),
                        "status_after": "first_dm_sent",
                        "estimated_minutes": "15"})
    # Only 1/20 = 5% reply
    touches.append({"investor_id": "i0", "touch_date": _today(),
                    "status_after": "replied_negative", "estimated_minutes": "5"})
    write_touches(touches)
    r = run_script("campaign_summary.py")
    payload = json.loads(r.stdout)
    assert any("reply rate" in f.lower() for f in payload["bottleneck_flags"])


def test_invalid_touch_date_in_momentum_calc_skipped(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """Bad touch_date doesn't crash momentum calc."""
    write_pipeline([{"investor_id": "x", "status": "soft_commit"}])
    write_touches([
        {"investor_id": "x", "touch_date": "not-a-date",
         "status_after": "soft_commit", "estimated_minutes": "60"},
    ])
    r = run_script("campaign_summary.py")
    assert r.returncode == 0
