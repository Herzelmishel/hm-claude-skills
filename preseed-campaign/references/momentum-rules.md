# Momentum Rules

## Velocity Check

A wave is **STALLED** when ALL of:
- Wave has been active for >14 days (`today - wave_started_date > 14`)
- 0 `soft_commit` events recorded in `touches.csv` since `wave_started_date`
- 0 `partner_meeting_booked` events recorded in `touches.csv` since `wave_started_date`

A wave is **HEALTHY** when ANY of:
- ≥1 soft commit in the last 7 days
- ≥3 partner meetings booked in the last 14 days
- `momentum_score` ≥ 50

A wave is **WARNING** between healthy and stalled.

## Stalled Wave Behavior

`/preseed-campaign wave` performs this check before advancing:

```
1. Read campaign.yaml.current_wave
2. Read touches.csv for events since wave_started_date
3. If wave is STALLED:
     STOP
     Output: "Current wave is STALLED. Run /preseed-campaign diagnose."
     Do not increment current_wave
4. If wave is WARNING:
     Output a warning, but allow advance
5. If wave is HEALTHY:
     Advance to next wave
```

## Time-to-Close Calculation

```python
# Pseudocode for momentum_check.py
days_remaining = (target_first_close_date - today).days
gap_remaining = target_first_close_amount_usd - sum(commitments.csv.signed_safe_amount)
avg_check = mean(commitments.csv.soft_commit_amount) if any commits else 50000
call_to_commit_rate = soft_commits_count / intro_calls_done_count
expected_per_call = avg_check * call_to_commit_rate
calls_needed = gap_remaining / expected_per_call if expected_per_call > 0 else None
required_per_day = calls_needed / days_remaining if days_remaining > 0 else None
```

## Momentum Score Formula

```python
def momentum_score(touches_csv, today):
    last_7 = touches in last 7 days
    commits = count(last_7 where status_after = soft_commit) * 40
    replies = count(last_7 where status_after starts_with replied_positive) * 30
    calls = count(last_7 where status_after = intro_call_booked) * 30
    return min(100, commits + replies + calls)
```

## Trend Detection

`momentum_check.py` writes both:
- `momentum_score`: today's value
- `momentum_score_prev`: from last review

Trend:
- `up`: today > prev + 10
- `flat`: |today - prev| <= 10
- `down`: today < prev - 10

Surface `down` as a warning in weekly summary even if absolute score is healthy.

## Founder-Effort Math

```python
estimated_minutes_by_type = {
  "outreach": 15,
  "warm_update": 6,
  "intro_request": 10,
  "meeting": 60,
  "material_sent": 5,
  "material_viewed": 0,        # passive event, no founder time
  "takeaway": 5,
  "intro_made": 5,
}
```

If a touch has explicit `estimated_minutes`, use that. Otherwise use the table.

## Required-Action Sanity Check

If `required_per_day > 2`:
- Solo founder cannot sustain >2 first calls per day
- Surface warning: "Time-to-close target requires X calls/day. Either extend `target_first_close_date` or reduce `target_first_close_amount_usd`."

If `required_per_day < 0.3`:
- Pace is too slow — first close at risk of slipping
- Surface warning: "On current pace, first close will land Y days late. Increase wave size or accelerate outreach."
