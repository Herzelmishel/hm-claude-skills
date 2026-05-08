---
name: preseed-prep
description: Prepare for Agentis pre-seed investor calls and generate 24-hour follow-up drafts. Source-disciplined, lead-aware, voice-matched.
argument-hint: "[investor_id] [intro_call|partner_meeting|angel_chat|post-meeting]"
when-not-to-use:
  - Without round-brief.yaml and investors.csv
  - As a substitute for outreach — run /preseed-outreach first
  - For pipeline state changes — use /preseed-pipeline
outputs:
  prep/[investor-slug].md: pre-call brief
  prep/[investor-slug]-post-call.md: post-call notes template
  prep/[investor-slug]-followup.md: 24-hour follow-up email draft
---

# preseed-prep

Prepare for one investor meeting at a time. Generate the brief, the question bank, and the post-meeting follow-up. Cite every claim. Mark unknown facts as `unknown`. Being wrong in the meeting is worse than being underprepared.

## When to use

- The user has a scheduled call with a scored investor (`intro_call_booked`, `partner_meeting_booked`, or an angel chat)
- The user just finished a meeting and needs the 24-hour follow-up draft
- The user wants a refreshed prep brief before a follow-on conversation
- A lead candidate needs a term-discussion agenda (`lead_candidate = yes` in `investors.csv`)

## When NOT to use

- Without `round-brief.yaml` and `investors.csv` — the brief lacks anchors and the source-discipline rule cannot run
- As a substitute for outreach drafts — use `/preseed-outreach`
- For pipeline state changes (status, touches, commitments) — use `/preseed-pipeline`
- To research an investor from scratch — `/preseed-prospect` covers research and scoring

## Pre-checks

1. `~/fundraising/campaign.yaml` exists — if missing, stop and tell user to run `/preseed-campaign setup`
2. `~/fundraising/.sys/vocabulary.yaml` exists — load `statuses`, `roles`, `confidence`, `material_interactions`, `commitment_status`
3. `~/fundraising/story/round-brief.yaml` exists — if missing, refuse with a plain-language message
4. `~/fundraising/investors/investors.csv` contains the requested `investor_id` — if not, refuse
5. The investor row has at least one `source_url` — if not, the brief cannot be source-disciplined; refuse and route to `/preseed-prospect`
6. If `voice/voice-fingerprint.yaml` is missing, warn that the post-meeting follow-up will not be voice-matched

## Modes

The argument selects the mode. Each mode has different content focus and different commitment-ladder targets.

| Mode | Trigger | Output | Min next step (commitment ladder) |
|---|---|---|---|
| `intro_call` | First meeting with a micro-VC, fund partner, or unknown angel | `prep/[slug].md` | Second meeting OR a clear pass with intro asks |
| `partner_meeting` | Full-partner pitch, often diligence-stage | `prep/[slug].md` (incl. lead-candidate section if applicable) | Term sheet path OR diligence/allocation conversation |
| `angel_chat` | 1:1 with an operator-angel or commerce-founder-angel | `prep/[slug].md` (lighter than partner brief) | Soft interest minimum, often verbal commit |
| `post-meeting` | Just-finished meeting; user pastes notes | `prep/[slug]-post-call.md` + `prep/[slug]-followup.md` | 24-hour follow-up email draft, ≤150 words |

## Pre-Call Brief structure (`prep/[investor-slug].md`)

The brief is a single page, scannable. Nine sections, in order:

```markdown
## 1. Investor Profile
Thesis, check size range, notable deals, recent signals (every claim cited
with source_url + source_date from investors.csv).
Founder-friendliness signals: pro-rata history, board style, follow-on rate.
Mark unknown facts as `unknown` — never guess.

## 2. Why This Investor + Why Agentis Now
Specific match between their thesis and Agentis's current proof. One paragraph,
no boilerplate. The proof points must already exist in story/proof-ledger.md
and tie to dated artifacts.

## 3. What They Will Likely Ask
Top 5 questions they're most likely to ask, ordered by probability.
For each: a 2–3 sentence strong answer that does not over-claim.
Hardest expected question gets a longer answer with evidence.

## 4. Likely Objections + Responses
Top 3 objections + best prepared responses. Pull from story/objection-bank.md.
Each response is 2–3 sentences. No defensive language. Each acknowledges the
concern before answering.

## 5. What NOT to Volunteer
Information that would hurt before context is established. Examples:
- Founder background gaps the investor hasn't asked about
- Cap table / advisor structure not yet finalized
- Customer churn from earlier pilot
List 3–5 items, with the rule: do not lie if asked, do not volunteer.

## 6. Questions to Ask
3–5 questions demonstrating knowledge of their thesis and portfolio.
Each cites a specific portco or post (with source_url) so it doesn't read as
boilerplate.

## 7. Founder-Friendliness Test
One question to probe how this investor treats founders in tough situations
(e.g., "Tell me about a portco that went sideways and how you showed up").
Use the answer to decide whether to push for term discussion.

## 8. Opening Frame
One sentence to open the call and set the right tone. Tied to the meeting goal.
For partner meetings, anchor on a recent product or customer milestone.

## 9. Meeting Goal (explicit)
Minimum acceptable next step from this conversation, drawn from the commitment
ladder above. Stated as a sentence, not a phrase.

## 10. For Lead Candidates (only if lead_candidate = yes)
- Term discussion agenda: SAFE cap, MFN, pro-rata expectations, board/observer
- What a "yes" looks like from this investor: term sheet vs. email confirm
- Allocation conversation timing
- See references/lead-prep-rubric.md for the full lead playbook
```

See `references/prep-rubric.md` for what good looks like in each section, with Agentis-specific examples.

## Post-Meeting Follow-Up structure (`prep/[investor-slug]-followup.md`)

Generated when mode is `post-meeting`. Three parts, ≤150 words total. Sent within 24 hours of the call.

```markdown
1. 2-sentence recap of their stated interest or concern — in their words,
   not your spin. Quote where helpful.
2. The specific material they asked for, linked. If they didn't ask for
   anything, default to the one-pager + cap table.
3. Proposed next step with a specific date and a specific ask.
```

**Rules**:
- ≤150 words (counted before save)
- Voice-matched against `voice-fingerprint.yaml` if present
- No banned phrases from `~/fundraising/.sys/anti-voice.txt`
- Subject line ≤80 chars, references the meeting topic
- Ends with closer pattern from fingerprint

A `prep/[investor-slug]-post-call.md` template is also written so the user can drop their raw notes against the 9-section brief structure for traceability.

## Source Discipline

Every investor-specific claim must cite a `source_url` already present in `investors.csv`. The 6 sources of legitimate claims:

1. `linkedin_post` (with `source_date`)
2. `linkedin_profile` (current as of `source_date`)
3. `firm_website` (e.g., portfolio page, thesis page)
4. `crunchbase`, `twitter`, `newsletter`, `podcast`, `conference_talk`, `portfolio_company`
5. Investor's own published interviews, podcasts, posts
6. Public deal announcements citing the investor

If the user asks for a brief and the investor has no source_urls, refuse and route to `/preseed-prospect` to populate the row.

Unknown facts are marked `unknown`. Walking into a meeting with `check_size_range: unknown` is fine. Walking in with a guessed range is worse — it is the kind of thing investors test.

## Lead-Candidate Specific Section

When `lead_candidate = yes`, the brief MUST include a Term Discussion Agenda. See `references/lead-prep-rubric.md` for the full playbook. Summary:

- SAFE cap discussion timing (don't anchor on first call unless investor asks)
- Pro-rata expectations (lead candidates typically expect 1–2x pro-rata)
- MFN clause behavior
- Board / observer expectations (most pre-seed leads do not take a board seat — observer rights or none)
- Allocation conversation framework

What a "yes" looks like by lead-candidate type:
- Pre-seed fund: term sheet
- Solo GP / micro-VC: signed SAFE within 14 days of soft commit
- Operator-angel-leading-syndicate: verbal lead commit + AngelList rolling vehicle target

## Outputs

- `prep/[investor-slug].md` — pre-call brief, regenerated each time the mode is `intro_call`, `partner_meeting`, or `angel_chat`
- `prep/[investor-slug]-post-call.md` — post-call notes template, generated once per meeting
- `prep/[investor-slug]-followup.md` — 24-hour follow-up draft, generated when mode is `post-meeting`

## Rules

- **Cite every claim.** Unknown = `unknown`.
- **Lead candidates get the term-discussion agenda.** Non-leads do not.
- **24-hour rule** for the follow-up. Past 24 hours, the dynamic shifts and a different drafting strategy is needed (see `/preseed-pipeline` ghost protocol).
- **150-word cap** on the follow-up. Hard limit.
- **Meeting goal is explicit.** Every brief states the minimum acceptable next step.
- **Voice-matched output.** Load `voice-fingerprint.yaml`. Skip with warning if missing.
- **Workspace `.sys/` is the source of truth.** Vocabulary, schemas, anti-voice — all loaded from `~/fundraising/.sys/`, never from another skill's `references/` directory.

## GDPR / EU investor note

Briefs for EU/EEA/UK-based investors use only data already public on their professional surface. Do not enrich with private data. Cite public source URLs only.
