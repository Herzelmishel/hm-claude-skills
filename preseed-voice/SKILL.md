---
name: preseed-voice
description: Extract Herzel's voice fingerprint from real writing samples. Run once after /preseed-story so all downstream outreach is voice-matched.
argument-hint: "[path to samples directory]"
---

# preseed-voice

Build the founder voice fingerprint that every downstream outreach skill
in the Agentis pre-seed suite reads. The fingerprint is the difference
between investor messages that sound like Herzel and investor messages
that sound like an LLM with a tie on.

## When to use

- After `/preseed-story` produces `story/round-brief.yaml`
- After Herzel has dropped 3+ writing samples into `voice/samples/`
- Any time samples are added (re-run to refresh the fingerprint)
- Before the first wave of outreach is drafted

## When NOT to use

- Before `round-brief.yaml` exists — story comes first, voice second
- For drafting messages — use `/preseed-outreach`, which loads the
  fingerprint automatically
- To score a single message — `score_voice_match.py` is callable
  directly by `/preseed-outreach`

## Pre-checks

Before doing anything:

1. Read `~/fundraising/campaign.yaml` — if missing, stop and tell user
   to run `/preseed-campaign setup`
2. Read `~/fundraising/.sys/vocabulary.yaml` — if missing, run setup
3. Read `~/fundraising/story/round-brief.yaml` — if missing, stop and
   tell user to run `/preseed-story`
4. List `~/fundraising/voice/samples/` — count `.txt` and `.md` files

If sample count is 0:
- Stop. Tell the user: "No samples found. Drop 5+ writing samples into
  `~/fundraising/voice/samples/` (LinkedIn posts, founder updates, real
  emails to advisors — your words only). Then re-run."

If sample count is 1–2:
- Warn. Run anyway. The `WARNING:` block in `founder-voice.md` will
  explain that fingerprint confidence is low.

## Inputs

Source files for fingerprint extraction:

| Location | Type | Notes |
|---|---|---|
| `~/fundraising/voice/samples/*.txt` | raw text | LinkedIn posts, tweets, DMs |
| `~/fundraising/voice/samples/*.md` | markdown | founder updates, blog drafts |
| `~/.claude/skills/preseed-voice/references/anti-voice-defaults.md` | banned defaults | seeded into the fingerprint |

Anonymize before dropping in: redact customer names, dollar figures
that are not yet public, anything you wouldn't want in a generated
draft.

## Workflow

1. Confirm pre-checks pass
2. Run `scripts/build_voice_fingerprint.py`
3. Read the script's JSON summary on stdout
4. Confirm three files were written:
   - `~/fundraising/voice/voice-fingerprint.yaml`
   - `~/fundraising/voice/founder-voice.md`
   - `~/fundraising/voice/voice-examples.md`
5. Confirm `~/fundraising/.sys/anti-voice.txt` was appended with
   samples-derived bans
6. Update `campaign.yaml`: set `voice_gate: passed` (skill responsibility)
7. Tell the user:
   - Sample count and confidence level
   - Top 3 opener patterns (so they recognize the extraction worked)
   - Detected register
   - Any banned phrases the script auto-added
   - The voice-score threshold currently in effect
8. Suggest next step: `/preseed-prospect lead-only` to generate the
   first investor list

## Outputs

```
~/fundraising/voice/voice-fingerprint.yaml   ← machine-readable, loaded by /preseed-outreach
~/fundraising/voice/founder-voice.md         ← human-readable do/don't guide
~/fundraising/voice/voice-examples.md        ← side-by-side AI default vs. founder voice
~/fundraising/.sys/anti-voice.txt            ← appended with samples-derived bans
```

## `voice-fingerprint.yaml` schema

```yaml
sample_count: 7                       # int, required
avg_sentence_length_words: 14.3       # float, required
contraction_rate: 0.58                # float 0–1
paragraph_avg_sentences: 2.1          # float
em_dash_rate: 0.32                    # float 0–1, normalized
register: casual_direct               # casual_direct | formal_warm | technical_terse
opener_patterns:                      # top 3 most common first-sentence patterns
  - "Quick update:"
  - "Two things:"
  - "Here's the thing"
closer_patterns:                      # top 3 most common last-sentence patterns
  - "— Herzel"
  - "More soon."
  - "That's it."
signature_phrases:                    # n-grams that recur across ≥2 samples
  - "the real problem is"
  - "what we're seeing"
banned_default:                       # universal AI tells (seeded)
  - "I hope this email finds you well"
  - "I wanted to reach out"
  - "circling back"
  - "Just following up"
  - "leveraging"
banned_personal:                      # phrases that NEVER appear in samples
  - "synergy"
  - "ecosystem"
  - "world-class"
preferred_alternatives:               # AI default → Herzel-equivalent
  "I wanted to reach out": "Quick one — "
  "circling back": "Picking this back up:"
  "Just following up": "Update on this:"
voice_score_threshold: 0.7            # below this = needs_human_review = high
confidence: high                      # high | medium | low (warns at low)
```

## Enforcement (across all outreach)

`/preseed-outreach` always loads `voice-fingerprint.yaml` before
generating messages, and:

1. **Sentence length tolerance ±3 words.** Generated messages whose
   average sentence length deviates by more than 3 words from the
   fingerprint average are penalized in the voice score.
2. **Opener match preferred.** Generation tries to use one of the
   top-3 opener patterns. If it can't, it accepts the penalty.
3. **Banned-phrase rejection.** Any phrase from `banned_default` ∪
   `banned_personal` causes hard rejection in `validate_outreach.py`.
4. **Voice score per message.** `score_voice_match.py` runs against
   every generated draft. Messages below `voice_score_threshold` get
   `needs_human_review = high` in `outreach.csv`.

`validate_outreach.py` runs the anti-voice check at message-creation
time — no banned phrase ever lands in `outreach.csv` unedited.

## warm_update + followup_3_day rules

These two message types are the most common voice-fail modes — both
default to the most generic AI cadence. Stricter rules apply.

### warm_update (150 words, milestone-anchored)

- **Opens with a concrete fact** — never "Hope you're well", never "It's
  been a while". A real number, a real customer, a real shipped thing.
  Examples: "Hit $40k MRR last week.", "Closed our second LOI yesterday."
- **One specific number, one specific learning.** No more, no less. A
  warm update with three milestones reads as a press release; one with
  zero numbers reads as small talk.
- **Optional ask, dated.** "Worth a 20-minute call next Wed/Thu?" is the
  shape — never "Would love your thoughts!"
- **Closer matches Herzel's actual signature.** Pull from
  `closer_patterns`. If none match, default to `— Herzel`.
- **Length matches the fingerprint cadence.** Target word count is
  `paragraph_avg_sentences × avg_sentence_length_words × 4` (≈4
  paragraphs). Hard cap 150 words.

### followup_3_day

- **Never starts with "Just following up".** Banned. Rejected by
  `validate_outreach.py` automatically.
- **Leads with new information.** A metric, a customer signal, a press
  mention, a product release. If there's no new information, the right
  answer is to wait, not send.
- **Tone matches Herzel's email tone**, not LinkedIn tone. Check
  `register` — most founders have a slightly more formal email register.
- **One ask, dated.** Same shape as warm_update.

## Re-running

Re-run `/preseed-voice` whenever:
- New samples are added to `voice/samples/`
- Outreach drafts are consistently scoring <0.7 (fingerprint may be
  drifting from current voice)
- Herzel notices messages reading off-voice in production

The fingerprint is overwritten on re-run. If you want history, copy the
existing `voice-fingerprint.yaml` to `voice-fingerprint-vN.yaml` first.

## Rules

- Never invent samples — only extract from real files in
  `voice/samples/`
- Never claim a fingerprint is high-confidence with <5 samples
- Never overwrite `~/fundraising/.sys/anti-voice.txt` — append below the
  `## samples` marker, preserving defaults
- Surface script errors via the plain-language envelope, not raw
  tracebacks
- The skill never sends or publishes anything — voice extraction only
