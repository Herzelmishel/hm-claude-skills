# Message Rules — preseed-outreach

Detailed per-message-type specification. Every rule below is enforced by `validate_outreach.py` or `count_message_chars.py`. The voice fingerprint at `~/fundraising/voice/voice-fingerprint.yaml` is loaded for every draft and integrated into the structural and lexical checks.

All status / ask_stage values reference `~/fundraising/.sys/vocabulary.yaml`. Banned phrases reference `~/fundraising/.sys/anti-voice.txt` (defaults plus samples-derived bans).

---

## 1. `connection_note`

**Channel**: `linkedin_connection`
**ask_stage**: `permission`
**Limit**: ≤200 characters (LinkedIn hard cap; counted by `count_message_chars.py`)

**Required structure**:
1. One specific reference to the investor — pulled from a `source_url` already in `investors.csv`
2. One sentence on why Agentis touches their thesis (no pitch body, no metrics)
3. A soft permission ask — "ok if I share more?", "open to a quick note?"

**Banned content**:
- Any pitch ("we built", "our platform", "we help…")
- Any metric ("$X MRR", "Y% growth")
- Any link
- Any banned phrase from `.sys/anti-voice.txt` (default examples: "I hope this finds you well", "circling back", "pick your brain")
- Any compliment without a source ("love your portfolio", "huge fan")

**Voice constraint**:
- Sentence length ±3 words of `voice-fingerprint.yaml` `avg_sentence_length_words`
- Opener pattern matches one of `opener_patterns`, or close enough to score ≥0.7 in `score_voice_match.py`
- Contraction rate within ±0.15 of `contraction_rate`

---

## 2. `accepted_dm`

**Channel**: `linkedin_dm`
**ask_stage**: `call`
**Limit**: ≤120 words (soft target; reject above 150)

**Required structure**:
1. One-line thanks for connecting (no "I hope this finds you well")
2. The specific signal that justified the connect (citing the same `source_url` as the connection note)
3. A 2–3 sentence framing of what Agentis is — buyer + problem + financial cost
4. One ask: 15-min call, with two suggested time windows or a Calendly link

**Banned content**:
- A whole pitch (save it for `pitch` stage)
- Multiple asks
- Generic "would love to connect" filler

**Voice constraint**:
- Closer pattern from `closer_patterns`
- No anti-voice phrases

---

## 3. `followup_3_day`

**Channel**: `linkedin_dm` (or `email` if warm path)
**ask_stage**: `call`
**Limit**: ≤80 words

**Required structure**:
1. NEW information — a metric, a customer signal, a press mention, a product update
2. One sentence connecting it to the previous ask
3. Re-issue the call ask, dated

**Banned content**:
- "Just following up" (banned by default in `anti-voice.txt`)
- "Bumping this up" / "wanted to circle back" (banned)
- A repeat of the original message with no new value

**Voice constraint**:
- Lead with the new fact, not with an apology for following up
- Tone matches `voice-fingerprint.yaml` `register`

---

## 4. `followup_7_day`

**Channel**: same as `followup_3_day`
**ask_stage**: `call`
**Limit**: ≤60 words

**Required structure**:
1. Single sentence: "I'll stop here for now — let me know if timing changes."
2. One closing piece of value (a stat, a link to a recent piece) — optional
3. No third ask. This is the last touch in the wave.

**Banned content**:
- A third explicit ask
- "Just one more nudge"
- Anything desperate

**Voice constraint**:
- Closer pattern from `closer_patterns`

---

## 5. `warm_intro_ask`

**Channel**: `email` (to introducer, not to investor)
**ask_stage**: `permission` (the ask is to the introducer)
**Limit**: ≤100 words

**Required structure**:
1. Direct address to introducer with relationship context ("Saw you connected to X via Y")
2. The reason X fits Agentis (one sentence, cited)
3. Permission ask: "Open to forwarding the blurb below?"
4. Reference: the `forwardable_intro_blurb` is included below or attached

**Banned content**:
- A pitch to the introducer
- "Could you make an intro?" without giving them paste-ready text
- Any obligation language ("would mean a lot to me")

---

## 6. `forwardable_intro_blurb`

**Channel**: written for the introducer to paste into a new email or DM
**ask_stage**: `permission`
**Limit**: ≤120 words

**Required structure**:
1. Third-person reference to founder: "Herzel runs Agentis…"
2. One sentence on what Agentis does (the buyer + problem)
3. One specific proof point with date
4. The ask: "looking to chat with [investor type] who care about [thesis]"
5. No salutation, no signoff — the introducer adds those

**Banned content**:
- First-person ("I run Agentis…")
- Salutation ("Hi X,") — the introducer writes that
- Footer / signature

---

## 7. `warm_update`

**Channel**: `email` (or `linkedin_dm` if that was the prior channel)
**ask_stage**: not in the staircase — this is the `nurture` cadence message
**Limit**: ≤150 words (counted by `count_message_chars.py`)

**Required structure**:
1. Open with a concrete fact ("Hit $X in pilot revenue last week" / "Signed [logo]")
2. One specific learning from the last 30 days
3. One pointer to the next milestone with a date
4. Optional: one sentence ask if the milestone has changed their answer

**Banned content**:
- "Hope you're well" / "Hope this finds you well"
- A repeat of the original pitch
- Vague claims ("traction is strong", "going well")
- Any ask larger than 15 minutes of their time

**Voice constraint**:
- Opener pattern from `opener_patterns`
- Length matches Herzel's natural cadence (paragraph_avg_sentences from fingerprint)

---

### Nurture cadence — 21 / 45 / 90 days

A `nurture` investor (status=`nurture` in `vocabulary.yaml`) gets a `warm_update` on a fixed schedule from `last_warm_touch`:

| Days since `last_warm_touch` | Touch | Content focus |
|---|---|---|
| 21 | First nudge | Most recent shipped milestone — number, customer name, or product release |
| 45 | Second nudge | Product update or learning — what's changed in the thesis since last touch |
| 90 | Last nudge | Round status — "we're [X]% closed, soft circle includes [descriptor]" |

If the investor does not engage at the 90-day touch:
- Move status to `do_not_contact` (per `vocabulary.yaml`) for the remainder of this round
- Log final touch in `touches.csv` with notes
- Re-evaluate at next round

This cadence is computed by `warm_list.py` (in the `preseed-pipeline` skill) and feeds into the drafting trigger here.

---

## 8. `pass_response`

**Channel**: same as the channel the pass came in on
**ask_stage**: `follow_up` (logged as `pass_response` for clarity)
**Limit**: ≤80 words

**Required structure**:
1. One sentence acknowledgement — direct, not bitter ("Got it — appreciate the directness.")
2. One sentence reflecting back their `pass_reason` in their words (no spin, no rebuttal)
3. The ask: "Could you point me to 1–2 others who'd be a better fit for this stage / thesis?"

**Banned content**:
- A counter-pitch
- "Sorry to hear that"
- Any attempt to flip the pass — that goes in `reapproach_note` later

---

## 9. `reapproach_note`

**Channel**: based on prior channel
**ask_stage**: `permission` (resets the staircase)
**Limit**: ≤100 words

**Trigger**: the milestone in `pipeline.csv.reapproach_trigger` has been hit.

**Required structure**:
1. One-line reference to the prior pass and the specific `pass_reason`
2. The milestone — concrete, dated, verifiable
3. New ask: 15 min to re-share the picture

**Banned content**:
- A claim that "everything has changed"
- A claim that the pass reason has been fully solved unless a verifiable artifact proves it

---

## 10. `fast_forward_pitch`

**Channel**: `email` (typically — the deck/data room is the carrier)
**ask_stage**: `pitch`
**Limit**: ≤120 words

**Trigger**: investor explicitly asked for materials in writing. The exact request is quoted in `outreach.csv` `source_signal` column.

**Required structure**:
1. Single-sentence acknowledgement of their ask (citing their words)
2. Material delivered: deck link, data room link, one-pager link
3. One specific number from the materials worth their attention
4. Soft next step — "happy to walk through if helpful, or you can poke at it on your own"

**Banned content**:
- A fresh full pitch — they already asked, the deck does the work
- Long preambles
- Multiple asks

---

## 11. `takeaway_email`

**Channel**: `email` (or `linkedin_dm` if that was the meeting follow-up channel)
**ask_stage**: `takeaway`
**Limit**: ≤80 words (counted by `count_message_chars.py`)

**Trigger**: status post-meeting AND no touch in `touches.csv` >14 days. Auto-drafted by `ghost_check.py` (in `preseed-pipeline`); this skill writes the per-investor file when invoked manually.

**Required structure**:
1. One factual sentence: "Haven't heard back since [date of last meeting]."
2. One sentence pulling the allocation: "Pulling [their range] back to the open allocation."
3. One sentence forcing a yes/no: "If I'm reading this wrong, let me know in the next 48 hours and I'll hold."

**Banned content**:
- "Just checking in" (banned)
- "Hope you're well" (banned)
- Any apology for sending
- Any softening language that undermines the takeaway
- More than three sentences

**Voice constraint**:
- Tone matches `register` from fingerprint
- Closer pattern from `closer_patterns`

---

## 12. `meeting_confirmation`

**Channel**: `email`
**ask_stage**: `call` or `pitch` (depending on the meeting type)
**Limit**: ≤60 words

**Required structure**:
1. Confirm time + zone
2. Dial-in or location
3. One prep nudge — "I'll come ready to discuss [their stated focus]"

**Banned content**:
- A whole pre-pitch
- Calendar manipulation language ("flexible if anything changes")

---

## Voice fingerprint enforcement (applies to all 12)

1. Every draft is scored 0–1 by `score_voice_match.py` against the loaded fingerprint
2. Drafts below `voice_score_threshold` (default 0.7) get `needs_human_review = high` in `outreach.csv`
3. Any banned phrase from `.sys/anti-voice.txt` triggers a hard fail in `validate_outreach.py` — the message is rewritten before export
4. Sentence length, opener pattern, closer pattern, contraction rate, and em-dash rate are scored
5. `signature_phrases` from the fingerprint should appear naturally in `warm_update` and longer messages — never forced

---

## Source discipline (applies to all 12)

Every personalized hook (a reference to the investor's portfolio, post, podcast, or conference talk) must trace to a `source_url` already present in `investors.csv` for that investor. `validate_outreach.py` fails the message if the personalized hook cannot be matched to a source URL.

If the user wants to use a new signal, they must add it to `investors.csv` first via `/preseed-prospect` so the source is captured with `source_date` and `source_type`.
