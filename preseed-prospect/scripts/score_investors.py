#!/usr/bin/env python3
"""
score_investors.py — apply the investor scoring rubric to investors.csv.

Reads:  ~/fundraising/investors/investors.csv
Writes: ~/fundraising/investors/investors.csv (updated in place)

For each non-disqualified investor row:
  - Validates that source_urls is non-empty (cannot score uncited claims)
  - Computes score_100 from the six factors + conflict penalty
  - Computes score_10 = round(score_100 / 10)
  - If a disqualification reason is present in the row, sets disqualified=yes

For disqualified rows: score_100 and score_10 are left as 0; disqualified=yes.

Outputs JSON summary to stdout on success.
On failure: prints JSON error envelope to stdout and exits 1.

Stdlib only.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

CSV_PATH = Path.home() / "fundraising" / "investors" / "investors.csv"

# Factor maximum weights (must match rubric)
WEIGHTS = {
    "thesis_fit": 30,
    "stage_fit": 25,
    "check_size_fit": 15,
    "warm_path": 15,
    "recent_signal": 10,
    "geography_fit": 5,
}
MAX_CONFLICT_PENALTY = 25


def fail(error: str, field: str = "", fix: str = "") -> None:
    """Emit shared error envelope and exit 1."""
    envelope = {"error": error, "field": field, "fix": fix}
    print(json.dumps(envelope))
    sys.exit(1)


def parse_int(value: str, default: int = 0) -> int:
    if value is None:
        return default
    s = str(value).strip()
    if s == "":
        return default
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return default


def conflict_penalty(severity: str) -> int:
    """Map conflict_severity enum to penalty (0..MAX_CONFLICT_PENALTY)."""
    s = (severity or "").strip().lower()
    if s == "direct":
        return 25
    if s == "adjacent":
        return 10
    if s == "strategic":
        return 5
    return 0


def truthy(v: str) -> bool:
    return (v or "").strip().lower() in {"yes", "true", "1", "y"}


def score_row(row: dict, row_num: int) -> tuple[int, int]:
    """Return (score_100, score_10). Mutates `disqualified` if reason is set without flag."""
    # If disqualified reason present but flag not set, set the flag.
    if (row.get("disqualified_reason") or "").strip() and not truthy(row.get("disqualified")):
        row["disqualified"] = "yes"

    if truthy(row.get("disqualified")):
        # Disqualification still requires a reason
        if not (row.get("disqualified_reason") or "").strip():
            fail(
                error="Disqualified row missing reason",
                field="disqualified_reason",
                fix=f"Row {row_num} has disqualified=yes but no disqualified_reason. Add the gate name (e.g., 'no_preseed_evidence').",
            )
        return 0, 0

    # Score factors expected as integer columns in the CSV.
    # Column names mirror the rubric factor keys for clarity.
    factor_cols = {
        "thesis_fit": "thesis_match",
        "stage_fit": "stage_fit",
        "check_size_fit": "check_size_range",   # qualitative, but operator may pre-grade as int
        "warm_path": "warm_path_evidence",
        "recent_signal": "recent_signal",
        "geography_fit": "geography",
    }

    raw = 0
    for factor, max_pts in WEIGHTS.items():
        # The operator scores each factor as an integer up to max_pts in a *_score column.
        # If a *_score column is missing, fall back to 0 and surface low confidence.
        score_col = f"{factor}_score"
        pts = parse_int(row.get(score_col, ""), default=0)
        if pts < 0:
            pts = 0
        if pts > max_pts:
            pts = max_pts
        raw += pts

    raw -= conflict_penalty(row.get("conflict_severity", ""))
    if raw < 0:
        raw = 0
    if raw > 100:
        raw = 100

    score_10 = round(raw / 10)
    return raw, score_10


def main() -> None:
    if not CSV_PATH.exists():
        fail(
            error="investors.csv not found",
            field=str(CSV_PATH),
            fix="Run /preseed-prospect to generate investors.csv before scoring.",
        )

    with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            fail(
                error="investors.csv has no header row",
                field="header",
                fix="Recreate investors.csv from the schema in ~/fundraising/.sys/schemas.yaml",
            )
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    # Ensure score columns exist so we can write them back.
    for col in ("score_100", "score_10", "disqualified"):
        if col not in fieldnames:
            fieldnames.append(col)

    investors_total = 0
    disqualified_count = 0
    lead_candidates = 0

    for idx, row in enumerate(rows, start=2):  # start=2 because of header
        investors_total += 1

        # Source URL gate — every row needs at least one source unless disqualified.
        source_urls = (row.get("source_urls") or "").strip()
        if not truthy(row.get("disqualified")) and not source_urls:
            fail(
                error="Row missing source_urls",
                field=f"row {idx}: source_urls",
                fix=f"Add at least one source URL for row {idx} ({row.get('investor_name', '')}). Every claim must be sourced — see references/source-quality.md.",
            )

        score_100, score_10 = score_row(row, idx)
        row["score_100"] = str(score_100)
        row["score_10"] = str(score_10)

        if truthy(row.get("disqualified")):
            disqualified_count += 1
        if truthy(row.get("lead_candidate")) and not truthy(row.get("disqualified")):
            lead_candidates += 1

    # Write back atomically.
    tmp_path = CSV_PATH.with_suffix(".csv.tmp")
    with tmp_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Backfill any missing keys to avoid DictWriter ValueError
            for col in fieldnames:
                row.setdefault(col, "")
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    tmp_path.replace(CSV_PATH)

    summary = {
        "ok": True,
        "investors_total": investors_total,
        "disqualified": disqualified_count,
        "lead_candidates": lead_candidates,
        "csv_path": str(CSV_PATH),
    }
    print(json.dumps(summary))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        fail(
            error="Unexpected error scoring investors",
            field=type(exc).__name__,
            fix=f"{exc}. Check investors.csv format and re-run.",
        )
