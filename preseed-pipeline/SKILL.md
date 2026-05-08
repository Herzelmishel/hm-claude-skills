---
name: preseed-pipeline
description: Track and diagnose the Agentis pre-seed pipeline. Status, events, commitments, soft circle, warm list, ghost handling, close.
argument-hint: "[update|weekly-review|warm-list|close-check]"
when-not-to-use:
  - For drafting messages — use /preseed-outreach
  - For call prep — use /preseed-prep
  - For story updates — use /preseed-story
outputs:
  pipeline/pipeline.csv: current pipeline state (source of truth)
  pipeline/touches.csv: event log, append-only
  pipeline/commitments.csv: all commitment states
  pipeline/pipeline.md: generated readable view
  pipeline/weekly-summary.md: generated weekly diagnosis
  pipeline/warm-list.md: generated warm-touch action list
  pipeline/soft-circle-map.md: generated name-drop sequencing
---

# preseed-pipeline

Pipeline is the system of record for the round. Every status change, every touch, every commitment is logged here. Conversion math comes from event-based denominators in `touches.csv`. Diagnosis comes from `commitments.csv`. Outputs are surfaced as markdown views — never hand-edited.

## When to use

- The user reports a status change (call booked, pass, soft commit, signed SAFE)
- The user wants the weekly diagnosis (`weekly-review`)
- The user wants the warm-list action plan (`warm-list`)
- The user wants close-check status before declaring first close (`close-check`)
- An automated step needs the soft-circle map regenerated after a soft commit

## When NOT to use

- For drafting messages — use `/preseed-outreach`
- For meeting prep — use `/preseed-prep`
- For changing the story or one-pager — use `/preseed-story`
- For prospecting a new investor — use `/preseed-prospect`

## Pre-checks

1. `~/fundraising/campaign.yaml` exists — if missing, stop and tell user to run `/preseed-campaign setup`
2. `~/fundraising/.sys/vocabulary.yaml` exists — load `statuses`, `material_interactions`, `commitment_status`
3. `~/fundraising/.sys/schemas.yaml` exists — schemas for `pipeline.csv`, `touches.csv`, `commitments.csv`
4. `~/fundraising/pipeline/pipeline.csv` exists — if missing, initialize from schema
5. `~/fundraising/pipeline/touches.csv` exists — if missing, initialize from schema
6. `~/fundraising/pipeline/commitments.csv` exists — if missing, initialize from schema
7. The `investor_id` referenced is present in `~/fundraising/investors/investors.csv`

## Three Source-of-Truth Files

| File | Role | Mutability |
|---|---|---|
| `pipeline.csv` | Current investor state | Updated by `update_pipeline.py` only |
| `touches.csv` | Event log, every action taken | **Append-only.** Never overwrite. |
| `commitments.csv` | Commitment states | Updated on relevant status change |

Schemas live in `~/fundraising/.sys/schemas.yaml`. Never hand-edit the source-of-truth CSVs — use `update_pipeline.py` and the helper scripts.

## Modes

### `update`

The user reports a status change for one investor. The skill calls `update_pipeline.py` with `--investor-id`, `--new-status`, `--note`. The script:

- Validates `new-status` against `vocabulary.yaml`
- Captures the prior status as `status_before`
- Updates `pipeline.csv`, sets `last_touch_date = today`
- Appends a new row to `touches.csv` with a fresh `touch_id` (UUID)
- If `new-status = pass`, prompts for `pass_reason` and `reapproach_trigger`, then runs `reapproach_notes.py`
- If `new-status = ghosted`, sets `ghost_flag_date`
- Recomputes `next_action` and `next_action_date` per `references/next-action-rules.md`

### `weekly-review`

Calls `campaign_summary.py`, then `warm_list.py`, then `ghost_check.py`. Produces:
- `pipeline/weekly-summary.md` — conversion math, momentum score, bottleneck flags, top 5 next actions, hours-per-pass and hours-per-commit
- `pipeline/warm-list.md` — investors due for a warm touch
- Newly-ghosted investors flagged with takeaway drafts in `outreach/`

### `warm-list`

Calls `warm_list.py` standalone. Generates `pipeline/warm-list.md` with the 21 / 45 / 90 day cadence.

### `close-check`

Reads `commitments.csv`. Surfaces:
- Total `signed_safe_amount` and `cash_received_amount`
- Distance to `target_first_close_amount_usd` (from `campaign.yaml`)
- The soft-circle map (regenerated)
- Time-to-close math from `momentum_check.py` (delegated to `/preseed-campaign`)

## Pass & Ghost Protocol

### Pass protocol (when status changes to `pass`)

1. `update_pipeline.py` prompts for `pass_reason` (their actual words, not your spin)
2. Prompts for `reapproach_trigger` (the milestone that would change their answer)
3. Calls `reapproach_notes.py` to generate `outreach/[investor-slug]-reapproach.md` keyed to that trigger
4. Generates a `pass_response` row in `outreach.csv` (asks for 1–2 intros to better-fit investors) — delegated to `/preseed-outreach` on next run
5. Sets status to `pass`, NOT `do_not_contact` (unless the user explicitly flagged the investor as do-not-contact)

### Ghost protocol (`ghost_check.py`)

Runs on every `weekly-review` and on every `update`. Detects investors where:
- `status` is in {`intro_call_done`, `partner_meeting_done`, `data_room_accessed`, `diligence`}
- No row in `touches.csv` for this investor in the last 14 days
- `last_meeting_date` is populated

Action:
1. Sets status to `ghosted`, `ghost_flag_date = today`
2. Generates `outreach/[investor-slug]-takeaway.md` — voice-matched, ≤80 words ("Haven't heard back. Pulling the allocation. Let me know if I'm reading this wrong.")
3. The user sends the takeaway manually (this skill never sends)
4. User marks `takeaway_sent_date` via `update_pipeline.py`
5. After 48 hours: if reply received, revert status to prior post-meeting state (logged as a touch). If no reply, move to `pass` with `pass_reason = ghosted`, run normal pass protocol.

Why: ghosting is the single most common failure mode at pre-seed. Unmanaged, it leaves the pipeline cluttered with phantom "active" investors and starves momentum. The takeaway forces a yes/no and cleans the pipeline within 48 hours.

## Anti-ghost detection logic (used by `ghost_check.py`)

```
For each investor in pipeline.csv:
  if status in {intro_call_done, partner_meeting_done, data_room_accessed, diligence}:
    if last_meeting_date is set:
      latest_touch_date = max(touch_date for touches where investor_id matches)
      days_silent = today - max(latest_touch_date, last_meeting_date)
      if days_silent > 14 and status != ghosted:
        flag_ghosted(investor_id)
        write_takeaway_draft(investor_id)
```

`status` and `material_interactions` reference `vocabulary.yaml`.

## Warm List Management

A `nurture` investor is one who said "too early, keep me posted." This is the highest-conversion group at close — running into a hot moment with a strong nurture group creates the round's compression.

`warm_list.py` produces `pipeline/warm-list.md` with the 21 / 45 / 90 day cadence (see `references/warm-list-rules.md`):

- Day 21 from `last_warm_touch`: First nudge — most recent shipped milestone
- Day 45: Second nudge — product update or thesis evolution
- Day 90: Final nudge — round status + soft-circle descriptor

If a `nurture` investor passes the 90-day touch with no positive signal, status moves to `do_not_contact` for this round. Re-evaluate at next round.

## Soft-Circle Map

Generated from `commitments.csv` where `soft_circle_permission = yes`:

- Lists who can be name-dropped, with role/sector descriptor (NOT the investor's name by default)
- Suggests sequencing — which investor to reveal to which prospect, in what order, to maximize FOMO
- See `references/soft-circle-rules.md` for sequencing strategy

The descriptor-first rule is non-negotiable: name only after explicit user confirmation. Never name-drop without `soft_circle_permission = yes`.

## Conversion Math (event-based denominators from `touches.csv`)

```
accept_rate           = unique connected         / unique connection_sent
reply_rate            = unique replied           / unique first_dm_sent
positive_reply_rate   = unique replied_positive  / unique first_dm_sent
call_booking_rate     = unique intro_call_booked / unique connected
call_to_commit_rate   = unique soft_commit       / unique intro_call_done
signed_to_cash_rate   = unique cash_received     / unique signed_safe
```

Computed in `campaign_summary.py`. Surface in `weekly-summary.md`.

## Bottleneck Diagnosis

| Symptom | Root cause |
|---|---|
| Low approval rate (`approved` / `identified`) | ICP too broad; tighten in `/preseed-prospect` |
| Low intro-made rate | Network map weak; activate more introducers |
| Low accept rate | Profile / targeting / connection note problem |
| Low reply rate | Message generic or investor wrong fit |
| Good calls, few commits | Story / terms / proof / founder-fit issue |
| Many "not now" responses | Round needs sharper milestone |
| High commit rate, slow signing | Terms or legal complexity; simplify SAFE |

`campaign_summary.py` flags bottlenecks based on these thresholds and surfaces them in the weekly summary.

## `data_room_accessed` handling

When an investor accesses the data room (a high-value diligence signal):

1. Status moves to `data_room_accessed` (per `vocabulary.yaml`)
2. `data_room_accessed_date` is populated in `pipeline.csv`
3. A row is appended to `touches.csv` with `material_interaction = data_room_accessed` and `estimated_minutes = 30` (founder-effort tracking)
4. The investor is now in the post-meeting bucket for ghost detection — 14-day silence triggers takeaway

This status is tracked separately because it is the strongest pre-commit diligence signal we have.

## Outputs

- `pipeline/pipeline.csv` — current state (only `update_pipeline.py` writes here)
- `pipeline/touches.csv` — append-only event log
- `pipeline/commitments.csv` — commitment states
- `pipeline/pipeline.md` — generated readable view (regenerated on every update)
- `pipeline/weekly-summary.md` — generated by `weekly-review`
- `pipeline/warm-list.md` — generated by `warm-list` or `weekly-review`
- `pipeline/soft-circle-map.md` — generated after first soft commit
- `outreach/[slug]-takeaway.md` and `outreach/[slug]-reapproach.md` — generated by helper scripts

## Rules

- `touches.csv` is **append-only**. Never overwrite, never delete.
- `pipeline.md`, `weekly-summary.md`, `warm-list.md`, `soft-circle-map.md`, `pipeline.md` are generated views. Do not hand-edit.
- All status / commitment / interaction enums come from `~/fundraising/.sys/vocabulary.yaml`. Never hardcode.
- Schemas come from `~/fundraising/.sys/schemas.yaml`. Workspace `.sys/` is the source of truth — never reach into another skill's `references/` directory at runtime.
- Conversion math uses **event-based** denominators from `touches.csv`. Never count `pipeline.csv` rows as the denominator.
- Surface script errors using JSON envelope: `{"error": "...", "field": "...", "fix": "..."}`. Translate to plain language for the user.
- Never name-drop without `soft_circle_permission = yes`.

## Scripts

| Script | When to run | Purpose |
|---|---|---|
| `scripts/update_pipeline.py` | On every status change | Atomic update of pipeline.csv + append to touches.csv |
| `scripts/campaign_summary.py` | `weekly-review` | Conversion math, hours, bottleneck flags, weekly-summary.md |
| `scripts/warm_list.py` | `warm-list` and `weekly-review` | 21/45/90-day cadence list |
| `scripts/reapproach_notes.py` | After status=pass | Drafts re-approach note keyed to reapproach_trigger |
| `scripts/ghost_check.py` | On every update + every `weekly-review` | Detects 14+ day post-meeting silence, drafts takeaway |
