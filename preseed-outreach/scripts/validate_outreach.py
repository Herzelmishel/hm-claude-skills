#!/usr/bin/env python3
"""
validate_outreach.py — preseed-outreach

Comprehensive validation of ~/fundraising/outreach/outreach.csv. Stops at the
first error and emits a JSON error envelope. Exit 1 on any failure, 0 on
success.

Checks performed for every row:
  (a) Anti-voice — message text MUST NOT contain any banned phrase from
      ~/fundraising/.sys/anti-voice.txt (case-insensitive substring).
  (b) ask_stage progression — value must be in vocabulary.yaml ask_stages,
      and progression rules:
        - connection_note populated  → ask_stage in {permission, fast_forward}
        - accepted_dm populated      → ask_stage in {call, fast_forward, pitch}
        - fast_forward_pitch present → ask_stage = fast_forward
        - takeaway_email present     → ask_stage = takeaway
  (c) voice_score column populated — non-empty for every row that has any
      message body.
  (d) needs_human_review correctness — must be "high" when voice_score < 0.7.
  (e) source_url present for every row that uses a personalized hook
      (source_signal column non-empty).

Stdlib only. No yaml dependency: parses vocabulary.yaml ask_stages section
with a simple line scanner since the file shape is fixed by the seed template.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

FUNDRAISING = Path.home() / "fundraising"
OUTREACH_CSV = FUNDRAISING / "outreach" / "outreach.csv"
VOCAB_YAML = FUNDRAISING / ".sys" / "vocabulary.yaml"
ANTI_VOICE = FUNDRAISING / ".sys" / "anti-voice.txt"

MESSAGE_FIELDS = (
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
)

VOICE_THRESHOLD = 0.7


def emit_error(message: str, field: str, fix: str) -> int:
    print(json.dumps({"error": message, "field": field, "fix": fix}))
    return 1


def load_ask_stages() -> list[str]:
    """Parse the ask_stages list from vocabulary.yaml without a YAML library."""
    if not VOCAB_YAML.exists():
        return []
    stages: list[str] = []
    in_section = False
    try:
        for raw in VOCAB_YAML.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if stripped.startswith("ask_stages:"):
                in_section = True
                continue
            if in_section:
                if not stripped:
                    continue
                if stripped.startswith("- "):
                    # Strip optional comment after the value.
                    value = stripped[2:].split("#", 1)[0].strip()
                    # Allow "permission       ← can I send" decorations.
                    value = value.split("←", 1)[0].strip()
                    if value:
                        stages.append(value)
                    continue
                # First non-list, non-blank line ends the section.
                if not raw.startswith((" ", "\t", "-")):
                    break
    except OSError:
        return []
    return stages


def load_anti_voice() -> list[str]:
    if not ANTI_VOICE.exists():
        return []
    phrases: list[str] = []
    try:
        for raw in ANTI_VOICE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            phrases.append(line.lower())
    except OSError:
        return []
    return phrases


def find_banned_phrase(text: str, banned: list[str]) -> str | None:
    if not text:
        return None
    haystack = text.lower()
    for phrase in banned:
        if phrase in haystack:
            return phrase
    return None


def parse_voice_score(value: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def validate_row(
    row: dict[str, str],
    row_index: int,
    ask_stages: list[str],
    banned: list[str],
) -> tuple[str, str, str] | None:
    """Return (error_message, field, fix) or None if row is valid."""
    investor_id = (row.get("investor_id") or "").strip() or f"row_{row_index}"

    # (a) Anti-voice: scan every message field.
    for mf in MESSAGE_FIELDS:
        text = row.get(mf) or ""
        if not text.strip():
            continue
        hit = find_banned_phrase(text, banned)
        if hit:
            return (
                f"Banned phrase detected in {mf} (row {row_index}, investor {investor_id}): "
                f"\"{hit}\"",
                f"{mf} (row {row_index})",
                f"Rewrite the {mf} for investor {investor_id} to remove \"{hit}\". "
                f"See ~/fundraising/.sys/anti-voice.txt for the full ban list and "
                f"voice-fingerprint.yaml for preferred alternatives.",
            )

    # (b) ask_stage progression.
    ask_stage = (row.get("ask_stage") or "").strip()
    if not ask_stage:
        return (
            f"ask_stage is empty on row {row_index} (investor {investor_id}).",
            f"ask_stage (row {row_index})",
            "Set ask_stage to one of: permission, call, pitch, follow_up, "
            "fast_forward, takeaway. See ~/fundraising/.sys/vocabulary.yaml.",
        )
    if ask_stages and ask_stage not in ask_stages:
        return (
            f"ask_stage '{ask_stage}' on row {row_index} is not in vocabulary.yaml.",
            f"ask_stage (row {row_index})",
            f"Set ask_stage to one of {ask_stages}.",
        )

    cn_present = bool((row.get("connection_note") or "").strip())
    dm_present = bool((row.get("accepted_dm") or "").strip())
    ff_present = bool((row.get("fast_forward_pitch") or "").strip())
    tk_present = bool((row.get("takeaway_email") or "").strip())

    if cn_present and ask_stage not in {"permission", "fast_forward"}:
        return (
            f"connection_note populated on row {row_index} but ask_stage is "
            f"'{ask_stage}'.",
            f"ask_stage (row {row_index})",
            "Set ask_stage to 'permission' for a connection note (or "
            "'fast_forward' if the connect was a response to an investor "
            "material request).",
        )
    if dm_present and ask_stage not in {"call", "fast_forward", "pitch"}:
        return (
            f"accepted_dm populated on row {row_index} but ask_stage is "
            f"'{ask_stage}'.",
            f"ask_stage (row {row_index})",
            "Set ask_stage to 'call' for an accepted_dm (or 'fast_forward' / "
            "'pitch' if the investor asked for materials).",
        )
    if ff_present and ask_stage != "fast_forward":
        return (
            f"fast_forward_pitch populated on row {row_index} but ask_stage is "
            f"'{ask_stage}'.",
            f"ask_stage (row {row_index})",
            "Set ask_stage to 'fast_forward' when the investor explicitly "
            "requested materials.",
        )
    if tk_present and ask_stage != "takeaway":
        return (
            f"takeaway_email populated on row {row_index} but ask_stage is "
            f"'{ask_stage}'.",
            f"ask_stage (row {row_index})",
            "Set ask_stage to 'takeaway' for the anti-ghost email.",
        )

    has_any_message = any((row.get(mf) or "").strip() for mf in MESSAGE_FIELDS)

    # (c) voice_score populated for any row with a message.
    voice_raw = (row.get("voice_score") or "").strip()
    if has_any_message and voice_raw == "":
        return (
            f"voice_score is empty on row {row_index} (investor {investor_id}) "
            f"but the row contains a message.",
            f"voice_score (row {row_index})",
            "Run score_voice_match.py against this row's message text to "
            "populate voice_score (0–1).",
        )

    voice_score = parse_voice_score(voice_raw)

    # (d) needs_human_review correctness.
    nhr = (row.get("needs_human_review") or "").strip().lower()
    if voice_score is not None and voice_score < VOICE_THRESHOLD and nhr != "high":
        return (
            f"needs_human_review must be 'high' when voice_score < "
            f"{VOICE_THRESHOLD} (row {row_index}, score={voice_score}).",
            f"needs_human_review (row {row_index})",
            f"Set needs_human_review = 'high' for investor {investor_id} "
            f"because voice_score {voice_score} is below the {VOICE_THRESHOLD} "
            "threshold.",
        )

    # (e) source_url present when source_signal present.
    src_signal = (row.get("source_signal") or "").strip()
    src_url = (row.get("source_url") or "").strip()
    if src_signal and not src_url:
        return (
            f"source_signal populated on row {row_index} but source_url is "
            f"empty.",
            f"source_url (row {row_index})",
            "Add the source_url for this signal. Every personalized hook "
            "must trace to a public URL already in investors.csv.",
        )

    return None


def main() -> int:
    if not OUTREACH_CSV.exists():
        return emit_error(
            "outreach.csv not found",
            field=str(OUTREACH_CSV),
            fix="Run /preseed-outreach to generate the first message set.",
        )
    if not VOCAB_YAML.exists():
        return emit_error(
            "vocabulary.yaml not found",
            field=str(VOCAB_YAML),
            fix="Run /preseed-campaign setup to seed ~/fundraising/.sys/.",
        )

    ask_stages = load_ask_stages()
    banned = load_anti_voice()

    if not banned:
        # Not a hard failure: warn-only via JSON, but continue.
        print(
            json.dumps(
                {
                    "warning": "anti-voice.txt is empty or missing — "
                    "anti-voice check is a no-op.",
                    "field": str(ANTI_VOICE),
                    "fix": "Run /preseed-voice to populate banned phrases.",
                }
            )
        )

    try:
        with OUTREACH_CSV.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader, start=2):
                err = validate_row(row, index, ask_stages, banned)
                if err is not None:
                    message, field, fix = err
                    return emit_error(message, field, fix)
    except (OSError, csv.Error) as exc:
        return emit_error(
            f"Failed to read outreach.csv: {exc}",
            field=str(OUTREACH_CSV),
            fix="Verify the file is valid CSV with a header row.",
        )

    print(json.dumps({"ok": True, "checked": "outreach.csv"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
