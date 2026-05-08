"""Tests for preseed-outreach/scripts/validate_outreach.py."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest


def _run(mod, capsys):
    code = mod.main()
    out = capsys.readouterr().out
    err = capsys.readouterr().err
    lines = [ln for ln in out.splitlines() if ln.strip()]
    parsed = json.loads(lines[-1]) if lines else {}
    return parsed, code, out, err


# ---------- happy path -----------------------------------------------------


def test_valid_outreach_passes(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv([baseline_outreach_row()])
    parsed, code, _, _ = _run(load_validate_outreach, capsys)
    assert code == 0
    assert parsed["ok"] is True


# ---------- anti-voice -----------------------------------------------------


def test_banned_phrase_in_message(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [
            baseline_outreach_row(
                connection_note="Just want to leverage some synergy with you."
            )
        ]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "Banned phrase" in err["error"]
    # First match is whichever appears first in the banned list.
    assert ("synergy" in err["error"] or "leverage" in err["error"])


def test_anti_voice_missing_warns(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    load_validate_outreach,
    capsys,
):
    """No anti-voice.txt → JSON warning printed, validation still passes."""
    write_outreach_csv([baseline_outreach_row()])
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 0
    # First line is the warning JSON.
    lines = out.splitlines()
    warn = json.loads(lines[0])
    assert "warning" in warn


# ---------- ask_stage progression -----------------------------------------


def test_connection_note_with_wrong_stage_fails(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [baseline_outreach_row(ask_stage="pitch", connection_note="hi there")]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "connection_note populated" in err["error"]


def test_fast_forward_allows_connection_note(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    """Regression: fast_forward stage must allow connection_note."""
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="fast_forward",
                connection_note="responding to your data request",
            )
        ]
    )
    parsed, code, _, _ = _run(load_validate_outreach, capsys)
    assert code == 0


def test_accepted_dm_with_invalid_stage(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="permission",
                connection_note="",
                accepted_dm="I am interested",
            )
        ]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    assert "accepted_dm populated" in json.loads(out.splitlines()[0])["error"]


def test_fast_forward_pitch_requires_fast_forward_stage(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="pitch",
                connection_note="",
                fast_forward_pitch="here is the deck",
            )
        ]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    assert "fast_forward_pitch populated" in json.loads(out.splitlines()[0])["error"]


def test_takeaway_email_requires_takeaway_stage(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="permission",
                connection_note="",
                takeaway_email="closing loop",
            )
        ]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    assert "takeaway_email populated" in json.loads(out.splitlines()[0])["error"]


def test_invalid_ask_stage(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [baseline_outreach_row(ask_stage="invented_stage")]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "not in vocabulary.yaml" in err["error"]


def test_empty_ask_stage(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv([baseline_outreach_row(ask_stage="")])
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "ask_stage is empty" in err["error"]


# ---------- voice_score ----------------------------------------------------


def test_voice_score_required_when_message_present(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [baseline_outreach_row(voice_score="")]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "voice_score is empty" in err["error"]


def test_low_voice_score_requires_high_review(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [baseline_outreach_row(voice_score="0.5", needs_human_review="low")]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "needs_human_review must be 'high'" in err["error"]


def test_low_voice_score_with_high_review_passes(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [baseline_outreach_row(voice_score="0.4", needs_human_review="high")]
    )
    parsed, code, _, _ = _run(load_validate_outreach, capsys)
    assert code == 0


def test_unparseable_voice_score_skipped(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    """Non-float voice_score should not crash; needs_human_review check only fires when parseable."""
    write_outreach_csv(
        [baseline_outreach_row(voice_score="bogus", needs_human_review="low")]
    )
    parsed, code, _, _ = _run(load_validate_outreach, capsys)
    assert code == 0


# ---------- source_url -----------------------------------------------------


def test_source_signal_without_url(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [baseline_outreach_row(source_signal="signal here", source_url="")]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "source_signal populated" in err["error"]


# ---------- length limits --------------------------------------------------


def test_length_connection_note_too_long(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    write_outreach_csv(
        [baseline_outreach_row(connection_note="x" * 201)]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "connection_note" in err["error"]
    assert "exceeds limit" in err["error"]


def test_length_warm_update_too_long(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    text = " ".join(["w"] * 151)
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
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "warm_update" in err["error"]


def test_length_takeaway_too_long(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    text = " ".join(["w"] * 81)
    write_outreach_csv(
        [
            baseline_outreach_row(
                ask_stage="takeaway",
                connection_note="",
                takeaway_email=text,
                source_signal="",
                source_url="",
            )
        ]
    )
    parsed, code, out, _ = _run(load_validate_outreach, capsys)
    assert code == 1
    err = json.loads(out.splitlines()[0])
    assert "takeaway_email" in err["error"]


# ---------- vocabulary parser regressions ---------------------------------


def test_vocabulary_with_comments_parses(
    tmp_workspace,
    write_outreach_csv,
    baseline_outreach_row,
    seed_anti_voice,
    load_validate_outreach,
    capsys,
):
    vocab = tmp_workspace / "fundraising" / ".sys" / "vocabulary.yaml"
    vocab.write_text(
        "# header comment\n"
        "ask_stages:\n"
        "  # mid comment\n"
        "\n"
        "  - permission       ← decoration\n"
        "  - call # inline\n"
        "  - pitch\n"
        "  - follow_up\n"
        "  - fast_forward\n"
        "  - takeaway\n"
        "another_section:\n"  # top-level key terminates section
        "  - x\n",
        encoding="utf-8",
    )
    write_outreach_csv([baseline_outreach_row(ask_stage="permission")])
    parsed, code, _, _ = _run(load_validate_outreach, capsys)
    assert code == 0


# ---------- exit codes / inputs -------------------------------------------


def test_missing_outreach_csv_exits_2(tmp_workspace, load_validate_outreach, capsys):
    code = load_validate_outreach.main()
    out = capsys.readouterr().out
    err = json.loads(out.strip().splitlines()[-1])
    assert code == 2
    assert err["error"] == "outreach.csv not found"


def test_missing_vocab_exits_2(
    tmp_workspace, write_outreach_csv, baseline_outreach_row, load_validate_outreach, capsys
):
    write_outreach_csv([baseline_outreach_row()])
    # No vocabulary.yaml seeded.
    code = load_validate_outreach.main()
    out = capsys.readouterr().out
    err = json.loads(out.strip().splitlines()[-1])
    assert code == 2
    assert err["error"] == "vocabulary.yaml not found"


# ---------- helpers --------------------------------------------------------


def test_count_chars_helper(load_validate_outreach):
    assert load_validate_outreach._count_chars("") == 0
    assert load_validate_outreach._count_chars(None) == 0
    assert load_validate_outreach._count_chars("hi") == 2


def test_count_words_helper(load_validate_outreach):
    cw = load_validate_outreach._count_words
    assert cw("") == 0
    assert cw(None) == 0
    assert cw("a b c") == 3


def test_find_banned_phrase(load_validate_outreach):
    f = load_validate_outreach.find_banned_phrase
    assert f("we leverage SYNERGIES daily", ["leverage", "synergy"]) == "leverage"
    assert f("clean text", ["leverage"]) is None
    assert f("", ["leverage"]) is None


def test_parse_voice_score(load_validate_outreach):
    p = load_validate_outreach.parse_voice_score
    assert p("0.5") == 0.5
    assert p("") is None
    assert p(None) is None
    assert p("not a number") is None


def test_load_anti_voice_missing(tmp_workspace, load_validate_outreach):
    assert load_validate_outreach.load_anti_voice() == []


def test_load_anti_voice_strips_comments(tmp_workspace, seed_anti_voice, load_validate_outreach):
    phrases = load_validate_outreach.load_anti_voice()
    assert "synergy" in phrases
    assert "leverage" in phrases
    assert all(not p.startswith("#") for p in phrases)


# ---------- subprocess -----------------------------------------------------


def test_subprocess_happy(
    write_outreach_csv,
    baseline_outreach_row,
    seed_vocabulary_yaml,
    seed_anti_voice,
    run_script,
):
    write_outreach_csv([baseline_outreach_row()])
    proc = run_script("validate_outreach.py")
    assert proc.returncode == 0


def test_subprocess_missing_csv_exit_2(tmp_workspace, run_script):
    proc = run_script("validate_outreach.py")
    assert proc.returncode == 2
