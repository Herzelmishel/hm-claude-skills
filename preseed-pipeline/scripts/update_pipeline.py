#!/usr/bin/env python3
"""
update_pipeline.py — preseed-pipeline

Atomic update for one investor:
  1. Validates --new-status against ~/fundraising/.sys/vocabulary.yaml
  2. Reads pipeline.csv, captures status_before
  3. Updates pipeline.csv (status, last_touch_date, optional ghost / takeaway
     fields)
  4. Appends a new row to touches.csv with a UUID touch_id, status_before,
     status_after, estimated_minutes, channel, owner, notes
  5. If --new-status pass → prompts for pass_reason and reapproach_trigger,
     persists them, and prints next-step instruction to invoke
     reapproach_notes.py
  6. If --new-status ghosted → sets ghost_flag_date = today

Args:
  --investor-id   ID matching investor_id column in investors.csv / pipeline.csv
  --new-status    A status from vocabulary.yaml
  --note          Optional free-form note for touches.csv

Output: JSON summary on stdout. Exit 1 on any error.
Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from datetime import date
from pathlib import Path

FUNDRAISING = Path.home() / "fundraising"
PIPELINE_CSV = FUNDRAISING / "pipeline" / "pipeline.csv"
TOUCHES_CSV = FUNDRAISING / "pipeline" / "touches.csv"
VOCAB_YAML = FUNDRAISING / ".sys" / "vocabulary.yaml"

# Estimated minutes per touch_type (founder-effort tracking).
ESTIMATED_MINUTES = {
    "outreach": 15,
    "meeting": 60,
    "material_sent": 10,
    "material_viewed": 5,
    "warm_update": 10,
    "takeaway": 10,
    "intro_request": 15,
    "diligence_qa": 30,
    "default": 15,
}

# Status → most-likely touch_type (used when caller doesn't pass --touch-type).
STATUS_TO_TOUCH_TYPE = {
    "intro_call_done": "meeting",
    "partner_meeting_done": "meeting",
    "data_room_accessed": "material_viewed",
    "diligence": "diligence_qa",
    "ghosted": "takeaway",
    "pass": "outreach",
    "soft_commit": "meeting",
    "signed_safe": "meeting",
    "cash_received": "meeting",
    "nurture": "warm_update",
    "default": "outreach",
}


# Exit-code conventions (per skill spec):
#   1 validation, 2 missing input, 3 dependency, 4 unsafe/integrity violation
def emit_error(message: str, field: str, fix: str, code: int = 1) -> int:
    print(json.dumps({"error": message, "field": field, "fix": fix}))
    return code


def sanitize_cell(value) -> str:
    """Defuse CSV/spreadsheet formula injection.

    HeyReach and other tools open exported CSV in Excel/Sheets, which
    interprets cells starting with =, +, -, @, tab, or carriage return as
    formulas. Prefix a single quote so the cell is treated as text.
    """
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update pipeline.csv and append a touch.")
    parser.add_argument("--investor-id", required=True)
    parser.add_argument("--new-status", required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--touch-type", default="")
    parser.add_argument("--channel", default="")
    parser.add_argument("--material-interaction", default="none")
    parser.add_argument("--owner", default="herzel")
    parser.add_argument("--pass-reason", default="")
    parser.add_argument("--reapproach-trigger", default="")
    return parser.parse_args()


def load_statuses() -> list[str]:
    """Parse vocabulary.yaml statuses section without a YAML library.

    Section terminates only when a top-level key (letter at column 0
    followed by ':') appears. Blank lines and comments (lines starting
    with '#') are skipped.
    """
    if not VOCAB_YAML.exists():
        return []
    statuses: list[str] = []
    in_section = False
    try:
        for raw in VOCAB_YAML.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if stripped.startswith("statuses:"):
                in_section = True
                continue
            if in_section:
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    # Comment line — skip; do not terminate section.
                    continue
                if stripped.startswith("- "):
                    value = stripped[2:].split("#", 1)[0]
                    value = value.split("←", 1)[0]
                    # Lines may contain "identified | approved | ..." pipe lists.
                    for piece in value.split("|"):
                        token = piece.strip()
                        if token:
                            statuses.append(token)
                    continue
                # Only a top-level key (letter at col 0, has ':') terminates.
                if raw and raw[0].isalpha() and ":" in raw:
                    break
                # Otherwise (indented continuation, etc.) keep scanning.
    except OSError:
        return []
    return statuses


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {key: sanitize_cell(row.get(key, "")) for key in fieldnames}
            )


def append_touch(
    fieldnames: list[str],
    row: dict[str, str],
) -> None:
    """Append a touch row, validating the existing header first.

    csv.DictWriter writes columns in the writer's declared order — if the
    on-disk header has drifted (manual edit, schema change), naive append
    silently misaligns rows. Read the existing header first; if the file
    has data rows, require the script's fieldnames to be a subset of the
    on-disk header and use the on-disk order so we never reorder columns
    under the user's feet. If the file is missing, empty, or header-only,
    (re)write the canonical header and the row.
    """
    file_exists = TOUCHES_CSV.exists()
    existing_header: list[str] | None = None
    has_rows = False

    if file_exists:
        with TOUCHES_CSV.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                existing_header = next(reader)
            except StopIteration:
                existing_header = None
            else:
                # Detect at least one data row beyond the header.
                for _ in reader:
                    has_rows = True
                    break

    if not file_exists or existing_header is None or not has_rows:
        # File missing OR empty OR header-only → (re)initialize with our
        # canonical fieldnames, then write the row.
        with TOUCHES_CSV.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(
                {key: sanitize_cell(row.get(key, "")) for key in fieldnames}
            )
        return

    # Existing header with data rows — must contain every column the script
    # expects to write. Otherwise refuse (integrity violation, exit code 4).
    missing = [f for f in fieldnames if f not in existing_header]
    if missing:
        print(
            json.dumps(
                {
                    "error": "touches.csv header mismatch",
                    "field": "header",
                    "fix": (
                        f"Existing header is {existing_header}, script "
                        f"expects {fieldnames}. Manually align or delete "
                        "touches.csv to recreate."
                    ),
                }
            )
        )
        sys.exit(4)

    # Use the on-disk header order so we never reorder columns under the
    # user's feet. Any extra on-disk columns (forward-compat) get blanks.
    with TOUCHES_CSV.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=existing_header)
        writer.writerow(
            {key: sanitize_cell(row.get(key, "")) for key in existing_header}
        )


def main() -> int:
    args = parse_args()

    if not PIPELINE_CSV.exists():
        return emit_error(
            "pipeline.csv not found",
            field=str(PIPELINE_CSV),
            fix="Run /preseed-campaign setup to initialize pipeline files.",
            code=2,
        )
    if not VOCAB_YAML.exists():
        return emit_error(
            "vocabulary.yaml not found",
            field=str(VOCAB_YAML),
            fix="Run /preseed-campaign setup to seed ~/fundraising/.sys/.",
            code=2,
        )

    statuses = load_statuses()
    if statuses and args.new_status not in statuses:
        return emit_error(
            f"Unknown status '{args.new_status}'",
            field="--new-status",
            fix=f"Use one of: {sorted(set(statuses))}",
        )

    # --- Read pipeline.csv and find investor row.
    try:
        pl_fields, pl_rows = read_csv_rows(PIPELINE_CSV)
    except (OSError, csv.Error) as exc:
        return emit_error(
            f"Failed to read pipeline.csv: {exc}",
            field=str(PIPELINE_CSV),
            fix="Verify the file is valid CSV with a header row.",
        )

    if "investor_id" not in pl_fields:
        return emit_error(
            "investor_id column missing from pipeline.csv",
            field="investor_id",
            fix="Initialize pipeline.csv from ~/fundraising/.sys/schemas.yaml.",
        )

    target_idx = -1
    for idx, row in enumerate(pl_rows):
        if (row.get("investor_id") or "").strip() == args.investor_id:
            target_idx = idx
            break

    if target_idx == -1:
        return emit_error(
            f"investor_id '{args.investor_id}' not found in pipeline.csv",
            field="investor_id",
            fix=f"Add the investor first via /preseed-prospect or check the ID spelling.",
        )

    target = pl_rows[target_idx]
    status_before = (target.get("status") or "").strip()
    today = date.today().isoformat()

    # Ensure all required columns exist; add if missing (forward-compatible).
    for column in (
        "status",
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
    ):
        if column not in pl_fields:
            pl_fields.append(column)
        target.setdefault(column, "")

    # --- Update target row.
    target["status"] = args.new_status
    target["last_touch_date"] = today

    if args.new_status in {"intro_call_done", "partner_meeting_done"}:
        target["last_meeting_date"] = today
    if args.new_status == "data_room_accessed":
        target["data_room_accessed_date"] = today
        # Carry the meeting_date if not already populated.
        if not target.get("last_meeting_date"):
            target["last_meeting_date"] = today
    if args.new_status == "ghosted":
        target["ghost_flag_date"] = today
    if args.new_status == "nurture":
        # warm-list cadence pivots on last_warm_touch.
        target["last_warm_touch"] = today

    # Pass protocol — persist pass_reason / reapproach_trigger if provided.
    pass_protocol_pending = False
    if args.new_status == "pass":
        if args.pass_reason:
            target["pass_reason"] = args.pass_reason
        if args.reapproach_trigger:
            target["reapproach_trigger"] = args.reapproach_trigger
        if not args.pass_reason or not args.reapproach_trigger:
            pass_protocol_pending = True

    notes_existing = target.get("notes") or ""
    if args.note:
        sep = " | " if notes_existing else ""
        target["notes"] = f"{notes_existing}{sep}{today}: {args.note}"

    # --- Write pipeline.csv back.
    try:
        write_csv_rows(PIPELINE_CSV, pl_fields, pl_rows)
    except OSError as exc:
        return emit_error(
            f"Failed to write pipeline.csv: {exc}",
            field=str(PIPELINE_CSV),
            fix="Verify file permissions on ~/fundraising/pipeline/pipeline.csv.",
        )

    # --- Append to touches.csv.
    touch_type = (
        args.touch_type
        or STATUS_TO_TOUCH_TYPE.get(args.new_status, STATUS_TO_TOUCH_TYPE["default"])
    )
    estimated = ESTIMATED_MINUTES.get(touch_type, ESTIMATED_MINUTES["default"])

    touch_fields = [
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
    touch_row = {
        "touch_id": str(uuid.uuid4()),
        "investor_id": args.investor_id,
        "touch_date": today,
        "touch_type": touch_type,
        "channel": args.channel,
        "message_id": "",
        "material_interaction": args.material_interaction or "none",
        "status_before": status_before,
        "status_after": args.new_status,
        "estimated_minutes": str(estimated),
        "owner": args.owner,
        "notes": args.note,
        "source": "update_pipeline.py",
    }

    try:
        append_touch(touch_fields, touch_row)
    except OSError as exc:
        return emit_error(
            f"Failed to append to touches.csv: {exc}",
            field=str(TOUCHES_CSV),
            fix="Verify file permissions on ~/fundraising/pipeline/touches.csv.",
        )

    summary = {
        "ok": True,
        "investor_id": args.investor_id,
        "status_before": status_before,
        "status_after": args.new_status,
        "touch_id": touch_row["touch_id"],
        "estimated_minutes": estimated,
    }

    if pass_protocol_pending:
        summary["next_step"] = (
            "Provide --pass-reason and --reapproach-trigger to complete pass "
            "protocol, then run reapproach_notes.py to draft the re-approach "
            "note."
        )
    elif args.new_status == "pass":
        summary["next_step"] = (
            f"Run reapproach_notes.py --investor-id {args.investor_id} to "
            "generate the re-approach draft."
        )
    elif args.new_status == "ghosted":
        summary["next_step"] = (
            f"Run ghost_check.py to confirm and write the takeaway draft "
            f"for investor {args.investor_id}."
        )

    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
