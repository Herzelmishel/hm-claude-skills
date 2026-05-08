#!/usr/bin/env python3
"""
validate_investors_csv.py — schema-check ~/fundraising/investors/investors.csv.

Reads:
  - ~/fundraising/investors/investors.csv
  - ~/fundraising/.sys/schemas.yaml         (defines investors.csv schema)
  - ~/fundraising/.sys/vocabulary.yaml      (defines enums)

Checks:
  1. Required-field presence (per schemas.yaml.investors_csv.required_fields)
  2. HeyReach-required fields (first_name, last_name, linkedin_profile_url) populated on every row
  3. source_urls / source_dates / source_types are aligned (same length when split on ';')
  4. No guessed emails in public_contact_path:
       Reject any value matching an email regex unless that exact email also appears
       inside one of the source_urls (i.e. the email was on a public page).
  5. Enum validation: role, ask_stage, source_types — values must be in vocabulary.yaml
  6. Disqualified rows have a disqualified_reason

On first failure: emits the JSON error envelope (with row number + column) and exits 1.
On success: emits {"ok": true, "rows_validated": N}.

Stdlib only — minimal YAML parsed manually for the small subset we need.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

CSV_PATH = Path.home() / "fundraising" / "investors" / "investors.csv"
SCHEMAS_PATH = Path.home() / "fundraising" / ".sys" / "schemas.yaml"
VOCAB_PATH = Path.home() / "fundraising" / ".sys" / "vocabulary.yaml"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

DEFAULT_REQUIRED_FIELDS = [
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
]

HEYREACH_REQUIRED = ["first_name", "last_name", "linkedin_profile_url"]


def fail(error: str, field: str = "", fix: str = "") -> None:
    print(json.dumps({"error": error, "field": field, "fix": fix}))
    sys.exit(1)


def load_yaml_lists(path: Path) -> dict[str, list[str]]:
    """
    Parse a *very* small subset of YAML — only top-level keys mapping to a list of
    `- value` items. Sufficient for vocabulary.yaml and the enum sections of schemas.yaml.

    Returns: {section_name: [values...], ...}
    """
    if not path.exists():
        return {}
    out: dict[str, list[str]] = {}
    current_key: str | None = None
    try:
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                # top-level key (no indentation): "name:" possibly with trailing comment
                if not line.startswith((" ", "\t")) and stripped.endswith(":"):
                    current_key = stripped[:-1].strip()
                    out[current_key] = []
                    continue
                # list item under current_key
                if current_key and stripped.startswith("-"):
                    item = stripped[1:].strip()
                    # strip trailing inline comment
                    if "#" in item:
                        item = item.split("#", 1)[0].strip()
                    # may contain a "|"-separated set on a single line
                    if "|" in item:
                        for part in item.split("|"):
                            p = part.strip()
                            if p:
                                out[current_key].append(p)
                    else:
                        if item:
                            out[current_key].append(item)
    except OSError as exc:
        fail(
            error=f"Could not read {path.name}",
            field=str(path),
            fix=f"{exc}. Run /preseed-campaign setup to regenerate .sys/ files.",
        )
    return out


def load_required_fields() -> list[str]:
    """Try to read required field list from schemas.yaml; fall back to defaults."""
    if not SCHEMAS_PATH.exists():
        return DEFAULT_REQUIRED_FIELDS
    sections = load_yaml_lists(SCHEMAS_PATH)
    # Look for a section named like 'investors_csv_required_fields' or 'investors_required'
    for key in (
        "investors_csv_required_fields",
        "investors_required_fields",
        "investors_required",
    ):
        if key in sections and sections[key]:
            return sections[key]
    return DEFAULT_REQUIRED_FIELDS


def load_enums() -> dict[str, set[str]]:
    vocab = load_yaml_lists(VOCAB_PATH)
    return {
        "roles": set(vocab.get("roles", [])),
        "ask_stages": set(vocab.get("ask_stages", [])),
        "source_types": set(vocab.get("source_types", [])),
        "confidence": set(vocab.get("confidence", [])),
    }


def is_truthy(v: str) -> bool:
    return (v or "").strip().lower() in {"yes", "true", "1", "y"}


def split_semi(value: str) -> list[str]:
    if value is None:
        return []
    return [p.strip() for p in str(value).split(";") if p.strip()]


def main() -> None:
    if not CSV_PATH.exists():
        fail(
            error="investors.csv not found",
            field=str(CSV_PATH),
            fix="Run /preseed-prospect to generate investors.csv before validating.",
        )

    required_fields = load_required_fields()
    enums = load_enums()

    with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            fail(
                error="investors.csv has no header row",
                field="header",
                fix="Recreate investors.csv from the schema in ~/fundraising/.sys/schemas.yaml",
            )
        header = list(reader.fieldnames)

        # Header-level: required columns must exist as columns.
        for col in required_fields:
            if col not in header:
                fail(
                    error="Required column missing from header",
                    field=col,
                    fix=f"Add column '{col}' to investors.csv. See ~/fundraising/.sys/schemas.yaml for full schema.",
                )

        rows_validated = 0
        for idx, row in enumerate(reader, start=2):  # row 1 is header; data starts at 2
            disqualified = is_truthy(row.get("disqualified", ""))

            # 1. Required-field check (per row)
            for col in required_fields:
                # Disqualified rows still need the basics, but ask_stage may be empty
                if disqualified and col in {"ask_stage"}:
                    continue
                if not (row.get(col) or "").strip():
                    fail(
                        error="Missing required field",
                        field=f"row {idx}: {col}",
                        fix=f"Add a value for '{col}' in row {idx} ({row.get('investor_name', '')}). See SKILL.md for required-field list.",
                    )

            # 2. HeyReach-required fields (every row, including disqualified)
            for col in HEYREACH_REQUIRED:
                if not (row.get(col) or "").strip():
                    fail(
                        error="HeyReach-required field missing",
                        field=f"row {idx}: {col}",
                        fix=f"Add '{col}' to row {idx}. HeyReach CSV import requires first_name, last_name, and linkedin_profile_url for every row.",
                    )

            # 3. source_urls / source_dates / source_types alignment
            urls = split_semi(row.get("source_urls", ""))
            dates = split_semi(row.get("source_dates", ""))
            types = split_semi(row.get("source_types", ""))
            if not urls and not disqualified:
                fail(
                    error="No source_urls for non-disqualified investor",
                    field=f"row {idx}: source_urls",
                    fix=f"Add at least one source URL for row {idx}. Every investor claim must be sourced — see references/source-quality.md.",
                )
            if urls and (len(urls) != len(dates) or len(urls) != len(types)):
                fail(
                    error="source_urls / source_dates / source_types length mismatch",
                    field=f"row {idx}: source_urls",
                    fix=f"Row {idx} has {len(urls)} URLs, {len(dates)} dates, {len(types)} types. They must be aligned (same count, same order, ';'-separated).",
                )
            # source_types enum check
            if enums.get("source_types"):
                for t in types:
                    if t not in enums["source_types"]:
                        fail(
                            error="Invalid source_type",
                            field=f"row {idx}: source_types",
                            fix=f"'{t}' is not in vocabulary.yaml source_types. Allowed: {sorted(enums['source_types'])}.",
                        )

            # 4. No guessed emails in public_contact_path
            contact = (row.get("public_contact_path") or "").strip()
            if contact and contact.lower() != "unknown":
                m = EMAIL_RE.search(contact)
                if m:
                    email = m.group(0)
                    sourced = any(email.lower() in u.lower() for u in urls)
                    if not sourced:
                        fail(
                            error="Guessed email in public_contact_path",
                            field=f"row {idx}: public_contact_path",
                            fix=(
                                f"Email '{email}' on row {idx} is not present in any source_url. "
                                "Email-pattern guesses are forbidden — use a contact form URL, LinkedIn URL, or set to 'unknown'. "
                                "See references/source-quality.md."
                            ),
                        )

            # 5. Enum validation: role, ask_stage, confidence
            role = (row.get("role") or "").strip()
            if enums.get("roles") and role and role not in enums["roles"]:
                fail(
                    error="Invalid role",
                    field=f"row {idx}: role",
                    fix=f"'{role}' is not in vocabulary.yaml roles. Allowed: {sorted(enums['roles'])}.",
                )
            ask_stage = (row.get("ask_stage") or "").strip()
            if enums.get("ask_stages") and ask_stage and ask_stage not in enums["ask_stages"]:
                fail(
                    error="Invalid ask_stage",
                    field=f"row {idx}: ask_stage",
                    fix=f"'{ask_stage}' is not in vocabulary.yaml ask_stages. Allowed: {sorted(enums['ask_stages'])}.",
                )
            confidence = (row.get("confidence") or "").strip()
            if enums.get("confidence") and confidence and confidence not in enums["confidence"]:
                fail(
                    error="Invalid confidence value",
                    field=f"row {idx}: confidence",
                    fix=f"'{confidence}' is not in vocabulary.yaml confidence. Allowed: {sorted(enums['confidence'])}.",
                )

            # 6. Disqualified rows must have a reason
            if disqualified and not (row.get("disqualified_reason") or "").strip():
                fail(
                    error="Disqualified row missing reason",
                    field=f"row {idx}: disqualified_reason",
                    fix=f"Row {idx} has disqualified=yes but no disqualified_reason. Add the gate name (see references/disqualification-rules.md).",
                )

            rows_validated += 1

    print(json.dumps({"ok": True, "rows_validated": rows_validated, "csv_path": str(CSV_PATH)}))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        fail(
            error="Unexpected error validating investors.csv",
            field=type(exc).__name__,
            fix=f"{exc}. Check investors.csv format and re-run.",
        )
