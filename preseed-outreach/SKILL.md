---
name: preseed-outreach
description: Draft human-reviewed pre-seed investor outreach for Agentis by channel, relationship status, and ask stage. All output is a draft — never sent automatically.
argument-hint: "[investor_id] or [warm-update] or [takeaway]"
when-not-to-use:
  - Before round-brief.yaml exists (run /preseed-story first)
  - Before investors.csv has scored investors (run /preseed-prospect first)
  - For call prep — use /preseed-prep
  - For pipeline state changes — use /preseed-pipeline
outputs:
  outreach/outreach.csv: all messages by investor, channel, ask stage
  outreach/[investor-slug].md: per-investor message set
  outreach/[investor-slug]-reapproach.md: generated on pass detection
  outreach/[investor-slug]-takeaway.md: generated when investor is flagged ghosted
  outreach/warm-update-template.md: 150-word milestone update template
  outreach/review-checklist.md: human review gate before any send
---

# preseed-outreach

Draft pre-seed investor outreach for Agentis. Voice-matched, source-cited, ask-staged. Every message is a draft. The user sends manually. The skill never claims to have sent anything.

## When to use

- The user wants outreach drafts for one or more scored investors
- A scheduled warm-update is due (status=`nurture`, `last_warm_touch` >21 days)
- A ghost-flagged investor needs a takeaway draft
- An investor passed and a re-approach note is needed
- The user wants the per-investor message set written to `outreach/[investor-slug].md`

## When NOT to use

- Before `round-brief.yaml` exists — run `/preseed-story`
- Before `investors.csv` is scored — run `/preseed-prospect`
- For call preparation — use `/preseed-prep`
- For changing pipeline state or logging touches — use `/preseed-pipeline`
- To send anything — this skill never sends

## Pre-checks (run before any drafting)

1. `~/fundraising/campaign.yaml` exists — if missing, stop and tell user to run `/preseed-campaign setup`
2. `~/fundraising/.sys/vocabulary.yaml` exists — load `ask_stages`, `statuses`, `material_interactions`, `relationship_strength`
3. `~/fundraising/.sys/anti-voice.txt` exists — load every line as a banned phrase (case-insensitive substring match)
4. `~/fundraising/story/round-brief.yaml` exists — if missing, stop and refuse with a plain-language message
5. `~/fundraising/voice/voice-fingerprint.yaml` exists — if missing, warn loudly that messages will not be voice-matched and ask the user to confirm before proceeding
6. The investor referenced exists in `~/fundraising/investors/investors.csv` — if not, refuse and tell the user to run `/preseed-prospect` for that investor
7. Every personalized hook the draft uses must trace back to a `source_url` already present in `investors.csv` for that investor — never invent a recent post, podcast, or portfolio event

## Channel Decision Logic

Use this table to choose what to draft first. Status values come from `vocabulary.yaml` — never hardcode.

| Condition | Generate first |
|---|---|
| `warm_path_confidence` = high or medium | `warm_intro_ask` + `forwardable_intro_blurb` |
| No warm path, not yet `connected` | `connection_note` (≤200 chars, ask_stage=`permission`) or InMail variant |
| `connected`, no `first_dm_sent` yet | `accepted_dm` (ask_stage=`call`) |
| `connected`, replied with material request ("send the deck", "share data room") | `fast_forward_pitch` — skip `call` stage, go straight to `pitch` |
| `first_dm_sent`, no reply, day 3 | `followup_3_day` |
| `followup_3_day` sent, no reply, day 7 | `followup_7_day` (last touch in wave) |
| Status = `pass` | `pass_response` (asks for 1–2 intros) + queue `reapproach_note` keyed to `reapproach_trigger` |
| Status = `nurture` AND `last_warm_touch` >21 days | `warm_update` (≤150 words, milestone-anchored) |
| Status post-meeting AND no touch in `touches.csv` for >14 days | `takeaway_email` (≤80 words) |
| `intro_call_booked` or `partner_meeting_booked` | `meeting_confirmation` |

## Ask Progression

Outreach follows a staged ask. Each stage has tight rules — see `references/ask-progression.md`.

```
permission   ← can I send you something?         (connection note or InMail intro)
    ↓
call         ← 15-minute call?                   (accepted DM, intro thread)
    ↓
pitch        ← can I walk you through Agentis?   (deck, data room invitation)
    ↓
follow_up    ← what's next?                      (after a meeting has occurred)

OVERRIDES (jump out of the staircase):
fast_forward ← investor explicitly asked for materials early — skip call, jump to pitch
takeaway     ← anti-ghost ("taking you off the list") after 14+ days post-meeting silence
```

`fast_forward` override conditions:
- Investor messaged in writing asking for the deck, data room, financials, or a memo
- The request must be quoted in `outreach.csv` `source_signal` column

`takeaway` override conditions:
- Status is in {`intro_call_done`, `partner_meeting_done`, `data_room_accessed`, `diligence`}
- No row in `touches.csv` for this investor in the last 14 days
- `last_meeting_date` is populated

## Message Set (12 message types)

Every active investor gets some subset of these, written into `outreach.csv` and `outreach/[investor-slug].md`:

1. **`connection_note`** — ≤200 chars, ask_stage=`permission`, no pitch
2. **`accepted_dm`** — ask_stage=`call`, soft ask for 15 min, leads with one specific signal from their public surface
3. **`followup_3_day`** — value-add not repeat; new metric, new customer signal, new press
4. **`followup_7_day`** — last touch in wave; explicit close or stop
5. **`warm_intro_ask`** — message to introducer requesting forward
6. **`forwardable_intro_blurb`** — third-person about Herzel/Agentis, written to be pasted by the introducer
7. **`warm_update`** — ≤150 words; one specific number + one specific learning; for nurture track
8. **`pass_response`** — short reply to a pass; asks for 1–2 intros to others who'd be a better fit
9. **`reapproach_note`** — generated when the `reapproach_trigger` milestone is hit
10. **`fast_forward_pitch`** — investor asked for materials; this is the cover note for the deck/data room
11. **`takeaway_email`** — ≤80 words, anti-ghost, forces yes/no, never desperate
12. **`meeting_confirmation`** — short confirmation reply with time, dial-in, and one prep nudge

## `outreach.csv` Schema

Source of truth for message state. See `~/fundraising/.sys/schemas.yaml` for the canonical column list.

```
investor_id, investor_name
channel                       ← linkedin_connection | linkedin_dm | linkedin_inmail | email | introducer_email
relationship_status
ask_stage                     ← from vocabulary.yaml (incl. fast_forward, takeaway)
connection_note
accepted_dm
followup_3_day
followup_7_day
warm_intro_ask
forwardable_intro_blurb
warm_update
pass_response
reapproach_note
fast_forward_pitch
takeaway_email
meeting_confirmation
source_signal                 ← the public artifact the message hooks into
source_url                    ← where source_signal came from
char_count_connection_note    ← computed by count_message_chars.py
voice_score                   ← 0–1 from score_voice_match.py
needs_human_review            ← yes | no | high
review_notes
```

## Message Rules

- **Connection note**: ≤200 characters (LinkedIn limit). No pitch. ask_stage=`permission` only.
- **Warm update**: ≤150 words. Opens with a concrete fact, never "Hope you're well". One number, one learning, optional ask.
- **Takeaway email**: ≤80 words. Direct. Forces yes/no. Never desperate. Never apologetic. Never "checking in".
- **Voice fingerprint enforcement**: every draft scored 0–1 against `voice-fingerprint.yaml`. Below `voice_score_threshold` (default 0.7) sets `needs_human_review = high`.
- **Anti-voice rejection**: any banned phrase from `.sys/anti-voice.txt` (case-insensitive substring match) fails the message in `validate_outreach.py`. The message must be rewritten before it can be exported.
- **Source discipline**: every personalized hook maps to a `source_url` already in `investors.csv`. No invented posts, podcasts, portfolio events, or quotes.
- **No fake familiarity**: no "I've been following your work for years" unless the user has confirmed it.
- **No "pick your brain"**: banned phrase by default in `anti-voice.txt`.
- **No unsupported claim about the investor**: stage focus, check size, thesis must trace to `source_url` + `source_date`.
- **Forwardable intro blurb**: third-person about Herzel ("Herzel runs Agentis…"), short, paste-ready, no salutation.

See `references/message-rules.md` for the complete per-message specification, including the 21/45/90-day nurture cadence.

## Channel Rules (LinkedIn vs InMail vs Email)

- **LinkedIn connection note**: ≤200 chars, no pitch, no link, ask_stage=`permission`
- **LinkedIn DM after connect**: longer than the note, opens with the source signal that justified the connect, ask_stage=`call`
- **LinkedIn InMail**: a different surface from the connect note; can be slightly longer, but still no deck attached, ask_stage=`permission` or `call`
- **Email**: used for warm-path follow-ups, post-meeting threads, and pass-responses. Subject line must be specific; never "Quick question" or "Touching base".
- **Introducer email** (`forwardable_intro_blurb`): written for the introducer to forward; third-person reference to founder; short enough to copy-paste

See `references/channel-rules.md` for full per-channel specification.

## Outputs

Always write to:
- `outreach/outreach.csv` — append/update the row for this investor; never overwrite other rows
- `outreach/[investor-slug].md` — readable per-investor message set (regenerated each time)

Generate on demand:
- `outreach/[investor-slug]-reapproach.md` — when status flips to `pass` (delegated to `reapproach_notes.py`)
- `outreach/[investor-slug]-takeaway.md` — when ghost detector flags the investor (delegated to `ghost_check.py`)
- `outreach/warm-update-template.md` — once at first warm-update generation, then reused
- `outreach/review-checklist.md` — once; human review gate before any wave send

## Rules

- **All messages are drafts.** Never claim to have sent. Never automate LinkedIn. Never bypass platform limits.
- Every message must be exported to `outreach.csv` and pass `validate_outreach.py` before it is considered ready for human review.
- Voice fingerprint is required input for every draft. If missing, halt and warn.
- Mark unknown investor facts as `unknown`. Do not guess.
- Workspace `.sys/` is the source of truth for vocabulary, schemas, and banned phrases. Never load from another skill's `references/` directory at runtime.
- Surface script errors using the JSON envelope: `{"error": "...", "field": "...", "fix": "..."}`. Translate to plain-language next steps for the user.

## GDPR notice (EU investors)

When an investor's `geography` field places them in the EU/EEA/UK:
- Use only data already public on their professional surface (LinkedIn profile, firm website, podcasts they appeared on)
- Never store private data in `investors.csv` beyond what is already publicly accessible
- Do not enrich with third-party private data sources
- The personalized hook must cite a public `source_url`
- The user is the data controller for any outbound message; this skill is a drafting tool only

## Scripts

| Script | When to run | Purpose |
|---|---|---|
| `scripts/count_message_chars.py` | After drafts are written | Validates connection note ≤200 chars, warm_update ≤150 words, takeaway_email ≤80 words. Writes `char_count_connection_note`. Exits 1 on any violation. |
| `scripts/validate_outreach.py` | Before declaring drafts ready | Anti-voice check, ask_stage progression check, voice_score populated, `needs_human_review` set correctly, every hook has a `source_url`. Returns first error in envelope format. |

Both scripts use stdlib only and the shared error envelope format defined in `~/fundraising/.sys/scripts.yaml`.
