# Next-Action Rules — preseed-pipeline

Rules for computing `next_action` and `next_action_date` for each investor based on current status. Used by `update_pipeline.py` after every status change and surfaced in `pipeline.md` and `weekly-summary.md`.

All status values reference `~/fundraising/.sys/vocabulary.yaml`.

---

## Computing the next action

For each investor row, the next action is determined by status + most recent touch + lead-candidate flag.

| Status | next_action | next_action_date |
|---|---|---|
| `identified` | "Score and approve via /preseed-prospect" | today + 1 |
| `approved` (warm path exists) | "Send warm intro ask via /preseed-outreach" | today + 1 |
| `approved` (no warm path) | "Send connection note via /preseed-outreach" | today + 1 |
| `intro_requested` (>3 days, no movement) | "Nudge introducer politely" | today + 0 (overdue) |
| `intro_requested` (≤3 days) | "Wait for introducer reply" | last_touch + 3 |
| `intro_made` | "Wait for investor reply, prepare follow-up" | today + 5 |
| `connection_sent` (≤14 days) | "Wait for accept" | last_touch + 14 |
| `connection_sent` (>14 days) | "Move to pass — no accept" | today + 0 |
| `connected` (no first_dm_sent) | "Send accepted DM via /preseed-outreach" | today + 1 |
| `first_dm_sent` (3 days, no reply) | "Send 3-day follow-up via /preseed-outreach" | today + 0 |
| `first_dm_sent` (7 days, no reply) | "Send 7-day follow-up (last in wave)" | today + 0 |
| `first_dm_sent` (>10 days, no reply) | "Move to nurture or pass" | today + 0 |
| `replied_positive` | "Book intro call via /preseed-outreach" | today + 1 |
| `replied_neutral` | "Move to nurture, schedule warm update" | today + 0 |
| `replied_negative` | "Run pass protocol via /preseed-pipeline update --new-status pass" | today + 0 |
| `intro_call_booked` | "Run /preseed-prep [id] intro_call" | meeting_date - 1 |
| `intro_call_done` (no follow-up sent) | "Run /preseed-prep [id] post-meeting (24-hour follow-up)" | meeting_date + 1 |
| `intro_call_done` (follow-up sent, ≤14 days) | "Wait for reply" | last_meeting + 7 |
| `intro_call_done` (>14 days silent) | "Triggers ghost detection — takeaway draft" | today + 0 |
| `partner_meeting_booked` | "Run /preseed-prep [id] partner_meeting" | meeting_date - 1 |
| `partner_meeting_done` (no follow-up sent) | "Run /preseed-prep [id] post-meeting" | meeting_date + 1 |
| `data_room_accessed` | "Reach out re: diligence questions, schedule follow-up call" | last_meeting + 3 |
| `diligence` (active) | "Respond to diligence questions, hold cadence" | last_touch + 2 |
| `diligence` (>14 days silent) | "Triggers ghost detection — takeaway draft" | today + 0 |
| `ghosted` (takeaway not yet sent) | "Send takeaway draft (outreach/[slug]-takeaway.md)" | ghost_flag_date + 1 |
| `ghosted` (takeaway sent, ≤2 days) | "Wait for 48-hour reply window" | takeaway_sent + 2 |
| `ghosted` (takeaway sent, >2 days, no reply) | "Move to pass with reason=ghosted" | today + 0 |
| `nurture` (`last_warm_touch` ≤21 days) | "Hold — next warm update at day 21" | last_warm_touch + 21 |
| `nurture` (`last_warm_touch` 21–45 days) | "Send 21-day warm update via /preseed-outreach warm-update" | today + 0 |
| `nurture` (`last_warm_touch` 45–90 days) | "Send 45-day warm update — product/thesis update" | today + 0 |
| `nurture` (`last_warm_touch` >90 days, no positive signal) | "Move to do_not_contact for this round" | today + 0 |
| `soft_commit` | "Send terms / SAFE via counsel" | today + 3 |
| `terms_sent` (≤7 days) | "Wait for signature" | terms_sent_date + 7 |
| `terms_sent` (>7 days) | "Nudge with status check" | today + 0 |
| `signed_safe` | "Send wire instructions" | signed_date + 1 |
| `cash_received` | "Update soft-circle map; close-loop email" | today + 1 |
| `pass` (reapproach_trigger NOT yet hit) | "Hold — milestone target = [reapproach_trigger]" | n/a |
| `pass` (reapproach_trigger hit) | "Send reapproach note via /preseed-outreach" | today + 0 |
| `do_not_contact` | "No action this round" | n/a |
| `deferred` | "Move to nurture in 30 days" | last_touch + 30 |

---

## Lead-candidate overrides

If `lead_candidate = yes`, the next action shifts to a longer-courtship rhythm:

- After `intro_call_done`: target a second meeting within 14 days, not just a 24-hour follow-up
- After `partner_meeting_done`: terms-discussion agenda from `/preseed-prep` (lead-prep-rubric.md)
- After `soft_commit`: paper deadline tightened — terms within 7 days for solo GPs, within 14 days for funds. If missed, treat as soft and apply ghost monitoring.

---

## Date arithmetic rules

- All dates use ISO format: `YYYY-MM-DD`
- `today + N` means N calendar days forward
- `last_touch` references the most recent `touch_date` in `touches.csv` for this investor
- `last_meeting` references `last_meeting_date` in `pipeline.csv`
- `last_warm_touch` references `last_warm_touch` in `pipeline.csv`
- `ghost_flag_date` and `takeaway_sent_date` are populated by the ghost protocol
- `terms_sent_date` and `signed_date` come from `commitments.csv`

---

## Why these rules exist

The `next_action` and `next_action_date` columns are what make `pipeline.md` and `weekly-summary.md` actionable. Without them, the user has to mentally compute "what should I do for this investor today" 30+ times in a single review session — which is the failure mode that causes pipelines to drift.

`update_pipeline.py` recomputes `next_action` on every status change. `campaign_summary.py` reads them to surface the top 5 actions in the weekly summary, ranked by `next_action_date` (overdue first) and `score_10` (high-conviction investors break ties).
