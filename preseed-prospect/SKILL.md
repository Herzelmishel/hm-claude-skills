---
name: preseed-prospect
description: Research and score pre-seed investors for Agentis. Generates investor list, lead candidates, intro paths, and source-of-truth CSVs. Network-first — maps Herzel's warm paths before any cold candidate. Every claim is sourced; unknown facts are marked unknown, never guessed.
argument-hint: "[wave size] or [lead-only]"
---

# preseed-prospect

Build the scored investor list, lead-candidate roster, and warm-path map that `/preseed-campaign wave` consumes. This skill is research, scoring, and disqualification — never message drafting (use `/preseed-outreach`) and never single-investor deep prep (use `/preseed-prep`).

## When to use

- After `/preseed-story` has produced `round-brief.yaml` and `investor-icp.md`
- At the start of every wave to add new candidates and rescore existing ones
- After a story refresh that materially changes the ICP
- When the warm-list runs thin and the campaign needs new candidates to map intro paths to

## When NOT to use

- Before `/preseed-story` is complete — the ICP and Fundability Diagnosis drive scoring
- To research a single named investor in depth — use `/preseed-prep`
- For outreach drafting — use `/preseed-outreach`
- For pipeline state changes — use `/preseed-pipeline`

## Pre-checks (stop with plain-language fix on failure)

1. `~/fundraising/campaign.yaml` exists. If missing → run `/preseed-campaign setup`.
2. `~/fundraising/.sys/vocabulary.yaml` exists. If missing → run setup.
3. `~/fundraising/.sys/schemas.yaml` exists (defines `investors.csv` + `intro-paths.csv` schemas). Load the CSV schemas from here — do not redefine.
4. `~/fundraising/story/round-brief.yaml` exists. If missing → tell user to run `/preseed-story` first. No prospecting without a story.
5. `~/fundraising/story/investor-icp.md` exists with both inclusion and exclusion sections.

Always load `vocabulary.yaml` from `.sys/`, never from this skill's directory.

## Workflow (9 steps)

1. **Load context.** Read `round-brief.yaml`, `investor-icp.md`, and the live Fundability Diagnosis section from `round-brief.md`. The diagnosis fields 5 and 6 (best/worst archetype) drive prioritization and disqualification.
2. **Generate candidates.** Use the network-first approach below before generating any cold candidates.
3. **Verify each candidate** with public sources. Every claim needs `source_url` + `source_date` + `source_type`. See `references/source-quality.md` for hierarchy and rules.
4. **Apply disqualification gates.** Set `disqualified: yes` and populate `disqualified_reason` for any candidate hitting a gate. See `references/disqualification-rules.md`.
5. **Score remaining investors** with the rubric (`references/investor-scoring-rubric.md`). Run `scripts/score_investors.py` to compute `score_100` and `score_10`.
6. **Designate lead candidates.** Apply lead-candidate rules below. Mark `lead_candidate: yes/no`.
7. **Map warm intro paths.** Populate `intro-paths.csv` for every investor with a plausible warm route — even weak. Mark `relationship_strength` honestly.
8. **Select wave cohort.** Apply wave rules from `/preseed-campaign` (Wave 1 ≥60% lead candidates).
9. **Validate and write.** Run `scripts/validate_investors_csv.py` before finalizing. Surface any error envelope verbatim with the row + column.

## Network-First Approach

Before generating any cold candidate, map Herzel's existing graph:

- LinkedIn 2nd-degree connections to known pre-seed investors
- Alumni networks (Herzel's prior companies, schools, professional groups) for investor-role connections
- Portfolio company founders of likely micro-VCs — these founders are the highest-conversion warm path
- Existing customer-advisor candidates and operator-angels in commerce
- Any investor who has met Herzel before, even casually (record `prior_contact: yes` in notes)

Source intro paths from this map first. Only after the warm graph is exhausted for the wave size do you supplement with cold candidates. Cold candidates that score high but have no warm path go to a separate "cold queue" — not into the wave.

## Disqualification Gates

Eight gates (full rubric in `references/disqualification-rules.md`). Setting `disqualified: yes` requires populating `disqualified_reason` with the specific gate triggered.

1. Direct competitor portfolio conflict
2. No pre-seed or angel evidence in last 18 months
3. Check size mismatch (min check >$1M, or stated max <$25k)
4. No relevant domain fit (no commerce, no operations SaaS, no relevant ai/data thesis)
5. No public source for any claimed fit
6. Prior pass — unless the story has materially changed (see disqualification-rules.md for what "material" means)
7. Strategic conflict (cap table or fund position incompatible with Agentis)
8. Investor currently inactive (no investment, post, or content in last 12 months)

## Lead Candidate Rules

Only investors meeting *all* of these are marked `lead_candidate: yes`:

- Public evidence of leading or anchoring at least one pre-seed round in the last 18 months
- Willing and able to set terms (SAFE cap, MFN, pro-rata) — usually means a fund GP or a serial angel with a known check pattern
- Reachable through a warm path with `relationship_strength` ≥ medium, OR a credible cold path with strong recent signal
- Check size band overlaps Agentis's lead-reserve allocation (typically $250k–$750k at pre-seed)

Wave 1 must have ≥60% lead candidates. The wave selector enforces this.

## Scoring Model (100 points)

Detailed bands and verification rules in `references/investor-scoring-rubric.md`.

| Factor | Weight |
|---|---|
| Thesis / domain fit | 30 |
| Stage fit | 25 |
| Check-size fit | 15 |
| Warm path evidence | 15 |
| Recent signal | 10 |
| Geography fit | 5 |
| Portfolio conflict penalty | up to −25 |

`score_10` is `round(score_100 / 10)` — used for wave selection and pipeline display.

## `investors.csv` schema reference

The full column list is defined in `~/fundraising/.sys/schemas.yaml`. The plan summarizes columns; the schemas file is canonical. Required-for-HeyReach columns: `first_name`, `last_name`, `linkedin_profile_url` — all three must be present for every row that will be exported. `validate_investors_csv.py` enforces this.

Every row also requires:
- `source_urls` (semicolon-separated, ≥1 URL)
- `source_dates` (semicolon-separated, same length as source_urls)
- `source_types` from `vocabulary.yaml` `source_types` enum

## `intro-paths.csv` schema reference

Defined in `~/fundraising/.sys/schemas.yaml`. Every entry must reference a valid `investor_id` from `investors.csv`. `relationship_strength` uses the `vocabulary.yaml` enum (`strong | medium | weak | unknown`). Never invent introducers.

## GDPR & data privacy

Some investors are based in the EU. When collecting and storing investor data:

- Store only data that is publicly available or shared by the investor themselves
- Never scrape, never use bought lists, never store private contact info you weren't given
- Mark `geography` accurately — EU-based investors trigger a `gdpr_subject: yes` flag in notes
- For any EU-based investor you intend to email directly: the first contact must include a brief data-source disclosure ("found you via [public source], happy to remove you from my outreach list — reply with 'remove'") — this is enforced in `/preseed-outreach`'s message rules
- Never export EU investor records to third-party tools without confirming the tool's GDPR posture (HeyReach: confirm DPA in place before exporting EU rows)
- If unsure whether a contact path is GDPR-compliant, set `public_contact_path: unknown` and surface to user

## Outputs

| File | Role |
|---|---|
| `investors/investors.csv` | Scored investor source of truth |
| `investors/investors.md` | Generated readable view (do not edit directly) |
| `investors/intro-paths.csv` | Intro path source of truth |
| `investors/sources.md` | All source URLs used in this wave's research, dated |

## Rules

- Never invent investor facts, check sizes, posts, portfolio companies, or warm paths.
- Every investor-specific claim requires `source_url` + `source_date` + `source_type` + `confidence`.
- Never guess emails. `public_contact_path` is for genuinely public contact methods (firm contact form, public personal site, public LinkedIn). Email-pattern guesses are forbidden — `validate_investors_csv.py` rejects them.
- Mark unknown facts as `unknown` — never fill blanks with assumptions.
- Set `disqualified: yes` only when a specific gate is triggered, with the gate name in `disqualified_reason`.
- Lead candidate designation requires evidence in the row (cited lead deals from public sources). No self-described leads.
- Network-first before cold. Cold candidates with no warm path do not enter waves.
- For EU investors, follow the GDPR rules above before exporting or contacting.
- All outputs are drafts. The user is the only one who initiates contact. This skill never sends, queues, or schedules anything.
- Load `vocabulary.yaml` and `schemas.yaml` from `~/fundraising/.sys/`, never from this skill's directory.
