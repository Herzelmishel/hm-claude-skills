#!/usr/bin/env python3
"""score_voice_match.py — score a message 0–1 against a voice fingerprint.

Reads a fingerprint from voice-fingerprint.yaml and a message from
stdin or --message, then computes a composite voice_score with these
sub-scores:

  sentence_length_match   penalty if avg deviates >3 words from fp
  opener_match             1.0 if message opens with a known pattern, else penalty
  banned_phrase_check      0 hard if any banned phrase is present, else 1
  em_dash_match            penalty if em-dash use deviates >0.3 from fp

Banned phrases are a HARD veto: any banned-phrase hit caps the final
composite at 0.3 regardless of how the other dimensions score.

Output (stdout, JSON):
  {
    "voice_score": 0.78,
    "issues": ["sentence too long: 22 vs target 14"],
    "sub_scores": {...}
  }

Exit code: always 0 unless input is malformed. A low score is a flag,
not an error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from statistics import mean


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

def fail(error: str, *, field: str = "", fix: str = "", code: int = 1) -> None:
    print(json.dumps({"error": error, "field": field, "fix": fix}))
    sys.exit(code)


# ---------------------------------------------------------------------------
# Tiny YAML loader (top-level scalar + list values only — sufficient for
# voice-fingerprint.yaml).
# ---------------------------------------------------------------------------

def load_fingerprint_yaml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text)
        if isinstance(loaded, dict):
            return loaded
    except ImportError:
        pass
    return _load_yaml_minimal(text)


def _coerce(raw: str):
    raw = raw.strip()
    if raw == "" or raw.lower() in {"null", "~"}:
        return None
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
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
    """Top-level + simple list/map nesting parser."""
    lines = []
    for raw in text.splitlines():
        # strip whole-line comment, keep inline
        stripped = raw.split("#", 1)[0].rstrip() if raw.lstrip().startswith("#") \
            else raw.rstrip()
        if stripped.strip() == "":
            continue
        lines.append(stripped)

    data: dict = {}
    i = 0
    n = len(lines)

    def indent(s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    while i < n:
        line = lines[i]
        if indent(line) != 0 or ":" not in line:
            i += 1
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "" or rest in {"|", ">"}:
            # list or map
            j = i + 1
            children = []
            map_children: dict = {}
            mode = None  # "list" | "map"
            while j < n and indent(lines[j]) > 0:
                child = lines[j]
                child_stripped = child.strip()
                if child_stripped.startswith("- "):
                    mode = mode or "list"
                    item = child_stripped[2:].strip()
                    children.append(_coerce(item))
                elif child_stripped == "[]":
                    mode = "list"
                elif child_stripped == "{}":
                    mode = "map"
                elif ":" in child_stripped:
                    mode = mode or "map"
                    ck, _, cv = child_stripped.partition(":")
                    map_children[_coerce(ck.strip())] = _coerce(cv.strip())
                j += 1
            if mode == "list":
                data[key] = children
            elif mode == "map":
                data[key] = map_children
            else:
                data[key] = ""
            i = j
        else:
            data[key] = _coerce(rest)
            i += 1
    return data


# ---------------------------------------------------------------------------
# Tokenization (mirrors build_voice_fingerprint.py)
# ---------------------------------------------------------------------------

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def split_sentences(text: str) -> list[str]:
    """Split text into sentences with extra fallbacks for short messages.

    Beyond the default terminator+space+capital rule, also split on:
      - paragraph breaks (\n\n) and single \n followed by a capital
      - em-dashes preceded by 5+ words on the left side
      - if the result is still 1 sentence and the message has > 25 words,
        split on the longest pause character (em-dash, semicolon, or
        comma followed by a capital)
    """
    if not text:
        return []
    raw = text

    # First split on paragraph breaks: \n\n always splits; single \n
    # splits when followed by a capital.
    parts: list[str] = re.split(r"\n\s*\n+", raw)
    refined: list[str] = []
    for part in parts:
        # split on \n + capital
        sub = re.split(r"\n(?=[A-Z\"'(])", part)
        refined.extend(sub)

    # Apply default terminator+space+capital rule across each chunk
    refined2: list[str] = []
    for chunk in refined:
        chunk = re.sub(r"[ \t]+", " ", chunk).strip()
        if not chunk:
            continue
        for s in SENTENCE_SPLIT_RE.split(chunk):
            s = s.strip()
            if s:
                refined2.append(s)

    # Em-dash split when there are 5+ words on the left side
    refined3: list[str] = []
    for s in refined2:
        # repeatedly split off leading clause if rule satisfied
        remaining = s
        while True:
            m = re.search(r"\s—\s|\s--\s", remaining)
            if not m:
                break
            left = remaining[: m.start()]
            right = remaining[m.end():]
            if len(WORD_RE.findall(left)) >= 5 and right.strip():
                refined3.append(left.strip())
                remaining = right.strip()
                continue
            break
        if remaining.strip():
            refined3.append(remaining.strip())

    # Final fallback: still 1 sentence and > 25 words → split on longest pause
    if len(refined3) <= 1 and refined3:
        only = refined3[0]
        if len(WORD_RE.findall(only)) > 25:
            # Try em-dash, then semicolon, then comma+capital
            split_re = re.compile(
                r"\s—\s|\s--\s|;\s+|,\s+(?=[A-Z])"
            )
            pieces = [p.strip() for p in split_re.split(only) if p.strip()]
            if len(pieces) > 1:
                refined3 = pieces

    return refined3


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


# ---------------------------------------------------------------------------
# Sub-scorers
# ---------------------------------------------------------------------------

def score_sentence_length(message: str, target_avg: float) -> tuple[float, str]:
    sents = split_sentences(message)
    if not sents:
        return 1.0, ""
    lengths = [word_count(s) for s in sents if word_count(s) > 0]
    if not lengths:
        return 1.0, ""
    avg = mean(lengths)
    delta = abs(avg - target_avg)
    if delta <= 3:
        return 1.0, ""
    # 1.0 at delta=3, 0.0 at delta=10
    score = max(0.0, 1.0 - (delta - 3) / 7)
    if avg > target_avg:
        issue = (f"sentence too long: avg {avg:.1f} vs target {target_avg:.1f}"
                 " (±3 tolerance)")
    else:
        issue = (f"sentence too short: avg {avg:.1f} vs target "
                 f"{target_avg:.1f} (±3 tolerance)")
    return round(score, 3), issue


def score_opener_match(message: str, opener_patterns: list[str]
                       ) -> tuple[float, str]:
    if not opener_patterns:
        return 1.0, ""
    sents = split_sentences(message)
    if not sents:
        return 0.5, "no opener detectable"
    first = sents[0].lower().strip()
    for pat in opener_patterns:
        if not pat:
            continue
        if first.startswith(pat.lower().strip()):
            return 1.0, ""
    return 0.6, (
        "opener does not match any of: "
        + ", ".join(f"'{p}'" for p in opener_patterns[:3])
    )


def score_banned_phrases(message: str, banned: list[str]
                         ) -> tuple[float, list[str]]:
    if not banned:
        return 1.0, []
    haystack = message.lower()
    hits = []
    for phrase in banned:
        if not phrase:
            continue
        if phrase.lower() in haystack:
            hits.append(phrase)
    if hits:
        # cap message returned to keep envelope small
        return 0.0, [f"uses banned phrase: '{h}'" for h in hits[:5]]
    return 1.0, []


def score_em_dash(message: str, target_rate: float) -> tuple[float, str]:
    if not message:
        return 1.0, ""
    chars = len(message) or 1
    occurrences = message.count("—") + message.count("--")
    per_1k = occurrences / (chars / 1000)
    msg_rate = min(1.0, per_1k / 5)
    delta = abs(msg_rate - target_rate)
    if delta <= 0.3:
        return 1.0, ""
    score = max(0.0, 1.0 - (delta - 0.3) * 2)
    if msg_rate > target_rate:
        return round(score, 3), (
            f"em-dash overused (rate {msg_rate:.2f} vs target "
            f"{target_rate:.2f})"
        )
    return round(score, 3), (
        f"em-dash underused (rate {msg_rate:.2f} vs target "
        f"{target_rate:.2f})"
    )


# ---------------------------------------------------------------------------
# Composite score
# ---------------------------------------------------------------------------

WEIGHTS = {
    "sentence_length": 0.30,
    "opener": 0.20,
    "banned_phrase": 0.40,  # banned phrases are critical
    "em_dash": 0.10,
}


def compute_voice_score(message: str, fp: dict) -> dict:
    target_avg = float(fp.get("avg_sentence_length_words") or 14)
    openers = fp.get("opener_patterns") or []
    banned = list(fp.get("banned_default") or []) + \
        list(fp.get("banned_personal") or [])
    em_target = float(fp.get("em_dash_rate") or 0.0)

    s_len, issue_len = score_sentence_length(message, target_avg)
    s_open, issue_open = score_opener_match(message, openers)
    s_banned, issues_banned = score_banned_phrases(message, banned)
    s_em, issue_em = score_em_dash(message, em_target)

    composite = (
        s_len * WEIGHTS["sentence_length"]
        + s_open * WEIGHTS["opener"]
        + s_banned * WEIGHTS["banned_phrase"]
        + s_em * WEIGHTS["em_dash"]
    )

    # Banned phrases are a HARD veto: any banned-phrase hit caps the
    # composite at 0.3 so the message still surfaces a numeric hint of why
    # but never crosses the review threshold.
    if s_banned == 0.0:
        composite = min(composite, 0.3)

    issues: list[str] = []
    if issue_len:
        issues.append(issue_len)
    if issue_open:
        issues.append(issue_open)
    issues.extend(issues_banned)
    if issue_em:
        issues.append(issue_em)

    return {
        "voice_score": round(composite, 3),
        "threshold": float(fp.get("voice_score_threshold") or 0.7),
        "needs_human_review": (
            "high" if composite < float(fp.get("voice_score_threshold") or 0.7)
            else "no"
        ),
        "issues": issues,
        "sub_scores": {
            "sentence_length": s_len,
            "opener": s_open,
            "banned_phrase": s_banned,
            "em_dash": s_em,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Score a message against a voice fingerprint."
    )
    parser.add_argument(
        "--fingerprint",
        type=Path,
        default=None,
        help="Path to voice-fingerprint.yaml.",
    )
    parser.add_argument(
        "--message",
        type=str,
        default=None,
        help="Inline message to score. If omitted, read from stdin.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Override workspace root.",
    )
    args = parser.parse_args(argv)

    workspace = args.workspace if args.workspace else (
        Path.home() / "fundraising"
    )
    fp_path = args.fingerprint if args.fingerprint else (
        workspace / "voice" / "voice-fingerprint.yaml"
    )

    if not fp_path.exists():
        fail(
            error="voice-fingerprint.yaml not found",
            field="voice/voice-fingerprint.yaml",
            fix="Run /preseed-voice to build the fingerprint first.",
            code=2,
        )

    try:
        fp = load_fingerprint_yaml(fp_path)
    except Exception as exc:
        fail(
            error=f"Could not parse voice-fingerprint.yaml: {exc}",
            field="voice/voice-fingerprint.yaml",
            fix="Re-run /preseed-voice to regenerate the fingerprint.",
            code=1,
        )

    if args.message is not None:
        message = args.message
    else:
        message = sys.stdin.read()

    if not message or not message.strip():
        fail(
            error="No message provided",
            field="message",
            fix=(
                "Pass via --message '<text>' or pipe a message to stdin."
            ),
            code=1,
        )

    result = compute_voice_score(message, fp)
    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
