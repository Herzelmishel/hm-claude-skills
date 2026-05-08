"""Regression test: preseed-pipeline SKILL.md must enforce the story gate."""
from pathlib import Path

SKILL_MD = Path(__file__).resolve().parents[2] / "preseed-pipeline" / "SKILL.md"


def test_skill_md_exists():
    assert SKILL_MD.is_file(), f"Expected {SKILL_MD} to exist"


def test_skill_md_references_round_brief_yaml():
    """Story gate: SKILL.md must reference round-brief.yaml as a precondition."""
    text = SKILL_MD.read_text()
    assert "round-brief.yaml" in text, (
        "preseed-pipeline/SKILL.md must reference story/round-brief.yaml "
        "as a precondition (story gate)."
    )


def test_skill_md_mentions_preseed_story():
    """User must be told to run /preseed-story when round-brief is missing."""
    text = SKILL_MD.read_text()
    assert "/preseed-story" in text, (
        "preseed-pipeline/SKILL.md must instruct user to run /preseed-story "
        "when story/round-brief.yaml is missing."
    )


def test_skill_md_has_pre_checks_section():
    """Pre-checks section must exist (the gate lives there)."""
    text = SKILL_MD.read_text().lower()
    assert "pre-check" in text or "preconditions" in text or "before doing" in text, (
        "preseed-pipeline/SKILL.md must have a Pre-checks section."
    )
