# Lead-Prep Rubric — preseed-prep

Lead candidates set the round. They write the first big check, anchor the SAFE cap, and create the social proof that pulls in the rest of the round. Their meetings are different from angel chats and most intro calls. This rubric is for `lead_candidate = yes` rows in `investors.csv`.

All `commitment_status` values reference `~/fundraising/.sys/vocabulary.yaml`.

---

## Pre-seed lead dynamics

**Who sets terms**: the lead. Other investors typically MFN to the lead's terms. This means the SAFE cap negotiation happens with the lead first.

**How to anchor expectations**:
- Don't anchor on a cap in the first call unless the investor asks directly
- When asked, give a band tied to comparable pre-seeds in your sector ("we're seeing $X–$Y in commerce-AI pre-seeds, we'd be in that range")
- Defer specifics until the second meeting OR until terms-stage entry
- Never anchor below `terms-plan.md` cap

**Founder-friendliness matters more for leads**: a lead controls the round documentation, the wire timing, and often the diligence pace. A bad lead can stall a round for 60 days. The Founder-Friendliness Test (Section 7 of the brief) is doubly important.

---

## Term Discussion Agenda — checklist

The Term Discussion Agenda lives inside the lead-candidate prep brief. It is NOT to be brought up in meeting 1 unless the investor opens it. From meeting 2 onward, it is on the agenda.

```
[ ] SAFE cap timing — when in the conversation does this come up?
[ ] Pro-rata expectations — 0x, 1x, 2x, super pro-rata?
[ ] MFN clause — do they expect a side letter?
[ ] Board / observer expectations — pre-seed leads typically want observer or none
[ ] Allocation conversation — what's their target check size for this round?
[ ] Other terms — discount? Most-favored-nation across the round?
```

### SAFE cap discussion timing

- **Meeting 1 (intro_call)**: only if they ask. If asked, give the band, not a number.
- **Meeting 2 (partner_meeting or follow-up)**: agenda topic. Walk through the cap rationale: comparable pre-seeds, milestone alignment, ownership math (if they take $X at $Y cap, they own approximately Z%).
- **Diligence**: cap should be settled. Now negotiating discount, MFN, pro-rata.

**Banned**: anchoring on a low cap to seem reasonable. Pre-seed cap is structurally negotiable; investors expect a real conversation about ownership, not a giveaway.

### Pro-rata expectations

| Lead type | Typical pro-rata expectation |
|---|---|
| Pre-seed fund (named partner) | 1x pro-rata |
| Solo GP / micro-VC | 1x pro-rata, sometimes 2x |
| Operator-angel-leading-syndicate | 0–1x; depends on fund size |
| Strategic angel | 0–0.5x |

Pro-rata is a side letter, not a SAFE cap negotiation. It can be expanded as a concession to close the lead.

### MFN clause

- Pre-seed funds typically expect MFN — if a later investor in this round gets better terms, the lead inherits them
- Operator-angels usually don't ask for MFN
- Side letter format is standard; do not improvise legal language — defer to counsel

### Board / observer expectations

Pre-seed leads typically do NOT take a board seat at this stage. The defaults:

- Observer rights on the board (most common)
- No board seat (typical for solo GPs)
- Information rights (monthly or quarterly updates)

Red flag: a pre-seed lead asking for a full board seat at $750K–$1M check size. That signals control concerns; raise the question with counsel.

### Allocation conversation

The allocation conversation is the explicit ask: "We have allocation reserved for $X at $Y cap. Are we aligned on you taking that allocation?" This is how a soft commit becomes a hard commit.

- Don't have this conversation before they have access to materials and at least one customer reference
- Have it before terms-stage so the negotiation is concrete
- Allocation reservation is logged in `commitments.csv` `allocation_reserved` column

---

## What a "yes" looks like by lead-candidate type

The "yes" artifact differs by type. Knowing the artifact in advance shapes how the meeting closes.

### Pre-seed fund (named partner with carry)

**A "yes" is a term sheet.** A verbal yes is not a yes — pre-seed funds often diligence longer than the founder hopes. The Meeting Goal for a partner meeting with a fund should be:

> Term sheet conversation within 14 days, with diligence checkpoints in between (data room access, customer ref calls, founder background ref calls).

Verbal commit + email confirm is a soft commit, not a hard commit. Wait for paper.

### Solo GP / micro-VC

**A "yes" is a signed SAFE within 14 days of soft commit.** Solo GPs move faster than partner-fund processes. The bottleneck is usually their LP confirmation, not their own conviction.

The Meeting Goal:
> Soft verbal commit + agreement on cap range. Paper within 14 days.

If 14 days pass without paper, treat as soft and apply ghost-detection logic (`/preseed-pipeline ghost`).

### Operator-angel leading a syndicate

**A "yes" is a verbal lead commit + a syndicate vehicle (AngelList rolling fund or syndicate-of-record) targeted.**

Operator-angels who lead don't always lead with their own check — they aggregate other angels under a syndicate. The check size on paper is the syndicate total, not the lead's personal commit.

The Meeting Goal:
> Verbal lead commit + agreement on syndicate vehicle + target syndicate total. Wire path identified.

This dynamic affects soft-circle sequencing — the syndicate members can be name-dropped to other prospects (with `soft_circle_permission = yes`) under a descriptor like "operator-angel syndicate at $X target".

### Strategic angel (industry executive who doubles as a customer/advisor candidate)

**A "yes" is a verbal commit + a customer or advisor relationship documented.**

Strategic angels often commit small ($25K–$100K) but bring distribution, hiring leverage, or customer access. The check is part of the commit; the relationship is the rest.

The Meeting Goal:
> Verbal commit + scoped advisor / customer / hiring-help relationship + cap-table treatment.

---

## Lead-pursuit rules per wave

- Each wave (`/preseed-campaign wave`) should have **2–3 lead candidates** pursued on a dedicated track
- Lead candidates get **more meetings before term discussion** — typically 2–3 vs. 1–2 for non-leads
- Lead candidates get **explicit term-discussion agenda** from meeting 2 onward
- Lead candidates get **pro-rata and board/observer expectation setting** before terms are sent

A wave without lead candidates does not advance. `/preseed-campaign wave` enforces a 60% lead-candidate floor in Wave 1. See `momentum-rules.md` in the campaign skill for stalled-wave handling.

---

## Common lead-candidate failure modes

| Failure | Root cause | Fix |
|---|---|---|
| Lead "keeps asking for one more thing" | They're stalling — usually conviction or process bottleneck | Run takeaway protocol after 14 days post-meeting silence (`/preseed-pipeline ghost`) |
| Lead verbally commits, paper never shows | LP / vehicle issue, or lead never had real allocation | Set a 14-day paper deadline at soft commit; if missed, treat as ghosted |
| Lead asks for a board seat at pre-seed | Control concern | Negotiate down to observer; if they refuse, this is a likely bad-fit lead |
| Lead anchors low on cap | Either signaling bad terms or testing | Cite comparable pre-seeds, hold the band, don't break |
| Lead asks for super pro-rata + MFN + board seat | Treating you like a series A | Push back on stage-appropriate terms; bring counsel |

When any of these surface, log in `pipeline.csv.notes` and flag to `/preseed-campaign diagnose` before the next wave.
