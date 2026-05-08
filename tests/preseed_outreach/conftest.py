"""Local conftest for preseed-outreach tests.

Sets HOME to a tmp_path before importing the scripts so their module-level
``Path.home()`` constants resolve into the test workspace.
"""
from __future__ import annotations

import csv
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "preseed-outreach"
    / "scripts"
)


@pytest.fixture
def tmp_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "fundraising" / "outreach").mkdir(parents=True)
    (tmp_path / "fundraising" / ".sys").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def seed_vocabulary_yaml(tmp_workspace: Path) -> Path:
    path = tmp_workspace / "fundraising" / ".sys" / "vocabulary.yaml"
    path.write_text(
        "# vocabulary.yaml — preseed-outreach\n"
        "ask_stages:\n"
        "  # human-readable comment\n"
        "  - permission       ← can I send\n"
        "  - call\n"
        "  - pitch\n"
        "  - follow_up\n"
        "  - fast_forward    # decoration\n"
        "  - takeaway\n"
        "source_types:\n"
        "  - linkedin\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def seed_anti_voice(tmp_workspace: Path) -> Path:
    path = tmp_workspace / "fundraising" / ".sys" / "anti-voice.txt"
    path.write_text(
        "# Anti-voice phrases\n"
        "synergy\n"
        "leverage\n"
        "circle back\n"
        "\n"
        "# blank above\n",
        encoding="utf-8",
    )
    return path


OUTREACH_HEADER = [
    "investor_id",
    "ask_stage",
    "connection_note",
    "accepted_dm",
    "followup_3_day",
    "followup_7_day",
    "warm_intro_ask",
    "forwardable_intro_blurb",
    "warm_update",
    "pass_response",
    "reapproach_note",
    "fast_forward_pitch",
    "takeaway_email",
    "meeting_confirmation",
    "voice_score",
    "needs_human_review",
    "source_signal",
    "source_url",
]


def _baseline_outreach_row(**overrides) -> dict:
    row = {k: "" for k in OUTREACH_HEADER}
    row.update(
        {
            "investor_id": "inv_001",
            "ask_stage": "permission",
            "connection_note": "Hi — quick note about your portfolio.",
            "voice_score": "0.85",
            "needs_human_review": "low",
            "source_signal": "blog post on margin economics",
            "source_url": "https://example.com/post",
        }
    )
    row.update(overrides)
    return row


@pytest.fixture
def baseline_outreach_row():
    return _baseline_outreach_row


@pytest.fixture
def write_outreach_csv(tmp_workspace: Path):
    csv_path = tmp_workspace / "fundraising" / "outreach" / "outreach.csv"

    def _write(rows, header=None):
        hdr = header or OUTREACH_HEADER
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=hdr)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k, "") for k in hdr})
        return csv_path

    return _write


@pytest.fixture
def load_count_message_chars(tmp_workspace: Path):
    sys.path.insert(0, str(SCRIPTS_DIR))
    sys.modules.pop("count_message_chars", None)
    mod = importlib.import_module("count_message_chars")
    importlib.reload(mod)
    yield mod
    sys.modules.pop("count_message_chars", None)
    if str(SCRIPTS_DIR) in sys.path:
        sys.path.remove(str(SCRIPTS_DIR))


@pytest.fixture
def load_validate_outreach(tmp_workspace: Path):
    sys.path.insert(0, str(SCRIPTS_DIR))
    sys.modules.pop("validate_outreach", None)
    mod = importlib.import_module("validate_outreach")
    importlib.reload(mod)
    yield mod
    sys.modules.pop("validate_outreach", None)
    if str(SCRIPTS_DIR) in sys.path:
        sys.path.remove(str(SCRIPTS_DIR))


@pytest.fixture
def run_script(tmp_workspace: Path):
    def _run(script_name: str) -> subprocess.CompletedProcess:
        script_path = SCRIPTS_DIR / script_name
        return subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env={"HOME": str(tmp_workspace), "PATH": "/usr/bin:/bin"},
        )

    return _run


def parse_last_json(text: str) -> dict:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise AssertionError("no JSON output")
    return json.loads(lines[-1])


@pytest.fixture
def last_json():
    return parse_last_json
