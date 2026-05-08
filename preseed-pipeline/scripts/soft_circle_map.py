#!/usr/bin/env python3
"""
soft_circle_map.py — preseed-pipeline

Reads ~/fundraising/pipeline/commitments.csv and writes
~/fundraising/pipeline/soft-circle-map.md — the descriptor-first FOMO
sequencing reference for the round.

Rules (see references/soft-circle-rules.md):
  - Confirmed members = soft_circle_permission == "yes"
    Default rendering: descriptor-first (role / sector). Names ONLY when
    --names-confirmed flag is passed (and even then only as an internal
    column for the user's eyes — never auto-inserted into outreach).
  - Pending = soft_circle_permission == "ask"  → "needs confirmation"
  - No-go  = soft_circle_permission == "no"    → never name-dropped, ever

Optional enrichment: if ~/fundraising/investors/investors.csv is present
the script joins on investor_id to surface role / sector / check_size_range
for the descriptor.

Output: writes the markdown file. Prints JSON summary on stdout.

Exit codes:
  0  success
  1  validation error (e.g., commitments.csv missing required columns)
  2  missing input (commitments.csv not found)

Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

FUNDRAISING = Path.home() / "fundraising"
COMMITMENTS_CSV = FUNDRAISING / "pipeline" / "commitments.csv"
INVESTORS_CSV = FUNDRAISING / "investors" / "investors.csv"
SOFT_CIRCLE_MD = FUNDRAISING / "pipeline" / "soft-circle-map.md"

REQUIRED_COMMITMENT_FIELDS = {
    "investor_id",
    "soft_circle_permission",
}

# FOMO-by-archetype matching table — see references/soft-circle-rules.md.
# Maps the role of a confirmed soft-circle member to the prospect archetypes
# that named member is most likely to compel.
FOMO_MATCH = [
    (
        "operator_angel",
        "Other operator-angels; commerce founders evaluating the round",
    ),
    (
        "commerce_founder_angel",
        "Other commerce-founder-angels; commerce-vertical micro-VCs",
    ),
    (
        "ai_saas_angel",
        "Pattern-matched AI/SaaS angels; AI-infra GPs",
    ),
    (
        "preseed_fund",
        "Solo GPs; other named pre-seed funds; strategic angels on the fence",
    ),
    (
        "micro_vc",
        "Pre-seed funds; well-known operator-angels; fence-sitter angels",
    ),
    (
        "scout",
        "Other scouts; fund-curious angels",
    ),
    (
        "strategic_angel",
        "Industry peers; customer-archetype operators",
    ),
    (
        "customer_advisor_candidate",
        "Customers in adjacent spaces; operator-angels",
    ),
]


def emit_error(message: str, field: str, fix: str, exit_code: int = 1) -> int:
    print(json.dumps({"error": message, "field": field, "fix": fix}))
    return exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate soft-circle-map.md from commitments.csv."
    )
    parser.add_argument(
        "--names-confirmed",
        action="store_true",
        help=(
            "If set, render the internal Name column for confirmed members. "
            "Off by default — descriptor only."
        ),
    )
    return parser.parse_args()


def read_csv_safe(
    path: Path,
) -> tuple[list[str], list[dict[str, str]]] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader.fieldnames or []), list(reader)
    except (OSError, csv.Error):
        return None


def build_investor_index(
    rows: list[dict[str, str]] | None,
) -> dict[str, dict[str, str]]:
    if not rows:
        return {}
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        iid = (row.get("investor_id") or "").strip()
        if iid:
            index[iid] = row
    return index


def descriptor_for(commit: dict[str, str], investor: dict[str, str] | None) -> str:
    """Build a descriptor like 'B2B-SaaS operator-angel'."""
    role = ""
    domain = ""
    geography = ""
    if investor:
        role = (investor.get("role") or "").strip()
        # operator_relevance / domain_fit / thesis_match are free-text; use
        # the most specific one available.
        domain = (
            (investor.get("operator_relevance") or "").strip()
            or (investor.get("domain_fit") or "").strip()
            or (investor.get("thesis_match") or "").strip()
        )
        geography = (investor.get("geography") or "").strip()

    role_clean = role.replace("_", "-") if role else ""
    pieces: list[str] = []
    if domain:
        # First few words — domain fields are sometimes verbose.
        short = " ".join(domain.split()[:6])
        pieces.append(short)
    if role_clean:
        pieces.append(role_clean)
    if not pieces:
        # Fall back to firm_or_handle without revealing a personal name.
        firm = (investor or {}).get("firm_or_handle") or ""
        firm = firm.strip()
        pieces.append(firm or "investor (descriptor missing — fill in role/sector)")
    descriptor = " ".join(pieces).strip()
    if geography:
        descriptor = f"{descriptor} ({geography})"
    return descriptor


def display_name(investor: dict[str, str] | None, commit: dict[str, str]) -> str:
    if investor:
        full = " ".join(
            piece
            for piece in (
                (investor.get("first_name") or "").strip(),
                (investor.get("last_name") or "").strip(),
            )
            if piece
        )
        if full:
            return full
        name = (investor.get("investor_name") or "").strip()
        if name:
            return name
    return (commit.get("investor_name") or "").strip() or (
        commit.get("investor_id") or ""
    ).strip()


def fmt_amount(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    # Plain pass-through; commitments may already store strings like "$50K".
    return value


def fomo_match_for(role: str) -> str:
    role = (role or "").strip()
    for key, message in FOMO_MATCH:
        if role == key:
            return message
    return "Match by archetype: see soft-circle-rules.md FOMO table"


def render_markdown(
    confirmed: list[dict[str, str]],
    pending: list[dict[str, str]],
    no_go: list[dict[str, str]],
    investors: dict[str, dict[str, str]],
    show_names: bool,
    today_iso: str,
) -> str:
    lines: list[str] = []
    lines.append("# Soft Circle Map")
    lines.append("")
    lines.append(f"_Generated by soft_circle_map.py on {today_iso}._")
    lines.append("")
    lines.append(
        "Internal reference. Never share externally. Never auto-insert names "
        "into outreach drafts — the user names a soft-circle member only after "
        "explicit in-session confirmation."
    )
    lines.append("")

    # --- Active soft circle.
    lines.append("## Active soft circle (permission = yes)")
    lines.append("")
    if not confirmed:
        lines.append("_No confirmed soft-circle members yet._")
        lines.append("")
    else:
        if show_names:
            lines.append(
                "| Descriptor | Name (internal only) | Commit | Best-match prospect |"
            )
            lines.append("|---|---|---|---|")
        else:
            lines.append("| Descriptor | Commit | Best-match prospect |")
            lines.append("|---|---|---|")

        for commit in confirmed:
            iid = (commit.get("investor_id") or "").strip()
            inv = investors.get(iid)
            descriptor = descriptor_for(commit, inv)
            role = (inv or {}).get("role", "") if inv else ""
            match = fomo_match_for(role)
            amount = (
                fmt_amount(commit.get("signed_safe_amount", ""))
                or fmt_amount(commit.get("soft_commit_amount", ""))
                or fmt_amount(commit.get("cash_received_amount", ""))
            )
            commit_status = (commit.get("commitment_status") or "").strip()
            commit_cell = amount + (
                f" ({commit_status})" if commit_status and amount else commit_status
            )
            commit_cell = commit_cell.strip() or "—"
            if show_names:
                name = display_name(inv, commit) or "—"
                lines.append(
                    f"| {descriptor} | {name} | {commit_cell} | {match} |"
                )
            else:
                lines.append(f"| {descriptor} | {commit_cell} | {match} |")
        lines.append("")

    # --- FOMO-by-archetype matching table.
    lines.append("## FOMO-by-archetype matching")
    lines.append("")
    lines.append(
        "Different prospect archetypes are moved by different social proof. "
        "Match the strongest soft-circle name to the prospect's archetype:"
    )
    lines.append("")
    lines.append("| Soft-circle member archetype | Prospects most compelled |")
    lines.append("|---|---|")
    for role_key, message in FOMO_MATCH:
        lines.append(f"| {role_key.replace('_', '-')} | {message} |")
    lines.append("")

    # --- Name-drop sequencing strategy.
    lines.append("## Name-drop sequencing strategy")
    lines.append("")
    confirmed_count = len(confirmed)
    if confirmed_count <= 2:
        stage = "Stage A — early wave (0–2 commits)"
        plan = (
            "Use descriptors only. Do not name-drop unless the prospect asks "
            "directly and the named investor's permission covers their archetype."
        )
    elif confirmed_count <= 5:
        stage = "Stage B — mid wave (3–5 commits)"
        plan = (
            "Use the strongest archetype-match name when a prospect explicitly "
            "asks. Save the strongest name for the highest-conviction prospect."
        )
    else:
        stage = "Stage C — closing wave (6+ commits)"
        plan = (
            "Reveal multiple names in sequence. Lead with the highest-credibility "
            "match for each prospect to compress the round."
        )
    lines.append(f"**Current stage:** {stage}")
    lines.append("")
    lines.append(plan)
    lines.append("")
    lines.append(
        "Default reveal pattern: descriptor first (\"we have a [role/sector] "
        "in the soft circle\"), then — only if the prospect asks and the user "
        "confirms in-session — the name."
    )
    lines.append("")

    # --- Needs confirmation.
    lines.append("## Needs confirmation (permission = ask)")
    lines.append("")
    if not pending:
        lines.append("_None._")
    else:
        lines.append("| Descriptor | Notes |")
        lines.append("|---|---|")
        for commit in pending:
            iid = (commit.get("investor_id") or "").strip()
            inv = investors.get(iid)
            descriptor = descriptor_for(commit, inv)
            note = (commit.get("notes") or "").strip() or (
                "Ask explicitly for permission before any name-drop or "
                "descriptor-drop."
            )
            lines.append(f"| {descriptor} | {note} |")
    lines.append("")

    # --- No-go.
    lines.append("## No-go (permission = no)")
    lines.append("")
    if not no_go:
        lines.append("_None._")
    else:
        lines.append("| Descriptor | Notes |")
        lines.append("|---|---|")
        for commit in no_go:
            iid = (commit.get("investor_id") or "").strip()
            inv = investors.get(iid)
            descriptor = descriptor_for(commit, inv)
            note = (commit.get("notes") or "").strip() or (
                "Explicit refusal. Never name-drop in any artifact."
            )
            lines.append(f"| {descriptor} | {note} |")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()

    if not COMMITMENTS_CSV.exists():
        return emit_error(
            "commitments.csv not found",
            field=str(COMMITMENTS_CSV),
            fix="Run /preseed-campaign setup to initialize pipeline files.",
            exit_code=2,
        )

    commit_data = read_csv_safe(COMMITMENTS_CSV)
    if commit_data is None:
        return emit_error(
            "Failed to read commitments.csv",
            field=str(COMMITMENTS_CSV),
            fix="Verify the file is valid CSV with a header row.",
        )

    commit_fields, commit_rows = commit_data
    missing = REQUIRED_COMMITMENT_FIELDS.difference(commit_fields)
    if missing:
        return emit_error(
            f"commitments.csv missing required columns: {sorted(missing)}",
            field="header",
            fix=(
                "Initialize commitments.csv from ~/fundraising/.sys/schemas.yaml "
                "or add the missing columns."
            ),
        )

    investor_data = read_csv_safe(INVESTORS_CSV)
    investors = build_investor_index(
        investor_data[1] if investor_data else None
    )

    confirmed: list[dict[str, str]] = []
    pending: list[dict[str, str]] = []
    no_go: list[dict[str, str]] = []
    for row in commit_rows:
        permission = (row.get("soft_circle_permission") or "").strip().lower()
        if permission == "yes":
            confirmed.append(row)
        elif permission == "ask":
            pending.append(row)
        elif permission == "no":
            no_go.append(row)
        # blank / unknown → skip silently (not yet decided)

    today_iso = date.today().isoformat()
    markdown = render_markdown(
        confirmed=confirmed,
        pending=pending,
        no_go=no_go,
        investors=investors,
        show_names=args.names_confirmed,
        today_iso=today_iso,
    )

    try:
        SOFT_CIRCLE_MD.parent.mkdir(parents=True, exist_ok=True)
        SOFT_CIRCLE_MD.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        return emit_error(
            f"Failed to write soft-circle-map.md: {exc}",
            field=str(SOFT_CIRCLE_MD),
            fix="Verify file permissions on ~/fundraising/pipeline/.",
        )

    print(
        json.dumps(
            {
                "ok": True,
                "generated_at": today_iso,
                "output_path": str(SOFT_CIRCLE_MD),
                "confirmed_count": len(confirmed),
                "pending_count": len(pending),
                "no_go_count": len(no_go),
                "names_rendered": bool(args.names_confirmed),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
