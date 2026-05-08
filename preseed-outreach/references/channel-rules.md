# Channel Rules — preseed-outreach

Each channel has a different surface, audience expectation, and platform constraint. This file is the source of truth for which channel-specific rules apply when drafting.

---

## LinkedIn connection note

**Surface**: the 200-character note attached to a connection request.

**Hard rules**:
- ≤200 characters — counted by `count_message_chars.py`. LinkedIn truncates at 200 on most desktop and mobile surfaces.
- ask_stage = `permission` only. Never `call`, never `pitch`.
- No links. LinkedIn often strips links from connection notes and the recipient sees a broken artifact.
- No pitch — no metrics, no claims, no "we help…".
- No deck. No attachment of any kind.
- Plain text only — no emoji unless it appears in `voice-fingerprint.yaml.signature_phrases`.

**Why**: LinkedIn explicitly limits this surface; the platform also penalizes accounts that send pitchy connection notes via lower acceptance rates and can rate-limit the account. Keeping the note narrow and permission-based is the only reliable way to reach the investor's inbox.

**Required content**:
- One specific reference to the investor sourced from `investors.csv`
- One soft permission ask

---

## LinkedIn DM (after connect)

**Surface**: a message in an existing 1:1 thread with someone you are already connected to.

**Hard rules**:
- ≤120 words soft target; reject above 150.
- ask_stage = `call`. The connection note already used `permission`; this thread is for the next ask.
- One link maximum (deck or Calendly), only if it adds value to the call ask.
- No "thanks for connecting!" filler — go straight to the signal.

**Why**: this is a different surface from the connection note. The recipient has already opted in. The norm here is shorter than email but longer than the connect note. Pitchy DMs trigger LinkedIn warnings and block subsequent invites.

**Required content**:
- The specific signal that justified the connect (the same `source_url` cited in the connection note)
- 2–3 sentences on Agentis fit
- One time-bound ask with two windows or a Calendly link

---

## LinkedIn InMail

**Surface**: a paid Sales Navigator InMail to someone you are not connected to. Different surface from the connection note.

**Hard rules**:
- ≤300 words.
- ask_stage = `permission` or `call`.
- Subject line is required and matters — keep it specific and short ("Profit leakage in mid-market commerce — open to a quick note?").
- One link maximum.

**Why**: InMails arrive in a separate inbox tab and can be archived without being read. The subject line carries 80% of the open. InMail allows more length than a connect note because the surface is closer to email.

**Required content**:
- Subject line ≤80 characters
- The signal that justified outreach
- One ask, dated

---

## When to use LinkedIn vs Email

| Path | First touch channel |
|---|---|
| Cold, no warm path, investor active on LinkedIn | LinkedIn connection note |
| Cold, no warm path, investor email is published on firm site | Email (cold) |
| Cold, no warm path, investor has Sales Nav presence but rarely accepts cold connects | LinkedIn InMail |
| Warm path (`warm_path_confidence` = high or medium) | Email (introducer-forwarded blurb) |
| Post-meeting | Email |
| Pass response | Same channel the pass arrived on |
| `nurture` warm update | Email — investor said keep me posted, email respects that |

**Heuristic**: prefer LinkedIn for first touch when the investor is actively posting on LinkedIn (recent post within 30 days). Prefer email when the investor's primary public surface is their firm site, podcast, or Twitter/X with a published email.

---

## Email (cold and warm)

**Surface**: standard email to a publicly listed address (investor firm site, public profile, conference bio).

**Hard rules**:
- Subject line ≤80 characters, specific. Banned subjects include "Quick question", "Touching base", "Hi from [name]".
- Body ≤180 words for cold, ≤220 words for post-meeting threads.
- One link maximum in cold; up to two in warm/post-meeting (deck + data room is fine).
- ask_stage matches the staircase — `permission` for cold, `call` for warm-path first touch, `pitch` for fast-forward, `follow_up` for post-meeting.
- Signature includes name, role, company, and one link (firm site or Agentis site). No long disclaimers.

**Why**: email is the most reliable surface for warm paths and post-meeting flow. A bad subject line kills the open; a bad first sentence kills the read. Warmth and source discipline matter more than length.

**Required content (cold)**:
- Subject naming the specific signal
- Open with the signal — no preamble
- 2–3 sentence frame
- One ask, dated

---

## Introducer email (`warm_intro_ask` + `forwardable_intro_blurb`)

**Surface**: email to the introducer, not the investor. The blurb is what the introducer pastes when they forward.

**Hard rules** for the `warm_intro_ask`:
- ≤100 words
- Direct, no obligation language
- Includes the `forwardable_intro_blurb` inline below the message — the introducer should be able to copy-paste it

**Hard rules** for the `forwardable_intro_blurb`:
- ≤120 words
- **Third-person reference to the founder** — "Herzel runs Agentis…", never "I run Agentis"
- No salutation ("Hi X,") — the introducer adds that
- No signoff ("Best, Herzel") — the introducer signs off
- One specific dated proof point
- One ask: "looking to chat with [type] who care about [thesis]"

**Why**: the introducer's job is to drop the blurb into a new thread or DM and add their own framing. Anything that requires the introducer to rewrite the blurb increases friction and lowers the chance of an actual intro happening. Third-person is the only voice that survives the forward.

---

## Channel decision short list

When in doubt, use the channel decision logic table in `SKILL.md`. The summary:

1. Warm path exists → email via introducer (`warm_intro_ask` + `forwardable_intro_blurb`)
2. Cold, LinkedIn-active investor → connect note → DM after accept
3. Cold, email-only-public investor → cold email
4. Material requested in writing → fast-forward email with deck link
5. Post-meeting → email follow-up within 24 hours
6. Ghosted → email takeaway (or LinkedIn DM if that was the meeting thread channel)
7. `nurture` 21/45/90 cadence → email warm update

**Never** do the following:
- Send a deck attached to a LinkedIn connection note (platform strips it; looks unprofessional)
- Cold-email an investor whose firm explicitly says "no unsolicited pitches" without a warm path
- Send the same message on multiple channels within 7 days
- Send to a personal Gmail/Yahoo address pulled from a leaked source — `public_contact_path` only
