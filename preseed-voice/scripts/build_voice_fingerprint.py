#!/usr/bin/env python3
"""build_voice_fingerprint.py — extract a structural + lexical voice
fingerprint from raw writing samples.

Reads:
  ~/fundraising/voice/samples/*.txt
  ~/fundraising/voice/samples/*.md

Writes:
  ~/fundraising/voice/voice-fingerprint.yaml   (machine-readable)
  ~/fundraising/voice/founder-voice.md         (human-readable do/don't)
  ~/fundraising/voice/voice-examples.md        (AI default vs founder voice)

Appends:
  ~/fundraising/.sys/anti-voice.txt (samples-derived bans below ## samples)

Stdlib only — re, statistics, collections.Counter.

Exit codes:
  0  success
  1  failure (envelope on stdout)
  2  required input missing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

def fail(error: str, *, field: str = "", fix: str = "", file: str = "",
         code: int = 1) -> None:
    envelope = {"error": error, "field": field, "fix": fix}
    if file:
        envelope["file"] = file
    print(json.dumps(envelope))
    sys.exit(code)


# ---------------------------------------------------------------------------
# Default banned phrases (fallback if anti-voice.txt is missing)
# ---------------------------------------------------------------------------

FALLBACK_BANNED = [
    "I hope this email finds you well",
    "I hope you're doing well",
    "I wanted to reach out",
    "I'm reaching out because",
    "I would love to",
    "It would be great to",
    "Just following up",
    "Circling back",
    "Touching base",
    "Hope you're well",
    "Pick your brain",
    "Moreover",
    "Furthermore",
    "In addition",
    "leveraging",
    "synergy",
    "ecosystem",
    "world-class",
    "best-in-class",
    "game-changer",
]


def load_default_bans(workspace: Path, skill_root: Path) -> list[str]:
    """Prefer the workspace anti-voice.txt; fall back to skill seed file."""
    workspace_anti = workspace / ".sys" / "anti-voice.txt"
    if workspace_anti.exists():
        return _parse_anti_voice_txt(workspace_anti)
    skill_anti = skill_root / "references" / "anti-voice-defaults.md"
    if skill_anti.exists():
        return _parse_anti_voice_md(skill_anti)
    return list(FALLBACK_BANNED)


def _parse_anti_voice_txt(path: Path) -> list[str]:
    """anti-voice.txt has phrases one per line, possibly under markers."""
    lines = path.read_text(encoding="utf-8").splitlines()
    phrases: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        # strip inline comment
        line = re.split(r"\s+#\s+", line, maxsplit=1)[0].strip()
        if line:
            phrases.append(line)
    return phrases


def _parse_anti_voice_md(path: Path) -> list[str]:
    """anti-voice-defaults.md uses `## Phrases` marker + `- ` lines."""
    text = path.read_text(encoding="utf-8")
    if "## Phrases" in text:
        text = text.split("## Phrases", 1)[1]
    phrases: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        phrase = line[2:].strip()
        phrase = re.split(r"\s+#\s+", phrase, maxsplit=1)[0].strip()
        if phrase:
            phrases.append(phrase)
    return phrases


# ---------------------------------------------------------------------------
# Sample loading
# ---------------------------------------------------------------------------

def load_samples(samples_dir: Path) -> list[tuple[str, str]]:
    """Return list of (filename, raw_text) tuples."""
    out: list[tuple[str, str]] = []
    if not samples_dir.exists():
        return out
    for path in sorted(samples_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if path.suffix.lower() == ".md":
            text = _strip_markdown(text)
        text = text.strip()
        if text:
            out.append((path.name, text))
    return out


def _strip_markdown(text: str) -> str:
    """Light-touch markdown stripping — keep prose, remove syntax."""
    # remove fenced code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # remove inline code
    text = re.sub(r"`[^`]+`", "", text)
    # remove headings markers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # remove bold/italic markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    # remove blockquote markers
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # convert links [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # bullet list markers at line start
    text = re.sub(r"^[\-\*\+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    return text


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
CONTRACTION_RE = re.compile(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", re.IGNORECASE)


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


# ---------------------------------------------------------------------------
# Structural features
# ---------------------------------------------------------------------------

def compute_avg_sentence_length(texts: list[str]) -> float:
    lengths: list[int] = []
    for t in texts:
        for s in split_sentences(t):
            wc = word_count(s)
            if wc > 0:
                lengths.append(wc)
    return round(mean(lengths), 2) if lengths else 0.0


def compute_contraction_rate(texts: list[str]) -> float:
    contractions = 0
    total_words = 0
    for t in texts:
        contractions += len(CONTRACTION_RE.findall(t))
        total_words += word_count(t)
    if total_words == 0:
        return 0.0
    # approximate verb-phrase candidates as words/6
    candidates = max(1, total_words // 6)
    rate = contractions / candidates
    return round(min(1.0, rate), 3)


def compute_paragraph_avg_sentences(texts: list[str]) -> float:
    counts: list[int] = []
    for t in texts:
        for p in split_paragraphs(t):
            n = len(split_sentences(p))
            if n > 0:
                counts.append(n)
    return round(mean(counts), 2) if counts else 0.0


def compute_em_dash_rate(texts: list[str]) -> float:
    total_chars = sum(len(t) for t in texts)
    if total_chars == 0:
        return 0.0
    occurrences = 0
    for t in texts:
        occurrences += t.count("—")  # em-dash
        occurrences += t.count("--")
    per_1k = occurrences / (total_chars / 1000) if total_chars > 0 else 0.0
    # 5 per 1000 chars = saturated
    return round(min(1.0, per_1k / 5), 3)


def extract_opener_patterns(texts: list[str], top_n: int = 3) -> list[str]:
    counter: Counter = Counter()
    for t in texts:
        sents = split_sentences(t)
        if not sents:
            continue
        first = sents[0].strip()
        normalized = re.sub(r"\s+", " ", first.lower())
        # opener = up to first boundary in first 6 words
        boundary = re.search(r"^([^,:—]+(?:[,:—]))", normalized)
        if boundary:
            opener = boundary.group(1).strip()
        else:
            words = normalized.split()
            opener = " ".join(words[:3]).strip()
        if opener:
            counter[opener] += 1
    # display as title-case-ish (preserve original case of first occurrence)
    top = counter.most_common(top_n)
    out: list[str] = []
    for opener, _count in top:
        # try to find original casing in any sample
        for t in texts:
            sents = split_sentences(t)
            if not sents:
                continue
            first = sents[0].strip()
            if first.lower().startswith(opener):
                out.append(first[: len(opener)])
                break
        else:
            out.append(opener)
    return out


def extract_closer_patterns(texts: list[str], top_n: int = 3) -> list[str]:
    counter: Counter = Counter()
    for t in texts:
        sents = split_sentences(t)
        if not sents:
            continue
        last = sents[-1].strip()
        # only short closers (<=4 words) are useful as patterns
        wc = word_count(last)
        if wc > 8:
            continue
        normalized = re.sub(r"\s+", " ", last)
        counter[normalized] += 1
    return [c for c, _ in counter.most_common(top_n)]


# ---------------------------------------------------------------------------
# Lexical features
# ---------------------------------------------------------------------------

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on",
    "for", "with", "as", "at", "by", "is", "are", "was", "were", "be",
    "been", "being", "it", "its", "this", "that", "these", "those", "i",
    "you", "we", "they", "he", "she", "him", "her", "them", "us", "my",
    "your", "our", "their", "his", "hers",
}


def extract_signature_phrases(texts: list[str], min_doc_count: int = 2,
                              min_total: int = 3) -> list[str]:
    """N-gram (3-5) phrases that recur across multiple documents."""
    candidates: dict[str, dict] = {}  # phrase -> {"total": int, "docs": set}

    for idx, t in enumerate(texts):
        # tokenize on word boundaries, lowercase
        tokens = [w.lower() for w in WORD_RE.findall(t)]
        for n in (3, 4, 5):
            for i in range(len(tokens) - n + 1):
                gram = tuple(tokens[i:i + n])
                # skip if all stopwords
                if all(w in STOPWORDS for w in gram):
                    continue
                # skip if entirely punctuation/short tokens
                if all(len(w) <= 2 for w in gram):
                    continue
                key = " ".join(gram)
                rec = candidates.setdefault(
                    key, {"total": 0, "docs": set()}
                )
                rec["total"] += 1
                rec["docs"].add(idx)

    # filter
    surviving = [
        (phrase, rec["total"])
        for phrase, rec in candidates.items()
        if len(rec["docs"]) >= min_doc_count and rec["total"] >= min_total
    ]
    surviving.sort(key=lambda x: (-x[1], x[0]))
    return [p for p, _ in surviving[:5]]


def classify_register(texts: list[str], avg_sent: float,
                      contraction_rate: float) -> str:
    haystack = " ".join(texts).lower()
    casual_markers = (
        " honestly", " look,", " fwiw", " tbh", " ngl", " obviously",
    )
    has_casual = any(m in haystack for m in casual_markers)

    # technical_terse: short sentences AND code-like density
    code_like = (
        len(re.findall(r"\b\d+\.\d+\.\d+\b", haystack)) +  # version
        len(re.findall(r"[/][a-z\-_]+(?:[/][a-z\-_]+)+", haystack)) +  # path
        len(re.findall(r"\b[A-Z_]{3,}\b", " ".join(texts))) +  # CONSTS
        len(re.findall(r"\$[A-Za-z]+", haystack))  # vars
    )
    total_tokens = sum(word_count(t) for t in texts) or 1
    code_density = code_like / total_tokens

    if avg_sent > 0 and avg_sent < 14 and code_density > 0.005:
        return "technical_terse"
    if contraction_rate > 0.4 and avg_sent < 16 and has_casual:
        return "casual_direct"
    if 14 <= avg_sent <= 22 and 0.15 <= contraction_rate <= 0.4 \
            and ("please " in haystack or "thanks" in haystack) \
            and "i hope this finds you well" not in haystack:
        return "formal_warm"
    return "casual_direct" if contraction_rate > 0.3 else "formal_warm"


def compute_technical_density(texts: list[str]) -> float:
    total = sum(word_count(t) for t in texts) or 1
    technical = 0
    haystack = " ".join(texts)
    technical += len(re.findall(r"\b\d+(?:[\.,]\d+)?%?\b", haystack))
    technical += len(re.findall(r"\$\d", haystack))
    technical += len(re.findall(r"\b[A-Z]{2,}\b", haystack))
    technical += len(re.findall(r"\b\d+\s*(?:ms|s|kb|mb|gb|tb|x)\b",
                                haystack, re.IGNORECASE))
    return round(technical / total, 4)


# ---------------------------------------------------------------------------
# Anti-voice extraction
# ---------------------------------------------------------------------------

def compute_banned_personal(texts: list[str], default_bans: list[str]
                            ) -> list[str]:
    """Default phrases that NEVER appear in samples — safely banned."""
    haystack = " ".join(texts).lower()
    out: list[str] = []
    for phrase in default_bans:
        if phrase.lower() not in haystack:
            out.append(phrase)
    return out


def preferred_alternatives() -> dict:
    """Static AI-default → Herzel-equivalent map.

    Future versions could derive this from samples (e.g., what does the
    user say instead of "circling back" when they pick something up).
    For now, ship a reasonable default that the user can edit.
    """
    return {
        "I wanted to reach out": "Quick one — ",
        "Just following up": "Update on this:",
        "Circling back": "Picking this back up:",
        "I hope this email finds you well": "Quick note:",
        "Touching base": "Update:",
        "leveraging": "using",
        "synergy": "fit",
        "world-class": "real",
    }


# ---------------------------------------------------------------------------
# YAML output
# ---------------------------------------------------------------------------

def yaml_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if s == "" or re.search(r"[:#\n]", s) or s.strip() != s \
            or s.lower() in {"yes", "no", "true", "false", "null"}:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def render_fingerprint_yaml(fp: dict) -> str:
    lines: list[str] = []
    lines.append("# voice-fingerprint.yaml — generated by build_voice_fingerprint.py")
    lines.append(f"# generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    scalar_keys = [
        "sample_count", "avg_sentence_length_words", "contraction_rate",
        "paragraph_avg_sentences", "em_dash_rate", "register",
        "technical_density", "voice_score_threshold", "confidence",
    ]
    for k in scalar_keys:
        if k in fp:
            lines.append(f"{k}: {yaml_scalar(fp[k])}")

    list_keys = [
        "opener_patterns", "closer_patterns", "signature_phrases",
        "banned_default", "banned_personal",
    ]
    for k in list_keys:
        items = fp.get(k) or []
        lines.append(f"{k}:")
        if not items:
            lines.append("  []")
            continue
        for item in items:
            lines.append(f"  - {yaml_scalar(item)}")

    alt = fp.get("preferred_alternatives") or {}
    lines.append("preferred_alternatives:")
    if not alt:
        lines.append("  {}")
    for k, v in alt.items():
        lines.append(f"  {yaml_scalar(k)}: {yaml_scalar(v)}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Markdown outputs
# ---------------------------------------------------------------------------

def render_founder_voice_md(fp: dict, sample_files: list[str]) -> str:
    confidence = fp.get("confidence", "low")
    sample_count = fp.get("sample_count", 0)

    out: list[str] = []
    out.append("# Founder Voice — Herzel")
    out.append("")
    out.append(
        f"Generated from {sample_count} sample(s). Confidence: **{confidence}**."
    )
    out.append("")

    if confidence == "low":
        out.append("> **WARNING:** Fewer than 3 samples were available. The")
        out.append("> fingerprint is using defaults for missing patterns.")
        out.append("> Drop more samples into `voice/samples/` and re-run for")
        out.append("> a stronger fingerprint.")
        out.append("")

    out.append("## Quick reference")
    out.append("")
    out.append("| Metric | Value |")
    out.append("|---|---|")
    out.append(f"| Avg sentence length | {fp.get('avg_sentence_length_words')} words |")
    out.append(f"| Contraction rate | {fp.get('contraction_rate')} |")
    out.append(f"| Paragraph avg sentences | {fp.get('paragraph_avg_sentences')} |")
    out.append(f"| Em-dash rate | {fp.get('em_dash_rate')} (0–1) |")
    out.append(f"| Register | {fp.get('register')} |")
    out.append(f"| Technical density | {fp.get('technical_density')} |")
    out.append(f"| Voice-score threshold | {fp.get('voice_score_threshold')} |")
    out.append("")

    out.append("## Do")
    out.append("")
    openers = fp.get("opener_patterns") or []
    if openers:
        out.append("**Open with one of these patterns:**")
        for o in openers:
            out.append(f"- `{o}`")
        out.append("")
    closers = fp.get("closer_patterns") or []
    if closers:
        out.append("**Close with:**")
        for c in closers:
            out.append(f"- `{c}`")
        out.append("")
    sigs = fp.get("signature_phrases") or []
    if sigs:
        out.append("**Signature phrases (use naturally):**")
        for s in sigs:
            out.append(f"- {s}")
        out.append("")

    out.append(f"- Target average sentence length: "
               f"{fp.get('avg_sentence_length_words')} words (±3)")
    out.append(f"- Match contraction rate ({fp.get('contraction_rate')}) — "
               "if your draft sounds stiff, add contractions")
    out.append(f"- Keep paragraphs around "
               f"{fp.get('paragraph_avg_sentences')} sentences")

    out.append("")
    out.append("## Don't")
    out.append("")
    out.append(
        "**Banned defaults — never use** "
        "(also enforced by `validate_outreach.py`):"
    )
    for phrase in (fp.get("banned_default") or [])[:15]:
        out.append(f"- {phrase}")
    out.append("")
    if fp.get("banned_personal"):
        out.append("**Personal bans — phrases never seen in your samples:**")
        for phrase in fp["banned_personal"][:10]:
            out.append(f"- {phrase}")
        out.append("")

    out.append("## Preferred swaps")
    out.append("")
    out.append("| Don't write | Write instead |")
    out.append("|---|---|")
    for k, v in (fp.get("preferred_alternatives") or {}).items():
        out.append(f"| {k} | {v} |")
    out.append("")

    out.append("## Source samples")
    out.append("")
    for f in sample_files:
        out.append(f"- `{f}`")
    out.append("")

    out.append("## How this is used")
    out.append("")
    out.append("`/preseed-outreach` loads `voice-fingerprint.yaml` automatically")
    out.append("before drafting any message. Drafts are scored 0–1 by")
    out.append("`score_voice_match.py`. Anything below the threshold gets")
    out.append("`needs_human_review = high` in `outreach.csv`. Banned phrases")
    out.append("hard-fail the draft.")
    return "\n".join(out) + "\n"


def render_voice_examples_md(fp: dict) -> str:
    avg = fp.get("avg_sentence_length_words", 14)
    opener = (fp.get("opener_patterns") or ["Quick update:"])[0]
    closer = (fp.get("closer_patterns") or ["— Herzel"])[0]

    out: list[str] = []
    out.append("# Voice Examples — AI default vs. Herzel voice")
    out.append("")
    out.append("Side-by-side rewrites for the most common message types.")
    out.append("Use these as anchors when drafting in `/preseed-outreach`.")
    out.append("")

    examples = [
        (
            "Connection note (LinkedIn, ≤200 chars)",
            (
                "Hi [Name], I hope this message finds you well. I wanted to "
                "reach out because I'm building an exciting AI startup in the "
                "ecommerce space and I would love to connect. Best regards."
            ),
            (
                f"{opener} saw your post on profit erosion at scale. "
                "We're building Agentis — real-time margin protection for "
                "mid-market ecom. Worth a connect?"
            ),
        ),
        (
            "First DM after accept",
            (
                "Thank you for connecting! I am reaching out to discuss a "
                "potential opportunity to leverage synergies between our "
                "ecosystems. Would love to schedule a quick call at your "
                "earliest convenience."
            ),
            (
                "Thanks for connecting. Quick context: Agentis spots margin "
                "leaks across pricing, promos, and returns in real time. Two "
                "Shopify Plus pilots running. Worth 15 min next week?"
            ),
        ),
        (
            "3-day follow-up (followup_3_day)",
            (
                "Just following up on my previous message. I wanted to "
                "circle back and see if you had any thoughts. Looking forward "
                "to hearing from you."
            ),
            (
                "Update — closed our second LOI yesterday ($4.2M GMV brand). "
                "Same margin-leak pattern as the first pilot. Still worth "
                "comparing notes if you have 15 min Tue/Wed?"
            ),
        ),
        (
            "Warm update (nurture, ~150 words)",
            (
                "Hope you're doing well! It's been a while since we last "
                "spoke. I wanted to reach out and provide an update on our "
                "progress. We have been making significant strides and "
                "leveraging cutting-edge AI to drive impact in the ecommerce "
                "ecosystem. Looking forward to your continued support."
            ),
            (
                f"{opener} two pilots live, $40k MRR, both Shopify Plus "
                "brands in sub-$10M GMV.\n\n"
                "What we're seeing: most margin leaks aren't pricing — "
                "they're return rates on promo orders. Customers we onboard "
                "are clawing back 1.8 points of gross margin in week one.\n\n"
                "Not pitching, just keeping you posted. If a 20-minute walk-"
                f"through would be useful, Wed or Thu work.\n\n{closer}"
            ),
        ),
        (
            "Takeaway email (anti-ghost, ≤80 words)",
            (
                "I hope this finds you well. I wanted to follow up one more "
                "time as I haven't heard from you. If you are still "
                "interested in moving forward, please let me know at your "
                "earliest convenience. Otherwise, I understand and wish you "
                "all the best in your future endeavors."
            ),
            (
                "Haven't heard back since we spoke. Pulling the allocation "
                "Friday unless you say otherwise. No hard feelings either "
                f"way — just need to be honest with the round.\n\n{closer}"
            ),
        ),
    ]

    for title, ai, herzel in examples:
        out.append(f"## {title}")
        out.append("")
        out.append("**AI default (don't):**")
        out.append("")
        out.append("> " + ai.replace("\n", "\n> "))
        out.append("")
        out.append("**Herzel voice (do):**")
        out.append("")
        out.append("> " + herzel.replace("\n", "\n> "))
        out.append("")

    out.append(f"_Target avg sentence length: {avg} words. Use opener "
               f"`{opener}` or one of the alternatives in "
               "`founder-voice.md`._")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# anti-voice.txt append
# ---------------------------------------------------------------------------

def append_anti_voice(workspace: Path, samples_bans: list[str]) -> None:
    path = workspace / ".sys" / "anti-voice.txt"
    if not path.exists():
        # ensure parent exists
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# anti-voice phrases\n## defaults\n## samples\n",
            encoding="utf-8",
        )

    existing = path.read_text(encoding="utf-8")
    existing_phrases = set(p.lower() for p in _parse_anti_voice_txt(path))

    new_phrases = [
        p for p in samples_bans
        if p and p.lower() not in existing_phrases
    ]
    if not new_phrases:
        return

    # ensure ## samples marker exists
    if "## samples" not in existing:
        existing = existing.rstrip() + "\n\n## samples\n"

    # split at marker, append
    head, _, tail = existing.partition("## samples")
    appended = "## samples" + tail.rstrip() + "\n"
    appended += "# Added by build_voice_fingerprint.py "
    appended += datetime.now(timezone.utc).strftime("%Y-%m-%d") + "\n"
    for p in new_phrases:
        appended += p + "\n"
    path.write_text(head + appended, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build the founder voice fingerprint from samples."
    )
    parser.add_argument(
        "--samples-dir",
        type=Path,
        default=None,
        help="Override samples directory.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Override workspace root (default: ~/fundraising).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="voice_score_threshold to embed (default 0.7).",
    )
    args = parser.parse_args(argv)

    workspace = args.workspace if args.workspace else (
        Path.home() / "fundraising"
    )
    samples_dir = args.samples_dir if args.samples_dir else (
        workspace / "voice" / "samples"
    )
    skill_root = Path(__file__).resolve().parent.parent

    if not samples_dir.exists():
        fail(
            error="Samples directory not found",
            field="voice/samples",
            fix=(
                f"Create {samples_dir} and drop 5+ writing samples there "
                "(LinkedIn posts, founder updates, real DMs to advisors). "
                "Then re-run /preseed-voice."
            ),
            file=str(samples_dir),
            code=2,
        )

    samples = load_samples(samples_dir)
    sample_files = [name for name, _ in samples]
    texts = [text for _, text in samples]

    sample_count = len(samples)
    if sample_count >= 5:
        confidence = "high"
    elif sample_count >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    if sample_count == 0:
        # build a minimal fingerprint with defaults so downstream skills don't
        # crash, but loudly warn.
        fp = {
            "sample_count": 0,
            "avg_sentence_length_words": 14.0,
            "contraction_rate": 0.4,
            "paragraph_avg_sentences": 2.0,
            "em_dash_rate": 0.2,
            "register": "casual_direct",
            "technical_density": 0.0,
            "opener_patterns": [],
            "closer_patterns": [],
            "signature_phrases": [],
            "banned_default": load_default_bans(workspace, skill_root),
            "banned_personal": [],
            "preferred_alternatives": preferred_alternatives(),
            "voice_score_threshold": args.threshold,
            "confidence": "low",
        }
    else:
        avg_sent = compute_avg_sentence_length(texts)
        contraction = compute_contraction_rate(texts)
        para_avg = compute_paragraph_avg_sentences(texts)
        em_rate = compute_em_dash_rate(texts)
        openers = extract_opener_patterns(texts)
        closers = extract_closer_patterns(texts)
        sigs = extract_signature_phrases(texts)
        register = classify_register(texts, avg_sent, contraction)
        tech_density = compute_technical_density(texts)
        defaults = load_default_bans(workspace, skill_root)
        personal = compute_banned_personal(texts, defaults)
        fp = {
            "sample_count": sample_count,
            "avg_sentence_length_words": avg_sent,
            "contraction_rate": contraction,
            "paragraph_avg_sentences": para_avg,
            "em_dash_rate": em_rate,
            "register": register,
            "technical_density": tech_density,
            "opener_patterns": openers,
            "closer_patterns": closers,
            "signature_phrases": sigs,
            "banned_default": defaults,
            "banned_personal": personal,
            "preferred_alternatives": preferred_alternatives(),
            "voice_score_threshold": args.threshold,
            "confidence": confidence,
        }

    voice_dir = workspace / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)

    fingerprint_path = voice_dir / "voice-fingerprint.yaml"
    founder_path = voice_dir / "founder-voice.md"
    examples_path = voice_dir / "voice-examples.md"

    try:
        fingerprint_path.write_text(render_fingerprint_yaml(fp),
                                    encoding="utf-8")
        founder_path.write_text(render_founder_voice_md(fp, sample_files),
                                encoding="utf-8")
        examples_path.write_text(render_voice_examples_md(fp),
                                 encoding="utf-8")
    except OSError as exc:
        fail(
            error=f"Could not write voice files: {exc}",
            field="voice/",
            fix="Check write permissions on the workspace.",
            code=1,
        )

    # append samples-derived bans
    if fp["banned_personal"]:
        try:
            append_anti_voice(workspace, fp["banned_personal"])
        except OSError as exc:
            fail(
                error=f"Could not append to anti-voice.txt: {exc}",
                field=".sys/anti-voice.txt",
                fix="Check write permissions on the workspace.",
                code=1,
            )

    summary = {
        "ok": True,
        "sample_count": sample_count,
        "confidence": fp["confidence"],
        "register": fp["register"],
        "avg_sentence_length_words": fp["avg_sentence_length_words"],
        "opener_patterns": fp["opener_patterns"],
        "closer_patterns": fp["closer_patterns"],
        "voice_score_threshold": fp["voice_score_threshold"],
        "files_written": [
            str(fingerprint_path),
            str(founder_path),
            str(examples_path),
        ],
        "anti_voice_appended": len(fp["banned_personal"]),
    }
    if confidence == "low":
        summary["warning"] = (
            "Fewer than 3 samples — fingerprint confidence is low. "
            "Add more samples and re-run."
        )
    print(json.dumps(summary, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
