# Ask Progression — preseed-outreach

The staged ask is the structural backbone of every outreach sequence. Investors rarely commit before being walked up a ladder of small commitments. Skipping a stage usually triggers a pass, and pushing the ask too late wastes the wave window.

All ask_stage values are defined in `~/fundraising/.sys/vocabulary.yaml`. Never hardcode them in prose.

---

## The four-stage staircase

```
permission   →   call   →   pitch   →   follow_up
```

Each stage represents a real-world commitment from the investor. `validate_outreach.py` enforces correct progression — you cannot draft a `pitch` message without an `accepted_dm` or equivalent recorded `call` step in `outreach.csv`.

---

### Stage 1 — `permission`

**The micro-commitment**: "ok to send you something / hear more?"

**What's permitted**:
- LinkedIn connection note
- Cold email asking permission to share more
- LinkedIn InMail with permission framing
- A specific reference to the investor's public surface (post, podcast, portfolio company)
- A one-sentence frame for Agentis (buyer + problem)

**What's banned**:
- A full pitch
- A deck link
- A 15-minute call ask (that's stage 2)
- Multiple asks
- Investor compliments without a source

**What triggers progression to `call`**:
- Investor accepts LinkedIn connection — move to `accepted_dm` (ask_stage = `call`)
- Investor replies positively to permission email — move to `accepted_dm`
- Investor replies asking for materials — JUMP to `fast_forward` override (skip `call`)
- Investor replies with a pass — log `pass`, generate `pass_response` + `reapproach_note`

---

### Stage 2 — `call`

**The micro-commitment**: "15 minutes on a call?"

**What's permitted**:
- LinkedIn DM after connect
- Email follow-up after permission reply
- A 2–3 sentence frame on Agentis (buyer + problem + financial cost)
- Two suggested time windows or a Calendly link
- One specific signal cited from `investors.csv`

**What's banned**:
- A full pitch deck
- A long pitch body — save for stage 3
- Multiple asks ("happy to send the deck or jump on a call")

**What triggers progression to `pitch`**:
- Investor confirms a meeting time — log `intro_call_booked`, draft `meeting_confirmation`
- Investor asks for the deck before the call — JUMP to `fast_forward`
- Investor declines but says "keep me posted" — set status `nurture`, drafting moves to `warm_update` cadence
- Investor passes — log `pass`, generate `pass_response` + `reapproach_note`

---

### Stage 3 — `pitch`

**The micro-commitment**: "walk me through Agentis."

**What's permitted**:
- Deck link, data room link, or scheduled walkthrough call
- Cover note (≤120 words)
- One specific number worth their attention
- Soft next step ("happy to walk through, or poke at it on your own")

**What's banned**:
- Treating this as a fresh cold pitch — they already asked
- Long preambles repeating prior context
- Multiple asks
- Materials that aren't ready (no half-built decks)

**What triggers progression to `follow_up`**:
- Pitch meeting concludes — set status `intro_call_done` or `partner_meeting_done`, draft post-meeting follow-up
- Investor accesses data room — log `data_room_accessed`, set `data_room_accessed_date`
- Investor requests financials, customer references, or technical spec — log `material_interaction` in `touches.csv`, prepare requested artifact
- Investor passes — log `pass`, run pass protocol

---

### Stage 4 — `follow_up`

**The micro-commitment**: "what's next?"

**What's permitted**:
- 24-hour post-meeting email (≤150 words, drafted by `/preseed-prep` post-meeting mode)
- Specific material the investor asked for (linked)
- A proposed next step with a specific date
- A reflection of their stated interest or concern in their words

**What's banned**:
- Re-pitching content already covered in the meeting
- Vague "next steps" without dates
- Sending materials they didn't ask for

**What triggers progression**:
- Investor confirms next step — keep status, log touch, schedule next meeting prep
- Investor requests terms — set status `terms_sent`, generate term sheet (lead candidates only)
- Investor goes silent for >14 days post-meeting — `ghost_check.py` flags `ghosted`, draft `takeaway_email`
- Investor passes — run pass protocol

---

## Override 1 — `fast_forward`

**Trigger conditions** (all required):
1. Investor explicitly requested materials in writing — deck, data room, financials, memo, or one-pager
2. The exact request text is quoted in `outreach.csv` `source_signal` column
3. The request did not require any prior pitch from the founder

**Effect**:
- Skip the `call` stage entirely
- Generate `fast_forward_pitch` (cover note for the materials)
- Log a `material_sent` event in `touches.csv` with `material_interaction` set appropriately
- The cover note is ≤120 words and links to the materials

**Why**: when an investor asks for the deck unprompted, they have already self-qualified through the `permission` stage. Forcing them through a `call` ask wastes the window of interest and signals a rigid process. Skip the call. Send the deck. Follow up after they engage with materials.

**Banned**:
- Treating fast-forward as license to send a long re-pitch in the cover note
- Sending materials that are not yet ready
- Skipping fast-forward when the investor only generally said "interesting" — that is not a material request

---

## Override 2 — `takeaway`

**Trigger conditions** (all required):
1. Status is in {`intro_call_done`, `partner_meeting_done`, `data_room_accessed`, `diligence`}
2. No touch in `touches.csv` for >14 days
3. `last_meeting_date` is populated

**Effect**:
- Generate `takeaway_email` (≤80 words)
- Set status to `ghosted`, `ghost_flag_date` to today
- Wait 48 hours after takeaway is sent (user marks `takeaway_sent_date`)
- If reply received: revert status to prior post-meeting state, log touch
- If no reply 48 hours after takeaway: move to `pass` with `pass_reason: ghosted`, run normal pass protocol

**Why**: ghosting is the single most common pre-seed failure mode. Unmanaged, it leaves the pipeline cluttered with phantom "active" investors and starves momentum. The takeaway is structurally short, never desperate, and forces a hard yes/no that cleans the pipeline within 48 hours.

**Banned**:
- Sending a takeaway before 14 days of post-meeting silence
- Wording that softens the takeaway ("just wanted to check in") — that defeats the mechanic
- Sending two takeaways to the same investor in the same wave
- Triggering takeaway from `nurture` (use `warm_update` cadence instead) or pre-meeting statuses
