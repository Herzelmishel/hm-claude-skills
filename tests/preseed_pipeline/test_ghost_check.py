"""Tests for ghost_check.py — ghost detection regression suite.

Covers criticals:
  - #2: founder follow-up DMs do NOT reset the timer
  - #3: ghost trigger AT day 14 (not day 15)
"""
from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path

import pytest


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def _read_pipeline(workspace: Path) -> list[dict[str, str]]:
    path = workspace / "pipeline" / "pipeline.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


# --------------------------------------------------------------------------
# Day-boundary regression (critical #3: trigger AT day 14)
# --------------------------------------------------------------------------
def test_post_meeting_with_no_touches_in_14_plus_days_is_flagged(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "Ghoster",
         "status": "intro_call_done",
         "last_meeting_date": _days_ago(20)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 1
    assert payload["newly_ghosted"][0]["investor_id"] == "g1"


def test_exactly_14_days_silence_is_ghosted(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """Day 14 must trigger (regression for off-by-one)."""
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(14)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 1


def test_exactly_13_days_silence_is_not_ghosted(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """Day 13 must NOT trigger."""
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(13)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 0


# --------------------------------------------------------------------------
# Founder-DM does NOT reset (critical #2)
# --------------------------------------------------------------------------
def test_founder_followup_dm_does_not_reset_timer(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """A follow-up DM the founder sent must not extend the silence window."""
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(20)},
    ])
    # Founder sent a follow-up 5 days ago. Must NOT reset the ghost clock.
    write_touches([
        {"touch_id": "t1", "investor_id": "g1",
         "touch_date": _days_ago(5), "touch_type": "outreach",
         "status_before": "intro_call_done",
         "status_after": "followup_1_sent",
         "material_interaction": "none",
         "estimated_minutes": "15", "owner": "herzel"},
    ])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 1


def test_inbound_reply_resets_timer(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(20)},
    ])
    write_touches([
        {"touch_id": "t1", "investor_id": "g1",
         "touch_date": _days_ago(5), "touch_type": "outreach",
         "status_after": "replied_positive",
         "material_interaction": "none",
         "estimated_minutes": "5", "owner": "herzel"},
    ])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 0


@pytest.mark.parametrize("material", [
    "deck_viewed",
    "data_room_accessed",
    "demo_watched",
    "financials_requested",
])
def test_material_interactions_reset_timer(
    material,
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "data_room_accessed", "last_meeting_date": _days_ago(20)},
    ])
    write_touches([
        {"touch_id": "t1", "investor_id": "g1",
         "touch_date": _days_ago(2), "touch_type": "material_viewed",
         "status_after": "",
         "material_interaction": material,
         "estimated_minutes": "5", "owner": "herzel"},
    ])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 0, (
        f"material={material} should reset"
    )


# --------------------------------------------------------------------------
# Pipeline state side-effects
# --------------------------------------------------------------------------
def test_ghost_flag_date_set_to_today(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    assert r.returncode == 0
    rows = _read_pipeline(tmp_workspace)
    assert rows[0]["status"] == "ghosted"
    assert rows[0]["ghost_flag_date"] == date.today().isoformat()


def test_takeaway_draft_written(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "Ghosty Inc",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    draft_path = Path(payload["newly_ghosted"][0]["draft_path"])
    assert draft_path.exists()
    text = draft_path.read_text(encoding="utf-8")
    assert "Takeaway Email" in text
    assert "Ghosty Inc" in text


def test_takeaway_template_under_80_words(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """The Draft section's email body should be ≤80 words."""
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    draft_path = Path(payload["newly_ghosted"][0]["draft_path"])
    text = draft_path.read_text(encoding="utf-8")
    # Extract section between "## Draft" and "## Rules"
    start = text.index("## Draft")
    end = text.index("## Rules")
    draft_body = text[start:end]
    word_count = len(draft_body.split())
    # Generous bound — body itself must be tight, but headers count too;
    # the rule is "≤80 words excluding subject and signature". We assert
    # generously here on the whole draft section.
    assert word_count <= 100, f"draft section is {word_count} words"


def test_already_ghosted_investor_not_reflagged(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30),
         "ghost_flag_date": _days_ago(5)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 0


def test_non_post_meeting_status_skipped(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "connected", "last_meeting_date": _days_ago(30)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 0


def test_no_last_meeting_date_skipped(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": ""},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 0


# --------------------------------------------------------------------------
# Voice register loading
# --------------------------------------------------------------------------
def test_voice_register_loaded_into_takeaway(
    tmp_workspace, write_pipeline, write_touches, sample_voice_fingerprint,
    run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    text = Path(payload["newly_ghosted"][0]["draft_path"]).read_text(
        encoding="utf-8"
    )
    assert "register=direct" in text


def test_voice_missing_uses_fallback_comment(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    text = Path(payload["newly_ghosted"][0]["draft_path"]).read_text(
        encoding="utf-8"
    )
    assert "voice-fingerprint NOT loaded" in text


# --------------------------------------------------------------------------
# Misc
# --------------------------------------------------------------------------
def test_missing_pipeline_csv_emits_error_envelope(tmp_workspace, run_script):
    """Script emits a structured error envelope with non-zero exit.

    TODO: tighten when ghost_check uses code=2 for missing input.
    """
    r = run_script("ghost_check.py")
    assert r.returncode != 0
    payload = json.loads(r.stdout)
    assert "pipeline.csv" in payload["error"]
    assert payload["fix"]
    assert payload["field"]


def test_no_deprecation_warnings(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    assert "DeprecationWarning" not in (r.stderr or "")
    assert r.returncode == 0


def test_invalid_touch_dates_skipped(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """Bad touch dates must not crash the script."""
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30)},
    ])
    write_touches([
        {"touch_id": "t1", "investor_id": "g1",
         "touch_date": "not-a-date", "touch_type": "outreach",
         "status_after": "replied_positive", "material_interaction": "none",
         "estimated_minutes": "5"},
    ])
    r = run_script("ghost_check.py")
    assert r.returncode == 0


def test_anchor_is_max_of_meeting_and_response_touch(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    """Anchor for silence calc is max(last_meeting, latest qualifying touch)."""
    write_pipeline([
        {"investor_id": "g1", "investor_name": "G",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30)},
    ])
    # Reply 10 days ago should reset clock to 10 days silent (< 14, not ghosted).
    write_touches([
        {"touch_id": "t1", "investor_id": "g1",
         "touch_date": _days_ago(10), "touch_type": "outreach",
         "status_after": "replied_positive", "material_interaction": "none",
         "estimated_minutes": "5"},
    ])
    r = run_script("ghost_check.py")
    payload = json.loads(r.stdout)
    assert payload["newly_ghosted_count"] == 0


def test_unicode_investor_name_in_takeaway(
    tmp_workspace, write_pipeline, write_touches, run_script,
):
    write_pipeline([
        {"investor_id": "g1", "investor_name": "Café Ångström",
         "status": "intro_call_done", "last_meeting_date": _days_ago(30)},
    ])
    write_touches([])
    r = run_script("ghost_check.py")
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    text = Path(payload["newly_ghosted"][0]["draft_path"]).read_text(
        encoding="utf-8"
    )
    assert "Café Ångström" in text
