"""Tests for preseed-outreach/scripts/count_message_chars.py."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest


def _read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _run(mod, capsys):
    code = mod.main()
    out = capsys.readouterr().out
    parsed = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    return parsed, code, out


# ---------- happy path -----------------------------------------------------


def test_short_connection_note_passes(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    csv_path = write_outreach_csv([baseline_outreach_row(connection_note="hi")])
    parsed, code, _ = _run(load_count_message_chars, capsys)
    assert code == 0
    assert parsed["ok"] is True
    rows = _read_csv(csv_path)
    assert rows[0]["char_count_connection_note"] == "2"


def test_connection_note_at_200_chars_passes(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    csv_path = write_outreach_csv(
        [baseline_outreach_row(connection_note="x" * 200)]
    )
    parsed, code, _ = _run(load_count_message_chars, capsys)
    assert code == 0
    assert parsed["ok"] is True
    rows = _read_csv(csv_path)
    assert rows[0]["char_count_connection_note"] == "200"


def test_connection_note_201_chars_fails(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    csv_path = write_outreach_csv(
        [baseline_outreach_row(investor_id="inv_abc", connection_note="x" * 201)]
    )
    parsed, code, out = _run(load_count_message_chars, capsys)
    assert code == 1
    # First JSON is the error envelope, second is the violations list.
    lines = [ln for ln in out.splitlines() if ln.strip()]
    err = json.loads(lines[0])
    detail = json.loads(lines[1])
    assert "Length limit exceeded" in err["error"]
    assert "connection_note" in err["field"]
    assert detail["violations"][0]["row"] == 2
    assert detail["violations"][0]["actual"] == 201
    # char_count column written even on failure
    rows = _read_csv(csv_path)
    assert rows[0]["char_count_connection_note"] == "201"


def test_warm_update_at_150_words_passes(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    text = " ".join(["word"] * 150)
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="follow_up",
                connection_note="",
                warm_update=text,
                source_signal="",
                source_url="",
            )
        ]
    )
    parsed, code, _ = _run(load_count_message_chars, capsys)
    assert code == 0
    assert parsed["ok"] is True


def test_warm_update_151_words_fails(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    text = " ".join(["word"] * 151)
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="follow_up",
                connection_note="",
                warm_update=text,
            )
        ]
    )
    parsed, code, out = _run(load_count_message_chars, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "warm_update" in err["field"]


def test_takeaway_at_80_words_passes(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    text = " ".join(["w"] * 80)
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="takeaway",
                connection_note="",
                takeaway_email=text,
            )
        ]
    )
    parsed, code, _ = _run(load_count_message_chars, capsys)
    assert code == 0


def test_takeaway_81_words_fails(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    text = " ".join(["w"] * 81)
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="takeaway",
                connection_note="",
                takeaway_email=text,
            )
        ]
    )
    parsed, code, out = _run(load_count_message_chars, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "takeaway_email" in err["field"]


# ---------- column behaviour ----------------------------------------------


def test_char_count_column_added_when_missing(
    tmp_workspace, baseline_outreach_row, load_count_message_chars, capsys
):
    csv_path = tmp_workspace / "fundraising" / "outreach" / "outreach.csv"
    # Build CSV without char_count_connection_note column
    header = [
        "investor_id",
        "ask_stage",
        "connection_note",
        "warm_update",
        "takeaway_email",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerow(
            {
                "investor_id": "i1",
                "ask_stage": "permission",
                "connection_note": "hello",
                "warm_update": "",
                "takeaway_email": "",
            }
        )
    parsed, code, _ = _run(load_count_message_chars, capsys)
    assert code == 0
    rows = _read_csv(csv_path)
    assert rows[0]["char_count_connection_note"] == "5"


def test_emoji_counted_per_codepoint(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    """len() counts codepoints, so each emoji is 1 char per Python semantics."""
    csv_path = write_outreach_csv(
        [baseline_outreach_row(connection_note="hi 🦄 🎉")]
    )
    _run(load_count_message_chars, capsys)
    rows = _read_csv(csv_path)
    # "hi " = 3, 🦄 = 1, " " = 1, 🎉 = 1 -> 6
    assert rows[0]["char_count_connection_note"] == "6"


def test_empty_connection_note_allowed(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="follow_up",
                connection_note="",
                warm_update="short update",
                source_signal="",
                source_url="",
            )
        ]
    )
    parsed, code, _ = _run(load_count_message_chars, capsys)
    assert code == 0
    assert parsed["ok"] is True


def test_other_columns_preserved(
    write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    """Regression: extrasaction shouldn't drop columns the script doesn't know about."""
    csv_path = write_outreach_csv(
        [baseline_outreach_row(forwardable_intro_blurb="for John")]
    )
    _run(load_count_message_chars, capsys)
    rows = _read_csv(csv_path)
    assert rows[0]["forwardable_intro_blurb"] == "for John"
    assert rows[0]["voice_score"] == "0.85"
    assert rows[0]["needs_human_review"] == "low"


# ---------- formula injection ---------------------------------------------


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@"])
def test_csv_injection_sanitized(
    prefix, write_outreach_csv, baseline_outreach_row, load_count_message_chars, capsys
):
    csv_path = write_outreach_csv(
        [baseline_outreach_row(forwardable_intro_blurb=f"{prefix}cmd|/calc")]
    )
    _run(load_count_message_chars, capsys)
    rows = _read_csv(csv_path)
    assert rows[0]["forwardable_intro_blurb"].startswith("'")


# ---------- error paths ----------------------------------------------------


def test_missing_csv_returns_1(tmp_workspace, load_count_message_chars, capsys):
    code = load_count_message_chars.main()
    out = capsys.readouterr().out
    err = json.loads(out.strip().splitlines()[-1])
    assert code == 1
    assert err["error"] == "outreach.csv not found"


def test_missing_required_column(
    tmp_workspace, load_count_message_chars, capsys
):
    csv_path = tmp_workspace / "fundraising" / "outreach" / "outreach.csv"
    csv_path.write_text("investor_id,connection_note\nx,y\n", encoding="utf-8")
    code = load_count_message_chars.main()
    out = capsys.readouterr().out
    err = json.loads(out.strip().splitlines()[-1])
    assert code == 1
    assert "Missing required column" in err["error"]


# ---------- pure helpers ---------------------------------------------------


def test_count_words_helper(load_count_message_chars):
    cw = load_count_message_chars.count_words
    assert cw("") == 0
    assert cw(None) == 0
    assert cw("one two three") == 3
    assert cw("  spaced   words  here ") == 3


def test_count_chars_helper(load_count_message_chars):
    assert load_count_message_chars.count_chars("") == 0
    assert load_count_message_chars.count_chars(None) == 0
    assert load_count_message_chars.count_chars("hello") == 5


def test_sanitize_cell_helper(load_count_message_chars):
    s = load_count_message_chars.sanitize_cell
    assert s(None) == ""
    assert s("=evil") == "'=evil"
    assert s("safe") == "safe"


# ---------- subprocess -----------------------------------------------------


def test_subprocess_happy(
    write_outreach_csv, baseline_outreach_row, run_script
):
    write_outreach_csv([baseline_outreach_row()])
    proc = run_script("count_message_chars.py")
    assert proc.returncode == 0
    assert json.loads(proc.stdout.strip().splitlines()[-1])["ok"] is True


def test_subprocess_violation(
    write_outreach_csv, baseline_outreach_row, run_script
):
    write_outreach_csv([baseline_outreach_row(connection_note="x" * 201)])
    proc = run_script("count_message_chars.py")
    assert proc.returncode == 1
