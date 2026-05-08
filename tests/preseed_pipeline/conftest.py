"""Shared pytest fixtures for preseed-pipeline script tests.

These tests exercise the six scripts in
~/.claude/skills/preseed-pipeline/scripts/ as black boxes.

The scripts read/write files under ``Path.home() / "fundraising"``, so each
test gets its own isolated workspace via a redirected ``HOME`` env var.
"""
from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest


SCRIPTS_DIR = Path.home() / ".claude" / "skills" / "preseed-pipeline" / "scripts"


# --------------------------------------------------------------------------
# Workspace fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def tmp_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a fundraising/ workspace under a fresh fake HOME.

    Scripts hard-code ``Path.home() / "fundraising"``. Redirecting HOME
    isolates each test and prevents accidental writes to the real workspace.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fundraising = fake_home / "fundraising"
    (fundraising / "pipeline").mkdir(parents=True)
    (fundraising / "outreach").mkdir(parents=True)
    (fundraising / "investors").mkdir(parents=True)
    (fundraising / ".sys").mkdir(parents=True)
    (fundraising / "voice").mkdir(parents=True)

    monkeypatch.setenv("HOME", str(fake_home))
    # Some libs cache HOME via expanduser; clear those too.
    monkeypatch.setenv("USERPROFILE", str(fake_home))

    return fundraising


@pytest.fixture
def seed_vocabulary_yaml(tmp_workspace: Path) -> Path:
    """Write a vocabulary.yaml with a comment line inside the statuses block.

    Regression: the parser must skip ``#`` lines instead of treating them
    as a section terminator.
    """
    text = dedent(
        """
        # vocabulary.yaml — preseed pipeline

        statuses:
          # Outreach lifecycle
          - identified
          - approved
          - connection_sent
          - connected
          - first_dm_sent
          # Reply branches
          - replied_positive
          - replied_neutral
          - replied_negative
          - intro_call_booked
          - intro_call_done
          - partner_meeting_booked
          - partner_meeting_done
          - data_room_accessed
          - diligence
          - soft_commit
          - terms_sent
          - signed_safe
          - cash_received
          - pass
          - ghosted
          - nurture
          - do_not_contact

        channels:
          - linkedin
          - email
          - twitter
        """
    ).strip() + "\n"
    target = tmp_workspace / ".sys" / "vocabulary.yaml"
    target.write_text(text, encoding="utf-8")
    return target


@pytest.fixture
def seed_schemas_yaml(tmp_workspace: Path) -> Path:
    target = tmp_workspace / ".sys" / "schemas.yaml"
    target.write_text("schemas: {}\n", encoding="utf-8")
    return target


@pytest.fixture
def sample_voice_fingerprint(tmp_workspace: Path) -> Path:
    text = dedent(
        """
        register: direct
        voice_score_threshold: 0.7
        avg_sentence_length_words: 14
        opener_patterns:
          - "Picking this back up — "
          - "Quick one — "
        """
    ).strip() + "\n"
    target = tmp_workspace / "voice" / "voice-fingerprint.yaml"
    target.write_text(text, encoding="utf-8")
    return target


# --------------------------------------------------------------------------
# CSV helpers
# --------------------------------------------------------------------------
PIPELINE_FIELDS = [
    "investor_id",
    "investor_name",
    "status",
    "score_10",
    "lead_candidate",
    "last_touch_date",
    "last_warm_touch",
    "last_meeting_date",
    "data_room_accessed_date",
    "ghost_flag_date",
    "takeaway_sent_date",
    "pass_reason",
    "reapproach_trigger",
    "next_action",
    "next_action_date",
    "notes",
]

TOUCH_FIELDS = [
    "touch_id",
    "investor_id",
    "touch_date",
    "touch_type",
    "channel",
    "message_id",
    "material_interaction",
    "status_before",
    "status_after",
    "estimated_minutes",
    "owner",
    "notes",
    "source",
]

INVESTOR_FIELDS = [
    "investor_id",
    "investor_name",
    "first_name",
    "last_name",
    "firm_or_handle",
    "role",
    "operator_relevance",
    "domain_fit",
    "thesis_match",
    "geography",
    "check_size_range",
]

COMMITMENT_FIELDS = [
    "investor_id",
    "investor_name",
    "soft_circle_permission",
    "commitment_status",
    "soft_commit_amount",
    "signed_safe_amount",
    "cash_received_amount",
    "notes",
]


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


@pytest.fixture
def write_pipeline(tmp_workspace: Path):
    """Factory to write pipeline.csv with custom rows."""
    def _write(rows: list[dict], fields: list[str] | None = None) -> Path:
        path = tmp_workspace / "pipeline" / "pipeline.csv"
        write_csv(path, fields or PIPELINE_FIELDS, rows)
        return path
    return _write


@pytest.fixture
def write_touches(tmp_workspace: Path):
    def _write(rows: list[dict], fields: list[str] | None = None) -> Path:
        path = tmp_workspace / "pipeline" / "touches.csv"
        write_csv(path, fields or TOUCH_FIELDS, rows)
        return path
    return _write


@pytest.fixture
def write_commitments(tmp_workspace: Path):
    def _write(rows: list[dict], fields: list[str] | None = None) -> Path:
        path = tmp_workspace / "pipeline" / "commitments.csv"
        write_csv(path, fields or COMMITMENT_FIELDS, rows)
        return path
    return _write


@pytest.fixture
def write_investors(tmp_workspace: Path):
    def _write(rows: list[dict], fields: list[str] | None = None) -> Path:
        path = tmp_workspace / "investors" / "investors.csv"
        write_csv(path, fields or INVESTOR_FIELDS, rows)
        return path
    return _write


@pytest.fixture
def sample_investors_csv(write_investors) -> Path:
    rows = [
        {
            "investor_id": "inv_001",
            "investor_name": "Alice Operator",
            "first_name": "Alice",
            "last_name": "Operator",
            "firm_or_handle": "@aliceop",
            "role": "operator_angel",
            "operator_relevance": "B2B SaaS pricing operator",
            "geography": "NYC",
            "check_size_range": "25k-50k",
        },
        {
            "investor_id": "inv_002",
            "investor_name": "Bob Builder",
            "first_name": "Bob",
            "last_name": "Builder",
            "firm_or_handle": "Builder Capital",
            "role": "preseed_fund",
            "thesis_match": "AI for commerce",
            "geography": "SF",
            "check_size_range": "100k-250k",
        },
        {
            "investor_id": "inv_003",
            "investor_name": "Carol Commerce",
            "first_name": "Carol",
            "last_name": "Commerce",
            "firm_or_handle": "@carolc",
            "role": "commerce_founder_angel",
            "domain_fit": "ecommerce ops",
            "geography": "LA",
        },
    ]
    return write_investors(rows)


@pytest.fixture
def sample_pipeline_state(write_pipeline, write_touches):
    """Return ({pipeline_path, touches_path}, helper) with several investors."""
    pipeline_rows = [
        {
            "investor_id": "inv_001",
            "investor_name": "Alice Operator",
            "status": "connected",
            "score_10": "8",
            "lead_candidate": "yes",
        },
        {
            "investor_id": "inv_002",
            "investor_name": "Bob Builder",
            "status": "intro_call_done",
            "score_10": "9",
            "last_meeting_date": "2026-04-01",
        },
        {
            "investor_id": "inv_003",
            "investor_name": "Carol Commerce",
            "status": "nurture",
            "score_10": "7",
            "last_warm_touch": "2026-03-15",
        },
    ]
    write_pipeline(pipeline_rows)
    write_touches([])
    return pipeline_rows


# --------------------------------------------------------------------------
# Subprocess runner
# --------------------------------------------------------------------------
@pytest.fixture
def run_script(monkeypatch: pytest.MonkeyPatch):
    """Run a pipeline script as a subprocess with the test's HOME.

    Returns CompletedProcess with stdout/stderr/returncode.
    """
    def _run(name: str, *args: str, env_overrides: dict | None = None,
             input_text: str | None = None) -> subprocess.CompletedProcess:
        script = SCRIPTS_DIR / name
        if not script.exists():
            raise FileNotFoundError(script)
        env = os.environ.copy()
        # Critical: the monkeypatched HOME must reach the subprocess.
        env["HOME"] = os.environ.get("HOME", env["HOME"])
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONWARNINGS"] = "error::DeprecationWarning"
        # Forward coverage subprocess startup variables if set.
        for cov_var in ("COVERAGE_PROCESS_START", "PYTHONPATH"):
            if cov_var in os.environ:
                env[cov_var] = os.environ[cov_var]
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True,
            text=True,
            env=env,
            input=input_text,
            timeout=20,
        )
    return _run
