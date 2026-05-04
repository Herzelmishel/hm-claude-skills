---
name: humanizer
description: Rewrite drafts so they read like a human wrote them, not AI. Use this skill whenever the user asks to rewrite, polish, humanize, de-AI, soften, or fix the tone of any piece of writing. Especially trigger on LinkedIn posts, cold emails, blog posts, investor updates, founder content, and marketing copy. Also trigger when the user shares a draft and says it "sounds off," "sounds like AI," "feels robotic," or "needs more voice," even when they do not explicitly ask for humanizing. The skill strips AI tells like em dashes, fake depth, rule-of-three padding, and flat rhythm, and adds opinion, specificity, and rhythm variation while preserving meaning.
---

# Humanizer

Strip AI tells from writing. Add what AI leaves out. Keep the meaning intact.

## Why this exists

LLMs have a default cadence. Medium-medium-medium sentences. Em dashes. Rule of three. Vague depth without commitment. Readers spot the pattern in seconds in 2026. This skill rewrites drafts so they read like a real person wrote them, with opinions, rhythm, and specifics.

## Core workflow

Run two passes, then a self-check, then one final revision.

- Pass 1: Voice. Add what AI leaves out.
- Pass 2: Tells. Scan for the four families and rewrite anything that matches.
- Self-check: answer four questions in one line each.
- Final revision: apply what the self-check surfaced.

## Severity dial

Match the edit depth to the context.

- Light: investor updates, board memos, contracts, formal docs. Cut the worst tells (em dashes, fake depth, sycophancy) but keep professional structure. Do not add first person if it is not already there.
- Medium: LinkedIn posts, blog intros, sales emails, partner outreach. Add voice. Vary rhythm. Cut all four families. First person is fine where it fits.
- Heavy: founder posts, contrarian takes, personal essays, hot takes. Push opinions. Lean into first person. Add concrete specifics. Break smooth cadence on purpose.

Default to medium when unclear. If context is ambiguous and a wrong call would damage the piece, ask the user one question before starting.

## Pass 1: Voice catalog

Things AI drafts skip. Add them back.

Opinions over reporting.

- Before: The new pricing model has been generally well received.
- After: The new pricing finally makes sense for solo users. For teams of 20+, it is still a tough sell.

Rhythm variation. Default AI cadence is medium-medium-medium. Mix in short and long.

- Before: The dashboard provides analytics. Users can view metrics. The interface is responsive.
- After: The dashboard works. It is not pretty, and the filtering needs help, but the core analytics load fast and that is what matters.

First person where it fits.

- Before: It can be observed that the integration occasionally fails.
- After: I have watched the integration fail twice this week. Same error both times.

Specific over abstract.

- Before: Performance has improved significantly.
- After: Page load dropped from 4.2s to 1.6s after the rewrite.

Mixed feelings where they exist.

- Before: The feature is a clear win.
- After: The feature ships what we promised. It also doubles our infra cost, which I am still not sure was worth it.

## Pass 2: Tells catalog

Four families. Cut or rewrite anything matching.

### Family 1: Inflated importance

Words and phrases to flag: stands as, testament, pivotal, underscores, reflects broader, evolving landscape, key turning point, leading expert, widely discussed, vibrant, seamless, breathtaking, renowned, unlock, empower.

- Before: The acquisition stands as a pivotal moment, reflecting broader shifts in the AI tooling landscape.
- After: The acquisition was Notion's biggest yet. It also got them a calendar product they had been trying to build for two years.

- Before: This powerful platform offers a seamless and intuitive experience to help teams unlock their potential.
- After: The platform replaces three tools: Slack reminders, Notion task lists, and a shared calendar. Teams use it because they can drop the other three.

Vague attribution belongs here too. "Experts argue" without a name is filler.

- Before: Experts believe this approach will reshape how engineering teams work.
- After: A 2024 GitHub study found teams using AI code review shipped 26% more PRs per week.

### Family 2: Fake depth

The most insidious family. The text sounds analytical without saying anything.

Watch for -ing endings doing fake-depth work: highlighting, emphasizing, ensuring, fostering, reflecting, contributing, reinforcing.

- Before: The redesign uses muted tones, creating a calmer experience and reinforcing the brand's premium positioning.
- After: The redesign uses muted tones. The designer told me he wanted it to feel less aggressive than the old neon palette.

Copula avoidance. The model dodges plain "is" and reaches for "serves as" or "plays a role."

- Before: The CRM serves as a central source of truth for all customer interactions.
- After: The CRM is where every customer interaction gets logged. Calls, emails, support tickets, all in one place.

Rule of three. The AI's favorite cadence. Sometimes three is right. Often two is better and three is padding.

- Before: The tool saves time, reduces errors, and improves collaboration.
- After: The tool catches errors before they ship. That is most of the value.

Negative parallelism. "Not just X but also Y" is overused enough to be a tell.

- Before: It is not just about speed, it is about reliability.
- After: Speed matters. Reliability matters more.

### Family 3: Cosmetic tells

Surface stuff. Easy to fix, immediately spotted by readers.

- Em dashes everywhere. Use commas or periods. Em dashes are a strong AI signal in 2026.
- Bold for no reason. Just write the sentence plainly.
- Title case headings. Use sentence case. "Product features and benefits," not "Product Features And Benefits."
- Emojis. Drop them.
- Curly quotes. Use straight quotes. Curly quotes come from Word and from AI.
- Inline-header lists ("Speed: faster load times. Security: better encryption."). Rewrite as prose.
- Elegant variation. "The app is slow. The application crashes." Pick one word and stick with it.
- False ranges. "Everything from solo founders to Fortune 500 companies." Almost always overstated. Be specific about who actually uses it.

### Family 4: Conversational artifacts

These give away the chat origin.

Chatbot framing.

- Before: Here is a breakdown of the process. Let me know if you would like me to expand on any step.
- After: The process has three steps: ingest, transform, load.

Knowledge-cutoff hedges.

- Before: While details are limited, the feature appears to have launched recently.
- After: The feature launched in March 2026.

Sycophancy.

- Before: Great question, this is a really thoughtful observation.
- After: Just answer.

Filler phrases. "In order to," "has the ability to," "it should be noted that."

- Before: In order to improve performance, the system has the ability to process data in parallel.
- After: To improve performance, the system processes data in parallel.

Excessive hedging. "May potentially," "could possibly," "might tend to."

- Before: This could potentially lead to reduced churn over time.
- After: This should reduce churn.

Generic conclusions.

- Before: Overall, the outlook is positive and the team is well-positioned for continued growth.
- After: The team plans to ship the mobile app in Q3 and double the eng team by end of year.

## Self-check

After Pass 2, answer all four in one line each. Be specific. Cite the exact phrase or sentence.

1. Where is the rhythm still flat? Look for three or more medium-length sentences in a row.
2. Where am I still describing instead of taking a position?
3. Which abstractions still do not have a concrete number, name, or detail behind them?
4. What single phrase would still tip a reader off that this is AI?

Use the answers to do one final pass.

## When not to humanize

Skip or go very light when any of these are true.

- The piece is a legal document, contract, or compliance text. Plain corporate voice is the point.
- The user pasted text from a known author and wants edits inside their voice. Match the existing voice rather than imposing humanizer defaults.
- The piece is technical documentation where precision beats personality.
- The user asked for a specific tone (formal, academic, ceremonial) that conflicts with humanizer defaults. Their explicit request wins.
- The draft is already strong and the user just wants a light proof. Do not force voice changes the draft does not need.

If unsure, ask the user one question about context before applying.

## Output format

Return three things in this order. Use these exact section labels.

1. Draft rewrite. The first pass with Voice and Tells fixed.
2. Audit. The four self-check answers, one line each.
3. Final rewrite. The revision based on the audit.

Do not include commentary or explanation outside these three sections unless the user asks.
