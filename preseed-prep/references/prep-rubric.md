# Prep Rubric — preseed-prep

Detailed rubric for each pre-call brief section. What "good" looks like, what "bad" looks like, and Agentis-specific examples.

The brief is one page, scannable. Each section is 3–8 lines. The rubric protects against three failure modes: vague claims, generic questions, and missed term discussion (for lead candidates).

---

## Commitment Ladder Mapping

The Meeting Goal section anchors on the commitment-ladder rung this conversation is supposed to reach. Below the line is failure; above the line is bonus.

| Meeting type | Minimum acceptable next step | Bonus |
|---|---|---|
| `angel_chat` (operator/commerce-founder-angel) | Soft interest stated verbally, with a reason to re-engage in 14 days | Soft commit + a cap range |
| `intro_call` (micro-VC, scout) | Second meeting scheduled, ideally with the fund partner | Term-sheet path opened |
| `partner_meeting` (full partner) | Diligence path opened: data room access, customer ref calls, or term-sheet timing question | Term sheet within 14 days |
| `post-meeting` follow-up | They reply with their stated next step OR clear pass | Materially-engaged reply (asks a question, makes an intro) |

Failure to reach the minimum next step is not a pass — it is a signal that the brief, the story, or the targeting needs work. Surface this to `/preseed-pipeline diagnose` for the next wave.

---

## Section 1 — Investor Profile

**Good**:
- Thesis stated in one specific sentence with a `source_url`
- Check size range as a numeric band, or `unknown`
- 2–3 named portfolio companies with sectors
- Recent signal (post, podcast, deal announcement) within 90 days, dated

**Bad**:
- "Invests broadly across software" (no thesis)
- "Has done many deals" (no specifics)
- Old signals (>180 days) treated as recent
- Any claim without a `source_url`

**Agentis example (good)**:
> Thesis: focuses on commerce infrastructure and operator-led tools serving DTC brands [source: firm-thesis-page, 2026-03-12]. Check size: $250K–$1M leads at pre-seed [source: portfolio-public-data, 2026-04-22]. Recent signal: published a Q1 letter on margin pressure in mid-market commerce, citing a portfolio company example [source: substack-post-url, 2026-04-08].

---

## Section 2 — Why This Investor + Why Agentis Now

**Good**:
- One sentence on the thesis match, citing the investor's own framing
- One Agentis proof point that is dated, real, and verifiable from `proof-ledger.md`
- One sentence on why this is the right wave (timing, milestone)

**Bad**:
- "We think you'd be a great fit" (no investor specificity)
- A claim that depends on an unshipped feature
- Any traction claim without a dated proof point

---

## Section 3 — Top 5 Likely Questions

**Good**:
- Questions sourced from the investor's recent posts, podcasts, or known portfolio patterns
- Strong answers each ≤100 words
- The hardest question gets a longer answer with evidence
- Includes at least one team / founder background question
- Includes at least one why-now question

**Bad**:
- Generic FAQ ("what's your moat?")
- Answers that over-claim
- No evidence in the answer

**Required questions for any pre-seed pitch**:
1. Why now? (technology shift, regulatory shift, customer behavior shift)
2. Why you? (founder-market fit)
3. What's the smallest version of this that wins?
4. Who's your first 10 customers?
5. What's the hardest thing about this?

**Agentis example — "Why now?" answer (good)**:
> Three things changed in the last 18 months: 1) margin compression hit a 5-year low across mid-market commerce as paid acquisition costs ballooned [source: meta-cpms-data], 2) brands now see profit, not GMV, as the metric finance asks about every Monday, 3) the cost of running real-time data pipelines on top of Shopify/NetSuite/Aftership dropped by 60% with the new wave of zero-ETL tools. We don't think Agentis was buildable in 2022.

---

## Section 4 — Top 3 Objections + Responses

**Good**:
- Pulled from `story/objection-bank.md` — no ad-hoc objections
- Each response acknowledges the concern in one sentence before answering
- Response avoids defensive tone
- One objection should be the one Herzel personally finds hardest

**Bad**:
- Generic objections ("isn't this just a dashboard?") without a tailored answer
- Defensive tone ("actually, that's not true")
- Skipping the hardest objection because it's uncomfortable

**Agentis example — "Why won't Shopify build this?" (good)**:
> Fair concern. Shopify's surface is one channel; the brands we work with sell across Shopify, Amazon, retail, and wholesale, and the profit leak shows up at the boundary between channels. Shopify ships horizontal merchant tools — they don't ship vertical-finance tools. Our wedge is the multi-channel margin layer. If Shopify ships a single-channel version, our customers still need us for the other 60% of revenue.

---

## Section 5 — What NOT to Volunteer

**Good**:
- 3–5 specific items with the rule "do not lie if asked, do not volunteer"
- Each item explains why volunteering hurts the conversation flow

**Bad**:
- Items that would actually require a lie if asked (those go in the founder honesty plan, not here)
- Vague items ("the cap table situation")

**Agentis examples (good)**:
- The 2024 pilot that churned at month 3 → don't volunteer; if asked, frame it as the wedge that drove the current ICP narrowing
- The unfinished SOC 2 path → don't volunteer in a first call; covered explicitly in `partner_meeting`
- The cap table line item for the early advisor → don't volunteer; explain only when terms come up

---

## Section 6 — Questions to Ask (3–5)

**Good**:
- Each question references a specific portco, post, or thesis from this investor — not from a generic playbook
- One question is about how they show up post-investment (founder-friendliness)
- One question probes their conviction-vs-process style

**Bad**:
- Generic ("how do you make decisions?")
- Questions answerable from a Google search of the firm
- More than 5 questions (signals nervousness)

**Agentis example questions (good)**:
1. "Your Q1 letter referenced [portco] hitting a margin floor — what's the one thing they did that surprised you the most?"
2. "When you led [recent deal], the round closed in 5 days. What signal made you move that fast?"
3. "You've written about board observer rights specifically — how do you typically structure that with first-time founders?"
4. "What does month 1 of a typical pre-seed investment look like for you?"

---

## Section 7 — Founder-Friendliness Test (one question)

**Good**:
- Open-ended, asks for a specific story, not an opinion
- Allows the investor to disqualify themselves if they treat founders poorly
- Gets asked late in the conversation, after rapport

**Bad**:
- "Are you founder-friendly?" (yes/no, useless)
- "How do you handle conflict?" (too abstract)

**Recommended question**:
> "Tell me about a time a portco hit a hard stretch — what did you do in the first 30 days?"

The answer reveals whether they show up, leave the founder alone, or pile on. If the answer is hand-wavy or pivots to a success story, lower the conviction on this investor.

---

## Section 8 — Opening Frame (one sentence)

**Good**:
- Anchors on a specific recent Agentis milestone
- Or anchors on a specific recent investor signal that triggered the meeting
- Sets the right pacing (calm, not breathless)

**Bad**:
- "So, do you want me to walk through the deck?"
- "Before we start, can I ask about your fund?"
- A canned elevator pitch

**Agentis example (good)**:
> "Quick context on where we are: shipped the multi-channel margin pull from Shopify + Amazon last month, three pilots active, [investor] reached out after the [signal] post — happy to start wherever's most useful for you."

---

## Section 9 — Meeting Goal

Stated as a sentence, drawn from the commitment ladder above. Not a phrase. Not a checklist.

**Good**:
> "Minimum: confirmation of a second meeting within 14 days with their fund partner, with a clear topic (deeper product walkthrough or customer references). Bonus: a verbal soft commit and a cap range."

**Bad**:
> "Get to next steps." (no specifics)
> "Close the round." (not a single-meeting goal)

The Meeting Goal is the rubric for whether the meeting succeeded — not whether the investor liked the founder.

---

## Section 10 — For Lead Candidates

Only included when `lead_candidate = yes` in `investors.csv`. See `references/lead-prep-rubric.md` for the full lead playbook.
