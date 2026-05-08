# Schema Definitions

Seed template. Copied to `~/fundraising/.sys/schemas.yaml` at setup.

## campaign.yaml

```yaml
required:
  - version
  - company
  - stage
  - target_raise_usd
  - instrument
  - current_wave
  - wave_size_target
  - lead_candidate_pct
  - campaign_status
  - story_gate

optional:
  - target_first_close_amount_usd
  - target_first_close_date
  - simple_mode               # bool, default false
  - snapshot_on_change        # bool, default false
  - voice_gate
  - last_review_date
  - next_review_date
  - wave_started_date
  - momentum_score
  - wave_<n>_investors        # repeats per wave
  - wave_<n>_start_date
```

## investors.csv

```yaml
required_columns:
  - investor_id              # unique slug, e.g. jane-doe-acme-2026
  - first_name
  - last_name
  - investor_name
  - firm_or_handle
  - role                     # vocab.roles
  - lead_candidate           # yes | no
  - linkedin_profile_url     # required for HeyReach import
  - public_contact_path
  - check_size_range
  - stage_fit
  - domain_fit
  - score_100
  - score_10
  - confidence               # vocab.confidence
  - source_urls
  - source_dates
  - source_types             # vocab.source_types

optional_columns:
  - geography
  - operator_relevance
  - investment_evidence
  - recent_signal
  - thesis_match
  - portfolio_conflict
  - conflict_severity
  - disqualified             # yes | no
  - disqualified_reason
  - warm_path_evidence
  - warm_path_confidence     # vocab.confidence
  - intro_owner
  - intro_request_status     # vocab.intro_status
  - recommended_channel
  - ask_stage                # vocab.ask_stages
  - why_this_wave

required_constraints:
  - investor_id is unique
  - if lead_candidate = yes, investment_evidence must include "led" or "anchored"
  - source_urls and source_dates have equal counts
```

## intro-paths.csv

```yaml
required_columns:
  - investor_id
  - investor_name
  - introducer_name
  - introducer_relationship
  - relationship_strength    # vocab.relationship_strength
  - intro_status             # vocab.intro_status

optional_columns:
  - firm_or_handle
  - intro_angle
  - intro_request_text
  - last_intro_touch_date
  - next_intro_action
  - confidence               # vocab.confidence
```

## outreach.csv

```yaml
required_columns:
  - investor_id
  - investor_name
  - channel
  - relationship_status
  - ask_stage                # vocab.ask_stages
  - char_count_connection_note
  - voice_score              # 0-1 from score_voice_match.py
  - needs_human_review       # yes | no | high

optional_columns:
  - connection_note
  - accepted_dm
  - followup_3_day
  - followup_7_day
  - warm_intro_ask
  - forwardable_intro_blurb
  - warm_update
  - pass_response
  - reapproach_note
  - fast_forward_pitch
  - takeaway_email
  - meeting_confirmation
  - source_signal
  - source_url
  - review_notes

required_constraints:
  - char_count_connection_note <= 200
  - takeaway_email word count <= 80
  - warm_update word count <= 150
```

## pipeline.csv

```yaml
required_columns:
  - investor_id
  - investor_name
  - status                   # vocab.statuses
  - last_touch_date

optional_columns:
  - firm
  - check_size_range
  - lead_candidate
  - score_10
  - pass_reason
  - reapproach_trigger
  - last_warm_touch
  - last_meeting_date        # required if status is post-meeting
  - data_room_accessed_date
  - ghost_flag_date
  - takeaway_sent_date
  - next_action
  - next_action_date
  - owner
  - notes
  - source

required_constraints:
  - if status in [intro_call_done, partner_meeting_done, data_room_accessed, diligence], last_meeting_date must be set
  - if status = pass, pass_reason must be set
  - if status = ghosted, ghost_flag_date must be set
```

## touches.csv

```yaml
required_columns:
  - touch_id
  - investor_id
  - touch_date
  - touch_type               # vocab.touch_types
  - status_before
  - status_after

optional_columns:
  - channel
  - message_id
  - material_interaction     # vocab.material_interactions
  - estimated_minutes
  - owner
  - notes
  - source

required_constraints:
  - append-only — no overwrites
  - touch_id is unique
  - status_before and status_after both in vocab.statuses
```

## commitments.csv

```yaml
required_columns:
  - investor_id
  - investor_name
  - commitment_status        # vocab.commitment_status
  - soft_circle_permission   # vocab.soft_circle_permission

optional_columns:
  - soft_commit_amount
  - signed_safe_amount
  - cash_received_amount
  - allocation_reserved
  - terms_sent_date
  - signed_date
  - cash_received_date
  - notes

required_constraints:
  - investor_id matches investors.csv
```

## voice-fingerprint.yaml

```yaml
required:
  - sample_count
  - avg_sentence_length_words
  - voice_score_threshold

optional:
  - contraction_rate
  - paragraph_avg_sentences
  - opener_patterns
  - closer_patterns
  - register
  - signature_phrases
  - em_dash_rate
  - banned_default
  - banned_personal
  - preferred_alternatives
```
