#!/usr/bin/env python3
"""
count_message_chars.py — preseed-outreach

Reads ~/fundraising/outreach/outreach.csv and validates length limits per
message type:

  - connection_note    ≤ 200 characters     (LinkedIn hard cap)
  - warm_update        ≤ 150 words
  - takeaway_email     ≤ 80 words

Writes the char_count_connection_note column on every row. On any violation,
prints a JSON error envelope to stdout and exits 1. On success, prints a JSON
summary and exits 0.

Stdlib only.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

OUTREACH_CSV = Path.home() / "fundraising" / "outreach" / "outreach.csv"

LIMITS = {
    "connection_note": ("chars", 200),
    "warm_update": ("words", 150),
    "takeaway_email": ("words", 80),
}


def emit_error(message: str, field: str, fix: str) -> None:
    print(json.dumps({"error": message, "field": field, "fix": fix}))


def count_chars(text: str) -> int:
    return len(text or "")


def count_words(text: str) -> int:
    if not text:
        return 0
    # Treat any whitespace-separated run as one word.
    return len(re.findall(r"\S+", text))


def main() -> int:
    if not OUTREACH_CSV.exists():
        emit_error(
            "outreach.csv not found",
            field=str(OUTREACH_CSV),
            fix="Run /preseed-outreach to generate the first message set, "
            "or check that ~/fundraising/outreach/outreach.csv exists.",
        )
        return 1

    try:
        with OUTREACH_CSV.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        emit_error(
            f"Failed to read outreach.csv: {exc}",
            field=str(OUTREACH_CSV),
            fix="Verify the file is valid CSV with a header row.",
        )
        return 1

    for required in ("investor_id", "connection_note", "warm_update", "takeaway_email"):
        if required not in fieldnames:
            emit_error(
                f"Missing required column: {required}",
                field=required,
                fix=f"Add the {required} column to outreach.csv per the schema.",
            )
            return 1

    if "char_count_connection_note" not in fieldnames:
        fieldnames = list(fieldnames) + ["char_count_connection_note"]

    violations = []
    summary = {
        "rows": len(rows),
        "violations": 0,
        "connection_note_violations": 0,
        "warm_update_violations": 0,
        "takeaway_email_violations": 0,
    }

    for index, row in enumerate(rows, start=2):  # header is row 1
        investor_id = row.get("investor_id", "").strip() or f"row_{index}"

        cn = row.get("connection_note", "") or ""
        cn_chars = count_chars(cn)
        row["char_count_connection_note"] = str(cn_chars)
        if cn.strip() and cn_chars > LIMITS["connection_note"][1]:
            summary["connection_note_violations"] += 1
            violations.append(
                {
                    "row": index,
                    "investor_id": investor_id,
                    "field": "connection_note",
                    "limit": LIMITS["connection_note"][1],
                    "unit": "chars",
                    "actual": cn_chars,
                }
            )

        wu = row.get("warm_update", "") or ""
        wu_words = count_words(wu)
        if wu.strip() and wu_words > LIMITS["warm_update"][1]:
            summary["warm_update_violations"] += 1
            violations.append(
                {
                    "row": index,
                    "investor_id": investor_id,
                    "field": "warm_update",
                    "limit": LIMITS["warm_update"][1],
                    "unit": "words",
                    "actual": wu_words,
                }
            )

        te = row.get("takeaway_email", "") or ""
        te_words = count_words(te)
        if te.strip() and te_words > LIMITS["takeaway_email"][1]:
            summary["takeaway_email_violations"] += 1
            violations.append(
                {
                    "row": index,
                    "investor_id": investor_id,
                    "field": "takeaway_email",
                    "limit": LIMITS["takeaway_email"][1],
                    "unit": "words",
                    "actual": te_words,
                }
            )

    summary["violations"] = len(violations)

    # Always write the char_count column back, even on violation.
    try:
        with OUTREACH_CSV.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                row.setdefault("char_count_connection_note", "")
                writer.writerow(row)
    except OSError as exc:
        emit_error(
            f"Failed to write outreach.csv: {exc}",
            field=str(OUTREACH_CSV),
            fix="Verify file permissions on ~/fundraising/outreach/outreach.csv.",
        )
        return 1

    if violations:
        first = violations[0]
        emit_error(
            f"Length limit exceeded for {first['field']} on row {first['row']}: "
            f"{first['actual']} {first['unit']} (limit {first['limit']}).",
            field=f"{first['field']} (investor_id={first['investor_id']})",
            fix=(
                f"Tighten the {first['field']} for investor {first['investor_id']} "
                f"to ≤{first['limit']} {first['unit']}. "
                f"Total violations across file: {len(violations)}. "
                f"See remaining rows in the violations summary."
            ),
        )
        # Print the full violations list as a separate JSON line for tooling.
        print(json.dumps({"violations": violations, "summary": summary}))
        return 1

    print(json.dumps({"ok": True, "summary": summary}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
