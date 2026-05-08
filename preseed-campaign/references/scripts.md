# Script Execution Order & Error Format

Seed template. Copied to `~/fundraising/.sys/scripts.yaml` at setup.

## Error Envelope

All scripts that can fail emit JSON to stdout on error, exit code 1:

```json
{
  "error": "Missing required field",
  "field": "linkedin_profile_url",
  "fix": "Add LinkedIn URL to row 12 of investors.csv",
  "file": "investors/investors.csv",
  "line": 13
}
```

On success: exit code 0, JSON to stdout if there's structured output, otherwise no stdout.

## Execution Order Per Skill

### setup (preseed-campaign)
```
1. build_campaign.py     — creates directory tree + .sys/ + campaign.yaml + GETTING-STARTED.md
2. (optional) validate_round_brief.py — only if story/round-brief.yaml exists
```

### wave (preseed-campaign)
```
1. validate_round_brief.py
2. validate_investors_csv.py
3. momentum_check.py     — if STALLED, stop here
4. select wave (in-skill logic, no script)
5. update campaign.yaml
```

### review (preseed-campaign)
```
1. campaign_summary.py   — writes pipeline/weekly-summary.md
2. warm_list.py          — writes pipeline/warm-list.md
3. ghost_check.py        — flags 14+ day silences
4. momentum_check.py     — updates momentum_score in campaign.yaml
```

### diagnose (preseed-campaign)
```
1. campaign_summary.py   — fresh conversion math
2. momentum_check.py     — fresh momentum
3. (in-skill) bottleneck matrix application
```

### close (preseed-campaign)
```
1. (in-skill) read commitments.csv, compute totals + aging
2. (in-skill) write soft-circle-map.md
```

### preseed-story
```
1. validate_round_brief.py — after writing round-brief.yaml
```

### preseed-voice
```
1. build_voice_fingerprint.py — reads voice/samples/, writes voice-fingerprint.yaml
2. (validation in-skill)
```

### preseed-prospect
```
1. (in-skill) generate candidate list
2. score_investors.py
3. validate_investors_csv.py
```

### preseed-outreach
```
1. (in-skill) generate messages
2. count_message_chars.py
3. validate_outreach.py — includes anti-voice check + voice score
4. score_voice_match.py — runs per message
```

### preseed-prep
```
(no scripts — pure model work backed by file reads)
```

### preseed-pipeline
```
update mode:
  1. update_pipeline.py    — applies status change, appends to touches.csv
  2. ghost_check.py        — re-runs ghost detection
  3. (if status=pass) reapproach_notes.py

weekly-review mode:
  1. campaign_summary.py
  2. warm_list.py
  3. ghost_check.py

warm-list mode:
  1. warm_list.py only
```

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Validation failed (envelope explains) |
| 2 | Required input file missing |
| 3 | Required dependency missing (e.g. PyYAML not installed) |
| 4 | Unsafe operation refused (e.g. attempting to overwrite touches.csv) |

## Fallback Behavior

If a script fails:
1. The skill SHOULD surface the error envelope to the user verbatim
2. The skill MUST NOT silently continue
3. The skill MAY suggest the manual equivalent (e.g. "open `investors.csv` and check row 12")
4. The skill MUST wait for the user to fix and re-run

If a script is missing entirely:
1. Tell the user the script path
2. Suggest re-running `/preseed-campaign setup` to restore
3. Do not proceed without it

## Logging

Scripts SHOULD NOT write logs to stdout/stderr unless they are the structured error envelope. Verbose logs go to:

```
~/fundraising/.sys/logs/[script_name]-YYYY-MM-DD.log
```

This keeps the model's output clean.
