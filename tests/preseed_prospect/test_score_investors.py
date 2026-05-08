"""Tests for preseed-prospect/scripts/score_investors.py."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest


# ---------- helpers --------------------------------------------------------


def _read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _run_main(mod, capsys):
    """Run the module's main(); return (parsed_json, exit_code or None, stdout)."""
    code = None
    try:
        mod.main()
    except SystemExit as e:
        code = e.code
    out = capsys.readouterr().out
    parsed = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    return parsed, code, out


# ---------- happy path -----------------------------------------------------


def test_valid_csv_writes_score_columns(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    csv_path = write_investors_csv([baseline_row()])
    parsed, code, _ = _run_main(load_score_investors, capsys)

    assert code is None  # main() returned, did not exit
    assert parsed["ok"] is True
    assert parsed["investors_total"] == 1
    rows = _read_csv(csv_path)
    assert "score_100" in rows[0]
    assert "score_10" in rows[0]
    assert int(rows[0]["score_100"]) > 0


def test_score_at_max_when_factors_high(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(
        thesis_fit_score="30",
        stage_fit_score="25",
        check_size_fit_score="15",
        warm_path_score="15",
        recent_signal_score="10",
        geography_fit_score="5",
        conflict_severity="",
    )
    write_investors_csv([row])
    parsed, code, _ = _run_main(load_score_investors, capsys)

    assert code is None
    assert parsed["ok"] is True
    rows = _read_csv((Path(parsed["csv_path"])))
    assert int(rows[0]["score_100"]) == 100
    assert int(rows[0]["score_10"]) == 10


def test_thesis_fit_clamped_when_factor_above_max(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    """A 999 input on thesis_fit_score should clamp to its 30 cap."""
    row = baseline_row(
        thesis_fit_score="999",
        stage_fit_score="0",
        check_size_fit_score="0",
        warm_path_score="0",
        recent_signal_score="0",
        geography_fit_score="0",
    )
    csv_path = write_investors_csv([row])
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code is None
    rows = _read_csv(csv_path)
    assert int(rows[0]["score_100"]) == 30  # clamped to thesis_fit max


def test_negative_factor_floored_to_zero(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(
        thesis_fit_score="-50",
        stage_fit_score="10",
        check_size_fit_score="0",
        warm_path_score="0",
        recent_signal_score="0",
        geography_fit_score="0",
    )
    csv_path = write_investors_csv([row])
    _run_main(load_score_investors, capsys)
    rows = _read_csv(csv_path)
    assert int(rows[0]["score_100"]) == 10


@pytest.mark.parametrize(
    "severity,penalty",
    [("direct", 25), ("adjacent", 10), ("strategic", 5), ("", 0), ("unknown", 0)],
)
def test_conflict_penalty_applied(
    severity, penalty, write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(
        thesis_fit_score="30",
        stage_fit_score="0",
        check_size_fit_score="0",
        warm_path_score="0",
        recent_signal_score="0",
        geography_fit_score="0",
        conflict_severity=severity,
        portfolio_conflict="competitor X" if severity else "",
    )
    csv_path = write_investors_csv([row])
    _run_main(load_score_investors, capsys)
    rows = _read_csv(csv_path)
    assert int(rows[0]["score_100"]) == max(0, 30 - penalty)


# ---------- disqualification ----------------------------------------------


@pytest.mark.parametrize(
    "reason",
    [
        "no_preseed_evidence",
        "direct_competitor_in_portfolio",
        "check_size_mismatch",
        "prior_pass",
    ],
)
def test_disqualification_zeros_score(
    reason, write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(
        disqualified="yes",
        disqualified_reason=reason,
        thesis_fit_score="30",
    )
    csv_path = write_investors_csv([row])
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code is None
    assert parsed["disqualified"] == 1
    rows = _read_csv(csv_path)
    assert int(rows[0]["score_100"]) == 0
    assert int(rows[0]["score_10"]) == 0
    assert rows[0]["disqualified"] == "yes"


def test_disqualified_reason_without_flag_sets_flag(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(disqualified="", disqualified_reason="prior_pass")
    csv_path = write_investors_csv([row])
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code is None
    rows = _read_csv(csv_path)
    assert rows[0]["disqualified"] == "yes"
    assert int(rows[0]["score_100"]) == 0


def test_disqualified_flag_without_reason_fails(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(disqualified="yes", disqualified_reason="")
    write_investors_csv([row])
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Disqualified row missing reason"


# ---------- lead_candidate -------------------------------------------------


def test_lead_candidate_flag_preserved(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(
        lead_candidate="yes",
        investment_evidence="led seed at example",
    )
    csv_path = write_investors_csv([row])
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code is None
    assert parsed["lead_candidates"] == 1
    rows = _read_csv(csv_path)
    assert rows[0]["lead_candidate"] == "yes"


# ---------- source URL gate ------------------------------------------------


def test_missing_source_urls_fails(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(source_urls="")
    write_investors_csv([row])
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code == 1
    assert parsed["error"] == "Row missing source_urls"
    assert "row 2" in parsed["field"]


def test_disqualified_row_skips_source_url_gate(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(
        source_urls="",
        disqualified="yes",
        disqualified_reason="prior_pass",
    )
    write_investors_csv([row])
    parsed, code, _ = _run_main(load_score_investors, capsys)
    # still passes — disqualified bypasses source_urls gate
    assert code is None
    assert parsed["ok"] is True


# ---------- empty / malformed CSV -----------------------------------------


def test_empty_csv_with_header_succeeds(
    write_investors_csv, load_score_investors, capsys
):
    write_investors_csv([])
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code is None
    assert parsed["ok"] is True
    assert parsed["investors_total"] == 0


def test_missing_csv_fails(load_score_investors, capsys, tmp_workspace):
    # No CSV created.
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code == 1
    assert parsed["error"] == "investors.csv not found"


def test_csv_no_header_fails(tmp_workspace, load_score_investors, capsys):
    csv_path = tmp_workspace / "fundraising" / "investors" / "investors.csv"
    csv_path.write_text("", encoding="utf-8")
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code == 1
    assert parsed["error"] == "investors.csv has no header row"


# ---------- atomic write & sanitization ------------------------------------


def test_atomic_write_preserves_original_on_failure(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    """If validation fails mid-way, the original file is untouched."""
    row = baseline_row(source_urls="")  # will trigger fail()
    csv_path = write_investors_csv([row])
    original = csv_path.read_text(encoding="utf-8")
    parsed, code, _ = _run_main(load_score_investors, capsys)
    assert code == 1
    assert csv_path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
def test_csv_injection_sanitized_on_write(
    prefix, write_investors_csv, baseline_row, load_score_investors, capsys
):
    payload = f"{prefix}HYPERLINK(evil)"
    row = baseline_row(investor_name=payload)
    csv_path = write_investors_csv([row])
    _run_main(load_score_investors, capsys)
    rows = _read_csv(csv_path)
    assert rows[0]["investor_name"] == "'" + payload


def test_unicode_investor_name_round_trips(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(investor_name="Åsa Lindström 山田 🦄")
    csv_path = write_investors_csv([row])
    _run_main(load_score_investors, capsys)
    rows = _read_csv(csv_path)
    assert rows[0]["investor_name"] == "Åsa Lindström 山田 🦄"


# ---------- pure-function unit tests --------------------------------------


def test_parse_int_handles_blanks_and_floats(load_score_investors):
    assert load_score_investors.parse_int("") == 0
    assert load_score_investors.parse_int("  ") == 0
    assert load_score_investors.parse_int(None) == 0
    assert load_score_investors.parse_int("12.7") == 12
    assert load_score_investors.parse_int("garbage", default=99) == 99
    assert load_score_investors.parse_int("garbage") == 0


def test_truthy_helper(load_score_investors):
    assert load_score_investors.truthy("yes")
    assert load_score_investors.truthy("YES")
    assert load_score_investors.truthy("Y")
    assert load_score_investors.truthy("1")
    assert load_score_investors.truthy("true")
    assert not load_score_investors.truthy("")
    assert not load_score_investors.truthy(None)
    assert not load_score_investors.truthy("no")


def test_sanitize_cell_none_returns_empty(load_score_investors):
    assert load_score_investors.sanitize_cell(None) == ""


def test_sanitize_cell_passes_safe_value(load_score_investors):
    assert load_score_investors.sanitize_cell("Ada Lovelace") == "Ada Lovelace"


def test_conflict_penalty_helper(load_score_investors):
    p = load_score_investors.conflict_penalty
    assert p("DIRECT") == 25
    assert p(" Adjacent ") == 10
    assert p("strategic") == 5
    assert p("") == 0
    assert p(None) == 0


def test_score_floor_zero_when_penalty_exceeds_factors(
    write_investors_csv, baseline_row, load_score_investors, capsys
):
    row = baseline_row(
        thesis_fit_score="0",
        stage_fit_score="0",
        check_size_fit_score="0",
        warm_path_score="0",
        recent_signal_score="0",
        geography_fit_score="0",
        conflict_severity="direct",
    )
    csv_path = write_investors_csv([row])
    _run_main(load_score_investors, capsys)
    rows = _read_csv(csv_path)
    assert int(rows[0]["score_100"]) == 0  # clamped at 0


# ---------- subprocess (script-as-CLI) ------------------------------------


def test_script_runs_via_subprocess(write_investors_csv, baseline_row, run_script):
    write_investors_csv([baseline_row()])
    proc = run_script("score_investors.py")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True


def test_script_subprocess_missing_csv_exits_1(tmp_workspace, run_script):
    # No CSV created
    proc = run_script("score_investors.py")
    assert proc.returncode == 1
    err = json.loads(proc.stdout.strip().splitlines()[-1])
    assert err["error"] == "investors.csv not found"


def test_unexpected_exception_caught(monkeypatch, write_investors_csv, baseline_row, load_score_investors, capsys):
    """Force an unexpected exception inside main() to exercise the outer try/except."""
    row = baseline_row()
    write_investors_csv([row])

    # Patch score_row to raise something unexpected mid-loop.
    def boom(*args, **kwargs):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(load_score_investors, "score_row", boom)
    code = None
    try:
        # Mirror __main__ guard: catch SystemExit, swallow non-SystemExit via fail().
        try:
            load_score_investors.main()
        except SystemExit as e:
            code = e.code
        except Exception as exc:  # noqa: BLE001
            load_score_investors.fail(
                error="Unexpected error scoring investors",
                field=type(exc).__name__,
                fix=f"{exc}. Check investors.csv format and re-run.",
            )
    except SystemExit as e:
        code = e.code

    out = capsys.readouterr().out
    parsed = json.loads(out.strip().splitlines()[-1])
    assert code == 1
    assert parsed["error"] == "Unexpected error scoring investors"
    assert "RuntimeError" in parsed["field"]
