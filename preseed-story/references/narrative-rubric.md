# Narrative Rubric — pre-seed story quality rules

This is the rubric every artifact in `/preseed-story` is judged against. The nine Story Quality Gates in `SKILL.md` map to the rules below. The point is not to sound impressive — it is to give a busy investor a reason to spend the next 60 minutes on you instead of someone else.

---

## 1. The one-liner test (one breath)

A pre-seed investor reads a one-liner and decides whether to keep reading. If they have to re-read it, you've already lost.

**Rule:** ≤30 words, no nested clauses, says who it's for, what changes for them, and how. Read aloud — if you run out of breath, it's too long. If you can't picture the buyer at the end, it's too vague.

**Weak:**
> Agentis is an AI-native platform that leverages real-time data and machine learning to optimize unit economics for ecommerce companies across the entire customer lifecycle.

Why it's weak: "AI-native", "leverages", "entire customer lifecycle" — three abstractions in one sentence. Could be any startup. No buyer. No mechanism.

**Strong:**
> Agentis helps mid-market ecommerce brands protect gross margin in real time by detecting profit leaks across pricing, promotions, fulfillment, and returns before they compound.

Why it's strong: buyer (mid-market ecommerce brands), outcome (protect gross margin), how (real-time detection), where (four named loss surfaces), urgency (before they compound).

---

## 2. Buyer specificity

"Ecommerce brands" is not a buyer. It is a market segment three layers above a buyer.

**Rule:** the buyer description must contain at least three of: title, GMV band, vertical, geography, business model (DTC vs. wholesale vs. marketplace), team size, current tooling.

**Weak:**
> We sell to ecommerce brands.

**Acceptable:**
> Mid-market DTC brands, $25M–$200M GMV, with a Head of Ecommerce or COO as champion.

**Strong:**
> Mid-market DTC and DTC+wholesale brands doing $25M–$200M annual GMV in apparel, beauty, and home goods, where a Head of Ecommerce or VP of Operations owns gross margin and runs a Shopify Plus or BigCommerce stack with NetSuite or Brightpearl on the back end.

The strong version excludes more brands than it includes. That's the point — it lets the prospecting skill find them and lets the investor picture the next ten customers.

---

## 3. Problem with financial cost

"Inefficiency" is not a problem. "Margin erosion" is not a problem. "Brands struggle to" is not a problem. A problem is a number — usually a number the buyer is currently losing per month.

**Rule:** the problem statement names a dollar cost, a frequency (per month, per quarter, per order), and a quantified buyer reaction (they discount, they over-promo, they lose 4% on returns).

**Weak:**
> Ecommerce brands struggle with operational inefficiency that hurts profitability.

**Strong:**
> A $50M GMV apparel brand loses 3–7 points of gross margin per quarter to undetected leaks: returns drift, promo stacking errors, free shipping abuse, and SKU-level pricing rot. On a $50M base, that's $1.5M–$3.5M per year — invisible until the quarter closes.

The strong version is testable. An investor can ask another founder. Either you're right or you're wrong, but you're not vague.

---

## 4. Why now (not generic AI)

"AI is finally good enough" is not a why-now. Every founder says this. Every seed deck has said this for three years. It's noise.

**Rule:** "why now" must cite a specific, recent change in the buyer's world — a regulation, a cost shock, a platform change, a behavior shift — that didn't exist 18 months ago and that the buyer feels.

**Weak:**
> AI has finally reached a level where real-time profit optimization is possible at this price point.

**Strong (Agentis-specific candidate):**
> Three things broke at once for mid-market ecommerce: ad CAC up 40% post-iOS 14.5, return rates back to pre-COVID highs after the 2024 free-returns reversal, and a Shopify checkout-extensibility migration that exposed promo-stacking bugs nobody knew they had. Brands now know they're bleeding margin but don't have the in-house data team to find it.

The strong version is verifiable. Anyone can fact-check the iOS 14.5 number, the return-rate data, the Shopify migration. The weak version cannot be fact-checked because it's vapor.

---

## 5. Proof rules — real, dated, verifiable

A pre-seed founder has very little proof. That is fine. What is not fine is hiding the lack of proof behind soft phrases.

**Rule:** every proof point in `round-brief.md` lives in `proof-ledger.md` with: claim, date, source URL or document, strength (`strong | moderate | thin`), how to verify. If a claim cannot be verified, mark it `thin` and treat it as a hypothesis, not a proof.

**Banned phrases** (any of these in a brief = automatic gate failure):
- "significant traction"
- "early customer interest"
- "rapidly growing"
- "explosive demand"
- "loved by users"
- "best-in-class"
- "game-changing"

**Weak:**
> We're seeing significant early traction with several mid-market brands.

**Strong:**
> Three paid pilots signed in March 2026 ($2k/month each, 6-month commits) with apparel brands at $30M, $80M, and $120M GMV. Two more in legal review. Average pilot found $40k–$110k in annualized leak in the first 14 days. (Pilot agreements + leak reports in proof-ledger.md, dated 2026-03-04 through 2026-03-22.)

The strong version is small. That's fine. It is real, dated, and verifiable. An investor can ask one of the brands.

---

## 6. Ask tied to a milestone

"$1M to grow the business" is not an ask. It's a wish.

**Rule:** every dollar of the round must be tied to a milestone in `terms-plan.md`. Milestones must be specific (revenue numbers, hire counts, product launches) and dated. The next round (seed) story must be obvious from this milestone.

**Weak:**
> Raising $1M to expand the team and accelerate growth.

**Strong:**
> Raising $1.5M post-money SAFE at $12M cap to take Agentis from $24k MRR (12 customers) to $90k MRR (40 customers) over 14 months, by hiring two founding engineers and one part-time GTM, and by shipping the auto-remediation engine. That MRR unlocks a $4M–$6M seed at $25M+.

The strong version tells the investor exactly what they're buying: a path from now to seed. It also disqualifies investors who don't believe the path is possible — which is a feature, not a bug.

---

## 7. Valuation cap defensibility

A cap pulled from "what felt right" is not defensible. A cap pulled from comparables is.

**Rule:** the cap must be backed by at least two named comparable rounds (similar stage, similar revenue, similar team) and an explicit acknowledgment of where Agentis is stronger or weaker than each.

**Weak:**
> $15M cap. We feel this is fair given our progress.

**Strong:**
> $12M post-money cap. Comparables: [Brand A] raised pre-seed at $10M cap with no revenue but a stronger team pedigree (ex-Stripe founder); [Brand B] raised pre-seed at $14M cap at $15k MRR with a thinner moat. Agentis is at $24k MRR with three paid pilots — stronger proof than [B], thinner team brand than [A] — so $12M splits the difference and leaves room for a clean seed.

---

## 8. Risk-naming rules

The investor will find every risk in diligence. The only choice is whether they hear the framing from you first.

**Rule:** `round-brief.md` includes a Risks section with at least three risks across at least three categories (technical, market, founder, distribution, regulatory). Each risk has a current mitigation or acknowledgment that this is a real exposure.

**Banned framing:**
- Listing only weak risks ("we may need to hire more engineers")
- Hiding behind euphemism ("opportunities for improvement")
- Naming risks without mitigations

**Strong example:**
> Distribution risk: we don't yet know whether mid-market brands will buy from a founder-led motion or whether we need a channel partner (Shopify Plus partner network). Current mitigation: two of three paid pilots came through a Shopify Plus partner intro, suggesting partner-led GTM is plausible. We'll know in 90 days.
>
> Technical risk: real-time leak detection at high SKU counts (>50k) hasn't been pressure-tested. Current pilots are <10k SKUs. Mitigation: the architecture uses Clickhouse and is benchmarked to 500k SKUs offline; production proof at 50k+ is a Q3 milestone.
>
> Founder risk: solo technical founder until co-founder #2 starts full-time. Mitigation: Udi joins full-time June 2026; hire #1 (founding engineer) is the gate before scaling pilots.

---

## 9. ICP exclusion-density rule

An ICP that includes everyone is a wish list. A real ICP excludes more investors than it includes.

**Rule:** `investor-icp.md` has a hard exclusions section that is longer than the inclusion section. If you're not turning investors away, you don't have an ICP.

**Weak ICP:**
> We're targeting pre-seed investors in B2B SaaS who care about commerce.

(This excludes literally no one. Useless to the prospecting skill.)

**Strong ICP (Agentis sketch):**
>
> **Include:**
> - Operator angels who've built or scaled a $50M+ ecommerce brand
> - Commerce-focused micro-VCs ($10M–$50M funds) with at least three pre-seed-stage investments in the last 18 months
> - Pre-seed funds that lead or anchor and write $250k–$750k checks
>
> **Exclude:**
> - Any fund that hasn't priced a round in the last 12 months (no current process)
> - Any investor whose portfolio includes a direct competitor (Profitwell-for-ecom, Drivepoint, Glew, Triple Whale margin module)
> - Any fund whose minimum check is >$1M (we won't fit)
> - Any investor known to require board control at pre-seed
> - Any fund with no commerce or operations thesis posts in the last 18 months
> - Any investor who passed in the last 6 months on a story that hasn't materially changed
> - Any investor whose stated thesis is consumer-only or hardware-only
> - Any fund based outside the US, Israel, or UK that doesn't do USD SAFEs
>
> Inclusions: 3 lines. Exclusions: 8 lines. That's a real ICP.

---

## How to apply this rubric

1. Read each gate aloud against the live artifact
2. Score each gate `pass | fail | needs work`
3. If any gate fails, the brief does not ship to prospecting yet
4. The Fundability Diagnosis (see `fundability-rubric.md`) is built on top of these gates — it tells you which gate, if strengthened, has the highest leverage on the round.
