#!/usr/bin/env python3
"""
campaign_summary.py — preseed-pipeline

Reads pipeline.csv, touches.csv, commitments.csv. Computes:
  - Conversion rates with event-based denominators from touches.csv
  - estimated_hours_spent per investor + totals
  - hours_per_pass / hours_per_commit
  - Bottleneck flags
  - Top 5 next actions by next_action_date overdue / score_10

Writes ~/fundraising/pipeline/weekly-summary.md.
Prints JSON summary to stdout. Exit 1 on any error.

Stdlib only.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

FUNDRAISING = Path.home() / "fundraising"
PIPELINE_CSV = FUNDRAISING / "pipeline" / "pipeline.csv"
TOUCHES_CSV = FUNDRAISING / "pipeline" / "touches.csv"
COMMITMENTS_CSV = FUNDRAISING / "pipeline" / "commitments.csv"
SUMMARY_MD = FUNDRAISING / "pipeline" / "weekly-summary.md"


# Exit codes: 1 validation, 2 missing input, 3 dependency, 4 unsafe.
def emit_error(message: str, field: str, fix: str, code: int = 1) -> int:
    print(json.dumps({"error": message, "field": field, "fix": fix}))
    return code


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_iso(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def safe_div(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 3) if denominator else 0.0


def safe_float(value: str) -> float:
    try:
        return float((value or "0").strip())
    except ValueError:
        return 0.0


def main() -> int:
    if not PIPELINE_CSV.exists():
        return emit_error(
            "pipeline.csv not found",
            field=str(PIPELINE_CSV),
            fix="Run /preseed-campaign setup to initialize pipeline files.",
        )

    pipeline = read_csv(PIPELINE_CSV)
    touches = read_csv(TOUCHES_CSV)
    commitments = read_csv(COMMITMENTS_CSV)

    today = date.today()

    # --- Event-based conversion math.
    def unique_in_status(status: str) -> set[str]:
        return {
            (row.get("investor_id") or "").strip()
            for row in touches
            if (row.get("status_after") or "").strip() == status
            and (row.get("investor_id") or "").strip()
        }

    connection_sent = unique_in_status("connection_sent")
    connected = unique_in_status("connected")
    first_dm_sent = unique_in_status("first_dm_sent")
    replied_positive = unique_in_status("replied_positive")
    replied_neutral = unique_in_status("replied_neutral")
    replied_negative = unique_in_status("replied_negative")
    intro_call_booked = unique_in_status("intro_call_booked")
    intro_call_done = unique_in_status("intro_call_done")
    soft_commit = unique_in_status("soft_commit")
    signed_safe = unique_in_status("signed_safe")
    cash_received = unique_in_status("cash_received")

    replied = replied_positive | replied_neutral | replied_negative

    rates = {
        "accept_rate": safe_div(len(connected), len(connection_sent)),
        "reply_rate": safe_div(len(replied), len(first_dm_sent)),
        "positive_reply_rate": safe_div(len(replied_positive), len(first_dm_sent)),
        "call_booking_rate": safe_div(len(intro_call_booked), len(connected)),
        "call_to_commit_rate": safe_div(len(soft_commit), len(intro_call_done)),
        "signed_to_cash_rate": safe_div(len(cash_received), len(signed_safe)),
    }

    # --- Hours: founder-effort tracking.
    minutes_per_investor: dict[str, int] = {}
    for row in touches:
        iid = (row.get("investor_id") or "").strip()
        if not iid:
            continue
        try:
            minutes = int((row.get("estimated_minutes") or "0").strip() or "0")
        except ValueError:
            minutes = 0
        minutes_per_investor[iid] = minutes_per_investor.get(iid, 0) + minutes

    hours_per_investor = {
        iid: round(minutes / 60.0, 2) for iid, minutes in minutes_per_investor.items()
    }
    total_hours = round(sum(minutes_per_investor.values()) / 60.0, 2)

    # --- Pass / commit hours ratios.
    passed_ids = {
        (row.get("investor_id") or "").strip()
        for row in pipeline
        if (row.get("status") or "").strip() == "pass"
    }
    commit_ids = {
        (row.get("investor_id") or "").strip()
        for row in pipeline
        if (row.get("status") or "").strip()
        in {"soft_commit", "terms_sent", "signed_safe", "cash_received"}
    }

    pass_hours = sum(hours_per_investor.get(i, 0) for i in passed_ids)
    commit_hours = sum(hours_per_investor.get(i, 0) for i in commit_ids)
    hours_per_pass = round(pass_hours / max(len(passed_ids), 1), 2)
    hours_per_commit = round(commit_hours / max(len(commit_ids), 1), 2)

    # --- Bottleneck flags.
    flags: list[str] = []
    if rates["accept_rate"] and rates["accept_rate"] < 0.30:
        flags.append("Low accept rate — review profile, targeting, and connection note.")
    if rates["reply_rate"] and rates["reply_rate"] < 0.20:
        flags.append("Low reply rate — message generic or investor wrong fit.")
    if (
        len(intro_call_done) >= 5
        and rates["call_to_commit_rate"]
        and rates["call_to_commit_rate"] < 0.10
    ):
        flags.append(
            "Calls happening but few commits — story / terms / proof / founder-fit issue."
        )
    if rates["signed_to_cash_rate"] and rates["signed_to_cash_rate"] < 0.70 and len(signed_safe) >= 3:
        flags.append("Slow wire-after-sign — terms or legal complexity; simplify SAFE.")

    # --- Top 5 next actions: order by overdue then score_10.
    actionable = []
    for row in pipeline:
        next_action = (row.get("next_action") or "").strip()
        if not next_action:
            continue
        nad = parse_iso(row.get("next_action_date") or "")
        days_overdue = (today - nad).days if nad else -999
        try:
            score10 = float((row.get("score_10") or "0").strip() or "0")
        except ValueError:
            score10 = 0.0
        actionable.append(
            {
                "investor_id": (row.get("investor_id") or "").strip(),
                "investor_name": (row.get("investor_name") or "").strip(),
                "status": (row.get("status") or "").strip(),
                "next_action": next_action,
                "next_action_date": (row.get("next_action_date") or "").strip(),
                "days_overdue": days_overdue,
                "score_10": score10,
            }
        )
    actionable.sort(key=lambda x: (-x["days_overdue"], -x["score_10"]))
    top5 = actionable[:5]

    # --- Commitments roll-up.
    soft_amount = sum(safe_float(r.get("soft_commit_amount", "")) for r in commitments)
    signed_amount = sum(safe_float(r.get("signed_safe_amount", "")) for r in commitments)
    cash_amount = sum(safe_float(r.get("cash_received_amount", "")) for r in commitments)

    # --- momentum_score: composite of last 7 days activity.
    seven_days_ago = today.toordinal() - 7
    commits_recent = positive_recent = calls_recent = 0
    for row in touches:
        td = parse_iso(row.get("touch_date") or "")
        if not td or td.toordinal() < seven_days_ago:
            continue
        sa = (row.get("status_after") or "").strip()
        if sa in {"soft_commit", "signed_safe", "cash_received"}:
            commits_recent += 1
        if sa == "replied_positive":
            positive_recent += 1
        if sa in {"intro_call_booked", "partner_meeting_booked"}:
            calls_recent += 1
    momentum_score = min(
        100, commits_recent * 40 + positive_recent * 30 + calls_recent * 30
    )

    # --- Render markdown summary.
    lines: list[str] = []
    lines.append(f"# Weekly Summary — {today.isoformat()}")
    lines.append("")
    lines.append("Generated by campaign_summary.py. Do not hand-edit.")
    lines.append("")
    lines.append("## Pipeline State")
    lines.append("")
    lines.append(f"- Investors tracked: {len(pipeline)}")
    lines.append(f"- Soft commits: {len(soft_commit)} (${soft_amount:,.0f})")
    lines.append(f"- Signed SAFEs: {len(signed_safe)} (${signed_amount:,.0f})")
    lines.append(f"- Cash received: {len(cash_received)} (${cash_amount:,.0f})")
    lines.append(f"- Total founder hours spent: {total_hours}h")
    lines.append(f"- Hours / pass: {hours_per_pass}h ({len(passed_ids)} passes)")
    lines.append(f"- Hours / commit: {hours_per_commit}h ({len(commit_ids)} commits)")
    lines.append(f"- Momentum score (last 7 days): {momentum_score}/100")
    lines.append("")
    lines.append("## Conversion Math (event-based, from touches.csv)")
    lines.append("")
    lines.append("| Metric | Rate | Numerator / Denominator |")
    lines.append("|---|---|---|")
    lines.append(f"| Accept rate | {rates['accept_rate']:.1%} | {len(connected)} / {len(connection_sent)} |")
    lines.append(f"| Reply rate | {rates['reply_rate']:.1%} | {len(replied)} / {len(first_dm_sent)} |")
    lines.append(f"| Positive reply rate | {rates['positive_reply_rate']:.1%} | {len(replied_positive)} / {len(first_dm_sent)} |")
    lines.append(f"| Call booking rate | {rates['call_booking_rate']:.1%} | {len(intro_call_booked)} / {len(connected)} |")
    lines.append(f"| Call → commit rate | {rates['call_to_commit_rate']:.1%} | {len(soft_commit)} / {len(intro_call_done)} |")
    lines.append(f"| Signed → cash rate | {rates['signed_to_cash_rate']:.1%} | {len(cash_received)} / {len(signed_safe)} |")
    lines.append("")
    lines.append("## Bottleneck Flags")
    lines.append("")
    if flags:
        for flag in flags:
            lines.append(f"- {flag}")
    else:
        lines.append("- None at current thresholds.")
    lines.append("")
    lines.append("## Top 5 Next Actions")
    lines.append("")
    if not top5:
        lines.append("- No actionable next steps. Run /preseed-pipeline update to capture state.")
    else:
        lines.append("| Investor | Status | Action | Date | Overdue (days) |")
        lines.append("|---|---|---|---|---|")
        for item in top5:
            overdue = item["days_overdue"]
            overdue_label = f"{overdue}" if overdue >= 0 else "—"
            lines.append(
                f"| {item['investor_name'] or item['investor_id']} "
                f"| {item['status']} "
                f"| {item['next_action']} "
                f"| {item['next_action_date']} "
                f"| {overdue_label} |"
            )
    lines.append("")
    lines.append("## Founder Hours per Investor (top 10 by spend)")
    lines.append("")
    top_hours = sorted(hours_per_investor.items(), key=lambda kv: -kv[1])[:10]
    if not top_hours:
        lines.append("- No touches logged yet.")
    else:
        lines.append("| Investor ID | Hours |")
        lines.append("|---|---|")
        for iid, hours in top_hours:
            lines.append(f"| {iid} | {hours} |")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Run `/preseed-pipeline warm-list` to see warm-update cadence (21/45/90).")
    lines.append("- Run `/preseed-campaign diagnose` if any bottleneck flag is set.")
    lines.append("")

    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "ok": True,
        "summary_path": str(SUMMARY_MD),
        "rates": rates,
        "momentum_score": momentum_score,
        "total_hours": total_hours,
        "hours_per_pass": hours_per_pass,
        "hours_per_commit": hours_per_commit,
        "soft_commit_amount": soft_amount,
        "signed_amount": signed_amount,
        "cash_amount": cash_amount,
        "bottleneck_flags": flags,
        "top_actions": top5,
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
