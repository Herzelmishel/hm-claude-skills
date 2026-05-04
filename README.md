# HM Claude Skills

A collection of personal Claude skills built by Herzel Mishel. Each skill is a self-contained folder with a `SKILL.md` file and any supporting scripts, references, or assets it needs.

## Skills in this repo

- `humanizer/` - Rewrites drafts to sound human, not AI. Strips em dashes, fake depth, rule-of-three padding, and flat rhythm. Adds opinion, specificity, and rhythm variation. Useful for LinkedIn posts, cold emails, blog posts, investor updates, and founder content.

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

## Adding a new skill

1. Create a new folder at the repo root named after the skill (lowercase, hyphenated).
2. Add a `SKILL.md` with YAML frontmatter (`name`, `description`) at the top.
3. Update this README under "Skills in this repo."
4. Commit with a message like `add <skill-name> skill`.

## License

Personal use. Not licensed for commercial redistribution at this time. Contact me if you want to use these in another product.
