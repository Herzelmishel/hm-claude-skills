# Shared Vocabulary

Seed template. Copied to `~/fundraising/.sys/vocabulary.yaml` at setup. The workspace copy is the runtime source of truth — do NOT load this file directly in downstream skills.

```yaml
# ====================================================================
# CANONICAL ENUMS — single source of truth for the entire skill suite
# ====================================================================

roles:
  - operator_angel
  - commerce_founder_angel
  - ai_saas_angel
  - micro_vc
  - preseed_fund
  - scout
  - strategic_angel
  - customer_advisor_candidate

statuses:
  - identified
  - approved
  - intro_requested
  - intro_made
  - connection_sent
  - connected
  - first_dm_sent
  - followup_1_sent
  - followup_2_sent
  - replied_positive
  - replied_neutral
  - replied_negative
  - nurture
  - intro_call_booked
  - intro_call_done
  - partner_meeting_booked
  - partner_meeting_done
  - data_room_accessed
  - diligence
  - soft_commit
  - terms_sent
  - signed_safe
  - cash_received
  - ghosted
  - pass
  - deferred
  - do_not_contact

confidence:
  - high
  - medium
  - low
  - unknown

source_types:
  - linkedin_post
  - linkedin_profile
  - firm_website
  - crunchbase
  - twitter
  - newsletter
  - podcast
  - conference_talk
  - portfolio_company

relationship_strength:
  - strong
  - medium
  - weak
  - unknown

ask_stages:
  - permission
  - call
  - pitch
  - follow_up
  - fast_forward
  - takeaway

commitment_status:
  - soft_commit
  - hard_commit
  - terms_sent
  - signed
  - wired
  - passed

soft_circle_permission:
  - yes
  - no
  - ask

material_interactions:
  - none
  - deck_viewed
  - data_room_accessed
  - demo_watched
  - financials_requested

intro_status:
  - not_asked
  - asked
  - made
  - declined

touch_types:
  - outreach
  - meeting
  - material_sent
  - material_viewed
  - warm_update
  - takeaway
  - intro_request
  - intro_made
```

## Rules

- Every CSV column that takes an enum value MUST validate against this list
- No skill or script may invent new status codes — extend this file via PR
- The workspace copy at `~/fundraising/.sys/vocabulary.yaml` is what runtime checks read
