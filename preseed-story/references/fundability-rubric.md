# Fundability Rubric — diagnosing where the story actually breaks

The Fundability Diagnosis sits at the bottom of `round-brief.md`. It is internal-only — never copy any of it into the one-pager or any outreach. Its job is to tell you, before you spend hours pitching, where the leverage is. Strengthening the wrong gate burns time. Strengthening the right one moves the round.

This rubric explains how to fill in each of the six fields.

---

## Field 1 — Strongest investor reason to believe

The single most compelling thing about this round, viewed from the investor's seat. Not what you wish were strongest. What is actually strongest, today.

**How to find it:**
1. Read `proof-ledger.md`. Look for the proof point with the highest `strength` rating that is also non-obvious — something an investor would not assume.
2. Cross-check with `round-brief.md`'s team and why-now sections. Is there an unfair advantage hiding there?
3. Pick exactly one. Pre-seed investors don't buy three things — they buy one and forgive the rest.

**Common candidates at pre-seed:**
- Founder pedigree (specific prior outcome)
- A single dated proof point that makes the wedge obvious (e.g., a paid pilot with a recognizable brand)
- Privileged distribution (existing relationships that other founders cannot replicate)
- A wedge that is visibly small but visibly defensible

**Weak:** "We have a great team and growing traction."

**Strong:** "Three paid pilots in 90 days with $30M–$120M GMV apparel brands, all sourced through a Shopify Plus partner channel that competing solutions cannot easily replicate."

---

## Field 2 — Weakest investor reason to pass

The single biggest reason a thoughtful investor will say no. Not the easiest reason — the *real* reason. If you write something here you can't fix or address, you're being honest. If you write something soft, you're hiding.

**How to find it:**
1. Read the Risks section of `round-brief.md`. Which risk would an investor weight most heavily?
2. Read the rejected/exclusion section of `investor-icp.md` — what trait disqualifies you from the investor archetypes you'd otherwise want?
3. Imagine the partner-meeting memo. What's the partner who is skeptical going to point at?

**Common candidates at pre-seed:**
- Solo technical founder, no GTM co-founder
- ICP overlaps with a well-funded incumbent
- Why-now is real but small — looks like a feature, not a company
- No commerce or operator angels in current cap table — no proof of insider belief
- No charging revenue (pilots only)

**Weak:** "We need more product validation."

**Strong:** "Solo technical founder until June 2026; no commerce-operator on the cap table yet, which means investors with a pattern-match for ecom buys see a missing pillar."

---

## Field 3 — Proof gap

The specific evidence that, if it existed, would flip Field 2. Not a vague wish — a specific, definable artifact.

**How to find it:**
1. Take Field 2. Ask: what is the smallest, most concrete proof point that would defang it?
2. Sanity check: is the gap closable in <90 days? At pre-seed, gaps that take 9 months are not gaps — they are a different round.

**Examples (mapped to the Field 2 examples above):**
- Solo founder gap → close by getting Udi to sign as full-time co-founder by [date], announce to existing pipeline
- Incumbent overlap gap → close with a customer testimonial that explicitly says "I evaluated [incumbent] and chose Agentis because..."
- Feature-not-company gap → close with a second wedge revealing the platform vision (a logical adjacency the wedge unlocks)
- Cap-table gap → close by closing 1–2 named operator angels at any check size, before pitching VCs

---

## Field 4 — Fastest way to close that gap

The next 30–60 days, written as a verb. Not a strategy doc — a single-sentence action with a date.

**Test:** if a co-founder read this sentence, could they execute it tomorrow?

**Weak:** "Build out advisor network and customer references."

**Strong:** "By June 30: close 2 operator angel commits (Brand A founder, Brand B operator) at $25k each, with explicit permission to name in pitches. Use those names to unlock the apparel-vertical micro-VC tier in Wave 2."

---

## Field 5 — Best investor archetype for this stage

The investor type whose buying logic best matches your strengths. This drives the prospecting skill's wave 1 selection.

**Pre-seed archetypes (use the vocabulary from `.sys/vocabulary.yaml`):**

| Archetype | Best when... |
|---|---|
| `operator_angel` | Strongest signal is founder + small dated proof, weakest signal is institutional pattern-match |
| `commerce_founder_angel` | Buyer is commerce-specific, you can name-drop a brand they know |
| `ai_saas_angel` | Why-now hinges on AI infrastructure, technical depth is the moat |
| `micro_vc` | You can articulate a credible Series A path and have ≥1 dated proof point |
| `preseed_fund` | Story is sharp, willing to lead, proof is moderate but story is enterprise-grade |
| `scout` | Network access; usually anchors a wave but rarely sets terms |
| `strategic_angel` | A specific person whose presence on the cap table is itself a proof point |
| `customer_advisor_candidate` | Domain expert who can become a paid customer or advisor |

**Pick the archetype that:**
1. Buys against your Field 1 strength
2. Forgives or doesn't see your Field 2 weakness
3. You can reach via a warm path

---

## Field 6 — Worst investor archetype (do not target)

The archetype you would burn time pitching. Be ruthless. This is the disqualification feed for `/preseed-prospect`.

**How to find it:**
1. Whose buying logic specifically penalizes Field 2?
2. Whose process timeline is too long for your runway?
3. Whose minimum check exceeds your max single-investor allocation?
4. Whose thesis explicitly excludes your space?

**Examples:**
- "Tier-1 generalist seed funds" — process is 6+ weeks, minimum check $500k, partner-meeting bar is too high for $24k MRR
- "Consumer-only pre-seed funds" — Agentis is B2B SaaS sold to commerce buyers; consumer thesis fights you
- "Funds led by ex-founders of direct competitors" — conflict and proof asymmetry

---

## Worked example — Agentis (May 2026 sketch)

Use as a template, not as truth. Fill in actual values from your live brief.

```
Strongest investor reason to believe:
  Three paid pilots ($2k/mo, 6-month commits) signed in 90 days with $30M, $80M, $120M
  GMV apparel brands. Each pilot found $40k–$110k in annualized leak in the first
  14 days. Pilots came through a Shopify Plus partner channel — a privileged
  distribution motion that's hard for incumbents to copy.

Weakest investor reason to pass:
  Solo technical founder until Udi joins full-time in June 2026. Cap table has no
  commerce-operator angels yet. Investors who pattern-match commerce wins look for
  ex-DTC operators on the cap table; we don't have that signal.

Proof gap:
  No commerce-operator angel commitments. Without one or two named ex-DTC operators
  on the SAFE, the team-risk and ICP-validation arguments are thinner than they
  could be.

Fastest way to close that gap:
  By 2026-06-15: close 2 operator angel commits at $25k each from named DTC founders
  (Brand A, Brand B). Get explicit soft_circle_permission. Use those names to anchor
  Wave 2 (commerce-thesis micro-VCs).

Best investor archetype for this stage:
  commerce_founder_angel + commerce-thesis micro_vc. They forgive solo-founder risk
  if the wedge proof is brand-recognizable and the partner-channel motion is real.

Worst investor archetype (do not target):
  Tier-1 generalist seed funds (too late-stage in process, partner bar too high
  for current MRR), consumer-only pre-seed funds (thesis mismatch), and any fund
  whose stated thesis is "AI infra" with no commerce track record (will treat the
  wedge as a feature, not a category).
```

---

## How this feeds downstream skills

| Field | Downstream consumer |
|---|---|
| 1 (Strongest) | `/preseed-outreach` — the hook in connection notes and warm intro asks |
| 2 (Weakest) | `/preseed-prep` — pre-call objection prep |
| 3 (Proof gap) | `/preseed-campaign diagnose` — flags the bottleneck root cause |
| 4 (Fastest fix) | `/preseed-campaign` action item, dated, surfaced in weekly review |
| 5 (Best archetype) | `/preseed-prospect` — Wave 1 lead-candidate selection |
| 6 (Worst archetype) | `/preseed-prospect` — auto-disqualification |

When any of these change (a new pilot signs, an angel commits, a story refresh), update the diagnosis and propagate. The downstream skills are designed to read the live diagnosis on each run.
