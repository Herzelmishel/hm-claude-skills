---
name: preseed-story
description: Build and validate Agentis pre-seed positioning before any investor contact. Produces round-brief.yaml + one-pager + proof ledger + objection bank + ICP + terms plan in one pass. Use when starting a raise, after a pivot, or when investor objections cluster around a specific weakness in the story.
argument-hint: "[pitch notes or company brief]"
---

# preseed-story

Build the single source of truth for Agentis's pre-seed narrative. Every downstream skill (`/preseed-prospect`, `/preseed-outreach`, `/preseed-prep`, `/preseed-pipeline`) refuses to run without `story/round-brief.yaml`. This skill is the gate.

## When to use

- First thing after `/preseed-campaign setup` — before any prospecting or outreach
- After a material story change: new ICP, new wedge, new proof point, new round size or cap
- When investor pass reasons cluster on a single weakness ("market unclear", "why now is generic", "ask doesn't tie to a milestone") — refresh the brief, don't rebuild
- Before refreshing the one-pager for a new wave

## When NOT to use

- After outreach has started — use `/preseed-story refresh` to amend, do not rebuild from scratch (downstream IDs and references depend on it)
- For investor-specific messaging — use `/preseed-outreach`
- For call prep — use `/preseed-prep`
- To change pipeline state — use `/preseed-pipeline`

## Pre-checks (stop and emit plain-language fix on failure)

1. `~/fundraising/campaign.yaml` exists. If missing, stop and tell user to run `/preseed-campaign setup`.
2. `~/fundraising/.sys/vocabulary.yaml` exists. If missing, run `/preseed-campaign setup` to seed it.
3. `~/fundraising/.sys/schemas.yaml` exists (this defines `round-brief.yaml` schema). If missing, run setup.
4. Load `vocabulary.yaml` from the workspace, never from this skill's directory. Workspace is the source of truth — see Shared Contract in the plan.

## Process

Build all seven artifacts in one pass. Order matters: each artifact feeds the next.

### 1. `story/round-brief.md` (human-readable)

Long-form narrative. Sections:
- One-liner (single breath, see Agentis candidate below)
- The buyer (specific persona — title, company stage, GMV band, geography)
- The problem (in dollars — quantified leak per month)
- Why now (non-generic; tied to a specific change in the buyer's world, not "AI is hot")
- What Agentis does (mechanism, not adjectives)
- Proof to date (every claim dated and sourced; pulls from `proof-ledger.md`)
- Wedge (the smallest valuable thing, the first 10 customers)
- Moat trajectory (how the wedge becomes a moat over 18 months)
- Team (Herzel + Udi + Igor; relevant prior expertise)
- Round (size, instrument, cap, MFN, allocation logic)
- Use of funds (tied to the milestone in `terms-plan.md`)
- Risks (named before the investor names them — tech, market, founder, distribution)
- What we want from investors (capital, intros, hires, customers)

### 2. `story/round-brief.yaml` (machine-readable)

Schema lives in `~/fundraising/.sys/schemas.yaml` — do not redefine it here. Required fields per the schema must all be populated. Use `unknown` for genuine unknowns; never guess. This file is loaded by every downstream skill.

### 3. `story/one-pager.md`

Investor-ready, single page. Structure (this is the contract — match it exactly):

1. Company name + one-liner
2. Problem (with cost in $)
3. Solution (what Agentis does — mechanism)
4. Traction (2–3 specific dated proof points)
5. Ask (round size, instrument, cap)
6. Use of funds (each line tied to a milestone)
7. Team (Herzel + co-founders, relevant expertise)
8. Contact (Herzel + booking link or email)

### 4. `story/proof-ledger.md`

Every proof point in the round brief lives here with: claim, date, source URL or document, strength (`strong | moderate | thin`), and how to verify. If a claim is in the brief but not the ledger, the brief fails the quality gate. See `references/narrative-rubric.md` for proof rules.

### 5. `story/objection-bank.md`

Top 10 objections an investor will raise, with the strongest current response for each. Group by:
- Market (TAM / wedge / timing)
- Founder (why this team)
- Product (why now buildable, why defensible)
- Distribution (CAC, channel, sales motion)
- Round (cap, dilution, follow-on logic)

Each objection has: question phrasing investors actually use, the strong response (1–3 sentences), and the proof point that backs it.

### 6. `story/investor-icp.md`

The ideal investor profile, plus an explicit exclusion list (which the prospecting skill consumes). The ICP must exclude more investors than it includes — an ICP that doesn't disqualify is not an ICP. See `references/narrative-rubric.md` for ICP exclusion-density rules.

Required sections:
- Investor archetype (operator angel / commerce-founder angel / micro-VC / pre-seed fund / strategic angel — pick one or two)
- Stage discipline (must lead/anchor at pre-seed, not seed-only)
- Check size band (min, target, max)
- Domain proof signals (what their portfolio or posts must show)
- Geography (where they invest, where they don't)
- Hard exclusions (direct competitor portfolio, no pre-seed evidence, fund stage mismatch, prior pass with no story change)

### 7. `story/terms-plan.md`

The defensible math behind the ask. Required fields:
- Round size (target, min viable, max)
- Instrument (SAFE — post-money assumed)
- Valuation cap with defensibility logic (comparable rounds, traction, team — not "we feel")
- MFN (yes/no, why)
- Pro-rata (yes/no, what side letter)
- Allocation logic (lead reserve, top angels reserve, advisor pool)
- Milestones the round buys (revenue, hires, product) — each tied to a use-of-funds line
- First-close target (date + amount, mirrors `campaign.yaml`)

## Story Quality Gates (automated — block progression on failure)

These nine gates are checked before any downstream skill is allowed to run. Each maps to a rubric rule in `references/narrative-rubric.md`. If a gate fails, surface the failure with the exact field and the rubric rule violated, then stop.

1. **One-liner is clear in one breath** — read aloud test, ≤30 words
2. **Buyer is specific** — not "ecommerce brands"; must specify role, GMV band, vertical
3. **Problem has a financial cost** — dollars per month, not "inefficiency"
4. **"Why now" is not generic AI timing** — must cite a specific change in the buyer's world (returns rate spike, ad cost crush, supply chain reshape)
5. **Proof is real, dated, verifiable** — no "significant traction"; every claim in `proof-ledger.md` with source + date
6. **Ask is tied to a specific milestone** — `terms-plan.md` use-of-funds maps line-by-line to milestones
7. **Valuation cap logic is defensible** — at least two named comparables in `terms-plan.md`
8. **Risks are named before the investor names them** — `round-brief.md` has a Risks section with ≥3 risks and current mitigations
9. **ICP excludes more investors than it includes** — `investor-icp.md` has a hard exclusions section longer than its inclusion list

## Fundability Diagnosis

After the seven artifacts are built, generate a Fundability Diagnosis section at the end of `round-brief.md`. Use the worked rubric in `references/fundability-rubric.md`. Required fields:

```
Strongest investor reason to believe:
Weakest investor reason to pass:
Proof gap:
Fastest way to close that gap:
Best investor archetype for this stage:
Worst investor archetype (do not target):
```

This diagnosis is the input to `/preseed-prospect` ICP filtering and `/preseed-campaign diagnose`.

## Agentis One-Liner Candidate

Use as the starting point. Iterate against the rubric — do not adopt verbatim without read-aloud test.

> Agentis helps mid-market ecommerce brands protect gross margin in real time by detecting profit leaks across pricing, promotions, fulfillment, and returns before they compound.

## Outputs

| File | Role |
|---|---|
| `story/round-brief.md` | Human-readable narrative + Fundability Diagnosis |
| `story/round-brief.yaml` | Machine-readable, loaded by all downstream skills |
| `story/one-pager.md` | Investor-ready single page |
| `story/proof-ledger.md` | Every proof point with source, date, strength |
| `story/objection-bank.md` | Investor objections + best responses |
| `story/investor-icp.md` | ICP + hard exclusions (consumed by `/preseed-prospect`) |
| `story/terms-plan.md` | Round size, SAFE cap, allocation, milestones |

## Rules

- Never invent proof points, customer names, revenue numbers, or comparable rounds. If a number is unknown, write `unknown` — do not guess.
- Every proof claim must appear in `proof-ledger.md` with a source URL and date. The brief and the ledger must reconcile.
- The one-pager pulls only from the round brief — never add new claims that aren't in the brief.
- Risks section must be honest. An investor who finds an unstated risk in diligence is much harder to recover than one who heard it framed by the founder.
- Refresh, don't rebuild. After the first build, prefer surgical edits — downstream skills hold references to specific brief fields.
- The Fundability Diagnosis is a planning tool, not investor-facing. Never copy it into the one-pager or any outreach.
- Load `vocabulary.yaml` from `~/fundraising/.sys/`, never from this skill directory.
