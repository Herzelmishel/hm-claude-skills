---
name: preseed-campaign
description: Run the Agentis pre-seed fundraising campaign. Setup, wave planning, diagnosis, momentum tracking, and first-close.
disable-model-invocation: true
argument-hint: "[setup|wave|review|diagnose|close]"
---

# preseed-campaign

Controller for the Agentis pre-seed fundraising operating system. Orchestrates the seven-skill suite. Does not draft messages, narrative, or research — delegates that to leaf skills. Owns sequencing, gates, and state.

## When to use

- `/preseed-campaign setup` — first run; creates `~/fundraising/` and `.sys/` config
- `/preseed-campaign wave` — select or advance an investor wave
- `/preseed-campaign review` — weekly status check + warm-list + bottlenecks
- `/preseed-campaign diagnose` — deep bottleneck analysis (run before launching new wave when stalled)
- `/preseed-campaign close` — first-close status, soft-circle map, term-sheet aging

## When NOT to use

- Before `/preseed-story` has produced `story/round-brief.yaml` — stop and tell the user
- For drafting messages — use `/preseed-outreach`
- For call prep — use `/preseed-prep`
- For investor research — use `/preseed-prospect`

## Pre-checks (every mode)

1. Read `~/fundraising/campaign.yaml` — if missing, only `setup` is allowed; everything else stops
2. Read `~/fundraising/.sys/vocabulary.yaml` — if missing, run setup
3. For `wave|review|diagnose|close`: confirm `story/round-brief.yaml` exists — if missing, tell user to run `/preseed-story`
4. Surface all script errors using the plain-language error envelope: `{"error": "...", "field": "...", "fix": "..."}`

## Mode: setup

**Purpose**: Initialize the campaign workspace and seed the `.sys/` config.

**Steps**:

1. Create `~/fundraising/` directory tree:
   ```
   campaign.yaml, README.md, GETTING-STARTED.md
   .sys/vocabulary.yaml, .sys/schemas.yaml, .sys/scripts.yaml, .sys/anti-voice.txt
   voice/samples/
   story/, investors/, outreach/, prep/, pipeline/
   ```
2. Copy seed templates from `~/.claude/skills/preseed-campaign/references/` into `~/fundraising/.sys/`:
   - `vocabulary.md` → `.sys/vocabulary.yaml` (extract YAML block)
   - `schemas.md` → `.sys/schemas.yaml`
   - `scripts.md` → `.sys/scripts.yaml`
3. Copy `~/.claude/skills/preseed-voice/references/anti-voice-defaults.md` → `.sys/anti-voice.txt` (extract list)
4. Run `validate_round_brief.py` if `story/round-brief.yaml` exists; otherwise note: "Story not yet built. Run `/preseed-story` next."
5. Write initial `campaign.yaml`:
   ```yaml
   version: 1
   company: Agentis
   stage: pre-seed
   target_raise_usd: 1000000        # placeholder; updated from round-brief.yaml
   instrument: SAFE
   target_first_close_amount_usd: 500000
   target_first_close_date: null    # set during /preseed-campaign wave
   current_wave: 0
   wave_size_target: 12
   lead_candidate_pct: 0.60
   campaign_status: setup_complete
   simple_mode: false               # set true for reduced output / lighter operations
   snapshot_on_change: false        # if true, copy round-brief.yaml to round-brief-vN.yaml on edit
   story_gate: pending
   voice_gate: pending
   last_review_date: null
   next_review_date: null
   wave_started_date: null
   momentum_score: null
   ```
6. Write `GETTING-STARTED.md` (the 7-day onboarding sequence — see `references/campaign-workflow.md`)
7. Tell user the next step: "Run `/preseed-story` to build the round brief, then `/preseed-voice` to capture your writing voice."

## Mode: wave

**Purpose**: Select and activate the next investor wave.

**Steps**:

1. Confirm `story_gate: passed` and `voice_gate: passed` in `campaign.yaml`
2. Read `investors/investors.csv` — if missing, tell user to run `/preseed-prospect`
3. Run `validate_investors_csv.py` — surface errors with plain-language fixes
4. Run `momentum_check.py` — if previous wave is `STALLED`, refuse to advance and tell user to run `diagnose` first
5. Filter investors: `disqualified = false`, not in any prior wave
6. Sort by `score_10` desc, with `lead_candidate = yes` first
7. Apply wave rules:
   - Wave size: 10–15 (use `wave_size_target` from campaign.yaml)
   - ≥60% of wave must be `lead_candidate = yes` (`lead_candidate_pct` from campaign.yaml)
8. Update `campaign.yaml`:
   - Increment `current_wave`
   - `wave_{n}_investors: [investor_id list]`
   - `wave_started_date: today`
   - If `target_first_close_date` is null, prompt user to set it (recommend: 60 days from today)
9. Generate `outreach/review-checklist.md` listing the wave investors with per-investor review items
10. Tell user: which investors are in this wave, lead candidates highlighted, warm paths available

## Mode: review

**Purpose**: Weekly status + warm-list + next actions.

**Steps**:

1. Run `campaign_summary.py` → generates `pipeline/weekly-summary.md`
2. Run `warm_list.py` → generates `pipeline/warm-list.md`
3. Run `ghost_check.py` → flags any investor in 14+ day post-meeting silence
4. Run `momentum_check.py` → updates `momentum_score`, `time_to_close_days_remaining`
5. Read all generated files; report to user:
   - Current wave number and status
   - Conversion math: accept_rate, reply_rate, call_booking_rate, call_to_commit_rate
   - Momentum score (0–100) and trend (vs. last review)
   - Bottleneck identified
   - Warm list count + 3 most overdue
   - Ghost flags (if any) — with takeaway draft locations
   - Next 5 actions with dates
6. Update `campaign.yaml`:
   - `last_review_date: today`
   - `next_review_date: today + 7 days`
   - `momentum_score: <computed>`

## Mode: diagnose

**Purpose**: Deep bottleneck analysis. Required before launching a new wave when current wave is stalled.

**Steps**:

1. Read `pipeline/touches.csv` and `pipeline/pipeline.csv`
2. Compute event-based conversion math (denominators from `touches.csv`)
3. Apply bottleneck matrix (see `references/campaign-workflow.md`):

   | Symptom | Root cause | Specific fix |
   |---|---|---|
   | accept_rate < 30% | Profile, targeting, or note | Rewrite connection note; review LinkedIn profile |
   | reply_rate < 20% | Generic message or wrong fit | Tighten ICP; rewrite first DM with proof point |
   | call_rate < 40% of replies | Story or ask | Sharpen one-liner; verify proof is dated and verifiable |
   | call_to_commit < 25% | Terms, traction, or fit | Re-examine cap; verify proof; check founder-investor fit |
   | many "not now" | No milestone urgency | Define a sharper milestone in `terms-plan.md` |
   | low intro_made_rate | Network map weak | Activate more introducers from `intro-paths.csv` |
   | momentum_score < 30 | Wave is dying | Pivot story or targeting before next wave |

4. If wave is `STALLED` (>14 days, 0 commits, 0 partner meetings booked), write **MANDATORY ACTION** block in `weekly-summary.md`
5. Write specific recommended action — be concrete ("rewrite connection note: lead with X" not "improve outreach")
6. Tell user what to fix before launching next wave

## Mode: close

**Purpose**: First-close mechanics — soft-circle, term-sheet aging, allocation status.

**Steps**:

1. Read `pipeline/commitments.csv`
2. Compute totals: soft commits, signed SAFEs, cash received, allocation reserved
3. Generate `pipeline/soft-circle-map.md`:
   - List investors with `soft_circle_permission: yes` (by role/sector descriptor unless user confirms naming)
   - Suggest name-drop sequencing for next prospects
   - Flag investors where `soft_circle_permission = ask` — tell user to confirm
4. Aging checks:
   - `terms_sent_date` > 7 days ago without `signed_date` → flag for follow-up
   - `signed_date` > 5 business days ago without `cash_received_date` → flag for wire follow-up
5. Compute progress: current_committed / target_first_close_amount_usd
6. Tell user:
   - Total committed and % of first-close target
   - Allocation remaining
   - Aging items requiring action
   - Next milestones for first close

## Outputs

```
campaign.yaml                ← updated on every mode run
README.md                    ← regenerated on review
GETTING-STARTED.md           ← generated once at setup
pipeline/weekly-summary.md   ← generated on review/diagnose
pipeline/warm-list.md        ← generated on review
pipeline/soft-circle-map.md  ← generated on close
outreach/review-checklist.md ← generated on wave
```

## Rules

- Never invent data — read from files, run scripts, report what's there
- Never draft messages, narrative, or research — leaf skills only
- Surface all script errors via the plain-language envelope, not raw tracebacks
- `pipeline.md`, `README.md`, `weekly-summary.md` are generated views — never tell user to edit them directly
- All pipeline state changes go through `update_pipeline.py`, not manual CSV edits
- Never name-drop an investor without `soft_circle_permission = yes`
- Refuse to advance to a new wave if current wave is `STALLED` and no `diagnose` has been run

## Script Failure Fallback

If a script fails or is unavailable:
1. Surface the exact command and error to the user
2. Provide the manual equivalent (e.g., "If `momentum_check.py` fails, manually check: any soft commits in the last 14 days?")
3. Do not silently continue — wait for user direction
