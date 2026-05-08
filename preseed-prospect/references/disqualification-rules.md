# Disqualification Rules

Eight gates. Hitting any one sets `disqualified: yes` and populates `disqualified_reason` with the gate name. Disqualified investors are excluded from wave selection by `/preseed-campaign wave`. They remain in `investors.csv` so future passes (e.g., a story refresh) can re-evaluate.

Every disqualification must be backed by a sourced URL. "I think they don't do pre-seed" is not a disqualification — it's a research gap.

---

## Gate 1 — Direct competitor portfolio conflict

**Definition:** the investor has a portfolio company that is a direct competitor to Agentis (Profitwell-for-ecom, Drivepoint, Glew, Triple Whale's margin module, Lifo, or any other named competitor in `round-brief.yaml`).

**How to check:**
1. Pull the investor's portfolio page (firm website) — check every commerce / SaaS / analytics company against the competitor list
2. Cross-reference with Crunchbase if the firm doesn't list portfolio publicly
3. Check announced investments in last 24 months specifically for the competitor list

**Edge cases:**
- A small angel check (<$10k) into a competitor still triggers this gate — angel checks signal personal conviction
- An "advisor" relationship without an investment usually does NOT trigger this gate (note in `notes` field, do not disqualify)
- A portfolio company that competes on a single feature but has a different ICP triggers `conflict_severity: adjacent` and the −10 penalty, not full disqualification — re-score, do not disqualify

**Set:** `disqualified: yes`, `disqualified_reason: direct_competitor_portfolio`, `conflict_severity: direct`

---

## Gate 2 — No pre-seed or angel evidence

**Definition:** no public evidence the investor has invested at pre-seed, friends-and-family, or angel stage in the last 18 months.

**What counts as evidence:**
- A pre-seed deal announcement naming this investor as participant or lead, dated within last 18 months
- Crunchbase round data showing pre-seed or seed-stage participation in last 18 months
- The investor's own post about a pre-seed investment they made
- A verified scout post on AngelList or similar

**What does NOT count:**
- "We invest at all stages" (without examples)
- LinkedIn bio that says "investor" without recent deal activity
- A 3-year-old pre-seed deal with no recent activity since

**Edge cases:**
- A new fund with first close <12 months ago and 1–2 announced deals — give the benefit of the doubt; rescore as `confidence: low` rather than disqualify
- A solo angel who did 1 angel deal 18+ months ago — disqualify. Pre-seed at our stage requires active deployment.

**Set:** `disqualified: yes`, `disqualified_reason: no_preseed_evidence`

---

## Gate 3 — Check size mismatch

**Definition:** the investor's typical or minimum check size does not fit Agentis's allocation bands ($10k–$100k for angels, $250k–$750k for lead reserve).

**How to determine:**
1. Read firm website's "what we invest" page
2. Compute typical check from last 5–10 deals (Crunchbase ranges)
3. Look for explicit minimums ("we don't write checks under $1M")

**Specific disqualifying patterns:**
- Min check >$1M (Agentis's max single-investor allocation is below this)
- Stated check range of $25k–$50k for a fund (not Agentis's allocation band but might be too small to matter — disqualify only if the wave is full of larger candidates)
- "We only do follow-ons" (not relevant at Agentis's pre-seed stage)

**Edge cases:**
- An investor whose typical check is $1.5M but who has done $250k–$500k checks in last 12 months — do NOT disqualify; mark `check_size_fit: edge` and note in `notes`
- A fund moving up-stage (last 3 deals all $1M+, prior ones smaller) — disqualify; momentum is up-stage

**Set:** `disqualified: yes`, `disqualified_reason: check_size_mismatch`

---

## Gate 4 — No relevant domain fit

**Definition:** the investor's stated thesis and portfolio show no relevance to Agentis's domain (ecommerce, commerce ops, vertical SaaS, ai-for-commerce, RevOps for ecom, ERP/back-office for commerce, retail tech, supply chain SaaS).

**How to check:**
1. Read the firm's thesis page
2. Tag the investor's last 10–15 portfolio investments by category
3. If 0 of last 15 investments fall in any relevant category, gate triggers

**Edge cases:**
- Generalist funds that have made *one* commerce investment in last 18 months — DO NOT disqualify; mark `thesis_match: generalist_with_commerce` and score 8–14 on Factor 1
- Consumer-only funds (DTC brands as their portcos, not B2B SaaS) — DO disqualify. Their LP narrative is consumer; B2B SaaS for commerce is a thesis mismatch.
- Pure infrastructure funds (databases, devtools) with no application-layer commerce investments — disqualify

**Set:** `disqualified: yes`, `disqualified_reason: no_domain_fit`

---

## Gate 5 — No public source for any claimed fit

**Definition:** the entire research entry for this investor relies on hearsay or a single weak source. No `firm_website`, no `crunchbase`, no recent post — just an introducer's verbal recommendation.

**Why this is a gate:** prospecting on hearsay alone wastes the warm path and the introducer's credibility.

**How to check:**
- Count `source_urls` for the row. If 0, gate triggers.
- If `source_urls` is non-empty but every URL is a single low-tier source (e.g., one Twitter post from 2 years ago), gate triggers.

**Edge cases:**
- An investor who has been verbally recommended by a current customer-advisor and where Herzel can verify with the introducer in <48h — note the gap, do NOT disqualify, set `confidence: unknown` and revisit after the verification call.

**Set:** `disqualified: yes`, `disqualified_reason: no_public_source`

---

## Gate 6 — Prior pass (without material story change)

**Definition:** this investor has previously passed on Agentis, AND the story has not materially changed since the pass.

**What counts as a "material story change":**
- A new ICP / wedge (e.g., shifted from generalist ecom to apparel-specific)
- A 3x+ change in MRR or pilot count
- A new co-founder of significant relevance
- A new lead investor or named angel on the cap table
- A successful product milestone tied to the prior pass reason ("they passed because returns module was vapor; we shipped it")

**What does NOT count:**
- "We've made progress generally"
- A new post on LinkedIn
- A small uptick in the same metric
- A team rebrand or website refresh
- More time elapsed without other change

**How to check:**
1. Read `pipeline.csv` for this investor — if `status: pass` and `pass_reason` is set, look at the date
2. Compare against `round-brief.yaml`'s last material change log
3. If the pass is <6 months old AND no material change → disqualify
4. If the pass is >6 months old → re-evaluate; usually do not auto-disqualify

**Edge cases:**
- An investor passed 4 months ago because "too early" with `reapproach_trigger: "$50k MRR"` — if Agentis is now at $50k MRR, this is a material change → DO NOT disqualify, generate re-approach via `/preseed-pipeline`
- An investor passed for "team risk" — co-founder joining full-time IS a material change

**Set (when disqualifying):** `disqualified: yes`, `disqualified_reason: prior_pass_no_material_change`

---

## Gate 7 — Strategic conflict

**Definition:** the investor has a position that conflicts strategically with Agentis even without a direct competitor portco.

**Examples:**
- They are also a strategic investor in a major prospective Agentis customer where information sharing would create conflict
- They sit on the board of a competing platform
- Their fund LP base includes a direct competitor's parent company (rare and hard to source — usually requires a tip-off from another founder)
- They publicly bet against the Agentis thesis (rare — would require a substantive public position)

**How to check:**
- Read partner LinkedIn for board roles
- Read public LP disclosures (rare; usually not available)
- Cross-reference firm investments with Agentis's customer pipeline

**Edge cases:**
- The investor is on the board of a company whose product overlaps tangentially but not directly — note in `notes`, do not disqualify
- The investor publicly disagreed with a *broad* thesis ("AI infra is overhyped") that is not specifically about Agentis's wedge — do not disqualify

**Set:** `disqualified: yes`, `disqualified_reason: strategic_conflict`

---

## Gate 8 — Investor currently inactive

**Definition:** no investment, post, podcast, or substantive content from this investor in the last 12 months.

**How to check:**
- Crunchbase: last investment date >12 months ago
- LinkedIn / Twitter: no original post in last 12 months (likes and shares don't count)
- Firm website: portfolio additions / news posts >12 months stale

**Why:** inactive investors waste warm intros. Even if they're sitting on dry powder, the friction of getting them to engage is much higher than active investors.

**Edge cases:**
- A new fund still raising (no deals yet but partner is publicly active) — DO NOT disqualify; mark `confidence: medium` and `notes: pre-deployment`
- An investor who took a sabbatical for a known reason and is now back — DO NOT disqualify if the return is publicly stated; treat their post-return activity as the relevant signal
- A deliberately quiet investor (some senior angels post very little) — if they have a recent investment in last 12 months, do not disqualify on quiet-LinkedIn alone

**Set:** `disqualified: yes`, `disqualified_reason: investor_inactive`

---

## Disqualification flow

For each candidate, evaluate gates in order:

1. Run gate 5 first (no public source) — fail-fast
2. Run gates 1, 2, 3, 4 in any order — these are the most common
3. Run gate 6 if the investor exists in `pipeline.csv`
4. Run gates 7, 8 last — these are rarer and require deeper research

If any gate triggers, populate:
- `disqualified: yes`
- `disqualified_reason: <gate_name>`
- Note any specific edge-case reasoning in `notes`
- Stop scoring; the row does not need a score

The validator (`validate_investors_csv.py`) will fail if `disqualified: yes` is set without a `disqualified_reason`.
