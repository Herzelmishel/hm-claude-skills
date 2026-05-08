"""Tests for preseed-campaign/scripts/build_campaign.py."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


def _import_build_campaign():
    """Fresh import after Path.home() patches are in place."""
    if "build_campaign" in sys.modules:
        del sys.modules["build_campaign"]
    import build_campaign
    return build_campaign


# ---------------------------------------------------------------------------
# Helpers / direct-function tests
# ---------------------------------------------------------------------------

def test_skill_root_resolves_to_preseed_campaign():
    bc = _import_build_campaign()
    root = bc.skill_root()
    assert root.name == "preseed-campaign"
    assert (root / "references" / "vocabulary.md").exists()


def test_workspace_root_uses_path_home(empty_home):
    bc = _import_build_campaign()
    assert bc.workspace_root() == empty_home / "fundraising"


def test_extract_first_yaml_block_pulls_fenced(tmp_path):
    bc = _import_build_campaign()
    md = tmp_path / "x.md"
    md.write_text(
        "Header text\n\n```yaml\nfoo: 1\nbar: two\n```\n\nMore text.\n",
        encoding="utf-8",
    )
    out = bc.extract_first_yaml_block(md)
    assert "foo: 1" in out
    assert "bar: two" in out
    assert out.endswith("\n")


def test_extract_first_yaml_block_falls_back_to_full_when_no_fence(tmp_path):
    bc = _import_build_campaign()
    md = tmp_path / "x.md"
    md.write_text("just text, no fence\n", encoding="utf-8")
    assert bc.extract_first_yaml_block(md) == "just text, no fence\n"


def test_extract_anti_voice_phrases_after_marker(tmp_path):
    bc = _import_build_campaign()
    md = tmp_path / "anti.md"
    md.write_text(
        "intro text\n## Phrases\n- Hello world  # this is a comment\n"
        "- \"quoted phrase\"\n- 'single quoted'\n- # comment-only\n"
        "- normal phrase\n",
        encoding="utf-8",
    )
    phrases = bc.extract_anti_voice_phrases(md)
    assert "Hello world" in phrases
    assert "quoted phrase" in phrases
    assert "single quoted" in phrases
    assert "normal phrase" in phrases


def test_extract_anti_voice_phrases_falls_back_without_marker(tmp_path):
    bc = _import_build_campaign()
    md = tmp_path / "anti.md"
    md.write_text("- one\n- two\n", encoding="utf-8")
    phrases = bc.extract_anti_voice_phrases(md)
    assert phrases == ["one", "two"]


# ---------------------------------------------------------------------------
# Full main() execution
# ---------------------------------------------------------------------------

def test_main_when_fresh_workspace_then_creates_dir_tree_and_seeds(empty_home):
    bc = _import_build_campaign()
    with pytest.raises(SystemExit) as excinfo:
        bc.main([])
    assert excinfo.value.code == 0

    root = empty_home / "fundraising"
    assert root.is_dir()
    for sub in (
        ".sys", ".sys/logs", "voice", "voice/samples",
        "story", "investors", "outreach", "prep", "pipeline",
    ):
        assert (root / sub).is_dir(), f"missing {sub}"

    # .sys files seeded
    assert (root / ".sys" / "vocabulary.yaml").exists()
    assert (root / ".sys" / "schemas.yaml").exists()
    assert (root / ".sys" / "scripts.yaml").exists()
    assert (root / ".sys" / "anti-voice.txt").exists()
    assert (root / "campaign.yaml").exists()
    assert (root / "GETTING-STARTED.md").exists()


def test_main_when_fresh_workspace_then_vocabulary_extracted_correctly(
        empty_home, capsys):
    bc = _import_build_campaign()
    with pytest.raises(SystemExit):
        bc.main([])

    vocab = (empty_home / "fundraising" / ".sys" / "vocabulary.yaml") \
        .read_text(encoding="utf-8")
    assert "roles:" in vocab
    assert "operator_angel" in vocab
    assert "statuses:" in vocab
    # Should not include the markdown wrapper
    assert "```" not in vocab


def test_main_when_fresh_workspace_then_anti_voice_seeded_from_voice_skill(
        empty_home):
    bc = _import_build_campaign()
    with pytest.raises(SystemExit):
        bc.main([])

    text = (empty_home / "fundraising" / ".sys" / "anti-voice.txt") \
        .read_text(encoding="utf-8")
    assert "## defaults" in text
    assert "## samples" in text
    # one of the seed phrases:
    assert "leveraging" in text or "world-class" in text


def test_main_when_campaign_yaml_present_without_force_then_skip_overwrite(
        tmp_workspace, capsys):
    bc = _import_build_campaign()

    sentinel = "## SENTINEL_DO_NOT_OVERWRITE\n"
    campaign_path = tmp_workspace / "campaign.yaml"
    campaign_path.write_text(sentinel + campaign_path.read_text(encoding="utf-8"),
                             encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        bc.main([])
    assert excinfo.value.code == 0
    assert sentinel in campaign_path.read_text(encoding="utf-8")


def test_main_when_force_then_campaign_yaml_rewritten(tmp_workspace):
    bc = _import_build_campaign()
    campaign_path = tmp_workspace / "campaign.yaml"
    campaign_path.write_text("## OLD_CONTENT\n", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        bc.main(["--force"])
    assert excinfo.value.code == 0
    new_text = campaign_path.read_text(encoding="utf-8")
    assert "OLD_CONTENT" not in new_text
    assert "company: Agentis" in new_text


def test_main_when_workspace_flag_then_writes_to_custom_path(empty_home, tmp_path):
    bc = _import_build_campaign()
    custom = tmp_path / "elsewhere"
    with pytest.raises(SystemExit) as excinfo:
        bc.main(["--workspace", str(custom)])
    assert excinfo.value.code == 0
    assert (custom / "campaign.yaml").exists()
    assert (custom / "GETTING-STARTED.md").exists()


def test_campaign_yaml_uses_timezone_aware_datetime(empty_home):
    """Regression: setup_date must come from a timezone-aware utcnow()."""
    bc = _import_build_campaign()
    with pytest.raises(SystemExit):
        bc.main([])

    text = (empty_home / "fundraising" / "campaign.yaml") \
        .read_text(encoding="utf-8")
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert f"setup_date: {today_utc}" in text


def test_getting_started_uses_timezone_aware_datetime(empty_home):
    bc = _import_build_campaign()
    with pytest.raises(SystemExit):
        bc.main([])
    text = (empty_home / "fundraising" / "GETTING-STARTED.md") \
        .read_text(encoding="utf-8")
    assert "UTC" in text


def test_main_when_seed_template_missing_then_emits_error_envelope(
        empty_home, monkeypatch, capsys):
    """Force a missing-source path by pointing the skill_root at an empty dir."""
    bc = _import_build_campaign()

    fake_skill_root = empty_home / "fake_skill"
    (fake_skill_root / "references").mkdir(parents=True)
    monkeypatch.setattr(bc, "skill_root", lambda: fake_skill_root)

    with pytest.raises(SystemExit) as excinfo:
        bc.main([])
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip().splitlines()[-1])
    assert "Missing" in payload["error"]
    assert payload["field"] == "references"


def test_main_when_dir_creation_fails_then_emits_envelope(
        empty_home, monkeypatch, capsys):
    bc = _import_build_campaign()

    def boom(self, *args, **kwargs):
        raise OSError("permission denied")
    monkeypatch.setattr(Path, "mkdir", boom)

    with pytest.raises(SystemExit) as excinfo:
        bc.main([])
    assert excinfo.value.code == 1
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["field"] == "workspace"


def test_seed_sys_config_skips_when_dest_exists_without_force(tmp_workspace):
    bc = _import_build_campaign()
    # All .sys files already exist via tmp_workspace fixture
    result = bc.seed_sys_config(tmp_workspace, force=False)
    assert result["written"] == []
    assert any("vocabulary.yaml" in s for s in result["skipped"])


def test_seed_sys_config_writes_when_force(tmp_workspace):
    bc = _import_build_campaign()
    result = bc.seed_sys_config(tmp_workspace, force=True)
    assert any("vocabulary.yaml" in w for w in result["written"])
    assert any("anti-voice.txt" in w for w in result["written"])


def test_seed_sys_config_writes_default_anti_voice_header_when_no_phrases(
        tmp_workspace, monkeypatch, tmp_path):
    """Cover the empty-phrases branch in seed_sys_config."""
    bc = _import_build_campaign()
    fake_anti = tmp_path / "anti.md"
    fake_anti.write_text("# nothing here, no phrases marker\n", encoding="utf-8")

    real_path = Path

    class _SwapPath(type(Path())):
        pass

    # Easier path: monkeypatch extract_anti_voice_phrases to return [].
    monkeypatch.setattr(bc, "extract_anti_voice_phrases", lambda p: [])
    # Force overwrite so anti-voice.txt gets re-written.
    result = bc.seed_sys_config(tmp_workspace, force=True)
    text = (tmp_workspace / ".sys" / "anti-voice.txt").read_text(encoding="utf-8")
    assert "anti-voice phrases" in text
