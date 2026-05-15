---
name: brand-docs
description: Apply consistent HycosAI/Agentis brand identity to every document you create — Word docs, PowerPoint decks, and PDFs. Loads ~/brand/brand-system.yaml and enforces colors, fonts, header/footer, table styles, and layout. Use when creating or auditing any business document. Trigger: /brand-docs [setup|doc|deck|pdf|audit]
origin: ECC
trigger: /brand-docs
argument-hint: "[setup | doc <title> | deck <title> | pdf <title> | audit <file>]"
---

# Brand Docs

Every document you create should look like it came from the same place. This skill loads your brand system and enforces it across Word docs, PowerPoint decks, and PDFs — same fonts, same colors, same header/footer, same table style, every time.

Brand tokens live in `~/brand/brand-system.yaml`. The HycosAI/Agentis brand is pre-loaded. Run `/brand-docs setup` only when you want to update or review the tokens.

## When to Activate

- User asks to create a document, proposal, brief, overview, report, or deck
- User asks to create a PDF, Word doc, or PowerPoint presentation
- User says "make it look branded" or "apply our brand"
- User runs `/brand-docs [subcommand]`
- Any document creation request when `~/brand/brand-system.yaml` exists

## Brand System

Always load `~/brand/brand-system.yaml` before creating any document. If the file is missing, stop and tell the user: "Brand file not found at ~/brand/brand-system.yaml. Run /brand-docs setup to create it."

The brand defines:
- **Colors**: h1 (dark navy), h2 (medium blue), accent, table headers, body text, muted
- **Typography**: font family, sizes per heading level, body, footer
- **Layout**: page size, margins, header/footer templates, cover page structure
- **Tables**: header row styling, first-column bold rule
- **Style rules**: what never to do (in the `never_do` list)

## Modes

### `/brand-docs setup`

Update or review brand tokens interactively.

1. Read `~/brand/brand-system.yaml` if it exists — show current values
2. Ask which tokens the user wants to change (or confirm all are correct)
3. Write updated values back to `~/brand/brand-system.yaml`
4. Confirm: "Brand system saved. All future documents will use these values."

If the file does not exist, run the full brand discovery:
1. Ask: do you have a logo, colors, fonts, or a reference document?
2. Walk through each token section (identity → colors → typography → layouts → tables)
3. Ask one question per section with a concrete default to accept or override
4. Save to `~/brand/brand-system.yaml`

### `/brand-docs doc <title>`

Create a branded Word document using `mcp__Word__By_Anthropic__*`.

**Workflow:**
1. Load `~/brand/brand-system.yaml`
2. Ask for content outline if not provided
3. Create `.docx` via `mcp__Word__By_Anthropic__create_document`
4. Add cover page: logo placeholder (top-left), large centered title, italic subtitle, doc metadata footer
5. For each section: insert H1 heading (h1 color, bold, numbered), H2 subheadings (h2 color, bold), body paragraphs
6. Apply header to every content page: logo + doc label (right side)
7. Apply footer to every content page: "Confidential. [Month Year]. | Page {N} of {TOTAL}"
8. For tables: set header row to table_header_bg with white bold text; first column bold
9. Save and deliver the file path

**Typography enforcement (Word styles):**
- All text: font = brand `typography.font`
- H1: size = `h1_size`, bold, color = `colors.h1`
- H2: size = `h2_size`, bold, color = `colors.h2`
- Body: size = `body_size`, color = `colors.body_text`
- Footer text: size = `footer_size`, color = `colors.muted`

### `/brand-docs deck <title>`

Create a branded PowerPoint using `mcp__PowerPoint__By_Anthropic__*`.

**Workflow:**
1. Load `~/brand/brand-system.yaml`
2. Ask for slide outline if not provided (or accept content passed inline)
3. Create `.pptx` via `mcp__PowerPoint__By_Anthropic__create_presentation`
4. Slide 1 (Title slide): large centered title (h1 color), italic subtitle (accent color), logo bottom-right, background white
5. Content slides: slide title in h1 color bold, body in body_text color, HycosAI logo small in bottom-right
6. Table slides: header row in table_header_bg with white text; data rows white with body_text
7. Save and deliver the file path

**Slide layout rules:**
- Aspect ratio: 16:9
- Title font size: 28pt, bold, h1 color
- Body font size: 18pt, regular, body_text color
- Footer: page number bottom-right, small, muted color
- Logo: bottom-right corner, every slide

### `/brand-docs pdf <title>`

Create a branded PDF by building HTML with inline brand CSS, then rendering.

**Workflow:**
1. Load `~/brand/brand-system.yaml`
2. Build full HTML document with:
   - `<style>` block embedding all brand tokens as CSS variables
   - Page header (logo + doc label) using CSS `@page` or fixed header div
   - Cover page structure matching the reference doc
   - H1, H2, body, table, blockquote styles all using brand tokens
3. Render to PDF via `mcp__Claude_Preview__preview_start` + screenshot, or via `nutrient-document-processing` HTML→PDF if available
4. Deliver the PDF path

**HTML CSS template (apply brand tokens):**
```css
:root {
  --color-h1: /* colors.h1 */;
  --color-h2: /* colors.h2 */;
  --color-accent: /* colors.accent */;
  --color-body: /* colors.body_text */;
  --color-muted: /* colors.muted */;
  --font: /* typography.font */, sans-serif;
}
body { font-family: var(--font); font-size: /* body_size */pt; color: var(--color-body); }
h1 { color: var(--color-h1); font-size: /* h1_size */pt; font-weight: 700; }
h2 { color: var(--color-h2); font-size: /* h2_size */pt; font-weight: 700; }
table thead tr { background: var(--color-h1); color: #fff; font-weight: 700; }
blockquote { border-left: 4px solid var(--color-h2); padding-left: 12px; font-style: italic; }
```

### `/brand-docs audit <file_path>`

Check an existing document against the brand system.

**Workflow:**
1. Load `~/brand/brand-system.yaml`
2. Read the document (use PDF/Word MCP tools or text extraction)
3. Score 5 dimensions (0–10 each):
   - **Font consistency** — is Calibri (or brand font) used throughout?
   - **Color accuracy** — do headings use the correct hex values?
   - **Header/footer** — present on every content page with correct template?
   - **Table styling** — correct header row color and white text?
   - **Logo presence** — HycosAI logo visible in header or cover?
4. Report: score per dimension, specific mismatches with exact fixes, overall pass/fail (pass = all ≥ 7)

## Quality Gates

Before delivering any document:
- [ ] Font is `typography.font` — no other fonts
- [ ] H1 headings are `colors.h1`, H2 are `colors.h2`
- [ ] Header appears on every content page (not cover)
- [ ] Footer appears on every content page with page numbers
- [ ] Tables have dark header row with white text
- [ ] No gradients, no shadows, no centered body text
- [ ] `never_do` list fully respected

## Persistence Rules

- Always read `~/brand/brand-system.yaml` fresh at the start of every document creation — never cache in memory
- Never hardcode brand values in responses; always derive from the YAML
- Output documents to `~/Documents/` unless the user specifies a different path
- After creating a document, show the file path and a one-line summary of brand rules applied
