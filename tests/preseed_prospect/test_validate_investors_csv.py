"""Tests for preseed-prospect/scripts/validate_investors_csv.py."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest


def _run(mod, capsys):
    code = None
    try:
        mod.main()
    except SystemExit as e:
        code = e.code
    out = capsys.readouterr().out
    parsed = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    return parsed, code


# ---------- happy path -----------------------------------------------------


def test_valid_csv_passes(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    seed_schemas_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv([baseline_row()])
    parsed, code = _run(load_validate_investors, capsys)
    assert code is None
    assert parsed["ok"] is True
    assert parsed["rows_validated"] == 1


def test_valid_csv_no_schemas_yaml_uses_defaults(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    """schemas.yaml absent → default required-fields list applies."""
    write_investors_csv([baseline_row()])
    parsed, code = _run(load_validate_investors, capsys)
    assert code is None
    assert parsed["ok"] is True


# ---------- missing CSV ----------------------------------------------------


def test_missing_csv_fails(load_validate_investors, capsys, tmp_workspace):
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "investors.csv not found"


def test_csv_no_header_fails(tmp_workspace, load_validate_investors, capsys):
    csv_path = tmp_workspace / "fundraising" / "investors" / "investors.csv"
    csv_path.write_text("", encoding="utf-8")
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "investors.csv has no header row"


# ---------- required columns ----------------------------------------------


def test_missing_required_column_in_header(
    tmp_workspace, seed_vocabulary_yaml, seed_schemas_yaml, load_validate_investors, capsys
):
    csv_path = tmp_workspace / "fundraising" / "investors" / "investors.csv"
    # header missing 'investor_id'
    csv_path.write_text("first_name,last_name\nAda,Lovelace\n", encoding="utf-8")
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Required column missing from header"
    assert parsed["field"] == "investor_id"


def test_required_field_blank_on_row(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    seed_schemas_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv([baseline_row(investor_name="")])
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Missing required field"
    assert "investor_name" in parsed["field"]


def test_disqualified_row_can_skip_ask_stage(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    seed_schemas_yaml,
    load_validate_investors,
    capsys,
):
    """disqualified rows allow ask_stage to be empty per source."""
    write_investors_csv(
        [
            baseline_row(
                ask_stage="",
                disqualified="yes",
                disqualified_reason="prior_pass",
            )
        ]
    )
    parsed, code = _run(load_validate_investors, capsys)
    assert code is None
    assert parsed["ok"] is True


# ---------- HeyReach fields ------------------------------------------------


@pytest.mark.parametrize("missing_field", ["first_name", "last_name", "linkedin_profile_url"])
def test_heyreach_required_field_missing(
    missing_field,
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    # Use generic required-field gate and HeyReach gate. Disqualified=no so all checks fire.
    row = baseline_row(**{missing_field: ""})
    write_investors_csv([row])
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    # Required-field check fires before HeyReach for first_name/last_name/linkedin_profile_url
    # (all three are in DEFAULT_REQUIRED_FIELDS) so error may be the generic one.
    assert parsed["error"] in {
        "Missing required field",
        "HeyReach-required field missing",
    }
    assert missing_field in parsed["field"]


# ---------- source_urls / dates / types alignment -------------------------


def test_source_urls_dates_types_mismatch(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv(
        [
            baseline_row(
                source_urls="https://a.com;https://b.com",
                source_dates="2025-01-01",  # only one date for two URLs
                source_types="linkedin;blog",
            )
        ]
    )
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert "length mismatch" in parsed["error"]


def test_no_source_urls_for_active_investor(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    # required-field check on source_urls fires first since '' is empty.
    write_investors_csv(
        [
            baseline_row(
                source_urls="",
                source_dates="",
                source_types="",
            )
        ]
    )
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert "source_urls" in parsed["field"]


# ---------- email-pattern guard -------------------------------------------


def test_email_in_contact_path_not_in_sources_fails(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv(
        [
            baseline_row(
                public_contact_path="ada@example.com",
                source_urls="https://example.com/about",  # email not in URL
                source_dates="2025-01-01",
                source_types="blog",
            )
        ]
    )
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Guessed email in public_contact_path"


def test_email_appearing_in_sources_passes(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv(
        [
            baseline_row(
                public_contact_path="ada@example.com",
                source_urls="https://example.com/?contact=ada@example.com",
                source_dates="2025-01-01",
                source_types="blog",
            )
        ]
    )
    parsed, code = _run(load_validate_investors, capsys)
    assert code is None
    assert parsed["ok"] is True


def test_unknown_contact_path_passes(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv([baseline_row(public_contact_path="UNKNOWN")])
    parsed, code = _run(load_validate_investors, capsys)
    assert code is None
    assert parsed["ok"] is True


# ---------- enum validation -----------------------------------------------


def test_invalid_role_rejected(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv([baseline_row(role="janitor")])
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Invalid role"
    assert "janitor" in parsed["fix"]


def test_invalid_ask_stage_rejected(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv([baseline_row(ask_stage="not_a_stage")])
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Invalid ask_stage"


def test_invalid_source_type_rejected(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv(
        [baseline_row(source_types="myspace")]
    )
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Invalid source_type"


def test_invalid_confidence_rejected(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv([baseline_row(confidence="extreme")])
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Invalid confidence value"


# ---------- disqualified ---------------------------------------------------


def test_disqualified_without_reason(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    load_validate_investors,
    capsys,
):
    write_investors_csv(
        [baseline_row(disqualified="yes", disqualified_reason="")]
    )
    parsed, code = _run(load_validate_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Disqualified row missing reason"


# ---------- vocabulary parser regression ----------------------------------


def test_vocabulary_yaml_with_comments_parses(
    tmp_workspace,
    write_investors_csv,
    baseline_row,
    load_validate_investors,
    capsys,
):
    """Comments and blank lines must not break the YAML parser."""
    vocab = tmp_workspace / "fundraising" / ".sys" / "vocabulary.yaml"
    vocab.write_text(
        "# top header\n"
        "\n"
        "roles:\n"
        "  # block comment\n"
        "  - partner # inline comment\n"
        "  - associate\n"
        "ask_stages:\n"
        "  - permission\n"
        "  - call | pitch\n"  # pipe-separated entries
        "source_types:\n"
        "  - linkedin\n"
        "confidence:\n"
        "  - high\n",
        encoding="utf-8",
    )
    write_investors_csv(
        [baseline_row(role="partner", ask_stage="permission", confidence="high", source_types="linkedin")]
    )
    parsed, code = _run(load_validate_investors, capsys)
    assert code is None
    assert parsed["ok"] is True


def test_vocabulary_yaml_missing_returns_empty_enums(
    tmp_workspace,
    write_investors_csv,
    baseline_row,
    load_validate_investors,
    capsys,
):
    """No vocabulary.yaml at all → enum checks are skipped, validation passes."""
    write_investors_csv([baseline_row(role="anything", confidence="anything", ask_stage="anything")])
    parsed, code = _run(load_validate_investors, capsys)
    assert code is None
    assert parsed["ok"] is True


# ---------- helper unit tests ---------------------------------------------


def test_split_semi_handles_whitespace(load_validate_investors):
    s = load_validate_investors.split_semi
    assert s("a;b;c") == ["a", "b", "c"]
    assert s(" a ; b ;; c ") == ["a", "b", "c"]
    assert s("") == []
    assert s(None) == []


def test_is_truthy_helper(load_validate_investors):
    t = load_validate_investors.is_truthy
    assert t("yes") and t("YES") and t("1") and t("y") and t("true")
    assert not t("") and not t(None) and not t("no")


def test_load_required_fields_falls_back(tmp_workspace, load_validate_investors):
    """No schemas.yaml → defaults."""
    fields = load_validate_investors.load_required_fields()
    assert "investor_id" in fields
    assert "linkedin_profile_url" in fields


def test_load_required_fields_reads_schemas(
    tmp_workspace, seed_schemas_yaml, load_validate_investors
):
    fields = load_validate_investors.load_required_fields()
    assert "investor_id" in fields
    assert "linkedin_profile_url" in fields


# ---------- subprocess -----------------------------------------------------


def test_script_subprocess_happy_path(
    write_investors_csv,
    baseline_row,
    seed_vocabulary_yaml,
    seed_schemas_yaml,
    run_script,
):
    write_investors_csv([baseline_row()])
    proc = run_script("validate_investors_csv.py")
    assert proc.returncode == 0
    assert json.loads(proc.stdout.strip().splitlines()[-1])["ok"] is True


def test_script_subprocess_missing_csv(tmp_workspace, run_script):
    proc = run_script("validate_investors_csv.py")
    assert proc.returncode == 1
    err = json.loads(proc.stdout.strip().splitlines()[-1])
    assert err["error"] == "investors.csv not found"
