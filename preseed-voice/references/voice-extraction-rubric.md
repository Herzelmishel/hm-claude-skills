# Voice Extraction Rubric

How `build_voice_fingerprint.py` turns raw writing samples into a
structured fingerprint that downstream skills enforce.

The fingerprint captures **how Herzel actually writes**, not how an LLM
defaults to writing. Pre-seed outreach is judged on conviction and
specificity. A message that reads as voice-matched gets read; a message
that reads as a template gets archived.

## What we extract

Three layers, each independently scorable:

| Layer | Captures | Used downstream by |
|---|---|---|
| Structural | Sentence length, paragraph cadence, opener/closer patterns, em-dash use, contraction rate | `score_voice_match.py`, message generation |
| Lexical | Register (casual/formal/technical), signature phrases, technical density | message generation, `validate_outreach.py` |
| Anti-voice | Banned defaults (AI tells), banned personal (never appears in samples) | `validate_outreach.py` rejection list |

## Structural extraction

### Sentence length

Tokenize on `[.!?]` followed by whitespace. Drop empty tokens. Count
words per sentence (whitespace-split, strip punctuation). Compute the
mean across all samples.

Why: pre-seed founders typically write 12–18 word sentences in their
working voice. AI defaults to 22–28. A messaging skill that targets the
wrong average produces drafts that sound borrowed.

### Opener patterns

For every sample, take the **first sentence**. Normalize: lowercase,
strip leading whitespace, replace runs of whitespace with single
spaces. Then extract the **first 1–4 word prefix** that ends at a
clear boundary (colon, comma, em-dash) — or, if no such boundary
exists in the first 6 words, take the first 3 words.

Examples:
- "Quick update: shipped the export endpoint." → opener `"Quick update:"`
- "Two things — one good, one bad." → opener `"Two things —"`
- "Here's where we are on Agentis." → opener `"Here's where we are"`

Count frequency. Top 3 most common become `opener_patterns`.

### Closer patterns

Take the **last sentence** of each sample. Same normalization. Capture
short signoffs (≤4 words) intact. Frequency-rank, take top 3. Sign-offs
like "— Herzel" or "More soon." are common.

### Contraction rate

Count tokens matching `r"\b\w+'(?:s|t|re|ve|ll|d|m)\b"` (e.g., it's,
won't, we're, I've, you'll, I'd, I'm). Divide by total verb-phrase
candidates (auxiliary + main verb pairs is too brittle to detect with
regex; we approximate as `total_word_count / 6` — average sentence
contains roughly one verb phrase per 6 words). Clamp to `[0, 1]`.

A high contraction rate (>0.5) classifies the writer as **conversational**.
A low rate (<0.15) classifies as **formal**.

### Paragraph cadence

Split on blank lines. For each paragraph, count sentences. Mean across
all paragraphs is `paragraph_avg_sentences`. Most working-founder
writing lands at 1.5–3.0; investor-update writing 2–4.

### Em-dash rate

Count em-dashes (`—`, U+2014) and double-hyphens (`--`) per 1000
characters of source. Output as a 0–1 normalized value:

```python
em_dash_rate = min(1.0, occurrences / (len(text) / 1000) / 5)
```

Anchor: 5 em-dashes per 1000 characters = saturated (1.0). Most writers
fall in the 0.0–0.4 range. Useful as a generation hint — "use em-dashes
sparingly" is meaningless without a target.

## Lexical extraction

### Register classification

Three buckets, picked by a heuristic score:

- **casual_direct**: contraction_rate > 0.4 AND avg_sentence_length < 16
  AND uses at least one of: "honestly", "look,", "fwiw", "tbh"
- **formal_warm**: contraction_rate 0.15–0.4, avg_sentence_length 14–22,
  uses "please" or "thanks" but not "I hope this finds you well"
- **technical_terse**: avg_sentence_length < 14 AND contains code-like
  tokens (regex, JSON snippet, command line, version numbers, file
  paths) at >0.5% density

Default fallback: `casual_direct` if contraction_rate > 0.3, else
`formal_warm`.

### Signature phrases

N-gram extraction (n = 3 to 5). Lowercase, strip punctuation. Count
occurrences across all samples. Keep n-grams that:
- Appear in ≥2 different samples (not a single-document quirk)
- Have count ≥3 across the corpus
- Are not stop-word-only (filter common phrases like "and the of")

Top 5 by count become `signature_phrases`. Examples Herzel might use:
"the real problem is", "what we're seeing", "to be clear", "here's the
thing".

### Technical density

Ratio of technical tokens (numbers, percentages, currency, code
fragments, units) to total tokens. Useful for outreach: a founder who
writes 5% technical density should not produce messages with 0%.

## Anti-voice extraction

Two layers:

### `banned_default` (seeded from `anti-voice-defaults.md`)

These are universal AI tells. Every fingerprint inherits them. They are
written to `~/fundraising/.sys/anti-voice.txt` at setup. The fingerprint
also embeds them so any subsequent re-extract can self-validate without
reaching into the skill directory.

### `banned_personal` (computed from samples)

Take the default banned list. For each phrase, check if the user's
samples contain the phrase (case-insensitive). If a phrase NEVER
appears in samples, it's "safely banned" — appending it to a generated
message would be off-voice with high confidence.

This is appended to `~/fundraising/.sys/anti-voice.txt` below the
`## samples` marker so the workspace anti-voice list grows over time as
more samples are added.

## Confidence handling

Sample count drives confidence:

| Samples | Confidence | Behavior |
|---|---|---|
| 0–2 | low (warning) | Write a `WARNING:` block at the top of `founder-voice.md`. Generate fingerprint with defaults filled in. |
| 3–4 | medium | Normal output. Note in `founder-voice.md` that more samples improve match. |
| 5+ | high | Full extraction. No warnings. |

The `voice_score_threshold` defaults to **0.7** at all confidence
levels. Higher threshold = more flagged messages, slower iteration but
higher fidelity. Lower in the workspace's voice-fingerprint.yaml only
after you've calibrated against ~10 generated messages.

## Example fingerprint output

After processing 7 LinkedIn posts + 3 founder updates, you might get:

```yaml
sample_count: 10
avg_sentence_length_words: 14.6
contraction_rate: 0.58
paragraph_avg_sentences: 2.1
opener_patterns:
  - "Quick update:"
  - "Two things:"
  - "Here's the thing"
closer_patterns:
  - "— Herzel"
  - "More soon."
  - "That's it."
register: casual_direct
signature_phrases:
  - "the real problem is"
  - "what we're seeing"
  - "to be clear"
em_dash_rate: 0.32
technical_density: 0.07
banned_default:
  - "I hope this email finds you well"
  - "I wanted to reach out"
  - "circling back"
  # ... (full list inherited from anti-voice-defaults)
banned_personal:
  - "synergy"
  - "ecosystem"
  - "world-class"
preferred_alternatives:
  "I wanted to reach out": "Quick one — "
  "circling back": "Picking this back up:"
  "Just following up": "Update on this:"
voice_score_threshold: 0.7
```

## What this fingerprint enables

Downstream:

1. `score_voice_match.py` — reads the fingerprint, scores any message
   0–1 across sentence length, opener match, banned phrases, em-dash
   rate. Used inline by `validate_outreach.py` and surfaced per-message
   in `outreach.csv` as `voice_score`.

2. Message generation in `/preseed-outreach` — the model is told the
   target avg sentence length, opener patterns, register, and the full
   banned-phrase list. The structural fingerprint is the most powerful
   constraint because LLM defaults regress toward longer, more formal
   sentences without it.

3. `validate_outreach.py` — hard-fails any message containing a phrase
   from `banned_default` ∪ `banned_personal`. Soft-flags messages where
   sentence length is >3 words off the fingerprint average.
