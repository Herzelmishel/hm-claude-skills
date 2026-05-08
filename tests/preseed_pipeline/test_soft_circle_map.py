"""Tests for soft_circle_map.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _read_md(workspace: Path) -> str:
    return (workspace / "pipeline" / "soft-circle-map.md").read_text(
        encoding="utf-8"
    )


def test_generates_map_for_yes_permission(
    tmp_workspace, write_commitments, sample_investors_csv, run_script,
):
    write_commitments([
        {"investor_id": "inv_001", "soft_circle_permission": "yes",
         "soft_commit_amount": "$25K"},
    ])
    r = run_script("soft_circle_map.py")
    assert r.returncode == 0, r.stdout + r.stderr
    md = _read_md(tmp_workspace)
    assert "Active soft circle" in md
    assert "operator-angel" in md  # role rendered as descriptor


def test_default_uses_descriptors_not_names(
    tmp_workspace, write_commitments, sample_investors_csv, run_script,
):
    """Default rendering is descriptor-only — privacy default."""
    write_commitments([
        {"investor_id": "inv_001", "soft_circle_permission": "yes"},
    ])
    r = run_script("soft_circle_map.py")
    md = _read_md(tmp_workspace)
    # Without --names-confirmed, the actual name "Alice Operator" must NOT
    # appear in the active soft-circle table row.
    # The MD always has FOMO archetype table; just check the active section.
    active_start = md.index("## Active soft circle")
    active_end = md.index("## FOMO-by-archetype matching")
    active_section = md[active_start:active_end]
    assert "Alice Operator" not in active_section
    payload = json.loads(r.stdout)
    assert payload["names_rendered"] is False


def test_names_confirmed_flag_renders_names(
    tmp_workspace, write_commitments, sample_investors_csv, run_script,
):
    write_commitments([
        {"investor_id": "inv_001", "soft_circle_permission": "yes"},
    ])
    r = run_script("soft_circle_map.py", "--names-confirmed")
    assert r.returncode == 0
    md = _read_md(tmp_workspace)
    assert "Alice Operator" in md
    payload = json.loads(r.stdout)
    assert payload["names_rendered"] is True


def test_pending_section_lists_ask_permission(
    tmp_workspace, write_commitments, sample_investors_csv, run_script,
):
    write_commitments([
        {"investor_id": "inv_002", "soft_circle_permission": "ask",
         "notes": "still discussing"},
    ])
    r = run_script("soft_circle_map.py")
    md = _read_md(tmp_workspace)
    pending_start = md.index("## Needs confirmation")
    pending_end = md.index("## No-go")
    pending_section = md[pending_start:pending_end]
    assert "still discussing" in pending_section
    payload = json.loads(r.stdout)
    assert payload["pending_count"] == 1


def test_no_go_section_lists_no_permission(
    tmp_workspace, write_commitments, sample_investors_csv, run_script,
):
    write_commitments([
        {"investor_id": "inv_003", "soft_circle_permission": "no",
         "notes": "explicit refusal"},
    ])
    r = run_script("soft_circle_map.py")
    md = _read_md(tmp_workspace)
    no_go_idx = md.index("## No-go")
    after = md[no_go_idx:]
    assert "explicit refusal" in after
    payload = json.loads(r.stdout)
    assert payload["no_go_count"] == 1


def test_fomo_matching_table_present(
    tmp_workspace, write_commitments, run_script,
):
    write_commitments([])
    r = run_script("soft_circle_map.py")
    md = _read_md(tmp_workspace)
    assert "FOMO-by-archetype matching" in md
    # The table includes role keys.
    assert "operator-angel" in md
    assert "preseed-fund" in md
    assert "commerce-founder-angel" in md


def test_joins_investors_csv_for_descriptors(
    tmp_workspace, write_commitments, sample_investors_csv, run_script,
):
    write_commitments([
        {"investor_id": "inv_002", "soft_circle_permission": "yes"},
    ])
    r = run_script("soft_circle_map.py")
    md = _read_md(tmp_workspace)
    # Bob is a preseed_fund w/ thesis_match "AI for commerce" → both should
    # appear in the descriptor.
    assert "preseed-fund" in md
    assert "AI for commerce" in md
    assert "(SF)" in md  # geography rendered


def test_empty_commitments_csv_graceful(
    tmp_workspace, write_commitments, run_script,
):
    write_commitments([])
    r = run_script("soft_circle_map.py")
    assert r.returncode == 0
    md = _read_md(tmp_workspace)
    assert "No confirmed soft-circle members yet" in md
    payload = json.loads(r.stdout)
    assert payload["confirmed_count"] == 0


def test_missing_commitments_csv_returns_exit_2(tmp_workspace, run_script):
    r = run_script("soft_circle_map.py")
    assert r.returncode == 2
    payload = json.loads(r.stdout)
    assert "commitments.csv" in payload["error"]


def test_commitments_missing_required_column_returns_exit_1(
    tmp_workspace, write_commitments, run_script,
):
    """Missing required column → validation error code 1."""
    # Write commitments.csv without soft_circle_permission column
    write_commitments([{"investor_id": "x"}], fields=["investor_id"])
    r = run_script("soft_circle_map.py")
    assert r.returncode == 1
    payload = json.loads(r.stdout)
    assert "soft_circle_permission" in payload["error"]


def test_exit_0_with_json_summary_on_success(
    tmp_workspace, write_commitments, run_script,
):
    write_commitments([
        {"investor_id": "x", "soft_circle_permission": "yes"},
        {"investor_id": "y", "soft_circle_permission": "ask"},
        {"investor_id": "z", "soft_circle_permission": "no"},
    ])
    r = run_script("soft_circle_map.py")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["ok"] is True
    assert payload["confirmed_count"] == 1
    assert payload["pending_count"] == 1
    assert payload["no_go_count"] == 1
    assert payload["output_path"].endswith("soft-circle-map.md")


def test_blank_permission_skipped_silently(
    tmp_workspace, write_commitments, run_script,
):
    write_commitments([
        {"investor_id": "x", "soft_circle_permission": ""},
        {"investor_id": "y", "soft_circle_permission": "yes"},
    ])
    r = run_script("soft_circle_map.py")
    payload = json.loads(r.stdout)
    assert payload["confirmed_count"] == 1
    # blank not counted in any bucket


def test_stage_classification_in_markdown(
    tmp_workspace, write_commitments, run_script,
):
    """Stage A (0-2), Stage B (3-5), Stage C (6+) is rendered."""
    # 1 confirmed → Stage A
    write_commitments([
        {"investor_id": "x", "soft_circle_permission": "yes"},
    ])
    r = run_script("soft_circle_map.py")
    md = _read_md(tmp_workspace)
    assert "Stage A" in md


def test_stage_b_with_4_confirmed(
    tmp_workspace, write_commitments, run_script,
):
    write_commitments([
        {"investor_id": f"x{i}", "soft_circle_permission": "yes"}
        for i in range(4)
    ])
    r = run_script("soft_circle_map.py")
    md = _read_md(tmp_workspace)
    assert "Stage B" in md


def test_stage_c_with_7_confirmed(
    tmp_workspace, write_commitments, run_script,
):
    write_commitments([
        {"investor_id": f"x{i}", "soft_circle_permission": "yes"}
        for i in range(7)
    ])
    r = run_script("soft_circle_map.py")
    md = _read_md(tmp_workspace)
    assert "Stage C" in md


def test_amount_columns_rendered_in_commit_cell(
    tmp_workspace, write_commitments, sample_investors_csv, run_script,
):
    write_commitments([
        {"investor_id": "inv_001", "soft_circle_permission": "yes",
         "signed_safe_amount": "$50K", "commitment_status": "signed"},
    ])
    r = run_script("soft_circle_map.py")
    md = _read_md(tmp_workspace)
    assert "$50K" in md
    assert "signed" in md


def test_handles_missing_investors_csv(
    tmp_workspace, write_commitments, run_script,
):
    """When investors.csv is missing, descriptors fall back gracefully."""
    write_commitments([
        {"investor_id": "x", "soft_circle_permission": "yes"},
    ])
    # No investors.csv exists → script should still succeed.
    r = run_script("soft_circle_map.py")
    assert r.returncode == 0


def test_no_deprecation_warnings(
    tmp_workspace, write_commitments, run_script,
):
    write_commitments([])
    r = run_script("soft_circle_map.py")
    assert "DeprecationWarning" not in (r.stderr or "")
    assert r.returncode == 0
