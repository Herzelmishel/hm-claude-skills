"""Tests for reapproach_notes.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_writes_reapproach_md(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "inv_1", "investor_name": "Sample Investor",
         "status": "pass",
         "pass_reason": "too early stage",
         "reapproach_trigger": "first paying customer"},
    ])
    r = run_script("reapproach_notes.py", "--investor-id", "inv_1")
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    md_path = Path(payload["draft_path"])
    assert md_path.exists()
    text = md_path.read_text(encoding="utf-8")
    assert "Sample Investor" in text
    assert "too early stage" in text
    assert "first paying customer" in text


def test_voice_fingerprint_loaded_when_present(
    tmp_workspace, write_pipeline, sample_voice_fingerprint, run_script,
):
    write_pipeline([
        {"investor_id": "inv_1", "investor_name": "X",
         "status": "pass",
         "pass_reason": "x", "reapproach_trigger": "y"},
    ])
    r = run_script("reapproach_notes.py", "--investor-id", "inv_1")
    payload = json.loads(r.stdout)
    md = Path(payload["draft_path"]).read_text(encoding="utf-8")
    assert "voice-fingerprint loaded" in md
    assert "register=direct" in md


def test_voice_missing_emits_warning_comment(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "inv_1", "investor_name": "X",
         "status": "pass",
         "pass_reason": "x", "reapproach_trigger": "y"},
    ])
    r = run_script("reapproach_notes.py", "--investor-id", "inv_1")
    assert r.returncode == 0, r.stdout + r.stderr
    md = Path(json.loads(r.stdout)["draft_path"]).read_text(encoding="utf-8")
    assert "voice-fingerprint NOT loaded" in md


def test_investor_not_in_pipeline_returns_envelope(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([])
    r = run_script("reapproach_notes.py", "--investor-id", "missing")
    assert r.returncode == 1
    payload = json.loads(r.stdout)
    assert payload["field"] == "investor_id"


def test_missing_pipeline_csv_returns_exit_1(
    tmp_workspace, run_script,
):
    """No pipeline.csv → emit_error w/ default code 1 per script."""
    r = run_script("reapproach_notes.py", "--investor-id", "x")
    payload = json.loads(r.stdout)
    assert "pipeline.csv not found" in payload["error"]
    assert r.returncode == 1


def test_missing_pass_reason_or_trigger_returns_envelope(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "inv_1", "investor_name": "X",
         "status": "pass", "pass_reason": "", "reapproach_trigger": ""},
    ])
    r = run_script("reapproach_notes.py", "--investor-id", "inv_1")
    assert r.returncode == 1
    payload = json.loads(r.stdout)
    assert "pass_reason" in payload["error"]


@pytest.mark.parametrize("name,expected_slug_part", [
    ("Café Müller", "caf"),  # unicode normalization
    ("Acme & Co.", "acme-co"),
    ("Dr. Jane O'Reilly", "dr-jane-o-reilly"),
])
def test_slug_handles_special_chars(
    name, expected_slug_part,
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "inv_1", "investor_name": name,
         "status": "pass", "pass_reason": "x", "reapproach_trigger": "y"},
    ])
    r = run_script("reapproach_notes.py", "--investor-id", "inv_1")
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert expected_slug_part in payload["draft_path"]


def test_empty_name_falls_back_to_id_in_slug(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "inv_xyz", "investor_name": "",
         "status": "pass", "pass_reason": "a", "reapproach_trigger": "b"},
    ])
    r = run_script("reapproach_notes.py", "--investor-id", "inv_xyz")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert "inv-xyz" in payload["draft_path"] or "inv_xyz" in payload["draft_path"]


def test_no_deprecation_warnings(
    tmp_workspace, write_pipeline, run_script,
):
    write_pipeline([
        {"investor_id": "i", "investor_name": "n",
         "status": "pass", "pass_reason": "x", "reapproach_trigger": "y"},
    ])
    r = run_script("reapproach_notes.py", "--investor-id", "i")
    assert "DeprecationWarning" not in (r.stderr or "")
    assert r.returncode == 0
