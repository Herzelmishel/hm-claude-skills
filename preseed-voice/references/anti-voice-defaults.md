# Anti-Voice Defaults

Default banned phrases for `~/fundraising/.sys/anti-voice.txt`. Copied
once at `/preseed-campaign setup`. Append samples-derived bans below the
defaults — `build_voice_fingerprint.py` adds them automatically.

These phrases are the most common "AI tells" — generic openers, hollow
intensifiers, business-school hedges. They make outreach feel like a
template even when the rest of the message is good.

## Why each category is banned

- **Generic openers** ("I hope this email finds you well", "I'm reaching
  out because", "Just following up", "Circling back", "Touching base"):
  signal that the sender hasn't read the recipient's recent work and is
  blasting at scale. Investors pattern-match these instantly.
- **Hedged intent** ("I would love to", "It would be great to", "I
  wanted to reach out"): low-conviction phrasing. Pre-seed investors are
  betting on conviction. Lead with the ask, not your hope of one.
- **Stuffy connectives** ("Moreover", "Furthermore", "In addition"):
  the cadence of a freshman essay, not a founder email. A new line and
  a short sentence does the same job.
- **Buzzwords** ("leveraging", "synergy", "ecosystem", "world-class",
  "best-in-class", "game-changer"): hollow intensifiers. They mean the
  writer hasn't said the actual thing — what number, which customer,
  which mechanism.

## Format

The script that loads this file looks for the `## Phrases` marker and
extracts each subsequent line that starts with `- `. Inline comments
after `  #` are stripped. Quotes are stripped. Empty lines are ignored.

Order does not matter. Case is preserved here but matched
case-insensitively at runtime.

## Phrases

- I hope this email finds you well
- I hope this finds you well
- I hope you're doing well
- I hope you are doing well
- I wanted to reach out
- I'm reaching out because
- I am reaching out because
- I would love to
- I'd love to chat
- It would be great to
- It would be amazing to
- Just following up
- Just wanted to follow up
- Circling back
- Touching base
- Hope you're well
- Hope all is well
- Quick question
- Pick your brain
- Moreover
- Furthermore
- In addition
- leveraging
- synergy
- synergies
- ecosystem
- world-class
- best-in-class
- game-changer
- game changer
- next-generation
- cutting-edge
- bleeding-edge
- revolutionary
- disruptive
- thought leader
- thought leadership
- holistic
- low-hanging fruit
- move the needle
- ground-breaking
- groundbreaking
- paradigm shift
- value-add
- at the end of the day
- in today's fast-paced world
- in the dynamic landscape of
- in an ever-evolving
- as you may know
- as you are aware
- as a leader in
- I trust this finds you
- I trust you are well
- Per my last email
- As per our previous conversation
- Looking forward to hearing back
- Looking forward to your response
- Please find attached
- Kindly find
- Kindly let me know
- Don't hesitate to reach out
- Feel free to reach out

## Notes

This list is intentionally aggressive — better to flag a borderline
phrase and let the user override than to ship a generic email.

`validate_outreach.py` reads `~/fundraising/.sys/anti-voice.txt` (not
this file directly). The workspace copy is editable.

Add personal bans by editing `~/fundraising/.sys/anti-voice.txt`
below the `## samples` marker after running `/preseed-voice`.
