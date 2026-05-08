"""Local conftest for preseed-prospect tests.

The scripts under test compute their target paths at import time using
``Path.home()``. We isolate the filesystem by setting ``HOME`` to a per-test
``tmp_path`` *before* any import, then reload the module so the constants
re-bind.
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
    / "preseed-prospect"
    / "scripts"
)


# ----- workspace -----------------------------------------------------------


@pytest.fixture
def tmp_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a fresh ~/fundraising tree under tmp_path and patch HOME."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Path.home() honours $HOME on POSIX
    (tmp_path / "fundraising" / "investors").mkdir(parents=True)
    (tmp_path / "fundraising" / "outreach").mkdir(parents=True)
    (tmp_path / "fundraising" / ".sys").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def seed_vocabulary_yaml(tmp_workspace: Path) -> Path:
    path = tmp_workspace / "fundraising" / ".sys" / "vocabulary.yaml"
    path.write_text(
        # comments are mixed in to lock the regression for the YAML parser
        "# vocabulary.yaml — preseed-prospect\n"
        "roles:\n"
        "  - partner\n"
        "  - principal\n"
        "  - associate\n"
        "  # inline comment\n"
        "  - scout\n"
        "ask_stages:\n"
        "  - permission\n"
        "  - call\n"
        "  - pitch\n"
        "  - follow_up\n"
        "  - fast_forward\n"
        "  - takeaway\n"
        "source_types:\n"
        "  - linkedin\n"
        "  - twitter\n"
        "  - blog\n"
        "  - portfolio_page\n"
        "  - news\n"
        "confidence:\n"
        "  - low\n"
        "  - med\n"
        "  - high\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def seed_schemas_yaml(tmp_workspace: Path) -> Path:
    path = tmp_workspace / "fundraising" / ".sys" / "schemas.yaml"
    path.write_text(
        "# schemas.yaml\n"
        "investors_csv_required_fields:\n"
        "  - investor_id\n"
        "  - first_name\n"
        "  - last_name\n"
        "  - investor_name\n"
        "  - role\n"
        "  - lead_candidate\n"
        "  - linkedin_profile_url\n"
        "  - source_urls\n"
        "  - source_dates\n"
        "  - source_types\n"
        "  - ask_stage\n"
        "  - confidence\n",
        encoding="utf-8",
    )
    return path


# ----- CSV builders --------------------------------------------------------


INVESTORS_HEADER = [
    "investor_id",
    "first_name",
    "last_name",
    "investor_name",
    "role",
    "lead_candidate",
    "linkedin_profile_url",
    "source_urls",
    "source_dates",
    "source_types",
    "ask_stage",
    "confidence",
    "public_contact_path",
    "disqualified",
    "disqualified_reason",
    "investment_evidence",
    "thesis_fit_score",
    "stage_fit_score",
    "check_size_fit_score",
    "warm_path_score",
    "recent_signal_score",
    "geography_fit_score",
    "conflict_severity",
    "portfolio_conflict",
]


def _baseline_row(**overrides) -> dict:
    row = {
        "investor_id": "inv_001",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "investor_name": "Ada Lovelace",
        "role": "partner",
        "lead_candidate": "no",
        "linkedin_profile_url": "https://linkedin.com/in/ada",
        "source_urls": "https://example.com/ada",
        "source_dates": "2025-01-01",
        "source_types": "linkedin",
        "ask_stage": "permission",
        "confidence": "med",
        "public_contact_path": "unknown",
        "disqualified": "",
        "disqualified_reason": "",
        "investment_evidence": "wrote first check at company X",
        "thesis_match_score": "10",
        "stage_fit_score": "10",
        "check_size_fit_score": "5",
        "warm_path_score": "5",
        "recent_signal_score": "5",
        "geography_fit_score": "2",
        "conflict_severity": "",
        "portfolio_conflict": "",
    }
    row.update(overrides)
    return row


@pytest.fixture
def write_investors_csv(tmp_workspace: Path):
    csv_path = tmp_workspace / "fundraising" / "investors" / "investors.csv"

    def _write(rows, header=None):
        hdr = header or INVESTORS_HEADER
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=hdr)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k, "") for k in hdr})
        return csv_path

    return _write


@pytest.fixture
def baseline_row():
    return _baseline_row


# ----- module loaders ------------------------------------------------------


@pytest.fixture
def load_score_investors(tmp_workspace: Path):
    """Import score_investors with HOME pointing at the tmp workspace."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    sys.modules.pop("score_investors", None)
    mod = importlib.import_module("score_investors")
    importlib.reload(mod)
    yield mod
    sys.modules.pop("score_investors", None)
    if str(SCRIPTS_DIR) in sys.path:
        sys.path.remove(str(SCRIPTS_DIR))


@pytest.fixture
def load_validate_investors(tmp_workspace: Path):
    sys.path.insert(0, str(SCRIPTS_DIR))
    sys.modules.pop("validate_investors_csv", None)
    mod = importlib.import_module("validate_investors_csv")
    importlib.reload(mod)
    yield mod
    sys.modules.pop("validate_investors_csv", None)
    if str(SCRIPTS_DIR) in sys.path:
        sys.path.remove(str(SCRIPTS_DIR))


# ----- subprocess runner ---------------------------------------------------


@pytest.fixture
def run_script(tmp_workspace: Path):
    def _run(script_name: str) -> subprocess.CompletedProcess:
        script_path = SCRIPTS_DIR / script_name
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env={"HOME": str(tmp_workspace), "PATH": "/usr/bin:/bin"},
        )
        return proc

    return _run


def parse_last_json(text: str) -> dict:
    """Many scripts emit one JSON object per line; pick the last non-empty one."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise AssertionError("no JSON output")
    return json.loads(lines[-1])


@pytest.fixture
def last_json():
    return parse_last_json
