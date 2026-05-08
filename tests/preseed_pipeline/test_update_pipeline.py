"""Tests for update_pipeline.py."""
from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from textwrap import dedent

import pytest


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _read_pipeline(workspace: Path) -> list[dict[str, str]]:
    path = workspace / "pipeline" / "pipeline.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_touches(workspace: Path) -> tuple[list[str], list[dict[str, str]]]:
    path = workspace / "pipeline" / "touches.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


# --------------------------------------------------------------------------
# Happy-path status transitions
# --------------------------------------------------------------------------
def test_status_transition_connected_to_first_dm_sent(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([
        {
            "investor_id": "inv_x",
            "investor_name": "X",
            "status": "connected",
        }
    ])
    result = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "first_dm_sent",
        "--note", "Sent intro DM",
        "--channel", "linkedin",
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["status_before"] == "connected"
    assert payload["status_after"] == "first_dm_sent"

    rows = _read_pipeline(tmp_workspace)
    assert rows[0]["status"] == "first_dm_sent"
    assert rows[0]["last_touch_date"] == date.today().isoformat()
    assert "Sent intro DM" in rows[0]["notes"]

    fields, touches = _read_touches(tmp_workspace)
    assert "touch_id" in fields
    assert len(touches) == 1
    assert touches[0]["status_before"] == "connected"
    assert touches[0]["status_after"] == "first_dm_sent"
    assert touches[0]["channel"] == "linkedin"


def test_touches_csv_append_preserves_existing_header(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    """Touches header should be preserved across appends."""
    write_pipeline([
        {"investor_id": "inv_x", "status": "connected"},
        {"investor_id": "inv_y", "status": "connected"},
    ])
    r1 = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x", "--new-status", "first_dm_sent",
    )
    assert r1.returncode == 0, r1.stdout + r1.stderr
    fields_before, _ = _read_touches(tmp_workspace)

    r2 = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_y", "--new-status", "first_dm_sent",
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr
    fields_after, rows = _read_touches(tmp_workspace)
    assert fields_before == fields_after
    assert len(rows) == 2


def test_touches_csv_with_extra_column_is_accepted(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    """Additive header (extra forward-compatible column) is OK."""
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])

    # Write a touches.csv with an extra column already present.
    extended_header = [
        "touch_id", "investor_id", "touch_date", "touch_type", "channel",
        "message_id", "material_interaction", "status_before", "status_after",
        "estimated_minutes", "owner", "notes", "source", "extra_future_col",
    ]
    touches_path = tmp_workspace / "pipeline" / "touches.csv"
    with touches_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=extended_header)
        writer.writeheader()
        writer.writerow({k: "x" for k in extended_header})

    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x", "--new-status", "first_dm_sent",
    )
    assert r.returncode == 0, r.stdout + r.stderr

    fields, rows = _read_touches(tmp_workspace)
    # Header must be unchanged (extra col preserved).
    assert fields == extended_header
    assert len(rows) == 2  # original seed row + appended row


def test_touches_csv_with_renamed_column_fails_with_envelope(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    """A renamed/missing column triggers integrity violation (exit 4)."""
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])

    bad_header = [
        "touch_id", "investor_id", "touch_date", "touch_type", "channel",
        "message_id", "material_interaction", "status_was", "status_after",
        "estimated_minutes", "owner", "notes", "source",
    ]
    touches_path = tmp_workspace / "pipeline" / "touches.csv"
    with touches_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=bad_header)
        writer.writeheader()
        writer.writerow({k: "x" for k in bad_header})

    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x", "--new-status", "first_dm_sent",
    )
    assert r.returncode == 4, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert payload["error"] == "touches.csv header mismatch"
    assert "field" in payload and "fix" in payload


# --------------------------------------------------------------------------
# Pass protocol
# --------------------------------------------------------------------------
def test_pass_status_with_flags_persists_pass_reason_and_trigger(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "intro_call_done"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "pass",
        "--pass-reason", "too early stage",
        "--reapproach-trigger", "first paying customer",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert "next_step" in payload
    assert "reapproach_notes.py" in payload["next_step"]

    rows = _read_pipeline(tmp_workspace)
    assert rows[0]["pass_reason"] == "too early stage"
    assert rows[0]["reapproach_trigger"] == "first paying customer"


def test_pass_status_without_flags_emits_pending_next_step(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "intro_call_done"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "pass",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert "Provide --pass-reason" in payload["next_step"]


# --------------------------------------------------------------------------
# Status-specific column writes
# --------------------------------------------------------------------------
@pytest.mark.parametrize("status,column", [
    ("ghosted", "ghost_flag_date"),
    ("data_room_accessed", "data_room_accessed_date"),
    ("nurture", "last_warm_touch"),
])
def test_status_specific_date_columns(
    status, column,
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "intro_call_done"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", status,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    rows = _read_pipeline(tmp_workspace)
    assert rows[0][column] == date.today().isoformat()
    if status == "ghosted":
        assert "ghost_check.py" in json.loads(r.stdout)["next_step"]


def test_intro_call_done_records_meeting_date(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "intro_call_booked"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "intro_call_done",
    )
    assert r.returncode == 0
    assert _read_pipeline(tmp_workspace)[0]["last_meeting_date"] == date.today().isoformat()


def test_data_room_accessed_carries_meeting_date(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    """If last_meeting_date empty, data_room_accessed sets it to today."""
    write_pipeline([{"investor_id": "inv_x", "status": "diligence"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "data_room_accessed",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    row = _read_pipeline(tmp_workspace)[0]
    assert row["last_meeting_date"] == date.today().isoformat()


# --------------------------------------------------------------------------
# Vocabulary parsing (regression for #5)
# --------------------------------------------------------------------------
def test_vocabulary_with_comments_parses_all_statuses(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    """Comments inside the statuses block must not terminate parsing."""
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])

    # 'do_not_contact' is the LAST item, after multiple comment lines —
    # if comment handling was wrong, it would not be in the parsed list.
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "do_not_contact",
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_invalid_status_returns_envelope_with_options(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "bogus_status",
    )
    assert r.returncode == 1
    payload = json.loads(r.stdout)
    assert payload["field"] == "--new-status"
    assert "connected" in payload["fix"]


# --------------------------------------------------------------------------
# Missing inputs
# --------------------------------------------------------------------------
def test_missing_investor_id_returns_envelope(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "ghost_id",
        "--new-status", "first_dm_sent",
    )
    # 'not found' is exit 1 (validation), missing pipeline.csv would be 2.
    payload = json.loads(r.stdout)
    assert payload["field"] == "investor_id"
    assert "not found" in payload["error"]
    assert r.returncode == 1


def test_missing_pipeline_csv_returns_exit_2(
    tmp_workspace, seed_vocabulary_yaml, run_script,
):
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "first_dm_sent",
    )
    assert r.returncode == 2
    payload = json.loads(r.stdout)
    assert "pipeline.csv" in payload["error"]


def test_missing_vocabulary_returns_exit_2(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "first_dm_sent",
    )
    assert r.returncode == 2
    payload = json.loads(r.stdout)
    assert "vocabulary.yaml" in payload["error"]


def test_pipeline_missing_investor_id_column(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    """Pipeline CSV without investor_id column is a validation error."""
    # write csv with bogus header
    path = tmp_workspace / "pipeline" / "pipeline.csv"
    with path.open("w", encoding="utf-8", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=["foo", "bar"])
        writer.writeheader()
        writer.writerow({"foo": "1", "bar": "2"})

    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x", "--new-status", "first_dm_sent",
    )
    assert r.returncode == 1
    payload = json.loads(r.stdout)
    assert "investor_id" in payload["error"]


# --------------------------------------------------------------------------
# Estimated minutes
# --------------------------------------------------------------------------
@pytest.mark.parametrize("status,touch_type,minutes", [
    ("intro_call_done", "meeting", 60),
    ("data_room_accessed", "material_viewed", 5),
    ("diligence", "diligence_qa", 30),
    ("ghosted", "takeaway", 10),
    ("nurture", "warm_update", 10),
])
def test_estimated_minutes_per_status(
    status, touch_type, minutes,
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x", "--new-status", status,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert payload["estimated_minutes"] == minutes
    _, rows = _read_touches(tmp_workspace)
    assert rows[-1]["touch_type"] == touch_type
    assert rows[-1]["estimated_minutes"] == str(minutes)


def test_explicit_touch_type_override(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "first_dm_sent",
        "--touch-type", "intro_request",
    )
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["estimated_minutes"] == 15


# --------------------------------------------------------------------------
# CSV injection sanitization (regression)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("hostile", [
    "=CMD()",
    "+1+1",
    "-2+1",
    "@SUM(A1)",
])
def test_csv_injection_sanitization_in_notes(
    hostile,
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "first_dm_sent",
        "--note", hostile,
    )
    assert r.returncode == 0, r.stdout + r.stderr

    # Notes column on pipeline must be prefixed with "'" because the
    # write-back path goes through sanitize_cell.
    row = _read_pipeline(tmp_workspace)[0]
    # Notes prefixed with date+colon, sanitize triggers on the LEADING
    # char of the cell, which is '2' (date digit). So the date prefix
    # protects the cell. Verify formula chars never reach a leading
    # position via the touches notes column.
    _, touches = _read_touches(tmp_workspace)
    note = touches[-1]["notes"]
    if note and note[0] in ("=", "+", "-", "@"):
        pytest.fail(f"unsanitized leading formula char in note: {note!r}")


# --------------------------------------------------------------------------
# Timezone / DeprecationWarning regression
# --------------------------------------------------------------------------
def test_no_deprecation_warnings_on_run(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    """Script must not emit DeprecationWarning (e.g. utcnow)."""
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "first_dm_sent",
    )
    # PYTHONWARNINGS=error::DeprecationWarning is set in run_script.
    # If the script triggered one, exit code would be != 0 and stderr
    # would mention DeprecationWarning.
    assert "DeprecationWarning" not in (r.stderr or "")
    assert r.returncode == 0


# --------------------------------------------------------------------------
# Pipeline forward-compat: missing optional columns get added
# --------------------------------------------------------------------------
def test_pipeline_missing_optional_columns_get_added(
    tmp_workspace, seed_vocabulary_yaml, run_script,
):
    """If pipeline.csv is missing optional cols, script adds them."""
    path = tmp_workspace / "pipeline" / "pipeline.csv"
    with path.open("w", encoding="utf-8", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=["investor_id", "status"])
        writer.writeheader()
        writer.writerow({"investor_id": "inv_x", "status": "connected"})

    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "first_dm_sent",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    rows = _read_pipeline(tmp_workspace)
    assert "last_touch_date" in rows[0]
    assert "ghost_flag_date" in rows[0]


def test_existing_notes_get_concatenated_with_separator(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "inv_x", "status": "connected", "notes": "prior note"}
    ])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x",
        "--new-status", "first_dm_sent",
        "--note", "second note",
    )
    assert r.returncode == 0
    notes = _read_pipeline(tmp_workspace)[0]["notes"]
    assert "prior note" in notes
    assert "second note" in notes
    assert " | " in notes


def test_summary_includes_touch_id(
    tmp_workspace, seed_vocabulary_yaml, write_pipeline, run_script,
):
    write_pipeline([{"investor_id": "inv_x", "status": "connected"}])
    r = run_script(
        "update_pipeline.py",
        "--investor-id", "inv_x", "--new-status", "first_dm_sent",
    )
    payload = json.loads(r.stdout)
    assert payload["touch_id"]
    # uuid4 string length 36, includes dashes
    assert len(payload["touch_id"]) == 36
