#!/usr/bin/env python3
"""validate_round_brief.py — validate ~/fundraising/story/round-brief.yaml.

Confirms required fields are present and non-empty. Flags vague claims
that look like proof but aren't ("significant traction", "world-class
team", etc). Returns exit 0 on success, exit 1 with error envelope on
failure, exit 2 if the file is missing.

Stdlib-only YAML parser — small enough that we don't need PyYAML.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Required fields & vague-claim patterns
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = [
    "one_liner",
    "problem",
    "why_now",
    "solution",
    "traction",
    "ask",
    "team",
    "ideal_investor",
    "exclusions",
    "risks",
]

# Phrases that should never appear in a real round brief — they're verbal
# placeholder claims. The script flags them as warnings; the user has to
# decide whether to fix or override.
VAGUE_PATTERNS = [
    r"\bsignificant traction\b",
    r"\bworld[- ]class team\b",
    r"\bbest[- ]in[- ]class\b",
    r"\bgame[- ]chang(?:er|ing)\b",
    r"\bmassive (?:market|opportunity)\b",
    r"\brevolution(?:ize|ary|izing)\b",
    r"\bunique value proposition\b",
    r"\bsynergy\b",
    r"\bdisrupt(?:ive|ing|ion)\b",
    r"\bnext[- ]generation\b",
    r"\bstrong (?:traction|momentum|growth)\b",
    r"\bhuge (?:tam|market)\b",
    r"\bground[- ]breaking\b",
]


# ---------------------------------------------------------------------------
# Tiny YAML loader — handles the subset round-brief.yaml uses.
# Top-level keys can map to:
#   - scalar (string / number / bool / null)
#   - block string (next non-blank lines indented)
#   - list (`- item` lines indented)
#   - nested map (key: scalar/list at deeper indent)
# This is intentionally minimal; full PyYAML is optional.
# ---------------------------------------------------------------------------

def _load_yaml(text: str) -> dict:
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        pass
    return _load_yaml_minimal(text)


def _coerce_scalar(raw: str):
    raw = raw.strip()
    if raw == "" or raw.lower() == "null" or raw == "~":
        return None
    if raw.lower() in {"true", "yes"}:
        return True
    if raw.lower() in {"false", "no"}:
        return False
    if (raw.startswith('"') and raw.endswith('"')) or \
       (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


BLOCK_SCALAR_INDICATORS = {"|", "|-", "|+", ">", ">-", ">+"}


def _consume_block_scalar(
    raw_lines: list[str],
    start: int,
    key_indent: int,
    indicator: str,
) -> tuple[str, int]:
    """Consume a block scalar starting at line `start`.

    Returns (value, next_index_into_raw_lines). Includes lines with indent
    strictly greater than `key_indent`. Blank lines are preserved as empty
    lines for literal '|' style; folded '>' style joins on spaces with
    blanks acting as paragraph breaks.
    """
    folded = indicator.startswith(">")
    chomp = indicator[-1] if len(indicator) > 1 and indicator[-1] in {"-", "+"} else ""
    block_lines: list[str] = []
    j = start
    block_indent: int | None = None
    while j < len(raw_lines):
        raw = raw_lines[j]
        # blank line — keep going (it belongs to the block)
        if raw.strip() == "":
            block_lines.append("")
            j += 1
            continue
        cur_indent = len(raw) - len(raw.lstrip(" "))
        if cur_indent <= key_indent:
            break
        if block_indent is None:
            block_indent = cur_indent
        # Strip the block's base indentation
        strip_n = min(block_indent, cur_indent)
        block_lines.append(raw[strip_n:].rstrip("\r"))
        j += 1
    # Trim trailing empty lines according to chomping indicator
    while block_lines and block_lines[-1] == "":
        if chomp == "+":
            break
        block_lines.pop()
    if folded:
        # Folded: blanks are paragraph breaks (single newline), single newlines
        # become spaces.
        out_parts: list[str] = []
        buf: list[str] = []
        for line in block_lines:
            if line == "":
                if buf:
                    out_parts.append(" ".join(buf))
                    buf = []
                out_parts.append("")
            else:
                buf.append(line)
        if buf:
            out_parts.append(" ".join(buf))
        # Join paragraphs with newline; collapse runs of empties into a single \n
        value = "\n".join(out_parts)
        # Add a trailing newline for clip/keep
        if chomp != "-":
            value += "\n"
    else:
        value = "\n".join(block_lines)
        if chomp != "-":
            value += "\n"
    return value, j


def _load_yaml_minimal(text: str) -> dict:
    """Tiny indent-based YAML parser sufficient for round-brief.yaml.

    Handles block scalars (|, |-, |+, >, >-, >+) by consuming all lines
    indented deeper than the key, preserving content rather than merging
    it into following keys.
    """
    raw_lines = text.splitlines()

    def indent_of(s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    def is_blank_or_comment(s: str) -> bool:
        st = s.lstrip()
        return st == "" or st.startswith("#")

    def strip_inline_comment(s: str) -> str:
        # strip only inline (not in-string) comments — naive but matches input shape
        if "#" not in s:
            return s
        # heuristic: only strip if not within quotes
        in_s = False
        quote = ""
        out = []
        for ch in s:
            if in_s:
                if ch == quote:
                    in_s = False
                out.append(ch)
            else:
                if ch in ("'", '"'):
                    in_s = True
                    quote = ch
                    out.append(ch)
                elif ch == "#":
                    break
                else:
                    out.append(ch)
        return "".join(out).rstrip()

    def parse_block(start: int, base_indent: int) -> tuple:
        """Return (value, next_raw_index). value is dict, list, or string."""
        # Find first non-blank/non-comment line
        j = start
        while j < len(raw_lines) and is_blank_or_comment(raw_lines[j]):
            j += 1
        if j >= len(raw_lines):
            return None, j
        first = raw_lines[j]
        if indent_of(first) <= base_indent:
            return None, j
        # List?
        if first.lstrip().startswith("- "):
            items = []
            while j < len(raw_lines):
                if is_blank_or_comment(raw_lines[j]):
                    j += 1
                    continue
                line = raw_lines[j]
                if indent_of(line) <= base_indent:
                    break
                stripped = strip_inline_comment(line).rstrip()
                if not stripped.lstrip().startswith("- "):
                    break
                item = stripped.lstrip()[2:].strip()
                items.append(_coerce_scalar(item))
                j += 1
            return items, j
        # Nested map
        sub: dict = {}
        while j < len(raw_lines):
            if is_blank_or_comment(raw_lines[j]):
                j += 1
                continue
            line = raw_lines[j]
            ind = indent_of(line)
            if ind <= base_indent:
                break
            stripped_line = strip_inline_comment(line).rstrip().strip()
            if ":" not in stripped_line:
                # Should not happen for well-formed YAML at this level; skip.
                j += 1
                continue
            key, _, rest = stripped_line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest in BLOCK_SCALAR_INDICATORS:
                value, j2 = _consume_block_scalar(raw_lines, j + 1, ind, rest)
                sub[key] = value
                j = j2
            elif rest == "":
                child, j2 = parse_block(j + 1, ind)
                sub[key] = child if child is not None else ""
                j = j2
            else:
                sub[key] = _coerce_scalar(rest)
                j += 1
        return sub, j

    data: dict = {}
    i = 0
    while i < len(raw_lines):
        if is_blank_or_comment(raw_lines[i]):
            i += 1
            continue
        line = raw_lines[i]
        ind = indent_of(line)
        if ind != 0:
            i += 1
            continue
        stripped = strip_inline_comment(line).rstrip().strip()
        if ":" not in stripped:
            i += 1
            continue
        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest in BLOCK_SCALAR_INDICATORS:
            value, j = _consume_block_scalar(raw_lines, i + 1, 0, rest)
            data[key] = value
            i = j
        elif rest == "":
            value, j = parse_block(i + 1, 0)
            data[key] = value if value is not None else ""
            i = j
        else:
            data[key] = _coerce_scalar(rest)
            i += 1
    return data


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _flatten_for_search(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flatten_for_search(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_flatten_for_search(v) for v in value.values())
    return str(value)


def fail(error: str, *, field: str = "", fix: str = "", file: str = "",
         line: int = 0, code: int = 1) -> None:
    envelope = {"error": error, "field": field, "fix": fix}
    if file:
        envelope["file"] = file
    if line:
        envelope["line"] = line
    print(json.dumps(envelope))
    sys.exit(code)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Validate story/round-brief.yaml."
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Override path to round-brief.yaml.",
    )
    args = parser.parse_args(argv)

    path = args.path if args.path else (
        Path.home() / "fundraising" / "story" / "round-brief.yaml"
    )

    if not path.exists():
        fail(
            error="round-brief.yaml not found",
            field="story/round-brief.yaml",
            fix=(
                "Run /preseed-story to build the round brief, then re-run "
                "/preseed-campaign setup."
            ),
            file=str(path),
            code=2,
        )

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(
            error=f"Could not read round-brief.yaml: {exc}",
            field="story/round-brief.yaml",
            fix="Check file permissions.",
            file=str(path),
            code=1,
        )

    try:
        data = _load_yaml(text)
    except Exception as exc:
        fail(
            error=f"YAML parse failed: {exc}",
            field="story/round-brief.yaml",
            fix=(
                "Open the file and check for stray tabs or unmatched quotes. "
                "Indent with 2 spaces only."
            ),
            file=str(path),
            code=1,
        )

    if not isinstance(data, dict) or not data:
        fail(
            error="round-brief.yaml is empty or not a mapping",
            field="story/round-brief.yaml",
            fix="Re-run /preseed-story to regenerate the file.",
            file=str(path),
            code=1,
        )

    # Required field check.
    missing = []
    empty = []
    for fld in REQUIRED_FIELDS:
        if fld not in data:
            missing.append(fld)
        elif _is_empty(data[fld]):
            empty.append(fld)

    if missing:
        fail(
            error="Missing required field(s) in round-brief.yaml",
            field=missing[0],
            fix=(
                f"Add: {', '.join(missing)}. "
                "Re-run /preseed-story to regenerate the brief."
            ),
            file=str(path),
            code=1,
        )

    if empty:
        fail(
            error="Required field(s) present but empty",
            field=empty[0],
            fix=(
                f"Fill in: {', '.join(empty)}. Each field needs a real "
                "answer — vague placeholders fail the story gate."
            ),
            file=str(path),
            code=1,
        )

    # Vague-claim warning pass.
    haystack = _flatten_for_search(data).lower()
    warnings: list[str] = []
    for pattern in VAGUE_PATTERNS:
        if re.search(pattern, haystack, re.IGNORECASE):
            # readable phrase = strip regex bits
            readable = re.sub(r"\\b|\\|\(\?:|\)|\[\- \]", "", pattern)
            warnings.append(readable)

    summary = {
        "ok": True,
        "file": str(path),
        "fields_validated": REQUIRED_FIELDS,
        "vague_claim_warnings": warnings,
        "warning_message": (
            "Vague claims detected — replace with specific, dated proof."
            if warnings else ""
        ),
    }
    print(json.dumps(summary, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
