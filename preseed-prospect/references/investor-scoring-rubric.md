# Investor Scoring Rubric

The 100-point model used by `score_investors.py` and the lead-candidate criteria. Every band has a verification rule — if the row in `investors.csv` cannot satisfy it via a sourced URL, the points cannot be claimed.

Total possible: 100 points before penalty. Conflict penalty subtracts up to 25. `score_10 = round(score_100 / 10)`.

---

## Factor 1 — Thesis / domain fit (30 pts)

Does the investor's stated thesis align with Agentis's wedge?

**Definition:** explicit, public alignment with one or more of: ecommerce SaaS, commerce ops, profit/margin tooling, AI-for-commerce, vertical SaaS in DTC, RevOps for ecom, ERP/back-office for commerce.

**How to verify:** firm website thesis page, recent posts (LinkedIn, firm blog, Substack, Twitter) within the last 18 months, or a portfolio company that operates in one of these spaces. URL must be in `source_urls`.

**Bands:**
- **25–30 pts** — direct thesis match cited from a public source ("we invest in commerce SaaS", "vertical AI for ecom", or a recent post specifically about margin/profit tooling) AND the investor has invested in at least one company in the same wedge in the last 18 months
- **18–24 pts** — adjacent thesis (B2B SaaS for SMB/mid-market, AI applications, vertical SaaS more broadly) with some commerce exposure in the portfolio
- **10–17 pts** — generalist thesis with at least one commerce or operations portfolio company
- **3–9 pts** — generalist thesis, no commerce signal but no exclusion either
- **0 pts** — no thesis information available; mark `confidence: low` and consider deferring to next wave

---

## Factor 2 — Stage fit (25 pts)

Does the investor invest at pre-seed and on terms compatible with a SAFE round?

**Definition:** evidence the investor leads, anchors, or participates at the pre-seed stage with a check size and process compatible with a $500K–$2M SAFE round.

**How to verify:** Crunchbase round history, firm website, recent announcements, or LinkedIn posts about pre-seed-stage deals.

**Bands:**
- **22–25 pts** — explicitly pre-seed-led ≥3 times in last 18 months on SAFEs or convertible notes; clear willingness to write the first check
- **15–21 pts** — pre-seed participant (not always lead) ≥3 times in last 18 months; will participate in SAFE rounds
- **8–14 pts** — historically seed-led but has done at least one pre-seed round in the last 12 months; needs a strong "why now" to come this early
- **3–7 pts** — primarily seed-stage; pre-seed only as a follow-on or strategic exception
- **0 pts** — no pre-seed evidence in the last 18 months. Note: "0 pts" combined with "no pre-seed evidence" usually triggers a disqualification gate (see `disqualification-rules.md`).

---

## Factor 3 — Check-size fit (15 pts)

Does the investor's typical check size fit Agentis's allocation?

**Definition:** Agentis allocations: lead reserve $250k–$750k, top angels $25k–$100k, smaller angels $10k–$25k. The investor's check needs to fit one of these bands.

**How to verify:** firm "what we invest" page, public deal announcements, founder testimonials, or AngelList/Crunchbase historical check ranges.

**Bands:**
- **13–15 pts** — typical check size sits squarely inside an Agentis allocation band, with public evidence
- **9–12 pts** — typical check size is inside a band but at the edge (e.g., "our checks are $750k–$2M" — only the bottom edge fits)
- **5–8 pts** — flexible check size with public examples both above and below Agentis's bands
- **2–4 pts** — typical check size is outside but could conceivably stretch
- **0 pts** — check size unknown OR check size completely outside Agentis's bands (e.g., min check $1M+)

---

## Factor 4 — Warm path evidence (15 pts)

Is there a credible warm intro path?

**Definition:** a real human introducer Herzel can ask, with a real relationship to the investor. The introducer must exist as an entry in `intro-paths.csv`.

**How to verify:** mutual LinkedIn connection (with `relationship_strength` recorded), shared portfolio company, alumni network, prior interaction, customer-advisor connection.

**Bands:**
- **13–15 pts** — `relationship_strength: strong` introducer who has previously introduced founders to this investor and is willing to do it again
- **9–12 pts** — `relationship_strength: medium` introducer with a plausible path (mutual connection, shared portco, recent meaningful interaction)
- **5–8 pts** — `relationship_strength: weak` (a 2nd-degree LinkedIn connection or alumni link without recent contact)
- **2–4 pts** — no warm path identified, but a credible cold path exists (recent post Herzel can engage with, conference attendance, public DM history)
- **0 pts** — no warm path, no credible cold path. This usually deprioritizes the investor; cold-only candidates do not enter waves until warm paths are exhausted.

---

## Factor 5 — Recent signal (10 pts)

Is the investor active and writing checks now?

**Definition:** recent (last 12 months) public activity showing the investor is currently deploying capital and engaged with their stated thesis. See `source-quality.md` for what counts as a "recent_signal" source and the 18-month staleness rule.

**How to verify:** an investment announced within the last 12 months OR a post/podcast/newsletter within the last 6 months that's substantive (not a generic re-share).

**Bands:**
- **8–10 pts** — investment announced in last 6 months AND substantive thesis content in last 6 months
- **5–7 pts** — at least one of: investment in last 12 months OR substantive content in last 6 months
- **2–4 pts** — active LinkedIn presence but no recent investment announcement
- **0 pts** — no public activity in last 12 months. Combined with no investment evidence, this usually triggers the "investor inactive" disqualification gate.

---

## Factor 6 — Geography fit (5 pts)

Does the investor invest in Agentis's geographic profile?

**Definition:** Agentis is incorporated in Delaware (US C-corp) with founders split between Israel and the US. Investors must be willing to invest in US C-corps via SAFE.

**How to verify:** firm website's geographic disclosures, portfolio geography mix, public commentary on cross-border investing.

**Bands:**
- **5 pts** — investor regularly invests in US C-corps with Israeli/US-split founders; explicit cross-border experience
- **3–4 pts** — investor primarily US-based but has cross-border deals in portfolio
- **1–2 pts** — investor primarily non-US but has done at least one US C-corp deal
- **0 pts** — investor only invests in their home jurisdiction (e.g., UK-only, EU-only, no USD SAFE history)

---

## Conflict penalty (up to −25 pts)

Subtracted from the raw `score_100`. Penalty severity depends on conflict directness.

| Severity | Penalty | Definition |
|---|---|---|
| `direct` | −25 | Has portfolio company directly competing with Agentis (Profitwell-for-ecom, Drivepoint, Glew, Triple Whale margin module, Lifo, others identified in `round-brief.yaml` competitor list) |
| `adjacent` | −10 | Has portfolio company in adjacent space (analytics for ecom, BI for ecom) where information sharing or competitive concerns would arise |
| `strategic` | −5 | Has a strategic position (e.g., is also a strategic investor in a major Agentis customer that could create a conflict) |
| `none` | 0 | No portfolio conflict |

A `direct` conflict usually triggers the disqualification gate as well — penalty is applied to the score and the row is also marked `disqualified: yes` so the wave selector skips it.

---

## Lead-Candidate Criteria (separate gate)

`lead_candidate: yes` requires *all five*:

1. **Public evidence of leading or anchoring at least one pre-seed round in the last 18 months.** Self-described leads do not count. Look for "led by [Fund]" in announcements, founder testimonials naming them as lead, or fund's own announcement of leading.
2. **Willing and able to set terms.** Usually means a fund GP, partner, or a serial angel known to write the first check. A scout cannot be a lead candidate (scouts don't set terms).
3. **Check size band overlaps Agentis's lead reserve ($250k–$750k).** A $1M+ minimum check is too large; a $50k–$100k typical check is too small.
4. **Reachable via a warm path with `relationship_strength` ≥ medium**, OR a credible cold path supported by a recent direct signal (e.g., they posted about commerce SaaS in the last 30 days and Herzel can engage substantively).
5. **No disqualification gate triggered.**

Wave 1 must have ≥60% of investors with `lead_candidate: yes`.

---

## Worked example — scoring a hypothetical investor

Investor: "Jane Doe, Partner at Commerce Ventures (a $25M micro-VC)"

| Factor | Notes | Pts |
|---|---|---|
| Thesis / domain fit | Firm thesis page explicitly: "vertical AI for commerce ops". Three commerce-ops portfolio cos in last 18 months. | 28 |
| Stage fit | Has led 4 pre-seed rounds in last 18 months on SAFEs (cited in 2 announcements). | 24 |
| Check-size fit | Public range: "$300k–$750k lead checks". Squarely in lead reserve. | 14 |
| Warm path | Mutual portco founder (`relationship_strength: strong`); has done warm intros for that founder before. | 14 |
| Recent signal | Investment announced 2 months ago; substantive Substack post 3 weeks ago. | 9 |
| Geography fit | US-based, has 2 Israeli-US deals in portfolio. | 5 |
| Conflict penalty | No conflict. | 0 |
| **score_100** | | **94** |
| **score_10** | | **9** |
| **lead_candidate** | All five gates met. | **yes** |

This is a Wave 1 lead-candidate slot.
