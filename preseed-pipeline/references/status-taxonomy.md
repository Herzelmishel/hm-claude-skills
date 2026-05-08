# Status Taxonomy — preseed-pipeline

Detailed status definitions. Every status value is defined in `~/fundraising/.sys/vocabulary.yaml` — this file documents what triggers entry, what triggers exit, valid next states, and which scripts run on entry/exit.

Never hardcode statuses in code or prose. Always reference vocabulary.yaml. This file is documentation, not the source of truth.

---

## Pre-contact statuses

### `identified`
- **Entry**: investor row added to `investors.csv` by `/preseed-prospect`
- **Exit / next**: `approved` (passes ICP gates) or `disqualified` (fails ICP)
- **Scripts**: none on entry; `score_investors.py` runs on creation

### `approved`
- **Entry**: investor passes ICP gates and disqualification rules
- **Exit / next**: `intro_requested` (warm path) or `connection_sent` (cold path)
- **Scripts**: none

### `intro_requested`
- **Entry**: an introducer has been asked to forward the blurb
- **Exit / next**: `intro_made` (introducer agreed and sent) or back to `approved` (introducer declined)
- **Scripts**: none

### `intro_made`
- **Entry**: introducer sent the forwardable blurb to the investor
- **Exit / next**: `connected` (investor accepted intro / connected) or `pass` (investor declined to engage)
- **Scripts**: none

---

## Outreach statuses (cold path)

### `connection_sent`
- **Entry**: connection note was sent on LinkedIn (manually by user)
- **Exit / next**: `connected` (accepted), `pass` (declined), or stays in `connection_sent` (no action — flagged after 14 days)
- **Scripts**: none

### `connected`
- **Entry**: investor accepted connection request
- **Exit / next**: `first_dm_sent` after Herzel sends the accepted-DM
- **Scripts**: none

### `first_dm_sent`
- **Entry**: accepted DM sent
- **Exit / next**: `replied_positive` / `replied_neutral` / `replied_negative`, or `followup_1_sent` after 3 days, or stays silent
- **Scripts**: none

### `followup_1_sent` / `followup_2_sent`
- **Entry**: 3-day / 7-day follow-up sent
- **Exit / next**: `replied_*`, `pass`, or `nurture`
- **Scripts**: none

### `replied_positive` / `replied_neutral` / `replied_negative`
- **Entry**: investor replied with the corresponding sentiment
- **Exit / next**:
  - positive → `intro_call_booked`
  - neutral → `nurture`
  - negative → `pass`
- **Scripts**: none

---

## Engagement statuses

### `nurture`
- **Entry**: investor said "too early, keep me posted" or replied neutrally
- **Exit / next**: stays in `nurture` until a milestone unlocks, or moves to `do_not_contact` after 90+ days of silence with no positive signal
- **Scripts**: `warm_list.py` includes the investor in 21/45/90 cadence

### `intro_call_booked`
- **Entry**: investor confirmed a meeting time
- **Exit / next**: `intro_call_done` after meeting, or `pass` if cancelled
- **Scripts**: prompt user to invoke `/preseed-prep [investor_id] intro_call`

### `intro_call_done`
- **Entry**: meeting occurred; `last_meeting_date` populated
- **Exit / next**: `partner_meeting_booked`, `data_room_accessed`, `diligence`, `nurture`, `soft_commit`, `pass`, or `ghosted` (after 14 days silence)
- **Scripts**: prompt user to invoke `/preseed-prep [investor_id] post-meeting` for follow-up draft

### `partner_meeting_booked` / `partner_meeting_done`
- **Entry**: full-partner meeting booked / completed
- **Exit / next**: see `intro_call_done` exits
- **Scripts**: prompt for `/preseed-prep [investor_id] partner_meeting`

### `data_room_accessed`
- **Entry**: investor opened the data room (a high-value diligence signal)
- **Exit / next**: `diligence`, `soft_commit`, `pass`, or `ghosted`
- **Scripts**: append touch with `material_interaction = data_room_accessed`. Sets `data_room_accessed_date`.

### `diligence`
- **Entry**: investor is actively diligencing — customer references, financial questions, technical deep-dive
- **Exit / next**: `soft_commit`, `pass`, or `ghosted`
- **Scripts**: none

### `ghosted`
- **Entry**: detected by `ghost_check.py` — post-meeting status with >14 days of silence and `last_meeting_date` set
- **Exit / next**: prior post-meeting status (if reply received within 48 hours after takeaway) or `pass` with `pass_reason = ghosted`
- **Scripts on entry**: `ghost_check.py` writes `outreach/[slug]-takeaway.md` draft. User sends manually.
- **Scripts on exit**: `update_pipeline.py` reverts status or transitions to `pass`

---

## Commitment statuses

### `soft_commit`
- **Entry**: investor verbally committed (with or without a cap range)
- **Exit / next**: `terms_sent`, `signed_safe`, `pass` (rare), or `ghosted` (if commit goes silent)
- **Scripts**: regenerate `soft-circle-map.md` if `soft_circle_permission = yes`. Update `commitments.csv`.

### `terms_sent`
- **Entry**: SAFE / term sheet sent for signature
- **Exit / next**: `signed_safe` or `pass`
- **Scripts**: update `commitments.csv` with `terms_sent_date`

### `signed_safe`
- **Entry**: SAFE signed by both parties
- **Exit / next**: `cash_received`
- **Scripts**: update `commitments.csv` with `signed_safe_amount` and `signed_date`

### `cash_received`
- **Entry**: wire received
- **Exit / next**: terminal — investor stays here
- **Scripts**: update `commitments.csv` with `cash_received_amount` and `cash_received_date`

---

## Terminal / removal statuses

### `pass`
- **Entry**: investor declined to participate
- **Exit / next**: stays here unless a `reapproach_trigger` fires; then moves back to `approved` or `connection_sent` for the re-approach
- **Scripts on entry**: `reapproach_notes.py` writes `outreach/[slug]-reapproach.md` keyed to the recorded `reapproach_trigger`. `update_pipeline.py` prompts for `pass_reason` and `reapproach_trigger`.

### `deferred`
- **Entry**: investor explicitly deferred to a future round (not "no", just "later")
- **Exit / next**: `nurture` (after 30 days) or `do_not_contact`
- **Scripts**: none

### `do_not_contact`
- **Entry**: user explicitly flagged, OR `nurture` investor passed 90-day cadence with no positive signal, OR investor requested removal
- **Exit / next**: terminal for this round
- **Scripts**: none

---

## Valid status transitions (summary)

| From | To (most common) |
|---|---|
| `identified` | `approved`, `disqualified` |
| `approved` | `intro_requested`, `connection_sent` |
| `intro_requested` | `intro_made`, `approved` |
| `intro_made` | `connected`, `pass` |
| `connection_sent` | `connected`, `pass`, stays |
| `connected` | `first_dm_sent` |
| `first_dm_sent` | `replied_*`, `followup_1_sent`, stays |
| `replied_positive` | `intro_call_booked` |
| `replied_neutral` | `nurture` |
| `replied_negative` | `pass` |
| `intro_call_booked` | `intro_call_done`, `pass` |
| `intro_call_done` | `partner_meeting_booked`, `data_room_accessed`, `diligence`, `nurture`, `soft_commit`, `pass`, `ghosted` |
| `partner_meeting_done` | `data_room_accessed`, `diligence`, `soft_commit`, `pass`, `ghosted` |
| `data_room_accessed` | `diligence`, `soft_commit`, `pass`, `ghosted` |
| `diligence` | `soft_commit`, `pass`, `ghosted` |
| `ghosted` | prior post-meeting status (revert) or `pass` |
| `soft_commit` | `terms_sent`, `pass`, `ghosted` |
| `terms_sent` | `signed_safe`, `pass` |
| `signed_safe` | `cash_received` |
| `nurture` | `replied_positive`, `intro_call_booked`, `do_not_contact` |
| `pass` | back to `approved` (re-approach trigger fires) |

`update_pipeline.py` validates transitions against `vocabulary.yaml`. It does NOT enforce transition adjacency — pre-seed dynamics are messy and statuses sometimes jump (e.g., `connected` → `pass` after a quick LinkedIn reply).
