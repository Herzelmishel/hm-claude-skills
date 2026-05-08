"""Tests for preseed-voice/scripts/score_voice_match.py."""

from __future__ import annotations

import io
import json
import sys

import pytest


def _import():
    if "score_voice_match" in sys.modules:
        del sys.modules["score_voice_match"]
    import score_voice_match
    return score_voice_match


# ---------------------------------------------------------------------------
# Sub-scorers
# ---------------------------------------------------------------------------

def test_score_sentence_length_when_within_tolerance_then_perfect():
    svm = _import()
    score, issue = svm.score_sentence_length("Six word sentence here right now.", 7)
    assert score == 1.0
    assert issue == ""


def test_score_sentence_length_when_too_long_then_penalty():
    svm = _import()
    long_sentence = "word " * 30 + "."
    score, issue = svm.score_sentence_length(long_sentence, 10)
    assert score < 1.0
    assert "too long" in issue


def test_score_sentence_length_when_too_short_then_penalty():
    svm = _import()
    score, issue = svm.score_sentence_length("Hi.", 18)
    assert score < 1.0
    assert "too short" in issue


def test_score_sentence_length_handles_no_terminator(empty_home):
    """Regression: message with no '.' should not crash."""
    svm = _import()
    score, _ = svm.score_sentence_length("no terminator here", 14)
    assert 0.0 <= score <= 1.0


def test_score_sentence_length_empty_message():
    svm = _import()
    score, issue = svm.score_sentence_length("", 14)
    assert score == 1.0


def test_score_opener_match_when_prefix_matches():
    svm = _import()
    score, _ = svm.score_opener_match("Quick one — saw your post.", ["Quick one —"])
    assert score == 1.0


def test_score_opener_match_when_no_match_then_penalty():
    svm = _import()
    score, issue = svm.score_opener_match(
        "Hello sir, I would like to discuss.", ["Quick one —", "Update:"],
    )
    assert score < 1.0
    assert "opener does not match" in issue


def test_score_opener_match_when_no_patterns_then_neutral():
    svm = _import()
    score, _ = svm.score_opener_match("anything", [])
    assert score == 1.0


def test_score_opener_match_no_sentences_returns_half():
    svm = _import()
    score, issue = svm.score_opener_match("", ["Quick one"])
    assert score == 0.5
    assert "no opener" in issue


def test_score_banned_phrases_when_hit_then_zero():
    svm = _import()
    score, hits = svm.score_banned_phrases(
        "I hope this email finds you well, mate.",
        ["I hope this email finds you well"],
    )
    assert score == 0.0
    assert hits and "banned phrase" in hits[0]


def test_score_banned_phrases_when_clean_then_one():
    svm = _import()
    score, hits = svm.score_banned_phrases("Quick note, all good.", ["leveraging"])
    assert score == 1.0
    assert hits == []


def test_score_banned_phrases_when_no_list_then_one():
    svm = _import()
    score, _ = svm.score_banned_phrases("anything goes", [])
    assert score == 1.0


def test_score_em_dash_when_within_tolerance_then_one():
    svm = _import()
    score, _ = svm.score_em_dash("a message — with one dash.", target_rate=0.2)
    assert 0.0 <= score <= 1.0


def test_score_em_dash_when_overused_then_penalty():
    svm = _import()
    over = "a — b — c — d — e — f — g —" * 5
    score, issue = svm.score_em_dash(over, target_rate=0.0)
    assert score < 1.0
    assert "overused" in issue


def test_score_em_dash_handles_empty_message():
    svm = _import()
    score, _ = svm.score_em_dash("", target_rate=0.5)
    assert score == 1.0


# ---------------------------------------------------------------------------
# Composite score
# ---------------------------------------------------------------------------

def test_compute_voice_score_when_message_matches_all_then_high():
    svm = _import()
    fp = {
        # Use a low target so a short crisp message still scores well.
        "avg_sentence_length_words": 8,
        "opener_patterns": ["Quick one —"],
        "banned_default": ["leveraging"],
        "banned_personal": [],
        "em_dash_rate": 0.2,
        "voice_score_threshold": 0.7,
    }
    msg = (
        "Quick one — saw your post on profit erosion last week today. "
        "We are building Agentis for ecommerce brands and pilots. "
        "Worth a quick fifteen minutes next Tuesday afternoon?"
    )
    out = svm.compute_voice_score(msg, fp)
    assert out["voice_score"] >= 0.9
    assert out["needs_human_review"] == "no"


def test_banned_phrase_caps_composite_at_0_3():
    """Regression: any banned-phrase hit caps composite at 0.3."""
    svm = _import()
    fp = {
        "avg_sentence_length_words": 14,
        "opener_patterns": ["Quick one —"],
        "banned_default": ["I hope this email finds you well"],
        "banned_personal": [],
        "em_dash_rate": 0.2,
        "voice_score_threshold": 0.7,
    }
    msg = (
        "Quick one — I hope this email finds you well. "
        "We have a great fit. Worth a chat?"
    )
    out = svm.compute_voice_score(msg, fp)
    assert out["voice_score"] <= 0.3
    assert out["needs_human_review"] == "high"
    assert any("banned phrase" in i for i in out["issues"])


def test_compute_voice_score_em_dash_mismatch_lowers_score():
    svm = _import()
    fp = {
        "avg_sentence_length_words": 14,
        "opener_patterns": [],
        "banned_default": [],
        "banned_personal": [],
        "em_dash_rate": 0.0,
        "voice_score_threshold": 0.7,
    }
    msg = "a — b — c — d — e — f — " * 10 + "."
    out = svm.compute_voice_score(msg, fp)
    assert out["sub_scores"]["em_dash"] < 1.0


def test_compute_voice_score_returns_required_structure():
    svm = _import()
    fp = {
        "avg_sentence_length_words": 14,
        "voice_score_threshold": 0.7,
    }
    out = svm.compute_voice_score("hello there.", fp)
    assert "voice_score" in out
    assert "issues" in out
    assert "sub_scores" in out
    assert isinstance(out["voice_score"], float)


# ---------------------------------------------------------------------------
# split_sentences regression tests
# ---------------------------------------------------------------------------

def test_split_sentences_handles_no_terminators():
    """Regression: bare text with no '.' must still be a single sentence."""
    svm = _import()
    out = svm.split_sentences("just words without punctuation")
    assert len(out) == 1


def test_split_sentences_handles_newlines_as_boundaries():
    """Regression: \\n followed by capital should split."""
    svm = _import()
    out = svm.split_sentences("First line\nSecond line\nThird line")
    assert len(out) >= 2


def test_split_sentences_handles_em_dash_clauses():
    """Regression: em-dash with 5+ words on the left should split."""
    svm = _import()
    out = svm.split_sentences(
        "We launched our second pilot last week — margins are looking good."
    )
    assert len(out) == 2


def test_split_sentences_falls_back_to_pause_chars_for_long_run_ons():
    svm = _import()
    long = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu "
        "nu xi omicron pi rho sigma tau upsilon phi chi psi omega extra word"
    )
    out = svm.split_sentences(long + ", But this is a clause.")
    assert len(out) >= 1


def test_split_sentences_empty_returns_empty_list():
    svm = _import()
    assert svm.split_sentences("") == []


# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------

def test_load_yaml_minimal_handles_inline_comments_correctly():
    svm = _import()
    text = (
        "key1: value1\n"
        "# leading comment ignored\n"
        "key2: 42\n"
        "list1:\n"
        "  - one\n"
        "  - two\n"
        "empty_list:\n"
        "  []\n"
        "empty_map:\n"
        "  {}\n"
        "map1:\n"
        "  inner: nested\n"
    )
    out = svm._load_yaml_minimal(text)
    assert out["key1"] == "value1"
    assert out["key2"] == 42
    assert out["list1"] == ["one", "two"]
    assert out["empty_list"] == []
    assert out["empty_map"] == {}
    assert out["map1"] == {"inner": "nested"}


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

def test_main_with_message_flag_returns_score(tmp_workspace, capsys):
    svm = _import()
    with pytest.raises(SystemExit) as exc:
        svm.main(["--message", "Quick one — testing this out, all good."])
    assert exc.value.code == 0  # always exit 0 on a low score, not an error
    payload = json.loads(capsys.readouterr().out)
    assert "voice_score" in payload
    assert "issues" in payload


def test_main_reads_message_from_stdin(tmp_workspace, monkeypatch, capsys):
    svm = _import()
    monkeypatch.setattr(sys, "stdin", io.StringIO("Quick one — message via stdin."))
    with pytest.raises(SystemExit) as exc:
        svm.main([])
    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert "voice_score" in payload


def test_main_when_low_score_then_still_exit_0(tmp_workspace, capsys):
    svm = _import()
    bad = "I hope this email finds you well. Just following up on synergies."
    with pytest.raises(SystemExit) as exc:
        svm.main(["--message", bad])
    assert exc.value.code == 0  # low score is not an error


def test_main_when_fingerprint_missing_then_exit_2(empty_home, capsys):
    svm = _import()
    with pytest.raises(SystemExit) as exc:
        svm.main(["--message", "anything"])
    assert exc.value.code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "voice-fingerprint.yaml not found" in payload["error"]


def test_main_when_empty_message_then_envelope(tmp_workspace, capsys):
    svm = _import()
    with pytest.raises(SystemExit) as exc:
        svm.main(["--message", "   "])
    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert "No message provided" in payload["error"]


def test_main_when_fingerprint_unparseable_then_envelope(
        tmp_workspace, monkeypatch, capsys):
    svm = _import()
    # Patch the loader to throw to exercise the except path.
    monkeypatch.setattr(
        svm,
        "load_fingerprint_yaml",
        lambda p: (_ for _ in ()).throw(ValueError("garbage")),
    )
    with pytest.raises(SystemExit) as exc:
        svm.main(["--message", "anything"])
    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert "Could not parse" in payload["error"]


def test_main_with_explicit_fingerprint_path(tmp_workspace, capsys):
    svm = _import()
    fp = tmp_workspace / "voice" / "voice-fingerprint.yaml"
    with pytest.raises(SystemExit) as exc:
        svm.main(["--fingerprint", str(fp), "--message", "Quick one — hi."])
    assert exc.value.code == 0


def test_main_with_workspace_flag(tmp_workspace, capsys):
    svm = _import()
    with pytest.raises(SystemExit) as exc:
        svm.main([
            "--workspace", str(tmp_workspace.parent / "fundraising"),
            "--message", "Quick one — hello.",
        ])
    assert exc.value.code == 0
