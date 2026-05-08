# Warm-List Rules — preseed-pipeline

The warm list is the highest-conversion group at close. Investors in `nurture` told the user some version of "too early, keep me posted" — they signaled real interest at the wrong time. Running into a hot moment with a strong nurture group is what creates round compression.

All status values reference `~/fundraising/.sys/vocabulary.yaml`.

---

## The 21 / 45 / 90 cadence

A `nurture` investor receives a `warm_update` on a fixed schedule from `last_warm_touch`:

| Days since `last_warm_touch` | Touch | Content focus |
|---|---|---|
| 21 | First nudge | Most recent shipped milestone — number, customer name, or product release |
| 45 | Second nudge | Product update or learning — what's changed in the thesis since last touch |
| 90 | Final nudge | Round status — "we're [X]% closed, soft circle includes [descriptor]" |

After 90 days with no positive signal, the investor moves to `do_not_contact` for this round. Re-evaluate at next round.

`warm_list.py` produces `pipeline/warm-list.md` with the action list, sorted by overdue (most-overdue first).

---

## Why 21 / 45 / 90?

- **21 days**: short enough to stay top-of-mind; long enough to have a real milestone to share. Less than 21 days reads as needy and burns the relationship.
- **45 days**: long enough that the thesis has had time to evolve; sets a different cadence from a "monthly investor update" so it doesn't fatigue the recipient.
- **90 days**: the round is either coming together by now or stuck. The 90-day touch compresses the conversation — either they engage with the round update or they self-select out.

Empirically: at pre-seed, conversion of nurture investors at the 90-day touch is non-trivial — investors who said "too early" 3 months ago have often seen new milestones and have re-evaluated.

---

## Content guidance per cadence band

### 21-day (first nudge): milestone-anchored

**Required**:
- Open with a concrete fact (`Hit $X in pilot revenue last week`, `Signed [logo]`)
- One specific number
- One specific learning
- ≤150 words
- Does NOT include a "soft circle" reference (too early)
- May include a soft re-engagement ask only if the milestone genuinely re-opens the conversation

**Banned**:
- "Just checking in"
- "Hope you're well"
- A repeat of the original pitch
- Any vague claim ("traction is strong")

### 45-day (second nudge): product / thesis update

**Required**:
- Open with what's CHANGED since last touch — not just another data point
- Reference the prior 21-day touch ("Last update I mentioned X; here's what's evolved")
- One product update OR one thesis learning
- One pointer to the next milestone with a date
- ≤150 words

**Banned**:
- A literal repeat of the 21-day update
- Anything that doesn't show forward motion

### 90-day (final nudge): round status

**Required**:
- Open with round status as a fact ("Round is [X]% closed")
- Soft-circle descriptor (NOT names — see soft-circle-rules.md)
- One reason this could be the right moment for them
- A specific ask: "Want me to send the updated deck?"
- ≤150 words

**Banned**:
- Pressure language ("only [X] days left")
- Vague urgency ("closing soon")
- Name-dropping without `soft_circle_permission = yes`

The 90-day touch is the inflection point. Either the investor engages or moves to `do_not_contact`.

---

## When `last_warm_touch` resets

The clock resets to today when:
- A `warm_update` is sent (logged as a touch in `touches.csv`)
- A meaningful 1:1 happens (intro call, partner meeting)
- The investor replies positively

The clock does NOT reset when:
- A pass-response or pure status-change touch is logged
- The investor reacts on LinkedIn (likes a post)
- A wave-blast email is sent (it isn't a 1:1 touch)

`update_pipeline.py` is responsible for setting `last_warm_touch` correctly when logging touches that qualify.

---

## Movement to `do_not_contact`

A `nurture` investor moves to `do_not_contact` for the round when ALL of the following are true:

1. The 90-day warm update was sent
2. No positive reply within 14 days of that touch
3. No other engagement signal (no LinkedIn reaction to recent posts, no Common Room signal)

This is final for the round, not permanent. Re-evaluate on the next round.

`update_pipeline.py` handles this transition automatically when the user runs `/preseed-pipeline weekly-review` and `warm_list.py` flags the investor as past 90 days with no positive signal. The user confirms before the transition happens.

---

## Why warm updates are NOT pitches

Warm updates are not "here's another sales pitch." They are calibrated proof — small, dated, real. The 150-word cap forces brevity. The "lead with a fact, not a feeling" rule strips out filler. The cadence respects the investor's time.

A nurture investor who gets pitched on every warm update will mute the user. A nurture investor who gets a tight, milestone-anchored update every 21–45 days stays in the round long enough for the moment to align.

---

## What `warm-list.md` looks like

```markdown
# Warm List — Generated YYYY-MM-DD

## Overdue (action this week)

### 90-day (final nudge — moves to do_not_contact if no reply)
- [Investor 1] (last warm touch: YYYY-MM-DD, days since: 95) — final round-status touch
- ...

### 45-day (second nudge — product/thesis update)
- [Investor 2] (last warm touch: YYYY-MM-DD, days since: 47) — frame: product update
- ...

### 21-day (first nudge — milestone)
- [Investor 3] (last warm touch: YYYY-MM-DD, days since: 23) — frame: most recent milestone
- ...

## Upcoming (this week)
- [Investor 4] (last warm touch: YYYY-MM-DD, due in 2 days at 21-day mark)
- ...

## Holding
- [Investor 5] (last warm touch: YYYY-MM-DD, next touch in 18 days)
- ...

## Notes
Total nurture investors: N
Overdue count: M
Recommend: action overdue 90-day touches first; they're the highest-conversion group at close.
```

`campaign_summary.py` includes the warm-list summary in `weekly-summary.md` so the user sees it alongside the rest of the diagnosis.
