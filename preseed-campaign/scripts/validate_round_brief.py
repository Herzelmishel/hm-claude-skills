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


def _load_yaml_minimal(text: str) -> dict:
    """Tiny indent-based YAML parser sufficient for round-brief.yaml."""
    lines = text.splitlines()
    # strip comments / blank lines but remember original indices
    cleaned = []
    for idx, raw in enumerate(lines):
        stripped = raw.split("#", 1)[0].rstrip() if "#" in raw else raw.rstrip()
        if stripped.strip() == "":
            continue
        cleaned.append((idx, stripped))

    data: dict = {}
    i = 0

    def indent_of(s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    def parse_block(start: int, base_indent: int) -> tuple:
        """Return (value, next_index). value is dict, list, or string."""
        # detect list vs map by first child line
        if start >= len(cleaned):
            return None, start
        idx, line = cleaned[start]
        if indent_of(line) <= base_indent:
            return None, start
        if line.lstrip().startswith("- "):
            items = []
            j = start
            while j < len(cleaned):
                _, l = cleaned[j]
                if indent_of(l) <= base_indent:
                    break
                if not l.lstrip().startswith("- "):
                    break
                item = l.lstrip()[2:].strip()
                items.append(_coerce_scalar(item))
                j += 1
            return items, j
        # nested map
        sub: dict = {}
        j = start
        while j < len(cleaned):
            _, l = cleaned[j]
            ind = indent_of(l)
            if ind <= base_indent:
                break
            stripped_line = l.strip()
            if ":" not in stripped_line:
                # treat as block scalar continuation — append to last key
                if sub:
                    last_key = list(sub.keys())[-1]
                    if isinstance(sub[last_key], str):
                        sub[last_key] += " " + stripped_line
                j += 1
                continue
            key, _, rest = stripped_line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest == "" or rest == "|" or rest == ">":
                child, j2 = parse_block(j + 1, ind)
                if child is None:
                    sub[key] = ""
                else:
                    sub[key] = child
                j = j2
            else:
                sub[key] = _coerce_scalar(rest)
                j += 1
        return sub, j

    while i < len(cleaned):
        _, line = cleaned[i]
        ind = indent_of(line)
        stripped = line.strip()
        if ind != 0 or ":" not in stripped:
            i += 1
            continue
        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest in {"", "|", ">"}:
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
