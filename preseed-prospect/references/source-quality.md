# Source Quality

Every investor-specific claim in `investors.csv` must cite a source. This file defines what counts, ranks sources by reliability, and rules out the things that look like sources but aren't.

A claim without a source is not a claim. It is an assumption. Pre-seed pitching on assumptions burns warm intros.

---

## Source hierarchy (highest to lowest)

### 1. Firm website + recent post (HIGHEST)

The investor's own firm website (thesis page, portfolio, partner bio) **plus** a dated post from the partner or firm in the last 6 months that confirms the same claim.

- **Why it's highest:** the firm has incentive to keep public statements accurate, and a recent post proves the thesis is still active (theses drift).
- **Use for:** thesis fit, stage fit, current portfolio companies, check-size statements, geography focus.
- **`source_type` (vocabulary.yaml):** `firm_website` + `linkedin_post` (or `newsletter`, `podcast`, etc.)

### 2. Firm website only (HIGH)

The firm's own website without a corroborating recent post.

- **Use for:** thesis fit (with a `medium` confidence flag), partner bios, portfolio (if dated).
- **Caveat:** firm websites can be stale. If the most recent portfolio addition is 18+ months old, knock confidence to `low`.
- **`source_type`:** `firm_website`

### 3. Crunchbase / PitchBook public data (MEDIUM)

Public deal data, fund composition, partner history.

- **Use for:** investment evidence (lead vs. participant on past rounds), check-size ranges (computed from past deals), recency of activity.
- **Caveat:** Crunchbase is sometimes wrong about lead/participant attribution. When stage fit hinges on "led", cross-reference with the company's own announcement.
- **`source_type`:** `crunchbase`

### 4. Investor's LinkedIn profile / Twitter / podcast appearance (MEDIUM-LOW)

Self-described claims by the investor in their own public channels.

- **Use for:** thesis posts, recent signal, what they're currently excited about.
- **Caveat:** self-described claims about check size and lead history are weaker than third-party confirmation. "I lead pre-seed rounds" on a profile bio is weaker than a portfolio company saying "led by [X]".
- **`source_type`:** `linkedin_profile`, `linkedin_post`, `twitter`, `podcast`

### 5. Third-party blog post / news article (LOW)

Coverage by tech press, blogs, or industry publications.

- **Use for:** corroboration, recent activity signals, investor reputation.
- **Caveat:** press releases get repeated; the same claim across 5 articles is not 5 sources. Trace back to the original.
- **`source_type`:** `newsletter`, `linkedin_post` (if the third party posted on LinkedIn)

### 6. Portfolio company founder (LOW)

A founder who took money from this investor describing the experience.

- **Use for:** founder-friendliness signals, board behavior, follow-on patterns, term-setting style.
- **Caveat:** depends entirely on the founder's relationship to Herzel. Strongest when the founder is part of the warm-path graph and Herzel can ask directly.
- **`source_type`:** `portfolio_company`

### 7. Social proof from another founder (UNKNOWN)

"I heard from [founder] that [investor] does pre-seed." Verbal, second-hand.

- **Use for:** a starting point for further research, never as the sole source.
- **Caveat:** mark `confidence: unknown`. Surface to user. The claim still needs a verifiable primary source before the row is finalized.
- **`source_type`:** treat as informal — does not satisfy `source_urls` requirement.

---

## Recency rules — when does a source go stale?

A claim's strength is bounded by the date of its source.

| Claim type | Acceptable source date |
|---|---|
| `thesis_match` | last 18 months — older theses have likely drifted |
| `stage_fit` | last 12 months for "currently leading pre-seed"; 18 months for "has done pre-seed" |
| `recent_signal` | **last 12 months** for `recent_signal: yes`; **last 6 months** for full points (8–10) on Factor 5 |
| `check_size_range` | last 18 months — funds change positions and check sizes between funds |
| `warm_path_evidence` | last 12 months — a connection that hasn't talked to the investor in 2 years is not warm |
| `portfolio_conflict` | last 24 months — portfolio holdings drift |

`source_dates` in `investors.csv` is a semicolon-separated list of dates aligned to `source_urls`. `validate_investors_csv.py` enforces same-length pairing.

---

## What cannot be sourced

Some investor facts cannot be ethically or legally derived from public sources. Mark these `unknown` and never guess.

### Investor email addresses

Personal email patterns guessed from a name and domain are NOT a valid source. Email-pattern guessing fails the validator. The only acceptable values for `public_contact_path`:

- A contact form URL on the firm's website
- An explicitly public personal site with a "contact" page
- A LinkedIn profile URL (LinkedIn DM is a public contact path)
- A public Twitter handle (DMs may be open)
- An explicitly public email the investor has shared (e.g., on their own site or a public talk)
- The literal string `unknown`

If you cannot find a public contact path, write `unknown`. Do not guess.

### Internal thesis documents

LP letters, internal investment committee memos, decks shared with portfolio companies under NDA — none of these can be cited.

### Salary, personal finances, fund AUM by LP

Publicly disclosed AUM is sourceable. Anything beyond that — LP composition, partner draws, carry splits — is not.

### Pass history with other founders

Whether [Investor] passed on [Other Founder] is private to that pair. You can ask the other founder directly; you cannot cite it as a public source.

### Thesis drift you inferred

"They used to invest in commerce, now they don't anymore" is an inference, not a fact. Either find a public statement that confirms a thesis change, or treat the older thesis as still active until a fresh investment proves otherwise.

---

## How sources flow into the CSV

For each investor, populate three aligned columns:

```
source_urls:  https://commerceventures.com/thesis;https://www.linkedin.com/posts/jane-doe_commerce-ai-2026
source_dates: 2026-04-12;2026-04-30
source_types: firm_website;linkedin_post
```

Rules enforced by `validate_investors_csv.py`:
- All three columns must be the same length when split on `;`
- `source_types` values must come from `vocabulary.yaml` `source_types` enum
- At least one source URL is required
- `source_dates` must be ISO format (YYYY-MM-DD) and not in the future

---

## Summary table

| Source | Reliability | Best for | Confidence |
|---|---|---|---|
| Firm website + recent post | Highest | Thesis, stage, check size | high |
| Firm website only | High | Thesis, partner bios | medium-high |
| Crunchbase | Medium | Investment evidence, recency | medium |
| Self-LinkedIn / Twitter | Medium-Low | Signal, what they care about | medium |
| Third-party blog | Low | Corroboration | low |
| Portfolio founder | Low (varies) | Founder-friendliness | varies |
| Other-founder hearsay | Unknown | Lead generation only | unknown |
