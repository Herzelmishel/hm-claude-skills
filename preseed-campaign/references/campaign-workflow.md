# Campaign Workflow

The five-mode controller governs the fundraising loop:

```
setup → wave → review → diagnose → close
        ↑       ↓
        └─── iterate ───┘
```

## First 7 Days (GETTING-STARTED.md template)

Generated at `setup` time and copied to `~/fundraising/GETTING-STARTED.md`.

### Day 1 — Foundation
- Run `/preseed-campaign setup`
- Run `/preseed-story` — produces round brief, one-pager, ICP, terms plan
- Drop 5+ writing samples into `voice/samples/`
- Run `/preseed-voice` — extracts voice fingerprint

### Day 2 — Network Mapping
- Run `/preseed-prospect lead-only` — first pass, only lead candidates
- Manually verify top 20 candidates in LinkedIn / Crunchbase
- Identify warm intro paths in `intro-paths.csv`

### Day 3 — Wave 1 Launch
- Run `/preseed-campaign wave` — locks in 10–15 investors
- Run `/preseed-outreach` for each Wave 1 investor
- Human-review every message
- Send manually (LinkedIn / email)

### Day 4–6 — Pipeline Setup + Intros
- Run `/preseed-pipeline update` after every touch
- Activate warm introducers from `intro-paths.csv`
- Run `/preseed-prep` before each scheduled call

### Day 7 — First Review
- Run `/preseed-campaign review`
- If wave has any stalled signal, run `/preseed-campaign diagnose`
- Decide: iterate Wave 1 or launch Wave 2

## Bottleneck Matrix

| Symptom | Threshold | Root cause | Fix |
|---|---|---|---|
| Low approval rate | <50% candidates pass disqualification | ICP too broad | Tighten investor ICP in `story/investor-icp.md` |
| Low intro_made rate | <30% of asked intros land | Network map weak | Add 5+ introducers; activate alumni |
| Low accept rate | <30% connections accepted | Profile / targeting / note | Audit LinkedIn profile; rewrite connection note |
| Low reply rate | <20% of first DMs replied | Generic message or wrong fit | Tighten ICP; rewrite first DM with proof |
| Low call rate | <40% of replies → calls | Story or ask | Sharpen one-liner; verify proof is dated |
| Low call-to-commit | <25% of intro calls → soft commits | Terms / traction / fit | Re-examine cap; verify proof; check fit |
| Many "not now" | >50% replies are "too early" | No urgency | Define sharper milestone |
| Low momentum_score | <30 for 14+ days | Wave dying | Pivot story or targeting before next wave |

## Stalled Wave Rule

A wave is **STALLED** when ALL of:
- `wave_started_date` is more than 14 days ago
- 0 `soft_commit` events in `touches.csv` since wave started
- 0 `partner_meeting_booked` events in `touches.csv` since wave started

When stalled:
- `/preseed-campaign wave` refuses to advance
- User must run `/preseed-campaign diagnose`
- User must implement at least one fix from the bottleneck matrix before new wave

## Time-to-Close Math

```
days_remaining = target_first_close_date - today
gap_remaining_usd = target_first_close_amount_usd - current_committed_usd
expected_committed_per_call = avg_check × call_to_commit_rate
calls_needed = gap_remaining_usd / expected_committed_per_call
required_actions_per_day = calls_needed / days_remaining
```

If `required_actions_per_day` exceeds capacity (>2/day for solo founder), the model surfaces a warning and recommends extending the close date or lowering the first-close target.

## Momentum Score (0–100)

```
recent_commits  = soft_commits in last 7 days × 40
recent_replies  = positive_replies in last 7 days × 30
recent_calls    = calls_booked in last 7 days × 30
momentum_score  = min(100, recent_commits + recent_replies + recent_calls)
```

## Founder Effort Tracking

Surfaced in weekly summary:

```
Per-investor:
  hours_spent = sum(estimated_minutes for all touches) / 60
  
Aggregate:
  total_hours = sum across all investors
  hours_per_pass = total_hours / count(status=pass)
  hours_per_commit = total_hours / count(status=soft_commit)
```

When `hours_per_pass > 4`, recommend cutting bait earlier.

## Simple Mode

When `simple_mode: true` in `campaign.yaml`:
- Skip detailed bottleneck matrix in weekly summary
- Surface only top 3 next actions (not 5)
- Skip founder-effort calculations
- Wave size reduced to 8 (from 12)

Useful for first-time founders to reduce overload during the first 30 days.
