# Brand Discovery Setup Prompt

Use this when `/brand-docs setup` is called and no `~/brand/brand-system.yaml` exists yet,
or when the user wants to start from a reference document.

---

## Step 1 — Discover what the user has

Ask:

> "Let's set up your brand system. Do you have any of the following?
> 1. A logo file (PNG/SVG)
> 2. A reference document that already looks the way you want
> 3. Brand colors you know (hex codes, or describe them)
> 4. A preferred font
> 5. Starting from scratch
>
> Tell me which ones apply, or just share files/links."

Then branch:

- **Has reference doc or URL** → extract brand DNA from it (see Extraction below)
- **Has colors/fonts only** → fill in what's known, ask for the rest
- **Starting from scratch** → show 4 style directions (see Style Directions below)

---

## Step 2 — Brand DNA Extraction (from reference doc)

If the user provides a Google Doc, Word doc, PDF, or URL:

1. Open/read the document
2. Extract and record:
   - All fonts used (confirm the primary font)
   - All hex colors used (group by: headings / subheadings / body / accents / table headers)
   - Page header structure (logo position, label text pattern)
   - Page footer structure (confidentiality text, page numbering)
   - Cover page layout (centered title, subtitle style, metadata position)
   - Table header styling (background color, text color, bold?)
   - Any callout/blockquote styling (border color, italic?)
3. Present findings to user:
   > "Here's what I extracted from your document:
   > - Font: [detected font]
   > - H1 color: [hex] ([name])
   > - H2 color: [hex] ([name])
   > [etc.]
   > Does this look right? Anything to change?"
4. On confirmation → write to `~/brand/brand-system.yaml`

---

## Step 3 — Style Directions (starting from scratch)

Show 4 distinct aesthetic options as text descriptions. Ask the user to pick one or describe a mix:

**Option A — Executive / Boardroom**
- Colors: dark navy (#1F2D4A), charcoal (#333333), gold accent (#C9A84C)
- Font: Georgia (headings) + Calibri (body)
- Tone: formal, numbered sections, table-heavy

**Option B — Startup / Tech**
- Colors: near-black (#0D0D0D), electric blue (#0066FF), light gray (#F5F5F5)
- Font: Inter (headings) + Inter (body)
- Tone: minimal, bold headers, generous whitespace

**Option C — Consultant / Advisory**
- Colors: deep teal (#1A4D5C), warm gray (#6B6B6B), white
- Font: Garamond (headings) + Calibri (body)
- Tone: professional, callouts, subtle left-border quotes

**Option D — Brand / Creative**
- Colors: rich burgundy (#6B1B2A), warm cream (#FAF7F2), forest green (#2D5016)
- Font: Playfair Display (headings) + Lato (body)
- Tone: editorial, image-forward, centered titles

---

## Step 4 — Token Collection (one section at a time)

Walk through these questions in order, showing defaults in brackets:

1. **Identity**: "What is your brand/company name? Do you have a logo file to upload?"
2. **Primary color (H1)**: "What color for main headings? [current or suggested value]"
3. **Secondary color (H2)**: "What color for subheadings? [current or suggested value]"
4. **Font**: "What font? (must be available in Word/PowerPoint) [Calibri]"
5. **Page size**: "A4 or Letter? [A4]"
6. **Footer text pattern**: "Footer template? ['Confidential. [Month Year]. | Page {N} of {TOTAL}']"
7. **Tone/style notes**: "Anything specific to always do or never do?"

---

## Step 5 — Save

Write the completed YAML to `~/brand/brand-system.yaml`.

Confirm to user:
> "Your brand system is saved at ~/brand/brand-system.yaml.
> From now on, every document you ask me to create will use:
> - Font: [font]
> - Heading colors: [h1] / [h2]
> - Page size: [size]
> - Header: [brand] logo + doc label
> - Footer: [footer template]
>
> Run /brand-docs setup any time to update these values."
