# HM Claude Skills

A collection of personal Claude skills built by Herzel Mishel. Each skill is a self-contained folder with a `SKILL.md` file and any supporting scripts, references, or assets it needs.

## Skills in this repo

### General

- `humanizer/` — Rewrites drafts to sound human, not AI. Strips em dashes, fake depth, rule-of-three padding, and flat rhythm. Adds opinion, specificity, and rhythm variation. Useful for LinkedIn posts, cold emails, blog posts, investor updates, and founder content.

### Pre-seed fundraising operating system

A 7-skill suite that runs a pre-seed fundraising campaign as a learning loop: story → fit → warm path → outreach → meeting → diagnosis → iterate → close. State lives in CSV/YAML inside `~/fundraising/` (workspace), not in chat. All outreach is human-reviewed drafts — never automated sending.

- `preseed-campaign/` — Controller. Setup, wave planning, weekly review, bottleneck diagnosis, momentum tracking, first-close. Owns sequencing, gates, and state. Uses `disable-model-invocation: true`.
- `preseed-story/` — Positioning, narrative, proof, objections, terms, ICP, one-pager. Story gate that blocks all downstream skills until `round-brief.yaml` is built.
- `preseed-voice/` — Extracts founder voice fingerprint from real writing samples (LinkedIn posts, founder updates, emails). Loaded automatically by `preseed-outreach` so messages match the founder's actual cadence, not AI default.
- `preseed-prospect/` — Investor discovery and scoring. 100-point rubric, 8 disqualification gates, lead-candidate designation, network-first intro path mapping.
- `preseed-outreach/` — Voice-constrained, human-reviewed messages by channel and ask stage. Connection notes (≤200 chars), warm intros, fast-forward overrides, takeaway emails (anti-ghost), 21/45/90-day nurture cadence.
- `preseed-prep/` — Pre-call briefs and 24-hour follow-up drafts. Lead-candidate-specific term discussion agenda. Source-disciplined.
- `preseed-pipeline/` — Event log (touches.csv), state (pipeline.csv), commitments (commitments.csv). Anti-ghost protocol (14-day silence detection), warm list management, soft-circle FOMO map, conversion math, bottleneck diagnosis.

### How the pre-seed suite works together

```
/preseed-campaign setup       → workspace + .sys/ config + GETTING-STARTED.md
/preseed-story                → round-brief.yaml + one-pager + objection bank
/preseed-voice                → voice-fingerprint.yaml from samples
/preseed-prospect             → investors.csv + intro-paths.csv (scored, ranked)
/preseed-campaign wave        → select Wave 1 (10–15, ≥60% lead candidates)
/preseed-outreach <id>        → voice-matched drafts per channel
                                (human-reviewed, never auto-sent)
/preseed-prep <id>            → pre-call brief + 24h follow-up draft
/preseed-pipeline update      → log every status change to touches.csv
/preseed-campaign review      → weekly diagnosis + warm list + ghost detection
/preseed-campaign diagnose    → required when wave is STALLED
/preseed-campaign close       → soft-circle map + term sheet aging
```

Workspace state lives at `~/fundraising/` and is self-contained — `.sys/` holds vocabulary and schemas copied from skill seed templates, so no skill cross-references another skill at runtime.

## Repo layout

Each skill lives in its own folder, named after the skill. Inside each folder:

```
skill-name/
├── SKILL.md       (required, includes YAML frontmatter)
├── scripts/       (optional, executable helpers)
├── references/    (optional, docs loaded on demand)
└── assets/        (optional, templates and static files)
```

This matches the Anthropic skill-creator convention so any skill in this repo can be installed into Claude Code, Claude.ai (where supported), or other Claude environments without restructuring.

## How to use a skill

Three options.

1. Claude Code or Claude.ai with custom skills enabled. Drop the skill folder into the skills directory and Claude will load it automatically when a user prompt matches its description.
2. Inline. Paste the contents of `SKILL.md` into a system prompt or project instruction.
3. Manual. Open the `SKILL.md`, follow the workflow yourself or hand it to any LLM with the prompt "use this skill on the following draft."

For the pre-seed suite specifically, copy all seven `preseed-*` folders into `~/.claude/skills/`, then run `/preseed-campaign setup` to initialize the workspace.

## Adding a new skill

1. Create a new folder at the repo root named after the skill (lowercase, hyphenated).
2. Add a `SKILL.md` with YAML frontmatter (`name`, `description`) at the top.
3. Update this README under "Skills in this repo."
4. Commit with a message like `add <skill-name> skill`.

## License

Personal use. Not licensed for commercial redistribution at this time. Contact me if you want to use these in another product.
