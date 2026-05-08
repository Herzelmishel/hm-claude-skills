"""Tests for preseed-campaign/scripts/momentum_check.py."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone

import pytest


def _import():
    if "momentum_check" in sys.modules:
        del sys.modules["momentum_check"]
    import momentum_check
    return momentum_check


def _today_str(offset_days: int = 0) -> str:
    return (date.today() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Pure-function tests — momentum_score formula
# ---------------------------------------------------------------------------

def test_momentum_score_when_one_of_each_signal_then_100():
    """Regression: 1 commit + 1 reply + 1 call → 100."""
    mc = _import()
    today = date.today()
    touches = [
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "soft_commit"},
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "replied_positive"},
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "intro_call_booked"},
    ]
    assert mc.compute_momentum_score(touches, today) == 100


def test_momentum_score_when_only_5_commits_then_clamped_to_40():
    mc = _import()
    today = date.today()
    touches = [
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "soft_commit"}
        for _ in range(5)
    ]
    assert mc.compute_momentum_score(touches, today) == 40


def test_momentum_score_when_zero_signals_then_zero():
    mc = _import()
    assert mc.compute_momentum_score([], date.today()) == 0


def test_momentum_score_partner_meeting_counts_as_call():
    """Regression: partner_meeting_booked must count as a call."""
    mc = _import()
    today = date.today()
    touches = [
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "partner_meeting_booked"},
    ]
    assert mc.compute_momentum_score(touches, today) == 30


def test_momentum_score_ignores_old_touches():
    mc = _import()
    today = date.today()
    old = today - timedelta(days=30)
    touches = [
        {"touch_date": old.strftime("%Y-%m-%d"), "status_after": "soft_commit"},
    ]
    assert mc.compute_momentum_score(touches, today) == 0


def test_momentum_score_ignores_invalid_dates():
    mc = _import()
    touches = [
        {"touch_date": "not a date", "status_after": "soft_commit"},
        {"touch_date": "", "status_after": "soft_commit"},
    ]
    assert mc.compute_momentum_score(touches, date.today()) == 0


# ---------------------------------------------------------------------------
# Velocity status
# ---------------------------------------------------------------------------

def test_velocity_status_stalled_when_old_wave_no_progress():
    mc = _import()
    today = date.today()
    wave_started = today - timedelta(days=20)
    assert mc.compute_velocity_status([], wave_started, today, 0) == "STALLED"


def test_velocity_status_warning_when_no_wave():
    mc = _import()
    assert mc.compute_velocity_status([], None, date.today(), 0) == "WARNING"


def test_velocity_status_healthy_when_recent_commit():
    mc = _import()
    today = date.today()
    wave_started = today - timedelta(days=3)
    touches = [
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "soft_commit"},
    ]
    assert mc.compute_velocity_status(touches, wave_started, today, 100) == "HEALTHY"


def test_velocity_status_healthy_via_score_threshold():
    mc = _import()
    today = date.today()
    wave_started = today - timedelta(days=2)
    assert mc.compute_velocity_status([], wave_started, today, 60) == "HEALTHY"


def test_velocity_status_warning_in_between():
    mc = _import()
    today = date.today()
    wave_started = today - timedelta(days=10)  # not yet stalled
    # No commits, no partner meetings, score below 50 → WARNING
    assert mc.compute_velocity_status([], wave_started, today, 30) == "WARNING"


def test_velocity_status_stalled_only_when_no_commits_and_no_meetings():
    mc = _import()
    today = date.today()
    wave_started = today - timedelta(days=20)
    touches = [
        {"touch_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
         "status_after": "partner_meeting_booked"},
    ]
    # 1 partner meeting since wave_started → not stalled
    assert mc.compute_velocity_status(touches, wave_started, today, 0) != "STALLED"


def test_velocity_status_healthy_via_three_partner_meetings_in_14d():
    mc = _import()
    today = date.today()
    wave_started = today - timedelta(days=10)
    touches = [
        {"touch_date": (today - timedelta(days=2 * i)).strftime("%Y-%m-%d"),
         "status_after": "partner_meeting_booked"}
        for i in range(3)
    ]
    assert mc.compute_velocity_status(touches, wave_started, today, 0) == "HEALTHY"


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "today_score,prev,expected",
    [
        (100, 50, "up"),
        (50, 100, "down"),
        (50, 50, "flat"),
        (50, None, "unknown"),
        (50, "garbage", "unknown"),
        (60, 55, "flat"),  # within ±10
    ],
)
def test_compute_trend(today_score, prev, expected):
    mc = _import()
    assert mc.compute_trend(today_score, prev) == expected


# ---------------------------------------------------------------------------
# Time-to-close
# ---------------------------------------------------------------------------

def test_time_to_close_required_per_day_calculation():
    mc = _import()
    today = date.today()
    target_date = today + timedelta(days=10)
    # 4 intro_call_done, 2 soft_commit → 50% conversion
    touches = [
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "intro_call_done"},
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "intro_call_done"},
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "intro_call_done"},
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "intro_call_done"},
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "soft_commit"},
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "soft_commit"},
    ]
    commitments = [
        {"soft_commit_amount": "50000"},
        {"soft_commit_amount": "100000"},
    ]
    out = mc.compute_time_to_close(touches, commitments, 500_000.0, target_date, today)
    assert out["call_to_commit_rate"] == 0.5
    assert out["avg_check_usd"] == 75_000.0
    assert out["expected_per_call_usd"] == 37_500.0
    assert out["days_remaining"] == 10
    assert out["gap_remaining_usd"] is not None
    assert out["required_per_day"] is not None


def test_time_to_close_warns_when_pace_exceeds_capacity():
    mc = _import()
    today = date.today()
    target_date = today + timedelta(days=2)
    # 1 intro_call done, 1 commit at $25k → expected_per_call=25k, gap=475k → calls_needed=19, /2 days = 9.5/day
    touches = [
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "intro_call_done"},
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "soft_commit"},
    ]
    commitments = [{"soft_commit_amount": "25000"}]
    out = mc.compute_time_to_close(touches, commitments, 500_000.0, target_date, today)
    assert out["required_per_day"] > 2
    assert any("solo-founder capacity" in w for w in out["warnings"])


def test_time_to_close_warns_when_pace_too_slow():
    mc = _import()
    today = date.today()
    target_date = today + timedelta(days=300)
    touches = [
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "intro_call_done"},
        {"touch_date": today.strftime("%Y-%m-%d"), "status_after": "soft_commit"},
    ]
    commitments = [{"soft_commit_amount": "100000"}]
    out = mc.compute_time_to_close(touches, commitments, 500_000.0, target_date, today)
    if out["required_per_day"] is not None:
        assert out["required_per_day"] < 0.3
        assert any("too slow" in w.lower() for w in out["warnings"])


def test_time_to_close_handles_zero_commitments():
    """Regression: division-by-zero must be handled gracefully."""
    mc = _import()
    today = date.today()
    out = mc.compute_time_to_close([], [], 500_000.0, today + timedelta(days=10), today)
    assert out["avg_check_usd"] == 50_000.0  # default fallback
    assert out["call_to_commit_rate"] == 0.0
    assert out["expected_per_call_usd"] == 0.0
    assert out["calls_needed"] is None
    assert out["required_per_day"] is None


def test_time_to_close_uses_signed_safe_when_available():
    mc = _import()
    commitments = [
        {"signed_safe_amount": "100000", "soft_commit_amount": "50000"},
        {"signed_safe_amount": "150000", "soft_commit_amount": "150000"},
    ]
    out = mc.compute_time_to_close([], commitments, 500_000.0, None, date.today())
    assert out["current_committed_usd"] == 250_000.0


def test_time_to_close_when_no_target_amount_then_no_gap():
    mc = _import()
    out = mc.compute_time_to_close([], [], None, None, date.today())
    assert out["gap_remaining_usd"] is None
    assert out["calls_needed"] is None


# ---------------------------------------------------------------------------
# YAML round-trip
# ---------------------------------------------------------------------------

def test_parse_campaign_yaml_extracts_top_level_scalars():
    mc = _import()
    text = (
        "version: 1\n"
        "company: Agentis\n"
        'note: "with: colon"\n'
        "active: true\n"
        "missing: null\n"
        "ratio: 0.5\n"
    )
    out = mc.parse_campaign_yaml(text)
    assert out["version"] == 1
    assert out["company"] == "Agentis"
    assert out["note"] == "with: colon"
    assert out["active"] is True
    assert out["missing"] is None
    assert out["ratio"] == 0.5


def test_upsert_campaign_yaml_updates_in_place(tmp_workspace):
    mc = _import()
    path = tmp_workspace / "campaign.yaml"
    mc.upsert_campaign_yaml(path, {"momentum_score": 75, "velocity_status": "HEALTHY"})
    text = path.read_text(encoding="utf-8")
    assert "momentum_score: 75" in text
    assert "velocity_status: HEALTHY" in text


def test_upsert_campaign_yaml_appends_missing_keys(tmp_workspace):
    mc = _import()
    path = tmp_workspace / "campaign.yaml"
    mc.upsert_campaign_yaml(path, {"new_key_xyz": "abc"})
    text = path.read_text(encoding="utf-8")
    assert "new_key_xyz: abc" in text
    assert "managed by momentum_check.py" in text


def test_yaml_scalar_quotes_strings_with_special_chars():
    mc = _import()
    assert mc._yaml_scalar(None) == "null"
    assert mc._yaml_scalar(True) == "true"
    assert mc._yaml_scalar(False) == "false"
    assert mc._yaml_scalar(42) == "42"
    assert mc._yaml_scalar("simple") == "simple"
    assert mc._yaml_scalar("has: colon").startswith('"')


def test_parse_money_handles_garbage():
    mc = _import()
    assert mc.parse_money(None) == 0.0
    assert mc.parse_money("") == 0.0
    assert mc.parse_money("$50,000") == 50000.0
    assert mc.parse_money("not-money") == 0.0
    assert mc.parse_money("-") == 0.0


def test_parse_date_handles_multiple_formats():
    mc = _import()
    assert mc.parse_date("2026-05-08") == date(2026, 5, 8)
    assert mc.parse_date("2026-05-08T10:00:00") == date(2026, 5, 8)
    assert mc.parse_date("2026-05-08 10:00:00") == date(2026, 5, 8)
    assert mc.parse_date("garbage") is None
    assert mc.parse_date(None) is None
    assert mc.parse_date("") is None


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

def test_main_when_no_campaign_yaml_then_envelope(empty_home, capsys):
    mc = _import()
    with pytest.raises(SystemExit) as exc:
        mc.main([])
    assert exc.value.code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "campaign.yaml not found" in payload["error"]


def test_main_writes_momentum_to_campaign_yaml(
        tmp_workspace, sample_pipeline_state, capsys):
    mc = _import()
    today = date.today()
    sample_pipeline_state(
        tmp_workspace,
        touches=[
            {"touch_date": today.strftime("%Y-%m-%d"),
             "status_after": "soft_commit",
             "investor_id": "x"},
        ],
        commitments=[{"soft_commit_amount": "50000", "investor_id": "x"}],
    )
    with pytest.raises(SystemExit) as exc:
        mc.main([])
    assert exc.value.code == 0
    text = (tmp_workspace / "campaign.yaml").read_text(encoding="utf-8")
    assert "momentum_score: 40" in text
    assert "velocity_status:" in text
    assert "last_momentum_check_date:" in text


def test_main_uses_timezone_aware_datetime_for_check_date(
        tmp_workspace, sample_pipeline_state, capsys):
    """Regression: last_momentum_check_date should match today's UTC date."""
    mc = _import()
    sample_pipeline_state(tmp_workspace)
    with pytest.raises(SystemExit):
        mc.main([])
    text = (tmp_workspace / "campaign.yaml").read_text(encoding="utf-8")
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert today_utc in text


def test_main_no_write_flag_skips_yaml_update(
        tmp_workspace, sample_pipeline_state, capsys):
    mc = _import()
    sample_pipeline_state(tmp_workspace)
    before = (tmp_workspace / "campaign.yaml").read_text(encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        mc.main(["--no-write"])
    assert exc.value.code == 0
    after = (tmp_workspace / "campaign.yaml").read_text(encoding="utf-8")
    assert before == after


def test_main_workspace_flag_overrides_default(tmp_path, monkeypatch, capsys):
    mc = _import()
    custom = tmp_path / "custom-fundraising"
    custom.mkdir()
    (custom / "pipeline").mkdir()
    (custom / "campaign.yaml").write_text(
        "company: X\nmomentum_score: null\n", encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc:
        mc.main(["--workspace", str(custom)])
    assert exc.value.code == 0


def test_read_csv_dicts_returns_empty_for_missing_file(tmp_path):
    mc = _import()
    assert mc.read_csv_dicts(tmp_path / "missing.csv") == []
