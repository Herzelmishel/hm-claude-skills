#!/usr/bin/env python3
"""momentum_check.py — compute campaign momentum + velocity status.

Reads:
  ~/fundraising/campaign.yaml
  ~/fundraising/pipeline/touches.csv      (event log, append-only)
  ~/fundraising/pipeline/commitments.csv  (signed/wired/etc — for time-to-close)

Writes:
  Updates campaign.yaml with:
    momentum_score, momentum_score_prev, momentum_trend,
    velocity_status (HEALTHY|WARNING|STALLED), last_momentum_check_date

Stdout (success):
  JSON summary with momentum_score, velocity_status, conversion math,
  and time-to-close computation.

Exit codes:
  0  success
  1  validation error (envelope on stdout)
  2  required input file missing
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

def fail(error: str, *, field: str = "", fix: str = "", file: str = "",
         line: int = 0, code: int = 1) -> None:
    envelope = {"error": error, "field": field, "fix": fix}
    if file:
        envelope["file"] = file
    if line:
        envelope["line"] = line
    print(json.dumps(envelope))
    sys.exit(code)


# ---------------------------------------------------------------------------
# Lightweight YAML read/write — preserves comments and ordering by editing
# only the fields we manage in-place.
# ---------------------------------------------------------------------------

YAML_SCALAR_KEYS = {
    "wave_started_date",
    "target_first_close_date",
    "target_first_close_amount_usd",
    "current_wave",
    "momentum_score",
    "momentum_score_prev",
    "momentum_trend",
    "velocity_status",
    "last_momentum_check_date",
}


def parse_campaign_yaml(text: str) -> dict:
    """Minimal scalar extraction for top-level keys."""
    data: dict = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line or line[0] in (" ", "\t", "-"):
            continue
        if ":" not in line:
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest in {"", "|", ">"}:
            continue
        # strip quotes
        if (rest.startswith('"') and rest.endswith('"')) or \
           (rest.startswith("'") and rest.endswith("'")):
            rest = rest[1:-1]
        if rest.lower() in {"null", "~"}:
            data[key] = None
            continue
        if rest.lower() == "true":
            data[key] = True
            continue
        if rest.lower() == "false":
            data[key] = False
            continue
        # numeric
        try:
            data[key] = int(rest)
            continue
        except ValueError:
            pass
        try:
            data[key] = float(rest)
            continue
        except ValueError:
            pass
        data[key] = rest
    return data


def upsert_campaign_yaml(path: Path, updates: dict) -> None:
    """Update top-level scalar fields in campaign.yaml in place.

    Fields not present are appended at the bottom under a managed block.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    seen: set = set()

    for i, raw in enumerate(lines):
        # only touch top-level keys (no indent)
        if not raw or raw[0] in (" ", "\t", "#", "-"):
            continue
        if ":" not in raw:
            continue
        key, _, _rest = raw.partition(":")
        key_stripped = key.strip()
        if key_stripped in updates and key_stripped not in seen:
            new_val = _yaml_scalar(updates[key_stripped])
            # preserve trailing comment if any
            comment = ""
            if "#" in raw:
                _, comment_part = raw.split("#", 1)
                comment = "  #" + comment_part
            lines[i] = f"{key_stripped}: {new_val}{comment}"
            seen.add(key_stripped)

    appended: list[str] = []
    missing = [k for k in updates if k not in seen]
    if missing:
        if lines and lines[-1].strip() != "":
            appended.append("")
        appended.append("# managed by momentum_check.py")
        for k in missing:
            appended.append(f"{k}: {_yaml_scalar(updates[k])}")

    path.write_text("\n".join(lines + appended) + "\n", encoding="utf-8")


def _yaml_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if re.search(r"[:#\n]", s) or s.strip() != s:
        return '"' + s.replace('"', '\\"') + '"'
    return s


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def read_csv_dicts(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def parse_date(s: str | None):
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # last attempt: ISO date-time
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        return None


def parse_money(s: str | None) -> float:
    if not s:
        return 0.0
    s = re.sub(r"[^0-9.\-]", "", str(s))
    if not s or s == "-" or s == ".":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# Momentum math
# ---------------------------------------------------------------------------

def compute_momentum_score(touches: list[dict], today: date) -> int:
    """Compute a 0-100 momentum score from the last 7 days of touches.

    Each component contribution is clamped to its weight cap, so the
    presence of a single signal of each kind gives a perfect 100:

        score = min(commits, 1) * 40
              + min(replies, 1) * 30
              + min(calls,   1) * 30

    A "call" is any of intro_call_booked or partner_meeting_booked.
    """
    seven_days_ago = today - timedelta(days=7)
    commits = 0
    replies = 0
    calls = 0
    for t in touches:
        d = parse_date(t.get("touch_date"))
        if d is None or d < seven_days_ago or d > today:
            continue
        status_after = (t.get("status_after") or "").strip()
        if status_after == "soft_commit":
            commits += 1
        elif status_after.startswith("replied_positive"):
            replies += 1
        elif status_after in {"intro_call_booked", "partner_meeting_booked"}:
            calls += 1
    score = min(commits, 1) * 40 + min(replies, 1) * 30 + min(calls, 1) * 30
    return min(100, score)


def compute_velocity_status(touches: list[dict], wave_started: date | None,
                            today: date, momentum_score: int) -> str:
    if wave_started is None:
        return "WARNING"

    days_since = (today - wave_started).days

    # Stalled: >14 days, 0 soft_commits, 0 partner_meeting_booked since wave_started
    if days_since > 14:
        commits = 0
        partner_meetings = 0
        for t in touches:
            d = parse_date(t.get("touch_date"))
            if d is None or d < wave_started or d > today:
                continue
            after = (t.get("status_after") or "").strip()
            if after == "soft_commit":
                commits += 1
            elif after == "partner_meeting_booked":
                partner_meetings += 1
        if commits == 0 and partner_meetings == 0:
            return "STALLED"

    # Healthy if: >=1 soft_commit last 7 days OR >=3 partner_meetings last 14 days OR score>=50
    seven = today - timedelta(days=7)
    fourteen = today - timedelta(days=14)
    commits_7 = 0
    partner_14 = 0
    for t in touches:
        d = parse_date(t.get("touch_date"))
        if d is None:
            continue
        after = (t.get("status_after") or "").strip()
        if d >= seven and d <= today and after == "soft_commit":
            commits_7 += 1
        if d >= fourteen and d <= today and after == "partner_meeting_booked":
            partner_14 += 1
    if commits_7 >= 1 or partner_14 >= 3 or momentum_score >= 50:
        return "HEALTHY"

    return "WARNING"


def compute_trend(today_score: int, prev_score) -> str:
    try:
        prev = int(prev_score) if prev_score is not None else None
    except (TypeError, ValueError):
        prev = None
    if prev is None:
        return "unknown"
    delta = today_score - prev
    if delta > 10:
        return "up"
    if delta < -10:
        return "down"
    return "flat"


def compute_time_to_close(touches: list[dict], commitments: list[dict],
                          target_amount: float | None,
                          target_date: date | None,
                          today: date) -> dict:
    """Return time-to-close diagnostics."""
    # Current committed = sum of signed_safe_amount (fallback: soft_commit_amount)
    signed_sum = sum(parse_money(c.get("signed_safe_amount")) for c in commitments)
    soft_sum = sum(parse_money(c.get("soft_commit_amount")) for c in commitments)
    current_committed = signed_sum if signed_sum > 0 else soft_sum

    # Average check size — prefer soft_commit_amount because pre-seed is mostly soft
    check_amounts = [
        parse_money(c.get("soft_commit_amount"))
        for c in commitments
        if parse_money(c.get("soft_commit_amount")) > 0
    ]
    avg_check = mean(check_amounts) if check_amounts else 50_000.0

    # Conversion rate: soft commits / intro calls done
    soft_commit_count = sum(
        1 for t in touches
        if (t.get("status_after") or "").strip() == "soft_commit"
    )
    intro_calls_done = sum(
        1 for t in touches
        if (t.get("status_after") or "").strip() == "intro_call_done"
    )
    call_to_commit_rate = (
        soft_commit_count / intro_calls_done if intro_calls_done > 0 else 0.0
    )

    expected_per_call = avg_check * call_to_commit_rate

    days_remaining = None
    if target_date is not None:
        days_remaining = (target_date - today).days

    gap_remaining = None
    calls_needed = None
    required_per_day = None
    if target_amount is not None:
        gap_remaining = max(0.0, target_amount - current_committed)
        if expected_per_call > 0 and gap_remaining > 0:
            calls_needed = gap_remaining / expected_per_call
            if days_remaining is not None and days_remaining > 0:
                required_per_day = calls_needed / days_remaining

    warnings = []
    if required_per_day is not None:
        if required_per_day > 2:
            warnings.append(
                f"Required pace is {required_per_day:.2f} first-calls/day — "
                "exceeds solo-founder capacity. Extend close date or reduce target."
            )
        elif required_per_day < 0.3 and gap_remaining and gap_remaining > 0:
            warnings.append(
                "Pace is too slow for target close date. "
                "Increase wave size or accelerate outreach."
            )

    return {
        "current_committed_usd": round(current_committed, 2),
        "avg_check_usd": round(avg_check, 2),
        "call_to_commit_rate": round(call_to_commit_rate, 3),
        "expected_per_call_usd": round(expected_per_call, 2),
        "days_remaining": days_remaining,
        "gap_remaining_usd": (
            round(gap_remaining, 2) if gap_remaining is not None else None
        ),
        "calls_needed": (
            round(calls_needed, 2) if calls_needed is not None else None
        ),
        "required_per_day": (
            round(required_per_day, 2) if required_per_day is not None else None
        ),
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Compute momentum + velocity for the campaign."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Override workspace root (default: ~/fundraising).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        default=True,
        help="Write momentum_score back to campaign.yaml (default: true).",
    )
    parser.add_argument(
        "--no-write",
        dest="write",
        action="store_false",
        help="Skip updating campaign.yaml — print summary only.",
    )
    args = parser.parse_args(argv)

    root = args.workspace if args.workspace else (Path.home() / "fundraising")
    campaign_path = root / "campaign.yaml"
    touches_path = root / "pipeline" / "touches.csv"
    commitments_path = root / "pipeline" / "commitments.csv"

    if not campaign_path.exists():
        fail(
            error="campaign.yaml not found",
            field="campaign.yaml",
            fix="Run /preseed-campaign setup first.",
            file=str(campaign_path),
            code=2,
        )

    try:
        campaign_text = campaign_path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(error=f"Could not read campaign.yaml: {exc}", code=1,
             field="campaign.yaml", fix="Check file permissions.")

    campaign = parse_campaign_yaml(campaign_text)

    # touches.csv may not exist yet on a fresh setup — treat as empty
    touches = read_csv_dicts(touches_path)
    commitments = read_csv_dicts(commitments_path)

    today = date.today()
    wave_started = parse_date(campaign.get("wave_started_date"))
    target_date = parse_date(campaign.get("target_first_close_date"))
    target_amount = campaign.get("target_first_close_amount_usd")
    if isinstance(target_amount, str):
        target_amount = parse_money(target_amount) or None

    score = compute_momentum_score(touches, today)
    velocity = compute_velocity_status(touches, wave_started, today, score)
    prev_score = campaign.get("momentum_score")
    trend = compute_trend(score, prev_score)

    ttc = compute_time_to_close(
        touches, commitments,
        float(target_amount) if isinstance(target_amount, (int, float)) else None,
        target_date,
        today,
    )

    if args.write:
        try:
            upsert_campaign_yaml(
                campaign_path,
                {
                    "momentum_score_prev": prev_score if prev_score is not None else "null",
                    "momentum_score": score,
                    "momentum_trend": trend,
                    "velocity_status": velocity,
                    "last_momentum_check_date": today.strftime("%Y-%m-%d"),
                },
            )
        except OSError as exc:
            fail(
                error=f"Could not update campaign.yaml: {exc}",
                field="campaign.yaml",
                fix="Check write permissions on the workspace.",
                file=str(campaign_path),
                code=1,
            )

    summary = {
        "ok": True,
        "today": today.strftime("%Y-%m-%d"),
        "wave_started_date": (
            wave_started.strftime("%Y-%m-%d") if wave_started else None
        ),
        "momentum_score": score,
        "momentum_score_prev": (
            int(prev_score) if isinstance(prev_score, (int, float)) else None
        ),
        "momentum_trend": trend,
        "velocity_status": velocity,
        "touches_count": len(touches),
        "commitments_count": len(commitments),
        "time_to_close": ttc,
    }
    print(json.dumps(summary, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
