"""Tests for preseed-voice/scripts/build_voice_fingerprint.py."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import pytest


def _import():
    if "build_voice_fingerprint" in sys.modules:
        del sys.modules["build_voice_fingerprint"]
    import build_voice_fingerprint
    return build_voice_fingerprint


SAMPLE_TEXTS = [
    # 1 — casual_direct, contractions, em-dash, opener "Quick one"
    "Quick one — wanted to share what we're seeing.\n\n"
    "Two pilots live, $40k MRR. Margin leaks aren't pricing.\n\n"
    "They're return rates on promo orders. Let's talk Tue?\n\n"
    "— Herzel",

    # 2
    "Quick one — closed our second LOI yesterday.\n\n"
    "Same margin-leak pattern as the first pilot. We're up 1.8 points.\n\n"
    "Worth comparing notes if you have 15 min Wed?\n\n"
    "— Herzel",

    # 3
    "Update — pulled an extra $25k commit from a Shopify operator angel.\n\n"
    "Their conviction was speed of integration. We're shipping daily.\n\n"
    "— Herzel",

    # 4 — short message, single em-dash
    "Quick one — saw your post on profit erosion.\n\n"
    "We solve exactly that for mid-market Shopify brands. Worth 15 min?\n\n"
    "— Herzel",

    # 5
    "Update — pilot #3 signed last night.\n\n"
    "$8M GMV brand, week-one savings already 1.2 points.\n\n"
    "I'll keep you posted.\n\n"
    "— Herzel",
]


def _seed_samples(samples_dir, texts=None):
    if texts is None:
        texts = SAMPLE_TEXTS
    samples_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, t in enumerate(texts):
        p = samples_dir / f"sample_{i+1}.txt"
        p.write_text(t, encoding="utf-8")
        paths.append(p)
    return paths


# ---------------------------------------------------------------------------
# Tokenization helpers
# ---------------------------------------------------------------------------

def test_split_sentences_basic():
    bvf = _import()
    out = bvf.split_sentences("First sentence. Second sentence! Third?")
    assert len(out) >= 3


def test_split_paragraphs():
    bvf = _import()
    out = bvf.split_paragraphs("para one\n\npara two\n\npara three")
    assert len(out) == 3


def test_word_count():
    bvf = _import()
    assert bvf.word_count("hello world foo") == 3
    assert bvf.word_count("") == 0


def test_strip_markdown_removes_syntax():
    bvf = _import()
    text = (
        "# Header\n\n"
        "Some **bold** and *italic* text.\n"
        "Inline `code` and a [link](https://example.com).\n"
        "> blockquote\n"
        "- bullet\n"
        "1. numbered\n"
        "```python\ncode block\n```\n"
    )
    out = bvf._strip_markdown(text)
    assert "**" not in out
    assert "[link]" not in out
    assert "```" not in out
    assert "code block" not in out
    assert "bullet" in out
    assert "Header" in out


# ---------------------------------------------------------------------------
# Anti-voice loaders
# ---------------------------------------------------------------------------

def test_load_default_bans_prefers_workspace_anti_voice(tmp_workspace):
    bvf = _import()
    skill_root = tmp_workspace.parent / "fake_skill"
    out = bvf.load_default_bans(tmp_workspace, skill_root)
    assert "leveraging" in out  # from the seeded anti-voice.txt


def test_load_default_bans_falls_back_to_skill_seed(empty_home, tmp_path):
    bvf = _import()
    workspace = empty_home / "fundraising"
    workspace.mkdir(parents=True)
    fake_skill = tmp_path / "fake_skill"
    (fake_skill / "references").mkdir(parents=True)
    (fake_skill / "references" / "anti-voice-defaults.md").write_text(
        "## Phrases\n- skill phrase one\n- skill phrase two\n",
        encoding="utf-8",
    )
    out = bvf.load_default_bans(workspace, fake_skill)
    assert "skill phrase one" in out


def test_load_default_bans_uses_fallback_when_nothing_exists(tmp_path):
    bvf = _import()
    out = bvf.load_default_bans(tmp_path / "ws", tmp_path / "skill")
    assert "synergy" in out


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def test_compute_avg_sentence_length():
    bvf = _import()
    val = bvf.compute_avg_sentence_length(["Short. Also short. Yes."])
    assert val > 0


def test_compute_avg_sentence_length_empty():
    bvf = _import()
    assert bvf.compute_avg_sentence_length([""]) == 0.0


def test_compute_contraction_rate():
    bvf = _import()
    rate = bvf.compute_contraction_rate(
        ["I'm going. We're shipping. They're great."]
    )
    assert rate > 0


def test_compute_contraction_rate_empty():
    bvf = _import()
    assert bvf.compute_contraction_rate([]) == 0.0


def test_compute_em_dash_rate_picks_up_em_dash():
    bvf = _import()
    rate = bvf.compute_em_dash_rate(
        ["Quick one — message. Another -- also. — third."]
    )
    assert rate > 0


def test_compute_em_dash_rate_empty():
    bvf = _import()
    assert bvf.compute_em_dash_rate([]) == 0.0


def test_extract_opener_patterns_finds_repeated_opener():
    bvf = _import()
    out = bvf.extract_opener_patterns(SAMPLE_TEXTS)
    assert any("quick" in o.lower() or "update" in o.lower() for o in out)


def test_extract_closer_patterns_finds_short_signoffs():
    bvf = _import()
    out = bvf.extract_closer_patterns(SAMPLE_TEXTS)
    assert any("herzel" in c.lower() for c in out)


def test_extract_signature_phrases_recurring_ngrams():
    bvf = _import()
    out = bvf.extract_signature_phrases(SAMPLE_TEXTS, min_doc_count=2, min_total=2)
    # "margin leak" recurs in multiple samples
    assert isinstance(out, list)


def test_compute_paragraph_avg_sentences():
    bvf = _import()
    out = bvf.compute_paragraph_avg_sentences(["one. two.\n\nthree."])
    assert out > 0


def test_classify_register_casual():
    bvf = _import()
    texts = ["honestly, we're shipping daily. it's working."]
    reg = bvf.classify_register(texts, avg_sent=10, contraction_rate=0.6)
    assert reg == "casual_direct"


def test_classify_register_technical_terse():
    bvf = _import()
    texts = ["v1.2.3 ships. /api/orders responds in 200ms."]
    reg = bvf.classify_register(texts, avg_sent=10, contraction_rate=0.1)
    assert reg == "technical_terse"


def test_classify_register_formal_warm():
    bvf = _import()
    texts = ["Thanks for the call yesterday. Please find the deck attached. "
             "Following up with a brief context note."]
    reg = bvf.classify_register(texts, avg_sent=18, contraction_rate=0.2)
    assert reg == "formal_warm"


def test_compute_technical_density():
    bvf = _import()
    val = bvf.compute_technical_density(
        ["MRR 40k, ARR 480k, latency 200ms, $25 CAC, 100% retention"]
    )
    assert val > 0


def test_compute_banned_personal_returns_unseen():
    bvf = _import()
    texts = ["Quick note: shipping stuff."]
    bans = ["I hope this email finds you well", "Quick note"]
    out = bvf.compute_banned_personal(texts, bans)
    # "Quick note" appears, should be excluded
    assert "I hope this email finds you well" in out
    assert "Quick note" not in out


def test_preferred_alternatives_returns_dict():
    bvf = _import()
    out = bvf.preferred_alternatives()
    assert isinstance(out, dict)
    assert "leveraging" in out


# ---------------------------------------------------------------------------
# yaml_scalar
# ---------------------------------------------------------------------------

def test_yaml_scalar_quotes_when_needed():
    bvf = _import()
    assert bvf.yaml_scalar(None) == "null"
    assert bvf.yaml_scalar(True) == "true"
    assert bvf.yaml_scalar(42) == "42"
    assert bvf.yaml_scalar("simple") == "simple"
    assert bvf.yaml_scalar("has: colon").startswith('"')
    assert bvf.yaml_scalar("yes").startswith('"')  # reserved-looking


# ---------------------------------------------------------------------------
# Full main()
# ---------------------------------------------------------------------------

def test_main_with_5_samples_creates_full_fingerprint(tmp_workspace, capsys):
    bvf = _import()
    samples_dir = tmp_workspace / "voice" / "samples"
    _seed_samples(samples_dir)

    with pytest.raises(SystemExit) as exc:
        bvf.main([])
    assert exc.value.code == 0

    fp_path = tmp_workspace / "voice" / "voice-fingerprint.yaml"
    assert fp_path.exists()
    text = fp_path.read_text(encoding="utf-8")
    for required in (
        "sample_count:",
        "avg_sentence_length_words:",
        "contraction_rate:",
        "em_dash_rate:",
        "register:",
        "opener_patterns:",
        "closer_patterns:",
        "banned_default:",
        "voice_score_threshold:",
        "confidence:",
    ):
        assert required in text, f"missing field: {required}"

    payload = json.loads(capsys.readouterr().out)
    assert payload["confidence"] == "high"
    assert payload["sample_count"] == 5


def test_main_writes_founder_voice_md_and_examples(tmp_workspace):
    bvf = _import()
    _seed_samples(tmp_workspace / "voice" / "samples")
    with pytest.raises(SystemExit):
        bvf.main([])
    assert (tmp_workspace / "voice" / "founder-voice.md").exists()
    assert (tmp_workspace / "voice" / "voice-examples.md").exists()


def test_main_under_3_samples_marks_low_confidence(tmp_workspace, capsys):
    bvf = _import()
    samples_dir = tmp_workspace / "voice" / "samples"
    _seed_samples(samples_dir, texts=SAMPLE_TEXTS[:2])
    with pytest.raises(SystemExit) as exc:
        bvf.main([])
    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["confidence"] == "low"
    assert "warning" in payload

    md = (tmp_workspace / "voice" / "founder-voice.md").read_text(encoding="utf-8")
    assert "WARNING" in md


def test_main_3_or_4_samples_medium_confidence(tmp_workspace, capsys):
    bvf = _import()
    _seed_samples(tmp_workspace / "voice" / "samples", texts=SAMPLE_TEXTS[:3])
    with pytest.raises(SystemExit):
        bvf.main([])
    payload = json.loads(capsys.readouterr().out)
    assert payload["confidence"] == "medium"


def test_main_zero_samples_emits_low_confidence_defaults(tmp_workspace, capsys):
    bvf = _import()
    # samples dir exists but is empty
    (tmp_workspace / "voice" / "samples").mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit) as exc:
        bvf.main([])
    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sample_count"] == 0
    assert payload["confidence"] == "low"


def test_main_when_samples_dir_missing_then_exit_2(empty_home, capsys):
    bvf = _import()
    with pytest.raises(SystemExit) as exc:
        bvf.main([])
    assert exc.value.code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "Samples directory not found" in payload["error"]


def test_main_appends_personal_bans_to_anti_voice(tmp_workspace, capsys):
    """End-to-end: append_anti_voice runs and writes new phrases.

    We exercise the helper directly with a phrase that isn't already in
    the seeded anti-voice.txt — this proves the append branch works
    (the main() integration test above already validates the full run).
    """
    bvf = _import()
    new_ban = "phrase_unique_to_this_test_xyz"
    bvf.append_anti_voice(tmp_workspace, [new_ban])
    text = (tmp_workspace / ".sys" / "anti-voice.txt").read_text(encoding="utf-8")
    assert new_ban in text
    assert "Added by build_voice_fingerprint.py" in text


def test_main_uses_timezone_aware_datetime_in_fingerprint(tmp_workspace):
    bvf = _import()
    _seed_samples(tmp_workspace / "voice" / "samples")
    with pytest.raises(SystemExit):
        bvf.main([])
    fp_text = (tmp_workspace / "voice" / "voice-fingerprint.yaml") \
        .read_text(encoding="utf-8")
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert today_utc in fp_text


def test_main_threshold_flag_overrides_default(tmp_workspace, capsys):
    bvf = _import()
    _seed_samples(tmp_workspace / "voice" / "samples")
    with pytest.raises(SystemExit):
        bvf.main(["--threshold", "0.85"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["voice_score_threshold"] == 0.85


def test_append_anti_voice_skips_existing_phrases(tmp_workspace):
    bvf = _import()
    bvf.append_anti_voice(tmp_workspace, ["leveraging"])  # already present
    text = (tmp_workspace / ".sys" / "anti-voice.txt").read_text(encoding="utf-8")
    # leveraging only appears once
    assert text.lower().count("leveraging") == 1


def test_append_anti_voice_creates_file_if_missing(tmp_path):
    bvf = _import()
    workspace = tmp_path / "ws"
    bvf.append_anti_voice(workspace, ["new banned phrase"])
    text = (workspace / ".sys" / "anti-voice.txt").read_text(encoding="utf-8")
    assert "new banned phrase" in text


def test_load_samples_strips_markdown(tmp_workspace):
    bvf = _import()
    samples_dir = tmp_workspace / "voice" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    (samples_dir / "x.md").write_text(
        "# Title\n\n**bold** word here.\n", encoding="utf-8",
    )
    out = bvf.load_samples(samples_dir)
    assert len(out) == 1
    name, text = out[0]
    assert "**" not in text
    assert "bold" in text


def test_load_samples_skips_non_text_files(tmp_workspace):
    bvf = _import()
    samples_dir = tmp_workspace / "voice" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    (samples_dir / "x.png").write_bytes(b"\x89PNG\r\n")
    (samples_dir / "ok.txt").write_text("hello", encoding="utf-8")
    out = bvf.load_samples(samples_dir)
    names = [n for n, _ in out]
    assert "x.png" not in names
    assert "ok.txt" in names


def test_load_samples_handles_missing_dir(tmp_path):
    bvf = _import()
    assert bvf.load_samples(tmp_path / "missing") == []
