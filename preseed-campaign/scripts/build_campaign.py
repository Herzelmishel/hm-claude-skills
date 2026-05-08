#!/usr/bin/env python3
"""build_campaign.py — initializes ~/fundraising/ workspace.

Creates the directory tree, copies seed templates from this skill's
references/ into ~/fundraising/.sys/, writes initial campaign.yaml,
and generates GETTING-STARTED.md.

Exit codes:
    0  success
    1  validation failure (error envelope on stdout)
    2  required input file missing
    3  required dependency missing
    4  unsafe operation refused (e.g. attempting to overwrite an
       existing campaign.yaml without --force)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

def fail(error: str, *, field: str = "", fix: str = "", file: str = "",
         line: int = 0, code: int = 1) -> None:
    """Emit JSON error envelope to stdout and exit with given code."""
    envelope = {"error": error, "field": field, "fix": fix}
    if file:
        envelope["file"] = file
    if line:
        envelope["line"] = line
    print(json.dumps(envelope))
    sys.exit(code)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def skill_root() -> Path:
    """Return the directory of the preseed-campaign skill (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def workspace_root() -> Path:
    return Path.home() / "fundraising"


def extract_first_yaml_block(md_path: Path) -> str:
    """Extract the first ```yaml ... ``` fenced block from a markdown file.

    Falls back to the entire file content if no fenced block is found.
    """
    text = md_path.read_text(encoding="utf-8")
    match = re.search(r"```ya?ml\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).rstrip() + "\n"
    return text


def extract_anti_voice_phrases(md_path: Path) -> list[str]:
    """Extract phrases from anti-voice-defaults.md.

    Reads everything after a `## Phrases` marker and pulls each line
    starting with `- `. Falls back to scanning the whole file if no
    marker is present.
    """
    text = md_path.read_text(encoding="utf-8")
    if "## Phrases" in text:
        text = text.split("## Phrases", 1)[1]
    phrases: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        phrase = line[2:].strip()
        # strip trailing inline comment after `  #` or `# `
        phrase = re.split(r"\s+#\s+", phrase, maxsplit=1)[0].strip()
        # strip surrounding quotes if present
        if (phrase.startswith('"') and phrase.endswith('"')) or \
           (phrase.startswith("'") and phrase.endswith("'")):
            phrase = phrase[1:-1]
        if phrase:
            phrases.append(phrase)
    return phrases


# ---------------------------------------------------------------------------
# Directory tree + .sys/ seeding
# ---------------------------------------------------------------------------

DIRS = [
    "",
    ".sys",
    ".sys/logs",
    "voice",
    "voice/samples",
    "story",
    "investors",
    "outreach",
    "prep",
    "pipeline",
]


def make_dirs(root: Path) -> None:
    for sub in DIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)


def seed_sys_config(root: Path, force: bool = False) -> dict:
    """Copy seed templates from the skill into ~/fundraising/.sys/.

    Returns a dict describing which files were written / skipped.
    """
    skill = skill_root()
    refs = skill / "references"

    # anti-voice lives in the preseed-voice skill
    voice_skill_anti = (
        Path.home() / ".claude" / "skills" / "preseed-voice"
        / "references" / "anti-voice-defaults.md"
    )

    plan = [
        # (source_md, dest_yaml, transform)
        (refs / "vocabulary.md", root / ".sys" / "vocabulary.yaml", "yaml_block"),
        (refs / "schemas.md",    root / ".sys" / "schemas.yaml",    "yaml_block_or_full"),
        (refs / "scripts.md",    root / ".sys" / "scripts.yaml",    "yaml_block_or_full"),
    ]

    written: list[str] = []
    skipped: list[str] = []
    missing_sources: list[str] = []

    for src, dest, kind in plan:
        if not src.exists():
            missing_sources.append(str(src))
            continue
        if dest.exists() and not force:
            skipped.append(str(dest))
            continue
        if kind == "yaml_block":
            content = extract_first_yaml_block(src)
        else:
            # schemas.md / scripts.md may be wrapped in a single block or be
            # multiple blocks — preserve full file content as-is so the YAML
            # parsers downstream can use either YAML or markdown structure.
            content = src.read_text(encoding="utf-8")
        dest.write_text(content, encoding="utf-8")
        written.append(str(dest))

    # anti-voice
    anti_dest = root / ".sys" / "anti-voice.txt"
    if anti_dest.exists() and not force:
        skipped.append(str(anti_dest))
    elif voice_skill_anti.exists():
        phrases = extract_anti_voice_phrases(voice_skill_anti)
        if not phrases:
            # safety: write at least a header so downstream scripts find the file
            anti_dest.write_text(
                "# anti-voice phrases — defaults + samples-derived\n",
                encoding="utf-8",
            )
        else:
            header = (
                "# anti-voice phrases — banned in all generated outreach.\n"
                "# Defaults seeded from preseed-voice/references/anti-voice-defaults.md\n"
                "# Append samples-derived phrases below the marker.\n"
                "## defaults\n"
            )
            body = "\n".join(phrases) + "\n"
            anti_dest.write_text(header + body + "## samples\n", encoding="utf-8")
        written.append(str(anti_dest))
    else:
        missing_sources.append(str(voice_skill_anti))

    return {
        "written": written,
        "skipped": skipped,
        "missing_sources": missing_sources,
    }


# ---------------------------------------------------------------------------
# campaign.yaml
# ---------------------------------------------------------------------------

CAMPAIGN_YAML_TEMPLATE = """\
# campaign.yaml — Agentis pre-seed source of truth.
# Updated by /preseed-campaign on every mode run. Do not hand-edit fields
# managed by scripts (current_wave, momentum_score, last_review_date).

version: 1
company: Agentis
stage: pre-seed

# Round economics — placeholder until /preseed-story populates them.
target_raise_usd: 1000000
instrument: SAFE
target_first_close_amount_usd: 500000
target_first_close_date: null

# Wave state.
current_wave: 0
wave_size_target: 12
lead_candidate_pct: 0.60
wave_started_date: null

# Status gates.
campaign_status: setup_complete
story_gate: pending
voice_gate: pending

# Operating modes.
simple_mode: false
snapshot_on_change: false

# Cadence + momentum (managed by scripts).
last_review_date: null
next_review_date: null
momentum_score: null
momentum_score_prev: null

# Setup metadata.
setup_date: {setup_date}
"""


def write_campaign_yaml(root: Path, force: bool) -> Path:
    path = root / "campaign.yaml"
    if path.exists() and not force:
        return path
    content = CAMPAIGN_YAML_TEMPLATE.format(
        setup_date=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# GETTING-STARTED.md
# ---------------------------------------------------------------------------

GETTING_STARTED_TEMPLATE = """\
# Getting Started — Agentis Pre-Seed Campaign

You just ran `/preseed-campaign setup`. This file is generated once. The
seven-day path below takes you from an empty workspace to Wave 1 launched
and the first review run.

## Day 1 — Foundation
- Run `/preseed-story` — produces round brief, one-pager, ICP, terms plan
- Drop 5+ writing samples into `voice/samples/`
  (LinkedIn posts, founder updates, real DMs to advisors — your words only)
- Run `/preseed-voice` — extracts your voice fingerprint

## Day 2 — Network Mapping
- Run `/preseed-prospect lead-only` — first pass, only lead candidates
- Manually verify the top 20 candidates in LinkedIn / Crunchbase
- Identify warm intro paths in `investors/intro-paths.csv`

## Day 3 — Wave 1 Launch
- Run `/preseed-campaign wave` — locks in 10–15 investors (≥60% lead candidates)
- Run `/preseed-outreach` for each Wave 1 investor
- Human-review every message against `outreach/review-checklist.md`
- Send manually (LinkedIn / email) — the suite never sends for you

## Day 4–6 — Pipeline Setup + Intros
- Run `/preseed-pipeline update` after every touch
- Activate warm introducers from `intro-paths.csv`
- Run `/preseed-prep` before each scheduled call

## Day 7 — First Review
- Run `/preseed-campaign review`
- If wave shows any stalled signal, run `/preseed-campaign diagnose`
- Decide: iterate Wave 1 or launch Wave 2

## Where things live

| Path | What it is |
|---|---|
| `campaign.yaml` | Current campaign state (managed by scripts) |
| `.sys/vocabulary.yaml` | Canonical enums — never edit |
| `.sys/schemas.yaml` | CSV + YAML schema reference |
| `.sys/anti-voice.txt` | Banned phrases — append your own at the bottom |
| `voice/samples/` | Drop raw writing samples here (gitignore them) |
| `voice/voice-fingerprint.yaml` | Generated by /preseed-voice |
| `story/round-brief.yaml` | Required gate file — built by /preseed-story |
| `investors/investors.csv` | Scored investor source of truth |
| `pipeline/pipeline.csv` | Current pipeline state |
| `pipeline/touches.csv` | Append-only event log |
| `pipeline/commitments.csv` | Soft commits → signed SAFEs → cash |

## Rules to internalise

1. The suite never sends messages. Every message is a draft for you to review.
2. State lives in CSV/YAML. The Markdown files are generated views — don't
   hand-edit `pipeline.md`, `weekly-summary.md`, `README.md`, or `warm-list.md`.
3. Run a small wave first. Diagnose before expanding.
4. Cite every investor-specific claim. Mark unknown facts as `unknown`.
5. Use warm intro paths before cold outreach when you can.
6. Run the warm-list check every 7 days. Nurture investors are the highest-
   conversion group at first close.
7. Never name-drop another investor in a pitch without
   `soft_circle_permission: yes` recorded in `commitments.csv`.

Generated: {generated_at}
"""


def write_getting_started(root: Path, force: bool) -> Path:
    path = root / "GETTING-STARTED.md"
    if path.exists() and not force:
        return path
    content = GETTING_STARTED_TEMPLATE.format(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Initialize ~/fundraising/ workspace."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files (campaign.yaml, .sys/* seeds).",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Override workspace root (default: ~/fundraising).",
    )
    args = parser.parse_args(argv)

    root = args.workspace if args.workspace is not None else workspace_root()

    # Refuse to clobber an existing campaign without --force.
    campaign_path = root / "campaign.yaml"
    if campaign_path.exists() and not args.force:
        # This is not a fatal error — we still ensure dirs / seeds exist.
        # But we do not rewrite campaign.yaml.
        pass

    try:
        make_dirs(root)
    except OSError as exc:
        fail(
            error=f"Could not create workspace tree: {exc}",
            field="workspace",
            fix=f"Check filesystem permissions on {root}",
            code=1,
        )

    seed_result = seed_sys_config(root, force=args.force)
    if seed_result["missing_sources"]:
        # Seed sources missing means the skill install is incomplete.
        fail(
            error="Missing seed templates in skill directory",
            field="references",
            fix=(
                "Reinstall preseed-campaign and preseed-voice skills. "
                "Missing: " + ", ".join(seed_result["missing_sources"])
            ),
            code=2,
        )

    write_campaign_yaml(root, force=args.force)
    write_getting_started(root, force=args.force)

    summary = {
        "ok": True,
        "workspace": str(root),
        "sys_files_written": seed_result["written"],
        "sys_files_skipped": seed_result["skipped"],
        "campaign_yaml": str(campaign_path),
        "getting_started": str(root / "GETTING-STARTED.md"),
        "next_step": (
            "Run /preseed-story to build the round brief, "
            "then /preseed-voice once samples/ has 3+ files."
        ),
    }
    print(json.dumps(summary, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
